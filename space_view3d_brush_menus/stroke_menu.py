# gpl author: Ryan Inch (Imaginer)

import bpy
from bpy.types import Menu
from . import utils_core

airbrush = 'AIRBRUSH'
anchored = 'ANCHORED'
space = 'SPACE'
drag_dot = 'DRAG_DOT'
dots = 'DOTS'
line = 'LINE'
curve = 'CURVE'


class StrokeOptionsMenu(Menu):
    bl_label = "Stroke Options"
    bl_idname = "VIEW3D_MT_sv3_stroke_options"

    @classmethod
    def poll(self, context):
        return utils_core.get_mode() in (
                    utils_core.sculpt, utils_core.vertex_paint,
                    utils_core.weight_paint, utils_core.texture_paint,
                    utils_core.particle_edit
                    )

    def init(self):
        has_brush = utils_core.get_brush_link(bpy.context, types="brush")
        if utils_core.get_mode() == utils_core.sculpt:
            settings = bpy.context.tool_settings.sculpt

        elif utils_core.get_mode() == utils_core.texture_paint:
            settings = bpy.context.tool_settings.image_paint

        else:
            settings = bpy.context.tool_settings.vertex_paint

        stroke_method = has_brush.stroke_method if has_brush else None

        return settings, has_brush, stroke_method

    def draw(self, context):
        settings, brush, stroke_method = self.init()
        menu = utils_core.Menu(self)

        menu.add_item().menu(StrokeMethodMenu.bl_idname)
        menu.add_item().separator()

        if stroke_method:
            if stroke_method == space and brush:
                menu.add_item().prop(brush, "spacing",
                                     text=utils_core.PIW + "Spacing", slider=True)

            elif stroke_method == airbrush and brush:
                menu.add_item().prop(brush, "rate",
                                    text=utils_core.PIW + "Rate", slider=True)

            elif stroke_method == anchored and brush:
                menu.add_item().prop(brush, "use_edge_to_edge")

            else:
                pass

            if utils_core.get_mode() == utils_core.sculpt and stroke_method in (drag_dot, anchored):
                pass
            else:
                if brush:
                    menu.add_item().prop(brush, "jitter",
                                        text=utils_core.PIW + "Jitter", slider=True)

            menu.add_item().prop(settings, "input_samples",
                                text=utils_core.PIW + "Input Samples", slider=True)

            if stroke_method in [dots, space, airbrush] and brush:
                menu.add_item().separator()

                menu.add_item().prop(brush, "use_smooth_stroke", toggle=True)

                if brush.use_smooth_stroke:
                    menu.add_item().prop(brush, "smooth_stroke_radius",
                                        text=utils_core.PIW + "Radius", slider=True)
                    menu.add_item().prop(brush, "smooth_stroke_factor",
                                        text=utils_core.PIW + "Factor", slider=True)
        else:
            menu.add_item().label("No Stroke Options available", icon="INFO")


class StrokeMethodMenu(Menu):
    bl_label = "Stroke Method"
    bl_idname = "VIEW3D_MT_sv3_stroke_method"

    def init(self):
        has_brush = utils_core.get_brush_link(bpy.context, types="brush")
        if utils_core.get_mode() == utils_core.sculpt:
            path = "tool_settings.sculpt.brush.stroke_method"

        elif utils_core.get_mode() == utils_core.texture_paint:
            path = "tool_settings.image_paint.brush.stroke_method"

        else:
            path = "tool_settings.vertex_paint.brush.stroke_method"

        return has_brush, path

    def draw(self, context):
        brush, path = self.init()
        menu = utils_core.Menu(self)

        menu.add_item().label(text="Stroke Method")
        menu.add_item().separator()

        if brush:
            # add the menu items dynamicaly based on values in enum property
            for tool in brush.bl_rna.properties['stroke_method'].enum_items:
                if tool.identifier in [anchored, drag_dot] and \
                   utils_core.get_mode() in [utils_core.vertex_paint,
                                             utils_core.weight_paint]:
                    continue

                utils_core.menuprop(
                        menu.add_item(), tool.name, tool.identifier, path,
                        icon='RADIOBUT_OFF', disable=True,
                        disable_icon='RADIOBUT_ON'
                        )
        else:
            menu.add_item().label("No Stroke Method available", icon="INFO")
