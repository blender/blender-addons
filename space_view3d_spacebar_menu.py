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
# Contributed to by: meta-androcto, JayDez, sim88, sam #

bl_info = {
    "name": "Dynamic Context Menu",
    "author": "meta-androcto",
    "version": (1, 8, 0),
    "blender": (2, 77, 0),
    "location": "View3D > Spacebar",
    "description": "Object Mode Context Sensitive Spacebar Menu",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/3D_interaction/Dynamic_Spacebar_Menu",
    "tracker_url": "https://developer.blender.org/maniphest/task/create/?project=3&type=Bug",
    "category": "3D View",
}

import bpy
from bpy.types import Operator, Menu

### Dynamic Context Sensitive Menu ###
### Main Menu based on Object Type & 3d View Editor Mode ###

class VIEW3D_MT_Space_Dynamic_Menu(bpy.types.Menu):
    bl_label = "Dynamic Context Menu"

    def draw(self, context):
        layout = self.layout
        settings = context.tool_settings
        layout.operator_context = 'INVOKE_REGION_WIN'
        scene = context.scene
        obj = context.object

### No Object Selected ###
        if not context.active_object:
            layout.operator_context = 'INVOKE_REGION_WIN'
            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()
            layout.menu("VIEW3D_MT_AddMenu", icon='OBJECT_DATAMODE')
            layout.menu("VIEW3D_MT_View_Directions", icon='ZOOM_ALL')
            layout.menu("VIEW3D_MT_View_Navigation", icon='ROTATE')
            layout.menu("VIEW3D_MT_View_Toggle", icon='SPLITSCREEN')
            layout.operator("view3d.snap_cursor_to_center",
                            text="Cursor to Center")
            layout.operator("view3d.snap_cursor_to_grid",
                            text="Cursor to Grid")
            layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')
            layout.operator("view3d.properties", icon='MENU_PANEL')

### Mesh Object Mode ###
        if obj and obj.type == 'MESH' and obj.mode in {'OBJECT'}:
            layout.operator_context = 'INVOKE_REGION_WIN'
            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()
            layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
            layout.menu("VIEW3D_MT_Select_Object", icon='RESTRICT_SELECT_OFF')
            layout.menu("VIEW3D_MT_AddMenu", icon='OBJECT_DATAMODE')
            layout.menu("VIEW3D_MT_Object", icon='VIEW3D')
            layout.menu("VIEW3D_MT_TransformMenu", icon='MANIPUL')
            layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')
            layout.menu("VIEW3D_MT_CursorMenu", icon='CURSOR')
            layout.menu("VIEW3D_MT_ParentMenu", icon='ROTACTIVE')
            layout.menu("VIEW3D_MT_GroupMenu", icon='GROUP')
            layout.menu("VIEW3D_MT_object_specials", text = "Specials", icon='SOLO_OFF')
            layout.menu("VIEW3D_MT_Camera_Options", icon='OUTLINER_OB_CAMERA')
            layout.operator_menu_enum("object.modifier_add", "type", icon='MODIFIER')
            layout.operator("object.delete", text="Delete Object", icon='X_VEC')
            layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
            layout.menu("VIEW3D_MT_Object_Interactive_Mode", icon='EDIT')
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')
            layout.operator("view3d.properties", icon='MENU_PANEL')

## Mesh Edit Mode ##
        if obj and obj.type == 'MESH' and obj.mode in {'EDIT'}:
            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()
            layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
            layout.menu("VIEW3D_MT_Select_Edit_Mesh", icon='RESTRICT_SELECT_OFF')
            layout.menu("INFO_MT_mesh_add", text="Add Mesh", icon='OUTLINER_OB_MESH')
            layout.menu("VIEW3D_MT_Edit_Mesh", text="Mesh", icon='MESH_DATA')
            layout.menu("VIEW3D_MT_TransformMenuEdit", icon='MANIPUL')
            layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')
            layout.menu("VIEW3D_MT_EditCursorMenu", icon='CURSOR')
            layout.menu("VIEW3D_MT_UV_Map", icon='MOD_UVPROJECT')
            layout.menu("VIEW3D_MT_edit_mesh_specials", icon='SOLO_OFF')
            layout.menu("VIEW3D_MT_edit_mesh_extrude", icon='ORTHO')
            layout.menu("VIEW3D_MT_Edit_Multi", icon='VERTEXSEL')
            layout.menu("VIEW3D_MT_edit_mesh_delete", icon='X_VEC')
            layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
            layout.menu("VIEW3D_MT_Object_Interactive_Mode", icon='EDIT')
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')
            layout.operator("view3d.properties", icon='MENU_PANEL')

## Sculpt Mode ##
        if obj and obj.type == 'MESH' and obj.mode in {'SCULPT'}:

            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()
            layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
            layout.menu("VIEW3D_MT_sculpt", icon='SCULPTMODE_HLT')
            layout.menu("VIEW3D_MT_brush", icon='ZOOM_ALL')
            layout.menu("VIEW3D_MT_hide_mask", icon='SCULPTMODE_HLT')
            layout.menu("VIEW3D_MT_TransformMenu", icon='MANIPUL')
            layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')
            layout.menu("VIEW3D_MT_CursorMenu", icon='CURSOR')
            layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
            layout.menu("VIEW3D_MT_Object_Interactive_Mode", icon='EDIT')
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')
            layout.operator("view3d.properties", icon='MENU_PANEL')

## Vertex Paint ##
        if obj and obj.type == 'MESH' and obj.mode in {'VERTEX_PAINT'}:

            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()
            layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
            layout.menu("VIEW3D_MT_paint_vertex", icon='VPAINT_HLT')
            layout.menu("VIEW3D_MT_brush", icon='BRUSH_DATA')
            layout.operator("paint.vertex_color_set", icon='GROUP_VCOL')
            layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
            layout.menu("VIEW3D_MT_Object_Interactive_Mode", icon='EDIT')
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')
            layout.operator("view3d.properties", icon='MENU_PANEL')

## Weight Paint Menu ##
        if obj and obj.type == 'MESH' and obj.mode in {'WEIGHT_PAINT'}:

            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()
            layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
            layout.menu("VIEW3D_MT_paint_weight", icon='WPAINT_HLT')
            layout.menu("VIEW3D_MT_brush", icon='BRUSH_DATA')
            layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
            layout.menu("VIEW3D_MT_Object_Interactive_Mode", icon='EDIT')
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')
            layout.operator("view3d.properties", icon='MENU_PANEL')

## Texture Paint ##
        if obj and obj.type == 'MESH' and obj.mode in {'TEXTURE_PAINT'}:

            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()
            layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
            layout.menu("VIEW3D_MT_brush", icon='BRUSH_DATA')
            layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
            layout.menu("VIEW3D_MT_Object_Interactive_Mode", icon='EDIT')
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')
            layout.operator("view3d.properties", icon='MENU_PANEL')

### Curve Object Mode ###
        if obj and obj.type == 'CURVE' and obj.mode in {'OBJECT'}:

            layout.operator_context = 'INVOKE_REGION_WIN'
            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()
            layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
            layout.menu("VIEW3D_MT_Select_Object", icon='RESTRICT_SELECT_OFF')
            layout.menu("VIEW3D_MT_AddMenu", icon='OBJECT_DATAMODE')
            layout.menu("VIEW3D_MT_Object", icon='VIEW3D')
            layout.menu("VIEW3D_MT_TransformMenu", icon='MANIPUL')
            layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')
            layout.menu("VIEW3D_MT_CursorMenu", icon='CURSOR')
            layout.menu("VIEW3D_MT_ParentMenu", icon='ROTACTIVE')
            layout.menu("VIEW3D_MT_GroupMenu", icon='GROUP')
            layout.menu("VIEW3D_MT_object_specials", text = "Specials", icon='SOLO_OFF')
            layout.menu("VIEW3D_MT_Camera_Options", icon='OUTLINER_OB_CAMERA')
            layout.operator_menu_enum("object.modifier_add", "type", icon='MODIFIER')
            layout.operator("object.delete", text="Delete Object", icon='X_VEC')
            layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
            layout.operator("object.editmode_toggle", text="Enter Edit Mode",
                            icon='OBJECT_DATA')
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')
            layout.operator("view3d.properties", icon='MENU_PANEL')

## Edit Curve ##
        if obj and obj.type == 'CURVE' and obj.mode in {'EDIT'}:

            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()
            layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
            layout.menu("VIEW3D_MT_Select_Edit_Curve",
                        icon='RESTRICT_SELECT_OFF')
            layout.menu("INFO_MT_curve_add", text="Add Curve",
                        icon='OUTLINER_OB_CURVE')
            layout.menu("VIEW3D_MT_Edit_Curve", icon='CURVE_DATA')
            layout.menu("VIEW3D_MT_TransformMenu", icon='MANIPUL')
            layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')
            layout.menu("VIEW3D_MT_CursorMenu", icon='CURSOR')
            layout.menu("VIEW3D_MT_EditCurveCtrlpoints",
                        icon='CURVE_BEZCURVE')
            layout.menu("VIEW3D_MT_EditCurveSpecials",
                        icon= 'SOLO_OFF')
            layout.operator("curve.delete", text="Delete Object",
                            icon='X_VEC')
            layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
            layout.operator("object.editmode_toggle", text="Enter Object Mode",
                            icon='OBJECT_DATA')
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')
            layout.operator("view3d.properties", icon='MENU_PANEL')

### Surface Object Mode ###
        if obj and obj.type == 'SURFACE' and obj.mode in {'OBJECT'}:

            layout.operator_context = 'INVOKE_REGION_WIN'
            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()
            layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
            layout.menu("VIEW3D_MT_Select_Object", icon='RESTRICT_SELECT_OFF')
            layout.menu("VIEW3D_MT_AddMenu", icon='OBJECT_DATAMODE')
            layout.menu("VIEW3D_MT_Object", icon='VIEW3D')
            layout.menu("VIEW3D_MT_TransformMenu", icon='MANIPUL')
            layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')
            layout.menu("VIEW3D_MT_CursorMenu", icon='CURSOR')
            layout.menu("VIEW3D_MT_ParentMenu", icon='ROTACTIVE')
            layout.menu("VIEW3D_MT_GroupMenu", icon='GROUP')
            layout.menu("VIEW3D_MT_object_specials", text = "Specials", icon='SOLO_OFF')
            layout.menu("VIEW3D_MT_Camera_Options", icon='OUTLINER_OB_CAMERA')
            layout.operator_menu_enum("object.modifier_add", "type", icon='MODIFIER')
            layout.operator("object.delete", text="Delete Object", icon='X_VEC')
            layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
            layout.operator("object.editmode_toggle", text="Enter Edit Mode",
                            icon='OBJECT_DATA')
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')
            layout.operator("view3d.properties", icon='MENU_PANEL')

