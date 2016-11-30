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
    "blender": (2, 57, 0),
    "location": "View3D > Tool Shelf or Console",
    "description": "Display console defined mathutils variables in the 3D view",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/3D_interaction/Math_Viz",
    "support": "OFFICIAL",
    "category": "3D View",
}


if "bpy" in locals():
    import importlib
    importlib.reload(utils)
    importlib.reload(draw)
else:
    from . import utils, draw

import bpy
from bpy.props import StringProperty, BoolProperty, BoolVectorProperty, FloatProperty, PointerProperty, CollectionProperty
from .utils import get_var_states


class PanelConsoleVars(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = "Console Vars"
    bl_idname = "mathvis.panel_console_vars"
    bl_category = "Math Vis"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        col = box.column(align=True)
        variables = utils.get_math_data()
        var_states = get_var_states()

        for key in sorted(variables):
            ktype = variables[key]
            row = col.row(align=True)
            row.label(text='%s - %s' % (key, ktype.__name__))

            icon = 'RESTRICT_VIEW_OFF' if var_states.is_visible(key) else 'RESTRICT_VIEW_ON'
            prop = row.operator("mathvis.toggle_display", text='', icon=icon, emboss=False)
            prop.key = key

            icon = 'LOCKED' if var_states.is_locked(key) else 'UNLOCKED'
            prop = row.operator("mathvis.toggle_lock", text='', icon=icon, emboss=False)
            prop.key = key

            if var_states.is_locked(key):
                row.label(text='', icon='BLANK1')
            else:
                prop = row.operator("mathvis.delete_var", text='', icon='X', emboss=False)
                prop.key = key

        col = layout.column()
        col.prop(bpy.context.scene.MathVisProp, "name_hide")
        col.prop(bpy.context.scene.MathVisProp, "bbox_hide")
        col.prop(bpy.context.scene.MathVisProp, "bbox_scale")
        col.operator("mathvis.cleanup_console")


class DeleteVar(bpy.types.Operator):
    bl_idname = "mathvis.delete_var"
    bl_label = "Delete Var"
    bl_description = "Remove the variable from the Console."
    bl_options = {'REGISTER'}

    key = StringProperty(name="Key")

    def execute(self, context):
        locals = utils.console_namespace()
        var_states = get_var_states()
        var_states.delete(self.key)
        del locals[self.key]
        draw.tag_redraw_all_view3d_areas()
        return {'FINISHED'}


class ToggleDisplay(bpy.types.Operator):
    bl_idname = "mathvis.toggle_display"
    bl_label = "Hide/Unhide"
    bl_description = "Change the display state of the var"
    bl_options = {'REGISTER'}

    key = StringProperty(name="Key")

    def execute(self, context):
        var_states = get_var_states()
        var_states.toggle_display_state(self.key)
        draw.tag_redraw_all_view3d_areas()
        return {'FINISHED'}


class ToggleLock(bpy.types.Operator):
    bl_idname = "mathvis.toggle_lock"
    bl_label = "Lock/Unlock"
    bl_description = "Lock the var from being deleted"
    bl_options = {'REGISTER'}

    key = StringProperty(name="Key")

    def execute(self, context):
        var_states = get_var_states()
        var_states.toggle_lock_state(self.key)
        draw.tag_redraw_all_view3d_areas()
        return {'FINISHED'}


class ToggleMatrixBBoxDisplay(bpy.types.Operator):
    bl_idname = "mathvis.show_bbox"
    bl_label = "Show BBox"
    bl_description = "Show/Hide the BBox of Matrix items"
    bl_options = {'REGISTER'}

    def execute(self, context):
        var_states = get_var_states()
        var_states.toggle_show_bbox()
        draw.tag_redraw_all_view3d_areas()
        return {'FINISHED'}


class CleanupConsole(bpy.types.Operator):
    bl_idname = "mathvis.cleanup_console"
    bl_label = "Cleanup Math Vis Console"
    bl_description = "Remove all visualised variables from the Console."
    bl_options = {'REGISTER'}

    def execute(self, context):
        utils.cleanup_math_data()
        draw.tag_redraw_all_view3d_areas()
        return {'FINISHED'}


def menu_func_cleanup(self, context):
    self.layout.operator("mathvis.cleanup_console", text="Clear Math Vis")


def console_hook():
    draw.tag_redraw_all_view3d_areas()
    context = bpy.context
    for window in context.window_manager.windows:
        window.screen.areas.update()


def call_console_hook(self, context):
    console_hook()


class MathVisStateProp(bpy.types.PropertyGroup):
    key = StringProperty()
    state = BoolVectorProperty(default=(False, False), size=2)


class MathVisProp(bpy.types.PropertyGroup):

    bbox_hide = BoolProperty(name="Hide BBoxes",
                             default=False,
                             description="Hide the bounding boxes rendered for Matrix like items",
                             update=call_console_hook)

    name_hide = BoolProperty(name="Hide Names",
                             default=False,
                             description="Hide the names of the rendered items",
                             update=call_console_hook)

    bbox_scale = FloatProperty(name="Scale factor", min=0, default=1,
                               description="Resize the Bounding Box and the coordinate lines for the display of Matrix items")


def register():
    draw.callback_enable()

    import console_python
    console_python.execute.hooks.append((console_hook, ()))
    bpy.utils.register_module(__name__)
    if not 'MathVisStateProp' in dir(bpy.types.WindowManager):
        bpy.types.Scene.MathVisProp = PointerProperty(type=MathVisProp)
        bpy.types.WindowManager.MathVisStateProp = CollectionProperty(type=MathVisStateProp)
    bpy.types.CONSOLE_MT_console.prepend(menu_func_cleanup)


def unregister():
    context = bpy.context
    var_states = get_var_states()
    var_states.store_states()
    draw.callback_disable()

    import console_python
    console_python.execute.hooks.remove((console_hook, ()))
    bpy.types.CONSOLE_MT_console.remove(menu_func_cleanup)
    bpy.utils.unregister_module(__name__)
