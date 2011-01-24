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

import bpy

# Use some of the existing buttons.
import properties_render
properties_render.RENDER_PT_render.COMPAT_ENGINES.add('POVRAY_RENDER')
properties_render.RENDER_PT_dimensions.COMPAT_ENGINES.add('POVRAY_RENDER')
# properties_render.RENDER_PT_antialiasing.COMPAT_ENGINES.add('POVRAY_RENDER')
properties_render.RENDER_PT_shading.COMPAT_ENGINES.add('POVRAY_RENDER')  # We don't use it right now. Should be implemented later.
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
        return mat and (rd.use_game_engine == False) and (rd.engine in cls.COMPAT_ENGINES)


class TextureButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "texture"
    # COMPAT_ENGINES must be defined in each subclass, external engines can add themselves here

    @classmethod
    def poll(cls, context):
        tex = context.texture
        rd = context.scene.render
        return tex and (rd.use_game_engine == False) and (rd.engine in cls.COMPAT_ENGINES)


class ObjectButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    # COMPAT_ENGINES must be defined in each subclass, external engines can add themselves here

    @classmethod
    def poll(cls, context):
        obj = context.object
        rd = context.scene.render
        return obj and (rd.use_game_engine == False) and (rd.engine in cls.COMPAT_ENGINES)


class RENDER_PT_povray_export_settings(RenderButtonsPanel, bpy.types.Panel):
    bl_label = "Export Settings"
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        rd = scene.render

        layout.active = scene.pov_max_trace_level
        split = layout.split()

        col = split.column()
        col.label(text="Command line switches:")
        col.prop(scene, "pov_command_line_switches", text="")
        split = layout.split()
        col = split.column()
        col.prop(scene, "pov_tempfiles_enable", text="OS Tempfiles")
        if not scene.pov_tempfiles_enable:
            col = split.column()
            col.prop(scene, "pov_deletefiles_enable", text="Delete files")
        else:
            col = split.column()

        split = layout.split()
        if not scene.pov_tempfiles_enable:
            col = split.column()
            col.prop(scene, "pov_scene_name", text="Name")
            split = layout.split()
            col = split.column()
            col.prop(scene, "pov_scene_path", text="Path to files")
            #col.prop(scene, "pov_scene_path", text="Path to POV-file")
            split = layout.split()
            #col = split.column()  # Bug in POV-Ray RC3
            #col.prop(scene, "pov_renderimage_path", text="Path to image")
            #split = layout.split()

            col = split.column()
            col.prop(scene, "pov_indentation_character", text="Indent")
            col = split.column()
            if scene.pov_indentation_character == "2": 
                col.prop(scene, "pov_indentation_spaces", text="Spaces")
            split = layout.split()
            col = split.column()
            col.prop(scene, "pov_comments_enable", text="Comments")
            col = split.column()
            col.prop(scene, "pov_list_lf_enable", text="Line brakes in lists")


class RENDER_PT_povray_render_settings(RenderButtonsPanel, bpy.types.Panel):
    bl_label = "Render Settings"
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        rd = scene.render

        layout.active = scene.pov_max_trace_level
        split = layout.split()
        col = split.column()
        col.prop(scene, "pov_max_trace_level", text="Ray Depth")
        col = split.column()