## Edit Surface ##
        if obj and obj.type == 'SURFACE' and obj.mode in {'EDIT'}:

            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()
            layout.menu("INFO_MT_surface_add", text="Add Surface",
                        icon='OUTLINER_OB_SURFACE')
            layout.menu("VIEW3D_MT_TransformMenu", icon='MANIPUL')
            layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')
            layout.menu("VIEW3D_MT_CursorMenu", icon='CURSOR')
            layout.prop_menu_enum(settings, "proportional_edit",
                                  icon="PROP_CON")
            layout.prop_menu_enum(settings, "proportional_edit_falloff",
                                  icon="SMOOTHCURVE")
            layout.menu("VIEW3D_MT_EditCurveSpecials",
                        icon='SOLO_OFF')
            layout.menu("VIEW3D_MT_Select_Edit_Surface", icon='RESTRICT_SELECT_OFF')
            layout.operator("curve.delete", text="Delete Object",
                            icon='CANCEL')
            layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
            layout.operator("object.editmode_toggle", text="Enter Object Mode",
                            icon='OBJECT_DATA')
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')
            layout.operator("view3d.properties", icon='MENU_PANEL')

### Metaball Object Mode ###
        if obj and obj.type == 'META' and obj.mode in {'OBJECT'}:

            layout.operator_context = 'INVOKE_REGION_WIN'
            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()
            layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
            layout.menu("VIEW3D_MT_Select_Object", icon='RESTRICT_SELECT_OFF')
            layout.menu("VIEW3D_MT_AddMenu", icon='OBJECT_DATAMODE')
            layout.menu("VIEW3D_MT_Object", icon='VIEW3D')
            layout.menu("VIEW3D_MT_TransformMenu", icon='MANIPUL')
            layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')
            layout.menu("VIEW3D_MT_CursorMenu", icon='CURSOR')
            layout.menu("VIEW3D_MT_ParentMenu", icon='ROTACTIVE')
            layout.menu("VIEW3D_MT_GroupMenu", icon='GROUP')
            layout.menu("VIEW3D_MT_object_specials", text = "Specials", icon='SOLO_OFF')
            layout.menu("VIEW3D_MT_Camera_Options", icon='OUTLINER_OB_CAMERA')
            layout.operator_menu_enum("object.modifier_add", "type", icon='MODIFIER')
            layout.operator("object.delete", text="Delete Object", icon='X_VEC')
            layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
            layout.operator("object.editmode_toggle", text="Enter Edit Mode",
                            icon='OBJECT_DATA')
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')
            layout.operator("view3d.properties", icon='MENU_PANEL')

## Edit Metaball ##
        if obj and obj.type == 'META' and obj.mode in {'EDIT'}:

            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()
            layout.operator_menu_enum("object.metaball_add", "type",
                                      text="Add Metaball",
                                      icon='OUTLINER_OB_META')
            layout.menu("VIEW3D_MT_TransformMenu", icon='MANIPUL')
            layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')
            layout.menu("VIEW3D_MT_CursorMenu", icon='CURSOR')
            layout.prop_menu_enum(settings, "proportional_edit",
                                  icon="PROP_CON")
            layout.prop_menu_enum(settings, "proportional_edit_falloff",
                                  icon="SMOOTHCURVE")
            layout.menu("VIEW3D_MT_SelectMetaball", icon='RESTRICT_SELECT_OFF')
            layout.operator("mball.delete_metaelems", text="Delete Object",
                            icon='CANCEL')
            layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
            layout.operator("object.editmode_toggle", text="Enter Object Mode",
                            icon='OBJECT_DATA')
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')
            layout.operator("view3d.properties", icon='MENU_PANEL')

### Text Object Mode ###
        if obj and obj.type == 'FONT' and obj.mode in {'OBJECT'}:

            layout.operator_context = 'INVOKE_REGION_WIN'
            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()
            layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
            layout.menu("VIEW3D_MT_Select_Object", icon='RESTRICT_SELECT_OFF')
            layout.menu("VIEW3D_MT_AddMenu", icon='OBJECT_DATAMODE')
            layout.menu("VIEW3D_MT_Object", icon='VIEW3D')
            layout.menu("VIEW3D_MT_TransformMenu", icon='MANIPUL')
            layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')
            layout.menu("VIEW3D_MT_CursorMenu", icon='CURSOR')
            layout.menu("VIEW3D_MT_ParentMenu", icon='ROTACTIVE')
            layout.menu("VIEW3D_MT_GroupMenu", icon='GROUP')
            layout.menu("VIEW3D_MT_object_specials", text = "Specials", icon='SOLO_OFF')
            layout.menu("VIEW3D_MT_Camera_Options", icon='OUTLINER_OB_CAMERA')
            layout.operator("object.delete", text="Delete Object", icon='X_VEC')
            layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
            layout.operator("object.editmode_toggle", text="Enter Edit Mode",
                            icon='OBJECT_DATA')
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')
            layout.operator("view3d.properties", icon='MENU_PANEL')

### Text Edit Mode ###
        if obj and obj.type == 'FONT' and obj.mode in {'EDIT'}:

            layout.operator_context = 'INVOKE_REGION_WIN'
            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()
            layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
            layout.menu("VIEW3D_MT_select_edit_text", icon='VIEW3D')
            layout.menu("VIEW3D_MT_edit_font", icon='RESTRICT_SELECT_OFF')
            layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
            layout.operator("object.editmode_toggle", text="Enter Object Mode",
                            icon='OBJECT_DATA')
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')
            layout.operator("view3d.properties", icon='MENU_PANEL')

### Camera Object Mode ###
        if obj and obj.type == 'CAMERA' and obj.mode in {'OBJECT'}:

            layout.operator_context = 'INVOKE_REGION_WIN'
            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()
            layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
            layout.menu("VIEW3D_MT_Select_Object", icon='RESTRICT_SELECT_OFF')
            layout.menu("VIEW3D_MT_AddMenu", icon='OBJECT_DATAMODE')
            layout.menu("VIEW3D_MT_Object", icon='VIEW3D')
            layout.menu("VIEW3D_MT_TransformMenu", icon='MANIPUL')
            layout.menu("VIEW3D_MT_CursorMenuLite", icon='CURSOR')
            layout.menu("VIEW3D_MT_ParentMenu", icon='ROTACTIVE')
            layout.menu("VIEW3D_MT_GroupMenu", icon='GROUP')
            layout.menu("VIEW3D_MT_object_specials", text = "Specials", icon='SOLO_OFF')
            layout.menu("VIEW3D_MT_Camera_Options", icon='OUTLINER_OB_CAMERA')
            layout.operator("object.delete", text="Delete Object", icon='X_VEC')
            layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')
            layout.operator("view3d.properties", icon='MENU_PANEL')

### Lamp Object Mode ###
        if obj and obj.type == 'LAMP' and obj.mode in {'OBJECT'}:

            layout.operator_context = 'INVOKE_REGION_WIN'
            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()
            layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
            layout.menu("VIEW3D_MT_Select_Object", icon='RESTRICT_SELECT_OFF')
            layout.menu("VIEW3D_MT_AddMenu", icon='OBJECT_DATAMODE')
            layout.menu("VIEW3D_MT_Object", icon='VIEW3D')
            layout.menu("VIEW3D_MT_TransformMenuLite", icon='MANIPUL')
            layout.menu("VIEW3D_MT_CursorMenuLite", icon='CURSOR')
            layout.menu("VIEW3D_MT_ParentMenu", icon='ROTACTIVE')
            layout.menu("VIEW3D_MT_GroupMenu", icon='GROUP')
            layout.menu("VIEW3D_MT_object_specials", text = "Specials", icon='SOLO_OFF')
            layout.menu("VIEW3D_MT_Camera_Options", icon='OUTLINER_OB_CAMERA')
            layout.operator("object.delete", text="Delete Object", icon='X_VEC')
            layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')
            layout.operator("view3d.properties", icon='MENU_PANEL')

### Armature Object Mode ###
        if obj and obj.type == 'ARMATURE' and obj.mode in {'OBJECT'}:

            layout.operator_context = 'INVOKE_REGION_WIN'
            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()
            layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
            layout.menu("VIEW3D_MT_Select_Object", icon='RESTRICT_SELECT_OFF')
            layout.menu("VIEW3D_MT_AddMenu", icon='OBJECT_DATAMODE')
            layout.menu("VIEW3D_MT_Object", icon='VIEW3D')
            layout.menu("VIEW3D_MT_TransformMenuArmature", icon='MANIPUL')
            layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')
            layout.menu("VIEW3D_MT_CursorMenuLite", icon='CURSOR')
            layout.menu("VIEW3D_MT_ParentMenu", icon='ROTACTIVE')
            layout.menu("VIEW3D_MT_GroupMenu", icon='GROUP')
            layout.menu("VIEW3D_MT_object_specials", text = "Specials", icon='SOLO_OFF')
            layout.menu("VIEW3D_MT_Camera_Options", icon='OUTLINER_OB_CAMERA')
            layout.operator("object.delete", text="Delete Object", icon='X_VEC')
            layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
            layout.menu("VIEW3D_MT_Object_Interactive_Armature", icon='VIEW3D')
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')
            layout.operator("view3d.properties", icon='MENU_PANEL')

## Armature Edit ##
        if obj and obj.type == 'ARMATURE' and obj.mode in {'EDIT'}:

            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()
            layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
            layout.menu("VIEW3D_MT_Select_Edit_Armature",
                        icon='RESTRICT_SELECT_OFF')
            layout.menu("INFO_MT_armature_add", text="Add Armature",
                        icon='OUTLINER_OB_ARMATURE')
            layout.menu("VIEW3D_MT_Edit_Armature", text="Armature",
                        icon='OUTLINER_DATA_ARMATURE')
            layout.menu("VIEW3D_MT_EditArmatureTK",
                        icon='ARMATURE_DATA')
            layout.menu("VIEW3D_MT_TransformMenuArmatureEdit", icon='MANIPUL')
            layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')
            layout.menu("VIEW3D_MT_CursorMenuLite", icon='CURSOR')
            layout.menu("VIEW3D_MT_ParentMenu", icon='ROTACTIVE')
            layout.menu("VIEW3D_MT_armature_specials", icon='SOLO_OFF')
            layout.menu("VIEW3D_MT_edit_armature_roll",
                        icon='BONE_DATA')
            layout.operator("armature.delete", text="Delete Object",
                            icon='X_VEC')
            layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
            layout.menu("VIEW3D_MT_Object_Interactive_Armature", icon='VIEW3D')
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')
            layout.operator("view3d.properties", icon='MENU_PANEL')

