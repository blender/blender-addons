#====================== BEGIN GPL LICENSE BLOCK ======================
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
#======================= END GPL LICENSE BLOCK ========================

# <pep8 compliant>

import bpy
from math import acos
from mathutils import Vector, Matrix
from rigify.utils import MetarigError
from rigify.utils import copy_bone, put_bone
from rigify.utils import connected_children_names
from rigify.utils import strip_org, make_mechanism_name, make_deformer_name


def align_roll(obj, bone1, bone2):
    bone1_e = obj.data.edit_bones[bone1]
    bone2_e = obj.data.edit_bones[bone2]

    bone1_e.roll = 0.0

    # Get the directions the bones are pointing in, as vectors
    y1 = bone1_e.y_axis
    x1 = bone1_e.x_axis
    y2 = bone2_e.y_axis
    x2 = bone2_e.x_axis

    # Get the shortest axis to rotate bone1 on to point in the same direction as bone2
    axis = y1.cross(y2)
    axis.normalize()

    # Angle to rotate on that shortest axis
    angle = y1.angle(y2)

    # Create rotation matrix to make bone1 point in the same direction as bone2
    rot_mat = Matrix.Rotation(angle, 3, axis)

    # Roll factor
    x3 = rot_mat * x1
    dot = x2 * x3
    if dot > 1.0:
        dot = 1.0
    elif dot < -1.0:
        dot = -1.0
    roll = acos(dot)

    # Set the roll
    bone1_e.roll = roll

    # Check if we rolled in the right direction
    x3 = rot_mat * bone1_e.x_axis
    check = x2 * x3

    # If not, reverse
    if check < 0.9999:
        bone1_e.roll = -roll


class Rig:
    """ An FK arm rig, with hinge switch.

    """
    def __init__(self, obj, bone, params):
        """ Gather and validate data about the rig.
            Store any data or references to data that will be needed later on.
            In particular, store references to bones that will be needed, and
            store names of bones that will be needed.
            Do NOT change any data in the scene.  This is a gathering phase only.

        """
        self.obj = obj
        self.params = params

        # Get the chain of 3 connected bones
        self.org_bones = [bone] + connected_children_names(self.obj, bone)[:2]

        if len(self.org_bones) != 3:
            raise MetarigError("RIGIFY ERROR: Bone '%s': input to rig type must be a chain of 3 bones" % (strip_org(bone)))

        # Get rig parameters
        self.use_upper_arm_twist = params.use_upper_arm_twist
        self.use_forearm_twist = params.use_forearm_twist

    def generate(self):
        """ Generate the rig.
            Do NOT modify any of the original bones, except for adding constraints.
            The main armature should be selected and active before this is called.

        """
        bpy.ops.object.mode_set(mode='EDIT')

        # Create upper arm bones
        if self.use_upper_arm_twist:
            uarm1 = copy_bone(self.obj, self.org_bones[0], make_deformer_name(strip_org(self.org_bones[0] + ".01")))
            uarm2 = copy_bone(self.obj, self.org_bones[0], make_deformer_name(strip_org(self.org_bones[0] + ".02")))
            utip = copy_bone(self.obj, self.org_bones[0], make_mechanism_name(strip_org(self.org_bones[0] + ".tip")))
        else:
            uarm = copy_bone(self.obj, self.org_bones[0], make_deformer_name(strip_org(self.org_bones[0])))

        # Create forearm bones
        if self.use_forearm_twist:
            farm1 = copy_bone(self.obj, self.org_bones[1], make_deformer_name(strip_org(self.org_bones[1] + ".01")))
            farm2 = copy_bone(self.obj, self.org_bones[1], make_deformer_name(strip_org(self.org_bones[1] + ".02")))
            ftip = copy_bone(self.obj, self.org_bones[1], make_mechanism_name(strip_org(self.org_bones[1] + ".tip")))
        else:
            farm = copy_bone(self.obj, self.org_bones[1], make_deformer_name(strip_org(self.org_bones[1])))

        # Create hand bone
        hand = copy_bone(self.obj, self.org_bones[2], make_deformer_name(strip_org(self.org_bones[2])))

        # Get edit bones
        eb = self.obj.data.edit_bones

        org_uarm_e = eb[self.org_bones[0]]
        if self.use_upper_arm_twist:
            uarm1_e = eb[uarm1]
            uarm2_e = eb[uarm2]
            utip_e = eb[utip]
        else:
            uarm_e = eb[uarm]

        org_farm_e = eb[self.org_bones[1]]
        if self.use_forearm_twist:
            farm1_e = eb[farm1]
            farm2_e = eb[farm2]
            ftip_e = eb[ftip]
        else:
            farm_e = eb[farm]

        org_hand_e = eb[self.org_bones[2]]
        hand_e = eb[hand]

        # Parent and position upper arm bones
        if self.use_upper_arm_twist:
            uarm1_e.use_connect = False
            uarm2_e.use_connect = False
            utip_e.use_connect = False

            uarm1_e.parent = org_uarm_e.parent
            uarm2_e.parent = org_uarm_e
            utip_e.parent = org_uarm_e

            center = Vector((org_uarm_e.head + org_uarm_e.tail) / 2)

            uarm1_e.tail = center
            uarm2_e.head = center
            put_bone(self.obj, utip, org_uarm_e.tail)
            utip_e.length = org_uarm_e.length / 8
        else:
            uarm_e.use_connect = False
            uarm_e.parent = org_uarm_e

        # Parent and position forearm bones
        if self.use_forearm_twist:
            farm1_e.use_connect = False
            farm2_e.use_connect = False
            ftip_e.use_connect = False

            farm1_e.parent = org_farm_e
            farm2_e.parent = org_farm_e
            ftip_e.parent = org_farm_e

            center = Vector((org_farm_e.head + org_farm_e.tail) / 2)

            farm1_e.tail = center
            farm2_e.head = center
            put_bone(self.obj, ftip, org_farm_e.tail)
            ftip_e.length = org_farm_e.length / 8

            # Align roll of farm2 with hand
            align_roll(self.obj, farm2, hand)
        else:
            farm_e.use_connect = False
            farm_e.parent = org_farm_e

        # Parent hand
        hand_e.use_connect = False
        hand_e.parent = org_hand_e

        # Object mode, get pose bones
        bpy.ops.object.mode_set(mode='OBJECT')
        pb = self.obj.pose.bones

        if self.use_upper_arm_twist:
            uarm1_p = pb[uarm1]
        if self.use_forearm_twist:
            farm2_p = pb[farm2]
        # hand_p = pb[hand]  # UNUSED

        # Upper arm constraints
        if self.use_upper_arm_twist:
            con = uarm1_p.constraints.new('COPY_LOCATION')
            con.name = "copy_location"
            con.target = self.obj
            con.subtarget = self.org_bones[0]

            con = uarm1_p.constraints.new('COPY_SCALE')
            con.name = "copy_scale"
            con.target = self.obj
            con.subtarget = self.org_bones[0]

            con = uarm1_p.constraints.new('DAMPED_TRACK')
            con.name = "track_to"
            con.target = self.obj
            con.subtarget = utip

        # Forearm constraints
        if self.use_forearm_twist:
            con = farm2_p.constraints.new('COPY_ROTATION')
            con.name = "copy_rotation"
            con.target = self.obj
            con.subtarget = hand

            con = farm2_p.constraints.new('DAMPED_TRACK')
            con.name = "track_to"
            con.target = self.obj
            con.subtarget = ftip
