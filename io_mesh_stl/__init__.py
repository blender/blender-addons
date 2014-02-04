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

# <pep8-80 compliant>

bl_info = {
    "name": "STL format",
    "author": "Guillaume Bouchard (Guillaum)",
    "version": (1, 0),
    "blender": (2, 57, 0),
    "location": "File > Import-Export > Stl",
    "description": "Import-Export STL files",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
        "Scripts/Import-Export/STL",
    "tracker_url": "https://developer.blender.org/T22837",
    "support": 'OFFICIAL',
    "category": "Import-Export"}


# @todo write the wiki page

"""
Import-Export STL files (binary or ascii)

- Import automatically remove the doubles.
- Export can export with/without modifiers applied

Issues:

Import:
    - Does not handle the normal of the triangles
    - Does not handle endien
"""

if "bpy" in locals():
    import imp
    if "stl_utils" in locals():
        imp.reload(stl_utils)
    if "blender_utils" in locals():
        imp.reload(blender_utils)

import os

import bpy
from bpy.props import (StringProperty,
                       BoolProperty,
                       CollectionProperty,
                       EnumProperty,
                       FloatProperty,
                       )
from bpy_extras.io_utils import (ImportHelper,
                                 ExportHelper,
                                 axis_conversion,
                                 )
from bpy.types import Operator, OperatorFileListElement


class ImportSTL(Operator, ImportHelper):
    """Load STL triangle mesh data"""
    bl_idname = "import_mesh.stl"
    bl_label = "Import STL"
    bl_options = {'UNDO'}

    filename_ext = ".stl"

    filter_glob = StringProperty(
            default="*.stl",
            options={'HIDDEN'},
            )
    files = CollectionProperty(
            name="File Path",
            type=OperatorFileListElement,
            )
    directory = StringProperty(
            subtype='DIR_PATH',
            )

    def execute(self, context):
        from . import stl_utils
        from . import blender_utils

        paths = [os.path.join(self.directory, name.name)
                 for name in self.files]

        if not paths:
            paths.append(self.filepath)

        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')

        if bpy.ops.object.select_all.poll():
            bpy.ops.object.select_all(action='DESELECT')

        for path in paths:
            objName = bpy.path.display_name(os.path.basename(path))
            tris, pts = stl_utils.read_stl(path)
            blender_utils.create_and_link_mesh(objName, tris, pts)

        return {'FINISHED'}


class ExportSTL(Operator, ExportHelper):
    """Save STL triangle mesh data from the active object"""
    bl_idname = "export_mesh.stl"
    bl_label = "Export STL"

    filename_ext = ".stl"
    filter_glob = StringProperty(default="*.stl", options={'HIDDEN'})

    ascii = BoolProperty(
            name="Ascii",
            description="Save the file in ASCII file format",
            default=False,
            )
    use_mesh_modifiers = BoolProperty(
            name="Apply Modifiers",
            description="Apply the modifiers before saving",
            default=True,
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
            default='Y',
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
            default='Z',
            )
    global_scale = FloatProperty(
            name="Scale",
            min=0.01, max=1000.0,
            default=1.0,
            )

    def execute(self, context):
        from . import stl_utils
        from . import blender_utils
        import itertools
        from mathutils import Matrix

        global_matrix = axis_conversion(to_forward=self.axis_forward,
                                        to_up=self.axis_up,
                                        ).to_4x4() * Matrix.Scale(self.global_scale, 4)

        faces = itertools.chain.from_iterable(
            blender_utils.faces_from_mesh(ob, global_matrix, self.use_mesh_modifiers)
            for ob in context.selected_objects)

        stl_utils.write_stl(self.filepath, faces, self.ascii)

        return {'FINISHED'}


def menu_import(self, context):
    self.layout.operator(ImportSTL.bl_idname, text="Stl (.stl)")


def menu_export(self, context):
    default_path = os.path.splitext(bpy.data.filepath)[0] + ".stl"
    self.layout.operator(ExportSTL.bl_idname, text="Stl (.stl)")


def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_import.append(menu_import)
    bpy.types.INFO_MT_file_export.append(menu_export)


def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_import.remove(menu_import)
    bpy.types.INFO_MT_file_export.remove(menu_export)


if __name__ == "__main__":
    register()
