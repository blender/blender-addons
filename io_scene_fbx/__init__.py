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
    "name": "Autodesk FBX format",
    "author": "Campbell Barton, Bastien Montagne",
    "version": (3, 1, 0),
    "blender": (2, 70, 0),
    "location": "File > Import-Export",
    "description": "Export FBX meshes, UV's, vertex colors, materials, "
                   "textures, cameras, lamps and actions",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/Import-Export/Autodesk_FBX",
    "tracker_url": "",
    "support": 'OFFICIAL',
    "category": "Import-Export"}


if "bpy" in locals():
    import imp
    if "import_fbx" in locals():
        imp.reload(import_fbx)
    if "export_fbx_bin" in locals():
        imp.reload(export_fbx_bin)
    if "export_fbx" in locals():
        imp.reload(export_fbx)


import bpy
from bpy.props import (StringProperty,
                       BoolProperty,
                       FloatProperty,
                       EnumProperty,
                       )

from bpy_extras.io_utils import (ImportHelper,
                                 ExportHelper,
                                 path_reference_mode,
                                 axis_conversion,
                                 )


class ImportFBX(bpy.types.Operator, ImportHelper):
    """Load a FBX geometry file"""
    bl_idname = "import_scene.fbx"
    bl_label = "Import FBX"
    bl_options = {'UNDO', 'PRESET'}

    directory = StringProperty()

    filename_ext = ".fbx"
    filter_glob = StringProperty(default="*.fbx", options={'HIDDEN'})

    use_manual_orientation = BoolProperty(
        name="Manual Orientation",
        description="Specify orientation and scale, instead of using embedded data in FBX file",
        default=False,
    )
    axis_forward = EnumProperty(
        name="Forward",
        items=(('X', "X Forward", ""),
               ('Y', "Y Forward", ""),
               ('Z', "Z Forward", ""),
               ('-X', "-X Forward", ""),
               ('-Y', "-Y Forward", ""),
               ('-Z', "-Z Forward", ""),
               ),
        default='-Z',
    )
    axis_up = EnumProperty(
        name="Up",
        items=(('X', "X Up", ""),
               ('Y', "Y Up", ""),
               ('Z', "Z Up", ""),
               ('-X', "-X Up", ""),
               ('-Y', "-Y Up", ""),
               ('-Z', "-Z Up", ""),
               ),
        default='Y',
    )
    global_scale = FloatProperty(
        name="Scale",
        min=0.001, max=1000.0,
        default=1.0,
    )

    use_image_search = BoolProperty(
        name="Image Search",
        description="Search subdirs for any associated images (Warning, may be slow)",
        default=True,
    )

    use_alpha_decals = BoolProperty(
        name="Alpha Decals",
        description="Treat materials with alpha as decals (no shadow casting)",
        default=False,
        options={'HIDDEN'}
    )
    decal_offset = FloatProperty(
        name="Decal Offset",
        description="Displace geometry of alpha meshes",
        min=0.0, max=1.0,
        default=0.0,
        options={'HIDDEN'}
    )

    def draw(self, context):
        layout = self.layout

        layout.prop(self, "use_manual_orientation"),
        sub = layout.column()
        sub.enabled = self.use_manual_orientation
        sub.prop(self, "axis_forward")
        sub.prop(self, "axis_up")
        sub.prop(self, "global_scale")

        layout.prop(self, "use_image_search")
        #layout.prop(self, "use_alpha_decals")
        layout.prop(self, "decal_offset")

    def execute(self, context):
        keywords = self.as_keywords(ignore=("filter_glob", "directory"))
        keywords["use_cycles"] = (context.scene.render.engine == 'CYCLES')

        from . import import_fbx
        return import_fbx.load(self, context, **keywords)


