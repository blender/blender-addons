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
Pose Library mockup - functions.
"""

import re

from bpy.types import (
    Action,
    Object,
)


def select_bones(arm_object: Object, action: Action, *, select: bool) -> None:
    pose_bone_re = re.compile(r'pose.bones\["([^"]+)"\]')
    pose = arm_object.pose

    for fcurve in action.fcurves:
        data_path: str = fcurve.data_path
        match = pose_bone_re.match(data_path)
        if not match:
            continue

        bone_name = match.group(1)
        try:
            pose_bone = pose.bones[bone_name]
        except KeyError:
            continue

        pose_bone.bone.select = select
