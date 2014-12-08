#  RNA WIKI REFERENCE
#
# This file maps RNA to online URL's for right mouse context menu documentation access
#
# To make international, we made a script, 
# pointing the manuals to the proper language,
# specified in the 'User Preferences Window' by the users 
# Some Languages have their manual page, using a prefix or 
# being preceeded by their respective reference, for example
#
# Doc:2.6 --> Doc:FR/2.6
#
# The table in the script, contains all of the languages we have in the  
# Blender wiki website, for those other languages that still 
# doesn't have a team of translators, and/or don't have a manual for their languages
# we commented the lines below, you should add them to the language table
# when they have a proper manual in our Blender wiki, or added 
# to the Blender UI  translation table
# The Blender wiki manual uses a list of ISO_639-1 codes to convert languages to wiki manual prefixes 
#
# "DANISH":        "DK",     - Present in the wiki manual, but not present in Blender UI translations table
# "FARSI":         "FA",     - Present in the wiki manual, but not present in Blender UI translations table
# "KOREAN":        "KO",     - Present in the wiki manual, but not present in Blender UI translations table
# "LITHUANIAN":    "LT",     - Present in the wiki manual, but not present in Blender UI translations table
# "MACEDONIAN":    "MK",     - Present in the wiki manual, but not present in Blender UI translations table
# "MONGOLIAN":     "MN",     - Present in the wiki manual, but not present in Blender UI translations table
# "ROMANIAN":      "RO",     - Present in the wiki manual, but not present in Blender UI translations table
#
# "ESTONIAN":      "ET",     - Present in the wiki, as an empty page, not present in UI translations table
#
# "CROATIAN":      "HR",     - Present in Blender UI translations table, but without wiki manual
# "KYRGYZ":        "KY",     - Present in Blender UI translations table, but without wiki manual
# "NEPALI":        "NE",     - Present in Blender UI translations table, but without wiki manual
# "PERSIAN":       "FA",     - Present in Blender UI translations table, but without wiki manual
# "HEBREW":        "HE",     - Present in Blender UI translations table, but without wiki manual
# "HUNGARIAN":     "HU",     - Present in Blender UI translations table, but without wiki manual
# "SERBIAN_LATIN": "SR",     - Present in Blender UI translations table, but without wiki manual
#
# NOTES: 
#
#  CHINESE                   - Present in the wiki as simplified chinese, for both the traditional and simplified 
#  PORTUGUESE                - Present in the wiki for both Portuguese and Brazilian Portuguese
#  THAILANDESE               - It's the same being used for Turkish in the wiki
#
# URL prefix is the: url_manual_prefix + url_manual_mapping[id]

url_manual_prefix = "https://www.blender.org/manual/"

# TODO
"""
LANG = {
    "ARABIC":       "AR",
    "BULGARIAN":    "BG",
    "CATALAN":      "CA",
    "CZECH":        "CZ",
    "GERMAN":       "DE",
    "GREEK":        "EL",
    "RUSSIAN":      "RU",
    "SERBIAN":      "SR",
    "SWEDISH":      "SV",
    "TURKISH":      "TH",
    "UKRAINIAN":    "UK",
    "SPANISH":      "ES",
    "FINNISH":      "FI",
    "FRENCH":       "FR",
    "INDONESIAN":   "ID",
    "ITALIAN":      "IT",
    "JAPANESE":     "JA",
    "DUTCH":        "NL",
    "POLISH":       "PL",
    "PORTUGUESE":   "PT",
    "BRAZILIANPORTUGUESE":  "PT",
    "SIMPLIFIED_CHINESE":   "ZH",
    "TRADITIONAL_CHINESE":  "ZH",
}.get(__import__("bpy").context.user_preferences.system.language)

url_manual_prefix = url_manual_prefix \
    if LANG is None \
    else url_manual_prefix.replace("Doc:2.6", "Doc:" + LANG + "/" + "2.6")
"""

# - The first item is a wildcard - typical file system globbing
#   using python module 'fnmatch.fnmatch'
# - Expressions are evaluated top down (include catch-all expressions last).

