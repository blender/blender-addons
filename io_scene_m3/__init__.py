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

MAJOR_VERSION = 0
MINOR_VERSION = 2
BLENDER_VERSION = (2, 54, 0)
__version__ = "%d.%d.0" % (MAJOR_VERSION, MINOR_VERSION)
bl_info = {
    'name': 'Import: M3 (.m3)',
    'author': 'Cory Perry',
    'version': (0, 2, 0),
    'blender': (2, 5, 4),
    "api": 31878,
    "location": "File > Import",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/"\
        "Import-Export/M3_Import",
    "tracker_url": "http://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=24017",
    "category": "Import-Export",
    "description": "This script imports m3 format files to Blender."}

import bpy

try:
    init_data

    reload(import_m3)
    #reload(export_m3)
except:
    from io_mesh_m3 import import_m3
    #from io_mesh_m3 import export_m3

init_data = True


def menu_import(self, context):
    from io_mesh_m3 import import_m3
    self.layout.operator(import_m3.M3Importer.bl_idname, \
        text="Blizzard M3 (.m3)").filepath = "*.m3"


#def menu_export(self, context):
#    from io_mesh_raw import export_raw
#    import os
#    default_path = os.path.splitext(bpy.data.filepath)[0] + ".raw"
#    self.layout.operator(export_raw.RawExporter.bl_idname, \
#        text="Raw Faces (.raw)").filepath = default_path

def register():
    bpy.types.INFO_MT_file_import.append(menu_import)
#    bpy.types.INFO_MT_file_export.append(menu_export)


def unregister():
    bpy.types.INFO_MT_file_import.remove(menu_import)
#    bpy.types.INFO_MT_file_export.remove(menu_export)

if __name__ == "__main__":
    register()
