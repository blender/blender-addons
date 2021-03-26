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
from . import gui, keymaps, macros, operators

if _need_reload:
    import importlib

    gui = importlib.reload(gui)
    keymaps = importlib.reload(keymaps)
    macros = importlib.reload(macros)
    operators = importlib.reload(operators)

import bpy

addon_keymaps: List[Tuple[bpy.types.KeyMap, bpy.types.KeyMapItem]] = []


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
    keymaps.register()
    gui.register()


def unregister() -> None:
    gui.unregister()
    keymaps.unregister()
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
