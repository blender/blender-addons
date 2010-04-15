# add_mesh_diamond.py Copyright (C) 2008-2009, FourMadMen.com
#
# add diamond to the blender 2.50 add->mesh menu
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****

import bpy
from mathutils import Vector, Quaternion
from math import *
from bpy.props import *

bl_addon_info = {
    'name': 'Add Mesh: Diamond',
    'author': 'fourmadmen',
    'version': '2.1',
    'blender': (2, 5, 3),
    'location': 'View3D > Add > Mesh ',
    'description': 'Adds a mesh Diamond to the Add Mesh menu',
    'url': 'http://wiki.blender.org/index.php/Extensions:2.5/Py/' \
        'Scripts/Add_Mesh/Add_Diamond',
    'category': 'Add Mesh'}


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


def add_diamond(segments, girdle_radius, table_radius,
    crown_height, pavillion_height):

    PI_2 = pi * 2.0
    z_axis = (0.0, 0.0, -1.0)

    verts = []
    faces = []

    height = crown_height + pavillion_height
    half_height = height * 0.5

    # Vertex counter
    vert_cnt = 0

    # Tip
    verts.append((0.0, 0.0, -half_height))
    vert_tip = vert_cnt
    vert_cnt += 1

    # Middle vertex of the flat side
    verts.append((0.0, 0.0, half_height))
    vert_flat = vert_cnt
    vert_cnt += 1

    vert1_prev = None
    vert2_prev = None
    for index in range(segments):
        quat = Quaternion(z_axis, (index / segments) * PI_2)

        angle = PI_2 * index / segments

        vec = Vector(table_radius, 0.0, -half_height) * quat
        verts.append((vec.x, vec.y, vec.z))
        vert1 = vert_cnt
        vert_cnt += 1

        vec = Vector(girdle_radius, 0.0, half_height - pavillion_height) * quat
        verts.append((vec.x, vec.y, vec.z))
        vert2 = vert_cnt
        vert_cnt += 1

        if index == 0:
            # Remember vertex indices for next iteration.
            vert1_first = vert1
            vert2_first = vert2

        else:
            # Tip face
            faces.append([vert_tip, vert1_prev, vert1])
            # Side face
            faces.append([vert2, vert1, vert1_prev, vert2_prev])
            # Flat face
            faces.append([vert_flat, vert2, vert2_prev])

        vert1_prev = vert1
        vert2_prev = vert2

    # Create the last faces between first+last vertices
    # Tip face
    faces.append([vert_tip, vert1, vert1_first])
    # Side face
    faces.append([vert2_first, vert1_first, vert1, vert2])
    # Flat face
    faces.append([vert_flat, vert2_first, vert2])

    return verts, faces


class AddDiamond(bpy.types.Operator):
    '''Add a diamond mesh.'''
    bl_idname = "mesh.diamond_add"
    bl_label = "Add Diamond"
    bl_options = {'REGISTER', 'UNDO'}

    # edit - Whether to add or update.
    edit = BoolProperty(name="",
        description="",
        default=False,
        options={'HIDDEN'})
    segments = IntProperty(name="Segments",
        description="Number of segments for the diamond",
        default=32, min=3, max=256)
    girdle_radius = FloatProperty(name="Girdle Radius",
        description="Girdle radius of the diamond",
        default=1.0, min=0.01, max=100.0)
    table_radius = FloatProperty(name="Table Radius",
        description="Girdle radius of the diamond",
        default=0.8, min=0.01, max=100.0)
    crown_height = FloatProperty(name="Crown Height",
        description="Crown height of the diamond",
        default=0.25, min=0.01, max=100.0)
    pavillion_height = FloatProperty(name="Pavillion Height",
        description="pavillion height of the diamond",
        default=1.0, min=0.01, max=100.0)

    def execute(self, context):
        props = self.properties
        verts, faces = add_diamond(props.segments,
            props.girdle_radius,
            props.table_radius,
            props.crown_height,
            props.pavillion_height)

        obj = create_mesh_object(context, verts, [], faces,
            "Diamond", props.edit)

         # Store 'recall' properties in the object.
        recall_args_list = {
            "edit": True,
            "segments": props.segments,
            "girdle_radius": props.girdle_radius,
            "table_radius": props.table_radius,
            "crown_height": props.crown_height,
            "pavillion_height": props.pavillion_height}
        store_recall_properties(obj, self, recall_args_list)

        return {'FINISHED'}


# Register the operator
menu_func = (lambda self, context: self.layout.operator(AddDiamond.bl_idname,
                                        text="Diamond", icon='PLUGIN'))


def register():
    bpy.types.register(AddDiamond)

    # Add "Diamond" entry to the "Add Mesh" menu.
    bpy.types.INFO_MT_mesh_add.append(menu_func)


def unregister():
    bpy.types.unregister(AddDiamond)

    # Remove "Diamond" entry from the "Add Mesh" menu.
    bpy.types.INFO_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
    register()
