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
    Gizmo,
    GizmoGroup,
    PropertyGroup,
    UIList,
    Menu,
    Panel,
    Operator,
)
from bpy.props import (
    CollectionProperty,
    IntProperty,
    BoolProperty,
)
from bpy.app.handlers import persistent
from mathutils import Quaternion

bl_info = {
    "name": "VR Scene Inspection",
    "author": "Julian Eisel (Severin), Sebastian Koenig",
    "version": (0, 9, 0),
    "blender": (2, 90, 0),
    "location": "3D View > Sidebar > VR",
    "description": ("View the viewport with virtual reality glasses "
                    "(head-mounted displays)"),
    "support": "OFFICIAL",
    "warning": "This is an early, limited preview of in development "
               "VR support for Blender.",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/3d_view/vr_scene_inspection.html",
    "category": "3D View",
}


@persistent
def ensure_default_vr_landmark(context: bpy.context):
    # Ensure there's a default landmark (scene camera by default).
    landmarks = bpy.context.scene.vr_landmarks
    if not landmarks:
        landmarks.add()
        landmarks[0].type = 'SCENE_CAMERA'


def xr_landmark_active_type_update(self, context):
    wm = context.window_manager
    session_settings = wm.xr_session_settings
    landmark_active = VRLandmark.get_active_landmark(context)

    # Update session's base pose type to the matching type.
    if landmark_active.type == 'SCENE_CAMERA':
        session_settings.base_pose_type = 'SCENE_CAMERA'
    elif landmark_active.type == 'USER_CAMERA':
        session_settings.base_pose_type = 'OBJECT'
    elif landmark_active.type == 'CUSTOM':
        session_settings.base_pose_type = 'CUSTOM'


def xr_landmark_active_camera_update(self, context):
    session_settings = context.window_manager.xr_session_settings
    landmark_active = VRLandmark.get_active_landmark(context)

    # Update the anchor object to the (new) camera of this landmark.
    session_settings.base_pose_object = landmark_active.base_pose_camera


def xr_landmark_active_base_pose_location_update(self, context):
    session_settings = context.window_manager.xr_session_settings
    landmark_active = VRLandmark.get_active_landmark(context)

    session_settings.base_pose_location = landmark_active.base_pose_location


def xr_landmark_active_base_pose_angle_update(self, context):
    session_settings = context.window_manager.xr_session_settings
    landmark_active = VRLandmark.get_active_landmark(context)

    session_settings.base_pose_angle = landmark_active.base_pose_angle


def xr_landmark_type_update(self, context):
    landmark_selected = VRLandmark.get_selected_landmark(context)
    landmark_active = VRLandmark.get_active_landmark(context)

    # Only update session settings data if the changed landmark is actually
    # the active one.
    if landmark_active == landmark_selected:
        xr_landmark_active_type_update(self, context)


def xr_landmark_camera_update(self, context):
    landmark_selected = VRLandmark.get_selected_landmark(context)
    landmark_active = VRLandmark.get_active_landmark(context)

    # Only update session settings data if the changed landmark is actually
    # the active one.
    if landmark_active == landmark_selected:
        xr_landmark_active_camera_update(self, context)


def xr_landmark_base_pose_location_update(self, context):
    landmark_selected = VRLandmark.get_selected_landmark(context)
    landmark_active = VRLandmark.get_active_landmark(context)

    # Only update session settings data if the changed landmark is actually
    # the active one.
    if landmark_active == landmark_selected:
        xr_landmark_active_base_pose_location_update(self, context)


def xr_landmark_base_pose_angle_update(self, context):
    landmark_selected = VRLandmark.get_selected_landmark(context)
    landmark_active = VRLandmark.get_active_landmark(context)

    # Only update session settings data if the changed landmark is actually
    # the active one.
    if landmark_active == landmark_selected:
        xr_landmark_active_base_pose_angle_update(self, context)


def xr_landmark_camera_object_poll(self, object):
    return object.type == 'CAMERA'


def xr_landmark_active_update(self, context):
    wm = context.window_manager

    xr_landmark_active_type_update(self, context)
    xr_landmark_active_camera_update(self, context)
    xr_landmark_active_base_pose_location_update(self, context)
    xr_landmark_active_base_pose_angle_update(self, context)

    if wm.xr_session_state:
        wm.xr_session_state.reset_to_base_pose(context)