## Armature Pose ##
        if obj and obj.type == 'ARMATURE' and obj.mode in {'POSE'}:

            arm = context.active_object.data

            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()
            layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
            layout.menu("VIEW3D_MT_Select_Pose", icon='RESTRICT_SELECT_OFF')
            layout.menu("VIEW3D_MT_Pose", icon='OUTLINER_DATA_POSE')
            layout.menu("VIEW3D_MT_TransformMenuArmaturePose", icon='MANIPUL')
            layout.menu("VIEW3D_MT_pose_transform", icon='EMPTY_DATA')
            layout.menu("VIEW3D_MT_CursorMenuLite", icon='CURSOR')
            layout.menu("VIEW3D_MT_PoseCopy", icon='FILE')

            if arm.draw_type in {'BBONE', 'ENVELOPE'}:
                layout.operator("transform.transform",
                                text="Scale Envelope Distance").mode = 'BONE_SIZE'

            layout.menu("VIEW3D_MT_pose_apply", icon='AUTO')
            layout.operator("pose.relax", icon= 'ARMATURE_DATA')
            layout.menu("VIEW3D_MT_KeyframeMenu", icon='KEY_HLT')
            layout.menu("VIEW3D_MT_pose_specials", icon='SOLO_OFF')
            layout.menu("VIEW3D_MT_pose_group", icon= 'GROUP_BONE')
            layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
            layout.menu("VIEW3D_MT_Object_Interactive_Armature", icon='VIEW3D')
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')
            layout.operator("view3d.properties", icon='MENU_PANEL')

### Lattice Object Mode ###
        if obj and obj.type == 'LATTICE' and obj.mode in {'OBJECT'}:

            layout.operator_context = 'INVOKE_REGION_WIN'
            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()
            layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
            layout.menu("VIEW3D_MT_Select_Object", icon='RESTRICT_SELECT_OFF')
            layout.menu("VIEW3D_MT_AddMenu", icon='OBJECT_DATAMODE')
            layout.menu("VIEW3D_MT_Object", icon='VIEW3D')
            layout.menu("VIEW3D_MT_TransformMenu", icon='MANIPUL')
            layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')
            layout.menu("VIEW3D_MT_CursorMenu", icon='CURSOR')
            layout.menu("VIEW3D_MT_ParentMenu", icon='ROTACTIVE')
            layout.menu("VIEW3D_MT_GroupMenu", icon='GROUP')
            layout.menu("VIEW3D_MT_object_specials", text = "Specials", icon='SOLO_OFF')
            layout.menu("VIEW3D_MT_Camera_Options", icon='OUTLINER_OB_CAMERA')
            layout.operator_menu_enum("object.modifier_add", "type", icon='MODIFIER')
            layout.operator("object.delete", text="Delete Object", icon='X_VEC')
            layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
            layout.operator("object.editmode_toggle", text="Enter Edit Mode",
                            icon='OBJECT_DATA')
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')
            layout.operator("view3d.properties", icon='MENU_PANEL')

## Edit Lattice ##
        if obj and obj.type == 'LATTICE' and obj.mode in {'EDIT'}:

            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()
            layout.menu("VIEW3D_MT_TransformMenu", icon='MANIPUL')
            layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')
            layout.menu("VIEW3D_MT_CursorMenu", icon='CURSOR')
            layout.prop_menu_enum(settings, "proportional_edit",
                                  icon= "PROP_CON")
            layout.prop_menu_enum(settings, "proportional_edit_falloff",
                                  icon= "SMOOTHCURVE")
            layout.operator("lattice.make_regular")
            layout.menu("VIEW3D_MT_Select_Edit_Lattice",
                        icon='RESTRICT_SELECT_OFF')
            layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
            layout.operator("object.editmode_toggle", text="Enter Object Mode",
                            icon='OBJECT_DATA')
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')
            layout.operator("view3d.properties", icon='MENU_PANEL')

### Empty Object Mode ###
        if obj and obj.type == 'EMPTY' and obj.mode in {'OBJECT'}:

            layout.operator_context = 'INVOKE_REGION_WIN'
            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()
            layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
            layout.menu("VIEW3D_MT_Select_Object", icon='RESTRICT_SELECT_OFF')
            layout.menu("VIEW3D_MT_AddMenu", icon='OBJECT_DATAMODE')
            layout.menu("VIEW3D_MT_Object", icon='VIEW3D')
            layout.menu("VIEW3D_MT_TransformMenuLite", icon='MANIPUL')
            layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')
            layout.menu("VIEW3D_MT_CursorMenuLite", icon='CURSOR')
            layout.menu("VIEW3D_MT_ParentMenu", icon='ROTACTIVE')
            layout.menu("VIEW3D_MT_GroupMenu", icon='GROUP')
            layout.menu("VIEW3D_MT_object_specials", text = "Specials", icon='SOLO_OFF')
            layout.menu("VIEW3D_MT_Camera_Options", icon='OUTLINER_OB_CAMERA')
            layout.operator("object.delete", text="Delete Object", icon='X_VEC')
            layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')
            layout.operator("view3d.properties", icon='MENU_PANEL')

### Speaker Object Mode ###
        if obj and obj.type == 'SPEAKER' and obj.mode in {'OBJECT'}:

            layout.operator_context = 'INVOKE_REGION_WIN'
            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()
            layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
            layout.menu("VIEW3D_MT_Select_Object", icon='RESTRICT_SELECT_OFF')
            layout.menu("VIEW3D_MT_AddMenu", icon='OBJECT_DATAMODE')
            layout.menu("VIEW3D_MT_Object", icon='VIEW3D')
            layout.menu("VIEW3D_MT_TransformMenuLite", icon='MANIPUL')
            layout.menu("VIEW3D_MT_CursorMenuLite", icon='CURSOR')
            layout.menu("VIEW3D_MT_ParentMenu", icon='ROTACTIVE')
            layout.menu("VIEW3D_MT_GroupMenu", icon='GROUP')
            layout.operator("object.delete", text="Delete Object", icon='X_VEC')
            layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')
            layout.operator("view3d.properties", icon='MENU_PANEL')

## Particle Menu ##
        if obj and  context.mode == 'PARTICLE':

            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()
            layout.menu("VIEW3D_MT_TransformMenu", icon='MANIPUL')
            layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')
            layout.menu("VIEW3D_MT_CursorMenuLite", icon='CURSOR')
            layout.prop_menu_enum(settings, "proportional_edit",
                                  icon= "PROP_CON")
            layout.prop_menu_enum(settings, "proportional_edit_falloff",
                                  icon= "SMOOTHCURVE")
            layout.menu("VIEW3D_MT_particle", icon='PARTICLEMODE')
            layout.menu("VIEW3D_MT_particle_specials", text="Hair Specials", icon='HAIR')
            layout.menu("VIEW3D_MT_Select_Particle",
                        icon='RESTRICT_SELECT_OFF')
            layout.operator("object.delete", text="Delete Object", icon='X_VEC')
            layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
            layout.menu("VIEW3D_MT_Object_Interactive_Mode", icon='VIEW3D')
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')
            layout.operator("view3d.properties", icon='MENU_PANEL')

############ Object Menus #########

# ********** Object Menu **********
class VIEW3D_MT_Object(bpy.types.Menu):
    bl_context = "objectmode"
    bl_label = "Object"

    def draw(self, context):
        layout = self.layout
        view = context.space_data
        is_local_view = (view.local_view is not None)

        layout.operator("object.delete", text="Delete...").use_global = False
        layout.menu("VIEW3D_MT_object_parent")
        layout.menu("VIEW3D_MT_Duplicate")
        layout.operator("object.join")

        if is_local_view:
            layout.operator_context = 'EXEC_REGION_WIN'
            layout.operator("object.move_to_layer", text="Move out of Local View")
            layout.operator_context = 'INVOKE_REGION_WIN'
        else:
            layout.operator("object.move_to_layer", text="Move to Layer...")

        layout.menu("VIEW3D_MT_make_links", text="Make Links...")
        layout.menu("VIEW3D_MT_Object_Data_Link")
        layout.menu("VIEW3D_MT_object_constraints")
        layout.menu("VIEW3D_MT_object_track")
        layout.menu("VIEW3D_MT_object_animation")	
        layout.menu("VIEW3D_MT_object_game")
        layout.menu("VIEW3D_MT_object_showhide")
        layout.operator_menu_enum("object.convert", "target")

# ********** Object Add **********
class VIEW3D_MT_AddMenu(bpy.types.Menu):
    bl_label = "Add Object"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.menu("INFO_MT_mesh_add", text="Add Mesh",
                    icon='OUTLINER_OB_MESH')
        layout.menu("INFO_MT_curve_add", text="Add Curve",
                    icon='OUTLINER_OB_CURVE')
        layout.menu("INFO_MT_surface_add", text="Add Surface",
                    icon='OUTLINER_OB_SURFACE')
        layout.operator_menu_enum("object.metaball_add", "type",
                                  icon='OUTLINER_OB_META')
        layout.operator("object.text_add", text="Add Text",
                        icon='OUTLINER_OB_FONT')
        layout.menu("INFO_MT_armature_add", text="Add Armature",
                    icon='OUTLINER_OB_ARMATURE')
        layout.operator("object.add", text="Lattice",
                        icon='OUTLINER_OB_LATTICE').type = 'LATTICE'
        layout.operator_menu_enum("object.empty_add", "type", text="Empty", icon='OUTLINER_OB_EMPTY')
        layout.operator("object.speaker_add", text="Speaker", icon='OUTLINER_OB_SPEAKER')
        layout.operator("object.camera_add", text="Camera",
                        icon='OUTLINER_OB_CAMERA')
        layout.operator_menu_enum("object.lamp_add", "type",
                                  icon="OUTLINER_OB_LAMP")
        layout.operator_menu_enum("object.effector_add", "type",
                                  text="Force Field",
                                  icon='FORCE_FORCE')
        layout.menu("VIEW3D_MT_object_quick_effects", text="Quick Effects", icon='PARTICLES')
        layout.operator_menu_enum("object.group_instance_add", "group",
                                  text="Group Instance",
                                  icon='GROUP_VERTEX')

# ********** Object Manipulator **********
class VIEW3D_MT_ManipulatorMenu1(bpy.types.Menu):
    bl_label = "Manipulator"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        props = layout.operator("view3d.enable_manipulator",text ='Translate', icon='MAN_TRANS')
        props.translate = True
        props = layout.operator("view3d.enable_manipulator",text ='Rotate', icon='MAN_ROT')
        props.rotate = True
        props = layout.operator("view3d.enable_manipulator",text ='Scale', icon='MAN_SCALE')
        props.scale = True
        props = layout.operator("view3d.enable_manipulator",text ='Combo', icon='MAN_SCALE')
        props.scale = True
        props.rotate = True
        props.translate = True
        props = layout.operator("view3d.enable_manipulator",text ='Hide', icon='MAN_SCALE')
        props.scale = False
        props.rotate = False
        props.translate = False

