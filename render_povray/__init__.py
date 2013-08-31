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
    "name": "POV-Ray 3.7",
    "author": "Campbell Barton, Silvio Falcinelli, Maurice Raybaud, Constantin Rahn, Bastien Montagne",
    "version": (0, 0, 9),
    "blender": (2, 57, 0),
    "location": "Render > Engine > POV-Ray 3.7",
    "description": "Basic POV-Ray 3.7 integration for blender",
    "warning": "both POV-Ray 3.7 and this script are beta",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/Render/POV-Ray",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"
                   "func=detail&aid=23145",
    "category": "Render"}

if "bpy" in locals():
    import imp
    imp.reload(ui)
    imp.reload(render)
    imp.reload(update_files)

else:
    import bpy
    from bpy.types import (AddonPreferences,
                           PropertyGroup,
                           )
    from bpy.props import (StringProperty,
                           BoolProperty,
                           IntProperty,
                           FloatProperty,
                           FloatVectorProperty,
                           EnumProperty,
                           PointerProperty,
                           )
    from . import ui
    from . import render
    from . import update_files
    


###############################################################################
# Scene POV properties.
###############################################################################
class RenderPovSettingsScene(PropertyGroup):
    # File Options
    tempfiles_enable = BoolProperty(
            name="Enable Tempfiles",
            description="Enable the OS-Tempfiles. Otherwise set the path where to save the files",
            default=True)
    deletefiles_enable = BoolProperty(
            name="Delete files",
            description="Delete files after rendering. Doesn't work with the image",
            default=True)
    scene_name = StringProperty(
            name="Scene Name",
            description="Name of POV-Ray scene to create. Empty name will use the name of "
                        "the blend file",
            maxlen=1024)
    scene_path = StringProperty(
            name="Export scene path",
            # description="Path to directory where the exported scene (POV and INI) is created",  # Bug in POV-Ray RC3
            description="Path to directory where the files are created",
            maxlen=1024, subtype="DIR_PATH")
    renderimage_path = StringProperty(
            name="Rendered image path",
            description="Full path to directory where the rendered image is saved",
            maxlen=1024, subtype="DIR_PATH")
    list_lf_enable = BoolProperty(
            name="LF in lists",
            description="Enable line breaks in lists (vectors and indices). Disabled: "
                        "lists are exported in one line",
            default=True)

    # Not a real pov option, just to know if we should write
    radio_enable = BoolProperty(
            name="Enable Radiosity",
            description="Enable POV-Rays radiosity calculation",
            default=False)
    radio_display_advanced = BoolProperty(
            name="Advanced Options",
            description="Show advanced options",
            default=False)
    media_enable = BoolProperty(
            name="Enable Media",
            description="Enable POV-Rays atmospheric media",
            default=False)
    media_samples = IntProperty(
            name="Samples",
            description="Number of samples taken from camera to first object "
                        "encountered along ray path for media calculation",
            min=1, max=100, default=35)

    media_color = FloatVectorProperty(
            name="Media Color", description="The atmospheric media color",
            precision=4, step=0.01, min=0, soft_max=1,
            default=(0.001, 0.001, 0.001), options={'ANIMATABLE'}, subtype='COLOR')

    baking_enable = BoolProperty(
            name="Enable Baking",
            description="Enable POV-Rays texture baking",
            default=False)
    indentation_character = EnumProperty(
            name="Indentation",
            description="Select the indentation type",
            items=(('NONE', "None", "No indentation"),
                   ('TAB', "Tabs", "Indentation with tabs"),
                   ('SPACE', "Spaces", "Indentation with spaces")),
            default='SPACE')
    indentation_spaces = IntProperty(
            name="Quantity of spaces",
            description="The number of spaces for indentation",
            min=1, max=10, default=4)

    comments_enable = BoolProperty(
            name="Enable Comments",
            description="Add comments to pov file",
            default=True)

    # Real pov options
    command_line_switches = StringProperty(
            name="Command Line Switches",
            description="Command line switches consist of a + (plus) or - (minus) sign, followed "
                        "by one or more alphabetic characters and possibly a numeric value",
            maxlen=500)

    antialias_enable = BoolProperty(
            name="Anti-Alias", description="Enable Anti-Aliasing",
            default=True)

    antialias_method = EnumProperty(
            name="Method",
            description="AA-sampling method. Type 1 is an adaptive, non-recursive, super-sampling "
                        "method. Type 2 is an adaptive and recursive super-sampling method",
            items=(("0", "non-recursive AA", "Type 1 Sampling in POV-Ray"),
                   ("1", "recursive AA", "Type 2 Sampling in POV-Ray")),
            default="1")

    antialias_depth = IntProperty(
            name="Antialias Depth", description="Depth of pixel for sampling",
            min=1, max=9, default=3)

    antialias_threshold = FloatProperty(
            name="Antialias Threshold", description="Tolerance for sub-pixels",
            min=0.0, max=1.0, soft_min=0.05, soft_max=0.5, default=0.1)

    jitter_enable = BoolProperty(
            name="Jitter",
            description="Enable Jittering. Adds noise into the sampling process (it should be "
                        "avoided to use jitter in animation)",
            default=True)

    jitter_amount = FloatProperty(
            name="Jitter Amount", description="Amount of jittering",
            min=0.0, max=1.0, soft_min=0.01, soft_max=1.0, default=1.0)

    antialias_gamma = FloatProperty(
            name="Antialias Gamma",
            description="POV-Ray compares gamma-adjusted values for super sampling. Antialias "
                        "Gamma sets the Gamma before comparison",
            min=0.0, max=5.0, soft_min=0.01, soft_max=2.5, default=2.5)

    max_trace_level = IntProperty(
            name="Max Trace Level",
            description="Number of reflections/refractions allowed on ray path",
            min=1, max=256, default=5)

    photon_spacing = FloatProperty(
            name="Spacing",
            description="Average distance between photons on surfaces. half this get four times "
                        "as many surface photons",
            min=0.001, max=1.000, soft_min=0.001, soft_max=1.000, default=0.005, precision=3)

    photon_max_trace_level = IntProperty(
            name="Max Trace Level",
            description="Number of reflections/refractions allowed on ray path",
            min=1, max=256, default=5)

    photon_adc_bailout = FloatProperty(
            name="ADC Bailout",
            description="The adc_bailout for photons. Use adc_bailout = "
                        "0.01 / brightest_ambient_object for good results",
            min=0.0, max=1000.0, soft_min=0.0, soft_max=1.0, default=0.1, precision=3)

    photon_gather_min = IntProperty(
            name="Gather Min", description="Minimum number of photons gathered for each point",
            min=1, max=256, default=20)

    photon_gather_max = IntProperty(
            name="Gather Max", description="Maximum number of photons gathered for each point",
            min=1, max=256, default=100)

    radio_adc_bailout = FloatProperty(
            name="ADC Bailout",
            description="The adc_bailout for radiosity rays. Use "
                        "adc_bailout = 0.01 / brightest_ambient_object for good results",
            min=0.0, max=1000.0, soft_min=0.0, soft_max=1.0, default=0.01, precision=3)

    radio_always_sample = BoolProperty(
            name="Always Sample",
            description="Only use the data from the pretrace step and not gather "
                        "any new samples during the final radiosity pass",
            default=True)

    radio_brightness = FloatProperty(
            name="Brightness",
            description="Amount objects are brightened before being returned "
                        "upwards to the rest of the system",
            min=0.0, max=1000.0, soft_min=0.0, soft_max=10.0, default=1.0)

    radio_count = IntProperty(
            name="Ray Count",
            description="Number of rays for each new radiosity value to be calculated "
                        "(halton sequence over 1600)",
            min=1, max=10000, soft_max=1600, default=35)

    radio_error_bound = FloatProperty(
            name="Error Bound",
            description="One of the two main speed/quality tuning values, "
                        "lower values are more accurate",
            min=0.0, max=1000.0, soft_min=0.1, soft_max=10.0, default=1.8)

    radio_gray_threshold = FloatProperty(
            name="Gray Threshold",
            description="One of the two main speed/quality tuning values, "
                        "lower values are more accurate",
            min=0.0, max=1.0, soft_min=0, soft_max=1, default=0.0)

    radio_low_error_factor = FloatProperty(
            name="Low Error Factor",
            description="Just enough samples is slightly blotchy. Low error changes error "
                        "tolerance for less critical last refining pass",
            min=0.000001, max=1.0, soft_min=0.000001, soft_max=1.0, default=0.5)

    # max_sample - not available yet
    radio_media = BoolProperty(
            name="Media", description="Radiosity estimation can be affected by media",
            default=False)

    radio_minimum_reuse = FloatProperty(
            name="Minimum Reuse",
            description="Fraction of the screen width which sets the minimum radius of reuse "
                        "for each sample point (At values higher than 2% expect errors)",
            min=0.0, max=1.0, soft_min=0.1, soft_max=0.1, default=0.015, precision=3)

    radio_nearest_count = IntProperty(
            name="Nearest Count",
            description="Number of old ambient values blended together to "
                        "create a new interpolated value",
            min=1, max=20, default=5)

    radio_normal = BoolProperty(
            name="Normals", description="Radiosity estimation can be affected by normals",
            default=False)

    radio_recursion_limit = IntProperty(
            name="Recursion Limit",
            description="how many recursion levels are used to calculate "
                        "the diffuse inter-reflection",
            min=1, max=20, default=3)

    radio_pretrace_start = FloatProperty(
            name="Pretrace Start",
            description="Fraction of the screen width which sets the size of the "
                        "blocks in the mosaic preview first pass",
            min=0.01, max=1.00, soft_min=0.02, soft_max=1.0, default=0.08)

    radio_pretrace_end = FloatProperty(
            name="Pretrace End",
            description="Fraction of the screen width which sets the size of the blocks "
                        "in the mosaic preview last pass",
            min=0.001, max=1.00, soft_min=0.01, soft_max=1.00, default=0.04, precision=3)