class VIEW3D_MT_landmark_menu(Menu):
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
            ('USER_CAMERA', "Custom Camera",
             "Use an existing camera to define the VR view base location and "
             "rotation"),
            ('CUSTOM', "Custom Pose",
             "Allow a manually defined position and rotation to be used as "
             "the VR view base pose"),
        ],
        default='SCENE_CAMERA',
        update=xr_landmark_type_update,
    )
    base_pose_camera: bpy.props.PointerProperty(
        name="Camera",
        type=bpy.types.Object,
        poll=xr_landmark_camera_object_poll,
        update=xr_landmark_camera_update,
    )
    base_pose_location: bpy.props.FloatVectorProperty(
        name="Base Pose Location",
        subtype='TRANSLATION',
        update=xr_landmark_base_pose_location_update,
    )

    base_pose_angle: bpy.props.FloatProperty(
        name="Base Pose Angle",
        subtype='ANGLE',
        update=xr_landmark_base_pose_angle_update,
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

        col.menu("VIEW3D_MT_landmark_menu", icon='DOWNARROW_HLT', text="")

        if landmark_selected:
            layout.prop(landmark_selected, "type")

            if landmark_selected.type == 'USER_CAMERA':
                layout.prop(landmark_selected, "base_pose_camera")
            elif landmark_selected.type == 'CUSTOM':
                layout.prop(landmark_selected,
                            "base_pose_location", text="Location")
                layout.prop(landmark_selected,
                            "base_pose_angle", text="Angle")


@persistent
def create_vr_actions(context: bpy.context):
    # Create all vr action sets and actions.
    context = bpy.context
    wm = context.window_manager
    scene = context.scene
    action_set = scene.vr_action_set[0]
    actions = scene.vr_actions

    if wm.xr_session_state and len(actions) > 0:
        wm.xr_session_state.create_action_set(context, action_set.name)

        type = 'BUTTON'
        op_flag = 'PRESS'
        interaction_path0 = ""
        interaction_path1 = ""

        for action in actions:
            if action.type == 'BUTTON':
                type = 'BUTTON'		
                if action.op_flag == 'PRESS':	
                    op_flag = 'PRESS'
                elif action.op_flag == 'RELEASE':	
                    op_flag = 'RELEASE'
                elif action.op_flag == 'MODAL':
                    op_flag = 'MODAL'
                else:
                    continue
            elif action.type == 'POSE':
                type = 'POSE'					
            elif action.type == 'HAPTIC':
                type = 'HAPTIC'
            else:
                continue

            wm.xr_session_state.create_action(context, action_set.name, action.name, type, action.user_path0, action.user_path1, action.op, op_flag)         

            if action.type == 'POSE':
                wm.xr_session_state.create_action_space(context, action_set.name, action.name, action.user_path0, action.user_path1, \
                            action.pose_location, action.pose_rotation)
                if action.pose_is_controller:
                    wm.xr_session_state.set_controller_pose_action(context, action_set.name, action.name)

            interaction_path0 = action.user_path0 + action.component_path0
            interaction_path1 = action.user_path1 + action.component_path1

            wm.xr_session_state.create_action_binding(context, action_set.name, action_set.profile, action.name, interaction_path0, interaction_path1)  

        wm.xr_session_state.set_active_action_set(context, action_set.name)


@persistent
def ensure_default_vr_action_set(context: bpy.context):
    # Ensure there's a default action set.
    action_set = bpy.context.scene.vr_action_set
    if not action_set:
        action_set.add()


class VIEW3D_MT_action_menu(Menu):
    bl_label = "Action Controls"

    def draw(self, _context):
        layout = self.layout

        layout.operator("view3d.vr_action_set_clear")


class VRActionSet(PropertyGroup):
    name: bpy.props.StringProperty(
        name="VR action set.\nMust not contain upper case letters or special characters other than '-', '_', or '.'",
        default="action_set",
    )
    profile: bpy.props.StringProperty(
        name="OpenXR interaction profile path",
    )


class VRAction(PropertyGroup):
    name: bpy.props.StringProperty(
        name="VR action.\nMust not contain upper case letters or special characters other than '-', '_', or '.'",
        default="action",
    )
    type: bpy.props.EnumProperty(
        name="VR action type",
        items=[
            ('BUTTON', "Button", "Button input"),
            ('POSE', "Pose", "Pose input"),
            ('HAPTIC', "Haptic", "Haptic output"),
        ],
        default='BUTTON',
    )
    user_path0: bpy.props.StringProperty(
        name="OpenXR user path",
    )
    component_path0: bpy.props.StringProperty(
        name="OpenXR component path",
    )
    user_path1: bpy.props.StringProperty(
        name="OpenXR user path",
    )
    component_path1: bpy.props.StringProperty(
        name="OpenXR component path",
    )
    op: bpy.props.StringProperty(
        name="Python operator",
    )
    op_flag: bpy.props.EnumProperty(
        name="Operator flag",
        items=[
            ('PRESS', "Press",
             "Execute operator on press "
             "(non-modal operators only)"),
            ('RELEASE', "Release",
             "Execute operator on release "
             "(non-modal operators only)"),
            ('MODAL', "Modal",
             "Use modal execution "
             "(modal operators only)"),
        ],
        default='PRESS',
    )
    state0: bpy.props.FloatProperty(
        name="Current value",
    )
    state1: bpy.props.FloatProperty(
        name="Current value",
    )
    pose_is_controller: bpy.props.BoolProperty(
        name="Pose will be used for the VR controllers",
    )	
    pose_location: bpy.props.FloatVectorProperty(
        name="Pose location offset",
        subtype='TRANSLATION',
    )
    pose_rotation: bpy.props.FloatVectorProperty(
        name="Pose rotation offset",
        subtype='EULER',
    )
    pose_state_location0: bpy.props.FloatVectorProperty(
        name="Current pose location",
        subtype='TRANSLATION',
    )
    pose_state_rotation0: bpy.props.FloatVectorProperty(
        name="Current pose rotation",
        subtype='EULER',
    )
    pose_state_location1: bpy.props.FloatVectorProperty(
        name="Current pose location",
        subtype='TRANSLATION',
    )
    pose_state_rotation1: bpy.props.FloatVectorProperty(
        name="Current pose rotation",
        subtype='EULER',
    )
    haptic_duration: bpy.props.FloatProperty(
        name="Haptic duration in seconds",
    )
    haptic_frequency: bpy.props.FloatProperty(
        name="Haptic frequency",
    )
    haptic_amplitude: bpy.props.FloatProperty(
        name="Haptic amplitude",
    )

    @staticmethod
    def get_selected_action(context):
        scene = context.scene
        actions = scene.vr_actions

        return (
            None if (len(actions) <
                     1) else actions[scene.vr_actions_selected]
        )


class VIEW3D_UL_vr_actions(UIList):
    def draw_item(self, context, layout, _data, item, icon, _active_data,
                  _active_propname, index):
        action = item

        layout.emboss = 'NONE'

        layout.prop(action, "name", text="")


class VIEW3D_PT_vr_actions(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VR"
    bl_label = "Actions"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        action_set = scene.vr_action_set[0]
        action_selected = VRAction.get_selected_action(context)

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        layout.prop(action_set, "name", text="Action Set")
        layout.prop(action_set, "profile", text="Profile")

        row = layout.row()

        row.template_list("VIEW3D_UL_vr_actions", "", scene, "vr_actions",
                          scene, "vr_actions_selected", rows=2)

        col = row.column(align=True)
        col.operator("view3d.vr_action_add", icon='ADD', text="")
        col.operator("view3d.vr_action_remove", icon='REMOVE', text="")

        col.menu("VIEW3D_MT_action_menu", icon='DOWNARROW_HLT', text="")

        if action_selected:
            layout.prop(action_selected, "type", text="Type")
            layout.prop(action_selected, "user_path0", text="User Path 0")
            layout.prop(action_selected, "component_path0", text="Component Path 0")
            layout.prop(action_selected, "user_path1", text="User Path 1")
            layout.prop(action_selected, "component_path1", text="Component Path 1")

            if action_selected.type == 'BUTTON':
                layout.prop(action_selected,
                            "op", text="Operator")
                layout.prop(action_selected,
                            "op_flag", text="Operator Flag")
                layout.operator("view3d.vr_action_state_get", icon='PLAY', text="Get current states")
                layout.prop(action_selected,
                            "state0", text="State 0")
                layout.prop(action_selected,
                            "state1", text="State 1")
            elif action_selected.type == 'POSE':
                layout.prop(action_selected,
                            "pose_is_controller", text="Use for Controller Poses")
                layout.prop(action_selected,
                            "pose_location", text="Location Offset")
                layout.prop(action_selected,
                            "pose_rotation", text="Rotation Offset")
                layout.operator("view3d.vr_pose_action_state_get", icon='PLAY', text="Get current states")
                layout.prop(action_selected,
                            "pose_state_location0", text="Location State 0")
                layout.prop(action_selected,
                            "pose_state_rotation0", text="Rotation State 0")     
                layout.prop(action_selected,
                            "pose_state_location1", text="Location State 1")
                layout.prop(action_selected,
                            "pose_state_rotation1", text="Rotation State 1")   
            elif action_selected.type == 'HAPTIC':
                layout.prop(action_selected,
                            "haptic_duration", text="Duration")
                layout.prop(action_selected,
                            "haptic_frequency", text="Frequency")
                layout.prop(action_selected,
                            "haptic_amplitude", text="Amplitude")
                layout.operator("view3d.vr_haptic_action_apply", icon='PLAY', text="Apply haptic action")


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
        col.prop(session_settings, "show_selection", text="Selection")
        col.prop(session_settings, "selection_eye", text="Selection Eye")

        col = layout.column(align=True)
        col.prop(session_settings, "clip_start", text="Clip Start")
        col.prop(session_settings, "clip_end", text="End")


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
    bl_label = "Add VR Landmark from camera"
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
        lm.type = 'USER_CAMERA'
        lm.base_pose_camera = cam
        lm.name = "LM_" + cam.name

        # select newly created set
        scene.vr_landmarks_selected = len(landmarks) - 1

        return {'FINISHED'}


class VIEW3D_OT_vr_landmark_from_session(Operator):
    bl_idname = "view3d.vr_landmark_from_session"
    bl_label = "Add VR Landmark from session"
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
        xr_landmark_active_update(None, context)

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
        elif lm.type == 'USER_CAMERA':
            return lm.base_pose_camera is not None

        return True

    def execute(self, context):
        scene = context.scene
        lm = VRLandmark.get_selected_landmark(context)
        if lm.type == 'SCENE_CAMERA':
            lm_pos = scene.camera.location
        elif lm.type == 'USER_CAMERA':
            lm_pos = lm.base_pose_camera.location
        else:
            lm_pos = lm.base_pose_location
        scene.cursor.location = lm_pos

        return{'FINISHED'}


class VIEW3d_OT_add_camera_from_vr_landmark(Operator):
    bl_idname = "view3d.add_camera_from_vr_landmark"
    bl_label = "New Camera from VR Landmark"
    bl_description = "Create a new Camera from the selected VR Landmark"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        import math

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
        import math

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

    index: IntProperty(
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


class VIEW3D_OT_vr_action_add(Operator):
    bl_idname = "view3d.vr_action_add"
    bl_label = "Add VR Action"
    bl_description = "Add a new VR action to the list and select it"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        scene = context.scene
        actions = scene.vr_actions

        actions.add()

        # select newly created set
        scene.vr_actions_selected = len(actions) - 1

        return {'FINISHED'}


class VIEW3D_OT_vr_action_remove(Operator):
    bl_idname = "view3d.vr_action_remove"
    bl_label = "Remove VR Action"
    bl_description = "Delete the selected VR action from the list"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        scene = context.scene
        actions = scene.vr_actions

        if len(actions) > 0:
            action_selected_idx = scene.vr_actions_selected
            actions.remove(action_selected_idx)

            scene.vr_actions_selected -= 1

        return {'FINISHED'}


class VIEW3D_OT_vr_action_set_clear(Operator):
    bl_idname = "view3d.vr_action_set_clear"
    bl_label = "Clear VR Action Set"
    bl_description = "Clears the VR action set and deletes all actions"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        scene = context.scene
        action_set = scene.vr_action_set[0]
        actions = scene.vr_actions

        action_set.name = "action_set"
        action_set.profile = ""

        idx = len(actions) - 1;
        for action in actions:
            actions.remove(idx)
            idx -= 1

        scene.vr_actions_selected = 0

        return {'FINISHED'}


class VIEW3D_OT_vr_action_state_get(Operator):
    bl_idname = "view3d.vr_action_state_get"
    bl_label = "Get VR Action State"
    bl_description = "Get the current states of a VR action"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        wm = context.window_manager
        scene = context.scene
        action_set = scene.vr_action_set[0]
        actions = scene.vr_actions

        if wm.xr_session_state and len(actions) > 0:
            action = actions[scene.vr_actions_selected]
            if action.type == 'BUTTON':
                action.state0 = wm.xr_session_state.get_action_state(context, action_set.name, action.name, \
                            action.user_path0)
                action.state1 = wm.xr_session_state.get_action_state(context, action_set.name, action.name, \
                            action.user_path1)

        return {'FINISHED'}


class VIEW3D_OT_vr_pose_action_state_get(Operator):
    bl_idname = "view3d.vr_pose_action_state_get"
    bl_label = "Get VR Pose Action State"
    bl_description = "Get the current states of a VR pose action"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        wm = context.window_manager
        scene = context.scene
        action_set = scene.vr_action_set[0]
        actions = scene.vr_actions

        if wm.xr_session_state and len(actions) > 0:
            action = actions[scene.vr_actions_selected]
            if action.type == 'POSE':
                state = wm.xr_session_state.get_pose_action_state(context, action_set.name, action.name, \
                            action.user_path0)
                action.pose_state_location0[0] = state[0]
                action.pose_state_location0[1] = state[1]
                action.pose_state_location0[2] = state[2]
                quat = Quaternion()
                quat.w = state[3]
                quat.x = state[4]
                quat.y = state[5]
                quat.z = state[6]
                action.pose_state_rotation0 = quat.to_euler()

                state = wm.xr_session_state.get_pose_action_state(context, action_set.name, action.name, \
                            action.user_path1)
                action.pose_state_location1[0] = state[0]
                action.pose_state_location1[1] = state[1]
                action.pose_state_location1[2] = state[2]
                quat.w = state[3]
                quat.x = state[4]
                quat.y = state[5]
                quat.z = state[6]
                action.pose_state_rotation1 = quat.to_euler()

        return {'FINISHED'}


class VIEW3D_OT_vr_haptic_action_apply(Operator):
    bl_idname = "view3d.vr_haptic_action_apply"
    bl_label = "Apply VR Haptic Action"
    bl_description = "Apply a VR haptic action with the specified settings"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        wm = context.window_manager
        scene = context.scene
        action_set = scene.vr_action_set[0]
        actions = scene.vr_actions

        if wm.xr_session_state and len(actions) > 0:
            action = actions[scene.vr_actions_selected]
            if action.type == 'HAPTIC':
                wm.xr_session_state.apply_haptic_action(context, action_set.name, action.name, \
                            action.user_path0, action.user_path1, action.haptic_duration, action.haptic_frequency, action.haptic_amplitude)

        return {'FINISHED'}


class VIEW3D_PT_vr_viewport_feedback(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VR"
    bl_label = "Viewport Feedback"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        view3d = context.space_data

        col = layout.column(align=True)
        col.label(icon='ERROR', text="Note:")
        col.label(text="Settings here may have a significant")
        col.label(text="performance impact!")

        layout.separator()

        layout.prop(view3d.shading, "vr_show_virtual_camera")
        layout.prop(view3d.shading, "vr_show_controllers")
        layout.prop(view3d.shading, "vr_show_landmarks")
        layout.prop(view3d, "mirror_xr_session")


class VIEW3D_GT_vr_camera_cone(Gizmo):
    bl_idname = "VIEW_3D_GT_vr_camera_cone"

    aspect = 1.0, 1.0

    def draw(self, context):
        import bgl

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
        import bgl

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
        from mathutils import Matrix

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
            bpy.types.XrSessionState.is_running(context)
        )

    @staticmethod
    def _get_controller_pose_matrix(context, idx, scale):
        from mathutils import Matrix

        wm = context.window_manager

        loc = None
        rot = None
        if idx == 0:
            loc = wm.xr_session_state.controller_pose_location0
            rot = wm.xr_session_state.controller_pose_rotation0
        elif idx == 1:
            loc = wm.xr_session_state.controller_pose_location1
            rot = wm.xr_session_state.controller_pose_rotation1
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
        if view3d.mirror_xr_session:
            scale = 0.1
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

        from math import radians
        from mathutils import Matrix, Euler
        scene = context.scene
        landmarks = scene.vr_landmarks

        for lm in landmarks:
            if ((lm.type == 'SCENE_CAMERA' and not scene.camera) or
                    (lm.type == 'USER_CAMERA' and not lm.base_pose_camera)):
                continue

            gizmo = self.gizmos.new(VIEW3D_GT_vr_camera_cone.bl_idname)
            gizmo.aspect = 1 / 3, 1 / 4

            gizmo.color = gizmo.color_highlight = 0.2, 1.0, 0.6
            gizmo.alpha = 1.0

            self.gizmo = gizmo

            if lm.type == 'SCENE_CAMERA':
                cam = scene.camera
                lm_mat = cam.matrix_world if cam else Matrix.Identity(4)
            elif lm.type == 'USER_CAMERA':
                lm_mat = lm.base_pose_camera.matrix_world
            else:
                angle = lm.base_pose_angle
                raw_rot = Euler((radians(90.0), 0, angle))

                rotmat = Matrix.Identity(3)
                rotmat.rotate(raw_rot)
                rotmat.resize_4x4()

                transmat = Matrix.Translation(lm.base_pose_location)

                lm_mat = transmat @ rotmat

            self.gizmo.matrix_basis = lm_mat


classes = (
    VIEW3D_PT_vr_session,
    VIEW3D_PT_vr_session_view,
    VIEW3D_PT_vr_landmarks,
    VIEW3D_PT_vr_actions,
    VIEW3D_PT_vr_viewport_feedback,

    VRLandmark,
    VIEW3D_UL_vr_landmarks,
    VIEW3D_MT_landmark_menu,

    VRActionSet,
    VRAction,
    VIEW3D_UL_vr_actions,
    VIEW3D_MT_action_menu,

    VIEW3D_OT_vr_landmark_add,
    VIEW3D_OT_vr_landmark_remove,
    VIEW3D_OT_vr_landmark_activate,
    VIEW3D_OT_vr_landmark_from_session,
    VIEW3d_OT_add_camera_from_vr_landmark,
    VIEW3D_OT_camera_to_vr_landmark,
    VIEW3D_OT_vr_landmark_from_camera,
    VIEW3D_OT_cursor_to_vr_landmark,
    VIEW3D_OT_update_vr_landmark,

    VIEW3D_OT_vr_action_add,
    VIEW3D_OT_vr_action_remove,
    VIEW3D_OT_vr_action_set_clear,
    VIEW3D_OT_vr_action_state_get,
    VIEW3D_OT_vr_pose_action_state_get,
    VIEW3D_OT_vr_haptic_action_apply,

    VIEW3D_GT_vr_camera_cone,
    VIEW3D_GT_vr_controller_axes,
    VIEW3D_GGT_vr_viewer_pose,
    VIEW3D_GGT_vr_controller_poses,
    VIEW3D_GGT_vr_landmarks,
)


def register():
    if not bpy.app.build_options.xr_openxr:
        bpy.utils.register_class(VIEW3D_PT_vr_info)
        return

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.vr_landmarks = CollectionProperty(
        name="Landmark",
        type=VRLandmark,
    )
    bpy.types.Scene.vr_landmarks_selected = IntProperty(
        name="Selected Landmark"
    )
    bpy.types.Scene.vr_landmarks_active = IntProperty(
        update=xr_landmark_active_update,
    )
    bpy.types.Scene.vr_action_set = CollectionProperty(
        name="Action Set",
        type=VRActionSet,
    )	
    bpy.types.Scene.vr_actions = CollectionProperty(
        name="Action",
        type=VRAction,
    )
    bpy.types.Scene.vr_actions_selected = IntProperty(
        name="Selected Action",		
    )
    # View3DShading is the only per 3D-View struct with custom property
    # support, so "abusing" that to get a per 3D-View option.
    bpy.types.View3DShading.vr_show_virtual_camera = BoolProperty(
        name="Show VR Camera"
    )
    bpy.types.View3DShading.vr_show_controllers = BoolProperty(
        name="Show VR Controllers"
    )
    bpy.types.View3DShading.vr_show_landmarks = BoolProperty(
        name="Show Landmarks"
    )

    bpy.app.handlers.load_post.append(ensure_default_vr_landmark)
    bpy.app.handlers.load_post.append(ensure_default_vr_action_set)
    bpy.app.handlers.xr_session_start_pre.append(create_vr_actions)

def unregister():
    if not bpy.app.build_options.xr_openxr:
        bpy.utils.unregister_class(VIEW3D_PT_vr_info)
        return

    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.vr_landmarks
    del bpy.types.Scene.vr_landmarks_selected
    del bpy.types.Scene.vr_landmarks_active
    del bpy.types.Scene.vr_action_set
    del bpy.types.Scene.vr_actions
    del bpy.types.Scene.vr_actions_selected
    del bpy.types.View3DShading.vr_show_virtual_camera
    del bpy.types.View3DShading.vr_show_controllers
    del bpy.types.View3DShading.vr_show_landmarks

    bpy.app.handlers.load_post.remove(ensure_default_vr_landmark)
    bpy.app.handlers.load_post.remove(ensure_default_vr_action_set)
    bpy.app.handlers.xr_session_start_pre.remove(create_vr_actions)


if __name__ == "__main__":
    register()
