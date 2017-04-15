# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Original Author = Jacob Morris
# URL = blendingjacob.blogspot.com

bl_info = {
    "name": "CubeSter",
    "author": "Jacob Morris",
    "version": (0, 7),
    "blender": (2, 78, 0),
    "location": "View 3D > Toolbar > CubeSter",
    "description": "Takes image, image sequence, or audio file and converts it "
                   "into a height map based on pixel color and alpha values",
    "category": "Add Mesh"
    }

import bpy
import bmesh
from bpy.props import (
        BoolProperty,
        IntProperty,
        FloatProperty,
        StringProperty,
        EnumProperty,
        )
from bpy.types import (
        Operator,
        Panel,
        )

import timeit
from random import uniform
from math import radians
from os import (
        path,
        listdir,
        )


# load image if possible
def adjust_selected_image(self, context):
    scene = context.scene
    try:
        image = bpy.data.images.load(scene.cubester_load_image)
        scene.cubester_image = image.name
    except RuntimeError:
        self.report({"ERROR"}, "CubeSter: '{}' could not be loaded".format(scene.cubester_load_image))


# load color image if possible
def adjust_selected_color_image(self, context):
    scene = context.scene
    try:
        image = bpy.data.images.load(scene.cubester_load_color_image)
        scene.cubester_color_image = image.name
    except RuntimeError:
        self.report({"ERROR"}, "CubeSter: '{}' could not be loaded".format(scene.cubester_load_color_image))


# crate block at center position x, y with block width 2 * hx and 2 * hy and height of h
def create_block(x, y, hw, h, verts: list, faces: list):
    if bpy.context.scene.cubester_block_style == "size":
        z = 0.0
    else:
        z = h
        h = 2 * hw

    p = len(verts)
    verts += [(x - hw, y - hw, z), (x + hw, y - hw, z), (x + hw, y + hw, z), (x - hw, y + hw, z)]
    verts += [(x - hw, y - hw, z + h), (x + hw, y - hw, z + h),
              (x + hw, y + hw, z + h), (x - hw, y + hw, z + h)]

    faces += [(p, p + 1, p + 5, p + 4), (p + 1, p + 2, p + 6, p + 5),
              (p + 2, p + 3, p + 7, p + 6), (p, p + 4, p + 7, p + 3),
              (p + 4, p + 5, p + 6, p + 7), (p, p + 3, p + 2, p + 1)]


# go through all frames in len(frames), adjusting values at frames[x][y]
def create_f_curves(mesh, frames, frame_step_size, style):
    # use data to animate mesh
    action = bpy.data.actions.new("CubeSterAnimation")

    mesh.animation_data_create()
    mesh.animation_data.action = action

    data_path = "vertices[%d].co"

    vert_index = 4 if style == "blocks" else 0  # index of first vertex

    # loop for every face height value
    for frame_start_vert in range(len(frames[0])):
        # only go once if plane, otherwise do all four vertices that are in top plane if blocks
        end_point = frame_start_vert + 4 if style == "blocks" else frame_start_vert + 1

        # loop through to get the four vertices that compose the face
        for frame_vert in range(frame_start_vert, end_point):
            # fcurves for x, y, z
            fcurves = [action.fcurves.new(data_path % vert_index, i) for i in range(3)]
            frame_counter = 0  # go through each frame and add position
            temp_v = mesh.vertices[vert_index].co

            # loop through frames
            for frame in frames:
                # new x, y, z positions
                vals = [temp_v[0], temp_v[1], frame[frame_start_vert]]
                for i in range(3):  # for each x, y, z set each corresponding fcurve
                    fcurves[i].keyframe_points.insert(frame_counter, vals[i], {'FAST'})

                frame_counter += frame_step_size  # skip frames for smoother animation

            vert_index += 1

        # only skip vertices if made of blocks
        if style == "blocks":
            vert_index += 4


