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
    'name': "Node Wrangler (aka Nodes Efficiency Tools)",
    'author': "Bartek Skorupa, Greg Zaal",
    'version': (3, 2),
    'blender': (2, 69, 0),
    'location': "Node Editor Properties Panel  or  Ctrl-SPACE",
    'description': "Various tools to enhance and speed up node-based workflow",
    'warning': "",
    'wiki_url': "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
        "Scripts/Nodes/Nodes_Efficiency_Tools",
    'tracker_url': "https://developer.blender.org/T33543",
    'category': "Node",
}

import bpy, blf, bgl
from bpy.types import Operator, Panel, Menu
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty, FloatVectorProperty
from mathutils import Vector
from math import cos, sin, pi, sqrt

#################
# rl_outputs:
# list of outputs of Input Render Layer
# with attributes determinig if pass is used,
# and MultiLayer EXR outputs names and corresponding render engines
#
# rl_outputs entry = (render_pass, rl_output_name, exr_output_name, in_internal, in_cycles)
rl_outputs = (
    ('use_pass_ambient_occlusion', 'AO', 'AO', True, True),
    ('use_pass_color', 'Color', 'Color', True, False),
    ('use_pass_combined', 'Image', 'Combined', True, True),
    ('use_pass_diffuse', 'Diffuse', 'Diffuse', True, False),
    ('use_pass_diffuse_color', 'Diffuse Color', 'DiffCol', False, True),
    ('use_pass_diffuse_direct', 'Diffuse Direct', 'DiffDir', False, True),
    ('use_pass_diffuse_indirect', 'Diffuse Indirect', 'DiffInd', False, True),
    ('use_pass_emit', 'Emit', 'Emit', True, False),
    ('use_pass_environment', 'Environment', 'Env', True, False),
    ('use_pass_glossy_color', 'Glossy Color', 'GlossCol', False, True),
    ('use_pass_glossy_direct', 'Glossy Direct', 'GlossDir', False, True),
    ('use_pass_glossy_indirect', 'Glossy Indirect', 'GlossInd', False, True),
    ('use_pass_indirect', 'Indirect', 'Indirect', True, False),
    ('use_pass_material_index', 'IndexMA', 'IndexMA', True, True),
    ('use_pass_mist', 'Mist', 'Mist', True, False),
    ('use_pass_normal', 'Normal', 'Normal', True, True),
    ('use_pass_object_index', 'IndexOB', 'IndexOB', True, True),
    ('use_pass_reflection', 'Reflect', 'Reflect', True, False),
    ('use_pass_refraction', 'Refract', 'Refract', True, False),
    ('use_pass_shadow', 'Shadow', 'Shadow', True, True),
    ('use_pass_specular', 'Specular', 'Spec', True, False),
    ('use_pass_subsurface_color', 'Subsurface Color', 'SubsurfaceCol', False, True),
    ('use_pass_subsurface_direct', 'Subsurface Direct', 'SubsurfaceDir', False, True),
    ('use_pass_subsurface_indirect', 'Subsurface Indirect', 'SubsurfaceInd', False, True),
    ('use_pass_transmission_color', 'Transmission Color', 'TransCol', False, True),
    ('use_pass_transmission_direct', 'Transmission Direct', 'TransDir', False, True),
    ('use_pass_transmission_indirect', 'Transmission Indirect', 'TransInd', False, True),
    ('use_pass_uv', 'UV', 'UV', True, True),
    ('use_pass_vector', 'Speed', 'Vector', True, True),
    ('use_pass_z', 'Z', 'Depth', True, True),
)

# shader nodes
# (rna_type.identifier, type, rna_type.name)
# Keeping mixed case to avoid having to translate entries when adding new nodes in operators.
shaders_input_nodes_props = (
    ('ShaderNodeTexCoord', 'TEX_COORD', 'Texture Coordinate'),
    ('ShaderNodeAttribute', 'ATTRIBUTE', 'Attribute'),
    ('ShaderNodeLightPath', 'LIGHT_PATH', 'Light Path'),
    ('ShaderNodeFresnel', 'FRESNEL', 'Fresnel'),
    ('ShaderNodeLayerWeight', 'LAYER_WEIGHT', 'Layer Weight'),
    ('ShaderNodeRGB', 'RGB', 'RGB'),
    ('ShaderNodeValue', 'VALUE', 'Value'),
    ('ShaderNodeTangent', 'TANGENT', 'Tangent'),
    ('ShaderNodeNewGeometry', 'NEW_GEOMETRY', 'Geometry'),
    ('ShaderNodeWireframe', 'WIREFRAME', 'Wireframe'),
    ('ShaderNodeObjectInfo', 'OBJECT_INFO', 'Object Info'),
    ('ShaderNodeHairInfo', 'HAIR_INFO', 'Hair Info'),
    ('ShaderNodeParticleInfo', 'PARTICLE_INFO', 'Particle Info'),
    ('ShaderNodeCameraData', 'CAMERA', 'Camera Data'),
)
# (rna_type.identifier, type, rna_type.name)
# Keeping mixed case to avoid having to translate entries when adding new nodes in operators.
shaders_output_nodes_props = (
    ('ShaderNodeOutputMaterial', 'OUTPUT_MATERIAL', 'Material Output'),
    ('ShaderNodeOutputLamp', 'OUTPUT_LAMP', 'Lamp Output'),
    ('ShaderNodeOutputWorld', 'OUTPUT_WORLD', 'World Output'),
)
# (rna_type.identifier, type, rna_type.name)
# Keeping mixed case to avoid having to translate entries when adding new nodes in operators.
shaders_shader_nodes_props = (
    ('ShaderNodeMixShader', 'MIX_SHADER', 'Mix Shader'),
    ('ShaderNodeAddShader', 'ADD_SHADER', 'Add Shader'),
    ('ShaderNodeBsdfDiffuse', 'BSDF_DIFFUSE', 'Diffuse BSDF'),
    ('ShaderNodeBsdfGlossy', 'BSDF_GLOSSY', 'Glossy BSDF'),
    ('ShaderNodeBsdfTransparent', 'BSDF_TRANSPARENT', 'Transparent BSDF'),
    ('ShaderNodeBsdfRefraction', 'BSDF_REFRACTION', 'Refraction BSDF'),
    ('ShaderNodeBsdfGlass', 'BSDF_GLASS', 'Glass BSDF'),
    ('ShaderNodeBsdfTranslucent', 'BSDF_TRANSLUCENT', 'Translucent BSDF'),
    ('ShaderNodeBsdfAnisotropic', 'BSDF_ANISOTROPIC', 'Anisotropic BSDF'),
    ('ShaderNodeBsdfVelvet', 'BSDF_VELVET', 'Velvet BSDF'),
    ('ShaderNodeBsdfToon', 'BSDF_TOON', 'Toon BSDF'),
    ('ShaderNodeSubsurfaceScattering', 'SUBSURFACE_SCATTERING', 'Subsurface Scattering'),
    ('ShaderNodeEmission', 'EMISSION', 'Emission'),
    ('ShaderNodeBsdfHair', 'BSDF_HAIR', 'Hair BSDF'),
    ('ShaderNodeBackground', 'BACKGROUND', 'Background'),
    ('ShaderNodeAmbientOcclusion', 'AMBIENT_OCCLUSION', 'Ambient Occlusion'),
    ('ShaderNodeHoldout', 'HOLDOUT', 'Holdout'),
    ('ShaderNodeVolumeAbsorption', 'VOLUME_ABSORPTION', 'Volume Absorption'),
    ('ShaderNodeVolumeScatter', 'VOLUME_SCATTER', 'Volume Scatter'),
)
# (rna_type.identifier, type, rna_type.name)
# Keeping mixed case to avoid having to translate entries when adding new nodes in operators.
shaders_texture_nodes_props = (
    ('ShaderNodeTexImage', 'TEX_IMAGE', 'Image'),
    ('ShaderNodeTexEnvironment', 'TEX_ENVIRONMENT', 'Environment'),
    ('ShaderNodeTexSky', 'TEX_SKY', 'Sky'),
    ('ShaderNodeTexNoise', 'TEX_NOISE', 'Noise'),
    ('ShaderNodeTexWave', 'TEX_WAVE', 'Wave'),
    ('ShaderNodeTexVoronoi', 'TEX_VORONOI', 'Voronoi'),
    ('ShaderNodeTexMusgrave', 'TEX_MUSGRAVE', 'Musgrave'),
    ('ShaderNodeTexGradient', 'TEX_GRADIENT', 'Gradient'),
    ('ShaderNodeTexMagic', 'TEX_MAGIC', 'Magic'),
    ('ShaderNodeTexChecker', 'TEX_CHECKER', 'Checker'),
    ('ShaderNodeTexBrick', 'TEX_BRICK', 'Brick')
)
# (rna_type.identifier, type, rna_type.name)
# Keeping mixed case to avoid having to translate entries when adding new nodes in operators.
shaders_color_nodes_props = (
    ('ShaderNodeMixRGB', 'MIX_RGB', 'MixRGB'),
    ('ShaderNodeRGBCurve', 'CURVE_RGB', 'RGB Curves'),
    ('ShaderNodeInvert', 'INVERT', 'Invert'),
    ('ShaderNodeLightFalloff', 'LIGHT_FALLOFF', 'Light Falloff'),
    ('ShaderNodeHueSaturation', 'HUE_SAT', 'Hue/Saturation'),
    ('ShaderNodeGamma', 'GAMMA', 'Gamma'),
    ('ShaderNodeBrightContrast', 'BRIGHTCONTRAST', 'Bright Contrast'),
)
# (rna_type.identifier, type, rna_type.name)
# Keeping mixed case to avoid having to translate entries when adding new nodes in operators.
shaders_vector_nodes_props = (
    ('ShaderNodeMapping', 'MAPPING', 'Mapping'),
    ('ShaderNodeBump', 'BUMP', 'Bump'),
    ('ShaderNodeNormalMap', 'NORMAL_MAP', 'Normal Map'),
    ('ShaderNodeNormal', 'NORMAL', 'Normal'),
    ('ShaderNodeVectorCurve', 'CURVE_VEC', 'Vector Curves'),
    ('ShaderNodeVectorTransform', 'VECT_TRANSFORM', 'Vector Transform'),
)
# (rna_type.identifier, type, rna_type.name)
# Keeping mixed case to avoid having to translate entries when adding new nodes in operators.
shaders_converter_nodes_props = (
    ('ShaderNodeMath', 'MATH', 'Math'),
    ('ShaderNodeValToRGB', 'VALTORGB', 'ColorRamp'),
    ('ShaderNodeRGBToBW', 'RGBTOBW', 'RGB to BW'),
    ('ShaderNodeVectorMath', 'VECT_MATH', 'Vector Math'),
    ('ShaderNodeSeparateRGB', 'SEPRGB', 'Separate RGB'),
    ('ShaderNodeCombineRGB', 'COMBRGB', 'Combine RGB'),
    ('ShaderNodeSeparateHSV', 'SEPHSV', 'Separate HSV'),
    ('ShaderNodeCombineHSV', 'COMBHSV', 'Combine HSV'),
    ('ShaderNodeWavelength', 'WAVELENGTH', 'Wavelength'),
    ('ShaderNodeBlackbody', 'BLACKBODY', 'Blackbody'),
)
# (rna_type.identifier, type, rna_type.name)
# Keeping mixed case to avoid having to translate entries when adding new nodes in operators.
shaders_layout_nodes_props = (
    ('NodeFrame', 'FRAME', 'Frame'),
    ('NodeReroute', 'REROUTE', 'Reroute'),
)

# compositing nodes
# (rna_type.identifier, type, rna_type.name)
# Keeping mixed case to avoid having to translate entries when adding new nodes in operators.
compo_input_nodes_props = (
    ('CompositorNodeRLayers', 'R_LAYERS', 'Render Layers'),
    ('CompositorNodeImage', 'IMAGE', 'Image'),
    ('CompositorNodeMovieClip', 'MOVIECLIP', 'Movie Clip'),
    ('CompositorNodeMask', 'MASK', 'Mask'),
    ('CompositorNodeRGB', 'RGB', 'RGB'),
    ('CompositorNodeValue', 'VALUE', 'Value'),
    ('CompositorNodeTexture', 'TEXTURE', 'Texture'),
    ('CompositorNodeBokehImage', 'BOKEHIMAGE', 'Bokeh Image'),
    ('CompositorNodeTime', 'TIME', 'Time'),
    ('CompositorNodeTrackPos', 'TRACKPOS', 'Track Position'),
)
# (rna_type.identifier, type, rna_type.name)
# Keeping mixed case to avoid having to translate entries when adding new nodes in operators.
compo_output_nodes_props = (
    ('CompositorNodeComposite', 'COMPOSITE', 'Composite'),
    ('CompositorNodeViewer', 'VIEWER', 'Viewer'),
    ('CompositorNodeSplitViewer', 'SPLITVIEWER', 'Split Viewer'),
    ('CompositorNodeOutputFile', 'OUTPUT_FILE', 'File Output'),
    ('CompositorNodeLevels', 'LEVELS', 'Levels'),
)
# (rna_type.identifier, type, rna_type.name)
# Keeping mixed case to avoid having to translate entries when adding new nodes in operators.
compo_color_nodes_props = (
    ('CompositorNodeMixRGB', 'MIX_RGB', 'Mix'),
    ('CompositorNodeAlphaOver', 'ALPHAOVER', 'Alpha Over'),
    ('CompositorNodeInvert', 'INVERT', 'Invert'),
    ('CompositorNodeCurveRGB', 'CURVE_RGB', 'RGB Curves'),
    ('CompositorNodeHueSat', 'HUE_SAT', 'Hue Saturation Value'),
    ('CompositorNodeColorBalance', 'COLORBALANCE', 'Color Balance'),
    ('CompositorNodeHueCorrect', 'HUECORRECT', 'Hue Correct'),
    ('CompositorNodeBrightContrast', 'BRIGHTCONTRAST', 'Bright/Contrast'),
    ('CompositorNodeGamma', 'GAMMA', 'Gamma'),
    ('CompositorNodeColorCorrection', 'COLORCORRECTION', 'Color Correction'),
    ('CompositorNodeTonemap', 'TONEMAP', 'Tonemap'),
    ('CompositorNodeZcombine', 'ZCOMBINE', 'Z Combine'),
)
# (rna_type.identifier, type, rna_type.name)
# Keeping mixed case to avoid having to translate entries when adding new nodes in operators.
compo_converter_nodes_props = (
    ('CompositorNodeMath', 'MATH', 'Math'),
    ('CompositorNodeValToRGB', 'VALTORGB', 'ColorRamp'),
    ('CompositorNodeSetAlpha', 'SETALPHA', 'Set Alpha'),
    ('CompositorNodePremulKey', 'PREMULKEY', 'Alpha Convert'),
    ('CompositorNodeIDMask', 'ID_MASK', 'ID Mask'),
    ('CompositorNodeRGBToBW', 'RGBTOBW', 'RGB to BW'),
    ('CompositorNodeSepRGBA', 'SEPRGBA', 'Separate RGBA'),
    ('CompositorNodeCombRGBA', 'COMBRGBA', 'Combine RGBA'),
    ('CompositorNodeSepHSVA', 'SEPHSVA', 'Separate HSVA'),
    ('CompositorNodeCombHSVA', 'COMBHSVA', 'Combine HSVA'),
    ('CompositorNodeSepYUVA', 'SEPYUVA', 'Separate YUVA'),
    ('CompositorNodeCombYUVA', 'COMBYUVA', 'Combine YUVA'),
    ('CompositorNodeSepYCCA', 'SEPYCCA', 'Separate YCbCrA'),
    ('CompositorNodeCombYCCA', 'COMBYCCA', 'Combine YCbCrA'),
)
# (rna_type.identifier, type, rna_type.name)
# Keeping mixed case to avoid having to translate entries when adding new nodes in operators.
compo_filter_nodes_props = (
    ('CompositorNodeBlur', 'BLUR', 'Blur'),
    ('CompositorNodeBilateralblur', 'BILATERALBLUR', 'Bilateral Blur'),
    ('CompositorNodeDilateErode', 'DILATEERODE', 'Dilate/Erode'),
    ('CompositorNodeDespeckle', 'DESPECKLE', 'Despeckle'),
    ('CompositorNodeFilter', 'FILTER', 'Filter'),
    ('CompositorNodeBokehBlur', 'BOKEHBLUR', 'Bokeh Blur'),
    ('CompositorNodeVecBlur', 'VECBLUR', 'Vector Blur'),
    ('CompositorNodeDefocus', 'DEFOCUS', 'Defocus'),
    ('CompositorNodeGlare', 'GLARE', 'Glare'),
    ('CompositorNodeInpaint', 'INPAINT', 'Inpaint'),
    ('CompositorNodeDBlur', 'DBLUR', 'Directional Blur'),
    ('CompositorNodePixelate', 'PIXELATE', 'Pixelate'),
)
# (rna_type.identifier, type, rna_type.name)
# Keeping mixed case to avoid having to translate entries when adding new nodes in operators.
compo_vector_nodes_props = (
    ('CompositorNodeNormal', 'NORMAL', 'Normal'),
    ('CompositorNodeMapValue', 'MAP_VALUE', 'Map Value'),
    ('CompositorNodeMapRange', 'MAP_RANGE', 'Map Range'),
    ('CompositorNodeNormalize', 'NORMALIZE', 'Normalize'),
    ('CompositorNodeCurveVec', 'CURVE_VEC', 'Vector Curves'),
)
# (rna_type.identifier, type, rna_type.name)
# Keeping mixed case to avoid having to translate entries when adding new nodes in operators.
compo_matte_nodes_props = (
    ('CompositorNodeKeying', 'KEYING', 'Keying'),
    ('CompositorNodeKeyingScreen', 'KEYINGSCREEN', 'Keying Screen'),
    ('CompositorNodeChannelMatte', 'CHANNEL_MATTE', 'Channel Key'),
    ('CompositorNodeColorSpill', 'COLOR_SPILL', 'Color Spill'),
    ('CompositorNodeBoxMask', 'BOXMASK', 'Box Mask'),
    ('CompositorNodeEllipseMask', 'ELLIPSEMASK', 'Ellipse Mask'),
    ('CompositorNodeLumaMatte', 'LUMA_MATTE', 'Luminance Key'),
    ('CompositorNodeDiffMatte', 'DIFF_MATTE', 'Difference Key'),
    ('CompositorNodeDistanceMatte', 'DISTANCE_MATTE', 'Distance Key'),
    ('CompositorNodeChromaMatte', 'CHROMA_MATTE', 'Chroma Key'),
    ('CompositorNodeColorMatte', 'COLOR_MATTE', 'Color Key'),
    ('CompositorNodeDoubleEdgeMask', 'DOUBLEEDGEMASK', 'Double Edge Mask'),
)
# (rna_type.identifier, type, rna_type.name)
# Keeping mixed case to avoid having to translate entries when adding new nodes in operators.
compo_distort_nodes_props = (
    ('CompositorNodeScale', 'SCALE', 'Scale'),
    ('CompositorNodeLensdist', 'LENSDIST', 'Lens Distortion'),
    ('CompositorNodeMovieDistortion', 'MOVIEDISTORTION', 'Movie Distortion'),
    ('CompositorNodeTranslate', 'TRANSLATE', 'Translate'),
    ('CompositorNodeRotate', 'ROTATE', 'Rotate'),
    ('CompositorNodeFlip', 'FLIP', 'Flip'),
    ('CompositorNodeCrop', 'CROP', 'Crop'),
    ('CompositorNodeDisplace', 'DISPLACE', 'Displace'),
    ('CompositorNodeMapUV', 'MAP_UV', 'Map UV'),
    ('CompositorNodeTransform', 'TRANSFORM', 'Transform'),
    ('CompositorNodeStabilize', 'STABILIZE2D', 'Stabilize 2D'),
    ('CompositorNodePlaneTrackDeform', 'PLANETRACKDEFORM', 'Plane Track Deform'),
)
# (rna_type.identifier, type, rna_type.name)
# Keeping mixed case to avoid having to translate entries when adding new nodes in operators.
compo_layout_nodes_props = (
    ('NodeFrame', 'FRAME', 'Frame'),
    ('NodeReroute', 'REROUTE', 'Reroute'),
    ('CompositorNodeSwitch', 'SWITCH', 'Switch'),
)

