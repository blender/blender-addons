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
    importlib.reload(main)
else:
    from . import main

import bpy
from bpy.app.handlers import persistent
from enum import Enum
import math


# Default action maps.
class VRDefaultActionmaps(Enum):
    DEFAULT = "blender_default"
    GAMEPAD = "blender_default_gamepad"


# Default actions.
class VRDefaultActions(Enum):
    CONTROLLER_GRIP = "controller_grip"
    CONTROLLER_AIM = "controller_aim"
    TELEPORT = "teleport"
    NAV_GRAB = "nav_grab"
    FLY = "fly"
    FLY_FORWARD = "fly_forward"
    FLY_BACK = "fly_back"
    FLY_LEFT = "fly_left"
    FLY_RIGHT = "fly_right"
    FLY_UP = "fly_up"
    FLY_DOWN = "fly_down"
    FLY_TURNLEFT = "fly_turnleft"
    FLY_TURNRIGHT = "fly_turnright"
    RAYCAST_SELECT = "raycast_select"
    GRAB = "grab"
    UNDO = "undo"
    REDO = "redo"
    HAPTIC = "haptic"
    HAPTIC_LEFT = "haptic_left"
    HAPTIC_RIGHT = "haptic_right"
    HAPTIC_LEFTTRIGGER = "haptic_lefttrigger"
    HAPTIC_RIGHTTRIGGER = "haptic_righttrigger"

# Default action bindings.
class VRDefaultActionbindings(Enum):
    SIMPLE = "simple"
    OCULUS = "oculus"
    WMR = "wmr"
    VIVE = "vive"
    INDEX = "index"
    GAMEPAD = "gamepad"


class VRDefaultActionprofiles(Enum):
    SIMPLE = "/interaction_profiles/khr/simple_controller"
    OCULUS = "/interaction_profiles/oculus/touch_controller"
    WMR = "/interaction_profiles/microsoft/motion_controller"
    VIVE = "/interaction_profiles/htc/vive_controller"
    INDEX = "/interaction_profiles/valve/index_controller"
    GAMEPAD = "/interaction_profiles/microsoft/xbox_controller"


def vr_defaults_actionmap_add(ac, name):
    am = ac.actionmaps.new(name, True)

    return am


def vr_defaults_action_add(am,
                           name,
                           user_path0,
                           user_path1,
                           op,
                           op_mode,
                           bimanual,
                           haptic_name,
                           haptic_match_user_paths,
                           haptic_duration,
                           haptic_frequency,
                           haptic_amplitude,
                           haptic_mode):


    ami = am.actionmap_items.new(name, True)
    if ami:        
        ami.type = 'FLOAT'
        ami.user_path0 = user_path0
        ami.user_path1 = user_path1
        ami.op = op
        ami.op_mode = op_mode
        ami.bimanual = bimanual
        ami.haptic_name = haptic_name
        ami.haptic_match_user_paths = haptic_match_user_paths
        ami.haptic_duration = haptic_duration
        ami.haptic_frequency = haptic_frequency
        ami.haptic_amplitude = haptic_amplitude
        ami.haptic_mode = haptic_mode

    return ami


def vr_defaults_pose_action_add(am,
                                name,
                                user_path0,
                                user_path1,
                                is_controller_grip,
                                is_controller_aim):
    ami = am.actionmap_items.new(name, True)
    if ami:             
        ami.type = 'POSE'
        ami.user_path0 = user_path0
        ami.user_path1 = user_path1
        ami.pose_is_controller_grip = is_controller_grip
        ami.pose_is_controller_aim = is_controller_aim

    return ami


def vr_defaults_haptic_action_add(am,
                                  name,
                                  user_path0,
                                  user_path1):
    ami = am.actionmap_items.new(name, True)
    if ami:        
        ami.type = 'VIBRATION'
        ami.user_path0 = user_path0
        ami.user_path1 = user_path1
    
    return ami