###############################################################################
# Material POV properties.
###############################################################################
class RenderPovSettingsMaterial(PropertyGroup):
    irid_enable = BoolProperty(
            name="Enable Iridescence",
            description="Newton's thin film interference (like an oil slick on a puddle of "
                        "water or the rainbow hues of a soap bubble.)",
            default=False)

    mirror_use_IOR = BoolProperty(
            name="Correct Reflection",
            description="Use same IOR as raytrace transparency to calculate mirror reflections. "
                        "More physically correct",
            default=False)

    mirror_metallic = BoolProperty(
            name="Metallic Reflection",
            description="mirror reflections get colored as diffuse (for metallic materials)",
            default=False)

    conserve_energy = BoolProperty(
            name="Conserve Energy",
            description="Light transmitted is more correctly reduced by mirror reflections, "
                        "also the sum of diffuse and translucency gets reduced below one ",
            default=True)

    irid_amount = FloatProperty(
            name="amount",
            description="Contribution of the iridescence effect to the overall surface color. "
                        "As a rule of thumb keep to around 0.25 (25% contribution) or less, "
                        "but experiment. If the surface is coming out too white, try lowering "
                        "the diffuse and possibly the ambient values of the surface",
            min=0.0, max=1.0, soft_min=0.01, soft_max=1.0, default=0.25)

    irid_thickness = FloatProperty(
            name="thickness",
            description="A very thin film will have a high frequency of color changes while a "
                        "thick film will have large areas of color",
            min=0.0, max=1000.0, soft_min=0.1, soft_max=10.0, default=1)

    irid_turbulence = FloatProperty(
            name="turbulence", description="This parameter varies the thickness",
            min=0.0, max=10.0, soft_min=0.000, soft_max=1.0, default=0)

    interior_fade_color = FloatVectorProperty(
            name="Fade Color", description="Color of filtered attenuation for transparent materials",
            precision=4, step=0.01, min=0.0, soft_max=1.0,
            default=(0, 0, 0), options={'ANIMATABLE'}, subtype='COLOR')

    caustics_enable = BoolProperty(
            name="Caustics",
            description="use only fake refractive caustics (default) or photon based "
                        "reflective/refractive caustics",
            default=True)

    fake_caustics = BoolProperty(
            name="Fake Caustics", description="use only (Fast) fake refractive caustics",
            default=True)

    fake_caustics_power = FloatProperty(
            name="Fake caustics power",
            description="Values typically range from 0.0 to 1.0 or higher. Zero is no caustics. "
                        "Low, non-zero values give broad hot-spots while higher values give "
                        "tighter, smaller simulated focal points",
            min=0.00, max=10.0, soft_min=0.00, soft_max=1.10, default=0.5)

    photons_refraction = BoolProperty(
            name="Refractive Photon Caustics", description="more physically correct",
            default=False)

    photons_dispersion = FloatProperty(
            name="Chromatic Dispersion",
            description="Light passing through will be separated according to wavelength. "
                        "This ratio of refractive indices for violet to red controls how much "
                        "the colors are spread out 1 = no dispersion, good values are 1.01 to 1.1",
            min=1.0000, max=10.000, soft_min=1.0000, soft_max=1.1000, precision=4, default=1.0000)

    photons_dispersion_samples = IntProperty(
            name="Dispersion Samples", description="Number of color-steps for dispersion",
            min=2, max=128, default=7)

    photons_reflection = BoolProperty(
            name="Reflective Photon Caustics",
            description="Use this to make your Sauron's ring ;-P",
            default=False)

    refraction_type = EnumProperty(
            items=[("0", "None", "use only reflective caustics"),
                   ("1", "Fake Caustics", "use fake caustics"),
                   ("2", "Photons Caustics", "use photons for refractive caustics")],
            name="Refractive",
            description="use fake caustics (fast) or true photons for refractive Caustics",
            default="1")

    ##################################CustomPOV Code############################
    replacement_text = StringProperty(
            name="Declared name:",
            description="Type the declared name in custom POV code or an external "
                        ".inc it points at. texture {} expected",
            default="")


