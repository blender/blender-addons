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

bl_addon_info = {
    'name': 'Add Mesh: Archimedean Solids',
    'author': 'Buerbaum Martin (Pontiac)',
    'version': '0.1',
    'blender': (2, 5, 3),
    'location': 'View3D > Add > Mesh > Archimedean Solids',
    'description': 'Adds various archimedean solids to the Add Mesh menu',
    'url':
    'http://wiki.blender.org/index.php/Extensions:2.5/Py/' \
        'Scripts/Add_Mesh/',  # @todo Create wiki page and fix this link.
    'category': 'Add Mesh'}

import bpy
from math import sqrt
from mathutils import *
from bpy.props import *


# Stores the values of a list of properties and the
# operator id in a property group ('recall_op') inside the object.
# Could (in theory) be used for non-objects.
# Note: Replaces any existing property group with the same name!
# ob ... Object to store the properties in.
# op ... The operator that should be used.
# op_args ... A dictionary with valid Blender
#             properties (operator arguments/parameters).
def store_recall_properties(ob, op, op_args):
    if ob and op and op_args:
        recall_properties = {}

        # Add the operator identifier and op parameters to the properties.
        recall_properties['op'] = op.bl_idname
        recall_properties['args'] = op_args

        # Store new recall properties.
        ob['recall'] = recall_properties


# Apply view rotation to objects if "Align To" for
# new objects was set to "VIEW" in the User Preference.
def apply_object_align(context, ob):
    obj_align = bpy.context.user_preferences.edit.object_align

    if (context.space_data.type == 'VIEW_3D'
        and obj_align == 'VIEW'):
            view3d = context.space_data
            region = view3d.region_3d
            viewMatrix = region.view_matrix
            rot = viewMatrix.rotation_part()
            ob.rotation_euler = rot.invert().to_euler()


# Create a new mesh (object) from verts/edges/faces.
# verts/edges/faces ... List of vertices/edges/faces for the
#                       new mesh (as used in from_pydata).
# name ... Name of the new mesh (& object).
# edit ... Replace existing mesh data.
# Note: Using "edit" will destroy/delete existing mesh data.
def create_mesh_object(context, verts, edges, faces, name, edit):
    scene = context.scene
    obj_act = scene.objects.active

    # Can't edit anything, unless we have an active obj.
    if edit and not obj_act:
        return None

    # Create new mesh
    mesh = bpy.data.meshes.new(name)

    # Make a mesh from a list of verts/edges/faces.
    mesh.from_pydata(verts, edges, faces)

    # Update mesh geometry after adding stuff.
    mesh.update()

    # Deselect all objects.
    bpy.ops.object.select_all(action='DESELECT')

    if edit:
        # Replace geometry of existing object

        # Use the active obj and select it.
        ob_new = obj_act
        ob_new.selected = True

        if obj_act.mode == 'OBJECT':
            # Get existing mesh datablock.
            old_mesh = ob_new.data

            # Set object data to nothing
            ob_new.data = None

            # Clear users of existing mesh datablock.
            old_mesh.user_clear()

            # Remove old mesh datablock if no users are left.
            if (old_mesh.users == 0):
                bpy.data.meshes.remove(old_mesh)

            # Assign new mesh datablock.
            ob_new.data = mesh

    else:
        # Create new object
        ob_new = bpy.data.objects.new(name, mesh)

        # Link new object to the given scene and select it.
        scene.objects.link(ob_new)
        ob_new.selected = True

        # Place the object at the 3D cursor location.
        ob_new.location = scene.cursor_location

        apply_object_align(context, ob_new)

    if obj_act and obj_act.mode == 'EDIT':
        if not edit:
            # We are in EditMode, switch to ObjectMode.
            bpy.ops.object.mode_set(mode='OBJECT')

            # Select the active object as well.
            obj_act.selected = True

            # Apply location of new object.
            scene.update()

            # Join new object into the active.
            bpy.ops.object.join()

            # Switching back to EditMode.
            bpy.ops.object.mode_set(mode='EDIT')

            ob_new = obj_act

    else:
        # We are in ObjectMode.
        # Make the new object the active one.
        scene.objects.active = ob_new

    return ob_new


# A very simple "bridge" tool.
# Connects two equally long vertex rows with faces.
# Returns a list of the new faces (list of  lists)
#
# vertIdx1 ... First vertex list (list of vertex indices).
# vertIdx2 ... Second vertex list (list of vertex indices).
# closed ... Creates a loop (first & last are closed).
# flipped ... Invert the normal of the face(s).
#
# Note: You can set vertIdx1 to a single vertex index to create
#       a fan/star of faces.
# Note: If both vertex idx list are the same length they have
#       to have at least 2 vertices.
def createFaces(vertIdx1, vertIdx2, closed=False, flipped=False):
    faces = []

    if not vertIdx1 or not vertIdx2:
        return None

    if len(vertIdx1) < 2 and len(vertIdx2) < 2:
        return None

    fan = False
    if (len(vertIdx1) != len(vertIdx2)):
        if (len(vertIdx1) == 1 and len(vertIdx2) > 1):
            fan = True
        else:
            return None

    total = len(vertIdx2)

    if closed:
        # Bridge the start with the end.
        if flipped:
            face = [
                vertIdx1[0],
                vertIdx2[0],
                vertIdx2[total - 1]]
            if not fan:
                face.append(vertIdx1[total - 1])
            faces.append(face)

        else:
            face = [vertIdx2[0], vertIdx1[0]]
            if not fan:
                face.append(vertIdx1[total - 1])
            face.append(vertIdx2[total - 1])
            faces.append(face)

    # Bridge the rest of the faces.
    for num in range(total - 1):
        if flipped:
            if fan:
                face = [vertIdx2[num], vertIdx1[0], vertIdx2[num + 1]]
            else:
                face = [vertIdx2[num], vertIdx1[num],
                    vertIdx1[num + 1], vertIdx2[num + 1]]
            faces.append(face)
        else:
            if fan:
                face = [vertIdx1[0], vertIdx2[num], vertIdx2[num + 1]]
            else:
                face = [vertIdx1[num], vertIdx2[num],
                    vertIdx2[num + 1], vertIdx1[num + 1]]
            faces.append(face)

    return faces

########################


# Converts regular ngons to quads
# Note: Exists because most "fill" functions can not be
# controlled as easily.
def ngon_fill(ngon, offset=0):
    if offset > 0:
        for i in range(offset):
            ngon = ngon[1:] + [ngon[0]]

    if len(ngon) == 6:
        # Hexagon
        return [
            [ngon[0], ngon[1], ngon[2], ngon[3]],
            [ngon[0], ngon[3], ngon[4], ngon[5]]]

    elif len(ngon) == 8:
        # Octagon
        return [
            [ngon[0], ngon[1], ngon[2], ngon[3]],
            [ngon[0], ngon[3], ngon[4], ngon[7]],
            [ngon[7], ngon[4], ngon[5], ngon[6]]]

    else:
        return None
        # Not supported (yet)


# Returns the middle location of a _regular_ polygon.
# verts ... List of vertex coordinates (Vector) used by the ngon.
# ngon ... List of ngones (vertex indices of each ngon point)
def get_polygon_center(verts, ngons):
    faces = []

    for f in ngons:
        loc = Vector((0.0, 0.0, 0.0))

        for vert_idx in f:
            loc = loc + Vector(verts[vert_idx])

        loc = loc / len(f)

        vert_idx_new = len(verts)
        verts.append(loc)

        face_star = createFaces([vert_idx_new], f, closed=True)
        faces.extend(face_star)

    return verts, faces


