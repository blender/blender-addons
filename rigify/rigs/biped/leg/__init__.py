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
import imp
from . import fk, ik, deform

imp.reload(fk)
imp.reload(ik)
imp.reload(deform)

script = """
fk_leg = ["%s", "%s", "%s", "%s"]
ik_leg = ["%s", "%s", "%s", "%s", "%s", "%s"]
if is_selected(fk_leg+ik_leg):
    layout.prop(pose_bones[ik_leg[2]], '["ikfk_switch"]', text="FK / IK (" + ik_leg[2] + ")", slider=True)
if is_selected(fk_leg):
    try:
        pose_bones[fk_leg[0]]["isolate"]
        layout.prop(pose_bones[fk_leg[0]], '["isolate"]', text="Isolate Rotation (" + fk_leg[0] + ")", slider=True)
    except KeyError:
        pass
if is_selected(fk_leg+ik_leg):
    p = layout.operator("pose.rigify_leg_fk2ik_" + rig_id, text="Snap FK->IK (" + fk_leg[0] + ")")
    p.thigh_fk = fk_leg[0]
    p.shin_fk  = fk_leg[1]
    p.foot_fk  = fk_leg[2]
    p.mfoot_fk = fk_leg[3]
    p.thigh_ik = ik_leg[0]
    p.shin_ik  = ik_leg[1]
    p.mfoot_ik = ik_leg[5]
    p = layout.operator("pose.rigify_leg_ik2fk_" + rig_id, text="Snap IK->FK (" + fk_leg[0] + ")")
    p.thigh_fk  = fk_leg[0]
    p.shin_fk   = fk_leg[1]
    p.mfoot_fk  = fk_leg[3]
    p.thigh_ik  = ik_leg[0]
    p.shin_ik   = ik_leg[1]
    p.foot_ik   = ik_leg[2]
    p.pole      = ik_leg[3]
    p.footroll  = ik_leg[4]
    p.mfoot_ik  = ik_leg[5]
"""


