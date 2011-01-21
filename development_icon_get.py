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
    'name': 'Icons',
    'author': 'Crouch, N.tox, PKHG, Campbell Barton, Dany Lebel',
    'version': (1, 5, 0),
    'blender': (2, 5, 7),
    'api': 34404,
    'location': 'Text window > Properties panel (ctrl+F) or '\
        'Console > Console menu',
    'warning': '',
    'description': 'Click an icon to display its name and copy it '\
        'to the clipboard',
    'wiki_url': 'http://wiki.blender.org/index.php/Extensions:2.5/'\
        'Py/Scripts/System/Display_All_Icons',
    'tracker_url': 'http://projects.blender.org/tracker/index.php?'\
        'func=detail&aid=22011',
    'category': 'Development'}


import bpy


def create_icon_list():
    props = bpy.context.scene.icon_props
    keys = bpy.types.UILayout.bl_rna.functions['prop'].parameters['icon'].\
        items.keys()
    if props.search == '':
        list = keys
    else:
        list = [key for key in keys if props.search.lower() in key.lower()]
    if "BLENDER" in list:
        list.remove("BLENDER")
    return list


class IconProps(bpy.types.IDPropertyGroup):
    """
    Fake module like class
    bpy.context.scene.icon_props
    """
    pass


class WM_OT_icon_info(bpy.types.Operator):
    bl_label = "Icon Info"
    bl_description = "Click to copy this icon name to the clipboard"
    icon = bpy.props.StringProperty()
    icon_scroll = bpy.props.IntProperty()
        
    def invoke(self, context, event):
        bpy.data.window_managers['WinMan'].clipboard = self.icon
        self.report({'INFO'}, "Icon ID: %s" % self.icon)
        return {'FINISHED'}


class WM_OT_icon_prop_update(bpy.types.Operator):
    bl_label = "Icon Search"
    bl_description = "Update icon_prop values"
    
    def execute(self, context):
        props = context.scene.icon_props
        # set old values to new values
        props.search_old = props.search
        
        return {'FINISHED'}


class OBJECT_PT_icons(bpy.types.Panel):
    bl_space_type = "TEXT_EDITOR"
    bl_region_type = "UI"
    bl_label = "All icons"
    
    def __init__(self, x):
        self.amount = 10
        self.icon_list = create_icon_list()
    
    def draw(self, context):
        props = context.scene.icon_props
        # polling for updates
        if props.search != props.search_old:
            bpy.ops.wm.icon_prop_update()
            self.icon_list = create_icon_list()
            # adjusting max value of scroller
            IconProps.scroll = bpy.props.IntProperty(default=1, min=1,
                max=max(1, len(self.icon_list) - self.amount + 1),
                description="Drag to scroll icons")
        
        box = self.layout.box()
        # scroll view
        if not props.expand:
            # expand button
            toprow = box.row()
            toprow.prop(props, "expand", icon="TRIA_RIGHT", icon_only=True,
                emboss=False)
            # search buttons
            row = toprow.row(align=True)
            row.prop(props, "search", icon="VIEWZOOM")
            # scroll button
            row = toprow.row()
            row.active = props.bl_rna.scroll[1]['max'] > 1
            row.prop(props, "scroll")
            
            # icons
            row = box.row(align=True)
            if len(self.icon_list) == 0:
                row.label("No icons found")
            else:
                for icon in self.icon_list[props.scroll-1:
                props.scroll-1+self.amount]:
                    row.operator("wm.icon_info", text=" ", icon=icon,
                        emboss=False).icon = icon
                if len(self.icon_list) < self.amount:
                    for i in range(self.amount - len(self.icon_list) \
                    % self.amount):
                        row.label("")
        
        # expanded view
        else:
            # expand button
            toprow = box.row()
            toprow.prop(props, "expand", icon="TRIA_DOWN", icon_only=True,
                emboss=False)
            # search buttons
            row = toprow.row(align=True)
            row.prop(props, "search", icon="VIEWZOOM")
            # scroll button
            row = toprow.row()
            row.active = False
            row.prop(props, "scroll")
            
            # icons
            col = box.column(align=True)
            if len(self.icon_list) == 0:
                row.label("No icons found")
            else:
                for i, icon in enumerate(self.icon_list):
                    if i % self.amount == 0:
                        row = col.row(align=True)
                    row.operator("wm.icon_info", text=" ", icon=icon,
                        emboss=False).icon = icon
                for i in range(self.amount - len(self.icon_list) \
                % self.amount):
                    row.label("")


class CONSOLE_HT_icons(bpy.types.Header):
    bl_space_type = 'CONSOLE'
    
    def __init__(self, x):
        self.amount = 10
        self.icon_list = create_icon_list()
    
    def draw(self, context):
        props = context.scene.icon_props
        # polling for updates
        if props.search != props.search_old:
            bpy.ops.wm.icon_prop_update()
            self.icon_list = create_icon_list()
            # adjusting max value of scroller
            IconProps.scroll = bpy.props.IntProperty(default=1, min=1,
                max=max(1, len(self.icon_list) - self.amount + 1),
                description="Drag to scroll icons")
        
        # scroll view
        if props.console:
            layout = self.layout
            layout.separator()
            # search buttons
            row = layout.row()
            row.prop(props, "search", icon="VIEWZOOM")
            # scroll button
            row = layout.row()
            row.active = props.bl_rna.scroll[1]['max'] > 1
            row.prop(props, "scroll")
            
            # icons
            row = layout.row(align=True)
            if len(self.icon_list) == 0:
                row.label("No icons found")
            else:
                for icon in self.icon_list[props.scroll-1:
                props.scroll-1+self.amount]:
                    row.operator("wm.icon_info", text="", icon=icon,
                        emboss=False).icon = icon


def menu_func(self, context):
    self.layout.prop(bpy.context.scene.icon_props, 'console')


def register():
    bpy.types.Scene.icon_props = bpy.props.PointerProperty(type = IconProps)
    IconProps.console = bpy.props.BoolProperty(name='Show System Icons',
        description='Display the Icons in the console header', default=False)
    IconProps.expand = bpy.props.BoolProperty(default=False,
        description="Expand, to display all icons at once")
    IconProps.search = bpy.props.StringProperty(default="",
        description = "Search for icons by name")
    IconProps.search_old = bpy.props.StringProperty(default="",
        description = "Used to keep track of changes in IconProps.search")
    
    icons_total = len(create_icon_list())
    icons_per_row = 10
    IconProps.scroll = bpy.props.IntProperty(default=1, min=1,
        max=max(1, icons_total - icons_per_row + 1),
        description="Drag to scroll icons")
    
    bpy.types.CONSOLE_MT_console.append(menu_func)


def unregister():
    if bpy.context.scene.get('icon_props') != None:
        del bpy.context.scene['icon_props']
    try:
        del bpy.types.Scene.icon_props
        bpy.types.CONSOLE_MT_console.remove(menu_func)
    except:
        pass
    if __name__ == "__main__":
        # unregistering is only done automatically when run as add-on
        bpy.types.unregister(OBJECT_PT_icons)
        bpy.types.unregister(CONSOLE_HT_icons)


if __name__ == "__main__":
    register()