# v1 ... First vertex point (Vector)
# v2 ... Second vertex point (Vector)
# edgelength_middle .. Length of the middle section (va->vb)
# (v1)----(va)---------------(vb)----(v2)
def subdivide_edge_2_cuts(v1, v2, edgelength_middle):
    length = (v2 - v1).length
    vn = (v2 - v1).normalize()

    edgelength_1a_b2 = (length - edgelength_middle) / 2.0

    va = v1 + vn * edgelength_1a_b2
    vb = v1 + vn * (edgelength_1a_b2 + edgelength_middle)

    return (va, vb)


# Invert the normal of a face.
# Inverts the order of the vertices to change the normal direction of a face.
def invert_face_normal(face):
    return [face[0]] + list(reversed(face[1:]))

########################


# http://en.wikipedia.org/wiki/Truncated_tetrahedron
def add_truncated_tetrahedron(hexagon_side=2.0 * sqrt(2.0) / 3.0,
    star_ngons=False):

    size = 2.0

    if (hexagon_side < 0.0
        or hexagon_side > size * sqrt(2.0)):
        return None, None

    verts = []
    faces = []

    # Vertices of a simple Tetrahedron
    verts_tet = [
        Vector((1.0, 1.0, -1.0)),    # tip 0
        Vector((-1.0, 1.0, 1.0)),    # tip 1
        Vector((1.0, -1.0, 1.0)),    # tip 2
        Vector((-1.0, -1.0, -1.0))]  # tip 3

    # Calculate truncated vertices
    tri0 = []
    tri1 = []
    tri2 = []
    tri3 = []

    va, vb = subdivide_edge_2_cuts(verts_tet[0], verts_tet[1], hexagon_side)
    va_idx, vb_idx = len(verts), len(verts) + 1
    verts.extend([va, vb])
    tri0.append(va_idx)
    tri1.append(vb_idx)
    va, vb = subdivide_edge_2_cuts(verts_tet[0], verts_tet[2], hexagon_side)
    va_idx, vb_idx = len(verts), len(verts) + 1
    verts.extend([va, vb])
    tri0.append(va_idx)
    tri2.append(vb_idx)
    va, vb = subdivide_edge_2_cuts(verts_tet[0], verts_tet[3], hexagon_side)
    va_idx, vb_idx = len(verts), len(verts) + 1
    verts.extend([va, vb])
    tri0.append(va_idx)
    tri3.append(vb_idx)
    va, vb = subdivide_edge_2_cuts(verts_tet[1], verts_tet[2], hexagon_side)
    va_idx, vb_idx = len(verts), len(verts) + 1
    verts.extend([va, vb])
    tri1.append(va_idx)
    tri2.append(vb_idx)
    va, vb = subdivide_edge_2_cuts(verts_tet[1], verts_tet[3], hexagon_side)
    va_idx, vb_idx = len(verts), len(verts) + 1
    verts.extend([va, vb])
    tri1.append(va_idx)
    tri3.append(vb_idx)
    va, vb = subdivide_edge_2_cuts(verts_tet[2], verts_tet[3], hexagon_side)
    va_idx, vb_idx = len(verts), len(verts) + 1
    verts.extend([va, vb])
    tri2.append(va_idx)
    tri3.append(vb_idx)

    # Hexagon polygons (n-gons)
    ngon012 = [tri0[1], tri0[0], tri1[0], tri1[1], tri2[1], tri2[0]]
    ngon031 = [tri0[0], tri0[2], tri3[0], tri3[1], tri1[2], tri1[0]]
    ngon023 = [tri0[2], tri0[1], tri2[0], tri2[2], tri3[2], tri3[0]]
    ngon132 = [tri1[1], tri1[2], tri3[1], tri3[2], tri2[2], tri2[1]]

    if star_ngons:
        # Create stars from hexagons
        verts, faces_star = get_polygon_center(verts,
            [ngon012, ngon031, ngon023, ngon132])
        faces.extend(faces_star)

    else:
        # Create quads from hexagons
        hex_quads = ngon_fill(ngon012)
        faces.extend(hex_quads)
        hex_quads = ngon_fill(ngon031)
        faces.extend(hex_quads)
        hex_quads = ngon_fill(ngon023)
        faces.extend(hex_quads)
        hex_quads = ngon_fill(ngon132)
        faces.extend(hex_quads)

    # Invert face normals
    tri1 = [tri1[0]] + list(reversed(tri1[1:]))
    tri3 = [tri3[0]] + list(reversed(tri3[1:]))

    # Tri faces
    faces.extend([tri0, tri1, tri2, tri3])

    return verts, faces