# list of blend types of "Mix" nodes in a form that can be used as 'items' for EnumProperty.
# used list, not tuple for easy merging with other lists.
blend_types = [
    ('MIX', 'Mix', 'Mix Mode'),
    ('ADD', 'Add', 'Add Mode'),
    ('MULTIPLY', 'Multiply', 'Multiply Mode'),
    ('SUBTRACT', 'Subtract', 'Subtract Mode'),
    ('SCREEN', 'Screen', 'Screen Mode'),
    ('DIVIDE', 'Divide', 'Divide Mode'),
    ('DIFFERENCE', 'Difference', 'Difference Mode'),
    ('DARKEN', 'Darken', 'Darken Mode'),
    ('LIGHTEN', 'Lighten', 'Lighten Mode'),
    ('OVERLAY', 'Overlay', 'Overlay Mode'),
    ('DODGE', 'Dodge', 'Dodge Mode'),
    ('BURN', 'Burn', 'Burn Mode'),
    ('HUE', 'Hue', 'Hue Mode'),
    ('SATURATION', 'Saturation', 'Saturation Mode'),
    ('VALUE', 'Value', 'Value Mode'),
    ('COLOR', 'Color', 'Color Mode'),
    ('SOFT_LIGHT', 'Soft Light', 'Soft Light Mode'),
    ('LINEAR_LIGHT', 'Linear Light', 'Linear Light Mode'),
]

# list of operations of "Math" nodes in a form that can be used as 'items' for EnumProperty.
# used list, not tuple for easy merging with other lists.
operations = [
    ('ADD', 'Add', 'Add Mode'),
    ('MULTIPLY', 'Multiply', 'Multiply Mode'),
    ('SUBTRACT', 'Subtract', 'Subtract Mode'),
    ('DIVIDE', 'Divide', 'Divide Mode'),
    ('SINE', 'Sine', 'Sine Mode'),
    ('COSINE', 'Cosine', 'Cosine Mode'),
    ('TANGENT', 'Tangent', 'Tangent Mode'),
    ('ARCSINE', 'Arcsine', 'Arcsine Mode'),
    ('ARCCOSINE', 'Arccosine', 'Arccosine Mode'),
    ('ARCTANGENT', 'Arctangent', 'Arctangent Mode'),
    ('POWER', 'Power', 'Power Mode'),
    ('LOGARITHM', 'Logatithm', 'Logarithm Mode'),
    ('MINIMUM', 'Minimum', 'Minimum Mode'),
    ('MAXIMUM', 'Maximum', 'Maximum Mode'),
    ('ROUND', 'Round', 'Round Mode'),
    ('LESS_THAN', 'Less Than', 'Less Than Mode'),
    ('GREATER_THAN', 'Greater Than', 'Greater Than Mode'),
]

# in NWBatchChangeNodes additional types/operations. Can be used as 'items' for EnumProperty.
# used list, not tuple for easy merging with other lists.
navs = [
    ('CURRENT', 'Current', 'Leave at current state'),
    ('NEXT', 'Next', 'Next blend type/operation'),
    ('PREV', 'Prev', 'Previous blend type/operation'),
]

draw_color_sets = {
    "red_white": (
        (1.0, 1.0, 1.0, 0.7),
        (1.0, 0.0, 0.0, 0.7),
        (0.8, 0.2, 0.2, 1.0)
    ),
    "green": (
        (0.0, 0.0, 0.0, 1.0),
        (0.38, 0.77, 0.38, 1.0),
        (0.38, 0.77, 0.38, 1.0)
    ),
    "yellow": (
        (0.0, 0.0, 0.0, 1.0),
        (0.77, 0.77, 0.16, 1.0),
        (0.77, 0.77, 0.16, 1.0)
    ),
    "purple": (
        (0.0, 0.0, 0.0, 1.0),
        (0.38, 0.38, 0.77, 1.0),
        (0.38, 0.38, 0.77, 1.0)
    ),
    "grey": (
        (0.0, 0.0, 0.0, 1.0),
        (0.63, 0.63, 0.63, 1.0),
        (0.63, 0.63, 0.63, 1.0)
    ),
    "black": (
        (1.0, 1.0, 1.0, 0.7),
        (0.0, 0.0, 0.0, 0.7),
        (0.2, 0.2, 0.2, 1.0)
    )
}


def nice_hotkey_name(punc):
    # convert the ugly string name into the actual character
    pairs = (
        ('LEFTMOUSE', "LMB"),
        ('MIDDLEMOUSE', "MMB"),
        ('RIGHTMOUSE', "RMB"),
        ('SELECTMOUSE', "Select"),
        ('WHEELUPMOUSE', "Wheel Up"),
        ('WHEELDOWNMOUSE', "Wheel Down"),
        ('WHEELINMOUSE', "Wheel In"),
        ('WHEELOUTMOUSE', "Wheel Out"),
        ('ZERO', "0"),
        ('ONE', "1"),
        ('TWO', "2"),
        ('THREE', "3"),
        ('FOUR', "4"),
        ('FIVE', "5"),
        ('SIX', "6"),
        ('SEVEN', "7"),
        ('EIGHT', "8"),
        ('NINE', "9"),
        ('OSKEY', "Super"),
        ('RET', "Enter"),
        ('LINE_FEED', "Enter"),
        ('SEMI_COLON', ";"),
        ('PERIOD', "."),
        ('COMMA', ","),
        ('QUOTE', '"'),
        ('MINUS', "-"),
        ('SLASH', "/"),
        ('BACK_SLASH', "\\"),
        ('EQUAL', "="),
        ('NUMPAD_1', "Numpad 1"),
        ('NUMPAD_2', "Numpad 2"),
        ('NUMPAD_3', "Numpad 3"),
        ('NUMPAD_4', "Numpad 4"),
        ('NUMPAD_5', "Numpad 5"),
        ('NUMPAD_6', "Numpad 6"),
        ('NUMPAD_7', "Numpad 7"),
        ('NUMPAD_8', "Numpad 8"),
        ('NUMPAD_9', "Numpad 9"),
        ('NUMPAD_0', "Numpad 0"),
        ('NUMPAD_PERIOD', "Numpad ."),
        ('NUMPAD_SLASH', "Numpad /"),
        ('NUMPAD_ASTERIX', "Numpad *"),
        ('NUMPAD_MINUS', "Numpad -"),
        ('NUMPAD_ENTER', "Numpad Enter"),
        ('NUMPAD_PLUS', "Numpad +"),
    )
    nice_punc = False
    for (ugly, nice) in pairs:
        if punc == ugly:
            nice_punc = nice
            break
    if not nice_punc:
        nice_punc = punc.replace("_", " ").title()
    return nice_punc


def hack_force_update(context, nodes):
    if context.space_data.tree_type == "ShaderNodeTree":
        node = nodes.new('ShaderNodeMath')
        node.inputs[0].default_value = 0.0
        nodes.remove(node)
    return False


def dpifac():
    return bpy.context.user_preferences.system.dpi/72


def is_end_node(node):
    bool = True
    for output in node.outputs:
        if output.links:
            bool = False
            break
    return bool


def node_mid_pt(node, axis):
    if axis == 'x':
        d = node.location.x + (node.dimensions.x / 2)
    elif axis == 'y':
        d = node.location.y - (node.dimensions.y / 2)
    else:
        d = 0
    return d


def autolink(node1, node2, links):
    link_made = False

    for outp in node1.outputs:
        for inp in node2.inputs:
            if not inp.is_linked and inp.name == outp.name:
                link_made = True
                links.new(outp, inp)
                return True

    for outp in node1.outputs:
        for inp in node2.inputs:
            if not inp.is_linked and inp.type == outp.type:
                link_made = True
                links.new(outp, inp)
                return True

    # force some connection even if the type doesn't match
    for outp in node1.outputs:
        for inp in node2.inputs:
            if not inp.is_linked:
                link_made = True
                links.new(outp, inp)
                return True

    # even if no sockets are open, force one of matching type
    for outp in node1.outputs:
        for inp in node2.inputs:
            if inp.type == outp.type:
                link_made = True
                links.new(outp, inp)
                return True

    # do something!
    for outp in node1.outputs:
        for inp in node2.inputs:
            link_made = True
            links.new(outp, inp)
            return True

    print("Could not make a link from " + node1.name + " to " + node2.name)
    return link_made


def node_at_pos(nodes, context, event):
    nodes_near_mouse = []
    nodes_under_mouse = []
    target_node = None

    store_mouse_cursor(context, event)
    x, y = context.space_data.cursor_location
    x = x
    y = y

    # Make a list of each corner (and middle of border) for each node.
    # Will be sorted to find nearest point and thus nearest node
    node_points_with_dist = []
    for node in nodes:
        locx = node.location.x
        locy = node.location.y
        dimx = node.dimensions.x/dpifac()
        dimy = node.dimensions.y/dpifac()
        node_points_with_dist.append([node, sqrt((x - locx) ** 2 + (y - locy) ** 2)])  # Top Left
        node_points_with_dist.append([node, sqrt((x - (locx+dimx)) ** 2 + (y - locy) ** 2)])  # Top Right
        node_points_with_dist.append([node, sqrt((x - locx) ** 2 + (y - (locy-dimy)) ** 2)])  # Bottom Left
        node_points_with_dist.append([node, sqrt((x - (locx+dimx)) ** 2 + (y - (locy-dimy)) ** 2)])  # Bottom Right

        node_points_with_dist.append([node, sqrt((x - (locx+(dimx/2))) ** 2 + (y - locy) ** 2)])  # Mid Top
        node_points_with_dist.append([node, sqrt((x - (locx+(dimx/2))) ** 2 + (y - (locy-dimy)) ** 2)])  # Mid Bottom
        node_points_with_dist.append([node, sqrt((x - locx) ** 2 + (y - (locy-(dimy/2))) ** 2)])  # Mid Left
        node_points_with_dist.append([node, sqrt((x - (locx+dimx)) ** 2 + (y - (locy-(dimy/2))) ** 2)])  # Mid Right

        #node_points_with_dist.append([node, sqrt((x - (locx+(dimx/2))) ** 2 + (y - (locy-(dimy/2))) ** 2)])  # Center

    nearest_node = sorted(node_points_with_dist, key=lambda k: k[1])[0][0]

    for node in nodes:
        locx = node.location.x
        locy = node.location.y
        dimx = node.dimensions.x/dpifac()
        dimy = node.dimensions.y/dpifac()
        if (locx <= x <= locx + dimx) and \
           (locy - dimy <= y <= locy):
            nodes_under_mouse.append(node)

    if len(nodes_under_mouse) == 1:
        if nodes_under_mouse[0] != nearest_node:
            target_node = nodes_under_mouse[0]  # use the node under the mouse if there is one and only one
        else:
            target_node = nearest_node  # else use the nearest node
    else:
        target_node = nearest_node
    return target_node


def store_mouse_cursor(context, event):
    space = context.space_data
    v2d = context.region.view2d
    tree = space.edit_tree

    # convert mouse position to the View2D for later node placement
    if context.region.type == 'WINDOW':
        space.cursor_location_from_region(event.mouse_region_x, event.mouse_region_y)
    else:
        space.cursor_location = tree.view_center


def draw_line(x1, y1, x2, y2, size, colour=[1.0, 1.0, 1.0, 0.7]):
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glLineWidth(size)
    bgl.glShadeModel(bgl.GL_SMOOTH)

    bgl.glBegin(bgl.GL_LINE_STRIP)
    try:
        bgl.glColor4f(colour[0]+(1.0-colour[0])/4, colour[1]+(1.0-colour[1])/4, colour[2]+(1.0-colour[2])/4, colour[3]+(1.0-colour[3])/4)
        bgl.glVertex2f(x1, y1)
        bgl.glColor4f(colour[0], colour[1], colour[2], colour[3])
        bgl.glVertex2f(x2, y2)
    except:
        pass
    bgl.glEnd()
    bgl.glShadeModel(bgl.GL_FLAT)


def draw_circle(mx, my, radius, colour=[1.0, 1.0, 1.0, 0.7]):
    bgl.glBegin(bgl.GL_TRIANGLE_FAN)
    bgl.glColor4f(colour[0], colour[1], colour[2], colour[3])
    radius = radius
    sides = 32
    for i in range(sides + 1):
        cosine = radius * cos(i * 2 * pi / sides) + mx
        sine = radius * sin(i * 2 * pi / sides) + my
        bgl.glVertex2f(cosine, sine)
    bgl.glEnd()