# create material with given name, apply to object
def create_material(scene, ob, name):
    mat = bpy.data.materials.new("CubeSter_" + name)

    # image
    if not scene.cubester_use_image_color and scene.cubester_color_image in bpy.data.images:
        image = bpy.data.images[scene.cubester_color_image]
    else:
        image = bpy.data.images[scene.cubester_image]

    if scene.render.engine == "CYCLES":
        mat.use_nodes = True
        nodes = mat.node_tree.nodes

        att = nodes.new("ShaderNodeAttribute")
        att.attribute_name = "Col"
        att.location = (-200, 300)

        att = nodes.new("ShaderNodeTexImage")
        att.image = image

        if scene.cubester_load_type == "multiple":
            att.image.source = "SEQUENCE"
        att.location = (-200, 700)

        att = nodes.new("ShaderNodeTexCoord")
        att.location = (-450, 600)

        if scene.cubester_materials == "image":
            mat.node_tree.links.new(
                            nodes["Image Texture"].outputs[0],
                            nodes["Diffuse BSDF"].inputs[0]
                            )
            mat.node_tree.links.new(
                            nodes["Texture Coordinate"].outputs[2],
                            nodes["Image Texture"].inputs[0]
                            )
        else:
            mat.node_tree.links.new(
                            nodes["Attribute"].outputs[0],
                            nodes["Diffuse BSDF"].inputs[0]
                            )
    else:
        if scene.cubester_materials == "image" or scene.render.engine != "BLENDER_RENDER":
            tex = bpy.data.textures.new("CubeSter_" + name, "IMAGE")
            tex.image = image
            slot = mat.texture_slots.add()
            slot.texture = tex
        else:
            mat.use_vertex_color_paint = True

    ob.data.materials.append(mat)


# generate mesh from audio
def create_mesh_from_audio(self, scene, verts, faces):
    audio_filepath = scene.cubester_audio_path
    width = scene.cubester_audio_width_blocks
    length = scene.cubester_audio_length_blocks
    size_per_hundred = scene.cubester_size_per_hundred_pixels

    size = size_per_hundred / 100

    # create all blocks
    y = -(width / 2) * size + (size / 2)
    for r in range(width):
        x = -(length / 2) * size + (size / 2)
        for c in range(length):
            create_block(x, y, size / 2, 1, verts, faces)

            x += size
        y += size

    # create object
    mesh = bpy.data.meshes.new("cubed")
    mesh.from_pydata(verts, [], faces)
    ob = bpy.data.objects.new("cubed", mesh)
    bpy.context.scene.objects.link(ob)
    bpy.context.scene.objects.active = ob
    ob.select = True

    # inital vertex colors
    if scene.cubester_materials == "image":
        picture = bpy.data.images[scene.cubester_color_image]
        pixels = list(picture.pixels)
        vert_colors = []

        skip_y = int(picture.size[1] / width)
        skip_x = int(picture.size[0] / length)

        for row in range(0, picture.size[1], skip_y + 1):
            # go through each column, step by appropriate amount
            for column in range(0, picture.size[0] * 4, 4 + skip_x * 4):
                r, g, b, a = get_pixel_values(picture, pixels, row, column)
                vert_colors += [(r, g, b) for i in range(24)]

        bpy.ops.mesh.vertex_color_add()
        i = 0
        for c in ob.data.vertex_colors[0].data:
            c.color = vert_colors[i]
            i += 1

        # image sequence handling
        if scene.cubester_load_type == "multiple":
            images = find_sequence_images(self, bpy.context)

            frames_vert_colors = []

            max_images = scene.cubester_max_images + 1 if \
                        len(images[0]) > scene.cubester_max_images else len(images[0])

            # goes through and for each image for each block finds new height
            for image_index in range(0, max_images, scene.cubester_skip_images):
                filepath = images[0][image_index]
                name = images[1][image_index]
                picture = fetch_image(self, name, filepath)
                pixels = list(picture.pixels)

                frame_colors = []

                for row in range(0, picture.size[1], skip_y + 1):
                    for column in range(0, picture.size[0] * 4, 4 + skip_x * 4):
                        r, g, b, a = get_pixel_values(picture, pixels, row, column)
                        frame_colors += [(r, g, b) for i in range(24)]

                frames_vert_colors.append(frame_colors)

            scene.cubester_vertex_colors[ob.name] = {"type": "vertex", "frames": frames_vert_colors,
                                                     "frame_skip": scene.cubester_frame_step,
                                                     "total_images": max_images}

        # either add material or create
        if ("CubeSter_" + "Vertex") in bpy.data.materials:
            ob.data.materials.append(bpy.data.materials["CubeSter_" + "Vertex"])
        else:
            create_material(scene, ob, "Vertex")

    # set keyframe for each object as initial point
    frame = [1 for i in range(int(len(verts) / 8))]
    frames = [frame]

    area = bpy.context.area
    old_type = area.type
    area.type = "GRAPH_EDITOR"

    scene.frame_current = 0

    create_f_curves(mesh, frames, 1, "blocks")

    # deselect all fcurves
    fcurves = ob.data.animation_data.action.fcurves.data.fcurves
    for i in fcurves:
        i.select = False

    max_images = scene.cubester_audio_max_freq
    min_freq = scene.cubester_audio_min_freq
    freq_frame = scene.cubester_audio_offset_type

    freq_step = (max_images - min_freq) / length
    freq_sub_step = freq_step / width

    frame_step = scene.cubester_audio_frame_offset

    # animate each block with a portion of the frequency
    for c in range(length):
        frame_off = 0
        for r in range(width):
            if freq_frame == "frame":
                scene.frame_current = frame_off
                l = c * freq_step
                h = (c + 1) * freq_step
                frame_off += frame_step
            else:
                l = c * freq_step + (r * freq_sub_step)
                h = c * freq_step + ((r + 1) * freq_sub_step)

            pos = c + (r * length)  # block number
            index = pos * 4  # first index for vertex

            # select curves
            for i in range(index, index + 4):
                curve = i * 3 + 2  # fcurve location
                fcurves[curve].select = True

            bpy.ops.graph.sound_bake(filepath=bpy.path.abspath(audio_filepath), low=l, high=h)

            # deselect curves
            for i in range(index, index + 4):
                curve = i * 3 + 2  # fcurve location
                fcurves[curve].select = False

    area.type = old_type

    # UV unwrap
    create_uv_map(bpy.context, width, length)

    # if radial apply needed modifiers
    if scene.cubester_audio_block_layout == "radial":
        # add bezier curve of correct width
        bpy.ops.curve.primitive_bezier_circle_add()
        curve = bpy.context.object
        # slope determined off of collected data
        curve_size = (0.319 * (width * (size * 100)) - 0.0169) / 100
        curve.dimensions = (curve_size, curve_size, 0.0)
        # correct for z height
        curve.scale = (curve.scale[0], curve.scale[0], curve.scale[0])

        ob.select = True
        curve.select = False
        scene.objects.active = ob

        # data was collected and then multi-variable regression was done in Excel
        # influence of width and length
        width_infl, length_infl, intercept = -0.159125, 0.49996, 0.007637
        x_offset = ((width * (size * 100) * width_infl) +
                   (length * (size * 100) * length_infl) + intercept) / 100
        ob.location = (ob.location[0] + x_offset, ob.location[1], ob.location[2])

        ob.rotation_euler = (radians(-90), 0.0, 0.0)
        bpy.ops.object.modifier_add(type="CURVE")
        ob.modifiers["Curve"].object = curve
        ob.modifiers["Curve"].deform_axis = "POS_Z"