# http://en.wikipedia.org/wiki/Truncated_cube
# http://en.wikipedia.org/wiki/Cuboctahedron
def add_cuboctahedron(octagon_side=0.0, star_ngons=False):
    size = 2.0

    if (octagon_side > size or octagon_side < 0.0):
        return None, None, None

    s = octagon_side
    verts = []
    faces = []

    name = "Cuboctahedron"
    if s == 0.0:
        # Upper quad face
        dist = z = size / 2.0
        face_top = [len(verts), len(verts) + 1, len(verts) + 2, len(verts) + 3]
        verts.append(Vector((dist, 0.0, z)))
        verts.append(Vector((0.0, dist, z)))
        verts.append(Vector((-dist, 0.0, z)))
        verts.append(Vector((0.0, -dist, z)))
        faces.append(face_top)

        # 4 vertices on the z=0.0 plane
        z = 0.0
        v_xp_yp = len(verts)
        verts.append(Vector((dist, dist, z)))
        v_xp_yn = len(verts)
        verts.append(Vector((dist, -dist, z)))
        v_xn_yn = len(verts)
        verts.append(Vector((-dist, -dist, z)))
        v_xn_yp = len(verts)
        verts.append(Vector((-dist, dist, z)))

        # Lower quad face
        z = -size / 2.0
        face_bot = [len(verts), len(verts) + 1, len(verts) + 2, len(verts) + 3]
        verts.append((dist, 0.0, z))
        verts.append((0.0, -dist, z))
        verts.append((-dist, 0.0, z))
        verts.append((0.0, dist, z))
        faces.append(face_bot)

        # Last 4 faces
        face_yp = [v_xp_yp, face_bot[3], v_xn_yp, face_top[1]]
        face_yn = [v_xn_yn, face_bot[1], v_xp_yn, face_top[3]]
        face_xp = [v_xp_yn, face_bot[0], v_xp_yp, face_top[0]]
        face_xn = [v_xn_yp, face_bot[2], v_xn_yn, face_top[2]]
        faces.extend([face_yp, face_yn, face_xp, face_xn])

        # Tris top
        tri_xp_yp_zp = [v_xp_yp, face_top[1], face_top[0]]
        tri_xp_yn_zp = [v_xp_yn, face_top[0], face_top[3]]
        tri_xn_yp_zp = [v_xn_yp, face_top[2], face_top[1]]
        tri_xn_yn_zp = [v_xn_yn, face_top[3], face_top[2]]
        faces.extend([tri_xp_yp_zp, tri_xp_yn_zp, tri_xn_yp_zp, tri_xn_yn_zp])

        # Tris bottom
        tri_xp_yp_zn = [v_xp_yn, face_bot[1], face_bot[0]]
        tri_xp_yn_zn = [v_xp_yp, face_bot[0], face_bot[3]]
        tri_xn_yp_zn = [v_xn_yn, face_bot[2], face_bot[1]]
        tri_xn_yn_zn = [v_xn_yp, face_bot[3], face_bot[2]]
        faces.extend([tri_xp_yp_zn, tri_xp_yn_zn, tri_xn_yp_zn, tri_xn_yn_zn])

    else:
        name = "TruncatedCube"

        # Vertices of a simple Cube
        verts_cube = [
            Vector((1.0, 1.0, 1.0)),     # tip 0
            Vector((1.0, -1.0, 1.0)),    # tip 1
            Vector((-1.0, -1.0, 1.0)),   # tip 2
            Vector((-1.0, 1.0, 1.0)),    # tip 3
            Vector((1.0, 1.0, -1.0)),    # tip 4
            Vector((1.0, -1.0, -1.0)),   # tip 5
            Vector((-1.0, -1.0, -1.0)),  # tip 6
            Vector((-1.0, 1.0, -1.0))]   # tip 7

        tri_xp_yp_zp = []
        tri_xp_yn_zp = []
        tri_xn_yp_zp = []
        tri_xn_yn_zp = []
        tri_xp_yp_zn = []
        tri_xp_yn_zn = []
        tri_xn_yp_zn = []
        tri_xn_yn_zn = []

        # Prepare top & bottom octagons.
        ngon_top = []
        ngon_bot = []

        # Top edges
        va, vb = subdivide_edge_2_cuts(verts_cube[0], verts_cube[1], s)
        va_idx, vb_idx = len(verts), len(verts) + 1
        verts.extend([va, vb])
        tri_xp_yp_zp.append(va_idx)
        tri_xp_yn_zp.append(vb_idx)
        ngon_top.extend([va_idx, vb_idx])
        va, vb = subdivide_edge_2_cuts(verts_cube[1], verts_cube[2], s)
        va_idx, vb_idx = len(verts), len(verts) + 1
        verts.extend([va, vb])
        tri_xp_yn_zp.append(va_idx)
        tri_xn_yn_zp.append(vb_idx)
        ngon_top.extend([va_idx, vb_idx])
        va, vb = subdivide_edge_2_cuts(verts_cube[2], verts_cube[3], s)
        va_idx, vb_idx = len(verts), len(verts) + 1
        verts.extend([va, vb])
        tri_xn_yn_zp.append(va_idx)
        tri_xn_yp_zp.append(vb_idx)
        ngon_top.extend([va_idx, vb_idx])
        va, vb = subdivide_edge_2_cuts(verts_cube[3], verts_cube[0], s)
        va_idx, vb_idx = len(verts), len(verts) + 1
        verts.extend([va, vb])
        tri_xn_yp_zp.append(va_idx)
        tri_xp_yp_zp.append(vb_idx)
        ngon_top.extend([va_idx, vb_idx])

        # Top-down edges
        va, vb = subdivide_edge_2_cuts(verts_cube[0], verts_cube[4], s)
        va_idx, vb_idx = len(verts), len(verts) + 1
        verts.extend([va, vb])
        tri_xp_yp_zp.append(va_idx)
        tri_xp_yp_zn.append(vb_idx)
        top_down_0 = [va_idx, vb_idx]
        va, vb = subdivide_edge_2_cuts(verts_cube[1], verts_cube[5], s)
        va_idx, vb_idx = len(verts), len(verts) + 1
        verts.extend([va, vb])
        tri_xp_yn_zp.append(va_idx)
        tri_xp_yn_zn.append(vb_idx)
        top_down_1 = [va_idx, vb_idx]
        va, vb = subdivide_edge_2_cuts(verts_cube[2], verts_cube[6], s)
        va_idx, vb_idx = len(verts), len(verts) + 1
        verts.extend([va, vb])
        tri_xn_yn_zp.append(va_idx)
        tri_xn_yn_zn.append(vb_idx)
        top_down_2 = [va_idx, vb_idx]
        va, vb = subdivide_edge_2_cuts(verts_cube[3], verts_cube[7], s)
        va_idx, vb_idx = len(verts), len(verts) + 1
        verts.extend([va, vb])
        tri_xn_yp_zp.append(va_idx)
        tri_xn_yp_zn.append(vb_idx)
        top_down_3 = [va_idx, vb_idx]

        # Bottom edges
        va, vb = subdivide_edge_2_cuts(verts_cube[4], verts_cube[5], s)
        va_idx, vb_idx = len(verts), len(verts) + 1
        verts.extend([va, vb])
        tri_xp_yp_zn.append(va_idx)
        tri_xp_yn_zn.append(vb_idx)
        ngon_bot.extend([va_idx, vb_idx])
        va, vb = subdivide_edge_2_cuts(verts_cube[5], verts_cube[6], s)
        va_idx, vb_idx = len(verts), len(verts) + 1
        verts.extend([va, vb])
        tri_xp_yn_zn.append(va_idx)
        tri_xn_yn_zn.append(vb_idx)
        ngon_bot.extend([va_idx, vb_idx])
        va, vb = subdivide_edge_2_cuts(verts_cube[6], verts_cube[7], s)
        va_idx, vb_idx = len(verts), len(verts) + 1
        verts.extend([va, vb])
        tri_xn_yn_zn.append(va_idx)
        tri_xn_yp_zn.append(vb_idx)
        ngon_bot.extend([va_idx, vb_idx])
        va, vb = subdivide_edge_2_cuts(verts_cube[7], verts_cube[4], s)
        va_idx, vb_idx = len(verts), len(verts) + 1
        verts.extend([va, vb])
        tri_xn_yp_zn.append(va_idx)
        tri_xp_yp_zn.append(vb_idx)
        ngon_bot.extend([va_idx, vb_idx])

        # Octagon polygons (n-gons)
        ngon_0 = [
            top_down_0[1], top_down_0[0], ngon_top[0], ngon_top[1],
            top_down_1[0], top_down_1[1], ngon_bot[1], ngon_bot[0]]
        ngon_1 = [
            top_down_1[1], top_down_1[0], ngon_top[2], ngon_top[3],
            top_down_2[0], top_down_2[1], ngon_bot[3], ngon_bot[2]]
        ngon_2 = [
            top_down_2[1], top_down_2[0], ngon_top[4], ngon_top[5],
            top_down_3[0], top_down_3[1], ngon_bot[5], ngon_bot[4]]
        ngon_3 = [
            top_down_3[1], top_down_3[0], ngon_top[6], ngon_top[7],
            top_down_0[0], top_down_0[1], ngon_bot[7], ngon_bot[6]]

        # Invert face normals where needed.
        ngon_top = invert_face_normal(ngon_top)
        tri_xp_yp_zp = invert_face_normal(tri_xp_yp_zp)
        tri_xp_yn_zn = invert_face_normal(tri_xp_yn_zn)
        tri_xn_yp_zn = invert_face_normal(tri_xn_yp_zn)
        tri_xn_yn_zn = invert_face_normal(tri_xn_yn_zn)

        # Tris
        faces.extend([tri_xp_yp_zp, tri_xp_yn_zp, tri_xn_yp_zp, tri_xn_yn_zp])
        faces.extend([tri_xp_yp_zn, tri_xp_yn_zn, tri_xn_yp_zn, tri_xn_yn_zn])

        if star_ngons:
            ngons = [ngon_top, ngon_bot, ngon_0, ngon_1, ngon_2, ngon_3]
            # Create stars from octagons.
            verts, faces_star = get_polygon_center(verts, ngons)
            faces.extend(faces_star)

        else:
            # Create quads from octagons.

            # The top octagon is the only polygon we don't need to offset.
            oct_quads = ngon_fill(ngon_top)
            faces.extend(oct_quads)

            ngons = [ngon_bot, ngon_0, ngon_1, ngon_2, ngon_3]
            for ngon in ngons:
                # offset=1 Offset vertices so QUADS are created with
                # orthagonal edges. Superficial change - Could be omitted.
                oct_quads = ngon_fill(ngon, offset=1)
                faces.extend(oct_quads)

    return verts, faces, name


