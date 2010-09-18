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

# <pep8 compliant>

bl_addon_info = {
    'name': 'Copy Attributes Menu',
    'author': 'Bassam Kurdali, Fabian Fricke, wiseman303',
    'version': (0, 40),
    'blender': (2, 5, 4),
    'api': 31989,
    'location': 'View3D > Ctrl/C',
    'description': 'Copy Attributes Menu from Blender 2.4',
    'wiki_url': 'http://wiki.blender.org/index.php/Extensions:2.5/Py/'\
        'Scripts/3D_interaction/Copy_Attributes_Menu',
    'tracker_url': 'https://projects.blender.org/tracker/index.php?'\
        'func=detail&aid=22588&group_id=153&atid=468',
    'category': '3D View'}

__bpydoc__ = """
Copy Menu


"""
import bpy
import mathutils
from mathutils import *


def build_exec(loopfunc, func):
    '''Generator function that returns exec functions for operators '''

    def exec_func(self, context):
        loopfunc(self, context, func)
        return {'FINISHED'}
    return exec_func


def build_invoke(loopfunc, func):
    '''Generator function that returns invoke functions for operators'''

    def invoke_func(self, context, event):
        loopfunc(self, context, func)
        return {'FINISHED'}
    return invoke_func


def build_op(idname, label, description, fpoll, fexec, finvoke):
    '''Generator function that returns the basic operator'''

    class myopic(bpy.types.Operator):
        bl_idname = idname
        bl_label = label
        bl_description = description
        execute = fexec
        poll = fpoll
        invoke = finvoke
    return myopic


def genops(copylist, oplist, prefix, poll_func, loopfunc):
    '''Generate ops from the copy list and its associated functions '''
    for op in copylist:
        exec_func = build_exec(loopfunc, op[3])
        invoke_func = build_invoke(loopfunc, op[3])
        opclass = build_op(prefix + op[0], "Copy " + op[1], op[2],
           poll_func, exec_func, invoke_func)
        oplist.append(opclass)


def generic_copy(source, target, string=""):
    ''' copy attributes from source to target that have string in them '''
    for attr in dir(source):
        if attr.find(string) > -1:
            try:
                setattr(target, attr, getattr(source, attr))
            except:
                pass
    return


def getmat(bone, active, context, ignoreparent):
    '''Helper function for visual transform copy,
       gets the active transform in bone space
    '''
    data_bone = context.active_object.data.bones[bone.name]
    #all matrices are in armature space unless commented otherwise
    otherloc = active.matrix #final 4x4 mat of target, location.
    bonemat_local = Matrix(data_bone.matrix_local) #self rest matrix
    if data_bone.parent:
        parentposemat = Matrix(
           context.active_object.pose.bones[data_bone.parent.name].matrix)
        parentbonemat = Matrix(data_bone.parent.matrix_local)
    else:
        parentposemat = bonemat_local.copy().identity()
        parentbonemat = bonemat_local.copy().identity()
    if parentbonemat == parentposemat or ignoreparent:
        newmat = bonemat_local.invert() * otherloc
    else:
        bonemat = parentbonemat.invert() * bonemat_local

        newmat = bonemat.invert() * parentposemat.invert() * otherloc
    return newmat


def rotcopy(item, mat):
    '''copy rotation to item from matrix mat depending on item.rotation_mode'''
    if item.rotation_mode == 'QUATERNION':
        item.rotation_quaternion = mat.rotation_part().to_quat()
    elif item.rotation_mode == 'AXIS_ANGLE':
        quat = mat.rotation_part().to_quat()
        item.rotation_axis_angle = Vector([quat.axis[0],
           quat.axis[1], quat.axis[2], quat.angle])
    else:
        item.rotation_euler = mat.rotation_part().to_euler(item.rotation_mode)


def pLoopExec(self, context, funk):
    '''Loop over selected bones and execute funk on them'''
    active = context.active_pose_bone
    selected = context.selected_pose_bones
    selected.remove(active)
    for bone in selected:
        funk(bone, active, context)

#The following functions are used o copy attributes frome active to bone


def pLocLocExec(bone, active, context):
    bone.location = active.location


def pLocRotExec(bone, active, context):
    rotcopy(bone, active.matrix_local.rotation_part())


def pLocScaExec(bone, active, context):
    bone.scale = active.scale


def pVisLocExec(bone, active, context):
    bone.location = getmat(bone, active, context, False).translation_part()