class Rig:
    """ A leg rig, with IK/FK switching, a hinge switch, and foot roll.

    """
    def __init__(self, obj, bone, params):
        """ Gather and validate data about the rig.
            Store any data or references to data that will be needed later on.
            In particular, store names of bones that will be needed.
            Do NOT change any data in the scene.  This is a gathering phase only.

        """
        # Gather deform rig
        self.deform_rig = deform.Rig(obj, bone, params)

        # Gather FK rig
        self.fk_rig = fk.Rig(obj, bone, params)

        # Gather IK rig
        self.ik_rig = ik.Rig(obj, bone, params, ikfk_switch=True)

    def generate(self):
        """ Generate the rig.
            Do NOT modify any of the original bones, except for adding constraints.
            The main armature should be selected and active before this is called.

        """
        self.deform_rig.generate()
        fk_controls = self.fk_rig.generate()
        ik_controls = self.ik_rig.generate()
        return [script % (fk_controls[0], fk_controls[1], fk_controls[2], fk_controls[3], ik_controls[0], ik_controls[1], ik_controls[2], ik_controls[3], ik_controls[4], ik_controls[5])]

    @classmethod
    def add_parameters(self, group):
        """ Add the parameters of this rig type to the
            RigifyParameters PropertyGroup

        """
        items = [('X', 'X', ''), ('Y', 'Y', ''), ('Z', 'Z', ''), ('-X', '-X', ''), ('-Y', '-Y', ''), ('-Z', '-Z', '')]
        group.primary_rotation_axis = bpy.props.EnumProperty(items=items, name="Primary Rotation Axis", default='X')

        group.bend_hint = bpy.props.BoolProperty(name="Bend Hint", default=True, description="Give IK chain a hint about which way to bend (useful for perfectly straight chains)")

        group.separate_ik_layers = bpy.props.BoolProperty(name="Separate IK Control Layers:", default=False, description="Enable putting the ik controls on a separate layer from the fk controls")
        group.ik_layers = bpy.props.BoolVectorProperty(size=32, description="Layers for the ik controls to be on")

        group.use_thigh_twist = bpy.props.BoolProperty(name="Thigh Twist", default=True, description="Generate the dual-bone twist setup for the thigh")
        group.use_shin_twist = bpy.props.BoolProperty(name="Shin Twist", default=True, description="Generate the dual-bone twist setup for the shin")

    @classmethod
    def parameters_ui(self, layout, obj, bone):
        """ Create the ui for the rig parameters.

        """
        params = obj.pose.bones[bone].rigify_parameters[0]

        r = layout.row()
        r.prop(params, "separate_ik_layers")

        r = layout.row()
        r.active = params.separate_ik_layers

        col = r.column(align=True)
        row = col.row(align=True)
        row.prop(params, "ik_layers", index=0, toggle=True, text="")
        row.prop(params, "ik_layers", index=1, toggle=True, text="")
        row.prop(params, "ik_layers", index=2, toggle=True, text="")
        row.prop(params, "ik_layers", index=3, toggle=True, text="")
        row.prop(params, "ik_layers", index=4, toggle=True, text="")
        row.prop(params, "ik_layers", index=5, toggle=True, text="")
        row.prop(params, "ik_layers", index=6, toggle=True, text="")
        row.prop(params, "ik_layers", index=7, toggle=True, text="")
        row = col.row(align=True)
        row.prop(params, "ik_layers", index=16, toggle=True, text="")
        row.prop(params, "ik_layers", index=17, toggle=True, text="")
        row.prop(params, "ik_layers", index=18, toggle=True, text="")
        row.prop(params, "ik_layers", index=19, toggle=True, text="")
        row.prop(params, "ik_layers", index=20, toggle=True, text="")
        row.prop(params, "ik_layers", index=21, toggle=True, text="")
        row.prop(params, "ik_layers", index=22, toggle=True, text="")
        row.prop(params, "ik_layers", index=23, toggle=True, text="")

        col = r.column(align=True)
        row = col.row(align=True)
        row.prop(params, "ik_layers", index=8, toggle=True, text="")
        row.prop(params, "ik_layers", index=9, toggle=True, text="")
        row.prop(params, "ik_layers", index=10, toggle=True, text="")
        row.prop(params, "ik_layers", index=11, toggle=True, text="")
        row.prop(params, "ik_layers", index=12, toggle=True, text="")
        row.prop(params, "ik_layers", index=13, toggle=True, text="")
        row.prop(params, "ik_layers", index=14, toggle=True, text="")
        row.prop(params, "ik_layers", index=15, toggle=True, text="")
        row = col.row(align=True)
        row.prop(params, "ik_layers", index=24, toggle=True, text="")
        row.prop(params, "ik_layers", index=25, toggle=True, text="")
        row.prop(params, "ik_layers", index=26, toggle=True, text="")
        row.prop(params, "ik_layers", index=27, toggle=True, text="")
        row.prop(params, "ik_layers", index=28, toggle=True, text="")
        row.prop(params, "ik_layers", index=29, toggle=True, text="")
        row.prop(params, "ik_layers", index=30, toggle=True, text="")
        row.prop(params, "ik_layers", index=31, toggle=True, text="")

        r = layout.row()
        r.label(text="Knee rotation axis:")
        r.prop(params, "primary_rotation_axis", text="")

        r = layout.row()
        r.prop(params, "bend_hint")

        col = layout.column()
        col.prop(params, "use_thigh_twist")
        col.prop(params, "use_shin_twist")

    @classmethod
    def create_sample(self, obj):
        # generated by rigify.utils.write_meta_rig
        bpy.ops.object.mode_set(mode='EDIT')
        arm = obj.data

        bones = {}

        bone = arm.edit_bones.new('thigh')
        bone.head[:] = -0.0000, 0.0000, 1.0000
        bone.tail[:] = -0.0000, -0.0500, 0.5000
        bone.roll = -0.0000
        bone.use_connect = False
        bones['thigh'] = bone.name
        bone = arm.edit_bones.new('shin')
        bone.head[:] = -0.0000, -0.0500, 0.5000
        bone.tail[:] = -0.0000, 0.0000, 0.1000
        bone.roll = -0.0000
        bone.use_connect = True
        bone.parent = arm.edit_bones[bones['thigh']]
        bones['shin'] = bone.name
        bone = arm.edit_bones.new('foot')
        bone.head[:] = -0.0000, 0.0000, 0.1000
        bone.tail[:] = 0.0000, -0.1200, 0.0300
        bone.roll = 0.0000
        bone.use_connect = True
        bone.parent = arm.edit_bones[bones['shin']]
        bones['foot'] = bone.name
        bone = arm.edit_bones.new('heel')
        bone.head[:] = -0.0000, 0.0000, 0.1000
        bone.tail[:] = -0.0000, 0.0600, 0.0000
        bone.roll = -0.0000
        bone.use_connect = True
        bone.parent = arm.edit_bones[bones['shin']]
        bones['heel'] = bone.name
        bone = arm.edit_bones.new('heel.02')
        bone.head[:] = -0.0500, -0.0200, 0.0000
        bone.tail[:] = 0.0500, -0.0200, 0.0000
        bone.roll = 0.0000
        bone.use_connect = False
        bone.parent = arm.edit_bones[bones['heel']]
        bones['heel.02'] = bone.name
        bone = arm.edit_bones.new('toe')
        bone.head[:] = 0.0000, -0.1200, 0.0300
        bone.tail[:] = 0.0000, -0.2000, 0.0300
        bone.roll = 3.1416
        bone.use_connect = True
        bone.parent = arm.edit_bones[bones['foot']]
        bones['toe'] = bone.name

        bpy.ops.object.mode_set(mode='OBJECT')
        pbone = obj.pose.bones[bones['thigh']]
        pbone.rigify_type = 'biped.leg'
        pbone.lock_location = (True, True, True)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'
        pbone.rigify_parameters.add()
        pbone = obj.pose.bones[bones['shin']]
        pbone.rigify_type = ''
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'
        pbone = obj.pose.bones[bones['foot']]
        pbone.rigify_type = ''
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'
        pbone = obj.pose.bones[bones['heel']]
        pbone.rigify_type = ''
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'
        pbone = obj.pose.bones[bones['toe']]
        pbone.rigify_type = ''
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'

        bpy.ops.object.mode_set(mode='EDIT')
        for bone in arm.edit_bones:
            bone.select = False
            bone.select_head = False
            bone.select_tail = False
        for b in bones:
            bone = arm.edit_bones[bones[b]]
            bone.select = True
            bone.select_head = True
            bone.select_tail = True
            arm.edit_bones.active = bone