# http://en.wikipedia.org/wiki/Rhombicuboctahedron
# Note: quad_size=0 would result in a Cuboctahedron
def add_rhombicuboctahedron(quad_size=sqrt(2.0) / (1.0 + sqrt(2) / 2.0)):
    size = 2.0

    if (quad_size > size or quad_size < 0.0):
        return None, None

    faces = []
    verts = []

    # Top & bottom faces (quads)
    face_top = []
    face_bot = []
    for z, up in [(size / 2.0, True), (-size / 2.0, False)]:
        face = []
        face.append(len(verts))
        verts.append(Vector((quad_size / 2.0, quad_size / 2.0, z)))
        face.append(len(verts))
        verts.append(Vector((quad_size / 2.0, -quad_size / 2.0, z)))
        face.append(len(verts))
        verts.append(Vector((-quad_size / 2.0, -quad_size / 2.0, z)))
        face.append(len(verts))
        verts.append(Vector((-quad_size / 2.0, quad_size / 2.0, z)))

        if up:
            # Top face (quad)
            face_top = face
        else:
            # Bottom face (quad)
            face_bot = face

    edgeloop_up = []
    edgeloop_low = []
    for z, up in [(quad_size / 2.0, True), (-quad_size / 2.0, False)]:
        edgeloop = []

        edgeloop.append(len(verts))
        verts.append(Vector((size / 2.0, quad_size / 2.0, z)))
        edgeloop.append(len(verts))
        verts.append(Vector((size / 2.0, -quad_size / 2.0, z)))
        edgeloop.append(len(verts))
        verts.append(Vector((quad_size / 2.0, -size / 2.0, z)))
        edgeloop.append(len(verts))
        verts.append(Vector((-quad_size / 2.0, -size / 2.0, z)))
        edgeloop.append(len(verts))
        verts.append(Vector((-size / 2.0, -quad_size / 2.0, z)))
        edgeloop.append(len(verts))
        verts.append(Vector((-size / 2.0, quad_size / 2.0, z)))
        edgeloop.append(len(verts))
        verts.append(Vector((-quad_size / 2.0, size / 2.0, z)))
        edgeloop.append(len(verts))
        verts.append(Vector((quad_size / 2.0, size / 2.0, z)))

        if up:
            # Upper 8-sider
            edgeloop_up = edgeloop
        else:
            # Lower 8-sider
            edgeloop_low = edgeloop

    face_top_idx = len(faces)
    faces.append(face_top)
    faces.append(face_bot)
    faces_middle = createFaces(edgeloop_low, edgeloop_up, closed=True)
    faces.extend(faces_middle)

    # Upper Quads
    faces.append([edgeloop_up[0], face_top[0], face_top[1], edgeloop_up[1]])
    faces.append([edgeloop_up[2], face_top[1], face_top[2], edgeloop_up[3]])
    faces.append([edgeloop_up[4], face_top[2], face_top[3], edgeloop_up[5]])
    faces.append([edgeloop_up[6], face_top[3], face_top[0], edgeloop_up[7]])

    # Upper Tris
    faces.append([face_top[0], edgeloop_up[0], edgeloop_up[7]])
    faces.append([face_top[1], edgeloop_up[2], edgeloop_up[1]])
    faces.append([face_top[2], edgeloop_up[4], edgeloop_up[3]])
    faces.append([face_top[3], edgeloop_up[6], edgeloop_up[5]])

    # Lower Quads
    faces.append([edgeloop_low[0], edgeloop_low[1], face_bot[1], face_bot[0]])
    faces.append([edgeloop_low[2], edgeloop_low[3], face_bot[2], face_bot[1]])
    faces.append([edgeloop_low[4], edgeloop_low[5], face_bot[3], face_bot[2]])
    faces.append([edgeloop_low[6], edgeloop_low[7], face_bot[0], face_bot[3]])

    # Lower Tris
    faces.append([face_bot[0], edgeloop_low[7], edgeloop_low[0]])
    faces.append([face_bot[1], edgeloop_low[1], edgeloop_low[2]])
    faces.append([face_bot[2], edgeloop_low[3], edgeloop_low[4]])
    faces.append([face_bot[3], edgeloop_low[5], edgeloop_low[6]])

    # Invert face normal
    f = faces[face_top_idx]
    faces[face_top_idx] = invert_face_normal(faces[face_top_idx])

    return verts, faces


