#  RNA MANUAL REFERENCE
#
# This file maps RNA to online URL's for right mouse context menu documentation access
#
# To make international, we made a script,
# pointing the manuals to the proper language,
# specified in the 'User Preferences Window' by the users
# Some Languages have their manual page, using a prefix or
# being preceded by their respective reference, for example
#
# manual/ --> manual/ru/
#
# The table in the script, contains all of the languages we have in the
# Blender manual website, for those other languages that still
# doesn't have a team of translators, and/or don't have a manual for their languages
# we commented the lines below, you should add them to the language table
# when they have a proper manual in our Blender manual, or added
# to the Blender UI  translation table
# The Blender manual uses a list of ISO_639-1 codes to convert languages to manual prefixes
#
# URL is the: url_manual_prefix + url_manual_mapping[id]

import bpy

url_manual_prefix = "https://www.blender.org/manual/"

language = ""
if bpy.context.user_preferences.system.use_international_fonts:
    language = bpy.context.user_preferences.system.language
    if language == 'DEFAULT':
        import os
        language = os.getenv('LANG', '').split('.')[0]

LANG = {
#   "ar_EG":        "ar",
#   "bg_BG":        "bg",
#   "ca_AD":        "ca",
#   "cs_CZ":        "cz",
    "de_DE":        "de",  # German.
#   "el_GR":        "el",
    "ru_RU":        "ru",  # Russian.
#   "sr_RS":        "sr",
#   "sv_SE":        "sv",
#   "tr_TR":        "th",
#   "uk_UA":        "uk",
#   "es":           "es",
#   "fi_FI":        "fi",
    "fr_FR":        "fr",  # French.
#   "id_ID":        "id",
#   "it_IT":        "it",
#   "ja_JP":        "ja",
#   "nl_NL":        "nl",
#   "pl_PL":        "pl",
#   "pt_PT":        "pt",
#   "pt_BR":        "pt",
    "zh_CN":        "zh.cn",  # Chinese - Should be changed to "zh_cn" but there is a bug in sphinx-intl.
    "zh_TW":        "zh.cn",  # Taiwanese Chinese - for until we have a zh_tw version?
}.get(language)

if LANG is not None:
    url_manual_prefix = url_manual_prefix.replace("manual", "manual/" + LANG)

# - The first item is a wildcard - typical file system globbing
#   using python module 'fnmatch.fnmatch'
# - Expressions are evaluated top down (include catch-all expressions last).

