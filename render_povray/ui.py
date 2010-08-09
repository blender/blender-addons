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


# Radiosity panel, use in the scene for now.
FloatProperty = bpy.types.Scene.FloatProperty
IntProperty = bpy.types.Scene.IntProperty
BoolProperty = bpy.types.Scene.BoolProperty

# Not a real pov option, just to know if we should write
BoolProperty(attr="pov_radio_enable",
                name="Enable Radiosity",
                description="Enable povrays radiosity calculation",
                default=False)
BoolProperty(attr="pov_radio_display_advanced",
                name="Advanced Options",
                description="Show advanced options",
                default=False)

# Real pov options
FloatProperty(attr="pov_radio_adc_bailout",
                name="ADC Bailout",
                description="The adc_bailout for radiosity rays. Use adc_bailout = 0.01 / brightest_ambient_object for good results",
                min=0.0, max=1000.0, soft_min=0.0, soft_max=1.0, default=0.01)

BoolProperty(attr="pov_radio_always_sample",
                name="Always Sample",
                description="Only use the data from the pretrace step and not gather any new samples during the final radiosity pass",
                default=True)

FloatProperty(attr="pov_radio_brightness",
                name="Brightness",
                description="Amount objects are brightened before being returned upwards to the rest of the system",
                min=0.0, max=1000.0, soft_min=0.0, soft_max=10.0, default=1.0)

IntProperty(attr="pov_radio_count",
                name="Ray Count",
                description="Number of rays that are sent out whenever a new radiosity value has to be calculated",
                min=1, max=1600, default=35)

FloatProperty(attr="pov_radio_error_bound",
                name="Error Bound",
                description="One of the two main speed/quality tuning values, lower values are more accurate",
                min=0.0, max=1000.0, soft_min=0.1, soft_max=10.0, default=1.8)

FloatProperty(attr="pov_radio_gray_threshold",
                name="Gray Threshold",
                description="One of the two main speed/quality tuning values, lower values are more accurate",
                min=0.0, max=1.0, soft_min=0, soft_max=1, default=0.0)

FloatProperty(attr="pov_radio_low_error_factor",
                name="Low Error Factor",
                description="If you calculate just enough samples, but no more, you will get an image which has slightly blotchy lighting",
                min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, default=0.5)

# max_sample - not available yet
BoolProperty(attr="pov_radio_media",
                name="Media",
                description="Radiosity estimation can be affected by media",
                default=False)

FloatProperty(attr="pov_radio_minimum_reuse",
                name="Minimum Reuse",
                description="Fraction of the screen width which sets the minimum radius of reuse for each sample point (At values higher than 2% expect errors)",
                min=0.0, max=1.0, soft_min=0.1, soft_max=0.1, default=0.015)

IntProperty(attr="pov_radio_nearest_count",
                name="Nearest Count",
                description="Number of old ambient values blended together to create a new interpolated value",
                min=1, max=20, default=5)

BoolProperty(attr="pov_radio_normal",
                name="Normals",
                description="Radiosity estimation can be affected by normals",
                default=False)

IntProperty(attr="pov_radio_recursion_limit",
                name="Recursion Limit",
                description="how many recursion levels are used to calculate the diffuse inter-reflection",
                min=1, max=20, default=3)



# Use some of the existing buttons.
import properties_render
properties_render.RENDER_PT_render.COMPAT_ENGINES.add('POVRAY_RENDER')
properties_render.RENDER_PT_dimensions.COMPAT_ENGINES.add('POVRAY_RENDER')
properties_render.RENDER_PT_antialiasing.COMPAT_ENGINES.add('POVRAY_RENDER')
properties_render.RENDER_PT_output.COMPAT_ENGINES.add('POVRAY_RENDER')
del properties_render

# Use only a subset of the world panels
import properties_world
properties_world.WORLD_PT_preview.COMPAT_ENGINES.add('POVRAY_RENDER')
properties_world.WORLD_PT_context_world.COMPAT_ENGINES.add('POVRAY_RENDER')
properties_world.WORLD_PT_world.COMPAT_ENGINES.add('POVRAY_RENDER')
properties_world.WORLD_PT_mist.COMPAT_ENGINES.add('POVRAY_RENDER')
del properties_world

# Example of wrapping every class 'as is'
import properties_material
for member in dir(properties_material):
    subclass = getattr(properties_material, member)
    try:
        subclass.COMPAT_ENGINES.add('POVRAY_RENDER')
    except:
        pass
del properties_material

import properties_data_mesh
for member in dir(properties_data_mesh):
    subclass = getattr(properties_data_mesh, member)
    try:
        subclass.COMPAT_ENGINES.add('POVRAY_RENDER')
    except:
        pass
del properties_data_mesh

import properties_texture
for member in dir(properties_texture):
    subclass = getattr(properties_texture, member)
    try:
        subclass.COMPAT_ENGINES.add('POVRAY_RENDER')
    except:
        pass
del properties_texture

import properties_data_camera
for member in dir(properties_data_camera):
    subclass = getattr(properties_data_camera, member)
    try:
        subclass.COMPAT_ENGINES.add('POVRAY_RENDER')
    except:
        pass
del properties_data_camera



class RenderButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    # COMPAT_ENGINES must be defined in each subclass, external engines can add themselves here

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return (rd.use_game_engine == False) and (rd.engine in self.COMPAT_ENGINES)


class RENDER_PT_povray_radiosity(RenderButtonsPanel, bpy.types.Panel):
    bl_label = "Radiosity"
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    def draw_header(self, context):
        scene = context.scene

        self.layout.prop(scene, "pov_radio_enable", text="")

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        rd = scene.render

        layout.active = scene.pov_radio_enable

        split = layout.split()

        col = split.column()
        col.prop(scene, "pov_radio_count", text="Rays")
        col.prop(scene, "pov_radio_recursion_limit", text="Recursions")
        col = split.column()
        col.prop(scene, "pov_radio_error_bound", text="Error")

        layout.prop(scene, "pov_radio_display_advanced")

        if scene.pov_radio_display_advanced:
            split = layout.split()

            col = split.column()
            col.prop(scene, "pov_radio_adc_bailout", slider=True)
            col.prop(scene, "pov_radio_gray_threshold", slider=True)
            col.prop(scene, "pov_radio_low_error_factor", slider=True)

            col = split.column()
            col.prop(scene, "pov_radio_brightness")
            col.prop(scene, "pov_radio_minimum_reuse", text="Min Reuse")
            col.prop(scene, "pov_radio_nearest_count")

            split = layout.split()

            col = split.column()
            col.label(text="Estimation Influence:")
            col.prop(scene, "pov_radio_media")
            col.prop(scene, "pov_radio_normal")

            col = split.column()
            col.prop(scene, "pov_radio_always_sample")



