# gpl author: Ryan Inch (Imaginer)

import bpy
from bpy.types import (
        Operator,
        Menu,
        )
from bpy.props import BoolProperty
from . import utils_core
from bl_ui.properties_paint_common import UnifiedPaintPanel


def get_current_brush_icon(tool):
    if utils_core.get_mode() == utils_core.sculpt:
        icons = {"BLOB": 'BRUSH_BLOB',
                "CLAY": 'BRUSH_CLAY',
                "CLAY_STRIPS": 'BRUSH_CLAY_STRIPS',
                "CREASE": 'BRUSH_CREASE',
                "DRAW": 'BRUSH_SCULPT_DRAW',
                "FILL": 'BRUSH_FILL',
                "FLATTEN": 'BRUSH_FLATTEN',
                "GRAB": 'BRUSH_GRAB',
                "INFLATE": 'BRUSH_INFLATE',
                "LAYER": 'BRUSH_LAYER',
                "MASK": 'BRUSH_MASK',
                "NUDGE": 'BRUSH_NUDGE',
                "PINCH": 'BRUSH_PINCH',
                "ROTATE": 'BRUSH_ROTATE',
                "SCRAPE": 'BRUSH_SCRAPE',
                "SIMPLIFY": 'BRUSH_SUBTRACT',
                "SMOOTH": 'BRUSH_SMOOTH',
                "SNAKE_HOOK": 'BRUSH_SNAKE_HOOK',
                "THUMB": 'BRUSH_THUMB'}

    elif utils_core.get_mode() == utils_core.vertex_paint:
        icons = {"ADD": 'BRUSH_ADD',
                "BLUR": 'BRUSH_BLUR',
                "DARKEN": 'BRUSH_DARKEN',
                "LIGHTEN": 'BRUSH_LIGHTEN',
                "MIX": 'BRUSH_MIX',
                "MUL": 'BRUSH_MULTIPLY',
                "SUB": 'BRUSH_SUBTRACT'}

    elif utils_core.get_mode() == utils_core.weight_paint:
        icons = {"ADD": 'BRUSH_ADD',
                "BLUR": 'BRUSH_BLUR',
                "DARKEN": 'BRUSH_DARKEN',
                "LIGHTEN": 'BRUSH_LIGHTEN',
                "MIX": 'BRUSH_MIX',
                "MUL": 'BRUSH_MULTIPLY',
                "SUB": 'BRUSH_SUBTRACT'}

    elif utils_core.get_mode() == utils_core.texture_paint:
        icons = {"CLONE": 'BRUSH_CLONE',
                "DRAW": 'BRUSH_TEXDRAW',
                "FILL": 'BRUSH_TEXFILL',
                "MASK": 'BRUSH_TEXMASK',
                "SMEAR": 'BRUSH_SMEAR',
                "SOFTEN": 'BRUSH_SOFTEN'}

    icon = icons[tool]

    return icon


