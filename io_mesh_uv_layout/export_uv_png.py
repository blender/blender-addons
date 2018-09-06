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


class Export_UV_PNG:
    def begin(self, fw, image_size, opacity):
        self.filepath = fw.__self__.name
        fw.__self__.close()

        self.scene = bpy.data.scenes.new("uv_temp")

        image_width = image_size[0]
        image_height = image_size[1]

        self.scene.render.resolution_x = image_width
        self.scene.render.resolution_y = image_height
        self.scene.render.resolution_percentage = 100

        self.scene.render.alpha_mode = 'TRANSPARENT'

        if image_width > image_height:
            self.scene.render.pixel_aspect_y = image_width / image_height
        elif image_width < image_height:
            self.scene.render.pixel_aspect_x = image_height / image_width

        self.base_material = bpy.data.materials.new("uv_temp_base")
        self.base_material.use_nodes = True
        self.base_material.node_tree.nodes.clear()
        output_node = self.base_material.node_tree.nodes.new(type="ShaderNodeOutputMaterial")
        emission_node = self.base_material.node_tree.nodes.new(type="ShaderNodeEmission")
        emission_node.inputs["Color"].default_value = (1.0, 1.0, 1.0, opacity)
        self.base_material.node_tree.links.new(
                                    output_node.inputs["Surface"],
                                    emission_node.outputs["Emission"])

        self.material_wire = self.base_material.copy()
        self.material_wire.name = "Wire"
        self.material_wire.node_tree.nodes['Emission'].inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)

        self.base_material.blend_method = "BLEND"

        self.material_solids_list = []  # list of lists
        self.material_solids_list.append([self.base_material,
                                          self.material_wire])

        self.mesh_list = []
        self.obj_list = []

    def build(self, mesh_source, face_iter_func):
        material_solids = [self.base_material.copy() for i in range(max(1, len(mesh_source.materials)))]

        self.material_solids_list.append(material_solids)

        mesh = bpy.data.meshes.new("uv_temp")
        self.mesh_list.append(mesh)

        for mat_solid in material_solids:
            mesh.materials.append(mat_solid)

        # setup materials
        for i, mat_solid in enumerate(material_solids):
            if mesh_source.materials and mesh_source.materials[i]:
                mat_solid.node_tree.nodes['Emission'].\
                        inputs["Color"].default_value[0:3]\
                        = mesh_source.materials[i].diffuse_color

        # Add materials for wireframe modifier.
        for mat_solid in material_solids:
            mesh.materials.append(self.material_wire)

        polys_source = mesh_source.polygons

        # get unique UV's in case there are many overlapping
        # which slow down filling.
        face_hash = {(uvs, polys_source[i].material_index)
                     for i, uvs in face_iter_func()}

        # now set the faces coords and locations
        # build mesh data
        mesh_new_vertices = []
        mesh_new_materials = []
        mesh_new_polys_startloop = []
        mesh_new_polys_totloop = []
        mesh_new_loops_vertices = []

        current_vert = 0

        for uvs, mat_idx in face_hash:
            num_verts = len(uvs)
            # dummy = (0.0,) * num_verts
            for uv in uvs:
                mesh_new_vertices += (uv[0], uv[1], 0.0)
            mesh_new_polys_startloop.append(current_vert)
            mesh_new_polys_totloop.append(num_verts)
            mesh_new_loops_vertices += range(current_vert,
                                             current_vert + num_verts)
            mesh_new_materials.append(mat_idx)
            current_vert += num_verts

        mesh.vertices.add(current_vert)
        mesh.loops.add(current_vert)
        mesh.polygons.add(len(mesh_new_polys_startloop))

        mesh.vertices.foreach_set("co", mesh_new_vertices)
        mesh.loops.foreach_set("vertex_index", mesh_new_loops_vertices)
        mesh.polygons.foreach_set("loop_start", mesh_new_polys_startloop)
        mesh.polygons.foreach_set("loop_total", mesh_new_polys_totloop)
        mesh.polygons.foreach_set("material_index", mesh_new_materials)

        mesh.update(calc_edges=True)

        obj_solid = bpy.data.objects.new("uv_temp_solid", mesh)

        wire_mod = obj_solid.modifiers.new("wire_mod", 'WIREFRAME')
        wire_mod.use_replace = False
        wire_mod.use_relative_offset = True

        wire_mod.material_offset = len(material_solids)

        self.obj_list.append(obj_solid)
        self.scene.collection.objects.link(obj_solid)

    def end(self):
        # setup the camera
        cam = bpy.data.cameras.new("uv_temp")
        cam.type = 'ORTHO'
        cam.ortho_scale = 1.0
        obj_cam = bpy.data.objects.new("uv_temp_cam", cam)
        obj_cam.location = 0.5, 0.5, 1.0
        self.scene.collection.objects.link(obj_cam)
        self.obj_list.append(obj_cam)
        self.scene.camera = obj_cam

        # scene render settings
        self.scene.render.alpha_mode = 'TRANSPARENT'
        self.scene.render.image_settings.color_mode = 'RGBA'

        self.scene.frame_start = 1
        self.scene.frame_end = 1

        self.scene.render.image_settings.file_format = 'PNG'
        self.scene.render.filepath = self.filepath

        self.scene.update()

        data_context = {"blend_data": bpy.context.blend_data,
                        "scene": self.scene}
        bpy.ops.render.render(data_context, write_still=True)

        # cleanup
        bpy.data.scenes.remove(self.scene, do_unlink=True)

        for obj in self.obj_list:
            bpy.data.objects.remove(obj, do_unlink=True)

        bpy.data.cameras.remove(cam, do_unlink=True)

        for mesh in self.mesh_list:
            bpy.data.meshes.remove(mesh, do_unlink=True)

        for material_solids in self.material_solids_list:
            for mat_solid in material_solids:
                bpy.data.materials.remove(mat_solid, do_unlink=True)
