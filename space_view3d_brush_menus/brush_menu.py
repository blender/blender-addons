from bpy.props import *
from .Utils.core import *

def get_current_brush_icon(tool):
    if get_mode() == sculpt:
        icons = {"BLOB":'BRUSH_BLOB',
                "CLAY":'BRUSH_CLAY',
                "CLAY_STRIPS":'BRUSH_CLAY_STRIPS',
                "CREASE":'BRUSH_CREASE',
                "DRAW":'BRUSH_SCULPT_DRAW',
                "FILL":'BRUSH_FILL',
                "FLATTEN":'BRUSH_FLATTEN',
                "GRAB":'BRUSH_GRAB',
                "INFLATE":'BRUSH_INFLATE',
                "LAYER":'BRUSH_LAYER',
                "MASK":'BRUSH_MASK',
                "NUDGE":'BRUSH_NUDGE',
                "PINCH":'BRUSH_PINCH',
                "ROTATE":'BRUSH_ROTATE',
                "SCRAPE":'BRUSH_SCRAPE',
                "SIMPLIFY":'BRUSH_SUBTRACT',
                "SMOOTH":'BRUSH_SMOOTH',
                "SNAKE_HOOK":'BRUSH_SNAKE_HOOK',
                "THUMB":'BRUSH_THUMB'}

    elif get_mode() == vertex_paint:
        icons = {"ADD":'BRUSH_ADD',
                "BLUR":'BRUSH_BLUR',
                "DARKEN":'BRUSH_DARKEN',
                "LIGHTEN":'BRUSH_LIGHTEN',
                "MIX":'BRUSH_MIX',
                "MUL":'BRUSH_MULTIPLY',
                "SUB":'BRUSH_SUBTRACT'}

    elif get_mode() == weight_paint:
        icons = {"ADD":'BRUSH_ADD',
                "BLUR":'BRUSH_BLUR',
                "DARKEN":'BRUSH_DARKEN',
                "LIGHTEN":'BRUSH_LIGHTEN',
                "MIX":'BRUSH_MIX',
                "MUL":'BRUSH_MULTIPLY',
                "SUB":'BRUSH_SUBTRACT'}

    elif get_mode() == texture_paint:
        icons = {"CLONE":'BRUSH_CLONE',
                "DRAW":'BRUSH_TEXDRAW',
                "FILL":'BRUSH_TEXFILL',
                "MASK":'BRUSH_TEXMASK',
                "SMEAR":'BRUSH_SMEAR',
                "SOFTEN":'BRUSH_SOFTEN'}
                
    icon = icons[tool]

    return icon