def draw_rounded_node_border(node, radius=8, colour=[1.0, 1.0, 1.0, 0.7]):
    bgl.glEnable(bgl.GL_BLEND)
    settings = bpy.context.user_preferences.addons[__name__].preferences
    if settings.bgl_antialiasing:
        bgl.glEnable(bgl.GL_LINE_SMOOTH)
    sides = 16
    bgl.glColor4f(colour[0], colour[1], colour[2], colour[3])

    nlocx = (node.location.x+1)*dpifac()
    nlocy = (node.location.y+1)*dpifac()
    ndimx = node.dimensions.x
    ndimy = node.dimensions.y

    bgl.glBegin(bgl.GL_TRIANGLE_FAN)
    mx, my = bpy.context.region.view2d.view_to_region(nlocx, nlocy)
    bgl.glVertex2f(mx,my)
    for i in range(sides+1):
        if (4<=i<=8):
            if mx != 12000 and my != 12000:  # nodes that go over the view border give 12000 as coords
                cosine = radius * cos(i * 2 * pi / sides) + mx
                sine = radius * sin(i * 2 * pi / sides) + my
                bgl.glVertex2f(cosine, sine)
    bgl.glEnd()

    bgl.glBegin(bgl.GL_TRIANGLE_FAN)
    mx, my = bpy.context.region.view2d.view_to_region(nlocx + ndimx, nlocy)
    bgl.glVertex2f(mx,my)
    for i in range(sides+1):
        if (0<=i<=4):
            if mx != 12000 and my != 12000:
                cosine = radius * cos(i * 2 * pi / sides) + mx
                sine = radius * sin(i * 2 * pi / sides) + my
                bgl.glVertex2f(cosine, sine)

    bgl.glEnd()
    bgl.glBegin(bgl.GL_TRIANGLE_FAN)
    mx, my = bpy.context.region.view2d.view_to_region(nlocx, nlocy - ndimy)
    bgl.glVertex2f(mx,my)
    for i in range(sides+1):
        if (8<=i<=12):
            if mx != 12000 and my != 12000:
                cosine = radius * cos(i * 2 * pi / sides) + mx
                sine = radius * sin(i * 2 * pi / sides) + my
                bgl.glVertex2f(cosine, sine)
    bgl.glEnd()

    bgl.glBegin(bgl.GL_TRIANGLE_FAN)
    mx, my = bpy.context.region.view2d.view_to_region(nlocx + ndimx, nlocy - ndimy)
    bgl.glVertex2f(mx,my)
    for i in range(sides+1):
        if (12<=i<=16):
            if mx != 12000 and my != 12000:
                cosine = radius * cos(i * 2 * pi / sides) + mx
                sine = radius * sin(i * 2 * pi / sides) + my
                bgl.glVertex2f(cosine, sine)
    bgl.glEnd()


    bgl.glBegin(bgl.GL_QUADS)
    m1x, m1y = bpy.context.region.view2d.view_to_region(nlocx, nlocy)
    m2x, m2y = bpy.context.region.view2d.view_to_region(nlocx, nlocy - ndimy)
    if m1x != 12000 and m1y != 12000 and m2x != 12000 and m2y != 12000:
        bgl.glVertex2f(m2x-radius,m2y)  # draw order is important, start with bottom left and go anti-clockwise
        bgl.glVertex2f(m2x,m2y)
        bgl.glVertex2f(m1x,m1y)
        bgl.glVertex2f(m1x-radius,m1y)
    bgl.glEnd()

    bgl.glBegin(bgl.GL_QUADS)
    m1x, m1y = bpy.context.region.view2d.view_to_region(nlocx, nlocy)
    m2x, m2y = bpy.context.region.view2d.view_to_region(nlocx + ndimx, nlocy)
    if m1x != 12000 and m1y != 12000 and m2x != 12000 and m2y != 12000:
        bgl.glVertex2f(m1x,m2y)  # draw order is important, start with bottom left and go anti-clockwise
        bgl.glVertex2f(m2x,m2y)
        bgl.glVertex2f(m2x,m1y+radius)
        bgl.glVertex2f(m1x,m1y+radius)
    bgl.glEnd()

    bgl.glBegin(bgl.GL_QUADS)
    m1x, m1y = bpy.context.region.view2d.view_to_region(nlocx + ndimx, nlocy)
    m2x, m2y = bpy.context.region.view2d.view_to_region(nlocx + ndimx, nlocy - ndimy)
    if m1x != 12000 and m1y != 12000 and m2x != 12000 and m2y != 12000:
        bgl.glVertex2f(m2x,m2y)  # draw order is important, start with bottom left and go anti-clockwise
        bgl.glVertex2f(m2x+radius,m2y)
        bgl.glVertex2f(m1x+radius,m1y)
        bgl.glVertex2f(m1x,m1y)
    bgl.glEnd()

    bgl.glBegin(bgl.GL_QUADS)
    m1x, m1y = bpy.context.region.view2d.view_to_region(nlocx, nlocy-ndimy)
    m2x, m2y = bpy.context.region.view2d.view_to_region(nlocx + ndimx, nlocy-ndimy)
    if m1x != 12000 and m1y != 12000 and m2x != 12000 and m2y != 12000:
        bgl.glVertex2f(m1x,m2y)  # draw order is important, start with bottom left and go anti-clockwise
        bgl.glVertex2f(m2x,m2y)
        bgl.glVertex2f(m2x,m1y-radius)
        bgl.glVertex2f(m1x,m1y-radius)
    bgl.glEnd()

    bgl.glDisable(bgl.GL_BLEND)
    if settings.bgl_antialiasing:
        bgl.glDisable(bgl.GL_LINE_SMOOTH)


def draw_callback_mixnodes(self, context, mode):
    if self.mouse_path:
        nodes = context.space_data.node_tree.nodes
        settings = context.user_preferences.addons[__name__].preferences
        if settings.bgl_antialiasing:
            bgl.glEnable(bgl.GL_LINE_SMOOTH)

        if mode == "LINK":
            col_outer = [1.0, 0.2, 0.2, 0.4]
            col_inner = [0.0, 0.0, 0.0, 0.5]
            col_circle_inner = [0.3, 0.05, 0.05, 1.0]
        if mode == "LINKMENU":
            col_outer = [0.4, 0.6, 1.0, 0.4]
            col_inner = [0.0, 0.0, 0.0, 0.5]
            col_circle_inner = [0.08, 0.15, .3, 1.0]
        elif mode == "MIX":
            col_outer = [0.2, 1.0, 0.2, 0.4]
            col_inner = [0.0, 0.0, 0.0, 0.5]
            col_circle_inner = [0.05, 0.3, 0.05, 1.0]

        m1x = self.mouse_path[0][0]
        m1y = self.mouse_path[0][1]
        m2x = self.mouse_path[-1][0]
        m2y = self.mouse_path[-1][1]

        n1 = nodes[context.scene.NWLazySource]
        n2 = nodes[context.scene.NWLazyTarget]

        draw_rounded_node_border(n1, radius=6, colour=col_outer)  # outline
        draw_rounded_node_border(n1, radius=5, colour=col_inner)  # inner
        draw_rounded_node_border(n2, radius=6, colour=col_outer)  # outline
        draw_rounded_node_border(n2, radius=5, colour=col_inner)  # inner

        draw_line(m1x, m1y, m2x, m2y, 4, col_outer)  # line outline
        draw_line(m1x, m1y, m2x, m2y, 2, col_inner)  # line inner

        # circle outline
        draw_circle(m1x, m1y, 6, col_outer)
        draw_circle(m2x, m2y, 6, col_outer)

        # circle inner
        draw_circle(m1x, m1y, 5, col_circle_inner)
        draw_circle(m2x, m2y, 5, col_circle_inner)

        # restore opengl defaults
        bgl.glLineWidth(1)
        bgl.glDisable(bgl.GL_BLEND)
        bgl.glColor4f(0.0, 0.0, 0.0, 1.0)

        if settings.bgl_antialiasing:
            bgl.glDisable(bgl.GL_LINE_SMOOTH)


def get_nodes_links(context):
    space = context.space_data
    tree = space.node_tree
    nodes = tree.nodes
    links = tree.links
    active = nodes.active
    context_active = context.active_node
    # check if we are working on regular node tree or node group is currently edited.
    # if group is edited - active node of space_tree is the group
    # if context.active_node != space active node - it means that the group is being edited.
    # in such case we set "nodes" to be nodes of this group, "links" to be links of this group
    # if context.active_node == space.active_node it means that we are not currently editing group
    is_main_tree = True
    if active:
        is_main_tree = context_active == active
    if not is_main_tree:  # if group is currently edited
        tree = active.node_tree
        nodes = tree.nodes
        links = tree.links

    return nodes, links


# Addon prefs
class NWNodeWrangler(bpy.types.AddonPreferences):
    bl_idname = __name__

    merge_hide = EnumProperty(
        name="Hide Mix nodes",
        items=(
            ("ALWAYS", "Always", "Always collapse the new merge nodes"),
            ("NON_SHADER", "Non-Shader", "Collapse in all cases except for shaders"),
            ("NEVER", "Never", "Never collapse the new merge nodes")
        ),
        default='NON_SHADER',
        description="When merging nodes with the Ctrl+Numpad0 hotkey (and similar) specifiy whether to collapse them or show the full node with options expanded")
    merge_position = EnumProperty(
        name="Mix Node Position",
        items=(
            ("CENTER", "Center", "Place the Mix node between the two nodes"),
            ("BOTTOM", "Bottom", "Place the Mix node at the same height as the lowest node")
        ),
        default='CENTER',
        description="When merging nodes with the Ctrl+Numpad0 hotkey (and similar) specifiy the position of the new nodes")
    bgl_antialiasing = BoolProperty(
        name="Line Antialiasing",
        default=False,
        description="Remove aliasing artifacts on lines drawn in interactive modes such as Lazy Connect (Alt+LMB) and Lazy Merge (Alt+RMB) - this may cause issues on some systems"
    )

    show_hotkey_list = BoolProperty(
        name="Show Hotkey List",
        default=False,
        description="Expand this box into a list of all the hotkeys for functions in this addon"
    )
    hotkey_list_filter = StringProperty(
        name="        Filter by Name",
        default="",
        description="Show only hotkeys that have this text in their name"
    )

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "merge_position")
        col.prop(self, "merge_hide")
        col.prop(self, "bgl_antialiasing")

        box = col.box()
        col = box.column(align=True)

        hotkey_button_name = "Show Hotkey List"
        if self.show_hotkey_list:
            hotkey_button_name = "Hide Hotkey List"
        col.prop(self, "show_hotkey_list", text=hotkey_button_name, toggle=True)
        if self.show_hotkey_list:
            col.prop(self, "hotkey_list_filter", icon="VIEWZOOM")
            col.separator()
            for hotkey in kmi_defs:
                if hotkey[6]:
                    hotkey_name = hotkey[6]

                    if self.hotkey_list_filter.lower() in hotkey_name.lower():
                        row = col.row(align=True)
                        row.label(hotkey_name)
                        keystr = nice_hotkey_name(hotkey[1])
                        if hotkey[3]:
                            keystr = "Shift " + keystr
                        if hotkey[4]:
                            keystr = "Alt " + keystr
                        if hotkey[2]:
                            keystr = "Ctrl " + keystr
                        row.label(keystr)


class NWBase:
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None


# OPERATORS
class NWLazyMix(Operator, NWBase):
    """Add a Mix RGB/Shader node by interactively drawing lines between nodes"""
    bl_idname = "node.nw_lazy_mix"
    bl_label = "Mix Nodes"
    bl_options = {'REGISTER', 'UNDO'}

    def modal(self, context, event):
        context.area.tag_redraw()
        nodes, links = get_nodes_links(context)
        cont = True

        start_pos = [event.mouse_region_x, event.mouse_region_y]

        node1 = None
        if not context.scene.NWBusyDrawing:
            node1 = node_at_pos(nodes, context, event)
            if node1:
                context.scene.NWBusyDrawing = node1.name
        else:
            if context.scene.NWBusyDrawing != 'STOP':
                node1 = nodes[context.scene.NWBusyDrawing]

        context.scene.NWLazySource = node1.name
        context.scene.NWLazyTarget = node_at_pos(nodes, context, event).name

        if event.type == 'MOUSEMOVE':
            self.mouse_path.append((event.mouse_region_x, event.mouse_region_y))

        elif event.type == 'RIGHTMOUSE':
            end_pos = [event.mouse_region_x, event.mouse_region_y]
            bpy.types.SpaceNodeEditor.draw_handler_remove(self._handle, 'WINDOW')

            node2 = None
            node2 = node_at_pos(nodes, context, event)
            if node2:
                context.scene.NWBusyDrawing = node2.name

            if node1 == node2:
                cont = False

            if cont:
                if node1 and node2:
                    for node in nodes:
                        node.select = False
                    node1.select = True
                    node2.select = True

                    bpy.ops.node.nw_merge_nodes(mode="MIX", merge_type="AUTO")

            context.scene.NWBusyDrawing = ""
            return {'FINISHED'}

        elif event.type == 'ESC':
            print('cancelled')
            bpy.types.SpaceNodeEditor.draw_handler_remove(self._handle, 'WINDOW')
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.area.type == 'NODE_EDITOR':
            # the arguments we pass the the callback
            args = (self, context, 'MIX')
            # Add the region OpenGL drawing callback
            # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
            self._handle = bpy.types.SpaceNodeEditor.draw_handler_add(draw_callback_mixnodes, args, 'WINDOW', 'POST_PIXEL')

            self.mouse_path = []

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}


class NWLazyConnect(Operator, NWBase):
    """Connect two nodes without clicking a specific socket (automatically determined"""
    bl_idname = "node.nw_lazy_connect"
    bl_label = "Lazy Connect"
    bl_options = {'REGISTER', 'UNDO'}
    with_menu = BoolProperty()

    def modal(self, context, event):
        context.area.tag_redraw()
        nodes, links = get_nodes_links(context)
        cont = True

        start_pos = [event.mouse_region_x, event.mouse_region_y]

        node1 = None
        if not context.scene.NWBusyDrawing:
            node1 = node_at_pos(nodes, context, event)
            if node1:
                context.scene.NWBusyDrawing = node1.name
        else:
            if context.scene.NWBusyDrawing != 'STOP':
                node1 = nodes[context.scene.NWBusyDrawing]

        context.scene.NWLazySource = node1.name
        context.scene.NWLazyTarget = node_at_pos(nodes, context, event).name

        if event.type == 'MOUSEMOVE':
            self.mouse_path.append((event.mouse_region_x, event.mouse_region_y))

        elif event.type == 'RIGHTMOUSE':
            end_pos = [event.mouse_region_x, event.mouse_region_y]
            bpy.types.SpaceNodeEditor.draw_handler_remove(self._handle, 'WINDOW')

            node2 = None
            node2 = node_at_pos(nodes, context, event)
            if node2:
                context.scene.NWBusyDrawing = node2.name

            if node1 == node2:
                cont = False

            link_success = False
            if cont:
                if node1 and node2:
                    original_sel = []
                    original_unsel = []
                    for node in nodes:
                        if node.select == True:
                            node.select = False
                            original_sel.append(node)
                        else:
                            original_unsel.append(node)
                    node1.select = True
                    node2.select = True

                    #link_success = autolink(node1, node2, links)
                    if self.with_menu:
                        if len(node1.outputs) > 1 and node2.inputs:
                            bpy.ops.wm.call_menu("INVOKE_DEFAULT", name=NWConnectionListOutputs.bl_idname)
                        elif len(node1.outputs) == 1:
                            bpy.ops.node.nw_call_inputs_menu(from_socket=0)
                    else:
                        link_success = autolink(node1, node2, links)

                    for node in original_sel:
                        node.select = True
                    for node in original_unsel:
                        node.select = False

            if link_success:
                hack_force_update(context, nodes)
            context.scene.NWBusyDrawing = ""
            return {'FINISHED'}

        elif event.type == 'ESC':
            bpy.types.SpaceNodeEditor.draw_handler_remove(self._handle, 'WINDOW')
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.area.type == 'NODE_EDITOR':
            nodes, links = get_nodes_links(context)
            node = node_at_pos(nodes, context, event)
            if node:
                context.scene.NWBusyDrawing = node.name

            # the arguments we pass the the callback
            mode = "LINK"
            if self.with_menu:
                mode = "LINKMENU"
            args = (self, context, mode)
            # Add the region OpenGL drawing callback
            # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
            self._handle = bpy.types.SpaceNodeEditor.draw_handler_add(draw_callback_mixnodes, args, 'WINDOW', 'POST_PIXEL')

            self.mouse_path = []

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}


class NWDeleteUnused(Operator, NWBase):
    """Delete all nodes whose output is not used"""
    bl_idname = 'node.nw_del_unused'
    bl_label = 'Delete Unused Nodes'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        valid = False
        if context.space_data:
            if context.space_data.node_tree:
                if context.space_data.node_tree.nodes:
                    valid = True
        return valid

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        end_types = 'OUTPUT_MATERIAL', 'OUTPUT', 'VIEWER', 'COMPOSITE', \
            'SPLITVIEWER', 'OUTPUT_FILE', 'LEVELS', 'OUTPUT_LAMP', \
            'OUTPUT_WORLD', 'GROUP', 'GROUP_INPUT', 'GROUP_OUTPUT'

        # Store selection
        selection = []
        for node in nodes:
            if node.select == True:
                selection.append(node.name)

        deleted_nodes = []
        temp_deleted_nodes = []
        del_unused_iterations = len(nodes)
        for it in range(0, del_unused_iterations):
            temp_deleted_nodes = list(deleted_nodes)  # keep record of last iteration
            for node in nodes:
                node.select = False
            for node in nodes:
                if is_end_node(node) and not node.type in end_types and node.type != 'FRAME':
                    node.select = True
                    deleted_nodes.append(node.name)
                    bpy.ops.node.delete()

            if temp_deleted_nodes == deleted_nodes:  # stop iterations when there are no more nodes to be deleted
                break
        # get unique list of deleted nodes (iterations would count the same node more than once)
        deleted_nodes = list(set(deleted_nodes))
        for n in deleted_nodes:
            self.report({'INFO'}, "Node " + n + " deleted")
        num_deleted = len(deleted_nodes)
        n = ' node'
        if num_deleted > 1:
            n += 's'
        if num_deleted:
            self.report({'INFO'}, "Deleted " + str(num_deleted) + n)
        else:
            self.report({'INFO'}, "Nothing deleted")

        # Restore selection
        nodes, links = get_nodes_links(context)
        for node in nodes:
            if node.name in selection:
                node.select = True
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class NWSwapOutputs(Operator, NWBase):
    """Swap the output connections of the two selected nodes"""
    bl_idname = 'node.nw_swap_outputs'
    bl_label = 'Swap Outputs'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        snode = context.space_data
        if context.selected_nodes:
            return len(context.selected_nodes) == 2
        else:
            return False

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        selected_nodes = context.selected_nodes
        n1 = selected_nodes[0]
        n2 = selected_nodes[1]
        n1_outputs = []
        n2_outputs = []

        out_index = 0
        for output in n1.outputs:
            if output.links:
                for link in output.links:
                    n1_outputs.append([out_index, link.to_socket])
                    links.remove(link)
            out_index += 1

        out_index = 0
        for output in n2.outputs:
            if output.links:
                for link in output.links:
                    n2_outputs.append([out_index, link.to_socket])
                    links.remove(link)
            out_index += 1

        for connection in n1_outputs:
            try:
                links.new(n2.outputs[connection[0]], connection[1])
            except:
                self.report({'WARNING'}, "Some connections have been lost due to differing numbers of output sockets")
        for connection in n2_outputs:
            try:
                links.new(n1.outputs[connection[0]], connection[1])
            except:
                self.report({'WARNING'}, "Some connections have been lost due to differing numbers of output sockets")

        hack_force_update(context, nodes)
        return {'FINISHED'}


class NWResetBG(Operator, NWBase):
    """Reset the zoom and position of the background image"""
    bl_idname = 'node.nw_bg_reset'
    bl_label = 'Reset Backdrop'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        snode = context.space_data
        return snode.tree_type == 'CompositorNodeTree'

    def execute(self, context):
        context.space_data.backdrop_zoom = 1
        context.space_data.backdrop_x = 0
        context.space_data.backdrop_y = 0
        return {'FINISHED'}


