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

# <pep8-80 compliant>

import bpy

# maybe we could also just use the svg exporter, import it again
# and render it. Unfortunately the svg importer does not work atm.
def export(filepath, face_data, colors, width, height, opacity):
    aspect = width / height

    # curves for lines
    lines = curve_from_uvs(face_data, aspect, 1 / min(width, height))
    lines_object = bpy.data.objects.new("temp_lines_object", lines)
    black_material = make_colored_material((0, 0, 0))
    lines.materials.append(black_material)

    # background mesh
    background_mesh = background_mesh_from_uvs(face_data, colors, aspect, opacity)
    background_object = bpy.data.objects.new("temp_background_object", background_mesh)
    background_object.location = (0, 0, -1)

    # camera
    camera = bpy.data.cameras.new("temp_camera")
    camera_object = bpy.data.objects.new("temp_camera_object", camera)
    camera.type = "ORTHO"
    camera.ortho_scale = max(1, aspect)
    camera_object.location = (aspect / 2, 0.5, 1)
    camera_object.rotation_euler = (0, 0, 0)

    # scene
    scene = bpy.data.scenes.new("temp_scene")
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.alpha_mode = "TRANSPARENT"
    scene.render.filepath = filepath

    # Link everything to the scene
    scene.collection.objects.link(lines_object)
    scene.collection.objects.link(camera_object)
    scene.collection.objects.link(background_object)
    scene.camera = camera_object

    # Render
    override = {"scene" : scene}
    bpy.ops.render.render(override, write_still=True)

    # Cleanup
    bpy.data.objects.remove(lines_object)
    bpy.data.objects.remove(camera_object)
    bpy.data.objects.remove(background_object)

    for material in background_mesh.materials:
        bpy.data.materials.remove(material)
    bpy.data.meshes.remove(background_mesh)

    bpy.data.cameras.remove(camera)
    bpy.data.curves.remove(lines)
    bpy.data.materials.remove(black_material)
    bpy.data.scenes.remove(scene)

def curve_from_uvs(face_data, aspect, thickness):
    lines = bpy.data.curves.new("temp_curve", "CURVE")
    lines.fill_mode = "BOTH"
    lines.bevel_depth = thickness
    lines.offset = -thickness / 2
    lines.dimensions = "3D"

    for uvs, _ in face_data:
        for i in range(len(uvs)):
            start = uvs[i]
            end = uvs[(i+1) % len(uvs)]

            spline = lines.splines.new("POLY")
            # one point is already there
            spline.points.add(1)
            points = spline.points

            points[0].co.x = start[0] * aspect
            points[0].co.y = start[1]

            points[1].co.x = end[0] * aspect
            points[1].co.y = end[1]

    return lines

def background_mesh_from_uvs(face_data, colors, aspect, opacity):
    mesh = bpy.data.meshes.new("temp_background")

    vertices = []
    polygons = []
    for uvs, _ in face_data:
        polygon = []
        for uv in uvs:
            polygon.append(len(vertices))
            vertices.append((uv[0] * aspect, uv[1], 0))
        polygons.append(tuple(polygon))

    mesh.from_pydata(vertices, [], polygons)

    materials, material_index_by_color = make_polygon_background_materials(colors, opacity)
    for material in materials:
        mesh.materials.append(material)

    for generated_polygon, (_, color) in zip(mesh.polygons, face_data):
        generated_polygon.material_index = material_index_by_color[color]

    mesh.update()
    mesh.validate()

    return mesh

def make_polygon_background_materials(colors, opacity=1):
    materials = []
    material_index_by_color = {}
    for i, color in enumerate(colors):
        material = make_colored_material(color, opacity)
        materials.append(material)
        material_index_by_color[color] = i
    return materials, material_index_by_color

def make_colored_material(color, opacity=1):
    material = bpy.data.materials.new("temp_material")
    material.use_nodes = True
    material.blend_method = "BLEND"
    tree = material.node_tree
    tree.nodes.clear()

    output_node = tree.nodes.new("ShaderNodeOutputMaterial")
    emission_node = tree.nodes.new("ShaderNodeEmission")

    emission_node.inputs["Color"].default_value = [color[0], color[1], color[2], opacity]
    tree.links.new(emission_node.outputs["Emission"], output_node.inputs["Surface"])

    return material
