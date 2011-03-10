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

UI_SLIDERS = '''
import bpy
from mathutils import Matrix, Vector
from math import acos

rig_id = "%s"


def get_pose_matrix_in_other_space(mat, pbs):
    """ Returns the transform matrix relative to pbs's transform space.
        In other words, you could take the matrix returned from this, slap
        it into pbs, and it would have the same world transform as mat.
        This is with constraints applied.
    """
    rest_inv = pbs.bone.matrix_local.inverted()

    if pbs.parent:
        par_inv = pbs.parent.matrix.inverted()
        par_rest = pbs.parent.bone.matrix_local.copy()

        smat = rest_inv * (par_rest * (par_inv * mat))
    else:
        smat = rest_inv * mat

    return smat


def get_local_matrix_with_constraints(pose_bone):
    """ Returns the local matrix of the given pose bone, with constraints
        applied.
    """
    return get_pose_matrix_in_other_space(pose_bone.matrix, pose_bone)


def set_pose_rotation(pb, mat):
    """ Sets the pose bone's rotation to the same rotation as the given matrix.
        Matrix should be given in local space.
    """
    q = mat.to_quaternion()

    if pb.rotation_mode == 'QUATERNION':
        pb.rotation_quaternion = q
    elif pb.rotation_mode == 'AXIS_ANGLE':
        pb.rotation_axis_angle[0] = q.angle
        pb.rotation_axis_angle[1] = q.axis[0]
        pb.rotation_axis_angle[2] = q.axis[1]
        pb.rotation_axis_angle[3] = q.axis[2]
    else:
        pb.rotation_euler = q.to_euler(pb.rotation_mode)


def set_pose_scale(pb, mat):
    """ Sets the pose bone's scale to the same scale as the given matrix.
        Matrix should be given in local space.
    """
    pb.scale = mat.to_scale()


def set_pose_translation(pb, mat):
    """ Sets the pose bone's translation to the same translation as the given matrix.
        Matrix should be given in local space.
    """
    if pb.bone.use_local_location == True:
        pb.location = mat.to_translation()
    else:
        loc = mat.to_translation()

        rest = pb.bone.matrix_local.copy()
        if pb.bone.parent:
            par_rest = pb.bone.parent.matrix_local.copy()
        else:
            par_rest = Matrix()

        q = (par_rest.inverted() * rest).to_quaternion()
        pb.location = loc * q


def fk2ik_arm(obj, fk, ik):
    """ Matches the fk bones in an arm rig to the ik bones.
    """
    pb = obj.pose.bones

    uarm = pb[fk[0]]
    farm = pb[fk[1]]
    hand = pb[fk[2]]

    uarmi = pb[ik[0]]
    farmi = pb[ik[1]]
    handi = pb[ik[2]]

    uarmmat = get_pose_matrix_in_other_space(uarmi.matrix, uarm)
    set_pose_rotation(uarm, uarmmat)
    set_pose_scale(uarm, uarmmat)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='POSE')

    farmmat = get_pose_matrix_in_other_space(farmi.matrix, farm)
    set_pose_rotation(farm, farmmat)
    set_pose_scale(farm, farmmat)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='POSE')

    handmat = get_pose_matrix_in_other_space(handi.matrix, hand)
    set_pose_rotation(hand, handmat)
    set_pose_scale(hand, handmat)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='POSE')


def ik2fk_arm(obj, fk, ik):
    """ Matches the ik bones in an arm rig to the fk bones.
    """
    pb = obj.pose.bones

    uarm = pb[fk[0]]
    farm = pb[fk[1]]
    hand = pb[fk[2]]

    uarmi = pb[ik[0]]
    farmi = pb[ik[1]]
    handi = pb[ik[2]]
    pole = pb[ik[3]]

    # Hand position
    handmat = get_pose_matrix_in_other_space(hand.matrix, handi)
    set_pose_translation(handi, handmat)
    set_pose_rotation(handi, handmat)
    set_pose_scale(handi, handmat)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='POSE')

    # Pole target position
    a = uarm.matrix.to_translation()
    b = farm.matrix.to_translation() + farm.vector

    # Vector from the head of the upper arm to the
    # tip of the forearm
    armv = b - a

    # Create a vector that is not aligned with armv.
    # It doesn't matter what vector.  Just any vector
    # that's guaranteed to not be pointing in the same
    # direction.
    if abs(armv[0]) < abs(armv[1]) and abs(armv[0]) < abs(armv[2]):
        v = Vector((1,0,0))
    elif abs(armv[1]) < abs(armv[2]):
        v = Vector((0,1,0))
    else:
        v = Vector((0,0,1))

    # cross v with armv to get a vector perpendicular to armv
    pv = v.cross(armv).normalized() * (uarm.length + farm.length)

    def set_pole(pvi):
        # Translate pvi into armature space
        ploc = a + (armv/2) + pvi

        # Set pole target to location
        mat = get_pose_matrix_in_other_space(Matrix().Translation(ploc), pole)
        set_pose_translation(pole, mat)

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='POSE')

    set_pole(pv)

    # Get the rotation difference between the ik and fk upper arms
    q1 = uarm.matrix.to_quaternion()
    q2 = uarmi.matrix.to_quaternion()
    angle = acos(min(1,max(-1,q1.dot(q2)))) * 2

    # Compensate for the rotation difference
    if angle > 0.00001:
        pv *= Matrix.Rotation(angle, 4, armv).to_quaternion()
        set_pole(pv)

        q1 = uarm.matrix.to_quaternion()
        q2 = uarmi.matrix.to_quaternion()
        angle2 = acos(min(1,max(-1,q1.dot(q2)))) * 2
        if angle2 > 0.00001:
            pv *= Matrix.Rotation((angle*(-2)), 4, armv).to_quaternion()
            set_pole(pv)


def fk2ik_leg(obj, fk, ik):
    """ Matches the fk bones in a leg rig to the ik bones.
    """
    pb = obj.pose.bones

    thigh = pb[fk[0]]
    shin  = pb[fk[1]]
    foot  = pb[fk[2]]
    mfoot = pb[fk[3]]

    thighi = pb[ik[0]]
    shini  = pb[ik[1]]
    mfooti = pb[ik[2]]

    thighmat = get_pose_matrix_in_other_space(thighi.matrix, thigh)
    set_pose_rotation(thigh, thighmat)
    set_pose_scale(thigh, thighmat)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='POSE')

    shinmat = get_pose_matrix_in_other_space(shini.matrix, shin)
    set_pose_rotation(shin, shinmat)
    set_pose_scale(shin, shinmat)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='POSE')

    mat = mfoot.bone.matrix_local.inverted() * foot.bone.matrix_local
    footmat = get_pose_matrix_in_other_space(mfooti.matrix, foot) * mat
    set_pose_rotation(foot, footmat)
    set_pose_scale(foot, footmat)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='POSE')


def ik2fk_leg(obj, fk, ik):
    """ Matches the ik bones in a leg rig to the fk bones.
    """
    pb = obj.pose.bones

    thigh = pb[fk[0]]
    shin  = pb[fk[1]]
    mfoot = pb[fk[2]]

    thighi   = pb[ik[0]]
    shini    = pb[ik[1]]
    footi    = pb[ik[2]]
    footroll = pb[ik[3]]
    pole     = pb[ik[4]]
    mfooti   = pb[ik[5]]

    # Clear footroll
    set_pose_rotation(footroll, Matrix())

    # Foot position
    mat = mfooti.bone.matrix_local.inverted() * footi.bone.matrix_local
    footmat = get_pose_matrix_in_other_space(mfoot.matrix, footi) * mat
    set_pose_translation(footi, footmat)
    set_pose_rotation(footi, footmat)
    set_pose_scale(footi, footmat)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='POSE')

    # Pole target position
    a = thigh.matrix.to_translation()
    b = shin.matrix.to_translation() + shin.vector

    # Vector from the head of the thigh to the
    # tip of the shin
    legv = b - a

    # Create a vector that is not aligned with legv.
    # It doesn't matter what vector.  Just any vector
    # that's guaranteed to not be pointing in the same
    # direction.
    if abs(legv[0]) < abs(legv[1]) and abs(legv[0]) < abs(legv[2]):
        v = Vector((1,0,0))
    elif abs(legv[1]) < abs(legv[2]):
        v = Vector((0,1,0))
    else:
        v = Vector((0,0,1))

    # Get a vector perpendicular to legv
    pv = v.cross(legv).normalized() * (thigh.length + shin.length)

    def set_pole(pvi):
        # Translate pvi into armature space
        ploc = a + (legv/2) + pvi

        # Set pole target to location
        mat = get_pose_matrix_in_other_space(Matrix().Translation(ploc), pole)
        set_pose_translation(pole, mat)

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='POSE')

    set_pole(pv)

    # Get the rotation difference between the ik and fk thighs
    q1 = thigh.matrix.to_quaternion()
    q2 = thighi.matrix.to_quaternion()
    angle = acos(min(1,max(-1,q1.dot(q2)))) * 2

    # Compensate for the rotation difference
    if angle > 0.00001:
        pv *= Matrix.Rotation(angle, 4, legv).to_quaternion()
        set_pole(pv)

        q1 = thigh.matrix.to_quaternion()
        q2 = thighi.matrix.to_quaternion()
        angle2 = acos(min(1,max(-1,q1.dot(q2)))) * 2
        if angle2 > 0.00001:
            pv *= Matrix.Rotation((angle*(-2)), 4, legv).to_quaternion()
            set_pole(pv)


class Rigify_Arm_FK2IK(bpy.types.Operator):
    """ Snaps an FK arm to an IK arm.
    """
    bl_idname = "pose.rigify_arm_fk2ik_" + rig_id
    bl_label = "Rigify Snap FK arm to IK"
    bl_options = {'UNDO'}

    uarm_fk = bpy.props.StringProperty(name="Upper Arm FK Name")
    farm_fk = bpy.props.StringProperty(name="Forerm FK Name")
    hand_fk = bpy.props.StringProperty(name="Hand FK Name")

    uarm_ik = bpy.props.StringProperty(name="Upper Arm IK Name")
    farm_ik = bpy.props.StringProperty(name="Forearm IK Name")
    hand_ik = bpy.props.StringProperty(name="Hand IK Name")

    @classmethod
    def poll(cls, context):
        return (context.active_object != None and context.mode == 'POSE')

    def execute(self, context):
        use_global_undo = context.user_preferences.edit.use_global_undo
        context.user_preferences.edit.use_global_undo = False
        try:
            fk2ik_arm(context.active_object, fk=[self.uarm_fk, self.farm_fk, self.hand_fk], ik=[self.uarm_ik, self.farm_ik, self.hand_ik])
        finally:
            context.user_preferences.edit.use_global_undo = use_global_undo
        return {'FINISHED'}


class Rigify_Arm_IK2FK(bpy.types.Operator):
    """ Snaps an IK arm to an FK arm.
    """
    bl_idname = "pose.rigify_arm_ik2fk_" + rig_id
    bl_label = "Rigify Snap IK arm to FK"
    bl_options = {'UNDO'}

    uarm_fk = bpy.props.StringProperty(name="Upper Arm FK Name")
    farm_fk = bpy.props.StringProperty(name="Forerm FK Name")
    hand_fk = bpy.props.StringProperty(name="Hand FK Name")

    uarm_ik = bpy.props.StringProperty(name="Upper Arm IK Name")
    farm_ik = bpy.props.StringProperty(name="Forearm IK Name")
    hand_ik = bpy.props.StringProperty(name="Hand IK Name")
    pole = bpy.props.StringProperty(name="Pole IK Name")

    @classmethod
    def poll(cls, context):
        return (context.active_object != None and context.mode == 'POSE')

    def execute(self, context):
        use_global_undo = context.user_preferences.edit.use_global_undo
        context.user_preferences.edit.use_global_undo = False
        try:
            ik2fk_arm(context.active_object, fk=[self.uarm_fk, self.farm_fk, self.hand_fk], ik=[self.uarm_ik, self.farm_ik, self.hand_ik, self.pole])
        finally:
            context.user_preferences.edit.use_global_undo = use_global_undo
        return {'FINISHED'}


class Rigify_Leg_FK2IK(bpy.types.Operator):
    """ Snaps an FK leg to an IK leg.
    """
    bl_idname = "pose.rigify_leg_fk2ik_" + rig_id
    bl_label = "Rigify Snap FK leg to IK"
    bl_options = {'UNDO'}

    thigh_fk = bpy.props.StringProperty(name="Thigh FK Name")
    shin_fk  = bpy.props.StringProperty(name="Shin FK Name")
    foot_fk  = bpy.props.StringProperty(name="Foot FK Name")
    mfoot_fk = bpy.props.StringProperty(name="MFoot FK Name")


    thigh_ik = bpy.props.StringProperty(name="Thigh IK Name")
    shin_ik  = bpy.props.StringProperty(name="Shin IK Name")
    mfoot_ik = bpy.props.StringProperty(name="MFoot IK Name")

    @classmethod
    def poll(cls, context):
        return (context.active_object != None and context.mode == 'POSE')

    def execute(self, context):
        use_global_undo = context.user_preferences.edit.use_global_undo
        context.user_preferences.edit.use_global_undo = False
        try:
            fk2ik_leg(context.active_object, fk=[self.thigh_fk, self.shin_fk, self.foot_fk, self.mfoot_fk], ik=[self.thigh_ik, self.shin_ik, self.mfoot_ik])
        finally:
            context.user_preferences.edit.use_global_undo = use_global_undo
        return {'FINISHED'}


class Rigify_Leg_IK2FK(bpy.types.Operator):
    """ Snaps an IK leg to an FK leg.
    """
    bl_idname = "pose.rigify_leg_ik2fk_" + rig_id
    bl_label = "Rigify Snap IK leg to FK"
    bl_options = {'UNDO'}

    thigh_fk = bpy.props.StringProperty(name="Thigh FK Name")
    shin_fk  = bpy.props.StringProperty(name="Shin FK Name")
    mfoot_fk = bpy.props.StringProperty(name="MFoot FK Name")

    thigh_ik = bpy.props.StringProperty(name="Thigh IK Name")
    shin_ik  = bpy.props.StringProperty(name="Shin IK Name")
    foot_ik  = bpy.props.StringProperty(name="Foot IK Name")
    footroll = bpy.props.StringProperty(name="Foot Roll Name")
    pole     = bpy.props.StringProperty(name="Pole IK Name")
    mfoot_ik = bpy.props.StringProperty(name="MFoot IK Name")

    @classmethod
    def poll(cls, context):
        return (context.active_object != None and context.mode == 'POSE')

    def execute(self, context):
        use_global_undo = context.user_preferences.edit.use_global_undo
        context.user_preferences.edit.use_global_undo = False
        try:
            ik2fk_leg(context.active_object, fk=[self.thigh_fk, self.shin_fk, self.mfoot_fk], ik=[self.thigh_ik, self.shin_ik, self.foot_ik, self.footroll, self.pole, self.mfoot_ik])
        finally:
            context.user_preferences.edit.use_global_undo = use_global_undo
        return {'FINISHED'}


bpy.utils.register_class(Rigify_Arm_FK2IK)
bpy.utils.register_class(Rigify_Arm_IK2FK)
bpy.utils.register_class(Rigify_Leg_FK2IK)
bpy.utils.register_class(Rigify_Leg_IK2FK)


class RigUI(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Rig Main Properties"
    bl_idname = rig_id + "_PT_rig_ui"

    @classmethod
    def poll(self, context):
        if context.mode != 'POSE':
            return False
        try:
            return (context.active_object.data.get("rig_id") == rig_id)
        except (AttributeError, KeyError, TypeError):
            return False

    def draw(self, context):
        layout = self.layout
        pose_bones = context.active_object.pose.bones
        try:
            selected_bones = [bone.name for bone in context.selected_pose_bones]
            selected_bones += [context.active_pose_bone.name]
        except (AttributeError, TypeError):
            return

        def is_selected(names):
            # Returns whether any of the named bones are selected.
            if type(names) == list:
                for name in names:
                    if name in selected_bones:
                        return True
            elif names in selected_bones:
                return True
            return False


'''


def layers_ui(layers):
    """ Turn a list of booleans into a layer UI.
    """

    code = '''
class RigLayers(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Rig Layers"
    bl_idname = rig_id + "_PT_rig_layers"

    @classmethod
    def poll(self, context):
        try:
            return (context.active_object.data.get("rig_id") == rig_id)
        except (AttributeError, KeyError, TypeError):
            return False

    def draw(self, context):
        layout = self.layout
        col = layout.column()
'''
    i = 0
    for layer in layers:
        if layer:
            code += "\n        row = col.row()\n"
            if i == 28:
                code += "        row.prop(context.active_object.data, 'layers', index=%s, toggle=True, text='Root')\n" % (str(i))
            else:
                code += "        row.prop(context.active_object.data, 'layers', index=%s, toggle=True, text='%s')\n" % (str(i), str(i + 1))
        i += 1

    return code


UI_REGISTER = '''

def register():
    bpy.utils.register_class(RigUI)
    bpy.utils.register_class(RigLayers)

register()
'''