class NWAddAttrNode(Operator, NWBase):
    """Add an Attribute node with this name"""
    bl_idname = 'node.nw_add_attr_node'
    bl_label = 'Add UV map'
    attr_name = StringProperty()
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.node.add_node('INVOKE_DEFAULT', use_transform=True, type="ShaderNodeAttribute")
        nodes, links = get_nodes_links(context)
        nodes.active.attribute_name = self.attr_name
        return {'FINISHED'}


class NWEmissionViewer(Operator, NWBase):
    bl_idname = "node.nw_emission_viewer"
    bl_label = "Emission Viewer"
    bl_description = "Connect active node to Emission Shader for shadeless previews"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        valid = False
        if space.type == 'NODE_EDITOR':
            if space.tree_type == 'ShaderNodeTree' and space.node_tree is not None and (context.active_node.type != "OUTPUT_MATERIAL" or context.active_node.type != "OUTPUT_WORLD"):
                valid = True
        return valid

    def invoke(self, context, event):
        shader_type = context.space_data.shader_type
        if shader_type == 'OBJECT':
            shader_output_type = "OUTPUT_MATERIAL"
            shader_output_ident = "ShaderNodeOutputMaterial"
            shader_viewer_ident = "ShaderNodeEmission"
        elif shader_type == 'WORLD':
            shader_output_type = "OUTPUT_WORLD"
            shader_output_ident = "ShaderNodeOutputWorld"
            shader_viewer_ident = "ShaderNodeBackground"
        shader_types = [x[1] for x in shaders_shader_nodes_props]
        mlocx = event.mouse_region_x
        mlocy = event.mouse_region_y
        select_node = bpy.ops.node.select(mouse_x=mlocx, mouse_y=mlocy, extend=False)
        if 'FINISHED' in select_node:  # only run if mouse click is on a node
            nodes, links = get_nodes_links(context)
            in_group = context.active_node != context.space_data.node_tree.nodes.active
            active = nodes.active
            valid = False
            output_types = [x[1] for x in shaders_output_nodes_props]
            if active:
                if (active.name != "Emission Viewer") and (active.type not in output_types) and not in_group:
                    if active.select:
                        if active.type not in shader_types:
                            valid = True
            if valid:
                # get material_output node
                materialout_exists = False
                materialout = None  # placeholder node
                for node in nodes:
                    if node.type == shader_output_type:
                        materialout_exists = True
                        materialout = node
                if not materialout:
                    materialout = nodes.new(shader_output_ident)
                    sorted_by_xloc = (sorted(nodes, key=lambda x: x.location.x))
                    max_xloc_node = sorted_by_xloc[-1]
                    if max_xloc_node.name == 'Emission Viewer':
                        max_xloc_node = sorted_by_xloc[-2]
                    materialout.location.x = max_xloc_node.location.x + max_xloc_node.dimensions.x + 80
                    sum_yloc = 0
                    for node in nodes:
                        sum_yloc += node.location.y
                    materialout.location.y = sum_yloc / len(nodes)  # put material output at average y location
                    materialout.select = False
                # get Emission Viewer node
                emission_exists = False
                emission_placeholder = nodes[0]
                for node in nodes:
                    if "Emission Viewer" in node.name:
                        emission_exists = True
                        emission_placeholder = node

                position = 0
                for link in links:  # check if Emission Viewer is already connected to active node
                    if link.from_node.name == active.name and "Emission Viewer" in link.to_node.name and "Emission Viewer" in materialout.inputs[0].links[0].from_node.name:
                        num_outputs = len(link.from_node.outputs)
                        index = 0
                        for output in link.from_node.outputs:
                            if link.from_socket == output:
                                position = index
                            index = index + 1
                        position = position + 1
                        if position >= num_outputs:
                            position = 0

                # Store selection
                selection = []
                for node in nodes:
                    if node.select == True:
                        selection.append(node.name)

                locx = active.location.x
                locy = active.location.y
                dimx = active.dimensions.x
                dimy = active.dimensions.y
                if not emission_exists:
                    emission = nodes.new(shader_viewer_ident)
                    emission.hide = True
                    emission.location = [materialout.location.x, (materialout.location.y + 40)]
                    emission.label = "Viewer"
                    emission.name = "Emission Viewer"
                    emission.use_custom_color = True
                    emission.color = (0.6, 0.5, 0.4)
                else:
                    emission = emission_placeholder

                nodes.active = emission
                links.new(active.outputs[position], emission.inputs[0])
                bpy.ops.node.nw_link_out()

                # Restore selection
                emission.select = False
                nodes.active = active
                for node in nodes:
                    if node.name in selection:
                        node.select = True
            else:  # if active node is a shader, connect to output
                if (active.name != "Emission Viewer") and (active.type not in output_types) and not in_group:
                    bpy.ops.node.nw_link_out()

                    # ----Delete Emission Viewer----
                    if [x for x in nodes if x.name == 'Emission Viewer']:
                        # Store selection
                        selection = []
                        for node in nodes:
                            if node.select == True:
                                selection.append(node.name)
                                node.select = False
                        # Delete it
                        nodes['Emission Viewer'].select = True
                        bpy.ops.node.delete()
                        # Restore selection
                        for node in nodes:
                            if node.name in selection:
                                node.select = True

            return {'FINISHED'}
        else:
            return {'CANCELLED'}


class NWFrameSelected(Operator, NWBase):
    bl_idname = "node.nw_frame_selected"
    bl_label = "Frame Selected"
    bl_description = "Add a frame node and parent the selected nodes to it"
    bl_options = {'REGISTER', 'UNDO'}
    label_prop = StringProperty(name='Label', default=' ', description='The visual name of the frame node')
    color_prop = FloatVectorProperty(name="Color", description="The color of the frame node", default=(0.6, 0.6, 0.6),
                                     min=0, max=1, step=1, precision=3, subtype='COLOR_GAMMA', size=3)

    @classmethod
    def poll(cls, context):
        space = context.space_data
        valid = False
        if space.type == 'NODE_EDITOR':
            if space.node_tree is not None:
                valid = True
        return valid

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        selected = []
        for node in nodes:
            if node.select == True:
                selected.append(node)

        bpy.ops.node.add_node(type='NodeFrame')
        frm = nodes.active
        frm.label = self.label_prop
        frm.use_custom_color = True
        frm.color = self.color_prop

        for node in selected:
            node.parent = frm

        return {'FINISHED'}


class NWReloadImages(Operator, NWBase):
    bl_idname = "node.nw_reload_images"
    bl_label = "Reload Images"
    bl_description = "Update all the image nodes to match their files on disk"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        valid = False
        if space.type == 'NODE_EDITOR':
            if space.node_tree is not None:
                valid = True
        return valid

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        image_types = ["IMAGE", "TEX_IMAGE", "TEX_ENVIRONMENT", "TEXTURE"]
        num_reloaded = 0
        for node in nodes:
            if node.type in image_types:
                if node.type == "TEXTURE":
                    if node.texture:  # node has texture assigned
                        if node.texture.type in ['IMAGE', 'ENVIRONMENT_MAP']:
                            if node.texture.image:  # texture has image assigned
                                node.texture.image.reload()
                                num_reloaded += 1
                else:
                    if node.image:
                        node.image.reload()
                        num_reloaded += 1

        if num_reloaded:
            self.report({'INFO'}, "Reloaded images")
            print("Reloaded " + str(num_reloaded) + " images")
            hack_force_update(context, nodes)
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "No images found to reload in this node tree")
            return {'CANCELLED'}


class NWSwitchNodeType(Operator, NWBase):
    """Switch type of selected nodes """
    bl_idname = "node.nw_swtch_node_type"
    bl_label = "Switch Node Type"
    bl_options = {'REGISTER', 'UNDO'}

    to_type = EnumProperty(
        name="Switch to type",
        items=list(shaders_input_nodes_props) +
        list(shaders_output_nodes_props) +
        list(shaders_shader_nodes_props) +
        list(shaders_texture_nodes_props) +
        list(shaders_color_nodes_props) +
        list(shaders_vector_nodes_props) +
        list(shaders_converter_nodes_props) +
        list(shaders_layout_nodes_props) +
        list(compo_input_nodes_props) +
        list(compo_output_nodes_props) +
        list(compo_color_nodes_props) +
        list(compo_converter_nodes_props) +
        list(compo_filter_nodes_props) +
        list(compo_vector_nodes_props) +
        list(compo_matte_nodes_props) +
        list(compo_distort_nodes_props) +
        list(compo_layout_nodes_props),
    )

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        to_type = self.to_type
        # Those types of nodes will not swap.
        src_excludes = ('NodeFrame')
        # Those attributes of nodes will be copied if possible
        attrs_to_pass = ('color', 'hide', 'label', 'mute', 'parent',
                         'show_options', 'show_preview', 'show_texture',
                         'use_alpha', 'use_clamp', 'use_custom_color', 'location'
                         )
        selected = [n for n in nodes if n.select]
        reselect = []
        for node in [n for n in selected if
                     n.rna_type.identifier not in src_excludes and
                     n.rna_type.identifier != to_type]:
            new_node = nodes.new(to_type)
            for attr in attrs_to_pass:
                if hasattr(node, attr) and hasattr(new_node, attr):
                    setattr(new_node, attr, getattr(node, attr))
            # set image datablock of dst to image of src
            if hasattr(node, 'image') and hasattr(new_node, 'image'):
                if node.image:
                    new_node.image = node.image
            # Special cases
            if new_node.type == 'SWITCH':
                new_node.hide = True
            # Dictionaries: src_sockets and dst_sockets:
            # 'INPUTS': input sockets ordered by type (entry 'MAIN' main type of inputs).
            # 'OUTPUTS': output sockets ordered by type (entry 'MAIN' main type of outputs).
            # in 'INPUTS' and 'OUTPUTS':
            # 'SHADER', 'RGBA', 'VECTOR', 'VALUE' - sockets of those types.
            # socket entry:
            # (index_in_type, socket_index, socket_name, socket_default_value, socket_links)
            src_sockets = {
                'INPUTS': {'SHADER': [], 'RGBA': [], 'VECTOR': [], 'VALUE': [], 'MAIN': None},
                'OUTPUTS': {'SHADER': [], 'RGBA': [], 'VECTOR': [], 'VALUE': [], 'MAIN': None},
            }
            dst_sockets = {
                'INPUTS': {'SHADER': [], 'RGBA': [], 'VECTOR': [], 'VALUE': [], 'MAIN': None},
                'OUTPUTS': {'SHADER': [], 'RGBA': [], 'VECTOR': [], 'VALUE': [], 'MAIN': None},
            }
            types_order_one = 'SHADER', 'RGBA', 'VECTOR', 'VALUE'
            types_order_two = 'SHADER', 'VECTOR', 'RGBA', 'VALUE'
            # check src node to set src_sockets values and dst node to set dst_sockets dict values
            for sockets, nd in ((src_sockets, node), (dst_sockets, new_node)):
                # Check node's inputs and outputs and fill proper entries in "sockets" dict
                for in_out, in_out_name in ((nd.inputs, 'INPUTS'), (nd.outputs, 'OUTPUTS')):
                    # enumerate in inputs, then in outputs
                    # find name, default value and links of socket
                    for i, socket in enumerate(in_out):
                        the_name = socket.name
                        dval = None
                        # Not every socket, especially in outputs has "default_value"
                        if hasattr(socket, 'default_value'):
                            dval = socket.default_value
                        socket_links = []
                        for lnk in socket.links:
                            socket_links.append(lnk)
                        # check type of socket to fill proper keys.
                        for the_type in types_order_one:
                            if socket.type == the_type:
                                # create values for sockets['INPUTS'][the_type] and sockets['OUTPUTS'][the_type]
                                # entry structure: (index_in_type, socket_index, socket_name, socket_default_value, socket_links)
                                sockets[in_out_name][the_type].append((len(sockets[in_out_name][the_type]), i, the_name, dval, socket_links))
                    # Check which of the types in inputs/outputs is considered to be "main".
                    # Set values of sockets['INPUTS']['MAIN'] and sockets['OUTPUTS']['MAIN']
                    for type_check in types_order_one:
                        if sockets[in_out_name][type_check]:
                            sockets[in_out_name]['MAIN'] = type_check
                            break

            matches = {
                'INPUTS': {'SHADER': [], 'RGBA': [], 'VECTOR': [], 'VALUE_NAME': [], 'VALUE': [], 'MAIN': []},
                'OUTPUTS': {'SHADER': [], 'RGBA': [], 'VECTOR': [], 'VALUE_NAME': [], 'VALUE': [], 'MAIN': []},
            }

            for inout, soctype in (
                    ('INPUTS', 'MAIN',),
                    ('INPUTS', 'SHADER',),
                    ('INPUTS', 'RGBA',),
                    ('INPUTS', 'VECTOR',),
                    ('INPUTS', 'VALUE',),
                    ('OUTPUTS', 'MAIN',),
                    ('OUTPUTS', 'SHADER',),
                    ('OUTPUTS', 'RGBA',),
                    ('OUTPUTS', 'VECTOR',),
                    ('OUTPUTS', 'VALUE',),
            ):
                if src_sockets[inout][soctype] and dst_sockets[inout][soctype]:
                    if soctype == 'MAIN':
                        sc = src_sockets[inout][src_sockets[inout]['MAIN']]
                        dt = dst_sockets[inout][dst_sockets[inout]['MAIN']]
                    else:
                        sc = src_sockets[inout][soctype]
                        dt = dst_sockets[inout][soctype]
                    # start with 'dt' to determine number of possibilities.
                    for i, soc in enumerate(dt):
                        # if src main has enough entries - match them with dst main sockets by indexes.
                        if len(sc) > i:
                            matches[inout][soctype].append(((sc[i][1], sc[i][3]), (soc[1], soc[3])))
                        # add 'VALUE_NAME' criterion to inputs.
                        if inout == 'INPUTS' and soctype == 'VALUE':
                            for s in sc:
                                if s[2] == soc[2]:  # if names match
                                    # append src (index, dval), dst (index, dval)
                                    matches['INPUTS']['VALUE_NAME'].append(((s[1], s[3]), (soc[1], soc[3])))

            # When src ['INPUTS']['MAIN'] is 'VECTOR' replace 'MAIN' with matches VECTOR if possible.
            # This creates better links when relinking textures.
            if src_sockets['INPUTS']['MAIN'] == 'VECTOR' and matches['INPUTS']['VECTOR']:
                matches['INPUTS']['MAIN'] = matches['INPUTS']['VECTOR']

            # Pass default values and RELINK:
            for tp in ('MAIN', 'SHADER', 'RGBA', 'VECTOR', 'VALUE_NAME', 'VALUE'):
                # INPUTS: Base on matches in proper order.
                for (src_i, src_dval), (dst_i, dst_dval) in matches['INPUTS'][tp]:
                    # pass dvals
                    if src_dval and dst_dval and tp in {'RGBA', 'VALUE_NAME'}:
                        new_node.inputs[dst_i].default_value = src_dval
                    # Special case: switch to math
                    if node.type in {'MIX_RGB', 'ALPHAOVER', 'ZCOMBINE'} and\
                            new_node.type == 'MATH' and\
                            tp == 'MAIN':
                        new_dst_dval = max(src_dval[0], src_dval[1], src_dval[2])
                        new_node.inputs[dst_i].default_value = new_dst_dval
                        if node.type == 'MIX_RGB':
                            if node.blend_type in [o[0] for o in operations]:
                                new_node.operation = node.blend_type
                    # Special case: switch from math to some types
                    if node.type == 'MATH' and\
                            new_node.type in {'MIX_RGB', 'ALPHAOVER', 'ZCOMBINE'} and\
                            tp == 'MAIN':
                        for i in range(3):
                            new_node.inputs[dst_i].default_value[i] = src_dval
                        if new_node.type == 'MIX_RGB':
                            if node.operation in [t[0] for t in blend_types]:
                                new_node.blend_type = node.operation
                            # Set Fac of MIX_RGB to 1.0
                            new_node.inputs[0].default_value = 1.0
                    # make link only when dst matching input is not linked already.
                    if node.inputs[src_i].links and not new_node.inputs[dst_i].links:
                        in_src_link = node.inputs[src_i].links[0]
                        in_dst_socket = new_node.inputs[dst_i]
                        links.new(in_src_link.from_socket, in_dst_socket)
                        links.remove(in_src_link)
                # OUTPUTS: Base on matches in proper order.
                for (src_i, src_dval), (dst_i, dst_dval) in matches['OUTPUTS'][tp]:
                    for out_src_link in node.outputs[src_i].links:
                        out_dst_socket = new_node.outputs[dst_i]
                        links.new(out_dst_socket, out_src_link.to_socket)
            # relink rest inputs if possible, no criteria
            for src_inp in node.inputs:
                for dst_inp in new_node.inputs:
                    if src_inp.links and not dst_inp.links:
                        src_link = src_inp.links[0]
                        links.new(src_link.from_socket, dst_inp)
                        links.remove(src_link)
            # relink rest outputs if possible, base on node kind if any left.
            for src_o in node.outputs:
                for out_src_link in src_o.links:
                    for dst_o in new_node.outputs:
                        if src_o.type == dst_o.type:
                            links.new(dst_o, out_src_link.to_socket)
            # relink rest outputs no criteria if any left. Link all from first output.
            for src_o in node.outputs:
                for out_src_link in src_o.links:
                    if new_node.outputs:
                        links.new(new_node.outputs[0], out_src_link.to_socket)
            nodes.remove(node)
        return {'FINISHED'}


