# SPDX-License-Identifier: GPL-2.0-or-later

if "bpy" in locals():
    import importlib
    importlib.reload(action_map)
    importlib.reload(defaults)
    importlib.reload(properties)
else:
    from . import action_map, defaults, properties

import bpy
from bpy.types import (
    Gizmo,
    GizmoGroup,
    Operator,
)
from bpy_extras.io_utils import ExportHelper, ImportHelper
import math
from math import radians
from mathutils import Euler, Matrix, Quaternion, Vector
import os.path


### Landmarks.
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


class VIEW3D_OT_vr_camera_landmark_from_session(Operator):
    bl_idname = "view3d.vr_camera_landmark_from_session"
    bl_label = "Add Camera and VR Landmark from Session"
    bl_description = "Create a new Camera and VR Landmark from the viewer pose of the running VR session and select it"
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        return bpy.types.XrSessionState.is_running(context)

    def execute(self, context):
        scene = context.scene
        landmarks = scene.vr_landmarks
        wm = context.window_manager

        lm = landmarks.add()
        lm.type = 'OBJECT'
        scene.vr_landmarks_selected = len(landmarks) - 1

        loc = wm.xr_session_state.viewer_pose_location
        rot = wm.xr_session_state.viewer_pose_rotation.to_euler()

        cam = bpy.data.cameras.new("Camera_" + lm.name)
        new_cam = bpy.data.objects.new("Camera_" + lm.name, cam)
        scene.collection.objects.link(new_cam)
        new_cam.location = loc
        new_cam.rotation_euler = rot

        lm.base_pose_object = new_cam

        return {'FINISHED'}


class VIEW3D_OT_update_vr_landmark(Operator):
    bl_idname = "view3d.update_vr_landmark"
    bl_label = "Update Custom VR Landmark"
    bl_description = "Update the selected landmark from the current viewer pose in the VR session"
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        selected_landmark = properties.VRLandmark.get_selected_landmark(context)
        return bpy.types.XrSessionState.is_running(context) and selected_landmark.type == 'CUSTOM'

    def execute(self, context):
        wm = context.window_manager

        lm = properties.VRLandmark.get_selected_landmark(context)

        loc = wm.xr_session_state.viewer_pose_location
        rot = wm.xr_session_state.viewer_pose_rotation.to_euler()

        lm.base_pose_location = loc
        lm.base_pose_angle = rot

        # Re-activate the landmark to trigger viewer reset and flush landmark settings to the session settings.
        properties.vr_landmark_active_update(None, context)

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
        lm = properties.VRLandmark.get_selected_landmark(context)
        if lm.type == 'SCENE_CAMERA':
            return context.scene.camera is not None
        elif lm.type == 'OBJECT':
            return lm.base_pose_object is not None

        return True

    def execute(self, context):
        scene = context.scene
        lm = properties.VRLandmark.get_selected_landmark(context)
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
        lm = properties.VRLandmark.get_selected_landmark(context)

        cam = bpy.data.cameras.new("Camera_" + lm.name)
        new_cam = bpy.data.objects.new("Camera_" + lm.name, cam)
        scene.collection.objects.link(new_cam)
        angle = lm.base_pose_angle
        new_cam.location = lm.base_pose_location
        new_cam.rotation_euler = (math.pi / 2, 0, angle)

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
        lm = properties.VRLandmark.get_selected_landmark(context)

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
class VIEW3D_OT_vr_actionmap_add(Operator):
    bl_idname = "view3d.vr_actionmap_add"
    bl_label = "Add VR Action Map"
    bl_description = "Add a new VR action map to the scene"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        session_settings = context.window_manager.xr_session_settings

        am = session_settings.actionmaps.new("actionmap", False)    
        if not am:
            return {'CANCELLED'}

        # Select newly created actionmap.
        session_settings.selected_actionmap = len(session_settings.actionmaps) - 1

        return {'FINISHED'}


