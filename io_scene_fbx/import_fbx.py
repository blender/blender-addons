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

# Script copyright (C) Blender Foundation

# FBX 7.1.0 -> 7.4.0 loader for Blender

# Not totally pep8 compliant.
#   pep8 import_fbx.py --ignore=E501,E123,E702,E125

if "bpy" in locals():
    import importlib
    if "parse_fbx" in locals():
        importlib.reload(parse_fbx)
    if "fbx_utils" in locals():
        importlib.reload(fbx_utils)

import bpy

# -----
# Utils
from . import parse_fbx, fbx_utils

from .parse_fbx import data_types, FBXElem
from .fbx_utils import (
    units_convertor_iter,
    array_to_matrix4,
    similar_values,
    similar_values_iter,
)

# global singleton, assign on execution
fbx_elem_nil = None

# Units convertors...
convert_deg_to_rad_iter = units_convertor_iter("degree", "radian")

MAT_CONVERT_BONE = fbx_utils.MAT_CONVERT_BONE.inverted()
MAT_CONVERT_LAMP = fbx_utils.MAT_CONVERT_LAMP.inverted()
MAT_CONVERT_CAMERA = fbx_utils.MAT_CONVERT_CAMERA.inverted()


def elem_find_first(elem, id_search, default=None):
    for fbx_item in elem.elems:
        if fbx_item.id == id_search:
            return fbx_item
    return default


def elem_find_iter(elem, id_search):
    for fbx_item in elem.elems:
        if fbx_item.id == id_search:
            yield fbx_item


def elem_find_first_string(elem, id_search):
    fbx_item = elem_find_first(elem, id_search)
    if fbx_item is not None:
        assert(len(fbx_item.props) == 1)
        assert(fbx_item.props_type[0] == data_types.STRING)
        return fbx_item.props[0].decode('utf-8')
    return None


def elem_find_first_bytes(elem, id_search, decode=True):
    fbx_item = elem_find_first(elem, id_search)
    if fbx_item is not None:
        assert(len(fbx_item.props) == 1)
        assert(fbx_item.props_type[0] == data_types.STRING)
        return fbx_item.props[0]
    return None


def elem_repr(elem):
    return "%s: props[%d=%r], elems=(%r)" % (
        elem.id,
        len(elem.props),
        ", ".join([repr(p) for p in elem.props]),
        # elem.props_type,
        b", ".join([e.id for e in elem.elems]),
        )


def elem_split_name_class(elem):
    assert(elem.props_type[-2] == data_types.STRING)
    elem_name, elem_class = elem.props[-2].split(b'\x00\x01')
    return elem_name, elem_class


def elem_name_ensure_class(elem, clss=...):
    elem_name, elem_class = elem_split_name_class(elem)
    if clss is not ...:
        assert(elem_class == clss)
    return elem_name.decode('utf-8')


def elem_split_name_class_nodeattr(elem):
    assert(elem.props_type[-2] == data_types.STRING)
    elem_name, elem_class = elem.props[-2].split(b'\x00\x01')
    assert(elem_class == b'NodeAttribute')
    assert(elem.props_type[-1] == data_types.STRING)
    elem_class = elem.props[-1]
    return elem_name, elem_class


def elem_uuid(elem):
    assert(elem.props_type[0] == data_types.INT64)
    return elem.props[0]


def elem_prop_first(elem, default=None):
    return elem.props[0] if (elem is not None) and elem.props else default


# ----
# Support for
# Properties70: { ... P:
def elem_props_find_first(elem, elem_prop_id):

    # support for templates (tuple of elems)
    if type(elem) is not FBXElem:
        assert(type(elem) is tuple)
        for e in elem:
            result = elem_props_find_first(e, elem_prop_id)
            if result is not None:
                return result
        assert(len(elem) > 0)
        return None

    for subelem in elem.elems:
        assert(subelem.id == b'P')
        if subelem.props[0] == elem_prop_id:
            return subelem
    return None


def elem_props_get_color_rgb(elem, elem_prop_id, default=None):
    elem_prop = elem_props_find_first(elem, elem_prop_id)
    if elem_prop is not None:
        assert(elem_prop.props[0] == elem_prop_id)
        if elem_prop.props[1] == b'Color':
            # FBX version 7300
            assert(elem_prop.props[1] == b'Color')
            assert(elem_prop.props[2] == b'')
            assert(elem_prop.props[3] in {b'A', b'A+', b'AU'})
        else:
            assert(elem_prop.props[1] == b'ColorRGB')
            assert(elem_prop.props[2] == b'Color')
        assert(elem_prop.props_type[4:7] == bytes((data_types.FLOAT64,)) * 3)
        return elem_prop.props[4:7]
    return default


def elem_props_get_vector_3d(elem, elem_prop_id, default=None):
    elem_prop = elem_props_find_first(elem, elem_prop_id)
    if elem_prop is not None:
        assert(elem_prop.props_type[4:7] == bytes((data_types.FLOAT64,)) * 3)
        return elem_prop.props[4:7]
    return default


def elem_props_get_number(elem, elem_prop_id, default=None):
    elem_prop = elem_props_find_first(elem, elem_prop_id)
    if elem_prop is not None:
        assert(elem_prop.props[0] == elem_prop_id)
        if elem_prop.props[1] == b'double':
            assert(elem_prop.props[1] == b'double')
            assert(elem_prop.props[2] == b'Number')
        else:
            assert(elem_prop.props[1] == b'Number')
            assert(elem_prop.props[2] == b'')
            assert(elem_prop.props[3] in {b'A', b'A+', b'AU'})

        # we could allow other number types
        assert(elem_prop.props_type[4] == data_types.FLOAT64)

        return elem_prop.props[4]
    return default


def elem_props_get_integer(elem, elem_prop_id, default=None):
    elem_prop = elem_props_find_first(elem, elem_prop_id)
    if elem_prop is not None:
        assert(elem_prop.props[0] == elem_prop_id)
        if elem_prop.props[1] == b'int':
            assert(elem_prop.props[1] == b'int')
            assert(elem_prop.props[2] == b'Integer')
        elif elem_prop.props[1] == b'ULongLong':
            assert(elem_prop.props[1] == b'ULongLong')
            assert(elem_prop.props[2] == b'')

        # we could allow other number types
        assert(elem_prop.props_type[4] in {data_types.INT32, data_types.INT64})

        return elem_prop.props[4]
    return default


def elem_props_get_bool(elem, elem_prop_id, default=None):
    elem_prop = elem_props_find_first(elem, elem_prop_id)
    if elem_prop is not None:
        assert(elem_prop.props[0] == elem_prop_id)
        assert(elem_prop.props[1] == b'bool')
        assert(elem_prop.props[2] == b'')
        assert(elem_prop.props[3] == b'')

        # we could allow other number types
        assert(elem_prop.props_type[4] == data_types.INT32)
        assert(elem_prop.props[4] in {0, 1})

        return bool(elem_prop.props[4])
    return default


def elem_props_get_enum(elem, elem_prop_id, default=None):
    elem_prop = elem_props_find_first(elem, elem_prop_id)
    if elem_prop is not None:
        assert(elem_prop.props[0] == elem_prop_id)
        assert(elem_prop.props[1] == b'enum')
        assert(elem_prop.props[2] == b'')
        assert(elem_prop.props[3] == b'')

        # we could allow other number types
        assert(elem_prop.props_type[4] == data_types.INT32)

        return elem_prop.props[4]
    return default


def elem_props_get_visibility(elem, elem_prop_id, default=None):
    elem_prop = elem_props_find_first(elem, elem_prop_id)
    if elem_prop is not None:
        assert(elem_prop.props[0] == elem_prop_id)
        assert(elem_prop.props[1] == b'Visibility')
        assert(elem_prop.props[2] == b'')
        assert(elem_prop.props[3] in {b'A', b'A+', b'AU'})

        # we could allow other number types
        assert(elem_prop.props_type[4] == data_types.FLOAT64)

        return elem_prop.props[4]
    return default


# ----------------------------------------------------------------------------
# Blender

# ------
# Object
from collections import namedtuple


FBXTransformData = namedtuple("FBXTransformData", (
    "loc",
    "rot", "rot_ofs", "rot_piv", "pre_rot", "pst_rot", "rot_ord", "rot_alt_mat",
    "sca", "sca_ofs", "sca_piv",
))


object_tdata_cache = {}


def blen_read_object_transform_do(transform_data):
    from mathutils import Matrix, Euler

    # translation
    lcl_translation = Matrix.Translation(transform_data.loc)

    # rotation
    to_rot = lambda rot, rot_ord: Euler(convert_deg_to_rad_iter(rot), rot_ord).to_matrix().to_4x4()
    lcl_rot = to_rot(transform_data.rot, transform_data.rot_ord) * transform_data.rot_alt_mat
    pre_rot = to_rot(transform_data.pre_rot, transform_data.rot_ord)
    pst_rot = to_rot(transform_data.pst_rot, transform_data.rot_ord)

    rot_ofs = Matrix.Translation(transform_data.rot_ofs)
    rot_piv = Matrix.Translation(transform_data.rot_piv)
    sca_ofs = Matrix.Translation(transform_data.sca_ofs)
    sca_piv = Matrix.Translation(transform_data.sca_piv)

    # scale
    lcl_scale = Matrix()
    lcl_scale[0][0], lcl_scale[1][1], lcl_scale[2][2] = transform_data.sca

    return (
        lcl_translation *
        rot_ofs *
        rot_piv *
        pre_rot *
        lcl_rot *
        pst_rot *
        rot_piv.inverted() *
        sca_ofs *
        sca_piv *
        lcl_scale *
        sca_piv.inverted()
    )


# XXX This might be weak, now that we can add vgroups from both bones and shapes, name collisions become
#     more likely, will have to make this more robust!!!
def add_vgroup_to_objects(vg_indices, vg_weights, vg_name, objects):
    assert(len(vg_indices) == len(vg_weights))
    if vg_indices:
        for obj in objects:
            # We replace/override here...
            vg = obj.vertex_groups.get(vg_name)
            if vg is None:
                vg = obj.vertex_groups.new(vg_name)
            for i, w in zip(vg_indices, vg_weights):
                vg.add((i,), w, 'REPLACE')