class BrushOptionsMenu(bpy.types.Menu):
    bl_label = "Brush Options"
    bl_idname = "VIEW3D_MT_sv3_brush_options"

    @classmethod
    def poll(self, context):
        if get_mode() in [sculpt, vertex_paint, weight_paint, texture_paint, particle_edit]:
            return True
        else:
            return False

    def draw(self, context):
        menu = Menu(self)

        if get_mode() == sculpt:
            self.sculpt(menu, context)

        elif get_mode() in [vertex_paint, weight_paint]:
            self.vw_paint(menu, context)

        elif get_mode() == texture_paint:
            self.texpaint(menu, context)

        else:
            self.particle(menu, context)

    def sculpt(self, menu, context):
        menu.add_item().menu("VIEW3D_MT_Brush_Selection1", text="Brush", icon=get_current_brush_icon(context.tool_settings.sculpt.brush.sculpt_tool))
        menu.add_item().menu(BrushRadiusMenu.bl_idname)
        menu.add_item().menu(BrushStrengthMenu.bl_idname)
        menu.add_item().menu(BrushAutosmoothMenu.bl_idname)
        menu.add_item().menu(BrushModeMenu.bl_idname)
        menu.add_item().menu("VIEW3D_MT_sv3_texture_menu")
        menu.add_item().menu("VIEW3D_MT_sv3_stroke_options")
        menu.add_item().menu("VIEW3D_MT_sv3_brush_curve_menu")
        menu.add_item().menu("VIEW3D_MT_sv3_dyntopo")
        menu.add_item().menu("VIEW3D_MT_sv3_master_symmetry_menu")
        
    def vw_paint(self, menu, context):
        if get_mode() == vertex_paint:
            menu.add_item().operator(ColorPickerPopup.bl_idname, icon="COLOR")
            menu.add_item().separator()
            menu.add_item().menu("VIEW3D_MT_Brush_Selection1", text="Brush", icon=get_current_brush_icon(context.tool_settings.vertex_paint.brush.vertex_tool))
            menu.add_item().menu(BrushRadiusMenu.bl_idname)
            menu.add_item().menu(BrushStrengthMenu.bl_idname)
            menu.add_item().menu(BrushModeMenu.bl_idname)
            menu.add_item().menu("VIEW3D_MT_sv3_texture_menu")
            menu.add_item().menu("VIEW3D_MT_sv3_stroke_options")
            menu.add_item().menu("VIEW3D_MT_sv3_brush_curve_menu")
        if get_mode() == weight_paint:
            menu.add_item().menu("VIEW3D_MT_Brush_Selection1", text="Brush", icon=get_current_brush_icon(context.tool_settings.vertex_paint.brush.vertex_tool))
            menu.add_item().menu(BrushWeightMenu.bl_idname)
            menu.add_item().menu(BrushRadiusMenu.bl_idname)
            menu.add_item().menu(BrushStrengthMenu.bl_idname)
            menu.add_item().menu(BrushModeMenu.bl_idname)
            menu.add_item().menu("VIEW3D_MT_sv3_stroke_options")
            menu.add_item().menu("VIEW3D_MT_sv3_brush_curve_menu")

    def texpaint(self, menu, context):
        toolsettings = context.tool_settings.image_paint
        
        if context.image_paint_object and not toolsettings.detect_data():
            menu.add_item().label("Missing Data", icon='ERROR')
            menu.add_item().label("See Tool Shelf")
        else:
            if toolsettings.brush.image_tool in {'DRAW', 'FILL'} and \
               toolsettings.brush.blend not in {'ERASE_ALPHA', 'ADD_ALPHA'}:
                menu.add_item().operator(ColorPickerPopup.bl_idname, icon="COLOR")
                menu.add_item().separator()
                
            menu.add_item().menu("VIEW3D_MT_Brush_Selection1", text="Brush", icon=get_current_brush_icon(toolsettings.brush.image_tool))

            if toolsettings.brush.image_tool in {'MASK'}:
                menu.add_item().menu(BrushWeightMenu.bl_idname, text="Mask Value")
            
            if toolsettings.brush.image_tool not in {'FILL'}:
                menu.add_item().menu(BrushRadiusMenu.bl_idname)
                
            menu.add_item().menu(BrushStrengthMenu.bl_idname)
                
            if toolsettings.brush.image_tool in {'DRAW'}:
                menu.add_item().menu(BrushModeMenu.bl_idname)
            menu.add_item().menu("VIEW3D_MT_sv3_texture_menu")
            menu.add_item().menu("VIEW3D_MT_sv3_stroke_options")
            menu.add_item().menu("VIEW3D_MT_sv3_brush_curve_menu")
            menu.add_item().menu("VIEW3D_MT_sv3_master_symmetry_menu")


    def particle(self, menu, context):
        if context.tool_settings.particle_edit.tool == 'NONE':
            menu.add_item().label("No Brush Selected")
            menu.add_item().menu("VIEW3D_MT_sv3_brushes_menu", text="Select Brush")
        else:
            menu.add_item().menu("VIEW3D_MT_sv3_brushes_menu")
            menu.add_item().menu(BrushRadiusMenu.bl_idname)
            if context.tool_settings.particle_edit.tool != 'ADD':
                menu.add_item().menu(BrushStrengthMenu.bl_idname)

            else:
                menu.add_item().menu(ParticleCountMenu.bl_idname)
                menu.add_item().separator()
                menu.add_item().prop(context.tool_settings.particle_edit,
                                     "use_default_interpolate", toggle=True)

                menu.add_item().prop(context.tool_settings.particle_edit.brush,
                                     "steps", slider=True)
                menu.add_item().prop(context.tool_settings.particle_edit,
                                     "default_key_count", slider=True)

            if context.tool_settings.particle_edit.tool == 'LENGTH':
                menu.add_item().separator()
                menu.add_item().menu(ParticleLengthMenu.bl_idname)

            if context.tool_settings.particle_edit.tool == 'PUFF':
                menu.add_item().separator()
                menu.add_item().menu(ParticlePuffMenu.bl_idname)
                menu.add_item().prop(context.tool_settings.particle_edit.brush,
                                     "use_puff_volume", toggle=True)


