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

'''
Import/Export STL files (binary or ascii)

- Import automatically remove the doubles.
- Export can export with/without modifiers applied

Issues:

Import:
    - Does not handle the normal of the triangles
    - Does not handle endien

Export:
    - Does not do the object space transformation
    - Export only one object (the selected one)
'''

bl_addon_info = {
    'name': 'I/O: STL',
    'author': 'Guillaume Bouchard (Guillaum)',
    'version': '1',
    'blender': (2, 5, 3),
    'location': 'File > Import/Export > Stl',
    'description': 'Import/Export Stl files',
     'wiki_url': 'http://wiki.blender.org/index.php/Extensions:2.5/Py/' \
        'Scripts/File I-O/STL',  # @todo write the page
    'category': 'Import/Export'}

import bpy
from bpy.props import *

from io_mesh_stl import stl_utils, blender_utils


class StlImporter(bpy.types.Operator):
    '''
    Load STL triangle mesh data
    '''
    bl_idname = "import_mesh.stl"
    bl_label = "Import STL"

    filepath = StringProperty(name="File Path",
                          description="File path used for importing "
                                      "the STL file",
                          maxlen=1024,
                          default="")
    filename = StringProperty(name="File Name",
                              description="Name of the file.")
    directory = StringProperty(name="Directory",
                               description="Directory of the file.")

    def execute(self, context):
        objName = bpy.utils.display_name(self.properties.filename)
        tris, pts = stl_utils.read_stl(self.properties.filepath)

        blender_utils.create_and_link_mesh(objName, tris, pts)

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.manager
        wm.add_fileselect(self)

        return {'RUNNING_MODAL'}


class StlExporter(bpy.types.Operator):
    '''
    Save STL triangle mesh data from the active object
    '''
    bl_idname = "export_mesh.stl"
    bl_label = "Export STL"

    filepath = StringProperty(name="File Path",
                          description="File path used for exporting "
                                      "the active object to STL file",
                          maxlen=1024,
                          default="")
    filename = StringProperty(name="File Name",
                              description="Name of the file.")
    directory = StringProperty(name="Directory",
                               description="Directory of the file.")
    check_existing = BoolProperty(name="Check Existing",
                                  description="Check and warn on "
                                              "overwriting existing files",
                                  default=True,
                                  options={'HIDDEN'})

    ascii = BoolProperty(name="Ascii",
                         description="Save the file in ASCII file format",
                         default=False)
    apply_modifiers = BoolProperty(name="Apply Modifiers",
                                   description="Apply the modifiers "
                                               "before saving",
                                   default=True)

    def execute(self, context):
        ob = context.active_object

        faces = blender_utils.faces_from_mesh(ob,
                                              self.properties.apply_modifiers)
        stl_utils.write_stl(self.properties.filepath, faces, self.properties.ascii)

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.manager
        wm.add_fileselect(self)
        return {'RUNNING_MODAL'}


def menu_import(self, context):
    self.layout.operator(StlImporter.bl_idname,
                         text="Stl (.stl)").filepath = "*.stl"


def menu_export(self, context):
    default_path = bpy.data.filepath.replace(".blend", ".stl")
    self.layout.operator(StlExporter.bl_idname,
                         text="Stl (.stl)").filepath = default_path


def register():
    bpy.types.register(StlImporter)
    bpy.types.register(StlExporter)
    bpy.types.INFO_MT_file_import.append(menu_import)
    bpy.types.INFO_MT_file_export.append(menu_export)


def unregister():
    bpy.types.unregister(StlImporter)
    bpy.types.unregister(StlExporter)
    bpy.types.INFO_MT_file_import.remove(menu_import)
    bpy.types.INFO_MT_file_export.remove(menu_export)


if __name__ == "__main__":
    register()