class BrushOptionsMenu(Menu):
    bl_label = "Brush Options"
    bl_idname = "VIEW3D_MT_sv3_brush_options"

    @classmethod
    def poll(self, context):
        return utils_core.get_mode() in (
                    utils_core.sculpt, utils_core.vertex_paint,
                    utils_core.weight_paint, utils_core.texture_paint,
                    utils_core.particle_edit
                    )

    def draw_brushes(self, menu, h_brush, ico, context):
        if utils_core.addon_settings(lists=True) == 'popup' or not h_brush:
            menu.add_item().operator(
                    "view3d.sv3_brush_menu_popup", text="Brush",
                    icon=ico
                    )
        else:
            menu.add_item().menu(
                    "VIEW3D_MT_sv3_brushes_menu", text="Brush",
                    icon=ico
                    )

    def draw(self, context):
        menu = utils_core.Menu(self)

        if utils_core.get_mode() == utils_core.sculpt:
            self.sculpt(menu, context)

        elif utils_core.get_mode() in (utils_core.vertex_paint,
                                       utils_core.weight_paint):
            self.vw_paint(menu, context)

        elif utils_core.get_mode() == utils_core.texture_paint:
            self.texpaint(menu, context)

        else:
            self.particle(menu, context)

    def sculpt(self, menu, context):
        has_brush = utils_core.get_brush_link(context, types="brush")
        icons = get_current_brush_icon(has_brush.sculpt_tool) if \
                has_brush else "BRUSH_DATA"

        self.draw_brushes(menu, has_brush, icons, context)

        menu.add_item().menu(BrushRadiusMenu.bl_idname)

        if has_brush:
            # if the active brush is unlinked these menus don't do anything
            menu.add_item().menu(BrushStrengthMenu.bl_idname)
            menu.add_item().menu(BrushAutosmoothMenu.bl_idname)
            menu.add_item().menu(BrushModeMenu.bl_idname)
            menu.add_item().menu("VIEW3D_MT_sv3_texture_menu")
            menu.add_item().menu("VIEW3D_MT_sv3_stroke_options")
            menu.add_item().menu("VIEW3D_MT_sv3_brush_curve_menu")

        menu.add_item().menu("VIEW3D_MT_sv3_dyntopo")
        menu.add_item().menu("VIEW3D_MT_sv3_master_symmetry_menu")

    def vw_paint(self, menu, context):
        has_brush = utils_core.get_brush_link(context, types="brush")
        icons = get_current_brush_icon(has_brush.vertex_tool) if \
                has_brush else "BRUSH_DATA"

        if utils_core.get_mode() == utils_core.vertex_paint:
            menu.add_item().operator(ColorPickerPopup.bl_idname, icon="COLOR")
            menu.add_item().separator()

        self.draw_brushes(menu, has_brush, icons, context)

        if utils_core.get_mode() == utils_core.vertex_paint:
            menu.add_item().menu(BrushRadiusMenu.bl_idname)

            if has_brush:
                # if the active brush is unlinked these menus don't do anything
                menu.add_item().menu(BrushStrengthMenu.bl_idname)
                menu.add_item().menu(BrushModeMenu.bl_idname)
                menu.add_item().menu("VIEW3D_MT_sv3_texture_menu")
                menu.add_item().menu("VIEW3D_MT_sv3_stroke_options")
                menu.add_item().menu("VIEW3D_MT_sv3_brush_curve_menu")

        if utils_core.get_mode() == utils_core.weight_paint:
            menu.add_item().menu(BrushWeightMenu.bl_idname)
            menu.add_item().menu(BrushRadiusMenu.bl_idname)

            if has_brush:
                # if the active brush is unlinked these menus don't do anything
                menu.add_item().menu(BrushStrengthMenu.bl_idname)
                menu.add_item().menu(BrushModeMenu.bl_idname)
                menu.add_item().menu("VIEW3D_MT_sv3_stroke_options")
                menu.add_item().menu("VIEW3D_MT_sv3_brush_curve_menu")

    def texpaint(self, menu, context):
        toolsettings = context.tool_settings.image_paint

        if context.image_paint_object and not toolsettings.detect_data():
            menu.add_item().label("Missing Data", icon="INFO")
            menu.add_item().label("See Tool Shelf", icon="BACK")
        else:
            has_brush = utils_core.get_brush_link(context, types="brush")
            if has_brush and has_brush.image_tool in {'DRAW', 'FILL'} and \
               has_brush.blend not in {'ERASE_ALPHA', 'ADD_ALPHA'}:
                menu.add_item().operator(ColorPickerPopup.bl_idname, icon="COLOR")
                menu.add_item().separator()

            icons = get_current_brush_icon(has_brush.image_tool) if \
                    has_brush else "BRUSH_DATA"

            self.draw_brushes(menu, has_brush, icons, context)

            if has_brush:
                # if the active brush is unlinked these menus don't do anything
                if has_brush and has_brush.image_tool in {'MASK'}:
                    menu.add_item().menu(BrushWeightMenu.bl_idname, text="Mask Value")

                if has_brush and has_brush.image_tool not in {'FILL'}:
                    menu.add_item().menu(BrushRadiusMenu.bl_idname)

                menu.add_item().menu(BrushStrengthMenu.bl_idname)

                if has_brush and has_brush.image_tool in {'DRAW'}:
                    menu.add_item().menu(BrushModeMenu.bl_idname)

                menu.add_item().menu("VIEW3D_MT_sv3_texture_menu")
                menu.add_item().menu("VIEW3D_MT_sv3_stroke_options")
                menu.add_item().menu("VIEW3D_MT_sv3_brush_curve_menu")

            menu.add_item().menu("VIEW3D_MT_sv3_master_symmetry_menu")

    def particle(self, menu, context):
        if context.tool_settings.particle_edit.tool == 'NONE':
            menu.add_item().label("No Brush Selected", icon="INFO")
            menu.add_item().separator()
            menu.add_item().menu("VIEW3D_MT_sv3_brushes_menu",
                                text="Select Brush", icon="BRUSH_DATA")
        else:
            menu.add_item().menu("VIEW3D_MT_sv3_brushes_menu",
                                icon="BRUSH_DATA")
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


