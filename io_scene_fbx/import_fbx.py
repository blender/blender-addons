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

import bpy

# -----
# Utils
from .parse_fbx import data_types


def tuple_deg_to_rad(eul):
    return eul[0] / 57.295779513, eul[1] / 57.295779513, eul[2] / 57.295779513


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
    """ Return
    """
    assert(elem.props_type[-2] == data_types.STRING)
    elem_name, elem_class = elem.props[-2].split(b'\x00\x01')
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
            assert(elem_prop.props[3] == b'A')

        # we could allow other number types
        assert(elem_prop.props_type[4] == data_types.FLOAT64)

        return elem_prop.props[4]
    return default


# ----------------------------------------------------------------------------
# Blender

# ------
# Object

def blen_read_object(fbx_obj, object_data, global_matrix):
    elem_name, elem_class = elem_split_name_class(fbx_obj)
    elem_name_utf8 = elem_name.decode('utf-8')

    const_vector_zero_3d = 0.0, 0.0, 0.0
    const_vector_one_3d = 1.0, 1.0, 1.0

    # Object data must be created already
    obj = bpy.data.objects.new(name=elem_name_utf8, object_data=object_data)

    fbx_props = elem_find_first(fbx_obj, b'Properties70')
    assert(fbx_props is not None)

    loc = elem_props_get_vector_3d(fbx_props, b'Lcl Translation', const_vector_zero_3d)
    rot = elem_props_get_vector_3d(fbx_props, b'Lcl Rotation', const_vector_zero_3d)
    sca = elem_props_get_vector_3d(fbx_props, b'Lcl Scaling', const_vector_one_3d)

    obj.location = loc
    obj.rotation_euler = tuple_deg_to_rad(rot)
    obj.scale = sca

    obj.matrix_basis = global_matrix * obj.matrix_basis

    return obj


# ----
# Mesh

def blen_read_geom_layerinfo(fbx_layer):
    return (
        elem_find_first_string(fbx_layer, b'Name'),
        elem_find_first_bytes(fbx_layer, b'MappingInformationType'),
        elem_find_first_bytes(fbx_layer, b'ReferenceInformationType'),
        )


def blen_read_geom_uv(fbx_obj, mesh):

    for uvlayer_id in (b'LayerElementUV',):
        fbx_uvlayer = elem_find_first(fbx_obj, uvlayer_id)

        if fbx_uvlayer is None:
            continue

        # all should be valid
        (fbx_uvlayer_name,
         fbx_uvlayer_mapping,
         fbx_uvlayer_ref,
         ) = blen_read_geom_layerinfo(fbx_uvlayer)

        # print(fbx_uvlayer_name, fbx_uvlayer_mapping, fbx_uvlayer_ref)

        fbx_layer_data = elem_prop_first(elem_find_first(fbx_uvlayer, b'UV'))
        fbx_layer_index = elem_prop_first(elem_find_first(fbx_uvlayer, b'UVIndex'))

        # TODO, generic mappuing apply function
        if fbx_uvlayer_mapping == b'ByPolygonVertex':
            if fbx_uvlayer_ref == b'IndexToDirect':
                # TODO, more generic support for mapping types
                uv_tex = mesh.uv_textures.new(name=fbx_uvlayer_name)
                uv_lay = mesh.uv_layers[fbx_uvlayer_name]
                uv_data = [luv.uv for luv in uv_lay.data]

                for i, j in enumerate(fbx_layer_index):
                    uv_data[i][:] = fbx_layer_data[(j * 2): (j * 2) + 2]
            else:
                print("warning uv layer ref type unsupported:", fbx_uvlayer_ref)
        else:
            print("warning uv layer mapping type unsupported:", fbx_uvlayer_mapping)


