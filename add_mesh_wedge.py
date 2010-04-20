# add_mesh_wedge.py Copyright (C) 2008-2009, FourMadMen.com
#
# add wedge to the blender 2.50 add->mesh menu
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
    'name': 'Add Mesh: Wedge',
    'author': 'fourmadmen',
    'version': '1.2',
    'blender': (2, 5, 3),
    'location': 'View3D > Add > Mesh ',
    'description': 'Adds a mesh Wedge to the Add Mesh menu',
    'url': 'http://wiki.blender.org/index.php/Extensions:2.5/Py/' \
        'Scripts/Add_Wedge',
    'category': 'Add Mesh'}


"""
Name: 'Wedge'
Blender: 250
Group: 'AddMesh'
Tip: 'Add Wedge Object...'
__author__ = ["Four Mad Men", "FourMadMen.com"]
__version__ = '0.10'
__url__ = [""]
email__=["bwiki {at} fourmadmen {dot} com"]

Usage:

* Launch from Add Mesh menu

* Modify parameters as desired or keep defaults

"""


import bpy
from bpy.props import *
from mathutils import *


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


# @todo Align wedge aling axis?
def add_wedge(size_x, size_y, size_z):
    verts = []
    faces = []

    size_x /= 2.0
    size_y /= 2.0
    size_z /= 2.0

    vIdx_top = []
    vIdx_bot = []

    vIdx_top.append(len(verts))
    verts.append(Vector(-size_x, -size_y, size_z))
    vIdx_bot.append(len(verts))
    verts.append(Vector(-size_x, -size_y, -size_z))

    vIdx_top.append(len(verts))
    verts.append(Vector(size_x, -size_y, size_z))
    vIdx_bot.append(len(verts))
    verts.append(Vector(size_x, -size_y, -size_z))

    vIdx_top.append(len(verts))
    verts.append(Vector(-size_x, size_y, size_z))
    vIdx_bot.append(len(verts))
    verts.append(Vector(-size_x, size_y, -size_z))

    faces.append(vIdx_top)
    faces.append(vIdx_bot)
    faces_outside = createFaces(vIdx_top, vIdx_bot, closed=True)
    faces.extend(faces_outside)

    return verts, faces


class AddWedge(bpy.types.Operator):
    '''Add a wedge mesh.'''
    bl_idname = "mesh.primitive_wedge_add"
    bl_label = "Add Wedge"
    bl_options = {'REGISTER', 'UNDO'}

    # edit - Whether to add or update.
    edit = BoolProperty(name="",
        description="",
        default=False,
        options={'HIDDEN'})
    size_x = FloatProperty(name="Size X",
        description="Size along the X axis",
        min=0.01,
        max=9999.0,
        default=2.0)
    size_y = FloatProperty(name="Size Y",
        description="Size along the Y axis",
        min=0.01,
        max=9999.0,
        default=2.0)
    size_z = FloatProperty(name="Size Z",
        description="Size along the Z axis",
        min=0.01,
        max=9999.0,
        default=2.00)

    def execute(self, context):
        props = self.properties

        verts, faces = add_wedge(
            props.size_x,
            props.size_y,
            props.size_z)

        obj = create_mesh_object(context, verts, [], faces, "Wedge",
            props.edit)

        # Store 'recall' properties in the object.
        recall_args_list = {
            "edit": True,
            "size_x": props.size_x,
            "size_y": props.size_y,
            "size_z": props.size_z}
        store_recall_properties(obj, self, recall_args_list)

        return {'FINISHED'}


# Register the operator
menu_func = (lambda self, context: self.layout.operator(AddWedge.bl_idname,
    text="Add Wedge", icon='PLUGIN'))


def register():
    bpy.types.register(AddWedge)

    # Add "Wedge" menu to the "Add Mesh" menu.
    bpy.types.INFO_MT_mesh_add.append(menu_func)


def unregister():
    bpy.types.unregister(AddWedge)

    # Remove "Wedge" menu from the "Add Mesh" menu.
    bpy.types.INFO_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
    register()
