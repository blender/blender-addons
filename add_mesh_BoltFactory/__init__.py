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


bl_addon_info = {
    'name': 'Add Mesh: BoltFactory',
    'author': 'Aaron Keith',
    'version': '3.9',
    'blender': (2, 5, 3),
    'location': 'add Mesh',
    'wiki_url': 'http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/Add_Mesh/BoltFactory',
    'tracker_url': 'https://projects.blender.org/tracker/index.php?func=detail&aid=22842&group_id=153&atid=468',
    'category': 'Add Mesh'}

import bpy
from add_mesh_BoltFactory.Boltfactory import add_mesh_bolt

################################################################################
##### REGISTER #####

add_mesh_bolt_button = (lambda self, context: self.layout.operator
            (add_mesh_bolt.bl_idname, text="BOLT", icon="PLUGIN"))

classes = [
add_mesh_bolt
    ]

def register():
    register = bpy.types.register
    for cls in classes:
        register(cls)

    bpy.types.INFO_MT_mesh_add.append(add_mesh_bolt_button)
    #bpy.types.VIEW3D_PT_tools_objectmode.prepend(add_mesh_bolt_button) #just for testing

def unregister():
    unregister = bpy.types.unregister
    for cls in classes:
        unregister(cls)

    bpy.types.INFO_MT_mesh_add.remove(add_mesh_bolt_button)
    #bpy.types.VIEW3D_PT_tools_objectmode.remove(add_mesh_bolt_button) #just for testing
    
if __name__ == "__main__":
    register()