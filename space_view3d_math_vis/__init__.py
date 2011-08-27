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

bl_info = {
    "name": "Math Vis (Console)",
    "author": "Campbell Barton",
    "version": (0, 1),
    "blender": (2, 5, 7),
    "api": 35622,
    "location": "View3D > Tool Shelf or Console",
    "description": "Display console defined mathutils variables in the 3D view",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"\
        "Scripts/3D_interaction/Math_Viz",
    "tracker_url": "http://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=25545",
    "support": "OFFICIAL",
    "category": "3D View"}

if "bpy" in locals():
    import imp
    imp.reload(utils)
    imp.reload(draw)
else:
    from . import utils, draw

import bpy


class VIEW3D_PT_math_vis(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label = "Math View"

    def draw(self, context):
        callbacks = draw.callbacks
        ok = False
        for region in context.area.regions:
            if callbacks.get(hash(region)):
                ok = True
                break

        self.layout.operator("view3d.math_vis_toggle", emboss=False, icon='CHECKBOX_HLT' if ok else 'CHECKBOX_DEHLT')


class SetupMathView(bpy.types.Operator):
    '''Visualize mathutils type python variables from the interactive console, see addon docs'''
    bl_idname = "view3d.math_vis_toggle"
    bl_label = "Use Math Vis"

    def execute(self, context):
        callbacks = draw.callbacks
        region = context.region
        region_id = hash(region)
        cb_data = callbacks.get(region_id)
        if cb_data is None:
            handle_pixel = region.callback_add(draw.draw_callback_px, (self, context), 'POST_PIXEL')
            handle_view = region.callback_add(draw.draw_callback_view, (self, context), 'POST_VIEW')
            callbacks[region_id] = region, handle_pixel, handle_view
        else:
            region.callback_remove(cb_data[1])
            region.callback_remove(cb_data[2])
            del callbacks[region_id]

        context.area.tag_redraw()
        return {'FINISHED'}


def console_hook():
    for region, handle_pixel, handle_view in draw.callbacks.values():
        region.tag_redraw()


def register():
    bpy.utils.register_module(__name__)

    import console_python
    console_python.execute.hooks.append((console_hook, ()))


def unregister():
    bpy.utils.unregister_module(__name__)

    import console_python
    console_python.execute.hooks.remove((console_hook, ()))

    draw.callbacks_clear()