# generate mesh from image(s)
def create_mesh_from_image(self, scene, verts, faces):
    context = bpy.context
    picture = bpy.data.images[scene.cubester_image]
    pixels = list(picture.pixels)

    x_pixels = picture.size[0] / (scene.cubester_skip_pixels + 1)
    y_pixels = picture.size[1] / (scene.cubester_skip_pixels + 1)

    width = x_pixels / 100 * scene.cubester_size_per_hundred_pixels
    height = y_pixels / 100 * scene.cubester_size_per_hundred_pixels

    step = width / x_pixels
    half_width = step / 2

    y = -height / 2 + half_width

    vert_colors = []
    weights = [uniform(0.0, 1.0) for i in range(4)]  # random weights
    rows = 0

    # go through each row of pixels stepping by scene.cubester_skip_pixels + 1
    for row in range(0, picture.size[1], scene.cubester_skip_pixels + 1):
        rows += 1
        x = -width / 2 + half_width  # reset to left edge of mesh
        # go through each column, step by appropriate amount
        for column in range(0, picture.size[0] * 4, 4 + scene.cubester_skip_pixels * 4):
            r, g, b, a = get_pixel_values(picture, pixels, row, column)
            h = find_point_height(r, g, b, a, scene)

            # if not transparent
            if h != -1:
                if scene.cubester_mesh_style == "blocks":
                    create_block(x, y, half_width, h, verts, faces)
                    vert_colors += [(r, g, b) for i in range(24)]
                else:
                    verts += [(x, y, h)]
                    vert_colors += [(r, g, b) for i in range(4)]

            x += step
        y += step

        # if plane not blocks, then remove last 4 items from vertex_colors
        # as the faces have already wrapped around
        if scene.cubester_mesh_style == "plane":
            del vert_colors[len(vert_colors) - 4:len(vert_colors)]

    # create faces if plane based and not block based
    if scene.cubester_mesh_style == "plane":
        off = int(len(verts) / rows)
        for r in range(rows - 1):
            for c in range(off - 1):
                faces += [(r * off + c, r * off + c + 1, (r + 1) * off + c + 1, (r + 1) * off + c)]

    mesh = bpy.data.meshes.new("cubed")
    mesh.from_pydata(verts, [], faces)
    ob = bpy.data.objects.new("cubed", mesh)
    context.scene.objects.link(ob)
    context.scene.objects.active = ob
    ob.select = True

    # uv unwrap
    if scene.cubester_mesh_style == "blocks":
        create_uv_map(context, rows, int(len(faces) / 6 / rows))
    else:
        create_uv_map(context, rows - 1, int(len(faces) / (rows - 1)))

    # material
    # determine name and if already created
    if scene.cubester_materials == "vertex":  # vertex color
        image_name = "Vertex"
    elif not scene.cubester_use_image_color and scene.cubester_color_image in bpy.data.images and \
            scene.cubester_materials == "image":  # replaced image
        image_name = scene.cubester_color_image
    else:  # normal image
        image_name = scene.cubester_image

    # either add material or create
    if ("CubeSter_" + image_name) in bpy.data.materials:
        ob.data.materials.append(bpy.data.materials["CubeSter_" + image_name])

    # create material
    else:
        create_material(scene, ob, image_name)

    # vertex colors
    bpy.ops.mesh.vertex_color_add()
    i = 0
    for c in ob.data.vertex_colors[0].data:
        c.color = vert_colors[i]
        i += 1

    frames = []
    # image sequence handling
    if scene.cubester_load_type == "multiple":
        images = find_sequence_images(self, context)
        frames_vert_colors = []

        max_images = scene.cubester_max_images + 1 if \
                    len(images[0]) > scene.cubester_max_images else len(images[0])

        # goes through and for each image for each block finds new height
        for image_index in range(0, max_images, scene.cubester_skip_images):
            filepath = images[0][image_index]
            name = images[1][image_index]
            picture = fetch_image(self, name, filepath)
            pixels = list(picture.pixels)

            frame_heights = []
            frame_colors = []

            for row in range(0, picture.size[1], scene.cubester_skip_pixels + 1):
                for column in range(0, picture.size[0] * 4, 4 + scene.cubester_skip_pixels * 4):
                    r, g, b, a = get_pixel_values(picture, pixels, row, column)
                    h = find_point_height(r, g, b, a, scene)

                    if h != -1:
                        frame_heights.append(h)
                        if scene.cubester_mesh_style == "blocks":
                            frame_colors += [(r, g, b) for i in range(24)]
                        else:
                            frame_colors += [(r, g, b) for i in range(4)]

            if scene.cubester_mesh_style == "plane":
                del vert_colors[len(vert_colors) - 4:len(vert_colors)]

            frames.append(frame_heights)
            frames_vert_colors.append(frame_colors)

        # determine what data to use
        if scene.cubester_materials == "vertex" or scene.render.engine == "BLENDER_ENGINE":
            scene.cubester_vertex_colors[ob.name] = {
                                            "type": "vertex", "frames": frames_vert_colors,
                                            "frame_skip": scene.cubester_frame_step,
                                            "total_images": max_images
                                            }
        else:
            scene.cubester_vertex_colors[ob.name] = {
                                            "type": "image", "frame_skip": scene.cubester_frame_step,
                                            "total_images": max_images
                                            }
            att = get_image_node(ob.data.materials[0])
            att.image_user.frame_duration = len(frames) * scene.cubester_frame_step

        # animate mesh
        create_f_curves(mesh, frames, scene.cubester_frame_step, scene.cubester_mesh_style)


