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

import properties_data_lamp
for member in dir(properties_data_lamp):
    subclass = getattr(properties_data_lamp, member)
    try:
        subclass.COMPAT_ENGINES.add('POVRAY_RENDER')
    except:
        pass
del properties_data_lamp



class RenderButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    # COMPAT_ENGINES must be defined in each subclass, external engines can add themselves here

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return (rd.use_game_engine == False) and (rd.engine in cls.COMPAT_ENGINES)

class MaterialButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"
    # COMPAT_ENGINES must be defined in each subclass, external engines can add themselves here

    @classmethod
    def poll(cls, context):
        mat = context.material
        rd = context.scene.render
        return (rd.use_game_engine == False) and (rd.engine in cls.COMPAT_ENGINES)

########################################MR######################################
class MATERIAL_PT_povray_mirrorIOR(MaterialButtonsPanel, bpy.types.Panel):
    bl_label = "IOR Mirror"
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    def draw_header(self, context):
        scene = context.material

        self.layout.prop(scene, "pov_mirror_use_IOR", text="")

    def draw(self, context):
        layout = self.layout

        mat = context.material
        layout.active = mat.pov_mirror_use_IOR

        if mat.pov_mirror_use_IOR:
            split = layout.split()
            col = split.column()
            row = col.row()
            row.alignment = 'CENTER'
            row.label(text="The current Raytrace ")
            row = col.row()
            row.alignment = 'CENTER'
            row.label(text="Transparency IOR is: "+str(mat.raytrace_transparency.ior))
  

class MATERIAL_PT_povray_metallic(MaterialButtonsPanel, bpy.types.Panel):
    bl_label = "metallic Mirror"
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    def draw_header(self, context):
        scene = context.material

        self.layout.prop(scene, "pov_mirror_metallic", text="")

    def draw(self, context):
        layout = self.layout

        mat = context.material
        layout.active = mat.pov_mirror_metallic

class MATERIAL_PT_povray_conserve_energy(MaterialButtonsPanel, bpy.types.Panel):
    bl_label = "conserve energy"
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    def draw_header(self, context):
        mat = context.material

        self.layout.prop(mat, "pov_conserve_energy", text="")

    def draw(self, context):
        layout = self.layout

        mat = context.material
        layout.active = mat.pov_conserve_energy

class MATERIAL_PT_povray_iridescence(MaterialButtonsPanel, bpy.types.Panel):
    bl_label = "iridescence"
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    def draw_header(self, context):
        mat = context.material

        self.layout.prop(mat, "pov_irid_enable", text="")

    def draw(self, context):
        layout = self.layout

        mat = context.material
        layout.active = mat.pov_irid_enable
        
        if mat.pov_irid_enable:
            split = layout.split()

            col = split.column()
            col.prop(mat, "pov_irid_amount", slider=True)
            col.prop(mat, "pov_irid_thickness", slider=True)
            col.prop(mat, "pov_irid_turbulence", slider=True)


class MATERIAL_PT_povray_caustics(MaterialButtonsPanel, bpy.types.Panel):
    bl_label = "Caustics"
    COMPAT_ENGINES = {'POVRAY_RENDER'}


    def draw_header(self, context):
        mat = context.material

        self.layout.prop(mat, "pov_caustics_enable", text="")

    def draw(self, context):
        
        layout = self.layout

        mat = context.material
        layout.active = mat.pov_caustics_enable
        Radio = 1
        if mat.pov_caustics_enable:
            split = layout.split()

            col = split.column()
            col.prop(mat, "pov_refraction_type")
            if mat.pov_refraction_type=="0":
                mat.pov_fake_caustics = False
                mat.pov_photons_refraction = False
                mat.pov_photons_reflection = True
            elif mat.pov_refraction_type=="1":
                mat.pov_fake_caustics = True
                mat.pov_photons_refraction = False
                col.prop(mat, "pov_fake_caustics_power", slider=True)
            elif mat.pov_refraction_type=="2":
                mat.pov_fake_caustics = False
                mat.pov_photons_refraction = True
                col.prop(mat, "pov_photons_dispersion", slider=True)
            col.prop(mat, "pov_photons_reflection")
                
                

##            col.prop(mat, "pov_fake_caustics")
##            if mat.pov_fake_caustics:
##                col.prop(mat, "pov_fake_caustics_power", slider=True)
##                mat.pov_photons_refraction=0
##            else:
##                col.prop(mat, "pov_photons_refraction")
##            if mat.pov_photons_refraction:
##                col.prop(mat, "pov_photons_dispersion", slider=True)
##                Radio = 0
##                mat.pov_fake_caustics=Radio
##            col.prop(mat, "pov_photons_reflection")
####TODO : MAKE THIS A real RADIO BUTTON (using EnumProperty?)
######################################EndMR#####################################

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