class VIEW3D_OT_vr_actionmap_remove(Operator):
    bl_idname = "view3d.vr_actionmap_remove"
    bl_label = "Remove VR Action Map"
    bl_description = "Delete the selected VR action map from the scene"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        session_settings = context.window_manager.xr_session_settings

        am = action_map.vr_actionmap_selected_get(session_settings)
        if not am:
            return {'CANCELLED'}

        session_settings.actionmaps.remove(am)

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
        session_settings = context.window_manager.xr_session_settings
        if (self.index >= len(session_settings.actionmaps)):
            return {'CANCELLED'}

        session_settings.active_actionmap = (
            self.index if self.properties.is_property_set(
                "index") else session_settings.selected_actionmap
        )

        action_map.vr_actionset_active_update(context)

        return {'FINISHED'}


class VIEW3D_OT_vr_actionmaps_defaults_load(Operator):
    bl_idname = "view3d.vr_actionmaps_defaults_load"
    bl_label = "Load Default VR Action Maps"
    bl_description = "Load default VR action maps"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        session_settings = context.window_manager.xr_session_settings

        filepath = defaults.vr_get_default_config_path()

        if not action_map.vr_load_actionmaps(session_settings, filepath): 
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
        session_settings = context.window_manager.xr_session_settings

        filename, ext = os.path.splitext(self.filepath)
        if (ext != ".py"):
            return {'CANCELLED'}

        if not action_map.vr_load_actionmaps(session_settings, self.filepath):
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
        session_settings = context.window_manager.xr_session_settings

        filename, ext = os.path.splitext(self.filepath)
        if (ext != ".py"):
            return {'CANCELLED'}
        
        if not action_map.vr_save_actionmaps(session_settings, self.filepath):
            return {'CANCELLED'}
        
        return {'FINISHED'}


class VIEW3D_OT_vr_actionmap_copy(Operator):
    bl_idname = "view3d.vr_actionmap_copy"
    bl_label = "Copy VR Action Map"
    bl_description = "Copy selected VR action map"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        session_settings = context.window_manager.xr_session_settings

        am = action_map.vr_actionmap_selected_get(session_settings)
        if not am:
            return {'CANCELLED'}

        # Copy actionmap.
        am_new = session_settings.actionmaps.new_from_actionmap(am)
        if not am_new:
            return {'CANCELLED'}
        
        # Select newly created actionmap.
        session_settings.selected_actionmap = len(session_settings.actionmaps) - 1

        return {'FINISHED'}


class VIEW3D_OT_vr_actionmaps_clear(Operator):
    bl_idname = "view3d.vr_actionmaps_clear"
    bl_label = "Clear VR Action Maps"
    bl_description = "Delete all VR action maps from the scene"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        session_settings = context.window_manager.xr_session_settings

        while session_settings.actionmaps:
            session_settings.actionmaps.remove(session_settings.actionmaps[0])

        return {'FINISHED'} 


class VIEW3D_OT_vr_action_add(Operator):
    bl_idname = "view3d.vr_action_add"
    bl_label = "Add VR Action"
    bl_description = "Add a new VR action to the action map"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        session_settings = context.window_manager.xr_session_settings

        am = action_map.vr_actionmap_selected_get(session_settings)
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
        session_settings = context.window_manager.xr_session_settings

        am = action_map.vr_actionmap_selected_get(session_settings)
        if not am:
            return {'CANCELLED'}

        ami = action_map.vr_actionmap_item_selected_get(am)
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
        session_settings = context.window_manager.xr_session_settings

        am = action_map.vr_actionmap_selected_get(session_settings)
        if not am:
            return {'CANCELLED'}

        ami = action_map.vr_actionmap_item_selected_get(am)
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
        session_settings = context.window_manager.xr_session_settings

        am = action_map.vr_actionmap_selected_get(session_settings)
        if not am:
            return {'CANCELLED'}

        while am.actionmap_items:
            am.actionmap_items.remove(am.actionmap_items[0])

        return {'FINISHED'}