# generate uv map for object
def create_uv_map(context, rows, columns):
    mesh = context.object.data
    mesh.uv_textures.new("cubester")
    bm = bmesh.new()
    bm.from_mesh(mesh)

    uv_layer = bm.loops.layers.uv[0]
    bm.faces.ensure_lookup_table()

    x_scale = 1 / columns
    y_scale = 1 / rows

    y_pos = 0.0
    x_pos = 0.0
    count = columns - 1  # hold current count to compare to if need to go to next row

    # if blocks
    if context.scene.cubester_mesh_style == "blocks":
        for fa in range(int(len(bm.faces) / 6)):
            for i in range(6):
                pos = (fa * 6) + i
                bm.faces[pos].loops[0][uv_layer].uv = (x_pos, y_pos)
                bm.faces[pos].loops[1][uv_layer].uv = (x_pos + x_scale, y_pos)
                bm.faces[pos].loops[2][uv_layer].uv = (x_pos + x_scale, y_pos + y_scale)
                bm.faces[pos].loops[3][uv_layer].uv = (x_pos, y_pos + y_scale)

            x_pos += x_scale

            if fa >= count:
                y_pos += y_scale
                x_pos = 0.0
                count += columns

    # if planes
    else:
        for fa in range(len(bm.faces)):
            bm.faces[fa].loops[0][uv_layer].uv = (x_pos, y_pos)
            bm.faces[fa].loops[1][uv_layer].uv = (x_pos + x_scale, y_pos)
            bm.faces[fa].loops[2][uv_layer].uv = (x_pos + x_scale, y_pos + y_scale)
            bm.faces[fa].loops[3][uv_layer].uv = (x_pos, y_pos + y_scale)

            x_pos += x_scale

            if fa >= count:
                y_pos += y_scale
                x_pos = 0.0
                count += columns

    bm.to_mesh(mesh)


