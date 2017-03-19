from bpy.props import *
from .Utils.core import *

airbrush = 'AIRBRUSH'
anchored = 'ANCHORED'
space = 'SPACE'
drag_dot = 'DRAG_DOT'
dots = 'DOTS'
line = 'LINE'
curve = 'CURVE'


class StrokeOptionsMenu(bpy.types.Menu):
    bl_label = "Stroke Options"
    bl_idname = "VIEW3D_MT_sv3_stroke_options"

    @classmethod
    def poll(self, context):
        if get_mode() in [sculpt, vertex_paint, weight_paint, texture_paint, particle_edit]:
            return True
        else:
            return False

    def init(self):
        if get_mode() == sculpt:
            settings = bpy.context.tool_settings.sculpt
            brush = settings.brush

            if bpy.app.version > (2, 71):
                stroke_method = brush.stroke_method

            else:
                stroke_method = brush.sculpt_stroke_method

        elif get_mode() == texture_paint:
            settings = bpy.context.tool_settings.image_paint
            brush = settings.brush
            stroke_method = brush.stroke_method

        else:
            settings = bpy.context.tool_settings.vertex_paint
            brush = settings.brush
            stroke_method = brush.stroke_method

        return settings, brush, stroke_method

    def draw(self, context):
        settings, brush, stroke_method = self.init()
        menu = Menu(self)

        menu.add_item().menu(StrokeMethodMenu.bl_idname)

        menu.add_item().separator()

        if stroke_method == space:
            menu.add_item().prop(brush, "spacing", text=PIW+"Spacing", slider=True)

        elif stroke_method == airbrush:
            menu.add_item().prop(brush, "rate", text=PIW+"Rate", slider=True)

        elif stroke_method == anchored:
                menu.add_item().prop(brush, "use_edge_to_edge")
                
        else:
            pass

        if get_mode() == sculpt and stroke_method in [drag_dot, anchored]:
            pass
        else:
            menu.add_item().prop(brush, "jitter", text=PIW+"Jitter", slider=True)

        menu.add_item().prop(settings, "input_samples", text=PIW+"Input Samples", slider=True)
        
        if stroke_method in [dots, space, airbrush]:
            menu.add_item().separator()

            menu.add_item().prop(brush, "use_smooth_stroke", toggle=True)

            if brush.use_smooth_stroke:
                menu.add_item().prop(brush, "smooth_stroke_radius", text=PIW+"Radius", slider=True)
                menu.add_item().prop(brush, "smooth_stroke_factor", text=PIW+"Factor", slider=True)


class StrokeMethodMenu(bpy.types.Menu):
    bl_label = "Stroke Method"
    bl_idname = "VIEW3D_MT_sv3_stroke_method"

    def init(self):
        if get_mode() == sculpt:
            brush = bpy.context.tool_settings.sculpt.brush
            path = "tool_settings.sculpt.brush.stroke_method"

        elif get_mode() == texture_paint:
            brush = bpy.context.tool_settings.image_paint.brush
            path = "tool_settings.image_paint.brush.stroke_method"

        else:
            brush = bpy.context.tool_settings.vertex_paint.brush
            path = "tool_settings.vertex_paint.brush.stroke_method"

        return brush, path

    def draw(self, context):
        brush, path = self.init()
        menu = Menu(self)

        menu.add_item().label(text="Stroke Method")
        menu.add_item().separator()

        # add the menu items dynamicaly based on values in enum property
        for tool in brush.bl_rna.properties['stroke_method'].enum_items:
            if tool.identifier in [anchored, drag_dot] and get_mode() in [vertex_paint, weight_paint]:
                continue
                
            menuprop(menu.add_item(), tool.name, tool.identifier, path,
                     icon='RADIOBUT_OFF', disable=True,
                     disable_icon='RADIOBUT_ON')