url_manual_mapping = (

    # *** User Prefs ***
    ("bpy.types.UserPreferences.*",                "preferences"),
    ("bpy.types.UserPreferencesView.*",            "preferences/interface.html"),
    ("bpy.types.UserPreferencesEdit.*",            "preferences/editing.html"),
    ("bpy.types.UserPreferencesInput.*",           "preferences/input.html"),
    ("bpy.ops.wm.addon_*",                         "preferences/add_ons.html"),
    ("bpy.types.Theme.*",                          "preferences/themes.html"),
    ("bpy.types.UserPreferencesFilePaths.*",       "preferences/file.html"),
    ("bpy.types.UserPreferencesSystem.*",          "preferences/system.html"),
    ("bpy.types.UserSolidLight.*",                 "preferences/system.html"),

    # *** Modifiers ***
    # --- Intro ---
    ("bpy.types.Modifier.show_*", "modeling/modifiers/the_stack.html"),
    ("bpy.types.Modifier.*", "modeling/modifiers"),  # catchall for various generic options
    # --- Modify Modifiers ---
    ("bpy.types.DataTransferModifier.*",           "modeling/modifiers/modify/data_transfer.html"),
    ("bpy.types.MeshCacheModifier.*",              "modeling/modifiers/modify/mesh_cache.html"),
    ("bpy.types.NormalEditModifier.*",             "modeling/modifiers/modify/normal_edit.html"),
    ("bpy.types.UVProjectModifier.*",              "modeling/modifiers/modify/uv_project.html"),
    ("bpy.types.UVWarpModifier.*",                 "modeling/modifiers/modify/uv_warp.html"),
    ("bpy.types.VertexWeightMixModifier.*",        "modeling/modifiers/modify/vertex_weight.html"),
    ("bpy.types.VertexWeightEditModifier.*",       "modeling/modifiers/modify/vertex_weight.html"),
    ("bpy.types.VertexWeightProximityModifier.*",  "modeling/modifiers/modify/vertex_weight.html"),
    # --- Generate Modifiers ---
    ("bpy.types.ArrayModifier.*",            "modeling/modifiers/generate/array.html"),
    ("bpy.types.BevelModifier.*",            "modeling/modifiers/generate/bevel.html"),
    ("bpy.types.BooleanModifier.*",          "modeling/modifiers/generate/booleans.html"),
    ("bpy.types.BuildModifier.*",            "modeling/modifiers/generate/build.html"),
    ("bpy.types.DecimateModifier.*",         "modeling/modifiers/generate/decimate.html"),
    ("bpy.types.EdgeSplitModifier.*",        "modeling/modifiers/generate/edge_split.html"),
    ("bpy.types.MaskModifier.*",             "modeling/modifiers/generate/mask.html"),
    ("bpy.types.MirrorModifier.*",           "modeling/modifiers/generate/mirror.html"),
    ("bpy.types.MultiresModifier.*",         "modeling/modifiers/generate/multiresolution.html"),
    ("bpy.types.RemeshModifier.*",           "modeling/modifiers/generate/remesh.html"),
    ("bpy.types.ScrewModifier.*",            "modeling/modifiers/generate/screw.html"),
    ("bpy.types.SkinModifier.*",             "modeling/modifiers/generate/skin.html"),
    ("bpy.types.SolidifyModifier.*",         "modeling/modifiers/generate/solidify.html"),
    ("bpy.types.SubsurfModifier.*",          "modeling/modifiers/generate/subsurf.html"),
    ("bpy.types.TriangulateModifier.*",      "modeling/modifiers/generate/triangulate.html"),
    ("bpy.types.WireframeModifier.*",        "modeling/modifiers/generate/wireframe.html"),
    # --- Deform Modifiers ---
    ("bpy.types.ArmatureModifier.*",         "modeling/modifiers/deform/armature.html"),
    ("bpy.types.CastModifier.*",             "modeling/modifiers/deform/cast.html"),
    ("bpy.types.CorrectiveSmoothModifier.*", "modeling/modifiers/deform/corrective_smooth.html"),
    ("bpy.types.CurveModifier.*",            "modeling/modifiers/deform/curve.html"),
    ("bpy.types.DisplaceModifier.*",         "modeling/modifiers/deform/displace.html"),
    ("bpy.types.HookModifier.*",             "modeling/modifiers/deform/hooks.html"),
    ("bpy.types.LaplacianSmoothModifier.*",  "modeling/modifiers/deform/laplacian_smooth.html"),
    ("bpy.types.LaplacianDeformModifier.*",  "modeling/modifiers/deform/laplacian_deform.html"),
    ("bpy.types.LatticeModifier.*",          "modeling/modifiers/deform/lattice.html"),
    ("bpy.types.MeshDeformModifier.*",       "modeling/modifiers/deform/mesh_deform.html"),
    ("bpy.types.ShrinkwrapModifier.*",       "modeling/modifiers/deform/shrinkwrap.html"),
    ("bpy.types.SimpleDeformModifier.*",     "modeling/modifiers/deform/simple_deform.html"),
    ("bpy.types.SmoothModifier.*",           "modeling/modifiers/deform/smooth.html"),
    # ("bpy.types.SurfaceModifier.*",        "Modifiers/Deform/"),  # USERS NEVER SEE THIS
    ("bpy.types.WarpModifier.*",             "modeling/modifiers/deform/warp.html"),
    ("bpy.types.WaveModifier.*",             "modeling/modifiers/deform/wave.html"),
    # --- Simulate Modifiers ---
    ("bpy.types.ClothModifier.*",             "physics/cloth"),
    ("bpy.types.CollisionModifier.*",         "physics/collision.html"),
    ("bpy.types.DynamicPaintModifier.*",      "physics/dynamic_paint"),
    ("bpy.types.ExplodeModifier.*",           "modeling/modifiers/simulate/explode.html"),
    ("bpy.types.FluidSimulationModifier.*",   "physics/fluid"),
    ("bpy.types.OceanModifier.*",             "modeling/modifiers/simulate/ocean.html"),
    ("bpy.types.ParticleInstanceModifier.*",  "modeling/modifiers/simulate/particle_instance.html"),
    ("bpy.types.ParticleSystemModifier.*",    "physics/particles"),
    ("bpy.types.SmokeModifier.*",             "physics/smoke"),
    ("bpy.types.SoftBodyModifier.*",          "physics/soft_body"),

    # *** Constraints ***
    ("bpy.types.Constraint.*",                "rigging/constraints"),
    ("bpy.types.Constraint.mute",             "rigging/constraints/interface/the_stack.html"),  # others could be added here?
    # --- Motion Tracking Constraints ---
    ("bpy.types.FollowTrackConstraint.*",     "rigging/constraints/motion_tracking/follow_track.html"),
    ("bpy.types.ObjectSolverConstraint.*",    "rigging/constraints/motion_tracking/object_solver.html"),
    ("bpy.types.CameraSolverConstraint.*",    "rigging/constraints/motion_tracking/camera_solver.html"),
    # --- Transform Constraints ---
    ("bpy.types.CopyLocationConstraint.*",    "rigging/constraints/transform/copy_location.html"),
    ("bpy.types.CopyRotationConstraint.*",    "rigging/constraints/transform/copy_rotation.html"),
    ("bpy.types.CopyScaleConstraint.*",       "rigging/constraints/transform/copy_scale.html"),
    ("bpy.types.CopyTransformsConstraint.*",  "rigging/constraints/transform/copy_transforms.html"),
    ("bpy.types.LimitDistanceConstraint.*",   "rigging/constraints/transform/limit_distance.html"),
    ("bpy.types.LimitLocationConstraint.*",   "rigging/constraints/transform/limit_location.html"),
    ("bpy.types.LimitRotationConstraint.*",   "rigging/constraints/transform/limit_rotation.html"),
    ("bpy.types.LimitScaleConstraint.*",      "rigging/constraints/transform/limit_scale.html"),
    ("bpy.types.MaintainVolumeConstraint.*",  "rigging/constraints/transform/maintain_volume.html"),
    ("bpy.types.TransformConstraint.*",       "rigging/constraints/transform/transformation.html"),
    # --- Tracking Constraints ---
    ("bpy.types.ClampToConstraint.*",         "rigging/constraints/tracking/clamp_to.html"),
    ("bpy.types.DampedTrackConstraint.*",     "rigging/constraints/tracking/damped_track.html"),
    ("bpy.types.KinematicConstraint.*",       "rigging/constraints/tracking/ik_solver.html"),
    ("bpy.types.LockedTrackConstraint.*",     "rigging/constraints/tracking/locked_track.html"),
    ("bpy.types.SplineIKConstraint.*",        "rigging/constraints/tracking/spline_ik.html"),
    ("bpy.types.StretchToConstraint.*",       "rigging/constraints/tracking/stretch_to.html"),
    ("bpy.types.TrackToConstraint.*",         "rigging/constraints/tracking/track_to.html"),
    # --- Relationship Constraints ---
    ("bpy.types.ActionConstraint.*",          "rigging/constraints/relationship/action.html"),
    ("bpy.types.ChildOfConstraint.*",         "rigging/constraints/relationship/action.html"),
    ("bpy.types.FloorConstraint.*",           "rigging/constraints/relationship/child_of.html"),
    ("bpy.types.FollowPathConstraint.*",      "rigging/constraints/relationship/follow_path.html"),
    ("bpy.types.PivotConstraint.*",           "rigging/constraints/relationship/pivot.html"),
    ("bpy.types.RigidBodyJointConstraint.*",  "rigging/constraints/relationship/rigid_body_joint.html"),
    ("bpy.types.ShrinkwrapConstraint.*",      "rigging/constraints/relationship/shrinkwrap.html"),

    # *** Render Settings ***
    ("bpy.types.ImageFormatSettings.*",        "data_system/files/image_formats.html"),
    ("bpy.types.RenderSettings.filepath",      "render/output/output.html#output-panel"),
    ("bpy.types.RenderSettings.display_mode",  "render/output/display.html#displaying-renders"),
    ("bpy.types.RenderSettings.*",             "render"),  # catchall, todo - refine

    # *** FreeStyle ***
    ("bpy.types.LineStyleAlphaModifier_AlongStroke.*",            "render/freestyle/parameter_editor/line_style/alpha.html#along-stroke"),
    ("bpy.types.LineStyleAlphaModifier_CreaseAngle.*",            "render/freestyle/parameter_editor/line_style/alpha.html#crease-angle"),
    ("bpy.types.LineStyleAlphaModifier_Curvature_3D.*",           "render/freestyle/parameter_editor/line_style/alpha.html#d-curvature"),
    ("bpy.types.LineStyleAlphaModifier_DistanceFromCamera.*",     "render/freestyle/parameter_editor/line_style/alpha.html#distance-from-camera"),
    ("bpy.types.LineStyleAlphaModifier_DistanceFromObject.*",     "render/freestyle/parameter_editor/line_style/alpha.html#distance-from-object"),
    ("bpy.types.LineStyleAlphaModifier_Material.*",               "render/freestyle/parameter_editor/line_style/alpha.html#material"),
    ("bpy.types.LineStyleAlphaModifier_Noise.*",                  "render/freestyle/parameter_editor/line_style/alpha.html#noise"),
    ("bpy.types.LineStyleAlphaModifier_Tangent.*",                "render/freestyle/parameter_editor/line_style/alpha.html#tangent"),
    ("bpy.types.LineStyleColorModifier_AlongStroke.*",            "render/freestyle/parameter_editor/line_style/color.html#along-stroke"),
    ("bpy.types.LineStyleColorModifier_CreaseAngle.*",            "render/freestyle/parameter_editor/line_style/color.html#crease-angle"),
    ("bpy.types.LineStyleColorModifier_Curvature_3D.*",           "render/freestyle/parameter_editor/line_style/color.html#d-curvature"),
    ("bpy.types.LineStyleColorModifier_DistanceFromCamera.*",     "render/freestyle/parameter_editor/line_style/color.html#distance-from-camera"),
    ("bpy.types.LineStyleColorModifier_DistanceFromObject.*",     "render/freestyle/parameter_editor/line_style/color.html#distance-from-object"),
    ("bpy.types.LineStyleColorModifier_Material.*",               "render/freestyle/parameter_editor/line_style/color.html#material"),
    ("bpy.types.LineStyleColorModifier_Noise.*",                  "render/freestyle/parameter_editor/line_style/color.html#noise"),
    ("bpy.types.LineStyleColorModifier_Tangent.*",                "render/freestyle/parameter_editor/line_style/color.html#tangent"),
    ("bpy.types.LineStyleGeometryModifier_2DOffset.*",            "render/freestyle/parameter_editor/line_style/geometry.html#d-offset"),
    ("bpy.types.LineStyleGeometryModifier_2DTransform.*",         "render/freestyle/parameter_editor/line_style/geometry.html#d-transform"),
    ("bpy.types.LineStyleGeometryModifier_BackboneStretcher.*",   "render/freestyle/parameter_editor/line_style/geometry.html#backbone-stretcher"),
    ("bpy.types.LineStyleGeometryModifier_BezierCurve.*",         "render/freestyle/parameter_editor/line_style/geometry.html#bezier-curve"),
    ("bpy.types.LineStyleGeometryModifier_Blueprint.*",           "render/freestyle/parameter_editor/line_style/geometry.html#blueprint"),
    ("bpy.types.LineStyleGeometryModifier_GuidingLines.*",        "render/freestyle/parameter_editor/line_style/geometry.html#guiding-lines"),
    ("bpy.types.LineStyleGeometryModifier_PerlinNoise1D.*",       "render/freestyle/parameter_editor/line_style/geometry.html#perlin-noise-1d"),
    ("bpy.types.LineStyleGeometryModifier_PerlinNoise2D.*",       "render/freestyle/parameter_editor/line_style/geometry.html#perlin-noise-2d"),
    ("bpy.types.LineStyleGeometryModifier_Polygonalization.*",    "render/freestyle/parameter_editor/line_style/geometry.html#polygonization"),
    ("bpy.types.LineStyleGeometryModifier_Sampling.*",            "render/freestyle/parameter_editor/line_style/geometry.html#sampling"),
    ("bpy.types.LineStyleGeometryModifier_Simplification.*",      "render/freestyle/parameter_editor/line_style/geometry.html#simplification"),
    ("bpy.types.LineStyleGeometryModifier_SinusDisplacement.*",   "render/freestyle/parameter_editor/line_style/geometry.html#sinus-displacement"),
    ("bpy.types.LineStyleGeometryModifier_SpatialNoise.*",        "render/freestyle/parameter_editor/line_style/geometry.html#spatial-noise"),
    ("bpy.types.LineStyleGeometryModifier_TipRemover.*",          "render/freestyle/parameter_editor/line_style/geometry.html#tip-remover"),
#   ("bpy.types.LineStyleTextureSlot.*",                          ""), Todo
    ("bpy.types.LineStyleThicknessModifier_AlongStroke.*",        "render/freestyle/parameter_editor/line_style/thickness.html#along-stroke"),
    ("bpy.types.LineStyleThicknessModifier_Calligraphy.*",        "render/freestyle/parameter_editor/line_style/thickness.html#calligraphy"),
    ("bpy.types.LineStyleThicknessModifier_CreaseAngle.*",        "render/freestyle/parameter_editor/line_style/thickness.html#crease-angle"),
    ("bpy.types.LineStyleThicknessModifier_Curvature_3D.*",       "render/freestyle/parameter_editor/line_style/thickness.html#d-curvature"),
    ("bpy.types.LineStyleThicknessModifier_DistanceFromCamera.*", "render/freestyle/parameter_editor/line_style/thickness.html#distance-from-camera"),
    ("bpy.types.LineStyleThicknessModifier_DistanceFromObject.*", "render/freestyle/parameter_editor/line_style/thickness.html#distance-from-object"),
    ("bpy.types.LineStyleThicknessModifier_Material.*",           "render/freestyle/parameter_editor/line_style/thickness.html#material"),
    ("bpy.types.LineStyleThicknessModifier_Noise.*",              "render/freestyle/parameter_editor/line_style/thickness.html#noise"),
    ("bpy.types.LineStyleThicknessModifier_Tangent.*",            "render/freestyle/parameter_editor/line_style/thickness.html#tangent"),
    ("bpy.types.FreestyleLineSet.*",                              "render/freestyle/parameter_editor/line_set.html"),
    ("bpy.types.FreestyleLineStyle.*",                            "render/freestyle/parameter_editor/line_style.html"),
#   ("bpy.types.FreestyleModuleSettings.*",                       ""), Todo
#   ("bpy.types.FreestyleSettings.*",                             ""), Todo
    ("bpy.types.Linesets.*",                                      "render/freestyle/parameter_editor/line_set.html"),

    # *** ID Subclasses ***
    ("bpy.types.Action.*",        "animation/actions.html"),
    #("bpy.types.Brush.*", ""),   # TODO - manual has no place for this! XXX
    ("bpy.types.Curve.*",         "modeling/curves"),
    ("bpy.types.GreasePencil.*",  "interface/grease_pencil"),
    ("bpy.types.Group.*",         "editors/3dview/object/relationships/groups.html"),
    ("bpy.types.Image.*",         "editors/uv_image/texturing/textures/image.html"),
    ("bpy.types.ShapeKey.*",      "animation/shape_keys.html"), # not an id but include because of key
    ("bpy.types.Key.*",           "animation/shape_keys.html"),
    #("bpy.types.Lattice.*", ""),  # TODO - manual has no place for this! XXX
    ("bpy.types.Library.*",       "data_system/linked_libraries.html"),
    ("bpy.types.Mask.*",          "editors/movie_clip_editor/masking.html"),

    # *** Materials (blender internal) ***
    ("bpy.types.Material.diffuse*",  "render/blender_render/materials/properties/diffuse_shaders.html"),
    ("bpy.types.Material.specular*", "render/blender_render/materials/properties/specular_shaders.html"),
    ("bpy.types.Material.ambient*",  "render/blender_render/materials/properties/shading.html"),
    ("bpy.types.Material.preview_render_type", "render/blender_render/materials/properties/preview.html"),
    ("bpy.types.Material.*",                   "render/blender_render"),  # catchall, until the section is filled in
    # ("bpy.types.MaterialSlot.link", "render/blender_render/materials/options.html#material-naming_and_linking"),  # TODO, T42839
    ("bpy.types.MaterialVolume.*",    "render/blender_render/materials/special_effects/volume.html"),
    ("bpy.types.MaterialHalo.*",      "render/blender_render/materials/special_effects/halo.html"),
    ("bpy.types.MaterialStrand.*",    "render/blender_render/materials/properties/strands.html"),
    ("bpy.types.MaterialSubsurfaceScattering.*",  "render/blender_render/materials/properties/subsurface_scattering.html"),
    ("bpy.types.MaterialRaytraceMirror.*",        "render/blender_render/materials/properties/mirror.html"),
    ("bpy.types.MaterialRaytraceTransparency.*",  "render/blender_render/materials/properties/transparency.html#raytraced-transparency"),
    # ... todo, many more options
    ("bpy.types.MovieClip.*",                  "editors/movie_clip_editor"),
    ("bpy.types.MovieTrackingCamera.*",        "editors/movie_clip_editor/tracking/clip.html#tools-available-in-reconstruction-mode"),
    ("bpy.types.MovieTrackingStabilization.*", "editors/movie_clip_editor/tracking/introduction.html#tools-for-scene-orientation-and-stabilization"),
    ("bpy.types.MovieTrackingTrack*",          "editors/movie_clip_editor/index.html#tools-available-in-tracking-mode"),
    ("bpy.types.MovieTracking*",               "editors/movie_clip_editor"),
    ("bpy.types.SpaceClipEditor.*",            "editors/movie_clip_editor/introduction.html"),
    ("bpy.types.ColorManaged*",                "render/post_process/cm_and_exposure.html"),
    #("bpy.types.NodeTree.*", ""),             # dont document
    ("bpy.types.Object.*",                     "editors/3dview/object"),  # catchall, todo - refine
    ("bpy.types.ParticleSettings.*",           "physics/particles"),
    ("bpy.types.Scene.*",                      "data_system/scenes.html"),
    ("bpy.types.Screen.*",                     "interface/screens.html"),
    ("bpy.types.Sound.*",                      "editors/3dview/object/types/speaker.html"),
    ("bpy.types.Speaker.*",                    "editors/3dview/object/types/speaker.html"),
    ("bpy.types.Text.*",                       "editors/text_editor.html"),
    ("bpy.types.Texture.*",                    "render/blender_render/textures"),
    ("bpy.types.VectorFont.*",                 "modeling/texts"),
    ("bpy.types.WindowManager.*",              "interface/window_system"),
    ("bpy.types.World.*",                      "render/blender_render/world"),
    ("bpy.types.WorldLighting.*ao*",           "render/blender_render/lighting/ambient_occlusion.html"),
    ("bpy.types.WorldLighting.*ambient*",      "render/blender_render/lighting/ambient_occlusion.html"),
    ("bpy.types.WorldLighting.*environment*",  "render/blender_render/lighting/ambient_light.html"),
    # only other WorldLighting props are in Gather panel
    ("bpy.types.WorldLighting.*",              "render/blender_render/lighting/ambient_occlusion.html#gather"),

    # *** Cycles ***
    ("bpy.types.CyclesRenderSettings.*",     "render/cycles/settings/integrator.html"),
    ("bpy.types.CyclesVisibilitySettings.*", "render/cycles/settings/light_paths.html#ray-visibility"),
    ("bpy.types.CyclesWorldSettings.*",      "render/cycles/world.html"),
    ("bpy.types.SceneRenderLayer.*pass*",    "render/blender_render/passes.html"),
    ("bpy.types.SceneRenderLayer.*",         "render/post_process/layers.html"),
    ("bpy.types.Cycles*",                    "render/cycles"),

    # Currently all manual links on all sockets and values (such as Fac, Roughness, Color...) are NodeSocket* type.
    # It'd be much better if the name of the socket could be used for the manual reference
    ("bpy.types.NodeSocket*", "editors/node_editor/node_parts.html"),  # no generic socket type page exists, but composite types are the same

    # *** Cycles Material Nodes ***
    # Outputs
    ("bpy.types.ShaderNodeOutputLamp.*",           "render/cycles/lamps.html"),
    ("bpy.types.ShaderNodeOutputMaterial.*",       "render/cycles/materials"),
    ("bpy.types.ShaderNodeOutputWorld.*",          "render/cycles/world.html"),
    # Shaders
    ("bpy.types.ShaderNodeAddShader.*",            "render/cycles/nodes/shaders.html#mix-and-add"),
    ("bpy.types.ShaderNodeAmbientOcclusion.*",     "render/cycles/nodes/shaders.html#ambient-occlusion"),
    ("bpy.types.ShaderNodeBackground.*",           "render/cycles/nodes/shaders.html#background"),
    ("bpy.types.ShaderNodeBsdfAnisotropic.*",      "render/cycles/nodes/shaders.html#anisotropic"),
    ("bpy.types.ShaderNodeBsdfDiffuse.*",          "render/cycles/nodes/shaders.html#diffuse"),
    ("bpy.types.ShaderNodeBsdfGlass.*",            "render/cycles/nodes/shaders.html#glass"),
    ("bpy.types.ShaderNodeBsdfGlossy.*",           "render/cycles/nodes/shaders.html#glossy"),
    ("bpy.types.ShaderNodeBsdfHair.*",             "render/cycles/nodes/shaders.html#hair"),
    ("bpy.types.ShaderNodeBsdfRefraction.*",       "render/cycles/nodes/shaders.html#refraction"),
    ("bpy.types.ShaderNodeBsdfToon.*",             "render/cycles/nodes/shaders.html#toon"),
    ("bpy.types.ShaderNodeBsdfTranslucent.*",      "render/cycles/nodes/shaders.html#translucent"),
    ("bpy.types.ShaderNodeBsdfTransparent.*",      "render/cycles/nodes/shaders.html#transparent"),
    ("bpy.types.ShaderNodeBsdfVelvet.*",           "render/cycles/nodes/shaders.html#velvet"),
    ("bpy.types.ShaderNodeEmission.*",             "render/cycles/nodes/shaders.html#emission"),
    ("bpy.types.ShaderNodeHoldout.*",              "render/cycles/nodes/shaders.html#holdout"),
    ("bpy.types.ShaderNodeMixShader.*",            "render/cycles/nodes/shaders.html#mix-and-add"),
    ("bpy.types.ShaderNodeSubsurfaceScattering.*", "render/cycles/nodes/shaders.html#subsurface-scattering"),
    ("bpy.types.ShaderNodeVolumeAbsorption.*",     "render/cycles/nodes/shaders.html#volume-absorption"),
    ("bpy.types.ShaderNodeVolumeScatter.*",        "render/cycles/nodes/shaders.html#volume-scatter"),
    # Textures
    ("bpy.types.ShaderNodeTexBrick.*",        "render/cycles/nodes/textures.html#brick-texture"),
    ("bpy.types.ShaderNodeTexChecker.*",      "render/cycles/nodes/textures.html#checker-texture"),
    ("bpy.types.ShaderNodeTexEnvironment.*",  "render/cycles/nodes/textures.html#environment-texture"),
    ("bpy.types.ShaderNodeTexGradient.*",     "render/cycles/nodes/textures.html#gradient-texture"),
    ("bpy.types.ShaderNodeTexImage.*",        "render/cycles/nodes/textures.html#image-texture"),
    ("bpy.types.ShaderNodeTexMagic.*",        "render/cycles/nodes/textures.html#magic-texture"),
    ("bpy.types.ShaderNodeTexMusgrave.*",     "render/cycles/nodes/textures.html#musgrave-texture"),
    ("bpy.types.ShaderNodeTexNoise.*",        "render/cycles/nodes/textures.html#noise-texture"),
    ("bpy.types.ShaderNodeTexSky.*",          "render/cycles/nodes/textures.html#sky-texture"),
    ("bpy.types.ShaderNodeTexVoronoi.*",      "render/cycles/nodes/textures.html#voronoi-texture"),
    ("bpy.types.ShaderNodeTexWave.*",         "render/cycles/nodes/textures.html#wave-texture"),
    # Other
    ("bpy.types.ShaderNodeAttribute.*",       "render/cycles/nodes/more.html#attribute"),
    ("bpy.types.ShaderNodeBlackbody.*",       "render/cycles/nodes/more.html#blackbody"),
    # ("bpy.types.ShaderNodeBrightContrast.*", ""),
    ("bpy.types.ShaderNodeBump.*",            "render/cycles/nodes/more.html#bump"),
    ("bpy.types.ShaderNodeCameraData.*",      "render/cycles/nodes/input.html#camera-data"),
    # ("bpy.types.ShaderNodeCombineHSV.*",    ""),
    # ("bpy.types.ShaderNodeCombineRGB.*",    ""),
    ("bpy.types.ShaderNodeFresnel.*",         "render/cycles/nodes/more.html#fresnel"),
    # ("bpy.types.ShaderNodeGamma.*", ""),
    ("bpy.types.ShaderNodeGeometry.*",        "render/cycles/nodes/more.html#geometry"),
    ("bpy.types.ShaderNodeHairInfo.*",        "render/cycles/nodes/input.html#hair-info"),
    # ("bpy.types.ShaderNodeHueSaturation.*", ""),
    # ("bpy.types.ShaderNodeInvert.*",        ""),
    ("bpy.types.ShaderNodeLayerWeight.*",     "render/cycles/nodes/more.html#layer-weight"),
    ("bpy.types.ShaderNodeLightFalloff.*",    "render/cycles/nodes/more.html#light-falloff"),
    ("bpy.types.ShaderNodeLightPath.*",       "render/cycles/nodes/more.html#light-path"),
    ("bpy.types.ShaderNodeMapping.*",         "render/cycles/nodes/more.html#mapping"),
    # # ("bpy.types.ShaderNodeMath.*",        ""),
    # ("bpy.types.ShaderNodeMixRGB.*",        ""),
    ("bpy.types.ShaderNodeNormalMap.*",       "render/cycles/nodes/more.html#normal-map"),
    ("bpy.types.ShaderNodeObjectInfo.*",      "render/cycles/nodes/more.html#object-info"),
    ("bpy.types.ShaderNodeParticleInfo.*",    "render/cycles/nodes/more.html#particle-info"),
    ("bpy.types.ShaderNodeRGB.*",             "render/cycles/nodes/more.html#rgb"),
    # ("bpy.types.ShaderNodeRGBCurve.*",      ""),
    # ("bpy.types.ShaderNodeRGBToBW.*",       ""),
    # ("bpy.types.ShaderNodeSeparateHSV.*",   ""),
    # ("bpy.types.ShaderNodeSeparateRGB.*",   ""),
    ("bpy.types.ShaderNodeTangent.*",         "render/cycles/nodes/more.html#tangent"),
    ("bpy.types.ShaderNodeTexCoord.*",        "render/cycles/nodes/more.html#texture-coordinates"),
    ("bpy.types.ShaderNodeValue.*",           "render/cycles/nodes/more.html#value"),
    # ("bpy.types.ShaderNodeVectorCurve.*",   ""),
    ("bpy.types.ShaderNodeVectorMath.*",      "render/cycles/nodes/more.html"),  # TODO doc
    ("bpy.types.ShaderNodeVectorTransform.*", "render/cycles/nodes/more.html#vector-transform"),
    ("bpy.types.ShaderNodeWavelength.*",      "render/cycles/nodes/more.html#wavelength"),
    ("bpy.types.ShaderNodeWireframe.*",       "render/cycles/nodes/more.html#wireframe"),
    ("bpy.types.ShaderNodeGroup.*",           "editors/node_editor/node_groups.html"),
    ("bpy.types.ShaderNode*",                 "render/cycles/nodes"),
    ("bpy.types.ShaderNodeScript.*",          "render/cycles/osl.html"),

    # *** Compositing Nodes ***
    # Input
    ("bpy.types.CompositorNodeBokehImage.*",  "compositing/types/input/bokeh_image.html"),
    ("bpy.types.CompositorNodeImage.*",       "compositing/types/input/image.html"),
    ("bpy.types.CompositorNodeMask.*",        "compositing/types/input/mask.html"),
    ("bpy.types.CompositorNodeMovieClip.*",   "compositing/types/input/movie_clip.html"),
    ("bpy.types.CompositorNodeRGB.*",         "compositing/types/input/rgb.html"),
    ("bpy.types.CompositorNodeRLayers.*",     "compositing/types/input/render_layers.html"),
    ("bpy.types.CompositorNodeTexture.*",     "compositing/types/input/texture.html"),
    ("bpy.types.CompositorNodeTime.*",        "compositing/types/input/time.html"),
    ("bpy.types.CompositorNodeTrackPos.*",    "compositing/types/input/track_position.html"),
    ("bpy.types.CompositorNodeValue.*",       "compositing/types/input/value.html"),
    # Output
    ("bpy.types.CompositorNodeComposite.*",   "compositing/types/output/composite.html"),
    ("bpy.types.CompositorNodeLevels.*",      "compositing/types/output/levels.html"),
    ("bpy.types.CompositorNodeOutputFile*",   "compositing/types/output/file.html"),
    ("bpy.types.CompositorNodeSplitViewer.*", "compositing/types/output/split_viewer.html"),
    ("bpy.types.CompositorNodeViewer.*",      "compositing/types/output/viewer.html"),
    # Color
    ("bpy.types.CompositorNodeAlphaOver.*",       "compositing/types/color/alpha_over.html"),
    ("bpy.types.CompositorNodeBrightContrast.*",  "compositing/types/color/bright_contrast.html"),
    ("bpy.types.CompositorNodeColorBalance.*",    "compositing/types/color/bright_contrast.html"),
    ("bpy.types.CompositorNodeColorCorrection.*", "compositing/types/color/color_correction.html"),
    ("bpy.types.CompositorNodeCurveRGB.*",        "compositing/types/color/rgb_curves.html"),
    ("bpy.types.CompositorNodeGamma.*",           "compositing/types/color/gamma.html"),
    ("bpy.types.CompositorNodeHueCorrect.*",      "compositing/types/color/hue_correct.html"),
    ("bpy.types.CompositorNodeHueSat.*",          "compositing/types/color/hue_saturation.html"),
    ("bpy.types.CompositorNodeInvert.*",          "compositing/types/color/invert.html"),
    ("bpy.types.CompositorNodeMixRGB.*",          "compositing/types/color/mix.html"),
    ("bpy.types.CompositorNodeTonemap.*",         "compositing/types/color/tone_map.html"),
    ("bpy.types.CompositorNodeZcombine.*",        "compositing/types/color/z_combine.html"),
    # Converter
    ("bpy.types.CompositorNodeSep*",         "compositing/types/converter/combine_separate.html"),
    ("bpy.types.CompositorNodeComb*",        "compositing/types/converter/combine_separate.html"),
    ("bpy.types.CompositorNodeIDMask.*",     "compositing/types/converter/id_mask.html"),
    ("bpy.types.CompositorNodeMath.*",       "compositing/types/converter/math.html"),
    ("bpy.types.CompositorNodePremulKey.*",  "compositing/types/converter/alpha_convert.html"),
    ("bpy.types.CompositorNodeRGBToBW.*",    "compositing/types/converter/rgb_to_bw.html"),
    ("bpy.types.CompositorNodeSetAlpha.*",   "compositing/types/converter/set_alpha.html"),
    # Filter
    ("bpy.types.CompositorNodeBilateralblur.*", "compositing/types/filter/bilateral_blur.html"),
    ("bpy.types.CompositorNodeBlur.*",          "compositing/types/filter/blur_node.html"),
    ("bpy.types.CompositorNodeBokehBlur.*",     "compositing/types/filter/bokeh_blur.html"),
    ("bpy.types.CompositorNodeDBlur.*",         "compositing/types/filter/directional_blur.html"),
    ("bpy.types.CompositorNodeDefocus.*",       "compositing/types/filter/defocus.html"),
    ("bpy.types.CompositorNodeDespeckle.*",     "compositing/types/filter/despeckle.html"),
    ("bpy.types.CompositorNodeDilateErode.*",   "compositing/types/filter/dilate_erode.html"),
    ("bpy.types.CompositorNodeFilter.*",        "compositing/types/filter/filter_node.html"),
    ("bpy.types.CompositorNodeGlare.*",         "compositing/types/filter/glare.html"),
    ("bpy.types.CompositorNodeInpaint.*",       "compositing/types/filter/inpaint.html"),
    ("bpy.types.CompositorNodePixelate.*",      "compositing/types/filter/pixelate.html"),
    ("bpy.types.CompositorNodeSunBeams.*",      "compositing/types/filter/sun_beams.html"),
    ("bpy.types.CompositorNodeVecBlur.*",       "compositing/types/filter/vector_blur.html"),
    # Vector
    ("bpy.types.CompositorNodeCurveVec.*",   "compositing/types/vector/vector_curves.html"),
    ("bpy.types.CompositorNodeMapRange.*",   "compositing/types/vector/map_range.html"),
    ("bpy.types.CompositorNodeMapValue.*",   "compositing/types/vector/map_value.html"),
    ("bpy.types.CompositorNodeNormal.*",     "compositing/types/vector/normal.html"),
    ("bpy.types.CompositorNodeNormalize.*",  "compositing/types/vector/normalize.html"),
    # Matte
    ("bpy.types.CompositorNodeBoxMask.*",        "compositing/types/matte/box_mask.html"),
    ("bpy.types.CompositorNodeChannelMatte.*",   "compositing/types/matte/channel_key.html"),
    ("bpy.types.CompositorNodeChromaMatte.*",    "compositing/types/matte/chroma_key.html"),
    ("bpy.types.CompositorNodeColorMatte.*",     "compositing/types/matte/color_key.html"),
    ("bpy.types.CompositorNodeColorSpill.*",     "compositing/types/matte/color_spill_key.html"),
    ("bpy.types.CompositorNodeDiffMatte.*",      "compositing/types/matte/difference_key.html"),
    ("bpy.types.CompositorNodeDistanceMatte.*",  "compositing/types/matte/difference_key.html"),
    ("bpy.types.CompositorNodeDoubleEdgeMask.*", "compositing/types/matte/double_edge_mask.html"),
    ("bpy.types.CompositorNodeEllipseMask.*",    "compositing/types/matte/ellipse_mask.html"),
    ("bpy.types.CompositorNodeKeying.*",         "compositing/types/matte/keying.html"),
    ("bpy.types.CompositorNodeKeyingScreen.*",   "compositing/types/matte/keying_screen.html"),
    ("bpy.types.CompositorNodeLumaMatte.*",      "compositing/types/matte/luminance_key.html"),
    # Distort
    ("bpy.types.CompositorNodeCrop.*",             "compositing/types/distort/crop.html"),
    ("bpy.types.CompositorNodeDisplace.*",         "compositing/types/distort/displace.html"),
    ("bpy.types.CompositorNodeFlip.*",             "compositing/types/distort/flip.html"),
    ("bpy.types.CompositorNodeLensdist.*",         "compositing/types/distort/lens.html"),
    ("bpy.types.CompositorNodeMapUV.*",            "compositing/types/distort/map_uv.html"),
    ("bpy.types.CompositorNodeMovieDistortion.*",  "compositing/types/distort/movie_distortion.html"),
    ("bpy.types.CompositorNodePlaneTrackDeform.*", "compositing/types/distort/plane_track_deform.html"),
    ("bpy.types.CompositorNodeRotate.*",           "compositing/types/distort/rotate.html"),
    ("bpy.types.CompositorNodeScale.*",            "compositing/types/distort/scale.html"),
    ("bpy.types.CompositorNodeStabilize.*",        "compositing/types/distort/stabilize_2d.html"),
    ("bpy.types.CompositorNodeTransform.*",        "compositing/types/distort/transform.html"),
    ("bpy.types.CompositorNodeTranslate.*",        "compositing/types/distort/translate.html"),
    # Other
    ("bpy.types.CompositorNodeGroup.*", "editors/node_editor/node_groups.html"),
    ("bpy.types.CompositorNode*",       "compositing/types"),  # catch anything else

    ("bpy.types.ColorRamp*", "interface/extended_controls.html#color-ramp-widget"),

    # *** Sequencer ***
    ("bpy.types.AddSequence.*",            "editors/sequencer/strips/effects/add.html"),
    ("bpy.types.AdjustmentSequence.*",     "editors/sequencer/strips/effects/adjustment.html"),
    ("bpy.types.AlphaOverSequence.",       "editors/sequencer/strips/effects/alpha_over_under_overdrop.html"),
    ("bpy.types.AlphaUnderSequence.*",     "editors/sequencer/strips/effects/alpha_over_under_overdrop.html"),
    ("bpy.types.ColorSequence.*",          "editors/sequencer/strips/effects/color.html"),
    ("bpy.types.CrossSequence.*",          "editors/sequencer/strips/effects/cross.html"),
    ("bpy.types.EffectSequence.*",         "editors/sequencer/strips/effects"),
    ("bpy.types.GammaCrossSequence.*",     "editors/sequencer/strips/effects/cross.html"),
    ("bpy.types.GaussianBlurSequence.*",   "editors/sequencer/strips/effects/blur.html"),
    ("bpy.types.GlowSequence.*",           "editors/sequencer/strips/effects/glow.html"),
    ("bpy.types.ImageSequence.*",          "editors/sequencer/strips/image_movie.html"),
    ("bpy.types.MaskSequence.*",           "editors/sequencer/strips/mask.html"),
    ("bpy.types.MetaSequence.*",           "editors/sequencer/strips/meta.html"),
    ("bpy.types.MovieSequence.*",          "editors/sequencer/strips/image_movie.html"),
    ("bpy.types.MulticamSequence.*",       "editors/sequencer/strips/effects/multicam.html"),
    ("bpy.types.MultiplySequence.*",       "editors/sequencer/strips/effects/multiply.html"),
    ("bpy.types.OverDropSequence.*",       "editors/sequencer/strips/effects/alpha_over_under_overdrop.html"),
    ("bpy.types.SceneSequence.*",          "editors/sequencer/strips/scene.html"),
    ("bpy.types.SoundSequence.*",          "editors/sequencer/strips/audio.html"),
    ("bpy.types.SpeedControlSequence.*",   "editors/sequencer/strips/effects/speed_control.html"),
    ("bpy.types.SubtractSequence.*",       "editors/sequencer/strips/effects/subtract.html"),
    ("bpy.types.TextSequence.*",           "editors/sequencer/strips/effects/text.html"),
    ("bpy.types.TransformSequence.*",      "editors/sequencer/strips/effects/transform.html"),
    ("bpy.types.WipeSequence.*",           "editors/sequencer/strips/effects/wipe.html"),
    # Modifiers
    ("bpy.types.BrightContrastModifier.*", "editors/sequencer/properties/modifiers.html"),
    ("bpy.types.ColorBalanceModifier.*",   "editors/sequencer/properties/modifiers.html"),
    ("bpy.types.CurvesModifier.*",         "editors/sequencer/properties/modifiers.html"),
    ("bpy.types.HueCorrectModifier.*",     "editors/sequencer/properties/modifiers.html"),

    # ("bpy.types.SequenceColorBalanceData.*", ""),
    # ("py.types.SequenceCrop.*",              ""),
    # ("bpy.types.SequenceEditor.*",           ""),
    # ("bpy.types.SequenceElement.*",          ""),
    ("bpy.types.SequenceModifier.*",           "editors/sequencer/properties/modifiers.html"),
    ("bpy.types.SequenceProxy.*",              "editors/sequencer/properties/proxy_timecode.html"),
    # ("bpy.types.SequenceTransform.*",        ""),

    ("bpy.types.Sequence.*",                   "editors/sequencer"), # catch anything else

    # *** ID Subclasses (cont.) Object Data ***
    ("bpy.types.Mesh.*",       "modeling/meshes"),    # catchall, todo - refine
    ("bpy.types.MetaBall.*",   "modeling/metas"),     # catchall, todo - refine
    ("bpy.types.TextCurve.*",  "modeling/texts"),     # catchall, todo - refine
    ("bpy.types.Armature.*",   "rigging/armatures"),  # catchall, todo - refine
    ("bpy.types.Camera.*",     "editors/3dview/object/types/camera/index.html"),      # catchall, todo - refine

    ("bpy.types.PointLamp.*",  "render/blender_render/lighting/lamps/point"),  # catchall, todo - refine
    ("bpy.types.AreaLamp.*",   "render/blender_render/lighting/lamps/area"),  # catchall, todo - refine
    ("bpy.types.SpotLamp.*",   "render/blender_render/lighting/lamps/spot"),  # catchall, todo - refine
    ("bpy.types.SunLamp.*",    "render/blender_render/lighting/lamps/sun"),   # catchall, todo - refine
    ("bpy.types.HemiLamp.*",   "render/blender_render/lighting/lamps/hemi.html"),  # catchall, todo - refine
    ("bpy.types.Lamp.*",       "render/blender_render/lighting"),             # catchall, todo - refine

    # --- Animation ---
    ("bpy.types.Keyframe.*",   "animation/actions.html"),
    ("bpy.types.FCurve.*",     "editors/graph_editor/fcurves.html"),

    # --- Rigging ---
    ("bpy.types.Bone.*",       "rigging/armatures/bones.html"),
    ("bpy.types.EditBone.*",   "rigging/armatures/bones.html"),
    ("bpy.types.PoseBone.*",   "rigging/posing"),

    # --- World ---
    ("bpy.types.World.*",      "render/blender_render/world"),

    ("bpy.types.Texture.*",    "render/blender_render/textures"),

    # *** Spaces ***
    ("bpy.types.SpaceConsole.*",            "editors/python_console.html"),
    ("bpy.types.SpaceDopeSheetEditor.*",    "editors/dope_sheet"),
    ("bpy.types.SpaceFileBrowser.*",        "editors/file_browser/introduction.html"),
    ("bpy.types.SpaceGraphEditor.*",        "editors/graph_editor"),
    ("bpy.types.SpaceImageEditor.*",        "editors/uv_image"),
    ("bpy.types.SpaceInfo.*",               "editors/info"),
    ("bpy.types.SpaceLogicEditor.*",        "editors/logic_editor.html"),
    ("bpy.types.SpaceNLA.*",                "editors/nla.html"),
    ("bpy.types.SpaceNodeEditor.*",         "editors/node_editor"),
    ("bpy.types.SpaceOutliner.*",           "editors/outliner.html"),
    ("bpy.types.SpaceProperties.*",         "editors/properties"),
    ("bpy.types.SpaceSequenceEditor.*",     "editors/sequencer"),
    ("bpy.types.SpaceTextEditor.*",         "editors/text_editor.html"),
    ("bpy.types.SpaceTimeline.*",           "editors/timeline.html"),
    ("bpy.types.SpaceUVEditor.*",           "editors/uv_image"),
    ("bpy.types.SpaceUserPreferences.*",    "preferences"),
    ("bpy.types.SpaceView3D.*",             "editors/3dview"),
    ("bpy.types.Space.*",                   "editors"), # Catchall

    # === Operators ===
    # Catch all only for now!
    # *** Window/Screen ***

    ("bpy.ops.action.*",      "animation/actions.html"),
    ("bpy.ops.anim.*",        "animation"),
    ("bpy.ops.armature.*",    "rigging/armatures/"),
    ("bpy.ops.boid.*",        "physics/particles/physics/boids.html"),
    # ("bpy.ops.brush.*",     ""),  # TODO
    ("bpy.ops.buttons.*",     "interface/buttons_and_controls.html"),
    ("bpy.ops.camera.*",      "editors/3dview/object/types/camera/index.html"),
    ("bpy.ops.clip.*",        "editors/movie_clip_editor/index.html#movie-clip-editor"),
    ("bpy.ops.cloth.*",       "physics/cloth"),
    ("bpy.ops.console.*",     "editors/python_console.html"),
    ("bpy.ops.constraint.*",  "rigging/constraints"),
    ("bpy.ops.curve.*",       "modeling/curves"),
    ("bpy.ops.dpaint.*",      "physics/dynamic_paint"),
    # ("bpy.ops.ed.*",  ""),           # TODO, this is for internal use only?
    # ("bpy.ops.export_anim.*",  ""),  # TODO
    # ("bpy.ops.export_mesh.*",  ""),  # TODO
    # ("bpy.ops.export_scene.*",  ""), # TODO
    ("bpy.ops.file.*",  ""),
    ("bpy.ops.fluid.*",       "physics/fluid"),
    ("bpy.ops.font.*",        "modeling/texts"),
    ("bpy.ops.gpencil.*",     "interface/grease_pencil/index.html"),
    ("bpy.ops.graph.*",       "editors/graph_editor/fcurves.html"),
    ("bpy.ops.group.*",       "editors/3dview/object/relationships/groups.html"),
    ("bpy.ops.image.*",       "editors/uv_image/texturing/textures/image.html"),
    # ("bpy.ops.import_anim.*",  ""),   # TODO
    # ("bpy.ops.import_curve.*",  ""),  # TODO
    # ("bpy.ops.import_mesh.*",  ""),   # TODO
    # ("bpy.ops.import_scene.*",  ""),  # TODO
    # ("bpy.ops.info.*",  ""),          # TODO
    ("bpy.ops.lamp.*",             "render/blender_render/lighting"),  # --- todo ... all below ---
    # ("bpy.ops.lattice.*",  ""),  # TODO
    ("bpy.ops.logic.*",            "game_engine/logic"),
    ("bpy.ops.marker.*",           "animation/markers.html"),
    ("bpy.ops.mask.*",  "editors/movie_clip_editor/masking.html"),
    ("bpy.ops.material.new",    "render/blender_render/materials/assigning_a_material.html#creating-a-new-material"),
    ("bpy.ops.material.*",      "render/blender_render"),
    ("bpy.ops.mesh.vertices_smooth",      "modeling/meshes/editing/deforming/smooth.html"),
    ("bpy.ops.view3d.edit_mesh_extrude*", "modeling/meshes/editing/duplicating/extrude.html"),
    ("bpy.ops.mesh.subdivide",            "modeling/meshes/editing/subdividing/subdivide.html"),
    ("bpy.ops.mesh.loopcut_slide",        "modeling/meshes/editing/subdividing/loop_subdivide.html"),
    ("bpy.ops.mesh.bridge-edge-loops",    "modeling/meshes/editing/edges.html#bridge-edge-loops"),
    ("bpy.ops.mesh.duplicate_move",       "modeling/meshes/editing/duplicating/duplicate.html"),
    ("bpy.ops.mesh.spin",                 "modeling/meshes/editing/duplicating/spin.html"),
    ("bpy.ops.mesh.screw",                "modeling/meshes/editing/duplicating/screw.html"),
    ("bpy.ops.mesh.knife*",               "modeling/meshes/editing/subdividing/knife_subdivide.html"),
    ("bpy.ops.mesh.bisect",               "modeling/meshes/editing/subdividing/bisect.html"),
    ("bpy.ops.mball.*",                   "modeling/metas"),
    ("bpy.ops.mesh.*",                    "modeling/meshes"),
    ("bpy.ops.nla.*",                     "editors/nla.html"),
    # ("bpy.ops.node.*",  ""),            # TODO
    ("bpy.ops.object.*shape_key*",        "animation/shape_keys.html"),
    ("bpy.ops.object.join_shapes",        "animation/shape_keys.html"),
    ("bpy.ops.object.*",                  "editors/3dview/transform"),
    ("bpy.ops.outliner.*",                "editors/outliner.html"),
    # ("bpy.ops.paint.*",  ""),           # TODO
    ("bpy.ops.particle.*",                "physics/particles"),
    ("bpy.ops.pose.*",                    "rigging/posing"),
    ("bpy.ops.poselib.*",                 "rigging/posing/pose_library.html"),
    # ("bpy.ops.ptcache.*",  ""),         # TODO

    ("bpy.ops.render.play-rendered-anim", "render/output/display.html#animation-playback"),
    ("bpy.ops.render.*",  "render"),      # catchall

    ("bpy.ops.scene.*",                   "data_system/scenes.html"),
    ("bpy.ops.screen.*",                  "interface/window_system"),
    ("bpy.ops.script.*",                  "advanced/scripting"),
    ("bpy.ops.sculpt.*",                  "painting_sculpting/sculpting/index.html"),
    ("bpy.ops.sequencer.*",               "editors/sequencer"),
    # ("bpy.ops.sketch.*",  ""),          # TODO
    ("bpy.ops.sound.*",                   "editors/3dview/object/types/speaker.html"),
    ("bpy.ops.surface.*",                 "modeling/surfaces"),
    ("bpy.ops.text.*",                    "editors/text_editor.html"),
    ("bpy.ops.texture.*",                 "render/blender_render/textures"),
    ("bpy.ops.time.*",                    "editors/timeline.html"),
    ("bpy.ops.transform.edge_slide",      "modeling/meshes/editing/edges.html#edge-slide"),
    ("bpy.ops.transform.vert_slide",      "modeling/meshes/editing/vertices.html#vertex-slide"),
    ("bpy.ops.transform.shrink_fatten",   "modeling/meshes/editing/deforming/shrink-fatten.html"),
    ("bpy.ops.transform.push_pull",       "modeling/meshes/editing/deforming/push_pull.html"),
    ("bpy.ops.transform.*",               "editors/3dview/transform/transform_control"),
    ("bpy.ops.ui.*",                      "interface"),
    ("bpy.ops.uv.*",                      "editors/uv_image/index.html"),
    # ("bpy.ops.view2d.*",  ""),          # TODO
    ("bpy.ops.view3d.*",                  "editors/3dview/"),
    ("bpy.ops.wm.*",                      "interface/window_system"),
    ("bpy.ops.world.*",                   "render/blender_render/world"),

    # === Tool Settings ===
    ("bpy.types.MeshStatVis.*",           "modeling/meshes/mesh_analysis.html"),
)

# may have 'url_reference_mapping'... etc later
