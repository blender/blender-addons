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
    importlib.reload(defaults)
else:
    from . import action_map_io, defaults

import bpy
from bpy.app.handlers import persistent
from bpy_extras.io_utils import ExportHelper, ImportHelper
import importlib.util
import os.path


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


def vr_actionmap_binding_selected_get(ami):
    actionmap_bindings = ami.bindings
    return (
        None if (len(actionmap_bindings) <
                 1) else actionmap_bindings[ami.selected_binding]
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

    scene = context.scene

    for am in ac.actionmaps:    
        if len(am.actionmap_items) < 1:
            continue

        ok = session_state.action_set_create(context, am)
        if not ok:
            return

        controller_grip_name = ""
        controller_aim_name = ""

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

            for amb in ami.bindings:
                # Check for bindings that require OpenXR extensions.
                if amb.name == defaults.VRDefaultActionbindings.REVERB_G2.value:
                   if not scene.vr_actions_enable_reverb_g2:
                       continue
                elif amb.name == defaults.VRDefaultActionbindings.COSMOS.value:
                   if not scene.vr_actions_enable_cosmos:
                       continue
                elif amb.name == defaults.VRDefaultActionbindings.HUAWEI.value:
                   if not scene.vr_actions_enable_huawei:
                       continue

                ok = session_state.action_binding_create(context, am, ami, amb)
                if not ok:
                    return

        # Set controller pose actions.
        if controller_grip_name and controller_aim_name:
            session_state.controller_pose_actions_set(context, am.name, controller_grip_name, controller_aim_name)

    # Set active action set.
    am = vr_actionmap_active_get(ac)
    if am:
        session_state.active_action_set_set(context, am.name)


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

    action_map_io.actionconfig_init_from_data(ac, file.actionconfig_data, file.actionconfig_version)

    return True


def vr_save_actionmaps(context, filepath, sort=False):
    # Export all actionmaps for active actionconfig.
    actionconfigs = context.window_manager.xr_session_settings.actionconfigs
    if not actionconfigs:
        return False
    ac = actionconfigs.active
    if not ac:
        return False

    action_map_io.actionconfig_export_as_data(ac, filepath, sort=sort)

    print("Saved XR actionmaps: " + filepath)
    
    return True


def register():
    bpy.types.Scene.vr_actions_enable_cosmos = bpy.props.BoolProperty(
        description="Enable bindings for the HTC Vive Cosmos controllers. Note that this may not be supported by all OpenXR runtimes",
        default=False,
    )
    bpy.types.Scene.vr_actions_enable_huawei = bpy.props.BoolProperty(
        description="Enable bindings for the Huawei controllers. Note that this may not be supported by all OpenXR runtimes",
        default=False,
    )
    bpy.types.Scene.vr_actions_enable_reverb_g2 = bpy.props.BoolProperty(
        description="Enable bindings for the HP Reverb G2 controllers. Note that this may not be supported by all OpenXR runtimes",
        default=False,
    )

    bpy.app.handlers.load_post.append(vr_activate_user_actionconfig)
    bpy.app.handlers.xr_session_start_pre.append(vr_create_actions)


def unregister():
    del bpy.types.Scene.vr_actions_enable_cosmos
    del bpy.types.Scene.vr_actions_enable_huawei
    del bpy.types.Scene.vr_actions_enable_reverb_g2

    bpy.app.handlers.load_post.remove(vr_activate_user_actionconfig)
    bpy.app.handlers.xr_session_start_pre.remove(vr_create_actions)
