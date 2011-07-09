# paint_palette.py (c) 2011 Dany Lebel (Axon_D)
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
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****


bl_info = {
    "name": "Paint Palettes",
    "author": "Dany Lebel (Axon D)",
    "version": (0,8,2),
    "blender": (2, 5, 7),
    "api": 36826,
    "location": "Image Editor and 3D View > Any Paint mode > Color Palette or Weight Palette panel",
    "description": "Palettes for color and weight paint modes",
    "warning": "beta",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/Paint/Palettes",
    "tracker_url": "http://projects.blender.org/tracker/index.php?func=detail&aid=25908",
    "category": "Paint"}

"""
This addon brings palettes to the paint modes.

    * Color Palette for Image Painting, Texture Paint and Vertex Paint modes.
    * Weight Palette for the Weight Paint mode.

Set a number of colors (or weights according to the mode) and then associate it
with the brush by using the button under the color.
"""

import bpy
from bpy.props import *


class AddPresetBase():
    '''Base preset class, only for subclassing
    subclasses must define
     - preset_values
     - preset_subdir '''
    # bl_idname = "script.preset_base_add"
    # bl_label = "Add a Python Preset"
    bl_options = {'REGISTER'}  # only because invoke_props_popup requires.

    name = bpy.props.StringProperty(name="Name",
        description="Name of the preset, used to make the path name",
        maxlen=64, default="")
    remove_active = bpy.props.BoolProperty(default=False, options={'HIDDEN'})

    @staticmethod
    def as_filename(name):  # could reuse for other presets
        for char in " !@#$%^&*(){}:\";'[]<>,.\\/?":
            name = name.replace(char, '_')
        return name.lower().strip()

    def execute(self, context):
        import os

        if hasattr(self, "pre_cb"):
            self.pre_cb(context)

        preset_menu_class = getattr(bpy.types, self.preset_menu)

        if not self.remove_active:

            if not self.name:
                return {'FINISHED'}

            filename = self.as_filename(self.name)

            target_path = bpy.utils.user_resource('SCRIPTS',
                os.path.join("presets", self.preset_subdir), create=True)

            if not target_path:
                self.report({'WARNING'}, "Failed to create presets path")
                return {'CANCELLED'}

            filepath = os.path.join(target_path, filename) + ".py"

            if hasattr(self, "add"):
                self.add(context, filepath)
            else:
                file_preset = open(filepath, 'w')
                file_preset.write("import bpy\n")

                if hasattr(self, "preset_defines"):
                    for rna_path in self.preset_defines:
                        exec(rna_path)
                        file_preset.write("%s\n" % rna_path)
                    file_preset.write("\n")


                for rna_path in self.preset_values:
                    value = eval(rna_path)
                    # convert thin wrapped sequences to simple lists to repr()
                    try:
                        value = value[:]
                    except:
                        pass

                    file_preset.write("%s = %r\n" % (rna_path, value))
                file_preset.write("\
ci = bpy.context.window_manager.palette_props.current_color_index\n\
palette_props = bpy.context.window_manager.palette_props\n\
image_paint = bpy.context.tool_settings.image_paint\n\
vertex_paint = bpy.context.tool_settings.vertex_paint\n\
if ci == 0:\n\
    image_paint.brush.color = palette_props.color_0\n\
    vertex_paint.brush.color = palette_props.color_0\n\
elif ci == 1:\n\
    image_paint.brush.color = palette_props.color_1\n\
    vertex_paint.brush.color = palette_props.color_1\n\
elif ci == 2:\n\
    image_paint.brush.color = palette_props.color_2\n\
    vertex_paint.brush.color = palette_props.color_2\n\
elif ci == 3:\n\
    image_paint.brush.color = palette_props.color_3\n\
    vertex_paint.brush.color = palette_props.color_3\n\
elif ci == 4:\n\
    image_paint.brush.color = palette_props.color_4\n\
    vertex_paint.brush.color = palette_props.color_4\n\
elif ci == 5:\n\
    image_paint.brush.color = palette_props.color_5\n\
    vertex_paint.brush.color = palette_props.color_5\n\
elif ci == 6:\n\
    image_paint.brush.color = palette_props.color_6\n\
    vertex_paint.brush.color = palette_props.color_6\n\
elif ci == 7:\n\
    image_paint.brush.color = palette_props.color_7\n\
    vertex_paint.brush.color = palette_props.color_7\n\
elif ci == 8:\n\
    image_paint.brush.color = palette_props.color_8\n\
    vertex_paint.brush.color = palette_props.color_8")

                file_preset.close()

            preset_menu_class.bl_label = bpy.path.display_name(filename)

        else:
            preset_active = preset_menu_class.bl_label

            # fairly sloppy but convenient.
            filepath = bpy.utils.preset_find(preset_active, self.preset_subdir)

            if not filepath:
                filepath = bpy.utils.preset_find(preset_active,
                    self.preset_subdir, display_name=True)

            if not filepath:
                return {'CANCELLED'}

            if hasattr(self, "remove"):
                self.remove(context, filepath)
            else:
                try:
                    os.remove(filepath)
                except:
                    import traceback
                    traceback.print_exc()

            # XXX, stupid!
            preset_menu_class.bl_label = "Presets"

        if hasattr(self, "post_cb"):
            self.post_cb(context)

        return {'FINISHED'}

    def check(self, context):
        self.name = self.as_filename(self.name)

    def invoke(self, context, event):
        if not self.remove_active:
            wm = context.window_manager
            return wm.invoke_props_dialog(self)
        else:
            return self.execute(context)

