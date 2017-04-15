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

bl_info = {
    "name": "Mesh: Constellation",
    "author": "Oscurart",
    "version": (1, 0),
    "blender": (2, 67, 0),
    "location": "Add > Mesh > Constellation",
    "description": "Adds a new Mesh From Selected",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Add Mesh"}

import bpy
from bpy.types import Operator
from bpy.props import FloatProperty
from math import sqrt


def VertDis(a, b):
    dst = sqrt(pow(a.co.x - b.co.x, 2) +
               pow(a.co.y - b.co.y, 2) +
               pow(a.co.z - b.co.z, 2))
    return(dst)


def OscConstellation(limit):
    actobj = bpy.context.object
    vertlist = []
    edgelist = []
    edgei = 0

    for ind, verta in enumerate(actobj.data.vertices[:]):
        for vertb in actobj.data.vertices[ind:]:
            if VertDis(verta, vertb) <= limit:
                vertlist.append(verta.co[:])
                vertlist.append(vertb.co[:])
                edgelist.append((edgei, edgei + 1))
                edgei += 2

    mesh = bpy.data.meshes.new("rsdata")
    object = bpy.data.objects.new("rsObject", mesh)
    bpy.context.scene.objects.link(object)
    mesh.from_pydata(vertlist, edgelist, [])


class Oscurart_Constellation (Operator):
    bl_idname = "mesh.constellation"
    bl_label = "Constellation"
    bl_description = "Create a Constellation Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    limit = FloatProperty(
                name='Limit',
                default=2,
                min=0
                )

    @classmethod
    def poll(cls, context):
        return(bpy.context.active_object.type == "MESH")

    def execute(self, context):
        OscConstellation(self.limit)

        return {'FINISHED'}


# Register

def add_osc_constellation_button(self, context):
    self.layout.operator(
        Oscurart_Constellation.bl_idname,
        text="Constellation",
        icon="PLUGIN")


def register():
    bpy.utils.register_class(Oscurart_Constellation)
    bpy.types.INFO_MT_mesh_add.append(add_osc_constellation_button)


def unregister():
    bpy.utils.unregister_class(Oscurart_Constellation)
    bpy.types.INFO_MT_mesh_add.remove(add_osc_constellation_button)


if __name__ == '__main__':
    register()