class BrushRadiusMenu(Menu):
    bl_label = "Radius"
    bl_idname = "VIEW3D_MT_sv3_brush_radius_menu"
    bl_description = "Change the size of the brushes"

    def init(self, context):
        if utils_core.get_mode() == utils_core.particle_edit:
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
        menu = utils_core.Menu(self)

        # add the top slider
        menu.add_item().prop(proppath, "size", slider=True)
        menu.add_item().separator()

        # add the rest of the menu items
        for i in range(len(settings)):
            utils_core.menuprop(
                    menu.add_item(), settings[i][0], settings[i][1],
                    datapath, icon='RADIOBUT_OFF', disable=True,
                    disable_icon='RADIOBUT_ON'
                    )


class BrushStrengthMenu(Menu):
    bl_label = "Strength"
    bl_idname = "VIEW3D_MT_sv3_brush_strength_menu"

    def init(self, context):
        settings = [["1.0", 1.0],
                    ["0.7", 0.7],
                    ["0.5", 0.5],
                    ["0.3", 0.3],
                    ["0.2", 0.2],
                    ["0.1", 0.1]]

        proppath = utils_core.get_brush_link(context, types="brush")

        if utils_core.get_mode() == utils_core.sculpt:
            datapath = "tool_settings.sculpt.brush.strength"

        elif utils_core.get_mode() == utils_core.vertex_paint:
            datapath = "tool_settings.vertex_paint.brush.strength"

        elif utils_core.get_mode() == utils_core.weight_paint:
            datapath = "tool_settings.weight_paint.brush.strength"

        elif utils_core.get_mode() == utils_core.texture_paint:
            datapath = "tool_settings.image_paint.brush.strength"

        else:
            datapath = "tool_settings.particle_edit.brush.strength"
            proppath = context.tool_settings.particle_edit.brush

        return settings, datapath, proppath

    def draw(self, context):
        settings, datapath, proppath = self.init(context)
        menu = utils_core.Menu(self)

        # add the top slider
        if proppath:
            menu.add_item().prop(proppath, "strength", slider=True)
            menu.add_item().separator()

            # add the rest of the menu items
            for i in range(len(settings)):
                utils_core.menuprop(
                        menu.add_item(), settings[i][0], settings[i][1],
                        datapath, icon='RADIOBUT_OFF', disable=True,
                        disable_icon='RADIOBUT_ON'
                        )
        else:
            menu.add_item().label("No brushes available", icon="INFO")


