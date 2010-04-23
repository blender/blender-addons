#3d_cursor_menu.py (c) 2010 Jonathan Smith (JayDez)
#Original Script by: Mariano Hidalgo (uselessdreamer)
#contributed to by: Crouch, sim88, sam, meta-androcto
#
#Tested with r27779
#
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

bl_addon_info = {
    'name': '3D View: Dynamic Menu',
    'author': 'JayDez, sim88, meta-androcto',
    'version': '1.3',
    'blender': (2, 5, 3),
    'location': 'View3D > Mouse > Menu ',
    'description': 'Dynamic Menu Object/Edit mode in the 3D View',
    'url': 'http://wiki.blender.org/index.php/Extensions:2.5/Py/' \
        'Scripts/3D_interaction/Dynamic_Menu',
    'category': '3D View'}
"Add Dynamic Menu (Right click in View3D)"

"""
Name: '3D Dynamic Menu'
Blender: 253
"""

__author__ = ["JayDez, sim88, meta-androcto, sam"]
__version__ = '1.3'
__url__ = [""]
__bpydoc__ = """
Dynamic Menu
This adds a the Dynamic Menu in the 3DView.

Usage:
* Right click in an empty space in the 3D View(that means nothing
selectable is there). If your select mouse is set to left then left
click in the 3D View.

* Choose your function from the menu.

Version history:
v1.3 - (JayDez) - Changed toggle editmode to an if statement, so that
    if you are in editmode it will show change to object mode but
    otherwise it shows change to edit mode. Also added seperate icons
    for change to edit mode and to object mode.
v1.2 - (JayDez) - Editing docs, changing 3D cursor to dynamic menu,
    reorganizing menu.
v1.1 - (meta-androcto) - added editmode menu
v1.0 - (meta-androcto) - initial final revision (commited to contrib)
v0.1 through 0.9 - various tests/contributions by various people and scripts
    Devs: JayDez, Crouch, sim88, meta-androcto, Sam
    Scripts: 3D Cursor Menu, Original Dynamic Menu
"""
import bpy
from bpy import *


# Classes for VIEW3D_MT_curs()
class pivot_cursor(bpy.types.Operator):
    bl_idname = "view3d.pivot_cursor"
    bl_label = "Cursor as Pivot Point"

    def poll(self, context):
        return bpy.context.space_data.pivot_point != 'CURSOR'

    def execute(self, context):
        bpy.context.space_data.pivot_point = 'CURSOR'
        return {'FINISHED'}


class revert_pivot(bpy.types.Operator):
    bl_idname = "view3d.revert_pivot"
    bl_label = "Reverts Pivot Point to median"

    def poll(self, context):
        return bpy.context.space_data.pivot_point != 'MEDIAN_POINT'

    def execute(self, context):
        bpy.context.space_data.pivot_point = 'MEDIAN_POINT'
        # @todo Change this to 'BOUDNING_BOX_CENTER' if needed...
        return{'FINISHED'}


# Dynamic Menu
class VIEW3D_MT_Dynamic_Menu(bpy.types.Menu):
    bl_label = "Dynamic Menu"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        obj_act = context.active_object

        sel_objs = 0
        if context.selected_objects:
            sel_objs = len(context.selected_objects)

        # Search Block
        layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')

        layout.separator()

        if context.mode == 'OBJECT':
            # Add block
            layout.menu("INFO_MT_mesh_add", text="Add Mesh",
                icon='OUTLINER_OB_MESH')
            layout.operator_menu_enum("object.lamp_add", "type",
                icon="OUTLINER_OB_LAMP")
            layout.operator_menu_enum("object.curve_add", "type",
                icon='OUTLINER_OB_CURVE')
            layout.menu("INFO_MT_armature_add", text="Add Armature",
                icon='OUTLINER_OB_ARMATURE')
            layout.operator("object.add", text="Add Empty",
                icon='OUTLINER_OB_EMPTY')

            if sel_objs:
                layout.separator()

                # Transform block
                layout.menu('VIEW3D_MT_transform', icon='MAN_TRANS')

            layout.separator()

            # Other things
            layout.menu("VIEW3D_MT_object_group", icon='GROUP')
            layout.operator("object.modifier_add", icon='MODIFIER')

            # Display only when objects are actually selected.
            if sel_objs:
                layout.separator()

                # Parent block (add delete parent)
                layout.operator("object.parent_set", icon='ROTACTIVE')

                layout.separator()

                if sel_objs == 1:
                    # Delete block
                    layout.operator("object.delete", text="Delete Object",
                        icon='CANCEL')
                elif sel_objs > 1:
                    # Delete block
                    layout.operator("object.delete", text="Delete Objects",
                        icon='CANCEL')

        elif context.mode == 'EDIT_MESH':
            # Add block
            bl_label = "Create"

            layout.menu("INFO_MT_mesh_add", text="Add Mesh",
                icon='OUTLINER_OB_MESH')

            layout.separator()

            # Transform block
            layout.menu('VIEW3D_MT_transform', icon='MAN_TRANS')

            layout.separator()

            # Select block
            layout.menu("VIEW3D_MT_edit_mesh_selection_mode", icon='EDIT')
            layout.menu("VIEW3D_MT_selectS", icon='OBJECT_DATAMODE')

            # Edit block
            layout.menu("VIEW3D_MT_edit_mesh_vertices", icon='VERTEXSEL')
            layout.menu("VIEW3D_MT_edit_mesh_edges", icon='EDGESEL')
            layout.menu("VIEW3D_MT_edit_mesh_faces", icon='FACESEL')

            layout.separator()

            # Tools block
            layout.operator("mesh.loopcut_slide", text="Loopcut",
                icon='EDIT_VEC')
            layout.menu("VIEW3D_MT_edit_mesh_specials", icon='MODIFIER')
            layout.menu("VIEW3D_MT_uv_map", icon='MOD_UVPROJECT')
            layout.separator()
            layout.operator("mesh.delete", icon='CANCEL')

        # History/Cursor Block
        layout.menu("VIEW3D_MT_undoS", icon='ARROW_LEFTRIGHT')
        layout.operator("transform.snap_type", text="Snap Tools",
            icon='SNAP_ON')
        layout.menu("VIEW3D_MT_curs", icon='CURSOR')

        # Display editmode/objectmode toggle if active obj. is a mesh.
        if obj_act.type == 'MESH':
            layout.separator()

            # Toggle Editmode
            if context.mode != 'EDIT_MESH':
                layout.operator("object.editmode_toggle",
                    text="Enter Edit Mode",
                    icon='EDITMODE_HLT')
            if context.mode != 'OBJECT':
                layout.operator("object.editmode_toggle",
                    text="Enter Object Mode",
                    icon='OBJECT_DATAMODE')


