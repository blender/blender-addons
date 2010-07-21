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
    'name': 'Object: Fracture Tools',
    'author': 'pildanovak',
    'version': '2.0',
    'blender': (2, 5, 3),
    'location': 'Fracture tools (Search > Fracture Object & ,' \
        'Add -> Fracture Helper Objects',
    'description': 'Fractured Object, Bomb, Projectile, Recorder',
    'warning': '', # used for warning icon and text in addons panel
    'wiki_url': 'http://wiki.blender.org/index.php/Extensions:2.5/Py/' \
        'Scripts/Object/Fracture',
    'tracker_url': 'https://projects.blender.org/tracker/index.php?'\
        'func=detail&aid=21793&group_id=153&atid=469',
    'category': 'Object'}


import bpy
from object_fracture import fracture_ops, fracture_setup


class INFO_MT_add_fracture_objects(bpy.types.Menu):
    bl_idname = "INFO_MT_add_fracture_objects"
    bl_label = "Fracture Helper Objects"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("object.import_fracture_bomb",
            text="Bomb")
        layout.operator("object.import_fracture_projectile",
            text="Projectile")
        layout.operator("object.import_fracture_recorder",
            text="Rigidbody Recorder")

import space_info
# Define the submenu
menu_func = (lambda self,
    context: self.layout.menu("INFO_MT_add_fracture_objects", icon="PLUGIN"))


def register():
    bpy.types.register(fracture_ops.FractureSimple)
    bpy.types.register(fracture_ops.FractureGroup)
    bpy.types.register(fracture_ops.ImportFractureRecorder)
    bpy.types.register(fracture_ops.ImportFractureBomb)
    bpy.types.register(fracture_ops.ImportFractureProjectile)
    bpy.types.register(fracture_setup.SetupFractureShards)
    bpy.types.register(INFO_MT_add_fracture_objects)

    # Add the "add fracture objects" menu to the "Add" menu
    space_info.INFO_MT_add.append(menu_func)


def unregister():
    bpy.types.unregister(fracture_ops.FractureSimple)
    bpy.types.unregister(fracture_ops.FractureGroup)
    bpy.types.unregister(fracture_ops.ImportFractureRecorder)
    bpy.types.unregister(fracture_ops.ImportFractureBomb)
    bpy.types.unregister(fracture_ops.ImportFractureProjectile)
    bpy.types.unregister(fracture_setup.SetupFractureShards)
    bpy.types.unregister(INFO_MT_add_fracture_objects)

    # Remove "add fracture objects" menu from the "Add" menu.
    space_info.INFO_MT_add.remove(menu_func)

if __name__ == "__main__":
    register()