class BrushModeMenu(Menu):
    bl_label = "Brush Mode"
    bl_idname = "VIEW3D_MT_sv3_brush_mode_menu"

    def init(self):
        has_brush = utils_core.get_brush_link(bpy.context, types="brush")

        if utils_core.get_mode() == utils_core.sculpt:
            enum = has_brush.bl_rna.properties['sculpt_plane'].enum_items if \
                   has_brush else None
            path = "tool_settings.sculpt.brush.sculpt_plane"

        elif utils_core.get_mode() == utils_core.texture_paint:
            enum = has_brush.bl_rna.properties['blend'].enum_items if \
                   has_brush else None
            path = "tool_settings.image_paint.brush.blend"

        else:
            enum = has_brush.bl_rna.properties['vertex_tool'].enum_items if \
                   has_brush else None
            path = "tool_settings.vertex_paint.brush.vertex_tool"

        return enum, path

    def draw(self, context):
        enum, path = self.init()
        menu = utils_core.Menu(self)
        colum_n = utils_core.addon_settings(lists=False)

        menu.add_item().label(text="Brush Mode")
        menu.add_item().separator()

        if enum:
            if utils_core.get_mode() == utils_core.texture_paint:
                column_flow = menu.add_item("column_flow", columns=colum_n)

                # add all the brush modes to the menu
                for brush in enum:
                    utils_core.menuprop(
                            menu.add_item(parent=column_flow), brush.name,
                            brush.identifier, path, icon='RADIOBUT_OFF',
                            disable=True, disable_icon='RADIOBUT_ON'
                            )
            else:
                # add all the brush modes to the menu
                for brush in enum:
                    utils_core.menuprop(
                            menu.add_item(), brush.name,
                            brush.identifier, path, icon='RADIOBUT_OFF',
                            disable=True, disable_icon='RADIOBUT_ON'
                            )
        else:
            menu.add_item().label("No brushes available", icon="INFO")


class BrushAutosmoothMenu(Menu):
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
        menu = utils_core.Menu(self)
        has_brush = utils_core.get_brush_link(context, types="brush")

        if has_brush:
            # add the top slider
            menu.add_item().prop(has_brush, "auto_smooth_factor", slider=True)
            menu.add_item().separator()

            # add the rest of the menu items
            for i in range(len(settings)):
                utils_core.menuprop(
                        menu.add_item(), settings[i][0], settings[i][1],
                        "tool_settings.sculpt.brush.auto_smooth_factor",
                        icon='RADIOBUT_OFF', disable=True,
                        disable_icon='RADIOBUT_ON'
                        )
        else:
            menu.add_item().label("No Smooth options available", icon="INFO")


class BrushWeightMenu(Menu):
    bl_label = "Weight"
    bl_idname = "VIEW3D_MT_sv3_brush_weight_menu"

    def draw(self, context):
        if utils_core.get_mode() == utils_core.weight_paint:
            brush = context.tool_settings.unified_paint_settings
            brushstr = "tool_settings.unified_paint_settings.weight"
            name = "Weight"
        else:
            brush = context.tool_settings.image_paint.brush
            brushstr = "tool_settings.image_paint.brush.weight"
            name = "Mask Value"

        menu = utils_core.Menu(self)
        settings = [["1.0", 1.0],
                    ["0.7", 0.7],
                    ["0.5", 0.5],
                    ["0.3", 0.3],
                    ["0.2", 0.2],
                    ["0.1", 0.1]]
        if brush:
            # add the top slider
            menu.add_item().prop(brush,
                                 "weight", text=name, slider=True)
            menu.add_item().separator()

            # add the rest of the menu items
            for i in range(len(settings)):
                utils_core.menuprop(
                        menu.add_item(), settings[i][0], settings[i][1],
                        brushstr,
                        icon='RADIOBUT_OFF', disable=True,
                        disable_icon='RADIOBUT_ON'
                        )
        else:
            menu.add_item().label("No brush available", icon="INFO")


class ParticleCountMenu(Menu):
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
        menu = utils_core.Menu(self)

        # add the top slider
        menu.add_item().prop(context.tool_settings.particle_edit.brush,
                             "count", slider=True)
        menu.add_item().separator()

        # add the rest of the menu items
        for i in range(len(settings)):
            utils_core.menuprop(
                    menu.add_item(), settings[i][0], settings[i][1],
                    "tool_settings.particle_edit.brush.count",
                    icon='RADIOBUT_OFF', disable=True,
                    disable_icon='RADIOBUT_ON'
                    )


class ParticleLengthMenu(Menu):
    bl_label = "Length Mode"
    bl_idname = "VIEW3D_MT_sv3_particle_length_menu"

    def draw(self, context):
        menu = utils_core.Menu(self)
        path = "tool_settings.particle_edit.brush.length_mode"

        # add the menu items
        for item in context.tool_settings.particle_edit.brush. \
          bl_rna.properties['length_mode'].enum_items:
            utils_core.menuprop(
                    menu.add_item(), item.name, item.identifier, path,
                    icon='RADIOBUT_OFF',
                    disable=True,
                    disable_icon='RADIOBUT_ON'
                    )