# http://en.wikipedia.org/wiki/Truncated_octahedron
def add_truncated_octahedron(hexagon_side=sqrt(2) / 3.0, star_ngons=False):
    if (hexagon_side < 0.0
        or hexagon_side > sqrt(2)):
        return None, None

    hs = hexagon_side

    verts = []
    faces = []

    # Vertices of a simple Octahedron
    verts_oct = [
        Vector((0.0, 0.0, 1.0)),    # tip 0 - Top
        Vector((1.0, 0.0, 0.0)),    # tip 1 - xp y0
        Vector((0.0, -1.0, 0.0)),   # tip 2 - x0 yn
        Vector((-1.0, 0.0, 0.0)),   # tip 3 - xn y0
        Vector((0.0, 1.0, 0.0)),    # tip 4 - x0 yp
        Vector((0.0, 0.0, -1.0))]   # tip 5 - Bottom

    tip_top = []
    tip_1 = []
    tip_2 = []
    tip_3 = []
    tip_4 = []
    tip_bot = []

    # Top edges
    va, vb = subdivide_edge_2_cuts(verts_oct[0], verts_oct[1], hs)
    va_idx, vb_idx = len(verts), len(verts) + 1
    verts.extend([va, vb])
    tip_top.append(va_idx)
    tip_1.append(vb_idx)
    va, vb = subdivide_edge_2_cuts(verts_oct[0], verts_oct[2], hs)
    va_idx, vb_idx = len(verts), len(verts) + 1
    verts.extend([va, vb])
    tip_top.append(va_idx)
    tip_2.append(vb_idx)
    va, vb = subdivide_edge_2_cuts(verts_oct[0], verts_oct[3], hs)
    va_idx, vb_idx = len(verts), len(verts) + 1
    verts.extend([va, vb])
    tip_top.append(va_idx)
    tip_3.append(vb_idx)
    va, vb = subdivide_edge_2_cuts(verts_oct[0], verts_oct[4], hs)
    va_idx, vb_idx = len(verts), len(verts) + 1
    verts.extend([va, vb])
    tip_top.append(va_idx)
    tip_4.append(vb_idx)

    # Circumference edges
    va, vb = subdivide_edge_2_cuts(verts_oct[1], verts_oct[2], hs)
    va_idx, vb_idx = len(verts), len(verts) + 1
    verts.extend([va, vb])
    tip_1.append(va_idx)
    tip_2.append(vb_idx)
    va, vb = subdivide_edge_2_cuts(verts_oct[2], verts_oct[3], hs)
    va_idx, vb_idx = len(verts), len(verts) + 1
    verts.extend([va, vb])
    tip_2.append(va_idx)
    tip_3.append(vb_idx)
    va, vb = subdivide_edge_2_cuts(verts_oct[3], verts_oct[4], hs)
    va_idx, vb_idx = len(verts), len(verts) + 1
    verts.extend([va, vb])
    tip_3.append(va_idx)
    tip_4.append(vb_idx)
    va, vb = subdivide_edge_2_cuts(verts_oct[4], verts_oct[1], hs)
    va_idx, vb_idx = len(verts), len(verts) + 1
    verts.extend([va, vb])
    tip_4.append(va_idx)
    tip_1.append(vb_idx)

    # Bottom edges
    va, vb = subdivide_edge_2_cuts(verts_oct[5], verts_oct[1], hs)
    va_idx, vb_idx = len(verts), len(verts) + 1
    verts.extend([va, vb])
    tip_bot.append(va_idx)
    tip_1.append(vb_idx)
    va, vb = subdivide_edge_2_cuts(verts_oct[5], verts_oct[2], hs)
    va_idx, vb_idx = len(verts), len(verts) + 1
    verts.extend([va, vb])
    tip_bot.append(va_idx)
    tip_2.append(vb_idx)
    va, vb = subdivide_edge_2_cuts(verts_oct[5], verts_oct[3], hs)
    va_idx, vb_idx = len(verts), len(verts) + 1
    verts.extend([va, vb])
    tip_bot.append(va_idx)
    tip_3.append(vb_idx)
    va, vb = subdivide_edge_2_cuts(verts_oct[5], verts_oct[4], hs)
    va_idx, vb_idx = len(verts), len(verts) + 1
    verts.extend([va, vb])
    tip_bot.append(va_idx)
    tip_4.append(vb_idx)

    # Hexagons
    ngon_12_zp = [tip_top[0], tip_top[1],
        tip_2[0], tip_2[1],
        tip_1[1], tip_1[0]]
    ngon_23_zp = [tip_top[1], tip_top[2],
        tip_3[0], tip_3[1],
        tip_2[2], tip_2[0]]
    ngon_34_zp = [tip_top[2], tip_top[3],
        tip_4[0], tip_4[1],
        tip_3[2], tip_3[0]]
    ngon_41_zp = [tip_top[3], tip_top[0],
        tip_1[0], tip_1[2],
        tip_4[2], tip_4[0]]

    ngon_12_zn = [tip_bot[0], tip_bot[1],
        tip_2[3], tip_2[1],
        tip_1[1], tip_1[3]]
    ngon_23_zn = [tip_bot[1], tip_bot[2],
        tip_3[3], tip_3[1],
        tip_2[2], tip_2[3]]
    ngon_34_zn = [tip_bot[2], tip_bot[3],
        tip_4[3], tip_4[1],
        tip_3[2], tip_3[3]]
    ngon_41_zn = [tip_bot[3], tip_bot[0],
        tip_1[3], tip_1[2],
        tip_4[2], tip_4[3]]

    # Fix vertex order (and fix normal at the same time)
    tip_1 = tip_1[:2] + list(reversed(tip_1[2:]))
    tip_2 = list(reversed(tip_2[:2])) + tip_2[2:]
    tip_3 = list(reversed(tip_3[:2])) + tip_3[2:]
    tip_4 = list(reversed(tip_4[:2])) + tip_4[2:]

    # Invert face normals
    tip_top = invert_face_normal(tip_top)
    ngon_12_zn = invert_face_normal(ngon_12_zn)
    ngon_23_zn = invert_face_normal(ngon_23_zn)
    ngon_34_zn = invert_face_normal(ngon_34_zn)
    ngon_41_zn = invert_face_normal(ngon_41_zn)

    # Tip quads
    faces.extend([tip_top, tip_bot])
    faces.extend([tip_1, tip_2, tip_3, tip_4])

    if star_ngons:
            ngons = [ngon_12_zp, ngon_23_zp, ngon_34_zp, ngon_41_zp,
                ngon_12_zn, ngon_23_zn, ngon_34_zn, ngon_41_zn]
            # Create stars from octagons.
            verts, faces_star = get_polygon_center(verts, ngons)
            faces.extend(faces_star)

    else:
        # Create quads from hexagons.
        ngons = [ngon_12_zp, ngon_23_zp, ngon_34_zp, ngon_41_zp]
        for ngon in ngons:
            # offset=2 Offset vertices so QUADS are created with
            # orthagonal edges. Superficial change - Could be omitted.
            hex_quads = ngon_fill(ngon, offset=2)
            faces.extend(hex_quads)

        ngons = [ngon_12_zn, ngon_23_zn, ngon_34_zn, ngon_41_zn]
        for ngon in ngons:
            # offset=1 Offset vertices so QUADS are created with
            # orthagonal edges. Superficial change - Could be omitted.
            hex_quads = ngon_fill(ngon, offset=1)
            faces.extend(hex_quads)

    return verts, faces