def blen_read_object_transform_preprocess(fbx_props, fbx_obj, rot_alt_mat):
    # This is quite involved, 'fbxRNode.cpp' from openscenegraph used as a reference
    const_vector_zero_3d = 0.0, 0.0, 0.0
    const_vector_one_3d = 1.0, 1.0, 1.0

    loc = list(elem_props_get_vector_3d(fbx_props, b'Lcl Translation', const_vector_zero_3d))
    rot = list(elem_props_get_vector_3d(fbx_props, b'Lcl Rotation', const_vector_zero_3d))
    sca = list(elem_props_get_vector_3d(fbx_props, b'Lcl Scaling', const_vector_one_3d))

    rot_ofs = elem_props_get_vector_3d(fbx_props, b'RotationOffset', const_vector_zero_3d)
    rot_piv = elem_props_get_vector_3d(fbx_props, b'RotationPivot', const_vector_zero_3d)
    sca_ofs = elem_props_get_vector_3d(fbx_props, b'ScalingOffset', const_vector_zero_3d)
    sca_piv = elem_props_get_vector_3d(fbx_props, b'ScalingPivot', const_vector_zero_3d)

    is_rot_act = elem_props_get_bool(fbx_props, b'RotationActive', False)

    if is_rot_act:
        pre_rot = elem_props_get_vector_3d(fbx_props, b'PreRotation', const_vector_zero_3d)
        pst_rot = elem_props_get_vector_3d(fbx_props, b'PostRotation', const_vector_zero_3d)
        rot_ord = {
            0: 'XYZ',
            1: 'XYZ',
            2: 'XZY',
            3: 'YZX',
            4: 'YXZ',
            5: 'ZXY',
            6: 'ZYX',
            }.get(elem_props_get_enum(fbx_props, b'RotationOrder', 0))
    else:
        pre_rot = const_vector_zero_3d
        pst_rot = const_vector_zero_3d
        rot_ord = 'XYZ'

    return FBXTransformData(loc,
                            rot, rot_ofs, rot_piv, pre_rot, pst_rot, rot_ord, rot_alt_mat,
                            sca, sca_ofs, sca_piv)


def blen_read_object(fbx_tmpl, fbx_obj, object_data):
    elem_name_utf8 = elem_name_ensure_class(fbx_obj)

    # Object data must be created already
    obj = bpy.data.objects.new(name=elem_name_utf8, object_data=object_data)

    fbx_props = (elem_find_first(fbx_obj, b'Properties70'),
                 elem_find_first(fbx_tmpl, b'Properties70', fbx_elem_nil))
    assert(fbx_props[0] is not None)

    # ----
    # Misc Attributes

    obj.color[0:3] = elem_props_get_color_rgb(fbx_props, b'Color', (0.8, 0.8, 0.8))
    obj.hide = not bool(elem_props_get_visibility(fbx_props, b'Visibility', 1.0))

    # ----
    # Transformation

    from mathutils import Matrix
    from math import pi

    # rotation corrections
    if obj.type == 'CAMERA':
        rot_alt_mat = MAT_CONVERT_CAMERA
    elif obj.type == 'LAMP':
        rot_alt_mat = MAT_CONVERT_LAMP
    else:
        rot_alt_mat = Matrix()

    transform_data = object_tdata_cache.get(obj)
    if transform_data is None:
        transform_data = blen_read_object_transform_preprocess(fbx_props, fbx_obj, rot_alt_mat)
        object_tdata_cache[obj] = transform_data
    obj.matrix_basis = blen_read_object_transform_do(transform_data)

    return obj


# --------
# Armature

def blen_read_armatures_add_bone(bl_obj, bl_arm, bones, b_uuid, matrices, fbx_tmpl_model):
    from mathutils import Matrix, Vector

    b_item, bsize, p_uuid, clusters = bones[b_uuid]
    fbx_bdata, bl_bname = b_item
    if bl_bname is not None:
        return bl_arm.edit_bones[bl_bname]  # Have already been created...

    p_ebo = None
    if p_uuid is not None:
        # Recurse over parents!
        p_ebo = blen_read_armatures_add_bone(bl_obj, bl_arm, bones, p_uuid, matrices, fbx_tmpl_model)

    if clusters:
        # Note in some cases, one bone can have several clusters (kind of LoD?), in Blender we'll always
        # use only the first, for now.
        fbx_cdata, meshes, objects = clusters[0]
        objects = {blen_o for fbx_o, blen_o in objects}

        # We assume matrices in cluster are rest pose of bones (they are in Global space!).
        # TransformLink is matrix of bone, in global space.
        # TransformAssociateModel is matrix of armature, in global space (at bind time).
        elm = elem_find_first(fbx_cdata, b'Transform', default=None)
        mmat_bone = array_to_matrix4(elm.props[0]) if elm is not None else None
        elm = elem_find_first(fbx_cdata, b'TransformLink', default=None)
        bmat_glob = array_to_matrix4(elm.props[0]) if elm is not None else Matrix()
        elm = elem_find_first(fbx_cdata, b'TransformAssociateModel', default=None)
        amat_glob = array_to_matrix4(elm.props[0]) if elm is not None else Matrix()

        mmat_glob = bmat_glob * mmat_bone

        # We seek for matrix of bone in armature space...
        bmat_arm = amat_glob.inverted() * bmat_glob

        # Bone correction, works here...
        bmat_loc = (p_ebo.matrix.inverted() * bmat_arm) if p_ebo else bmat_arm
        bmat_loc = bmat_loc * MAT_CONVERT_BONE
        bmat_arm = (p_ebo.matrix * bmat_loc) if p_ebo else bmat_loc
    else:
        # Armature bound to no mesh...
        fbx_cdata, meshes, objects = (None, (), ())
        mmat_bone = None
        amat_glob = bl_obj.matrix_world

        fbx_props = (elem_find_first(fbx_bdata, b'Properties70'),
                     elem_find_first(fbx_tmpl_model, b'Properties70', fbx_elem_nil))
        assert(fbx_props[0] is not None)

        # Bone correction, works here...
        transform_data = blen_read_object_transform_preprocess(fbx_props, fbx_bdata, MAT_CONVERT_BONE)
        bmat_loc = blen_read_object_transform_do(transform_data)
        # Bring back matrix in armature space.
        bmat_arm = (p_ebo.matrix * bmat_loc) if p_ebo else bmat_loc

    # ----
    # Now, create the (edit)bone.
    bone_name = elem_name_ensure_class(fbx_bdata, b'Model')

    ebo = bl_arm.edit_bones.new(name=bone_name)
    bone_name = ebo.name  # Might differ from FBX bone name!
    b_item[1] = bone_name  # since ebo is only valid in Edit mode... :/

    # So that our bone gets its final length, but still Y-aligned in armature space.
    ebo.tail = Vector((0.0, 1.0, 0.0)) * bsize
    # And rotate/move it to its final "rest pose".
    ebo.matrix = bmat_arm.normalized()

    # Connection to parent.
    if p_ebo is not None:
        ebo.parent = p_ebo
        if similar_values_iter(p_ebo.tail, ebo.head):
            ebo.use_connect = True

    if fbx_cdata is not None:
        # ----
        # Add a new vgroup to the meshes (their objects, actually!).
        # Quite obviously, only one mesh is expected...
        indices = elem_prop_first(elem_find_first(fbx_cdata, b'Indexes', default=None), default=())
        weights = elem_prop_first(elem_find_first(fbx_cdata, b'Weights', default=None), default=())
        add_vgroup_to_objects(indices, weights, bone_name, objects)

    # ----
    # If we get a valid mesh matrix (in bone space), store armature and mesh global matrices, we need to set temporarily
    # both objects to those matrices when actually binding them via the modifier.
    # Note we assume all bones were bound with the same mesh/armature (global) matrix, we do not support otherwise
    # in Blender anyway!
    if mmat_bone is not None:
        for obj in objects:
            if obj in matrices:
                continue
            matrices[obj] = (amat_glob, mmat_glob)

    return ebo


def blen_read_armatures(fbx_tmpl, armatures, fbx_bones_to_fake_object, scene, global_matrix, arm_parents):
    from mathutils import Matrix

    if global_matrix is None:
        global_matrix = Matrix()

    for a_item, bones in armatures:
        fbx_adata, bl_adata = a_item
        matrices = {}

        # ----
        # Armature data.
        elem_name_utf8 = elem_name_ensure_class(fbx_adata, b'Model')
        bl_arm = bpy.data.armatures.new(name=elem_name_utf8)

        # Need to create the object right now, since we can only add bones in Edit mode... :/
        assert(a_item[1] is None)

        if fbx_adata.props[2] in {b'LimbNode', b'Root'}:
            # rootbone-as-armature case...
            fbx_bones_to_fake_object[fbx_adata.props[0]] = bl_adata = blen_read_object(fbx_tmpl, fbx_adata, bl_arm)
            # reset transform.
            bl_adata.matrix_basis = Matrix()
        else:
            bl_adata = a_item[1] = blen_read_object(fbx_tmpl, fbx_adata, bl_arm)

        # Instantiate in scene.
        obj_base = scene.objects.link(bl_adata)
        obj_base.select = True

        # Switch to Edit mode.
        scene.objects.active = bl_adata
        is_hidden = bl_adata.hide
        bl_adata.hide = False  # Can't switch to Edit mode hidden objects...
        bpy.ops.object.mode_set(mode='EDIT')

        for b_uuid in bones:
            blen_read_armatures_add_bone(bl_adata, bl_arm, bones, b_uuid, matrices, fbx_tmpl)

        bpy.ops.object.mode_set(mode='OBJECT')
        bl_adata.hide = is_hidden

        # Bind armature to objects.
        arm_mat_back = bl_adata.matrix_basis.copy()
        for ob_me, (amat, mmat) in matrices.items():
            # bring global armature & mesh matrices into *Blender* global space.
            amat = global_matrix * amat
            mmat = global_matrix * mmat

            bl_adata.matrix_basis = amat
            me_mat_back = ob_me.matrix_basis.copy()
            ob_me.matrix_basis = mmat

            mod = ob_me.modifiers.new(elem_name_utf8, 'ARMATURE')
            mod.object = bl_adata

            ob_me.parent = bl_adata
            ob_me.matrix_basis = me_mat_back
            # Store the pair for later space corrections (bring back mesh in parent space).
            arm_parents.add((bl_adata, ob_me))
        bl_adata.matrix_basis = arm_mat_back

        # Set Pose transformations...
        for b_item, _b_size, _p_uuid, _clusters in bones.values():
            fbx_bdata, bl_bname = b_item
            fbx_props = (elem_find_first(fbx_bdata, b'Properties70'),
                         elem_find_first(fbx_tmpl, b'Properties70', fbx_elem_nil))
            assert(fbx_props[0] is not None)

            pbo = b_item[1] = bl_adata.pose.bones[bl_bname]
            transform_data = object_tdata_cache.get(pbo)
            if transform_data is None:
                # Bone correction, gives a mess as result. :(
                transform_data = blen_read_object_transform_preprocess(fbx_props, fbx_bdata, MAT_CONVERT_BONE)
                object_tdata_cache[pbo] = transform_data
            mat = blen_read_object_transform_do(transform_data)
            if pbo.parent:
                # Bring back matrix in armature space.
                mat = pbo.parent.matrix * mat
            pbo.matrix = mat


