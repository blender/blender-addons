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
    "name": "Demo Mode",
    "author": "Campbell Barton",
    "blender": (2, 5, 7),
    "api": 35622,
    "location": "Demo Menu",
    "description": "TODO",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"\
        "Scripts/TODO/DemoMode",
    "tracker_url": "",
    "support": 'OFFICIAL',
    "category": "Import-Export"}

# To support reload properly, try to access a package var, if it's there, reload everything
if "bpy" in locals():
    import imp
    if "config" in locals():
        imp.reload(config)


import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty
from io_utils import ImportHelper


class DemoModeSetup(bpy.types.Operator):
    '''Creates a demo script and optionally executes'''
    bl_idname = "wm.demo_mode_setup"
    bl_label = "Demo Mode"
    bl_options = {'PRESET'}

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.

    # these are used to create the file list.
    filepath = StringProperty(name="File Path", description="Filepath used for importing the file", maxlen=1024, default="", subtype='FILE_PATH')
    random_order = BoolProperty(name="Random Order", description="Select files randomly", default=False)
    mode = EnumProperty(items=(
            ('AUTO', "Automatic", ""),
            ('PLAY', "Play", ""),
            ('RENDER', "Render", ""),
            ),
                name="Method")

    run = BoolProperty(name="Run Immediately!", description="Run demo immediately", default=True)

    # these are mapped directly to the config!
    #
    # anim
    # ====
    anim_cycles = FloatProperty(name="Cycles", description="Number of times to play the animation", min=0.1, max=1000.0, soft_min=1.0, soft_max=1000.0, default=1.0)
    anim_time_min = FloatProperty(name="Time Min", description="Minimum number of seconds to show the animation for (for small loops)", min=0.0, max=1000.0, soft_min=1.0, soft_max=1000.0, default=4.0)
    anim_time_max = FloatProperty(name="Time Max", description="Maximum number of seconds to show the animation for (incase the end frame is very high for no reason)", min=0.0, max=100000000.0, soft_min=1.0, soft_max=100000000.0, default=60.0)
    anim_screen_switch = FloatProperty(name="Screen Switch", description="Time between switching screens (in seconds) or 0 to disable", min=0.0, max=100000000.0, soft_min=1.0, soft_max=60.0, default=0.0)
    #
    # render
    # ======
    display_render = FloatProperty(name="Render Delay", description="Time to display the rendered image before moving on (in seconds)", min=0.0, max=60.0, default=4.0)
    anim_render = BoolProperty(name="Render Anim", description="Render entire animation (render mode only)", default=False)

    def execute(self, context):
        from . import config

        keywords = self.as_keywords(ignore=("filepath", "random_order", "run"))

        from . import config
        cfg_str, dirpath = config.as_string(self.filepath, self.random_order, **keywords)
        text = bpy.data.texts.get("demo.py")
        if text is None:
            text = bpy.data.texts.new("demo.py")

        text.from_string(cfg_str)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def check(self, context):
        return True  # lazy

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "run")

        col.label("Generate Settings:")
        col.prop(self, "mode")
        col.prop(self, "random_order")
        
        mode = self.mode
        
        col.separator()
        colsub = col.column()
        colsub.active = (mode in ('AUTO', 'ANIMATE'))
        colsub.label("Animate Settings:")
        colsub.prop(self, "anim_cycles")
        colsub.prop(self, "anim_time_min")
        colsub.prop(self, "anim_time_max")

        col.separator()
        colsub = col.column()
        colsub.active = (mode in ('AUTO', 'RENDER'))
        colsub.label("Render Settings:")
        colsub.prop(self, "render_anim")


def menu_func(self, context):
    self.layout.operator(DemoModeSetup.bl_idname)


def register():
    bpy.utils.register_class(DemoModeSetup)

    bpy.types.INFO_MT_file_import.append(menu_func)


def unregister():
    bpy.utils.unregister_class(DemoModeSetup)

    bpy.types.INFO_MT_file_import.remove(menu_func)

if __name__ == "__main__":
    register()
