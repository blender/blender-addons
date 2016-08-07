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
from bpy.types import (
            Operator,
            Panel,
            )
import os


# -------------------------------- RENDER ALL SCENES ---------------------

def defRenderAll(frametype, scenes):

    activescene = bpy.context.scene
    FC = bpy.context.scene.frame_current
    FS = bpy.context.scene.frame_start
    FE = bpy.context.scene.frame_end
    print("---------------------")
    types = {'MESH', 'META', 'CURVE'}

    for ob in bpy.data.objects:
        if ob.type in types:
            if not len(ob.material_slots):
                ob.data.materials.append(None)

    slotlist = {ob: [sl.material for sl in ob.material_slots]
                for ob in bpy.data.objects if ob.type in types if len(ob.material_slots)}

    for scene in scenes:
        renpath = scene.render.filepath

        if frametype:
            scene.frame_start = FC
            scene.frame_end = FC
            scene.frame_end = FC
            scene.frame_start = FC

        filename = os.path.basename(bpy.data.filepath.rpartition(".")[0])
        uselayers = {layer: layer.use for layer in scene.render.layers}
        for layer, usado in uselayers.items():
            if usado:
                for i in scene.render.layers:
                    i.use = False
                layer.use = 1
                print("SCENE: %s" % scene.name)
                print("LAYER: %s" % layer.name)
                scene.render.filepath = os.path.join(
                    os.path.dirname(renpath), filename, scene.name, layer.name, "%s_%s_%s" %
                    (filename, scene.name, layer.name))
                bpy.context.window.screen.scene = scene
                bpy.ops.render.render(
                    animation=True,
                    write_still=True,
                    layer=layer.name,
                    scene=scene.name)
                print("DONE")
                print("---------------------")
        for layer, usado in uselayers.items():
            layer.use = usado
        scene.render.filepath = renpath
        for ob, slots in slotlist.items():
            ob.data.materials.clear()
            for slot in slots:
                ob.data.materials.append(slot)
        if frametype:
            scene.frame_start = FS
            scene.frame_end = FE
            scene.frame_end = FE
            scene.frame_start = FS

    bpy.context.window.screen.scene = activescene


class renderAll (Operator):
    bl_idname = "render.render_all_scenes_osc"
    bl_label = "Render All Scenes"

    frametype = bpy.props.BoolProperty(default=False)

    def execute(self, context):
        defRenderAll(self.frametype, [scene for scene in bpy.data.scenes])
        return {'FINISHED'}


# --------------------------------RENDER SELECTED SCENES------------------

class renderSelected (Operator):
    bl_idname = "render.render_selected_scenes_osc"
    bl_label = "Render Selected Scenes"

    frametype = bpy.props.BoolProperty(default=False)

    def execute(self, context):
        defRenderAll(
            self.frametype,
            [sc for sc in bpy.data.scenes if sc.oscurart.use_render_scene])
        return {'FINISHED'}


# --------------------------------RENDER CURRENT SCENE--------------------

class renderCurrent (Operator):
    bl_idname = "render.render_current_scene_osc"
    bl_label = "Render Current Scene"

    frametype = bpy.props.BoolProperty(default=False)

    def execute(self, context):

        defRenderAll(self.frametype, [bpy.context.scene])

        return {'FINISHED'}


# --------------------------RENDER CROP----------------------

def OscRenderCropFunc():

    SCENENAME = os.path.split(bpy.data.filepath)[-1].partition(".")[0]
    rcParts = bpy.context.scene.oscurart.rcPARTS
    # don't divide by zero
    PARTS = (rcParts if rcParts and rcParts > 0 else 1)
    CHUNKYSIZE = 1 / PARTS
    FILEPATH = bpy.context.scene.render.filepath
    bpy.context.scene.render.use_border = True
    bpy.context.scene.render.use_crop_to_border = True
    for PART in range(PARTS):
        bpy.context.scene.render.border_min_y = PART * CHUNKYSIZE
        bpy.context.scene.render.border_max_y = (
            PART * CHUNKYSIZE) + CHUNKYSIZE
        bpy.context.scene.render.filepath = "%s_part%s" % (
                                            os.path.join(FILEPATH,
                                                         SCENENAME,
                                                         bpy.context.scene.name,
                                                         SCENENAME),
                                            PART
                                            )
        bpy.ops.render.render(animation=False, write_still=True)

    bpy.context.scene.render.filepath = FILEPATH


class renderCrop (Operator):
    bl_idname = "render.render_crop_osc"
    bl_label = "Render Crop: Render!"

    def execute(self, context):
        OscRenderCropFunc()
        return {'FINISHED'}


# ---------------------------------- BROKEN FRAMES ---------------------

class SumaFile(Operator):
    bl_idname = "object.add_broken_file"
    bl_label = "Add Broken Files"

    def execute(self, context):
        os.chdir(os.path.dirname(bpy.data.filepath))
        absdir = os.path.join(
            os.path.dirname(bpy.data.filepath),
            bpy.context.scene.render.filepath.replace(r"//",
                                                      ""))
        for root, folder, files in os.walk(absdir):
            for f in files:
                if os.path.getsize(os.path.join(root, f)) < 10:
                    print(f)
                    i = bpy.context.scene.broken_files.add()
                    i.filename = f
                    i.fullpath = os.path.join(root, f)
                    i.value = os.path.getsize(os.path.join(root, f))
                    i.checkbox = True
        return {'FINISHED'}