def pVisRotExec(bone, active, context):
    rotcopy(bone, getmat(bone, active,
      context, not context.active_object.data.bones[bone.name].use_hinge))


def pVisScaExec(bone, active, context):
    bone.scale = getmat(bone, active, context,
       not context.active_object.data.bones[bone.name].use_inherit_scale)\
          .scale_part()


def pDrwExec(bone, active, context):
    bone.custom_shape = active.custom_shape


def pLokExec(bone, active, context):
    for index, state in enumerate(active.lock_location):
        bone.lock_location[index] = state
    for index, state in enumerate(active.lock_rotation):
        bone.lock_rotation[index] = state
    bone.lock_rotations_4d = active.lock_rotations_4d
    bone.lock_rotation_w = active.lock_rotation_w
    for index, state in enumerate(active.lock_scale):
        bone.lock_scale[index] = state


def pConExec(bone, active, context):
    for old_constraint in  active.constraints.values():
        new_constraint = bone.constraints.new(old_constraint.type)
        generic_copy(old_constraint, new_constraint)


def pIKsExec(bone, active, context):
    generic_copy(active, bone, "ik_")

pose_copies = (('POSE_LOC_LOC', "Local Location",
                "Copy Location from Active to Selected", pLocLocExec),
                ('POSE_LOC_ROT', "Local Rotation",
                "Copy Rotation from Active to Selected", pLocRotExec),
                ('POSE_LOC_SCA', "Local Scale",
                "Copy Scale from Active to Selected", pLocScaExec),
                ('POSE_VIS_LOC', "Visual Location",
                "Copy Location from Active to Selected", pVisLocExec),
                ('POSE_VIS_ROT', "Visual Rotation",
                "Copy Rotation from Active to Selected", pVisRotExec),
                ('POSE_VIS_SCA', "Visual Scale",
                "Copy Scale from Active to Selected", pVisScaExec),
                ('POSE_DRW', "Bone Shape",
                "Copy Bone Shape from Active to Selected", pDrwExec),
                ('POSE_LOK', "Protected Transform",
                "Copy Protected Tranforms from Active to Selected", pLokExec),
                ('POSE_CON', "Bone Constraints",
                "Copy Object Constraints from Active to Selected", pConExec),
                ('POSE_IKS', "IK Limits",
                "Copy IK Limits from Active to Selected", pIKsExec))


@classmethod
def pose_poll_func(cls, context):
    return(context.mode == 'POSE')


def pose_invoke_func(self, context, event):
    wm = context.window_manager
    wm.invoke_props_dialog(self)
    return {'RUNNING_MODAL'}


class CopySelectedPoseConstraints(bpy.types.Operator):
    ''' Copy Chosen constraints from active to selected'''
    bl_idname = "pose.copy_selected_constraints"
    bl_label = "Copy Selected Constraints"
    selection = bpy.props.BoolVectorProperty(size=32)

    poll = pose_poll_func
    invoke = pose_invoke_func

    def draw(self, context):
        layout = self.layout
        props = self.properties
        for idx, const in enumerate(context.active_pose_bone.constraints):
            layout.prop(props, 'selection', index=idx, text=const.name,
               toggle=True)

    def execute(self, context):
        active = context.active_pose_bone
        selected = context.selected_pose_bones[:]
        selected.remove(active)
        for bone in selected:
            for index, flag in enumerate(self.selection):
                if flag:
                    old_constraint = active.constraints[index]
                    new_constraint = bone.constraints.new(\
                       active.constraints[index].type)
                    generic_copy(old_constraint, new_constraint)
        return {'FINISHED'}

pose_ops = [] #list of pose mode copy operators

genops(pose_copies, pose_ops, "pose.copy_", pose_poll_func, pLoopExec)


class VIEW3D_MT_posecopypopup(bpy.types.Menu):
    bl_label = "Copy Attributes"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        for op in pose_copies:
            layout.operator("pose.copy_" + op[0])
        layout.operator("pose.copy_selected_constraints")
        layout.operator("pose.copy", text="copy pose")


def obLoopExec(self, context, funk):
    '''Loop over selected objects and execute funk on them'''
    active = context.active_object
    selected = context.selected_objects[:]
    selected.remove(active)
    for obj in selected:
        msg = funk(obj, active, context)
    if msg:
        self.report({msg[0]}, msg[1])

#The following functions are used o copy attributes from
#active to selected object


