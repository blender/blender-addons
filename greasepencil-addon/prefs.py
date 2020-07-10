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

import bpy
import os
from bpy.props import (
        BoolProperty,
        EnumProperty,
        # IntProperty,
        )


class GreasePencilAddonPrefs(bpy.types.AddonPreferences):
    bl_idname = os.path.splitext(__name__)[0]#'greasepencil-addon'#can be called 'master'
    # bl_idname = __name__

    pref_tabs : EnumProperty(
        items=(('PREF', "Preferences", "Preferences properties of GP"),
               ('TUTO', "Tutorial", "How to use the tool"),
               # ('KEYMAP', "Keymap", "customise the default keymap"),
               ),
               default='PREF')

    # --- props
    use_clic_drag : BoolProperty(
        name='Use click drag directly on points',
        description="Change the active tool to 'tweak' during modal, Allow to direct clic-drag points of the box",
        default=True)
    
    default_deform_type : EnumProperty(
        items=(('KEY_LINEAR', "Linear (perspective mode)", "Linear interpolation, like corner deform / perspective tools of classic 2D", 'IPO_LINEAR',0),
               ('KEY_BSPLINE', "Spline (smooth deform)", "Spline interpolation transformation\nBest when lattice is subdivided", 'IPO_CIRC',1),
               ),
        name='Starting interpolation', default='KEY_LINEAR', description='Choose default interpolation when entering mode')
    
    # About interpolation : https://docs.blender.org/manual/en/2.83/animation/shape_keys/shape_keys_panel.html#fig-interpolation-type

    auto_swap_deform_type : BoolProperty(
        name='Auto swap interpolation mode',
        description="Automatically set interpolation to 'spline' when subdividing lattice\n Back to 'linear' when",
        default=True)

    def draw(self, context):
            layout = self.layout
            # layout.use_property_split = True
            row= layout.row(align=True)
            row.prop(self, "pref_tabs", expand=True)

            if self.pref_tabs == 'PREF':
                layout.label(text='Box deform tool preferences')
                layout.prop(self, "use_clic_drag")
                # layout.separator()
                layout.prop(self, "default_deform_type")
                layout.label(text="Deformer type can be changed during modal with 'M' key, this is for default behavior", icon='INFO')
                
                layout.prop(self, "auto_swap_deform_type")
                layout.label(text="Once 'M' is hit, auto swap is desactivated to stay in your chosen mode", icon='INFO')

            if self.pref_tabs == 'TUTO':

                #**Behavior from context mode**
                col = layout.column()
                col.label(text='Box deform tool')
                col.label(text="Usage:", icon='MOD_LATTICE')
                col.label(text="Use the shortcut 'Ctrl+T' in available modes (listed below)")
                col.label(text="The lattice box is generated facing your view (be sure to face canvas if you want to stay on it)")
                col.label(text="Use shortcuts below to deform (a help will be displayed in the topbar)")

                col.separator()
                col.label(text="Shortcuts:", icon='HAND')
                col.label(text="Spacebar / Enter : Confirm")
                col.label(text="Delete / Backspace / Tab(twice) / Ctrl+T : Cancel")
                col.label(text="M : Toggle between Linear and Spline mode at any moment")
                col.label(text="1-9 top row number : Subdivide the box")
                col.label(text="Ctrl + arrows-keys : Subdivide the box incrementally in individual X/Y axis")

                col.separator()
                col.label(text="Modes and deformation target:", icon='PIVOT_BOUNDBOX')
                col.label(text="- Object mode : The whole GP object is deformed (including all frames)")
                col.label(text="- GPencil Edit mode : Deform Selected points")
                col.label(text="- Gpencil Paint : Deform last Strokes")
                # col.label(text="- Lattice edit : Revive the modal after a ctrl+Z")

                col.separator()
                col.label(text="Notes:", icon='TEXT')
                col.label(text="- If you return in box deform after applying (with a ctrl+Z), you need to hit 'Ctrl+T' again to revive the modal.")
                col.label(text="- A cancel warning will be displayed the first time you hit Tab")



def register():
    bpy.utils.register_class(GreasePencilAddonPrefs)
    # Force box deform running to false
    bpy.context.preferences.addons[os.path.splitext(__name__)[0]].preferences.boxdeform_running = False

def unregister():
    bpy.utils.unregister_class(GreasePencilAddonPrefs)
