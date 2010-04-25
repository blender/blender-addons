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


def add_rhombicuboctahedron(quad_size=sqrt(2.0) / (1.0 + sqrt(2) / 2.0)):
    faces = []
    verts = []

    size = 2.0

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
    faces[face_top_idx] = [f[0]] + list(reversed(f[1:]))

    return verts, faces


# Returns the middle location of a _regular_ polygon.
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


def subdivide_edge_2_cuts(v1, v2, edgelength_middle):
    v1 = Vector(v1)
    v2 = Vector(v2)

    length = (v2 - v1).length
    vn = (v2 - v1).normalize()

    edgelength_1a_b2 = (length - edgelength_middle) / 2.0

    va = v1 + vn * edgelength_1a_b2
    vb = v1 + vn * (edgelength_1a_b2 + edgelength_middle)

    return (va, vb)


def add_truncated_tetrahedron(hexagon_side=2.0 * sqrt(2.0) / 3.0,
    star_ngons=False):
    verts = []
    faces = []

    # Vertices of a simple Tetrahedron
    verts_tet = [
        (1.0, 1.0, -1.0),    # tip 0
        (-1.0, 1.0, 1.0),    # tip 1
        (1.0, -1.0, 1.0),    # tip 2
        (-1.0, -1.0, -1.0)]  # tip 3

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
        (quad1, quad2) = (
            [ngon012[0], ngon012[1], ngon012[2], ngon012[3]],
            [ngon012[0], ngon012[3], ngon012[4], ngon012[5]])
        faces.extend([quad1, quad2])
        (quad1, quad2) = (
            [ngon031[0], ngon031[1], ngon031[2], ngon031[3]],
            [ngon031[0], ngon031[3], ngon031[4], ngon031[5]])
        faces.extend([quad1, quad2])
        (quad1, quad2) = (
            [ngon023[0], ngon023[1], ngon023[2], ngon023[3]],
            [ngon023[0], ngon023[3], ngon023[4], ngon023[5]])
        faces.extend([quad1, quad2])
        (quad1, quad2) = (
            [ngon132[0], ngon132[1], ngon132[2], ngon132[3]],
            [ngon132[0], ngon132[3], ngon132[4], ngon132[5]])
        faces.extend([quad1, quad2])

    # Invert face normals
    tri1 = [tri1[0]] + list(reversed(tri1[1:]))
    tri3 = [tri3[0]] + list(reversed(tri3[1:]))

    # Tri faces
    faces.extend([tri0, tri1, tri2, tri3])

    return verts, faces


class AddRhombicuboctahedron(bpy.types.Operator):
    '''Add a mesh for a thombicuboctahedron.'''
    bl_idname = 'mesh.primitive_thombicuboctahedron_add'
    bl_label = 'Add Rhombicuboctahedron'
    bl_description = 'Create a mesh for a thombicuboctahedron.'
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

        obj = create_mesh_object(context, verts, [], faces,
            'Rhombicuboctahedron', props.edit)

        # Store 'recall' properties in the object.
        recall_args_list = {
            'edit': True,
            'quad_size': props.quad_size}
        store_recall_properties(obj, self, recall_args_list)

        return {'FINISHED'}


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

        obj = create_mesh_object(context, verts, [], faces,
            'TrTetrahedron', props.edit)

        # Store 'recall' properties in the object.
        recall_args_list = {
            'edit': True,
            'hexagon_side': props.hexagon_side,
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
        layout.operator("mesh.primitive_thombicuboctahedron_add",
            text="Rhombicuboctahedron")

import space_info

# Define "Archimedean Solids" menu
menu_func = (lambda self, context: self.layout.menu(
    "INFO_MT_mesh_archimedean_solids_add", icon="PLUGIN"))


def register():
    # Register the operators/menus.
    bpy.types.register(AddRhombicuboctahedron)
    bpy.types.register(AddTruncatedTetrahedron)
    bpy.types.register(INFO_MT_mesh_archimedean_solids_add)

    # Add "Archimedean Solids" menu to the "Add Mesh" menu
    space_info.INFO_MT_mesh_add.append(menu_func)


def unregister():
    # Unregister the operators/menus.
    bpy.types.unregister(AddRhombicuboctahedron)
    bpy.types.unregister(AddTruncatedTetrahedron)
    bpy.types.unregister(INFO_MT_mesh_archimedean_solids_add)

    # Remove "Archimedean Solids" menu from the "Add Mesh" menu.
    space_info.INFO_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
    register()
