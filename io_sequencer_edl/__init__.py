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
    "name": "Import EDL",
    "author": "Campbell Barton",
    "version": (1, 0),
    "blender": (2, 65, 0),
    "location": "Sequencer -> Track View Properties",
    "description": "Load a CMX formatted EDL into the sequencer",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:"
                "2.6/Py/Scripts/Import-Export/EDL_Import",
    "tracker_url": "",
    "category": "Import"}

import bpy


# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.props import (StringProperty,
                       IntProperty,
                       PointerProperty,
                       CollectionProperty,
                       )
from bpy.types import Operator

# ----------------------------------------------------------------------------
# Main Operators


class ReloadEDL(Operator):
    bl_idname = "sequencer.import_edl_refresh"
    bl_label = "Refresh Reels"

    def execute(self, context):
        import os
        from . import import_edl

        scene = context.scene
        edl_import_info = scene.edl_import_info

        filepath = edl_import_info.filepath
        dummy_fps = 25

        if not os.path.exists(filepath):
            self.report({'ERROR'}, "File Not Found %r" % filepath)
            return {'CANCELLED'}

        elist = import_edl.EditList()
        if not elist.parse(filepath, dummy_fps):
            self.report({'ERROR'}, "Failed to parse EDL %r" % filepath)
            return {'CANCELLED'}

        scene = context.scene
        edl_import_info = scene.edl_import_info
        bl_reels = edl_import_info.reels

        #scene[EDL_DATA_ID] = {}
        data_prev = {reel.name: (reel.filepath, reel.frame_offset)
                     for reel in edl_import_info.reels}

        reels = elist.getReels()
        reels = [k for k in reels.keys() if k != "bw"]

        # re-create reels collection, keeping old values
        bl_reels.clear()
        for k in sorted(reels):
            reel = bl_reels.add()
            reel.name = k
            filepath, frame_offset = data_prev.get(k, (None, None))
            if filepath is not None:
                reel.filepath = filepath
                reel.frame_offset = frame_offset

        return {'FINISHED'}


class ImportEDL(Operator):
    """Import an EDL into the sequencer"""
    bl_idname = "sequencer.import_edl"
    bl_label = "Import Video Sequence (.edl)"

    def execute(self, context):
        import os
        from . import import_edl
        scene = context.scene
        edl_import_info = scene.edl_import_info

        filepath = edl_import_info.filepath
        reel_filepaths = {reel.name: reel.filepath
                          for reel in edl_import_info.reels}
        reel_offsets = {reel.name: reel.frame_offset
                        for reel in edl_import_info.reels}

        if not os.path.exists(filepath):
            self.report({'ERROR'}, "File Not Found %r" % filepath)
            return {'CANCELLED'}

        msg = import_edl.load_edl(
                scene, filepath,
                reel_filepaths, reel_offsets)

        if msg:
            self.report({'WARNING'}, msg)

        return {'FINISHED'}


# ----------------------------------------------------------------------------
# Persistent Scene Data Types (store EDL import info)

class EDLReelInfo(bpy.types.PropertyGroup):
    name = StringProperty(
            name="Name",
            )
    filepath = StringProperty(
            name="Video File",
            subtype='FILE_PATH',
            )
    frame_offset = IntProperty(
            name="Frame Offset",
            )


class EDLImportInfo(bpy.types.PropertyGroup):
    filepath = StringProperty(
            subtype='FILE_PATH',
            )
    reels = bpy.props.CollectionProperty(
            type=EDLReelInfo,
            )


# ----------------------------------------------------------------------------
# Panel to show EDL Import UI


class SEQUENCER_PT_import_edl(bpy.types.Panel):
    bl_label = "EDL Import"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        edl_import_info = scene.edl_import_info

        layout.operator("sequencer.import_edl")

        col = layout.column(align=True)
        col.prop(edl_import_info, "filepath", text="")
        col.operator("sequencer.import_edl_refresh", icon='FILE_REFRESH')

        box = layout.box()
        reel = None
        for reel in scene.edl_import_info.reels:
            col = box.column(align=True)
            col.label(text=reel.name)
            col.prop(reel, "filepath", text="")
            col.prop(reel, "frame_offset")

        if reel is None:
            box.label("Empty (No EDL Data)")


def register():
    bpy.utils.register_class(ReloadEDL)
    bpy.utils.register_class(ImportEDL)
    bpy.utils.register_class(SEQUENCER_PT_import_edl)

    # edl_import_info
    bpy.utils.register_class(EDLReelInfo)
    bpy.utils.register_class(EDLImportInfo)
    bpy.types.Scene.edl_import_info = PointerProperty(type=EDLImportInfo)


def unregister():
    bpy.utils.unregister_class(ReloadEDL)
    bpy.utils.unregister_class(ImportEDL)
    bpy.utils.unregister_class(SEQUENCER_PT_import_edl)

    # edl_import_info
    bpy.utils.unregister_class(EDLImportInfo)
    bpy.utils.unregister_class(EDLReelInfo)
    del bpy.types.Scene.edl_import_info
