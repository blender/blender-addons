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

# (c) 2011 Phil Cote (cotejrp1)
'''
bl_info = {
    'name': 'Mesh Pyramid',
    'author': 'Phil Cote, cotejrp1, (http://www.blenderaddons.com)',
    'version': (0, 5),
    "blender": (2, 63, 0),
    'location': 'View3D > Add > Mesh',
    'description': 'Create an egyption-style step pyramid',
    'warning': '',  # used for warning icon and text in addons panel
    'category': 'Add Mesh'}
'''

import bpy
import bmesh
from bpy.props import FloatProperty, IntProperty
from math import pi
from mathutils import Quaternion, Vector
from bpy_extras.object_utils import AddObjectHelper, object_data_add


def create_step(width, base_level, step_height, num_sides):
        
        axis = [0,0,-1]
        PI2 = pi * 2
        rad = width / 2
        
        quat_angles = [(cur_side/num_sides) * PI2 
                            for cur_side in range(num_sides)]
                            
        quaternions = [Quaternion(axis, quat_angle) 
                            for quat_angle in quat_angles]
                            
        init_vectors = [Vector([rad, 0, base_level])] * len(quaternions)
        
        quat_vector_pairs = list(zip(quaternions, init_vectors))
        vectors = [quaternion * vec for quaternion, vec in quat_vector_pairs]
        bottom_list = [(vec.x, vec.y, vec.z) for vec in vectors]
        top_list = [(vec.x, vec.y, vec.z+step_height) for vec in vectors]
        full_list = bottom_list + top_list
        return full_list


def split_list(l, n):
    """
    split the blocks up.  Credit to oremj for this one.
    http://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks-in-python
    """
    n *= 2
    returned_list = [l[i:i+n] for i in range(0, len(l), n)]
    return returned_list
    


def get_connector_pairs(lst, n_sides):
    # chop off the verts that get used for the base and top
    lst = lst[n_sides:]
    lst = lst[:-n_sides]
    lst = split_list(lst, n_sides)
    return lst

def add_pyramid_object(self, context):
        all_verts = []
        
        height_offset = 0
        cur_width = self.width
        
        for i in range(self.num_steps):
            verts_loc = create_step(cur_width, height_offset, self.height,
                                    self.num_sides)
            height_offset += self.height
            cur_width -= self.reduce_by
            all_verts.extend(verts_loc)        
        
        mesh = bpy.data.meshes.new("Pyramid")
        bm = bmesh.new()

        for v_co in all_verts:
            bm.verts.new(v_co)
        
        
        # do the sides.
        n = self.num_sides
        
        def add_faces(n, block_vert_sets):
            for bvs in block_vert_sets:
                for i in range(self.num_sides-1):
                    bm.faces.new([bvs[i], bvs[i+n], bvs[i+n+1], bvs[i+1]])
                bm.faces.new([bvs[n-1], bvs[(n*2)-1], bvs[n], bvs[0]])
                
        
        # get the base and cap faces done.
        bm.faces.new(bm.verts[0:self.num_sides])
        bm.faces.new(bm.verts[-self.num_sides:])
        
        # side faces
        block_vert_sets = split_list(bm.verts, self.num_sides)
        add_faces(self.num_sides, block_vert_sets)
        
        # connector faces between faces and faces of the block above it.
        connector_pairs = get_connector_pairs(bm.verts, self.num_sides)
        add_faces(self.num_sides, connector_pairs)
        
        bm.to_mesh(mesh)
        mesh.update()
        res = object_data_add(context, mesh, operator=self)
    

class AddPyramid(bpy.types.Operator, AddObjectHelper):
    '''Add a mesh pyramid'''
    bl_idname = "mesh.primitive_steppyramid_add"
    bl_label = "Pyramid"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    
    num_sides = IntProperty(
                    name="Number Sides",
                    description = "How many sides each step will have",
                    min = 3, max = 20, default=4)
    num_steps = IntProperty(
                    name="Number of Steps",
                    description="How many steps for the overall pyramid",
                    min=1, max=20, default=10)
                
    width = FloatProperty(
            name="Initial Width",
            description="Initial base step width",
            min=0.01, max=100.0,
            default=2)
            
    height = FloatProperty(
            name="Height",
            description="How tall each step will be",
            min=0.01, max=100.0,
            default=0.1)
            
    reduce_by = FloatProperty(
                name="Reduce Step By", 
                description = "How much to reduce each succeeding step by",
                min=.01, max = 2.0, default= .20) 
    

    def execute(self, context):
        add_pyramid_object(self, context)
        return {'FINISHED'}

'''
def menu_func(self, context):
    self.layout.operator(AddPyramid.bl_idname, icon='PLUGIN')


def register():
    bpy.utils.register_class(AddPyramid)
    bpy.types.INFO_MT_mesh_add.append(menu_func)


def unregister():
    bpy.utils.unregister_class(AddPyramid)
    bpy.types.INFO_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
    register()
'''