# returns length in frames
def find_audio_length(self, context):
    audio_file = context.scene.cubester_audio_path
    length = 0

    if audio_file != "":
        # confirm that strip hasn't been loaded yet
        for strip in context.scene.sequence_editor.sequences_all:
            if type(strip) == bpy.types.SoundSequence and strip.sound.filepath == audio_file:
                length = strip.frame_final_duration

        if length == 0:
            area = context.area
            old_type = area.type
            area.type = "SEQUENCE_EDITOR"

            bpy.ops.sequencer.sound_strip_add(filepath=audio_file)
            area.type = old_type

        # find audio file
        for strip in context.scene.sequence_editor.sequences_all:
            if type(strip) == bpy.types.SoundSequence and strip.sound.filepath == audio_file:
                length = strip.frame_final_duration

    context.scene.cubester_audio_file_length = str(length)


# if already loaded return image, else load and return
def fetch_image(self, name, load_path):
    if name in bpy.data.images:
        return bpy.data.images[name]
    else:
        try:
            image = bpy.data.images.load(load_path)
            return image
        except RuntimeError:
            self.report({"ERROR"}, "CubeSter: '{}' could not be loaded".format(load_path))
            return None


# find height for point
def find_point_height(r, g, b, a, scene):
    if a:  # if not completely transparent
        normalize = 1

        # channel weighting
        if not scene.cubester_advanced:
            composed = 0.25 * r + 0.25 * g + 0.25 * b + 0.25 * a
        else:
            # user defined weighting
            if not scene.cubester_random_weights:
                composed = scene.cubester_weight_r * r + scene.cubester_weight_g * g + \
                        scene.cubester_weight_b * b + scene.cubester_weight_a * a
                total = scene.cubester_weight_r + scene.cubester_weight_g + scene.cubester_weight_b + \
                        scene.cubester_weight_a

                normalize = 1 / total
            # random weighting
            else:
                weights = [uniform(0.0, 1.0) for i in range(4)]
                composed = weights[0] * r + weights[1] * g + weights[2] * b + weights[3] * a
                total = weights[0] + weights[1] + weights[2] + weights[3]
                normalize = 1 / total

        if scene.cubester_invert:
            h = (1 - composed) * scene.cubester_height_scale * normalize
        else:
            h = composed * scene.cubester_height_scale * normalize

        return h
    else:
        return -1


# find all images that would belong to sequence
def find_sequence_images(self, context):
    scene = context.scene
    images = [[], []]

    if scene.cubester_image in bpy.data.images:
        image = bpy.data.images[scene.cubester_image]
        main = image.name.split(".")[0]

        # first part of name to check against other files
        length = len(main)
        keep_going = True
        for i in range(length - 1, -1, -1):
            if main[i].isdigit() and keep_going:
                length -= 1
            else:
                keep_going = not keep_going
        name = main[0:length]

        dir_name = path.dirname(bpy.path.abspath(image.filepath))

        try:
            for file in listdir(dir_name):
                if path.isfile(path.join(dir_name, file)) and file.startswith(name):
                    images[0].append(path.join(dir_name, file))
                    images[1].append(file)
        except FileNotFoundError:
            self.report({"ERROR"}, "CubeSter: '{}' directory not found".format(dir_name))

    return images


# get image node
def get_image_node(mat):
    nodes = mat.node_tree.nodes
    att = nodes["Image Texture"]

    return att


# get the RGBA values from pixel
def get_pixel_values(picture, pixels, row, column):
    # determine i position to start at based on row and column position
    i = (row * picture.size[0] * 4) + column
    pixs = pixels[i: i + 4]
    r = pixs[0]
    g = pixs[1]
    b = pixs[2]
    a = pixs[3]

    return r, g, b, a


# frame change handler for materials
def material_frame_handler(scene):
    frame = scene.frame_current

    keys = list(scene.cubester_vertex_colors.keys())

    # get keys and see if object is still in scene
    for i in keys:
        # if object is in scene then update information
        if i in bpy.data.objects:
            ob = bpy.data.objects[i]
            data = scene.cubester_vertex_colors[ob.name]
            skip_frames = data["frame_skip"]

            # update materials using vertex colors
            if data['type'] == "vertex":
                colors = data["frames"]

                if frame % skip_frames == 0 and 0 <= frame < (data['total_images'] - 1) * skip_frames:
                    use_frame = int(frame / skip_frames)
                    color = colors[use_frame]

                    i = 0
                    for c in ob.data.vertex_colors[0].data:
                        c.color = color[i]
                        i += 1

            else:
                att = get_image_node(ob.data.materials[0])
                offset = frame - int(frame / skip_frames)
                att.image_user.frame_offset = -offset

        # if the object is no longer in the scene then delete then entry
        else:
            del scene.cubester_vertex_colors[i]


