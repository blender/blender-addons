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
########################################################
#
# Before changing this file please discuss with admins.
#
########################################################
# <pep8 compliant>

import bpy
import mathutils
from bpy.props import FloatVectorProperty


class AddObjectHelper:
    '''Helper Class for Add Object Operators'''
    location = FloatVectorProperty(name='Location', description='Location of new Object')
    rotation = FloatVectorProperty(name='Rotation', description='Rotation of new Object')


#Initialize loc, rot of operator
def add_object_align_init(context, operator):
    '''Initialize loc, rot of operator
    context: Blender Context
    operator: the active Operator (self)
    Initializes the Operators location and rotation variables
    according to user preferences (align to view)
    See AddObjectHelper class
    Returns Matrix
    '''
    if (operator
        and operator.properties.is_property_set("location")
        and operator.properties.is_property_set("rotation")):
        location = mathutils.Matrix.Translation(mathutils.Vector(operator.properties.location))
        rotation = mathutils.Euler(operator.properties.rotation).to_matrix().to_4x4()
    else:
        # TODO, local view cursor!
        location = mathutils.Matrix.Translation(context.scene.cursor_location)

        if context.user_preferences.edit.object_align == 'VIEW' and context.space_data.type == 'VIEW_3D':
            rotation = context.space_data.region_3d.view_matrix.to_3x3().inverted().to_4x4()
        else:
            rotation = mathutils.Matrix()

        # set the operator properties
        if operator:
            operator.properties.location = location.to_translation()
            operator.properties.rotation = rotation.to_euler()

    return location * rotation


def add_object_data(context, obdata, operator=None):
    '''Create Object from data

    context: Blender Context
    obdata: Object data (mesh, curve, camera,...)
    operator: the active operator (self)

    Returns the Object
    '''

    scene = context.scene

    # ugh, could be made nicer
    for ob in scene.objects:
        ob.select = False

    obj_new = bpy.data.objects.new(obdata.name, obdata)
    obj_new.update_tag()

    base = scene.objects.link(obj_new)
    base.select = True

    if context.space_data and context.space_data.type == 'VIEW_3D':
        base.layers_from_view(context.space_data)

    obj_new.matrix_world = add_object_align_init(context, operator)

    obj_act = scene.objects.active

    if obj_act and obj_act.mode == 'EDIT' and obj_act.type == obj_new.type:
        bpy.ops.object.mode_set(mode='OBJECT')

        obj_act.select = True
        scene.update()  # apply location
        #scene.objects.active = obj_new

        bpy.ops.object.join()  # join into the active.

        bpy.ops.object.mode_set(mode='EDIT')
    else:
        scene.objects.active = obj_new
        if context.user_preferences.edit.use_enter_edit_mode:
            bpy.ops.object.mode_set(mode='EDIT')

    return base


def flatten_vector_list(list):
    '''flatten a list of vetcors to use in foreach_set and the like'''
    if not list:
        return None

    result = []
    for vec in list:
        result.extend([i for i in vec])

    return result


def list_to_vector_list(list, dimension=3):
    '''make Vector objects out of a list'''
    #test if list contains right number of elements

    result = []
    for i in range(0, len(list), dimension):
        try:
            vec = mathutils.Vector([list[i + ind] for ind in range(dimension)])
        except:
            print('Number of elemnts doesnt match into the vectors.')
            return None

        result.append(vec)

    return result
