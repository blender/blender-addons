# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****

bl_info = {
    "name": "Blend File Utils",
    "author": "Campbell Barton",
    "version": (0, 1),
    "blender": (2, 76, 0),
    "location": "File > External Data > Blend Utils",
    "description": "Utility for packing blend files",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Import-Export/BlendFile_Utils",
    "support": 'OFFICIAL',
    "category": "Import-Export",
    }


import bpy
from bpy.types import Operator
from bpy_extras.io_utils import ExportHelper

from .bl_utils.subprocess_helper import SubprocessHelper


class ExportBlendPack(Operator, ExportHelper, SubprocessHelper):
    """Packs a blend file and all its dependencies into an archive for easy redistribution"""
    bl_idname = "export_blend.pack"
    bl_label = "Pack Blend to Archive"

    # ExportHelper
    filename_ext = ".zip"

    # SubprocessHelper
    report_interval = 0.25

    temp_dir = None

    @classmethod
    def poll(cls, context):
        return bpy.data.is_saved

    def process_pre(self):
        import os
        import tempfile

        self.temp_dir = tempfile.TemporaryDirectory()

        filepath_blend = bpy.data.filepath

        self.command = (
            bpy.app.binary_path_python,
            os.path.join(os.path.dirname(__file__), "blendfile_pack.py"),
            # file to pack
            "--input", filepath_blend,
            # file to write
            "--output", bpy.path.ensure_ext(self.filepath, ".zip"),
            "--temp", self.temp_dir.name,
            )

    def process_post(self, returncode):
        if self.temp_dir is not None:
            try:
                self.temp_dir.cleanup()
            except:
                import traceback
                traceback.print_exc()


def menu_func(self, context):
    layout = self.layout
    layout.separator()
    layout.operator(ExportBlendPack.bl_idname)


classes = (
    ExportBlendPack,
    )


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.INFO_MT_file_external_data.append(menu_func)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.types.INFO_MT_file_external_data.remove(menu_func)


if __name__ == "__main__":
    register()