class BrushRadiusMenu(bpy.types.Menu):
    bl_label = "Radius"
    bl_idname = "VIEW3D_MT_sv3_brush_radius_menu"

    def init(self, context):
        if get_mode() == particle_edit:
            settings = [["100", 100],
                        ["70", 70],
                        ["50", 50],
                        ["30", 30],
                        ["20", 20],
                        ["10", 10]]
                        
            datapath = "tool_settings.particle_edit.brush.size"
            proppath = context.tool_settings.particle_edit.brush

        else:
            settings = [["200", 200],
                        ["150", 150],
                        ["100", 100],
                        ["50", 50],
                        ["35", 35],
                        ["10", 10]]
                        
            datapath = "tool_settings.unified_paint_settings.size"
            proppath = context.tool_settings.unified_paint_settings

        return settings, datapath, proppath

    def draw(self, context):
        settings, datapath, proppath = self.init(context)
        menu = Menu(self)

        # add the top slider
        menu.add_item().prop(proppath, "size", slider=True)
        menu.add_item().separator()

        # add the rest of the menu items
        for i in range(len(settings)):
            menuprop(menu.add_item(), settings[i][0], settings[i][1],
                     datapath, icon='RADIOBUT_OFF', disable=True,
                     disable_icon='RADIOBUT_ON')


class BrushStrengthMenu(bpy.types.Menu):
    bl_label = "Strength"
    bl_idname = "VIEW3D_MT_sv3_brush_strength_menu"

    def init(self, context):
        settings = [["1.0", 1.0],
                    ["0.7", 0.7],
                    ["0.5", 0.5],
                    ["0.3", 0.3],
                    ["0.2", 0.2],
                    ["0.1", 0.1]]

        if get_mode() == sculpt:
            datapath = "tool_settings.sculpt.brush.strength"
            proppath = context.tool_settings.sculpt.brush

        elif get_mode() == vertex_paint:
            datapath = "tool_settings.vertex_paint.brush.strength"
            proppath = context.tool_settings.vertex_paint.brush

        elif get_mode() == weight_paint:
            datapath = "tool_settings.weight_paint.brush.strength"
            proppath = context.tool_settings.weight_paint.brush

        elif get_mode() == texture_paint:
            datapath = "tool_settings.image_paint.brush.strength"
            proppath = context.tool_settings.image_paint.brush

        else:
            datapath = "tool_settings.particle_edit.brush.strength"
            proppath = context.tool_settings.particle_edit.brush

        return settings, datapath, proppath

    def draw(self, context):
        settings, datapath, proppath = self.init(context)
        menu = Menu(self)

        # add the top slider
        menu.add_item().prop(proppath, "strength", slider=True)
        menu.add_item().separator()

        # add the rest of the menu items
        for i in range(len(settings)):
            menuprop(menu.add_item(), settings[i][0], settings[i][1],
                     datapath, icon='RADIOBUT_OFF', disable=True,
                     disable_icon='RADIOBUT_ON')


