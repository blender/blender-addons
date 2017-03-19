# gpl author: Stanislav Blinov

bl_info = {
    "name": "V/E/F Context Menu",
    "author": "Stanislav Blinov",
    "version": (1, 0, 0),
    "blender": (2, 74, 0),
    "description": "Vert Edge Face Double Right Click Edit Mode",
    "category": "Mesh",
}

import bpy
from bpy.types import (
        Menu,
        Operator,
        )


class MESH_MT_CombinedMenu(Menu):
    bl_idname = "mesh.addon_combined_component_menu"
    bl_label = "Components"

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def draw(self, context):
        layout = self.layout

        mode = context.tool_settings.mesh_select_mode
        if mode[0]:
            layout.menu("VIEW3D_MT_edit_mesh_vertices")
        if mode[1]:
            layout.menu("VIEW3D_MT_edit_mesh_edges")
        if mode[2]:
            layout.menu("VIEW3D_MT_edit_mesh_faces")


class MESH_OT_CallContextMenu(Operator):
    bl_idname = "mesh.addon_call_context_menu"
    bl_label = "Context Menu"

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        mode = context.tool_settings.mesh_select_mode
        num = sum(int(m) for m in mode)
        if num == 1:
            if mode[0]:
                return bpy.ops.wm.call_menu(name="VIEW3D_MT_edit_mesh_vertices")
            if mode[1]:
                return bpy.ops.wm.call_menu(name="VIEW3D_MT_edit_mesh_edges")
            if mode[2]:
                return bpy.ops.wm.call_menu(name="VIEW3D_MT_edit_mesh_faces")
        else:
            return bpy.ops.wm.call_menu(name=MESH_MT_CombinedMenu.bl_idname)


classes = [
    MESH_MT_CombinedMenu,
    MESH_OT_CallContextMenu
]

addon_keymaps = []


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
    kmi = km.keymap_items.new('mesh.addon_call_context_menu', 'RIGHTMOUSE', 'DOUBLE_CLICK')


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    wm = bpy.context.window_manager

    # remove multiselect keybinding
    km = wm.keyconfigs.addon.keymaps['3D View']
    for kmi in km.keymap_items:
        if kmi.idname == 'wm.call_menu':
            if kmi.properties.name == "mesh.addon_call_context_menu":
                km.keymap_items.remove(kmi)
                break


if __name__ == "__main__":
    register()