def obLoc(ob, active, context):
    ob.location = active.location


def obRot(ob, active, context):
    rotcopy(ob, active.matrix_world.rotation_part())


def obSca(ob, active, context):
    ob.scale = active.scale


def obDrw(ob, active, context):
    ob.draw_type = active.draw_type
    ob.show_axis = active.show_axis
    ob.show_bounds = active.show_bounds
    ob.draw_bounds_type = active.draw_bounds_type
    ob.show_name = active.show_name
    ob.show_texture_space = active.show_texture_space
    ob.show_transparent = active.show_transparent
    ob.show_wire = active.show_wire
    ob.empty_draw_type = active.empty_draw_type
    ob.empty_draw_size = active.empty_draw_size


def obOfs(ob, active, context):
    ob.time_offset = active.time_offset
    return('INFO', "time offset copied")


def obDup(ob, active, context):
    generic_copy(active, ob, "dupli")
    return('INFO', "duplication method copied")


def obCol(ob, active, context):
    ob.color = active.color


def obMas(ob, active, context):
    ob.game.mass = active.game.mass
    return('INFO', "mass copied")


def obLok(ob, active, context):
    for index, state in enumerate(active.lock_location):
        ob.lock_location[index] = state
    for index, state in enumerate(active.lock_rotation):
        ob.lock_rotation[index] = state
    for index, state in enumerate(active.lock_rotations_4d):
        ob.lock_rotations_4d[index] = state
    ob.lock_rotation_w = active.lock_rotation_w
    for index, state in enumerate(active.lock_scale):
        ob.lock_scale[index] = state
    return('INFO', "transform locks copied")


def obCon(ob, active, context):
    #for consistency with 2.49, delete old constraints first
    for removeconst in ob.constraints:
        ob.constraints.remove(removeconst)
    for old_constraint in  active.constraints.values():
        new_constraint = ob.constraints.new(old_constraint.type)
        generic_copy(old_constraint, new_constraint)
    return('INFO', "constraints copied")


def obTex(ob, active, context):
    if 'texspace_location' in dir(ob.data) and 'texspace_location' in dir(
       active.data):
        ob.data.texspace_location[:] = active.data.texspace_location[:]
    if 'texspace_size' in dir(ob.data) and 'texspace_size' in dir(active.data):
        ob.data.texspace_size[:] = active.data.texspace_size[:]
    return('INFO', "texture space copied")


def obIdx(ob, active, context):
    ob.pass_index = active.pass_index
    return('INFO', "pass index copied")


def obMod(ob, active, context):
    for modifier in ob.modifiers:
        #remove existing before adding new:
        ob.modifiers.remove(modifier)
    for old_modifier in active.modifiers.values():
        new_modifier = ob.modifiers.new(name=old_modifier.name,
           type=old_modifier.type)
        generic_copy(old_modifier, new_modifier)
    return('INFO', "modifiers copied")


def obWei(ob, active, context):
    me_source = active.data
    me_target = ob.data
    # sanity check: do source and target have the same amount of verts?
    if len(me_source.vertices) != len(me_target.vertices):
        return('ERROR', "objects have different vertex counts, doing nothing")
    vgroups_IndexName = {}
    for i in range(0, len(active.vertex_groups)):
        groups = active.vertex_groups[i]
        vgroups_IndexName[groups.index] = groups.name
    data = {} # vert_indices, [(vgroup_index, weights)]
    for v in me_source.vertices:
        vg = v.groups
        vi = v.index
        if len(vg) > 0:
            vgroup_collect = []
            for i in range(0, len(vg)):
                vgroup_collect.append((vg[i].group, vg[i].weight))
            data[vi] = vgroup_collect
    # write data to target
    if ob != active:
        # add missing vertex groups
        for vgroup_name in vgroups_IndexName.values():
            #check if group already exists...
            already_present = 0
            for i in range(0, len(ob.vertex_groups)):
                if ob.vertex_groups[i].name == vgroup_name:
                    already_present = 1
            # ... if not, then add
            if already_present == 0:
                ob.vertex_groups.new(name=vgroup_name)
        # write weights
        for v in me_target.vertices:
            for vi_source, vgroupIndex_weight in data.items():
                if v.index == vi_source:

                    for i in range(0, len(vgroupIndex_weight)):
                        groupName = vgroups_IndexName[vgroupIndex_weight[i][0]]
                        groups = ob.vertex_groups
                        for vgs in range(0, len(groups)):
                            if groups[vgs].name == groupName:
                                ob.vertex_groups.assign(v.index, groups[vgs],
                                   vgroupIndex_weight[i][1], "REPLACE")
    return('INFO', "weights copied")

