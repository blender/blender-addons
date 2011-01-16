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

bl_info = {
    "name": "POV-Ray 3.7",
    "author": "Campbell Barton, Silvio Falcinelli, Maurice Raybaud, Constantin Rahn",
    "version": (0, 0, 6),
    "blender": (2, 5, 6),
    "api": 34318,
    "location": "Info Header (engine dropdown)",
    "description": "Basic POV-Ray 3.7 integration for blender",
    "warning": "both POV-Ray 3.7 and this script are beta",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"\
        "Scripts/Render/PovRay",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=23145",
    "category": "Render"}


if "bpy" in locals():
    import imp
    imp.reload(ui)
    imp.reload(render)

else:
    import bpy
    from bpy.props import *
    from render_povray import ui
    from render_povray import render

def register():
    Scene = bpy.types.Scene

    # Not a real pov option, just to know if we should write
    Scene.pov_radio_enable = BoolProperty(
            name="Enable Radiosity",
            description="Enable POV-Rays radiosity calculation",
            default=False)
    Scene.pov_radio_display_advanced = BoolProperty(
            name="Advanced Options",
            description="Show advanced options",
            default=False)
    Scene.pov_media_enable = BoolProperty(
        name="Enable Media",
        description="Enable POV-Rays atmospheric media",
        default=False)
    Scene.pov_media_samples = IntProperty(
            name="Samples", description="Number of samples taken from camera to first object encountered along ray path for media calculation",
            min=1, max=100, default=35)
    Scene.pov_media_color = FloatProperty(
            name="Media Color", description="The atmospheric media color. Grey value for now",
            min=0.00, max=1.00, soft_min=0.01, soft_max=1.00, default=0.01)
    Scene.pov_baking_enable = BoolProperty(
            name="Enable Baking",
            description="Enable POV-Rays texture baking",
            default=False)
    Scene.pov_indentation_character = EnumProperty(
            name="Indentation",
            description="Select the indentation type",
            items=(("0", "None", "No indentation"),
               ("1", "Tabs", "Indentation with tabs"),
               ("2", "Spaces", "Indentation with spaces")),
            default="1")
    Scene.pov_indentation_spaces = IntProperty(
            name="Quantity of spaces",
            description="The number of spaces for indentation",
            min=1, max=10, default=3)
    
    Scene.pov_comments_enable = BoolProperty(
            name="Enable Comments",
            description="Add comments to pov file",
            default=True)

    # Real pov options
    Scene.pov_command_line_switches = StringProperty(name="Command Line Switches",
            description="Command line switches consist of a + (plus) or - (minus) sign, followed by one or more alphabetic characters and possibly a numeric value.",
            default="", maxlen=500)
    
    Scene.pov_max_trace_level = IntProperty(
            name="Max Trace Level", description="Number of reflections/refractions allowed on ray path",
            min=1, max=256, default=5)
    
    Scene.pov_radio_adc_bailout = FloatProperty(
            name="ADC Bailout", description="The adc_bailout for radiosity rays. Use adc_bailout = 0.01 / brightest_ambient_object for good results",
            min=0.0, max=1000.0, soft_min=0.0, soft_max=1.0, default=0.01, precision=3)

    Scene.pov_radio_always_sample = BoolProperty(
            name="Always Sample", description="Only use the data from the pretrace step and not gather any new samples during the final radiosity pass",
            default=True)

    Scene.pov_radio_brightness = FloatProperty(
            name="Brightness", description="Amount objects are brightened before being returned upwards to the rest of the system",
            min=0.0, max=1000.0, soft_min=0.0, soft_max=10.0, default=1.0)

    Scene.pov_radio_count = IntProperty(
            name="Ray Count", description="Number of rays for each new radiosity value to be calculated (halton sequence over 1600)",
            min=1, max=10000, soft_max=1600, default=35)

    Scene.pov_radio_error_bound = FloatProperty(
            name="Error Bound", description="One of the two main speed/quality tuning values, lower values are more accurate",
            min=0.0, max=1000.0, soft_min=0.1, soft_max=10.0, default=1.8)

    Scene.pov_radio_gray_threshold = FloatProperty(
            name="Gray Threshold", description="One of the two main speed/quality tuning values, lower values are more accurate",
            min=0.0, max=1.0, soft_min=0, soft_max=1, default=0.0)

    Scene.pov_radio_low_error_factor = FloatProperty(
            name="Low Error Factor", description="Just enough samples is slightly blotchy. Low error changes error tolerance for less critical last refining pass",
            min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, default=0.5)

    # max_sample - not available yet
    Scene.pov_radio_media = BoolProperty(
            name="Media", description="Radiosity estimation can be affected by media",
            default=False)

    Scene.pov_radio_minimum_reuse = FloatProperty(
            name="Minimum Reuse", description="Fraction of the screen width which sets the minimum radius of reuse for each sample point (At values higher than 2% expect errors)",
            min=0.0, max=1.0, soft_min=0.1, soft_max=0.1, default=0.015, precision=3)

    Scene.pov_radio_nearest_count = IntProperty(
            name="Nearest Count", description="Number of old ambient values blended together to create a new interpolated value",
            min=1, max=20, default=5)

    Scene.pov_radio_normal = BoolProperty(
            name="Normals", description="Radiosity estimation can be affected by normals",
            default=False)

    Scene.pov_radio_recursion_limit = IntProperty(
            name="Recursion Limit", description="how many recursion levels are used to calculate the diffuse inter-reflection",
            min=1, max=20, default=3)

    Scene.pov_radio_pretrace_start = FloatProperty(
            name="Pretrace Start", description="Fraction of the screen width which sets the size of the blocks in the mosaic preview first pass",
            min=0.01, max=1.00, soft_min=0.02, soft_max=1.0, default=0.08)

    Scene.pov_radio_pretrace_end = FloatProperty(
            name="Pretrace End", description="Fraction of the screen width which sets the size of the blocks in the mosaic preview last pass",
            min=0.001, max=1.00, soft_min=0.01, soft_max=1.00, default=0.04, precision=3)

    ########################################MR######################################
    Mat = bpy.types.Material

    Mat.pov_irid_enable = BoolProperty(
            name="Enable Iridescence",
            description="Newton's thin film interference (like an oil slick on a puddle of water or the rainbow hues of a soap bubble.)",
            default=False)            

    Mat.pov_mirror_use_IOR = BoolProperty(
            name="Correct Reflection",
            description="Use same IOR as raytrace transparency to calculate mirror reflections. More physically correct",
            default=False)

    Mat.pov_mirror_metallic = BoolProperty(
            name="Metallic Reflection",
            description="mirror reflections get colored as diffuse (for metallic materials)",
            default=False)

    Mat.pov_conserve_energy = BoolProperty(
            name="Conserve Energy",
            description="Light transmitted is more correctly reduced by mirror reflections, also the sum of diffuse and translucency gets reduced below one ",
            default=True)

    Mat.pov_irid_amount = FloatProperty(
            name="amount",
            description="Contribution of the iridescence effect to the overall surface color. As a rule of thumb keep to around 0.25 (25% contribution) or less, but experiment. If the surface is coming out too white, try lowering the diffuse and possibly the ambient values of the surface.",
            min=0.0, max=1.0, soft_min=0.01, soft_max=1.0, default=0.25)

    Mat.pov_irid_thickness = FloatProperty(
            name="thickness",
            description="A very thin film will have a high frequency of color changes while a thick film will have large areas of color.",
            min=0.0, max=1000.0, soft_min=0.1, soft_max=10.0, default=1)

    Mat.pov_irid_turbulence = FloatProperty(
            name="turbulence",
            description="This parameter varies the thickness.",
            min=0.0, max=10.0, soft_min=0.000, soft_max=1.0, default=0)

    Mat.pov_caustics_enable = BoolProperty(
            name="Caustics",
            description="use only fake refractive caustics (default) or photon based reflective/refractive caustics",
            default=True)

    Mat.pov_fake_caustics = BoolProperty(
            name="Fake Caustics",
            description="use only (Fast) fake refractive caustics",
            default=True)

    Mat.pov_fake_caustics_power = FloatProperty(
            name="Fake caustics power",
            description="Values typically range from 0.0 to 1.0 or higher. Zero is no caustics. Low, non-zero values give broad hot-spots while higher values give tighter, smaller simulated focal points",
            min=0.00, max=10.0, soft_min=0.00, soft_max=1.10, default=0.1)

    Mat.pov_photons_refraction = BoolProperty(
            name="Refractive Photon Caustics",
            description="more physically correct",
            default=False)

    Mat.pov_photons_dispersion = FloatProperty(
            name="chromatic dispersion",
            description="Light passing through will be separated according to wavelength. This ratio of refractive indices for violet to red controls how much the colors are spread out 1 = no dispersion, good values are 1.01 to 1.1",
            min=1.00, max=10.0, soft_min=1.00, soft_max=1.10, default=1.00)

    Mat.pov_photons_reflection = BoolProperty(
            name="Reflective Photon Caustics",
            description="Use this to make your Sauron's ring ;-P",
            default=False)

    Mat.pov_refraction_type = EnumProperty(
            items=[("0","None","use only reflective caustics"),
                   ("1","Fake Caustics","use fake caustics"),
                   ("2","Photons Caustics","use photons for refractive caustics"),
                   ],
            name="Refractive",
            description="use fake caustics (fast) or true photons for refractive Caustics",
            default="1")#ui.py has to be loaded before render.py with this.
    
    ########################################################################################
    #Custom texture gamma
    Tex = bpy.types.Texture 
    Tex.pov_tex_gamma_enable = BoolProperty(
            name="Enable custom texture gamma",
            description="Notify some custom gamma for which texture has been precorrected without the file format carrying it and only if it differs from your OS expected standard (see pov doc)",
            default=False)
    Tex.pov_tex_gamma_value = FloatProperty(
            name="Custom texture gamma",
            description="value for which the file was issued e.g. a Raw photo is gamma 1.0",
            min=0.45, max=5.00, soft_min=1.00, soft_max=2.50, default=1.00)

    #Importance sampling
    Obj = bpy.types.Object
    Obj.pov_importance_value = FloatProperty(
            name="Radiosity Importance",
            description="Priority value relative to other objects for sampling radiosity rays. Increase to get more radiosity rays at comparatively small yet bright objects",
            min=0.01, max=1.00, default=1.00)
    
    ######################################EndMR#####################################

