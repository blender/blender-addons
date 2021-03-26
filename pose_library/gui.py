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

"""
Pose Library mockup GUI definition.
"""

import bpy
from bpy.types import (
    Action,
    Context,
    Panel,
)

from bpy_extras import asset_utils


class VIEW3D_PT_pose_library(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Animation"
    bl_label = "Pose Library"

    def draw(self, context: Context) -> None:
        layout = self.layout

        row = layout.row(align=True)
        row.operator("poselib.create_pose_asset")
        if bpy.types.POSELIB_OT_restore_previous_action.poll(context):
            row.operator("poselib.restore_previous_action", text="", icon='LOOP_BACK')
        row.operator("poselib.copy_as_asset", icon="COPYDOWN", text="")

        if hasattr(layout, "template_asset_view"):
            workspace = context.workspace
            layout.template_asset_view(
                "pose_assets",
                workspace,
                "active_asset_library",
                context.window_manager,
                "pose_assets",
                workspace,
                "active_pose_asset_index",
                filter_id_types={"filter_action"},
            )


class ASSETBROWSER_PT_pose_library_usage(asset_utils.AssetBrowserPanel, Panel):
    bl_region_type = "TOOLS"
    bl_label = "Pose Library"

    def draw(self, context: Context) -> None:
        layout = self.layout
        wm = context.window_manager

        col = layout.column(align=True)
        col.label(text="Use Pose Asset")
        col.prop(wm, "poselib_apply_flipped")
        props = col.operator("poselib.apply_pose_asset")
        props.apply_flipped = wm.poselib_apply_flipped
        props = col.operator("poselib.blend_pose_asset")
        props.apply_flipped = wm.poselib_apply_flipped

        row = col.row(align=True)
        row.operator("poselib.pose_asset_select_bones", text="Select", icon="BONE_DATA").select = True
        row.operator("poselib.pose_asset_select_bones", text="Deselect").select = False


class ASSETBROWSER_PT_pose_library_editing(asset_utils.AssetBrowserPanel, Panel):
    bl_region_type = "TOOL_PROPS"
    bl_label = "Pose Library"

    def draw(self, context: Context) -> None:
        layout = self.layout

        col = layout.column(align=True)
        col.enabled = bpy.types.ASSET_OT_assign_action.poll(context)
        col.label(text="Activate & Edit")
        col.operator("asset.assign_action")

        # Creation
        col = layout.column(align=True)
        col.enabled = bpy.types.ANIM_OT_paste_asset.poll(context)
        col.label(text="Create Pose Asset")
        col.operator("poselib.paste_asset", icon="PASTEDOWN")


class DOPESHEET_PT_asset_panel(Panel):
    bl_space_type = "DOPESHEET_EDITOR"
    bl_region_type = "UI"
    bl_label = "Create Pose Asset"

    def draw(self, context: Context) -> None:
        layout = self.layout
        col = layout.column(align=True)
        row = col.row(align=True)
        row.operator("poselib.create_pose_asset")
        if bpy.types.POSELIB_OT_restore_previous_action.poll(context):
            row.operator("poselib.restore_previous_action", text="", icon='LOOP_BACK')
        col.operator("poselib.copy_as_asset", icon="COPYDOWN")


classes = (
    ASSETBROWSER_PT_pose_library_editing,
    ASSETBROWSER_PT_pose_library_usage,
    DOPESHEET_PT_asset_panel,
    VIEW3D_PT_pose_library,
)

register, unregister = bpy.utils.register_classes_factory(classes)
