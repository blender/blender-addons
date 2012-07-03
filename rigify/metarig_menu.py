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

# <pep8 compliant>

import bpy
from rigify.metarigs import human


class AddHuman(bpy.types.Operator):
    """Add an advanced human metarig base"""
    bl_idname = "object.armature_human_advanced_add"
    bl_label = "Add Humanoid (advanced metarig)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.armature_add()
        obj = context.active_object
        mode_orig = obj.mode
        bpy.ops.object.mode_set(mode='EDIT')  # grr, remove bone
        bones = context.active_object.data.edit_bones
        bones.remove(bones[0])
        human.create(obj)
        bpy.ops.object.mode_set(mode=mode_orig)
        return {'FINISHED'}


# Add to a menu
menu_func = (lambda self, context: self.layout.operator(AddHuman.bl_idname,
                    icon='OUTLINER_OB_ARMATURE', text="Human (Meta-Rig)"))


def register():
    bpy.utils.register_class(AddHuman)

    bpy.types.INFO_MT_armature_add.append(menu_func)


def unregister():
    bpy.utils.unregister_class(AddHuman)

    bpy.types.INFO_MT_armature_add.remove(menu_func)