class RENDER_PT_povray_antialias(RenderButtonsPanel, bpy.types.Panel):
    bl_label = "Anti-Aliasing"
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    def draw_header(self, context):
        scene = context.scene

        self.layout.prop(scene, "pov_antialias_enable", text="")

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        rd = scene.render

        layout.active = scene.pov_antialias_enable

        split = layout.split()
        col = split.column()
        col.prop(scene, "pov_antialias_method", text="")
        col = split.column()
        col.prop(scene, "pov_jitter_enable", text="Jitter")

        split = layout.split()
        col = split.column()
        col.prop(scene, "pov_antialias_depth", text="AA Depth")
        sub = split.column()
        sub.prop(scene, "pov_jitter_amount", text="Jitter Amount")
        if scene.pov_jitter_enable:
            sub.enabled = True
        else:
            sub.enabled = False

        split = layout.split()
        col = split.column()
        col.prop(scene, "pov_antialias_threshold", text="AA Threshold")
        col = split.column()
        col.prop(scene, "pov_antialias_gamma", text="AA Gamma")


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
        col.prop(scene, "pov_radio_error_bound", text="Error Bound")

        layout.prop(scene, "pov_radio_display_advanced")

        if scene.pov_radio_display_advanced:
            split = layout.split()

            col = split.column()
            col.prop(scene, "pov_radio_adc_bailout", slider=True)
            col.prop(scene, "pov_radio_gray_threshold", slider=True)
            col.prop(scene, "pov_radio_low_error_factor", slider=True)
            col.prop(scene, "pov_radio_pretrace_start", slider=True)

            col = split.column()
            col.prop(scene, "pov_radio_brightness")
            col.prop(scene, "pov_radio_minimum_reuse", text="Min Reuse")
            col.prop(scene, "pov_radio_nearest_count")
            col.prop(scene, "pov_radio_pretrace_end", slider=True)

            split = layout.split()

            col = split.column()
            col.label(text="Estimation Influence:")
            col.prop(scene, "pov_radio_media")
            col.prop(scene, "pov_radio_normal")

            col = split.column()
            col.prop(scene, "pov_radio_always_sample")


class RENDER_PT_povray_media(RenderButtonsPanel, bpy.types.Panel):
    bl_label = "Atmosphere Media"
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    def draw_header(self, context):
        scene = context.scene

        self.layout.prop(scene, "pov_media_enable", text="")

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        rd = scene.render

        layout.active = scene.pov_media_enable
        split = layout.split()

        col = split.column()
        col.prop(scene, "pov_media_samples", text="Samples")
        col = split.column()
        col.prop(scene, "pov_media_color", text="Color")

##class RENDER_PT_povray_baking(RenderButtonsPanel, bpy.types.Panel):
##    bl_label = "Baking"
##    COMPAT_ENGINES = {'POVRAY_RENDER'}
##
##    def draw_header(self, context):
##        scene = context.scene
##
##        self.layout.prop(scene, "pov_baking_enable", text="")
##
##    def draw(self, context):
##        layout = self.layout
##
##        scene = context.scene
##        rd = scene.render
##
##        layout.active = scene.pov_baking_enable


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
            row.label(text="Transparency IOR is: " + str(mat.raytrace_transparency.ior))


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
##            if mat.pov_refraction_type=="0":
##                mat.pov_fake_caustics = False
##                mat.pov_photons_refraction = False
##                mat.pov_photons_reflection = True
            if mat.pov_refraction_type == "1":
##                mat.pov_fake_caustics = True
##                mat.pov_photons_refraction = False
                col.prop(mat, "pov_fake_caustics_power", slider=True)
            elif mat.pov_refraction_type == "2":
##                mat.pov_fake_caustics = False
##                mat.pov_photons_refraction = True
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


class TEXTURE_PT_povray_tex_gamma(TextureButtonsPanel, bpy.types.Panel):
    bl_label = "Image Gamma"
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    def draw_header(self, context):
        tex = context.texture

        self.layout.prop(tex, "pov_tex_gamma_enable", text="")

    def draw(self, context):
        layout = self.layout

        tex = context.texture

        layout.active = tex.pov_tex_gamma_enable
        split = layout.split()

        col = split.column()
        col.prop(tex, "pov_tex_gamma_value", text="Gamma Value")


class OBJECT_PT_povray_obj_importance(ObjectButtonsPanel, bpy.types.Panel):
    bl_label = "POV-Ray"
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    def draw(self, context):
        layout = self.layout

        obj = context.object

        layout.active = obj.pov_importance_value
        split = layout.split()

        col = split.column()
        col.prop(obj, "pov_importance_value", text="Importance")
