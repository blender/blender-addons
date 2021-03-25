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
Pose Library mockup - operators.
"""

from pathlib import Path
from typing import Any, Optional, Set, Tuple

_need_reload = "functions" in locals()
from . import asset_browser, functions, pose_creation, pose_usage

if _need_reload:
    import importlib

    asset_browser = importlib.reload(asset_browser)
    functions = importlib.reload(functions)
    pose_creation = importlib.reload(pose_creation)
    pose_usage = importlib.reload(pose_usage)


import bpy
from bpy_extras import asset_utils
from bpy.props import (BoolProperty, StringProperty)
from bpy.types import (
    Action,
    Context,
    Object,
    Operator,
)


class ANIM_OT_dummy(Operator):
    bl_idname = "anim.dummy"
    bl_label = "Dummy Operator"
    bl_options = {"REGISTER"}

    def execute(self, context: Context) -> Set[str]:
        return {"CANCELLED"}


class PoseAssetCreator:
    @classmethod
    def poll(cls, context: Context) -> bool:
        return bool(
            # There must be an object.
            context.object
            # It must be in pose mode with selected bones.
            and context.object.mode == "POSE"
            and context.object.pose
            and context.selected_pose_bones_from_active_object
        )


class LocalPoseAssetUser:
    @classmethod
    def poll(cls, context: Context) -> bool:
        return bool(
            isinstance(getattr(context, "id", None), Action)
            and context.object
            and context.object.mode == "POSE"  # This condition may not be desired.
        )


class ANIM_OT_create_pose_asset(PoseAssetCreator, Operator):
    bl_idname = "anim.create_pose_asset"
    bl_label = "Create Pose Asset"
    bl_description = "Create a new Action that contains the pose of the selected bones, and mark it as Asset"
    bl_options = {"REGISTER", "UNDO"}

    pose_name: StringProperty(name="Pose Name")  # type: ignore

    def execute(self, context: Context) -> Set[str]:
        pose_name = self.pose_name or context.object.name
        asset = pose_creation.create_pose_asset_from_context(context, pose_name)
        if not asset:
            self.report({"WARNING"}, "No keyframes were found for this pose")
            return {"CANCELLED"}

        # No longer necessary since rB17534e28ff4.
        # self.render_preview(context, asset)

        # Switch to the newly created Action, i.e. follow the creating-is-editing design of Blender.
        anim_data = context.object.animation_data_create()
        anim_data.action = asset

        asset_browse_area: Optional[bpy.types.Area] = asset_browser.area_for_category(
            context.screen, "ANIMATION"
        )
        if not asset_browse_area:
            return {"FINISHED"}

        # After creating an asset, the window manager has to process the
        # notifiers before editors should be manipulated.

        pose_creation.assign_tags_from_asset_browser(asset, asset_browse_area)

        # Pass deferred=True, because we just created a new asset that isn't
        # known to the Asset Browser space yet. That requires the processing of
        # notifiers, which will only happen after this code has finished
        # running.
        asset_browser.activate_asset(asset, asset_browse_area, deferred=True)

        return {"FINISHED"}

    def render_preview(self, context: Context, asset: Any) -> None:
        image_dblock = pose_creation.render_preview(context)
        temp_preview = Path(bpy.app.tempdir) / "temp_preview.png"
        try:
            image_dblock.save_render(str(temp_preview))
            load_ctx = {
                **context.copy(),
                "id": asset,
            }
            bpy.ops.ed.lib_id_load_custom_preview(load_ctx, filepath=str(temp_preview))
        finally:
            try:
                temp_preview.unlink()
            except FileNotFoundError:
                pass


class ANIM_OT_asset_activate(Operator):
    bl_idname = "anim.asset_activate"
    bl_label = "Focus in Asset Browser"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        return bool(
            context.object
            and context.object.animation_data
            and context.object.animation_data.action
        )

    def execute(self, context: Context) -> Set[str]:
        asset_browser_area = asset_browser.area_for_category(
            context.screen, "ANIMATION"
        )
        if not asset_browser_area:
            self.report({"ERROR"}, "There is no Asset Browser open at the moment")
            return {"CANCELLED"}

        action_asset = context.object.animation_data.action
        asset_browser.activate_asset(action_asset, asset_browser_area, deferred=False)

        return {"FINISHED"}


class ASSET_OT_assign_action(LocalPoseAssetUser, Operator):
    bl_idname = "asset.assign_action"
    bl_label = "Assign Action"
    bl_description = "Set this pose Action as active Action on the active Object"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context) -> Set[str]:
        context.object.animation_data_create().action = context.id
        return {"FINISHED"}


class ANIM_OT_copy_as_asset(PoseAssetCreator, Operator):
    bl_idname = "anim.copy_as_asset"
    bl_label = "Copy Pose As Asset"
    bl_description = "Create a new pose asset on the clipboard, to be pasted into an Asset Browser"
    bl_options = {"REGISTER"}

    CLIPBOARD_ASSET_MARKER = "ASSET-BLEND="

    def execute(self, context: Context) -> Set[str]:
        asset = pose_creation.create_pose_asset_from_context(
            context, new_asset_name=context.object.name
        )
        if asset is None:
            self.report({"WARNING"}, "No animation data found to create asset from")
            return {"CANCELLED"}

        filepath = self.save_datablock(asset)

        functions.asset_clear(context, asset)
        if asset.users > 0:
            self.report({"ERROR"}, "Whaaaat who is using our brand new asset?")
            return {"FINISHED"}

        bpy.data.actions.remove(asset)

        context.window_manager.clipboard = "%s%s" % (
            self.CLIPBOARD_ASSET_MARKER,
            filepath,
        )

        # TODO(Sybren): tag asset browser for refreshing, as now the clipboard
        # contains a pastable asset.
        return {"FINISHED"}

    def save_datablock(self, action: Action) -> Path:
        tempdir = Path(bpy.app.tempdir)
        filepath = tempdir / "copied_asset.blend"
        bpy.data.libraries.write(
            str(filepath),
            datablocks={action},
            path_remap="NONE",
            fake_user=True,
            compress=True,  # Single-datablock blend file, likely little need to diff.
        )
        return filepath


class ASSET_OT_paste_asset(Operator):
    bl_idname = "anim.paste_asset"
    bl_label = "Paste As New Asset"
    bl_description = "Paste the Asset that was previously copied using Copy As Asset"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        clipboard: str = context.window_manager.clipboard
        if not clipboard:
            return False
        marker = ANIM_OT_copy_as_asset.CLIPBOARD_ASSET_MARKER
        return clipboard.startswith(marker)

    def execute(self, context: Context) -> Set[str]:
        clipboard = context.window_manager.clipboard
        marker_len = len(ANIM_OT_copy_as_asset.CLIPBOARD_ASSET_MARKER)
        filepath = Path(clipboard[marker_len:])

        assets = functions.load_assets_from(filepath)
        if not assets:
            self.report({"ERROR"}, "Did not find any assets on clipboard")
            return {"CANCELLED"}

        self.report({"INFO"}, "Pasted %d assets" % len(assets))

        # TODO: Remove the need for refreshing. This should happen automatically
        # when linking/appending assets.
        asset_browser.refresh(context)

        return {"FINISHED"}


class PoseAssetUser:
    @classmethod
    def poll(cls, context: Context) -> bool:
        return bool(
            context.space_data.type == "FILE_BROWSER"
            and context.space_data.browse_mode == "ASSETS"
            and context.space_data.params.asset_library
            and context.space_data.params.filename
            and context.object
            and context.object.mode == "POSE"  # This condition may not be desired.
            and asset_utils.SpaceAssetInfo.get_active_asset(context) is not None
        )

    def execute(self, context: Context) -> Set[str]:
        if context.space_data.params.asset_library == "LOCAL":
            return self.use_pose(context, context.id)
        return self._load_and_use_pose(context)

    def use_pose(self, context: Context, asset: bpy.types.ID) -> Set[str]:
        # Implement in subclass.
        pass

    def _load_and_use_pose(self, context: Context) -> Set[str]:
        asset_load_info = functions.active_asset_load_info(context)
        if asset_load_info.id_type != "Action":
            self.report(  # type: ignore
                {"ERROR"},
                f"Selected asset {asset_load_info.asset_name} is not an Action",
            )
            return {"CANCELLED"}

        with bpy.types.BlendData.temp_data() as temp_data:
            str_path = str(asset_load_info.file_path)
            with temp_data.libraries.load(str_path) as (data_from, data_to):
                data_to.actions = [asset_load_info.asset_name]

            action: Action = data_to.actions[0]
            return self.use_pose(context, action)


class ANIM_OT_pose_asset_apply(PoseAssetUser, Operator):
    bl_idname = "anim.pose_asset_apply"
    bl_label = "Apply Pose"
    bl_description = "Apply the Pose to the currently selected bones"
    bl_options = {"REGISTER", "UNDO"}

    def use_pose(self, context: Context, pose_asset: Action) -> Set[str]:
        arm_object: Object = context.object
        arm_object.pose.apply_pose_from_action(pose_asset)
        return {"FINISHED"}


class ANIM_OT_pose_asset_select_bones(PoseAssetUser, Operator):
    bl_idname = "anim.pose_asset_select_bones"
    bl_label = "Select Bones"
    bl_options = {"REGISTER", "UNDO"}

    select: BoolProperty(name="Select", default=True)  # type: ignore

    def use_pose(self, context: Context, pose_asset: Action) -> Set[str]:
        arm_object: Object = context.object
        pose_usage.select_bones(arm_object, pose_asset, select=self.select)
        verb = "Selected" if self.select else "Deselected"
        self.report({"INFO"}, f"{verb} bones from {pose_asset.name}")
        return {"FINISHED"}


classes = (
    ANIM_OT_asset_activate,
    ANIM_OT_copy_as_asset,
    ANIM_OT_create_pose_asset,
    ANIM_OT_dummy,
    ANIM_OT_pose_asset_apply,
    ANIM_OT_pose_asset_select_bones,
    ASSET_OT_assign_action,
    ASSET_OT_paste_asset,
)

register, unregister = bpy.utils.register_classes_factory(classes)