# ********** Object Mirror **********
class VIEW3D_MT_MirrorMenu(bpy.types.Menu):
    bl_label = "Mirror"

    def draw(self, context):
        layout = self.layout
        layout.operator("transform.mirror", text="Interactive Mirror")
        layout.operator_context = 'INVOKE_REGION_WIN'
        props = layout.operator("transform.mirror", text="X Global")
        props.constraint_axis = (True, False, False)
        props.constraint_orientation = 'GLOBAL'
        props = layout.operator("transform.mirror", text="Y Global")
        props.constraint_axis = (False, True, False)
        props.constraint_orientation = 'GLOBAL'
        props = layout.operator("transform.mirror", text="Z Global")
        props.constraint_axis = (False, False, True)
        props.constraint_orientation = 'GLOBAL'

        if context.edit_object:

            props = layout.operator("transform.mirror", text="X Local")
            props.constraint_axis = (True, False, False)
            props.constraint_orientation = 'LOCAL'
            props = layout.operator("transform.mirror", text="Y Local")
            props.constraint_axis = (False, True, False)
            props.constraint_orientation = 'LOCAL'
            props = layout.operator("transform.mirror", text="Z Local")
            props.constraint_axis = (False, False, True)
            props.constraint_orientation = 'LOCAL'
            layout.operator("object.vertex_group_mirror")

# ********** Object Snap Cursor **********
class VIEW3D_MT_Pivot(bpy.types.Menu):
    bl_label = "Pivot"

    def draw(self, context):
        layout = self.layout
        layout.prop(context.space_data, "pivot_point", expand=True)
        if context.active_object.mode == 'OBJECT':
            layout.prop(context.space_data, "use_pivot_point_align", text="Center Points")

class VIEW3D_Snap_Context(bpy.types.Menu):
    bl_label = "Snapping"

    def draw(self, context):
        layout = self.layout
        toolsettings = context.tool_settings
        layout.prop(toolsettings, "snap_element", expand=True)
        layout.prop(toolsettings, "use_snap")
		
class VIEW3D_Snap_Origin(bpy.types.Menu):
    bl_label = "Snap Origin"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'EXEC_AREA'
        layout.operator("object.origin_set",
                        text="Geometry to Origin").type = 'GEOMETRY_ORIGIN'
        layout.operator("object.origin_set",
                        text="Origin to Geometry").type = 'ORIGIN_GEOMETRY'
        layout.operator("object.origin_set",
                        text="Origin to 3D Cursor").type = 'ORIGIN_CURSOR'
        layout.operator("object.origin_set",
                        text="Origin to Center of Mass").type = 'ORIGIN_CENTER_OF_MASS'

class VIEW3D_MT_CursorMenu(bpy.types.Menu):
    bl_label = "Snap Cursor"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.menu("VIEW3D_Snap_Origin")
        layout.menu("VIEW3D_Snap_Context")
        layout.operator("view3d.snap_cursor_to_selected",
                        text="Cursor to Selected")
        layout.operator("view3d.snap_cursor_to_center",
                        text="Cursor to Center")
        layout.operator("view3d.snap_cursor_to_grid",
                        text="Cursor to Grid")
        layout.operator("view3d.snap_cursor_to_active",
                        text="Cursor to Active")
        layout.operator("view3d.snap_selected_to_cursor", text="Selection to Cursor").use_offset = False
        layout.operator("view3d.snap_selected_to_cursor", text="Selection to Cursor (Offset)").use_offset = True
        layout.operator("view3d.snap_selected_to_grid",
                        text="Selection to Grid")
        layout.menu("VIEW3D_MT_Pivot")
        layout.operator("view3d.pivot_cursor",
                        text="Set Cursor as Pivot Point")
        layout.operator("view3d.revert_pivot",
                        text="Revert Pivot Point")

class VIEW3D_MT_CursorMenuLite(bpy.types.Menu):
    bl_label = "Snap Cursor"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.menu("VIEW3D_Snap_Origin")
        layout.operator("view3d.snap_cursor_to_selected",
                        text="Cursor to Selected")
        layout.operator("view3d.snap_cursor_to_center",
                        text="Cursor to Center")
        layout.operator("view3d.snap_cursor_to_grid",
                        text="Cursor to Grid")
        layout.operator("view3d.snap_cursor_to_active",
                        text="Cursor to Active")
        layout.operator("view3d.snap_selected_to_cursor", text="Selection to Cursor").use_offset = False
        layout.operator("view3d.snap_selected_to_cursor", text="Selection to Cursor (Offset)").use_offset = True
        layout.operator("view3d.snap_selected_to_grid",
                        text="Selection to Grid")
        layout.menu("VIEW3D_MT_Pivot")
        layout.operator("view3d.pivot_cursor",
                        text="Set Cursor as Pivot Point")
        layout.operator("view3d.revert_pivot",
                        text="Revert Pivot Point")

# ********** Object Interactive Mode **********
class InteractiveMode(bpy.types.Menu):
	bl_idname = "VIEW3D_MT_Object_Interactive_Mode"
	bl_label = "Interactive Mode"
	bl_description = "Menu of objects interactive modes (Window Types)"
	
	def draw(self, context):
		self.layout.operator(SetObjectMode.bl_idname, text="Object", icon="OBJECT_DATAMODE").mode = "OBJECT"
		self.layout.operator(SetObjectMode.bl_idname, text="Edit", icon="EDITMODE_HLT").mode = "EDIT"
		self.layout.operator(SetObjectMode.bl_idname, text="Sculpt", icon="SCULPTMODE_HLT").mode = "SCULPT"
		self.layout.operator(SetObjectMode.bl_idname, text="Vertex Paint", icon="VPAINT_HLT").mode = "VERTEX_PAINT"
		self.layout.operator(SetObjectMode.bl_idname, text="Weight Paint", icon="WPAINT_HLT").mode = "WEIGHT_PAINT"
		self.layout.operator(SetObjectMode.bl_idname, text="Texture Paint", icon="TPAINT_HLT").mode = "TEXTURE_PAINT"
		self.layout.operator(SetObjectMode.bl_idname, text="Particle Edit", icon="PARTICLEMODE").mode = "PARTICLE_EDIT"

# ********** Object Armature Interactive Mode **********
class InteractiveModeArmature(bpy.types.Menu):
	bl_idname = "VIEW3D_MT_Object_Interactive_Armature"
	bl_label = "Interactive Mode"
	bl_description = "Menu of objects interactive mode"
	
	def draw(self, context):
		self.layout.operator(SetObjectMode.bl_idname, text="Object", icon="OBJECT_DATAMODE").mode = "OBJECT"
		self.layout.operator(SetObjectMode.bl_idname, text="Edit", icon="EDITMODE_HLT").mode = "EDIT"
		self.layout.operator(SetObjectMode.bl_idname, text="Pose", icon="POSE_HLT").mode = "POSE"

# ********** Object Parent **********
class VIEW3D_MT_ParentMenu(bpy.types.Menu):
    bl_label = "Parent"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.parent_set", text="Set")
        layout.operator("object.parent_clear", text="Clear")

# ********** Object Group **********
class VIEW3D_MT_GroupMenu(bpy.types.Menu):
    bl_label = "Group"

    def draw(self, context):
        layout = self.layout
        layout.operator("group.create")
        layout.operator("group.objects_remove")
        layout.operator("group.objects_remove_all")
        layout.operator("group.objects_add_active")
        layout.operator("group.objects_remove_active")

# ********** Object Camera Options **********
class VIEW3D_MT_Camera_Options(bpy.types.Menu):
    bl_label = "Camera"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'EXEC_REGION_WIN'
        layout.operator("object.camera_add", text="Add Camera", icon='OUTLINER_OB_CAMERA')
        self.layout.operator("view3d.object_as_camera", text="Object As Camera", icon='OUTLINER_OB_CAMERA')
        self.layout.operator("view3d.viewnumpad", text="View Active Camera" , icon='OUTLINER_OB_CAMERA').type = 'CAMERA'


class VIEW3D_MT_Object_Data_Link(Menu):
    bl_label = "Object Data"

    def draw(self, context):
        layout = self.layout

        layout.operator_menu_enum("object.make_local", "type", text="Make Local...")
        layout.menu("VIEW3D_MT_make_single_user")
        layout.operator("object.proxy_make", text="Make Proxy...")
        layout.operator("object.make_dupli_face")
        layout.operator("object.data_transfer")
        layout.operator("object.datalayout_transfer")

class VIEW3D_MT_Duplicate(Menu):
    bl_label = "Duplicate"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.duplicate_move")
        layout.operator("object.duplicate_move_linked")
        layout.separator()

class VIEW3D_MT_KeyframeMenu(bpy.types.Menu):
    bl_label = "Keyframe"

    def draw(self, context):
        layout = self.layout
        layout.operator("anim.keyframe_insert_menu",
                        text="Insert Keyframe...")
        layout.operator("anim.keyframe_delete_v3d",
                        text="Delete Keyframe...")
        layout.operator("anim.keying_set_active_set",
                        text="Change Keying Set...")

class VIEW3D_MT_UndoS(bpy.types.Menu):
    bl_label = "Undo/Redo"

    def draw(self, context):
        layout = self.layout

        layout.operator("ed.undo")
        layout.operator("ed.redo")
        layout.operator("ed.undo_history")

############ Edit Mode Menu's #########

# ********** Edit Mesh **********
class VIEW3D_MT_Edit_Mesh(Menu):
    bl_label = "Mesh"

    def draw(self, context):
        layout = self.layout
        toolsettings = context.tool_settings

        layout.menu("VIEW3D_MT_edit_mesh_vertices", icon='VERTEXSEL')
        layout.menu("VIEW3D_MT_edit_mesh_edges", icon='EDGESEL')
        layout.menu("VIEW3D_MT_edit_mesh_faces", icon='FACESEL')
        layout.operator("mesh.duplicate_move")
        layout.menu("VIEW3D_MT_edit_mesh_clean", icon='AUTO')
        layout.menu("VIEW3D_MT_edit_mesh_normals", icon='META_DATA')
        layout.operator("mesh.loopcut_slide",
                        text="Loopcut", icon='EDIT_VEC')
        layout.operator("mesh.symmetrize")
        layout.operator("mesh.symmetry_snap")
        layout.operator("mesh.bisect")
        layout.operator_menu_enum("mesh.sort_elements", "type", text="Sort Elements...")
        layout.prop(toolsettings, "use_mesh_automerge")
        layout.prop_menu_enum(toolsettings, "proportional_edit")
        layout.prop_menu_enum(toolsettings, "proportional_edit_falloff")
        layout.menu("VIEW3D_MT_edit_mesh_showhide")