def blen_read_geom(fbx_obj):
    elem_name, elem_class = elem_split_name_class(fbx_obj)
    assert(elem_class == b'Geometry')
    elem_name_utf8 = elem_name.decode('utf-8')

    fbx_verts = elem_prop_first(elem_find_first(fbx_obj, b'Vertices'))
    fbx_polys = elem_prop_first(elem_find_first(fbx_obj, b'PolygonVertexIndex'))
    # TODO
    # fbx_edges = elem_prop_first(elem_find_first(fbx_obj, b'Edges'))

    mesh = bpy.data.meshes.new(name=elem_name_utf8)
    mesh.vertices.add(len(fbx_verts) // 3)
    mesh.vertices.foreach_set("co", fbx_verts)

    mesh.loops.add(len(fbx_polys))

    #poly_loops = []  # pairs (loop_start, loop_total)
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

    blen_read_geom_uv(fbx_obj, mesh)

    mesh.validate()
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


def load(operator, context, filepath="",
         global_matrix=None,
         use_cycles=True,
         use_image_search=False):

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
    # Connections
    def connection_filter_ex(fbx_uuid, fbx_id, dct):
        return [(c_found[0], c_found[1], c_type)
                for (c_uuid, c_type) in dct.get(fbx_uuid, ())
                for c_found in (fbx_table_nodes[c_uuid],)
                if c_found[0].id == fbx_id]

    def connection_filter_forward(fbx_uuid, fbx_id):
        return connection_filter_ex(fbx_uuid, fbx_id, fbx_connection_map)

    def connection_filter_reverse(fbx_uuid, fbx_id):
        return connection_filter_ex(fbx_uuid, fbx_id, fbx_connection_map_reverse)

    def _():
        # link Material's to Geometry (via Model's)
        for fbx_uuid, fbx_item in fbx_table_nodes.items():
            fbx_obj, blen_data = fbx_item
            if fbx_obj.id != b'Geometry':
                continue

            mesh = fbx_table_nodes[fbx_uuid][1]
            for fbx_lnk, fbx_lnk_item, fbx_lnk_type in connection_filter_forward(fbx_uuid, b'Model'):

                # create when linking since we need object data
                obj = blen_read_object(fbx_lnk, mesh, global_matrix)
                # fbx_lnk_item[1] = obj

                # instance in scene
                obj_base = scene.objects.link(obj)
                obj_base.select = True

                # link materials
                fbx_lnk_uuid = elem_uuid(fbx_lnk)
                for fbx_lnk_material, material, fbx_lnk_material_type in connection_filter_reverse(fbx_lnk_uuid, b'Material'):
                    mesh.materials.append(material)
    _(); del _

    def _():
        # textures that use this material
        def texture_bumpfac_get(fbx_obj):
            fbx_props = elem_find_first(fbx_obj, b'Properties70')
            return elem_props_get_number(fbx_props, b'BumpFactor', 1.0)

        for fbx_uuid, fbx_item in fbx_table_nodes.items():
            fbx_obj, blen_data = fbx_item
            if fbx_obj.id != b'Material':
                continue

            material = fbx_table_nodes[fbx_uuid][1]
            for fbx_lnk, image, fbx_lnk_type in connection_filter_reverse(fbx_uuid, b'Texture'):
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
                        elif lnk_type == b'TransparentColor':
                            ma_wrap.alpha_image_set(image)
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
                    if fbx_lnk_type.props[0] == b'OP':
                        lnk_type = fbx_lnk_type.props[3]

                        # cache converted texture
                        tex = texture_cache.get(image)
                        if tex is None:
                            tex = bpy.data.textures.new(name=image.name, type='IMAGE')
                            tex.image = image
                            texture_cache[image] = tex

                        mtex = material.texture_slots.add()
                        mtex.texture = tex
                        mtex.texture_coords = 'UV'
                        mtex.use_map_color_diffuse = False

                        if lnk_type == b'DiffuseColor':
                            mtex.use_map_color_diffuse = True
                            mtex.blend_type = 'MULTIPLY'
                        elif lnk_type == b'SpecularColor':
                            mtex.use_map_color_spec = True
                            mtex.blend_type = 'MULTIPLY'
                        elif lnk_type == b'ReflectionColor':
                            mtex.use_map_raymir = True
                        elif lnk_type == b'TransparentColor':
                            pass
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
    _(); del _

    # print(list(sorted(locals().keys())))

    return {'FINISHED'}