object_copies = (('OBJ_LOC', "Location",
                "Copy Location from Active to Selected", obLoc),
                ('OBJ_ROT', "Rotation",
                "Copy Rotation from Active to Selected", obRot),
                ('OBJ_SCA', "Scale",
                "Copy Scale from Active to Selected", obSca),
                ('OBJ_DRW', "Draw Options",
                "Copy Draw Options from Active to Selected", obDrw),
                ('OBJ_OFS', "Time Offset",
                "Copy Time Offset from Active to Selected", obOfs),
                ('OBJ_DUP', "Dupli",
                "Copy Dupli from Active to Selected", obDup),
                ('OBJ_COL', "Object Color",
                "Copy Object Color from Active to Selected", obCol),
                ('OBJ_MAS', "Mass",
                "Copy Mass from Active to Selected", obMas),
                #('OBJ_DMP', "Damping",
                #"Copy Damping from Active to Selected"),
                #('OBJ_ALL', "All Physical Attributes",
                #"Copy Physical Atributes from Active to Selected"),
                #('OBJ_PRP', "Properties",
                #"Copy Properties from Active to Selected"),
                #('OBJ_LOG', "Logic Bricks",
                #"Copy Logic Bricks from Active to Selected"),
                ('OBJ_LOK', "Protected Transform",
                "Copy Protected Tranforms from Active to Selected", obLok),
                ('OBJ_CON', "Object Constraints",
                "Copy Object Constraints from Active to Selected", obCon),
                #('OBJ_NLA', "NLA Strips",
                #"Copy NLA Strips from Active to Selected"),
                #('OBJ_TEX', "Texture Space",
                #"Copy Texture Space from Active to Selected", obTex),
                #('OBJ_SUB', "Subsurf Settings",
                #"Copy Subsurf Setings from Active to Selected"),
                #('OBJ_SMO', "AutoSmooth",
                #"Copy AutoSmooth from Active to Selected"),
                ('OBJ_IDX', "Pass Index",
                "Copy Pass Index from Active to Selected", obIdx),
                ('OBJ_MOD', "Modifiers",
                "Copy Modifiers from Active to Selected", obMod),
                ('OBJ_WEI', "Vertex Weights",
                "Copy vertex weights based on indices", obWei))


@classmethod
def object_poll_func(cls, context):
    return(len(context.selected_objects) > 1)


def object_invoke_func(self, context, event):
    wm = context.window_manager
    wm.invoke_props_dialog(self)
    return {'RUNNING_MODAL'}


class CopySelectedObjectConstraints(bpy.types.Operator):
    ''' Copy Chosen constraints from active to selected'''
    bl_idname = "object.copy_selected_constraints"
    bl_label = "Copy Selected Constraints"
    selection = bpy.props.BoolVectorProperty(size=32)

    poll = object_poll_func

    invoke = object_invoke_func

    def draw(self, context):
        layout = self.layout
        props = self.properties
        for idx, const in enumerate(context.active_object.constraints):
            layout.prop(props, 'selection', index=idx, text=const.name,
               toggle=True)

    def execute(self, context):
        active = context.active_object
        selected = context.selected_objects[:]
        selected.remove(active)
        for obj in selected:
            for index, flag in enumerate(self.selection):
                if flag:
                    old_constraint = active.constraints[index]
                    new_constraint = obj.constraints.new(\
                       active.constraints[index].type)
                    generic_copy(old_constraint, new_constraint)
        return{'FINISHED'}


class CopySelectedObjectModifiers(bpy.types.Operator):
    ''' Copy Chosen modifiers from active to selected'''
    bl_idname = "object.copy_selected_modifiers"
    bl_label = "Copy Selected Modifiers"
    selection = bpy.props.BoolVectorProperty(size=32)

    poll = object_poll_func

    invoke = object_invoke_func

    def draw(self, context):
        layout = self.layout
        props = self.properties
        for idx, const in enumerate(context.active_object.modifiers):
            layout.prop(props, 'selection', index=idx, text=const.name,
               toggle=True)

    def execute(self, context):
        active = context.active_object
        selected = context.selected_objects[:]
        selected.remove(active)
        for obj in selected:
            for index, flag in enumerate(self.selection):
                if flag:
                    old_modifier = active.modifiers[index]
                    new_modifier = obj.modifiers.new(\
                       type=active.modifiers[index].type,
                       name=active.modifiers[index].name)
                    generic_copy(old_modifier, new_modifier)
        return{'FINISHED'}