class VIEW3D_OT_vr_action_user_path_add(Operator):
    bl_idname = "view3d.vr_action_user_path_add"
    bl_label = "Add User Path"
    bl_description = "Add a new user path to the VR action"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        session_settings = context.window_manager.xr_session_settings

        am = action_map.vr_actionmap_selected_get(session_settings)
        if not am:
            return {'CANCELLED'}

        ami = action_map.vr_actionmap_item_selected_get(am)
        if not ami:
            return {'CANCELLED'}

        user_path = ami.user_paths.new("/")
        if not user_path:
            return {'CANCELLED'}

        # Select newly created user path.
        ami.selected_user_path = len(ami.user_paths) - 1

        return {'FINISHED'}


class VIEW3D_OT_vr_action_user_path_remove(Operator):
    bl_idname = "view3d.vr_action_user_path_remove"
    bl_label = "Remove User Path"
    bl_description = "Delete the selected user path from the VR action"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        session_settings = context.window_manager.xr_session_settings

        am = action_map.vr_actionmap_selected_get(session_settings)
        if not am:
            return {'CANCELLED'}

        ami = action_map.vr_actionmap_item_selected_get(am)
        if not ami:
            return {'CANCELLED'}

        user_path = action_map.vr_actionmap_user_path_selected_get(ami)
        if not user_path:
            return {'CANCELLED'}

        ami.user_paths.remove(user_path)

        return {'FINISHED'}


class VIEW3D_OT_vr_action_user_paths_clear(Operator):
    bl_idname = "view3d.vr_action_user_paths_clear"
    bl_label = "Clear User Paths"
    bl_description = "Delete all user paths from the VR action"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        session_settings = context.window_manager.xr_session_settings

        am = action_map.vr_actionmap_selected_get(session_settings)
        if not am:
            return {'CANCELLED'}

        ami = action_map.vr_actionmap_item_selected_get(am)
        if not ami:
            return {'CANCELLED'}

        while ami.user_paths:
            ami.user_paths.remove(ami.user_paths[0])

        return {'FINISHED'}


class VIEW3D_OT_vr_actionbinding_add(Operator):
    bl_idname = "view3d.vr_actionbinding_add"
    bl_label = "Add VR Action Binding"
    bl_description = "Add a new VR action binding to the action"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        session_settings = context.window_manager.xr_session_settings

        am = action_map.vr_actionmap_selected_get(session_settings)
        if not am:
            return {'CANCELLED'}

        ami = action_map.vr_actionmap_item_selected_get(am)
        if not ami:
            return {'CANCELLED'}

        amb = ami.bindings.new("binding", False)    
        if not amb:
            return {'CANCELLED'}

        # Select newly created binding.
        ami.selected_binding = len(ami.bindings) - 1

        return {'FINISHED'}


class VIEW3D_OT_vr_actionbinding_remove(Operator):
    bl_idname = "view3d.vr_actionbinding_remove"
    bl_label = "Remove VR Action Binding"
    bl_description = "Delete the selected VR action binding from the action"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        session_settings = context.window_manager.xr_session_settings

        am = action_map.vr_actionmap_selected_get(session_settings)
        if not am:
            return {'CANCELLED'}

        ami = action_map.vr_actionmap_item_selected_get(am)
        if not ami:
            return {'CANCELLED'}

        amb = action_map.vr_actionmap_binding_selected_get(ami)
        if not amb:
            return {'CANCELLED'}

        ami.bindings.remove(amb)

        return {'FINISHED'}


class VIEW3D_OT_vr_actionbinding_copy(Operator):
    bl_idname = "view3d.vr_actionbinding_copy"
    bl_label = "Copy VR Action Binding"
    bl_description = "Copy selected VR action binding"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        session_settings = context.window_manager.xr_session_settings

        am = action_map.vr_actionmap_selected_get(session_settings)
        if not am:
            return {'CANCELLED'}

        ami = action_map.vr_actionmap_item_selected_get(am)
        if not ami:
            return {'CANCELLED'}

        amb = action_map.vr_actionmap_binding_selected_get(ami)
        if not amb:
            return {'CANCELLED'}

        # Copy binding.
        amb_new = ami.bindings.new_from_binding(amb)
        if not amb_new:
            return {'CANCELLED'}
        
        # Select newly created binding.
        ami.selected_binding = len(ami.bindings) - 1

        return {'FINISHED'}


