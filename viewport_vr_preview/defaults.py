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
from bpy.app.handlers import persistent
import os.path, importlib.util, math
from enum import Enum
from bl_keymap_utils.io import keyconfig_import_from_data_exec

def vr_defaults_action_set_add(scene, name, profile):
    bpy.ops.view3d.vr_action_set_add()
    
    action_set = scene.vr_action_sets[scene.vr_action_sets_selected]
    if action_set:
        action_set.name = name
        action_set.profile = profile
        
    return action_set


def vr_defaults_action_set_remove(scene, name):
    action_set_selected_prev = scene.vr_action_sets_selected
    
    idx = 0
    for action_set in scene.vr_action_sets:
        if (action_set.name == name):
            scene.vr_action_sets_selected = idx

            bpy.ops.view3d.vr_action_set_remove()

            scene.vr_action_sets_selected = action_set_selected_prev
            return

        idx += 1


def vr_defaults_action_add(action_set,
                           name,
                           user_path0,
                           component_path0,
                           user_path1,
                           component_path1,
                           threshold,
                           op,
                           op_flag):
    bpy.ops.view3d.vr_action_add()
    
    action = action_set.actions[action_set.actions_selected]
    if action:        
        action.name = name
        action.type = 'BUTTON'
        action.user_path0 = user_path0
        action.component_path0 = component_path0
        action.user_path1 = user_path1
        action.component_path1 = component_path1
        action.threshold = threshold
        action.op = op
        action.op_flag = op_flag
        
    return action


def vr_defaults_pose_action_add(action_set,
                                name,
                                user_path0,
                                component_path0,
                                user_path1,
                                component_path1,
                                is_controller,
                                location,
                                rotation):
    bpy.ops.view3d.vr_action_add()
    
    action = action_set.actions[action_set.actions_selected]
    if action:        
        action.name = name
        action.type = 'POSE'
        action.user_path0 = user_path0
        action.component_path0 = component_path0
        action.user_path1 = user_path1
        action.component_path1 = component_path1
        action.pose_is_controller = is_controller
        action.pose_location = location
        action.pose_rotation = rotation
        
    return action


def vr_defaults_haptic_action_add(action_set,
                                  name,
                                  user_path0,
                                  component_path0,
                                  user_path1,
                                  component_path1,
                                  duration,
                                  frequency,
                                  amplitude):
    bpy.ops.view3d.vr_action_add()
    
    action = action_set.actions[action_set.actions_selected]
    if action:        
        action.name = name
        action.type = 'HAPTIC'
        action.user_path0 = user_path0
        action.component_path0 = component_path0
        action.user_path1 = user_path1
        action.component_path1 = component_path1
        action.duration = duration
        action.frequency = frequency
        action.amplitude = amplitude
    
    return action


# Default action sets.
class VRDefaultActionSetNames(Enum):
    OCULUS = "default_oculus"
    WMR = "default_wmr"
    VIVE = "default_vive"
    INDEX = "default_index"

# Default actions.
class VRDefaultActionNames(Enum):
    CONTROLLER_POSE = "controller_pose"
    RAYCAST_SELECT = "raycast_select"
    GRAB = "grab"
    UNDO = "undo"
    REDO = "redo"


def vr_defaults_load_oculus(scene):
    action_set = vr_defaults_action_set_add(scene,
                                            VRDefaultActionSetNames.OCULUS.value,
                                            "/interaction_profiles/oculus/touch_controller")
    if not action_set:
        return

    vr_defaults_pose_action_add(action_set,
                                VRDefaultActionNames.CONTROLLER_POSE.value,
                                "/user/hand/left",
                                "/input/grip/pose",
                                "/user/hand/right",
                                "/input/grip/pose",
                                True,
                                (0, 0, 0),
                                (math.radians(-50), 0, 0)) 
    vr_defaults_action_add(action_set,
                           VRDefaultActionNames.RAYCAST_SELECT.value,
                           "/user/hand/left",
                           "/input/trigger/value",
                           "/user/hand/right",
                           "/input/trigger/value",
                           0.3,
                           "wm.xr_select_raycast",
                           'MODAL')      
    vr_defaults_action_add(action_set,
                           VRDefaultActionNames.GRAB.value,
                           "/user/hand/left",
                           "/input/squeeze/value",
                           "/user/hand/right",
                           "/input/squeeze/value",
                           0.3,
                           "wm.xr_grab",
                           'MODAL')
    vr_defaults_action_add(action_set,
                           VRDefaultActionNames.UNDO.value,
                           "/user/hand/left",
                           "/input/x/click",
                           "",
                           "",
                           0.3,
                           "ed.undo",
                           'PRESS')        
    vr_defaults_action_add(action_set,
                           VRDefaultActionNames.REDO.value,
                           "/user/hand/right",
                           "/input/a/click",
                           "",
                           "",
                           0.3,
                           "ed.redo",
                           'PRESS')

    action_set.actions_selected = 0


