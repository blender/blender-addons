# ##### BEGIN GPL LICENSE BLOCK #####
#
#  The Blender Rock Creation tool is for rapid generation of mesh rocks.
#  Copyright (C) 2011  Paul Marshall
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####

import bpy

def setlocation(oper, context):
    if oper.align == "WORLD":
        location = oper.location - context.active_object.location
        bpy.ops.transform.translate(value = location, orient_type='GLOBAL')
        bpy.ops.transform.rotate(value = oper.rotation[0], orient_axis = 'X', orient_type='GLOBAL')
        bpy.ops.transform.rotate(value = oper.rotation[1], orient_axis = 'Y', orient_type='GLOBAL')
        bpy.ops.transform.rotate(value = oper.rotation[2], orient_axis = 'Z', orient_type='GLOBAL')
        
    elif oper.align == "VIEW":
        bpy.ops.transform.translate(value = oper.location)
        bpy.ops.transform.rotate(value = oper.rotation[0], orient_axis = 'X')
        bpy.ops.transform.rotate(value = oper.rotation[1], orient_axis = 'Y')
        bpy.ops.transform.rotate(value = oper.rotation[2], orient_axis = 'Z')

    elif oper.align == "CURSOR":
        location = context.active_object.location
        oper.location = bpy.context.scene.cursor.location - location
        oper.rotation = bpy.context.scene.cursor.rotation_euler

        bpy.ops.transform.translate(value = oper.location)
        bpy.ops.transform.rotate(value = oper.rotation[0], orient_axis = 'X')
        bpy.ops.transform.rotate(value = oper.rotation[1], orient_axis = 'Y')
        bpy.ops.transform.rotate(value = oper.rotation[2], orient_axis = 'Z')