# ********** Edit Multiselect **********
class VIEW3D_MT_Edit_Multi(bpy.types.Menu):
    bl_label = "Multi Select"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.separator()
        prop = layout.operator("wm.context_set_value", text="Vertex Select",
                               icon='VERTEXSEL')
        prop.value = "(True, False, False)"
        prop.data_path = "tool_settings.mesh_select_mode"

        prop = layout.operator("wm.context_set_value", text="Edge Select",
                               icon='EDGESEL')
        prop.value = "(False, True, False)"
        prop.data_path = "tool_settings.mesh_select_mode"

        prop = layout.operator("wm.context_set_value", text="Face Select",
                               icon='FACESEL')
        prop.value = "(False, False, True)"
        prop.data_path = "tool_settings.mesh_select_mode"
        layout.separator()

        prop = layout.operator("wm.context_set_value",
                               text="Vertex & Edge Select",
                               icon='EDITMODE_HLT')
        prop.value = "(True, True, False)"
        prop.data_path = "tool_settings.mesh_select_mode"

        prop = layout.operator("wm.context_set_value",
                               text="Vertex & Face Select",
                               icon='ORTHO')
        prop.value = "(True, False, True)"
        prop.data_path = "tool_settings.mesh_select_mode"

        prop = layout.operator("wm.context_set_value",
                               text="Edge & Face Select",
                               icon='SNAP_FACE')
        prop.value = "(False, True, True)"
        prop.data_path = "tool_settings.mesh_select_mode"
        layout.separator()

        prop = layout.operator("wm.context_set_value",
                               text="Vertex & Edge & Face Select",
                               icon='SNAP_VOLUME')
        prop.value = "(True, True, True)"
        prop.data_path = "tool_settings.mesh_select_mode"

# ********** Edit Mesh Edge **********
class VIEW3D_MT_EditM_Edge(bpy.types.Menu):
    bl_label = "Edges"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

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
        layout.operator("mesh.loop_multi_select", text="Edge Loop")
        layout.operator("mesh.loop_multi_select", text="Edge Ring").ring = True
        layout.operator("mesh.loop_to_region")
        layout.operator("mesh.region_to_loop")


# ********** Edit Mesh Cursor **********
class VIEW3D_MT_EditCursorMenu(bpy.types.Menu):
    bl_label = "Snap Cursor"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("object.setorigintoselected",
                        text="Origin to Selected V/F/E")
        layout.menu("VIEW3D_Snap_Origin")
        layout.menu("VIEW3D_Snap_Context")
        layout.operator("view3d.snap_cursor_to_selected",
                        text="Cursor to Selected")
        layout.operator("view3d.snap_cursor_to_center",
                        text="Cursor to Center")
        layout.operator("view3d.snap_cursor_to_grid",
                        text="Cursor to Grid")
        layout.operator("view3d.snap_cursor_to_active",
                        text="Cursor to Active")
        layout.operator("view3d.snap_selected_to_cursor", text="Selection to Cursor").use_offset = False
        layout.operator("view3d.snap_selected_to_cursor", text="Selection to Cursor (Offset)").use_offset = True
        layout.operator("view3d.snap_selected_to_grid",
                        text="Selection to Grid")
        layout.menu("VIEW3D_MT_Pivot")
        layout.operator("view3d.pivot_cursor",
                        text="Set Cursor as Pivot Point")
        layout.operator("view3d.revert_pivot",
                        text="Revert Pivot Point")
        layout.operator("view3d.snap_cursor_to_edge_intersection",
                        text="Cursor to Edge Intersection")

# ********** Edit Mesh UV **********
class VIEW3D_MT_UV_Map(bpy.types.Menu):
    bl_label = "UV Mapping"

    def draw(self, context):
        layout = self.layout
        layout.operator("uv.unwrap")
        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("uv.smart_project")
        layout.operator("uv.lightmap_pack")
        layout.operator("uv.follow_active_quads")
        layout.operator_context = 'EXEC_REGION_WIN'
        layout.operator("uv.cube_project")
        layout.operator("uv.cylinder_project")
        layout.operator("uv.sphere_project")
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("uv.project_from_view").scale_to_bounds = False
        layout.operator("uv.project_from_view", text="Project from View (Bounds)").scale_to_bounds = True
        layout.operator("uv.reset")


# ********** Edit Curve **********
class VIEW3D_MT_Edit_Curve(bpy.types.Menu):
    bl_label = "Curve"

    def draw(self, context):
        layout = self.layout

        toolsettings = context.tool_settings

        layout.operator("curve.extrude_move")
        layout.operator("curve.spin")
        layout.operator("curve.duplicate_move")
        layout.operator("curve.split")
        layout.operator("curve.separate")
        layout.operator("curve.make_segment")
        layout.operator("curve.cyclic_toggle")
        layout.operator("curve.delete", text="Delete...")
        layout.menu("VIEW3D_MT_edit_curve_segments")
        layout.prop_menu_enum(settings, "proportional_edit",
                              icon="PROP_CON")
        layout.prop_menu_enum(settings, "proportional_edit_falloff",
                              icon="SMOOTHCURVE")
        layout.menu("VIEW3D_MT_edit_curve_showhide")

class VIEW3D_MT_EditCurveCtrlpoints(bpy.types.Menu):
    bl_label = "Control Points"

    def draw(self, context):
        layout = self.layout

        edit_object = context.edit_object

        if edit_object.type == 'CURVE':
            layout.operator("transform.transform").mode = 'TILT'
            layout.operator("curve.tilt_clear")
            layout.operator("curve.separate")
            layout.operator_menu_enum("curve.handle_type_set", "type")
            layout.menu("VIEW3D_MT_hook")

class VIEW3D_MT_EditCurveSegments(bpy.types.Menu):
    bl_label = "Curve Segments"

    def draw(self, context):
        layout = self.layout
        layout.operator("curve.subdivide")
        layout.operator("curve.switch_direction")

class VIEW3D_MT_EditCurveSpecials(bpy.types.Menu):
    bl_label = "Specials"

    def draw(self, context):
        layout = self.layout
        layout.operator("curve.subdivide")
        layout.operator("curve.switch_direction")
        layout.operator("curve.spline_weight_set")
        layout.operator("curve.radius_set")
        layout.operator("curve.smooth")
        layout.operator("curve.smooth_weight")
        layout.operator("curve.smooth_radius")
        layout.operator("curve.smooth_tilt")

############ Armature Menu's #########


class VIEW3D_MT_Edit_Armature(bpy.types.Menu):
    bl_label = "Armature"

    def draw(self, context):
        layout = self.layout

        edit_object = context.edit_object
        arm = edit_object.data
        toolsettings = context.tool_settings

        layout.prop_menu_enum(toolsettings, "proportional_edit", icon="PROP_CON")
        layout.prop_menu_enum(toolsettings, "proportional_edit_falloff", icon="SMOOTHCURVE")
        layout.menu("VIEW3D_MT_bone_options_toggle", text="Bone Settings")
        layout.operator("armature.merge")
        layout.operator("armature.fill")
        layout.operator("armature.split")
        layout.operator("armature.separate")
        layout.operator("armature.switch_direction", text="Switch Direction")
        layout.operator_context = 'EXEC_AREA'
        layout.operator("armature.symmetrize")
        layout.operator("armature.delete")
        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("armature.armature_layers")
        layout.operator("armature.bone_layers")

class VIEW3D_MT_EditArmatureTK(bpy.types.Menu):
    bl_label = "Armature Tools"

    def draw(self, context):
        layout = self.layout
        layout.operator("armature.subdivide", text="Subdivide")
        layout.operator("armature.extrude_move")
        layout.operator("armature.extrude_forked")
        layout.operator("armature.duplicate_move")
        layout.menu("VIEW3D_MT_edit_armature_delete")
        layout.operator("transform.transform",
                        text="Scale Envelope Distance").mode = 'BONE_SIZE'
        layout.operator("transform.transform",
                        text="Scale B-Bone Width").mode = 'BONE_SIZE'

############ Armature Pose Menu's #########

class VIEW3D_MT_Pose(bpy.types.Menu):
    bl_label = "Pose"

    def draw(self, context):
        layout = self.layout

        layout.menu("VIEW3D_MT_object_animation")
        layout.menu("VIEW3D_MT_pose_slide")
        layout.menu("VIEW3D_MT_pose_propagate")
        layout.menu("VIEW3D_MT_pose_library")
        layout.menu("VIEW3D_MT_pose_motion")
        layout.menu("VIEW3D_MT_pose_group")
        layout.menu("VIEW3D_MT_object_parent")
        layout.menu("VIEW3D_MT_pose_ik")
        layout.menu("VIEW3D_MT_pose_constraints")
        layout.menu("VIEW3D_MT_PoseNames")
        layout.operator("pose.quaternions_flip")
        layout.operator_context = 'INVOKE_AREA'
        layout.operator("armature.armature_layers", text="Change Armature Layers...")
        layout.operator("pose.bone_layers", text="Change Bone Layers...")
        layout.menu("VIEW3D_MT_pose_showhide")
        layout.menu("VIEW3D_MT_bone_options_toggle", text="Bone Settings")

############ Transform Menu's #########

class VIEW3D_MT_TransformMenu(bpy.types.Menu):
    bl_label = "Transform"

    def draw(self, context):
        layout = self.layout
        layout.menu("VIEW3D_MT_ManipulatorMenu1")
        layout.menu("VIEW3D_MT_object_clear")
        layout.menu("VIEW3D_MT_object_apply")
        layout.operator("transform.translate", text="Grab/Move")
        layout.operator("transform.rotate", text="Rotate")
        layout.operator("transform.resize", text="Scale")
        layout.operator("transform.translate", text="Move Texture Space").texture_space = True
        layout.operator("transform.resize", text="Scale Texture Space").texture_space = True
        layout.operator("object.randomize_transform")
        layout.operator("transform.tosphere", text="To Sphere")
        layout.operator("transform.shear", text="Shear")
        layout.operator("transform.bend", text="Bend")
        layout.operator("transform.push_pull", text="Push/Pull")
        layout.operator("object.align")
        layout.operator_context = 'EXEC_REGION_WIN'
        layout.operator("transform.transform",
                        text="Align to Transform Orientation").mode = 'ALIGN'

# ********** Edit Mesh Transform **********
class VIEW3D_MT_TransformMenuEdit(bpy.types.Menu):
    bl_label = "Transform"

    def draw(self, context):
        layout = self.layout
        layout.menu("VIEW3D_MT_ManipulatorMenu1")
        layout.operator("transform.translate", text="Grab/Move")
        layout.operator("transform.rotate", text="Rotate")
        layout.operator("transform.resize", text="Scale")
        layout.operator("transform.tosphere", text="To Sphere")
        layout.operator("transform.shear", text="Shear")
        layout.operator("transform.bend", text="Bend")
        layout.operator("transform.push_pull", text="Push/Pull")
        layout.operator("transform.vertex_warp", text="Warp")
        layout.operator("transform.vertex_random", text="Randomize")
        layout.operator("transform.translate", text="Move Texture Space").texture_space = True
        layout.operator("transform.resize", text="Scale Texture Space").texture_space = True
        layout.operator_context = 'EXEC_REGION_WIN'
        layout.operator("transform.transform",
                        text="Align to Transform Orientation").mode = 'ALIGN'
        layout.operator_context = 'EXEC_AREA'
        layout.operator("object.origin_set",
                        text="Geometry to Origin").type = 'GEOMETRY_ORIGIN'