class BrushModeMenu(bpy.types.Menu):
    bl_label = "Brush Mode"
    bl_idname = "VIEW3D_MT_sv3_brush_mode_menu"

    def init(self):
        if get_mode() == sculpt:
            enum = bpy.context.tool_settings.sculpt.brush.bl_rna.properties['sculpt_plane'].enum_items
            path = "tool_settings.sculpt.brush.sculpt_plane"

        elif get_mode() == texture_paint:
            enum = bpy.context.tool_settings.image_paint.brush.bl_rna.properties['blend'].enum_items
            path = "tool_settings.image_paint.brush.blend"

        else:
            enum = bpy.context.tool_settings.vertex_paint.brush.bl_rna.properties['vertex_tool'].enum_items
            path = "tool_settings.vertex_paint.brush.vertex_tool"

        return enum, path

    def draw(self, context):
        enum, path = self.init()
        menu = Menu(self)

        menu.add_item().label(text="Brush Mode")
        menu.add_item().separator()

        if get_mode() == texture_paint:
            column_flow = menu.add_item("column_flow", columns=2)

            # add all the brush modes to the menu
            for brush in enum:
                menuprop(menu.add_item(parent=column_flow), brush.name,
                         brush.identifier, path, icon='RADIOBUT_OFF',
                         disable=True, disable_icon='RADIOBUT_ON')

        else:
            # add all the brush modes to the menu
            for brush in enum:
                menuprop(menu.add_item(), brush.name,
                         brush.identifier, path, icon='RADIOBUT_OFF',
                         disable=True, disable_icon='RADIOBUT_ON')


class BrushAutosmoothMenu(bpy.types.Menu):
    bl_label = "Autosmooth"
    bl_idname = "VIEW3D_MT_sv3_brush_autosmooth_menu"

    def init(self):
        settings = [["1.0", 1.0],
                    ["0.7", 0.7],
                    ["0.5", 0.5],
                    ["0.3", 0.3],
                    ["0.2", 0.2],
                    ["0.1", 0.1]]

        return settings

    def draw(self, context):
        settings = self.init()
        menu = Menu(self)

        # add the top slider
        menu.add_item().prop(context.tool_settings.sculpt.brush,
                             "auto_smooth_factor", slider=True)
        menu.add_item().separator()

        # add the rest of the menu items
        for i in range(len(settings)):
            menuprop(menu.add_item(), settings[i][0], settings[i][1],
                     "tool_settings.sculpt.brush.auto_smooth_factor",
                     icon='RADIOBUT_OFF', disable=True,
                     disable_icon='RADIOBUT_ON')


class BrushWeightMenu(bpy.types.Menu):
    bl_label = "Weight"
    bl_idname = "VIEW3D_MT_sv3_brush_weight_menu"

    def draw(self, context):
        if get_mode() == weight_paint:
            brush = context.tool_settings.unified_paint_settings
            brushstr = "tool_settings.unified_paint_settings.weight"
            name = "Weight"
        else:
            brush = context.tool_settings.image_paint.brush
            brushstr = "tool_settings.image_paint.brush.weight"
            name = "Mask Value"
        
        menu = Menu(self)
        settings = [["1.0", 1.0],
                    ["0.7", 0.7],
                    ["0.5", 0.5],
                    ["0.3", 0.3],
                    ["0.2", 0.2],
                    ["0.1", 0.1]]

        # add the top slider
        menu.add_item().prop(brush,
                             "weight", text=name, slider=True)
        menu.add_item().separator()

        # add the rest of the menu items
        for i in range(len(settings)):
            menuprop(menu.add_item(), settings[i][0], settings[i][1],
                     brushstr,
                     icon='RADIOBUT_OFF', disable=True,
                     disable_icon='RADIOBUT_ON')


class ParticleCountMenu(bpy.types.Menu):
    bl_label = "Count"
    bl_idname = "VIEW3D_MT_sv3_particle_count_menu"

    def init(self):
        settings = [["50", 50],
                    ["25", 25],
                    ["10", 10],
                    ["5", 5],
                    ["3", 3],
                    ["1", 1]]

        return settings

    def draw(self, context):
        settings = self.init()
        menu = Menu(self)

        # add the top slider
        menu.add_item().prop(context.tool_settings.particle_edit.brush,
                             "count", slider=True)
        menu.add_item().separator()

        # add the rest of the menu items
        for i in range(len(settings)):
            menuprop(menu.add_item(), settings[i][0], settings[i][1],
                     "tool_settings.particle_edit.brush.count",
                     icon='RADIOBUT_OFF', disable=True,
                     disable_icon='RADIOBUT_ON')


