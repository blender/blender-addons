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
    "name": "Collada",
    "author": "Gaia Clary",
    "version": (1, 0),
    "blender": (2, 7, 8),
    "location": "File > Import/Export > Blender Collada",
    "description": "Import/Export Collada (Blender default Implementation)",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Dev:2.5/Source/Architecture/COLLADA",
    "tracker_url": "http://projects.blender.org/tracker/?atid=498&group_id=9&func=browse",
    "support": 'OFFICIAL',
    "category": "Import-Export",
}

import bpy
import os
import shutil

from bpy_extras.io_utils import (
        ImportHelper,
        ExportHelper
        )
from bpy.props import (
        StringProperty,
        BoolProperty,
        EnumProperty,
        IntProperty
        )

# Text strings

import_units_description = \
'''Specify the measurement units to be used in Blender:

- Disabled: match import to Blender's current Unit settings,
- Enabled: use the settings from the Imported scene'''
        
class ImportCollada(bpy.types.Operator, ImportHelper):
    '''Import as Collada-1.4.1'''
    bl_idname = "wm.collada_import"
    bl_label  = "Import Collada"
    bl_options = {'UNDO'}

    # ImportHelper mixin class uses this
    filename_ext = ".dae"

    filter_glob = StringProperty(
            default="*.dae",
            options={'HIDDEN'},
            )

    # Import data options

    import_units = BoolProperty(
            name        = "Import Units",
            description = import_units_description,
            default     = False
            )

    # Armature Options

    fix_orientation = BoolProperty(
            name        = "Fix Leaf Bones",
            description = "Fix Orientation of Leaf Bones (Collada does only support Joints)",
            default     = False
            )

    find_chains = BoolProperty(
            name        = "Find Bone Chains",
            description = "Find best matching Bone Chains and ensure bones in chain are connected",
            default     = False
            )

    auto_connect = BoolProperty(
            name        = "Auto Connect",
            description = "Set use_connect for parent bones which have exactly one child bone",
            default     = False
            )

    min_chain_length = IntProperty(
            name        = "Minimum Chain Length",
            description = "When searching Bone Chains disregard chains of length below this value",
            min         = 0,
            default     = 0
            )

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label("Import Data Options", icon='MESH_DATA')
        col = box.column()
        col.prop(self, 'import_units')
        
        box = layout.box()
        box.label("Armature Options", icon='ARMATURE_DATA')
        col = box.column()
        col.prop(self, 'fix_orientation')
        col.prop(self, 'find_chains')
        col.prop(self, 'auto_connect')
        col.prop(self, 'min_chain_length')
        
        
    def execute(self, context):
        return bpy.ops.wm.collada_importo(
            filepath         = self.filepath,
            import_units     = self.import_units,
            fix_orientation  = self.fix_orientation,
            find_chains      = self.find_chains,
            auto_connect     = self.auto_connect,
            min_chain_length = self.min_chain_length
        )
        


