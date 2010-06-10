#
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
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****

'''List properties of selected objects'''

bl_addon_info = {
    "name": "3D View: Object Property Chart",
    "author": "Campbell Barton (ideasman42)",
    "version": "0.1",
    "blender": (2, 5, 3),
    "location": "Tool Shelf",
    "description": "Edit arbitrary selected properties for objects of the same type"}

import bpy


class View3DEditProps(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    
    bl_label = "Property Chart"
    bl_context = "objectmode"
    
    _PROP_STORAGE_ID = "view3d_edit_props"

    def draw(self, context):
        layout = self.layout
        obj = context.object
        
        if obj is None:
            return

        obj_type_sel = [obj_sel for obj_sel in context.selected_objects if obj.type == obj_sel.type]

        if not obj_type_sel:
            return

        # box = layout.separator()
        
        col = layout.column()
        
        id_storage = context.scene
        
        strings = id_storage.get(self._PROP_STORAGE_ID)
        
        if strings is None:
            strings = id_storage[self._PROP_STORAGE_ID] = ""

        if strings:
            strings = strings.split()

            row = col.row(align=True)
            for attr_string in strings:
                row.label(text=attr_string.rsplit(".", 1)[-1])

            for obj in obj_type_sel:
                row = col.row(align=True)
                for attr_string in strings:

                    attrs = attr_string.split(".")
                    val_new = obj
                    for i, attr in enumerate(attrs):
                        val_old = val_new
                        val_new = getattr(val_old, attr, Ellipsis)
                        
                        if val_new == Ellipsis:
                            break

                    if val_new is not Ellipsis:
                        row.prop(val_old, attrs[-1], text="")
                    else:
                        row.label(text="")
        
        col.label(text="Display Properties")
        col.prop(id_storage, '["%s"]' % self._PROP_STORAGE_ID, text="")


def register():
    bpy.types.register(View3DEditProps)


def unregister():
    bpy.types.unregister(View3DEditProps)

if __name__ == "__main__":
    register()
