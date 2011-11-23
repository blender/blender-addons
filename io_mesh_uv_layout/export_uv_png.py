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

# <pep8 compliant>

import bpy


def write(fw, mesh_source, image_width, image_height, opacity, face_iter_func):
    filepath = fw.__self__.name
    fw.__self__.close()

    material_solids = [bpy.data.materials.new("uv_temp_solid") for i in range(max(1, len(mesh_source.materials)))]
    material_wire = bpy.data.materials.new("uv_temp_wire")

    scene = bpy.data.scenes.new("uv_temp")
    mesh = bpy.data.meshes.new("uv_temp")
    for mat_solid in material_solids:
        mesh.materials.append(mat_solid)

    tot_verts = 0
    for f in mesh_source.faces:
        tot_verts += len(f.vertices)

    faces_source = mesh_source.faces

    # get unique UV's in case there are many overlapping which slow down filling.
    face_hash_3 = set()
    face_hash_4 = set()
    for i, uv in face_iter_func():
        material_index = faces_source[i].material_index
        if len(uv) == 3:
            face_hash_3.add((uv[0][0], uv[0][1], uv[1][0], uv[1][1], uv[2][0], uv[2][1], material_index))
        else:
            face_hash_4.add((uv[0][0], uv[0][1], uv[1][0], uv[1][1], uv[2][0], uv[2][1], uv[3][0], uv[3][1], material_index))

    # now set the faces coords and locations
    # build mesh data
    mesh_new_vertices = []
    mesh_new_materials = []
    mesh_new_face_vertices = []

    current_vert = 0

    for face_data in face_hash_3:
        mesh_new_vertices.extend([face_data[0], face_data[1], 0.0, face_data[2], face_data[3], 0.0, face_data[4], face_data[5], 0.0])
        mesh_new_face_vertices.extend([current_vert, current_vert + 1, current_vert + 2, 0])
        mesh_new_materials.append(face_data[6])
        current_vert += 3
    for face_data in face_hash_4:
        mesh_new_vertices.extend([face_data[0], face_data[1], 0.0, face_data[2], face_data[3], 0.0, face_data[4], face_data[5], 0.0, face_data[6], face_data[7], 0.0])
        mesh_new_face_vertices.extend([current_vert, current_vert + 1, current_vert + 2, current_vert + 3])
        mesh_new_materials.append(face_data[8])
        current_vert += 4

    mesh.vertices.add(len(mesh_new_vertices) // 3)
    mesh.faces.add(len(mesh_new_face_vertices) // 4)

    mesh.vertices.foreach_set("co", mesh_new_vertices)
    mesh.faces.foreach_set("vertices_raw", mesh_new_face_vertices)
    mesh.faces.foreach_set("material_index", mesh_new_materials)

    mesh.update(calc_edges=True)

    obj_solid = bpy.data.objects.new("uv_temp_solid", mesh)
    obj_wire = bpy.data.objects.new("uv_temp_wire", mesh)
    base_solid = scene.objects.link(obj_solid)
    base_wire = scene.objects.link(obj_wire)
    base_solid.layers[0] = True
    base_wire.layers[0] = True

    # place behind the wire
    obj_solid.location = 0, 0, -1

    obj_wire.material_slots[0].link = 'OBJECT'
    obj_wire.material_slots[0].material = material_wire

    # setup the camera
    cam = bpy.data.cameras.new("uv_temp")
    cam.type = 'ORTHO'
    cam.ortho_scale = 1.0
    obj_cam = bpy.data.objects.new("uv_temp_cam", cam)
    obj_cam.location = 0.5, 0.5, 1.0
    scene.objects.link(obj_cam)
    scene.camera = obj_cam

    # setup materials
    for i, mat_solid in enumerate(material_solids):
        if mesh_source.materials and mesh_source.materials[i]:
            mat_solid.diffuse_color = mesh_source.materials[i].diffuse_color

        mat_solid.use_shadeless = True
        mat_solid.use_transparency = True
        mat_solid.alpha = opacity

    material_wire.type = 'WIRE'
    material_wire.use_shadeless = True
    material_wire.diffuse_color = 0, 0, 0

    # scene render settings
    scene.render.use_raytrace = False
    scene.render.alpha_mode = 'STRAIGHT'
    scene.render.image_settings.color_mode = 'RGBA'

    scene.render.resolution_x = image_width
    scene.render.resolution_y = image_height
    scene.render.resolution_percentage = 100

    if image_width > image_height:
        scene.render.pixel_aspect_y = image_width / image_height
    elif image_width < image_height:
        scene.render.pixel_aspect_x = image_height / image_width

    scene.frame_start = 1
    scene.frame_end = 1

    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = filepath

    data_context = {"blend_data": bpy.context.blend_data, "scene": scene}
    bpy.ops.render.render(data_context, write_still=True)

    # cleanup
    bpy.data.scenes.remove(scene)
    bpy.data.objects.remove(obj_cam)
    bpy.data.objects.remove(obj_solid)
    bpy.data.objects.remove(obj_wire)

    bpy.data.cameras.remove(cam)
    bpy.data.meshes.remove(mesh)

    bpy.data.materials.remove(material_wire)
    for mat_solid in material_solids:
        bpy.data.materials.remove(mat_solid)
