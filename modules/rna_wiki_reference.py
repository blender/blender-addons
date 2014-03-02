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

url_manual_prefix = "http://wiki.blender.org/index.php/Doc:2.6/Manual/"

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

# - The first item is a wildcard - typical file system globbing
#   using python module 'fnmatch.fnmatch'
# - Expressions are evaluated top down (include catch-all expressions last).

url_manual_mapping = (

    # *** User Prefs ***
    ("bpy.types.UserPreferences.*",                "Preferences"),
    ("bpy.types.UserPreferencesView.*",            "Preferences/Interface"),
    ("bpy.types.UserPreferencesEdit.*",            "Preferences/Editing"),
    ("bpy.types.UserPreferencesInput.*",           "Preferences/Input"),
    ("bpy.ops.wm.addon_*",                         "Preferences/Addons"),
    ("bpy.types.Theme.*",                          "Preferences/Themes"),
    ("bpy.types.UserPreferencesFilePaths.*",       "Preferences/File"),
    ("bpy.types.UserPreferencesSystem.*",          "Preferences/System"),
    ("bpy.types.UserSolidLight.*",                 "Preferences/System"),

    # *** Modifiers ***
    # --- Intro ---
    ("bpy.types.Modifier.show_*", "Modifiers/The_Stack"),
    ("bpy.types.Modifier.*", "Modifiers"),  # catchall for various generic options
    # --- Modify Modifiers ---
    ("bpy.types.MeshCacheModifier.*",              "Modifiers/Modify/Mesh_Cache"),
    ("bpy.types.UVProjectModifier.*",              "Modifiers/Modify/UV_Project"),
    ("bpy.types.UVWarpModifier.*",                 "Modifiers/Modify/UV_Warp"),
    ("bpy.types.VertexWeightMixModifier.*",        "Modifiers/Modify/Vertex_Weight"),
    ("bpy.types.VertexWeightEditModifier.*",       "Modifiers/Modify/Vertex_Weight"),
    ("bpy.types.VertexWeightProximityModifier.*",  "Modifiers/Modify/Vertex_Weight"),
    # --- Generate Modifiers ---
    ("bpy.types.ArrayModifier.*",      "Modifiers/Generate/Array"),
    ("bpy.types.BevelModifier.*",      "Modifiers/Generate/Bevel"),
    ("bpy.types.BooleanModifier.*",    "Modifiers/Generate/Booleans"),
    ("bpy.types.BuildModifier.*",      "Modifiers/Generate/Build"),
    ("bpy.types.DecimateModifier.*",   "Modifiers/Generate/Decimate"),
    ("bpy.types.EdgeSplitModifier.*",  "Modifiers/Generate/Edge_Split"),
    ("bpy.types.MaskModifier.*",       "Modifiers/Generate/Mask"),
    ("bpy.types.MirrorModifier.*",     "Modifiers/Generate/Mirror"),
    ("bpy.types.MultiresModifier.*",   "Modifiers/Generate/Multiresolution"),
    ("bpy.types.RemeshModifier.*",     "Modifiers/Generate/"),
    ("bpy.types.ScrewModifier.*",      "Modifiers/Generate/Screw"),
    ("bpy.types.SkinModifier.*",       "Modifiers/Generate/Skin"),
    ("bpy.types.SolidifyModifier.*",   "Modifiers/Generate/Solidify"),
    ("bpy.types.SubsurfModifier.*",    "Modifiers/Generate/Subsurf"),
    ("bpy.types.TriangulateModifier.*","Modifiers/Generate/Triangulate"),
    # --- Deform Modifiers ---
    ("bpy.types.ArmatureModifier.*",      "Modifiers/Deform/Armature"),
    ("bpy.types.CastModifier.*",          "Modifiers/Deform/Cast"),
    ("bpy.types.CurveModifier.*",         "Modifiers/Deform/Curve"),
    ("bpy.types.DisplaceModifier.*",      "Modifiers/Deform/Displace"),
    ("bpy.types.HookModifier.*",          "Modifiers/Deform/Hooks"),
    ("bpy.types.LaplacianSmoothModifier.*", "Modifiers/Deform/Laplacian_Smooth"),
    ("bpy.types.LatticeModifier.*",       "Modifiers/Deform/Lattice"),
    ("bpy.types.MeshDeformModifier.*",    "Modifiers/Deform/Mesh_Deform"),
    ("bpy.types.ShrinkwrapModifier.*",    "Modifiers/Deform/Shrinkwrap"),
    ("bpy.types.SimpleDeformModifier.*",  "Modifiers/Deform/Simple_Deform"),
    ("bpy.types.SmoothModifier.*",        "Modifiers/Deform/Smooth"),
    # ("bpy.types.SurfaceModifier.*",     "Modifiers/Deform/"),  # USERS NEVER SEE THIS
    ("bpy.types.WarpModifier.*",          "Modifiers/Deform/Warp"),
    ("bpy.types.WaveModifier.*",          "Modifiers/Deform/Wave"),
    # --- Simulate Modifiers ---
    ("bpy.types.ClothModifier.*",             "Physics/Cloth"),
    ("bpy.types.CollisionModifier.*",         "Physics/Collision"),
    ("bpy.types.DynamicPaintModifier.*",      "Physics/Dynamic_Paint"),
    ("bpy.types.ExplodeModifier.*",           "Modifiers/Simulate/Explode"),
    ("bpy.types.FluidSimulationModifier.*",   "Physics/Fluid"),
    ("bpy.types.OceanModifier.*",             "Modifiers/Simulate/Ocean"),
    ("bpy.types.ParticleInstanceModifier.*",  "Modifiers/Simulate/Particle_Instance"),
    ("bpy.types.ParticleSystemModifier.*",    "Physics/Particles"),
    ("bpy.types.SmokeModifier.*",             "Physics/Smoke"),
    ("bpy.types.SoftBodyModifier.*",          "Physics/Soft_Body"),

    # *** Constraints ***
    ("bpy.types.Constraint.*", "Constraints"),
    ("bpy.types.Constraint.mute", "Constraints/The_Stack"),  # others could be added here?
    # --- Transform Constraints ---
    ("bpy.types.CopyLocationConstraint.*",    "Constraints/Transform/Copy_Location"),
    ("bpy.types.CopyRotationConstraint.*",    "Constraints/Transform/Copy_Rotation"),
    ("bpy.types.CopyScaleConstraint.*",       "Constraints/Transform/Copy_Scale"),
    ("bpy.types.CopyTransformsConstraint.*",  "Constraints/Transform/Copy_Transforms"),
    ("bpy.types.LimitDistanceConstraint.*",   "Constraints/Transform/Limit_Distance"),
    ("bpy.types.LimitLocationConstraint.*",   "Constraints/Transform/Limit_Location"),
    ("bpy.types.LimitRotationConstraint.*",   "Constraints/Transform/Limit_Rotation"),
    ("bpy.types.LimitScaleConstraint.*",      "Constraints/Transform/Limit_Scale"),
    ("bpy.types.MaintainVolumeConstraint.*",  "Constraints/Transform/Maintain_Volume"),
    ("bpy.types.TransformConstraint.*",       "Constraints/Transform/Transformation"),
    # --- Tracking Constraints ---
    ("bpy.types.ClampToConstraint.*",      "Constraints/Tracking/Clamp_To"),
    ("bpy.types.DampedTrackConstraint.*",  "Constraints/Tracking/Damped_Track"),
    ("bpy.types.KinematicConstraint.*",    "Constraints/Tracking/IK_Solver"),
    ("bpy.types.LockedTrackConstraint.*",  "Constraints/Tracking/Locked_Track"),
    ("bpy.types.SplineIKConstraint.*",     "Constraints/Tracking/Spline_IK"),
    ("bpy.types.StretchToConstraint.*",    "Constraints/Tracking/Stretch_To"),
    ("bpy.types.TrackToConstraint.*",      "Constraints/Tracking/Track_To"),
    # --- Relationship Constraints ---
    ("bpy.types.ActionConstraint.*",          "Constraints/Relationship/Action"),
    ("bpy.types.CameraSolverConstraint.*",    "Motion_Tracking"),  # not exact match
    ("bpy.types.ChildOfConstraint.*",         "Constraints/Relationship/Action"),
    ("bpy.types.FloorConstraint.*",           "Constraints/Relationship/Child_Of"),
    ("bpy.types.FollowPathConstraint.*",      "Constraints/Relationship/Floor"),
    ("bpy.types.FollowTrackConstraint.*",     "Constraints/Relationship/Follow_Path"),
    ("bpy.types.ObjectSolverConstraint.*",    "Motion_Tracking"),  # not exact match
    ("bpy.types.PivotConstraint.*",           "Constraints/Relationship/Pivot"),
    ("bpy.types.PythonConstraint.*",          "Constraints/Relationship/Script"),
    ("bpy.types.RigidBodyJointConstraint.*",  "Constraints/Relationship/Rigid_Body_Joint"),
    ("bpy.types.ShrinkwrapConstraint.*",      "Constraints/Relationship/Shrinkwrap"),

    ("bpy.types.ImageFormatSettings.*",  "Render/Output#File_Type"),
    ("bpy.types.RenderSettings.filepath",  "Render/Output#File_Locations"),
    ("bpy.types.RenderSettings.display_mode",  "Render/Display#Displaying_Renders"),
    ("bpy.types.RenderSettings.*",       "Render"),  # catchall, TODO - refine

    # *** ID Subclasses ***
    ("bpy.types.Action.*", "Animation/Actions"),
    #("bpy.types.Brush.*", ""),  # TODO - manual has no place for this! XXX
    ("bpy.types.Curve.*", "Modeling/Curves"),
    ("bpy.types.GreasePencil.*", "3D_interaction/Sketching/Drawing"),
    ("bpy.types.Group.*", "Modeling/Objects/Groups_and_Parenting#Grouping_objects"),
    ("bpy.types.Image.*", "Textures/Types/Image"),
    ("bpy.types.ShapeKey.*", "Animation/Techs/Shape/Shape_Keys"), # not an ID but include because of Key
    ("bpy.types.Key.*", "Animation/Techs/Shape/Shape_Keys"),
    #("bpy.types.Lattice.*", ""), # TODO - manual has no place for this! XXX
    ("bpy.types.Library.*", "Manual/Data_System/Linked_Libraries"),
    #("bpy.types.Mask.*", ""), # TODO - manual has no place for this! XXX
    # *** Materials (blender internal) ***
    ("bpy.types.Material.diffuse*", "Materials/Properties/Diffuse_Shaders"),
    ("bpy.types.Material.specular*", "Materials/Properties/Specular_Shaders"),
    ("bpy.types.Material.ambient*", "Materials/Properties/Ambient_Light_Effect"),
    ("bpy.types.Material.preview_render_type", "Materials/Preview"),
    ("bpy.types.Material.*", "Materials"),  # catchall, until the section is filled in

    ("bpy.types.MaterialSlot.link", "Materials/Options#Material_naming_and_linking"),
    ("bpy.types.MaterialVolume.*", "Materials/Properties/Volume"),
    ("bpy.types.MaterialHalo.*", "Materials/Halos"),
    ("bpy.types.MaterialStrand.*", "Materials/Properties/Strands"),
    ("bpy.types.MaterialSubsurfaceScattering.*", "Materials/Properties/Subsurface_Scattering"),
    ("bpy.types.MaterialRaytraceMirror.*", "Materials/Properties/Raytraced_Reflections"),
    ("bpy.types.MaterialRaytraceTransparency.*", "Materials/Properties/Raytraced_Transparency#Raytraced_Transparency"),
    # ... todo, many more options
    ("bpy.types.MovieClip.*", "Motion_Tracking#Movie_Clip_Editor"),
    ("bpy.types.MovieTrackingCamera.*", "Motion_Tracking#Camera_Data_Panel"),
    ("bpy.types.MovieTrackingStabilization.*", "Motion_Tracking#Tools_available_in_reconstruction_mode"),
    ("bpy.types.MovieTrackingTrack*", "Motion_Tracking#Tools_available_in_tracking_mode"),
    ("bpy.types.MovieTracking*", "Motion_Tracking"),
    ("bpy.types.SpaceClipEditor.*", "Motion_Tracking#Movie_Clip_Editor"),
    ("bpy.types.ColorManaged*", "Render/Post_Process/CM_And_Exposure"),
    #("bpy.types.NodeTree.*", ""),  # dont document
    ("bpy.types.Object.*",  "Modeling/Objects"),  # catchall, TODO - refine
    ("bpy.types.ParticleSettings.*", "Physics/Particles"),
    ("bpy.types.Scene.*", "Interface/Scenes"),
    ("bpy.types.Screen.*", "Interface/Screens"),
    #("bpy.types.Sound.*", ""), # TODO - manual has no place for this! XXX
    #("bpy.types.Speaker.*", ""), # TODO - manual has no place for this! XXX
    ("bpy.types.Text.*", "Extensions/Python/Text_editor"),
    ("bpy.types.Texture.*", "Textures"),
    ("bpy.types.VectorFont.*", "Modeling/Texts"),
    ("bpy.types.WindowManager.*", "Interface/Window_system"),
    ("bpy.types.World.*", "World"),
    ("bpy.types.WorldLighting.*ao*", "Lighting/Ambient_Occlusion"),
    ("bpy.types.WorldLighting.*ambient*", "Lighting/Ambient_Occlusion"),
    ("bpy.types.WorldLighting.*environment*", "Lighting/Ambient_Light"),
    ("bpy.types.WorldLighting.*", "Lighting/Ambient_Occlusion#Gather"),  # only other WorldLighting props are in Gather panel

    # *** Cycles ***
    ("bpy.types.CyclesRenderSettings.*", "Render/Cycles/Integrator"),
    ("bpy.types.CyclesVisibilitySettings.*", "Render/Cycles/Light_Paths#Ray_Visibility"),
    ("bpy.types.CyclesWorldSettings.*", "Render/Cycles/World"),
    ("bpy.types.SceneRenderLayer.*pass*", "Render/Post_Process/Passes"),
    ("bpy.types.SceneRenderLayer.*", "Render/Post_Process/Layers"),
    ("bpy.types.Cycles*", "Render/Cycles"),

    # Currently all manual links on all sockets and values (such as Fac, Roughness, Color...) are NodeSocket* type.
    # It'd be much better if the name of the socket could be used for the manual reference
    ("bpy.types.NodeSocket*", "Composite_Nodes/Node_Controls"),  # no generic socket type page exists, but composite types are the same

    # *** Cycles Material Nodes ***
    # Outputs
    ("bpy.types.ShaderNodeOutputLamp.*", "Render/Cycles/Lamps"),
    ("bpy.types.ShaderNodeOutputMaterial.*", "Render/Cycles/Materials"),
    ("bpy.types.ShaderNodeOutputWorld.*", "Render/Cycles/World"),
    # Shaders
    ("bpy.types.ShaderNodeAddShader.*", "Render/Cycles/Nodes/Shaders#Mix_and_Add"),
    ("bpy.types.ShaderNodeAmbientOcclusion.*", "Render/Cycles/Nodes/Shaders#Ambient_Occlusion"),
    ("bpy.types.ShaderNodeBackground.*", "Render/Cycles/Nodes/Shaders#Background"),
    ("bpy.types.ShaderNodeBsdfAnisotropic.*", "Render/Cycles/Nodes/Shaders#Anisotropic"),
    ("bpy.types.ShaderNodeBsdfDiffuse.*", "Render/Cycles/Nodes/Shaders#Diffuse"),
    ("bpy.types.ShaderNodeBsdfGlass.*", "Render/Cycles/Nodes/Shaders#Glass"),
    ("bpy.types.ShaderNodeBsdfGlossy.*", "Render/Cycles/Nodes/Shaders#Glossy"),
    ("bpy.types.ShaderNodeBsdfHair.*", "Render/Cycles/Nodes/Shaders"),  # TODO doc
    ("bpy.types.ShaderNodeBsdfRefraction.*", "Render/Cycles/Nodes/Shaders#Refraction"),
    ("bpy.types.ShaderNodeBsdfToon.*", "Render/Cycles/Nodes/Shaders#Toon"),
    ("bpy.types.ShaderNodeBsdfTranslucent.*", "Render/Cycles/Nodes/Shaders#Translucent"),
    ("bpy.types.ShaderNodeBsdfTransparent.*", "Render/Cycles/Nodes/Shaders#Transparent"),
    ("bpy.types.ShaderNodeBsdfVelvet.*", "Render/Cycles/Nodes/Shaders#Velvet"),
    ("bpy.types.ShaderNodeEmission.*", "Render/Cycles/Nodes/Shaders#Emission"),
    ("bpy.types.ShaderNodeHoldout.*", "Render/Cycles/Nodes/Shaders#Holdout"),
    ("bpy.types.ShaderNodeMixShader.*", "Render/Cycles/Nodes/Shaders#Mix_and_Add"),
    ("bpy.types.ShaderNodeSubsurfaceScattering.*", "Render/Cycles/Nodes/Shaders#Subsurface_Scattering"),
    ("bpy.types.ShaderNodeVolumeAbsorption.*", "Render/Cycles/Nodes/Shaders"),  # TODO doc
    ("bpy.types.ShaderNodeVolumeScatter.*", "Render/Cycles/Nodes/Shaders"),  # TODO doc
    # Textures
    ("bpy.types.ShaderNodeTexBrick.*", "Render/Cycles/Nodes/Textures#Brick_Texture"),
    ("bpy.types.ShaderNodeTexChecker.*", "Render/Cycles/Nodes/Textures#Checker_Texture"),
    ("bpy.types.ShaderNodeTexEnvironment.*", "Render/Cycles/Nodes/Textures#Environment_Texture"),
    ("bpy.types.ShaderNodeTexGradient.*", "Render/Cycles/Nodes/Textures#Gradient_Texture"),
    ("bpy.types.ShaderNodeTexImage.*", "Render/Cycles/Nodes/Textures#Image_Texture"),
    ("bpy.types.ShaderNodeTexMagic.*", "Render/Cycles/Nodes/Textures#Magic_Texture"),
    ("bpy.types.ShaderNodeTexMusgrave.*", "Render/Cycles/Nodes/Textures#Musgrave_Texture"),
    ("bpy.types.ShaderNodeTexNoise.*", "Render/Cycles/Nodes/Textures#Noise_Texture"),
    ("bpy.types.ShaderNodeTexSky.*", "Render/Cycles/Nodes/Textures#Sky_Texture"),
    ("bpy.types.ShaderNodeTexVoronoi.*", "Render/Cycles/Nodes/Textures#Voronoi_Texture"),
    ("bpy.types.ShaderNodeTexWave.*", "Render/Cycles/Nodes/Textures#Wave_Texture"),
    # Other
    ("bpy.types.ShaderNodeAttribute.*", "Render/Cycles/Nodes/More#Attribute"),
    ("bpy.types.ShaderNodeBlackbody.*", "Render/Cycles/Nodes/More#Blackbody"),
    ("bpy.types.ShaderNodeBrightContrast.*", "Composite_Nodes/Types/Color#Bright.2FContrast"),
    ("bpy.types.ShaderNodeBump.*", "Render/Cycles/Nodes/More#Bump"),
    ("bpy.types.ShaderNodeCameraData.*", "Render/Cycles/Nodes/More"),  # TODO doc
    ("bpy.types.ShaderNodeCombineHSV.*", "Composite_Nodes/Types/Convertor#Separate.2FCombine_HSVA_Nodes"),
    ("bpy.types.ShaderNodeCombineRGB.*", "Composite_Nodes/Types/Convertor#Separate.2FCombine_RGBA_Node"),
    ("bpy.types.ShaderNodeFresnel.*", "Render/Cycles/Nodes/More#Fresnel"),
    ("bpy.types.ShaderNodeGamma.*", "Composite_Nodes/Types/Color#Gamma"),
    ("bpy.types.ShaderNodeGeometry.*", "Render/Cycles/Nodes/More#Geometry"),
    ("bpy.types.ShaderNodeHairInfo.*", "Render/Cycles/Nodes/More#Hair_Info"),
    ("bpy.types.ShaderNodeHueSaturation.*", "Composite_Nodes/Types/Color#Hue_Saturation_Node"),
    ("bpy.types.ShaderNodeInvert.*", "Composite_Nodes/Types/Color#Invert"),
    ("bpy.types.ShaderNodeLayerWeight.*", "Render/Cycles/Nodes/More#Layer_Weight"),
    ("bpy.types.ShaderNodeLightFalloff.*", "Render/Cycles/Nodes/More#Light_Falloff"),
    ("bpy.types.ShaderNodeLightPath.*", "Render/Cycles/Nodes/More#Light_Path"),
    ("bpy.types.ShaderNodeMapping.*", "Render/Cycles/Nodes/More#Mapping"),
    ("bpy.types.ShaderNodeMath.*", "Composite_Nodes/Types/Convertor#Math_Node"),
    ("bpy.types.ShaderNodeMixRGB.*", "Composite_Nodes/Types/Color#Mix_Node"),
    ("bpy.types.ShaderNodeNormalMap.*", "Render/Cycles/Nodes/More#Normal_Map"),
    ("bpy.types.ShaderNodeObjectInfo.*", "Render/Cycles/Nodes/More#Object_Info"),
    ("bpy.types.ShaderNodeParticleInfo.*", "Render/Cycles/Nodes/More#Particle_Info"),
    ("bpy.types.ShaderNodeRGB.*", "Render/Cycles/Nodes/More#RGB"),
    ("bpy.types.ShaderNodeRGBCurve.*", "Composite_Nodes/Types/Color#RGB_Curves_Node"),
    ("bpy.types.ShaderNodeRGBToBW.*", "Composite_Nodes/Types/Convertor#RGB_to_BW_Node"),
    ("bpy.types.ShaderNodeSeparateHSV.*", "Composite_Nodes/Types/Convertor#Separate.2FCombine_HSVA_Nodes"),
    ("bpy.types.ShaderNodeSeparateRGB.*", "Composite_Nodes/Types/Convertor#Separate.2FCombine_RGBA_Node"),
    ("bpy.types.ShaderNodeTangent.*", "Render/Cycles/Nodes/More#Tangent"),
    ("bpy.types.ShaderNodeTexCoord.*", "Render/Cycles/Nodes/More#Texture_Coordinates"),
    ("bpy.types.ShaderNodeValue.*", "Render/Cycles/Nodes/More#Value"),
    ("bpy.types.ShaderNodeVectorCurve.*", "Composite_Nodes/Types/Vector#Vector_Curves_Node"),
    ("bpy.types.ShaderNodeVectorMath.*", "Render/Cycles/Nodes/More"),  # TODO doc
    ("bpy.types.ShaderNodeVectorTransform.*", "Render/Cycles/Nodes/More#Vector_Transform"),
    ("bpy.types.ShaderNodeWavelength.*", "Render/Cycles/Nodes/More#Wavelength"),
    ("bpy.types.ShaderNodeWireframe.*", "Render/Cycles/Nodes/More#Wireframe"),

    ("bpy.types.ShaderNodeGroup.*", "Composite_Nodes/Node_Groups"),
    ("bpy.types.ShaderNode*", "Render/Cycles/Nodes"),

    ("bpy.types.ShaderNodeScript.*", "Render/Cycles/Nodes/OSL"),

    # *** Compositing Nodes ***
    # Input
    ("bpy.types.CompositorNodeBokehImage.*", "Composite_Nodes/Types/Input"),  # TODO doc
    ("bpy.types.CompositorNodeImage.*", "Composite_Nodes/Types/Input#Image_node"),
    ("bpy.types.CompositorNodeMask.*", "Composite_Nodes/Types/Input"),  # TODO doc
    ("bpy.types.CompositorNodeMovieClip.*", "Composite_Nodes/Types/Input"),  # TODO doc
    ("bpy.types.CompositorNodeRGB.*", "Composite_Nodes/Types/Input#RGB_node"),
    ("bpy.types.CompositorNodeRLayers.*", "Composite_Nodes/Types/Input#Render_Layers_Node"),
    ("bpy.types.CompositorNodeTexture.*", "Composite_Nodes/Types/Input#Texture_Node"),
    ("bpy.types.CompositorNodeTime.*", "Composite_Nodes/Types/Input#Time_node"),
    ("bpy.types.CompositorNodeTrackPos.*", "Composite_Nodes/Types/Input"),  # TODO doc
    ("bpy.types.CompositorNodeValue.*", "Composite_Nodes/Types/Input#Value_node"),
    # Output
    ("bpy.types.CompositorNodeComposite.*", "Composite_Nodes/Types/Output#Composite_Output_Nodes"),
    ("bpy.types.CompositorNodeLevels.*", "Composite_Nodes/Types/Output#Levels_Node"),
    ("bpy.types.CompositorNodeOutputFile*", "Composite_Nodes/Types/Output#File_Output_Node"),
    ("bpy.types.CompositorNodeSplitViewer.*", "Composite_Nodes/Types/Output#SplitViewer_Node"),
    ("bpy.types.CompositorNodeViewer.*", "Composite_Nodes/Types/Output#Viewer"),
    # Color
    ("bpy.types.CompositorNodeAlphaOver.*", "Composite_Nodes/Types/Color#AlphaOver_Node"),
    ("bpy.types.CompositorNodeBrightContrast.*", "Composite_Nodes/Types/Color#Bright.2FContrast"),
    ("bpy.types.CompositorNodeColorBalance.*", "Composite_Nodes/Types/Color#Color_Balance"),
    ("bpy.types.CompositorNodeColorCorrection.*", "Composite_Nodes/Types/Color"),  # TODO doc
    ("bpy.types.CompositorNodeCurveRGB.*", "Composite_Nodes/Types/Color#RGB_Curves_Node"),
    ("bpy.types.CompositorNodeGamma.*", "Composite_Nodes/Types/Color#Gamma"),
    ("bpy.types.CompositorNodeHueCorrect.*", "Composite_Nodes/Types/Color#Hue_Correct"),
    ("bpy.types.CompositorNodeHueSat.*", "Composite_Nodes/Types/Color#Hue_Saturation_Node"),
    ("bpy.types.CompositorNodeInvert.*", "Composite_Nodes/Types/Color#Invert"),
    ("bpy.types.CompositorNodeMixRGB.*", "Composite_Nodes/Types/Color#Mix_Node"),
    ("bpy.types.CompositorNodeTonemap.*", "Composite_Nodes/Types/Color#Tone_Map"),
    ("bpy.types.CompositorNodeZcombine.*", "Composite_Nodes/Types/Color#Z-Combine_Node"),
    # Converter (Misspelt 'Convertor' in wiki)
    ("bpy.types.CompositorNodeSep*", "Composite_Nodes/Types/Convertor#Combine.2FSeparate_Nodes"),
    ("bpy.types.CompositorNodeComb*", "Composite_Nodes/Types/Convertor#Combine.2FSeparate_Nodes"),
    ("bpy.types.CompositorNodeIDMask.*", "Composite_Nodes/Types/Convertor#ID_Mask_Node"),
    ("bpy.types.CompositorNodeMath.*", "Composite_Nodes/Types/Convertor#Math_Node"),
    ("bpy.types.CompositorNodePremulKey.*", "Composite_Nodes/Types/Convertor#Alpha_Convert"),
    ("bpy.types.CompositorNodeRGBToBW.*", "Composite_Nodes/Types/Convertor#RGB_to_BW_Node"),
    ("bpy.types.CompositorNodeSetAlpha.*", "Composite_Nodes/Types/Convertor#Set_Alpha_Node"),
    # Filter
    ("bpy.types.CompositorNodeBilateralblur.*", "Composite_Nodes/Types/Filter#Bilateral_Blur_Node"),
    ("bpy.types.CompositorNodeBlur.*", "Composite_Nodes/Types/Filter#Blur_Node"),
    ("bpy.types.CompositorNodeBokehBlur.*", "Composite_Nodes/Types/Filter"),  # TODO doc
    ("bpy.types.CompositorNodeDBlur.*", "Composite_Nodes/Types/Filter#Directional_Blur_Node"),
    ("bpy.types.CompositorNodeDefocus.*", "Composite_Nodes/Types/Filter#Defocus"),
    ("bpy.types.CompositorNodeDespeckle.*", "Composite_Nodes/Types/Filter"),  # TODO doc
    ("bpy.types.CompositorNodeDilateErode.*", "Composite_Nodes/Types/Filter#Dilate.2FErode_Node"),
    ("bpy.types.CompositorNodeFilter.*", "Composite_Nodes/Types/Filter#Filter_Node"),
    ("bpy.types.CompositorNodeGlare.*", "Composite_Nodes/Types/Filter"),  # TODO doc
    ("bpy.types.CompositorNodeInpaint.*", "Composite_Nodes/Types/Filter"),  # TODO doc
    ("bpy.types.CompositorNodePixelate.*", "Composite_Nodes/Types/Filter"),  # TODO doc
    ("bpy.types.CompositorNodeVecBlur.*", "Composite_Nodes/Types/Filter#Vector_.28Motion.29_Blur_Node"),
    # Vector
    ("bpy.types.CompositorNodeCurveVec.*", "Composite_Nodes/Types/Vector#Vector_Curves_Node"),
    ("bpy.types.CompositorNodeMapRange.*", "Composite_Nodes/Types/Vector"),  # TODO doc
    ("bpy.types.CompositorNodeMapValue.*", "Composite_Nodes/Types/Vector#Map_Value_Node"),
    ("bpy.types.CompositorNodeNormal.*", "Composite_Nodes/Types/Vector#Normal_Node"),
    ("bpy.types.CompositorNodeNormalize.*", "Composite_Nodes/Types/Vector#Normalize"),
    # Matte
    ("bpy.types.CompositorNodeBoxMask.*", "Composite_Nodes/Types/Matte"),  # TODO doc
    ("bpy.types.CompositorNodeChannelMatte.*", "Composite_Nodes/Types/Matte#Channel_Key_Node"),
    ("bpy.types.CompositorNodeChromaMatte.*", "Composite_Nodes/Types/Matte#Chroma_Key_Node"),
    ("bpy.types.CompositorNodeColorMatte.*", "Composite_Nodes/Types/Matte#Color_Key"),
    ("bpy.types.CompositorNodeColorSpill.*", "Composite_Nodes/Types/Matte#Color_Spill_Node"),
    ("bpy.types.CompositorNodeDiffMatte.*", "Composite_Nodes/Types/Matte#Difference_Key_Node"),
    ("bpy.types.CompositorNodeDistanceMatte.*", "Composite_Nodes/Types/Matte#Distance_Key"),  # TODO doc (header is there, no text)
    ("bpy.types.CompositorNodeDoubleEdgeMask.*", "Composite_Nodes/Types/Matte"),  # TODO doc
    ("bpy.types.CompositorNodeEllipseMask.*", "Composite_Nodes/Types/Matte"),  # TODO doc
    ("bpy.types.CompositorNodeKeying.*", "Composite_Nodes/Types/Matte"),  # TODO doc
    ("bpy.types.CompositorNodeKeyingScreen.*", "Composite_Nodes/Types/Matte"),  # TODO doc
    ("bpy.types.CompositorNodeLumaMatte.*", "Composite_Nodes/Types/Matte#Luminance_Key_Node"),
    # Distort
    ("bpy.types.CompositorNodeCrop.*", "Composite_Nodes/Types/Distort#Crop_Node"),
    ("bpy.types.CompositorNodeDisplace.*", "Composite_Nodes/Types/Distort#Displace_Node"),
    ("bpy.types.CompositorNodeFlip.*", "Composite_Nodes/Types/Distort#Flip_Node"),
    ("bpy.types.CompositorNodeLensdist.*", "Composite_Nodes/Types/Distort#Lens_Distortion"),
    ("bpy.types.CompositorNodeMapUV.*", "Composite_Nodes/Types/Distort#Map_UV_Node"),
    ("bpy.types.CompositorNodeMovieDistortion.*", "Composite_Nodes/Types/Distort"),  # TODO doc
    ("bpy.types.CompositorNodePlaneTrackDeform.*", "Composite_Nodes/Types/Distort"),  # TODO doc
    ("bpy.types.CompositorNodeRotate.*", "Composite_Nodes/Types/Distort#Rotate_Node"),
    ("bpy.types.CompositorNodeScale.*", "Composite_Nodes/Types/Distort#Scale_Node"),
    ("bpy.types.CompositorNodeStabilize.*", "Composite_Nodes/Types/Distort"),  # TODO doc
    ("bpy.types.CompositorNodeTransform.*", "Composite_Nodes/Types/Distort"),  # TODO doc
    ("bpy.types.CompositorNodeTranslate.*", "Composite_Nodes/Types/Distort#Translate_Node"),
    #Other
    ("bpy.types.CompositorNodeGroup.*", "Composite_Nodes/Node_Groups"),
    ("bpy.types.CompositorNode*", "Composite_Nodes/Types"),  # catch anything else

    ("bpy.types.ColorRamp*", "Materials/Properties/Ramps"),

    # *** ID Subclasses (cont.) Object Data ***
    ("bpy.types.Mesh.*",  "Modeling/Meshes"),  # catchall, TODO - refine
    ("bpy.types.MetaBall.*",  "Modeling/Metas"),  # catchall, TODO - refine
    ("bpy.types.TextCurve.*",  "Modeling/Texts"),  # catchall, TODO - refine
    ("bpy.types.Armature.*",  "Rigging/Armatures"),  # catchall, TODO - refine
    ("bpy.types.Camera.*",  "Render/Camera"),  # catchall, TODO - refine

    ("bpy.types.PointLamp.*",  "Lighting/Lamps/Lamp"),  # catchall, TODO - refine
    ("bpy.types.AreaLamp.*",   "Lighting/Lamps/Area"),  # catchall, TODO - refine
    ("bpy.types.SpotLamp.*",   "Lighting/Lamps/Spot"),  # catchall, TODO - refine
    ("bpy.types.SunLamp.*",    "Lighting/Lamps/Sun"),   # catchall, TODO - refine
    ("bpy.types.HemiLamp.*",   "Lighting/Lamps/Hemi"),  # catchall, TODO - refine
    ("bpy.types.Lamp.*",       "Lighting"),             # catchall, TODO - refine

    # --- Animation ---
    ("bpy.types.Keyframe.*", "Animation/Keyframes"),
    ("bpy.types.FCurve.*", "Animation/Editors/Graph/FCurves"),
    
    # --- Rigging ---
    ("bpy.types.Bone.*",      "Armatures/Bones"),
    ("bpy.types.EditBone.*",  "Armatures/Bones"),
    ("bpy.types.PoseBone.*",  "Rigging/Posing"),

    # --- World ---
    ("bpy.types.World.*",  "World"),

    ("bpy.types.Texture.*",  "Textures"),

    # *** Spaces ***
    ("bpy.types.SpaceView3D.*", "3D_interaction/Navigating/3D_View_Options"),

    # === Operators ===
    # Catch all only for now!
    # *** Window/Screen ***
    
    ("bpy.ops.action.*",  "Animation/Actions"),
    ("bpy.ops.anim.*",  "Animation"),
    ("bpy.ops.armature.*",  "Rigging/Armatures"),
    ("bpy.ops.boid.*",  "Physics/Particles/Physics/Boids"),
    # ("bpy.ops.brush.*",  ""),  # TODO
    ("bpy.ops.buttons.*",  "Interface/Buttons_and_Controls"),
    ("bpy.ops.camera.*",  "Render/Camera"),
    ("bpy.ops.clip.*",  "Motion_Tracking#Movie_Clip_Editor"),
    ("bpy.ops.cloth.*",  "Physics/Cloth"),
    ("bpy.ops.console.*",  "Python/Console"),
    ("bpy.ops.constraint.*",  "Constraints"),
    ("bpy.ops.curve.*",  "Modeling/Curves"),
    ("bpy.ops.dpaint.*",  "Physics/Dynamic_Paint"),
    # ("bpy.ops.ed.*",  ""),  # TODO, this is for internal use only?
    # ("bpy.ops.export_anim.*",  ""),  # TODO
    # ("bpy.ops.export_mesh.*",  ""),  # TODO
    # ("bpy.ops.export_scene.*",  ""),  # TODO
    ("bpy.ops.file.*",  ""),
    ("bpy.ops.fluid.*",  "Physics/Fluid"),
    ("bpy.ops.font.*",  "Modeling/Texts"),
    ("bpy.ops.gpencil.*",  "3D_interaction/Sketching/Drawing"),
    ("bpy.ops.graph.*",  "Animation/Editors/Graph/FCurves"),
    ("bpy.ops.group.*",  "Modeling/Objects/Groups_and_Parenting#Grouping_objects"),
    ("bpy.ops.image.*",  "Textures/Types/Image"),
    # ("bpy.ops.import_anim.*",  ""),  # TODO
    # ("bpy.ops.import_curve.*",  ""),  # TODO
    # ("bpy.ops.import_mesh.*",  ""),  # TODO
    # ("bpy.ops.import_scene.*",  ""),  # TODO
    # ("bpy.ops.info.*",  ""),  # TODO
    ("bpy.ops.lamp.*",  "Lighting"),  # --- TODO ... all below ---
    # ("bpy.ops.lattice.*",  ""),  # TODO
    ("bpy.ops.logic.*",  "Game_Engine/Logic"),
    ("bpy.ops.marker.*",  "Animation/Markers"),
    # ("bpy.ops.mask.*",  ""),  # TODO
    ("bpy.ops.material.new",  "Materials/Assigning_a_material#Creating_a_new_Material"),
    ("bpy.ops.material.*",  "Materials"),
    ("bpy.ops.mesh.vertices_smooth", "Modeling/Meshes/Editing/Deforming/Smooth"),
    ("bpy.ops.view3d.edit_mesh_extrude*", "Modeling/Meshes/Editing/Duplicating/Extrude"),
    ("bpy.ops.mesh.subdivide", "Modeling/Meshes/Editing/Subdividing/Subdivide"),
    ("bpy.ops.mesh.loopcut_slide", "Modeling/Meshes/Editing/Subdividing/Loop_Subdivide"),
    ("bpy.ops.mesh.bridge_edge_loops", "Modeling/Meshes/Editing/Edges#Bridge_Edge_Loops"),
    ("bpy.ops.mesh.duplicate_move", "Modeling/Meshes/Editing/Duplicating/Duplicate"),
    ("bpy.ops.mesh.spin", "Modeling/Meshes/Editing/Duplicating/Spin"),
    ("bpy.ops.mesh.screw", "Modeling/Meshes/Editing/Duplicating/Screw"),
    ("bpy.ops.mesh.knife*", "Modeling/Meshes/Editing/Subdividing/Knife_Subdivide"),
    ("bpy.ops.mesh.bisect", "Modeling/Meshes/Editing/Subdividing/Bisect"),
    ("bpy.ops.mball.*",  "Modeling/Metas"),
    ("bpy.ops.mesh.*",  "Modeling/Meshes"),
    ("bpy.ops.nla.*",  "Animation/Editors/NLA"),
    # ("bpy.ops.node.*",  ""),  # TODO
    ("bpy.ops.object.*shape_key*", "Animation/Techs/Shape/Shape_Keys"),
    ("bpy.ops.object.join_shapes", "Animation/Techs/Shape/Shape_Keys"),
    ("bpy.ops.object.*",  "Modeling/Objects"),
    ("bpy.ops.outliner.*",  "Data_System/The_Outliner"),
    # ("bpy.ops.paint.*",  ""),  # TODO
    ("bpy.ops.particle.*",  "Physics/Particles"),
    ("bpy.ops.pose.*",  "Rigging/Posing"),
    ("bpy.ops.poselib.*",  "Rigging/Posing/Pose_Library"),
    # ("bpy.ops.ptcache.*",  ""),  # TODO

    ("bpy.ops.render.play_rendered_anim",  "Render/Display#Animation_Playback"),
    ("bpy.ops.render.*",  "Render"),  # catchall

    ("bpy.ops.scene.*",  "Interface/Scenes"),
    ("bpy.ops.screen.*",  "Interface/Window_system"),
    ("bpy.ops.script.*",  "Extensions/Python"),
    ("bpy.ops.sculpt.*",  "Modeling/Meshes/Editing/Sculpt_Mode"),
    ("bpy.ops.sequencer.*",  "Sequencer/Usage"),
    # ("bpy.ops.sketch.*",  ""),  # TODO
    # ("bpy.ops.sound.*",  ""),  # TODO
    ("bpy.ops.surface.*",  "Modeling/Surfaces"),
    ("bpy.ops.text.*",  "Extensions/Python/Text_editor"),
    ("bpy.ops.texture.*",  "Textures"),
    ("bpy.ops.time.*",  "Animation/Timeline"),
    ("bpy.ops.transform.edge_slide", "Modeling/Meshes/Editing/Edges#Edge_Slide"),
    ("bpy.ops.transform.vert_slide", "Modeling/Meshes/Editing/Vertices#Vertex_Slide"),
    ("bpy.ops.transform.shrink_fatten", "Modeling/Meshes/Editing/Deforming/Shrink-Fatten"),
    ("bpy.ops.transform.push_pull", "3D_interaction/Transformations/Advanced/Push_Pull"),
    ("bpy.ops.transform.*",  "3D_interaction/Transform_Control"),
    ("bpy.ops.ui.*",  "Interface"),
    ("bpy.ops.uv.*",  "Textures/Mapping/UV/Layout_Editing"),
    # ("bpy.ops.view2d.*",  ""),  # TODO
    ("bpy.ops.view3d.*",  "3D_interaction/Navigating/3D_View"),  # this link is a bit arbitrary
    ("bpy.ops.wm.*",      "Interface/Window_system"),
    ("bpy.ops.world.*",  "World"),
    
    # === Tool Settings ===
    ("bpy.types.MeshStatVis.*",  "Modeling/Meshes#Mesh_Analysis"),
)

# may have 'url_reference_mapping'... etc later
