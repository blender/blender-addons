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

import bpy
from bpy.types import Operator


# ---------------------------RELOAD IMAGES------------------


class reloadImages (Operator):
    bl_idname = "image.reload_images_osc"
    bl_label = "Reload Images"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        for imgs in bpy.data.images:
            imgs.reload()
        return {'FINISHED'}


# ------------------------ SAVE INCREMENTAL ------------------------

class saveIncremental(Operator):
    bl_idname = "file.save_incremental_osc"
    bl_label = "Save Incremental File"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        filepath = bpy.data.filepath
        if filepath.count("_v"):
            strnum = filepath.rpartition("_v")[-1].rpartition(".blend")[0]
            intnum = int(strnum)
            modnum = strnum.replace(str(intnum), str(intnum + 1))
            output = filepath.replace(strnum, modnum)
            basename = os.path.basename(filepath)
            bpy.ops.wm.save_as_mainfile(
                filepath=os.path.join(os.path.dirname(filepath), "%s_v%s.blend" %
                                       (basename.rpartition("_v")[0], str(modnum))))

        else:
            output = filepath.rpartition(".blend")[0] + "_v01"
            bpy.ops.wm.save_as_mainfile(filepath=output)

        return {'FINISHED'}

# ------------------------ REPLACE FILE PATHS ------------------------

bpy.types.Scene.oscSearchText = bpy.props.StringProperty(default="Search Text")
bpy.types.Scene.oscReplaceText = bpy.props.StringProperty(
    default="Replace Text")


class replaceFilePath(Operator):
    bl_idname = "file.replace_file_path_osc"
    bl_label = "Replace File Path"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        TEXTSEARCH = bpy.context.scene.oscSearchText
        TEXTREPLACE = bpy.context.scene.oscReplaceText

        for image in bpy.data.images:
            image.filepath = image.filepath.replace(TEXTSEARCH, TEXTREPLACE)

        return {'FINISHED'}


# ---------------------- SYNC MISSING GROUPS --------------------------

class reFreshMissingGroups(Operator):
    bl_idname = "file.sync_missing_groups"
    bl_label = "Sync Missing Groups"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        for group in bpy.data.groups:
            if group.library is not None:
                with bpy.data.libraries.load(group.library.filepath, link=True) as (linked, local):
                    local.groups = linked.groups
        return {'FINISHED'}
