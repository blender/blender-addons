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
    'name': 'Import Blizzard M3 format (.m3)',
    'author': 'Cory Perry',
    'version': (0, 2, 1),
    "blender": (2, 5, 7),
    "api": 36079,
    'location': 'File > Import > Blizzard M3 (.m3)',
    'description': 'Imports the Blizzard M3 format (.m3)',
    'warning': '',
    'wiki_url': 'http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/'\
        'Import-Export/M3_Import',
    'tracker_url': 'http://projects.blender.org/tracker/index.php?'\
        'func=detail&aid=24017',
    'category': 'Import-Export'}


# To support reload properly, try to access a package var, if it's there,
# reload everything
if "bpy" in locals():
    import imp
    if 'import_m3' in locals():
        imp.reload(import_m3)
#   if 'export_m3' in locals():
#       imp.reload(export_m3)

import time
import datetime
import bpy
from bpy.props import StringProperty, BoolProperty
from bpy_extras.io_utils import ImportHelper


class ImportM3(bpy.types.Operator, ImportHelper):
    '''Import from M3 file format (.m3)'''
    bl_idname = 'import_scene.blizzard_m3'
    bl_label = 'Import M3'
    bl_options = {'UNDO'}

    filename_ext = '.m3'
    filter_glob = StringProperty(default='*.m3', options={'HIDDEN'})

    use_image_search = BoolProperty(name='Image Search',
                        description='Search subdirectories for any associated'\
                                    'images', default=True)

    def execute(self, context):
        from . import import_m3
        print('Importing file', self.filepath)
        t = time.mktime(datetime.datetime.now().timetuple())
        with open(self.filepath, 'rb') as file:
            import_m3.read(file, context, self)
        t = time.mktime(datetime.datetime.now().timetuple()) - t
        print('Finished importing in', t, 'seconds')
        return {'FINISHED'}


def menu_func_import(self, context):
    self.layout.operator(ImportM3.bl_idname, text='Blizzard M3 (.m3)')


#def menu_func_export(self, context):
#   self.layout.operator(ExportM3.bl_idname, text='Blizzard M3 (.m3)')


def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(menu_func_import)
#   bpy.types.INFO_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)
#   bpy.types.INFO_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()