url_manual_mapping = (

    # *** User Prefs ***
    ("bpy.types.UserPreferences.*",                "preferences"),
    ("bpy.types.UserPreferencesView.*",            "preferences/interface.html"),
    ("bpy.types.UserPreferencesEdit.*",            "preferences/editing.html"),
    ("bpy.types.UserPreferencesInput.*",           "preferences/input.html"),
    ("bpy.ops.wm.addon_*",                         "preferences/addons.html"),
    ("bpy.types.Theme.*",                          "preferences/themes.html"),
    ("bpy.types.UserPreferencesFilePaths.*",       "preferences/file.html"),
    ("bpy.types.UserPreferencesSystem.*",          "preferences/system.html"),
    ("bpy.types.UserSolidLight.*",                 "preferences/system.html"),

    # *** Modifiers ***
    # --- Intro ---
    ("bpy.types.Modifier.show_*", "modifiers/the_stack.html"),
    ("bpy.types.Modifier.*", "modifiers"),  # catchall for various generic options
    # --- Modify Modifiers ---
    ("bpy.types.MeshCacheModifier.*",              "modifiers/modify/mesh_cache.html"),
    ("bpy.types.UVProjectModifier.*",              "modifiers/modify/uv_project.html"),
    ("bpy.types.UVWarpModifier.*",                 "modifiers/modify/uv_warp.html"),
    ("bpy.types.VertexWeightMixModifier.*",        "modifiers/modify/vertex_weight.html"),
    ("bpy.types.VertexWeightEditModifier.*",       "modifiers/modify/vertex_weight.html"),
    ("bpy.types.VertexWeightProximityModifier.*",  "modifiers/modify/vertex_weight.html"),
    # --- Generate Modifiers ---
    ("bpy.types.ArrayModifier.*",      "modifiers/generate/array.html"),
    ("bpy.types.BevelModifier.*",      "modifiers/generate/bevel.html"),
    ("bpy.types.BooleanModifier.*",    "modifiers/generate/booleans.html"),
    ("bpy.types.BuildModifier.*",      "modifiers/generate/build.html"),
    ("bpy.types.DecimateModifier.*",   "modifiers/generate/decimate.html"),
    ("bpy.types.EdgeSplitModifier.*",  "modifiers/generate/edge_split.html"),
    ("bpy.types.MaskModifier.*",       "modifiers/generate/mask.html"),
    ("bpy.types.MirrorModifier.*",     "modifiers/generate/mirror.html"),
    ("bpy.types.MultiresModifier.*",   "modifiers/generate/multiresolution.html"),
    ("bpy.types.RemeshModifier.*",     "modifiers/generate/remesh.html"),
    ("bpy.types.ScrewModifier.*",      "modifiers/generate/screw.html"),
    ("bpy.types.SkinModifier.*",       "modifiers/generate/skin.html"),
    ("bpy.types.SolidifyModifier.*",   "modifiers/generate/solidify.html"),
    ("bpy.types.SubsurfModifier.*",    "modifiers/generate/subsurf.html"),
    ("bpy.types.TriangulateModifier.*","modifiers/generate/triangulate.html"),
    # --- Deform Modifiers ---
    ("bpy.types.ArmatureModifier.*",      "modifiers/deform/armature.html"),
    ("bpy.types.CastModifier.*",          "modifiers/deform/cast.html"),
    ("bpy.types.CurveModifier.*",         "modifiers/deform/curve.html"),
    ("bpy.types.DisplaceModifier.*",      "modifiers/deform/displace.html"),
    ("bpy.types.HookModifier.*",          "modifiers/deform/hooks.html"),
    ("bpy.types.LaplacianSmoothModifier.*", "modifiers/deform/laplacian_smooth.html"),
    ("bpy.types.LatticeModifier.*",       "modifiers/deform/lattice.html"),
    ("bpy.types.MeshDeformModifier.*",    "modifiers/deform/mesh_deform.html"),
    ("bpy.types.ShrinkwrapModifier.*",    "modifiers/deform/shrinkwrap.html"),
    ("bpy.types.SimpleDeformModifier.*",  "modifiers/deform/simple_deform.html"),
    ("bpy.types.SmoothModifier.*",        "modifiers/deform/smooth.html"),
    # ("bpy.types.SurfaceModifier.*",     "Modifiers/Deform/"),  # USERS NEVER SEE THIS
    ("bpy.types.WarpModifier.*",          "modifiers/deform/warp.html"),
    ("bpy.types.WaveModifier.*",          "modifiers/deform/wave.html"),
    # --- Simulate Modifiers ---
    ("bpy.types.ClothModifier.*",             "physics/cloth.html"),
    ("bpy.types.CollisionModifier.*",         "physics/collision.html"),
    ("bpy.types.DynamicPaintModifier.*",      "physics/dynamic_paint.html"),
    ("bpy.types.ExplodeModifier.*",           "modifiers/simulate/explode.html"),
    ("bpy.types.FluidSimulationModifier.*",   "physics/fluid.html"),
    ("bpy.types.OceanModifier.*",             "modifiers/simulate/ocean.html"),
    ("bpy.types.ParticleInstanceModifier.*",  "modifiers/simulate/particle_instance.html"),
    ("bpy.types.ParticleSystemModifier.*",    "physics/particles.html"),
    ("bpy.types.SmokeModifier.*",             "physics/smoke.html"),
    ("bpy.types.SoftBodyModifier.*",          "physics/soft_body.html"),

    # *** Constraints ***
    ("bpy.types.Constraint.*", "constraints.html"),
    ("bpy.types.Constraint.mute", "constraints/the_stack.html"),  # others could be added here?
    # --- Transform Constraints ---
    ("bpy.types.CopyLocationConstraint.*",    "constraints/transform/copy_location.html"),
    ("bpy.types.CopyRotationConstraint.*",    "constraints/transform/copy_rotation.html"),
    ("bpy.types.CopyScaleConstraint.*",       "constraints/transform/copy_scale.html"),
    ("bpy.types.CopyTransformsConstraint.*",  "constraints/transform/copy_transforms.html"),
    ("bpy.types.LimitDistanceConstraint.*",   "constraints/transform/limit_distance.html"),
    ("bpy.types.LimitLocationConstraint.*",   "constraints/transform/limit_location.html"),
    ("bpy.types.LimitRotationConstraint.*",   "constraints/transform/limit_rotation.html"),
    ("bpy.types.LimitScaleConstraint.*",      "constraints/transform/limit_scale.html"),
    ("bpy.types.MaintainVolumeConstraint.*",  "constraints/transform/maintain_volume.html"),
    ("bpy.types.TransformConstraint.*",       "constraints/transform/transformation.html"),
    # --- Tracking Constraints ---
    ("bpy.types.ClampToConstraint.*",      "constraints/tracking/clamp_to.html"),
    ("bpy.types.DampedTrackConstraint.*",  "constraints/tracking/damped_track.html"),
    ("bpy.types.KinematicConstraint.*",    "constraints/tracking/ik_solver.html"),
    ("bpy.types.LockedTrackConstraint.*",  "constraints/tracking/locked_track.html"),
    ("bpy.types.SplineIKConstraint.*",     "constraints/tracking/spline_ik.html"),
    ("bpy.types.StretchToConstraint.*",    "constraints/tracking/stretch_to.html"),
    ("bpy.types.TrackToConstraint.*",      "constraints/tracking/track_to.html"),
    # --- Relationship Constraints ---
    ("bpy.types.ActionConstraint.*",          "constraints/relationship/action.html"),
    ("bpy.types.CameraSolverConstraint.*",    "motion_tracking.html"),  # not exact match
    ("bpy.types.ChildOfConstraint.*",         "constraints/relationship/action.html"),
    ("bpy.types.FloorConstraint.*",           "constraints/relationship/child_of.html"),
    ("bpy.types.FollowPathConstraint.*",      "constraints/relationship/floor.html"),
    ("bpy.types.FollowTrackConstraint.*",     "constraints/relationship/follow_path.html"),
    ("bpy.types.ObjectSolverConstraint.*",    "motion_tracking.html"),  # not exact match
    ("bpy.types.PivotConstraint.*",           "constraints/relationship/pivot.html"),
    ("bpy.types.PythonConstraint.*",          "constraints/relationship/script.html"),
    ("bpy.types.RigidBodyJointConstraint.*",  "constraints/relationship/rigid_body_joint.html"),
    ("bpy.types.ShrinkwrapConstraint.*",      "constraints/relationship/shrinkwrap.html"),

    ("bpy.types.ImageFormatSettings.*",  "render/output.html#file-type"),
    ("bpy.types.RenderSettings.filepath",  "render/output.html#file-locations"),
    ("bpy.types.RenderSettings.display_mode",  "render/display.html#displaying-renders"),
    ("bpy.types.RenderSettings.*",       "render"),  # catchall, todo - refine

    # *** ID Subclasses ***
    ("bpy.types.Action.*", "animation/basics/actions.html"),
    #("bpy.types.Brush.*", ""),  # TODO - manual has no place for this! XXX
    ("bpy.types.Curve.*", "modeling/curves.html"),
    ("bpy.types.GreasePencil.*", "3d_interaction/sketching/drawing.html"),
    ("bpy.types.Group.*", "modeling/objects/groups_and_parenting.html#grouping-objects"),
    ("bpy.types.Image.*", "textures/types/image.html"),
    ("bpy.types.ShapeKey.*", "animation/techs/shape/shape_keys.html"), # not an id but include because of key
    ("bpy.types.Key.*", "animation/techs/shape/shape_keys.html"),
    #("bpy.types.Lattice.*", ""), # TODO - manual has no place for this! XXX
    ("bpy.types.Library.*", "data_system/linked_libraries.html"),
    #("bpy.types.Mask.*", ""), # TODO - manual has no place for this! XXX
    # *** Materials (blender internal) ***
    ("bpy.types.Material.diffuse*", "materials/properties/diffuse_shaders.html"),
    ("bpy.types.Material.specular*", "materials/properties/specular_shaders.html"),
    ("bpy.types.Material.ambient*", "materials/properties/shading.html"),
    ("bpy.types.Material.preview_render_type", "materials/properties/preview.html"),
    ("bpy.types.Material.*", "materials.html"),  # catchall, until the section is filled in

    # ("bpy.types.MaterialSlot.link", "materials/options.html#material-naming_and_linking"),  # TODO, T42839
    ("bpy.types.MaterialVolume.*", "materials/special_effects/volume.html"),
    ("bpy.types.MaterialHalo.*", "materials/special_effects/halo.html"),
    ("bpy.types.MaterialStrand.*", "materials/properties/strands.html"),
    ("bpy.types.MaterialSubsurfaceScattering.*", "materials/properties/subsurface_scattering.html"),
    ("bpy.types.MaterialRaytraceMirror.*", "materials/properties/mirror.html"),
    ("bpy.types.MaterialRaytraceTransparency.*", "materials/properties/transparency.html#raytraced-transparency"),
    # ... todo, many more options
    ("bpy.types.MovieClip.*", "motion_tracking.html#movie-clip_editor.html"),
    ("bpy.types.MovieTrackingCamera.*", "motion_tracking.html#camera-data_panel"),
    ("bpy.types.MovieTrackingStabilization.*", "motion_tracking.html#tools-available-in-reconstruction-mode"),
    ("bpy.types.MovieTrackingTrack*", "motion_tracking.html#tools-available-in-tracking-mode"),
    ("bpy.types.MovieTracking*", "motion_tracking.html"),
    ("bpy.types.SpaceClipEditor.*", "motion_tracking.html#movie-clip-editor"),
    ("bpy.types.ColorManaged*", "render/post_process/cm_and_exposure.html"),
    #("bpy.types.NodeTree.*", ""),  # dont document
    ("bpy.types.Object.*",  "modeling/objects.html"),  # catchall, todo - refine
    ("bpy.types.ParticleSettings.*", "physics/particles.html"),
    ("bpy.types.Scene.*", "interface/scenes.html"),
    ("bpy.types.Screen.*", "interface/screens.html"),
    #("bpy.types.Sound.*", ""), # TODO - manual has no place for this! XXX
    #("bpy.types.Speaker.*", ""), # TODO - manual has no place for this! XXX
    ("bpy.types.Text.*", "extensions/python/text_editor.html"),
    ("bpy.types.Texture.*", "textures.html"),
    ("bpy.types.VectorFont.*", "modeling/texts.html"),
    ("bpy.types.WindowManager.*", "interface/window_system.html"),
    ("bpy.types.World.*", "world.html"),
    ("bpy.types.WorldLighting.*ao*", "lighting/ambient_occlusion.html"),
    ("bpy.types.WorldLighting.*ambient*", "lighting/ambient_occlusion.html"),
    ("bpy.types.WorldLighting.*environment*", "lighting/ambient_light.html"),
    ("bpy.types.WorldLighting.*", "lighting/ambient_occlusion.html#gather"),  # only other WorldLighting props are in Gather panel

    # *** Cycles ***
    ("bpy.types.CyclesRenderSettings.*", "render/cycles/integrator.html"),
    ("bpy.types.CyclesVisibilitySettings.*", "render/cycles/light_paths.html#ray-visibility"),
    ("bpy.types.CyclesWorldSettings.*", "render/cycles/world.html"),
    ("bpy.types.SceneRenderLayer.*pass*", "render/post_process/passes.html"),
    ("bpy.types.SceneRenderLayer.*", "render/post_process/layers.html"),
    ("bpy.types.Cycles*", "render/cycles"),

    # Currently all manual links on all sockets and values (such as Fac, Roughness, Color...) are NodeSocket* type.
    # It'd be much better if the name of the socket could be used for the manual reference
    ("bpy.types.NodeSocket*", "composite_nodes/node_controls.html"),  # no generic socket type page exists, but composite types are the same

    # *** Cycles Material Nodes ***
    # Outputs
    ("bpy.types.ShaderNodeOutputLamp.*", "render/cycles/lamps.html"),
    ("bpy.types.ShaderNodeOutputMaterial.*", "render/cycles/materials"),
    ("bpy.types.ShaderNodeOutputWorld.*", "render/cycles/world.html"),
    # Shaders
    ("bpy.types.ShaderNodeAddShader.*", "render/cycles/nodes/shaders.html#mix-and-add"),
    ("bpy.types.ShaderNodeAmbientOcclusion.*", "render/cycles/nodes/shaders.html#ambient-occlusion"),
    ("bpy.types.ShaderNodeBackground.*", "render/cycles/nodes/shaders.html#background"),
    ("bpy.types.ShaderNodeBsdfAnisotropic.*", "render/cycles/nodes/shaders.html#anisotropic"),
    ("bpy.types.ShaderNodeBsdfDiffuse.*", "render/cycles/nodes/shaders.html#diffuse"),
    ("bpy.types.ShaderNodeBsdfGlass.*", "render/cycles/nodes/shaders.html#glass"),
    ("bpy.types.ShaderNodeBsdfGlossy.*", "render/cycles/nodes/shaders.html#glossy"),
    ("bpy.types.ShaderNodeBsdfHair.*", "render/cycles/nodes/shaders.html"),  # todo doc
    ("bpy.types.ShaderNodeBsdfRefraction.*", "render/cycles/nodes/shaders.html#refraction"),
    ("bpy.types.ShaderNodeBsdfToon.*", "render/cycles/nodes/shaders.html#toon"),
    ("bpy.types.ShaderNodeBsdfTranslucent.*", "render/cycles/nodes/shaders.html#translucent"),
    ("bpy.types.ShaderNodeBsdfTransparent.*", "render/cycles/nodes/shaders.html#transparent"),
    ("bpy.types.ShaderNodeBsdfVelvet.*", "render/cycles/nodes/shaders.html#velvet"),
    ("bpy.types.ShaderNodeEmission.*", "render/cycles/nodes/shaders.html#emission"),
    ("bpy.types.ShaderNodeHoldout.*", "render/cycles/nodes/shaders.html#holdout"),
    ("bpy.types.ShaderNodeMixShader.*", "render/cycles/nodes/shaders.html#mix-and-add"),
    ("bpy.types.ShaderNodeSubsurfaceScattering.*", "render/cycles/nodes/shaders.html#subsurface-scattering"),
    ("bpy.types.ShaderNodeVolumeAbsorption.*", "render/cycles/nodes/shaders.html"),  # todo doc
    ("bpy.types.ShaderNodeVolumeScatter.*", "render/cycles/nodes/shaders.html"),  # todo doc
    # Textures
    ("bpy.types.ShaderNodeTexBrick.*", "render/cycles/nodes/textures.html#brick-texture"),
    ("bpy.types.ShaderNodeTexChecker.*", "render/cycles/nodes/textures.html#checker-texture"),
    ("bpy.types.ShaderNodeTexEnvironment.*", "render/cycles/nodes/textures.html#environment-texture"),
    ("bpy.types.ShaderNodeTexGradient.*", "render/cycles/nodes/textures.html#gradient-texture"),
    ("bpy.types.ShaderNodeTexImage.*", "render/cycles/nodes/textures.html#image-texture"),
    ("bpy.types.ShaderNodeTexMagic.*", "render/cycles/nodes/textures.html#magic-texture"),
    ("bpy.types.ShaderNodeTexMusgrave.*", "render/cycles/nodes/textures.html#musgrave-texture"),
    ("bpy.types.ShaderNodeTexNoise.*", "render/cycles/nodes/textures.html#noise-texture"),
    ("bpy.types.ShaderNodeTexSky.*", "render/cycles/nodes/textures.html#sky-texture"),
    ("bpy.types.ShaderNodeTexVoronoi.*", "render/cycles/nodes/textures.html#voronoi-texture"),
    ("bpy.types.ShaderNodeTexWave.*", "render/cycles/nodes/textures.html#wave-texture"),
    # Other
    ("bpy.types.ShaderNodeAttribute.*", "render/cycles/nodes/more.html#attribute"),
    ("bpy.types.ShaderNodeBlackbody.*", "render/cycles/nodes/more.html#blackbody"),
    ("bpy.types.ShaderNodeBrightContrast.*", "composite_nodes/types/color.html#bright-contrast"),
    ("bpy.types.ShaderNodeBump.*", "render/cycles/nodes/more.html#bump"),
    ("bpy.types.ShaderNodeCameraData.*", "render/cycles/nodes/more.html"),  # TODO doc
    ("bpy.types.ShaderNodeCombineHSV.*", "composite_nodes/types/convertor.html#separate-combine-hsva-nodes"),
    ("bpy.types.ShaderNodeCombineRGB.*", "composite_nodes/types/convertor.html#separate-combine-rgba-node"),
    ("bpy.types.ShaderNodeFresnel.*", "render/cycles/nodes/more.html#fresnel"),
    ("bpy.types.ShaderNodeGamma.*", "composite_nodes/types/color.html#gamma"),
    ("bpy.types.ShaderNodeGeometry.*", "render/cycles/nodes/more.html#geometry"),
    ("bpy.types.ShaderNodeHairInfo.*", "render/cycles/nodes/more.html#hair-info"),
    ("bpy.types.ShaderNodeHueSaturation.*", "composite_nodes/types/color.html#hue-saturation-node"),
    ("bpy.types.ShaderNodeInvert.*", "composite_nodes/types/color.html#invert"),
    ("bpy.types.ShaderNodeLayerWeight.*", "render/cycles/nodes/more.html#layer-weight"),
    ("bpy.types.ShaderNodeLightFalloff.*", "render/cycles/nodes/more.html#light-falloff"),
    ("bpy.types.ShaderNodeLightPath.*", "render/cycles/nodes/more.html#light-path"),
    ("bpy.types.ShaderNodeMapping.*", "render/cycles/nodes/more.html#mapping"),
    ("bpy.types.ShaderNodeMath.*", "composite_nodes/types/convertor.html#math-node"),
    ("bpy.types.ShaderNodeMixRGB.*", "composite_nodes/types/color.html#mix-node"),
    ("bpy.types.ShaderNodeNormalMap.*", "render/cycles/nodes/more.html#normal-map"),
    ("bpy.types.ShaderNodeObjectInfo.*", "render/cycles/nodes/more.html#object-info"),
    ("bpy.types.ShaderNodeParticleInfo.*", "render/cycles/nodes/more.html#particle-info"),
    ("bpy.types.ShaderNodeRGB.*", "render/cycles/nodes/more.html#rgb"),
    ("bpy.types.ShaderNodeRGBCurve.*", "composite_nodes/types/color.html#rgb-curves-node"),
    ("bpy.types.ShaderNodeRGBToBW.*", "composite_nodes/types/convertor.html#rgb-to-bw-node"),
    ("bpy.types.ShaderNodeSeparateHSV.*", "composite_nodes/types/convertor.html#separate-combine-hsva-nodes"),
    ("bpy.types.ShaderNodeSeparateRGB.*", "composite_nodes/types/convertor.html#separate-combine-rgba-node"),
    ("bpy.types.ShaderNodeTangent.*", "render/cycles/nodes/more.html#tangent"),
    ("bpy.types.ShaderNodeTexCoord.*", "render/cycles/nodes/more.html#texture-coordinates"),
    ("bpy.types.ShaderNodeValue.*", "render/cycles/nodes/more.html#value"),
    ("bpy.types.ShaderNodeVectorCurve.*", "composite_nodes/types/vector.html#vector-curves-node"),
    ("bpy.types.ShaderNodeVectorMath.*", "render/cycles/nodes/more.html"),  # TODO doc
    ("bpy.types.ShaderNodeVectorTransform.*", "render/cycles/nodes/more.html#vector-transform"),

    ("bpy.types.ShaderNodeWavelength.*", "render/cycles/nodes/more.html#wavelength"),
    ("bpy.types.ShaderNodeWireframe.*", "render/cycles/nodes/more.html#wireframe"),

    ("bpy.types.ShaderNodeGroup.*", "composite_nodes/node_groups.html"),
    ("bpy.types.ShaderNode*", "render/cycles/nodes"),

    ("bpy.types.ShaderNodeScript.*", "render/cycles/nodes/osl.html"),

    # *** Compositing Nodes ***
    # Input
    ("bpy.types.CompositorNodeBokehImage.*", "composite_nodes/types/input.html"),  # todo doc
    ("bpy.types.CompositorNodeImage.*", "composite_nodes/types/input.html#image-node"),
    ("bpy.types.CompositorNodeMask.*", "composite_nodes/types/input.html"),  # todo doc
    ("bpy.types.CompositorNodeMovieClip.*", "composite_nodes/types/input.html"),  # todo doc
    ("bpy.types.CompositorNodeRGB.*", "composite_nodes/types/input.html#rgb-node"),
    ("bpy.types.CompositorNodeRLayers.*", "composite_nodes/types/input.html#render-layers-node"),
    ("bpy.types.CompositorNodeTexture.*", "composite_nodes/types/input.html#texture-node"),
    ("bpy.types.CompositorNodeTime.*", "composite_nodes/types/input.html#time-node"),
    ("bpy.types.CompositorNodeTrackPos.*", "composite_nodes/types/input.html"),  # todo doc
    ("bpy.types.CompositorNodeValue.*", "composite_nodes/types/input.html#value-node"),
    # Output
    ("bpy.types.CompositorNodeComposite.*", "composite_nodes/types/output.html#composite-output-nodes"),
    ("bpy.types.CompositorNodeLevels.*", "composite_nodes/types/output.html#levels-node"),
    ("bpy.types.CompositorNodeOutputFile*", "composite_nodes/types/output.html#file-output-node"),
    ("bpy.types.CompositorNodeSplitViewer.*", "composite_nodes/types/output.html#splitviewer-node"),
    ("bpy.types.CompositorNodeViewer.*", "composite_nodes/types/output.html#viewer"),
    # Color
    ("bpy.types.CompositorNodeAlphaOver.*", "composite_nodes/types/color.html#alphaover-node"),
    ("bpy.types.CompositorNodeBrightContrast.*", "composite_nodes/types/color.html#bright-contrast"),
    ("bpy.types.CompositorNodeColorBalance.*", "composite_nodes/types/color.html#color-balance"),
    ("bpy.types.CompositorNodeColorCorrection.*", "composite_nodes/types/color.html"),  # todo doc
    ("bpy.types.CompositorNodeCurveRGB.*", "composite_nodes/types/color.html#rgb-curves-node"),
    ("bpy.types.CompositorNodeGamma.*", "composite_nodes/types/color.html#gamma"),
    ("bpy.types.CompositorNodeHueCorrect.*", "composite_nodes/types/color.html#hue-correct"),
    ("bpy.types.CompositorNodeHueSat.*", "composite_nodes/types/color.html#hue-saturation-node"),
    ("bpy.types.CompositorNodeInvert.*", "composite_nodes/types/color.html#invert"),
    ("bpy.types.CompositorNodeMixRGB.*", "composite_nodes/types/color.html#mix-node"),
    ("bpy.types.CompositorNodeTonemap.*", "composite_nodes/types/color.html#tone-map"),
    ("bpy.types.CompositorNodeZcombine.*", "composite_nodes/types/color.html#z-combine-node"),
    # Converter (Misspelt 'Convertor' in wiki)
    ("bpy.types.CompositorNodeSep*", "composite_nodes/types/convertor.html#combine-separate-nodes"),
    ("bpy.types.CompositorNodeComb*", "composite_nodes/types/convertor.html#combine-separate-nodes"),
    ("bpy.types.CompositorNodeIDMask.*", "composite_nodes/types/convertor.html#id-mask-node"),
    ("bpy.types.CompositorNodeMath.*", "composite_nodes/types/convertor.html#math-node"),
    ("bpy.types.CompositorNodePremulKey.*", "composite_nodes/types/convertor.html#alpha-convert"),
    ("bpy.types.CompositorNodeRGBToBW.*", "composite_nodes/types/convertor.html#rgb-to-bw-node"),
    ("bpy.types.CompositorNodeSetAlpha.*", "composite_nodes/types/convertor.html#set-alpha-node"),
    # Filter
    ("bpy.types.CompositorNodeBilateralblur.*", "composite_nodes/types/filter.html#bilateral-blur-node"),
    ("bpy.types.CompositorNodeBlur.*", "composite_nodes/types/filter.html#blur-node"),
    ("bpy.types.CompositorNodeBokehBlur.*", "composite_nodes/types/filter.html"),  # todo doc
    ("bpy.types.CompositorNodeDBlur.*", "composite_nodes/types/filter.html#directional-blur-node"),
    ("bpy.types.CompositorNodeDefocus.*", "composite_nodes/types/filter.html#defocus"),
    ("bpy.types.CompositorNodeDespeckle.*", "composite_nodes/types/filter.html"),  # todo doc
    ("bpy.types.CompositorNodeDilateErode.*", "composite_nodes/types/filter.html#dilate-erode-node"),
    ("bpy.types.CompositorNodeFilter.*", "composite_nodes/types/filter.html#filter-node"),
    ("bpy.types.CompositorNodeGlare.*", "composite_nodes/types/filter.html"),  # todo doc
    ("bpy.types.CompositorNodeInpaint.*", "composite_nodes/types/filter.html"),  # todo doc
    ("bpy.types.CompositorNodePixelate.*", "composite_nodes/types/filter.html"),  # todo doc
    ("bpy.types.CompositorNodeVecBlur.*", "composite_nodes/types/filter.html#vector-motion-blur-node"),
    # Vector
    ("bpy.types.CompositorNodeCurveVec.*", "composite_nodes/types/vector.html#vector-curves-node"),
    ("bpy.types.CompositorNodeMapRange.*", "composite_nodes/types/vector.html"),  # todo doc
    ("bpy.types.CompositorNodeMapValue.*", "composite_nodes/types/vector.html#map-value-node"),
    ("bpy.types.CompositorNodeNormal.*", "composite_nodes/types/vector.html#normal-node"),
    ("bpy.types.CompositorNodeNormalize.*", "composite_nodes/types/vector.html#normalize"),
    # Matte
    ("bpy.types.CompositorNodeBoxMask.*", "composite_nodes/types/matte.html"),  # todo doc
    ("bpy.types.CompositorNodeChannelMatte.*", "composite_nodes/types/matte.html#channel-key-node"),
    ("bpy.types.CompositorNodeChromaMatte.*", "composite_nodes/types/matte.html#chroma-key-node"),
    ("bpy.types.CompositorNodeColorMatte.*", "composite_nodes/types/matte.html#color-key"),
    ("bpy.types.CompositorNodeColorSpill.*", "composite_nodes/types/matte.html#color-spill-node"),
    ("bpy.types.CompositorNodeDiffMatte.*", "composite_nodes/types/matte.html#difference-key-node"),
    ("bpy.types.CompositorNodeDistanceMatte.*", "composite_nodes/types/matte.html#distance-key"),  # TODO doc (header is there, no text)
    ("bpy.types.CompositorNodeDoubleEdgeMask.*", "composite_nodes/types/matte.html"),  # todo doc
    ("bpy.types.CompositorNodeEllipseMask.*", "composite_nodes/types/matte.html"),  # todo doc
    ("bpy.types.CompositorNodeKeying.*", "composite_nodes/types/matte.html"),  # todo doc
    ("bpy.types.CompositorNodeKeyingScreen.*", "composite_nodes/types/matte.html"),  # todo doc
    ("bpy.types.CompositorNodeLumaMatte.*", "composite_nodes/types/matte.html#luminance-key-node"),
    # Distort
    ("bpy.types.CompositorNodeCrop.*", "composite_nodes/types/distort.html#crop-node"),
    ("bpy.types.CompositorNodeDisplace.*", "composite_nodes/types/distort.html#displace-node"),
    ("bpy.types.CompositorNodeFlip.*", "composite_nodes/types/distort.html#flip-node"),
    ("bpy.types.CompositorNodeLensdist.*", "composite_nodes/types/distort.html#lens-distortion"),
    ("bpy.types.CompositorNodeMapUV.*", "composite_nodes/types/distort.html#map-uv-node"),
    ("bpy.types.CompositorNodeMovieDistortion.*", "composite_nodes/types/distort.html"),  # todo doc
    ("bpy.types.CompositorNodePlaneTrackDeform.*", "composite_nodes/types/distort.html"),  # todo doc
    ("bpy.types.CompositorNodeRotate.*", "composite_nodes/types/distort.html#rotate-node"),
    ("bpy.types.CompositorNodeScale.*", "composite_nodes/types/distort.html#scale-node"),
    ("bpy.types.CompositorNodeStabilize.*", "composite_nodes/types/distort.html"),  # todo doc
    ("bpy.types.CompositorNodeTransform.*", "composite_nodes/types/distort.html"),  # todo doc
    ("bpy.types.CompositorNodeTranslate.*", "composite_nodes/types/distort.html#translate-node"),
    #Other
    ("bpy.types.CompositorNodeGroup.*", "composite_nodes/node_groups.html"),
    ("bpy.types.CompositorNode*", "composite_nodes/types.html"),  # catch anything else

    ("bpy.types.ColorRamp*", "materials/properties/ramps.html"),

    # *** ID Subclasses (cont.) Object Data ***
    ("bpy.types.Mesh.*",  "modeling/meshes.html"),  # catchall, todo - refine
    ("bpy.types.MetaBall.*",  "modeling/metas.html"),  # catchall, todo - refine
    ("bpy.types.TextCurve.*",  "modeling/texts.html"),  # catchall, todo - refine
    ("bpy.types.Armature.*",  "rigging/armatures.html"),  # catchall, todo - refine
    ("bpy.types.Camera.*",  "render/camera"),  # catchall, todo - refine

    ("bpy.types.PointLamp.*",  "lighting/lamps/lamp.html"),  # catchall, todo - refine
    ("bpy.types.AreaLamp.*",   "lighting/lamps/area.html"),  # catchall, todo - refine
    ("bpy.types.SpotLamp.*",   "lighting/lamps/spot.html"),  # catchall, todo - refine
    ("bpy.types.SunLamp.*",    "lighting/lamps/sun.html"),   # catchall, todo - refine
    ("bpy.types.HemiLamp.*",   "lighting/lamps/hemi.html"),  # catchall, todo - refine
    ("bpy.types.Lamp.*",       "lighting.html"),             # catchall, todo - refine

    # --- Animation ---
    ("bpy.types.Keyframe.*", "animation/basics/actions.html"),
    ("bpy.types.FCurve.*", "animation/editors/graph/fcurves.html"),
    
    # --- Rigging ---
    ("bpy.types.Bone.*",      "rigging/armatures/bones.html"),
    ("bpy.types.EditBone.*",  "rigging/armatures/bones.html"),
    ("bpy.types.PoseBone.*",  "rigging/posing.html"),

    # --- World ---
    ("bpy.types.World.*",  "world.html"),

    ("bpy.types.Texture.*",  "textures.html"),

    # *** Spaces ***
    ("bpy.types.SpaceView3D.*", "3d_interaction/navigating/3d_view_options.html"),

    # === Operators ===
    # Catch all only for now!
    # *** Window/Screen ***
    
    ("bpy.ops.action.*",  "animation/basics/actions.html"),
    ("bpy.ops.anim.*",  "animation.html"),
    ("bpy.ops.armature.*",  "rigging/armatures.html"),
    ("bpy.ops.boid.*",  "physics/particles/physics/boids.html"),
    # ("bpy.ops.brush.*",  ""),  # TODO
    ("bpy.ops.buttons.*",  "interface/buttons_and_controls.html"),
    ("bpy.ops.camera.*",  "render/camera"),
    ("bpy.ops.clip.*",  "motion_tracking.html#movie-clip-editor"),
    ("bpy.ops.cloth.*",  "physics/cloth.html"),
    ("bpy.ops.console.*",  "extensions/python/console.html"),
    ("bpy.ops.constraint.*",  "constraints.html"),
    ("bpy.ops.curve.*",  "modeling/curves.html"),
    ("bpy.ops.dpaint.*",  "physics/dynamic_paint.html"),
    # ("bpy.ops.ed.*",  ""),  # TODO, this is for internal use only?
    # ("bpy.ops.export_anim.*",  ""),  # TODO
    # ("bpy.ops.export_mesh.*",  ""),  # TODO
    # ("bpy.ops.export_scene.*",  ""),  # TODO
    ("bpy.ops.file.*",  ""),
    ("bpy.ops.fluid.*",  "physics/fluid.html"),
    ("bpy.ops.font.*",  "modeling/texts.html"),
    ("bpy.ops.gpencil.*",  "3d_interaction/sketching/drawing.html"),
    ("bpy.ops.graph.*",  "animation/editors/graph/fcurves.html"),
    ("bpy.ops.group.*",  "modeling/objects/groups_and_parenting.html#grouping-objects"),
    ("bpy.ops.image.*",  "textures/types/image.html"),
    # ("bpy.ops.import_anim.*",  ""),  # TODO
    # ("bpy.ops.import_curve.*",  ""),  # TODO
    # ("bpy.ops.import_mesh.*",  ""),  # TODO
    # ("bpy.ops.import_scene.*",  ""),  # TODO
    # ("bpy.ops.info.*",  ""),  # TODO
    ("bpy.ops.lamp.*",  "lighting.html"),  # --- todo ... all below ---
    # ("bpy.ops.lattice.*",  ""),  # TODO
    ("bpy.ops.logic.*",  "game_engine/logic.html"),
    ("bpy.ops.marker.*",  "animation/basics/markers.html"),
    # ("bpy.ops.mask.*",  ""),  # TODO
    ("bpy.ops.material.new",  "materials/assigning_a_material.html#creating-a-new-material"),
    ("bpy.ops.material.*",  "materials.html"),
    ("bpy.ops.mesh.vertices_smooth", "modeling/meshes/editing/deforming/smooth.html"),
    ("bpy.ops.view3d.edit_mesh_extrude*", "modeling/meshes/editing/duplicating/extrude.html"),
    ("bpy.ops.mesh.subdivide", "modeling/meshes/editing/subdividing/subdivide.html"),
    ("bpy.ops.mesh.loopcut_slide", "modeling/meshes/editing/subdividing/loop_subdivide.html"),
    ("bpy.ops.mesh.bridge-edge-loops", "modeling/meshes/editing/edges.html#bridge-edge-loops"),
    ("bpy.ops.mesh.duplicate_move", "modeling/meshes/editing/duplicating/duplicate.html"),
    ("bpy.ops.mesh.spin", "modeling/meshes/editing/duplicating/spin.html"),
    ("bpy.ops.mesh.screw", "modeling/meshes/editing/duplicating/screw.html"),
    ("bpy.ops.mesh.knife*", "modeling/meshes/editing/subdividing/knife_subdivide.html"),
    ("bpy.ops.mesh.bisect", "modeling/meshes/editing/subdividing/bisect.html"),
    ("bpy.ops.mball.*",  "modeling/metas.html"),
    ("bpy.ops.mesh.*",  "modeling/meshes.html"),
    ("bpy.ops.nla.*",  "animation/editors/nla.html"),
    # ("bpy.ops.node.*",  ""),  # TODO
    ("bpy.ops.object.*shape_key*", "animation/techs/shape/shape_keys.html"),
    ("bpy.ops.object.join_shapes", "animation/techs/shape/shape_keys.html"),
    ("bpy.ops.object.*",  "modeling/objects.html"),
    ("bpy.ops.outliner.*",  "data_system/the_outliner.html"),
    # ("bpy.ops.paint.*",  ""),  # TODO
    ("bpy.ops.particle.*",  "physics/particles.html"),
    ("bpy.ops.pose.*",  "rigging/posing.html"),
    ("bpy.ops.poselib.*",  "rigging/posing/pose_library.html"),
    # ("bpy.ops.ptcache.*",  ""),  # TODO

    ("bpy.ops.render.play-rendered-anim",  "render/display.html#animation-playback"),
    ("bpy.ops.render.*",  "render"),  # catchall

    ("bpy.ops.scene.*",  "interface/scenes.html"),
    ("bpy.ops.screen.*",  "interface/window_system.html"),
    ("bpy.ops.script.*",  "extensions/python.html"),
    ("bpy.ops.sculpt.*",  "modeling/meshes/editing/sculpt_mode.html"),
    ("bpy.ops.sequencer.*",  "sequencer/usage.html"),
    # ("bpy.ops.sketch.*",  ""),  # TODO
    # ("bpy.ops.sound.*",  ""),  # TODO
    ("bpy.ops.surface.*",  "modeling/surfaces.html"),
    ("bpy.ops.text.*",  "extensions/python/text_editor.html"),
    ("bpy.ops.texture.*",  "textures.html"),
    ("bpy.ops.time.*",  "animation/editors/timeline.html"),
    ("bpy.ops.transform.edge_slide", "modeling/meshes/editing/edges.html#edge-slide"),
    ("bpy.ops.transform.vert_slide", "modeling/meshes/editing/vertices.html#vertex-slide"),
    ("bpy.ops.transform.shrink_fatten", "modeling/meshes/editing/deforming/shrink-fatten.html"),
    ("bpy.ops.transform.push_pull", "3d_interaction/transformations/advanced/push_pull.html"),
    ("bpy.ops.transform.*",  "3d_interaction/transform_control.html"),
    ("bpy.ops.ui.*",  "interface.html"),
    ("bpy.ops.uv.*",  "textures/mapping/uv/layout_editing.html"),
    # ("bpy.ops.view2d.*",  ""),  # TODO
    ("bpy.ops.view3d.*",  "3d_interaction/navigating/3d_view.html"),  # this link is a bit arbitrary
    ("bpy.ops.wm.*",      "interface/window_system.html"),
    ("bpy.ops.world.*",  "world.html"),
    
    # === Tool Settings ===
    ("bpy.types.MeshStatVis.*",  "modeling/meshes.html#mesh-analysis"),
)

# may have 'url_reference_mapping'... etc later
