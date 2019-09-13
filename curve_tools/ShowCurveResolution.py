# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and / or
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
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110 - 1301, USA.
#
# ##### END GPL LICENSE BLOCK #####
#


# LOAD MODUL #
import bpy
from bpy import *
from bpy.props import *
from bpy.types import AddonPreferences, PropertyGroup

import bgl
import blf
import gpu
from gpu_extras.batch import batch_for_shader

import math
import mathutils
from mathutils import Vector
from mathutils.geometry import interpolate_bezier

import bpy_extras
from bpy_extras.view3d_utils import location_3d_to_region_2d as loc3d2d

 
 
def get_points(spline):

    bezier_points = spline.bezier_points

    if len(bezier_points) < 2: 
        return []

    r = spline.resolution_u + 1
    segments = len(bezier_points)
    
    if not spline.use_cyclic_u:
        segments -= 1
 
    point_list = []
    for i in range(segments):
        inext = (i + 1) % len(bezier_points)
 
        bezier_points1 = bezier_points[i].co
        handle1 = bezier_points[i].handle_right
        handle2 = bezier_points[inext].handle_left
        bezier_points2 = bezier_points[inext].co
        
        bezier = bezier_points1, handle1, handle2, bezier_points2, r
        points = interpolate_bezier(*bezier)
        point_list.extend(points)
 
    return point_list
 
def draw(self, context, spline, curve_vertcolor):
    
    points = get_points(spline)
    
    shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'POINTS', {"pos": points})
    
    shader.bind()
    shader.uniform_float("color", curve_vertcolor)
    batch.draw(shader)


class ShowCurveResolution(bpy.types.Operator):
    bl_idname = "curve.show_resolution"
    bl_label = "Show Curve Resolution"
    bl_description = "Show curve Resolution / [ESC] - remove"
    
    handlers = []
    
    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type in {'ESC'}: 
            for handler in self.handlers:
                try:
                    bpy.types.SpaceView3D.draw_handler_remove(handler, 'WINDOW')
                except:
                    pass
            for handler in self.handlers:
                self.handlers.remove(handler)
            return {'CANCELLED'}

        return {'PASS_THROUGH'}


    def invoke(self, context, event):

        if context.area.type == 'VIEW_3D':
        
            # color change in the panel
            curve_vertcolor = bpy.context.scene.curvetools.curve_vertcolor
            
            # the arguments we pass the the callback
            
            
            splines = context.active_object.data.splines
            for spline in splines:
                args = (self, context, spline, curve_vertcolor)
            
                # Add the region OpenGL drawing callback
                # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
                self.handlers.append(bpy.types.SpaceView3D.draw_handler_add(draw, args, 'WINDOW', 'POST_VIEW'))

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, 
            "View3D not found, cannot run operator")
            return {'CANCELLED'}
