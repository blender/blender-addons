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

bl_info = {
    "name": "Skinify Rig",
    "author": "Albert Makac (karab44)",
    "version": (0, 8),
    "blender": (2, 7, 8),
    "location": "Properties > Bone > Skinify Rig (visible on pose mode only)",
    "description": "Creates a mesh object from selected bones",
    "warning": "",
    "wiki_url": "https://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Object/Skinify",
    "category": "Object"}

# NOTE: there are some unused scene variables around commented out
# is the persintent scene props needed or can a property group be used instead?

import bpy
from bpy.props import (
        FloatProperty,
        IntProperty,
        BoolProperty
        )
# from bpy_extras import object_utils
from mathutils import Vector, Euler
from bpy.app.handlers import persistent

bpy.types.Scene.sub_level = IntProperty(
                                name="sub_level",
                                min=0, max=4,
                                default=1,
                                description="mesh density"
                                )
bpy.types.Scene.thickness = FloatProperty(
                                name="thickness",
                                min=0.01,
                                default=0.8,
                                description="adjust shape thickness"
                                )
bpy.types.Scene.finger_thickness = FloatProperty(
                                name="finger_thickness",
                                min=0.01, max=1.0,
                                default=0.25,
                                description="adjust finger thickness relative to body"
                                )
bpy.types.Scene.connect_mesh = BoolProperty(
                                name="solid_shape",
                                default=False,
                                description="makes solid shape from bone chains"
                                )
bpy.types.Scene.connect_parents = BoolProperty(
                                name="fill_gaps",
                                default=False,
                                description="fills the gaps between parented bones"
                                )
bpy.types.Scene.generate_all = BoolProperty(
                                name="all_shapes",
                                default=False,
                                description="generates shapes from all bones"
                                )
bpy.types.Scene.head_ornaments = BoolProperty(
                                name="head_ornaments",
                                default=False,
                                description="includes head ornaments"
                                )
bpy.types.Scene.apply_mod = BoolProperty(
                                name="apply_modifiers",
                                default=True,
                                description="applies Modifiers to mesh"
                                )
bpy.types.Scene.parent_armature = BoolProperty(
                                name="parent_armature",
                                default=True,
                                description="applies mesh to Armature"
                                )


# initialize properties
def init_props():
    scn = bpy.context.scene

    scn.connect_mesh = False
    scn.connect_parents = False
    scn.generate_all = False
    scn.thickness = 0.8
    scn.finger_thickness = 0.25
    scn.apply_mod = True
    scn.parent_armature = True
    scn.sub_level = 1


# selects vertices
def select_vertices(mesh_obj, idx):
    bpy.context.scene.objects.active = mesh_obj
    mode = mesh_obj.mode
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    for i in idx:
        mesh_obj.data.vertices[i].select = True

    selectedVerts = [v.index for v in mesh_obj.data.vertices if v.select]

    bpy.ops.object.mode_set(mode=mode)
    return selectedVerts