class ExecutePalettePreset(bpy.types.Operator):
    ''' Executes a preset '''
    bl_idname = "script.execute_preset"
    bl_label = "Execute a Python Preset"

    filepath = bpy.props.StringProperty(name="Path",
        description="Path of the Python file to execute",
        maxlen=512, default="")
    menu_idname = bpy.props.StringProperty(name="Menu ID Name",
        description="ID name of the menu this was called from", default="")

    def execute(self, context):
        from os.path import basename
        filepath = self.filepath

        # change the menu title to the most recently chosen option
        preset_class = getattr(bpy.types, self.menu_idname)
        preset_class.bl_label = bpy.path.display_name(basename(filepath))

        # execute the preset using script.python_file_run
        bpy.ops.script.python_file_run(filepath=filepath)
        return {'FINISHED'}


class PALETTE_MT_palette_presets(bpy.types.Menu):
    bl_label = "Palette Presets"
    preset_subdir = "palette"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


class AddPresetPalette(AddPresetBase, bpy.types.Operator):
    '''Add a Palette Preset'''
    bl_idname = "palette.preset_add"
    bl_label = "Add Palette Preset"
    preset_menu = "PALETTE_MT_palette_presets"

    preset_defines = [
        "window_manager = bpy.context.window_manager"
    ]

    preset_values = [
        "window_manager.palette_props.color_0",
        "window_manager.palette_props.color_1",
        "window_manager.palette_props.color_2",
        "window_manager.palette_props.color_3",
        "window_manager.palette_props.color_4",
        "window_manager.palette_props.color_5",
        "window_manager.palette_props.color_6",
        "window_manager.palette_props.color_7",
        "window_manager.palette_props.color_8",
        
    ]

    preset_subdir = "palette"


class BrushButtonsPanel():
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'

    @classmethod
    def poll(cls, context):
        sima = context.space_data
        toolsettings = context.tool_settings.image_paint
        return sima.show_paint and toolsettings.brush

