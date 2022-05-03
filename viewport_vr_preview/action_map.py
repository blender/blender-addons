# SPDX-License-Identifier: GPL-2.0-or-later

# <pep8 compliant>

if "bpy" in locals():
    import importlib
    importlib.reload(action_map_io)
    importlib.reload(defaults)
else:
    from . import action_map_io, defaults

import bpy
from bpy.app.handlers import persistent
from bpy_extras.io_utils import ExportHelper, ImportHelper
import importlib.util
import os.path


def vr_actionmap_active_get(session_settings):
    actionmaps = session_settings.actionmaps
    return (
        None if (len(actionmaps) <
                 1) else actionmaps[session_settings.active_actionmap]
    )


def vr_actionmap_selected_get(session_settings):
    actionmaps = session_settings.actionmaps
    return (
        None if (len(actionmaps) <
                 1) else actionmaps[session_settings.selected_actionmap]
    )


def vr_actionmap_item_selected_get(am):
    actionmap_items = am.actionmap_items
    return (
        None if (len(actionmap_items) <
                 1) else actionmap_items[am.selected_item]
    )


def vr_actionmap_user_path_selected_get(ami):
    user_paths = ami.user_paths
    return (
        None if (len(user_paths) <
                 1) else user_paths[ami.selected_user_path]
    )


def vr_actionmap_binding_selected_get(ami):
    actionmap_bindings = ami.bindings
    return (
        None if (len(actionmap_bindings) <
                 1) else actionmap_bindings[ami.selected_binding]
    )


def vr_actionmap_component_path_selected_get(amb):
    component_paths = amb.component_paths
    return (
        None if (len(component_paths) <
                 1) else component_paths[amb.selected_component_path]
    )


def vr_actionset_active_update(context):
    session_state = context.window_manager.xr_session_state
    if not session_state:
        return

    session_settings = context.window_manager.xr_session_settings
    am = vr_actionmap_active_get(session_settings)
    if not am:
        return

    session_state.active_action_set_set(context, am.name)


@persistent
def vr_create_actions(context: bpy.context):
    context = bpy.context
    session_state = context.window_manager.xr_session_state
    if not session_state:
        return

    # Check if actions are enabled.
    scene = context.scene
    if not scene.vr_actions_enable:
        return

    session_settings = context.window_manager.xr_session_settings

    if (len(session_settings.actionmaps) < 1):
        # Ensure default action maps.
        if not defaults.vr_ensure_default_actionmaps(session_settings):
            return

    for am in session_settings.actionmaps:    
        if len(am.actionmap_items) < 1:
            continue

        # Check for action maps where all bindings require OpenXR extensions.
        if am.name == defaults.VRDefaultActionmaps.TRACKER.value:
            if not session_settings.enable_vive_tracker_extension: #scene.vr_actions_enable_vive_tracker:
                continue

        ok = session_state.action_set_create(context, am)
        if not ok:
            return

        controller_grip_name = ""
        controller_aim_name = ""
        tracker_names = []

        for ami in am.actionmap_items:
            if len(ami.bindings) < 1:
                continue

            ok = session_state.action_create(context, am, ami)
            if not ok:
                return

            if ami.type == 'POSE':
                if ami.pose_is_controller_grip:
                    controller_grip_name = ami.name
                if ami.pose_is_controller_aim:
                    controller_aim_name = ami.name
                if ami.pose_is_tracker:
                    tracker_names.append(ami.name)

            for amb in ami.bindings:
                # Check for bindings that require OpenXR extensions.
                if amb.name == defaults.VRDefaultActionbindings.REVERB_G2.value:
                   if not scene.vr_actions_enable_reverb_g2:
                       continue
                elif amb.name == defaults.VRDefaultActionbindings.VIVE_COSMOS.value:
                   if not scene.vr_actions_enable_vive_cosmos:
                       continue
                elif amb.name == defaults.VRDefaultActionbindings.VIVE_FOCUS.value:
                   if not scene.vr_actions_enable_vive_focus:
                       continue
                elif amb.name == defaults.VRDefaultActionbindings.HUAWEI.value:
                   if not scene.vr_actions_enable_huawei:
                       continue

                ok = session_state.action_binding_create(context, am, ami, amb)
                if not ok:
                    return

        # Set controller and tracker pose actions.
        if controller_grip_name and controller_aim_name:
            session_state.controller_pose_actions_set(context, am.name, controller_grip_name, controller_aim_name)

        for tracker_name in tracker_names:
            session_state.tracker_pose_action_add(context, am.name, tracker_name)

    # Set active action set.
    vr_actionset_active_update(context)


def vr_load_actionmaps(session_settings, filepath):
    if not os.path.exists(filepath):
        return False

    spec = importlib.util.spec_from_file_location(os.path.basename(filepath), filepath)
    file = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(file)

    action_map_io.actionconfig_init_from_data(session_settings, file.actionconfig_data, file.actionconfig_version)

    return True


def vr_save_actionmaps(session_settings, filepath, sort=False):
    action_map_io.actionconfig_export_as_data(session_settings, filepath, sort=sort)

    print("Saved XR actionmaps: " + filepath)
    
    return True


def register():
    bpy.types.Scene.vr_actions_enable = bpy.props.BoolProperty(
        name="Use Controller Actions",
        description="Enable default VR controller actions, including controller poses and haptics",
        default=True,
    )
    bpy.types.Scene.vr_actions_enable_huawei = bpy.props.BoolProperty(
        description="Enable bindings for the Huawei controllers. Note that this may not be supported by all OpenXR runtimes",
        default=False,
    )
    bpy.types.Scene.vr_actions_enable_reverb_g2 = bpy.props.BoolProperty(
        description="Enable bindings for the HP Reverb G2 controllers. Note that this may not be supported by all OpenXR runtimes",
        default=False,
    )
    bpy.types.Scene.vr_actions_enable_vive_cosmos = bpy.props.BoolProperty(
        description="Enable bindings for the HTC Vive Cosmos controllers. Note that this may not be supported by all OpenXR runtimes",
        default=False,
    )
    bpy.types.Scene.vr_actions_enable_vive_focus = bpy.props.BoolProperty(
        description="Enable bindings for the HTC Vive Focus 3 controllers. Note that this may not be supported by all OpenXR runtimes",
        default=False,
    )
    # Stored in session settings to use in session creation as a workaround for SteamVR controller/tracker compatibility issues. 
    #bpy.types.Scene.vr_actions_enable_vive_tracker = bpy.props.BoolProperty(
    #    description="Enable bindings for the HTC Vive Trackers. Note that this may not be supported by all OpenXR runtimes",
    #    default=False,
    #)

    bpy.app.handlers.xr_session_start_pre.append(vr_create_actions)


def unregister():
    del bpy.types.Scene.vr_actions_enable
    del bpy.types.Scene.vr_actions_enable_huawei
    del bpy.types.Scene.vr_actions_enable_reverb_g2
    del bpy.types.Scene.vr_actions_enable_vive_cosmos
    del bpy.types.Scene.vr_actions_enable_vive_focus
    #del bpy.types.Scene.vr_actions_enable_vive_tracker

    bpy.app.handlers.xr_session_start_pre.remove(vr_create_actions)