# generates edges from vertices used by skin modifier
def generate_edges(mesh, shape_object, bones, scale, connect_mesh=False, connect_parents=False,
                   head_ornaments=False, generate_all=False):
    """
    This function adds vertices for all heads and tails
    """
    # scene preferences
    # scn = bpy.context.scene

    # detect the head, face, hands, breast, heels or other exceptionary bones to exclusion or customization
    common_ignore_list = ['eye', 'heel', 'breast', 'root']

    # bvh_ignore_list = []
    rigify_ignore_list = []
    pitchipoy_ignore_list = ['face', 'breast', 'pelvis', 'nose', 'lip', 'jaw', 'chin', 'ear.', 'brow',
                            'lid', 'forehead', 'temple', 'cheek', 'teeth', 'tongue']

    alternate_scale_list = []
    # rig_type rigify = 1, pitchipoy = 2
    rig_type = 0
    me = mesh
    verts = []
    edges = []
    idx = 0
    alternate_scale_idx_list = list()

    ignore_list = common_ignore_list
    # detect rig type
    for b in bones:
        if b.name == 'hips' and b.rigify_type == 'spine':
            ignore_list = ignore_list + rigify_ignore_list
            rig_type = 1
            break
        if b.name == 'spine' and b.rigify_type == 'pitchipoy.super_torso_turbo':
            ignore_list = ignore_list + pitchipoy_ignore_list
            rig_type = 2
            break

    # edge generator loop
    for b in bones:
        # look for rig's hands and their childs
        if 'hand' in b.name.lower():
            # prepare the list
            for c in b.children_recursive:
                alternate_scale_list.append(c.name)

        found = False

        for i in ignore_list:
            if i in b.name.lower():

                found = True
                break

        if found and generate_all is False:
            continue
            
        #fix for drawing rootbone and relationship lines
        if 'root' in b.name.lower() and generate_all is False:
            continue
                    

        # ignore any head ornaments
        if head_ornaments is False:
            if b.parent is not None:
                if 'head' in b.parent.name.lower():
                    continue

        if connect_parents:
            if b.parent is not None and b.parent.bone.select is True and b.bone.use_connect is False:
                if 'root' in b.parent.name.lower() and generate_all is False:
                    continue
                #ignore shoulder
                if 'shoulder' in b.name.lower() and connect_mesh is True:
                    continue
                #connect the upper arm directly with chest ommiting shoulders    
                if 'shoulder' in b.parent.name.lower() and connect_mesh is True:
                    vert1 = b.head
                    vert2 = b.parent.parent.tail                
                
                else:
                    vert1 = b.head
                    vert2 = b.parent.tail
                
                verts.append(vert1)
                verts.append(vert2)
                edges.append([idx, idx + 1])

                # also make list of edges made of gaps between the bones
                for a in alternate_scale_list:
                    if b.name == a:
                        alternate_scale_idx_list.append(idx)
                        alternate_scale_idx_list.append(idx + 1)

                idx = idx + 2
            # for bvh free floating hips and hips correction for rigify and pitchipoy
            if ((generate_all is False and 'hip' in b.name.lower()) or
              (generate_all is False and (b.name == 'hips' and rig_type == 1) or
              (b.name == 'spine' and rig_type == 2))):
                continue
                
        
        vert1 = b.head
        vert2 = b.tail
        verts.append(vert1)
        verts.append(vert2)

        edges.append([idx, idx + 1])

        for a in alternate_scale_list:
            if b.name == a:
                alternate_scale_idx_list.append(idx)
                alternate_scale_idx_list.append(idx + 1)

        idx = idx + 2

    # Create mesh from given verts, faces
    me.from_pydata(verts, edges, [])
    # Update mesh with new data
    me.update()

    # set object scale exact as armature's scale
    shape_object.scale = scale

    return alternate_scale_idx_list, rig_type


