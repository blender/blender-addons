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
    "name": "Add PolySphere",
    "author": "Andy Davies (metalliandy)",
    "version": (0,1,6),
    "blender": (2, 62, 0),
    "location": "View3D > Add > Mesh > PolySphere",
    "description": "Adds a PolySphere (all quads) for sculpting",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"
        "Scripts/Add_Mesh/Add_PolySphere",
    "tracker_url": "",
    "category": "Add Mesh"}
'''

import bpy

def Add_PolySphere():
    #Add Cube to scene
    bpy.ops.mesh.primitive_cube_add()

    #Changes name of Cube to PolySphere adds the variable cube
    cube = bpy.context.object
    cube.name = "PolySphere"

    #Positions Cube primitive to scene centre
    bpy.context.active_object.location = [0, 0, 0]

    #Adds Subsurf Modifier
    bpy.ops.object.modifier_add(type='SUBSURF')

    #Selects Subsurf Modifier for editing
    subsurf = cube.modifiers['Subsurf']

    #Changes Subsurf levels
    subsurf.levels = 3

    #Applys Subsurf Modifier
    bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Subsurf")

    #Adds smooth shading
    bpy.ops.object.shade_smooth()

    #Change to Editmode
    bpy.ops.object.editmode_toggle()

    #Selects cube in Editmode
    #bpy.ops.mesh.select_all(action='TOGGLE')

    #Adds transform "To Sphere"
    bpy.ops.transform.tosphere(value=1)

    #Change to Objectmode
    bpy.ops.object.editmode_toggle()

    #Scales Object to 2.0 Units
    bpy.ops.transform.resize(value=(1.15525, 1.15525, 1.15525), constraint_axis=(False, False, False), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1, snap=False, snap_target='CLOSEST', snap_point=(0, 0, 0), snap_align=False, snap_normal=(0, 0, 0), release_confirm=False)

    #Applys location, rotation and scale data
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

#makes PolySphere an operator
class AddPolySphere(bpy.types.Operator):

    bl_idname = "mesh.primitive_polysphere_add"
    bl_label = "Add PolySphere"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        Add_PolySphere()
        return {'FINISHED'}