# main properties
bpy.types.Scene.cubester_audio_image = EnumProperty(
                            name="Input Type",
                            items=(("image", "Image", ""),
                                   ("audio", "Audio", ""))
                                   )
bpy.types.Scene.cubester_audio_file_length = StringProperty(
                            default=""
                            )
# audio
bpy.types.Scene.cubester_audio_path = StringProperty(
                            default="",
                            name="Audio File",
                            subtype="FILE_PATH",
                            update=find_audio_length
                            )
bpy.types.Scene.cubester_audio_min_freq = IntProperty(
                            name="Minimum Frequency",
                            min=20, max=100000,
                            default=20
                            )
bpy.types.Scene.cubester_audio_max_freq = IntProperty(
                            name="Maximum Frequency",
                            min=21, max=999999,
                            default=5000
                            )
bpy.types.Scene.cubester_audio_offset_type = EnumProperty(
                            name="Offset Type",
                            items=(("freq", "Frequency Offset", ""),
                                   ("frame", "Frame Offset", "")),
                            description="Type of offset per row of mesh"
                            )
bpy.types.Scene.cubester_audio_frame_offset = IntProperty(
                            name="Frame Offset",
                            min=0, max=10,
                            default=2
                            )
bpy.types.Scene.cubester_audio_block_layout = EnumProperty(
                            name="Block Layout",
                            items=(("rectangle", "Rectangular", ""),
                                  ("radial", "Radial", ""))
                            )
bpy.types.Scene.cubester_audio_width_blocks = IntProperty(
                            name="Width Block Count",
                            min=1, max=10000,
                            default=5
                            )
bpy.types.Scene.cubester_audio_length_blocks = IntProperty(
                            name="Length Block Count",
                            min=1, max=10000,
                            default=50
                            )
# image
bpy.types.Scene.cubester_load_type = EnumProperty(
                            name="Image Input Type",
                            items=(("single", "Single Image", ""),
                                  ("multiple", "Image Sequence", ""))
                            )
bpy.types.Scene.cubester_image = StringProperty(
                            default="",
                            name=""
                            )
bpy.types.Scene.cubester_load_image = StringProperty(
                            default="",
                            name="Load Image",
                            subtype="FILE_PATH",
                            update=adjust_selected_image
                            )
bpy.types.Scene.cubester_skip_images = IntProperty(
                            name="Image Step",
                            min=1, max=30,
                            default=1,
                            description="Step from image to image by this number"
                            )
bpy.types.Scene.cubester_max_images = IntProperty(
                            name="Max Number Of Images",
                            min=2, max=1000,
                            default=10,
                            description="Maximum number of images to be used"
                            )
bpy.types.Scene.cubester_frame_step = IntProperty(
                            name="Frame Step Size",
                            min=1, max=10,
                            default=4,
                            description="The number of frames each picture is used"
                            )
bpy.types.Scene.cubester_skip_pixels = IntProperty(
                            name="Skip # Pixels",
                            min=0, max=256,
                            default=64,
                            description="Skip this number of pixels before placing the next"
                            )
bpy.types.Scene.cubester_mesh_style = EnumProperty(
                            name="Mesh Type",
                            items=(("blocks", "Blocks", ""),
                                   ("plane", "Plane", "")),
                            description="Compose mesh of multiple blocks or of a single plane"
                            )
bpy.types.Scene.cubester_block_style = EnumProperty(
                            name="Block Style",
                            items=(("size", "Vary Size", ""),
                                   ("position", "Vary Position", "")),
                            description="Vary Z-size of block, or vary Z-position"
                            )
bpy.types.Scene.cubester_height_scale = FloatProperty(
                            name="Height Scale",
                            subtype="DISTANCE",
                            min=0.1, max=2,
                            default=0.2
                            )
bpy.types.Scene.cubester_invert = BoolProperty(
                            name="Invert Height?",
                            default=False
                            )
# general adjustments
bpy.types.Scene.cubester_size_per_hundred_pixels = FloatProperty(
                            name="Size Per 100 Blocks/Points",
                            subtype="DISTANCE",
                            min=0.001, max=5,
                            default=1
                            )
# material based stuff
bpy.types.Scene.cubester_materials = EnumProperty(
                            name="Material",
                            items=(("vertex", "Vertex Colors", ""),
                                   ("image", "Image", "")),
                            description="Color with vertex colors, or uv unwrap and use an image"
                            )