class VIEW3D_OT_vr_actionbindings_clear(Operator):
    bl_idname = "view3d.vr_actionbindings_clear"
    bl_label = "Clear VR Action Bindings"
    bl_description = "Delete all VR action bindings from the action"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        session_settings = context.window_manager.xr_session_settings

        am = action_map.vr_actionmap_selected_get(session_settings)
        if not am:
            return {'CANCELLED'}

        ami = action_map.vr_actionmap_item_selected_get(am)
        if not ami:
            return {'CANCELLED'}

        while ami.bindings:
            ami.bindings.remove(ami.bindings[0])

        return {'FINISHED'}


class VIEW3D_OT_vr_actionbinding_component_path_add(Operator):
    bl_idname = "view3d.vr_actionbinding_component_path_add"
    bl_label = "Add Component Path"
    bl_description = "Add a new component path to the VR action binding"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        session_settings = context.window_manager.xr_session_settings

        am = action_map.vr_actionmap_selected_get(session_settings)
        if not am:
            return {'CANCELLED'}

        ami = action_map.vr_actionmap_item_selected_get(am)
        if not ami:
            return {'CANCELLED'}

        amb = action_map.vr_actionmap_binding_selected_get(ami)
        if not amb:
            return {'CANCELLED'}

        component_path = amb.component_paths.new("/")
        if not component_path:
            return {'CANCELLED'}

        # Select newly created component path.
        amb.selected_component_path = len(amb.component_paths) - 1

        return {'FINISHED'}


class VIEW3D_OT_vr_actionbinding_component_path_remove(Operator):
    bl_idname = "view3d.vr_actionbinding_component_path_remove"
    bl_label = "Remove Component Path"
    bl_description = "Delete the selected component path from the VR action binding"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        session_settings = context.window_manager.xr_session_settings

        am = action_map.vr_actionmap_selected_get(session_settings)
        if not am:
            return {'CANCELLED'}

        ami = action_map.vr_actionmap_item_selected_get(am)
        if not ami:
            return {'CANCELLED'}

        amb = action_map.vr_actionmap_binding_selected_get(ami)
        if not amb:
            return {'CANCELLED'}

        component_path = action_map.vr_actionmap_component_path_selected_get(amb)
        if not component_path:
            return {'CANCELLED'}

        amb.component_paths.remove(component_path)

        return {'FINISHED'}


class VIEW3D_OT_vr_actionbinding_component_paths_clear(Operator):
    bl_idname = "view3d.vr_actionbinding_component_paths_clear"
    bl_label = "Clear Component Paths"
    bl_description = "Delete all component paths from the VR action binding"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        session_settings = context.window_manager.xr_session_settings

        am = action_map.vr_actionmap_selected_get(session_settings)
        if not am:
            return {'CANCELLED'}

        ami = action_map.vr_actionmap_item_selected_get(am)
        if not ami:
            return {'CANCELLED'}

        amb = action_map.vr_actionmap_binding_selected_get(ami)
        if not amb:
            return {'CANCELLED'}

        while amb.component_paths:
            amb.component_paths.remove(amb.component_paths[0])

        return {'FINISHED'}


### Motion capture.
class VIEW3D_OT_vr_mocap_object_add(Operator):
    bl_idname = "view3d.vr_mocap_object_add"
    bl_label = "Add VR Motion Capture Object"
    bl_description = "Add a new VR motion capture object"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        session_settings = context.window_manager.xr_session_settings

        mocap_ob = session_settings.mocap_objects.new(None)    
        if not mocap_ob:
            return {'CANCELLED'}

        # Enable object binding by default.
        mocap_ob.enable = True

        context.scene.vr_mocap_objects.add()

        # Select newly created object.
        session_settings.selected_mocap_object = len(session_settings.mocap_objects) - 1

        return {'FINISHED'}