class IMAGE_OT_select_color(bpy.types.Operator):
    bl_label = ""
    bl_description = "Select this color"
    bl_idname = "paint.select_color"
    
    
    color_index = IntProperty()
    
    def invoke(self, context, event):
        palette_props = bpy.context.window_manager.palette_props
        palette_props.current_color_index = self.color_index
        
        if self.color_index == 0:
            color = palette_props.color_0
        elif self.color_index == 1:
            color = palette_props.color_1
        elif self.color_index == 2:
            color = palette_props.color_2
        elif self.color_index == 3:
            color = palette_props.color_3
        elif self.color_index == 4:
            color = palette_props.color_4
        elif self.color_index == 5:
            color = palette_props.color_5
        elif self.color_index == 6:
            color = palette_props.color_6
        elif self.color_index == 7:
            color = palette_props.color_7
        elif self.color_index == 8:
            color = palette_props.color_8
        elif self.color_index == 9:
            color = palette_props.color_9
        
        bpy.context.tool_settings.image_paint.brush.color = color
        bpy.context.tool_settings.vertex_paint.brush.color = color
        return {"FINISHED"}




def color_palette_draw(self, context):
    palette_props = bpy.context.window_manager.palette_props
    
    
    layout = self.layout

    row = layout.row(align=True)
    row.menu("PALETTE_MT_palette_presets", text=bpy.types.PALETTE_MT_palette_presets.bl_label)
    row.operator("palette.preset_add", text="", icon="ZOOMIN")
    row.operator("palette.preset_add", text="", icon="ZOOMOUT").remove_active = True
    
    
    if context.vertex_paint_object:
        brush = context.tool_settings.vertex_paint.brush
    elif context.image_paint_object:
        brush = context.tool_settings.image_paint.brush
    elif context.space_data.use_image_paint:
        brush = context.tool_settings.image_paint.brush
    
    
    for i in range(0, 9):
        if not i % 3:
            row = layout.row()
        
        
        
        if i == palette_props.current_color_index:
            
            if i == 0:
                palette_props.color_0 = brush.color[:]
            elif i == 1:
                palette_props.color_1 = brush.color[:]
            elif i == 2:
                palette_props.color_2 = brush.color[:]
            elif i == 3:
                palette_props.color_3 = brush.color[:]
            elif i == 4:
                palette_props.color_4 = brush.color[:]
            elif i == 5:
                palette_props.color_5 = brush.color[:]
            elif i == 6:
                palette_props.color_6 = brush.color[:]
            elif i == 7:
                palette_props.color_7 = brush.color[:]
            elif i == 8:
                palette_props.color_8 = brush.color[:]
            col = row.column()
            col.prop(brush, "color", text="")
            col.operator("paint.select_color",
                         icon="COLOR", emboss=False).color_index = i
        
        else :
            col = row.column(align=True)
            col.prop(palette_props, "color_%d" % i)
            col.operator("paint.select_color"
                         ).color_index = i
        
        

class IMAGE_PT_color_palette(BrushButtonsPanel, bpy.types.Panel):
    bl_label = "Color Palette"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        color_palette_draw(self, context)
        

class PaintPanel():
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    @staticmethod
    def paint_settings(context):
        ts = context.tool_settings

        if context.vertex_paint_object:
            return ts.vertex_paint
        elif context.weight_paint_object:
            return ts.weight_paint
        elif context.texture_paint_object:
            return ts.image_paint
        return None


class VIEW3D_PT_color_palette(PaintPanel, bpy.types.Panel):
    bl_label = "Color Palette"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.image_paint_object or context.vertex_paint_object)

    def draw(self, context):
        color_palette_draw(self, context)


