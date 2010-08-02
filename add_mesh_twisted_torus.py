# add_mesh_twisted_torus.py Copyright (C) 2009-2010, Paulo Gomes
# tuga3d {at} gmail {dot} com
# add twisted torus to the blender 2.50 add->mesh menu
# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****

bl_addon_info = {
    "name": "Add Mesh: Twisted Torus",
    "author": "Paulo_Gomes",
    "version": "0.11",
    "blender": (2, 5, 3),
    "location": "View3D > Add > Mesh ",
    "description": "Adds a mesh Twisted Torus to the Add Mesh menu",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/Add_Mesh/Add_Twisted_Torus",
    "tracker_url": "https://projects.blender.org/tracker/index.php?func=detail&aid=21622&group_id=153&atid=469",
    "category": "Add Mesh"}

"""
Usage:

* Launch from Add Mesh menu

* Modify parameters as desired or keep defaults
"""


import bpy
from bpy.props import *

import mathutils
from mathutils import *
from math import cos, sin, pi

# calculates the matrix for the new object
# depending on user pref
def align_matrix(context):
    loc = TranslationMatrix(context.scene.cursor_location)
    obj_align = context.user_preferences.edit.object_align
    if (context.space_data.type == 'VIEW_3D'
        and obj_align == 'VIEW'):
        rot = context.space_data.region_3d.view_matrix.rotation_part().invert().resize4x4()
    else:
        rot = Matrix()
    align_matrix = loc * rot
    return align_matrix


# Create a new mesh (object) from verts/edges/faces.
# verts/edges/faces ... List of vertices/edges/faces for the
#                       new mesh (as used in from_pydata).
# name ... Name of the new mesh (& object).
# edit ... Replace existing mesh data.
# Note: Using "edit" will destroy/delete existing mesh data.
def create_mesh_object(context, verts, edges, faces, name, edit, align_matrix):
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
        ob_new.select = True

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
        ob_new.select = True

        # Place the object at the 3D cursor location.
        # apply viewRotaion
        ob_new.matrix_world = align_matrix

    if obj_act and obj_act.mode == 'EDIT':
        if not edit:
            # We are in EditMode, switch to ObjectMode.
            bpy.ops.object.mode_set(mode='OBJECT')

            # Select the active object as well.
            obj_act.select = True

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


def add_twisted_torus(major_rad, minor_rad, major_seg, minor_seg, twists):
    PI_2 = pi * 2.0
    z_axis = (0.0, 0.0, 1.0)

    verts = []
    faces = []

    edgeloop_prev = []
    for major_index in range(major_seg):
        quat = Quaternion(z_axis, (major_index / major_seg) * PI_2)
        rot_twists = PI_2 * major_index / major_seg * twists

        edgeloop = []

        # Create section ring
        for minor_index in range(minor_seg):
            angle = (PI_2 * minor_index / minor_seg) + rot_twists

            vec = Vector((
                major_rad + (cos(angle) * minor_rad),
                0.0,
                sin(angle) * minor_rad))
            vec = vec * quat

            edgeloop.append(len(verts))
            verts.append(vec)

        # Remember very first edgeloop.
        if major_index == 0:
            edgeloop_first = edgeloop

        # Bridge last with current ring
        if edgeloop_prev:
            f = createFaces(edgeloop_prev, edgeloop, closed=True)
            faces.extend(f)

        edgeloop_prev = edgeloop

    # Bridge first and last ring
    f = createFaces(edgeloop_prev, edgeloop_first, closed=True)
    faces.extend(f)

    return verts, faces


class AddTwistedTorus(bpy.types.Operator):
    '''Add a torus mesh'''
    bl_idname = "mesh.primitive_twisted_torus_add"
    bl_label = "Add Torus"
    bl_options = {'REGISTER', 'UNDO'}

    # edit - Whether to add or update.
    edit = BoolProperty(name="",
        description="",
        default=False,
        options={'HIDDEN'})
    major_radius = FloatProperty(name="Major Radius",
        description="Radius from the origin to the" \
            " center of the cross section",
        min=0.01,
        max=100.0,
        default=1.0)
    minor_radius = FloatProperty(name="Minor Radius",
        description="Radius of the torus' cross section",
        min=0.01,
        max=100.0,
        default=0.25)
    major_segments = IntProperty(name="Major Segments",
        description="Number of segments for the main ring of the torus",
        min=3,
        max=256,
        default=48)
    minor_segments = IntProperty(name="Minor Segments",
        description="Number of segments for the minor ring of the torus",
        min=3,
        max=256,
        default=12)
    twists = IntProperty(name="Twists",
        description="Number of twists of the torus",
        min=0,
        max=256,
        default=1)

    use_abso = BoolProperty(name="Use Int+Ext Controls",
        description="Use the Int / Ext controls for torus dimensions",
        default=False)
    abso_major_rad = FloatProperty(name="Exterior Radius",
        description="Total Exterior Radius of the torus",
        min=0.01,
        max=100.0,
        default=1.0)
    abso_minor_rad = FloatProperty(name="Inside Radius",
        description="Total Interior Radius of the torus",
        min=0.01,
        max=100.0,
        default=0.5)
    align_matrix = Matrix()

    def execute(self, context):
        props = self.properties

        if props.use_abso == True:
            extra_helper = (props.abso_major_rad - props.abso_minor_rad) * 0.5
            props.major_radius = props.abso_minor_rad + extra_helper
            props.minor_radius = extra_helper

        verts, faces = add_twisted_torus(
            props.major_radius,
            props.minor_radius,
            props.major_segments,
            props.minor_segments,
            props.twists)

        # Actually create the mesh object from this geometry data.
        obj = create_mesh_object(context, verts, [], faces, "TwistedTorus",
            props.edit, self.align_matrix)

        return {'FINISHED'}

    def invoke(self, context, event):
        self.align_matrix = align_matrix(context)
        self.execute(context)
        return {'FINISHED'}

# Add to the menu
def menu_func(self, context):
    self.layout.operator(AddTwistedTorus.bl_idname, text="Twisted Torus", icon='MESH_DONUT')


def register():
    bpy.types.INFO_MT_mesh_add.append(menu_func)


def unregister():
    bpy.types.INFO_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
    register()