class NWMergeNodes(Operator, NWBase):
    bl_idname = "node.nw_merge_nodes"
    bl_label = "Merge Nodes"
    bl_description = "Merge Selected Nodes"
    bl_options = {'REGISTER', 'UNDO'}

    mode = EnumProperty(
        name="mode",
        description="All possible blend types and math operations",
        items=blend_types + [op for op in operations if op not in blend_types],
    )
    merge_type = EnumProperty(
        name="merge type",
        description="Type of Merge to be used",
        items=(
            ('AUTO', 'Auto', 'Automatic Output Type Detection'),
            ('SHADER', 'Shader', 'Merge using ADD or MIX Shader'),
            ('MIX', 'Mix Node', 'Merge using Mix Nodes'),
            ('MATH', 'Math Node', 'Merge using Math Nodes'),
        ),
    )

    def execute(self, context):
        settings = context.user_preferences.addons[__name__].preferences
        merge_hide = settings.merge_hide
        merge_position = settings.merge_position  # 'center' or 'bottom'

        do_hide = False
        do_hide_shader = False
        if merge_hide == 'ALWAYS':
            do_hide = True
            do_hide_shader = True
        elif merge_hide == 'NON_SHADER':
            do_hide = True

        tree_type = context.space_data.node_tree.type
        if tree_type == 'COMPOSITING':
            node_type = 'CompositorNode'
        elif tree_type == 'SHADER':
            node_type = 'ShaderNode'
        nodes, links = get_nodes_links(context)
        mode = self.mode
        merge_type = self.merge_type
        selected_mix = []  # entry = [index, loc]
        selected_shader = []  # entry = [index, loc]
        selected_math = []  # entry = [index, loc]

        for i, node in enumerate(nodes):
            if node.select and node.outputs:
                if merge_type == 'AUTO':
                    for (type, types_list, dst) in (
                            ('SHADER', ('MIX', 'ADD'), selected_shader),
                            ('RGBA', [t[0] for t in blend_types], selected_mix),
                            ('VALUE', [t[0] for t in operations], selected_math),
                    ):
                        output_type = node.outputs[0].type
                        valid_mode = mode in types_list
                        # When mode is 'MIX' use mix node for both 'RGBA' and 'VALUE' output types.
                        # Cheat that output type is 'RGBA',
                        # and that 'MIX' exists in math operations list.
                        # This way when selected_mix list is analyzed:
                        # Node data will be appended even though it doesn't meet requirements.
                        if output_type != 'SHADER' and mode == 'MIX':
                            output_type = 'RGBA'
                            valid_mode = True
                        if output_type == type and valid_mode:
                            dst.append([i, node.location.x, node.location.y])
                else:
                    for (type, types_list, dst) in (
                            ('SHADER', ('MIX', 'ADD'), selected_shader),
                            ('MIX', [t[0] for t in blend_types], selected_mix),
                            ('MATH', [t[0] for t in operations], selected_math),
                    ):
                        if merge_type == type and mode in types_list:
                            dst.append([i, node.location.x, node.location.y])
        # When nodes with output kinds 'RGBA' and 'VALUE' are selected at the same time
        # use only 'Mix' nodes for merging.
        # For that we add selected_math list to selected_mix list and clear selected_math.
        if selected_mix and selected_math and merge_type == 'AUTO':
            selected_mix += selected_math
            selected_math = []

        for nodes_list in [selected_mix, selected_shader, selected_math]:
            if nodes_list:
                count_before = len(nodes)
                # sort list by loc_x - reversed
                nodes_list.sort(key=lambda k: k[1], reverse=True)
                # get maximum loc_x
                loc_x = nodes_list[0][1] + 250.0
                nodes_list.sort(key=lambda k: k[2], reverse=True)
                if merge_position == 'CENTER':
                    loc_y = ((nodes_list[len(nodes_list) - 1][2]) + (nodes_list[len(nodes_list) - 2][2])) / 2  # average yloc of last two nodes (lowest two)
                else:
                    loc_y = nodes_list[len(nodes_list) - 1][2]
                offset_y = 100
                if not do_hide:
                    offset_y = 200
                if nodes_list == selected_shader and not do_hide_shader:
                    offset_y = 150.0
                the_range = len(nodes_list) - 1
                if len(nodes_list) == 1:
                    the_range = 1
                for i in range(the_range):
                    if nodes_list == selected_mix:
                        add_type = node_type + 'MixRGB'
                        add = nodes.new(add_type)
                        add.blend_type = mode
                        add.show_preview = False
                        add.hide = do_hide
                        if do_hide:
                            loc_y = loc_y - 50
                        first = 1
                        second = 2
                        add.width_hidden = 100.0
                    elif nodes_list == selected_math:
                        add_type = node_type + 'Math'
                        add = nodes.new(add_type)
                        add.operation = mode
                        add.hide = do_hide
                        if do_hide:
                            loc_y = loc_y - 50
                        first = 0
                        second = 1
                        add.width_hidden = 100.0
                    elif nodes_list == selected_shader:
                        if mode == 'MIX':
                            add_type = node_type + 'MixShader'
                            add = nodes.new(add_type)
                            add.hide = do_hide_shader
                            if do_hide_shader:
                                loc_y = loc_y - 50
                            first = 1
                            second = 2
                            add.width_hidden = 100.0
                        elif mode == 'ADD':
                            add_type = node_type + 'AddShader'
                            add = nodes.new(add_type)
                            add.hide = do_hide_shader
                            if do_hide_shader:
                                loc_y = loc_y - 50
                            first = 0
                            second = 1
                            add.width_hidden = 100.0
                    add.location = loc_x, loc_y
                    loc_y += offset_y
                    add.select = True
                count_adds = i + 1
                count_after = len(nodes)
                index = count_after - 1
                first_selected = nodes[nodes_list[0][0]]
                # "last" node has been added as first, so its index is count_before.
                last_add = nodes[count_before]
                # add links from last_add to all links 'to_socket' of out links of first selected.
                for fs_link in first_selected.outputs[0].links:
                    # Prevent cyclic dependencies when nodes to be marged are linked to one another.
                    # Create list of invalid indexes.
                    invalid_i = [n[0] for n in (selected_mix + selected_math + selected_shader)]
                    # Link only if "to_node" index not in invalid indexes list.
                    if fs_link.to_node not in [nodes[i] for i in invalid_i]:
                        links.new(last_add.outputs[0], fs_link.to_socket)
                # add link from "first" selected and "first" add node
                links.new(first_selected.outputs[0], nodes[count_after - 1].inputs[first])
                # add links between added ADD nodes and between selected and ADD nodes
                for i in range(count_adds):
                    if i < count_adds - 1:
                        links.new(nodes[index - 1].inputs[first], nodes[index].outputs[0])
                    if len(nodes_list) > 1:
                        links.new(nodes[index].inputs[second], nodes[nodes_list[i + 1][0]].outputs[0])
                    index -= 1
                # set "last" of added nodes as active
                nodes.active = last_add
                for i, x, y in nodes_list:
                    nodes[i].select = False

        return {'FINISHED'}


class NWBatchChangeNodes(Operator, NWBase):
    bl_idname = "node.nw_batch_change"
    bl_label = "Batch Change"
    bl_description = "Batch Change Blend Type and Math Operation"
    bl_options = {'REGISTER', 'UNDO'}

    blend_type = EnumProperty(
        name="Blend Type",
        items=blend_types + navs,
    )
    operation = EnumProperty(
        name="Operation",
        items=operations + navs,
    )

    def execute(self, context):

        nodes, links = get_nodes_links(context)
        blend_type = self.blend_type
        operation = self.operation
        for node in context.selected_nodes:
            if node.type == 'MIX_RGB':
                if not blend_type in [nav[0] for nav in navs]:
                    node.blend_type = blend_type
                else:
                    if blend_type == 'NEXT':
                        index = [i for i, entry in enumerate(blend_types) if node.blend_type in entry][0]
                        #index = blend_types.index(node.blend_type)
                        if index == len(blend_types) - 1:
                            node.blend_type = blend_types[0][0]
                        else:
                            node.blend_type = blend_types[index + 1][0]

                    if blend_type == 'PREV':
                        index = [i for i, entry in enumerate(blend_types) if node.blend_type in entry][0]
                        if index == 0:
                            node.blend_type = blend_types[len(blend_types) - 1][0]
                        else:
                            node.blend_type = blend_types[index - 1][0]

            if node.type == 'MATH':
                if not operation in [nav[0] for nav in navs]:
                    node.operation = operation
                else:
                    if operation == 'NEXT':
                        index = [i for i, entry in enumerate(operations) if node.operation in entry][0]
                        #index = operations.index(node.operation)
                        if index == len(operations) - 1:
                            node.operation = operations[0][0]
                        else:
                            node.operation = operations[index + 1][0]

                    if operation == 'PREV':
                        index = [i for i, entry in enumerate(operations) if node.operation in entry][0]
                        #index = operations.index(node.operation)
                        if index == 0:
                            node.operation = operations[len(operations) - 1][0]
                        else:
                            node.operation = operations[index - 1][0]

        return {'FINISHED'}


class NWChangeMixFactor(Operator, NWBase):
    bl_idname = "node.nw_factor"
    bl_label = "Change Factor"
    bl_description = "Change Factors of Mix Nodes and Mix Shader Nodes"
    bl_options = {'REGISTER', 'UNDO'}

    # option: Change factor.
    # If option is 1.0 or 0.0 - set to 1.0 or 0.0
    # Else - change factor by option value.
    option = FloatProperty()

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        option = self.option
        selected = []  # entry = index
        for si, node in enumerate(nodes):
            if node.select:
                if node.type in {'MIX_RGB', 'MIX_SHADER'}:
                    selected.append(si)

        for si in selected:
            fac = nodes[si].inputs[0]
            nodes[si].hide = False
            if option in {0.0, 1.0}:
                fac.default_value = option
            else:
                fac.default_value += option

        return {'FINISHED'}


class NWCopySettings(Operator, NWBase):
    bl_idname = "node.nw_copy_settings"
    bl_label = "Copy Settings"
    bl_description = "Copy Settings of Active Node to Selected Nodes"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        valid = False
        if (space.type == 'NODE_EDITOR' and
                space.node_tree is not None and
                context.active_node is not None and
                context.active_node.type is not 'FRAME'
                ):
            valid = True
        return valid

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        selected = [n for n in nodes if n.select]
        reselect = []  # duplicated nodes will be selected after execution
        active = nodes.active
        if active.select:
            reselect.append(active)

        for node in selected:
            if node.type == active.type and node != active:
                # duplicate active, relink links as in 'node', append copy to 'reselect', delete node
                bpy.ops.node.select_all(action='DESELECT')
                nodes.active = active
                active.select = True
                bpy.ops.node.duplicate()
                copied = nodes.active
                # Copied active should however inherit some properties from 'node'
                attributes = (
                    'hide', 'show_preview', 'mute', 'label',
                    'use_custom_color', 'color', 'width', 'width_hidden',
                )
                for attr in attributes:
                    setattr(copied, attr, getattr(node, attr))
                # Handle scenario when 'node' is in frame. 'copied' is in same frame then.
                if copied.parent:
                    bpy.ops.node.parent_clear()
                locx = node.location.x
                locy = node.location.y
                # get absolute node location
                parent = node.parent
                while parent:
                    locx += parent.location.x
                    locy += parent.location.y
                    parent = parent.parent
                copied.location = [locx, locy]
                # reconnect links from node to copied
                for i, input in enumerate(node.inputs):
                    if input.links:
                        link = input.links[0]
                        links.new(link.from_socket, copied.inputs[i])
                for out, output in enumerate(node.outputs):
                    if output.links:
                        out_links = output.links
                        for link in out_links:
                            links.new(copied.outputs[out], link.to_socket)
                bpy.ops.node.select_all(action='DESELECT')
                node.select = True
                bpy.ops.node.delete()
                reselect.append(copied)
            else:  # If selected wasn't copied, need to reselect it afterwards.
                reselect.append(node)
        # clean up
        bpy.ops.node.select_all(action='DESELECT')
        for node in reselect:
            node.select = True
        nodes.active = active

        return {'FINISHED'}


class NWCopyLabel(Operator, NWBase):
    bl_idname = "node.nw_copy_label"
    bl_label = "Copy Label"
    bl_options = {'REGISTER', 'UNDO'}

    option = EnumProperty(
        name="option",
        description="Source of name of label",
        items=(
            ('FROM_ACTIVE', 'from active', 'from active node',),
            ('FROM_NODE', 'from node', 'from node linked to selected node'),
            ('FROM_SOCKET', 'from socket', 'from socket linked to selected node'),
        )
    )

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        option = self.option
        active = nodes.active
        if option == 'FROM_ACTIVE':
            if active:
                src_label = active.label
                for node in [n for n in nodes if n.select and nodes.active != n]:
                    node.label = src_label
        elif option == 'FROM_NODE':
            selected = [n for n in nodes if n.select]
            for node in selected:
                for input in node.inputs:
                    if input.links:
                        src = input.links[0].from_node
                        node.label = src.label
                        break
        elif option == 'FROM_SOCKET':
            selected = [n for n in nodes if n.select]
            for node in selected:
                for input in node.inputs:
                    if input.links:
                        src = input.links[0].from_socket
                        node.label = src.name
                        break

        return {'FINISHED'}


class NWClearLabel(Operator, NWBase):
    bl_idname = "node.nw_clear_label"
    bl_label = "Clear Label"
    bl_options = {'REGISTER', 'UNDO'}

    option = BoolProperty()

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        for node in [n for n in nodes if n.select]:
            node.label = ''

        return {'FINISHED'}

    def invoke(self, context, event):
        if self.option:
            return self.execute(context)
        else:
            return context.window_manager.invoke_confirm(self, event)


class NWModifyLabels(Operator, NWBase):
    """Modify Labels of all selected nodes."""
    bl_idname = "node.nw_modify_labels"
    bl_label = "Modify Labels"
    bl_options = {'REGISTER', 'UNDO'}

    prepend = StringProperty(
        name="Add to Beginning"
    )
    append = StringProperty(
        name="Add to End"
    )
    replace_from = StringProperty(
        name="Text to Replace"
    )
    replace_to = StringProperty(
        name="Replace with"
    )

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        for node in [n for n in nodes if n.select]:
            node.label = self.prepend + node.label.replace(self.replace_from, self.replace_to) + self.append

        return {'FINISHED'}

    def invoke(self, context, event):
        self.prepend = ""
        self.append = ""
        self.remove = ""
        return context.window_manager.invoke_props_dialog(self)


class NWAddTextureSetup(Operator, NWBase):
    bl_idname = "node.nw_add_texture"
    bl_label = "Texture Setup"
    bl_description = "Add Texture Node Setup to Selected Shaders"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        valid = False
        if space.type == 'NODE_EDITOR':
            if space.tree_type == 'ShaderNodeTree' and space.node_tree is not None:
                valid = True
        return valid

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        active = nodes.active
        shader_types = [x[1] for x in shaders_shader_nodes_props if x[1] not in {'MIX_SHADER', 'ADD_SHADER'}]
        texture_types = [x[1] for x in shaders_texture_nodes_props]
        valid = False
        if active:
            if active.select:
                if active.type in shader_types or active.type in texture_types:
                    if not active.inputs[0].is_linked:
                        valid = True
        if valid:
            locx = active.location.x
            locy = active.location.y

            xoffset = [500.0, 700.0]
            isshader = True
            if active.type not in shader_types:
                xoffset = [290.0, 500.0]
                isshader = False

            coordout = 2
            image_type = 'ShaderNodeTexImage'

            if (active.type in texture_types and active.type != 'TEX_IMAGE') or (active.type == 'BACKGROUND'):
                coordout = 0  # image texture uses UVs, procedural textures and Background shader use Generated
                if active.type == 'BACKGROUND':
                    image_type = 'ShaderNodeTexEnvironment'

            if isshader:
                tex = nodes.new(image_type)
                tex.location = [locx - 200.0, locy + 28.0]

            map = nodes.new('ShaderNodeMapping')
            map.location = [locx - xoffset[0], locy + 80.0]
            map.width = 240
            coord = nodes.new('ShaderNodeTexCoord')
            coord.location = [locx - xoffset[1], locy + 40.0]
            active.select = False

            if isshader:
                nodes.active = tex
                links.new(tex.outputs[0], active.inputs[0])
                links.new(map.outputs[0], tex.inputs[0])
                links.new(coord.outputs[coordout], map.inputs[0])

            else:
                nodes.active = map
                links.new(map.outputs[0], active.inputs[0])
                links.new(coord.outputs[coordout], map.inputs[0])

        return {'FINISHED'}