###############################################################################
# Texture POV properties.
###############################################################################
class RenderPovSettingsTexture(PropertyGroup):
    #Custom texture gamma
    tex_gamma_enable = BoolProperty(
            name="Enable custom texture gamma",
            description="Notify some custom gamma for which texture has been precorrected "
                        "without the file format carrying it and only if it differs from your "
                        "OS expected standard (see pov doc)",
            default=False)

    tex_gamma_value = FloatProperty(
            name="Custom texture gamma",
            description="value for which the file was issued e.g. a Raw photo is gamma 1.0",
            min=0.45, max=5.00, soft_min=1.00, soft_max=2.50, default=1.00)

    ##################################CustomPOV Code############################
    #commented out below if we wanted custom pov code in texture only, inside exported material:
    #replacement_text = StringProperty(
    #        name="Declared name:",
    #        description="Type the declared name in custom POV code or an external .inc "
    #                    "it points at. pigment {} expected",
    #        default="")


###############################################################################
# Object POV properties.
###############################################################################
class RenderPovSettingsObject(PropertyGroup):
    # Importance sampling
    importance_value = FloatProperty(
            name="Radiosity Importance",
            description="Priority value relative to other objects for sampling radiosity rays. "
                        "Increase to get more radiosity rays at comparatively small yet "
                        "bright objects",
            min=0.01, max=1.00, default=0.50)

    # Collect photons
    collect_photons = BoolProperty(
            name="Receive Photon Caustics",
            description="Enable object to collect photons from other objects caustics. Turn "
                        "off for objects that don't really need to receive caustics (e.g. objects"
                        " that generate caustics often don't need to show any on themselves)",
            default=True)

    # Photons spacing_multiplier
    spacing_multiplier = FloatProperty(
            name="Photons Spacing Multiplier",
            description="Multiplier value relative to global spacing of photons. "
                        "Decrease by half to get 4x more photons at surface of "
                        "this object (or 8x media photons than specified in the globals",
            min=0.01, max=1.00, default=1.00)

    ##################################CustomPOV Code############################
    # Only DUMMIES below for now:
    replacement_text = StringProperty(
            name="Declared name:",
            description="Type the declared name in custom POV code or an external .inc "
                        "it points at. Any POV shape expected e.g: isosurface {}",
            default="")


