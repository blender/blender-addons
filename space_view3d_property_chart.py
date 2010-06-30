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
    'name': '3D View: Object Property Chart',
    'author': 'Campbell Barton (ideasman42)',
    'version': '0.1',
    'blender': (2, 5, 3),
    'location': 'Tool Shelf',
    'description': 'Edit arbitrary selected properties for objects of the same type',
    'wiki_url': 'http://wiki.blender.org/index.php/Extensions:2.5/Py/' \
        'Scripts/3D interaction/Object Property Chart',
    'tracker_url': 'https://projects.blender.org/tracker/index.php?' \
        'func=detail&aid=22701&group_id=153&atid=469',
    'category': '3D View'}

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

        selected_objects = context.selected_objects

        if not selected_objects:
            return

        # box = layout.separator()
        
        id_storage = context.scene
        
        strings = id_storage.get(self._PROP_STORAGE_ID)
        
        if strings is None:
            strings = id_storage[self._PROP_STORAGE_ID] = "data data.name"

        if strings:
            
            def obj_prop_get(obj, attr_string):
                """return a pair (rna_base, "rna_property") to give to the rna UI property function"""
                attrs = attr_string.split(".")
                val_new = obj
                for i, attr in enumerate(attrs):
                    val_old = val_new
                    val_new = getattr(val_old, attr, Ellipsis)
                    
                    if val_new == Ellipsis:
                        return None, None                        
                return val_old, attrs[-1]

            strings = strings.split()

            prop_all = []

            for obj in selected_objects:
                prop_pairs = []
                prop_found = False
                for attr_string in strings:
                    prop_pairs.append(obj_prop_get(obj, attr_string))
                    if prop_found == False and prop_pairs[-1] != (None, None): 
                        prop_found = True

                if prop_found:
                    prop_all.append((obj, prop_pairs))


            # Collected all props, now display them all
            row = layout.row()

            col = row.column()
            col.label(text="name")
            for obj, prop_pairs in prop_all:
                col.prop(obj, "name", text="")

            for i in range(len(strings)):
                col = row.column()
                col.label(text=strings[i].rsplit(".", 1)[-1])
                for obj, prop_pairs in prop_all:
                    data, attr = prop_pairs[i]
                    if data:
                        col.prop(data, attr, text="")
                    else:
                        col.label(text="<missing>")

        # edit the display props
        col = layout.column()
        col.label(text="Object Properties")
        col.prop(id_storage, '["%s"]' % self._PROP_STORAGE_ID, text="")

	
def register():
    bpy.types.register(View3DEditProps)


def unregister():
    bpy.types.unregister(View3DEditProps)

if __name__ == "__main__":
    register()