def unregister():
    import bpy
    Scene = bpy.types.Scene
    Mat = bpy.types.Material # MR
    Tex = bpy.types.Texture # MR
    Obj = bpy.types.Object # MR
    del Scene.pov_radio_enable
    del Scene.pov_radio_display_advanced
    del Scene.pov_radio_adc_bailout
    del Scene.pov_radio_always_sample
    del Scene.pov_radio_brightness
    del Scene.pov_radio_count
    del Scene.pov_radio_error_bound
    del Scene.pov_radio_gray_threshold
    del Scene.pov_radio_low_error_factor
    del Scene.pov_radio_media
    del Scene.pov_radio_minimum_reuse
    del Scene.pov_radio_nearest_count
    del Scene.pov_radio_normal
    del Scene.pov_radio_recursion_limit
    del Scene.pov_radio_pretrace_start # MR
    del Scene.pov_radio_pretrace_end # MR
    del Scene.pov_media_enable # MR
    del Scene.pov_media_samples # MR
    del Scene.pov_media_color # MR
    del Scene.pov_baking_enable # MR
    del Scene.pov_max_trace_level # MR
    del Scene.pov_command_line_switches #CR
    del Scene.pov_indentation_character # CR
    del Scene.pov_indentation_spaces #CR
    del Scene.pov_comments_enable #CR
    del Mat.pov_irid_enable # MR
    del Mat.pov_mirror_use_IOR # MR
    del Mat.pov_mirror_metallic # MR    
    del Mat.pov_conserve_energy # MR
    del Mat.pov_irid_amount # MR
    del Mat.pov_irid_thickness # MR  
    del Mat.pov_irid_turbulence # MR
    del Mat.pov_caustics_enable # MR
    del Mat.pov_fake_caustics # MR    
    del Mat.pov_fake_caustics_power # MR
    del Mat.pov_photons_refraction # MR
    del Mat.pov_photons_dispersion # MR  
    del Mat.pov_photons_reflection # MR 
    del Mat.pov_refraction_type # MR
    del Tex.pov_tex_gamma_enable # MR
    del Tex.pov_tex_gamma_value # MR
    del Obj.pov_importance_value # MR

if __name__ == "__main__":
    register()