# http://en.wikipedia.org/wiki/Truncated_cuboctahedron
def add_truncated_cuboctahedron(
    octagon_size=2.0 - (2.0 / sqrt(2.0)) * (2.0 / (4.0 / sqrt(2.0) + 1.0)),
    octagon_side=2.0 / (4.0 / sqrt(2.0) + 1.0),
    star_ngons=False):

    size = 2.0

    if (octagon_side < 0.0
        or octagon_size < 0.0
        or octagon_size < octagon_side
        or octagon_size > size
        or octagon_side > size):
        return None, None

    verts = []
    faces = []
    
    oside = octagon_side

    # Vertices of a simple Cube
    verts_cube = [
        Vector((1.0, 1.0, 1.0)),     # tip 0
        Vector((1.0, -1.0, 1.0)),    # tip 1
        Vector((-1.0, -1.0, 1.0)),   # tip 2
        Vector((-1.0, 1.0, 1.0)),    # tip 3
        Vector((1.0, 1.0, -1.0)),    # tip 4
        Vector((1.0, -1.0, -1.0)),   # tip 5
        Vector((-1.0, -1.0, -1.0)),  # tip 6
        Vector((-1.0, 1.0, -1.0))]   # tip 7

    tri_xp_yp_zp = []
    tri_xp_yn_zp = []
    tri_xn_yp_zp = []
    tri_xn_yn_zp = []
    tri_xp_yp_zn = []
    tri_xp_yn_zn = []
    tri_xn_yp_zn = []
    tri_xn_yn_zn = []

    # Prepare top & bottom octagons.
    oct_top = []
    oct_bot = []
    hex_0_zp = []
    hex_1_zp = []
    hex_2_zp = []
    hex_3_zp = []
    hex_0_zn = []
    hex_1_zn = []
    hex_2_zn = []
    hex_3_zn = []

    bevel_size = (size - octagon_size) / 2.0

    # Top edges ####
    bevel_z = Vector((0.0, 0.0, -bevel_size))

    va, vb = subdivide_edge_2_cuts(verts_cube[0], verts_cube[1], oside)
    va1, vb1 = va + Vector((-bevel_size, 0, 0)), vb + Vector((-bevel_size, 0, 0))
    va2, vb2 = va + bevel_z, vb + bevel_z
    va1_idx, vb1_idx = len(verts), len(verts) + 1
    va2_idx, vb2_idx = len(verts) + 2, len(verts) + 3
    verts.extend([va1, vb1, va2, vb2])
    #tri_xp_yp_zp.append(va_idx)
    #tri_xp_yn_zp.append(vb_idx)
    oct_top.extend([va1_idx, vb1_idx])
    quad_01_zp = [va1_idx, vb1_idx, vb2_idx, va2_idx]
    hex_0_zp.extend([va2_idx, va1_idx])
    hex_1_zp.extend([vb2_idx, vb1_idx])

    va, vb = subdivide_edge_2_cuts(verts_cube[1], verts_cube[2], oside)
    va1, vb1 = va + Vector((0, bevel_size, 0)), vb + Vector((0, bevel_size, 0))
    va2, vb2 = va + bevel_z, vb + bevel_z
    va1_idx, vb1_idx = len(verts), len(verts) + 1
    va2_idx, vb2_idx = len(verts) + 2, len(verts) + 3
    verts.extend([va1, vb1, va2, vb2])
    #tri_xp_yn_zp.append(va_idx)
    #tri_xn_yn_zp.append(vb_idx)
    oct_top.extend([va1_idx, vb1_idx])
    quad_12_zp = [va1_idx, vb1_idx, vb2_idx, va2_idx]
    hex_1_zp.extend([va1_idx, va2_idx])
    hex_2_zp.extend([vb2_idx, vb1_idx])

    va, vb = subdivide_edge_2_cuts(verts_cube[2], verts_cube[3], oside)
    va1, vb1 = va + Vector((bevel_size, 0, 0)), vb + Vector((bevel_size, 0, 0))
    va2, vb2 = va + bevel_z, vb + bevel_z
    va1_idx, vb1_idx = len(verts), len(verts) + 1
    va2_idx, vb2_idx = len(verts) + 2, len(verts) + 3
    verts.extend([va1, vb1, va2, vb2])
    oct_top.extend([va1_idx, vb1_idx])
    quad_23_zp = [va1_idx, vb1_idx, vb2_idx, va2_idx]
    hex_2_zp.extend([va1_idx, va2_idx])
    hex_3_zp.extend([vb2_idx, vb1_idx])

    va, vb = subdivide_edge_2_cuts(verts_cube[3], verts_cube[0], oside)
    va1, vb1 = va + Vector((0, -bevel_size, 0)), vb + Vector((0, -bevel_size, 0))
    va2, vb2 = va + bevel_z, vb + bevel_z
    va1_idx, vb1_idx = len(verts), len(verts) + 1
    va2_idx, vb2_idx = len(verts) + 2, len(verts) + 3
    verts.extend([va1, vb1, va2, vb2])
    #tri_xn_yp_zp.append(va_idx)
    #tri_xp_yp_zp.append(vb_idx)
    oct_top.extend([va1_idx, vb1_idx])
    quad_30_zp = [va1_idx, vb1_idx, vb2_idx, va2_idx]
    hex_3_zp.extend([va1_idx, va2_idx])
    hex_0_zp.extend([vb1_idx, vb2_idx])

    # Top-down edges ####
    va, vb = subdivide_edge_2_cuts(verts_cube[0], verts_cube[4], oside)
    va1, vb1 = va + Vector((-bevel_size, 0, 0)), vb + Vector((-bevel_size, 0, 0))
    va2, vb2 = va + Vector((0, -bevel_size, 0)), vb + Vector((0, -bevel_size, 0))
    va1_idx, vb1_idx = len(verts), len(verts) + 1
    va2_idx, vb2_idx = len(verts) + 2, len(verts) + 3
    verts.extend([va1, vb1, va2, vb2])
    #tri_xp_yp_zp.append(va_idx)
    #tri_xp_yp_zn.append(vb_idx)
    top_down_0_1 = [va1_idx, vb1_idx]
    top_down_0_2 = [va2_idx, vb2_idx]
    quad_04 = [vb1_idx, va1_idx, va2_idx, vb2_idx]
    hex_0_zp.extend([va1_idx, va2_idx])
    hex_0_zn.extend([vb1_idx, vb2_idx])

    va, vb = subdivide_edge_2_cuts(verts_cube[1], verts_cube[5], oside)
    va1, vb1 = va + Vector((-bevel_size, 0, 0)), vb + Vector((-bevel_size, 0, 0))
    va2, vb2 = va + Vector((0, bevel_size, 0)), vb + Vector((0, bevel_size, 0))
    va1_idx, vb1_idx = len(verts), len(verts) + 1
    va2_idx, vb2_idx = len(verts) + 2, len(verts) + 3
    verts.extend([va1, vb1, va2, vb2])
    #tri_xp_yn_zp.append(va_idx)
    #tri_xp_yn_zn.append(vb_idx)
    top_down_1_1 = [va1_idx, vb1_idx]
    top_down_1_2 = [va2_idx, vb2_idx]
    quad_15 = [va1_idx, vb1_idx, vb2_idx, va2_idx]
    hex_1_zp.extend([va1_idx, va2_idx])
    hex_1_zn.extend([vb1_idx, vb2_idx])

    va, vb = subdivide_edge_2_cuts(verts_cube[2], verts_cube[6], oside)
    va1, vb1 = va + Vector((bevel_size, 0, 0)), vb + Vector((bevel_size, 0, 0))
    va2, vb2 = va + Vector((0, bevel_size, 0)), vb + Vector((0, bevel_size, 0))
    va1_idx, vb1_idx = len(verts), len(verts) + 1
    va2_idx, vb2_idx = len(verts) + 2, len(verts) + 3
    verts.extend([va1, vb1, va2, vb2])
    #tri_xn_yn_zp.append(va_idx)
    #tri_xn_yn_zn.append(vb_idx)
    top_down_2_1 = [va1_idx, vb1_idx]
    top_down_2_2 = [va2_idx, vb2_idx]
    quad_26 = [vb1_idx, va1_idx, va2_idx, vb2_idx]
    hex_2_zp.extend([va2_idx, va1_idx])
    hex_2_zn.extend([vb2_idx, vb1_idx])

    va, vb = subdivide_edge_2_cuts(verts_cube[3], verts_cube[7], oside)
    va1, vb1 = va + Vector((bevel_size, 0, 0)), vb + Vector((bevel_size, 0, 0))
    va2, vb2 = va + Vector((0, -bevel_size, 0)), vb + Vector((0, -bevel_size, 0))
    va1_idx, vb1_idx = len(verts), len(verts) + 1
    va2_idx, vb2_idx = len(verts) + 2, len(verts) + 3
    verts.extend([va1, vb1, va2, vb2])
    #tri_xn_yp_zp.append(va_idx)
    #tri_xn_yp_zn.append(vb_idx)
    top_down_3_1 = [va1_idx, vb1_idx]
    top_down_3_2 = [va2_idx, vb2_idx]
    quad_37 = [va1_idx, vb1_idx, vb2_idx, va2_idx]
    hex_3_zp.extend([va1_idx, va2_idx])
    hex_3_zn.extend([vb1_idx, vb2_idx])
    
    # Bottom edges ####
    bevel_z = Vector((0.0, 0.0, bevel_size))

    va, vb = subdivide_edge_2_cuts(verts_cube[4], verts_cube[5], oside)
    va1, vb1 = va + Vector((-bevel_size, 0, 0)), vb + Vector((-bevel_size, 0, 0))
    va2, vb2 = va + bevel_z, vb + bevel_z
    va1_idx, vb1_idx = len(verts), len(verts) + 1
    va2_idx, vb2_idx = len(verts) + 2, len(verts) + 3
    verts.extend([va1, vb1, va2, vb2])
    #tri_xp_yp_zn.append(va_idx)
    #tri_xp_yn_zn.append(vb_idx)
    oct_bot.extend([va1_idx, vb1_idx])
    quad_45_zn = [vb1_idx, va1_idx, va2_idx, vb2_idx]
    hex_0_zn.extend([va2_idx, va1_idx])
    hex_1_zn.extend([vb2_idx, vb1_idx])

    va, vb = subdivide_edge_2_cuts(verts_cube[5], verts_cube[6], oside)
    va1, vb1 = va + Vector((0, bevel_size, 0)), vb + Vector((0, bevel_size, 0))
    va2, vb2 = va + bevel_z, vb + bevel_z
    va1_idx, vb1_idx = len(verts), len(verts) + 1
    va2_idx, vb2_idx = len(verts) + 2, len(verts) + 3
    verts.extend([va1, vb1, va2, vb2])
    #tri_xp_yn_zn.append(va_idx)
    #tri_xn_yn_zn.append(vb_idx)
    oct_bot.extend([va1_idx, vb1_idx])
    quad_56_zn = [vb1_idx, va1_idx, va2_idx, vb2_idx]
    hex_1_zn.extend([va1_idx, va2_idx])
    hex_2_zn.extend([vb2_idx, vb1_idx])

    va, vb = subdivide_edge_2_cuts(verts_cube[6], verts_cube[7], oside)
    va1, vb1 = va + Vector((bevel_size, 0, 0)), vb + Vector((bevel_size, 0, 0))
    va2, vb2 = va + bevel_z, vb + bevel_z
    va1_idx, vb1_idx = len(verts), len(verts) + 1
    va2_idx, vb2_idx = len(verts) + 2, len(verts) + 3
    verts.extend([va1, vb1, va2, vb2])
    #tri_xn_yn_zn.append(va_idx)
    #tri_xn_yp_zn.append(vb_idx)
    oct_bot.extend([va1_idx, vb1_idx])
    quad_67_zn = [vb1_idx, va1_idx, va2_idx, vb2_idx]
    hex_2_zn.extend([va1_idx, va2_idx])
    hex_3_zn.extend([vb2_idx, vb1_idx])

    va, vb = subdivide_edge_2_cuts(verts_cube[7], verts_cube[4], oside)
    va1, vb1 = va + Vector((0, -bevel_size, 0)), vb + Vector((0, -bevel_size, 0))
    va2, vb2 = va + bevel_z, vb + bevel_z
    va1_idx, vb1_idx = len(verts), len(verts) + 1
    va2_idx, vb2_idx = len(verts) + 2, len(verts) + 3
    verts.extend([va1, vb1, va2, vb2])
    #tri_xn_yp_zn.append(va_idx)
    #tri_xp_yp_zn.append(vb_idx)
    oct_bot.extend([va1_idx, vb1_idx])
    quad_74_zn = [vb1_idx, va1_idx, va2_idx, vb2_idx]
    hex_3_zn.extend([va1_idx, va2_idx])
    hex_0_zn.extend([vb1_idx, vb2_idx])

    # Octagon polygons (n-gons)
    oct_0 = [
        top_down_0_2[1], top_down_0_2[0], quad_01_zp[3], quad_01_zp[2],
        top_down_1_2[0], top_down_1_2[1], quad_45_zn[3], quad_45_zn[2]]
    oct_1 = [
        top_down_1_1[1], top_down_1_1[0], quad_12_zp[3], quad_12_zp[2],
        top_down_2_1[0], top_down_2_1[1], quad_56_zn[3], quad_56_zn[2]]
    oct_2 = [
        top_down_2_2[1], top_down_2_2[0], quad_23_zp[3], quad_23_zp[2],
        top_down_3_2[0], top_down_3_2[1], quad_67_zn[3], quad_67_zn[2]]
    oct_3 = [
        top_down_3_1[1], top_down_3_1[0], quad_30_zp[3], quad_30_zp[2],
        top_down_0_1[0], top_down_0_1[1], quad_74_zn[3], quad_74_zn[2]]

    # Invert face normals where needed.
    oct_top = invert_face_normal(oct_top)
    hex_0_zp = invert_face_normal(hex_0_zp)
    hex_1_zn = invert_face_normal(hex_1_zn)
    hex_2_zn = invert_face_normal(hex_2_zn)
    hex_3_zn = invert_face_normal(hex_3_zn)

    # Quads
    faces.extend([quad_01_zp, quad_12_zp, quad_23_zp, quad_30_zp])
    faces.extend([quad_04, quad_15, quad_26, quad_37])
    faces.extend([quad_45_zn, quad_56_zn, quad_67_zn, quad_74_zn])

    if star_ngons:
        # Create stars from octagons.
        ngons = [oct_top, oct_bot, oct_bot, oct_0, oct_1, oct_2, oct_3]

        verts, faces_star = get_polygon_center(verts, ngons)
        faces.extend(faces_star)
        
        # Create stars from hexagons.
        # @todo

    else:
        # Create quads from octagons.

        # The top octagon is the only polygon we don't need to offset.
        oct_quads = ngon_fill(oct_top)
        faces.extend(oct_quads)

        ngons = [oct_bot, oct_0, oct_1, oct_2, oct_3]
        for ngon in ngons:
            # offset=1 Offset vertices so QUADS are created with
            # orthagonal edges. Superficial change - Could be omitted.
            oct_quads = ngon_fill(ngon, offset=1)
            faces.extend(oct_quads)
        
        # Create quads from hexagons.
        ngons = [hex_0_zp, hex_1_zp, hex_2_zp, hex_3_zp]
        for ngon in ngons:
            hex_quads = ngon_fill(ngon)
            faces.extend(hex_quads)

        hex_quads = ngon_fill(hex_0_zn, offset=2)
        faces.extend(hex_quads)

        ngons = [hex_1_zn, hex_2_zn, hex_3_zn]
        for ngon in ngons:
            hex_quads = ngon_fill(ngon, offset=1)
            faces.extend(hex_quads)

    return verts, faces