class ParticlePuffMenu(Menu):
    bl_label = "Puff Mode"
    bl_idname = "VIEW3D_MT_sv3_particle_puff_menu"

    def draw(self, context):
        menu = utils_core.Menu(self)
        path = "tool_settings.particle_edit.brush.puff_mode"

        # add the menu items
        for item in context.tool_settings.particle_edit.brush. \
          bl_rna.properties['puff_mode'].enum_items:
            utils_core.menuprop(
                    menu.add_item(), item.name, item.identifier, path,
                    icon='RADIOBUT_OFF',
                    disable=True,
                    disable_icon='RADIOBUT_ON'
                    )


class FlipColorsAll(Operator):
    bl_label = "Flip Colors"
    bl_idname = "view3d.sv3_flip_colors_all"
    bl_description = "Switch between Foreground and Background colors"

    is_tex = BoolProperty(
                default=False,
                options={'HIDDEN'}
                )

    def execute(self, context):
        try:
            if self.is_tex is False:
                color = context.tool_settings.vertex_paint.brush.color
                secondary_color = context.tool_settings.vertex_paint.brush.secondary_color

                orig_prim = color.hsv
                orig_sec = secondary_color.hsv

                color.hsv = orig_sec
                secondary_color.hsv = orig_prim
            else:
                bpy.ops.paint.brush_colors_flip()

            return {'FINISHED'}

        except Exception as e:
            utils_core.error_handlers(self, "view3d.sv3_flip_colors_all", e,
                                     "Flip Colors could not be completed")

            return {'CANCELLED'}


class ColorPickerPopup(Operator):
    bl_label = "Color"
    bl_idname = "view3d.sv3_color_picker_popup"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(self, context):
        return utils_core.get_mode() in (
                        utils_core.vertex_paint,
                        utils_core.texture_paint
                        )

    def check(self, context):
        return True

    def draw(self, context):
        menu = utils_core.Menu(self)

        if utils_core.get_mode() == utils_core.texture_paint:
            settings = context.tool_settings.image_paint
            brush = getattr(settings, "brush", None)
        else:
            settings = context.tool_settings.vertex_paint
            brush = settings.brush
            brush = getattr(settings, "brush", None)

        if brush:
            menu.add_item().template_color_picker(brush, "color", value_slider=True)
            menu.add_item("row", align=True).prop(brush, "color", text="")
            menu.current_item.prop(brush, "secondary_color", text="")

            if utils_core.get_mode() == utils_core.vertex_paint:
                menu.current_item.operator(
                                FlipColorsAll.bl_idname,
                                icon='FILE_REFRESH', text=""
                                ).is_tex = False
            else:
                menu.current_item.operator(
                                FlipColorsAll.bl_idname,
                                icon='FILE_REFRESH', text=""
                                ).is_tex = True

            if settings.palette:
                menu.add_item("column").template_palette(settings, "palette", color=True)

            menu.add_item().template_ID(settings, "palette", new="palette.new")
        else:
            menu.add_item().label("No brushes currently available", icon="INFO")

            return

    def execute(self, context):
        return context.window_manager.invoke_popup(self, width=180)


class BrushMenuPopup(Operator):
    bl_label = "Color"
    bl_idname = "view3d.sv3_brush_menu_popup"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(self, context):
        return utils_core.get_mode() in (
                        utils_core.vertex_paint,
                        utils_core.texture_paint,
                        utils_core.sculpt,
                        utils_core.weight_paint
                        )

    def check(self, context):
        return True

    def draw(self, context):
        layout = self.layout
        settings = UnifiedPaintPanel.paint_settings(context)
        colum_n = utils_core.addon_settings(lists=False)

        if utils_core.addon_settings(lists=True) != 'popup':
            layout.label(text="Seems no active brush", icon="INFO")
            layout.label(text="in the Tool Shelf", icon="BACK")

        layout.template_ID_preview(settings, "brush",
                                   new="brush.add", rows=3, cols=colum_n)

    def execute(self, context):
        return context.window_manager.invoke_popup(self, width=180)
