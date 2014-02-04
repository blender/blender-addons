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
# Contributed to by
# Pontiac, Fourmadmen, varkenvarken, tuga3d, meta-androcto, metalliandy, dreampainter & cotejrp1#

bl_info = {
    "name": "Extra Objects",
    "author": "Multiple Authors",
    "version": (0, 3),
    "blender": (2, 63, 0),
    "location": "View3D > Add > Mesh > Extra Objects",
    "description": "Add extra object types",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
        "Scripts/Add_Mesh/Add_Extra",
    "tracker_url": "https://developer.blender.org/T22457",
    "category": "Add Mesh"}


if "bpy" in locals():
    import imp
    imp.reload(add_mesh_extra_objects)
    imp.reload(add_mesh_twisted_torus)
    imp.reload(add_mesh_gemstones)
    imp.reload(add_mesh_gears)
    imp.reload(add_mesh_3d_function_surface)
    imp.reload(add_mesh_polysphere)
    imp.reload(add_mesh_supertoroid)
    imp.reload(add_mesh_pyramid)
    imp.reload(add_mesh_torusknot)
    imp.reload(add_mesh_honeycomb)
    imp.reload(add_mesh_teapot)
else:
    from . import add_mesh_extra_objects
    from . import add_mesh_twisted_torus
    from . import add_mesh_gemstones
    from . import add_mesh_gears
    from . import add_mesh_3d_function_surface
    from . import add_mesh_polysphere
    from . import add_mesh_supertoroid
    from . import add_mesh_pyramid
    from . import add_mesh_torusknot
    from . import add_mesh_honeycomb
    from . import add_mesh_teapot
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
        layout.menu("INFO_MT_mesh_basic_add", text="Basic Objects")
        layout.menu("INFO_MT_mesh_torus_add", text="Torus Objects")
        layout.menu("INFO_MT_mesh_misc_add", text="Misc Objects")

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

class INFO_MT_mesh_basic_add(bpy.types.Menu):
    # Define the "Simple Objects" menu
    bl_idname = "INFO_MT_mesh_basic_add"
    bl_label = "Simple Objects"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("mesh.primitive_sqorus_add",
            text="Sqorus")
        layout.operator("mesh.primitive_wedge_add")
        layout.operator("mesh.primitive_star_add",
            text="Star")
        layout.operator("mesh.primitive_trapezohedron_add",
            text="Trapezohedron")
        layout.operator("mesh.primitive_polysphere_add",
            text="Polysphere")

class INFO_MT_mesh_torus_add(bpy.types.Menu):
    # Define the "Simple Objects" menu
    bl_idname = "INFO_MT_mesh_torus_add"
    bl_label = "Torus Objects"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("mesh.primitive_twisted_torus_add",
            text="Twisted Torus")
        layout.operator("mesh.primitive_supertoroid_add",
            text="Supertoroid")
        layout.operator("mesh.primitive_torusknot_add",
            text="Torus Knot")

class INFO_MT_mesh_misc_add(bpy.types.Menu):
    # Define the "Simple Objects" menu
    bl_idname = "INFO_MT_mesh_misc_add"
    bl_label = "Misc Objects"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("mesh.primitive_steppyramid_add",
            text="Step Pyramid")
        layout.operator("mesh.honeycomb_add",
            text="Honeycomb")
        layout.operator("mesh.primitive_teapot_add",
            text="Teapot+")
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