########################


class AddTruncatedTetrahedron(bpy.types.Operator):
    '''Add a mesh for a truncated tetrahedron.'''
    bl_idname = 'mesh.primitive_truncated_tetrahedron_add'
    bl_label = 'Add Truncated Tetrahedron'
    bl_description = 'Create a mesh for a truncated tetrahedron.'
    bl_options = {'REGISTER', 'UNDO'}

    # edit - Whether to add or update.
    edit = BoolProperty(name='',
        description='',
        default=False,
        options={'HIDDEN'})
    hexagon_side = FloatProperty(name='Hexagon Side',
        description='One length of the hexagon side' \
            ' (on the original tetrahedron edge).',
        min=0.01,
        max=2.0 * sqrt(2.0) - 0.01,
        default=2.0 * sqrt(2.0) / 3.0)
    star_ngons = BoolProperty(name='Star N-Gon',
        description='Create star-shaped hexagons.',
        default=False)

    def execute(self, context):
        props = self.properties

        verts, faces = add_truncated_tetrahedron(
            props.hexagon_side,
            props.star_ngons)

        if not verts:
            return {'CANCELLED'}

        obj = create_mesh_object(context, verts, [], faces,
            'TrTetrahedron', props.edit)

        # Store 'recall' properties in the object.
        recall_args_list = {
            'edit': True,
            'hexagon_side': props.hexagon_side,
            'star_ngons': props.star_ngons}
        store_recall_properties(obj, self, recall_args_list)

        return {'FINISHED'}


