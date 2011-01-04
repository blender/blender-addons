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

import bpy
from mathutils import Vector
from rigify.utils import MetarigError
from rigify.utils import copy_bone, flip_bone, put_bone
from rigify.utils import connected_children_names
from rigify.utils import strip_org, make_mechanism_name, make_deformer_name
from rigify.utils import obj_to_bone, create_circle_widget
from rna_prop_ui import rna_idprop_ui_prop_get


script = """
hips = "%s"
ribs = "%s"
if is_selected([hips, ribs]):
    layout.prop(pose_bones[ribs], '["pivot_slide"]', text="Pivot Slide (" + ribs + ")", slider=True)
if is_selected(ribs):
    layout.prop(pose_bones[ribs], '["isolate"]', text="Isolate Rotation (" + ribs + ")", slider=True)
"""


class Rig:
    """ A "spine" rig.  It turns a chain of bones into a rig with two controls:
        One for the hips, and one for the rib cage.

    """
    def __init__(self, obj, bone_name, params):
        """ Gather and validate data about the rig.

        """
        self.obj = obj
        self.org_bones = [bone_name] + connected_children_names(obj, bone_name)
        self.params = params

        if len(self.org_bones) <= 1:
            raise MetarigError("RIGIFY ERROR: Bone '%s': input to rig type must be a chain of 2 or more bones." % (strip_org(bone)))

    def gen_deform(self):
        """ Generate the deformation rig.

        """
        for name in self.org_bones:
            bpy.ops.object.mode_set(mode='EDIT')
            eb = self.obj.data.edit_bones

            # Create deform bone
            bone_e = eb[copy_bone(self.obj, name)]

            # Change its name
            bone_e.name = make_deformer_name(strip_org(name))
            bone_name = bone_e.name

            # Leave edit mode
            bpy.ops.object.mode_set(mode='OBJECT')

            # Get the pose bone
            bone = self.obj.pose.bones[bone_name]

            # Constrain to the original bone
            con = bone.constraints.new('COPY_TRANSFORMS')
            con.name = "copy_transforms"
            con.target = self.obj
            con.subtarget = name

    def gen_control(self):
        """ Generate the control rig.

        """
        #---------------------------------
        # Create the hip and rib controls
        bpy.ops.object.mode_set(mode='EDIT')

        # Copy org bones
        hip_control = copy_bone(self.obj, self.org_bones[0], strip_org(self.org_bones[0]))
        rib_control = copy_bone(self.obj, self.org_bones[-1], strip_org(self.org_bones[-1]))
        rib_mch = copy_bone(self.obj, self.org_bones[-1], make_mechanism_name(strip_org(self.org_bones[-1] + ".follow")))
        hinge = copy_bone(self.obj, self.org_bones[0], make_mechanism_name(strip_org(self.org_bones[-1]) + ".hinge"))

        eb = self.obj.data.edit_bones

        hip_control_e = eb[hip_control]
        rib_control_e = eb[rib_control]
        rib_mch_e = eb[rib_mch]
        hinge_e = eb[hinge]

        # Parenting
        hip_control_e.use_connect = False
        rib_control_e.use_connect = False
        rib_mch_e.use_connect = False
        hinge_e.use_connect = False

        hinge_e.parent = None
        rib_control_e.parent = hinge_e
        rib_mch_e.parent = rib_control_e

        # Position
        flip_bone(self.obj, hip_control)
        flip_bone(self.obj, hinge)

        hinge_e.length /= 2
        rib_mch_e.length /= 2

        put_bone(self.obj, rib_control, hip_control_e.head)
        put_bone(self.obj, rib_mch, hip_control_e.head)

        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.object.mode_set(mode='EDIT')
        eb = self.obj.data.edit_bones

        # Switch to object mode
        bpy.ops.object.mode_set(mode='OBJECT')
        pb = self.obj.pose.bones
        hip_control_p = pb[hip_control]
        rib_control_p = pb[rib_control]
        hinge_p = pb[hinge]

        # No translation on rib control
        rib_control_p.lock_location = [True, True, True]

        # Hip does not use local location
        hip_control_p.bone.use_local_location = False

        # Custom hinge property
        prop = rna_idprop_ui_prop_get(rib_control_p, "isolate", create=True)
        rib_control_p["isolate"] = 1.0
        prop["soft_min"] = prop["min"] = 0.0
        prop["soft_max"] = prop["max"] = 1.0

        # Constraints
        con = hinge_p.constraints.new('COPY_LOCATION')
        con.name = "copy_location"
        con.target = self.obj
        con.subtarget = hip_control

        con1 = hinge_p.constraints.new('COPY_ROTATION')
        con1.name = "isolate_off.01"
        con1.target = self.obj
        con1.subtarget = hip_control

        con2 = rib_control_p.constraints.new('COPY_SCALE')
        con2.name = "isolate_off.02"
        con2.target = self.obj
        con2.subtarget = hip_control
        con2.use_offset = True
        con2.target_space = 'LOCAL'
        con2.owner_space = 'LOCAL'

        # Drivers for "isolate_off"
        fcurve = con1.driver_add("influence")
        driver = fcurve.driver
        var = driver.variables.new()
        driver.type = 'AVERAGE'
        var.name = "var"
        var.targets[0].id_type = 'OBJECT'
        var.targets[0].id = self.obj
        var.targets[0].data_path = rib_control_p.path_from_id() + '["isolate"]'
        mod = fcurve.modifiers[0]
        mod.poly_order = 1
        mod.coefficients[0] = 1.0
        mod.coefficients[1] = -1.0

        fcurve = con2.driver_add("influence")
        driver = fcurve.driver
        var = driver.variables.new()
        driver.type = 'AVERAGE'
        var.name = "var"
        var.targets[0].id_type = 'OBJECT'
        var.targets[0].id = self.obj
        var.targets[0].data_path = rib_control_p.path_from_id() + '["isolate"]'
        mod = fcurve.modifiers[0]
        mod.poly_order = 1
        mod.coefficients[0] = 1.0
        mod.coefficients[1] = -1.0

        # Appearence
        hip_control_p.custom_shape_transform = pb[self.org_bones[0]]
        rib_control_p.custom_shape_transform = pb[self.org_bones[-1]]

        #-------------------------
        # Create flex spine chain

        # Create bones/parenting/positiong
        bpy.ops.object.mode_set(mode='EDIT')
        flex_bones = []
        flex_helpers = []
        prev_bone = None
        for b in self.org_bones:
            # Create bones
            bone = copy_bone(self.obj, b, make_mechanism_name(strip_org(b) + ".flex"))
            helper = copy_bone(self.obj, rib_mch, make_mechanism_name(strip_org(b) + ".flex_h"))
            flex_bones += [bone]
            flex_helpers += [helper]

            eb = self.obj.data.edit_bones
            bone_e = eb[bone]
            helper_e = eb[helper]

            # Parenting
            bone_e.use_connect = False
            helper_e.use_connect = False
            if prev_bone == None:
                helper_e.parent = eb[hip_control]
            bone_e.parent = helper_e

            # Position
            put_bone(self.obj, helper, bone_e.head)
            helper_e.length /= 4

            prev_bone = bone

        # Constraints
        bpy.ops.object.mode_set(mode='OBJECT')
        pb = self.obj.pose.bones
        rib_control_p = pb[rib_control]
        rib_mch_p = pb[rib_mch]

        inc = 1.0 / (len(flex_helpers) - 1)
        inf = 1.0 / (len(flex_helpers) - 1)
        for b in zip(flex_helpers[1:], flex_bones[:-1], self.org_bones[1:]):
            bone_p = pb[b[0]]

            # Scale constraints
            con = bone_p.constraints.new('COPY_SCALE')
            con.name = "copy_scale1"
            con.target = self.obj
            con.subtarget = flex_helpers[0]
            con.influence = 1.0

            con = bone_p.constraints.new('COPY_SCALE')
            con.name = "copy_scale2"
            con.target = self.obj
            con.subtarget = rib_mch
            con.influence = inf

            # Bend constraints
            con = bone_p.constraints.new('COPY_ROTATION')
            con.name = "bend1"
            con.target = self.obj
            con.subtarget = flex_helpers[0]
            con.influence = 1.0

            con = bone_p.constraints.new('COPY_ROTATION')
            con.name = "bend2"
            con.target = self.obj
            con.subtarget = rib_mch
            con.influence = inf

            # If not the rib control
            if b[0] != flex_helpers[-1]:
                # Custom bend property
                prop_name = "bend_" + strip_org(b[2])
                prop = rna_idprop_ui_prop_get(rib_control_p, prop_name, create=True)
                rib_control_p[prop_name] = inf
                prop["min"] = 0.0
                prop["max"] = 1.0
                prop["soft_min"] = 0.0
                prop["soft_max"] = 1.0

                # Bend driver
                fcurve = con.driver_add("influence")
                driver = fcurve.driver
                var = driver.variables.new()
                driver.type = 'AVERAGE'
                var.name = prop_name
                var.targets[0].id_type = 'OBJECT'
                var.targets[0].id = self.obj
                var.targets[0].data_path = rib_control_p.path_from_id() + '["' + prop_name + '"]'

            # Location constraint
            con = bone_p.constraints.new('COPY_LOCATION')
            con.name = "copy_location"
            con.target = self.obj
            con.subtarget = b[1]
            con.head_tail = 1.0

            inf += inc

        #----------------------------
        # Create reverse spine chain

        # Create bones/parenting/positioning
        bpy.ops.object.mode_set(mode='EDIT')
        rev_bones = []
        prev_bone = None
        for b in zip(flex_bones, self.org_bones):
            # Create bones
            bone = copy_bone(self.obj, b[1], make_mechanism_name(strip_org(b[1]) + ".reverse"))
            rev_bones += [bone]
            eb = self.obj.data.edit_bones
            bone_e = eb[bone]

            # Parenting
            bone_e.use_connect = False
            bone_e.parent = eb[b[0]]

            # Position
            flip_bone(self.obj, bone)
            bone_e.tail = Vector(eb[b[0]].head)
            #bone_e.head = Vector(eb[b[0]].tail)
            if prev_bone == None:
                pass  # Position base bone wherever you want, for now do nothing (i.e. position at hips)
            else:
                put_bone(self.obj, bone, eb[prev_bone].tail)

            prev_bone = bone

        # Constraints
        bpy.ops.object.mode_set(mode='OBJECT')
        pb = self.obj.pose.bones
        prev_bone = None
        for bone in rev_bones:
            bone_p = pb[bone]

            con = bone_p.constraints.new('COPY_LOCATION')
            con.name = "copy_location"
            con.target = self.obj
            if prev_bone == None:
                con.subtarget = hip_control  # Position base bone wherever you want, for now hips
            else:
                con.subtarget = prev_bone
                con.head_tail = 1.0
            prev_bone = bone

        #---------------------------------------------
        # Constrain org bones to flex bone's rotation
        pb = self.obj.pose.bones
        for b in zip(self.org_bones, flex_bones):
            con = pb[b[0]].constraints.new('COPY_TRANSFORMS')
            con.name = "copy_rotation"
            con.target = self.obj
            con.subtarget = b[1]

        #---------------------------
        # Create pivot slide system
        pb = self.obj.pose.bones
        bone_p = pb[self.org_bones[0]]
        rib_control_p = pb[rib_control]

        # Custom pivot_slide property
        prop = rna_idprop_ui_prop_get(rib_control_p, "pivot_slide", create=True)
        rib_control_p["pivot_slide"] = 1.0 / len(self.org_bones)
        prop["min"] = 0.0
        prop["max"] = 1.0
        prop["soft_min"] = 1.0 / len(self.org_bones)
        prop["soft_max"] = 1.0 - (1.0 / len(self.org_bones))

        # Anchor constraint
        con = bone_p.constraints.new('COPY_LOCATION')
        con.name = "copy_location"
        con.target = self.obj
        con.subtarget = rev_bones[0]

        # Slide constraints
        i = 1
        tot = len(rev_bones)
        for rb in rev_bones:
            con = bone_p.constraints.new('COPY_LOCATION')
            con.name = "slide." + str(i)
            con.target = self.obj
            con.subtarget = rb
            con.head_tail = 1.0

            # Driver
            fcurve = con.driver_add("influence")
            driver = fcurve.driver
            var = driver.variables.new()
            driver.type = 'AVERAGE'
            var.name = "slide"
            var.targets[0].id_type = 'OBJECT'
            var.targets[0].id = self.obj
            var.targets[0].data_path = rib_control_p.path_from_id() + '["pivot_slide"]'
            mod = fcurve.modifiers[0]
            mod.poly_order = 1
            mod.coefficients[0] = 1 - i
            mod.coefficients[1] = tot

            i += 1

        # Create control widgets
        w1 = create_circle_widget(self.obj, hip_control, radius=1.0, head_tail=1.0)
        w2 = create_circle_widget(self.obj, rib_control, radius=1.0, head_tail=0.0)

        if w1 != None:
            obj_to_bone(w1, self.obj, self.org_bones[0])
        if w2 != None:
            obj_to_bone(w2, self.obj, self.org_bones[-1])

        # Return control names
        return hip_control, rib_control

    def generate(self):
        """ Generate the rig.
            Do NOT modify any of the original bones, except for adding constraints.
            The main armature should be selected and active before this is called.

        """
        self.gen_deform()
        hips, ribs = self.gen_control()

        return [script % (hips, ribs)]

    @classmethod
    def create_sample(self, obj):
        # generated by rigify.utils.write_metarig
        bpy.ops.object.mode_set(mode='EDIT')
        arm = obj.data

        bones = {}

        bone = arm.edit_bones.new('hips')
        bone.head[:] = 0.0000, 0.0000, 0.0000
        bone.tail[:] = -0.0000, -0.0590, 0.2804
        bone.roll = -0.0000
        bone.use_connect = False
        bones['hips'] = bone.name
        bone = arm.edit_bones.new('spine')
        bone.head[:] = -0.0000, -0.0590, 0.2804
        bone.tail[:] = 0.0000, 0.0291, 0.5324
        bone.roll = 0.0000
        bone.use_connect = True
        bone.parent = arm.edit_bones[bones['hips']]
        bones['spine'] = bone.name
        bone = arm.edit_bones.new('ribs')
        bone.head[:] = 0.0000, 0.0291, 0.5324
        bone.tail[:] = -0.0000, 0.0000, 1.0000
        bone.roll = -0.0000
        bone.use_connect = True
        bone.parent = arm.edit_bones[bones['spine']]
        bones['ribs'] = bone.name

        bpy.ops.object.mode_set(mode='OBJECT')
        pbone = obj.pose.bones[bones['hips']]
        pbone.rigify_type = 'spine'
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'
        pbone = obj.pose.bones[bones['spine']]
        pbone.rigify_type = ''
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'
        pbone = obj.pose.bones[bones['ribs']]
        pbone.rigify_type = ''
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'
        pbone = obj.pose.bones[bones['hips']]
        pbone['rigify_type'] = 'spine'

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

