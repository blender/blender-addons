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

# ----------------------------------------------------------
# Author: Antonio Vazquez (antonioya)
# ----------------------------------------------------------

# ----------------------------------------------
# Define Addon info
# ----------------------------------------------
bl_info = {
    "name": "MeasureIt",
    "author": "Antonio Vazquez (antonioya)",
    "location": "View3D > Tools Panel /Properties panel",
    "version": (1, 6, 6),
    "blender": (2, 7, 4),
    "description": "Tools for measuring objects.",
    'warning': 'Temporary: pending review fixes T48704',
    "wiki_url": "https://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/3D_interaction/Measureit",
    "category": "3D View"
    }

import sys
import os

# ----------------------------------------------
# Import modules
# ----------------------------------------------
if "bpy" in locals():
    import imp

    imp.reload(measureit_main)
    print("measureit: Reloaded multifiles")
else:
    from . import measureit_main

    print("measureit: Imported multifiles")

# noinspection PyUnresolvedReferences
import bpy
# noinspection PyUnresolvedReferences
from bpy.props import *


# --------------------------------------------------------------
# Register all operators and panels
# --------------------------------------------------------------
def register():
    bpy.utils.register_class(measureit_main.RunHintDisplayButton)
    bpy.utils.register_class(measureit_main.AddSegmentButton)
    bpy.utils.register_class(measureit_main.AddAreaButton)
    bpy.utils.register_class(measureit_main.AddSegmentOrtoButton)
    bpy.utils.register_class(measureit_main.AddAngleButton)
    bpy.utils.register_class(measureit_main.AddArcButton)
    bpy.utils.register_class(measureit_main.AddLabelButton)
    bpy.utils.register_class(measureit_main.AddNoteButton)
    bpy.utils.register_class(measureit_main.AddLinkButton)
    bpy.utils.register_class(measureit_main.AddOriginButton)
    bpy.utils.register_class(measureit_main.DeleteSegmentButton)
    bpy.utils.register_class(measureit_main.DeleteAllSegmentButton)
    bpy.utils.register_class(measureit_main.DeleteAllSumButton)
    bpy.utils.register_class(measureit_main.MeasureitEditPanel)
    bpy.utils.register_class(measureit_main.MeasureitMainPanel)
    bpy.utils.register_class(measureit_main.MeasureitConfPanel)
    bpy.utils.register_class(measureit_main.MeasureitRenderPanel)
    bpy.utils.register_class(measureit_main.RenderSegmentButton)

    # Define properties
    bpy.types.Scene.measureit_default_color = bpy.props.FloatVectorProperty(
        name="Default color",
        description="Default Color",
        default=(0.173, 0.545, 1.0, 1.0),
        min=0.1,
        max=1,
        subtype='COLOR',
        size=4)
    bpy.types.Scene.measureit_font_size = bpy.props.IntProperty(name="Text Size",
                                                                description="Default text size",
                                                                default=14, min=10, max=150)
    bpy.types.Scene.measureit_hint_space = bpy.props.FloatProperty(name='Separation', min=0, max=100, default=0.1,
                                                                   precision=3,
                                                                   description="Default distance to display measure")
    bpy.types.Scene.measureit_gl_ghost = bpy.props.BoolProperty(name="All",
                                                                description="Display measures for all objects,"
                                                                            " not only selected",
                                                                default=True)
    bpy.types.Scene.measureit_gl_txt = bpy.props.StringProperty(name="Text", maxlen=256,
                                                                description="Short description (use | for line break)")

    bpy.types.Scene.measureit_gl_precision = bpy.props.IntProperty(name='Precision', min=0, max=5, default=2,
                                                                   description="Number of decimal precision")
    bpy.types.Scene.measureit_gl_show_d = bpy.props.BoolProperty(name="ShowDist",
                                                                 description="Display distances",
                                                                 default=True)
    bpy.types.Scene.measureit_gl_show_n = bpy.props.BoolProperty(name="ShowName",
                                                                 description="Display texts",
                                                                 default=False)
    bpy.types.Scene.measureit_scale = bpy.props.BoolProperty(name="Scale",
                                                             description="Use scale factor",
                                                             default=False)
    bpy.types.Scene.measureit_scale_factor = bpy.props.FloatProperty(name='Factor', min=0.001, max=9999999,
                                                                     default=1.0,
                                                                     precision=3,
                                                                     description="Scale factor 1:x")
    bpy.types.Scene.measureit_scale_color = bpy.props.FloatVectorProperty(name="Scale color",
                                                                          description="Scale Color",
                                                                          default=(1, 1, 0, 1.0),
                                                                          min=0.1,
                                                                          max=1,
                                                                          subtype='COLOR',
                                                                          size=4)
    bpy.types.Scene.measureit_scale_font = bpy.props.IntProperty(name="Font",
                                                                 description="Text size",
                                                                 default=14, min=10, max=150)
    bpy.types.Scene.measureit_scale_pos_x = bpy.props.IntProperty(name="Position X",
                                                                  description="Margin on the X axis",
                                                                  default=5,
                                                                  min=0,
                                                                  max=100)
    bpy.types.Scene.measureit_scale_pos_y = bpy.props.IntProperty(name="Position Y",
                                                                  description="Margin on the Y axis",
                                                                  default=5,
                                                                  min=0,
                                                                  max=100)
    bpy.types.Scene.measureit_gl_scaletxt = bpy.props.StringProperty(name="ScaleText", maxlen=48,
                                                                     description="Scale title",
                                                                     default="Scale:")
    bpy.types.Scene.measureit_scale_precision = bpy.props.IntProperty(name='Precision', min=0, max=5, default=0,
                                                                      description="Number of decimal precision")

    bpy.types.Scene.measureit_ovr = bpy.props.BoolProperty(name="Override",
                                                           description="Override colors and fonts",
                                                           default=False)
    bpy.types.Scene.measureit_ovr_font = bpy.props.IntProperty(name="Font",
                                                               description="Override text size",
                                                               default=14, min=10, max=150)
    bpy.types.Scene.measureit_ovr_color = bpy.props.FloatVectorProperty(name="Override color",
                                                                        description="Override Color",
                                                                        default=(1, 0, 0, 1.0),
                                                                        min=0.1,
                                                                        max=1,
                                                                        subtype='COLOR',
                                                                        size=4)
    bpy.types.Scene.measureit_ovr_width = bpy.props.IntProperty(name='Override width', min=1, max=10, default=1,
                                                                description='override line width')

    bpy.types.Scene.measureit_units = bpy.props.EnumProperty(items=(('1', "Automatic", "Use scene units"),
                                                                    ('2', "Meters", ""),
                                                                    ('3', "Centimeters", ""),
                                                                    ('4', "Milimiters", ""),
                                                                    ('5', "Feet", ""),
                                                                    ('6', "Inches", "")),
                                                             name="Units",
                                                             default="2",
                                                             description="Units")
    bpy.types.Scene.measureit_render = bpy.props.BoolProperty(name="Render",
                                                              description="Save an image with measures over"
                                                                          " render image",
                                                              default=False)
    bpy.types.Scene.measureit_render_type = bpy.props.EnumProperty(items=(('1', "*Current", "Use current render"),
                                                                          ('2', "OpenGL", ""),
                                                                          ('3', "Animation OpenGL", ""),
                                                                          ('4', "Image", ""),
                                                                          ('5', "Animation", "")),
                                                                   name="Render type",
                                                                   description="Type of render image")
    bpy.types.Scene.measureit_sum = bpy.props.EnumProperty(items=(('99', "-", "Select a group for sum"),
                                                                  ('0', "A", ""),
                                                                  ('1', "B", ""),
                                                                  ('2', "C", ""),
                                                                  ('3', "D", ""),
                                                                  ('4', "E", ""),
                                                                  ('5', "F", ""),
                                                                  ('6', "G", ""),
                                                                  ('7', "H", ""),
                                                                  ('8', "I", ""),
                                                                  ('9', "J", ""),
                                                                  ('10', "K", ""),
                                                                  ('11', "L", ""),
                                                                  ('12', "M", ""),
                                                                  ('13', "N", ""),
                                                                  ('14', "O", ""),
                                                                  ('15', "P", ""),
                                                                  ('16', "Q", ""),
                                                                  ('17', "R", ""),
                                                                  ('18', "S", ""),
                                                                  ('19', "T", ""),
                                                                  ('20', "U", ""),
                                                                  ('21', "V", ""),
                                                                  ('22', "W", ""),
                                                                  ('23', "X", ""),
                                                                  ('24', "Y", ""),
                                                                  ('25', "Z", "")),
                                                           name="Sum in Group",
                                                           description="Add segment length in selected group")

    bpy.types.Scene.measureit_rf = bpy.props.BoolProperty(name="render_frame",
                                                          description="Add a frame in render output",
                                                          default=False)
    bpy.types.Scene.measureit_rf_color = bpy.props.FloatVectorProperty(name="Fcolor",
                                                                       description="Frame Color",
                                                                       default=(0.9, 0.9, 0.9, 1.0),
                                                                       min=0.1,
                                                                       max=1,
                                                                       subtype='COLOR',
                                                                       size=4)
    bpy.types.Scene.measureit_rf_border = bpy.props.IntProperty(name='fborder ', min=1, max=1000, default=10,
                                                                description='Frame space from border')
    bpy.types.Scene.measureit_rf_line = bpy.props.IntProperty(name='fline', min=1, max=10, default=1,
                                                              description='Line width for border')

    bpy.types.Scene.measureit_glarrow_a = bpy.props.EnumProperty(items=(('99', "--", "No arrow"),
                                                                        ('1', "Line",
                                                                         "The point of the arrow are lines"),
                                                                        ('2', "Triangle",
                                                                         "The point of the arrow is triangle"),
                                                                        ('3', "TShape",
                                                                         "The point of the arrow is a T")),
                                                                 name="A end",
                                                                 description="Add arrows to point A")
    bpy.types.Scene.measureit_glarrow_b = bpy.props.EnumProperty(items=(('99', "--", "No arrow"),
                                                                        ('1', "Line",
                                                                         "The point of the arrow are lines"),
                                                                        ('2', "Triangle",
                                                                         "The point of the arrow is triangle"),
                                                                        ('3', "TShape",
                                                                         "The point of the arrow is a T")),
                                                                 name="B end",
                                                                 description="Add arrows to point B")
    bpy.types.Scene.measureit_glarrow_s = bpy.props.IntProperty(name="Size",
                                                                description="Arrow size",
                                                                default=15, min=6, max=500)

    bpy.types.Scene.measureit_debug = bpy.props.BoolProperty(name="Debug",
                                                             description="Display information for debuging"
                                                                         " (expand/collapse for enabling or disabling)"
                                                                         " this information is only renderered for "
                                                                         "selected objects",
                                                             default=False)
    bpy.types.Scene.measureit_debug_select = bpy.props.BoolProperty(name="Selected",
                                                                    description="Display information "
                                                                                "for selected vertices/faces",
                                                                    default=False)
    bpy.types.Scene.measureit_debug_vertices = bpy.props.BoolProperty(name="Vertices",
                                                                      description="Display vertex number",
                                                                      default=True)
    bpy.types.Scene.measureit_debug_location = bpy.props.BoolProperty(name="Location",
                                                                      description="Display vertex location",
                                                                      default=False)
    bpy.types.Scene.measureit_debug_faces = bpy.props.BoolProperty(name="Faces",
                                                                   description="Display face number",
                                                                   default=False)
    bpy.types.Scene.measureit_debug_normals = bpy.props.BoolProperty(name="Normals",
                                                                     description="Display face normal "
                                                                                 "vector and creation order",
                                                                     default=False)
    bpy.types.Scene.measureit_debug_normal_details = bpy.props.BoolProperty(name="Details",
                                                                            description="Display face normal details",
                                                                            default=True)
    bpy.types.Scene.measureit_debug_font = bpy.props.IntProperty(name="Font",
                                                                 description="Debug text size",
                                                                 default=14, min=10, max=150)
    bpy.types.Scene.measureit_debug_color = bpy.props.FloatVectorProperty(name="Debug color",
                                                                          description="Debug Color",
                                                                          default=(1, 0, 0, 1.0),
                                                                          min=0.1,
                                                                          max=1,
                                                                          subtype='COLOR',
                                                                          size=4)
    bpy.types.Scene.measureit_debug_color2 = bpy.props.FloatVectorProperty(name="Debug face color",
                                                                           description="Debug face Color",
                                                                           default=(0, 1, 0, 1.0),
                                                                           min=0.1,
                                                                           max=1,
                                                                           subtype='COLOR',
                                                                           size=4)
    bpy.types.Scene.measureit_debug_color3 = bpy.props.FloatVectorProperty(name="Debug vector color",
                                                                           description="Debug vector Color",
                                                                           default=(1.0, 1.0, 0.1, 1.0),
                                                                           min=0.1,
                                                                           max=1,
                                                                           subtype='COLOR',
                                                                           size=4)
    bpy.types.Scene.measureit_debug_normal_size = bpy.props.FloatProperty(name='Len', min=0.001, max=9,
                                                                          default=0.5,
                                                                          precision=2,
                                                                          description="Normal arrow size")
    bpy.types.Scene.measureit_debug_width = bpy.props.IntProperty(name='Debug width', min=1, max=10, default=2,
                                                                  description='Vector line thickness')
    bpy.types.Scene.measureit_debug_precision = bpy.props.IntProperty(name='Precision', min=0, max=5, default=1,
                                                                      description="Number of decimal precision")

    # OpenGL flag
    wm = bpy.types.WindowManager
    # register internal property
    wm.measureit_run_opengl = bpy.props.BoolProperty(default=False)