class VIEW3D_OT_vr_mocap_object_remove(Operator):
    bl_idname = "view3d.vr_mocap_object_remove"
    bl_label = "Remove VR Motion Capture Object"
    bl_description = "Delete the selected VR motion capture object"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        session_settings = context.window_manager.xr_session_settings

        mocap_ob = properties.vr_mocap_object_selected_get(session_settings)
        if not mocap_ob:
            return {'CANCELLED'}

        context.scene.vr_mocap_objects.remove(session_settings.selected_mocap_object)

        session_settings.mocap_objects.remove(mocap_ob)

        return {'FINISHED'}


class VIEW3D_OT_vr_mocap_objects_enable(Operator):
    bl_idname = "view3d.vr_mocap_objects_enable"
    bl_label = "Enable VR Motion Capture Objects"
    bl_description = "Enable all VR motion capture objects"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        session_settings = context.window_manager.xr_session_settings

        for mocap_ob in session_settings.mocap_objects:
            mocap_ob.enable = True

        return {'FINISHED'}


class VIEW3D_OT_vr_mocap_objects_disable(Operator):
    bl_idname = "view3d.vr_mocap_objects_disable"
    bl_label = "Disable VR Motion Capture Objects"
    bl_description = "Disable all VR motion capture objects"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        session_settings = context.window_manager.xr_session_settings

        for mocap_ob in session_settings.mocap_objects:
            mocap_ob.enable = False

        return {'FINISHED'}


class VIEW3D_OT_vr_mocap_objects_clear(Operator):
    bl_idname = "view3d.vr_mocap_objects_clear"
    bl_label = "Clear VR Motion Capture Objects"
    bl_description = "Delete all VR motion capture objects from the scene"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        session_settings = context.window_manager.xr_session_settings

        context.scene.vr_mocap_objects.clear()

        while session_settings.mocap_objects:
            session_settings.mocap_objects.remove(session_settings.mocap_objects[0])

        return {'FINISHED'} 


class VIEW3D_OT_vr_mocap_object_help(Operator):
    bl_idname = "view3d.vr_mocap_object_help"
    bl_label = "Help"
    bl_description = "Display information about VR motion capture objects"
    bl_options = {'REGISTER'}

    def execute(self, context):
        info_header = "Common User Paths:"
        info_headset = "Headset - /user/head"
        info_left_controller = "Left Controller* - /user/hand/left"
        info_right_controller = "Right Controller* - /user/hand/right"
        info_note = "*Requires VR actions for controller poses"

        def draw(self, context):
            self.layout.label(text=info_header)
            self.layout.label(text=info_headset)
            self.layout.label(text=info_left_controller)
            self.layout.label(text=info_right_controller)
            self.layout.label(text=info_note)

        context.window_manager.popup_menu(draw, title="Motion Capture Objects", icon='INFO') 

        return {'FINISHED'}


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
        gpu.state.line_width_set(1.0)
        gpu.state.blend_set('ALPHA')

        self.draw_custom_shape(self.frame_shape)
        self.draw_custom_shape(self.lines_shape)


class VIEW3D_GT_vr_controller_grip(Gizmo):
    bl_idname = "VIEW_3D_GT_vr_controller_grip"

    def draw(self, context):
        gpu.state.line_width_set(1.0)
        gpu.state.blend_set('ALPHA')

        self.color = 0.422, 0.438, 0.446
        self.draw_preset_circle(self.matrix_basis, axis='POS_X')
        self.draw_preset_circle(self.matrix_basis, axis='POS_Y')
        self.draw_preset_circle(self.matrix_basis, axis='POS_Z')