# ********** Transform Lite/Short **********
class VIEW3D_MT_TransformMenuLite(bpy.types.Menu):
    bl_label = "Transform"

    def draw(self, context):
        layout = self.layout
        layout.menu("VIEW3D_MT_ManipulatorMenu1")
        layout.menu("VIEW3D_MT_object_clear")
        layout.menu("VIEW3D_MT_object_apply")
        layout.operator("transform.translate", text="Grab/Move")
        layout.operator("transform.rotate", text="Rotate")
        layout.operator("transform.resize", text="Scale")
        layout.operator("transform.transform",
                        text="Align to Transform Orientation").mode = 'ALIGN'

# ********** Transform Camera **********
class VIEW3D_MT_TransformMenuCamera(bpy.types.Menu):
    bl_label = "Transform"

    def draw(self, context):
        layout.menu("VIEW3D_MT_ManipulatorMenu1")
        layout.menu("VIEW3D_MT_object_clear")
        layout.menu("VIEW3D_MT_object_apply")
        layout.operator("transform.translate", text="Grab/Move")
        layout.operator("transform.rotate", text="Rotate")
        layout.operator("transform.resize", text="Scale")
        layout.operator("object.align")
        layout.operator_context = 'EXEC_REGION_WIN'
        layout.operator("transform.transform",
                        text="Align to Transform Orientation").mode = 'ALIGN'

# ********** Transform Armature  **********
class VIEW3D_MT_TransformMenuArmature(bpy.types.Menu):
    bl_label = "Transform"

    def draw(self, context):
        layout = self.layout
        layout.menu("VIEW3D_MT_ManipulatorMenu1")
        layout.operator("transform.translate", text="Grab/Move")
        layout.operator("transform.rotate", text="Rotate")
        layout.operator("transform.resize", text="Scale")
        layout.operator("armature.align")
        layout.operator("object.align")
        layout.operator_context = 'EXEC_AREA'
        layout.operator("object.origin_set",
                        text="Geometry to Origin").type = 'GEOMETRY_ORIGIN'
        layout.operator("object.origin_set",
                        text="Origin to Geometry").type = 'ORIGIN_GEOMETRY'
        layout.operator("object.origin_set",
                        text="Origin to 3D Cursor").type = 'ORIGIN_CURSOR'
        layout.operator("object.origin_set",
                        text="Origin to Center of Mass").type = 'ORIGIN_CENTER_OF_MASS'

# ********** Transform Armature Edit **********
class VIEW3D_MT_TransformMenuArmatureEdit(bpy.types.Menu):
    bl_label = "Transform"

    def draw(self, context):
        layout = self.layout
        layout.menu("VIEW3D_MT_ManipulatorMenu1")
        layout.operator("transform.translate", text="Grab/Move")
        layout.operator("transform.rotate", text="Rotate")
        layout.operator("transform.resize", text="Scale")
        layout.operator("transform.tosphere", text="To Sphere")
        layout.operator("transform.shear", text="Shear")
        layout.operator("transform.bend", text="Bend")
        layout.operator("transform.push_pull", text="Push/Pull")
        layout.operator("transform.vertex_warp", text="Warp")
        layout.operator("transform.vertex_random", text="Randomize")
        layout.operator("armature.align")
        layout.operator_context = 'EXEC_AREA'

# ********** Transform Armature Pose **********
class VIEW3D_MT_TransformMenuArmaturePose(bpy.types.Menu):
    bl_label = "Transform"

    def draw(self, context):
        layout = self.layout
        layout.menu("VIEW3D_MT_ManipulatorMenu1")
        layout.operator("transform.translate", text="Grab/Move")
        layout.operator("transform.rotate", text="Rotate")
        layout.operator("transform.resize", text="Scale")
        layout.separator()
        layout.operator("pose.transforms_clear", text="Clear All")
        layout.operator("pose.loc_clear", text="Location")
        layout.operator("pose.rot_clear", text="Rotation")
        layout.operator("pose.scale_clear", text="Scale")

        layout.separator()

        layout.operator("pose.user_transforms_clear", text="Reset unkeyed")
        obj = context.object
        if obj.type == 'ARMATURE' and obj.mode in {'EDIT', 'POSE'}:
            if obj.data.draw_type == 'BBONE':
                layout.operator("transform.transform", text="Scale BBone").mode = 'BONE_SIZE'
            elif obj.data.draw_type == 'ENVELOPE':
                layout.operator("transform.transform", text="Scale Envelope Distance").mode = 'BONE_SIZE'
                layout.operator("transform.transform", text="Scale Radius").mode = 'BONE_ENVELOPE'

############ View Menu's #########

class VIEW3D_MT_View_Directions(bpy.types.Menu):
    bl_label = "Directions"

    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.viewnumpad", text="Camera").type = 'CAMERA'
        layout.operator("view3d.viewnumpad", text="Top").type = 'TOP'
        layout.operator("view3d.viewnumpad", text="Bottom").type = 'BOTTOM'
        layout.operator("view3d.viewnumpad", text="Front").type = 'FRONT'
        layout.operator("view3d.viewnumpad", text="Back").type = 'BACK'
        layout.operator("view3d.viewnumpad", text="Right").type = 'RIGHT'
        layout.operator("view3d.viewnumpad", text="Left").type = 'LEFT'

class VIEW3D_MT_View_Border(bpy.types.Menu):
    bl_label = "Set Border"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("view3d.clip_border", text="Clipping Border...")
        layout.operator("view3d.zoom_border", text="Zoom Border...")
        layout.operator("view3d.render_border", text="Render Border...").camera_only = False

class VIEW3D_MT_View_Toggle(bpy.types.Menu):
    bl_label = "View Toggle"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("screen.area_dupli")
        layout.operator("screen.region_quadview")
        layout.operator("screen.screen_full_area", text="Toggle Maximize Area")
        layout.operator("screen.screen_full_area").use_hide_panels = True


