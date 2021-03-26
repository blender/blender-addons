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
Pose Library based on the Asset Browser.
"""

bl_info = {
    "name": "Pose Library",
    "description": "Pose Library based on the Asset Browser.",
    "author": "Sybren A. Stüvel",
    "version": (1, 0),
    "blender": (2, 93, 0),
    "warning": "In heavily development, things may change",
    "location": "Asset Browser -> Animations, and 3D Viewport -> Animation panel",
    # "doc_url": "{BLENDER_MANUAL_URL}/addons/animation/pose_library.html",
    "support": "OFFICIAL",
    "category": "Animation",
}

from typing import List, Tuple

_need_reload = "operators" in locals()
from . import gui, macros, operators

if _need_reload:
    import importlib

    gui = importlib.reload(gui)
    macros = importlib.reload(macros)
    operators = importlib.reload(operators)

import bpy

addon_keymaps: List[Tuple[bpy.types.KeyMap, bpy.types.KeyMapItem]] = []


def register_keymaps() -> None:

    wm = bpy.context.window_manager
    if wm.keyconfigs.addon is None:
        # This happens when Blender is running in the background.
        return

    km = wm.keyconfigs.addon.keymaps.new(
        name="File Browser Main", space_type="FILE_BROWSER"
    )

    # Double-click to apply pose.
    kmi = km.keymap_items.new("poselib.apply_pose_asset", "LEFTMOUSE", "DOUBLE_CLICK")
    addon_keymaps.append((km, kmi))

    # Ctrl-doubleclick to blend pose.
    kmi = km.keymap_items.new(
        "poselib.blend_pose", "LEFTMOUSE", "DOUBLE_CLICK", ctrl=True
    )
    addon_keymaps.append((km, kmi))

    # Alt-doubleclick to select bones.
    kmi = km.keymap_items.new(
        "poselib.select_asset_and_select_bones", "LEFTMOUSE", "DOUBLE_CLICK", alt=True
    )
    addon_keymaps.append((km, kmi))

    # Alt-shift-doubleclick to deselect bones.
    kmi = km.keymap_items.new(
        "poselib.select_asset_and_deselect_bones",
        "LEFTMOUSE",
        "DOUBLE_CLICK",
        alt=True,
        shift=True,
    )
    addon_keymaps.append((km, kmi))


def unregister_keymaps() -> None:
    # Clear shortcuts from the keymap.
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


def register() -> None:
    bpy.types.WindowManager.poselib_apply_flipped = bpy.props.BoolProperty(
        name="Apply Flipped",
        default=True,
    )
    bpy.types.WindowManager.poselib_merge_choices = bpy.props.EnumProperty(
        name="Animation",
        items=[
            ("REPLACE", "Replace", "Overwrite existing keyframes"),
            (
                "INSERT",
                "Insert",
                "Insert the animation segment, pushing existing keyframes down the timeline",
            ),
            ("BLEND", "Blend", "Blend with existing pose"),
        ],
        default="REPLACE",
    )

    # TODO(Sybren): this should be a property of the asset browser itself, not the scene.
    bpy.types.Scene.poselib_follow_active_asset = bpy.props.BoolProperty(
        name="Follow Active Asset",
        default=False,
    )
    operators.register()
    macros.register()
    gui.register()

    register_keymaps()


def unregister() -> None:
    unregister_keymaps()

    gui.unregister()
    macros.unregister()
    operators.unregister()

    try:
        del bpy.types.WindowManager.poselib_apply_flipped
    except AttributeError:
        pass
    try:
        del bpy.types.WindowManager.poselib_merge_choices
    except AttributeError:
        pass
    try:
        del bpy.types.WindowManager.poselib_default_asset_data
    except AttributeError:
        pass
    try:
        del bpy.types.Scene.poselib_follow_active_asset
    except AttributeError:
        pass