###############################################################################
# Camera POV properties.
###############################################################################
class RenderPovSettingsCamera(PropertyGroup):
    #DOF Toggle
    dof_enable = BoolProperty(
            name="Depth Of Field", description="EnablePOV-Ray Depth Of Field ",
            default=False)

    # Aperture (Intensity of the Blur)
    dof_aperture = FloatProperty(
            name="Aperture",
            description="Similar to a real camera's aperture effect over focal blur (though not "
                        "in physical units and independant of focal length). "
                        "Increase to get more blur",
            min=0.01, max=1.00, default=0.25)

    # Aperture adaptive sampling
    dof_samples_min = IntProperty(
            name="Samples Min", description="Minimum number of rays to use for each pixel",
            min=1, max=128, default=96)

    dof_samples_max = IntProperty(
            name="Samples Max", description="Maximum number of rays to use for each pixel",
            min=1, max=128, default=128)

    dof_variance = IntProperty(
            name="Variance",
            description="Minimum threshold (fractional value) for adaptive DOF sampling (up "
                        "increases quality and render time). The value for the variance should "
                        "be in the range of the smallest displayable color difference",
            min=1, max=100000, soft_max=10000, default=256)

    dof_confidence = FloatProperty(
            name="Confidence",
            description="Probability to reach the real color value. Larger confidence values "
                        "will lead to more samples, slower traces and better images",
            min=0.01, max=0.99, default=0.90)

    ##################################CustomPOV Code############################
    # Only DUMMIES below for now:
    replacement_text = StringProperty(
            name="Texts in blend file",
            description="Type the declared name in custom POV code or an external .inc "
                        "it points at. camera {} expected",
            default="")


