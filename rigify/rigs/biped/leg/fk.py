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
from rigify.utils import MetarigError
from rigify.utils import copy_bone
from rigify.utils import connected_children_names, has_connected_children
from rigify.utils import strip_org, make_mechanism_name
from rigify.utils import get_layers
from rigify.utils import create_widget, create_limb_widget
from rna_prop_ui import rna_idprop_ui_prop_get


class Rig:
    """ An FK leg rig, with hinge switch.

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
            raise MetarigError("RIGIFY ERROR: Bone '%s': incorrect bone configuration for rig type" % (strip_org(bone)))

        # Get the foot and heel
        foot = None
        heel = None
        for b in self.obj.data.bones[leg_bones[1]].children:
            if b.use_connect is True:
                if len(b.children) >= 1 and has_connected_children(b):
                    foot = b.name
                else:
                    heel = b.name

        if foot is None or heel is None:
            raise MetarigError("RIGIFY ERROR: Bone '%s': incorrect bone configuration for rig type" % (strip_org(bone)))

        # Get the toe
        toe = None
        for b in self.obj.data.bones[foot].children:
            if b.use_connect is True:
                toe = b.name

        # Get the toe
        if toe is None:
            raise MetarigError("RIGIFY ERROR: Bone '%s': incorrect bone configuration for rig type" % (strip_org(bone)))

        self.org_bones = leg_bones + [foot, toe, heel]

        # Get (optional) parent
        if self.obj.data.bones[bone].parent is None:
            self.org_parent = None
        else:
            self.org_parent = self.obj.data.bones[bone].parent.name

        # Get rig parameters
        if "layers" in params:
            self.layers = get_layers(params["layers"])
        else:
            self.layers = None

        self.primary_rotation_axis = params.primary_rotation_axis

    def generate(self):
        """ Generate the rig.
            Do NOT modify any of the original bones, except for adding constraints.
            The main armature should be selected and active before this is called.

        """
        bpy.ops.object.mode_set(mode='EDIT')

        # Create the control bones
        thigh = copy_bone(self.obj, self.org_bones[0], strip_org(self.org_bones[0]))
        shin = copy_bone(self.obj, self.org_bones[1], strip_org(self.org_bones[1]))
        foot = copy_bone(self.obj, self.org_bones[2], strip_org(self.org_bones[2]))

        # Create the foot mechanism bone
        foot_mch = copy_bone(self.obj, self.org_bones[2], make_mechanism_name(strip_org(self.org_bones[2])))

        # Create the hinge bones
        if self.org_parent != None:
            hinge = copy_bone(self.obj, self.org_parent, make_mechanism_name(thigh + ".hinge"))
            socket1 = copy_bone(self.obj, thigh, make_mechanism_name(thigh + ".socket1"))
            socket2 = copy_bone(self.obj, thigh, make_mechanism_name(thigh + ".socket2"))

        # Get edit bones
        eb = self.obj.data.edit_bones

        thigh_e = eb[thigh]
        shin_e = eb[shin]
        foot_e = eb[foot]
        foot_mch_e = eb[foot_mch]

        if self.org_parent != None:
            hinge_e = eb[hinge]
            socket1_e = eb[socket1]
            socket2_e = eb[socket2]

        # Parenting
        shin_e.parent = thigh_e
        foot_e.parent = shin_e

        foot_mch_e.use_connect = False
        foot_mch_e.parent = foot_e

        if self.org_parent != None:
            hinge_e.use_connect = False
            socket1_e.use_connect = False
            socket2_e.use_connect = False

            thigh_e.parent = hinge_e
            hinge_e.parent = socket2_e
            socket2_e.parent = None

        # Positioning
        vec = Vector(eb[self.org_bones[3]].vector)
        vec.normalize()
        foot_e.tail = foot_e.head + (vec * foot_e.length)
        foot_e.roll = eb[self.org_bones[3]].roll

        if self.org_parent != None:
            center = (hinge_e.head + hinge_e.tail) / 2
            hinge_e.head = center
            socket1_e.length /= 4
            socket2_e.length /= 3

        # Object mode, get pose bones
        bpy.ops.object.mode_set(mode='OBJECT')
        pb = self.obj.pose.bones

        thigh_p = pb[thigh]
        shin_p = pb[shin]
        foot_p = pb[foot]
        if self.org_parent != None:
            hinge_p = pb[hinge]

        if self.org_parent != None:
            # socket1_p = pb[socket1]  # UNUSED
            socket2_p = pb[socket2]

        # Set the knee to only bend on the x-axis.
        shin_p.rotation_mode = 'XYZ'
        if 'X' in self.primary_rotation_axis:
            shin_p.lock_rotation = (False, True, True)
        elif 'Y' in self.primary_rotation_axis:
            shin_p.lock_rotation = (True, False, True)
        else:
            shin_p.lock_rotation = (True, True, False)

        # Hinge transforms are locked, for auto-ik
        if self.org_parent != None:
            hinge_p.lock_location = True, True, True
            hinge_p.lock_rotation = True, True, True
            hinge_p.lock_rotation_w = True
            hinge_p.lock_scale = True, True, True

        # Set up custom properties
        if self.org_parent != None:
            prop = rna_idprop_ui_prop_get(thigh_p, "isolate", create=True)
            thigh_p["isolate"] = 0.0
            prop["soft_min"] = prop["min"] = 0.0
            prop["soft_max"] = prop["max"] = 1.0

        # Hinge constraints / drivers
        if self.org_parent != None:
            con = socket2_p.constraints.new('COPY_LOCATION')
            con.name = "copy_location"
            con.target = self.obj
            con.subtarget = socket1

            con = socket2_p.constraints.new('COPY_TRANSFORMS')
            con.name = "isolate_off"
            con.target = self.obj
            con.subtarget = socket1

            # Driver
            fcurve = con.driver_add("influence")
            driver = fcurve.driver
            var = driver.variables.new()
            driver.type = 'AVERAGE'
            var.name = "var"
            var.targets[0].id_type = 'OBJECT'
            var.targets[0].id = self.obj
            var.targets[0].data_path = thigh_p.path_from_id() + '["isolate"]'
            mod = fcurve.modifiers[0]
            mod.poly_order = 1
            mod.coefficients[0] = 1.0
            mod.coefficients[1] = -1.0

        # Constrain org bones to controls
        con = pb[self.org_bones[0]].constraints.new('COPY_TRANSFORMS')
        con.name = "fk"
        con.target = self.obj
        con.subtarget = thigh

        con = pb[self.org_bones[1]].constraints.new('COPY_TRANSFORMS')
        con.name = "fk"
        con.target = self.obj
        con.subtarget = shin

        con = pb[self.org_bones[2]].constraints.new('COPY_TRANSFORMS')
        con.name = "fk"
        con.target = self.obj
        con.subtarget = foot_mch

        # Set layers if specified
        if self.layers:
            thigh_p.bone.layers = self.layers
            shin_p.bone.layers = self.layers
            foot_p.bone.layers = self.layers

        # Create control widgets
        create_limb_widget(self.obj, thigh)
        create_limb_widget(self.obj, shin)

        ob = create_widget(self.obj, foot)
        if ob != None:
            verts = [(0.7, 1.5, 0.0), (0.7, -0.25, 0.0), (-0.7, -0.25, 0.0), (-0.7, 1.5, 0.0), (0.7, 0.723, 0.0), (-0.7, 0.723, 0.0), (0.7, 0.0, 0.0), (-0.7, 0.0, 0.0)]
            edges = [(1, 2), (0, 3), (0, 4), (3, 5), (4, 6), (1, 6), (5, 7), (2, 7)]
            mesh = ob.data
            mesh.from_pydata(verts, edges, [])
            mesh.update()

            mod = ob.modifiers.new("subsurf", 'SUBSURF')
            mod.levels = 2

        return [thigh, shin, foot, foot_mch]