class VIEW3D_GT_vr_controller_aim(Gizmo):
    bl_idname = "VIEW_3D_GT_vr_controller_aim"

    def draw(self, context):
        gpu.state.line_width_set(1.0)
        gpu.state.blend_set('ALPHA')

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
    def _get_controller_pose_matrix(context, idx, is_grip, scale):
        wm = context.window_manager

        loc = None
        rot = None
        if is_grip:
            loc = wm.xr_session_state.controller_grip_location_get(context, idx)
            rot = wm.xr_session_state.controller_grip_rotation_get(context, idx)
        else:
            loc = wm.xr_session_state.controller_aim_location_get(context, idx)
            rot = wm.xr_session_state.controller_aim_rotation_get(context, idx)

        rotmat = Matrix.Identity(3)
        rotmat.rotate(Quaternion(Vector(rot)))
        rotmat.resize_4x4()
        transmat = Matrix.Translation(loc)
        scalemat = Matrix.Scale(scale, 4)

        return transmat @ rotmat @ scalemat

    def setup(self, context):
        for idx in range(2):
            self.gizmos.new(VIEW3D_GT_vr_controller_grip.bl_idname)
            self.gizmos.new(VIEW3D_GT_vr_controller_aim.bl_idname)

        for gizmo in self.gizmos:
            gizmo.aspect = 1 / 3, 1 / 4
            gizmo.color_highlight = 1.0, 1.0, 1.0
            gizmo.alpha = 1.0

    def draw_prepare(self, context):
        grip_idx = 0
        aim_idx = 0
        idx = 0
        scale = 1.0
        for gizmo in self.gizmos:
            is_grip = (gizmo.bl_idname == VIEW3D_GT_vr_controller_grip.bl_idname)
            if (is_grip):
                idx = grip_idx
                grip_idx += 1
                scale = 0.1
            else:
                idx = aim_idx
                aim_idx += 1
                scale = 0.5
            gizmo.matrix_basis = self._get_controller_pose_matrix(context, idx, is_grip, scale)


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


classes = (
    VIEW3D_OT_vr_landmark_add,
    VIEW3D_OT_vr_landmark_remove,
    VIEW3D_OT_vr_landmark_activate,
    VIEW3D_OT_vr_landmark_from_session,
    VIEW3D_OT_vr_camera_landmark_from_session,
    VIEW3D_OT_add_camera_from_vr_landmark,
    VIEW3D_OT_camera_to_vr_landmark,
    VIEW3D_OT_vr_landmark_from_camera,
    VIEW3D_OT_cursor_to_vr_landmark,
    VIEW3D_OT_update_vr_landmark,

    VIEW3D_OT_vr_actionmap_add,
    VIEW3D_OT_vr_actionmap_remove,
    VIEW3D_OT_vr_actionmap_activate,
    VIEW3D_OT_vr_actionmaps_defaults_load,
    VIEW3D_OT_vr_actionmaps_import,
    VIEW3D_OT_vr_actionmaps_export,
    VIEW3D_OT_vr_actionmap_copy,
    VIEW3D_OT_vr_actionmaps_clear,
    VIEW3D_OT_vr_action_add,
    VIEW3D_OT_vr_action_remove,
    VIEW3D_OT_vr_action_copy,
    VIEW3D_OT_vr_actions_clear,
    VIEW3D_OT_vr_action_user_path_add,
    VIEW3D_OT_vr_action_user_path_remove,
    VIEW3D_OT_vr_action_user_paths_clear,
    VIEW3D_OT_vr_actionbinding_add,
    VIEW3D_OT_vr_actionbinding_remove,
    VIEW3D_OT_vr_actionbinding_copy,
    VIEW3D_OT_vr_actionbindings_clear,
    VIEW3D_OT_vr_actionbinding_component_path_add,
    VIEW3D_OT_vr_actionbinding_component_path_remove,
    VIEW3D_OT_vr_actionbinding_component_paths_clear,

    VIEW3D_OT_vr_mocap_object_add,
    VIEW3D_OT_vr_mocap_object_remove,
    VIEW3D_OT_vr_mocap_objects_enable,
    VIEW3D_OT_vr_mocap_objects_disable,
    VIEW3D_OT_vr_mocap_objects_clear,
    VIEW3D_OT_vr_mocap_object_help,

    VIEW3D_GT_vr_camera_cone,
    VIEW3D_GT_vr_controller_grip,
    VIEW3D_GT_vr_controller_aim,
    VIEW3D_GGT_vr_viewer_pose,
    VIEW3D_GGT_vr_controller_poses,
    VIEW3D_GGT_vr_landmarks,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