class ParticleLengthMenu(bpy.types.Menu):
    bl_label = "Length Mode"
    bl_idname = "VIEW3D_MT_sv3_particle_length_menu"

    def draw(self, context):
        menu = Menu(self)
        path = "tool_settings.particle_edit.brush.length_mode"

        # add the menu items
        for item in context.tool_settings.particle_edit.brush.bl_rna.properties['length_mode'].enum_items:
            menuprop(menu.add_item(), item.name, item.identifier, path,
                     icon='RADIOBUT_OFF',
                     disable=True, 
                     disable_icon='RADIOBUT_ON')

class ParticlePuffMenu(bpy.types.Menu):
    bl_label = "Puff Mode"
    bl_idname = "VIEW3D_MT_sv3_particle_puff_menu"

    def draw(self, context):
        menu = Menu(self)
        path = "tool_settings.particle_edit.brush.puff_mode"

        # add the menu items
        for item in context.tool_settings.particle_edit.brush.bl_rna.properties['puff_mode'].enum_items:
            menuprop(menu.add_item(), item.name, item.identifier, path,
                     icon='RADIOBUT_OFF',
                     disable=True, 
                     disable_icon='RADIOBUT_ON')

class FlipColorsTex(bpy.types.Operator):
    bl_label = "Flip Colors"
    bl_idname = "view3d.sv3_flip_colors_tex"

    def execute(self, context):
        try:
            bpy.ops.paint.brush_colors_flip()
        except:
            pass

        return {'FINISHED'}
    
class FlipColorsVert(bpy.types.Operator):
    bl_label = "Flip Colors"
    bl_idname = "view3d.sv3_flip_colors_vert"
    
    def execute(self, context):
        color = context.tool_settings.vertex_paint.brush.color
        secondary_color = context.tool_settings.vertex_paint.brush.secondary_color
        
        orig_prim = color.hsv
        orig_sec = secondary_color.hsv
        
        color.hsv = orig_sec
        secondary_color.hsv = orig_prim
        
        return {'FINISHED'}

class ColorPickerPopup(bpy.types.Operator):
    bl_label = "Color"
    bl_idname = "view3d.sv3_color_picker_popup"
    bl_options = {'REGISTER'}

    def check(self, context):
        return True
    
    def draw(self, context):
        menu = Menu(self)

        if get_mode() == texture_paint:
            settings = context.tool_settings.image_paint
            brush = settings.brush

        else:
            settings = context.tool_settings.vertex_paint
            brush = settings.brush

        menu.add_item().template_color_picker(brush, "color", value_slider=True)
        menu.add_item().prop(brush, "color", text="")
        menu.current_item.prop(brush, "secondary_color", text="")
        if get_mode() == vertex_paint:
            menu.current_item.operator(FlipColorsVert.bl_idname, icon='FILE_REFRESH', text="")
        else:
            menu.current_item.operator(FlipColorsTex.bl_idname, icon='FILE_REFRESH', text="")

        if settings.palette:
            menu.add_item("column").template_palette(settings, "palette", color=True)
        
        menu.add_item().template_ID(settings, "palette", new="palette.new")
        
    def execute(self, context):
        return context.window_manager.invoke_popup(self, width=180)


### ------------ New hotkeys and registration ------------ ###

addon_keymaps = []


def register():
    wm = bpy.context.window_manager
    modes = ['Sculpt', 'Vertex Paint', 'Weight Paint', 'Image Paint', 'Particle']

    for mode in modes:
        km = wm.keyconfigs.addon.keymaps.new(name=mode)
        kmi = km.keymap_items.new('wm.call_menu', 'V', 'PRESS', alt=True)
        kmi.properties.name = "VIEW3D_MT_sv3_brush_options"
        addon_keymaps.append((km, kmi))


def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