class VIEW3D_OT_select_weight(bpy.types.Operator):
    bl_label = ""
    bl_description = "Select this weight"
    bl_idname = "paint.select_weight"
    
    weight_index = IntProperty()
    
    def invoke(self, context, event):
        palette_props = bpy.context.window_manager.palette_props
        palette_props.current_weight_index = self.weight_index
        
        if self.weight_index == 0:
            weight = palette_props.weight_0
        elif self.weight_index == 1:
            weight = palette_props.weight_1
        elif self.weight_index == 2:
            weight = palette_props.weight_2
        elif self.weight_index == 3:
            weight = palette_props.weight_3
        elif self.weight_index == 4:
            weight = palette_props.weight_4
        elif self.weight_index == 5:
            weight = palette_props.weight_5
        elif self.weight_index == 6:
            weight = palette_props.weight_6
        elif self.weight_index == 7:
            weight = palette_props.weight_7
        elif self.weight_index == 8:
            weight = palette_props.weight_8
        elif self.weight_index == 9:
            weight = palette_props.weight_9
        elif self.weight_index == 10:
            weight = palette_props.weight_10
        
        bpy.context.tool_settings.vertex_group_weight = weight
        return {"FINISHED"}


class VIEW3D_OT_reset_weight_palette(bpy.types.Operator):
    bl_label = ""
    bl_idname = "paint.reset_weight_palette"
    
    def execute(self, context):
        palette_props = context.window_manager.palette_props
        
        
        if palette_props.current_weight_index == 0:
            print("coucou!")
            context.tool_settings.vertex_group_weight = 0.0
        palette_props.weight_0 = 0.0
        
        palette_props.weight_1 = 0.1
        if palette_props.current_weight_index == 1:
            context.tool_settings.vertex_group_weight = 0.1
        
        if palette_props.current_weight_index == 2:
            context.tool_settings.vertex_group_weight = 0.25
        palette_props.weight_2 = 0.25
        
        if palette_props.current_weight_index == 3:
            context.tool_settings.vertex_group_weight = 0.3333
        palette_props.weight_3 = 0.3333
        
        if palette_props.current_weight_index == 4:
            context.tool_settings.vertex_group_weight = 0.4
        palette_props.weight_4 = 0.4
        
        if palette_props.current_weight_index == 5:
            context.tool_settings.vertex_group_weight = 0.5
        palette_props.weight_5 = 0.5
        
        if palette_props.current_weight_index == 6:
            context.tool_settings.vertex_group_weight = 0.6
        palette_props.weight_6 = 0.6
        
        if palette_props.current_weight_index == 7:
            context.tool_settings.vertex_group_weight = 0.6666
        palette_props.weight_7 = 0.6666
        
        if palette_props.current_weight_index == 8:
            context.tool_settings.vertex_group_weight = 0.75
        palette_props.weight_8 = 0.75
        
        if palette_props.current_weight_index == 9:
            context.tool_settings.vertex_group_weight = 0.9
        palette_props.weight_9 = 0.9
        
        if palette_props.current_weight_index == 10:
            context.tool_settings.vertex_group_weight = 1.0
        palette_props.weight_10 = 1.0
        return {"FINISHED"}

