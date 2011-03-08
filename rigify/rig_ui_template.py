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

rig_id = "%s"


def get_pose_matrix_in_other_space(pose_bone, pbs):
    """ Returns the transform matrix of pose_bone relative to pbs's transform space.
        In other words, you could take the matrix returned from this, slap
        it into pbs, and it would have the same world transform as pb.
        This is with constraints applied.
    """
    mat = pose_bone.matrix.copy()
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
    return get_pose_matrix_in_other_space(pose_bone, pose_bone)


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
    pb.location = mat.to_translation()


def fk2ik(obj, fk, ik):
    """ Matches the fk bones in an arm rig to the ik bones.
    """
    pb = obj.pose.bones
    
    uarm = pb[fk[0]]
    farm = pb[fk[1]]
    hand = pb[fk[2]]
    
    uarmi = pb[ik[0]]
    farmi = pb[ik[1]]
    handi = pb[ik[2]]
    
    uarmmat = get_pose_matrix_in_other_space(uarmi, uarm)
    set_pose_rotation(uarm, uarmmat)
    set_pose_scale(uarm, uarmmat)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='POSE')
    
    farmmat = get_pose_matrix_in_other_space(farmi, farm)
    set_pose_rotation(farm, farmmat)
    set_pose_scale(farm, farmmat)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='POSE')
    
    handmat = get_pose_matrix_in_other_space(handi, hand)
    set_pose_rotation(hand, handmat)
    set_pose_scale(hand, handmat)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='POSE')
    

def ik2fk(obj, fk, ik):
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
    
    handmat = get_pose_matrix_in_other_space(hand, handi)
    set_pose_translation(handi, handmat)
    set_pose_rotation(handi, handmat)
    set_pose_scale(handi, handmat)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='POSE')


class Rigify_Arm_FK2IK(bpy.types.Operator):
    """ Snaps an FK arm to an IK arm.
    """
    bl_idname = "pose.rigify_arm_fk2ik"
    bl_label = "Rigify Snap FK arm to IK"
    
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
        fk2ik(context.active_object, fk=[self.uarm_fk, self.farm_fk, self.hand_fk], ik=[self.uarm_ik, self.farm_ik, self.hand_ik])
        return {'FINISHED'}


class Rigify_Arm_IK2FK(bpy.types.Operator):
    """ Snaps an IK arm to an FK arm.
    """
    bl_idname = "pose.rigify_arm_ik2fk"
    bl_label = "Snap IK arm to FK"
    
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
        ik2fk(context.active_object, fk=[self.uarm_fk, self.farm_fk, self.hand_fk], ik=[self.uarm_ik, self.farm_ik, self.hand_ik, self.pole])
        return {'FINISHED'}


bpy.utils.register_class(Rigify_Arm_FK2IK)
bpy.utils.register_class(Rigify_Arm_IK2FK)


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

