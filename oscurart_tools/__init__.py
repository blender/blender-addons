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
    "name": "Oscurart Tools",
    "author": "Oscurart, CodemanX",
    "version": (3, 2),
    "blender": (2, 77, 0),
    "location": "View3D > Tools > Oscurart Tools",
    "description": "Tools for objects, render, shapes, and files.",
    "warning": "",
    "wiki_url":
        "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/3D_interaction/Oscurart_Tools",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "Object",
    }

import bpy
from bpy.types import (
            AddonPreferences,
            Panel,
            PropertyGroup,
            )

from bpy.props import (
            StringProperty,
            BoolProperty,
            IntProperty,
            )

from . import oscurart_files
from . import oscurart_meshes
from . import oscurart_objects
from . import oscurart_shapes
from . import oscurart_render
from . import oscurart_animation


class View3DOscPanel(PropertyGroup):
    # CREA PANELES EN TOOLS
    osc_object_tools = BoolProperty(default=True)
    osc_mesh_tools = BoolProperty(default=True)
    osc_shapes_tools = BoolProperty(default=True)
    osc_render_tools = BoolProperty(default=True)
    osc_files_tools = BoolProperty(default=True)
    osc_animation_tools = BoolProperty(default=True)

    quick_animation_in = IntProperty(
                        default=1
                        )
    quick_animation_out = IntProperty(
                        default=250
                        )
    # SETEO VARIABLE DE ENTORNO
    SearchAndSelectOt = StringProperty(
                        default="Object name initials"
                        )
    # RENDER CROP
    rcPARTS = IntProperty(
                        default=1,
                        min=2,
                        max=50,
                        step=1
                            )
    RenameObjectOt = StringProperty(
                        default="Type here"
                        )


class VarColArchivos(PropertyGroup):
    filename = bpy.props.StringProperty(
                        name="",
                        default=""
                        )
    value = bpy.props.IntProperty(
                        name="",
                        default=10
                        )
    fullpath = bpy.props.StringProperty(
                        name="",
                        default=""
                        )
    checkbox = bpy.props.BoolProperty(
                        name="",
                        default=True
                        )


# PANELES
class OscPanelControl(Panel):
    bl_idname = "Oscurart Panel Control"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Oscurart Tools"
    bl_label = "Panels Switcher"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        oscurart = scene.oscurart

        col = layout.column(align=1)
        col.prop(oscurart, "osc_object_tools", text="Object", icon="OBJECT_DATAMODE")
        col.prop(oscurart, "osc_mesh_tools", text="Mesh", icon="EDITMODE_HLT")
        col.prop(oscurart, "osc_shapes_tools", text="Shapes", icon="SHAPEKEY_DATA")
        col.prop(oscurart, "osc_animation_tools", text="Animation", icon="POSE_DATA")
        col.prop(oscurart, "osc_render_tools", text="Render", icon="SCENE")
        col.prop(oscurart, "osc_files_tools", text="Files", icon="IMASEL")


class OscPanelObject(Panel):
    bl_idname = "Oscurart Object Tools"
    bl_label = "Object Tools"
    bl_category = "Oscurart Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.oscurart.osc_object_tools

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=1)

        colrow = col.row(align=1)
        colrow.operator("object.relink_objects_between_scenes", icon="LINKED")
        colrow = col.row(align=1)
        colrow.operator("object.copy_objects_groups_layers", icon="LINKED")
        colrow.operator("object.set_layers_to_other_scenes", icon="LINKED")
        colrow = col.row(align=1)
        colrow.operator("object.objects_to_groups", icon="GROUP")
        colrow = col.row(align=1)
        colrow.prop(bpy.context.scene.oscurart, "SearchAndSelectOt", text="")
        colrow.operator("object.search_and_select_osc", icon="ZOOM_SELECTED")
        colrow = col.row(align=1)
        colrow.prop(bpy.context.scene.oscurart, "RenameObjectOt", text="")
        colrow.operator("object.rename_objects_osc", icon="SHORTDISPLAY")
        col.operator(
            "object.distribute_osc",
            icon="OBJECT_DATAMODE",
            text="Distribute")
        col.operator(
            "object.duplicate_object_symmetry_osc",
            icon="OUTLINER_OB_EMPTY",
            text="Duplicate Sym")
        colrow = col.row(align=1)
        colrow.operator(
            "object.modifiers_remove_osc",
            icon="MODIFIER",
            text="Remove Modifiers")
        colrow.operator(
            "object.modifiers_apply_osc",
            icon="MODIFIER",
            text="Apply Modifiers")
        colrow = col.row(align=1)
        colrow.operator(
            "group.group_in_out_camera",
            icon="RENDER_REGION",
            text="Make Groups in out Camera")