def vr_defaults_actionbinding_add(ami,
                                  name,
                                  profile,
                                  component_path0,
                                  component_path1,
                                  threshold,
                                  axis0_region,
                                  axis1_region):
    amb = ami.bindings.new(name, True)    
    if amb:
        amb.profile = profile
        amb.component_path0 = component_path0
        amb.component_path1 = component_path1
        amb.threshold = threshold
        amb.axis0_region = axis0_region
        amb.axis1_region = axis1_region

    return amb


def vr_defaults_pose_actionbinding_add(ami,
                                  name,
                                  profile,
                                  component_path0,
                                  component_path1,
                                  location,
                                  rotation):
    amb = ami.bindings.new(name, True)    
    if amb:
        amb.profile = profile
        amb.component_path0 = component_path0
        amb.component_path1 = component_path1
        amb.pose_location = location
        amb.pose_rotation = rotation

    return amb


def vr_defaults_haptic_actionbinding_add(ami,
                                         name,
                                         profile,
                                         component_path0,
                                         component_path1):
    amb = ami.bindings.new(name, True)    
    if amb:
        amb.profile = profile
        amb.component_path0 = component_path0
        amb.component_path1 = component_path1


    return amb


def vr_defaults_create_default(ac):
    am = vr_defaults_actionmap_add(ac,
                                   VRDefaultActionmaps.DEFAULT.value)
    if not am:
        return

    ami = vr_defaults_pose_action_add(am,
                                      VRDefaultActions.CONTROLLER_GRIP.value,
                                      "/user/hand/left",
                                      "/user/hand/right",
                                      True,
                                      False)
    if ami:
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.SIMPLE.value,
                                           VRDefaultActionprofiles.SIMPLE.value,
                                           "/input/grip/pose",
                                           "/input/grip/pose",
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.OCULUS.value,
                                           VRDefaultActionprofiles.OCULUS.value,
                                           "/input/grip/pose",
                                           "/input/grip/pose",
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.WMR.value,
                                           VRDefaultActionprofiles.WMR.value,
                                           "/input/grip/pose",
                                           "/input/grip/pose",
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.VIVE.value,
                                           VRDefaultActionprofiles.VIVE.value,
                                           "/input/grip/pose",
                                           "/input/grip/pose",
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.INDEX.value,
                                           VRDefaultActionprofiles.INDEX.value,
                                           "/input/grip/pose",
                                           "/input/grip/pose",
                                           (0, 0, 0),
                                           (0, 0, 0))

    ami = vr_defaults_pose_action_add(am,
                                      VRDefaultActions.CONTROLLER_AIM.value,
                                      "/user/hand/left",
                                      "/user/hand/right",
                                      False,
                                      True)
    if ami:
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.SIMPLE.value,
                                           VRDefaultActionprofiles.SIMPLE.value,
                                           "/input/aim/pose",
                                           "/input/aim/pose",
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.OCULUS.value,
                                           VRDefaultActionprofiles.OCULUS.value,
                                           "/input/aim/pose",
                                           "/input/aim/pose",
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.WMR.value,
                                           VRDefaultActionprofiles.WMR.value,
                                           "/input/aim/pose",
                                           "/input/aim/pose",
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.VIVE.value,
                                           VRDefaultActionprofiles.VIVE.value,
                                           "/input/aim/pose",
                                           "/input/aim/pose",
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.INDEX.value,
                                           VRDefaultActionprofiles.INDEX.value,
                                           "/input/aim/pose",
                                           "/input/aim/pose",
                                           (0, 0, 0),
                                           (0, 0, 0))

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.TELEPORT.value,
                                 "/user/hand/left",
                                 "",
                                 "wm.xr_navigation_teleport",
                                 'MODAL',
                                 False,
                                 "",
                                 False,
                                 0.0,
                                 0.0,
                                 0.0,
                                 'PRESS')
    if ami:
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.SIMPLE.value,
                                      VRDefaultActionprofiles.SIMPLE.value,
                                      "/input/select/click",
                                      "",
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.OCULUS.value,
                                      VRDefaultActionprofiles.OCULUS.value,
                                      "/input/trigger/value",
                                      "",
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.WMR.value,
                                      VRDefaultActionprofiles.WMR.value,
                                      "/input/trigger/value",
                                      "",
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE.value,
                                      VRDefaultActionprofiles.VIVE.value,
                                      "/input/trigger/value",
                                      "",
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.INDEX.value,
                                      VRDefaultActionprofiles.INDEX.value,
                                      "/input/trigger/value",
                                      "",
                                      0.3,
                                      'ANY',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.NAV_GRAB.value,
                                 "/user/hand/left",
                                 "/user/hand/right",
                                 "wm.xr_navigation_grab",
                                 'MODAL',
                                 True,
                                 "",
                                 False,
                                 0.0,
                                 0.0,
                                 0.0,
                                 'PRESS')
    if ami:
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.OCULUS.value,
                                      VRDefaultActionprofiles.OCULUS.value,
                                      "/input/squeeze/value",
                                      "/input/squeeze/value",
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.WMR.value,
                                      VRDefaultActionprofiles.WMR.value,
                                      "/input/squeeze/click",
                                      "/input/squeeze/click",
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE.value,
                                      VRDefaultActionprofiles.VIVE.value,
                                      "/input/squeeze/click",
                                      "/input/squeeze/click",
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.INDEX.value,
                                      VRDefaultActionprofiles.INDEX.value,
                                      "/input/squeeze/value",
                                      "/input/squeeze/value",
                                      0.3,
                                      'ANY',
                                      'ANY')
    
    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY.value,
                                 "/user/hand/left",
                                 "/user/hand/right",
                                 "wm.xr_navigation_fly",
                                 'MODAL',
                                 False,
                                 "",
                                 False,
                                 0.0,
                                 0.0,
                                 0.0,
                                 'PRESS')
    if ami:
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.OCULUS.value,
                                      VRDefaultActionprofiles.OCULUS.value,
                                      "/input/thumbstick/click",
                                      "/input/thumbstick/click",
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.WMR.value,
                                      VRDefaultActionprofiles.WMR.value,
                                      "/input/thumbstick/click",
                                      "/input/thumbstick/click",
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.INDEX.value,
                                      VRDefaultActionprofiles.INDEX.value,
                                      "/input/thumbstick/click",
                                      "/input/thumbstick/click",
                                      0.3,
                                      'ANY',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY_FORWARD.value,
                                 "/user/hand/left",
                                 "",
                                 "wm.xr_navigation_fly",
                                 'MODAL',
                                 False,
                                 "",
                                 False,
                                 0.0,
                                 0.0,
                                 0.0,
                                 'PRESS')
    if ami:
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.OCULUS.value,
                                      VRDefaultActionprofiles.OCULUS.value,
                                      "/input/thumbstick/y",
                                      "",
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.WMR.value,
                                      VRDefaultActionprofiles.WMR.value,
                                      "/input/thumbstick/y",
                                      "",
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE.value,
                                      VRDefaultActionprofiles.VIVE.value,
                                      "/input/trackpad/y",
                                      "",
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.INDEX.value,
                                      VRDefaultActionprofiles.INDEX.value,
                                      "/input/thumbstick/y",
                                      "",
                                      0.3,
                                      'POSITIVE',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY_BACK.value,
                                 "/user/hand/left",
                                 "",
                                 "wm.xr_navigation_fly",
                                 'MODAL',
                                 False,
                                 "",
                                 False,
                                 0.0,
                                 0.0,
                                 0.0,
                                 'PRESS')
    if ami:
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.OCULUS.value,
                                      VRDefaultActionprofiles.OCULUS.value,
                                      "/input/thumbstick/y",
                                      "",
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.WMR.value,
                                      VRDefaultActionprofiles.WMR.value,
                                      "/input/thumbstick/y",
                                      "",
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE.value,
                                      VRDefaultActionprofiles.VIVE.value,
                                      "/input/trackpad/y",
                                      "",
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.INDEX.value,
                                      VRDefaultActionprofiles.INDEX.value,
                                      "/input/thumbstick/y",
                                      "",
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY_LEFT.value,
                                 "/user/hand/left",
                                 "",
                                 "wm.xr_navigation_fly",
                                 'MODAL',
                                 False,
                                 "",
                                 False,
                                 0.0,
                                 0.0,
                                 0.0,                                         
                                 'PRESS')
    if ami:
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.OCULUS.value,
                                      VRDefaultActionprofiles.OCULUS.value,
                                      "/input/thumbstick/x",
                                      "",
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.WMR.value,
                                      VRDefaultActionprofiles.WMR.value,
                                      "/input/thumbstick/x",
                                      "",
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE.value,
                                      VRDefaultActionprofiles.VIVE.value,
                                      "/input/trackpad/x",
                                      "",
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.INDEX.value,
                                      VRDefaultActionprofiles.INDEX.value, 
                                      "/input/thumbstick/x",
                                      "",
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY_RIGHT.value,
                                 "/user/hand/left",
                                 "",
                                 "wm.xr_navigation_fly",
                                 'MODAL',
                                 False,
                                 "",
                                 False,
                                 0.0,
                                 0.0,
                                 0.0,
                                 'PRESS')
    if ami:
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.OCULUS.value,
                                      VRDefaultActionprofiles.OCULUS.value, 
                                      "/input/thumbstick/x",
                                      "",
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.WMR.value,
                                      VRDefaultActionprofiles.WMR.value,
                                      "/input/thumbstick/x",
                                      "",
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE.value,
                                      VRDefaultActionprofiles.VIVE.value,
                                      "/input/trackpad/x",
                                      "",
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.INDEX.value,
                                      VRDefaultActionprofiles.INDEX.value,
                                      "/input/thumbstick/x",
                                      "",
                                      0.3,
                                      'POSITIVE',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY_UP.value,
                                 "/user/hand/right",
                                 "",
                                 "wm.xr_navigation_fly",
                                 'MODAL',
                                 False,
                                 "",
                                 False,
                                 0.0,
                                 0.0,
                                 0.0,
                                 'PRESS')
    if ami:
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.OCULUS.value,
                                      VRDefaultActionprofiles.OCULUS.value,
                                      "/input/thumbstick/y",
                                      "",
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.WMR.value,
                                      VRDefaultActionprofiles.WMR.value,
                                      "/input/thumbstick/y",
                                      "",
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE.value,
                                      VRDefaultActionprofiles.VIVE.value,
                                      "/input/trackpad/y",
                                      "",
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.INDEX.value,
                                      VRDefaultActionprofiles.INDEX.value,
                                      "/input/thumbstick/y",
                                      "",
                                      0.3,
                                      'POSITIVE',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY_DOWN.value,
                                 "/user/hand/right",
                                 "",
                                 "wm.xr_navigation_fly",
                                 'MODAL',
                                 False,
                                 "",
                                 False,
                                 0.0,
                                 0.0,
                                 0.0,
                                 'PRESS')
    if ami:
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.OCULUS.value,
                                      VRDefaultActionprofiles.OCULUS.value,
                                      "/input/thumbstick/y",
                                      "",
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.WMR.value,
                                      VRDefaultActionprofiles.WMR.value,
                                      "/input/thumbstick/y",
                                      "",
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE.value,
                                      VRDefaultActionprofiles.VIVE.value,
                                      "/input/trackpad/y",
                                      "",
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.INDEX.value,
                                      VRDefaultActionprofiles.INDEX.value,
                                      "/input/thumbstick/y",
                                      "",
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY_TURNLEFT.value,
                                 "/user/hand/right",
                                 "",
                                 "wm.xr_navigation_fly",
                                 'MODAL',
                                 False,
                                 "",
                                 False,
                                 0.0,
                                 0.0,
                                 0.0,
                                 'PRESS')
    if ami:
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.OCULUS.value,
                                      VRDefaultActionprofiles.OCULUS.value,
                                      "/input/thumbstick/x",
                                      "",
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.WMR.value,
                                      VRDefaultActionprofiles.WMR.value,
                                      "/input/thumbstick/x",
                                      "",
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE.value,
                                      VRDefaultActionprofiles.VIVE.value,
                                      "/input/trackpad/x",
                                      "",
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.INDEX.value,
                                      VRDefaultActionprofiles.INDEX.value,
                                      "/input/thumbstick/x",
                                      "",
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY_TURNRIGHT.value,
                                 "/user/hand/right",
                                 "",
                                 "wm.xr_navigation_fly",
                                 'MODAL',
                                 False,
                                 "",
                                 False,
                                 0.0,
                                 0.0,
                                 0.0,
                                 'PRESS')
    if ami:
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.OCULUS.value,
                                      VRDefaultActionprofiles.OCULUS.value,
                                      "/input/thumbstick/x",
                                      "",
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.WMR.value,
                                      VRDefaultActionprofiles.WMR.value,
                                      "/input/thumbstick/x",
                                      "",
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE.value,
                                      VRDefaultActionprofiles.VIVE.value,
                                      "/input/trackpad/x",
                                      "",
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.INDEX.value,
                                      VRDefaultActionprofiles.INDEX.value,
                                      "/input/thumbstick/x",
                                      "",
                                      0.3,
                                      'POSITIVE',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.RAYCAST_SELECT.value,
                                 "/user/hand/right",
                                 "",
                                 "wm.xr_select_raycast",
                                 'MODAL',
                                 False,
                                 "",
                                 False,
                                 0.0,
                                 0.0,
                                 0.0,
                                 'PRESS')
    if ami:
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.SIMPLE.value,
                                      VRDefaultActionprofiles.SIMPLE.value,
                                      "/input/select/click",
                                      "",
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.OCULUS.value,
                                      VRDefaultActionprofiles.OCULUS.value,
                                      "/input/trigger/value",
                                      "",
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.WMR.value,
                                      VRDefaultActionprofiles.WMR.value,
                                      "/input/trigger/value",
                                      "",
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE.value,
                                      VRDefaultActionprofiles.VIVE.value,
                                      "/input/trigger/value",
                                      "",
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.INDEX.value,
                                      VRDefaultActionprofiles.INDEX.value,
                                      "/input/trigger/value",
                                      "",
                                      0.3,
                                      'ANY',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.GRAB.value,
                                 "/user/hand/left",
                                 "/user/hand/right",
                                 "wm.xr_transform_grab",
                                 'MODAL',
                                 True,
                                 "",
                                 False,
                                 0.0,
                                 0.0,
                                 0.0,
                                 'PRESS')
    if ami:
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.SIMPLE.value,
                                      VRDefaultActionprofiles.SIMPLE.value,
                                      "/input/menu/click",
                                      "/input/menu/click",
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.OCULUS.value,
                                      VRDefaultActionprofiles.OCULUS.value,
                                      "/input/x/click",
                                      "/input/a/click",
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.WMR.value,
                                      VRDefaultActionprofiles.WMR.value,
                                      "/input/menu/click",
                                      "/input/menu/click",
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE.value,
                                      VRDefaultActionprofiles.VIVE.value,
                                      "/input/menu/click",
                                      "/input/menu/click",
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.INDEX.value,
                                      VRDefaultActionprofiles.INDEX.value,
                                      "/input/a/click",
                                      "/input/a/click",
                                      0.3,
                                      'ANY',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.UNDO.value,
                                 "/user/hand/left",
                                 "",
                                 "ed.undo",
                                 'PRESS',
                                 False,
                                 "haptic",
                                 True,
                                 0.3,
                                 3000.0,
                                 0.5,
                                 'PRESS')
    if ami:
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.OCULUS.value,
                                      VRDefaultActionprofiles.OCULUS.value,
                                      "/input/y/click",
                                      "",
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.WMR.value,
                                      VRDefaultActionprofiles.WMR.value,
                                      "/input/trackpad/click",
                                      "",
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE.value,
                                      VRDefaultActionprofiles.VIVE.value,
                                      "/input/trackpad/click",
                                      "",
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.INDEX.value,
                                      VRDefaultActionprofiles.INDEX.value,
                                      "/input/b/click",
                                      "",
                                      0.3,
                                      'ANY',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.REDO.value,
                                 "/user/hand/right",
                                 "",
                                 "ed.redo",
                                 'PRESS',
                                 False,
                                 "haptic",
                                 True,
                                 0.3,
                                 3000.0,
                                 0.5,
                                 'PRESS')
    if ami:
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.OCULUS.value,
                                      VRDefaultActionprofiles.OCULUS.value,
                                      "/input/b/click",
                                      "",
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.WMR.value,
                                      VRDefaultActionprofiles.WMR.value,
                                      "/input/trackpad/click",
                                      "",
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE.value,
                                      VRDefaultActionprofiles.VIVE.value,
                                      "/input/trackpad/click",
                                      "",
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.INDEX.value,
                                      VRDefaultActionprofiles.INDEX.value,
                                      "/input/b/click",
                                      "",
                                      0.3,
                                      'ANY',
                                      'ANY')

    ami = vr_defaults_haptic_action_add(am,
                                        VRDefaultActions.HAPTIC.value,
                                        "/user/hand/left",
                                        "/user/hand/right")
    if ami:
        vr_defaults_haptic_actionbinding_add(ami,
                                             VRDefaultActionbindings.SIMPLE.value,
                                             VRDefaultActionprofiles.SIMPLE.value,
                                             "/output/haptic",
                                             "/output/haptic")
        vr_defaults_haptic_actionbinding_add(ami,
                                             VRDefaultActionbindings.OCULUS.value,
                                             VRDefaultActionprofiles.OCULUS.value,
                                             "/output/haptic",
                                             "/output/haptic")
        vr_defaults_haptic_actionbinding_add(ami,
                                             VRDefaultActionbindings.WMR.value,
                                             VRDefaultActionprofiles.WMR.value,
                                             "/output/haptic",
                                             "/output/haptic")
        vr_defaults_haptic_actionbinding_add(ami,
                                             VRDefaultActionbindings.VIVE.value,
                                             VRDefaultActionprofiles.VIVE.value,
                                             "/output/haptic",
                                             "/output/haptic")
        vr_defaults_haptic_actionbinding_add(ami,
                                             VRDefaultActionbindings.INDEX.value,
                                             VRDefaultActionprofiles.INDEX.value,
                                             "/output/haptic",
                                             "/output/haptic")