# ---------
# Animation
def blen_read_animations_curves_iter(fbx_curves, blen_start_offset, fbx_start_offset, fps):
    """
    Get raw FBX AnimCurve list, and yield values for all curves at each singular curves' keyframes,
    together with (blender) timing, in frames.
    blen_start_offset is expected in frames, while fbx_start_offset is expected in FBX ktime.
    """
    # As a first step, assume linear interpolation between key frames, we'll (try to!) handle more
    # of FBX curves later.
    from .fbx_utils import FBX_KTIME
    timefac = fps / FBX_KTIME

    curves = tuple([0,
                    elem_prop_first(elem_find_first(c[2], b'KeyTime')),
                    elem_prop_first(elem_find_first(c[2], b'KeyValueFloat')),
                    c]
                    for c in fbx_curves)

    while True:
        tmin = min(curves, key=lambda e: e[1][e[0]])
        curr_fbxktime = tmin[1][tmin[0]]
        curr_values = []
        do_break = True
        for item in curves:
            idx, times, values, fbx_curve = item
            if idx != -1:
                do_break = False
            if times[idx] > curr_fbxktime:
                if idx == 0:
                    curr_values.append((values[idx], fbx_curve))
                else:
                    # Interpolate between this key and the previous one.
                    ifac = (curr_fbxktime - times[idx - 1]) / (times[idx] - times[idx - 1])
                    curr_values.append(((values[idx] - values[idx - 1]) * ifac + values[idx - 1], fbx_curve))
            else:
                curr_values.append((values[idx], fbx_curve))
                if idx >= 0:
                    idx += 1
                    if idx >= len(times):
                        # We have reached our last element for this curve, stay on it from now on...
                        idx = -1
                    item[0] = idx
        curr_blenkframe = (curr_fbxktime - fbx_start_offset) * timefac + blen_start_offset
        yield (curr_blenkframe, curr_values)
        if do_break:
            break


def blen_read_animations_action_item(action, item, cnodes, global_matrix, force_global, fps):
    """
    'Bake' loc/rot/scale into the action, taking into account global_matrix if no parent is present.
    """
    from bpy.types import Object, PoseBone, ShapeKey
    from mathutils import Euler, Matrix
    from itertools import chain

    blen_curves = []
    fbx_curves = []
    props = []

    if isinstance(item, ShapeKey):
        props = [(item.path_from_id("value"), 1, "Key")]
    else:  # Object or PoseBone:
        if item not in object_tdata_cache:
            print("ERROR! object '%s' has no transform data, while being animated!" % ob.name)
            return

        # We want to create actions for objects, but for bones we 'reuse' armatures' actions!
        grpname = None
        if item.id_data != item:
            grpname = item.name

        # Since we might get other channels animated in the end, due to all FBX transform magic,
        # we need to add curves for whole loc/rot/scale in any case.
        props = [(item.path_from_id("location"), 3, grpname or "Location"),
                 None,
                 (item.path_from_id("scale"), 3, grpname or "Scale")]
        rot_mode = item.rotation_mode
        if rot_mode == 'QUATERNION':
            props[1] = (item.path_from_id("rotation_quaternion"), 4, grpname or "Quaternion Rotation")
        elif rot_mode == 'AXIS_ANGLE':
            props[1] = (item.path_from_id("rotation_axis_angle"), 4, grpname or "Axis Angle Rotation")
        else:  # Euler
            props[1] = (item.path_from_id("rotation_euler"), 3, grpname or "Euler Rotation")

    blen_curves = [action.fcurves.new(prop, channel, grpname)
                   for prop, nbr_channels, grpname in props for channel in range(nbr_channels)]

    for curves, fbxprop in cnodes.values():
        for (fbx_acdata, _blen_data), channel in curves.values():
            fbx_curves.append((fbxprop, channel, fbx_acdata))

    if isinstance(item, ShapeKey):
        # We assume for now blen init point is frame 1.0, while FBX ktime init point is 0.
        for frame, values in blen_read_animations_curves_iter(fbx_curves, 1.0, 0, fps):
            value = 0.0
            for v, (fbxprop, channel, _fbx_acdata) in values:
                assert(fbxprop == b'DeformPercent')
                assert(channel == 0)
                value = v / 100.0

            for fc, v in zip(blen_curves, (value,)):
                fc.keyframe_points.insert(frame, v, {'NEEDED', 'FAST'}).interpolation = 'LINEAR'

    else:  # Object or PoseBone:
        transform_data = object_tdata_cache[item]
        rot_prev = item.rotation_euler.copy()

        # Pre-compute inverted local rest matrix of the bone, if relevant.
        if isinstance(item, PoseBone):
            # First, get local (i.e. parentspace) rest pose matrix
            restmat = item.bone.matrix_local
            if item.parent:
                restmat = item.parent.bone.matrix_local.inverted() * restmat
            restmat_inv = restmat.inverted()

        # We assume for now blen init point is frame 1.0, while FBX ktime init point is 0.
        for frame, values in blen_read_animations_curves_iter(fbx_curves, 1.0, 0, fps):
            for v, (fbxprop, channel, _fbx_acdata) in values:
                if fbxprop == b'Lcl Translation':
                    transform_data.loc[channel] = v
                elif fbxprop == b'Lcl Rotation':
                    transform_data.rot[channel] = v
                elif fbxprop == b'Lcl Scaling':
                    transform_data.sca[channel] = v
            mat = blen_read_object_transform_do(transform_data)
            # Don't forget global matrix - but never for bones!
            if isinstance(item, Object):
                if (not item.parent or force_global) and global_matrix is not None:
                    mat = global_matrix * mat
            else:  # PoseBone, Urg!
                # And now, remove that rest pose matrix from current mat (also in parent space).
                mat = restmat_inv * mat

            # Now we have a virtual matrix of transform from AnimCurves, we can insert keyframes!
            loc, rot, sca = mat.decompose()
            if rot_mode == 'QUATERNION':
                pass  # nothing to do!
            elif rot_mode == 'AXIS_ANGLE':
                vec, ang = rot.to_axis_angle()
                rot = ang, vec.x, vec.y, vec.z
            else:  # Euler
                rot = rot.to_euler(rot_mode, rot_prev)
                rot_prev = rot
            for fc, value in zip(blen_curves, chain(loc, rot, sca)):
                fc.keyframe_points.insert(frame, value, {'NEEDED', 'FAST'}).interpolation = 'LINEAR'

    # Since we inserted our keyframes in 'FAST' mode, we have to update the fcurves now.
    for fc in blen_curves:
        fc.update()


def blen_read_animations(fbx_tmpl_astack, fbx_tmpl_alayer, stacks, scene, global_matrix, force_global_objects):
    """
    Recreate an action per stack/layer/object combinations.
    Note actions are not linked to objects, this is up to the user!
    """
    actions = {}
    for as_uuid, ((fbx_asdata, _blen_data), alayers) in stacks.items():
        stack_name = elem_name_ensure_class(fbx_asdata, b'AnimStack')
        for al_uuid, ((fbx_aldata, _blen_data), items) in alayers.items():
            layer_name = elem_name_ensure_class(fbx_aldata, b'AnimLayer')
            for item, cnodes in items.items():
                id_data = item.id_data
                key = (as_uuid, al_uuid, id_data)
                action = actions.get(key)
                if action is None:
                    action_name = "|".join((id_data.name, stack_name, layer_name))
                    actions[key] = action = bpy.data.actions.new(action_name)
                    action.use_fake_user = True
                blen_read_animations_action_item(action, item, cnodes, global_matrix,
                                                 item in force_global_objects, scene.render.fps)


# ----
# Mesh

def blen_read_geom_layerinfo(fbx_layer):
    return (
        elem_find_first_string(fbx_layer, b'Name'),
        elem_find_first_bytes(fbx_layer, b'MappingInformationType'),
        elem_find_first_bytes(fbx_layer, b'ReferenceInformationType'),
        )


def blen_read_geom_array_mapped_vert(
        mesh, blen_data, blend_attr,
        fbx_layer_data, fbx_layer_index,
        fbx_layer_mapping, fbx_layer_ref,
        stride, item_size, descr,
        ):
    # TODO, generic mapping apply function
    if fbx_layer_mapping == b'ByVertice':
        if fbx_layer_ref == b'Direct':
            assert(fbx_layer_index is None)
            # TODO, more generic support for mapping types
            for i, blen_data_item in enumerate(blen_data):
                setattr(blen_data_item, blend_attr,
                        fbx_layer_data[(i * stride): (i * stride) + item_size])
            return True
        else:
            print("warning layer %r ref type unsupported: %r" % (descr, fbx_layer_ref))
    else:
        print("warning layer %r mapping type unsupported: %r" % (descr, fbx_layer_mapping))

    return False


def blen_read_geom_array_mapped_edge(
        mesh, blen_data, blend_attr,
        fbx_layer_data, fbx_layer_index,
        fbx_layer_mapping, fbx_layer_ref,
        stride, item_size, descr,
        xform=None,
        ):
    if fbx_layer_mapping == b'ByEdge':
        if fbx_layer_ref == b'Direct':
            if stride == 1:
                if xform is None:
                    for i, blen_data_item in enumerate(blen_data):
                        setattr(blen_data_item, blend_attr,
                                fbx_layer_data[i])
                else:
                    for i, blen_data_item in enumerate(blen_data):
                        setattr(blen_data_item, blend_attr,
                                xform(fbx_layer_data[i]))
            else:
                if xform is None:
                    for i, blen_data_item in enumerate(blen_data):
                        setattr(blen_data_item, blend_attr,
                                fbx_layer_data[(i * stride): (i * stride) + item_size])
                else:
                    for i, blen_data_item in enumerate(blen_data):
                        setattr(blen_data_item, blend_attr,
                                xform(fbx_layer_data[(i * stride): (i * stride) + item_size]))
            return True
        else:
            print("warning layer %r ref type unsupported: %r" % (descr, fbx_layer_ref))
    else:
        print("warning layer %r mapping type unsupported: %r" % (descr, fbx_layer_mapping))

    return False


def blen_read_geom_array_mapped_polygon(
        mesh, blen_data, blend_attr,
        fbx_layer_data, fbx_layer_index,
        fbx_layer_mapping, fbx_layer_ref,
        stride, item_size, descr,
        xform=None,
        ):
    if fbx_layer_mapping == b'ByPolygon':
        if fbx_layer_ref == b'IndexToDirect':
            if stride == 1:
                for i, blen_data_item in enumerate(blen_data):
                    setattr(blen_data_item, blend_attr,
                            fbx_layer_data[i])
            else:
                for i, blen_data_item in enumerate(blen_data):
                    setattr(blen_data_item, blend_attr,
                            fbx_layer_data[(i * stride): (i * stride) + item_size])
            return True
        elif fbx_layer_ref == b'Direct':
            # looks like direct may have different meanings!
            assert(stride == 1)
            if xform is None:
                for i in range(len(fbx_layer_data)):
                    setattr(blen_data[i], blend_attr, fbx_layer_data[i])
            else:
                for i in range(len(fbx_layer_data)):
                    setattr(blen_data[i], blend_attr, xform(fbx_layer_data[i]))
            return True
        else:
            print("warning layer %r ref type unsupported: %r" % (descr, fbx_layer_ref))
    else:
        print("warning layer %r mapping type unsupported: %r" % (descr, fbx_layer_mapping))

    return False