object_ops = []
genops(object_copies, object_ops, "object.copy_", object_poll_func, obLoopExec)


class VIEW3D_MT_copypopup(bpy.types.Menu):
    bl_label = "Copy Attributes"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        for op in object_copies:
            layout.operator("object.copy_" + op[0])
        layout.operator("object.copy_selected_constraints")
        layout.operator("object.copy_selected_modifiers")

#Begin Mesh copy settings:


class MESH_MT_CopyFaceSettings(bpy.types.Menu):
    bl_label = "Copy Face Settings"

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def draw(self, context):
        mesh = context.object.data
        uv = len(mesh.uv_textures) > 1
        vc = len(mesh.vertex_colors) > 1
        layout = self.layout

        layout.operator(MESH_OT_CopyFaceSettings.bl_idname,
                        text="Copy Material")['mode'] = 'MAT'
        if mesh.uv_textures.active:
            layout.operator(MESH_OT_CopyFaceSettings.bl_idname,
                            text="Copy Mode")['mode'] = 'MODE'
            layout.operator(MESH_OT_CopyFaceSettings.bl_idname,
                            text="Copy Transp")['mode'] = 'TRANSP'
            layout.operator(MESH_OT_CopyFaceSettings.bl_idname,
                            text="Copy Image")['mode'] = 'IMAGE'
            layout.operator(MESH_OT_CopyFaceSettings.bl_idname,
                            text="Copy UV Coords")['mode'] = 'UV'
        if mesh.vertex_colors.active:
            layout.operator(MESH_OT_CopyFaceSettings.bl_idname,
                            text="Copy Vertex Colors")['mode'] = 'VCOL'
        if uv or vc:
            layout.separator()
            if uv:
                layout.menu("MESH_MT_CopyModeFromLayer")
                layout.menu("MESH_MT_CopyTranspFromLayer")
                layout.menu("MESH_MT_CopyImagesFromLayer")
                layout.menu("MESH_MT_CopyUVCoordsFromLayer")
            if vc:
                layout.menu("MESH_MT_CopyVertexColorsFromLayer")


def _buildmenu(self, mesh, mode):
    layout = self.layout
    if mode == 'VCOL':
        layers = mesh.vertex_colors
    else:
        layers = mesh.uv_textures
    for layer in layers:
        if not layer.active:
            op = layout.operator(MESH_OT_CopyFaceSettings.bl_idname,
                                 text=layer.name)
            op['layer'] = layer.name
            op['mode'] = mode


@classmethod
def _poll_layer_uvs(cls, context):
    return context.mode == "EDIT_MESH" and len(
       context.object.data.uv_layers) > 1


@classmethod
def _poll_layer_vcols(cls, context):
    return context.mode == "EDIT_MESH" and len(
       context.object.data.vertex_colors) > 1


def _build_draw(mode):
    return (lambda self, context: _buildmenu(self, context.object.data, mode))

_layer_menu_data = (("UV Coords", _build_draw("UV"), _poll_layer_uvs),
                    ("Images", _build_draw("IMAGE"), _poll_layer_uvs),
                    ("Mode", _build_draw("MODE"), _poll_layer_uvs),
                    ("Transp", _build_draw("TRANSP"), _poll_layer_uvs),
                    ("Vertex Colors", _build_draw("VCOL"), _poll_layer_vcols))
_layer_menus = []
for name, draw_func, poll_func in _layer_menu_data:
    classname = "MESH_MT_Copy" + "".join(name.split()) + "FromLayer"
    menuclass = type(classname, (bpy.types.Menu,),
                     dict(bl_label="Copy " + name + " from layer",
                          bl_idname=classname,
                          draw=draw_func,
                          poll=poll_func))
    _layer_menus.append(menuclass)