class AddCuboctahedron(bpy.types.Operator):
    '''Add a mesh for a cuboctahedron (truncated cube).'''
    bl_idname = 'mesh.primitive_cuboctahedron_add'
    bl_label = 'Add Cuboctahedron or Truncated Cube'
    bl_description = 'Create a mesh for a cuboctahedron (or truncated cube).'
    bl_options = {'REGISTER', 'UNDO'}

    # edit - Whether to add or update.
    edit = BoolProperty(name='',
        description='',
        default=False,
        options={'HIDDEN'})
    octagon_side = FloatProperty(name='Octagon Side',
        description='One length of the octagon side' \
            ' (on the original cube edge).' \
            ' 0: Cuboctahedron, >0: Truncated Cube',
        min=0.00,
        max=1.99,
        default=0.0)
    star_ngons = BoolProperty(name='Star N-Gon',
        description='Create star-shaped octagons.',
        default=False)

    def execute(self, context):
        props = self.properties

        verts, faces, name = add_cuboctahedron(
            props.octagon_side,
            props.star_ngons)

        if not verts:
            return {'CANCELLED'}

        obj = create_mesh_object(context, verts, [], faces, name, props.edit)

        # Store 'recall' properties in the object.
        recall_args_list = {
            'edit': True,
            'octagon_side': props.octagon_side,
            'star_ngons': props.star_ngons}
        store_recall_properties(obj, self, recall_args_list)

        return {'FINISHED'}


class AddRhombicuboctahedron(bpy.types.Operator):
    '''Add a mesh for a rhombicuboctahedron.'''
    bl_idname = 'mesh.primitive_rhombicuboctahedron_add'
    bl_label = 'Add Rhombicuboctahedron'
    bl_description = 'Create a mesh for a rhombicuboctahedron.'
    bl_options = {'REGISTER', 'UNDO'}

    # edit - Whether to add or update.
    edit = BoolProperty(name='',
        description='',
        default=False,
        options={'HIDDEN'})
    quad_size = FloatProperty(name="Quad Size",
        description="Size of the orthogonal quad faces.",
        min=0.01,
        max=1.99,
        default=sqrt(2.0) / (1.0 + sqrt(2) / 2.0))

    def execute(self, context):
        props = self.properties

        verts, faces = add_rhombicuboctahedron(props.quad_size)

        if not verts:
            return {'CANCELLED'}

        obj = create_mesh_object(context, verts, [], faces,
            'Rhombicuboctahedron', props.edit)

        # Store 'recall' properties in the object.
        recall_args_list = {
            'edit': True,
            'quad_size': props.quad_size}
        store_recall_properties(obj, self, recall_args_list)

        return {'FINISHED'}


class AddTruncatedOctahedron(bpy.types.Operator):
    '''Add a mesh for a truncated octahedron.'''
    bl_idname = 'mesh.primitive_truncated_octahedron_add'
    bl_label = 'Add Truncated Octahedron'
    bl_description = 'Create a mesh for a truncated octahedron.'
    bl_options = {'REGISTER', 'UNDO'}

    # edit - Whether to add or update.
    edit = BoolProperty(name='',
        description='',
        default=False,
        options={'HIDDEN'})
    hexagon_side = FloatProperty(name='Hexagon Side',
        description='One length of the hexagon side' \
            ' (on the original octahedron edge).',
        min=0.01,
        max=sqrt(2) - 0.1,
        default=sqrt(2) / 3.0)
    star_ngons = BoolProperty(name='Star N-Gon',
        description='Create star-shaped hexagons.',
        default=False)

    def execute(self, context):
        props = self.properties

        verts, faces = add_truncated_octahedron(
            props.hexagon_side,
            props.star_ngons)

        if not verts:
            return {'CANCELLED'}

        obj = create_mesh_object(context, verts, [], faces,
            'TrOctahedron', props.edit)

        # Store 'recall' properties in the object.
        recall_args_list = {
            'edit': True,
            'hexagon_side': props.hexagon_side,
            'star_ngons': props.star_ngons}
        store_recall_properties(obj, self, recall_args_list)

        return {'FINISHED'}


class AddTruncatedCuboctahedron(bpy.types.Operator):
    '''Add a mesh for a truncated cuboctahedron.'''
    bl_idname = 'mesh.primitive_truncated_cuboctahedron_add'
    bl_label = 'Add Truncated Cuboctahedron'
    bl_description = 'Create a mesh for a truncated cuboctahedron.'
    bl_options = {'REGISTER', 'UNDO'}

    # edit - Whether to add or update.
    edit = BoolProperty(name='',
        description='',
        default=False,
        options={'HIDDEN'})
    octagon_size = FloatProperty(name='Octagon Size',
        description='The size (height/width) of the octagon.',
        min=0.02,
        max=1.99,
        default=2.0 - (2.0 / sqrt(2.0)) * (2.0 / (4.0 / sqrt(2.0) + 1.0)))
    octagon_side = FloatProperty(name='Octagon Side',
        description='One length of the octagon side' \
            ' (on the original cube edge).',
        min=0.01,
        max=1.98,
        default=2.0 / (4.0 / sqrt(2.0) + 1.0))
    star_ngons = BoolProperty(name='Star N-Gon',
        description='Create star-shaped octagons.',
        default=False)

    def execute(self, context):
        props = self.properties

        verts, faces = add_truncated_cuboctahedron(
            props.octagon_size,
            props.octagon_side,
            props.star_ngons)

        if not verts:
            return {'CANCELLED'}

        obj = create_mesh_object(context, verts, [], faces,
            'TrCuboctahedron', props.edit)

        # Store 'recall' properties in the object.
        recall_args_list = {
            'edit': True,
            'octagon_size': props.octagon_size,
            'octagon_side': props.octagon_side,
            'star_ngons': props.star_ngons}
        store_recall_properties(obj, self, recall_args_list)

        return {'FINISHED'}


class INFO_MT_mesh_archimedean_solids_add(bpy.types.Menu):
    # Define the "Archimedean Solids" menu
    bl_idname = "INFO_MT_mesh_archimedean_solids_add"
    bl_label = "Archimedean Solids"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("mesh.primitive_truncated_tetrahedron_add",
            text="Truncated Tetrahedron")
        layout.operator("mesh.primitive_cuboctahedron_add",
            text="Cuboctahedron or Truncated Cube")
        layout.operator("mesh.primitive_rhombicuboctahedron_add",
            text="Rhombicuboctahedron")
        layout.operator("mesh.primitive_truncated_octahedron_add",
            text="Truncated Octahedron")
        layout.operator("mesh.primitive_truncated_cuboctahedron_add",
            text="Truncated Cuboctahedron")

########################
import space_info

# Define "Archimedean Solids" menu
menu_func = (lambda self, context: self.layout.menu(
    "INFO_MT_mesh_archimedean_solids_add", icon="PLUGIN"))


def register():
    # Register the operators/menus.
    bpy.types.register(AddTruncatedTetrahedron)
    bpy.types.register(AddCuboctahedron)
    bpy.types.register(AddRhombicuboctahedron)
    bpy.types.register(AddTruncatedOctahedron)
    bpy.types.register(AddTruncatedCuboctahedron)
    bpy.types.register(INFO_MT_mesh_archimedean_solids_add)

    # Add "Archimedean Solids" menu to the "Add Mesh" menu
    space_info.INFO_MT_mesh_add.append(menu_func)


def unregister():
    # Unregister the operators/menus.
    bpy.types.unregister(AddTruncatedTetrahedron)
    bpy.types.unregister(AddCuboctahedron)
    bpy.types.unregister(AddRhombicuboctahedron)
    bpy.types.unregister(AddTruncatedOctahedron)
    bpy.types.unregister(AddTruncatedCuboctahedron)
    bpy.types.unregister(INFO_MT_mesh_archimedean_solids_add)

    # Remove "Archimedean Solids" menu from the "Add Mesh" menu.
    space_info.INFO_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
    register()
