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
    "name": "Import/Export: PDB format",
    "author": "Mariusz Maximus & Jong89",
    "version": (0, 9, 0),
    "blender": (2, 6, 0),
    "api": 35616,
    "location": "File > Import/Export > PDB",
    "description": "Import PDB files",
    "warning": "",
    "wiki_url": "http://blenderartists.org/forum/showthread.php?t=194336",
    "tracker_url": "http://blenderartists.org/forum/showthread.php?t=194336",
    "category": "Import-Export"}

# @todo write the wiki page

# To support reload properly, try to access a package var,
# if it's there, reload everything
if "bpy" in locals():
    import imp
    if "import_pdb" in locals():
        imp.reload(import_pdb)


import bpy
from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       )

from bpy_extras.io_utils import ImportHelper

class ImportPDB(bpy.types.Operator, ImportHelper):
    """Import from PDB file format (.pdb)"""
    bl_idname = 'import_scene.pdb'
    bl_label = 'Import PDB'
    bl_options= {'REGISTER', 'UNDO'}

    filename_ext = ".pdb"
    filter_glob = StringProperty(default="*.pdb", options={'HIDDEN'})

    filepath = StringProperty(
            name="File Path",
            description="Filepath used for importing the PDB file",
            maxlen= 1024,
            )
    multi_models = BoolProperty(
            name="Import all models",
            description="Import all alternative structures listed in file",
            default=False,
            )
    multimers = BoolProperty(
            name="Import Biomolecules",
            description="Import all file-listed biomolecules and multimers, "
                        "disable to import default biomolecule with all chains",
            default=False,
            )
    retain_alts = BoolProperty(
            name="Retain Alternative Atoms",
            description="Select to retain alternative atoms. "
                        "Some PDB files label coordinates of entries "
                        "in multiple models as alternates" ,
            default=False,
            )
    atom_subdivisions = IntProperty(
            name="Atom Subdivisions",
            description="Number of icosphere subdivisions for the atoms",
            min=1, max=6,
            default=3,
            )
    atom_size = FloatProperty(
            name="Atom Size",
            description="Multiplier for the van der Waals radius of the atoms",
            min=0, max=5,
            default=1,
            )
    scene_scale = FloatProperty(
            name="Scene Scale Factor",
            description="Number of Blender units equivalent to 1 angstrom",
            min=0, max=10,
            default=1,
            )

    def execute(self, context):
        from . import import_pdb
        import_pdb.load_pdb(self.filepath, context,
                            self.atom_size,
                            self.scene_scale,
                            self.atom_subdivisions,
                            self.retain_alts,
                            self.multi_models,
                            self.multimers)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

def menu_func(self, context):
    self.layout.operator(ImportPDB.bl_idname, text='Protein Databank (.pdb)')

def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_import.remove(menu_func)

if __name__ == '__main__':
    register()