class ExportFBX(bpy.types.Operator, ExportHelper):
    """Selection to an ASCII Autodesk FBX"""
    bl_idname = "export_scene.fbx"
    bl_label = "Export FBX"
    bl_options = {'UNDO', 'PRESET'}

    filename_ext = ".fbx"
    filter_glob = StringProperty(default="*.fbx", options={'HIDDEN'})

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.

    version = EnumProperty(
        items=(('BIN7400', "FBX 7.4 binary", "Newer 7.4 binary version, still in development (no animation yet)"),
               ('ASCII6100', "FBX 6.1 ASCII", "Legacy 6.1 ascii version"),
               ),
        name="Exporter Version",
        description="Choose which version of the exporter to use",
        default='BIN7400',
    )

    use_selection = BoolProperty(
        name="Selected Objects",
        description="Export selected objects on visible layers",
        default=False,
    )
    global_scale = FloatProperty(
        name="Scale",
        description="Scale all data (Some importers do not support scaled armatures!)",
        min=0.001, max=1000.0,
        soft_min=0.01, soft_max=1000.0,
        default=1.0,
    )
    axis_forward = EnumProperty(
        name="Forward",
        items=(('X', "X Forward", ""),
               ('Y', "Y Forward", ""),
               ('Z', "Z Forward", ""),
               ('-X', "-X Forward", ""),
               ('-Y', "-Y Forward", ""),
               ('-Z', "-Z Forward", ""),
               ),
        default='-Z',
    )
    axis_up = EnumProperty(
        name="Up",
        items=(('X', "X Up", ""),
               ('Y', "Y Up", ""),
               ('Z', "Z Up", ""),
               ('-X', "-X Up", ""),
               ('-Y', "-Y Up", ""),
               ('-Z', "-Z Up", ""),
               ),
        default='Y',
    )
    # 7.4 only
    bake_space_transform = BoolProperty(
        name="Bake Space Transform",
        description=("Bake space transform into object data, avoids getting unwanted rotations to objects when "
                     "target space is not aligned with Blender's space "
                     "(WARNING! experimental option, might give odd/wrong results)"),
        default=False,
    )

    object_types = EnumProperty(
        name="Object Types",
        options={'ENUM_FLAG'},
        items=(('EMPTY', "Empty", ""),
               ('CAMERA', "Camera", ""),
               ('LAMP', "Lamp", ""),
               ('ARMATURE', "Armature", ""),
               ('MESH', "Mesh", ""),
               ('OTHER', "Other", "Other geometry types, like curve, metaball, etc. (converted to meshes)"),
               ),
        description="Which kind of object to export",
        default={'EMPTY', 'CAMERA', 'LAMP', 'ARMATURE', 'MESH'},
    )

    use_mesh_modifiers = BoolProperty(
        name="Apply Modifiers",
        description="Apply modifiers to mesh objects (except Armature ones!)",
        default=True,
    )
    mesh_smooth_type = EnumProperty(
        name="Smoothing",
        items=(('OFF', "Off", "Don't write smoothing"),
               ('FACE', "Face", "Write face smoothing"),
               ('EDGE', "Edge", "Write edge smoothing"),
               ),
        description="Export smoothing information (not mandatory if your target importer understand split normals)",
        default='FACE',
    )
    use_mesh_edges = BoolProperty(
        name="Loose Edges",
        description="Export loose edges (as two-vertices polygons)",
        default=False,
    )
    # 7.4 only
    use_tspace = BoolProperty(
        name="Tangent Space",
        description=("Add binormal and tangent vectors, together with normal they form the tangent space "
                     "(will only work correctly with tris/quads only meshes!)"),
        default=False,
    )
    # 7.4 only
    use_custom_properties = BoolProperty(
        name="Custom Properties",
        description="Export custom properties",
        default=False,
    )
    # 6.1 only
    use_armature_deform_only = BoolProperty(
        name="Only Deform Bones",
        description="Only write deforming bones",
        default=False,
    )
    # Anim - 7.4
    bake_anim = BoolProperty(
        name="Baked Animation",
        description="Export baked keyframe animation",
        default=True,
    )
    bake_anim_use_nla_strips = BoolProperty(
        name="NLA Strips",
        description=("Export each non-muted NLA strip as a separated FBX's AnimStack, if any, "
                     "instead of global scene animation"),
        default=True,
    )
    bake_anim_use_all_actions = BoolProperty(
        name="All Actions",
        description=("Export each action as a separated FBX's AnimStack, "
                     "instead of global scene animation"),
        default=True,
    )
    bake_anim_step = FloatProperty(
        name="Sampling Rate",
        description=("How often to evaluate animated values (in frames)"),
        min=0.01, max=100.0,
        soft_min=0.1, soft_max=10.0,
        default=1.0,
    )
    bake_anim_simplify_factor = FloatProperty(
        name="Simplify",
        description=("How much to simplify baked values (0.0 to disable, the higher the more simplified"),
        min=0.0, max=10.0,  # No simplification to up to 0.05 slope/100 max_frame_step.
        default=1.0,  # default: min slope: 0.005, max frame step: 10.
    )
    # Anim - 6.1
    use_anim = BoolProperty(
        name="Animation",
        description="Export keyframe animation",
        default=True,
    )
    use_anim_action_all = BoolProperty(
        name="All Actions",
        description=("Export all actions for armatures or just the currently selected action"),
        default=True,
    )
    use_default_take = BoolProperty(
        name="Default Take",
        description=("Export currently assigned object and armature animations into a default take from the scene "
                     "start/end frames"),
        default=True
    )
    use_anim_optimize = BoolProperty(
        name="Optimize Keyframes",
        description="Remove double keyframes",
        default=True,
    )
    anim_optimize_precision = FloatProperty(
        name="Precision",
        description=("Tolerance for comparing double keyframes (higher for greater accuracy)"),
        min=0.0, max=20.0,  # from 10^2 to 10^-18 frames precision.
        soft_min=1.0, soft_max=16.0,
        default=6.0,  # default: 10^-4 frames.
    )
    # End anim
    path_mode = path_reference_mode
    # 7.4 only
    embed_textures = BoolProperty(
        name="Embed Textures",
        description="Embed textures in FBX binary file (only for \"Copy\" path mode!)",
        default=False,
    )
    batch_mode = EnumProperty(
        name="Batch Mode",
        items=(('OFF', "Off", "Active scene to file"),
               ('SCENE', "Scene", "Each scene as a file"),
               ('GROUP', "Group", "Each group as a file"),
               ),
    )
    use_batch_own_dir = BoolProperty(
        name="Batch Own Dir",
        description="Create a dir for each exported file",
        default=True,
    )
    use_metadata = BoolProperty(
        name="Use Metadata",
        default=True,
        options={'HIDDEN'},
    )

    def draw(self, context):
        layout = self.layout
        is_74bin = (self.version == 'BIN7400')

        layout.prop(self, "version")
        layout.prop(self, "use_selection")
        layout.prop(self, "global_scale")
        layout.prop(self, "axis_forward")
        layout.prop(self, "axis_up")
        if is_74bin:
            layout.prop(self, "bake_space_transform")

        layout.separator()
        layout.prop(self, "object_types")
        layout.prop(self, "use_mesh_modifiers")
        layout.prop(self, "mesh_smooth_type")
        layout.prop(self, "use_mesh_edges")
        layout.prop(self, "use_tspace")
        if is_74bin:
            layout.prop(self, "use_custom_properties")
            layout.prop(self, "bake_anim")
            col = layout.column()
            col.enabled = self.bake_anim
            col.prop(self, "bake_anim_use_nla_strips")
            col.prop(self, "bake_anim_use_all_actions")
            col.prop(self, "bake_anim_step")
            col.prop(self, "bake_anim_simplify_factor")
        else:
            layout.prop(self, "use_armature_deform_only")
            layout.prop(self, "use_anim")
            col = layout.column()
            col.enabled = self.use_anim
            col.prop(self, "use_anim_action_all")
            col.prop(self, "use_default_take")
            col.prop(self, "use_anim_optimize")
            col.prop(self, "anim_optimize_precision")

        layout.separator()
        layout.prop(self, "path_mode")
        if is_74bin:
            col = layout.column()
            col.enabled = (self.path_mode == 'COPY')
            col.prop(self, "embed_textures")
        layout.prop(self, "batch_mode")
        layout.prop(self, "use_batch_own_dir")

    @property
    def check_extension(self):
        return self.batch_mode == 'OFF'

    def execute(self, context):
        from mathutils import Matrix
        if not self.filepath:
            raise Exception("filepath not set")

        global_matrix = (Matrix.Scale(self.global_scale, 4) *
                         axis_conversion(to_forward=self.axis_forward,
                                         to_up=self.axis_up,
                                         ).to_4x4())

        keywords = self.as_keywords(ignore=("global_scale",
                                            "check_existing",
                                            "filter_glob",
                                            ))

        keywords["global_matrix"] = global_matrix

        if self.version == 'BIN7400':
            from . import export_fbx_bin
            return export_fbx_bin.save(self, context, **keywords)
        else:
            from . import export_fbx
            return export_fbx.save(self, context, **keywords)


def menu_func_import(self, context):
    self.layout.operator(ImportFBX.bl_idname, text="Autodesk FBX (.fbx)")


def menu_func_export(self, context):
    self.layout.operator(ExportFBX.bl_idname, text="Autodesk FBX (.fbx)")


def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_import.append(menu_func_import)
    bpy.types.INFO_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_import.remove(menu_func_import)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()
