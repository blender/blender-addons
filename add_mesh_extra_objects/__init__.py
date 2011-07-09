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

bl_info = {
    "name": "Extra Objects",
    "author": "Pontiac, Fourmadmen, varkenvarken, tuga3d, meta-androcto",
    "version": (0, 1),
    "blender": (2, 5, 7),
    "api": 35853,
    "location": "View3D > Add > Mesh > Extra Objects",
    "description": "Adds More Object Types.",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"\
        "Scripts/Add_Mesh/Add_Extra",
    "tracker_url": "http://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=22457",
    "category": "Add Mesh"}


if "bpy" in locals():
    import imp
    imp.reload(add_mesh_extra_objects)
    imp.reload(add_mesh_twisted_torus)
    imp.reload(add_mesh_gemstones)
    imp.reload(add_mesh_gears)
    imp.reload(add_mesh_3d_function_surface)
else:
    from . import add_mesh_extra_objects
    from . import add_mesh_twisted_torus
    from . import add_mesh_gemstones
    from . import add_mesh_gears
    from . import add_mesh_3d_function_surface

import bpy


class INFO_MT_mesh_extras_add(bpy.types.Menu):
    # Define the "Extras" menu
    bl_idname = "INFO_MT_mesh_extra_objects_add"
    bl_label = "Extra Objects"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.menu("INFO_MT_mesh_gemstones_add", text="Gemstones")
        layout.menu("INFO_MT_mesh_gears_add", text="Gears")
        layout.menu("INFO_MT_mesh_math_add", text="Math Function")
        layout.operator("mesh.primitive_twisted_torus_add",
            text="Twisted Torus")
        layout.operator("mesh.primitive_sqorus_add",
            text="Sqorus")
        layout.operator("mesh.primitive_wedge_add")
        layout.operator("mesh.primitive_star_add",
            text="Star")
        layout.operator("mesh.primitive_trapezohedron_add",
            text="Trapezohedron")

class INFO_MT_mesh_gemstones_add(bpy.types.Menu):
    # Define the "Gemstones" menu
    bl_idname = "INFO_MT_mesh_gemstones_add"
    bl_label = "Gemstones"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("mesh.primitive_diamond_add",
            text="Diamond")
        layout.operator("mesh.primitive_gem_add",
            text="Gem")

			
class INFO_MT_mesh_gears_add(bpy.types.Menu):
    # Define the "Gears" menu
    bl_idname = "INFO_MT_mesh_gears_add"
    bl_label = "Gears"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("mesh.primitive_gear",
            text="Gear")
        layout.operator("mesh.primitive_worm_gear",
            text="Worm")

class INFO_MT_mesh_math_add(bpy.types.Menu):
    # Define the "Math Function" menu
    bl_idname = "INFO_MT_mesh_math_add"
    bl_label = "Math Functions"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("mesh.primitive_z_function_surface",
            text="Z Math Surface")
        layout.operator("mesh.primitive_xyz_function_surface",
            text="XYZ Math Surface")

# Register all operators and panels

# Define "Extras" menu
def menu_func(self, context):
    self.layout.menu("INFO_MT_mesh_extra_objects_add", icon="PLUGIN")


def register():
    bpy.utils.register_module(__name__)

    # Add "Extras" menu to the "Add Mesh" menu
    bpy.types.INFO_MT_mesh_add.append(menu_func)


def unregister():
    bpy.utils.unregister_module(__name__)

    # Remove "Extras" menu from the "Add Mesh" menu.
    bpy.types.INFO_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
    register()
