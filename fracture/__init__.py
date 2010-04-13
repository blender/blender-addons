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
    'name': 'Object: Fracture tools',
    'author': 'pildanovak',
    'version': '2.0',
    'blender': (2, 5, 3),
    'location': 'Fracture tools (Search > Fracture Object,' \
        ' Add Bomb, Rigidbody Recorder)',
    'url': 'http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/',
    'category': 'Object'}

import bpy


def register():
    from fracture import fracture_ops, fracture_setup
    bpy.types.register(fracture_ops.FractureSimple)
    bpy.types.register(fracture_ops.FractureGroup)
    bpy.types.register(fracture_ops.ImportRecorder)
    bpy.types.register(fracture_ops.ImportBomb)
    bpy.types.register(fracture_ops.ImportProjectile)
    bpy.types.register(fracture_setup.SetupShards)


def unregister():
    from fracture import fracture_ops, fracture_setup
    bpy.types.unregister(fracture_ops.FractureSimple)
    bpy.types.unregister(fracture_ops.FractureGroup)
    bpy.types.unregister(fracture_ops.ImportRecorder)
    bpy.types.unregister(fracture_ops.ImportBomb)
    bpy.types.unregister(fracture_ops.ImportProjectile)
    bpy.types.unregister(fracture_setup.SetupShards)

if __name__ == "__main__":
    register()
