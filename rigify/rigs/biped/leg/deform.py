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
from rigify.utils import connected_children_names, has_connected_children
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
    """ A leg deform-bone setup.

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

        # Get the chain of 2 connected bones
        leg_bones = [bone] + connected_children_names(self.obj, bone)[:2]

        if len(leg_bones) != 2:
            raise MetarigError("RIGIFY ERROR: Bone '%s': incorrect bone configuration for rig type -- leg bones != 2" % (strip_org(bone)))

        # Get the foot and heel
        foot = None
        heel = None
        for b in self.obj.data.bones[leg_bones[1]].children:
            if b.use_connect is True:
                if len(b.children) >= 1 and has_connected_children(b):
                    foot = b.name
                else:
                    heel = b.name

        if foot is None:
            raise MetarigError("RIGIFY ERROR: Bone '%s': incorrect bone configuration for rig type -- could not find foot bone (that is, a bone with >1 children connected) attached to bone '%s'" % (strip_org(bone), strip_org(shin)))
        if heel is None:
            raise MetarigError("RIGIFY ERROR: Bone '%s': incorrect bone configuration for rig type -- could not find heel bone (that is, a bone with no childrenconnected) attached to bone '%s'" % (strip_org(bone), strip_org(shin)))
        # Get the toe
        toe = None
        for b in self.obj.data.bones[foot].children:
            if b.use_connect is True:
                toe = b.name

        if toe is None:
            raise MetarigError("RIGIFY ERROR: Bone '%s': incorrect bone configuration for rig type -- toe is None" % (strip_org(bone)))

        self.org_bones = leg_bones + [foot, toe, heel]

        # Get rig parameters
        self.use_thigh_twist = params.use_thigh_twist
        self.use_shin_twist = params.use_shin_twist

    def generate(self):
        """ Generate the rig.
            Do NOT modify any of the original bones, except for adding constraints.
            The main armature should be selected and active before this is called.

        """
        bpy.ops.object.mode_set(mode='EDIT')

        # Create upper arm bones
        if self.use_thigh_twist:
            thigh1 = copy_bone(self.obj, self.org_bones[0], make_deformer_name(strip_org(self.org_bones[0] + ".01")))
            thigh2 = copy_bone(self.obj, self.org_bones[0], make_deformer_name(strip_org(self.org_bones[0] + ".02")))
            utip = copy_bone(self.obj, self.org_bones[0], make_mechanism_name(strip_org(self.org_bones[0] + ".tip")))
        else:
            thigh = copy_bone(self.obj, self.org_bones[0], make_deformer_name(strip_org(self.org_bones[0])))

        # Create forearm bones
        if self.use_shin_twist:
            shin1 = copy_bone(self.obj, self.org_bones[1], make_deformer_name(strip_org(self.org_bones[1] + ".01")))
            shin2 = copy_bone(self.obj, self.org_bones[1], make_deformer_name(strip_org(self.org_bones[1] + ".02")))
            stip = copy_bone(self.obj, self.org_bones[1], make_mechanism_name(strip_org(self.org_bones[1] + ".tip")))
        else:
            shin = copy_bone(self.obj, self.org_bones[1], make_deformer_name(strip_org(self.org_bones[1])))

        # Create foot bone
        foot = copy_bone(self.obj, self.org_bones[2], make_deformer_name(strip_org(self.org_bones[2])))

        # Create toe bone
        toe = copy_bone(self.obj, self.org_bones[3], make_deformer_name(strip_org(self.org_bones[3])))

        # Get edit bones
        eb = self.obj.data.edit_bones

        org_thigh_e = eb[self.org_bones[0]]
        if self.use_thigh_twist:
            thigh1_e = eb[thigh1]
            thigh2_e = eb[thigh2]
            utip_e = eb[utip]
        else:
            thigh_e = eb[thigh]

        org_shin_e = eb[self.org_bones[1]]
        if self.use_shin_twist:
            shin1_e = eb[shin1]
            shin2_e = eb[shin2]
            stip_e = eb[stip]
        else:
            shin_e = eb[shin]

        org_foot_e = eb[self.org_bones[2]]
        foot_e = eb[foot]

        org_toe_e = eb[self.org_bones[3]]
        toe_e = eb[toe]

        # Parent and position thigh bones
        if self.use_thigh_twist:
            thigh1_e.use_connect = False
            thigh2_e.use_connect = False
            utip_e.use_connect = False

            thigh1_e.parent = org_thigh_e.parent
            thigh2_e.parent = org_thigh_e
            utip_e.parent = org_thigh_e

            center = Vector((org_thigh_e.head + org_thigh_e.tail) / 2)

            thigh1_e.tail = center
            thigh2_e.head = center
            put_bone(self.obj, utip, org_thigh_e.tail)
            utip_e.length = org_thigh_e.length / 8
        else:
            thigh_e.use_connect = False
            thigh_e.parent = org_thigh_e

        # Parent and position shin bones
        if self.use_shin_twist:
            shin1_e.use_connect = False
            shin2_e.use_connect = False
            stip_e.use_connect = False

            shin1_e.parent = org_shin_e
            shin2_e.parent = org_shin_e
            stip_e.parent = org_shin_e

            center = Vector((org_shin_e.head + org_shin_e.tail) / 2)

            shin1_e.tail = center
            shin2_e.head = center
            put_bone(self.obj, stip, org_shin_e.tail)
            stip_e.length = org_shin_e.length / 8

            # Align roll of shin2 with foot
            align_roll(self.obj, shin2, foot)
        else:
            shin_e.use_connect = False
            shin_e.parent = org_shin_e

        # Parent foot
        foot_e.use_connect = False
        foot_e.parent = org_foot_e

        # Parent toe
        toe_e.use_connect = False
        toe_e.parent = org_toe_e

        # Object mode, get pose bones
        bpy.ops.object.mode_set(mode='OBJECT')
        pb = self.obj.pose.bones

        if self.use_thigh_twist:
            thigh1_p = pb[thigh1]
        if self.use_shin_twist:
            shin2_p = pb[shin2]
        # foot_p = pb[foot]  # UNUSED

        # Thigh constraints
        if self.use_thigh_twist:
            con = thigh1_p.constraints.new('COPY_LOCATION')
            con.name = "copy_location"
            con.target = self.obj
            con.subtarget = self.org_bones[0]

            con = thigh1_p.constraints.new('COPY_SCALE')
            con.name = "copy_scale"
            con.target = self.obj
            con.subtarget = self.org_bones[0]

            con = thigh1_p.constraints.new('DAMPED_TRACK')
            con.name = "track_to"
            con.target = self.obj
            con.subtarget = utip

        # Shin constraints
        if self.use_shin_twist:
            con = shin2_p.constraints.new('COPY_ROTATION')
            con.name = "copy_rotation"
            con.target = self.obj
            con.subtarget = foot

            con = shin2_p.constraints.new('DAMPED_TRACK')
            con.name = "track_to"
            con.target = self.obj
            con.subtarget = stip
