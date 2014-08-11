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

bl_info = {
    "name": "Pie Menus Official",
    "author": "Antony Riakiotakis",
    "version": (1, 0, 0),
    "blender": (2, 71, 4),
    "description": "Enable official pie Menus in blender",
    "category": "User Interface",
}


import bpy
from bpy.types import Menu


class VIEW3D_PIE_object_mode(Menu):
    bl_label = "Mode"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()
        pie.operator_enum("OBJECT_OT_mode_set", "mode")


class VIEW3D_PIE_view(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()
        pie.operator_enum("VIEW3D_OT_viewnumpad", "type")
        pie.operator("VIEW3D_OT_view_persportho", text="Persp/Ortho", icon='RESTRICT_VIEW_OFF')


class VIEW3D_PIE_shade(Menu):
    bl_label = "Shade"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()
        pie.prop(context.space_data, "viewport_shade", expand=True)

        if context.active_object:
            if(context.mode == 'EDIT_MESH'):
                pie.operator("MESH_OT_faces_shade_smooth")
                pie.operator("MESH_OT_faces_shade_flat")
            else:
                pie.operator("OBJECT_OT_shade_smooth")
                pie.operator("OBJECT_OT_shade_flat")


class VIEW3D_PIE_manipulator(Menu):
    bl_label = "Manipulator"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()
        pie.prop(context.space_data, "transform_manipulators", expand=True)
        pie.prop(context.space_data, "show_manipulator")


class VIEW3D_PIE_pivot(Menu):
    bl_label = "Pivot"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()
        pie.prop(context.space_data, "pivot_point", expand=True)
        if context.active_object.mode == 'OBJECT':
            pie.prop(context.space_data, "use_pivot_point_align", text="Center Points")


class VIEW3D_PIE_snap(Menu):
    bl_label = "Snapping"

    def draw(self, context):
        layout = self.layout

        toolsettings = context.tool_settings
        pie = layout.menu_pie()
        pie.prop(toolsettings, "snap_element", expand=True)
        pie.prop(toolsettings, "use_snap")


addon_keymaps = []


def register():
    #register menus first
    bpy.utils.register_class(VIEW3D_PIE_object_mode)
    bpy.utils.register_class(VIEW3D_PIE_view)
    bpy.utils.register_class(VIEW3D_PIE_shade)
    bpy.utils.register_class(VIEW3D_PIE_manipulator)
    bpy.utils.register_class(VIEW3D_PIE_pivot)
    bpy.utils.register_class(VIEW3D_PIE_snap)

    wm = bpy.context.window_manager

    km = wm.keyconfigs.addon.keymaps.new(name='Object Non-modal')
    kmi = km.keymap_items.new('wm.call_menu_pie', 'TAB', 'PRESS')
    kmi.properties.name = 'VIEW3D_PIE_object_mode'
    kmi = km.keymap_items.new('wm.call_menu_pie', 'Z', 'PRESS')
    kmi.properties.name = 'VIEW3D_PIE_shade'
    kmi = km.keymap_items.new('wm.call_menu_pie', 'Q', 'PRESS')
    kmi.properties.name = 'VIEW3D_PIE_view'
    kmi = km.keymap_items.new('wm.call_menu_pie', 'SPACE', 'PRESS', ctrl=True)
    kmi.properties.name = 'VIEW3D_PIE_manipulator'
    kmi = km.keymap_items.new('wm.call_menu_pie', 'PERIOD', 'PRESS')
    kmi.properties.name = 'VIEW3D_PIE_pivot'
    kmi = km.keymap_items.new('wm.call_menu_pie', 'COMMA', 'PRESS')
    kmi.properties.name = 'VIEW3D_PIE_snap'

    addon_keymaps.append(km)


def unregister():
    bpy.utils.unregister_class(VIEW3D_PIE_object_mode)
    bpy.utils.unregister_class(VIEW3D_PIE_view)
    bpy.utils.unregister_class(VIEW3D_PIE_shade)
    bpy.utils.unregister_class(VIEW3D_PIE_manipulator)
    bpy.utils.unregister_class(VIEW3D_PIE_pivot)
    bpy.utils.unregister_class(VIEW3D_PIE_snap)

    wm = bpy.context.window_manager
    for km in addon_keymaps:
        for kmi in km.keymap_items:
            km.keymap_items.remove(kmi)

        wm.keyconfigs.addon.keymaps.remove(km)

    # clear the list
    del addon_keymaps[:]