def unregister():
    bpy.utils.unregister_class(measureit_main.RunHintDisplayButton)
    bpy.utils.unregister_class(measureit_main.AddSegmentButton)
    bpy.utils.unregister_class(measureit_main.AddAreaButton)
    bpy.utils.unregister_class(measureit_main.AddSegmentOrtoButton)
    bpy.utils.unregister_class(measureit_main.AddAngleButton)
    bpy.utils.unregister_class(measureit_main.AddArcButton)
    bpy.utils.unregister_class(measureit_main.AddLabelButton)
    bpy.utils.unregister_class(measureit_main.AddNoteButton)
    bpy.utils.unregister_class(measureit_main.AddLinkButton)
    bpy.utils.unregister_class(measureit_main.AddOriginButton)
    bpy.utils.unregister_class(measureit_main.DeleteSegmentButton)
    bpy.utils.unregister_class(measureit_main.DeleteAllSegmentButton)
    bpy.utils.unregister_class(measureit_main.DeleteAllSumButton)
    bpy.utils.unregister_class(measureit_main.MeasureitEditPanel)
    bpy.utils.unregister_class(measureit_main.MeasureitMainPanel)
    bpy.utils.unregister_class(measureit_main.MeasureitConfPanel)
    bpy.utils.unregister_class(measureit_main.MeasureitRenderPanel)
    bpy.utils.unregister_class(measureit_main.RenderSegmentButton)

    # Remove properties
    del bpy.types.Scene.measureit_default_color
    del bpy.types.Scene.measureit_font_size
    del bpy.types.Scene.measureit_hint_space
    del bpy.types.Scene.measureit_gl_ghost
    del bpy.types.Scene.measureit_gl_txt
    del bpy.types.Scene.measureit_gl_precision
    del bpy.types.Scene.measureit_gl_show_d
    del bpy.types.Scene.measureit_gl_show_n
    del bpy.types.Scene.measureit_scale
    del bpy.types.Scene.measureit_scale_factor
    del bpy.types.Scene.measureit_scale_color
    del bpy.types.Scene.measureit_scale_font
    del bpy.types.Scene.measureit_scale_pos_x
    del bpy.types.Scene.measureit_scale_pos_y
    del bpy.types.Scene.measureit_gl_scaletxt
    del bpy.types.Scene.measureit_scale_precision
    del bpy.types.Scene.measureit_ovr
    del bpy.types.Scene.measureit_ovr_font
    del bpy.types.Scene.measureit_ovr_color
    del bpy.types.Scene.measureit_ovr_width
    del bpy.types.Scene.measureit_units
    del bpy.types.Scene.measureit_render
    del bpy.types.Scene.measureit_render_type
    del bpy.types.Scene.measureit_sum
    del bpy.types.Scene.measureit_rf
    del bpy.types.Scene.measureit_rf_color
    del bpy.types.Scene.measureit_rf_border
    del bpy.types.Scene.measureit_rf_line
    del bpy.types.Scene.measureit_glarrow_a
    del bpy.types.Scene.measureit_glarrow_b
    del bpy.types.Scene.measureit_glarrow_s
    del bpy.types.Scene.measureit_debug
    del bpy.types.Scene.measureit_debug_select
    del bpy.types.Scene.measureit_debug_vertices
    del bpy.types.Scene.measureit_debug_faces
    del bpy.types.Scene.measureit_debug_normals
    del bpy.types.Scene.measureit_debug_normal_details
    del bpy.types.Scene.measureit_debug_font
    del bpy.types.Scene.measureit_debug_color
    del bpy.types.Scene.measureit_debug_color2
    del bpy.types.Scene.measureit_debug_color3
    del bpy.types.Scene.measureit_debug_normal_size
    del bpy.types.Scene.measureit_debug_width
    del bpy.types.Scene.measureit_debug_precision
    del bpy.types.Scene.measureit_debug_location

    # remove OpenGL data
    measureit_main.RunHintDisplayButton.handle_remove(measureit_main.RunHintDisplayButton, bpy.context)
    wm = bpy.context.window_manager
    p = 'measureit_run_opengl'
    if p in wm:
        del wm[p]


if __name__ == '__main__':
    register()
