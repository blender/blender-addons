# this file maps RNA to online URL's for right mouse context menu
# documentation access

# URL prefix is the: url_manual_prefix + url_manual_mapping[id]

url_manual_prefix = "http://wiki.blender.org/index.php/Doc:2.6/Manual/"

# - The first item is a regex mapping '.*' means anything.
# - Expressions are evaluated top down (include catch-all expressions last).
url_manual_mapping = (
    ("bpy.types.ArmatureModifier.*", "Modifiers/Deform/Armature"),
    ("bpy.types.SmoothModifier.*", "Modifiers/Deform/Smooth"),
    ("bpy.types.SubsurfModifier.*", "Modifiers/Generate/Subsurf"),
    
    ("bpy.types.Material.diffuse.*", "Materials/Properties/Diffuse_Shaders"),
)

# may have 'url_reference_mapping'... etc later
