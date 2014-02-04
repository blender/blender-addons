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
'''
bl_info = {
    "name": "Gemstones",
    "author": "Pontiac, Fourmadmen, Dreampainter",
    "version": (0, 4),
    "blender": (2, 57, 0),
    "location": "View3D > Add > Mesh > Gemstones",
    "description": "Adds various gemstone (Diamond & Gem) meshes.",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"
        "Scripts/Add_Mesh/Add_Gemstones",
    "tracker_url": "https://developer.blender.org/T21432",
    "category": "Add Mesh"}
'''
import bpy
from mathutils import *
from math import *
from bpy.props import *

# Create a new mesh (object) from verts/edges/faces.
# verts/edges/faces ... List of vertices/edges/faces for the
#                       new mesh (as used in from_pydata).
# name ... Name of the new mesh (& object).
def create_mesh_object(context, verts, edges, faces, name):

    # Create new mesh
    mesh = bpy.data.meshes.new(name)

    # Make a mesh from a list of verts/edges/faces.
    mesh.from_pydata(verts, edges, faces)

    # Update mesh geometry after adding stuff.
    mesh.update()

    from bpy_extras import object_utils
    return object_utils.object_data_add(context, mesh, operator=None)


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


# @todo Clean up vertex&face creation process a bit.
def add_gem(r1, r2, seg, h1, h2):
    """
    r1 = pavilion radius
    r2 = crown radius
    seg = number of segments
    h1 = pavilion height
    h2 = crown height
    Generates the vertices and faces of the gem
    """

    verts = []

    a = 2.0 * pi / seg             # Angle between segments
    offset = a / 2.0               # Middle between segments

    r3 = ((r1 + r2) / 2.0) / cos(offset)  # Middle of crown
    r4 = (r1 / 2.0) / cos(offset)  # Middle of pavilion
    h3 = h2 / 2.0                  # Middle of crown height
    h4 = -h1 / 2.0                 # Middle of pavilion height

    # Tip
    vert_tip = len(verts)
    verts.append(Vector((0.0, 0.0, -h1)))

    # Middle vertex of the flat side (crown)
    vert_flat = len(verts)
    verts.append(Vector((0.0, 0.0, h2)))

    edgeloop_flat = []
    for i in range(seg):
        s1 = sin(i * a)
        s2 = sin(offset + i * a)
        c1 = cos(i * a)
        c2 = cos(offset + i * a)

        verts.append((r4 * s1, r4 * c1, h4))    # Middle of pavilion
        verts.append((r1 * s2, r1 * c2, 0.0))   # Pavilion
        verts.append((r3 * s1, r3 * c1, h3))    # Middle crown
        edgeloop_flat.append(len(verts))
        verts.append((r2 * s2, r2 * c2, h2))    # Crown

    faces = []

    for index in range(seg):
        i = index * 4
        j = ((index + 1) % seg) * 4

        faces.append([j + 2, vert_tip, i + 2, i + 3])  # Tip -> Middle of pav
        faces.append([j + 2, i + 3, j + 3])            # Middle of pav -> pav
        faces.append([j + 3, i + 3, j + 4])            # Pav -> Middle crown
        faces.append([j + 4, i + 3, i + 4, i + 5])     # Crown quads
        faces.append([j + 4, i + 5, j + 5])            # Middle crown -> crown

    faces_flat = createFaces([vert_flat], edgeloop_flat, closed=True)
    faces.extend(faces_flat)

    return verts, faces


def add_diamond(segments, girdle_radius, table_radius,
    crown_height, pavilion_height):

    PI_2 = pi * 2.0
    z_axis = (0.0, 0.0, -1.0)

    verts = []
    faces = []

    height_flat = crown_height
    height_middle = 0.0
    height_tip = -pavilion_height

    # Middle vertex of the flat side (crown)
    vert_flat = len(verts)
    verts.append(Vector((0.0, 0.0, height_flat)))

    # Tip
    vert_tip = len(verts)
    verts.append(Vector((0.0, 0.0, height_tip)))

    verts_flat = []
    verts_girdle = []

    for index in range(segments):
        quat = Quaternion(z_axis, (index / segments) * PI_2)

        # angle = PI_2 * index / segments  # UNUSED

        # Row for flat side
        verts_flat.append(len(verts))
        vec = quat * Vector((table_radius, 0.0, height_flat))
        verts.append(vec)

        # Row for the middle/girdle
        verts_girdle.append(len(verts))
        vec = quat * Vector((girdle_radius, 0.0, height_middle))
        verts.append(vec)

    # Flat face
    faces_flat = createFaces([vert_flat], verts_flat, closed=True,
        flipped=True)
    # Side face
    faces_side = createFaces(verts_girdle, verts_flat, closed=True)
    # Tip faces
    faces_tip = createFaces([vert_tip], verts_girdle, closed=True)

    faces.extend(faces_tip)
    faces.extend(faces_side)
    faces.extend(faces_flat)

    return verts, faces


class AddDiamond(bpy.types.Operator):
    """Add a diamond mesh"""
    bl_idname = "mesh.primitive_diamond_add"
    bl_label = "Add Diamond"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    segments = IntProperty(name="Segments",
        description="Number of segments for the diamond",
        min=3,
        max=256,
        default=32)
    girdle_radius = FloatProperty(name="Girdle Radius",
        description="Girdle radius of the diamond",
        min=0.01,
        max=9999.0,
        default=1.0)
    table_radius = FloatProperty(name="Table Radius",
        description="Girdle radius of the diamond",
        min=0.01,
        max=9999.0,
        default=0.6)
    crown_height = FloatProperty(name="Crown Height",
        description="Crown height of the diamond",
        min=0.01,
        max=9999.0,
        default=0.35)
    pavilion_height = FloatProperty(name="Pavilion Height",
        description="Pavilion height of the diamond",
        min=0.01,
        max=9999.0,
        default=0.8)

    def execute(self, context):
        verts, faces = add_diamond(self.segments,
            self.girdle_radius,
            self.table_radius,
            self.crown_height,
            self.pavilion_height)

        obj = create_mesh_object(context, verts, [], faces, "Diamond")

        return {'FINISHED'}


class AddGem(bpy.types.Operator):
    """Add a diamond gem"""
    bl_idname = "mesh.primitive_gem_add"
    bl_label = "Add Gem"
    bl_description = "Create an offset faceted gem"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    segments = IntProperty(name="Segments",
        description="Longitudial segmentation",
        min=3,
        max=265,
        default=8,)
    pavilion_radius = FloatProperty(name="Radius",
       description="Radius of the gem",
       min=0.01,
       max=9999.0,
       default=1.0)
    crown_radius = FloatProperty(name="Table Radius",
       description="Radius of the table(top)",
       min=0.01,
       max=9999.0,
       default=0.6)
    crown_height = FloatProperty(name="Table height",
       description="Height of the top half",
       min=0.01,
       max=9999.0,
       default=0.35)
    pavilion_height = FloatProperty(name="Pavilion height",
       description="Height of bottom half",
       min=0.01,
       max=9999.0,
       default=0.8)

    def execute(self, context):

        # create mesh
        verts, faces = add_gem(
            self.pavilion_radius,
            self.crown_radius,
            self.segments,
            self.pavilion_height,
            self.crown_height)

        obj = create_mesh_object(context, verts, [], faces, "Gem")

        return {'FINISHED'}