class MESH_OT_CopyFaceSettings(bpy.types.Operator):
    """Copy settings from active face to all selected faces."""
    bl_idname = 'mesh.copy_face_settings'
    bl_label = "Copy Face Settings"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        mesh = context.object.data
        mode = self.properties.get('mode', 'MODE')
        layername = self.properties.get('layer')

        # Switching out of edit mode updates the selected state of faces and
        # makes the data from the uv texture and vertex color layers available.
        bpy.ops.object.editmode_toggle()

        if mode == 'MAT':
            from_data = mesh.faces
            to_data = from_data
        else:
            if mode == 'VCOL':
                layers = mesh.vertex_colors
                act_layer = mesh.vertex_colors.active
            else:
                layers = mesh.uv_textures
                act_layer = mesh.uv_textures.active
            if not layers or (layername and not layername in layers):
                    return _end({'CANCELLED'})
            from_data = layers[layername or act_layer.name].data
            to_data = act_layer.data
        from_face = from_data[mesh.faces.active]

        for f in mesh.faces:
            if f.select:
                if to_data != from_data:
                    from_face = from_data[f.index]
                if mode == 'MAT':
                    f.material_index = from_face.material_index
                    continue
                to_face = to_data[f.index]
                if to_face is from_face:
                    continue
                if mode == 'VCOL':
                    to_face.color1 = from_face.color1
                    to_face.color2 = from_face.color2
                    to_face.color3 = from_face.color3
                    to_face.color4 = from_face.color4
                elif mode == 'MODE':
                    to_face.use_alpha_sort = from_face.use_alpha_sort
                    to_face.use_billboard = from_face.use_billboard
                    to_face.use_collision = from_face.use_collision
                    to_face.use_halo = from_face.use_halo
                    to_face.hide = from_face.hide
                    to_face.use_light = from_face.use_light
                    to_face.use_object_color = from_face.use_object_color
                    to_face.use_shadow_cast = from_face.use_shadow_cast
                    to_face.use_blend_shared = from_face.use_blend_shared
                    to_face.use_image = from_face.use_image
                    to_face.use_bitmap_text = from_face.use_bitmap_text
                    to_face.use_twoside = from_face.use_twoside
                elif mode == 'TRANSP':
                    to_face.blend_type = from_face.blend_type
                elif mode in ('UV', 'IMAGE'):
                    attr = mode.lower()
                    setattr(to_face, attr, getattr(from_face, attr))
        return _end({'FINISHED'})


def _end(retval):
    # Clean up by returning to edit mode like it was before.
    bpy.ops.object.editmode_toggle()
    return(retval)


def _add_tface_buttons(self, context):
    row = self.layout.row()
    row.operator(MESH_OT_CopyFaceSettings.bl_idname,
                 text="Copy Mode")['mode'] = 'MODE'
    row.operator(MESH_OT_CopyFaceSettings.bl_idname,
                 text="Copy Transp")['mode'] = 'TRANSP'


def register():
    ''' mostly to get the keymap working '''
    km = bpy.context.window_manager.keyconfigs['Blender'].\
       keymaps['Object Mode']
    kmi = km.items.new('wm.call_menu', 'C', 'PRESS', ctrl=True)
    kmi.properties.name = 'VIEW3D_MT_copypopup'
    km = bpy.context.window_manager.keyconfigs['Blender'].keymaps['Pose']
    try:
        kmi = km.items['pose.copy']
        kmi.idname = 'wm.call_menu'
    except KeyError:
        kmi = km.items.new('wm.call_menu', 'C', 'PRESS', ctrl=True)
    kmi.properties.name = 'VIEW3D_MT_posecopypopup'
    bpy.types.DATA_PT_texface.append(_add_tface_buttons)
    km = bpy.context.window_manager.keyconfigs.active.keymaps['Mesh']
    kmi = km.items.new('wm.call_menu', 'C', 'PRESS')
    kmi.ctrl = True
    kmi.properties.name = 'MESH_MT_CopyFaceSettings'


def unregister():
    ''' mostly to remove the keymap '''
    kms = bpy.context.window_manager.keyconfigs['Blender'].keymaps['Pose']
    for item in kms.items:
        if item.name == 'Call Menu' and item.idname == 'wm.call_menu' and \
           item.properties.name == 'VIEW3D_MT_posecopypopup':
            item.idname = 'pose.copy'
            break
    bpy.types.DATA_PT_texface.remove(_add_tface_buttons)
    km = bpy.context.window_manager.keyconfigs.active.keymaps['Mesh']
    for kmi in km.items:
        if kmi.idname == 'wm.call_menu':
            if kmi.properties.name == 'MESH_MT_CopyFaceSettings':
                km.items.remove(kmi)

if __name__ == "__main__":
    register()