class NWAddReroutes(Operator, NWBase):
    """Add Reroute Nodes and link them to outputs of selected nodes"""
    bl_idname = "node.nw_add_reroutes"
    bl_label = "Add Reroutes"
    bl_description = "Add Reroutes to Outputs"
    bl_options = {'REGISTER', 'UNDO'}

    option = EnumProperty(
        name="option",
        items=[
            ('ALL', 'to all', 'Add to all outputs'),
            ('LOOSE', 'to loose', 'Add only to loose outputs'),
            ('LINKED', 'to linked', 'Add only to linked outputs'),
        ]
    )

    def execute(self, context):
        tree_type = context.space_data.node_tree.type
        option = self.option
        nodes, links = get_nodes_links(context)
        # output valid when option is 'all' or when 'loose' output has no links
        valid = False
        post_select = []  # nodes to be selected after execution
        # create reroutes and recreate links
        for node in [n for n in nodes if n.select]:
            if node.outputs:
                x = node.location.x
                y = node.location.y
                width = node.width
                # unhide 'REROUTE' nodes to avoid issues with location.y
                if node.type == 'REROUTE':
                    node.hide = False
                # When node is hidden - width_hidden not usable.
                # Hack needed to calculate real width
                if node.hide:
                    bpy.ops.node.select_all(action='DESELECT')
                    helper = nodes.new('NodeReroute')
                    helper.select = True
                    node.select = True
                    # resize node and helper to zero. Then check locations to calculate width
                    bpy.ops.transform.resize(value=(0.0, 0.0, 0.0))
                    width = 2.0 * (helper.location.x - node.location.x)
                    # restore node location
                    node.location = x, y
                    # delete helper
                    node.select = False
                    # only helper is selected now
                    bpy.ops.node.delete()
                x = node.location.x + width + 20.0
                if node.type != 'REROUTE':
                    y -= 35.0
                y_offset = -22.0
                loc = x, y
            reroutes_count = 0  # will be used when aligning reroutes added to hidden nodes
            for out_i, output in enumerate(node.outputs):
                pass_used = False  # initial value to be analyzed if 'R_LAYERS'
                # if node is not 'R_LAYERS' - "pass_used" not needed, so set it to True
                if node.type != 'R_LAYERS':
                    pass_used = True
                else:  # if 'R_LAYERS' check if output represent used render pass
                    node_scene = node.scene
                    node_layer = node.layer
                    # If output - "Alpha" is analyzed - assume it's used. Not represented in passes.
                    if output.name == 'Alpha':
                        pass_used = True
                    else:
                        # check entries in global 'rl_outputs' variable
                        for render_pass, out_name, exr_name, in_internal, in_cycles in rl_outputs:
                            if output.name == out_name:
                                pass_used = getattr(node_scene.render.layers[node_layer], render_pass)
                                break
                if pass_used:
                    valid = ((option == 'ALL') or
                             (option == 'LOOSE' and not output.links) or
                             (option == 'LINKED' and output.links))
                    # Add reroutes only if valid, but offset location in all cases.
                    if valid:
                        n = nodes.new('NodeReroute')
                        nodes.active = n
                        for link in output.links:
                            links.new(n.outputs[0], link.to_socket)
                        links.new(output, n.inputs[0])
                        n.location = loc
                        post_select.append(n)
                    reroutes_count += 1
                    y += y_offset
                    loc = x, y
            # disselect the node so that after execution of script only newly created nodes are selected
            node.select = False
            # nicer reroutes distribution along y when node.hide
            if node.hide:
                y_translate = reroutes_count * y_offset / 2.0 - y_offset - 35.0
                for reroute in [r for r in nodes if r.select]:
                    reroute.location.y -= y_translate
            for node in post_select:
                node.select = True

        return {'FINISHED'}


class NWLinkActiveToSelected(Operator, NWBase):
    """Link active node to selected nodes basing on various criteria"""
    bl_idname = "node.nw_link_active_to_selected"
    bl_label = "Link Active Node to Selected"
    bl_options = {'REGISTER', 'UNDO'}

    replace = BoolProperty()
    use_node_name = BoolProperty()
    use_outputs_names = BoolProperty()

    @classmethod
    def poll(cls, context):
        space = context.space_data
        valid = False
        if space.type == 'NODE_EDITOR':
            if space.node_tree is not None and context.active_node is not None:
                if context.active_node.select:
                    valid = True
        return valid

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        replace = self.replace
        use_node_name = self.use_node_name
        use_outputs_names = self.use_outputs_names
        active = nodes.active
        selected = [node for node in nodes if node.select and node != active]
        outputs = []  # Only usable outputs of active nodes will be stored here.
        for out in active.outputs:
            if active.type != 'R_LAYERS':
                outputs.append(out)
            else:
                # 'R_LAYERS' node type needs special handling.
                # outputs of 'R_LAYERS' are callable even if not seen in UI.
                # Only outputs that represent used passes should be taken into account
                # Check if pass represented by output is used.
                # global 'rl_outputs' list will be used for that
                for render_pass, out_name, exr_name, in_internal, in_cycles in rl_outputs:
                    pass_used = False  # initial value. Will be set to True if pass is used
                    if out.name == 'Alpha':
                        # Alpha output is always present. Doesn't have representation in render pass. Assume it's used.
                        pass_used = True
                    elif out.name == out_name:
                        # example 'render_pass' entry: 'use_pass_uv' Check if True in scene render layers
                        pass_used = getattr(active.scene.render.layers[active.layer], render_pass)
                        break
                if pass_used:
                    outputs.append(out)
        doit = True  # Will be changed to False when links successfully added to previous output.
        for out in outputs:
            if doit:
                for node in selected:
                    dst_name = node.name  # Will be compared with src_name if needed.
                    # When node has label - use it as dst_name
                    if node.label:
                        dst_name = node.label
                    valid = True  # Initial value. Will be changed to False if names don't match.
                    src_name = dst_name  # If names not used - this asignment will keep valid = True.
                    if use_node_name:
                        # Set src_name to source node name or label
                        src_name = active.name
                        if active.label:
                            src_name = active.label
                    elif use_outputs_names:
                        src_name = (out.name, )
                        for render_pass, out_name, exr_name, in_internal, in_cycles in rl_outputs:
                            if out.name in {out_name, exr_name}:
                                src_name = (out_name, exr_name)
                    if dst_name not in src_name:
                        valid = False
                    if valid:
                        for input in node.inputs:
                            if input.type == out.type or node.type == 'REROUTE':
                                if replace or not input.is_linked:
                                    links.new(out, input)
                                    if not use_node_name and not use_outputs_names:
                                        doit = False
                                    break

        return {'FINISHED'}


class NWAlignNodes(Operator, NWBase):
    bl_idname = "node.nw_align_nodes"
    bl_label = "Align nodes"
    bl_options = {'REGISTER', 'UNDO'}

    # option: 'Vertically', 'Horizontally'
    option = EnumProperty(
        name="option",
        description="Direction",
        items=(
            ('AXIS_X', "Align Vertically", 'Align Vertically'),
            ('AXIS_Y', "Aligh Horizontally", 'Aligh Horizontally'),
        )
    )

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        selected = []  # entry = [index, loc.x, loc.y, width, height]
        frames_reselect = []  # entry = frame node. will be used to reselect all selected frames
        active = nodes.active
        for i, node in enumerate(nodes):
            total_w = 0.0  # total width of all nodes. Will be calculated later.
            total_h = 0.0  # total height of all nodes. Will be calculated later
            if node.select:
                if node.type == 'FRAME':
                    node.select = False
                    frames_reselect.append(i)
                else:
                    locx = node.location.x
                    locy = node.location.y
                    width = node.dimensions[0]
                    height = node.dimensions[1]
                    total_w += width  # add nodes[i] width to total width of all nodes
                    total_h += height  # add nodes[i] height to total height of all nodes
                    # calculate relative locations
                    parent = node.parent
                    while parent is not None:
                        locx += parent.location.x
                        locy += parent.location.y
                        parent = parent.parent
                    selected.append([i, locx, locy, width, height])
        count = len(selected)
        if count > 1:  # aligning makes sense only if at least 2 nodes are selected
            selected_sorted_x = sorted(selected, key=lambda k: (k[1], -k[2]))
            selected_sorted_y = sorted(selected, key=lambda k: (-k[2], k[1]))
            min_x = selected_sorted_x[0][1]  # min loc.x
            min_x_loc_y = selected_sorted_x[0][2]  # loc y of node with min loc x
            min_x_w = selected_sorted_x[0][3]  # width of node with max loc x
            max_x = selected_sorted_x[count - 1][1]  # max loc.x
            max_x_loc_y = selected_sorted_x[count - 1][2]  # loc y of node with max loc.x
            max_x_w = selected_sorted_x[count - 1][3]  # width of node with max loc.x
            min_y = selected_sorted_y[0][2]  # min loc.y
            min_y_loc_x = selected_sorted_y[0][1]  # loc.x of node with min loc.y
            min_y_h = selected_sorted_y[0][4]  # height of node with min loc.y
            min_y_w = selected_sorted_y[0][3]  # width of node with min loc.y
            max_y = selected_sorted_y[count - 1][2]  # max loc.y
            max_y_loc_x = selected_sorted_y[count - 1][1]  # loc x of node with max loc.y
            max_y_w = selected_sorted_y[count - 1][3]  # width of node with max loc.y
            max_y_h = selected_sorted_y[count - 1][4]  # height of node with max loc.y

            if self.option == 'AXIS_Y':  # Horizontally. Equivelent of s -> x -> 0 with even spacing.
                loc_x = min_x
                #loc_y = (max_x_loc_y + min_x_loc_y) / 2.0
                loc_y = (max_y - max_y_h / 2.0 + min_y - min_y_h / 2.0) / 2.0
                offset_x = (max_x - min_x - total_w + max_x_w) / (count - 1)
                for i, x, y, w, h in selected_sorted_x:
                    nodes[i].location.x = loc_x
                    nodes[i].location.y = loc_y + h / 2.0
                    parent = nodes[i].parent
                    while parent is not None:
                        nodes[i].location.x -= parent.location.x
                        nodes[i].location.y -= parent.location.y
                        parent = parent.parent
                    loc_x += offset_x + w
            else:  # if self.option == 'AXIS_Y'
                loc_x = (max_x + max_x_w / 2.0 + min_x + min_x_w / 2.0) / 2.0
                loc_y = min_y
                offset_y = (max_y - min_y + total_h - min_y_h) / (count - 1)
                for i, x, y, w, h in selected_sorted_y:
                    nodes[i].location.x = loc_x - w / 2.0
                    nodes[i].location.y = loc_y
                    parent = nodes[i].parent
                    while parent is not None:
                        nodes[i].location.x -= parent.location.x
                        nodes[i].location.y -= parent.location.y
                        parent = parent.parent
                    loc_y += offset_y - h

            # reselect selected frames
            for i in frames_reselect:
                nodes[i].select = True
            # restore active node
            nodes.active = active

        return {'FINISHED'}


class NWSelectParentChildren(Operator, NWBase):
    bl_idname = "node.nw_select_parent_child"
    bl_label = "Select Parent or Children"
    bl_options = {'REGISTER', 'UNDO'}

    option = EnumProperty(
        name="option",
        items=(
            ('PARENT', 'Select Parent', 'Select Parent Frame'),
            ('CHILD', 'Select Children', 'Select members of selected frame'),
        )
    )

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        option = self.option
        selected = [node for node in nodes if node.select]
        if option == 'PARENT':
            for sel in selected:
                parent = sel.parent
                if parent:
                    parent.select = True
        else:  # option == 'CHILD'
            for sel in selected:
                children = [node for node in nodes if node.parent == sel]
                for kid in children:
                    kid.select = True

        return {'FINISHED'}


class NWDetachOutputs(Operator, NWBase):
    """Detach outputs of selected node leaving inluts liked"""
    bl_idname = "node.nw_detach_outputs"
    bl_label = "Detach Outputs"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        selected = context.selected_nodes
        bpy.ops.node.duplicate_move_keep_inputs()
        new_nodes = context.selected_nodes
        bpy.ops.node.select_all(action="DESELECT")
        for node in selected:
            node.select = True
        bpy.ops.node.delete_reconnect()
        for new_node in new_nodes:
            new_node.select = True
        bpy.ops.transform.translate('INVOKE_DEFAULT')

        return {'FINISHED'}


class NWLinkToOutputNode(Operator, NWBase):
    """Link to Composite node or Material Output node"""
    bl_idname = "node.nw_link_out"
    bl_label = "Connect to Output"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return (space.type == 'NODE_EDITOR' and space.node_tree is not None and context.active_node is not None)

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        active = nodes.active
        output_node = None
        tree_type = context.space_data.tree_type
        output_types_shaders = [x[1] for x in shaders_output_nodes_props]
        output_types_compo = ['COMPOSITE']
        output_types = output_types_shaders + output_types_compo
        for node in nodes:
            if node.type in output_types:
                output_node = node
                break
        if not output_node:
            bpy.ops.node.select_all(action="DESELECT")
            if tree_type == 'ShaderNodeTree':
                output_node = nodes.new('ShaderNodeOutputMaterial')
            elif tree_type == 'CompositorNodeTree':
                output_node = nodes.new('CompositorNodeComposite')
            output_node.location.x = active.location.x + active.dimensions.x + 80
            output_node.location.y = active.location.y
        if (output_node and active.outputs):
            output_index = 0
            for i, output in enumerate(active.outputs):
                if output.type == output_node.inputs[0].type:
                    output_index = i
                    break

            out_input_index = 0
            if tree_type == 'ShaderNodeTree':
                if active.outputs[output_index].type != 'SHADER':  # connect to displacement if not a shader
                    out_input_index = 2
            links.new(active.outputs[output_index], output_node.inputs[out_input_index])

        hack_force_update(context, nodes)  # viewport render does not update

        return {'FINISHED'}


class NWMakeLink(Operator, NWBase):
    """Make a link from one socket to another"""
    bl_idname = 'node.nw_make_link'
    bl_label = 'Make Link'
    bl_options = {'REGISTER', 'UNDO'}
    from_socket = IntProperty()
    to_socket = IntProperty()

    @classmethod
    def poll(cls, context):
        snode = context.space_data
        return (snode.type == 'NODE_EDITOR' and snode.node_tree is not None)

    def execute(self, context):
        nodes, links = get_nodes_links(context)

        n1 = nodes[context.scene.NWLazySource]
        n2 = nodes[context.scene.NWLazyTarget]

        links.new(n1.outputs[self.from_socket], n2.inputs[self.to_socket])

        hack_force_update(context, nodes)

        return {'FINISHED'}


class NWCallInputsMenu(Operator, NWBase):
    """Link from this output"""
    bl_idname = 'node.nw_call_inputs_menu'
    bl_label = 'Make Link'
    bl_options = {'REGISTER', 'UNDO'}
    from_socket = IntProperty()

    @classmethod
    def poll(cls, context):
        snode = context.space_data
        return (snode.type == 'NODE_EDITOR' and snode.node_tree is not None)

    def execute(self, context):
        nodes, links = get_nodes_links(context)

        context.scene.NWSourceSocket = self.from_socket

        n1 = nodes[context.scene.NWLazySource]
        n2 = nodes[context.scene.NWLazyTarget]
        if len(n2.inputs) > 1:
            bpy.ops.wm.call_menu("INVOKE_DEFAULT", name=NWConnectionListInputs.bl_idname)
        elif len(n2.inputs) == 1:
            links.new(n1.outputs[self.from_socket], n2.inputs[0])
        return {'FINISHED'}


#
#  P A N E L
#

def drawlayout(context, layout, mode='non-panel'):
    tree_type = context.space_data.tree_type

    col = layout.column(align=True)
    col.menu(NWMergeNodesMenu.bl_idname)
    col.separator()

    col = layout.column(align=True)
    col.menu(NWSwitchNodeTypeMenu.bl_idname, text="Switch Node Type")
    col.separator()

    if tree_type == 'ShaderNodeTree':
        col = layout.column(align=True)
        col.operator(NWAddTextureSetup.bl_idname, text="Add Texture Setup", icon='NODE_SEL')
        col.separator()

    col = layout.column(align=True)
    col.operator(NWDetachOutputs.bl_idname, icon='UNLINKED')
    col.operator(NWSwapOutputs.bl_idname)
    col.menu(NWAddReroutesMenu.bl_idname, text="Add Reroutes", icon='LAYER_USED')
    col.separator()

    col = layout.column(align=True)
    col.menu(NWLinkActiveToSelectedMenu.bl_idname, text="Link Active To Selected", icon='LINKED')
    col.operator(NWLinkToOutputNode.bl_idname, icon='DRIVER')
    col.separator()

    col = layout.column(align=True)
    if mode == 'panel':
        row = col.row(align=True)
        row.operator(NWClearLabel.bl_idname).option = True
        row.operator(NWModifyLabels.bl_idname)
    else:
        col.operator(NWClearLabel.bl_idname).option = True
        col.operator(NWModifyLabels.bl_idname)
    col.menu(NWBatchChangeNodesMenu.bl_idname, text="Batch Change")
    col.separator()
    col.menu(NWCopyToSelectedMenu.bl_idname, text="Copy to Selected")
    col.separator()

    col = layout.column(align=True)
    if tree_type == 'CompositorNodeTree':
        col.operator(NWResetBG.bl_idname, icon='ZOOM_PREVIOUS')
    col.operator(NWReloadImages.bl_idname, icon='FILE_REFRESH')
    col.separator()

    col = layout.column(align=True)
    col.operator(NWFrameSelected.bl_idname, icon='STICKY_UVS_LOC')
    col.separator()

    col = layout.column(align=True)
    col.operator(NWDeleteUnused.bl_idname, icon='CANCEL')
    col.separator()


class NodeWranglerPanel(Panel, NWBase):
    bl_idname = "NODE_PT_nw_node_wrangler"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Node Wrangler"

    prepend = StringProperty(
        name='prepend',
    )
    append = StringProperty()
    remove = StringProperty()

    def draw(self, context):
        self.layout.label(text="(Quick access: Ctrl+Space)")
        drawlayout(context, self.layout, mode='panel')


#
#  M E N U S
#
class NodeWranglerMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_node_wrangler_menu"
    bl_label = "Node Wrangler"

    def draw(self, context):
        drawlayout(context, self.layout)


class NWMergeNodesMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_merge_nodes_menu"
    bl_label = "Merge Selected Nodes"

    def draw(self, context):
        type = context.space_data.tree_type
        layout = self.layout
        if type == 'ShaderNodeTree':
            layout.menu(NWMergeShadersMenu.bl_idname, text="Use Shaders")
        layout.menu(NWMergeMixMenu.bl_idname, text="Use Mix Nodes")
        layout.menu(NWMergeMathMenu.bl_idname, text="Use Math Nodes")


class NWMergeShadersMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_merge_shaders_menu"
    bl_label = "Merge Selected Nodes using Shaders"

    def draw(self, context):
        layout = self.layout
        for type in ('MIX', 'ADD'):
            props = layout.operator(NWMergeNodes.bl_idname, text=type)
            props.mode = type
            props.merge_type = 'SHADER'


class NWMergeMixMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_merge_mix_menu"
    bl_label = "Merge Selected Nodes using Mix"

    def draw(self, context):
        layout = self.layout
        for type, name, description in blend_types:
            props = layout.operator(NWMergeNodes.bl_idname, text=name)
            props.mode = type
            props.merge_type = 'MIX'


class NWConnectionListOutputs(Menu, NWBase):
    bl_idname = "NODE_MT_nw_connection_list_out"
    bl_label = "From:"

    def draw(self, context):
        layout = self.layout
        nodes, links = get_nodes_links(context)

        n1 = nodes[context.scene.NWLazySource]

        if n1.type == "R_LAYERS":
            index=0
            for o in n1.outputs:
                if o.enabled:  # Check which passes the render layer has enabled
                    layout.operator(NWCallInputsMenu.bl_idname, text=o.name, icon="RADIOBUT_OFF").from_socket=index
                index+=1
        else:
            index=0
            for o in n1.outputs:
                layout.operator(NWCallInputsMenu.bl_idname, text=o.name, icon="RADIOBUT_OFF").from_socket=index
                index+=1


class NWConnectionListInputs(Menu, NWBase):
    bl_idname = "NODE_MT_nw_connection_list_in"
    bl_label = "To:"

    def draw(self, context):
        layout = self.layout
        nodes, links = get_nodes_links(context)

        n2 = nodes[context.scene.NWLazyTarget]

        #print (self.from_socket)

        index = 0
        for i in n2.inputs:
            op = layout.operator(NWMakeLink.bl_idname, text=i.name, icon="FORWARD")
            op.from_socket = context.scene.NWSourceSocket
            op.to_socket = index
            index+=1


class NWMergeMathMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_merge_math_menu"
    bl_label = "Merge Selected Nodes using Math"

    def draw(self, context):
        layout = self.layout
        for type, name, description in operations:
            props = layout.operator(NWMergeNodes.bl_idname, text=name)
            props.mode = type
            props.merge_type = 'MATH'


class NWBatchChangeNodesMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_batch_change_nodes_menu"
    bl_label = "Batch Change Selected Nodes"

    def draw(self, context):
        layout = self.layout
        layout.menu(NWBatchChangeBlendTypeMenu.bl_idname)
        layout.menu(NWBatchChangeOperationMenu.bl_idname)


class NWBatchChangeBlendTypeMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_batch_change_blend_type_menu"
    bl_label = "Batch Change Blend Type"

    def draw(self, context):
        layout = self.layout
        for type, name, description in blend_types:
            props = layout.operator(NWBatchChangeNodes.bl_idname, text=name)
            props.blend_type = type
            props.operation = 'CURRENT'


class NWBatchChangeOperationMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_batch_change_operation_menu"
    bl_label = "Batch Change Math Operation"

    def draw(self, context):
        layout = self.layout
        for type, name, description in operations:
            props = layout.operator(NWBatchChangeNodes.bl_idname, text=name)
            props.blend_type = 'CURRENT'
            props.operation = type


class NWCopyToSelectedMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_copy_node_properties_menu"
    bl_label = "Copy to Selected"

    def draw(self, context):
        layout = self.layout
        layout.operator(NWCopySettings.bl_idname, text="Settings from Active")
        layout.menu(NWCopyLabelMenu.bl_idname)


class NWCopyLabelMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_copy_label_menu"
    bl_label = "Copy Label"

    def draw(self, context):
        layout = self.layout
        layout.operator(NWCopyLabel.bl_idname, text="from Active Node's Label").option = 'FROM_ACTIVE'
        layout.operator(NWCopyLabel.bl_idname, text="from Linked Node's Label").option = 'FROM_NODE'
        layout.operator(NWCopyLabel.bl_idname, text="from Linked Output's Name").option = 'FROM_SOCKET'


class NWAddReroutesMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_add_reroutes_menu"
    bl_label = "Add Reroutes"
    bl_description = "Add Reroute Nodes to Selected Nodes' Outputs"

    def draw(self, context):
        layout = self.layout
        layout.operator(NWAddReroutes.bl_idname, text="to All Outputs").option = 'ALL'
        layout.operator(NWAddReroutes.bl_idname, text="to Loose Outputs").option = 'LOOSE'
        layout.operator(NWAddReroutes.bl_idname, text="to Linked Outputs").option = 'LINKED'


class NWLinkActiveToSelectedMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_link_active_to_selected_menu"
    bl_label = "Link Active to Selected"

    def draw(self, context):
        layout = self.layout
        layout.menu(NWLinkStandardMenu.bl_idname)
        layout.menu(NWLinkUseNodeNameMenu.bl_idname)
        layout.menu(NWLinkUseOutputsNamesMenu.bl_idname)


class NWLinkStandardMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_link_standard_menu"
    bl_label = "To All Selected"

    def draw(self, context):
        layout = self.layout
        props = layout.operator(NWLinkActiveToSelected.bl_idname, text="Don't Replace Links")
        props.replace = False
        props.use_node_name = False
        props.use_outputs_names = False
        props = layout.operator(NWLinkActiveToSelected.bl_idname, text="Replace Links")
        props.replace = True
        props.use_node_name = False
        props.use_outputs_names = False


class NWLinkUseNodeNameMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_link_use_node_name_menu"
    bl_label = "Use Node Name/Label"

    def draw(self, context):
        layout = self.layout
        props = layout.operator(NWLinkActiveToSelected.bl_idname, text="Don't Replace Links")
        props.replace = False
        props.use_node_name = True
        props.use_outputs_names = False
        props = layout.operator(NWLinkActiveToSelected.bl_idname, text="Replace Links")
        props.replace = True
        props.use_node_name = True
        props.use_outputs_names = False


class NWLinkUseOutputsNamesMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_link_use_outputs_names_menu"
    bl_label = "Use Outputs Names"

    def draw(self, context):
        layout = self.layout
        props = layout.operator(NWLinkActiveToSelected.bl_idname, text="Don't Replace Links")
        props.replace = False
        props.use_node_name = False
        props.use_outputs_names = True
        props = layout.operator(NWLinkActiveToSelected.bl_idname, text="Replace Links")
        props.replace = True
        props.use_node_name = False
        props.use_outputs_names = True


class NWNodeAlignMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_node_align_menu"
    bl_label = "Align Nodes"

    def draw(self, context):
        layout = self.layout
        layout.operator(NWAlignNodes.bl_idname, text="Horizontally").option = 'AXIS_X'
        layout.operator(NWAlignNodes.bl_idname, text="Vertically").option = 'AXIS_Y'


# TODO, add to toolbar panel
class NWUVMenu(bpy.types.Menu):
    bl_idname = "NODE_MT_nw_node_uvs_menu"
    bl_label = "UV Maps"

    @classmethod
    def poll(cls, context):
        if context.area.spaces[0].node_tree:
            if context.area.spaces[0].node_tree.type == 'SHADER':
                return True
            else:
                return False
        else:
            return False

    def draw(self, context):
        l = self.layout
        nodes, links = get_nodes_links(context)
        mat = context.object.active_material

        objs = []
        for obj in bpy.data.objects:
            for slot in obj.material_slots:
                if slot.material == mat:
                    objs.append(obj)
        uvs = []
        for obj in objs:
            if obj.data.uv_layers:
                for uv in obj.data.uv_layers:
                    uvs.append(uv.name)
        uvs = list(set(uvs))  # get a unique list

        if uvs:
            for uv in uvs:
                l.operator(NWAddAttrNode.bl_idname, text=uv).attr_name = uv
        else:
            l.label("No UV layers on objects with this material")


class NWVertColMenu(bpy.types.Menu):
    bl_idname = "NODE_MT_nw_node_vertex_color_menu"
    bl_label = "Vertex Colors"

    @classmethod
    def poll(cls, context):
        if context.area.spaces[0].node_tree:
            if context.area.spaces[0].node_tree.type == 'SHADER':
                return True
            else:
                return False
        else:
            return False

    def draw(self, context):
        l = self.layout
        nodes, links = get_nodes_links(context)
        mat = context.object.active_material

        objs = []
        for obj in bpy.data.objects:
            for slot in obj.material_slots:
                if slot.material == mat:
                    objs.append(obj)
        vcols = []
        for obj in objs:
            if obj.data.vertex_colors:
                for vcol in obj.data.vertex_colors:
                    vcols.append(vcol.name)
        vcols = list(set(vcols))  # get a unique list

        if vcols:
            for vcol in vcols:
                l.operator(NWAddAttrNode.bl_idname, text=vcol).attr_name = vcol
        else:
            l.label("No Vertex Color layers on objects with this material")


class NWSwitchNodeTypeMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_switch_node_type_menu"
    bl_label = "Switch Type to..."

    def draw(self, context):
        layout = self.layout
        tree = context.space_data.node_tree
        if tree.type == 'SHADER':
            layout.menu(NWSwitchShadersInputSubmenu.bl_idname)
            layout.menu(NWSwitchShadersOutputSubmenu.bl_idname)
            layout.menu(NWSwitchShadersShaderSubmenu.bl_idname)
            layout.menu(NWSwitchShadersTextureSubmenu.bl_idname)
            layout.menu(NWSwitchShadersColorSubmenu.bl_idname)
            layout.menu(NWSwitchShadersVectorSubmenu.bl_idname)
            layout.menu(NWSwitchShadersConverterSubmenu.bl_idname)
            layout.menu(NWSwitchShadersLayoutSubmenu.bl_idname)
        if tree.type == 'COMPOSITING':
            layout.menu(NWSwitchCompoInputSubmenu.bl_idname)
            layout.menu(NWSwitchCompoOutputSubmenu.bl_idname)
            layout.menu(NWSwitchCompoColorSubmenu.bl_idname)
            layout.menu(NWSwitchCompoConverterSubmenu.bl_idname)
            layout.menu(NWSwitchCompoFilterSubmenu.bl_idname)
            layout.menu(NWSwitchCompoVectorSubmenu.bl_idname)
            layout.menu(NWSwitchCompoMatteSubmenu.bl_idname)
            layout.menu(NWSwitchCompoDistortSubmenu.bl_idname)
            layout.menu(NWSwitchCompoLayoutSubmenu.bl_idname)


class NWSwitchShadersInputSubmenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_switch_shaders_input_submenu"
    bl_label = "Input"

    def draw(self, context):
        layout = self.layout
        for ident, type, rna_name in shaders_input_nodes_props:
            props = layout.operator(NWSwitchNodeType.bl_idname, text=rna_name)
            props.to_type = ident


class NWSwitchShadersOutputSubmenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_switch_shaders_output_submenu"
    bl_label = "Output"

    def draw(self, context):
        layout = self.layout
        for ident, type, rna_name in shaders_output_nodes_props:
            props = layout.operator(NWSwitchNodeType.bl_idname, text=rna_name)
            props.to_type = ident


class NWSwitchShadersShaderSubmenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_switch_shaders_shader_submenu"
    bl_label = "Shader"

    def draw(self, context):
        layout = self.layout
        for ident, type, rna_name in shaders_shader_nodes_props:
            props = layout.operator(NWSwitchNodeType.bl_idname, text=rna_name)
            props.to_type = ident


class NWSwitchShadersTextureSubmenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_switch_shaders_texture_submenu"
    bl_label = "Texture"

    def draw(self, context):
        layout = self.layout
        for ident, type, rna_name in shaders_texture_nodes_props:
            props = layout.operator(NWSwitchNodeType.bl_idname, text=rna_name)
            props.to_type = ident


class NWSwitchShadersColorSubmenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_switch_shaders_color_submenu"
    bl_label = "Color"

    def draw(self, context):
        layout = self.layout
        for ident, type, rna_name in shaders_color_nodes_props:
            props = layout.operator(NWSwitchNodeType.bl_idname, text=rna_name)
            props.to_type = ident


class NWSwitchShadersVectorSubmenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_switch_shaders_vector_submenu"
    bl_label = "Vector"

    def draw(self, context):
        layout = self.layout
        for ident, type, rna_name in shaders_vector_nodes_props:
            props = layout.operator(NWSwitchNodeType.bl_idname, text=rna_name)
            props.to_type = ident


class NWSwitchShadersConverterSubmenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_switch_shaders_converter_submenu"
    bl_label = "Converter"

    def draw(self, context):
        layout = self.layout
        for ident, type, rna_name in shaders_converter_nodes_props:
            props = layout.operator(NWSwitchNodeType.bl_idname, text=rna_name)
            props.to_type = ident


class NWSwitchShadersLayoutSubmenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_switch_shaders_layout_submenu"
    bl_label = "Layout"

    def draw(self, context):
        layout = self.layout
        for ident, type, rna_name in shaders_layout_nodes_props:
            if type != 'FRAME':
                props = layout.operator(NWSwitchNodeType.bl_idname, text=rna_name)
                props.to_type = ident


class NWSwitchCompoInputSubmenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_switch_compo_input_submenu"
    bl_label = "Input"

    def draw(self, context):
        layout = self.layout
        for ident, type, rna_name in compo_input_nodes_props:
            props = layout.operator(NWSwitchNodeType.bl_idname, text=rna_name)
            props.to_type = ident


class NWSwitchCompoOutputSubmenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_switch_compo_output_submenu"
    bl_label = "Output"

    def draw(self, context):
        layout = self.layout
        for ident, type, rna_name in compo_output_nodes_props:
            props = layout.operator(NWSwitchNodeType.bl_idname, text=rna_name)
            props.to_type = ident


class NWSwitchCompoColorSubmenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_switch_compo_color_submenu"
    bl_label = "Color"

    def draw(self, context):
        layout = self.layout
        for ident, type, rna_name in compo_color_nodes_props:
            props = layout.operator(NWSwitchNodeType.bl_idname, text=rna_name)
            props.to_type = ident


class NWSwitchCompoConverterSubmenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_switch_compo_converter_submenu"
    bl_label = "Converter"

    def draw(self, context):
        layout = self.layout
        for ident, type, rna_name in compo_converter_nodes_props:
            props = layout.operator(NWSwitchNodeType.bl_idname, text=rna_name)
            props.to_type = ident


class NWSwitchCompoFilterSubmenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_switch_compo_filter_submenu"
    bl_label = "Filter"

    def draw(self, context):
        layout = self.layout
        for ident, type, rna_name in compo_filter_nodes_props:
            props = layout.operator(NWSwitchNodeType.bl_idname, text=rna_name)
            props.to_type = ident


class NWSwitchCompoVectorSubmenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_switch_compo_vector_submenu"
    bl_label = "Vector"

    def draw(self, context):
        layout = self.layout
        for ident, type, rna_name in compo_vector_nodes_props:
            props = layout.operator(NWSwitchNodeType.bl_idname, text=rna_name)
            props.to_type = ident


class NWSwitchCompoMatteSubmenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_switch_compo_matte_submenu"
    bl_label = "Matte"

    def draw(self, context):
        layout = self.layout
        for ident, type, rna_name in compo_matte_nodes_props:
            props = layout.operator(NWSwitchNodeType.bl_idname, text=rna_name)
            props.to_type = ident


class NWSwitchCompoDistortSubmenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_switch_compo_distort_submenu"
    bl_label = "Distort"

    def draw(self, context):
        layout = self.layout
        for ident, type, rna_name in compo_distort_nodes_props:
            props = layout.operator(NWSwitchNodeType.bl_idname, text=rna_name)
            props.to_type = ident


class NWSwitchCompoLayoutSubmenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_switch_compo_layout_submenu"
    bl_label = "Layout"

    def draw(self, context):
        layout = self.layout
        for ident, type, rna_name in compo_layout_nodes_props:
            if type != 'FRAME':
                props = layout.operator(NWSwitchNodeType.bl_idname, text=rna_name)
                props.to_type = ident


#
#  APPENDAGES TO EXISTING UI
#


def select_parent_children_buttons(self, context):
    layout = self.layout
    layout.operator(NWSelectParentChildren.bl_idname, text="Select frame's members (children)").option = 'CHILD'
    layout.operator(NWSelectParentChildren.bl_idname, text="Select parent frame").option = 'PARENT'


def attr_nodes_menu_func(self, context):
    col = self.layout.column(align=True)
    col.menu("NODE_MT_nw_node_uvs_menu")
    col.menu("NODE_MT_nw_node_vertex_color_menu")
    col.separator()


def bgreset_menu_func(self, context):
    self.layout.operator(NWResetBG.bl_idname)


#
#  REGISTER/UNREGISTER CLASSES AND KEYMAP ITEMS
#