bpy.types.Scene.cubester_use_image_color = BoolProperty(
                            name="Use Original Image Colors'?",
                            default=True,
                            description="Use original image colors, or replace with other"
                            )
bpy.types.Scene.cubester_color_image = StringProperty(
                            default="", name=""
                            )
bpy.types.Scene.cubester_load_color_image = StringProperty(
                            default="",
                            name="Load Color Image",
                            subtype="FILE_PATH",
                            update=adjust_selected_color_image
                            )
bpy.types.Scene.cubester_vertex_colors = {}
# advanced
bpy.types.Scene.cubester_advanced = BoolProperty(
                            name="Advanced Options?"
                            )
bpy.types.Scene.cubester_random_weights = BoolProperty(
                            name="Random Weights?"
                            )
bpy.types.Scene.cubester_weight_r = FloatProperty(
                            name="Red",
                            subtype="FACTOR",
                            min=0.01, max=1.0,
                            default=0.25
                            )
bpy.types.Scene.cubester_weight_g = FloatProperty(
                            name="Green",
                            subtype="FACTOR",
                            min=0.01, max=1.0,
                            default=0.25
                            )
bpy.types.Scene.cubester_weight_b = FloatProperty(
                            name="Blue",
                            subtype="FACTOR",
                            min=0.01, max=1.0,
                            default=0.25
                            )
bpy.types.Scene.cubester_weight_a = FloatProperty(
                            name="Alpha",
                            subtype="FACTOR",
                            min=0.01, max=1.0,
                            default=0.25
                            )


