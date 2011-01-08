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


bl_addon_info = {
    'name': 'Icons',
    'author': 'Crouch, N.tox, PKHG, Campbell Barton, Dany Lebel',
    'version': (1, 4, 2),
    'blender': (2, 5, 6),
    'api': 33928,
    'location': 'Text window > Properties panel (ctrl+F) or '\
        'Console > Console menu',
    'warning': '',
    'description': 'Click an icon to display its name and copy it '\
        'to the clipboard',
    'wiki_url': 'http://wiki.blender.org/index.php/Extensions:2.5/'\
        'Py/Scripts/System/Display_All_Icons',
    'tracker_url': 'http://projects.blender.org/tracker/index.php?'\
        'func=detail&aid=22011',
    'category': 'System'}


import bpy


def create_icon_list():
    list = bpy.types.UILayout.bl_rna.functions['prop'].\
        parameters['icon'].items.keys()
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


class OBJECT_PT_icons(bpy.types.Panel):
    bl_space_type = "TEXT_EDITOR"
    bl_region_type = "UI"
    bl_label = "All icons"
    
    def __init__(self, x):
        self.amount = 10
        self.icon_list = create_icon_list()
    
    def draw(self, context):
        box = self.layout.box()
        
        # scroll view
        if not context.scene.icon_props.expand:
            row = box.row()
            row.prop(context.scene.icon_props, "expand",
                icon="TRIA_RIGHT", icon_only=True, emboss=False)
            row.prop(context.scene.icon_props, "scroll")

            row = box.row(align=True)
            for icon in self.icon_list[context.scene.icon_props.scroll-1:
            context.scene.icon_props.scroll-1+self.amount]:
                row.operator("wm.icon_info", text=" ", icon=icon,
                    emboss=False).icon = icon
        
        # expanded view
        else:
            row = box.row()
            row.prop(context.scene.icon_props, "expand",
                icon="TRIA_DOWN", icon_only=True, emboss=False)
            row = row.row()
            row.active = False
            row.prop(context.scene.icon_props, "scroll")

            col = box.column(align=True)
            row = col.row(align=True)
            for i, icon in enumerate(self.icon_list):
                if i % self.amount == 0:
                    row = col.row(align=True)
                row.operator("wm.icon_info", text=" ", icon=icon,
                    emboss=False).icon = icon


class CONSOLE_HT_icons(bpy.types.Header):
    bl_space_type = 'CONSOLE'
    
    def __init__(self, x):
        self.amount = 10
        self.icon_list = create_icon_list()
    
    def draw(self, context):
        # scroll view
        if context.scene.icon_props.console:
            layout = self.layout
            layout.separator()
            row = layout.row()
            row.prop(context.scene.icon_props, "scroll")
            row = layout.row(align=True)
            
            for icon in self.icon_list[context.scene.icon_props.scroll-1:
            context.scene.icon_props.scroll-1+self.amount]:
                row.operator("wm.icon_info", text="", icon=icon,
                    emboss=False).icon = icon


def menu_func(self, context):
    self.layout.prop(bpy.context.scene.icon_props, 'console')


def register():
    icons_total = len(create_icon_list())
    icons_per_row = 10
    
    bpy.types.Scene.icon_props = bpy.props.PointerProperty(type = IconProps)
    IconProps.console = bpy.props.BoolProperty(
        name='Show System Icons',
        description='Display the Icons in the console header', default=False)
    IconProps.expand = bpy.props.BoolProperty(default=False,
        description="Expand, to display all icons at once")
    IconProps.scroll = bpy.props.IntProperty(default=1, min=1,
        max=icons_total - icons_per_row + 1,
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