addon_keymaps = []
# kmi_defs entry: (identifier, key, CTRL, SHIFT, ALT, props, nice name)
# props entry: (property name, property value)
kmi_defs = (
    # MERGE NODES
    # NWMergeNodes with Ctrl (AUTO).
    (NWMergeNodes.bl_idname, 'NUMPAD_0', True, False, False,
        (('mode', 'MIX'), ('merge_type', 'AUTO'),), "Merge Nodes (Automatic)"),
    (NWMergeNodes.bl_idname, 'ZERO', True, False, False,
        (('mode', 'MIX'), ('merge_type', 'AUTO'),), "Merge Nodes (Automatic)"),
    (NWMergeNodes.bl_idname, 'NUMPAD_PLUS', True, False, False,
        (('mode', 'ADD'), ('merge_type', 'AUTO'),), "Merge Nodes (Add)"),
    (NWMergeNodes.bl_idname, 'EQUAL', True, False, False,
        (('mode', 'ADD'), ('merge_type', 'AUTO'),), "Merge Nodes (Add)"),
    (NWMergeNodes.bl_idname, 'NUMPAD_ASTERIX', True, False, False,
        (('mode', 'MULTIPLY'), ('merge_type', 'AUTO'),), "Merge Nodes (Multiply)"),
    (NWMergeNodes.bl_idname, 'EIGHT', True, False, False,
        (('mode', 'MULTIPLY'), ('merge_type', 'AUTO'),), "Merge Nodes (Multiply)"),
    (NWMergeNodes.bl_idname, 'NUMPAD_MINUS', True, False, False,
        (('mode', 'SUBTRACT'), ('merge_type', 'AUTO'),), "Merge Nodes (Subtract)"),
    (NWMergeNodes.bl_idname, 'MINUS', True, False, False,
        (('mode', 'SUBTRACT'), ('merge_type', 'AUTO'),), "Merge Nodes (Subtract)"),
    (NWMergeNodes.bl_idname, 'NUMPAD_SLASH', True, False, False,
        (('mode', 'DIVIDE'), ('merge_type', 'AUTO'),), "Merge Nodes (Divide)"),
    (NWMergeNodes.bl_idname, 'SLASH', True, False, False,
        (('mode', 'DIVIDE'), ('merge_type', 'AUTO'),), "Merge Nodes (Divide)"),
    (NWMergeNodes.bl_idname, 'COMMA', True, False, False,
        (('mode', 'LESS_THAN'), ('merge_type', 'MATH'),), "Merge Nodes (Less than)"),
    (NWMergeNodes.bl_idname, 'PERIOD', True, False, False,
        (('mode', 'GREATER_THAN'), ('merge_type', 'MATH'),), "Merge Nodes (Greater than)"),
    # NWMergeNodes with Ctrl Alt (MIX)
    (NWMergeNodes.bl_idname, 'NUMPAD_0', True, False, True,
        (('mode', 'MIX'), ('merge_type', 'MIX'),), "Merge Nodes (Color, Mix)"),
    (NWMergeNodes.bl_idname, 'ZERO', True, False, True,
        (('mode', 'MIX'), ('merge_type', 'MIX'),), "Merge Nodes (Color, Mix)"),
    (NWMergeNodes.bl_idname, 'NUMPAD_PLUS', True, False, True,
        (('mode', 'ADD'), ('merge_type', 'MIX'),), "Merge Nodes (Color, Add)"),
    (NWMergeNodes.bl_idname, 'EQUAL', True, False, True,
        (('mode', 'ADD'), ('merge_type', 'MIX'),), "Merge Nodes (Color, Add)"),
    (NWMergeNodes.bl_idname, 'NUMPAD_ASTERIX', True, False, True,
        (('mode', 'MULTIPLY'), ('merge_type', 'MIX'),), "Merge Nodes (Color, Multiply)"),
    (NWMergeNodes.bl_idname, 'EIGHT', True, False, True,
        (('mode', 'MULTIPLY'), ('merge_type', 'MIX'),), "Merge Nodes (Color, Multiply)"),
    (NWMergeNodes.bl_idname, 'NUMPAD_MINUS', True, False, True,
        (('mode', 'SUBTRACT'), ('merge_type', 'MIX'),), "Merge Nodes (Color, Subtract)"),
    (NWMergeNodes.bl_idname, 'MINUS', True, False, True,
        (('mode', 'SUBTRACT'), ('merge_type', 'MIX'),), "Merge Nodes (Color, Subtract)"),
    (NWMergeNodes.bl_idname, 'NUMPAD_SLASH', True, False, True,
        (('mode', 'DIVIDE'), ('merge_type', 'MIX'),), "Merge Nodes (Color, Divide)"),
    (NWMergeNodes.bl_idname, 'SLASH', True, False, True,
        (('mode', 'DIVIDE'), ('merge_type', 'MIX'),), "Merge Nodes (Color, Divide)"),
    # NWMergeNodes with Ctrl Shift (MATH)
    (NWMergeNodes.bl_idname, 'NUMPAD_PLUS', True, True, False,
        (('mode', 'ADD'), ('merge_type', 'MATH'),), "Merge Nodes (Math, Add)"),
    (NWMergeNodes.bl_idname, 'EQUAL', True, True, False,
        (('mode', 'ADD'), ('merge_type', 'MATH'),), "Merge Nodes (Math, Add)"),
    (NWMergeNodes.bl_idname, 'NUMPAD_ASTERIX', True, True, False,
        (('mode', 'MULTIPLY'), ('merge_type', 'MATH'),), "Merge Nodes (Math, Multiply)"),
    (NWMergeNodes.bl_idname, 'EIGHT', True, True, False,
        (('mode', 'MULTIPLY'), ('merge_type', 'MATH'),), "Merge Nodes (Math, Multiply)"),
    (NWMergeNodes.bl_idname, 'NUMPAD_MINUS', True, True, False,
        (('mode', 'SUBTRACT'), ('merge_type', 'MATH'),), "Merge Nodes (Math, Subtract)"),
    (NWMergeNodes.bl_idname, 'MINUS', True, True, False,
        (('mode', 'SUBTRACT'), ('merge_type', 'MATH'),), "Merge Nodes (Math, Subtract)"),
    (NWMergeNodes.bl_idname, 'NUMPAD_SLASH', True, True, False,
        (('mode', 'DIVIDE'), ('merge_type', 'MATH'),), "Merge Nodes (Math, Divide)"),
    (NWMergeNodes.bl_idname, 'SLASH', True, True, False,
        (('mode', 'DIVIDE'), ('merge_type', 'MATH'),), "Merge Nodes (Math, Divide)"),
    (NWMergeNodes.bl_idname, 'COMMA', True, True, False,
        (('mode', 'LESS_THAN'), ('merge_type', 'MATH'),), "Merge Nodes (Math, Less than)"),
    (NWMergeNodes.bl_idname, 'PERIOD', True, True, False,
        (('mode', 'GREATER_THAN'), ('merge_type', 'MATH'),), "Merge Nodes (Math, Greater than)"),
    # BATCH CHANGE NODES
    # NWBatchChangeNodes with Alt
    (NWBatchChangeNodes.bl_idname, 'NUMPAD_0', False, False, True,
        (('blend_type', 'MIX'), ('operation', 'CURRENT'),), "Batch change blend type (Mix)"),
    (NWBatchChangeNodes.bl_idname, 'ZERO', False, False, True,
        (('blend_type', 'MIX'), ('operation', 'CURRENT'),), "Batch change blend type (Mix)"),
    (NWBatchChangeNodes.bl_idname, 'NUMPAD_PLUS', False, False, True,
        (('blend_type', 'ADD'), ('operation', 'ADD'),), "Batch change blend type (Add)"),
    (NWBatchChangeNodes.bl_idname, 'EQUAL', False, False, True,
        (('blend_type', 'ADD'), ('operation', 'ADD'),), "Batch change blend type (Add)"),
    (NWBatchChangeNodes.bl_idname, 'NUMPAD_ASTERIX', False, False, True,
        (('blend_type', 'MULTIPLY'), ('operation', 'MULTIPLY'),), "Batch change blend type (Multiply)"),
    (NWBatchChangeNodes.bl_idname, 'EIGHT', False, False, True,
        (('blend_type', 'MULTIPLY'), ('operation', 'MULTIPLY'),), "Batch change blend type (Multiply)"),
    (NWBatchChangeNodes.bl_idname, 'NUMPAD_MINUS', False, False, True,
        (('blend_type', 'SUBTRACT'), ('operation', 'SUBTRACT'),), "Batch change blend type (Subtract)"),
    (NWBatchChangeNodes.bl_idname, 'MINUS', False, False, True,
        (('blend_type', 'SUBTRACT'), ('operation', 'SUBTRACT'),), "Batch change blend type (Subtract)"),
    (NWBatchChangeNodes.bl_idname, 'NUMPAD_SLASH', False, False, True,
        (('blend_type', 'DIVIDE'), ('operation', 'DIVIDE'),), "Batch change blend type (Divide)"),
    (NWBatchChangeNodes.bl_idname, 'SLASH', False, False, True,
        (('blend_type', 'DIVIDE'), ('operation', 'DIVIDE'),), "Batch change blend type (Divide)"),
    (NWBatchChangeNodes.bl_idname, 'COMMA', False, False, True,
        (('blend_type', 'CURRENT'), ('operation', 'LESS_THAN'),), "Batch change blend type (Current)"),
    (NWBatchChangeNodes.bl_idname, 'PERIOD', False, False, True,
        (('blend_type', 'CURRENT'), ('operation', 'GREATER_THAN'),), "Batch change blend type (Current)"),
    (NWBatchChangeNodes.bl_idname, 'DOWN_ARROW', False, False, True,
        (('blend_type', 'NEXT'), ('operation', 'NEXT'),), "Batch change blend type (Next)"),
    (NWBatchChangeNodes.bl_idname, 'UP_ARROW', False, False, True,
        (('blend_type', 'PREV'), ('operation', 'PREV'),), "Batch change blend type (Previous)"),
    # LINK ACTIVE TO SELECTED
    # Don't use names, don't replace links (K)
    (NWLinkActiveToSelected.bl_idname, 'K', False, False, False,
        (('replace', False), ('use_node_name', False), ('use_outputs_names', False),), "Link active to selected (Don't replace links)"),
    # Don't use names, replace links (Shift K)
    (NWLinkActiveToSelected.bl_idname, 'K', False, True, False,
        (('replace', True), ('use_node_name', False), ('use_outputs_names', False),), "Link active to selected (Replace links)"),
    # Use node name, don't replace links (')
    (NWLinkActiveToSelected.bl_idname, 'QUOTE', False, False, False,
        (('replace', False), ('use_node_name', True), ('use_outputs_names', False),), "Link active to selected (Don't replace links, node names)"),
    # Use node name, replace links (Shift ')
    (NWLinkActiveToSelected.bl_idname, 'QUOTE', False, True, False,
        (('replace', True), ('use_node_name', True), ('use_outputs_names', False),), "Link active to selected (Replace links, node names)"),
    # Don't use names, don't replace links (;)
    (NWLinkActiveToSelected.bl_idname, 'SEMI_COLON', False, False, False,
        (('replace', False), ('use_node_name', False), ('use_outputs_names', True),), "Link active to selected (Don't replace links, output names)"),
    # Don't use names, replace links (')
    (NWLinkActiveToSelected.bl_idname, 'SEMI_COLON', False, True, False,
        (('replace', True), ('use_node_name', False), ('use_outputs_names', True),), "Link active to selected (Replace links, output names)"),
    # CHANGE MIX FACTOR
    (NWChangeMixFactor.bl_idname, 'LEFT_ARROW', False, False, True, (('option', -0.1),), "Reduce Mix Factor by 0.1"),
    (NWChangeMixFactor.bl_idname, 'RIGHT_ARROW', False, False, True, (('option', 0.1),), "Increase Mix Factor by 0.1"),
    (NWChangeMixFactor.bl_idname, 'LEFT_ARROW', False, True, True, (('option', -0.01),), "Reduce Mix Factor by 0.01"),
    (NWChangeMixFactor.bl_idname, 'RIGHT_ARROW', False, True, True, (('option', 0.01),), "Increase Mix Factor by 0.01"),
    (NWChangeMixFactor.bl_idname, 'LEFT_ARROW', True, True, True, (('option', 0.0),), "Set Mix Factor to 0.0"),
    (NWChangeMixFactor.bl_idname, 'RIGHT_ARROW', True, True, True, (('option', 1.0),), "Set Mix Factor to 1.0"),
    (NWChangeMixFactor.bl_idname, 'NUMPAD_0', True, True, True, (('option', 0.0),), "Set Mix Factor to 0.0"),
    (NWChangeMixFactor.bl_idname, 'ZERO', True, True, True, (('option', 0.0),), "Set Mix Factor to 0.0"),
    (NWChangeMixFactor.bl_idname, 'NUMPAD_1', True, True, True, (('option', 1.0),), "Mix Factor to 1.0"),
    (NWChangeMixFactor.bl_idname, 'ONE', True, True, True, (('option', 1.0),), "Set Mix Factor to 1.0"),
    # CLEAR LABEL (Alt L)
    (NWClearLabel.bl_idname, 'L', False, False, True, (('option', False),), "Clear node labels"),
    # MODIFY LABEL (Alt Shift L)
    (NWModifyLabels.bl_idname, 'L', False, True, True, None, "Modify node labels"),
    # Copy Label from active to selected
    (NWCopyLabel.bl_idname, 'V', False, True, False, (('option', 'FROM_ACTIVE'),), "Copy label from active to selected"),
    # DETACH OUTPUTS (Alt Shift D)
    (NWDetachOutputs.bl_idname, 'D', False, True, True, None, "Detach outputs"),
    # LINK TO OUTPUT NODE (O)
    (NWLinkToOutputNode.bl_idname, 'O', False, False, False, None, "Link to output node"),
    # SELECT PARENT/CHILDREN
    # Select Children
    (NWSelectParentChildren.bl_idname, 'RIGHT_BRACKET', False, False, False, (('option', 'CHILD'),), "Select children"),
    # Select Parent
    (NWSelectParentChildren.bl_idname, 'LEFT_BRACKET', False, False, False, (('option', 'PARENT'),), "Select Parent"),
    # Add Texture Setup
    (NWAddTextureSetup.bl_idname, 'T', True, False, False, None, "Add texture setup"),
    # Reset backdrop
    (NWResetBG.bl_idname, 'Z', False, False, False, None, "Reset backdrop image zoom"),
    # Delete unused
    (NWDeleteUnused.bl_idname, 'X', False, False, True, None, "Delete unused nodes"),
    # Frame Seleted
    (NWFrameSelected.bl_idname, 'P', False, True, False, None, "Frame selected nodes"),
    # Swap Outputs
    (NWSwapOutputs.bl_idname, 'S', False, False, True, None, "Swap Outputs"),
    # Emission Viewer
    (NWEmissionViewer.bl_idname, 'LEFTMOUSE', True, True, False, None, "Connect to Cycles Viewer node"),
    # Reload Images
    (NWReloadImages.bl_idname, 'R', False, False, True, None, "Reload images"),
    # Lazy Mix
    (NWLazyMix.bl_idname, 'RIGHTMOUSE', False, False, True, None, "Lazy Mix"),
    # Lazy Connect
    (NWLazyConnect.bl_idname, 'RIGHTMOUSE', True, False, False, None, "Lazy Connect"),
    # Lazy Connect with Menu
    (NWLazyConnect.bl_idname, 'RIGHTMOUSE', True, True, False, (('with_menu', True),), "Lazy Connect with Socket Menu"),
    # MENUS
    ('wm.call_menu', 'SPACE', True, False, False, (('name', NodeWranglerMenu.bl_idname),), "Node Wranger menu"),
    ('wm.call_menu', 'SLASH', False, False, False, (('name', NWAddReroutesMenu.bl_idname),), "Add Reroutes menu"),
    ('wm.call_menu', 'NUMPAD_SLASH', False, False, False, (('name', NWAddReroutesMenu.bl_idname),), "Add Reroutes menu"),
    ('wm.call_menu', 'EQUAL', False, True, False, (('name', NWNodeAlignMenu.bl_idname),), "Node alignment menu"),
    ('wm.call_menu', 'BACK_SLASH', False, False, False, (('name', NWLinkActiveToSelectedMenu.bl_idname),), "Link active to selected (menu)"),
    ('wm.call_menu', 'C', False, True, False, (('name', NWCopyToSelectedMenu.bl_idname),), "Copy to selected (menu)"),
    ('wm.call_menu', 'S', False, True, False, (('name', NWSwitchNodeTypeMenu.bl_idname),), "Switch node type menu"),
)


def register():
    # props
    bpy.types.Scene.NWBusyDrawing = StringProperty(
        name="Busy Drawing!",
        default="",
        description="An internal property used to store only the first mouse position")
    bpy.types.Scene.NWLazySource = StringProperty(
        name="Lazy Source!",
        default="x",
        description="An internal property used to store the first node in a Lazy Connect operation")
    bpy.types.Scene.NWLazyTarget = StringProperty(
        name="Lazy Target!",
        default="x",
        description="An internal property used to store the last node in a Lazy Connect operation")
    bpy.types.Scene.NWSourceSocket = IntProperty(
        name="Source Socket!",
        default=0,
        description="An internal property used to store the source socket in a Lazy Connect operation")

    bpy.utils.register_module(__name__)

    # keymaps
    km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name='Node Editor', space_type="NODE_EDITOR")
    for (identifier, key, CTRL, SHIFT, ALT, props, nicename) in kmi_defs:
        kmi = km.keymap_items.new(identifier, key, 'PRESS', ctrl=CTRL, shift=SHIFT, alt=ALT)
        if props:
            for prop, value in props:
                setattr(kmi.properties, prop, value)
        addon_keymaps.append((km, kmi))

    # menu items
    bpy.types.NODE_MT_select.append(select_parent_children_buttons)
    bpy.types.NODE_MT_category_SH_NEW_INPUT.prepend(attr_nodes_menu_func)
    bpy.types.NODE_PT_category_SH_NEW_INPUT.prepend(attr_nodes_menu_func)
    bpy.types.NODE_PT_backdrop.append(bgreset_menu_func)


def unregister():
    # props
    del bpy.types.Scene.NWBusyDrawing
    del bpy.types.Scene.NWLazySource
    del bpy.types.Scene.NWLazyTarget
    del bpy.types.Scene.NWSourceSocket

    bpy.utils.unregister_module(__name__)

    # keymaps
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    # menuitems
    bpy.types.NODE_MT_select.remove(select_parent_children_buttons)
    bpy.types.NODE_MT_category_SH_NEW_INPUT.remove(attr_nodes_menu_func)
    bpy.types.NODE_PT_category_SH_NEW_INPUT.remove(attr_nodes_menu_func)
    bpy.types.NODE_PT_backdrop.remove(bgreset_menu_func)

if __name__ == "__main__":
    register()