class VIEW3D_MT_View_Menu(bpy.types.Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout
        layout.menu("VIEW3D_MT_view_cameras", text="Cameras")
        layout.menu("VIEW3D_MT_View_Directions")
        layout.menu("VIEW3D_MT_View_Navigation")
        layout.menu("VIEW3D_MT_Shade")
        layout.menu("VIEW3D_MT_View_Align")
        layout.menu("VIEW3D_MT_View_Toggle")
        layout.operator("view3d.view_persportho")
        layout.operator("view3d.localview", text="View Global/Local")
        layout.operator("view3d.view_selected").use_all_regions = False
        layout.operator("view3d.view_all").center = False
        layout.menu("VIEW3D_MT_View_Border")
        layout.operator("screen.area_dupli")
        layout.operator("view3d.layers", text="Show All Layers").nr = 0
        layout.operator("screen.animation_play", text="Playback Animation")

class VIEW3D_MT_View_Navigation(bpy.types.Menu):
    bl_label = "Navigation"

    def draw(self, context):
        from math import pi
        layout = self.layout
        layout.operator_enum("view3d.view_orbit", "type")
        props = layout.operator("view3d.view_orbit", "Orbit Opposite")
        props.type = 'ORBITRIGHT'
        props.angle = pi

        layout.operator("view3d.view_roll", text="Roll Left").type = 'LEFT'
        layout.operator("view3d.view_roll", text="Roll Right").type = 'RIGHT'
        layout.operator_enum("view3d.view_pan", "type")
        layout.operator("view3d.zoom", text="Zoom In").delta = 1
        layout.operator("view3d.zoom", text="Zoom Out").delta = -1
        layout.operator("view3d.zoom_camera_1_to_1", text="Zoom Camera 1:1")
        layout.operator("view3d.fly")
        layout.operator("view3d.walk")

class VIEW3D_MT_View_Align(bpy.types.Menu):
    bl_label = "Align View"

    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.view_all", text="Center Cursor and View All").center = True
        layout.operator("view3d.camera_to_view", text="Align Active Camera to View")
        layout.operator("view3d.camera_to_view_selected", text="Align Active Camera to Selected")
        layout.operator("view3d.view_selected")
        layout.operator("view3d.view_center_cursor")
        layout.operator("view3d.view_lock_to_active")
        layout.operator("view3d.view_lock_clear")

class VIEW3D_MT_View_Align_Selected(bpy.types.Menu):
    bl_label = "Align View to Active"

    def draw(self, context):
        layout = self.layout
        props = layout.operator("view3d.viewnumpad", text="Top")
        props.align_active = True
        props.type = 'TOP'
        props = layout.operator("view3d.viewnumpad", text="Bottom")
        props.align_active = True
        props.type = 'BOTTOM'
        props = layout.operator("view3d.viewnumpad", text="Front")
        props.align_active = True
        props.type = 'FRONT'
        props = layout.operator("view3d.viewnumpad", text="Back")
        props.align_active = True
        props.type = 'BACK'
        props = layout.operator("view3d.viewnumpad", text="Right")
        props.align_active = True
        props.type = 'RIGHT'
        props = layout.operator("view3d.viewnumpad", text="Left")
        props.align_active = True
        props.type = 'LEFT'

class VIEW3D_MT_View_Cameras(bpy.types.Menu):
    bl_label = "Cameras"

    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.object_as_camera")
        layout.operator("view3d.viewnumpad", text="Active Camera").type = 'CAMERA'
		
class VIEW3D_MT_Shade(Menu):
    bl_label = "Shade"

    def draw(self, context):
        layout = self.layout

        layout.prop(context.space_data, "viewport_shade", expand=True)

        if context.active_object:
            if(context.mode == 'EDIT_MESH'):
                layout.operator("MESH_OT_faces_shade_smooth")
                layout.operator("MESH_OT_faces_shade_flat")
            else:
                layout.operator("OBJECT_OT_shade_smooth")
                layout.operator("OBJECT_OT_shade_flat")

############ Select Menu's #########

## Object Select ##
class VIEW3D_MT_Select_Object(bpy.types.Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("view3d.select_border")
        layout.operator("view3d.select_circle")
        layout.operator("object.select_all").action = 'TOGGLE'
        layout.operator("object.select_all", text="Inverse").action = 'INVERT'
        layout.operator("object.select_random", text="Random")
        layout.operator("object.select_mirror", text="Mirror")
        layout.operator("object.select_by_layer", text="Select All by Layer")
        layout.operator_menu_enum("object.select_by_type", "type",
                                  text="Select All by Type...")
        layout.operator("object.select_camera", text="Select Camera")
        layout.operator_menu_enum("object.select_grouped", "type",
                                  text="Grouped")
        layout.operator_menu_enum("object.select_linked", "type",
                                  text="Linked")
        layout.operator("object.select_pattern", text="Select Pattern...")
        layout.menu("VIEW3D_MT_Select_Object_More_Less", text="More/Less")

class VIEW3D_MT_Select_Object_More_Less(bpy.types.Menu):
    bl_label = "Select More/Less"

    def draw(self, context):
        layout = self.layout
        layout.operator("object.select_more", text="More")
        layout.operator("object.select_less", text="Less")
        props = layout.operator("object.select_hierarchy", text="Parent")
        props.extend = False
        props.direction = 'PARENT'
        props = layout.operator("object.select_hierarchy", text="Child")
        props.extend = False
        props.direction = 'CHILD'
        props = layout.operator("object.select_hierarchy", text="Extend Parent")
        props.extend = True
        props.direction = 'PARENT'
        props = layout.operator("object.select_hierarchy", text="Extend Child")
        props.extend = True
        props.direction = 'CHILD'

## Edit Select ##
class VIEW3D_MT_Select_Edit_Mesh(bpy.types.Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.select_border")
        layout.operator("view3d.select_circle")
        layout.operator("mesh.select_all").action = 'TOGGLE'
        layout.operator("mesh.select_all", text="Inverse").action = 'INVERT'
        layout.operator("mesh.select_linked", text="Linked")
        layout.operator("mesh.faces_select_linked_flat",
                        text="Linked Flat Faces")
        layout.operator("mesh.select_random", text="Random")
        layout.operator("mesh.select_nth", text="Every N Number of Verts")
        layout.menu("VIEW3D_MT_Edit_Mesh_Select_Trait")
        layout.menu("VIEW3D_MT_Edit_Mesh_Select_Similar")
        layout.menu("VIEW3D_MT_Edit_Mesh_Select_More_Less")
        layout.operator("mesh.select_mirror", text="Mirror")
        layout.operator("mesh.edges_select_sharp", text="Sharp Edges")
        layout.operator("mesh.select_axis", text="Side of Active")
        layout.operator("mesh.shortest_path_select", text="Shortest Path")
        layout.operator("mesh.loop_multi_select", text="Edge Loops").ring = False
        layout.operator("mesh.loop_multi_select", text="Edge Rings").ring = True
        layout.operator("mesh.loop_to_region")
        layout.operator("mesh.region_to_loop")

class VIEW3D_MT_Edit_Mesh_Select_Similar(bpy.types.Menu):
    bl_label = "Select Similar"

    def draw(self, context):
        layout = self.layout
        layout.operator_enum("mesh.select_similar", "type")
        layout.operator("mesh.select_similar_region", text="Face Regions")

class VIEW3D_MT_Edit_Mesh_Select_Trait(bpy.types.Menu):
    bl_label = "Select All by Trait"

    def draw(self, context):
        layout = self.layout
        if context.scene.tool_settings.mesh_select_mode[2] is False:
            layout.operator("mesh.select_non_manifold", text="Non Manifold")
        layout.operator("mesh.select_loose", text="Loose Geometry")
        layout.operator("mesh.select_interior_faces", text="Interior Faces")
        layout.operator("mesh.select_face_by_sides", text="By Number of Verts")
        layout.operator("mesh.select_ungrouped", text="Ungrouped Verts")

class VIEW3D_MT_Edit_Mesh_Select_More_Less(bpy.types.Menu):
    bl_label = "Select More/Less"

    def draw(self, context):
        layout = self.layout
        layout.operator("mesh.select_more", text="More")
        layout.operator("mesh.select_less", text="Less")
        layout.operator("mesh.select_next_item", text="Next Active")
        layout.operator("mesh.select_prev_item", text="Previous Active")

## Edit Curve Select ##
class VIEW3D_MT_Select_Edit_Curve(bpy.types.Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.select_border")
        layout.operator("view3d.select_circle")
        layout.operator("curve.select_all").action = 'TOGGLE'
        layout.operator("curve.select_all", text="Inverse").action = 'INVERT'
        layout.operator("curve.select_random")
        layout.operator("curve.select_nth")
        layout.operator("curve.select_linked", text="Select Linked")
        layout.operator("curve.select_similar", text="Select Similar")
        layout.operator("curve.de_select_first")
        layout.operator("curve.de_select_last")
        layout.operator("curve.select_next")
        layout.operator("curve.select_previous")
        layout.operator("curve.select_more")
        layout.operator("curve.select_less")

## Armature Select ##
class VIEW3D_MT_SelectArmatureMenu(bpy.types.Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.select_border")
        layout.operator("armature.select_all")
        layout.operator("armature.select_inverse", text="Inverse")
        layout.operator("armature.select_hierarchy",
                        text="Parent").direction = 'PARENT'
        layout.operator("armature.select_hierarchy",
                        text="Child").direction = 'CHILD'
        props = layout.operator("armature.select_hierarchy",
                                text="Extend Parent")
        props.extend = True
        props.direction = 'PARENT'
        props = layout.operator("armature.select_hierarchy",
                                text="Extend Child")
        props.extend = True
        props.direction = 'CHILD'
        layout.operator("object.select_pattern", text="Select Pattern...")

class VIEW3D_MT_Select_Edit_Armature(bpy.types.Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        layout.operator("view3d.select_border")
        layout.operator("view3d.select_circle")

        layout.separator()

        layout.operator("armature.select_all").action = 'TOGGLE'
        layout.operator("armature.select_all", text="Inverse").action = 'INVERT'
        layout.operator("armature.select_mirror", text="Mirror").extend = False

        layout.separator()

        layout.operator("armature.select_more", text="More")
        layout.operator("armature.select_less", text="Less")

        layout.separator()

        props = layout.operator("armature.select_hierarchy", text="Parent")
        props.extend = False
        props.direction = 'PARENT'

        props = layout.operator("armature.select_hierarchy", text="Child")
        props.extend = False
        props.direction = 'CHILD'

        layout.separator()

        props = layout.operator("armature.select_hierarchy", text="Extend Parent")
        props.extend = True
        props.direction = 'PARENT'

        props = layout.operator("armature.select_hierarchy", text="Extend Child")
        props.extend = True
        props.direction = 'CHILD'

        layout.operator_menu_enum("armature.select_similar", "type", text="Similar")
        layout.operator("object.select_pattern", text="Select Pattern...")

class VIEW3D_MT_Select_Pose(bpy.types.Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.select_border")
        layout.operator("view3d.select_circle")
        layout.operator("pose.select_all").action = 'TOGGLE'
        layout.operator("pose.select_all", text="Inverse").action = 'INVERT'
        layout.operator("pose.select_mirror", text="Flip Active")
        layout.operator("pose.select_constraint_target",
                        text="Constraint Target")
        layout.operator("pose.select_linked", text="Linked")
        layout.operator("pose.select_hierarchy",
                        text="Parent").direction = 'PARENT'
        layout.operator("pose.select_hierarchy",
                        text="Child").direction = 'CHILD'
        props = layout.operator("pose.select_hierarchy", text="Extend Parent")
        props.extend = True
        props.direction = 'PARENT'
        props = layout.operator("pose.select_hierarchy", text="Extend Child")
        props.extend = True
        props.direction = 'CHILD'
        layout.operator_menu_enum("pose.select_grouped", "type",
                                  text="Grouped")
        layout.operator("object.select_pattern", text="Select Pattern...")
        layout.menu("VIEW3D_MT_select_pose_more_less")

class VIEW3D_MT_Select_Pose_More_Less(bpy.types.Menu):
    bl_label = "Select More/Less"

    def draw(self, context):
        layout = self.layout
        props = layout.operator("pose.select_hierarchy", text="Parent")
        props.extend = False
        props.direction = 'PARENT'

        props = layout.operator("pose.select_hierarchy", text="Child")
        props.extend = False
        props.direction = 'CHILD'

        props = layout.operator("pose.select_hierarchy", text="Extend Parent")
        props.extend = True
        props.direction = 'PARENT'

        props = layout.operator("pose.select_hierarchy", text="Extend Child")
        props.extend = True
        props.direction = 'CHILD'

class VIEW3D_MT_PoseCopy(bpy.types.Menu):
    bl_label = "Pose Copy"

    def draw(self, context):
        layout = self.layout
        layout.operator("pose.copy")
        layout.operator("pose.paste")
        layout.operator("pose.paste",
                        text="Paste X-Flipped Pose").flipped = True

class VIEW3D_MT_PoseNames(bpy.types.Menu):
    bl_label = "Pose Names"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'EXEC_AREA'
        layout.operator("pose.autoside_names",
                        text="AutoName Left/Right").axis = 'XAXIS'
        layout.operator("pose.autoside_names",
                        text="AutoName Front/Back").axis = 'YAXIS'
        layout.operator("pose.autoside_names",
                        text="AutoName Top/Bottom").axis = 'ZAXIS'
        layout.operator("pose.flip_names")

## Surface Select ##
class VIEW3D_MT_Select_Edit_Surface(bpy.types.Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.select_border")
        layout.operator("view3d.select_circle")
        layout.operator("curve.select_all").action = 'TOGGLE'
        layout.operator("curve.select_all", text="Inverse").action = 'INVERT'
        layout.operator("curve.select_random")
        layout.operator("curve.select_nth")
        layout.operator("curve.select_linked", text="Select Linked")
        layout.operator("curve.select_similar", text="Select Similar")
        layout.operator("curve.select_row")
        layout.operator("curve.select_more")
        layout.operator("curve.select_less")

## Metaball Select ##
class VIEW3D_MT_SelectMetaball(bpy.types.Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.select_border")
        layout.operator("mball.select_all").action = 'TOGGLE'
        layout.operator("mball.select_all").action = 'INVERT'
        layout.operator("mball.select_random_metaelems")

class VIEW3D_MT_Select_Edit_Metaball(bpy.types.Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.select_border")
        layout.operator("view3d.select_circle")
        layout.operator("mball.select_all").action = 'TOGGLE'
        layout.operator("mball.select_all", text="Inverse").action = 'INVERT'
        layout.operator("mball.select_random_metaelems")
        layout.operator_menu_enum("mball.select_similar", "type", text="Similar")

## Particle Select ##
class VIEW3D_MT_Select_Particle(bpy.types.Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        layout.operator("view3d.select_border")

        layout.separator()

        layout.operator("particle.select_all").action = 'TOGGLE'
        layout.operator("particle.select_linked")
        layout.operator("particle.select_all", text="Inverse").action = 'INVERT'

        layout.separator()

        layout.operator("particle.select_more")
        layout.operator("particle.select_less")

        layout.separator()

        layout.operator("particle.select_random")

        layout.separator()

        layout.operator("particle.select_roots", text="Roots")
        layout.operator("particle.select_tips", text="Tips")

## Lattice Edit Select ##
class VIEW3D_MT_Select_Edit_Lattice(bpy.types.Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        layout.operator("view3d.select_border")
        layout.operator("view3d.select_circle")
        layout.operator("lattice.select_mirror")
        layout.operator("lattice.select_random")
        layout.operator("lattice.select_all").action = 'TOGGLE'
        layout.operator("lattice.select_all", text="Inverse").action = 'INVERT'
        layout.operator("lattice.select_ungrouped", text="Ungrouped Verts")

## Grease Pencil Select ##
class VIEW3D_MT_Select_Gpencil(bpy.types.Menu):
    # To Do: used in 3dview header might work if mapped to mouse
    # Not in Class List yet
    bl_label = "Select"
    
    def draw(self, context):
        layout = self.layout

        layout.operator("gpencil.select_border")
        layout.operator("gpencil.select_circle")

        layout.separator()

        layout.operator("gpencil.select_all", text="(De)select All").action = 'TOGGLE'
        layout.operator("gpencil.select_all", text="Inverse").action = 'INVERT'
        layout.operator("gpencil.select_linked", text="Linked")
        #layout.operator_menu_enum("gpencil.select_grouped", "type", text="Grouped")
        layout.operator("gpencil.select_grouped", text="Grouped")

        layout.separator()

        layout.operator("gpencil.select_more")
        layout.operator("gpencil.select_less")

## Text Select ##
class VIEW3D_MT_Select_Edit_Text(bpy.types.Menu):
    # To Do: used in 3dview header might work if mapped to mouse
    # Not in Class List yet
    bl_label = "Edit"

    def draw(self, context):
        layout = self.layout
        layout.operator("font.text_copy", text="Copy")
        layout.operator("font.text_cut", text="Cut")
        layout.operator("font.text_paste", text="Paste")
        layout.operator("font.text_paste_from_file")
        layout.operator("font.select_all")

## Paint Mode Menus ##
class VIEW3D_MT_Select_Paint_Mask(bpy.types.Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.select_border")
        layout.operator("view3d.select_circle")
        layout.operator("paint.face_select_all").action = 'TOGGLE'
        layout.operator("paint.face_select_all", text="Inverse").action = 'INVERT'
        layout.operator("paint.face_select_linked", text="Linked")


class VIEW3D_MT_Select_Paint_Mask_Vertex(bpy.types.Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.select_border")
        layout.operator("view3d.select_circle")
        layout.operator("paint.vert_select_all").action = 'TOGGLE'
        layout.operator("paint.vert_select_all", text="Inverse").action = 'INVERT'
        layout.operator("paint.vert_select_ungrouped", text="Ungrouped Verts")


class VIEW3D_MT_Angle_Control(bpy.types.Menu):
    bl_label = "Angle Control"

    @classmethod
    def poll(cls, context):
        settings = UnifiedPaintPanel.paint_settings(context)
        if not settings:
            return False

        brush = settings.brush
        tex_slot = brush.texture_slot

        return tex_slot.has_texture_angle and tex_slot.has_texture_angle_source

    def draw(self, context):
        layout = self.layout

        settings = UnifiedPaintPanel.paint_settings(context)
        brush = settings.brush

        sculpt = (context.sculpt_object is not None)

        tex_slot = brush.texture_slot

        layout.prop(tex_slot, "use_rake", text="Rake")

        if brush.brush_capabilities.has_random_texture_angle and tex_slot.has_random_texture_angle:
            if sculpt:
                if brush.sculpt_capabilities.has_random_texture_angle:
                    layout.prop(tex_slot, "use_random", text="Random")
            else:
                layout.prop(tex_slot, "use_random", text="Random")


## Cursor Menu Operators ##
class VIEW3D_OT_Pivot_Cursor(bpy.types.Operator):
    "Cursor as Pivot Point"
    bl_idname = "view3d.pivot_cursor"
    bl_label = "Cursor as Pivot Point"

    @classmethod
    def poll(cls, context):
        return bpy.context.space_data.pivot_point != 'CURSOR'

    def execute(self, context):
        bpy.context.space_data.pivot_point = 'CURSOR'
        return {'FINISHED'}

class VIEW3D_OT_Revert_Pivot(bpy.types.Operator):
    "Revert Pivot Point"
    bl_idname = "view3d.revert_pivot"
    bl_label = "Reverts Pivot Point to median"

    @classmethod
    def poll(cls, context):
        return bpy.context.space_data.pivot_point != 'MEDIAN_POINT'

    def execute(self, context):
        bpy.context.space_data.pivot_point = 'MEDIAN_POINT'
        return{'FINISHED'}

## Cursor Edge Intersection Defs ##

def abs(val):
    if val > 0:
        return val
    return -val

def edgeIntersect(context, operator):
    from mathutils.geometry import intersect_line_line

    obj = context.active_object

    if (obj.type != "MESH"):
        operator.report({'ERROR'}, "Object must be a mesh")
        return None

    edges = []
    mesh = obj.data
    verts = mesh.vertices

    is_editmode = (obj.mode == 'EDIT')
    if is_editmode:
        bpy.ops.object.mode_set(mode='OBJECT')

    for e in mesh.edges:
        if e.select:
            edges.append(e)

            if len(edges) > 2:
                break

    if is_editmode:
        bpy.ops.object.mode_set(mode='EDIT')

    if len(edges) != 2:
        operator.report({'ERROR'},
                        "Operator requires exactly 2 edges to be selected")
        return

    line = intersect_line_line(verts[edges[0].vertices[0]].co,
                               verts[edges[0].vertices[1]].co,
                               verts[edges[1].vertices[0]].co,
                               verts[edges[1].vertices[1]].co)

    if line is None:
        operator.report({'ERROR'}, "Selected edges do not intersect")
        return

    point = line[0].lerp(line[1], 0.5)
    context.scene.cursor_location = obj.matrix_world * point

## Cursor Edge Intersection Operator ##
class VIEW3D_OT_CursorToEdgeIntersection(bpy.types.Operator):
    "Finds the mid-point of the shortest distance between two edges"

    bl_idname = "view3d.snap_cursor_to_edge_intersection"
    bl_label = "Cursor to Edge Intersection"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj != None and obj.type == 'MESH'

    def execute(self, context):
        edgeIntersect(context, self)
        return {'FINISHED'}

### Set Mode Operator ###

class SetObjectMode(bpy.types.Operator): 
	bl_idname = "object.set_object_mode"
	bl_label = "Set the object interactive mode"
	bl_description = "I set the interactive mode of object"
	bl_options = {'REGISTER'}
	
	mode = bpy.props.StringProperty(name="Interactive mode", default="OBJECT")
	
	def execute(self, context):
		if (context.active_object):
			try:
				bpy.ops.object.mode_set(mode=self.mode)
			except TypeError:
				self.report(type={"WARNING"}, message=context.active_object.name+" It is not possible to enter into the interactive mode")
		else:
			self.report(type={"WARNING"}, message="There is no active object")
		return {'FINISHED'}

## Origin To Selected Edit Mode ##
def vfeOrigin(context):
    cursorPositionX = bpy.context.scene.cursor_location[0]
    cursorPositionY = bpy.context.scene.cursor_location[1]
    cursorPositionZ = bpy.context.scene.cursor_location[2]
    bpy.ops.view3d.snap_cursor_to_selected()
    bpy.ops.object.mode_set()
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.cursor_location[0] = cursorPositionX
    bpy.context.scene.cursor_location[1] = cursorPositionY
    bpy.context.scene.cursor_location[2] = cursorPositionZ
    
class SetOriginToSelected(bpy.types.Operator):
    '''Tooltip'''
    bl_idname = "object.setorigintoselected"
    bl_label = "Set Origin to Selected"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        vfeOrigin(context)
        
        
        return {'FINISHED'}

### List The Classes ###

classes = [
    VIEW3D_MT_Space_Dynamic_Menu,
    VIEW3D_MT_AddMenu,
    VIEW3D_MT_Object,
    VIEW3D_MT_Edit_Mesh,
    VIEW3D_MT_TransformMenu,
    VIEW3D_MT_TransformMenuEdit,
    VIEW3D_MT_TransformMenuArmature,
    VIEW3D_MT_TransformMenuArmatureEdit,
    VIEW3D_MT_TransformMenuArmaturePose,
    VIEW3D_MT_TransformMenuLite,
    VIEW3D_MT_TransformMenuCamera,
    VIEW3D_MT_MirrorMenu,
    VIEW3D_MT_ParentMenu,
    VIEW3D_MT_GroupMenu,
    VIEW3D_MT_Select_Object,
    VIEW3D_MT_Select_Object_More_Less,
    VIEW3D_MT_Select_Edit_Mesh,
    VIEW3D_MT_Edit_Mesh_Select_Similar,
    VIEW3D_MT_Edit_Mesh_Select_Trait,
    VIEW3D_MT_Edit_Mesh_Select_More_Less,
    VIEW3D_MT_Select_Edit_Curve,
    VIEW3D_MT_SelectArmatureMenu,
    VIEW3D_MT_Select_Pose,
    VIEW3D_MT_Select_Pose_More_Less,
    VIEW3D_MT_Pose,
    VIEW3D_MT_PoseCopy,
    VIEW3D_MT_PoseNames,
    VIEW3D_MT_Select_Edit_Surface,
    VIEW3D_MT_SelectMetaball,
    VIEW3D_MT_Select_Edit_Metaball,
    VIEW3D_MT_Select_Particle,
    VIEW3D_MT_Select_Edit_Lattice,
    VIEW3D_MT_Select_Edit_Armature,
    VIEW3D_MT_Select_Paint_Mask,
    VIEW3D_MT_Select_Paint_Mask_Vertex,
    VIEW3D_MT_Angle_Control,
    VIEW3D_MT_Edit_Multi,
    VIEW3D_MT_EditM_Edge,
    VIEW3D_MT_Edit_Curve,
    VIEW3D_MT_EditCurveCtrlpoints,
    VIEW3D_MT_EditCurveSegments,
    VIEW3D_MT_EditCurveSpecials,
    VIEW3D_MT_Edit_Armature,
    VIEW3D_MT_EditArmatureTK,
    VIEW3D_MT_KeyframeMenu,
    VIEW3D_OT_Pivot_Cursor,
    VIEW3D_OT_Revert_Pivot,
    VIEW3D_MT_CursorMenu,
    VIEW3D_MT_CursorMenuLite,
    VIEW3D_MT_EditCursorMenu,
    VIEW3D_OT_CursorToEdgeIntersection,
    VIEW3D_MT_UndoS,
    VIEW3D_MT_Camera_Options,
    InteractiveMode,
    InteractiveModeArmature,
    SetObjectMode,
    VIEW3D_MT_View_Directions,
    VIEW3D_MT_View_Border,
    VIEW3D_MT_View_Toggle,
    VIEW3D_MT_View_Menu,
    VIEW3D_MT_View_Navigation,
    VIEW3D_MT_View_Align,
    VIEW3D_MT_View_Align_Selected,
    VIEW3D_MT_View_Cameras,
    VIEW3D_MT_UV_Map,
    VIEW3D_MT_Pivot,
    VIEW3D_Snap_Context,
    VIEW3D_Snap_Origin,
    VIEW3D_MT_Shade,
    VIEW3D_MT_ManipulatorMenu1,
    SetOriginToSelected,
    VIEW3D_MT_Object_Data_Link,
    VIEW3D_MT_Duplicate,
]

## Register Classes ^ & Hotkeys ##

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new('wm.call_menu', 'SPACE', 'PRESS')
        kmi.properties.name = "VIEW3D_MT_Space_Dynamic_Menu"

## Unegister Classes & Hotkeys ##

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps['3D View']
        for kmi in km.keymap_items:
            if kmi.idname == 'wm.call_menu':
                if kmi.properties.name == "VIEW3D_MT_Space_Dynamic_Menu":
                    km.keymap_items.remove(kmi)
                    break

if __name__ == "__main__":
    register()
