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
from mathutils import Vector
from math import pi, acos
from rigify.utils import MetarigError
from rigify.utils import copy_bone
from rigify.utils import connected_children_names
from rigify.utils import strip_org, make_mechanism_name, insert_before_lr
from rigify.utils import create_widget, create_line_widget, create_sphere_widget
from rna_prop_ui import rna_idprop_ui_prop_get


def angle_on_plane(plane, vec1, vec2):
    """ Return the angle between two vectors projected onto a plane.
    """
    plane.normalize()
    vec1 = vec1 - (plane * (vec1.dot(plane)))
    vec2 = vec2 - (plane * (vec2.dot(plane)))
    vec1.normalize()
    vec2.normalize()

    # Determine the angle
    angle = acos(max(-1.0, min(1.0, vec1.dot(vec2))))

    if angle < 0.00001:  # close enough to zero that sign doesn't matter
        return angle

    # Determine the sign of the angle
    vec3 = vec2.cross(vec1)
    vec3.normalize()
    sign = vec3.dot(plane)
    if sign >= 0:
        sign = 1
    else:
        sign = -1

    return angle * sign


class Rig:
    """ An IK arm rig, with an optional ik/fk switch.

    """
    def __init__(self, obj, bone, params, ikfk_switch=False):
        """ Gather and validate data about the rig.
            Store any data or references to data that will be needed later on.
            In particular, store references to bones that will be needed, and
            store names of bones that will be needed.
            Do NOT change any data in the scene.  This is a gathering phase only.

            ikfk_switch: if True, create an ik/fk switch slider
        """
        self.obj = obj
        self.params = params
        self.switch = ikfk_switch

        # Get the chain of 3 connected bones
        self.org_bones = [bone] + connected_children_names(self.obj, bone)[:2]

        if len(self.org_bones) != 3:
            raise MetarigError("RIGIFY ERROR: Bone '%s': input to rig type must be a chain of 3 bones" % (strip_org(bone)))

        # Get the rig parameters
        if params.separate_ik_layers:
            self.layers = list(params.ik_layers)
        else:
            self.layers = None

        self.bend_hint = params.bend_hint

        self.primary_rotation_axis = params.primary_rotation_axis

    def generate(self):
        """ Generate the rig.
            Do NOT modify any of the original bones, except for adding constraints.
            The main armature should be selected and active before this is called.

        """
        bpy.ops.object.mode_set(mode='EDIT')

        # Create the bones
        uarm = copy_bone(self.obj, self.org_bones[0], make_mechanism_name(strip_org(insert_before_lr(self.org_bones[0], "_ik"))))
        farm = copy_bone(self.obj, self.org_bones[1], make_mechanism_name(strip_org(insert_before_lr(self.org_bones[1], "_ik"))))

        hand = copy_bone(self.obj, self.org_bones[2], strip_org(insert_before_lr(self.org_bones[2], "_ik")))
        pole = copy_bone(self.obj, self.org_bones[0], strip_org(insert_before_lr(self.org_bones[0], "_pole")))

        vishand = copy_bone(self.obj, self.org_bones[2], "VIS-" + strip_org(insert_before_lr(self.org_bones[2], "_ik")))
        vispole = copy_bone(self.obj, self.org_bones[1], "VIS-" + strip_org(insert_before_lr(self.org_bones[0], "_pole")))

        # Get edit bones
        eb = self.obj.data.edit_bones

        uarm_e = eb[uarm]
        farm_e = eb[farm]
        hand_e = eb[hand]
        pole_e = eb[pole]
        vishand_e = eb[vishand]
        vispole_e = eb[vispole]

        # Parenting
        farm_e.parent = uarm_e

        hand_e.use_connect = False
        hand_e.parent = None

        pole_e.use_connect = False

        vishand_e.use_connect = False
        vishand_e.parent = None

        vispole_e.use_connect = False
        vispole_e.parent = None

        # Misc
        hand_e.use_local_location = False

        vishand_e.hide_select = True
        vispole_e.hide_select = True

        # Positioning
        v1 = farm_e.tail - uarm_e.head
        if 'X' in self.primary_rotation_axis or 'Y' in self.primary_rotation_axis:
            v2 = v1.cross(farm_e.x_axis)
            if (v2 * farm_e.z_axis) > 0.0:
                v2 *= -1.0
        else:
            v2 = v1.cross(farm_e.z_axis)
            if (v2 * farm_e.x_axis) < 0.0:
                v2 *= -1.0
        v2.normalize()
        v2 *= v1.length

        if '-' in self.primary_rotation_axis:
            v2 *= -1

        pole_e.head = farm_e.head + v2
        pole_e.tail = pole_e.head + (Vector((0, 1, 0)) * (v1.length / 8))
        pole_e.roll = 0.0

        vishand_e.tail = vishand_e.head + Vector((0, 0, v1.length / 32))
        vispole_e.tail = vispole_e.head + Vector((0, 0, v1.length / 32))

        # Determine the pole offset value
        plane = (farm_e.tail - uarm_e.head).normalized()
        vec1 = uarm_e.x_axis.normalized()
        vec2 = (pole_e.head - uarm_e.head).normalized()
        pole_offset = angle_on_plane(plane, vec1, vec2)

        # Object mode, get pose bones
        bpy.ops.object.mode_set(mode='OBJECT')
        pb = self.obj.pose.bones

        # uarm_p = pb[uarm]  # UNUSED
        farm_p = pb[farm]
        hand_p = pb[hand]
        pole_p = pb[pole]
        vishand_p = pb[vishand]
        vispole_p = pb[vispole]

        # Set the elbow to only bend on the primary axis
        if 'X' in self.primary_rotation_axis:
            farm_p.lock_ik_y = True
            farm_p.lock_ik_z = True
        elif 'Y' in self.primary_rotation_axis:
            farm_p.lock_ik_x = True
            farm_p.lock_ik_z = True
        else:
            farm_p.lock_ik_x = True
            farm_p.lock_ik_y = True

        # Pole target only translates
        pole_p.lock_location = False, False, False
        pole_p.lock_rotation = True, True, True
        pole_p.lock_rotation_w = True
        pole_p.lock_scale = True, True, True

        # Set up custom properties
        if self.switch is True:
            prop = rna_idprop_ui_prop_get(hand_p, "ikfk_switch", create=True)
            hand_p["ikfk_switch"] = 0.0
            prop["soft_min"] = prop["min"] = 0.0
            prop["soft_max"] = prop["max"] = 1.0

        # Bend direction hint
        if self.bend_hint:
            con = farm_p.constraints.new('LIMIT_ROTATION')
            con.name = "bend_hint"
            con.owner_space = 'LOCAL'
            if self.primary_rotation_axis == 'X':
                con.use_limit_x = True
                con.min_x = pi / 10
                con.max_x = pi / 10
            elif self.primary_rotation_axis == '-X':
                con.use_limit_x = True
                con.min_x = -pi / 10
                con.max_x = -pi / 10
            elif self.primary_rotation_axis == 'Y':
                con.use_limit_y = True
                con.min_y = pi / 10
                con.max_y = pi / 10
            elif self.primary_rotation_axis == '-Y':
                con.use_limit_y = True
                con.min_y = -pi / 10
                con.max_y = -pi / 10
            elif self.primary_rotation_axis == 'Z':
                con.use_limit_z = True
                con.min_z = pi / 10
                con.max_z = pi / 10
            elif self.primary_rotation_axis == '-Z':
                con.use_limit_z = True
                con.min_z = -pi / 10
                con.max_z = -pi / 10

        # IK Constraint
        con = farm_p.constraints.new('IK')
        con.name = "ik"
        con.target = self.obj
        con.subtarget = hand
        con.pole_target = self.obj
        con.pole_subtarget = pole
        con.pole_angle = pole_offset
        con.chain_count = 2

        # Constrain org bones to controls
        con = pb[self.org_bones[0]].constraints.new('COPY_TRANSFORMS')
        con.name = "ik"
        con.target = self.obj
        con.subtarget = uarm
        if self.switch is True:
            # IK/FK switch driver
            fcurve = con.driver_add("influence")
            driver = fcurve.driver
            var = driver.variables.new()
            driver.type = 'AVERAGE'
            var.name = "var"
            var.targets[0].id_type = 'OBJECT'
            var.targets[0].id = self.obj
            var.targets[0].data_path = hand_p.path_from_id() + '["ikfk_switch"]'

        con = pb[self.org_bones[1]].constraints.new('COPY_TRANSFORMS')
        con.name = "ik"
        con.target = self.obj
        con.subtarget = farm
        if self.switch is True:
            # IK/FK switch driver
            fcurve = con.driver_add("influence")
            driver = fcurve.driver
            var = driver.variables.new()
            driver.type = 'AVERAGE'
            var.name = "var"
            var.targets[0].id_type = 'OBJECT'
            var.targets[0].id = self.obj
            var.targets[0].data_path = hand_p.path_from_id() + '["ikfk_switch"]'

        con = pb[self.org_bones[2]].constraints.new('COPY_TRANSFORMS')
        con.name = "ik"
        con.target = self.obj
        con.subtarget = hand
        if self.switch is True:
            # IK/FK switch driver
            fcurve = con.driver_add("influence")
            driver = fcurve.driver
            var = driver.variables.new()
            driver.type = 'AVERAGE'
            var.name = "var"
            var.targets[0].id_type = 'OBJECT'
            var.targets[0].id = self.obj
            var.targets[0].data_path = hand_p.path_from_id() + '["ikfk_switch"]'

        # VIS hand constraints
        con = vishand_p.constraints.new('COPY_LOCATION')
        con.name = "copy_loc"
        con.target = self.obj
        con.subtarget = self.org_bones[2]

        con = vishand_p.constraints.new('STRETCH_TO')
        con.name = "stretch_to"
        con.target = self.obj
        con.subtarget = hand
        con.volume = 'NO_VOLUME'
        con.rest_length = vishand_p.length

        # VIS pole constraints
        con = vispole_p.constraints.new('COPY_LOCATION')
        con.name = "copy_loc"
        con.target = self.obj
        con.subtarget = self.org_bones[1]

        con = vispole_p.constraints.new('STRETCH_TO')
        con.name = "stretch_to"
        con.target = self.obj
        con.subtarget = pole
        con.volume = 'NO_VOLUME'
        con.rest_length = vispole_p.length

        # Set layers if specified
        if self.layers:
            hand_p.bone.layers = self.layers
            pole_p.bone.layers = self.layers
            vishand_p.bone.layers = self.layers
            vispole_p.bone.layers = self.layers

        # Create widgets
        create_line_widget(self.obj, vispole)
        create_line_widget(self.obj, vishand)
        create_sphere_widget(self.obj, pole)

        ob = create_widget(self.obj, hand)
        if ob != None:
            verts = [(0.7, 1.5, 0.0), (0.7, -0.25, 0.0), (-0.7, -0.25, 0.0), (-0.7, 1.5, 0.0), (0.7, 0.723, 0.0), (-0.7, 0.723, 0.0), (0.7, 0.0, 0.0), (-0.7, 0.0, 0.0)]
            edges = [(1, 2), (0, 3), (0, 4), (3, 5), (4, 6), (1, 6), (5, 7), (2, 7)]
            mesh = ob.data
            mesh.from_pydata(verts, edges, [])
            mesh.update()

            mod = ob.modifiers.new("subsurf", 'SUBSURF')
            mod.levels = 2

        return [uarm, farm, hand, pole]
