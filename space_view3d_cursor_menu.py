#3d_cursor_menu.py (c) 2010 Jonathan Smith (JayDez)
#Original Script by: Mariano Hidalgo (uselessdreamer)
#contributed to by: Crouch
#
#Tested with r27424
#
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

"""
3D Cursor Menu

This adds a 3D Cursor Menu in the 3DView.


Usage:
Enable in "user preferences>addons>3d_cursor_menu".

Right click in an empty space in the 3D View(that means nothing
selectable is there). If your select mouse is set to left then left
click in the 3D View.

Choose your function from the menu.

Version history:
v2.42 = (JayDez) - Added url for tech support.
v2.41 - (JayDez) - Cleaned up bpydoc, added underscores in the name.
v2.4 - (JayDez) - Added bpydoc as well as changing to click only
    (instead of double click).
v2.3 - (JayDez) - Added revert_pivot() which allows you to change
    pivot point back to normal(which right now is median point).
v2.2 - (Crouch) - Fix in register function, fix with random quotation
    mark which crashed script.
v2.1 - (Crouch) - added unregister() and set pivot point to cursor.
v2.0 - (JayDez) - 2.5 script (initial revision)
v1.0 - Original 2.49 script
"""

bl_addon_info = {
    'name': '3d View: Cursor Menu',
    'author': 'JayDez',
    'version': '2.4',
    'blender': (2, 5, 3),
    'location': 'View3D > Mouse > Menu ',
    'description': 'This adds a 3D Cursor Menu in the 3D View',
    'url': 'http://wiki.blender.org/index.php/Extensions:2.5/Py/' \
	    'Scripts/3D_interaction/Cursor_Menu',
    'category': '3D View'}

import bpy
from bpy import *


class pivot_cursor(bpy.types.Operator):
    bl_idname = "view3d.pivot_cursor"
    bl_label = "Cursor as Pivot Point"

    def poll(self, context):
        return bpy.context.space_data.pivot_point != 'CURSOR'

    def execute(self, context):
        bpy.context.space_data.pivot_point = 'CURSOR'
        return {'FINISHED'}


class revert_pivot(bpy.types.Operator):
    bl_idname = "view3d.revert_pivot"
    bl_label = "Reverts Pivot Point to median"

    def poll(self, context):
        return bpy.context.space_data.pivot_point != 'MEDIAN_POINT'

    def execute(self, context):
        bpy.context.space_data.pivot_point = 'MEDIAN_POINT'
        #change this to 'BOUDNING_BOX_CENTER' if needed...
        return{'FINISHED'}


class VIEW3D_MT_3D_Cursor_Menu(bpy.types.Menu):
    bl_label = "3D Cursor Menu"

    def draw(self, context):
        layout = self.layout

        layout.operator("view3d.snap_cursor_to_center", text="Snap Cursor to Center")
        layout.operator("view3d.snap_cursor_to_grid", text="Snap Cursor to Grid")
        layout.operator("view3d.snap_cursor_to_selected", text="Snap Cursor to Selected")
        layout.operator("view3d.snap_selected_to_cursor", text="Snap Selected to Cursor")

        layout.separator()

        layout.operator("view3d.pivot_cursor", text="Set Cursor as Pivot Point")
        layout.operator("view3d.revert_pivot", text="Revert Pivot Point")


def register():
    bpy.types.register(VIEW3D_MT_3D_Cursor_Menu)
    bpy.types.register(pivot_cursor)
    bpy.types.register(revert_pivot)
    km = bpy.context.manager.keyconfigs.active.keymaps['3D View']
    kmi = km.items.add('wm.call_menu', 'SELECTMOUSE', 'CLICK')
    kmi.properties.name = "VIEW3D_MT_3D_Cursor_Menu"


def unregister():
    bpy.types.unregister(VIEW3D_MT_3D_Cursor_Menu)
    bpy.types.unregister(pivot_cursor)
    bpy.types.unregister(revert_pivot)
    km = bpy.context.manager.keyconfigs.active.keymaps['3D View']
    for kmi in km.items:
        if kmi.idname == 'wm.call_menu':
            if kmi.properties.name == "VIEW3D_MT_3D_Cursor_Menu":
                km.remove_item(kmi)
                break

if __name__ == "__main__":
    register()
