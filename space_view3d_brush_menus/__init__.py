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
# Modified by Meta-Androcto


""" Copyright 2011 GPL licence applies"""

bl_info = {
    "name": "Sculpt/Paint Brush Menus",
    "description": "Fast access to brushes & tools in Sculpt and Paint Modes",
    "author": "Ryan Inch (Imaginer)",
    "version": (1, 1, 3),
    "blender": (2, 7, 8),
    "location": "Alt V in Sculpt/Paint Modes",
    "warning": '',  # used for warning icon and text in addons panel
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/3D_interaction/Advanced_UI_Menus",
    "category": "3D View"}

import sys
import os
from bl_ui.properties_paint_common import (
        UnifiedPaintPanel,
        brush_texture_settings,
        brush_texpaint_common,
        brush_mask_texture_settings,
        )
from .Utils.core import *

from . import brush_menu
from . import brushes
from . import curve_menu
from . import dyntopo_menu
from . import stroke_menu
from . import symmetry_menu
from . import texture_menu

# Use compact brushes menus #
def UseBrushesLists():
    # separate function just for more convience
    useLists = bpy.context.user_preferences.addons[__name__].preferences.use_brushes_lists

    return bool(useLists)

class VIEW3D_MT_Brush_Selection1(bpy.types.Menu):
    bl_label = "Brush Tool"

    def draw(self, context):
        layout = self.layout
        settings = UnifiedPaintPanel.paint_settings(context)

        # check if brush exists (for instance, in paint mode before adding a slot)
        if hasattr(settings, 'brush'):
            brush = settings.brush
        else:
            brush = None

        if not brush:
            return

        if not context.particle_edit_object:
            if UseBrushesLists():
                flow = layout.column_flow(columns=3)

                for brsh in bpy.data.brushes:
                    if (context.sculpt_object and brsh.use_paint_sculpt):
                        props = flow.operator("wm.context_set_id", text=brsh.name,
                                              icon_value=layout.icon(brsh))
                        props.data_path = "tool_settings.sculpt.brush"
                        props.value = brsh.name
                    elif (context.image_paint_object and brsh.use_paint_image):
                        props = flow.operator("wm.context_set_id", text=brsh.name,
                                              icon_value=layout.icon(brsh))
                        props.data_path = "tool_settings.image_paint.brush"
                        props.value = brsh.name
                    elif (context.vertex_paint_object and brsh.use_paint_vertex):
                        props = flow.operator("wm.context_set_id", text=brsh.name,
                                              icon_value=layout.icon(brsh))
                        props.data_path = "tool_settings.vertex_paint.brush"
                        props.value = brsh.name
                    elif (context.weight_paint_object and brsh.use_paint_weight):
                        props = flow.operator("wm.context_set_id", text=brsh.name,
                                              icon_value=layout.icon(brsh))
                        props.data_path = "tool_settings.weight_paint.brush"
                        props.value = brsh.name
            else:
                layout.template_ID_preview(settings, "brush", new="brush.add", rows=3, cols=8)


class VIEW3D_MT_Brushes_Pref(bpy.types.AddonPreferences):
    bl_idname = __name__


    use_brushes_lists = bpy.props.BoolProperty(
        name="Use compact menus for brushes",
        default=True,
        description=("Use more compact menus instead  \n"
                     "of thumbnails for displaying brushes")
    )

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, "use_brushes_lists")

def register():
    # register all blender classes
    bpy.utils.register_module(__name__)
    
    # register brush menu
    brush_menu.register()

def unregister():
    # unregister brush menu
    brush_menu.unregister()
    
    # delete all the properties you have created
    del_props()
    
    # unregister all blender classes
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