class CubeSterPanel(Panel):
    bl_idname = "OBJECT_PT.cubester"
    bl_label = "CubeSter"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "Create"
    bl_options = {"DEFAULT_CLOSED"}
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout.box()
        scene = bpy.context.scene
        images_found = 0
        rows = 0
        columns = 0

        layout.prop(scene, "cubester_audio_image", icon="IMAGE_COL")
        layout.separator()

        if scene.cubester_audio_image == "image":
            box = layout.box()
            box.prop(scene, "cubester_load_type")
            box.label("Image To Convert:")
            box.prop_search(scene, "cubester_image", bpy.data, "images")
            box.prop(scene, "cubester_load_image")
            layout.separator()

            # find number of approriate images if sequence
            if scene.cubester_load_type == "multiple":
                box = layout.box()
                # display number of images found there
                images = find_sequence_images(self, context)
                images_found = len(images[0]) if len(images[0]) <= scene.cubester_max_images \
                    else scene.cubester_max_images

                if len(images[0]):
                    box.label(str(len(images[0])) + " Images Found", icon="PACKAGE")

                box.prop(scene, "cubester_max_images")
                box.prop(scene, "cubester_skip_images")
                box.prop(scene, "cubester_frame_step")

                layout.separator()

            box = layout.box()
            box.prop(scene, "cubester_skip_pixels")
            box.prop(scene, "cubester_size_per_hundred_pixels")
            box.prop(scene, "cubester_height_scale")
            box.prop(scene, "cubester_invert", icon="FILE_REFRESH")

            layout.separator()
            box = layout.box()
            box.prop(scene, "cubester_mesh_style", icon="MESH_GRID")

            if scene.cubester_mesh_style == "blocks":
                box.prop(scene, "cubester_block_style")

        # audio file
        else:
            layout.prop(scene, "cubester_audio_path")
            layout.separator()
            box = layout.box()

            box.prop(scene, "cubester_audio_min_freq")
            box.prop(scene, "cubester_audio_max_freq")
            box.separator()
            box.prop(scene, "cubester_audio_offset_type")

            if scene.cubester_audio_offset_type == "frame":
                box.prop(scene, "cubester_audio_frame_offset")
            box.separator()

            box.prop(scene, "cubester_audio_block_layout")
            box.prop(scene, "cubester_audio_width_blocks")
            box.prop(scene, "cubester_audio_length_blocks")

            rows = scene.cubester_audio_width_blocks
            columns = scene.cubester_audio_length_blocks

            box.prop(scene, "cubester_size_per_hundred_pixels")

        # materials
        layout.separator()
        box = layout.box()

        box.prop(scene, "cubester_materials", icon="MATERIAL")

        if scene.cubester_materials == "image":
            box.prop(scene, "cubester_load_type")

            # find number of approriate images if sequence
            if scene.cubester_load_type == "multiple":
                # display number of images found there
                images = find_sequence_images(self, context)
                images_found = len(images[0]) if len(images[0]) <= scene.cubester_max_images \
                    else scene.cubester_max_images

                if len(images[0]):
                    box.label(str(len(images[0])) + " Images Found", icon="PACKAGE")
                box.prop(scene, "cubester_max_images")
                box.prop(scene, "cubester_skip_images")
                box.prop(scene, "cubester_frame_step")

            box.separator()

            if scene.cubester_audio_image == "image":
                box.prop(scene, "cubester_use_image_color", icon="COLOR")

            if not scene.cubester_use_image_color or scene.cubester_audio_image == "audio":
                box.label("Image To Use For Colors:")
                box.prop_search(scene, "cubester_color_image", bpy.data, "images")
                box.prop(scene, "cubester_load_color_image")

            if scene.cubester_image in bpy.data.images:
                rows = int(bpy.data.images[scene.cubester_image].size[1] / (scene.cubester_skip_pixels + 1))
                columns = int(bpy.data.images[scene.cubester_image].size[0] / (scene.cubester_skip_pixels + 1))

        layout.separator()
        box = layout.box()

        if scene.cubester_mesh_style == "blocks":
            box.label("Approximate Cube Count: " + str(rows * columns))
            box.label("Expected # Verts/Faces: " + str(rows * columns * 8) + " / " + str(rows * columns * 6))
        else:
            box.label("Approximate Point Count: " + str(rows * columns))
            box.label("Expected # Verts/Faces: " + str(rows * columns) + " / " + str(rows * (columns - 1)))

        # blocks and plane generation time values
        if scene.cubester_mesh_style == "blocks":
            slope = 0.0000876958
            intercept = 0.02501
            block_infl, frame_infl, intercept2 = 0.0025934, 0.38507, -0.5840189

        else:
            slope = 0.000017753
            intercept = 0.04201
            block_infl, frame_infl, intercept2 = 0.000619, 0.344636, -0.272759

        # if creating image based mesh
        points = rows * columns
        if scene.cubester_audio_image == "image":
            if scene.cubester_load_type == "single":
                time = rows * columns * slope + intercept  # approximate time count for mesh
            else:
                time = (points * slope) + intercept + (points * block_infl) + \
                       (images_found / scene.cubester_skip_images * frame_infl) + intercept2

                box.label("Images To Be Used: " + str(int(images_found / scene.cubester_skip_images)))

        # audio based mesh
        else:
            box.label("Audio Track Length: " + scene.cubester_audio_file_length + " frames")

            block_infl, frame_infl, intercept = 0.0948, 0.0687566, -25.85985
            time = (points * block_infl) + (int(scene.cubester_audio_file_length) * frame_infl) + intercept

        time_mod = "s"
        if time > 60:  # convert to minutes if needed
            time /= 60
            time_mod = "min"
        time = round(time, 3)

        box.label("Expected Time: " + str(time) + " " + time_mod)

        # advanced
        if scene.cubester_audio_image == "image":
            layout.separator()
            box = layout.box()
            box.prop(scene, "cubester_advanced", icon="TRIA_DOWN")
            if bpy.context.scene.cubester_advanced:
                box.prop(scene, "cubester_random_weights", icon="RNDCURVE")
                box.separator()

                if not bpy.context.scene.cubester_random_weights:
                    box.label("RGBA Channel Weights", icon="COLOR")
                    box.prop(scene, "cubester_weight_r")
                    box.prop(scene, "cubester_weight_g")
                    box.prop(scene, "cubester_weight_b")
                    box.prop(scene, "cubester_weight_a")

        # generate mesh
        layout.separator()
        layout.operator("mesh.cubester", icon="OBJECT_DATA")


class CubeSter(Operator):
    bl_idname = "mesh.cubester"
    bl_label = "Generate Mesh"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        verts, faces = [], []

        start = timeit.default_timer()
        scene = bpy.context.scene

        if scene.cubester_audio_image == "image":
            create_mesh_from_image(self, scene, verts, faces)
            frames = find_sequence_images(self, context)
            created = len(frames[0])
        else:
            create_mesh_from_audio(self, scene, verts, faces)
            created = int(scene.cubester_audio_file_length)

        stop = timeit.default_timer()

        if scene.cubester_mesh_style == "blocks" or scene.cubester_audio_image == "audio":
            self.report({"INFO"},
                        "CubeSter: {} blocks and {} frame(s) "
                        "in {}s".format(str(int(len(verts) / 8)),
                                        str(created),
                                        str(round(stop - start, 4)))
                        )
        else:
            self.report({"INFO"},
                        "CubeSter: {} points and {} frame(s) "
                        "in {}s" .format(str(len(verts)),
                                         str(created),
                                         str(round(stop - start, 4)))
                        )

        return {"FINISHED"}


def register():
    bpy.utils.register_module(__name__)
    bpy.app.handlers.frame_change_pre.append(material_frame_handler)


def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.app.handlers.frame_change_pre.remove(material_frame_handler)


if __name__ == "__main__":
    register()