###############################################################################
# Text POV properties.
###############################################################################
class RenderPovSettingsText(PropertyGroup):
    custom_code = BoolProperty(
            name="Custom Code",
            description="Add this text at the top of the exported POV-Ray file",
            default=False)


###############################################################################
# Povray Preferences.
###############################################################################
class PovrayPreferences(AddonPreferences):
    bl_idname = __name__

    filepath_povray = StringProperty(
                name="Povray Location",
                description="Path to renderer executable",
                subtype='FILE_PATH',
                )
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "filepath_povray")


def register():
    bpy.utils.register_module(__name__)

    bpy.types.Scene.pov = PointerProperty(type=RenderPovSettingsScene)
    bpy.types.Material.pov = PointerProperty(type=RenderPovSettingsMaterial)
    bpy.types.Texture.pov = PointerProperty(type=RenderPovSettingsTexture)
    bpy.types.Object.pov = PointerProperty(type=RenderPovSettingsObject)
    bpy.types.Camera.pov = PointerProperty(type=RenderPovSettingsCamera)
    bpy.types.Text.pov = PointerProperty(type=RenderPovSettingsText)


def unregister():
    bpy.utils.unregister_module(__name__)

    del bpy.types.Scene.pov
    del bpy.types.Material.pov
    del bpy.types.Texture.pov
    del bpy.types.Object.pov
    del bpy.types.Camera.pov
    del bpy.types.Text.pov


if __name__ == "__main__":
    register()
