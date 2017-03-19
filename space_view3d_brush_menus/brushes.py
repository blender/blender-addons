from bpy.props import *
from .Utils.core import *


 
class BrushesMenu(bpy.types.Menu):
    bl_label = "Brush"
    bl_idname = "VIEW3D_MT_sv3_brushes_menu"

    def init(self):
        if get_mode() == sculpt:
            datapath = "tool_settings.sculpt.brush"
            icon = {"BLOB": 'BRUSH_BLOB',
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

        elif get_mode() == vertex_paint:
            datapath = "tool_settings.vertex_paint.brush"
            icon = {"ADD": 'BRUSH_ADD',
                    "BLUR": 'BRUSH_BLUR',
                    "DARKEN": 'BRUSH_DARKEN',
                    "LIGHTEN": 'BRUSH_LIGHTEN',
                    "MIX": 'BRUSH_MIX',
                    "MUL": 'BRUSH_MULTIPLY',
                    "SUB": 'BRUSH_SUBTRACT'}

        elif get_mode() == weight_paint:
            datapath = "tool_settings.weight_paint.brush"
            icon = {"ADD": 'BRUSH_ADD',
                    "BLUR": 'BRUSH_BLUR',
                    "DARKEN": 'BRUSH_DARKEN',
                    "LIGHTEN": 'BRUSH_LIGHTEN',
                    "MIX": 'BRUSH_MIX',
                    "MUL": 'BRUSH_MULTIPLY',
                    "SUB": 'BRUSH_SUBTRACT'}

        elif get_mode() == texture_paint:
            datapath = "tool_settings.image_paint.brush"
            icon = {"CLONE": 'BRUSH_CLONE',
                    "DRAW": 'BRUSH_TEXDRAW',
                    "FILL": 'BRUSH_TEXFILL',
                    "MASK": 'BRUSH_TEXMASK',
                    "SMEAR": 'BRUSH_SMEAR',
                    "SOFTEN": 'BRUSH_SOFTEN'}

        elif get_mode() == particle_edit:
            datapath = "tool_settings.particle_edit.tool"
            icon = None

        else:
            datapath = ""

        return datapath, icon

    def draw(self, context):
        datapath, icon = self.init()
        menu = Menu(self)

        menu.add_item().label(text="Brush")
        menu.add_item().separator()

        current_brush = eval("bpy.context.{}".format(datapath))

        # get the current brush's name
        if current_brush and get_mode() != particle_edit:
            current_brush = current_brush.name

        if get_mode() == particle_edit:
            particle_tools = [["None", 'NONE'],
                              ["Comb", 'COMB'],
                              ["Smooth", 'SMOOTH'],
                              ["Add", 'ADD'],
                              ["Length", 'LENGTH'],
                              ["Puff", 'PUFF'],
                              ["Cut", 'CUT'],
                              ["Weight", 'WEIGHT']]

            # if you are in particle edit mode add the menu items for particle mode
            for tool in particle_tools:
                menuprop(menu.add_item(), tool[0], tool[1], datapath,
                         icon='RADIOBUT_OFF', disable=True,
                         disable_icon='RADIOBUT_ON')

        else:
            # iterate over all the brushes
            for item in bpy.data.brushes:
                if get_mode() == sculpt:
                    if item.use_paint_sculpt:
                        # if you are in sculpt mode and the brush is a sculpt brush add the brush to the menu
                        menuprop(menu.add_item(), item.name,
                                 'bpy.data.brushes["%s"]' % item.name,
                                 datapath, icon=icon[item.sculpt_tool],
                                 disable=True, custom_disable_exp=[item.name, current_brush],
                                 path=True)

                if get_mode() == vertex_paint:
                    if item.use_paint_vertex:
                        # if you are in vertex paint mode and the brush is a vertex paint brush add the brush to the menu
                        menuprop(menu.add_item(), item.name,
                                 'bpy.data.brushes["%s"]' % item.name,
                                 datapath, icon=icon[item.vertex_tool],
                                 disable=True, custom_disable_exp=[item.name, current_brush],
                                 path=True)

                if get_mode() == weight_paint:
                    if item.use_paint_weight:
                        # if you are in weight paint mode and the brush is a weight paint brush add the brush to the menu
                        menuprop(menu.add_item(), item.name,
                                 'bpy.data.brushes["%s"]' % item.name,
                                 datapath, icon=icon[item.vertex_tool],
                                 disable=True, custom_disable_exp=[item.name, current_brush],
                                 path=True)

                if get_mode() == texture_paint:
                    if item.use_paint_image:
                        # if you are in texture paint mode and the brush is a texture paint brush add the brush to the menu
                        menuprop(menu.add_item(), item.name,
                                 'bpy.data.brushes["%s"]' % item.name,
                                 datapath, icon=icon[item.image_tool],
                                 disable=True, custom_disable_exp=[item.name, current_brush],
                                 path=True)