class OscPanelMesh(Panel):
    bl_idname = "Oscurart Mesh Tools"
    bl_label = "Mesh Tools"
    bl_category = "Oscurart Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.oscurart.osc_mesh_tools

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=1)

        col.operator("mesh.object_to_mesh_osc", icon="MESH_MONKEY")
        col.operator("mesh.select_side_osc", icon="VERTEXSEL")
        colrow = col.row(align=1)
        colrow.operator("mesh.resym_save_map", icon="UV_SYNC_SELECT")
        colrow = col.row(align=1)
        colrow.operator(
            "mesh.resym_mesh",
            icon="UV_SYNC_SELECT",
            text="Resym Mesh")
        colrow.operator("mesh.resym_vertex_weights_osc", icon="UV_SYNC_SELECT")
        colrow = col.row(align=1)
        colrow.operator("mesh.reconst_osc", icon="UV_SYNC_SELECT")
        colrow = col.row(align=1)
        colrow.operator("mesh.overlap_uv_faces", icon="UV_FACESEL")
        colrow = col.row(align=1)
        colrow.operator("view3d.modal_operator", icon="STICKY_UVS_DISABLE")
        colrow = col.row(align=1)
        colrow.operator("file.export_groups_osc", icon='GROUP_VCOL')
        colrow.operator("file.import_groups_osc", icon='GROUP_VCOL')
        colrow = col.row(align=1)
        colrow.operator("mesh.export_vertex_colors", icon='COLOR')
        colrow.operator("mesh.import_vertex_colors", icon='COLOR')


class OscPanelShapes(Panel):
    bl_idname = "Oscurart Shapes Tools"
    bl_label = "Shapes Tools"
    bl_category = "Oscurart Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.oscurart.osc_shapes_tools

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=1)

        col.operator("object.shape_key_to_objects_osc", icon="OBJECT_DATAMODE")
        col.operator("mesh.create_lmr_groups_osc", icon="GROUP_VERTEX")
        col.operator("mesh.split_lr_shapes_osc", icon="SHAPEKEY_DATA")
        colrow = col.row(align=1)
        colrow.operator("mesh.create_symmetrical_layout_osc", icon="SETTINGS")
        colrow.operator("mesh.create_asymmetrical_layout_osc", icon="SETTINGS")


class OscPanelRender(Panel):
    bl_idname = "Oscurart Render Tools"
    bl_label = "Render Tools"
    bl_category = "Oscurart Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.oscurart.osc_render_tools

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=1)

        colrow = col.row(align=1)
        colrow.operator(
            "render.copy_render_settings_osc",
            icon="LIBRARY_DATA_DIRECT",
            text="Copy Render Settings").mode = "render"
        colrow.operator(
            "render.copy_render_settings_osc",
            icon="LIBRARY_DATA_DIRECT",
            text="Copy Cycles Settings").mode = "cycles"
        colrow = col.row(align=1)
        colrow.operator(
            "render.render_all_scenes_osc",
            icon="RENDER_STILL",
            text="All Scenes").frametype = False
        colrow.operator(
            "render.render_all_scenes_osc",
            text="> Frame").frametype = True
        colrow = col.row(align=1)
        colrow.operator(
            "render.render_current_scene_osc",
            icon="RENDER_STILL",
            text="Active Scene").frametype = False
        colrow.operator(
            "render.render_current_scene_osc",
            text="> Frame").frametype = True

        colrow = col.row(align=1)
        colrow.operator("render.render_crop_osc", icon="RENDER_REGION")
        colrow.prop(bpy.context.scene.oscurart, "rcPARTS", text="Parts")

        boxcol = layout.box().column(align=1)
        colrow = boxcol.row(align=1)
        colrow.operator(
            "render.render_selected_scenes_osc",
            icon="RENDER_STILL",
            text="Selected Scenes").frametype = False
        colrow.operator(
            "render.render_selected_scenes_osc",
            text="> Frame").frametype = True

        for sc in bpy.data.scenes[:]:
            boxcol.prop(sc, "use_render_scene", text=sc.name)


class OscPanelFiles(Panel):
    bl_idname = "Oscurart Files Tools"
    bl_label = "Files Tools"
    bl_category = "Oscurart Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.oscurart.osc_files_tools

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=1)
        col.operator("image.reload_images_osc", icon="IMAGE_COL")
        col.operator("file.sync_missing_groups", icon="LINK_AREA")


class OscPanelAnimation(Panel):
    bl_idname = "Oscurart Animation Tools"
    bl_label = "Animation Tools"
    bl_category = "Oscurart Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.oscurart.osc_animation_tools

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=1)
        row = col.row()

        col.operator("anim.quick_parent_osc", icon="OUTLINER_DATA_POSE")
        row = col.row(align=1)
        row.prop(bpy.context.scene.oscurart, "quick_animation_in", text="")
        row.prop(bpy.context.scene.oscurart, "quick_animation_out", text="")


class OscurartToolsAddonPreferences(bpy.types.AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    category = StringProperty(
            name="Category",
            description="Choose a name for the category of the panel",
            default="Oscurart Tools",
            )

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        col = row.column()
        col.label(text="Category:")
        col.prop(self, "category", text="")

# ========================= FIN DE SCRIPTS =========================


def register():
    bpy.utils.register_module(__name__)

    bpy.types.Scene.oscurart = bpy.props.PointerProperty(
                                        type=View3DOscPanel
                                        )
    bpy.types.Scene.use_render_scene = bpy.props.BoolProperty()

    bpy.types.Scene.broken_files = bpy.props.CollectionProperty(
                                        type=VarColArchivos
                                        )


def unregister():
    del bpy.types.Scene.oscurart
    del bpy.types.Scene.use_render_scene
    del bpy.types.Scene.broken_files

    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
