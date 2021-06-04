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

if "bpy" in locals():
    import importlib
    importlib.reload(io)
else:
    from . import io

import bpy
from bpy.types import (
    Gizmo,
    GizmoGroup,
    PropertyGroup,
    UIList,
    Menu,
    Panel,
    Operator,
)
from bpy.app.handlers import persistent
from bpy_extras.io_utils import ImportHelper, ExportHelper
import bgl
import math
from math import radians
from mathutils import Matrix, Euler
import os.path, importlib.util


### Session.
class VIEW3D_PT_vr_session(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VR"
    bl_label = "VR Session"

    def draw(self, context):
        layout = self.layout
        session_settings = context.window_manager.xr_session_settings

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        is_session_running = bpy.types.XrSessionState.is_running(context)

        # Using SNAP_FACE because it looks like a stop icon -- I shouldn't
        # have commit rights...
        toggle_info = (
            ("Start VR Session", 'PLAY') if not is_session_running else (
                "Stop VR Session", 'SNAP_FACE')
        )
        layout.operator("wm.xr_session_toggle",
                        text=toggle_info[0], icon=toggle_info[1])

        layout.separator()

        layout.prop(session_settings, "use_positional_tracking")
        layout.prop(session_settings, "use_absolute_tracking")


### View.
class VIEW3D_PT_vr_session_view(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VR"
    bl_label = "View"

    def draw(self, context):
        layout = self.layout
        session_settings = context.window_manager.xr_session_settings

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        col = layout.column(align=True, heading="Show")
        col.prop(session_settings, "show_floor", text="Floor")
        col.prop(session_settings, "show_annotation", text="Annotations")
        col.prop(session_settings, "show_controllers", text="Controllers")
        col.prop(session_settings, "show_custom_overlays", text="Custom Overlays")
        col.prop(session_settings, "show_selection", text="Selection")

        col = layout.column(align=True)
        col.prop(session_settings, "controller_draw_style", text="Controller Style")

        col = layout.column(align=True)
        col.prop(session_settings, "selection_eye", text="Selection Eye")

        col = layout.column(align=True)
        col.prop(session_settings, "clip_start", text="Clip Start")
        col.prop(session_settings, "clip_end", text="End")


### Landmarks.
@persistent
def vr_ensure_default_landmark(context: bpy.context):
    # Ensure there's a default landmark (scene camera by default).
    landmarks = bpy.context.scene.vr_landmarks
    if not landmarks:
        landmarks.add()
        landmarks[0].type = 'SCENE_CAMERA'


def vr_landmark_active_type_update(self, context):
    wm = context.window_manager
    session_settings = wm.xr_session_settings
    landmark_active = VRLandmark.get_active_landmark(context)

    # Update session's base pose type to the matching type.
    if landmark_active.type == 'SCENE_CAMERA':
        session_settings.base_pose_type = 'SCENE_CAMERA'
    elif landmark_active.type == 'OBJECT':
        session_settings.base_pose_type = 'OBJECT'
    elif landmark_active.type == 'CUSTOM':
        session_settings.base_pose_type = 'CUSTOM'


def vr_landmark_active_base_pose_object_update(self, context):
    session_settings = context.window_manager.xr_session_settings
    landmark_active = VRLandmark.get_active_landmark(context)

    # Update the anchor object to the (new) camera of this landmark.
    session_settings.base_pose_object = landmark_active.base_pose_object


def vr_landmark_active_base_pose_location_update(self, context):
    session_settings = context.window_manager.xr_session_settings
    landmark_active = VRLandmark.get_active_landmark(context)

    session_settings.base_pose_location = landmark_active.base_pose_location


def vr_landmark_active_base_pose_angle_update(self, context):
    session_settings = context.window_manager.xr_session_settings
    landmark_active = VRLandmark.get_active_landmark(context)

    session_settings.base_pose_angle = landmark_active.base_pose_angle


def vr_landmark_active_base_scale_update(self, context):
    session_settings = context.window_manager.xr_session_settings
    landmark_active = VRLandmark.get_active_landmark(context)

    session_settings.base_scale = landmark_active.base_scale


def vr_landmark_type_update(self, context):
    landmark_selected = VRLandmark.get_selected_landmark(context)
    landmark_active = VRLandmark.get_active_landmark(context)

    # Only update session settings data if the changed landmark is actually
    # the active one.
    if landmark_active == landmark_selected:
        vr_landmark_active_type_update(self, context)


def vr_landmark_base_pose_object_update(self, context):
    landmark_selected = VRLandmark.get_selected_landmark(context)
    landmark_active = VRLandmark.get_active_landmark(context)

    # Only update session settings data if the changed landmark is actually
    # the active one.
    if landmark_active == landmark_selected:
        vr_landmark_active_base_pose_object_update(self, context)


def vr_landmark_base_pose_location_update(self, context):
    landmark_selected = VRLandmark.get_selected_landmark(context)
    landmark_active = VRLandmark.get_active_landmark(context)

    # Only update session settings data if the changed landmark is actually
    # the active one.
    if landmark_active == landmark_selected:
        vr_landmark_active_base_pose_location_update(self, context)


def vr_landmark_base_pose_angle_update(self, context):
    landmark_selected = VRLandmark.get_selected_landmark(context)
    landmark_active = VRLandmark.get_active_landmark(context)

    # Only update session settings data if the changed landmark is actually
    # the active one.
    if landmark_active == landmark_selected:
        vr_landmark_active_base_pose_angle_update(self, context)


def vr_landmark_base_scale_update(self, context):
    landmark_selected = VRLandmark.get_selected_landmark(context)
    landmark_active = VRLandmark.get_active_landmark(context)

    # Only update session settings data if the changed landmark is actually
    # the active one.
    if landmark_active == landmark_selected:
        vr_landmark_active_base_scale_update(self, context)


def vr_landmark_active_update(self, context):
    wm = context.window_manager

    vr_landmark_active_type_update(self, context)
    vr_landmark_active_base_pose_object_update(self, context)
    vr_landmark_active_base_pose_location_update(self, context)
    vr_landmark_active_base_pose_angle_update(self, context)
    vr_landmark_active_base_scale_update(self, context)

    if wm.xr_session_state:
        wm.xr_session_state.reset_to_base_pose(context)


class VIEW3D_MT_vr_landmark_menu(Menu):
    bl_label = "Landmark Controls"

    def draw(self, _context):
        layout = self.layout

        layout.operator("view3d.vr_landmark_from_camera")
        layout.operator("view3d.update_vr_landmark")
        layout.separator()
        layout.operator("view3d.cursor_to_vr_landmark")
        layout.operator("view3d.camera_to_vr_landmark")
        layout.operator("view3d.add_camera_from_vr_landmark")


class VRLandmark(PropertyGroup):
    name: bpy.props.StringProperty(
        name="VR Landmark",
        default="Landmark"
    )
    type: bpy.props.EnumProperty(
        name="Type",
        items=[
            ('SCENE_CAMERA', "Scene Camera",
             "Use scene's currently active camera to define the VR view base "
             "location and rotation"),
            ('OBJECT', "Custom Object",
             "Use an existing object to define the VR view base location and "
             "rotation"),
            ('CUSTOM', "Custom Pose",
             "Allow a manually defined position and rotation to be used as "
             "the VR view base pose"),
        ],
        default='SCENE_CAMERA',
        update=vr_landmark_type_update,
    )
    base_pose_object: bpy.props.PointerProperty(
        name="Object",
        type=bpy.types.Object,
        update=vr_landmark_base_pose_object_update,
    )
    base_pose_location: bpy.props.FloatVectorProperty(
        name="Base Pose Location",
        subtype='TRANSLATION',
        update=vr_landmark_base_pose_location_update,
    )
    base_pose_angle: bpy.props.FloatProperty(
        name="Base Pose Angle",
        subtype='ANGLE',
        update=vr_landmark_base_pose_angle_update,
    )
    base_scale: bpy.props.FloatProperty(
        name="Base Scale",
        default=1.0,
        min=0.001,
        max=1000.0,
        soft_min=0.001,
        soft_max=1000.0,
        update=vr_landmark_base_scale_update,
    )

    @staticmethod
    def get_selected_landmark(context):
        scene = context.scene
        landmarks = scene.vr_landmarks

        return (
            None if (len(landmarks) <
                     1) else landmarks[scene.vr_landmarks_selected]
        )

    @staticmethod
    def get_active_landmark(context):
        scene = context.scene
        landmarks = scene.vr_landmarks

        return (
            None if (len(landmarks) <
                     1) else landmarks[scene.vr_landmarks_active]
        )


class VIEW3D_UL_vr_landmarks(UIList):
    def draw_item(self, context, layout, _data, item, icon, _active_data,
                  _active_propname, index):
        landmark = item
        landmark_active_idx = context.scene.vr_landmarks_active

        layout.emboss = 'NONE'

        layout.prop(landmark, "name", text="")

        icon = (
            'RADIOBUT_ON' if (index == landmark_active_idx) else 'RADIOBUT_OFF'
        )
        props = layout.operator(
            "view3d.vr_landmark_activate", text="", icon=icon)
        props.index = index


class VIEW3D_PT_vr_landmarks(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VR"
    bl_label = "Landmarks"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        landmark_selected = VRLandmark.get_selected_landmark(context)

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        row = layout.row()

        row.template_list("VIEW3D_UL_vr_landmarks", "", scene, "vr_landmarks",
                          scene, "vr_landmarks_selected", rows=3)

        col = row.column(align=True)
        col.operator("view3d.vr_landmark_add", icon='ADD', text="")
        col.operator("view3d.vr_landmark_remove", icon='REMOVE', text="")
        col.operator("view3d.vr_landmark_from_session", icon='PLUS', text="")

        col.menu("VIEW3D_MT_vr_landmark_menu", icon='DOWNARROW_HLT', text="")

        if landmark_selected:
            layout.prop(landmark_selected, "type")

            if landmark_selected.type == 'OBJECT':
                layout.prop(landmark_selected, "base_pose_object")
                layout.prop(landmark_selected, "base_scale", text="Scale")
            elif landmark_selected.type == 'CUSTOM':
                layout.prop(landmark_selected,
                            "base_pose_location", text="Location")
                layout.prop(landmark_selected,
                            "base_pose_angle", text="Angle")
                layout.prop(landmark_selected,
                            "base_scale", text="Scale")


class VIEW3D_OT_vr_landmark_add(Operator):
    bl_idname = "view3d.vr_landmark_add"
    bl_label = "Add VR Landmark"
    bl_description = "Add a new VR landmark to the list and select it"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        scene = context.scene
        landmarks = scene.vr_landmarks

        landmarks.add()

        # select newly created set
        scene.vr_landmarks_selected = len(landmarks) - 1

        return {'FINISHED'}


class VIEW3D_OT_vr_landmark_from_camera(Operator):
    bl_idname = "view3d.vr_landmark_from_camera"
    bl_label = "Add VR Landmark from Camera"
    bl_description = "Add a new VR landmark from the active camera object to the list and select it"
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        cam_selected = False

        vl_objects = bpy.context.view_layer.objects
        if vl_objects.active and vl_objects.active.type == 'CAMERA':
            cam_selected = True
        return cam_selected

    def execute(self, context):
        scene = context.scene
        landmarks = scene.vr_landmarks
        cam = context.view_layer.objects.active
        lm = landmarks.add()
        lm.type = 'OBJECT'
        lm.base_pose_object = cam
        lm.name = "LM_" + cam.name

        # select newly created set
        scene.vr_landmarks_selected = len(landmarks) - 1

        return {'FINISHED'}


class VIEW3D_OT_vr_landmark_from_session(Operator):
    bl_idname = "view3d.vr_landmark_from_session"
    bl_label = "Add VR Landmark from Session"
    bl_description = "Add VR landmark from the viewer pose of the running VR session to the list and select it"
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        return bpy.types.XrSessionState.is_running(context)

    def execute(self, context):
        scene = context.scene
        landmarks = scene.vr_landmarks
        wm = context.window_manager

        lm = landmarks.add()
        lm.type = "CUSTOM"
        scene.vr_landmarks_selected = len(landmarks) - 1

        loc = wm.xr_session_state.viewer_pose_location
        rot = wm.xr_session_state.viewer_pose_rotation.to_euler()

        lm.base_pose_location = loc
        lm.base_pose_angle = rot[2]

        return {'FINISHED'}


class VIEW3D_OT_update_vr_landmark(Operator):
    bl_idname = "view3d.update_vr_landmark"
    bl_label = "Update Custom VR Landmark"
    bl_description = "Update the selected landmark from the current viewer pose in the VR session"
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        selected_landmark = VRLandmark.get_selected_landmark(context)
        return bpy.types.XrSessionState.is_running(context) and selected_landmark.type == 'CUSTOM'

    def execute(self, context):
        wm = context.window_manager

        lm = VRLandmark.get_selected_landmark(context)

        loc = wm.xr_session_state.viewer_pose_location
        rot = wm.xr_session_state.viewer_pose_rotation.to_euler()

        lm.base_pose_location = loc
        lm.base_pose_angle = rot

        # Re-activate the landmark to trigger viewer reset and flush landmark settings to the session settings.
        vr_landmark_active_update(None, context)

        return {'FINISHED'}


class VIEW3D_OT_vr_landmark_remove(Operator):
    bl_idname = "view3d.vr_landmark_remove"
    bl_label = "Remove VR Landmark"
    bl_description = "Delete the selected VR landmark from the list"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        scene = context.scene
        landmarks = scene.vr_landmarks

        if len(landmarks) > 1:
            landmark_selected_idx = scene.vr_landmarks_selected
            landmarks.remove(landmark_selected_idx)

            scene.vr_landmarks_selected -= 1

        return {'FINISHED'}


class VIEW3D_OT_cursor_to_vr_landmark(Operator):
    bl_idname = "view3d.cursor_to_vr_landmark"
    bl_label = "Cursor to VR Landmark"
    bl_description = "Move the 3D Cursor to the selected VR Landmark"
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        lm = VRLandmark.get_selected_landmark(context)
        if lm.type == 'SCENE_CAMERA':
            return context.scene.camera is not None
        elif lm.type == 'OBJECT':
            return lm.base_pose_object is not None

        return True

    def execute(self, context):
        scene = context.scene
        lm = VRLandmark.get_selected_landmark(context)
        if lm.type == 'SCENE_CAMERA':
            lm_pos = scene.camera.location
        elif lm.type == 'OBJECT':
            lm_pos = lm.base_pose_object.location
        else:
            lm_pos = lm.base_pose_location
        scene.cursor.location = lm_pos

        return{'FINISHED'}


class VIEW3D_OT_add_camera_from_vr_landmark(Operator):
    bl_idname = "view3d.add_camera_from_vr_landmark"
    bl_label = "New Camera from VR Landmark"
    bl_description = "Create a new Camera from the selected VR Landmark"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        scene = context.scene
        lm = VRLandmark.get_selected_landmark(context)

        cam = bpy.data.cameras.new("Camera_" + lm.name)
        new_cam = bpy.data.objects.new("Camera_" + lm.name, cam)
        scene.collection.objects.link(new_cam)
        angle = lm.base_pose_angle
        new_cam.location = lm.base_pose_location
        new_cam.rotation_euler = (math.pi, 0, angle)

        return {'FINISHED'}


class VIEW3D_OT_camera_to_vr_landmark(Operator):
    bl_idname = "view3d.camera_to_vr_landmark"
    bl_label = "Scene Camera to VR Landmark"
    bl_description = "Position the scene camera at the selected landmark"
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.scene.camera is not None

    def execute(self, context):
        scene = context.scene
        lm = VRLandmark.get_selected_landmark(context)

        cam = scene.camera
        angle = lm.base_pose_angle
        cam.location = lm.base_pose_location
        cam.rotation_euler = (math.pi / 2, 0, angle)

        return {'FINISHED'}


class VIEW3D_OT_vr_landmark_activate(Operator):
    bl_idname = "view3d.vr_landmark_activate"
    bl_label = "Activate VR Landmark"
    bl_description = "Change to the selected VR landmark from the list"
    bl_options = {'UNDO', 'REGISTER'}

    index: bpy.props.IntProperty(
        name="Index",
        options={'HIDDEN'},
    )

    def execute(self, context):
        scene = context.scene

        if self.index >= len(scene.vr_landmarks):
            return {'CANCELLED'}

        scene.vr_landmarks_active = (
            self.index if self.properties.is_property_set(
                "index") else scene.vr_landmarks_selected
        )

        return {'FINISHED'}


### Actions.
def vr_actionconfig_active_get(context):
    if not context.window_manager.xr_session_settings.actionconfigs:
        return None
    return context.window_manager.xr_session_settings.actionconfigs.active


def vr_actionmap_selected_get(ac):
    actionmaps = ac.actionmaps
    return (
        None if (len(actionmaps) <
                 1) else actionmaps[ac.selected_actionmap]
    )


def vr_actionmap_active_get(ac):
    actionmaps = ac.actionmaps
    return (
        None if (len(actionmaps) <
                 1) else actionmaps[ac.active_actionmap]
    )


def vr_actionmap_item_selected_get(am):
    actionmap_items = am.actionmap_items
    return (
        None if (len(actionmap_items) <
                 1) else actionmap_items[am.selected_item]
    )


@persistent
def vr_activate_user_actionconfig(context: bpy.context):
    # Set user config as active.
    actionconfigs = bpy.context.window_manager.xr_session_settings.actionconfigs
    if actionconfigs:
        actionconfigs.active = actionconfigs.user


@persistent
def vr_create_actions(context: bpy.context):
    # Create all vr action sets and actions.
    context = bpy.context

    ac = vr_actionconfig_active_get(context)
    if not ac:
        return

    session_state = context.window_manager.xr_session_state
    if not session_state:
        return

    for am in ac.actionmaps:    
        if len(am.actionmap_items) < 1:
            continue

        ok = session_state.create_action_set(context, am.name)
        if not ok:
            return

        interaction_path0 = ""
        interaction_path1 = ""

        for ami in am.actionmap_items:
            ok = session_state.create_action(context, am.name, ami.name, ami.type,
                                             ami.user_path0, ami.user_path1, ami.threshold, ami.op, ami.op_flag)
            if not ok:
                return

            if ami.type == 'POSE':
                ok = session_state.create_action_space(context, am.name, ami.name,
                                                       ami.user_path0, ami.user_path1,
                                                       ami.pose_location, ami.pose_rotation)
                if not ok:
                    return
                
                if ami.pose_is_controller:
                    ok = session_state.set_controller_pose_action(context, am.name, ami.name)
                    if not ok:
                        return

            interaction_path0 = ami.user_path0 + ami.component_path0
            interaction_path1 = ami.user_path1 + ami.component_path1

            ok = session_state.create_action_binding(context, am.name, am.profile, ami.name,
                                                     interaction_path0, interaction_path1)
            if not ok:
                return

    # Set active action set.
    am = vr_actionmap_active_get(ac)
    if am:
        session_state.set_active_action_set(context, am.name)


def vr_load_actionmaps(context, filepath):
    # Import all actionmaps for active actionconfig.
    actionconfigs = context.window_manager.xr_session_settings.actionconfigs
    if not actionconfigs:
        return False
    ac = actionconfigs.active
    if not ac:
        return False

    if not os.path.exists(filepath):
        return False

    spec = importlib.util.spec_from_file_location(os.path.basename(filepath), filepath)
    file = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(file)

    io.actionconfig_init_from_data(ac, file.actionconfig_data, file.actionconfig_version)

    return True


def vr_save_actionmaps(context, filepath, sort=False):
    # Export all actionmaps for active actionconfig.
    actionconfigs = context.window_manager.xr_session_settings.actionconfigs
    if not actionconfigs:
        return False
    ac = actionconfigs.active
    if not ac:
        return False

    io.actionconfig_export_as_data(ac, filepath, sort=sort)

    print("Saved XR actionmaps: " + filepath)
    
    return True


def vr_get_default_config_path():
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs")
    return os.path.join(filepath, "default.py")


def vr_draw_ami(ami, layout, level):
    # Similar to draw_kmi() from rna_keymap_ui.py.
    indentpx = 16
    if level == 0:
        level = 0.0001
    indent = level * indentpx / bpy.context.region.width

    split = layout.split(factor=indent)
    col = split.column()
    col = split.column()

    if ami.op:
        col = col.column(align=True)
        box = col.box()
    else:
        box = col.column()

    split = box.split()

    # Header bar.
    row = split.row(align=True)
    #row.prop(ami, "show_expanded", text="", emboss=False)

    row.label(text="Operator Properties")
    row.label(text=ami.op_name)

    # Expanded, additional event settings.
    if ami.op:
        box = col.box()
        
        # Operator properties.
        box.template_xr_actionmap_item_properties(ami)


class VIEW3D_UL_vr_actionmaps(UIList):
    def draw_item(self, context, layout, _data, item, icon, _active_data,
                  _active_propname, index):
        ac = vr_actionconfig_active_get(context)
        if not ac:
            return

        am_active_idx = ac.active_actionmap
        am = item

        layout.emboss = 'NONE'

        layout.prop(am, "name", text="")

        icon = (
            'RADIOBUT_ON' if (index == am_active_idx) else 'RADIOBUT_OFF'
        )
        props = layout.operator(
            "view3d.vr_actionmap_activate", text="", icon=icon)
        props.index = index


class VIEW3D_MT_vr_actionmap_menu(Menu):
    bl_label = "Action Map Controls"

    def draw(self, _context):
        layout = self.layout

        layout.operator("view3d.vr_actionmaps_defaults_load")
        layout.operator("view3d.vr_actionmaps_import")
        layout.operator("view3d.vr_actionmaps_export")
        layout.operator("view3d.vr_actionmap_copy")
        layout.operator("view3d.vr_actionmaps_clear")


class VIEW3D_UL_vr_actions(UIList):
    def draw_item(self, context, layout, _data, item, icon, _active_data,
                  _active_propname, index):
        action = item

        layout.emboss = 'NONE'

        layout.prop(action, "name", text="")


class VIEW3D_MT_vr_action_menu(Menu):
    bl_label = "Action Controls"

    def draw(self, _context):
        layout = self.layout

        layout.operator("view3d.vr_action_copy")
        layout.operator("view3d.vr_actions_clear")


class VIEW3D_PT_vr_actions(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VR"
    bl_label = "Actions"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        ac = vr_actionconfig_active_get(context)
        if not ac:
            return
        
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        row0 = layout.row()
        col = row0.column(align=True)
        col.label(text="Action Maps")

        row1 = layout.row()
        row1.template_list("VIEW3D_UL_vr_actionmaps", "", ac, "actionmaps",
                           ac, "selected_actionmap", rows=3)

        col = row1.column(align=True)
        col.operator("view3d.vr_actionmap_add", icon='ADD', text="")
        col.operator("view3d.vr_actionmap_remove", icon='REMOVE', text="")

        col.menu("VIEW3D_MT_vr_actionmap_menu", icon='DOWNARROW_HLT', text="")

        am = vr_actionmap_selected_get(ac)
        
        if am:
            row = row0.split()
            col = row.column(align=True)
            col.label(text="Actions")

            row = layout.row()
            col0 = row.column(align=True)
            row = row.split()
            col1 = row.column(align=True)

            col0.prop(am, "name", text="Action Map")
            col0.prop(am, "profile", text="Profile")

            row1.template_list("VIEW3D_UL_vr_actions", "", am, "actionmap_items",
                               am, "selected_item", rows=3)

            col = row1.column(align=True)
            col.operator("view3d.vr_action_add", icon='ADD', text="")
            col.operator("view3d.vr_action_remove", icon='REMOVE', text="")

            col.menu("VIEW3D_MT_vr_action_menu", icon='DOWNARROW_HLT', text="")

            ami = vr_actionmap_item_selected_get(am)

            if ami:
                col1.prop(ami, "name", text="Action")
                col1.prop(ami, "type", text="Type")
                col1.prop(ami, "user_path0", text="User Path 0")
                col1.prop(ami, "component_path0", text="Component Path 0")
                col1.prop(ami, "user_path1", text="User Path 1")
                col1.prop(ami, "component_path1", text="Component Path 1")

                if ami.type == 'BUTTON' or ami.type == 'AXIS':
                    col1.prop(ami, "threshold", text="Threshold")
                    col1.prop(ami, "op", text="Operator")
                    col1.prop(ami, "op_flag", text="Operator Flag")
                    # Properties.
                    vr_draw_ami(ami, col1, 1)
                elif ami.type == 'POSE':
                    col1.prop(ami, "pose_is_controller", text="Use for Controller Poses")
                    col1.prop(ami, "pose_location", text="Location Offset")
                    col1.prop(ami, "pose_rotation", text="Rotation Offset") 
                elif ami.type == 'HAPTIC':
                    col1.prop(ami, "haptic_duration", text="Duration")
                    col1.prop(ami, "haptic_frequency", text="Frequency")
                    col1.prop(ami, "haptic_amplitude", text="Amplitude")


class VIEW3D_OT_vr_actionmap_add(Operator):
    bl_idname = "view3d.vr_actionmap_add"
    bl_label = "Add VR Action Map"
    bl_description = "Add a new VR action map to the scene"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        ac = vr_actionconfig_active_get(context)
        if not ac:
            return {'CANCELLED'}

        am = ac.actionmaps.new("actionmap", False)    
        if not am:
            return {'CANCELLED'}

        # Select newly created actionmap.
        ac.selected_actionmap = len(ac.actionmaps) - 1

        return {'FINISHED'}


class VIEW3D_OT_vr_actionmap_remove(Operator):
    bl_idname = "view3d.vr_actionmap_remove"
    bl_label = "Remove VR Action Map"
    bl_description = "Delete the selected VR action map from the scene"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        ac = vr_actionconfig_active_get(context)
        if not ac:
            return {'CANCELLED'}

        am = vr_actionmap_selected_get(ac)
        if not am:
            return {'CANCELLED'}

        ac.actionmaps.remove(am)

        return {'FINISHED'}


class VIEW3D_OT_vr_actionmap_activate(Operator):
    bl_idname = "view3d.vr_actionmap_activate"
    bl_label = "Activate VR Action Map"
    bl_description = "Set the current VR action map for the session"
    bl_options = {'UNDO', 'REGISTER'}

    index: bpy.props.IntProperty(
        name="Index",
        options={'HIDDEN'},
    )

    def execute(self, context):
        ac = vr_actionconfig_active_get(context)
        if not ac or (self.index >= len(ac.actionmaps)):
            return {'CANCELLED'}

        ac.active_actionmap = (
            self.index if self.properties.is_property_set(
                "index") else ac.selected_actionmap
        )

        session_state = context.window_manager.xr_session_state
        if session_state:
            am = vr_actionmap_active_get(ac)
            if am:
                session_state.set_active_action_set(context, am.name)

        return {'FINISHED'}


class VIEW3D_OT_vr_actionmaps_defaults_load(Operator):
    bl_idname = "view3d.vr_actionmaps_defaults_load"
    bl_label = "Load Default VR Action Maps"
    bl_description = "Load default VR action maps"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        ac = vr_actionconfig_active_get(context)
        if not ac:
            return {'CANCELLED'}

        filepath = vr_get_default_config_path()

        if not vr_load_actionmaps(context, filepath): 
            return {'CANCELLED'}
        
        return {'FINISHED'}


class VIEW3D_OT_vr_actionmaps_import(Operator, ImportHelper):
    bl_idname = "view3d.vr_actionmaps_import"
    bl_label = "Import VR Action Maps"
    bl_description = "Import VR action maps from configuration file"
    bl_options = {'UNDO', 'REGISTER'}

    filter_glob: bpy.props.StringProperty(
        default='*.py',
        options={'HIDDEN'},
    )

    def execute(self, context):
        filename, ext = os.path.splitext(self.filepath)
        if (ext != ".py"):
            return {'CANCELLED'}

        if not vr_load_actionmaps(context, self.filepath):
            return {'CANCELLED'}
        
        return {'FINISHED'}


class VIEW3D_OT_vr_actionmaps_export(Operator, ExportHelper):
    bl_idname = "view3d.vr_actionmaps_export"
    bl_label = "Export VR Action Maps"
    bl_description = "Export VR action maps to configuration file"
    bl_options = {'REGISTER'}

    filter_glob: bpy.props.StringProperty(
        default='*.py',
        options={'HIDDEN'},
    )
    filename_ext: bpy.props.StringProperty(
        default='.py',
        options={'HIDDEN'},
    )

    def execute(self, context):
        filename, ext = os.path.splitext(self.filepath)
        if (ext != ".py"):
            return {'CANCELLED'}
        
        if not vr_save_actionmaps(context, self.filepath):
            return {'CANCELLED'}
        
        return {'FINISHED'}


class VIEW3D_OT_vr_actionmap_copy(Operator):
    bl_idname = "view3d.vr_actionmap_copy"
    bl_label = "Copy VR Action Map"
    bl_description = "Copy selected VR action map"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        ac = vr_actionconfig_active_get(context)
        if not ac:
            return {'CANCELLED'}

        am = vr_actionmap_selected_get(ac)
        if not am:
            return {'CANCELLED'}

        # Copy actionmap.
        am_new = ac.actionmaps.new_from_actionmap(am)
        if not am_new:
            return {'CANCELLED'}
        
        # Select newly created actionmap.
        ac.selected_actionmap = len(ac.actionmaps) - 1

        return {'FINISHED'}


class VIEW3D_OT_vr_actionmaps_clear(Operator):
    bl_idname = "view3d.vr_actionmaps_clear"
    bl_label = "Clear VR Action Maps"
    bl_description = "Delete all VR action maps from the scene"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        ac = vr_actionconfig_active_get(context)
        if not ac:
            return {'CANCELLED'}

        while ac.actionmaps:
            ac.actionmaps.remove(ac.actionmaps[0])

        return {'FINISHED'} 


class VIEW3D_OT_vr_action_add(Operator):
    bl_idname = "view3d.vr_action_add"
    bl_label = "Add VR Action"
    bl_description = "Add a new VR action to the action map"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        ac = vr_actionconfig_active_get(context)
        if not ac:
            return {'CANCELLED'}

        am = vr_actionmap_selected_get(ac)
        if not am:
            return {'CANCELLED'}

        ami = am.actionmap_items.new("action", False)    
        if not ami:
            return {'CANCELLED'}

        # Select newly created item.
        am.selected_item = len(am.actionmap_items) - 1

        return {'FINISHED'}


class VIEW3D_OT_vr_action_remove(Operator):
    bl_idname = "view3d.vr_action_remove"
    bl_label = "Remove VR Action"
    bl_description = "Delete the selected VR action from the action map"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        ac = vr_actionconfig_active_get(context)
        if not ac:
            return {'CANCELLED'}

        am = vr_actionmap_selected_get(ac)
        if not am:
            return {'CANCELLED'}

        ami = vr_actionmap_item_selected_get(am)
        if not ami:
            return {'CANCELLED'}

        am.actionmap_items.remove(ami)

        return {'FINISHED'}


class VIEW3D_OT_vr_action_copy(Operator):
    bl_idname = "view3d.vr_action_copy"
    bl_label = "Copy VR Action"
    bl_description = "Copy selected VR action"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        ac = vr_actionconfig_active_get(context)
        if not ac:
            return {'CANCELLED'}

        am = vr_actionmap_selected_get(ac)
        if not am:
            return {'CANCELLED'}

        ami = vr_actionmap_item_selected_get(am)
        if not ami:
            return {'CANCELLED'}

        # Copy item.
        ami_new = am.actionmap_items.new_from_item(ami)
        if not ami_new:
            return {'CANCELLED'}
        
        # Select newly created item.
        am.selected_item = len(am.actionmap_items) - 1

        return {'FINISHED'}


class VIEW3D_OT_vr_actions_clear(Operator):
    bl_idname = "view3d.vr_actions_clear"
    bl_label = "Clear VR Actions"
    bl_description = "Delete all VR actions from the action map"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        ac = vr_actionconfig_active_get(context)
        if not ac:
            return {'CANCELLED'}

        am = vr_actionmap_selected_get(ac)
        if not am:
            return {'CANCELLED'}

        while am.actionmap_items:
            am.actionmap_items.remove(am.actionmap_items[0])

        return {'FINISHED'}


### Motion capture.
def vr_headset_object_update(self, context):
    session_settings = context.window_manager.xr_session_settings
    session_settings.headset_object = context.scene.vr_headset_object


def vr_controller0_object_update(self, context):
    session_settings = context.window_manager.xr_session_settings
    session_settings.controller0_object = context.scene.vr_controller0_object


def vr_controller1_object_update(self, context):
    session_settings = context.window_manager.xr_session_settings
    session_settings.controller1_object = context.scene.vr_controller1_object


class VIEW3D_PT_vr_motion_capture(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VR"
    bl_label = "Motion Capture"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        session_settings = context.window_manager.xr_session_settings

        col = layout.column(align=True)
        col.label(icon='ERROR', text="Note:")
        col.label(text="Settings here may have a significant")
        col.label(text="performance impact!")

        layout.separator()

        row = layout.row()
        row.label(text="Headset")
        col = row.column()
        col.prop(scene, "vr_headset_object", text="")
        col.prop(session_settings, "headset_object_enable", text="Enable")
        col.prop(session_settings, "headset_object_autokey", text="Auto Key")
            
        row = layout.row()
        row.label(text="Controller 0")
        col = row.column()
        col.prop(scene, "vr_controller0_object", text="")
        col.prop(session_settings, "controller0_object_enable", text="Enable")
        col.prop(session_settings, "controller0_object_autokey", text="Auto Key")

        row = layout.row()
        row.label(text="Controller 1")
        col = row.column()
        col.prop(scene, "vr_controller1_object", text="")
        col.prop(session_settings, "controller1_object_enable", text="Enable")
        col.prop(session_settings, "controller1_object_autokey", text="Auto Key")


### Viewport feedback.
class VIEW3D_PT_vr_viewport_feedback(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VR"
    bl_label = "Viewport Feedback"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        view3d = context.space_data
        session_settings = context.window_manager.xr_session_settings

        col = layout.column(align=True)
        col.label(icon='ERROR', text="Note:")
        col.label(text="Settings here may have a significant")
        col.label(text="performance impact!")

        layout.separator()

        layout.prop(view3d.shading, "vr_show_virtual_camera")
        layout.prop(view3d.shading, "vr_show_controllers")
        layout.prop(view3d.shading, "vr_show_landmarks")
        layout.prop(view3d, "mirror_xr_session")


### Info.
class VIEW3D_PT_vr_info(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VR"
    bl_label = "VR Info"

    @classmethod
    def poll(cls, context):
        return not bpy.app.build_options.xr_openxr

    def draw(self, context):
        layout = self.layout
        layout.label(icon='ERROR', text="Built without VR/OpenXR features.")


### Gizmos.
class VIEW3D_GT_vr_camera_cone(Gizmo):
    bl_idname = "VIEW_3D_GT_vr_camera_cone"

    aspect = 1.0, 1.0

    def draw(self, context):
        if not hasattr(self, "frame_shape"):
            aspect = self.aspect

            frame_shape_verts = (
                (-aspect[0], -aspect[1], -1.0),
                (aspect[0], -aspect[1], -1.0),
                (aspect[0], aspect[1], -1.0),
                (-aspect[0], aspect[1], -1.0),
            )
            lines_shape_verts = (
                (0.0, 0.0, 0.0),
                frame_shape_verts[0],
                (0.0, 0.0, 0.0),
                frame_shape_verts[1],
                (0.0, 0.0, 0.0),
                frame_shape_verts[2],
                (0.0, 0.0, 0.0),
                frame_shape_verts[3],
            )

            self.frame_shape = self.new_custom_shape(
                'LINE_LOOP', frame_shape_verts)
            self.lines_shape = self.new_custom_shape(
                'LINES', lines_shape_verts)

        # Ensure correct GL state (otherwise other gizmos might mess that up)
        bgl.glLineWidth(1)
        bgl.glEnable(bgl.GL_BLEND)

        self.draw_custom_shape(self.frame_shape)
        self.draw_custom_shape(self.lines_shape)


class VIEW3D_GT_vr_controller_axes(Gizmo):
    bl_idname = "VIEW_3D_GT_vr_controller_axes"

    def draw(self, context):
        bgl.glLineWidth(1)
        bgl.glEnable(bgl.GL_BLEND)

        self.color = 1.0, 0.2, 0.322
        self.draw_preset_arrow(self.matrix_basis, axis='POS_X')
        self.color = 0.545, 0.863, 0.0
        self.draw_preset_arrow(self.matrix_basis, axis='POS_Y')
        self.color = 0.157, 0.565, 1.0
        self.draw_preset_arrow(self.matrix_basis, axis='POS_Z')


class VIEW3D_GGT_vr_viewer_pose(GizmoGroup):
    bl_idname = "VIEW3D_GGT_vr_viewer_pose"
    bl_label = "VR Viewer Pose Indicator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT', 'SCALE', 'VR_REDRAWS'}

    @classmethod
    def poll(cls, context):
        view3d = context.space_data
        return (
            view3d.shading.vr_show_virtual_camera and
            bpy.types.XrSessionState.is_running(context) and
            not view3d.mirror_xr_session
        )

    @staticmethod
    def _get_viewer_pose_matrix(context):
        wm = context.window_manager

        loc = wm.xr_session_state.viewer_pose_location
        rot = wm.xr_session_state.viewer_pose_rotation

        rotmat = Matrix.Identity(3)
        rotmat.rotate(rot)
        rotmat.resize_4x4()
        transmat = Matrix.Translation(loc)

        return transmat @ rotmat

    def setup(self, context):
        gizmo = self.gizmos.new(VIEW3D_GT_vr_camera_cone.bl_idname)
        gizmo.aspect = 1 / 3, 1 / 4

        gizmo.color = gizmo.color_highlight = 0.2, 0.6, 1.0
        gizmo.alpha = 1.0

        self.gizmo = gizmo

    def draw_prepare(self, context):
        self.gizmo.matrix_basis = self._get_viewer_pose_matrix(context)


class VIEW3D_GGT_vr_controller_poses(GizmoGroup):
    bl_idname = "VIEW3D_GGT_vr_controller_poses"
    bl_label = "VR Controller Poses Indicator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT', 'SCALE', 'VR_REDRAWS'}

    @classmethod
    def poll(cls, context):
        view3d = context.space_data
        return (
            view3d.shading.vr_show_controllers and
            bpy.types.XrSessionState.is_running(context) and
            not view3d.mirror_xr_session
        )

    @staticmethod
    def _get_controller_pose_matrix(context, idx, scale):
        wm = context.window_manager

        loc = None
        rot = None
        if idx == 0:
            loc = wm.xr_session_state.controller_pose0_location
            rot = wm.xr_session_state.controller_pose0_rotation
        elif idx == 1:
            loc = wm.xr_session_state.controller_pose1_location
            rot = wm.xr_session_state.controller_pose1_rotation
        else:
            return Matrix.Identity(4);

        rotmat = Matrix.Identity(3)
        rotmat.rotate(rot)
        rotmat.resize_4x4()
        transmat = Matrix.Translation(loc)
        scalemat = Matrix.Scale(scale, 4)

        return transmat @ rotmat @ scalemat

    def setup(self, context):
        for idx in range(2):
            gizmo = self.gizmos.new(VIEW3D_GT_vr_controller_axes.bl_idname)
            gizmo.aspect = 1 / 3, 1 / 4
 
            gizmo.color = gizmo.color_highlight = 1.0, 1.0, 1.0
            gizmo.alpha = 1.0

        self.gizmo = gizmo

    def draw_prepare(self, context):
        view3d = context.space_data
        scale = 0.5
        idx = 0
        for gizmo in self.gizmos:
            gizmo.matrix_basis = self._get_controller_pose_matrix(context, idx, scale)
            idx += 1


class VIEW3D_GGT_vr_landmarks(GizmoGroup):
    bl_idname = "VIEW3D_GGT_vr_landmarks"
    bl_label = "VR Landmark Indicators"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT', 'SCALE'}

    @classmethod
    def poll(cls, context):
        view3d = context.space_data
        return (
            view3d.shading.vr_show_landmarks
        )

    def setup(self, context):
        pass

    def draw_prepare(self, context):
        # first delete the old gizmos
        for g in self.gizmos:
            self.gizmos.remove(g)

        scene = context.scene
        landmarks = scene.vr_landmarks

        for lm in landmarks:
            if ((lm.type == 'SCENE_CAMERA' and not scene.camera) or
                    (lm.type == 'OBJECT' and not lm.base_pose_object)):
                continue

            gizmo = self.gizmos.new(VIEW3D_GT_vr_camera_cone.bl_idname)
            gizmo.aspect = 1 / 3, 1 / 4

            gizmo.color = gizmo.color_highlight = 0.2, 1.0, 0.6
            gizmo.alpha = 1.0

            self.gizmo = gizmo

            if lm.type == 'SCENE_CAMERA':
                cam = scene.camera
                lm_mat = cam.matrix_world if cam else Matrix.Identity(4)
            elif lm.type == 'OBJECT':
                lm_mat = lm.base_pose_object.matrix_world
            else:
                angle = lm.base_pose_angle
                raw_rot = Euler((radians(90.0), 0, angle))

                rotmat = Matrix.Identity(3)
                rotmat.rotate(raw_rot)
                rotmat.resize_4x4()

                transmat = Matrix.Translation(lm.base_pose_location)

                lm_mat = transmat @ rotmat

            self.gizmo.matrix_basis = lm_mat

