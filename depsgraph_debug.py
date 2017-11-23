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

import bpy
from bpy.types import (
        Operator,
        Panel,
        )
from bpy.props import (StringProperty, )

bl_info = {
    "name": "Dependency Graph Debug",
    "author": "Sergey Sharybin",
    "version": (0, 1),
    "blender": (2, 79, 0),
    "description": "Various dependency graph debugging tools",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Development"}


def _get_depsgraph(context):
    scene = context.scene
    if bpy.app.version < (2, 80, 0,):
        return scene.depsgraph
    else:
        scene_layer = scene.view_layers.active
        return scene_layer.depsgraph


class SCENE_OT_depsgraph_graphviz(Operator):
    bl_idname = "scene.depsgraph_graphviz"
    bl_label = "Save Depsgraph"
    bl_description = "Save current scene's dependency graph to a graphviz file"

    filepath = StringProperty(
            name="File Path",
            description="Filepath used for saving the file",
            maxlen=1024,
            subtype='FILE_PATH',
            )

    @classmethod
    def poll(cls, context):
        depsgraph = _get_depsgraph(context)
        return depsgraph is not None

    def invoke(self, context, event):
        import os
        if not self.filepath:
            blend_filepath = context.blend_data.filepath
            if not blend_filepath:
                blend_filepath = "deg"
            else:
                blend_filepath = os.path.splitext(blend_filepath)[0]

            self.filepath = blend_filepath + ".dot"

        context.window_manager.fileselect_add(self)

        return {'RUNNING_MODAL'}

    def execute(self, context):
        depsgraph = _get_depsgraph(context)
        depsgraph.debug_graphviz(self.filepath)
        return {'FINISHED'}


class SCENE_OT_depsgraph_image(Operator):
    bl_idname = "scene.depsgraph_image"
    bl_label = "Depsgraph as Image"
    bl_description = "Create new image datablock from the dependency graph"

    def _getOrCreateImageForAbsPath(self, filepath):
        for image in bpy.data.images:
            if image.filepath == filepath:
                image.reload()
                return image
        return bpy.data.images.load(filepath, check_existing=True)

    def _findBestImageEditor(self, context, image):
        first_none_editor = None
        for area in context.screen.areas:
            if area.type != 'IMAGE_EDITOR':
                continue
            for space in area.spaces:
                if space.type != 'IMAGE_EDITOR':
                    continue
                if not space.image:
                    first_none_editor = space
                else:
                    if space.image == image:
                        return space
        return first_none_editor

    def execute(self, context):
        import os
        import subprocess
        import tempfile
        # Create temporary file.
        fd, dot_filepath = tempfile.mkstemp(suffix=".dot")
        os.close(fd)
        # Save dependency graph to graphviz file.
        depsgraph = _get_depsgraph(context)
        depsgraph.debug_graphviz(dot_filepath)
        # Convert graphviz to PNG image.
        png_filepath = os.path.join(bpy.app.tempdir, "depsgraph.png")
        command = ("dot", "-Tpng", dot_filepath, "-o", png_filepath)
        image = None
        try:
            subprocess.run(command)
            # Open image in Blender.
            image = self._getOrCreateImageForAbsPath(png_filepath)
        except:
            self.report({'ERROR'}, "Error invoking dot command")
            return {'CANCELLED'}
        finally:
            # Remove graphviz file.
            os.remove(dot_filepath)
        editor = self._findBestImageEditor(context, image)
        if editor:
            editor.image = image
        return {'FINISHED'}


class SCENE_PT_depsgraph(bpy.types.Panel):
    bl_label = "Dependency Graph"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (2, 80, 0,):
            return False
        depsgraph = _get_depsgraph(context)
        return depsgraph is not None

    def draw(self, context):
        layout = self.layout
        layout.operator("scene.depsgraph_graphviz")
        layout.operator("scene.depsgraph_image")


class RENDERLAYER_PT_depsgraph(bpy.types.Panel):
    bl_label = "Dependency Graph"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "view_layer"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if bpy.app.version < (2, 80, 0,):
            return False
        depsgraph = _get_depsgraph(context)
        return depsgraph is not None

    def draw(self, context):
        layout = self.layout
        layout.operator("scene.depsgraph_graphviz")
        layout.operator("scene.depsgraph_image")


def register():
    bpy.utils.register_class(SCENE_OT_depsgraph_graphviz)
    bpy.utils.register_class(SCENE_OT_depsgraph_image)
    bpy.utils.register_class(SCENE_PT_depsgraph)
    bpy.utils.register_class(RENDERLAYER_PT_depsgraph)


def unregister():
    bpy.utils.unregister_class(SCENE_OT_depsgraph_graphviz)
    bpy.utils.unregister_class(SCENE_OT_depsgraph_image)
    bpy.utils.unregister_class(SCENE_PT_depsgraph)
    bpy.utils.unregister_class(RENDERLAYER_PT_depsgraph)


if __name__ == "__main__":
    register()