class VIEW3D_PT_weight_palette(PaintPanel, bpy.types.Panel):
    bl_label = "Weight Palette"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.weight_paint_object
    
    def draw(self, context):
        palette_props = bpy.context.window_manager.palette_props
        vertex_group_weight = bpy.context.tool_settings.vertex_group_weight
        
        
        
        layout = self.layout
        
        box = layout.box()
        
        row = box.row()
        if palette_props.current_weight_index == 0:
            palette_props.weight_0 = vertex_group_weight
            row.operator("paint.select_weight", text="%.2f" % palette_props.weight_0,
                     emboss=False).weight_index = 0
        else :
            row.operator("paint.select_weight", text="%.2f" % palette_props.weight_0,
                     emboss=True).weight_index = 0
        
        row = box.row(align=True)
        if palette_props.current_weight_index == 1:
            palette_props.weight_1 = vertex_group_weight
            row.operator("paint.select_weight", text="%.2f" % palette_props.weight_1,
                     emboss=False).weight_index = 1
        else :
            row.operator("paint.select_weight", text="%.2f" % palette_props.weight_1,
                     emboss=True).weight_index = 1
        
        if palette_props.current_weight_index == 2:
            palette_props.weight_2 = vertex_group_weight
            row.operator("paint.select_weight", text="%.2f" % palette_props.weight_2,
                     emboss=False).weight_index = 2
        else :
            row.operator("paint.select_weight", text="%.2f" % palette_props.weight_2,
                     emboss=True).weight_index = 2
        
        if palette_props.current_weight_index == 3:
            palette_props.weight_3 = vertex_group_weight
            row.operator("paint.select_weight", text="%.2f" % palette_props.weight_3,
                     emboss=False).weight_index = 3
        else :
            row.operator("paint.select_weight", text="%.2f" % palette_props.weight_3,
                     emboss=True).weight_index = 3
        
        row = box.row(align=True)
        
        if palette_props.current_weight_index == 4:
            palette_props.weight_4 = vertex_group_weight
            row.operator("paint.select_weight", text="%.2f" % palette_props.weight_4,
                     emboss=False).weight_index = 4
        else :
            row.operator("paint.select_weight", text="%.2f" % palette_props.weight_4,
                     emboss=True).weight_index = 4
        
        if palette_props.current_weight_index == 5:
            palette_props.weight_5 = vertex_group_weight
            row.operator("paint.select_weight", text="%.2f" % palette_props.weight_5,
                     emboss=False).weight_index = 5
        else :
            row.operator("paint.select_weight", text="%.2f" % palette_props.weight_5,
                     emboss=True).weight_index = 5
        
        if palette_props.current_weight_index == 6:
            palette_props.weight_6 = vertex_group_weight
            row.operator("paint.select_weight", text="%.2f" % palette_props.weight_6,
                     emboss=False).weight_index = 6
        else :
            row.operator("paint.select_weight", text="%.2f" % palette_props.weight_6,
                     emboss=True).weight_index = 6

        row = box.row(align=True)
        
        if palette_props.current_weight_index == 7:
            palette_props.weight_7 = vertex_group_weight
            row.operator("paint.select_weight", text="%.2f" % palette_props.weight_7,
                     emboss=False).weight_index = 7
        else :
            row.operator("paint.select_weight", text="%.2f" % palette_props.weight_7,
                     emboss=True).weight_index = 7
        
        if palette_props.current_weight_index == 8:
            palette_props.weight_8 = vertex_group_weight
            row.operator("paint.select_weight", text="%.2f" % palette_props.weight_8,
                     emboss=False).weight_index = 8
        else :
            row.operator("paint.select_weight", text="%.2f" % palette_props.weight_8,
                     emboss=True).weight_index = 8
        
        if palette_props.current_weight_index == 9:
            palette_props.weight_9 = vertex_group_weight
            row.operator("paint.select_weight", text="%.2f" % palette_props.weight_9,
                     emboss=False).weight_index = 9
        else :
            row.operator("paint.select_weight", text="%.2f" % palette_props.weight_9,
                     emboss=True).weight_index = 9
        
        row = box.row()
        
        if palette_props.current_weight_index == 10:
            palette_props.weight_10 = vertex_group_weight
            row.operator("paint.select_weight", text="%.2f" % palette_props.weight_10,
                     emboss=False).weight_index = 10
        else :
            row.operator("paint.select_weight", text="%.2f" % palette_props.weight_10,
                     emboss=True).weight_index = 10
        
        row = layout.row()
        row.operator("paint.reset_weight_palette", text="Reset")