def generate_mesh(shape_object, size, thickness=0.8, finger_thickness=0.25, sub_level=1,
                  connect_mesh=False, connect_parents=False, generate_all=False, apply_mod=True,
                  alternate_scale_idx_list=[], rig_type=0):
    """
    This function adds modifiers for generated edges
    """
    # scn = bpy.context.scene

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')

    # add skin modifier
    shape_object.modifiers.new("Skin", 'SKIN')
    bpy.ops.mesh.select_all(action='SELECT')

    override = bpy.context.copy()
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for region in area.regions:
                if region.type == 'WINDOW':
                    override['area'] = area
                    override['region'] = region
                    override['edit_object'] = bpy.context.edit_object
                    override['scene'] = bpy.context.scene
                    override['active_object'] = shape_object
                    override['object'] = shape_object
                    override['modifier'] = bpy.context.object.modifiers
                    break

    # calculate optimal thickness for defaults
    bpy.ops.object.skin_root_mark(override)
    bpy.ops.transform.skin_resize(override,
                    value=(1 * thickness * (size / 10), 1 * thickness * (size / 10), 1 * thickness * (size / 10)),
                    constraint_axis=(False, False, False), constraint_orientation='GLOBAL',
                    mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH',
                    proportional_size=1)
    shape_object.modifiers["Skin"].use_smooth_shade = True
    shape_object.modifiers["Skin"].use_x_symmetry = True

    # select finger vertices and calculate optimal thickness for fingers to fix proportions
    if len(alternate_scale_idx_list) > 0:
        select_vertices(shape_object, alternate_scale_idx_list)

        bpy.ops.object.skin_loose_mark_clear(override, action='MARK')
        # by default set fingers thickness to 25 percent of body thickness
        bpy.ops.transform.skin_resize(override,
                                    value=(finger_thickness, finger_thickness, finger_thickness),
                                    constraint_axis=(False, False, False), constraint_orientation='GLOBAL',
                                    mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH',
                                    proportional_size=1)
        # make loose hands only for better topology

    # bpy.ops.mesh.select_all(action='DESELECT')

    if connect_mesh:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles()

    # fix rigify and pitchipoy hands topology
    if connect_mesh and connect_parents and generate_all is False and rig_type > 0:
        # thickness will set palm vertex for both hands look pretty
        corrective_thickness = 2.5
        # left hand verts
        merge_idx = []
        if rig_type == 1:            
            merge_idx = [7, 8, 13, 17, 22, 27]
        else:           
            merge_idx = [9, 14, 18, 23, 24, 29]
        select_vertices(shape_object, merge_idx)
        bpy.ops.mesh.merge(type='CENTER')
        bpy.ops.transform.skin_resize(override,
                                    value=(corrective_thickness, corrective_thickness, corrective_thickness),
                                    constraint_axis=(False, False, False), constraint_orientation='GLOBAL',
                                    mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH',
                                    proportional_size=1)
        bpy.ops.mesh.select_all(action='DESELECT')

        # right hand verts
        if rig_type == 1:           
            merge_idx = [30, 35, 39, 44, 45, 50]
        else:            
            merge_idx = [32, 37, 41, 46, 51, 52]

        select_vertices(shape_object, merge_idx)
        bpy.ops.mesh.merge(type='CENTER')
        bpy.ops.transform.skin_resize(override,
                                    value=(corrective_thickness, corrective_thickness, corrective_thickness),
                                    constraint_axis=(False, False, False), constraint_orientation='GLOBAL',
                                    mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH',
                                    proportional_size=1)

        # making hands even more pretty
        bpy.ops.mesh.select_all(action='DESELECT')
        hands_idx = []  # left and right hand vertices
        if rig_type == 1:
            #hands_idx = [8, 33] #L and R
            hands_idx = [6, 29]
        else:
            #hands_idx = [10, 35] #L and R
            hands_idx = [8, 31]
        select_vertices(shape_object, hands_idx)
        # change the thickness to make hands look less blocky and more sexy
        corrective_thickness = 0.7
        bpy.ops.transform.skin_resize(override,
                                    value=(corrective_thickness, corrective_thickness, corrective_thickness),
                                    constraint_axis=(False, False, False), constraint_orientation='GLOBAL',
                                    mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH',
                                    proportional_size=1)
        bpy.ops.mesh.select_all(action='DESELECT')

    # todo optionally take root from rig's hip tail or head depending on scenario
    root_idx = []
    if rig_type == 1:
        root_idx = [59]
    elif rig_type == 2:
        root_idx = [56]
    else:
        root_idx = [0]

    select_vertices(shape_object, root_idx)
    bpy.ops.object.skin_root_mark(override)
    # skin in edit mode
    # add Subsurf modifier
    shape_object.modifiers.new("Subsurf", 'SUBSURF')
    shape_object.modifiers["Subsurf"].levels = sub_level
    shape_object.modifiers["Subsurf"].render_levels = sub_level

    bpy.ops.object.mode_set(mode='OBJECT')

    # object mode apply all modifiers
    if apply_mod:
        bpy.ops.object.modifier_apply(override, apply_as='DATA', modifier="Skin")
        bpy.ops.object.modifier_apply(override, apply_as='DATA', modifier="Subsurf")

    return {'FINISHED'}