class ExportCollada(bpy.types.Operator, ExportHelper):
    '''Export as Collada-1.4.1'''
    bl_idname = "wm.collada_export"  # this is important since its how bpy.ops.export.some_data is constructed
    bl_label  = "Export Collada"
    bl_options = {'UNDO', 'PRESET'}

    # ExportHelper mixin class uses this
    filename_ext = ".dae"

    filter_glob = StringProperty(
            default="*.dae",
            options={'HIDDEN'},
            )

    # Export Data Options
    export_mesh_type = 0   #not used, only here to keep old presets compatible
    apply_modifiers = BoolProperty(
            name="Apply Modifiers",
            description="Apply modifiers to exported mesh (non destructive)",
            default=True
            )
    
    export_mesh_type_selection = EnumProperty(
            name="Apply Modifiers",
            items=(
                   ('view', "View",     "Apply modifier's View settings"),
                   ('render', "Render", "Apply modifier's Render settings"),
                   ),
            default = 'view'
            )

    selected = BoolProperty(
            name        = "Selection Only",
            description = "Export only selected elements",
            default     = True
            )

    include_children = BoolProperty(
            name        = "Include Children",
            description = "Export all children of selected objects (even if not selected)",
            default     = False
            )

    include_armatures = BoolProperty(
            name        = "Include Armatures",
            description = "Export related armatures (even if not selected)",
            default     = False
            )

    include_shapekeys = BoolProperty(
            name        = "Include Shape Keys",
            description = "Export all Shape Keys from Mesh Objects",
            default     = True
            )

    # Texture Options

    active_uv_only = BoolProperty(
            name        = "Only Selected UV Map",
            description = "Export only the selected UV Map",
            default     = False
            )

    include_uv_textures = BoolProperty(
            name        = "Include UV Textures",
            description = "Export textures assigned to the object UV Maps",
            default     = False
            )

    include_material_textures = BoolProperty(
            name        = "Include Material Textures",
            description = "Export textures assigned to the object Materials",
            default     = False
            )

    use_texture_copies = BoolProperty(
            name        = "Copy",
            description = "Copy textures to same folder where the .dae file is exported",
            default     = True
            )

    #Armature Options

    deform_bones_only = BoolProperty(
            name        = "Deform Bones only",
            description = "Only export deforming bones with armatures",
            default     = False
            )

    open_sim = BoolProperty(
            name        = "Export to SL/OpenSim",
            description = "Compatibility mode for SL, OpenSim and other compatible online worlds",
            default     = False
            )

    # Collada Options

    triangulate = BoolProperty(
            name        = "Triangulate",
            description = "Export Polygons (Quads & NGons) as Triangles",
            default     = False
            )

    use_object_instantiation = BoolProperty(
            name        = "Use Object Instances",
            description = "Instantiate multiple Objects from same Data",
            default     = False
            )

    use_blender_profile = BoolProperty(
            name        = "Use Blender Profile",
            description = "Export additional Blender specific information (for material, shaders, bones, etc.)",
            default     = False
            )

    export_transformation_type_selection = EnumProperty(
            name        = "Transformation Type",
            items=(
                   ('transrotloc', "View",   "use <translate>, <rotate>, <scale> to write transformations"),
                   ('matrix',      "Matrix", "use <matrix> to write transformations"),
                   ),
            default = 'matrix',
            description="Transformation type for translation, scale and rotation"
            )

    sort_by_name = BoolProperty(
            name        = "Sort by Object name",
            description = "Sort exported data by Object name",
            default     = False
            )

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label("Export Data Options", icon='MESH_DATA')

        col    = box.column()
        split  = col.split(percentage=0.6)
        split.prop(self, 'apply_modifiers')
        col=split.column()
        col.prop(self, 'export_mesh_type_selection', text='')
        col.enabled = self.apply_modifiers

        box.separator()

        col=box.column()
        col.prop(self, 'selected')
        col.prop(self, 'include_children')
        col.prop(self, 'include_armatures')
        col.prop(self, 'include_shapekeys')

        box = layout.box()
        box.label("Texture Options", icon='TEXTURE_DATA')

        col    = box.column()
        col.prop(self, 'active_uv_only')
        col.prop(self, 'include_uv_textures')
        col.prop(self, 'include_material_textures')
        col    = box.column()
        col.prop(self, 'use_texture_copies')
        
        box = layout.box()
        box.label("Armature Options", icon='ARMATURE_DATA')
        
        col    = box.column()
        col.prop(self, 'deform_bones_only')
        col.prop(self, 'open_sim')
        
        box = layout.box()
        box.label("Collada Options", icon='MODIFIER')
        
        col    = box.column()
        col.prop(self, 'triangulate')
        col.prop(self, 'use_object_instantiation')
        col.prop(self, 'use_blender_profile')
        split  = col.split(percentage=0.6)
        split.label('Transformation Type')
        split.prop(self, 'export_transformation_type_selection', text='')
        col.prop(self, 'sort_by_name')

    def execute(self, context):
        return bpy.ops.wm.collada_exporto(
            filepath                             = self.filepath,
            selected                             = self.selected,
            apply_modifiers                      = self.apply_modifiers,
            open_sim                             = self.open_sim,
            export_mesh_type_selection           = self.export_mesh_type_selection,
            include_children                     = self.include_children,
            include_armatures                    = self.include_armatures,
            include_shapekeys                    = self.include_shapekeys,
            active_uv_only                       = self.active_uv_only,
            include_uv_textures                  = self.include_uv_textures,
            include_material_textures            = self.include_material_textures,
            use_texture_copies                   = self.use_texture_copies,
            deform_bones_only                    = self.deform_bones_only,
            triangulate                          = self.triangulate,
            use_object_instantiation             = self.use_object_instantiation,
            use_blender_profile                  = self.use_blender_profile,
            export_transformation_type_selection = self.export_transformation_type_selection,
            sort_by_name                         = self.sort_by_name
        )

def menu_func_import(self, context):
    self.layout.operator(ImportCollada.bl_idname, text="Collada (.dae)")

    
def menu_func_export(self, context):
    self.layout.operator(ExportCollada.bl_idname, text="Collada (.dae)")

def copydir(src, dst):
    for root, dirs, files in os.walk(src):
        srcdir=root
        folder=srcdir[len(src):]
        dstdir=dst+folder
        if not os.path.exists(dstdir):
            os.makedirs(dstdir)
            
        for file in files:
            dstfile = os.path.join(dstdir,file)
            srcfile = os.path.join(srcdir,file)
            shutil.copyfile(srcfile, dstfile)

def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_export.prepend(menu_func_export)
    bpy.types.INFO_MT_file_import.prepend(menu_func_import)

    addon_home       = os.path.dirname(__file__)
    addon_presets    = os.path.join(addon_home, "presets")
    blender_scripts  = bpy.utils.user_resource('SCRIPTS', "presets")
    destdir          = os.path.join(blender_scripts, __name__)
    copydir(addon_presets, destdir)


def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_import.remove(menu_func_import)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()