def register():
    
    class Colors(bpy.types.PropertyGroup):
        """Class for colors CollectionProperty"""
        color = bpy.props.FloatVectorProperty(
            name="", description="", default=(0.8, 0.8, 0.8), min=0, max=1,
            step=1, precision=3, subtype='COLOR_GAMMA', size=3)
    
    
    class PaletteProps(bpy.types.PropertyGroup):
        current_color_index = IntProperty(
            name="Current Color Index", description="", default=0, min=-1)
    
        current_weight_index = IntProperty(
            name="Current Color Index", description="", default=10, min=-1)
        
        # Collection of colors
        colors = bpy.props.CollectionProperty(type=Colors)
        
        color_0 = bpy.props.FloatVectorProperty(
            name="", description="", default=(0.8, 0.8, 0.8), min=0, max=1,
            step=1, precision=3, subtype='COLOR_GAMMA', size=3)
        color_1 = bpy.props.FloatVectorProperty(
            name="", description="", default=(0.8, 0.8, 0.8), min=0, max=1,
            step=1, precision=3, subtype='COLOR_GAMMA', size=3)
        color_2 = bpy.props.FloatVectorProperty(
            name="", description="", default=(0.8, 0.8, 0.8), min=0, max=1,
            step=1, precision=3, subtype='COLOR_GAMMA', size=3)
        color_3 = bpy.props.FloatVectorProperty(
            name="", description="", default=(0.8, 0.8, 0.8), min=0, max=1,
            step=1, precision=3, subtype='COLOR_GAMMA', size=3)
        color_4 = bpy.props.FloatVectorProperty(
            name="", description="", default=(0.8, 0.8, 0.8), min=0, max=1,
            step=1, precision=3, subtype='COLOR_GAMMA', size=3)
        color_5 = bpy.props.FloatVectorProperty(
            name="", description="", default=(0.8, 0.8, 0.8), min=0, max=1,
            step=1, precision=3, subtype='COLOR_GAMMA', size=3)
        color_6 = bpy.props.FloatVectorProperty(
            name="", description="", default=(0.8, 0.8, 0.8), min=0, max=1,
            step=1, precision=3, subtype='COLOR_GAMMA', size=3)
        color_7 = bpy.props.FloatVectorProperty(
            name="", description="", default=(0.8, 0.8, 0.8), min=0, max=1,
            step=1, precision=3, subtype='COLOR_GAMMA', size=3)
        color_8 = bpy.props.FloatVectorProperty(
            name="", description="", default=(0.8, 0.8, 0.8), min=0, max=1,
            step=1, precision=3, subtype='COLOR_GAMMA', size=3)
        
        
        weight_0 = bpy.props.FloatProperty(
            default=0.0, min=0.0, max=1.0, precision=3)
        weight_1 = bpy.props.FloatProperty(
            default=0.1, min=0.0, max=1.0, precision=3)
        weight_2 = bpy.props.FloatProperty(
            default=0.25, min=0.0, max=1.0, precision=3)
        weight_3 = bpy.props.FloatProperty(
            default=0.333, min=0.0, max=1.0, precision=3)
        weight_4 = bpy.props.FloatProperty(
            default=0.4, min=0.0, max=1.0, precision=3)
        weight_5 = bpy.props.FloatProperty(
            default=0.5, min=0.0, max=1.0, precision=3)
        weight_6 = bpy.props.FloatProperty(
            default=0.6, min=0.0, max=1.0, precision=3)
        weight_7 = bpy.props.FloatProperty(
            default=0.6666, min=0.0, max=1.0, precision=3)
        weight_8 = bpy.props.FloatProperty(
            default=0.75, min=0.0, max=1.0, precision=3)
        weight_9 = bpy.props.FloatProperty(
            default=0.9, min=0.0, max=1.0, precision=3)
        weight_10 = bpy.props.FloatProperty(
            default=1.0, min=0.0, max=1.0, precision=3)
        pass
    
    
            
    
    
    bpy.utils.register_module(__name__)
    
    bpy.types.WindowManager.palette_props = PointerProperty(
            type=PaletteProps, name="Palette Props", description="")
    

    for i in range(0, 256):
        colors = bpy.context.window_manager.palette_props.colors.add()
    
    pass
    
    
def unregister():
    bpy.utils.unregister_module(__name__)
    pass


if __name__ == "__main__":
    register()