def main(context):
    """
    This script will create a custome shape
    """

    # ### Check if selection is OK ###
    if len(context.selected_pose_bones) == 0 or \
            context.selected_objects[0].type != 'ARMATURE':
        return {'CANCELLED'}, "No bone selected"

    scn = bpy.context.scene

    # initialize the mesh object
    mesh_name = context.selected_objects[0].name + "_mesh"
    obj_name = context.selected_objects[0].name + "_object"
    armature_object = context.object

    origin = context.object.location
    bone_selection = context.selected_pose_bones
    oldLocation = None
    oldRotation = None
    oldScale = None
    armature_object = scn.objects.active
    armature_object.select = True

    old_pose_pos = armature_object.data.pose_position
    bpy.ops.object.mode_set(mode='OBJECT')
    oldLocation = Vector(armature_object.location)
    oldRotation = Euler(armature_object.rotation_euler)
    oldScale = Vector(armature_object.scale)

    bpy.ops.object.rotation_clear(clear_delta=False)
    bpy.ops.object.location_clear(clear_delta=False)
    bpy.ops.object.scale_clear(clear_delta=False)
    if scn.apply_mod and scn.parent_armature:
            armature_object.data.pose_position = 'REST'

    scale = bpy.context.object.scale
    size = bpy.context.object.dimensions[2]

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    bpy.ops.object.add(type='MESH', enter_editmode=False, location=origin)

    # get the mesh object
    ob = scn.objects.active
    ob.name = obj_name
    me = ob.data
    me.name = mesh_name

    # this way we fit mesh and bvh with armature modifier correctly

    alternate_scale_idx_list, rig_type = generate_edges(me, ob, bone_selection, scale, scn.connect_mesh,
                                                        scn.connect_parents, scn.head_ornaments,
                                                        scn.generate_all)

    generate_mesh(ob, size, scn.thickness, scn.finger_thickness, scn.sub_level,
                  scn.connect_mesh, scn.connect_parents, scn.generate_all,
                  scn.apply_mod, alternate_scale_idx_list, rig_type)

    # parent mesh with armature only if modifiers are applied
    if scn.apply_mod and scn.parent_armature:
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        ob.select = True
        armature_object.select = True
        scn.objects.active = armature_object

        bpy.ops.object.parent_set(type='ARMATURE_AUTO')
        armature_object.data.pose_position = old_pose_pos
        armature_object.select = False
    else:
        bpy.ops.object.mode_set(mode='OBJECT')
        ob.location = oldLocation
        ob.rotation_euler = oldRotation
        ob.scale = oldScale
        ob.select = False
        armature_object.select = True
        scn.objects.active = armature_object

    armature_object.location = oldLocation
    armature_object.rotation_euler = oldRotation
    armature_object.scale = oldScale
    bpy.ops.object.mode_set(mode='POSE')

    return {'FINISHED'}, me


class BONE_OT_custom_shape(bpy.types.Operator):
    '''Creates a mesh object at the selected bones positions'''
    bl_idname = "object.skinify_rig"
    bl_label = "Skinify Rig"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        Mesh = main(context)
        if Mesh[0] == {'CANCELLED'}:
            self.report({'WARNING'}, Mesh[1])
            return {'CANCELLED'}
        else:
            self.report({'INFO'}, Mesh[1].name + " has been created")

            return {'FINISHED'}


class BONE_PT_custom_shape(bpy.types.Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "bone"
    bl_label = "Skinify rig"

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob and ob.mode == 'POSE' and context.bone

    def draw(self, context):
        layout = self.layout
        scn = context.scene

        row = layout.row()
        row.operator("object.skinify_rig", text="Add Shape", icon='BONE_DATA')
        row = layout.row()
        row.label("Thickness:")
        row.prop(scn, "thickness", text="Body", icon='MOD_SKIN')
        row.prop(scn, "finger_thickness", text="fingers", icon='HAND')
        row = layout.row()
        row.label("Mesh Density:")
        row.label(text="")
        row.prop(scn, "sub_level", icon='MESH_ICOSPHERE')
        row = layout.row()
        row.prop(scn, "connect_mesh", text="solid shape", icon='EDITMODE_HLT')
        row.prop(scn, "connect_parents", text="fill gaps", icon='CONSTRAINT_BONE')
        row = layout.row()
        row.prop(scn, "head_ornaments", text="head ornaments", icon='GROUP_BONE')
        row.prop(scn, "generate_all", text="all shapes", icon='GROUP_BONE')
        row = layout.row()
        row.prop(scn, "apply_mod", text="apply Modifiers", icon='FILE_TICK')
        if scn.apply_mod:
            row = layout.row()
            row.prop(scn, "parent_armature", text="parent to Armature", icon='POSE_HLT')


# startup defaults
@persistent
def startup_init(dummy):
    init_props()


def register():
    bpy.utils.register_class(BONE_OT_custom_shape)
    bpy.utils.register_class(BONE_PT_custom_shape)

    # startup defaults
    bpy.app.handlers.load_post.append(startup_init)


def unregister():
    bpy.utils.unregister_class(BONE_OT_custom_shape)
    bpy.utils.unregister_class(BONE_PT_custom_shape)


if __name__ == "__main__":
    register()