def vr_defaults_load_wmr(scene):
    action_set = vr_defaults_action_set_add(scene,
                                            VRDefaultActionSetNames.WMR.value,
                                            "/interaction_profiles/microsoft/motion_controller")
    if not action_set:
        return

    vr_defaults_pose_action_add(action_set,
                                VRDefaultActionNames.CONTROLLER_POSE.value,
                                "/user/hand/left",
                                "/input/grip/pose",
                                "/user/hand/right",
                                "/input/grip/pose",
                                True,
                                (0, 0, 0),
                                (math.radians(-45), 0, 0)) 
    vr_defaults_action_add(action_set,
                           VRDefaultActionNames.RAYCAST_SELECT.value,
                           "/user/hand/left",
                           "/input/trigger/value",
                           "/user/hand/right",
                           "/input/trigger/value",
                           0.3,
                           "wm.xr_select_raycast",
                           'MODAL')      
    vr_defaults_action_add(action_set,
                           VRDefaultActionNames.GRAB.value,
                           "/user/hand/left",
                           "/input/squeeze/click",
                           "/user/hand/right",
                           "/input/squeeze/click",
                           0.3,
                           "wm.xr_grab",
                           'MODAL')
    vr_defaults_action_add(action_set,
                           VRDefaultActionNames.UNDO.value,
                           "/user/hand/left",
                           "/input/menu/click",
                           "",
                           "",
                           0.3,
                           "ed.undo",
                           'PRESS')        
    vr_defaults_action_add(action_set,
                           VRDefaultActionNames.REDO.value,
                           "/user/hand/right",
                           "/input/menu/click",
                           "",
                           "",
                           0.3,
                           "ed.redo",
                           'PRESS')

    action_set.actions_selected = 0


def vr_defaults_load_vive(scene):
    action_set = vr_defaults_action_set_add(scene,
                                            VRDefaultActionSetNames.VIVE.value,
                                            "/interaction_profiles/htc/vive_controller")
    if not action_set:
        return

    vr_defaults_pose_action_add(action_set,
                                VRDefaultActionNames.CONTROLLER_POSE.value,
                                "/user/hand/left",
                                "/input/grip/pose",
                                "/user/hand/right",
                                "/input/grip/pose",
                                True,
                                (0, 0, 0),
                                (0, 0, 0)) 
    vr_defaults_action_add(action_set,
                           VRDefaultActionNames.RAYCAST_SELECT.value,
                           "/user/hand/left",
                           "/input/trigger/value",
                           "/user/hand/right",
                           "/input/trigger/value",
                           0.3,
                           "wm.xr_select_raycast",
                           'MODAL')      
    vr_defaults_action_add(action_set,
                           VRDefaultActionNames.GRAB.value,
                           "/user/hand/left",
                           "/input/squeeze/click",
                           "/user/hand/right",
                           "/input/squeeze/click",
                           0.3,
                           "wm.xr_grab",
                           'MODAL')
    vr_defaults_action_add(action_set,
                           VRDefaultActionNames.UNDO.value,
                           "/user/hand/left",
                           "/input/menu/click",
                           "",
                           "",
                           0.3,
                           "ed.undo",
                           'PRESS')        
    vr_defaults_action_add(action_set,
                           VRDefaultActionNames.REDO.value,
                           "/user/hand/right",
                           "/input/menu/click",
                           "",
                           "",
                           0.3,
                           "ed.redo",
                           'PRESS')

    action_set.actions_selected = 0


def vr_defaults_load_index(scene):
    action_set = vr_defaults_action_set_add(scene,
                                            VRDefaultActionSetNames.INDEX.value,
                                            "/interaction_profiles/valve/index_controller")
    if not action_set:
        return

    vr_defaults_pose_action_add(action_set,
                                VRDefaultActionNames.CONTROLLER_POSE.value,
                                "/user/hand/left",
                                "/input/grip/pose",
                                "/user/hand/right",
                                "/input/grip/pose",
                                True,
                                (0, 0, 0),
                                (0, 0, 0)) 
    vr_defaults_action_add(action_set,
                           VRDefaultActionNames.RAYCAST_SELECT.value,
                           "/user/hand/left",
                           "/input/trigger/value",
                           "/user/hand/right",
                           "/input/trigger/value",
                           0.3,
                           "wm.xr_select_raycast",
                           'MODAL')      
    vr_defaults_action_add(action_set,
                           VRDefaultActionNames.GRAB.value,
                           "/user/hand/left",
                           "/input/squeeze/value",
                           "/user/hand/right",
                           "/input/squeeze/value",
                           0.3,
                           "wm.xr_grab",
                           'MODAL')
    vr_defaults_action_add(action_set,
                           VRDefaultActionNames.UNDO.value,
                           "/user/hand/left",
                           "/input/a/click",
                           "",
                           "",
                           0.3,
                           "ed.undo",
                           'PRESS')        
    vr_defaults_action_add(action_set,
                           VRDefaultActionNames.REDO.value,
                           "/user/hand/right",
                           "/input/a/click",
                           "",
                           "",
                           0.3,
                           "ed.redo",
                           'PRESS')

    action_set.actions_selected = 0


@persistent
def vr_load_default_action_sets(context: bpy.context):
    scene = bpy.context.scene
    
    if len(scene.vr_action_sets) > 0:
        # Don't load defaults for scenes that already contain action sets.
        return

    # Load default action sets.
    vr_defaults_load_oculus(scene)
    vr_defaults_load_wmr(scene)
    vr_defaults_load_vive(scene)
    vr_defaults_load_index(scene)

    scene.vr_action_sets_selected = scene.vr_action_sets_active = 0

    # Load operator properties for default action sets.
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if not kc:
        return

    # Import XR Session key map.
    dirpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), '') 
    filename = os.path.splitext(os.path.basename(__file__))[0] + ".xrkey"
    filepath = dirpath + filename + ".py"

    if os.path.exists(filepath):                
        spec = importlib.util.spec_from_file_location(filename, filepath)
        xr_keymap = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(xr_keymap)

        keyconfig_import_from_data_exec(kc, xr_keymap.keyconfig_data, keyconfig_version=xr_keymap.keyconfig_version)


@persistent
def vr_unload_default_action_sets(context: bpy.context):
    scene = bpy.context.scene

    for name in VRDefaultActionSetNames:
        vr_defaults_action_set_remove(scene, name.value)