class VIEW3D_MT_selectS(bpy.types.Menu):
    bl_label = "Selections"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("mesh.select_all")
        layout.operator("mesh.select_inverse")
        layout.operator("mesh.select_more")
        layout.operator("mesh.select_less")
        layout.operator("view3d.select_circle")
        layout.operator("view3d.select_border")


class VIEW3D_MT_undoS(bpy.types.Menu):
    bl_label = "Undo/Redo"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("ed.undo", icon='TRIA_LEFT')
        layout.operator("ed.redo", icon='TRIA_RIGHT')


class VIEW3D_MT_curs(bpy.types.Menu):
    bl_label = "Cursor Menu"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("view3d.snap_cursor_to_center",
            text="Snap Cursor to Center")
        layout.operator("view3d.snap_cursor_to_grid",
            text="Snap Cursor to Grid")
        layout.operator("view3d.snap_cursor_to_selected",
            text="Snap Cursor to Selected")
        layout.operator("view3d.snap_selected_to_cursor",
            text="Snap Selected to Cursor")
        layout.separator()
        layout.operator("view3d.pivot_cursor",
            text="Set Cursor as Pivot Point")
        layout.operator("view3d.revert_pivot",
            text="Revert Pivot Point")


class VIEW3D_MT_editM_Edge(bpy.types.Menu):
    bl_label = "Edges"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.separator()
        layout.operator("mesh.mark_seam")
        layout.operator("mesh.mark_seam", text="Clear Seam").clear = True
        layout.separator()
        layout.operator("mesh.mark_sharp")
        layout.operator("mesh.mark_sharp", text="Clear Sharp").clear = True
        layout.operator("mesh.extrude_move_along_normals", text="Extrude")
        layout.separator()
        layout.operator("mesh.edge_rotate",
            text="Rotate Edge CW").direction = 'CW'
        layout.operator("mesh.edge_rotate",
            text="Rotate Edge CCW").direction = 'CCW'
        layout.separator()
        layout.operator("TFM_OT_edge_slide", text="Edge Slide")
        layout.operator("mesh.loop_multi_select",
            text="Edge Loop")
        layout.operator("mesh.loop_multi_select",
            text="Edge Ring").ring = True
        layout.operator("mesh.loop_to_region")
        layout.operator("mesh.region_to_loop")


def register():
    bpy.types.register(VIEW3D_MT_Dynamic_Menu)
    bpy.types.register(pivot_cursor)
    bpy.types.register(revert_pivot)
    bpy.types.register(VIEW3D_MT_curs)
    bpy.types.register(VIEW3D_MT_editM_Edge)
    bpy.types.register(VIEW3D_MT_selectS)
    bpy.types.register(VIEW3D_MT_undoS)

    km = bpy.context.manager.active_keyconfig.keymaps['3D View']
    kmi = km.items.add('wm.call_menu', 'SELECTMOUSE', 'CLICK')
    kmi.properties.name = "VIEW3D_MT_Dynamic_Menu"


def unregister():
    bpy.types.unregister(VIEW3D_MT_Dynamic_Menu)
    bpy.types.unregister(pivot_cursor)
    bpy.types.unregister(revert_pivot)
    bpy.types.unregister(VIEW3D_MT_curs)
    bpy.types.unregister(VIEW3D_MT_editM_Edge)
    bpy.types.unregister(VIEW3D_MT_selectS)
    bpy.types.unregister(VIEW3D_MT_undoS)

    km = bpy.context.manager.active_keyconfig.keymaps['3D View']
    for kmi in km.items:
        if kmi.idname == 'wm.call_menu':
            if kmi.properties.name == "VIEW3D_MT_Dynamic_Menu":
                km.remove_item(kmi)
                break

if __name__ == "__main__":
    register()