def vr_defaults_create_default_gamepad(ac):
    am = vr_defaults_actionmap_add(ac,
                                   VRDefaultActionmaps.GAMEPAD.value)

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.TELEPORT.value,
                                 "/user/gamepad",
                                 "",
                                 "wm.xr_navigation_teleport",
                                 'MODAL',
                                 False,
                                 "",
                                 False,
                                 0.0,
                                 0.0,
                                 0.0,
                                 'PRESS')
    if ami:
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.GAMEPAD.value,
                                      VRDefaultActionprofiles.GAMEPAD.value,
                                      "/input/trigger_left/value",
                                      "",
                                      0.3,
                                      'ANY',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY.value,
                                 "/user/gamepad",
                                 "",
                                 "wm.xr_navigation_fly",
                                 'MODAL',
                                 False,
                                 "",
                                 False,
                                 0.0,
                                 0.0,
                                 0.0,
                                 'PRESS')
    if ami:
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.GAMEPAD.value,
                                      VRDefaultActionprofiles.GAMEPAD.value,
                                      "/input/a/click",
                                      "",
                                      0.3,
                                      'ANY',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY_FORWARD.value,
                                 "/user/gamepad",
                                 "",
                                 "wm.xr_navigation_fly",
                                 'MODAL',
                                 False,
                                 "",
                                 False,
                                 0.0,
                                 0.0,
                                 0.0,
                                 'PRESS')
    if ami:
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.GAMEPAD.value,
                                      VRDefaultActionprofiles.GAMEPAD.value,
                                      "/input/thumbstick_left/y",
                                      "",
                                      0.3,
                                      'POSITIVE',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY_BACK.value,
                                 "/user/gamepad",
                                 "",
                                 "wm.xr_navigation_fly",
                                 'MODAL',
                                 False,
                                 "",
                                 False,
                                 0.0,
                                 0.0,
                                 0.0,
                                 'PRESS')
    if ami:
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.GAMEPAD.value,
                                      VRDefaultActionprofiles.GAMEPAD.value,
                                      "/input/thumbstick_left/y",
                                      "",
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY_LEFT.value,
                                 "/user/gamepad",
                                 "",
                                 "wm.xr_navigation_fly",
                                 'MODAL',
                                 False,
                                 "",
                                 False,
                                 0.0,
                                 0.0,
                                 0.0,
                                 'PRESS')
    if ami:
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.GAMEPAD.value,
                                      VRDefaultActionprofiles.GAMEPAD.value,
                                      "/input/thumbstick_left/x",
                                      "",
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY_RIGHT.value,
                                 "/user/gamepad",
                                 "",
                                 "wm.xr_navigation_fly",
                                 'MODAL',
                                 False,
                                 "",
                                 False,
                                 0.0,
                                 0.0,
                                 0.0,
                                 'PRESS')
    if ami:
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.GAMEPAD.value,
                                      VRDefaultActionprofiles.GAMEPAD.value,
                                      "/input/thumbstick_left/x",
                                      "",
                                      0.3,
                                      'POSITIVE',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY_UP.value,
                                 "/user/gamepad",
                                 "",
                                 "wm.xr_navigation_fly",
                                 'MODAL',
                                 False,
                                 "",
                                 False,
                                 0.0,
                                 0.0,
                                 0.0,
                                 'PRESS')
    if ami:
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.GAMEPAD.value,
                                      VRDefaultActionprofiles.GAMEPAD.value,
                                      "/input/thumbstick_right/y",
                                      "",
                                      0.3,
                                      'POSITIVE',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY_DOWN.value,
                                 "/user/gamepad",
                                 "",
                                 "wm.xr_navigation_fly",
                                 'MODAL',
                                 False,
                                 "",
                                 False,
                                 0.0,
                                 0.0,
                                 0.0,
                                 'PRESS')
    if ami:
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.GAMEPAD.value,
                                      VRDefaultActionprofiles.GAMEPAD.value,
                                      "/input/thumbstick_right/y",
                                      "",
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY_TURNLEFT.value,
                                 "/user/gamepad",
                                 "",
                                 "wm.xr_navigation_fly",
                                 'MODAL',
                                 False,
                                 "",
                                 False,
                                 0.0,
                                 0.0,
                                 0.0,
                                 'PRESS')
    if ami:
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.GAMEPAD.value,
                                      VRDefaultActionprofiles.GAMEPAD.value,
                                      "/input/thumbstick_right/x",
                                      "",
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY_TURNRIGHT.value,
                                 "/user/gamepad",
                                 "",
                                 "wm.xr_navigation_fly",
                                 'MODAL',
                                 False,
                                 "",
                                 False,
                                 0.0,
                                 0.0,
                                 0.0,
                                 'PRESS')
    if ami:
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.GAMEPAD.value,
                                      VRDefaultActionprofiles.GAMEPAD.value,
                                      "/input/thumbstick_right/x",
                                      "",
                                      0.3,
                                      'POSITIVE',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.RAYCAST_SELECT.value,
                                 "/user/gamepad",
                                 "",
                                 "wm.xr_select_raycast",
                                 'MODAL',
                                 False,
                                 "",
                                 False,
                                 0.0,
                                 0.0,
                                 0.0,
                                 'PRESS')
    if ami:
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.GAMEPAD.value,
                                      VRDefaultActionprofiles.GAMEPAD.value,
                                      "/input/trigger_right/value",
                                      "",
                                      0.3,
                                      'ANY',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.UNDO.value,
                                 "/user/gamepad",
                                 "",
                                 "ed.undo",
                                 'PRESS',
                                 False,
                                 "haptic_left",
                                 True,
                                 0.3,
                                 3000.0,
                                 0.5,
                                 'PRESS')
    if ami:
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.GAMEPAD.value,
                                      VRDefaultActionprofiles.GAMEPAD.value,
                                      "/input/x/click",
                                      "",
                                      0.3,
                                      'ANY',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.REDO.value,
                                 "/user/gamepad",
                                 "",
                                 "ed.redo",
                                 'PRESS',
                                 False,
                                 "haptic_right",
                                 True,
                                 0.3,
                                 3000.0,
                                 0.5,
                                 'PRESS')
    if ami:
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.GAMEPAD.value,
                                      VRDefaultActionprofiles.GAMEPAD.value,
                                      "/input/b/click",
                                      "",
                                      0.3,
                                      'ANY',
                                      'ANY')

    ami =vr_defaults_haptic_action_add(am,
                                       VRDefaultActions.HAPTIC_LEFT.value,
                                       "/user/gamepad",
                                       "")
    if ami:
        vr_defaults_haptic_actionbinding_add(ami,
                                             VRDefaultActionbindings.GAMEPAD.value,
                                             VRDefaultActionprofiles.GAMEPAD.value,
                                             "/output/haptic_left",
                                             "")

    ami =vr_defaults_haptic_action_add(am,
                                       VRDefaultActions.HAPTIC_RIGHT.value,
                                       "/user/gamepad",
                                       "")
    if ami:
        vr_defaults_haptic_actionbinding_add(ami,
                                             VRDefaultActionbindings.GAMEPAD.value,
                                             VRDefaultActionprofiles.GAMEPAD.value,                                              
                                             "/output/haptic_right",
                                             "")

    ami = vr_defaults_haptic_action_add(am,
                                        VRDefaultActions.HAPTIC_LEFTTRIGGER.value,
                                        "/user/gamepad",
                                        "")
    if ami:
        vr_defaults_haptic_actionbinding_add(ami,
                                             VRDefaultActionbindings.GAMEPAD.value,
                                             VRDefaultActionprofiles.GAMEPAD.value,                                              
                                             "/output/haptic_left_trigger",
                                             "")

    ami = vr_defaults_haptic_action_add(am,
                                        VRDefaultActions.HAPTIC_RIGHTTRIGGER.value,
                                        "/user/gamepad",
                                        "")
    if ami:
        vr_defaults_haptic_actionbinding_add(ami,
                                             VRDefaultActionbindings.GAMEPAD.value,
                                             VRDefaultActionprofiles.GAMEPAD.value,                                              
                                             "/output/haptic_right_trigger",
                                             "")


@persistent
def vr_init_default_actionconfig(context: bpy.context):
    context = bpy.context

    actionconfigs = context.window_manager.xr_session_settings.actionconfigs
    if not actionconfigs:
        return
    ac = actionconfigs.default
    if not ac:
        return

    # Set default config as active.
    actionconfigs.active = ac

    # Load default actionmaps.
    filepath = main.vr_get_default_config_path()

    loaded = main.vr_load_actionmaps(context, filepath)
    
    if not loaded:
        # Create and save default actionmaps.
        vr_defaults_create_default(ac)
        vr_defaults_create_default_gamepad(ac)

        main.vr_save_actionmaps(context, filepath, sort=False)
