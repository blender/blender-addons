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
from rigify.utils import copy_bone, flip_bone, put_bone
from rigify.utils import connected_children_names, has_connected_children
from rigify.utils import strip_org, make_mechanism_name, insert_before_lr
from rigify.utils import create_widget, create_line_widget, create_sphere_widget, create_circle_widget
from rna_prop_ui import rna_idprop_ui_prop_get


def align_x_axis(obj, bone, vec):
    """ Aligns the x-axis of a bone to the given vector.  This only works if it
        can be an exact match.
        Must be in edit mode.

    """
    vec.normalize()
    bone_e = obj.data.edit_bones[bone]
    dot = max(-1.0, min(1.0, bone_e.x_axis.dot(vec)))
    angle = acos(dot)

    bone_e.roll += angle

    dot1 = bone_e.x_axis.dot(vec)

    bone_e.roll -= angle * 2

    dot2 = bone_e.x_axis.dot(vec)

    if dot1 > dot2:
        bone_e.roll += angle * 2


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
    """ An IK leg rig, with an optional ik/fk switch.

    """
    def __init__(self, obj, bone, params, ikfk_switch=False):
        """ Gather and validate data about the rig.
            Store any data or references to data that will be needed later on.
            In particular, store references to bones that will be needed, and
            store names of bones that will be needed.
            Do NOT change any data in the scene.  This is a gathering phase only.
        """
        self.obj = obj
        self.params = params
        self.switch = ikfk_switch

        # Get the chain of 2 connected bones
        leg_bones = [bone] + connected_children_names(self.obj, bone)[:2]

        if len(leg_bones) != 2:
            raise MetarigError("RIGIFY ERROR: Bone '%s': incorrect bone configuration for rig type" % (strip_org(bone)))

        # Get the foot and heel
        foot = None
        heel = None
        rocker = None
        for b in self.obj.data.bones[leg_bones[1]].children:
            if b.use_connect is True:
                if len(b.children) >= 1 and has_connected_children(b):
                    foot = b.name
                else:
                    heel = b.name
                    if len(b.children) > 0:
                        rocker = b.children[0].name

        if foot is None or heel is None:
            print("blah")
            raise MetarigError("RIGIFY ERROR: Bone '%s': incorrect bone configuration for rig type" % (strip_org(bone)))

        # Get the toe
        toe = None
        for b in self.obj.data.bones[foot].children:
            if b.use_connect is True:
                toe = b.name

        # Get toe
        if toe is None:
            raise MetarigError("RIGIFY ERROR: Bone '%s': incorrect bone configuration for rig type" % (strip_org(bone)))

        self.org_bones = leg_bones + [foot, toe, heel, rocker]

        # Get rig parameters
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

        make_rocker = False
        if self.org_bones[5] is not None:
            make_rocker = True

        # Create the bones
        thigh = copy_bone(self.obj, self.org_bones[0], make_mechanism_name(strip_org(insert_before_lr(self.org_bones[0], "_ik"))))
        shin = copy_bone(self.obj, self.org_bones[1], make_mechanism_name(strip_org(insert_before_lr(self.org_bones[1], "_ik"))))

        foot = copy_bone(self.obj, self.org_bones[2], strip_org(insert_before_lr(self.org_bones[2], "_ik")))
        foot_ik_target = copy_bone(self.obj, self.org_bones[2], make_mechanism_name(strip_org(insert_before_lr(self.org_bones[2], "_ik_target"))))
        pole = copy_bone(self.obj, self.org_bones[0], strip_org(insert_before_lr(self.org_bones[0], "_pole")))

        toe = copy_bone(self.obj, self.org_bones[3], strip_org(self.org_bones[3]))
        toe_parent = copy_bone(self.obj, self.org_bones[2], make_mechanism_name(strip_org(self.org_bones[3] + ".parent")))
        toe_parent_socket1 = copy_bone(self.obj, self.org_bones[2], make_mechanism_name(strip_org(self.org_bones[3] + ".socket1")))
        toe_parent_socket2 = copy_bone(self.obj, self.org_bones[2], make_mechanism_name(strip_org(self.org_bones[3] + ".socket2")))

        foot_roll = copy_bone(self.obj, self.org_bones[4], strip_org(insert_before_lr(self.org_bones[2], "_roll")))
        roll1 = copy_bone(self.obj, self.org_bones[4], make_mechanism_name(strip_org(self.org_bones[2] + ".roll.01")))
        roll2 = copy_bone(self.obj, self.org_bones[4], make_mechanism_name(strip_org(self.org_bones[2] + ".roll.02")))

        if make_rocker:
            rocker1 = copy_bone(self.obj, self.org_bones[5], make_mechanism_name(strip_org(self.org_bones[2] + ".rocker.01")))
            rocker2 = copy_bone(self.obj, self.org_bones[5], make_mechanism_name(strip_org(self.org_bones[2] + ".rocker.02")))

        visfoot = copy_bone(self.obj, self.org_bones[2], "VIS-" + strip_org(insert_before_lr(self.org_bones[2], "_ik")))
        vispole = copy_bone(self.obj, self.org_bones[1], "VIS-" + strip_org(insert_before_lr(self.org_bones[0], "_pole")))

        # Get edit bones
        eb = self.obj.data.edit_bones

        org_foot_e = eb[self.org_bones[2]]
        thigh_e = eb[thigh]
        shin_e = eb[shin]
        foot_e = eb[foot]
        foot_ik_target_e = eb[foot_ik_target]
        pole_e = eb[pole]
        toe_e = eb[toe]
        toe_parent_e = eb[toe_parent]
        toe_parent_socket1_e = eb[toe_parent_socket1]
        toe_parent_socket2_e = eb[toe_parent_socket2]
        foot_roll_e = eb[foot_roll]
        roll1_e = eb[roll1]
        roll2_e = eb[roll2]
        if make_rocker:
            rocker1_e = eb[rocker1]
            rocker2_e = eb[rocker2]
        visfoot_e = eb[visfoot]
        vispole_e = eb[vispole]

        # Parenting
        shin_e.parent = thigh_e

        foot_e.use_connect = False
        foot_e.parent = None
        foot_ik_target_e.use_connect = False
        foot_ik_target_e.parent = roll2_e

        pole_e.use_connect = False
        pole_e.parent = foot_e

        toe_e.parent = toe_parent_e
        toe_parent_e.use_connect = False
        toe_parent_e.parent = toe_parent_socket1_e
        toe_parent_socket1_e.use_connect = False
        toe_parent_socket1_e.parent = roll1_e
        toe_parent_socket2_e.use_connect = False
        toe_parent_socket2_e.parent = eb[self.org_bones[2]]

        foot_roll_e.use_connect = False
        foot_roll_e.parent = foot_e

        roll1_e.use_connect = False
        roll1_e.parent = foot_e

        roll2_e.use_connect = False
        roll2_e.parent = roll1_e

        visfoot_e.use_connect = False
        visfoot_e.parent = None

        vispole_e.use_connect = False
        vispole_e.parent = None

        if make_rocker:
            rocker1_e.use_connect = False
            rocker2_e.use_connect = False

            roll1_e.parent = rocker2_e
            rocker2_e.parent = rocker1_e
            rocker1_e.parent = foot_e

        # Misc
        foot_e.use_local_location = False

        visfoot_e.hide_select = True
        vispole_e.hide_select = True

        # Positioning
        vec = Vector(toe_e.vector)
        vec.normalize()
        foot_e.tail = foot_e.head + (vec * foot_e.length)
        foot_e.roll = toe_e.roll

        v1 = shin_e.tail - thigh_e.head

        if 'X' in self.primary_rotation_axis or 'Y' in self.primary_rotation_axis:
            v2 = v1.cross(shin_e.x_axis)
            if (v2 * shin_e.z_axis) > 0.0:
                v2 *= -1.0
        else:
            v2 = v1.cross(shin_e.z_axis)
            if (v2 * shin_e.x_axis) < 0.0:
                v2 *= -1.0
        v2.normalize()
        v2 *= v1.length

        if '-' in self.primary_rotation_axis:
            v2 *= -1

        pole_e.head = shin_e.head + v2
        pole_e.tail = pole_e.head + (Vector((0, 1, 0)) * (v1.length / 8))
        pole_e.roll = 0.0

        flip_bone(self.obj, toe_parent_socket1)
        flip_bone(self.obj, toe_parent_socket2)
        toe_parent_socket1_e.head = Vector(org_foot_e.tail)
        toe_parent_socket2_e.head = Vector(org_foot_e.tail)
        toe_parent_socket1_e.tail = Vector(org_foot_e.tail) + (Vector((0, 0, 1)) * foot_e.length / 2)
        toe_parent_socket2_e.tail = Vector(org_foot_e.tail) + (Vector((0, 0, 1)) * foot_e.length / 3)
        toe_parent_socket2_e.roll = toe_parent_socket1_e.roll

        tail = Vector(roll1_e.tail)
        roll1_e.tail = Vector(org_foot_e.tail)
        roll1_e.tail = Vector(org_foot_e.tail)
        roll1_e.head = tail
        roll2_e.head = Vector(org_foot_e.tail)
        foot_roll_e.head = Vector(org_foot_e.tail)
        put_bone(self.obj, foot_roll, roll1_e.head)
        foot_roll_e.length /= 2

        roll_axis = roll1_e.vector.cross(org_foot_e.vector)
        align_x_axis(self.obj, roll1, roll_axis)
        align_x_axis(self.obj, roll2, roll_axis)
        foot_roll_e.roll = roll2_e.roll

        visfoot_e.tail = visfoot_e.head + Vector((0, 0, v1.length / 32))
        vispole_e.tail = vispole_e.head + Vector((0, 0, v1.length / 32))

        if make_rocker:
            d = toe_e.y_axis.dot(rocker1_e.x_axis)
            if d >= 0.0:
                flip_bone(self.obj, rocker2)
            else:
                flip_bone(self.obj, rocker1)

        # Weird alignment issues.  Fix.
        toe_parent_e.head = Vector(org_foot_e.head)
        toe_parent_e.tail = Vector(org_foot_e.tail)
        toe_parent_e.roll = org_foot_e.roll

        foot_e.head = Vector(org_foot_e.head)

        foot_ik_target_e.head = Vector(org_foot_e.head)
        foot_ik_target_e.tail = Vector(org_foot_e.tail)

        # Determine the pole offset value
        plane = (shin_e.tail - thigh_e.head).normalized()
        vec1 = thigh_e.x_axis.normalized()
        vec2 = (pole_e.head - thigh_e.head).normalized()
        pole_offset = angle_on_plane(plane, vec1, vec2)

        # Object mode, get pose bones
        bpy.ops.object.mode_set(mode='OBJECT')
        pb = self.obj.pose.bones

        # thigh_p = pb[thigh]  # UNUSED
        shin_p = pb[shin]
        foot_p = pb[foot]
        pole_p = pb[pole]
        foot_roll_p = pb[foot_roll]
        roll1_p = pb[roll1]
        roll2_p = pb[roll2]
        if make_rocker:
            rocker1_p = pb[rocker1]
            rocker2_p = pb[rocker2]
        toe_p = pb[toe]
        toe_parent_p = pb[toe_parent]
        toe_parent_socket1_p = pb[toe_parent_socket1]
        visfoot_p = pb[visfoot]
        vispole_p = pb[vispole]

        # Set the knee to only bend on the primary axis.
        if 'X' in self.primary_rotation_axis:
            shin_p.lock_ik_y = True
            shin_p.lock_ik_z = True
        elif 'Y' in self.primary_rotation_axis:
            shin_p.lock_ik_x = True
            shin_p.lock_ik_z = True
        else:
            shin_p.lock_ik_x = True
            shin_p.lock_ik_y = True

        # Foot roll control only rotates on x-axis, or x and y if rocker.
        foot_roll_p.rotation_mode = 'XYZ'
        if make_rocker:
            foot_roll_p.lock_rotation = False, False, True
        else:
            foot_roll_p.lock_rotation = False, True, True
        foot_roll_p.lock_location = True, True, True
        foot_roll_p.lock_scale = True, True, True

        # roll and rocker bones set to euler rotation
        roll1_p.rotation_mode = 'XYZ'
        roll2_p.rotation_mode = 'XYZ'
        if make_rocker:
            rocker1_p.rotation_mode = 'XYZ'
            rocker2_p.rotation_mode = 'XYZ'

        # Pole target only translates
        pole_p.lock_location = False, False, False
        pole_p.lock_rotation = True, True, True
        pole_p.lock_rotation_w = True
        pole_p.lock_scale = True, True, True

        # Set up custom properties
        if self.switch is True:
            prop = rna_idprop_ui_prop_get(foot_p, "ikfk_switch", create=True)
            foot_p["ikfk_switch"] = 0.0
            prop["soft_min"] = prop["min"] = 0.0
            prop["soft_max"] = prop["max"] = 1.0

        # Bend direction hint
        if self.bend_hint:
            con = shin_p.constraints.new('LIMIT_ROTATION')
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
        con = shin_p.constraints.new('IK')
        con.name = "ik"
        con.target = self.obj
        con.subtarget = foot_ik_target
        con.pole_target = self.obj
        con.pole_subtarget = pole
        con.pole_angle = pole_offset
        con.chain_count = 2

        # toe_parent constraint
        con = toe_parent_socket1_p.constraints.new('COPY_LOCATION')
        con.name = "copy_location"
        con.target = self.obj
        con.subtarget = toe_parent_socket2

        con = toe_parent_socket1_p.constraints.new('COPY_SCALE')
        con.name = "copy_scale"
        con.target = self.obj
        con.subtarget = toe_parent_socket2

        con = toe_parent_socket1_p.constraints.new('COPY_TRANSFORMS')  # drive with IK switch
        con.name = "fk"
        con.target = self.obj
        con.subtarget = toe_parent_socket2

        fcurve = con.driver_add("influence")
        driver = fcurve.driver
        var = driver.variables.new()
        driver.type = 'AVERAGE'
        var.name = "var"
        var.targets[0].id_type = 'OBJECT'
        var.targets[0].id = self.obj
        var.targets[0].data_path = foot_p.path_from_id() + '["ikfk_switch"]'
        mod = fcurve.modifiers[0]
        mod.poly_order = 1
        mod.coefficients[0] = 1.0
        mod.coefficients[1] = -1.0

        # Foot roll drivers
        fcurve = roll1_p.driver_add("rotation_euler", 0)
        driver = fcurve.driver
        var = driver.variables.new()
        driver.type = 'SCRIPTED'
        driver.expression = "min(0,var)"
        var.name = "var"
        var.targets[0].id_type = 'OBJECT'
        var.targets[0].id = self.obj
        var.targets[0].data_path = foot_roll_p.path_from_id() + '.rotation_euler[0]'

        fcurve = roll2_p.driver_add("rotation_euler", 0)
        driver = fcurve.driver
        var = driver.variables.new()
        driver.type = 'SCRIPTED'
        driver.expression = "max(0,var)"
        var.name = "var"
        var.targets[0].id_type = 'OBJECT'
        var.targets[0].id = self.obj
        var.targets[0].data_path = foot_roll_p.path_from_id() + '.rotation_euler[0]'

        if make_rocker:
            fcurve = rocker1_p.driver_add("rotation_euler", 0)
            driver = fcurve.driver
            var = driver.variables.new()
            driver.type = 'SCRIPTED'
            driver.expression = "max(0,-var)"
            var.name = "var"
            var.targets[0].id_type = 'OBJECT'
            var.targets[0].id = self.obj
            var.targets[0].data_path = foot_roll_p.path_from_id() + '.rotation_euler[1]'

            fcurve = rocker2_p.driver_add("rotation_euler", 0)
            driver = fcurve.driver
            var = driver.variables.new()
            driver.type = 'SCRIPTED'
            driver.expression = "max(0,var)"
            var.name = "var"
            var.targets[0].id_type = 'OBJECT'
            var.targets[0].id = self.obj
            var.targets[0].data_path = foot_roll_p.path_from_id() + '.rotation_euler[1]'

        # Constrain org bones to controls
        con = pb[self.org_bones[0]].constraints.new('COPY_TRANSFORMS')
        con.name = "ik"
        con.target = self.obj
        con.subtarget = thigh
        if self.switch is True:
            # IK/FK switch driver
            fcurve = con.driver_add("influence")
            driver = fcurve.driver
            var = driver.variables.new()
            driver.type = 'AVERAGE'
            var.name = "var"
            var.targets[0].id_type = 'OBJECT'
            var.targets[0].id = self.obj
            var.targets[0].data_path = foot_p.path_from_id() + '["ikfk_switch"]'

        con = pb[self.org_bones[1]].constraints.new('COPY_TRANSFORMS')
        con.name = "ik"
        con.target = self.obj
        con.subtarget = shin
        if self.switch is True:
            # IK/FK switch driver
            fcurve = con.driver_add("influence")
            driver = fcurve.driver
            var = driver.variables.new()
            driver.type = 'AVERAGE'
            var.name = "var"
            var.targets[0].id_type = 'OBJECT'
            var.targets[0].id = self.obj
            var.targets[0].data_path = foot_p.path_from_id() + '["ikfk_switch"]'

        con = pb[self.org_bones[2]].constraints.new('COPY_TRANSFORMS')
        con.name = "ik"
        con.target = self.obj
        con.subtarget = foot_ik_target
        if self.switch is True:
            # IK/FK switch driver
            fcurve = con.driver_add("influence")
            driver = fcurve.driver
            var = driver.variables.new()
            driver.type = 'AVERAGE'
            var.name = "var"
            var.targets[0].id_type = 'OBJECT'
            var.targets[0].id = self.obj
            var.targets[0].data_path = foot_p.path_from_id() + '["ikfk_switch"]'

        con = pb[self.org_bones[3]].constraints.new('COPY_TRANSFORMS')
        con.name = "copy_transforms"
        con.target = self.obj
        con.subtarget = toe

        # VIS foot constraints
        con = visfoot_p.constraints.new('COPY_LOCATION')
        con.name = "copy_loc"
        con.target = self.obj
        con.subtarget = self.org_bones[2]

        con = visfoot_p.constraints.new('STRETCH_TO')
        con.name = "stretch_to"
        con.target = self.obj
        con.subtarget = foot
        con.volume = 'NO_VOLUME'
        con.rest_length = visfoot_p.length

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
            foot_p.bone.layers = self.layers
            pole_p.bone.layers = self.layers
            foot_roll_p.bone.layers = self.layers
            visfoot_p.bone.layers = self.layers
            vispole_p.bone.layers = self.layers

            toe_p.bone.layers = [(i[0] or i[1]) for i in zip(toe_p.bone.layers, self.layers)]  # Both FK and IK layers

        # Create widgets
        create_line_widget(self.obj, vispole)
        create_line_widget(self.obj, visfoot)
        create_sphere_widget(self.obj, pole)
        create_circle_widget(self.obj, toe, radius=0.7, head_tail=0.5)

        ob = create_widget(self.obj, foot)
        if ob != None:
            verts = [(0.7, 1.5, 0.0), (0.7, -0.25, 0.0), (-0.7, -0.25, 0.0), (-0.7, 1.5, 0.0), (0.7, 0.723, 0.0), (-0.7, 0.723, 0.0), (0.7, 0.0, 0.0), (-0.7, 0.0, 0.0)]
            edges = [(1, 2), (0, 3), (0, 4), (3, 5), (4, 6), (1, 6), (5, 7), (2, 7)]
            mesh = ob.data
            mesh.from_pydata(verts, edges, [])
            mesh.update()

            mod = ob.modifiers.new("subsurf", 'SUBSURF')
            mod.levels = 2

        ob = create_widget(self.obj, foot_roll)
        if ob != None:
            verts = [(0.3999999761581421, 0.766044557094574, 0.6427875757217407), (0.17668449878692627, 3.823702598992895e-08, 3.2084670920085046e-08), (-0.17668461799621582, 9.874240447516058e-08, 8.285470443070153e-08), (-0.39999961853027344, 0.7660449147224426, 0.6427879333496094), (0.3562471270561218, 0.6159579753875732, 0.5168500542640686), (-0.35624682903289795, 0.6159582138061523, 0.5168502926826477), (0.20492683351039886, 0.09688037633895874, 0.0812922865152359), (-0.20492687821388245, 0.0968804731965065, 0.08129236847162247)]
            edges = [(1, 2), (0, 3), (0, 4), (3, 5), (1, 6), (4, 6), (2, 7), (5, 7)]
            mesh = ob.data
            mesh.from_pydata(verts, edges, [])
            mesh.update()

            mod = ob.modifiers.new("subsurf", 'SUBSURF')
            mod.levels = 2

        return [thigh, shin, foot, pole, foot_roll, foot_ik_target]
