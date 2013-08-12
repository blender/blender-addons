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

# FBX 7.1.0 -> 7.3.0 loader for Blender

# Not totally pep8 compliant.
#   pep8 import_fbx.py --ignore=E501,E123,E702,E125


import bpy

# -----
# Utils
from .parse_fbx import data_types


def tuple_deg_to_rad(eul):
    return (eul[0] / 57.295779513,
            eul[1] / 57.295779513,
            eul[2] / 57.295779513)


def elem_find_first(elem, id_search):
    for fbx_item in elem.elems:
        if fbx_item.id == id_search:
            return fbx_item


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


def elem_prop_first(elem):
    return elem.props[0] if (elem is not None) and elem.props else None


# ----
# Support for
# Properties70: { ... P:
def elem_props_find_first(elem, elem_prop_id):
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
            assert(elem_prop.props[3] == b'A')
        else:
            assert(elem_prop.props[1] == b'ColorRGB')
            assert(elem_prop.props[2] == b'Color')
            #print(elem_prop.props_type[4:7])
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
            assert(elem_prop.props[3] in {b'A', b'A+'})

        # we could allow other number types
        assert(elem_prop.props_type[4] == data_types.FLOAT64)

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


# ----------------------------------------------------------------------------
# Blender

# ------
# Object