class ClearFile(Operator):
    bl_idname = "object.clear_broken_file"
    bl_label = "Clear Broken Files"

    def execute(self, context):
        bpy.context.scene.broken_files.clear()
        return {'FINISHED'}


class DeleteFiles(Operator):
    bl_idname = "object.delete_broken_file"
    bl_label = "Delete Broken Files"

    def execute(self, context):
        for file in bpy.context.scene.broken_files:
            if file.checkbox:
                os.remove(file.fullpath)
        bpy.context.scene.broken_files.clear()
        return {'FINISHED'}


class BrokenFramesPanel(Panel):
    bl_label = "Oscurart Broken Render Files"
    bl_idname = "OBJECT_PT_osc_broken_files"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=1)

        for i in bpy.context.scene.broken_files:
            colrow = col.row(align=1)
            colrow.prop(i, "filename")
            colrow.prop(i, "value")
            colrow.prop(i, "checkbox")

        col = layout.column(align=1)
        colrow = col.row(align=1)
        colrow.operator("object.add_broken_file")
        colrow.operator("object.clear_broken_file")
        colrow = col.row(align=1)
        colrow.operator("object.delete_broken_file")


# --------------------------------COPY RENDER SETTINGS--------------------

def defCopyRenderSettings(mode):

    sc = bpy.context.scene
    sceneslist = bpy.data.scenes[:]
    sceneslist.remove(sc)

    excludes = {
        'name',
        'objects',
        'object_bases',
        'has_multiple_engines',
        'display_settings',
        'broken_files',
        'rna_type',
        'frame_subframe',
        'view_settings',
        'tool_settings',
        'render',
        'user_clear',
        'animation_data_create',
        'collada_export',
        'keying_sets',
        'icon_props',
        'image_settings',
        'library',
        'bake',
        'active_layer',
        'frame_current_final',
        'sequence_editor_clear',
        'rigidbody_world',
        'unit_settings',
        'orientations',
        '__slots__',
        'ray_cast',
        'sequencer_colorspace_settings',
        'ffmpeg',
        'is_movie_format',
        'frame_path',
        'frame_set',
        'network_render',
        'animation_data_clear',
        'is_nla_tweakmode',
        'keying_sets_all',
        'sequence_editor',
        '__doc__',
        'file_extension',
        'users',
        'node_tree',
        'is_updated_data',
        'bl_rna',
        'is_library_indirect',
        'cycles_curves',
        'timeline_markers',
        'statistics',
        'use_shading_nodes',
        'use_game_engine',
        'sequence_editor_create',
        'is_updated',
        '__module__',
        'update_tag',
        'update',
        'animation_data',
        'cycles',
        'copy',
        'game_settings',
        'layers',
        '__weakref__',
        'string',
        'double',
        'use_render_scene',
        'engine',
        'use_nodes',
        'world'}

    if mode == "render":
        scenerenderdict = {}
        scenedict = {}
        sceneimagesettingdict = {}
        for prop in dir(bpy.context.scene.render):
            if prop not in excludes:
                try:
                    scenerenderdict[prop] = getattr(
                        bpy.context.scene.render, prop)
                except:
                    print("%s does not exist." % (prop))

        for prop in dir(bpy.context.scene):
            if prop not in excludes:
                try:
                    scenedict[prop] = getattr(bpy.context.scene, prop)
                except:
                    print("%s does not exist." % (prop))

        for prop in dir(bpy.context.scene.render.image_settings):
            if prop not in excludes:
                try:
                    sceneimagesettingdict[prop] = getattr(
                        bpy.context.scene.render.image_settings,
                        prop)
                except:
                    print("%s does not exist." % (prop))

        # render
        for escena in sceneslist:
            for prop, value in scenerenderdict.items():
                try:
                    setattr(escena.render, prop, value)
                except:
                    print("%s was not copied!" % (prop))
                    pass
        # scene
        for escena in sceneslist:
            for prop, value in scenedict.items():
                try:
                    setattr(escena, prop, value)
                except:
                    print("%s was not copied!" % (prop))
                    pass
        # imageSettings
        for escena in sceneslist:
            for prop, value in sceneimagesettingdict.items():
                try:
                    setattr(escena.render.image_settings, prop, value)
                except:
                    print("%s was not copied!" % (prop))
                    pass

    if mode == "cycles":
        scenecyclesdict = {}
        for prop in dir(bpy.context.scene.cycles):
            if prop not in excludes:
                try:
                    scenecyclesdict[prop] = getattr(
                        bpy.context.scene.cycles, prop)
                except:
                    print("%s does not exist." % (prop))
        # cycles
        for escena in sceneslist:
            for prop, value in scenecyclesdict.items():
                try:
                    setattr(escena.cycles, prop, value)
                except:
                    print("%s was not copied!" % (prop))
                    pass


class copyRenderSettings(Operator):
    bl_idname = "render.copy_render_settings_osc"
    bl_label = "Copy Render Settings"

    mode = bpy.props.StringProperty(default="")

    def execute(self, context):

        defCopyRenderSettings(self.mode)

        return {'FINISHED'}
