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

# Contributed to by:
# meta-androcto, Bill Currie, Jorge Hernandez - Melenedez  Jacob Morris, Oscurart  #
# Rebellion, Antonis Karvelas, Eleanor Howick, lijenstina, Daniel Schalla, Domlysz #
# Unnikrishnan(kodemax), Florian Meyer, Omar ahmed, Brian Hinton (Nichod), liero   #
# Dannyboy, Mano-Wii, Kursad Karatas, teldredge

bl_info = {
    "name": "Add Advanced Objects",
    "author": "Meta Androcto,",
    "version": (0, 1, 1),
    "blender": (2, 78, 0),
    "location": "View3D > Add ",
    "description": "Add Object & Camera extras",
    "warning": "",
    "wiki_url": "https://wiki.blender.org/index.php/Extensions:2.6"
                "/Py/Scripts",
    "tracker_url": "",
    "category": "Object"}

if "bpy" in locals():
    import importlib

    importlib.reload(add_light_template)
    importlib.reload(scene_objects_bi)
    importlib.reload(scene_objects_cycles)
    importlib.reload(scene_texture_render)
    importlib.reload(trilighting)
    importlib.reload(pixelate_3d)
    importlib.reload(object_add_chain)
    importlib.reload(drop_to_ground)
    importlib.reload(circle_array)
    importlib.reload(unfold_transition)
    importlib.reload(copy2)
    importlib.reload(make_struts)
    importlib.reload(random_box_structure)
    importlib.reload(cubester)
    importlib.reload(rope_alpha)
    importlib.reload(add_mesh_aggregate)
    importlib.reload(object_mangle_tools)
    importlib.reload(arrange_on_curve)
    importlib.reload(object_laplace_lightning)
    importlib.reload(mesh_easylattice)
    importlib.reload(DelaunayVoronoi)
    importlib.reload(delaunayVoronoiBlender)
    importlib.reload(oscurart_constellation)
    importlib.reload(oscurart_chain_maker)

else:
    from . import (
        add_light_template,
        scene_objects_bi,
        scene_objects_cycles,
        scene_texture_render,
        trilighting,
        pixelate_3d,
        object_add_chain,
        oscurart_chain_maker,
        drop_to_ground,
        circle_array,
        unfold_transition,
        copy2,
        make_struts,
        random_box_structure,
        cubester,
        rope_alpha,
        add_mesh_aggregate,
        object_mangle_tools,
        arrange_on_curve,
        object_laplace_lightning,
        mesh_easylattice
        )
    from .delaunay_voronoi import (
        DelaunayVoronoi,
        delaunayVoronoiBlender,
        oscurart_constellation
        )

import bpy
from bpy.types import (
        Menu,
        AddonPreferences,
        )


class INFO_MT_scene_elements_add(Menu):
    # Define the "scenes" menu
    bl_idname = "INFO_MT_scene_elements"
    bl_label = "Test scenes"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("bi.add_scene",
                        text="Scene_Objects_BI")
        layout.operator("objects_cycles.add_scene",
                        text="Scene_Objects_Cycles")
        layout.operator("objects_texture.add_scene",
                        text="Scene_Textures_Cycles")


class INFO_MT_mesh_lamps_add(Menu):
    # Define the "lights" menu
    bl_idname = "INFO_MT_scene_lamps"
    bl_label = "Lighting Sets"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("object.add_light_template",
                        text="Add Light Template")
        layout.operator("object.trilighting",
                        text="Add Tri Lighting")


class INFO_MT_mesh_chain_add(Menu):
    # Define the "Chains" menu
    bl_idname = "INFO_MT_mesh_chain"
    bl_label = "Chains"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("mesh.primitive_chain_add", icon="LINKED")
        layout.operator("mesh.primitive_oscurart_chain_add", icon="LINKED")


class INFO_MT_array_mods_add(Menu):
    # Define the "array" menu
    bl_idname = "INFO_MT_array_mods"
    bl_label = "Array Mods"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        self.layout.menu("INFO_MT_mesh_chain", icon="LINKED")
        layout.operator("objects.circle_array_operator",
                        text="Circle Array", icon='MOD_ARRAY')
        layout.operator("object.agregate_mesh",
                        text="Aggregate Mesh", icon='MOD_ARRAY')
        obj = context.object
        if obj.type in ['MESH',]:  
            layout.operator("mesh.copy2",
                        text="Copy To Vert/Edge", icon='MOD_ARRAY')



class INFO_MT_quick_blocks_add(Menu):
    # Define the "Blocks" menu
    bl_idname = "INFO_MT_quick_tools"
    bl_label = "Block Tools"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator('object.pixelate', icon='MESH_GRID')
        obj = context.object
        if obj.type in ['MESH',]:  
            layout.operator("mesh.generate_struts",
                        text="Struts", icon='GRID')
            layout.operator("object.easy_lattice",
                        text="Easy Lattice", icon='MOD_LATTICE')
            layout.operator("object.make_structure",
                        text="Random Boxes", icon='SEQ_SEQUENCER')


class INFO_MT_Physics_tools_add(Menu):
    # Define the "mesh objects" menu
    bl_idname = "INFO_MT_physics_tools"
    bl_label = "Physics Tools"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("object.drop_on_active",
                        text="Drop To Ground")
        layout.operator("ball.rope",
                        text="Wrecking Ball", icon='PHYSICS')
        layout.operator("clot.rope",
                        text="Cloth Rope", icon='PHYSICS')


# Define "Extras" menu
def menu(self, context):
    layout = self.layout
    layout.operator_context = 'INVOKE_REGION_WIN'
    self.layout.separator()
    self.layout.menu("INFO_MT_scene_elements", icon="SCENE_DATA")
    self.layout.menu("INFO_MT_scene_lamps", icon="LAMP_SPOT")
    self.layout.separator()
    self.layout.menu("INFO_MT_array_mods", icon="MOD_ARRAY")
    self.layout.menu("INFO_MT_quick_tools", icon="MOD_BUILD")
    self.layout.menu("INFO_MT_physics_tools", icon="PHYSICS")


# Addons Preferences
class AddonPreferences(AddonPreferences):
    bl_idname = __name__

    def draw(self, context):
        layout = self.layout
        layout.label(text="----Add Menu Advanced----")
        layout.label(text="Quick Tools:")
        layout.label(text="Drop, Pixelate & Wrecking Ball")
        layout.label(text="Array Mods:")
        layout.label(text="Circle Array, Chains, Vert to Edge, Aggregate")


def register():
    object_mangle_tools.register()
    arrange_on_curve.register()
    bpy.utils.register_module(__name__)
    # Add "Extras" menu to the "Add" menu
    bpy.types.INFO_MT_add.append(menu)
    try:
        bpy.types.VIEW3D_MT_AddMenu.append(menu)
    except:
        pass


def unregister():
    object_mangle_tools.unregister()
    arrange_on_curve.unregister()
    # Remove "Extras" menu from the "Add" menu.
    bpy.types.INFO_MT_add.remove(menu)
    try:
        bpy.types.VIEW3D_MT_AddMenu.remove(menu)
    except:
        pass

    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