def blen_read_object(fbx_obj, object_data):
    elem_name, elem_class = elem_split_name_class(fbx_obj)
    elem_name_utf8 = elem_name.decode('utf-8')

    const_vector_zero_3d = 0.0, 0.0, 0.0
    const_vector_one_3d = 1.0, 1.0, 1.0

    # Object data must be created already
    obj = bpy.data.objects.new(name=elem_name_utf8, object_data=object_data)

    fbx_props = elem_find_first(fbx_obj, b'Properties70')
    assert(fbx_props is not None)

    # ----
    # Misc Attributes

    obj.color[0:3] = elem_props_get_color_rgb(fbx_props, b'Color', (0.8, 0.8, 0.8))

    # ----
    # Transformation

    # This is quite involved, 'fbxRNode.cpp' from openscenegraph used as a reference

    loc = elem_props_get_vector_3d(fbx_props, b'Lcl Translation', const_vector_zero_3d)
    rot = elem_props_get_vector_3d(fbx_props, b'Lcl Rotation', const_vector_zero_3d)
    sca = elem_props_get_vector_3d(fbx_props, b'Lcl Scaling', const_vector_one_3d)

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

    from mathutils import Matrix, Euler
    from math import pi

    # translation
    lcl_translation = Matrix.Translation(loc)

    # rotation
    if obj.type == 'CAMERA':
        rot_alt_mat = Matrix.Rotation(pi / -2.0, 4, 'Y')
    elif obj.type == 'LAMP':
        rot_alt_mat = Matrix.Rotation(pi / -2.0, 4, 'X')
    else:
        rot_alt_mat = Matrix()

    # rotation
    lcl_rot = Euler(tuple_deg_to_rad(rot), rot_ord).to_matrix().to_4x4() * rot_alt_mat
    pre_rot = Euler(tuple_deg_to_rad(pre_rot), rot_ord).to_matrix().to_4x4()
    pst_rot = Euler(tuple_deg_to_rad(pst_rot), rot_ord).to_matrix().to_4x4()

    rot_ofs = Matrix.Translation(rot_ofs)
    rot_piv = Matrix.Translation(rot_piv)
    sca_ofs = Matrix.Translation(sca_ofs)
    sca_piv = Matrix.Translation(sca_piv)

    # scale
    lcl_scale = Matrix()
    lcl_scale[0][0], lcl_scale[1][1], lcl_scale[2][2] = sca

    obj.matrix_basis = (
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

    return obj


# ----
# Mesh

def blen_read_geom_layerinfo(fbx_layer):
    return (
        elem_find_first_string(fbx_layer, b'Name'),
        elem_find_first_bytes(fbx_layer, b'MappingInformationType'),
        elem_find_first_bytes(fbx_layer, b'ReferenceInformationType'),
        )


def blen_read_geom_array_mapped_vert(
    blen_data,
    fbx_layer_data, fbx_layer_index,
    fbx_layer_mapping, fbx_layer_ref,
    stride, descr,
    ):
    # TODO, generic mapping apply function
    if fbx_layer_mapping == b'ByVertice':
        if fbx_layer_ref == b'Direct':
            assert(fbx_layer_index is None)
            # TODO, more generic support for mapping types
            for i, blen_data_item in enumerate(blen_data):
                blen_data_item[:] = fbx_layer_data[(i * stride): (i * stride) + stride]
            return True
        else:
            print("warning layer %r ref type unsupported: %r", (descr, fbx_layer_ref))
    else:
        print("warning layer %r mapping type unsupported: %r", (descr, fbx_layer_mapping))

    return False


def blen_read_geom_array_mapped_poly(
    blen_data,
    fbx_layer_data, fbx_layer_index,
    fbx_layer_mapping, fbx_layer_ref,
    stride, descr,
    ):

    if fbx_layer_mapping == b'ByPolygonVertex':
        if fbx_layer_ref == b'IndexToDirect':
            assert(fbx_layer_index is not None)
            for i, j in enumerate(fbx_layer_index):
                blen_data[i][:] = fbx_layer_data[(j * stride): (j * stride) + stride]
            return True
        else:
            print("warning layer %r ref type unsupported: %r", (descr, fbx_layer_ref))
    else:
        print("warning layer %r mapping type unsupported: %r", (descr, fbx_layer_mapping))

    return False


def blen_read_geom_layer_uv(fbx_obj, mesh):

    for layer_id in (b'LayerElementUV',):
        fbx_layer = elem_find_first(fbx_obj, layer_id)

        if fbx_layer is None:
            continue

        # all should be valid
        (fbx_layer_name,
         fbx_layer_mapping,
         fbx_layer_ref,
         ) = blen_read_geom_layerinfo(fbx_layer)

        fbx_layer_data = elem_prop_first(elem_find_first(fbx_layer, b'UV'))
        fbx_layer_index = elem_prop_first(elem_find_first(fbx_layer, b'UVIndex'))

        uv_tex = mesh.uv_textures.new(name=fbx_layer_name)
        uv_lay = mesh.uv_layers[fbx_layer_name]
        blen_data = [luv.uv for luv in uv_lay.data]

        blen_read_geom_array_mapped_poly(
            blen_data,
            fbx_layer_data, fbx_layer_index,
            fbx_layer_mapping, fbx_layer_ref,
            2, layer_id,
            )


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

    blen_data = [v.normal for v in mesh.vertices]

    return blen_read_geom_array_mapped_vert(
        blen_data,
        fbx_layer_data, None,
        fbx_layer_mapping, fbx_layer_ref,
        3, layer_id,
        )


def blen_read_geom(fbx_obj):
    elem_name, elem_class = elem_split_name_class(fbx_obj)
    assert(elem_class == b'Geometry')
    elem_name_utf8 = elem_name.decode('utf-8')

    fbx_verts = elem_prop_first(elem_find_first(fbx_obj, b'Vertices'))
    fbx_polys = elem_prop_first(elem_find_first(fbx_obj, b'PolygonVertexIndex'))
    # TODO
    # fbx_edges = elem_prop_first(elem_find_first(fbx_obj, b'Edges'))

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
                index = -(index + 1)
            l.vertex_index = index
        poly_loop_starts.append(poly_loop_prev)
        poly_loop_totals.append((i - poly_loop_prev) + 1)

        mesh.polygons.add(len(poly_loop_starts))
        mesh.polygons.foreach_set("loop_start", poly_loop_starts)
        mesh.polygons.foreach_set("loop_total", poly_loop_totals)

        blen_read_geom_layer_uv(fbx_obj, mesh)

    ok_normals = blen_read_geom_layer_normal(fbx_obj, mesh)

    mesh.validate()

    if not ok_normals:
        mesh.calc_normals()

    return mesh


# --------
# Material

def blen_read_material(fbx_obj,
                       cycles_material_wrap_map, use_cycles):
    elem_name, elem_class = elem_split_name_class(fbx_obj)
    assert(elem_class == b'Material')
    elem_name_utf8 = elem_name.decode('utf-8')

    ma = bpy.data.materials.new(name=elem_name_utf8)

    const_color_white = 1.0, 1.0, 1.0

    fbx_props = elem_find_first(fbx_obj, b'Properties70')
    assert(fbx_props is not None)

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

    ma.use_fake_user = 1
    return ma


# -------
# Texture

def blen_read_texture(fbx_obj, basedir, image_cache,
                      use_image_search):
    import os
    from bpy_extras import image_utils

    elem_name, elem_class = elem_split_name_class(fbx_obj)
    assert(elem_class == b'Texture')
    elem_name_utf8 = elem_name.decode('utf-8')

    filepath = elem_find_first_string(fbx_obj, b'FileName')
    if os.sep == '/':
        filepath = filepath.replace('\\', '/')
    else:
        filepath = filepath.replace('/', '\\')

    image = image_cache.get(filepath)
    if image is not None:
        return image

    image = image_utils.load_image(
        filepath,
        dirname=basedir,
        place_holder=True,
        recursive=use_image_search,
        )

    image.name = elem_name_utf8

    return image


def blen_read_camera(fbx_obj, global_scale):
    # meters to inches
    M2I = 0.0393700787

    elem_name, elem_class = elem_split_name_class_nodeattr(fbx_obj)
    assert(elem_class == b'Camera')
    elem_name_utf8 = elem_name.decode('utf-8')

    fbx_props = elem_find_first(fbx_obj, b'Properties70')
    assert(fbx_props is not None)

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


def blen_read_light(fbx_obj, global_scale):
    import math
    elem_name, elem_class = elem_split_name_class_nodeattr(fbx_obj)
    assert(elem_class == b'Light')
    elem_name_utf8 = elem_name.decode('utf-8')

    fbx_props = elem_find_first(fbx_obj, b'Properties70')
    assert(fbx_props is not None)

    light_type = {
        0: 'POINT',
        1: 'SUN',
        2: 'SPOT'}.get(elem_props_get_enum(fbx_props, b'LightType', 0), 'POINT')

    lamp = bpy.data.lamps.new(name=elem_name_utf8, type=light_type)

    if light_type == 'SPOT':
        lamp.spot_size = math.radians(elem_props_get_number(fbx_props, b'Cone angle', 45.0))

    # TODO, cycles
    lamp.color = elem_props_get_number(fbx_props, b'Color', (1.0, 1.0, 1.0))
    lamp.energy = elem_props_get_number(fbx_props, b'Intensity', 100.0) / 100.0
    lamp.distance = elem_props_get_number(fbx_props, b'DecayStart', 25.0) * global_scale
    lamp.shadow_method = ('RAY_SHADOW' if elem_props_get_bool(fbx_props, b'CastShadow', True) else 'NOSHADOW')
    lamp.shadow_color = elem_props_get_color_rgb(fbx_props, b'ShadowColor', (0.0, 0.0, 0.0))

    return lamp


def load(operator, context, filepath="",
         global_matrix=None,
         use_cycles=True,
         use_image_search=False,
         use_alpha_decals=False,
         decal_offset=0.0):

    global_scale = (sum(global_matrix.to_scale()) / 3.0) if global_matrix else 1.0

    import os
    from . import parse_fbx

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

    fbx_nodes = elem_find_first(elem_root, b'Objects')
    fbx_connections = elem_find_first(elem_root, b'Connections')

    if fbx_nodes is None:
        return print("no 'Objects' found")
    if fbx_connections is None:
        return print("no 'Connections' found")

    def _():
        for fbx_obj in fbx_nodes.elems:
            assert(fbx_obj.props_type == b'LSS')
            fbx_uuid = elem_uuid(fbx_obj)
            fbx_table_nodes[fbx_uuid] = [fbx_obj, None]
    _(); del _

    # ----
    # First load in the data
    # http://download.autodesk.com/us/fbx/20112/FBX_SDK_HELP/index.html?url=WS73099cc142f487551fea285e1221e4f9ff8-7fda.htm,topicNumber=d0e6388

    fbx_connection_map = {}
    fbx_connection_map_reverse = {}

    def _():
        for fbx_link in fbx_connections.elems:
            # print(fbx_link)
            c_type = fbx_link.props[0]
            c_src, c_dst = fbx_link.props[1:3]
            # if c_type == b'OO':

            fbx_connection_map.setdefault(c_src, []).append((c_dst, fbx_link))
            fbx_connection_map_reverse.setdefault(c_dst, []).append((c_src, fbx_link))
    _(); del _

    # ----
    # Load mesh data
    def _():
        for fbx_uuid, fbx_item in fbx_table_nodes.items():
            fbx_obj, blen_data = fbx_item
            if fbx_obj.id != b'Geometry':
                continue
            if fbx_obj.props[-1] == b'Mesh':
                assert(blen_data is None)
                fbx_item[1] = blen_read_geom(fbx_obj)
    _(); del _

    # ----
    # Load material data
    def _():
        for fbx_uuid, fbx_item in fbx_table_nodes.items():
            fbx_obj, blen_data = fbx_item
            if fbx_obj.id != b'Material':
                continue
            assert(blen_data is None)
            fbx_item[1] = blen_read_material(fbx_obj,
                                             cycles_material_wrap_map, use_cycles)
    _(); del _

    # ----
    # Load image data
    def _():
        for fbx_uuid, fbx_item in fbx_table_nodes.items():
            fbx_obj, blen_data = fbx_item
            if fbx_obj.id != b'Texture':
                continue
            fbx_item[1] = blen_read_texture(fbx_obj, basedir, image_cache,
                                            use_image_search)
    _(); del _

    # ----
    # Load camera data
    def _():
        for fbx_uuid, fbx_item in fbx_table_nodes.items():
            fbx_obj, blen_data = fbx_item
            if fbx_obj.id != b'NodeAttribute':
                continue
            if fbx_obj.props[-1] == b'Camera':
                assert(blen_data is None)
                fbx_item[1] = blen_read_camera(fbx_obj, global_scale)
    _(); del _

    # ----
    # Load lamp data
    def _():
        for fbx_uuid, fbx_item in fbx_table_nodes.items():
            fbx_obj, blen_data = fbx_item
            if fbx_obj.id != b'NodeAttribute':
                continue
            if fbx_obj.props[-1] == b'Light':
                assert(blen_data is None)
                fbx_item[1] = blen_read_light(fbx_obj, global_scale)
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

    def _():
        # Link objects, keep first, this also creates objects
        for fbx_uuid, fbx_item in fbx_table_nodes.items():
            fbx_obj, blen_data = fbx_item
            if fbx_obj.id != b'Model':
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
                    ok = True
                    break
            if ok:
                # print(fbx_lnk_type)
                # create when linking since we need object data
                obj = blen_read_object(fbx_obj, fbx_lnk_item)
                assert(fbx_item[1] is None)
                fbx_item[1] = obj

                # instance in scene
                obj_base = scene.objects.link(obj)
                obj_base.select = True
    _(); del _

    def _():
        # Parent objects, after we created them...
        for fbx_uuid, fbx_item in fbx_table_nodes.items():
            fbx_obj, blen_data = fbx_item
            if fbx_obj.id != b'Model':
                continue
            if fbx_item[1] is None:
                continue  # no object loaded.. ignore

            for (fbx_lnk,
                 fbx_lnk_item,
                 fbx_lnk_type) in connection_filter_forward(fbx_uuid, b'Model'):

                fbx_item[1].parent = fbx_lnk_item
    _(); del _

    def _():
        if global_matrix is not None:
            # Apply global matrix last (after parenting)
            for fbx_uuid, fbx_item in fbx_table_nodes.items():
                fbx_obj, blen_data = fbx_item
                if fbx_obj.id != b'Model':
                    continue
                if fbx_item[1] is None:
                    continue  # no object loaded.. ignore

                if fbx_item[1].parent is None:
                    fbx_item[1].matrix_basis = global_matrix * fbx_item[1].matrix_basis
    _(); del _

    def _():
        # link Material's to Geometry (via Model's)
        for fbx_uuid, fbx_item in fbx_table_nodes.items():
            fbx_obj, blen_data = fbx_item
            if fbx_obj.id != b'Geometry':
                continue

            mesh = fbx_table_nodes[fbx_uuid][1]
            for (fbx_lnk,
                 fbx_lnk_item,
                 fbx_lnk_type) in connection_filter_forward(fbx_uuid, b'Model'):

                # link materials
                fbx_lnk_uuid = elem_uuid(fbx_lnk)
                for (fbx_lnk_material,
                     material,
                     fbx_lnk_material_type) in connection_filter_reverse(fbx_lnk_uuid, b'Material'):

                    mesh.materials.append(material)
    _(); del _

    def _():
        material_images = {}

        # textures that use this material
        def texture_bumpfac_get(fbx_obj):
            fbx_props = elem_find_first(fbx_obj, b'Properties70')
            return elem_props_get_number(fbx_props, b'BumpFactor', 1.0)

        if not use_cycles:
            # Simple function to make a new mtex and set defaults
            def material_mtex_new(material, image):
                tex = texture_cache.get(image)
                if tex is None:
                    tex = bpy.data.textures.new(name=image.name, type='IMAGE')
                    tex.image = image
                    texture_cache[image] = tex

                mtex = material.texture_slots.add()
                mtex.texture = tex
                mtex.texture_coords = 'UV'
                mtex.use_map_color_diffuse = False
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

                        if lnk_type == b'DiffuseColor':
                            ma_wrap.diffuse_image_set(image)
                        elif lnk_type == b'SpecularColor':
                            ma_wrap.specular_image_set(image)
                        elif lnk_type == b'ReflectionColor':
                            ma_wrap.reflect_image_set(image)
                        elif lnk_type == b'TransparentColor':  # alpha
                            ma_wrap.alpha_image_set(image)
                            if use_alpha_decals:
                                material_decals.add(material)
                        elif lnk_type == b'DiffuseFactor':
                            pass  # TODO
                        elif lnk_type == b'ShininessExponent':
                            ma_wrap.hardness_image_set(image)
                        elif lnk_type == b'NormalMap':
                            ma_wrap.normal_image_set(image)
                            ma_wrap.normal_factor_set(texture_bumpfac_get(fbx_obj))
                        elif lnk_type == b'Bump':
                            ma_wrap.bump_image_set(image)
                            ma_wrap.bump_factor_set(texture_bumpfac_get(fbx_obj))
                        else:
                            print("WARNING: material link %r ignored" % lnk_type)

                        material_images.setdefault(material, {})[lnk_type] = image
                else:
                    if fbx_lnk_type.props[0] == b'OP':
                        lnk_type = fbx_lnk_type.props[3]

                        mtex = material_mtex_new(material, image)

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
                        elif lnk_type == b'NormalMap':
                            tex.use_normal_map = True  # not ideal!
                            mtex.use_map_normal = True
                            mtex.normal_factor = texture_bumpfac_get(fbx_obj)
                        elif lnk_type == b'Bump':
                            mtex.use_map_normal = True
                            mtex.normal_factor = texture_bumpfac_get(fbx_obj)
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

    # print(list(sorted(locals().keys())))
    return {'FINISHED'}