def blen_read_geom_array_mapped_polyloop(
        mesh, blen_data, blend_attr,
        fbx_layer_data, fbx_layer_index,
        fbx_layer_mapping, fbx_layer_ref,
        stride, item_size, descr,
        ):
    if fbx_layer_mapping == b'ByPolygonVertex':
        if fbx_layer_ref == b'IndexToDirect':
            assert(fbx_layer_index is not None)
            for i, j in enumerate(fbx_layer_index):
                if j != -1:
                    setattr(blen_data[i], blend_attr,
                            fbx_layer_data[(j * stride): (j * stride) + item_size])
            return True
        else:
            print("warning layer %r ref type unsupported: %r" % (descr, fbx_layer_ref))
    elif fbx_layer_mapping == b'ByVertice':
        if fbx_layer_ref == b'Direct':
            assert(fbx_layer_index is None)
            loops = mesh.loops
            polygons = mesh.polygons
            for p in polygons:
                for i in p.loop_indices:
                    j = loops[i].vertex_index
                    setattr(blen_data[i], blend_attr,
                            fbx_layer_data[(j * stride): (j * stride) + item_size])
        else:
            print("warning layer %r ref type unsupported: %r" % (descr, fbx_layer_ref))
    else:
        print("warning layer %r mapping type unsupported: %r" % (descr, fbx_layer_mapping))

    return False


def blen_read_geom_layer_material(fbx_obj, mesh):
    fbx_layer = elem_find_first(fbx_obj, b'LayerElementMaterial')

    if fbx_layer is None:
        return

    (fbx_layer_name,
     fbx_layer_mapping,
     fbx_layer_ref,
     ) = blen_read_geom_layerinfo(fbx_layer)

    if fbx_layer_mapping == b'AllSame':
        # only to quiet warning
        return

    layer_id = b'Materials'
    fbx_layer_data = elem_prop_first(elem_find_first(fbx_layer, layer_id))

    blen_data = mesh.polygons
    blen_read_geom_array_mapped_polygon(
        mesh, blen_data, "material_index",
        fbx_layer_data, None,
        fbx_layer_mapping, fbx_layer_ref,
        1, 1, layer_id,
        )


def blen_read_geom_layer_uv(fbx_obj, mesh):
    for layer_id in (b'LayerElementUV',):
        for fbx_layer in elem_find_iter(fbx_obj, layer_id):
            # all should be valid
            (fbx_layer_name,
             fbx_layer_mapping,
             fbx_layer_ref,
             ) = blen_read_geom_layerinfo(fbx_layer)

            fbx_layer_data = elem_prop_first(elem_find_first(fbx_layer, b'UV'))
            fbx_layer_index = elem_prop_first(elem_find_first(fbx_layer, b'UVIndex'))

            uv_tex = mesh.uv_textures.new(name=fbx_layer_name)
            uv_lay = mesh.uv_layers[-1]
            blen_data = uv_lay.data[:]

            # some valid files omit this data
            if fbx_layer_data is None:
                print("%r %r missing data" % (layer_id, fbx_layer_name))
                continue

            blen_read_geom_array_mapped_polyloop(
                mesh, blen_data, "uv",
                fbx_layer_data, fbx_layer_index,
                fbx_layer_mapping, fbx_layer_ref,
                2, 2, layer_id,
                )


def blen_read_geom_layer_color(fbx_obj, mesh):
    # almost same as UV's
    for layer_id in (b'LayerElementColor',):
        for fbx_layer in elem_find_iter(fbx_obj, layer_id):
            # all should be valid
            (fbx_layer_name,
             fbx_layer_mapping,
             fbx_layer_ref,
             ) = blen_read_geom_layerinfo(fbx_layer)

            fbx_layer_data = elem_prop_first(elem_find_first(fbx_layer, b'Colors'))
            fbx_layer_index = elem_prop_first(elem_find_first(fbx_layer, b'ColorIndex'))

            color_lay = mesh.vertex_colors.new(name=fbx_layer_name)
            blen_data = color_lay.data[:]

            # some valid files omit this data
            if fbx_layer_data is None:
                print("%r %r missing data" % (layer_id, fbx_layer_name))
                continue

            # ignore alpha layer (read 4 items into 3)
            blen_read_geom_array_mapped_polyloop(
                mesh, blen_data, "color",
                fbx_layer_data, fbx_layer_index,
                fbx_layer_mapping, fbx_layer_ref,
                4, 3, layer_id,
                )


def blen_read_geom_layer_smooth(fbx_obj, mesh):
    fbx_layer = elem_find_first(fbx_obj, b'LayerElementSmoothing')

    if fbx_layer is None:
        return False

    # all should be valid
    (fbx_layer_name,
     fbx_layer_mapping,
     fbx_layer_ref,
     ) = blen_read_geom_layerinfo(fbx_layer)

    layer_id = b'Smoothing'
    fbx_layer_data = elem_prop_first(elem_find_first(fbx_layer, layer_id))

    # udk has 'Direct' mapped, with no Smoothing, not sure why, but ignore these
    if fbx_layer_data is None:
        return False

    if fbx_layer_mapping == b'ByEdge':
        # some models have bad edge data, we cant use this info...
        if not mesh.edges:
            return False

        blen_data = mesh.edges
        ok_smooth = blen_read_geom_array_mapped_edge(
            mesh, blen_data, "use_edge_sharp",
            fbx_layer_data, None,
            fbx_layer_mapping, fbx_layer_ref,
            1, 1, layer_id,
            xform=lambda s: not s,
            )
        return ok_smooth
    elif fbx_layer_mapping == b'ByPolygon':
        blen_data = mesh.polygons
        return blen_read_geom_array_mapped_polygon(
            mesh, blen_data, "use_smooth",
            fbx_layer_data, None,
            fbx_layer_mapping, fbx_layer_ref,
            1, 1, layer_id,
            xform=lambda s: (s != 0),  # smoothgroup bitflags, treat as booleans for now
            )
    else:
        print("warning layer %r mapping type unsupported: %r" % (fbx_layer.id, fbx_layer_mapping))
        return False


def blen_read_geom_layer_normal(fbx_obj, mesh):
    fbx_layer = elem_find_first(fbx_obj, b'LayerElementNormal')

    if fbx_layer is None:
        return False

    (fbx_layer_name,
     fbx_layer_mapping,
     fbx_layer_ref,
     ) = blen_read_geom_layerinfo(fbx_layer)

    layer_id = b'Normals'
    fbx_layer_data = elem_prop_first(elem_find_first(fbx_layer, layer_id))

    blen_data = mesh.vertices

    return blen_read_geom_array_mapped_vert(
        mesh, blen_data, "normal",
        fbx_layer_data, None,
        fbx_layer_mapping, fbx_layer_ref,
        3, 3, layer_id,
        )


