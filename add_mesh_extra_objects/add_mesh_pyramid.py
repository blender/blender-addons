# add_mesh_pyramid.py (c) 2011 Phil Cote (cotejrp1)
#
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
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****
'''
bl_info = {
    'name': 'Mesh Pyramid',
    'author': 'Phil Cote, cotejrp1, (http://www.blenderaddons.com)',
    'version': (0,1),
    "blender": (2, 5, 7),
    "api": 35853,
    'location': 'View3D > Add > Mesh',
    'description': 'Create an egyption-style step pyramid',
    'warning': '', # used for warning icon and text in addons panel
    'category': 'Add Mesh'}
'''

import bpy
from bpy.props import FloatVectorProperty, IntProperty, FloatProperty
from add_utils import AddObjectHelper, add_object_data
from mathutils import Vector

def makePyramid( initialSize, stepHeight, stepWidth, numberSteps ):
    
    vertList = []
    faceList = []
 
    curSize = initialSize # how large each step will be overall
    
    # b = buttom, t = top, f = front, b = back, l = left, r = right
    x = y = z = 0
    voffset = 0 # refers relative vert indices to help make faces fo each step
    sn = 0 # step number
 
    while sn < numberSteps:
        # bottom verts for this iteration   
        bfl = (x,y,z)
        bfr = (x+curSize, y, z)
        bbl = (x,y+curSize,z)
        bbr = (x+curSize, y+curSize, z)
 
        # top verts for this iteration.
        tfl = (x,y,z+stepHeight)
        tfr = (x+curSize, y, z+stepHeight)
        tbl = (x,y+curSize,z+stepHeight)
        tbr = (x+curSize, y+curSize, z+stepHeight)
 
        # add to the vert buffer
        vertList.extend( ( bfl, bfr, bbl, bbr, tfl, tfr, tbl, tbr, ) )
        
        # side faces
        faceList.extend( ( ( voffset+4, voffset+5, voffset+1, voffset+0 ), ) )# front
        faceList.extend( ( ( voffset+6, voffset+7, voffset+3, voffset+2  ), ) )# back
        faceList.extend( ( ( voffset+2, voffset+6, voffset+4, voffset+0  ), ) ) # left
        faceList.extend( ( ( voffset+3, voffset+7, voffset+5, voffset+1 ), ) ) # right
 
 
        # horizontal connecting faces ( note: not applicable for the first iteration ).
        if voffset > 0:
          faceList.extend( ( (voffset-4, voffset-3, voffset+1, voffset+0 ), ) ) # connector front
          faceList.extend( ( (voffset-2, voffset-1, voffset+3, voffset+2 ), ) ) # back
          faceList.extend( ( (voffset-4, voffset-2, voffset+2, voffset+0 ), ) )  # left
          faceList.extend( ( (voffset-3, voffset-1, voffset+3, voffset+1 ), ) ) # right
            
 
        # set up parameters for the next iteration
        curSize = curSize - ( stepWidth * 2 )
        x = x + stepWidth
        y = y + stepWidth
        z = z + stepHeight
        sn = sn + 1
        voffset = voffset + 8
 
        
    # cap the top.
    voffset = voffset - 8 # corrects for the unnecessary voffset change done final iteration
    faceList.extend( ( (voffset+6, voffset+7, voffset+5, voffset+4), ) )
 
    # cap the bottom.
    faceList.extend( ( ( 2, 3, 1, 0), ) )
    return vertList, faceList


def add_pyramid_object( self, context ):
    verts, faces = makePyramid( self.initialSize, self.stepHeight, self.stepWidth, self.numberSteps )
    mesh_data = bpy.data.meshes.new( name = "Pyramid" )
    mesh_data.from_pydata( verts, [], faces )
    mesh_data.update()
    res = add_object_data( context, mesh_data, operator=self )
    
    
class OBJECT_OT_add_pyramid(bpy.types.Operator, AddObjectHelper):
    """Add a Mesh Object"""
    bl_idname = "mesh.primative_step_pyramid_add"
    bl_label = "Pyramid"
    bl_description = "Create a Pyramid Mesh"
    bl_options = {'REGISTER', 'UNDO'}
    
    initialSize = FloatProperty( name="Initial Size", default=2.0, min=0.0, max=20.0 )
    stepHeight= FloatProperty( name="Step Height", default=0.2, min=0.0, max=10.0 )
    stepWidth= FloatProperty( name="Step Width", default=0.2, min=0.0, max=10.0 )
    numberSteps= IntProperty( name="Number Steps", default=5, min=1, max=20 )
    

    def execute(self, context):
        add_pyramid_object(self, context)
        return {'FINISHED'}
