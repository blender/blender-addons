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
    'version': (0, 3),
    "blender": (2, 5, 8),
    "api": 37702,
    'location': 'View3D > Add > Mesh',
    'description': 'Create an egyption-style step pyramid',
    'warning': '',  # used for warning icon and text in addons panel
    'category': 'Add Mesh'}
'''

import bpy
from bpy.props import IntProperty, FloatProperty

from add_utils import AddObjectHelper, add_object_data


def makePyramid(initial_size, step_height, step_width, number_steps):

    vert_list = []
    face_list = []

    cur_size = initial_size  # how large each step will be overall

    # b = buttom, t = top, f = front, b = back, l = left, r = right
    x = y = z = 0
    voffset = 0  # relative vert indices to help make faces fo each step
    sn = 0  # step number

    while sn < number_steps:
        # bottom verts for this iteration
        bfl = (x, y, z)
        bfr = (x + cur_size, y, z)
        bbl = (x, y + cur_size, z)
        bbr = (x + cur_size, y + cur_size, z)

        # top verts for this iteration.
        tfl = (x, y, z + step_height)
        tfr = (x + cur_size, y, z + step_height)
        tbl = (x, y + cur_size, z + step_height)
        tbr = (x + cur_size, y + cur_size, z + step_height)

        # add to the vert buffer
        vert_list.extend((bfl, bfr, bbl, bbr, tfl, tfr, tbl, tbr,))

        # side faces
        face_list.extend((
            (voffset + 4, voffset + 5, voffset + 1, voffset + 0), # back
            (voffset + 6, voffset + 7, voffset + 3, voffset + 2), # front
            (voffset + 2, voffset + 6, voffset + 4, voffset + 0), # left
            (voffset + 3, voffset + 7, voffset + 5, voffset + 1), # right
            ))

        # horizontal connecting faces ( note: n/a for the first iteration ).
        if voffset > 0:
            face_list.extend((
                (voffset - 4, voffset - 3, voffset + 1, voffset + 0), # connector front
                (voffset - 2, voffset - 1, voffset + 3, voffset + 2), # back
                (voffset - 4, voffset - 2, voffset + 2, voffset + 0), # left
                (voffset - 3, voffset - 1, voffset + 3, voffset + 1), # right
                ))

        # set up parameters for the next iteration
        cur_size = cur_size - (step_width * 2)
        x = x + step_width
        y = y + step_width
        z = z + step_height
        sn = sn + 1
        voffset = voffset + 8

    voffset = voffset - 8  # remove extra voffset done on final iteration
    face_list.extend((
        (voffset + 6, voffset + 7, voffset + 5, voffset + 4), # cap the top.
        (2, 3, 1, 0), # cap the bottom.
        ))

    return vert_list, face_list


def add_pyramid_object(self, context):
    verts, faces = makePyramid(self.initial_size, self.step_height,
                            self.step_width, self.number_steps)

    mesh_data = bpy.data.meshes.new(name="Pyramid")
    mesh_data.from_pydata(verts, [], faces)
    mesh_data.update()
    res = add_object_data(context, mesh_data, operator=self)


class AddPyramid(bpy.types.Operator, AddObjectHelper):
    """Add a Mesh Object"""
    bl_idname = "mesh.primitive_steppyramid_add"
    bl_label = "Pyramid"
    bl_options = {'REGISTER', 'UNDO'}

    initial_size = FloatProperty(name="Initial Size", default=2.0,
                                min=0.0, max=20.0,
                                description="Set the initial size at the pyramid base")

    step_height = FloatProperty(name="Step Height", default=0.1,
                                min=0.0, max=10.0,
                                description="How tall each of the steps will be")

    step_width = FloatProperty(name="Step Width", default=0.1,
                                min=0.0, max=10.0,
                                description="How wide each step will be")

    number_steps = IntProperty(name="Number Steps", default=10,
                                min=1, max=20,
                                description="Total number of steps")

    def execute(self, context):
        add_pyramid_object(self, context)
        return {'FINISHED'}

'''
def menu_func(self, context):
    self.layout.operator(OBJECT_OT_add_pyramid.bl_idname,
                        text="Pyramid", icon="PLUGIN")


def register():
    bpy.utils.register_class(OBJECT_OT_add_pyramid)
    bpy.types.INFO_MT_mesh_add.append(menu_func)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_add_pyramid)
    bpy.types.INFO_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
    register()
'''