def blen_read_geom(fbx_tmpl, fbx_obj):
    # TODO, use 'fbx_tmpl'
    elem_name_utf8 = elem_name_ensure_class(fbx_obj, b'Geometry')

    fbx_verts = elem_prop_first(elem_find_first(fbx_obj, b'Vertices'))
    fbx_polys = elem_prop_first(elem_find_first(fbx_obj, b'PolygonVertexIndex'))
    fbx_edges = elem_prop_first(elem_find_first(fbx_obj, b'Edges'))

    if fbx_verts is None:
        fbx_verts = ()
    if fbx_polys is None:
        fbx_polys = ()

    mesh = bpy.data.meshes.new(name=elem_name_utf8)
    mesh.vertices.add(len(fbx_verts) // 3)
    mesh.vertices.foreach_set("co", fbx_verts)

    if fbx_polys:
        mesh.loops.add(len(fbx_polys))
        poly_loop_starts = []
        poly_loop_totals = []
        poly_loop_prev = 0
        for i, l in enumerate(mesh.loops):
            index = fbx_polys[i]
            if index < 0:
                poly_loop_starts.append(poly_loop_prev)
                poly_loop_totals.append((i - poly_loop_prev) + 1)
                poly_loop_prev = i + 1
                index ^= -1
            l.vertex_index = index

        mesh.polygons.add(len(poly_loop_starts))
        mesh.polygons.foreach_set("loop_start", poly_loop_starts)
        mesh.polygons.foreach_set("loop_total", poly_loop_totals)

        blen_read_geom_layer_material(fbx_obj, mesh)
        blen_read_geom_layer_uv(fbx_obj, mesh)
        blen_read_geom_layer_color(fbx_obj, mesh)

    if fbx_edges:
        # edges in fact index the polygons (NOT the vertices)
        import array
        tot_edges = len(fbx_edges)
        edges_conv = array.array('i', [0]) * (tot_edges * 2)

        edge_index = 0
        for i in fbx_edges:
            e_a = fbx_polys[i]
            if e_a >= 0:
                e_b = fbx_polys[i + 1]
                if e_b < 0:
                    e_b ^= -1
            else:
                # Last index of polygon, wrap back to the start.

                # ideally we wouldn't have to search back,
                # but it should only be 2-3 iterations.
                j = i - 1
                while j >= 0 and fbx_polys[j] >= 0:
                    j -= 1
                e_a ^= -1
                e_b = fbx_polys[j + 1]

            edges_conv[edge_index] = e_a
            edges_conv[edge_index + 1] = e_b
            edge_index += 2

        mesh.edges.add(tot_edges)
        mesh.edges.foreach_set("vertices", edges_conv)

    # must be after edge, face loading.
    ok_smooth = blen_read_geom_layer_smooth(fbx_obj, mesh)

    ok_normals = blen_read_geom_layer_normal(fbx_obj, mesh)

    mesh.validate()

    if not ok_normals:
        mesh.calc_normals()

    if not ok_smooth:
        for p in mesh.polygons:
            p.use_smooth = True

    return mesh


def blen_read_shape(fbx_tmpl, fbx_sdata, fbx_bcdata, meshes, scene, global_matrix):
    from mathutils import Vector

    elem_name_utf8 = elem_name_ensure_class(fbx_sdata, b'Geometry')
    indices = elem_prop_first(elem_find_first(fbx_sdata, b'Indexes'), default=())
    dvcos = tuple(co for co in zip(*[iter(elem_prop_first(elem_find_first(fbx_sdata, b'Vertices'), default=()))] * 3))
    # We completely ignore normals here!
    weight = elem_prop_first(elem_find_first(fbx_bcdata, b'DeformPercent'), default=100.0) / 100.0
    vgweights = tuple(vgw / 100.0 for vgw in elem_prop_first(elem_find_first(fbx_bcdata, b'FullWeights'), default=()))

    assert(len(vgweights) == len(indices) == len(dvcos))
    create_vg = bool(set(vgweights) - {1.0})

    keyblocks = []

    for me, objects in meshes:
        vcos = tuple((idx, me.vertices[idx].co + Vector(dvco)) for idx, dvco in zip(indices, dvcos))
        objects = list({blen_o for fbx_o, blen_o in objects})
        assert(objects)

        if me.shape_keys is None:
            objects[0].shape_key_add(name="Basis", from_mix=False)
        objects[0].shape_key_add(name=elem_name_utf8, from_mix=False)
        me.shape_keys.use_relative = True  # Should already be set as such.

        kb = me.shape_keys.key_blocks[elem_name_utf8]
        for idx, co in vcos:
            kb.data[idx].co[:] = co
        kb.value = weight

        # Add vgroup if necessary.
        if create_vg:
            add_vgroup_to_objects(indices, vgweights, elem_name_utf8, objects)
            kb.vertex_group = elem_name_utf8

        keyblocks.append(kb)

    return keyblocks


# --------
# Material

def blen_read_material(fbx_tmpl, fbx_obj, cycles_material_wrap_map, use_cycles):
    elem_name_utf8 = elem_name_ensure_class(fbx_obj, b'Material')

    ma = bpy.data.materials.new(name=elem_name_utf8)

    const_color_white = 1.0, 1.0, 1.0

    fbx_props = (elem_find_first(fbx_obj, b'Properties70'),
                 elem_find_first(fbx_tmpl, b'Properties70', fbx_elem_nil))
    assert(fbx_props[0] is not None)

    ma_diff = elem_props_get_color_rgb(fbx_props, b'DiffuseColor', const_color_white)
    ma_spec = elem_props_get_color_rgb(fbx_props, b'SpecularColor', const_color_white)
    ma_alpha = elem_props_get_number(fbx_props, b'Opacity', 1.0)
    ma_spec_intensity = ma.specular_intensity = elem_props_get_number(fbx_props, b'SpecularFactor', 0.25) * 2.0
    ma_spec_hardness = elem_props_get_number(fbx_props, b'Shininess', 9.6)
    ma_refl_factor = elem_props_get_number(fbx_props, b'ReflectionFactor', 0.0)
    ma_refl_color = elem_props_get_color_rgb(fbx_props, b'ReflectionColor', const_color_white)

    if use_cycles:
        from . import cycles_shader_compat
        # viewport color
        ma.diffuse_color = ma_diff

        ma_wrap = cycles_shader_compat.CyclesShaderWrapper(ma)
        ma_wrap.diffuse_color_set(ma_diff)
        ma_wrap.specular_color_set([c * ma_spec_intensity for c in ma_spec])
        ma_wrap.hardness_value_set(((ma_spec_hardness + 3.0) / 5.0) - 0.65)
        ma_wrap.alpha_value_set(ma_alpha)
        ma_wrap.reflect_factor_set(ma_refl_factor)
        ma_wrap.reflect_color_set(ma_refl_color)

        cycles_material_wrap_map[ma] = ma_wrap
    else:
        # TODO, number BumpFactor isnt used yet
        ma.diffuse_color = ma_diff
        ma.specular_color = ma_spec
        ma.alpha = ma_alpha
        ma.specular_intensity = ma_spec_intensity
        ma.specular_hardness = ma_spec_hardness * 5.10 + 1.0

        if ma_refl_factor != 0.0:
            ma.raytrace_mirror.use = True
            ma.raytrace_mirror.reflect_factor = ma_refl_factor
            ma.mirror_color = ma_refl_color

    return ma


# -------
# Texture

def blen_read_texture(fbx_tmpl, fbx_obj, basedir, image_cache,
                      use_image_search):
    import os
    from bpy_extras import image_utils

    elem_name_utf8 = elem_name_ensure_class(fbx_obj, b'Texture')

    filepath = elem_find_first_string(fbx_obj, b'FileName')
    if os.sep == '/':
        filepath = filepath.replace('\\', '/')
    else:
        filepath = filepath.replace('/', '\\')

    image = image_cache.get(filepath)
    if image is not None:
        return image

    try:
        image = image_utils.load_image(
            filepath,
            dirname=basedir,
            place_holder=True,
            recursive=use_image_search,
            )

        image_cache[filepath] = image
        # name can be ../a/b/c
        image.name = os.path.basename(elem_name_utf8)

        return image
    except Exception as e:
        print("Warning, failed to load image file %s..." % filepath);
        return None


def blen_read_camera(fbx_tmpl, fbx_obj, global_scale):
    # meters to inches
    M2I = 0.0393700787

    elem_name_utf8 = elem_name_ensure_class(fbx_obj, b'NodeAttribute')

    fbx_props = (elem_find_first(fbx_obj, b'Properties70'),
                 elem_find_first(fbx_tmpl, b'Properties70', fbx_elem_nil))
    assert(fbx_props[0] is not None)

    camera = bpy.data.cameras.new(name=elem_name_utf8)

    camera.lens = elem_props_get_number(fbx_props, b'FocalLength', 35.0)
    camera.sensor_width = elem_props_get_number(fbx_props, b'FilmWidth', 32.0 * M2I) / M2I
    camera.sensor_height = elem_props_get_number(fbx_props, b'FilmHeight', 32.0 * M2I) / M2I

    filmaspect = camera.sensor_width / camera.sensor_height
    # film offset
    camera.shift_x = elem_props_get_number(fbx_props, b'FilmOffsetX', 0.0) / (M2I * camera.sensor_width)
    camera.shift_y = elem_props_get_number(fbx_props, b'FilmOffsetY', 0.0) / (M2I * camera.sensor_height * filmaspect)

    camera.clip_start = elem_props_get_number(fbx_props, b'NearPlane', 0.01) * global_scale
    camera.clip_end = elem_props_get_number(fbx_props, b'FarPlane', 100.0) * global_scale

    return camera


def blen_read_light(fbx_tmpl, fbx_obj, global_scale):
    import math
    elem_name_utf8 = elem_name_ensure_class(fbx_obj, b'NodeAttribute')

    fbx_props = (elem_find_first(fbx_obj, b'Properties70'),
                 elem_find_first(fbx_tmpl, b'Properties70', fbx_elem_nil))
    # rare
    if fbx_props[0] is None:
        lamp = bpy.data.lamps.new(name=elem_name_utf8, type='POINT')
        return lamp

    light_type = {
        0: 'POINT',
        1: 'SUN',
        2: 'SPOT'}.get(elem_props_get_enum(fbx_props, b'LightType', 0), 'POINT')

    lamp = bpy.data.lamps.new(name=elem_name_utf8, type=light_type)

    if light_type == 'SPOT':
        spot_size = elem_props_get_number(fbx_props, b'OuterAngle', None)
        if spot_size is None:
            # Deprecated.
            spot_size = elem_props_get_number(fbx_props, b'Cone angle', 45.0)
        lamp.spot_size = math.radians(spot_size)

        spot_blend = elem_props_get_number(fbx_props, b'InnerAngle', None)
        if spot_blend is None:
            # Deprecated.
            spot_blend = elem_props_get_number(fbx_props, b'HotSpot', 45.0)
        lamp.spot_blend = 1.0 - (spot_blend / spot_size)

    # TODO, cycles
    lamp.color = elem_props_get_color_rgb(fbx_props, b'Color', (1.0, 1.0, 1.0))
    lamp.energy = elem_props_get_number(fbx_props, b'Intensity', 100.0) / 100.0
    lamp.distance = elem_props_get_number(fbx_props, b'DecayStart', 25.0) * global_scale
    lamp.shadow_method = ('RAY_SHADOW' if elem_props_get_bool(fbx_props, b'CastShadow', True) else 'NOSHADOW')
    lamp.shadow_color = elem_props_get_color_rgb(fbx_props, b'ShadowColor', (0.0, 0.0, 0.0))

    return lamp


def is_ascii(filepath, size):
    with open(filepath, 'r', encoding="utf-8") as f:
        try:
            f.read(size)
            return True
        except UnicodeDecodeError:
            pass

    return False


def load(operator, context, filepath="",
         use_manual_orientation=False,
         axis_forward='-Z',
         axis_up='Y',
         global_scale=1.0,
         use_cycles=True,
         use_image_search=False,
         use_alpha_decals=False,
         decal_offset=0.0):

    global fbx_elem_nil
    fbx_elem_nil = FBXElem('', (), (), ())

    import os, time
    from bpy_extras.io_utils import axis_conversion
    from mathutils import Matrix

    from . import parse_fbx
    from .fbx_utils import RIGHT_HAND_AXES, FBX_FRAMERATES

    start_time = time.process_time()

    # detect ascii files
    if is_ascii(filepath, 24):
        operator.report({'ERROR'}, "ASCII FBX files are not supported %r" % filepath)
        return {'CANCELLED'}

    try:
        elem_root, version = parse_fbx.parse(filepath)
    except:
        import traceback
        traceback.print_exc()

        operator.report({'ERROR'}, "Couldn't open file %r" % filepath)
        return {'CANCELLED'}

    if version < 7100:
        operator.report({'ERROR'}, "Version %r unsupported, must be %r or later" % (version, 7100))
        return {'CANCELLED'}

    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

    # deselect all
    if bpy.ops.object.select_all.poll():
        bpy.ops.object.select_all(action='DESELECT')

    basedir = os.path.dirname(filepath)

    cycles_material_wrap_map = {}
    image_cache = {}
    if not use_cycles:
        texture_cache = {}

    # Tables: (FBX_byte_id -> [FBX_data, None or Blender_datablock])
    fbx_table_nodes = {}

    if use_alpha_decals:
        material_decals = set()
    else:
        material_decals = None

    scene = context.scene


    #### Get some info from GlobalSettings.

    fbx_settings = elem_find_first(elem_root, b'GlobalSettings')
    fbx_settings_props = elem_find_first(fbx_settings, b'Properties70')
    if fbx_settings is None or fbx_settings_props is None:
        operator.report({'ERROR'}, "No 'GlobalSettings' found in file %r" % filepath)
        return {'CANCELLED'}

    # Compute global matrix and scale.
    if not use_manual_orientation:
        axis_forward = (elem_props_get_integer(fbx_settings_props, b'FrontAxis', 1),
                        elem_props_get_integer(fbx_settings_props, b'FrontAxisSign', 1))
        axis_up = (elem_props_get_integer(fbx_settings_props, b'UpAxis', 2),
                   elem_props_get_integer(fbx_settings_props, b'UpAxisSign', 1))
        axis_coord = (elem_props_get_integer(fbx_settings_props, b'CoordAxis', 0),
                      elem_props_get_integer(fbx_settings_props, b'CoordAxisSign', 1))
        axis_key = (axis_up, axis_forward, axis_coord)
        axis_up, axis_forward = {v: k for k, v in RIGHT_HAND_AXES.items()}.get(axis_key, ('Z', 'Y'))
        # FBX base unit seems to be the centimeter, while raw Blender Unit is equivalent to the meter...
        global_scale = elem_props_get_number(fbx_settings_props, b'UnitScaleFactor', 100.0) / 100.0
    global_matrix = (Matrix.Scale(global_scale, 4) *
                     axis_conversion(from_forward=axis_forward, from_up=axis_up).to_4x4())

    # Compute framerate settings.
    custom_fps = elem_props_get_number(fbx_settings_props, b'CustomFrameRate', 25.0)
    time_mode = elem_props_get_enum(fbx_settings_props, b'TimeMode')
    real_fps = {eid: val for val, eid in FBX_FRAMERATES[1:]}.get(time_mode, custom_fps)
    if real_fps < 0.0:
        real_fps = 25.0
    scene.render.fps = round(real_fps)
    scene.render.fps_base = scene.render.fps / real_fps


    #### And now, the "real" data.

    fbx_defs = elem_find_first(elem_root, b'Definitions')  # can be None
    fbx_nodes = elem_find_first(elem_root, b'Objects')
    fbx_connections = elem_find_first(elem_root, b'Connections')

    if fbx_nodes is None:
        operator.report({'ERROR'}, "No 'Objects' found in file %r" % filepath)
        return {'CANCELLED'}
    if fbx_connections is None:
        operator.report({'ERROR'}, "No 'Connections' found in file %r" % filepath)
        return {'CANCELLED'}

    # ----
    # First load property templates
    # Load 'PropertyTemplate' values.
    # Key is a tuple, (ObjectType, FBXNodeType)
    # eg, (b'Texture', b'KFbxFileTexture')
    #     (b'Geometry', b'KFbxMesh')
    fbx_templates = {}

    def _():
        if fbx_defs is not None:
            for fbx_def in fbx_defs.elems:
                if fbx_def.id == b'ObjectType':
                    for fbx_subdef in fbx_def.elems:
                        if fbx_subdef.id == b'PropertyTemplate':
                            assert(fbx_def.props_type == b'S')
                            assert(fbx_subdef.props_type == b'S')
                            # (b'Texture', b'KFbxFileTexture') - eg.
                            key = fbx_def.props[0], fbx_subdef.props[0]
                            fbx_templates[key] = fbx_subdef
    _(); del _

    def fbx_template_get(key):
        ret = fbx_templates.get(key, fbx_elem_nil)
        if ret is None:
            # Newest FBX (7.4 and above) use no more 'K' in their type names...
            key = (key[0], key[1][1:])
            return fbx_templates.get(key, fbx_elem_nil)
        return ret

    # ----
    # Build FBX node-table
    def _():
        for fbx_obj in fbx_nodes.elems:
            # TODO, investigate what other items after first 3 may be
            assert(fbx_obj.props_type[:3] == b'LSS')
            fbx_uuid = elem_uuid(fbx_obj)
            fbx_table_nodes[fbx_uuid] = [fbx_obj, None]
    _(); del _

    # ----
    # Load in the data
    # http://download.autodesk.com/us/fbx/20112/FBX_SDK_HELP/index.html?url=
    #        WS73099cc142f487551fea285e1221e4f9ff8-7fda.htm,topicNumber=d0e6388

    fbx_connection_map = {}
    fbx_connection_map_reverse = {}

    def _():
        for fbx_link in fbx_connections.elems:
            c_type = fbx_link.props[0]
            if fbx_link.props_type[1:3] == b'LL':
                c_src, c_dst = fbx_link.props[1:3]
                fbx_connection_map.setdefault(c_src, []).append((c_dst, fbx_link))
                fbx_connection_map_reverse.setdefault(c_dst, []).append((c_src, fbx_link))
    _(); del _

    # ----
    # Load mesh data
    def _():
        fbx_tmpl = fbx_template_get((b'Geometry', b'KFbxMesh'))

        for fbx_uuid, fbx_item in fbx_table_nodes.items():
            fbx_obj, blen_data = fbx_item
            if fbx_obj.id != b'Geometry':
                continue
            if fbx_obj.props[-1] == b'Mesh':
                assert(blen_data is None)
                fbx_item[1] = blen_read_geom(fbx_tmpl, fbx_obj)
    _(); del _

    # ----
    # Load material data
    def _():
        fbx_tmpl = fbx_template_get((b'Material', b'KFbxSurfacePhong'))
        # b'KFbxSurfaceLambert'

        for fbx_uuid, fbx_item in fbx_table_nodes.items():
            fbx_obj, blen_data = fbx_item
            if fbx_obj.id != b'Material':
                continue
            assert(blen_data is None)
            fbx_item[1] = blen_read_material(fbx_tmpl, fbx_obj,
                                             cycles_material_wrap_map, use_cycles)
    _(); del _

    # ----
    # Load image data
    def _():
        fbx_tmpl = fbx_template_get((b'Texture', b'KFbxFileTexture'))

        for fbx_uuid, fbx_item in fbx_table_nodes.items():
            fbx_obj, blen_data = fbx_item
            if fbx_obj.id != b'Texture':
                continue
            fbx_item[1] = blen_read_texture(fbx_tmpl, fbx_obj, basedir, image_cache,
                                            use_image_search)
    _(); del _

    # ----
    # Load camera data
    def _():
        fbx_tmpl = fbx_template_get((b'NodeAttribute', b'KFbxCamera'))

        for fbx_uuid, fbx_item in fbx_table_nodes.items():
            fbx_obj, blen_data = fbx_item
            if fbx_obj.id != b'NodeAttribute':
                continue
            if fbx_obj.props[-1] == b'Camera':
                assert(blen_data is None)
                fbx_item[1] = blen_read_camera(fbx_tmpl, fbx_obj, global_scale)
    _(); del _

    # ----
    # Load lamp data
    def _():
        fbx_tmpl = fbx_template_get((b'NodeAttribute', b'KFbxLight'))

        for fbx_uuid, fbx_item in fbx_table_nodes.items():
            fbx_obj, blen_data = fbx_item
            if fbx_obj.id != b'NodeAttribute':
                continue
            if fbx_obj.props[-1] == b'Light':
                assert(blen_data is None)
                fbx_item[1] = blen_read_light(fbx_tmpl, fbx_obj, global_scale)
    _(); del _

    # ----
    # Connections
    def connection_filter_ex(fbx_uuid, fbx_id, dct):
        return [(c_found[0], c_found[1], c_type)
                for (c_uuid, c_type) in dct.get(fbx_uuid, ())
                # 0 is used for the root node, which isnt in fbx_table_nodes
                for c_found in (() if c_uuid is 0 else (fbx_table_nodes[c_uuid],))
                if (fbx_id is None) or (c_found[0].id == fbx_id)]

    def connection_filter_forward(fbx_uuid, fbx_id):
        return connection_filter_ex(fbx_uuid, fbx_id, fbx_connection_map)

    def connection_filter_reverse(fbx_uuid, fbx_id):
        return connection_filter_ex(fbx_uuid, fbx_id, fbx_connection_map_reverse)

    # Armatures pre-processing!
    fbx_objects_ignore = set()
    fbx_objects_parent_ignore = set()
    # Arg! In some case, root bone is used as armature as well, in Blender we have to 'insert'
    # an armature object between them, so to handle possible parents of root bones we need a mapping
    # from root bone uuid to Blender's object...
    fbx_bones_to_fake_object = dict()
    armatures = []
    def _():
        nonlocal fbx_objects_ignore, fbx_objects_parent_ignore
        for a_uuid, a_item in fbx_table_nodes.items():
            root_bone = False
            fbx_adata, bl_adata = a_item = fbx_table_nodes.get(a_uuid, (None, None))
            if fbx_adata is None or fbx_adata.id != b'Model':
                continue
            elif fbx_adata.props[2] != b'Null':
                if fbx_adata.props[2] not in {b'LimbNode', b'Root'}:
                    continue
                # In some cases, armatures have no root 'Null' object, we have to consider all root bones
                # as armatures in this case. :/
                root_bone = True
                for p_uuid, p_ctype in fbx_connection_map.get(a_uuid, ()):
                    if p_ctype.props[0] != b'OO':
                        continue
                    fbx_pdata, bl_pdata = p_item = fbx_table_nodes.get(p_uuid, (None, None))
                    if (fbx_pdata and fbx_pdata.id == b'Model' and fbx_pdata.props[2] in {b'LimbNode', b'Root', b'Null'}):
                        # Not a root bone...
                        root_bone = False
                if not root_bone:
                    continue
                fbx_bones_to_fake_object[a_uuid] = None

            bones = {}
            todo_uuids = set() if root_bone else {a_uuid}
            init_uuids = {a_uuid} if root_bone else set()
            done_uuids = set()
            while todo_uuids or init_uuids:
                if init_uuids:
                    p_uuid = None
                    uuids = [(uuid, None) for uuid in init_uuids]
                    init_uuids = None
                else:
                    p_uuid = todo_uuids.pop()
                    uuids = fbx_connection_map_reverse.get(p_uuid, ())
                # bone -> cluster -> skin -> mesh.
                # XXX Note: only LimbNode for now (there are also Limb's :/ ).
                for b_uuid, b_ctype in uuids:
                    if b_ctype and b_ctype.props[0] != b'OO':
                        continue
                    fbx_bdata, bl_bdata = b_item = fbx_table_nodes.get(b_uuid, (None, None))
                    if (fbx_bdata is None or fbx_bdata.id != b'Model' or
                        fbx_bdata.props[2] not in {b'LimbNode', b'Root'}):
                        continue

                    # Find bone's size.
                    size = 1.0
                    for t_uuid, t_ctype in fbx_connection_map_reverse.get(b_uuid, ()):
                        if t_ctype.props[0] != b'OO':
                            continue
                        fbx_tdata, _bl_tdata = fbx_table_nodes.get(t_uuid, (None, None))
                        if fbx_tdata is None or fbx_tdata.id != b'NodeAttribute' or fbx_tdata.props[2] != b'LimbNode':
                            continue
                        fbx_props = (elem_find_first(fbx_tdata, b'Properties70'),)
                        size = elem_props_get_number(fbx_props, b'Size', default=size)
                        break  # Only one bone data per bone!

                    clusters = []
                    for c_uuid, c_ctype in fbx_connection_map.get(b_uuid, ()):
                        if c_ctype.props[0] != b'OO':
                            continue
                        fbx_cdata, _bl_cdata = fbx_table_nodes.get(c_uuid, (None, None))
                        if fbx_cdata is None or fbx_cdata.id != b'Deformer' or fbx_cdata.props[2] != b'Cluster':
                            continue
                        meshes = set()
                        objects = []
                        for s_uuid, s_ctype in fbx_connection_map.get(c_uuid, ()):
                            if s_ctype.props[0] != b'OO':
                                continue
                            fbx_sdata, _bl_sdata = fbx_table_nodes.get(s_uuid, (None, None))
                            if fbx_sdata is None or fbx_sdata.id != b'Deformer' or fbx_sdata.props[2] != b'Skin':
                                continue
                            for m_uuid, m_ctype in fbx_connection_map.get(s_uuid, ()):
                                if m_ctype.props[0] != b'OO':
                                    continue
                                fbx_mdata, bl_mdata = fbx_table_nodes.get(m_uuid, (None, None))
                                if fbx_mdata is None or fbx_mdata.id != b'Geometry' or fbx_mdata.props[2] != b'Mesh':
                                    continue
                                # Blenmeshes are assumed already created at that time!
                                assert(isinstance(bl_mdata, bpy.types.Mesh))
                                # And we have to find all objects using this mesh!
                                for o_uuid, o_ctype in fbx_connection_map.get(m_uuid, ()):
                                    if o_ctype.props[0] != b'OO':
                                        continue
                                    fbx_odata, bl_odata = o_item = fbx_table_nodes.get(o_uuid, (None, None))
                                    if fbx_odata is None or fbx_odata.id != b'Model' or fbx_odata.props[2] != b'Mesh':
                                        continue
                                    # bl_odata is still None, objects have not yet been created...
                                    objects.append(o_item)
                                meshes.add(bl_mdata)
                            # Skin deformers are only here to connect clusters to meshes, for us, nothing else to do.
                        clusters.append((fbx_cdata, meshes, objects))
                    # For now, we assume there is only one cluster & skin per bone (at least for a given armature)!
                    # XXX This is not true, some apps export several clusters (kind of LoD), we only use first one!
                    # assert(len(clusters) <= 1)
                    bones[b_uuid] = (b_item, size, p_uuid if (p_uuid != a_uuid or root_bone) else None, clusters)
                    fbx_objects_parent_ignore.add(b_uuid)
                    done_uuids.add(p_uuid)
                    todo_uuids.add(b_uuid)
            if bones:
                # in case we have no Null parent, rootbone will be a_item too...
                armatures.append((a_item, bones))
                fbx_objects_ignore.add(a_uuid)
        fbx_objects_ignore |= fbx_objects_parent_ignore
        # We need to handle parenting at object-level for rootbones-as-armature case :/
        fbx_objects_parent_ignore -= set(fbx_bones_to_fake_object.keys())
    _(); del _

    def _():
        fbx_tmpl = fbx_template_get((b'Model', b'KFbxNode'))

        # Link objects, keep first, this also creates objects
        for fbx_uuid, fbx_item in fbx_table_nodes.items():
            if fbx_uuid in fbx_objects_ignore:
                # armatures and bones, handled separately.
                continue
            fbx_obj, blen_data = fbx_item
            if fbx_obj.id != b'Model' or fbx_obj.props[2] in {b'Root', b'LimbNode'}:
                continue

            # Create empty object or search for object data
            if fbx_obj.props[2] == b'Null':
                fbx_lnk_item = None
                ok = True
            else:
                ok = False
                for (fbx_lnk,
                     fbx_lnk_item,
                     fbx_lnk_type) in connection_filter_reverse(fbx_uuid, None):

                    if fbx_lnk_type.props[0] != b'OO':
                        continue
                    if not isinstance(fbx_lnk_item, bpy.types.ID):
                        continue
                    if isinstance(fbx_lnk_item, (bpy.types.Material, bpy.types.Image)):
                        continue
                    # Need to check why this happens, Bird_Leg.fbx
                    # This is basic object parenting, also used by "bones".
                    if isinstance(fbx_lnk_item, (bpy.types.Object)):
                        continue
                    ok = True
                    break
            if ok:
                # create when linking since we need object data
                obj = blen_read_object(fbx_tmpl, fbx_obj, fbx_lnk_item)
                assert(fbx_item[1] is None)
                fbx_item[1] = obj

                # instance in scene
                obj_base = scene.objects.link(obj)
                obj_base.select = True
    _(); del _

    # Now that we have objects...

    # I) We can handle shapes.
    blend_shape_channels = {}  # We do not need Shapes themselves, but keyblocks, for anim.
    def _():
        fbx_tmpl = fbx_template_get((b'Geometry', b'KFbxShape'))

        for s_uuid, s_item in fbx_table_nodes.items():
            fbx_sdata, bl_sdata = s_item = fbx_table_nodes.get(s_uuid, (None, None))
            if fbx_sdata is None or fbx_sdata.id != b'Geometry' or fbx_sdata.props[2] != b'Shape':
                continue

            # shape -> blendshapechannel -> blendshape -> mesh.
            for bc_uuid, bc_ctype in fbx_connection_map.get(s_uuid, ()):
                if bc_ctype.props[0] != b'OO':
                    continue
                fbx_bcdata, _bl_bcdata = fbx_table_nodes.get(bc_uuid, (None, None))
                if fbx_bcdata is None or fbx_bcdata.id != b'Deformer' or fbx_bcdata.props[2] != b'BlendShapeChannel':
                    continue
                meshes = []
                objects = []
                for bs_uuid, bs_ctype in fbx_connection_map.get(bc_uuid, ()):
                    if bs_ctype.props[0] != b'OO':
                        continue
                    fbx_bsdata, _bl_bsdata = fbx_table_nodes.get(bs_uuid, (None, None))
                    if fbx_bsdata is None or fbx_bsdata.id != b'Deformer' or fbx_bsdata.props[2] != b'BlendShape':
                        continue
                    for m_uuid, m_ctype in fbx_connection_map.get(bs_uuid, ()):
                        if m_ctype.props[0] != b'OO':
                            continue
                        fbx_mdata, bl_mdata = fbx_table_nodes.get(m_uuid, (None, None))
                        if fbx_mdata is None or fbx_mdata.id != b'Geometry' or fbx_mdata.props[2] != b'Mesh':
                            continue
                        # Blenmeshes are assumed already created at that time!
                        assert(isinstance(bl_mdata, bpy.types.Mesh))
                        # And we have to find all objects using this mesh!
                        objects = []
                        for o_uuid, o_ctype in fbx_connection_map.get(m_uuid, ()):
                            if o_ctype.props[0] != b'OO':
                                continue
                            fbx_odata, bl_odata = o_item = fbx_table_nodes.get(o_uuid, (None, None))
                            if fbx_odata is None or fbx_odata.id != b'Model' or fbx_odata.props[2] != b'Mesh':
                                continue
                            # bl_odata is still None, objects have not yet been created...
                            objects.append(o_item)
                        meshes.append((bl_mdata, objects))
                    # BlendShape deformers are only here to connect BlendShapeChannels to meshes, nothing else to do.

                # keyblocks is a list of tuples (mesh, keyblock) matching that shape/blendshapechannel, for animation.
                keyblocks = blen_read_shape(fbx_tmpl, fbx_sdata, fbx_bcdata, meshes, scene, global_matrix)
                blend_shape_channels[bc_uuid] = keyblocks
    _(); del _

    # II) We can finish armatures processing.
    arm_parents = set()
    force_global_objects = set()
    def _():
        fbx_tmpl = fbx_template_get((b'Model', b'KFbxNode'))

        blen_read_armatures(fbx_tmpl, armatures, fbx_bones_to_fake_object, scene, global_matrix, arm_parents)
    _(); del _

    def _():
        # Parent objects, after we created them...
        for fbx_uuid, fbx_item in fbx_table_nodes.items():
            if fbx_uuid in fbx_objects_parent_ignore:
                # Ignore bones, but not armatures here!
                continue
            fbx_obj, blen_data = fbx_item
            if fbx_obj.id != b'Model':
                continue
            # Handle rootbone-as-armature case :/
            t_data = fbx_bones_to_fake_object.get(fbx_uuid)
            if t_data is not None:
                blen_data = t_data
            elif blen_data is None:
                continue  # no object loaded.. ignore

            for (fbx_lnk,
                 fbx_lnk_item,
                 fbx_lnk_type) in connection_filter_forward(fbx_uuid, b'Model'):

                blen_data.parent = fbx_lnk_item
    _(); del _

    def _():
        if global_matrix is not None:
            # Apply global matrix last (after parenting)
            for fbx_uuid, fbx_item in fbx_table_nodes.items():
                if fbx_uuid in fbx_objects_parent_ignore:
                    # Ignore bones, but not armatures here!
                    continue
                fbx_obj, blen_data = fbx_item
                if fbx_obj.id != b'Model':
                    continue
                # Handle rootbone-as-armature case :/
                t_data = fbx_bones_to_fake_object.get(fbx_uuid)
                if t_data is not None:
                    blen_data = t_data
                elif blen_data is None:
                    continue  # no object loaded.. ignore

                if blen_data.parent is None:
                    blen_data.matrix_basis = global_matrix * blen_data.matrix_basis

            for (ob_arm, ob_me) in arm_parents:
                # Rigged meshes are in global space in FBX...
                ob_me.matrix_basis = global_matrix * ob_me.matrix_basis
                # And reverse-apply armature transform, so that it gets valid parented (local) position!
                ob_me.matrix_parent_inverse = ob_arm.matrix_basis.inverted()
                force_global_objects.add(ob_me)
    _(); del _

    # Animation!
    def _():
        fbx_tmpl_astack = fbx_template_get((b'AnimationStack', b'FbxAnimStack'))
        fbx_tmpl_alayer = fbx_template_get((b'AnimationLayer', b'FbxAnimLayer'))
        stacks = {}

        # AnimationStacks.
        for as_uuid, fbx_asitem in fbx_table_nodes.items():
            fbx_asdata, _blen_data = fbx_asitem
            if fbx_asdata.id != b'AnimationStack' or fbx_asdata.props[2] != b'':
                continue
            stacks[as_uuid] = (fbx_asitem, {})

        # AnimationLayers (mixing is completely ignored for now, each layer results in an independent set of actions).
        def get_astacks_from_alayer(al_uuid):
            for as_uuid, as_ctype in fbx_connection_map.get(al_uuid, ()):
                if as_ctype.props[0] != b'OO':
                    continue
                fbx_asdata, _bl_asdata = fbx_table_nodes.get(as_uuid, (None, None))
                if (fbx_asdata is None or fbx_asdata.id != b'AnimationStack' or
                    fbx_asdata.props[2] != b'' or as_uuid not in stacks):
                    continue
                yield as_uuid
        for al_uuid, fbx_alitem in fbx_table_nodes.items():
            fbx_aldata, _blen_data = fbx_alitem
            if fbx_aldata.id != b'AnimationLayer' or fbx_aldata.props[2] != b'':
                continue
            for as_uuid in get_astacks_from_alayer(al_uuid):
                _fbx_asitem, alayers = stacks[as_uuid]
                alayers[al_uuid] = (fbx_alitem, {})

        # AnimationCurveNodes (also the ones linked to actual animated data!).
        curvenodes = {}
        for acn_uuid, fbx_acnitem in fbx_table_nodes.items():
            fbx_acndata, _blen_data = fbx_acnitem
            if fbx_acndata.id != b'AnimationCurveNode' or fbx_acndata.props[2] != b'':
                continue
            cnode = curvenodes[acn_uuid] = {}
            items = []
            for n_uuid, n_ctype in fbx_connection_map.get(acn_uuid, ()):
                if n_ctype.props[0] != b'OP':
                    continue
                lnk_prop = n_ctype.props[3]
                if lnk_prop in {b'Lcl Translation', b'Lcl Rotation', b'Lcl Scaling'}:
                    ob = fbx_table_nodes[n_uuid][1]
                    if ob is None:
                        continue
                    items.append((ob, lnk_prop))
                elif lnk_prop == b'DeformPercent':  # Shape keys.
                    keyblocks = blend_shape_channels.get(n_uuid)
                    if keyblocks is None:
                        continue
                    items += [(kb, lnk_prop) for kb in keyblocks]
            for al_uuid, al_ctype in fbx_connection_map.get(acn_uuid, ()):
                if al_ctype.props[0] != b'OO':
                    continue
                fbx_aldata, _blen_aldata = fbx_alitem = fbx_table_nodes.get(al_uuid, (None, None))
                if fbx_aldata is None or fbx_aldata.id != b'AnimationLayer' or fbx_aldata.props[2] != b'':
                    continue
                for as_uuid in get_astacks_from_alayer(al_uuid):
                    _fbx_alitem, anim_items = stacks[as_uuid][1][al_uuid]
                    assert(_fbx_alitem == fbx_alitem)
                    for item, item_prop in items:
                        # No need to keep curvenode FBX data here, contains nothing useful for us.
                        anim_items.setdefault(item, {})[acn_uuid] = (cnode, item_prop)

        # AnimationCurves (real animation data).
        for ac_uuid, fbx_acitem in fbx_table_nodes.items():
            fbx_acdata, _blen_data = fbx_acitem
            if fbx_acdata.id != b'AnimationCurve' or fbx_acdata.props[2] != b'':
                continue
            for acn_uuid, acn_ctype in fbx_connection_map.get(ac_uuid, ()):
                if acn_ctype.props[0] != b'OP':
                    continue
                fbx_acndata, _bl_acndata = fbx_table_nodes.get(acn_uuid, (None, None))
                if (fbx_acndata is None or fbx_acndata.id != b'AnimationCurveNode' or
                    fbx_acndata.props[2] != b'' or acn_uuid not in curvenodes):
                    continue
                # Note this is an infamous simplification of the compound props stuff,
                # seems to be standard naming but we'll probably have to be smarter to handle more exotic files?
                channel = {b'd|X': 0, b'd|Y': 1, b'd|Z': 2, b'd|DeformPercent': 0}.get(acn_ctype.props[3], None)
                if channel is None:
                    continue
                curvenodes[acn_uuid][ac_uuid] = (fbx_acitem, channel)

        # And now that we have sorted all this, apply animations!
        blen_read_animations(fbx_tmpl_astack, fbx_tmpl_alayer, stacks, scene, global_matrix, force_global_objects)

    _(); del _

    def _():
        # link Material's to Geometry (via Model's)
        for fbx_uuid, fbx_item in fbx_table_nodes.items():
            fbx_obj, blen_data = fbx_item
            if fbx_obj.id != b'Geometry':
                continue

            mesh = fbx_table_nodes[fbx_uuid][1]

            # can happen in rare cases
            if mesh is None:
                continue

            for (fbx_lnk,
                 fbx_lnk_item,
                 fbx_lnk_type) in connection_filter_forward(fbx_uuid, b'Model'):

                # link materials
                fbx_lnk_uuid = elem_uuid(fbx_lnk)
                for (fbx_lnk_material,
                     material,
                     fbx_lnk_material_type) in connection_filter_reverse(fbx_lnk_uuid, b'Material'):

                    mesh.materials.append(material)

            # We have to validate mesh polygons' mat_idx, see T41015!
            # Some FBX seem to have an extra 'default' material which is not defined in FBX file.
            if mesh.validate_material_indices():
                print("WARNING: mesh '%s' had invalid material indices, those were reset to first material" % mesh.name)
    _(); del _

    def _():
        material_images = {}

        fbx_tmpl = fbx_template_get((b'Material', b'KFbxSurfacePhong'))
        # b'KFbxSurfaceLambert'

        # textures that use this material
        def texture_bumpfac_get(fbx_obj):
            assert(fbx_obj.id == b'Material')
            fbx_props = (elem_find_first(fbx_obj, b'Properties70'),
                         elem_find_first(fbx_tmpl, b'Properties70', fbx_elem_nil))
            assert(fbx_props[0] is not None)
            # (x / 7.142) is only a guess, cycles usable range is (0.0 -> 0.5)
            return elem_props_get_number(fbx_props, b'BumpFactor', 2.5) / 7.142

        def texture_mapping_get(fbx_obj):
            assert(fbx_obj.id == b'Texture')

            fbx_props = (elem_find_first(fbx_obj, b'Properties70'),
                         elem_find_first(fbx_tmpl, b'Properties70', fbx_elem_nil))
            assert(fbx_props[0] is not None)
            return (elem_props_get_vector_3d(fbx_props, b'Translation', (0.0, 0.0, 0.0)),
                    elem_props_get_vector_3d(fbx_props, b'Rotation', (0.0, 0.0, 0.0)),
                    elem_props_get_vector_3d(fbx_props, b'Scaling', (1.0, 1.0, 1.0)),
                    (bool(elem_props_get_enum(fbx_props, b'WrapModeU', 0)),
                     bool(elem_props_get_enum(fbx_props, b'WrapModeV', 0))))

        if not use_cycles:
            # Simple function to make a new mtex and set defaults
            def material_mtex_new(material, image, tex_map):
                tex = texture_cache.get(image)
                if tex is None:
                    tex = bpy.data.textures.new(name=image.name, type='IMAGE')
                    tex.image = image
                    texture_cache[image] = tex

                mtex = material.texture_slots.add()
                mtex.texture = tex
                mtex.texture_coords = 'UV'
                mtex.use_map_color_diffuse = False

                # No rotation here...
                mtex.offset[:] = tex_map[0]
                mtex.scale[:] = tex_map[2]
                return mtex

        for fbx_uuid, fbx_item in fbx_table_nodes.items():
            fbx_obj, blen_data = fbx_item
            if fbx_obj.id != b'Material':
                continue

            material = fbx_table_nodes[fbx_uuid][1]
            for (fbx_lnk,
                 image,
                 fbx_lnk_type) in connection_filter_reverse(fbx_uuid, b'Texture'):

                if use_cycles:
                    if fbx_lnk_type.props[0] == b'OP':
                        lnk_type = fbx_lnk_type.props[3]

                        ma_wrap = cycles_material_wrap_map[material]

                        # tx/rot/scale
                        tex_map = texture_mapping_get(fbx_lnk)
                        if (tex_map[0] == (0.0, 0.0, 0.0) and
                                tex_map[1] == (0.0, 0.0, 0.0) and
                                tex_map[2] == (1.0, 1.0, 1.0) and
                                tex_map[3] == (False, False)):
                            use_mapping = False
                        else:
                            use_mapping = True
                            tex_map_kw = {
                                "translation": tex_map[0],
                                "rotation": [-i for i in tex_map[1]],
                                "scale": [((1.0 / i) if i != 0.0 else 1.0) for i in tex_map[2]],
                                "clamp": tex_map[3],
                                }

                        if lnk_type == b'DiffuseColor':
                            ma_wrap.diffuse_image_set(image)
                            if use_mapping:
                                ma_wrap.diffuse_mapping_set(**tex_map_kw)
                        elif lnk_type == b'SpecularColor':
                            ma_wrap.specular_image_set(image)
                            if use_mapping:
                                ma_wrap.specular_mapping_set(**tex_map_kw)
                        elif lnk_type == b'ReflectionColor':
                            ma_wrap.reflect_image_set(image)
                            if use_mapping:
                                ma_wrap.reflect_mapping_set(**tex_map_kw)
                        elif lnk_type == b'TransparentColor':  # alpha
                            ma_wrap.alpha_image_set(image)
                            if use_mapping:
                                ma_wrap.alpha_mapping_set(**tex_map_kw)
                            if use_alpha_decals:
                                material_decals.add(material)
                        elif lnk_type == b'DiffuseFactor':
                            pass  # TODO
                        elif lnk_type == b'ShininessExponent':
                            ma_wrap.hardness_image_set(image)
                            if use_mapping:
                                ma_wrap.hardness_mapping_set(**tex_map_kw)
                        elif lnk_type == b'NormalMap' or lnk_type == b'Bump':  # XXX, applications abuse bump!
                            ma_wrap.normal_image_set(image)
                            ma_wrap.normal_factor_set(texture_bumpfac_get(fbx_obj))
                            if use_mapping:
                                ma_wrap.normal_mapping_set(**tex_map_kw)
                            """
                        elif lnk_type == b'Bump':
                            ma_wrap.bump_image_set(image)
                            ma_wrap.bump_factor_set(texture_bumpfac_get(fbx_obj))
                            if use_mapping:
                                ma_wrap.bump_mapping_set(**tex_map_kw)
                            """
                        else:
                            print("WARNING: material link %r ignored" % lnk_type)

                        material_images.setdefault(material, {})[lnk_type] = image
                else:
                    if fbx_lnk_type.props[0] == b'OP':
                        lnk_type = fbx_lnk_type.props[3]

                        # tx/rot/scale (rot is ignored here!).
                        tex_map = texture_mapping_get(fbx_lnk)

                        mtex = material_mtex_new(material, image, tex_map)

                        if lnk_type == b'DiffuseColor':
                            mtex.use_map_color_diffuse = True
                            mtex.blend_type = 'MULTIPLY'
                        elif lnk_type == b'SpecularColor':
                            mtex.use_map_color_spec = True
                            mtex.blend_type = 'MULTIPLY'
                        elif lnk_type == b'ReflectionColor':
                            mtex.use_map_raymir = True
                        elif lnk_type == b'TransparentColor':  # alpha
                            material.use_transparency = True
                            material.transparency_method = 'RAYTRACE'
                            material.alpha = 0.0
                            mtex.use_map_alpha = True
                            mtex.alpha_factor = 1.0
                            if use_alpha_decals:
                                material_decals.add(material)
                        elif lnk_type == b'DiffuseFactor':
                            mtex.use_map_diffuse = True
                        elif lnk_type == b'ShininessExponent':
                            mtex.use_map_hardness = True
                        elif lnk_type == b'NormalMap' or lnk_type == b'Bump':  # XXX, applications abuse bump!
                            mtex.texture.use_normal_map = True  # not ideal!
                            mtex.use_map_normal = True
                            mtex.normal_factor = texture_bumpfac_get(fbx_obj)
                            """
                        elif lnk_type == b'Bump':
                            mtex.use_map_normal = True
                            mtex.normal_factor = texture_bumpfac_get(fbx_obj)
                            """
                        else:
                            print("WARNING: material link %r ignored" % lnk_type)

                        material_images.setdefault(material, {})[lnk_type] = image

        # Check if the diffuse image has an alpha channel,
        # if so, use the alpha channel.

        # Note: this could be made optional since images may have alpha but be entirely opaque
        for fbx_uuid, fbx_item in fbx_table_nodes.items():
            fbx_obj, blen_data = fbx_item
            if fbx_obj.id != b'Material':
                continue
            material = fbx_table_nodes[fbx_uuid][1]
            image = material_images.get(material, {}).get(b'DiffuseColor')
            # do we have alpha?
            if image and image.depth == 32:
                if use_alpha_decals:
                    material_decals.add(material)

                if use_cycles:
                    ma_wrap = cycles_material_wrap_map[material]
                    if ma_wrap.node_bsdf_alpha.mute:
                        ma_wrap.alpha_image_set_from_diffuse()
                else:
                    if not any((True for mtex in material.texture_slots if mtex and mtex.use_map_alpha)):
                        mtex = material_mtex_new(material, image)

                        material.use_transparency = True
                        material.transparency_method = 'RAYTRACE'
                        material.alpha = 0.0
                        mtex.use_map_alpha = True
                        mtex.alpha_factor = 1.0

            # propagate mapping from diffuse to all other channels which have none defined.
            if use_cycles:
                ma_wrap = cycles_material_wrap_map[material]
                ma_wrap.mapping_set_from_diffuse()

    _(); del _

    def _():
        # Annoying workaround for cycles having no z-offset
        if material_decals and use_alpha_decals:
            for fbx_uuid, fbx_item in fbx_table_nodes.items():
                fbx_obj, blen_data = fbx_item
                if fbx_obj.id != b'Geometry':
                    continue
                if fbx_obj.props[-1] == b'Mesh':
                    mesh = fbx_item[1]

                    if decal_offset != 0.0:
                        for material in mesh.materials:
                            if material in material_decals:
                                for v in mesh.vertices:
                                    v.co += v.normal * decal_offset
                                break

                    if use_cycles:
                        for obj in (obj for obj in bpy.data.objects if obj.data == mesh):
                            obj.cycles_visibility.shadow = False
                    else:
                        for material in mesh.materials:
                            if material in material_decals:
                                # recieve but dont cast shadows
                                material.use_raytrace = False
    _(); del _

    print('Import finished in %.4f sec.' % (time.process_time() - start_time))
    return {'FINISHED'}
