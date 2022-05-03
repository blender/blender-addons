# SPDX-License-Identifier: GPL-2.0-or-later

# <pep8 compliant>

if "bpy" in locals():
    import importlib
    importlib.reload(action_map)
else:
    from . import action_map

import bpy
from enum import Enum
import math
import os.path


# Default action maps.
class VRDefaultActionmaps(Enum):
    DEFAULT = "blender_default"
    GAMEPAD = "blender_default_gamepad"
    TRACKER = "blender_default_tracker"

# Default actions.
class VRDefaultActions(Enum):
    CONTROLLER_GRIP = "controller_grip"
    CONTROLLER_AIM = "controller_aim"
    TRACKER_HANDHELD_OBJECT = "handheld_object"
    TRACKER_LEFT_FOOT = "left_foot"
    TRACKER_RIGHT_FOOT = "right_foot"
    TRACKER_LEFT_SHOULDER = "left_shoulder"
    TRACKER_RIGHT_SHOULDER = "right_shoulder"
    TRACKER_LEFT_ELBOW = "left_elbow"
    TRACKER_RIGHT_ELBOW = "right_elbow"
    TRACKER_LEFT_KNEE = "left_knee"
    TRACKER_RIGHT_KNEE = "right_knee"
    TRACKER_WAIST = "waist"
    TRACKER_CHEST = "chest"
    TRACKER_CAMERA = "camera"
    TRACKER_KEYBOARD = "keyboard"
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
    NAV_RESET = "nav_reset"
    SELECT = "select"
    TRANSFORM = "transform"
    UNDO = "undo"
    REDO = "redo"
    HAPTIC = "haptic"
    HAPTIC_LEFT = "haptic_left"
    HAPTIC_RIGHT = "haptic_right"
    HAPTIC_LEFTTRIGGER = "haptic_lefttrigger"
    HAPTIC_RIGHTTRIGGER = "haptic_righttrigger"


# Default action bindings.
class VRDefaultActionbindings(Enum):
    GAMEPAD = "gamepad"
    HUAWEI = "huawei"
    INDEX = "index"
    OCULUS = "oculus"
    REVERB_G2 = "reverb_g2"
    SIMPLE = "simple"
    VIVE = "vive"
    VIVE_COSMOS = "vive_cosmos"
    VIVE_FOCUS = "vive_focus"
    VIVE_TRACKER = "vive_tracker"
    WMR = "wmr"


class VRDefaultActionprofiles(Enum):
    GAMEPAD = "/interaction_profiles/microsoft/xbox_controller"
    HUAWEI = "/interaction_profiles/huawei/controller"
    INDEX = "/interaction_profiles/valve/index_controller"
    OCULUS = "/interaction_profiles/oculus/touch_controller"
    REVERB_G2 = "/interaction_profiles/hp/mixed_reality_controller"
    SIMPLE = "/interaction_profiles/khr/simple_controller"
    VIVE = "/interaction_profiles/htc/vive_controller"
    VIVE_COSMOS = "/interaction_profiles/htc/vive_cosmos_controller"
    VIVE_FOCUS = "/interaction_profiles/htc/vive_focus3_controller"
    VIVE_TRACKER = "/interaction_profiles/htc/vive_tracker_htcx"
    WMR = "/interaction_profiles/microsoft/motion_controller"


def vr_defaults_actionmap_add(session_settings, name):
    am = session_settings.actionmaps.new(name, True)

    return am


def vr_defaults_action_add(am,
                           name,
                           user_paths,
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
        for path in user_paths:
            ami.user_paths.new(path)
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
                                user_paths,
                                is_controller_grip,
                                is_controller_aim,
                                is_tracker):
    ami = am.actionmap_items.new(name, True)
    if ami:
        ami.type = 'POSE'
        for path in user_paths:
            ami.user_paths.new(path)
        ami.pose_is_controller_grip = is_controller_grip
        ami.pose_is_controller_aim = is_controller_aim
        ami.pose_is_tracker = is_tracker

    return ami


def vr_defaults_haptic_action_add(am,
                                  name,
                                  user_paths):
    ami = am.actionmap_items.new(name, True)
    if ami:
        ami.type = 'VIBRATION'
        for path in user_paths:
            ami.user_paths.new(path)

    return ami


def vr_defaults_actionbinding_add(ami,
                                  name,
                                  profile,
                                  component_paths,
                                  threshold,
                                  axis0_region,
                                  axis1_region):
    amb = ami.bindings.new(name, True)
    if amb:
        amb.profile = profile
        for path in component_paths:
            amb.component_paths.new(path)
        amb.threshold = threshold
        amb.axis0_region = axis0_region
        amb.axis1_region = axis1_region

    return amb


def vr_defaults_pose_actionbinding_add(ami,
                                  name,
                                  profile,
                                  component_paths,
                                  location,
                                  rotation):
    amb = ami.bindings.new(name, True)
    if amb:
        amb.profile = profile
        for path in component_paths:
            amb.component_paths.new(path)
        amb.pose_location = location
        amb.pose_rotation = rotation

    return amb


def vr_defaults_haptic_actionbinding_add(ami,
                                         name,
                                         profile,
                                         component_paths):
    amb = ami.bindings.new(name, True)
    if amb:
        amb.profile = profile
        for path in component_paths:
            amb.component_paths.new(path)

    return amb


def vr_defaults_create_default(session_settings):
    am = vr_defaults_actionmap_add(session_settings,
                                   VRDefaultActionmaps.DEFAULT.value)
    if not am:
        return

    ami = vr_defaults_pose_action_add(am,
                                      VRDefaultActions.CONTROLLER_GRIP.value,
                                      ["/user/hand/left",
                                      "/user/hand/right"],
                                      True,
                                      False,
                                      False)
    if ami:
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.HUAWEI.value,
                                           VRDefaultActionprofiles.HUAWEI.value,
                                           ["/input/grip/pose",
                                           "/input/grip/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.INDEX.value,
                                           VRDefaultActionprofiles.INDEX.value,
                                           ["/input/grip/pose",
                                           "/input/grip/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.OCULUS.value,
                                           VRDefaultActionprofiles.OCULUS.value,
                                           ["/input/grip/pose",
                                           "/input/grip/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.REVERB_G2.value,
                                           VRDefaultActionprofiles.REVERB_G2.value,
                                           ["/input/grip/pose",
                                           "/input/grip/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.SIMPLE.value,
                                           VRDefaultActionprofiles.SIMPLE.value,
                                           ["/input/grip/pose",
                                           "/input/grip/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.VIVE.value,
                                           VRDefaultActionprofiles.VIVE.value,
                                           ["/input/grip/pose",
                                           "/input/grip/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.VIVE_COSMOS.value,
                                           VRDefaultActionprofiles.VIVE_COSMOS.value,
                                           ["/input/grip/pose",
                                           "/input/grip/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.VIVE_FOCUS.value,
                                           VRDefaultActionprofiles.VIVE_FOCUS.value,
                                           ["/input/grip/pose",
                                           "/input/grip/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.WMR.value,
                                           VRDefaultActionprofiles.WMR.value,
                                           ["/input/grip/pose",
                                           "/input/grip/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))

    ami = vr_defaults_pose_action_add(am,
                                      VRDefaultActions.CONTROLLER_AIM.value,
                                      ["/user/hand/left",
                                      "/user/hand/right"],
                                      False,
                                      True,
                                      False)
    if ami:
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.HUAWEI.value,
                                           VRDefaultActionprofiles.HUAWEI.value,
                                           ["/input/aim/pose",
                                           "/input/aim/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.INDEX.value,
                                           VRDefaultActionprofiles.INDEX.value,
                                           ["/input/aim/pose",
                                           "/input/aim/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.OCULUS.value,
                                           VRDefaultActionprofiles.OCULUS.value,
                                           ["/input/aim/pose",
                                           "/input/aim/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.REVERB_G2.value,
                                           VRDefaultActionprofiles.REVERB_G2.value,
                                           ["/input/aim/pose",
                                           "/input/aim/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.SIMPLE.value,
                                           VRDefaultActionprofiles.SIMPLE.value,
                                           ["/input/aim/pose",
                                           "/input/aim/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.VIVE.value,
                                           VRDefaultActionprofiles.VIVE.value,
                                           ["/input/aim/pose",
                                           "/input/aim/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.VIVE_COSMOS.value,
                                           VRDefaultActionprofiles.VIVE_COSMOS.value,
                                           ["/input/aim/pose",
                                           "/input/aim/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.VIVE_FOCUS.value,
                                           VRDefaultActionprofiles.VIVE_FOCUS.value,
                                           ["/input/aim/pose",
                                           "/input/aim/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.WMR.value,
                                           VRDefaultActionprofiles.WMR.value,
                                           ["/input/aim/pose",
                                           "/input/aim/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.TELEPORT.value,
                                 ["/user/hand/left"],
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
                                      VRDefaultActionbindings.HUAWEI.value,
                                      VRDefaultActionprofiles.HUAWEI.value,
                                      ["/input/trigger/value"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.INDEX.value,
                                      VRDefaultActionprofiles.INDEX.value,
                                      ["/input/trigger/value"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.OCULUS.value,
                                      VRDefaultActionprofiles.OCULUS.value,
                                      ["/input/trigger/value"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.REVERB_G2.value,
                                      VRDefaultActionprofiles.REVERB_G2.value,
                                      ["/input/trigger/value"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.SIMPLE.value,
                                      VRDefaultActionprofiles.SIMPLE.value,
                                      ["/input/select/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE.value,
                                      VRDefaultActionprofiles.VIVE.value,
                                      ["/input/trigger/value"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE_COSMOS.value,
                                      VRDefaultActionprofiles.VIVE_COSMOS.value,
                                      ["/input/trigger/value"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE_FOCUS.value,
                                      VRDefaultActionprofiles.VIVE_FOCUS.value,
                                      ["/input/trigger/value"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.WMR.value,
                                      VRDefaultActionprofiles.WMR.value,
                                      ["/input/trigger/value"],
                                      0.3,
                                      'ANY',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.NAV_GRAB.value,
                                 ["/user/hand/left",
                                 "/user/hand/right"],
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
                                      VRDefaultActionbindings.HUAWEI.value,
                                      VRDefaultActionprofiles.HUAWEI.value,
                                      ["/input/trackpad/click",
                                      "/input/trackpad/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.INDEX.value,
                                      VRDefaultActionprofiles.INDEX.value,
                                      ["/input/squeeze/force",
                                      "/input/squeeze/force"],
                                      0.5,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.OCULUS.value,
                                      VRDefaultActionprofiles.OCULUS.value,
                                      ["/input/squeeze/value",
                                      "/input/squeeze/value"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.REVERB_G2.value,
                                      VRDefaultActionprofiles.REVERB_G2.value,
                                      ["/input/squeeze/value",
                                      "/input/squeeze/value"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.SIMPLE.value,
                                      VRDefaultActionprofiles.SIMPLE.value,
                                      ["/input/menu/click",
                                      "/input/menu/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE.value,
                                      VRDefaultActionprofiles.VIVE.value,
                                      ["/input/squeeze/click",
                                      "/input/squeeze/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE_COSMOS.value,
                                      VRDefaultActionprofiles.VIVE_COSMOS.value,
                                      ["/input/squeeze/click",
                                      "/input/squeeze/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE_FOCUS.value,
                                      VRDefaultActionprofiles.VIVE_FOCUS.value,
                                      ["/input/squeeze/click",
                                      "/input/squeeze/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.WMR.value,
                                      VRDefaultActionprofiles.WMR.value,
                                      ["/input/squeeze/click",
                                      "/input/squeeze/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY_FORWARD.value,
                                 ["/user/hand/left"],
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
                                      VRDefaultActionbindings.HUAWEI.value,
                                      VRDefaultActionprofiles.HUAWEI.value,
                                      ["/input/trackpad/y"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.INDEX.value,
                                      VRDefaultActionprofiles.INDEX.value,
                                      ["/input/thumbstick/y"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.OCULUS.value,
                                      VRDefaultActionprofiles.OCULUS.value,
                                      ["/input/thumbstick/y"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.REVERB_G2.value,
                                      VRDefaultActionprofiles.REVERB_G2.value,
                                      ["/input/thumbstick/y"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE.value,
                                      VRDefaultActionprofiles.VIVE.value,
                                      ["/input/trackpad/y"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE_COSMOS.value,
                                      VRDefaultActionprofiles.VIVE_COSMOS.value,
                                      ["/input/thumbstick/y"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE_FOCUS.value,
                                      VRDefaultActionprofiles.VIVE_FOCUS.value,
                                      ["/input/thumbstick/y"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.WMR.value,
                                      VRDefaultActionprofiles.WMR.value,
                                      ["/input/thumbstick/y"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY_BACK.value,
                                 ["/user/hand/left"],
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
                                      VRDefaultActionbindings.HUAWEI.value,
                                      VRDefaultActionprofiles.HUAWEI.value,
                                      ["/input/trackpad/y"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.INDEX.value,
                                      VRDefaultActionprofiles.INDEX.value,
                                      ["/input/thumbstick/y"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.OCULUS.value,
                                      VRDefaultActionprofiles.OCULUS.value,
                                      ["/input/thumbstick/y"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.REVERB_G2.value,
                                      VRDefaultActionprofiles.REVERB_G2.value,
                                      ["/input/thumbstick/y"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE.value,
                                      VRDefaultActionprofiles.VIVE.value,
                                      ["/input/trackpad/y"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE_COSMOS.value,
                                      VRDefaultActionprofiles.VIVE_COSMOS.value,
                                      ["/input/thumbstick/y"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE_FOCUS.value,
                                      VRDefaultActionprofiles.VIVE_FOCUS.value,
                                      ["/input/thumbstick/y"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.WMR.value,
                                      VRDefaultActionprofiles.WMR.value,
                                      ["/input/thumbstick/y"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY_LEFT.value,
                                 ["/user/hand/left"],
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
                                      VRDefaultActionbindings.HUAWEI.value,
                                      VRDefaultActionprofiles.HUAWEI.value,
                                      ["/input/trackpad/x"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.INDEX.value,
                                      VRDefaultActionprofiles.INDEX.value,
                                      ["/input/thumbstick/x"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.OCULUS.value,
                                      VRDefaultActionprofiles.OCULUS.value,
                                      ["/input/thumbstick/x"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.REVERB_G2.value,
                                      VRDefaultActionprofiles.REVERB_G2.value,
                                      ["/input/thumbstick/x"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE.value,
                                      VRDefaultActionprofiles.VIVE.value,
                                      ["/input/trackpad/x"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE_COSMOS.value,
                                      VRDefaultActionprofiles.VIVE_COSMOS.value,
                                      ["/input/thumbstick/x"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE_FOCUS.value,
                                      VRDefaultActionprofiles.VIVE_FOCUS.value,
                                      ["/input/thumbstick/x"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.WMR.value,
                                      VRDefaultActionprofiles.WMR.value,
                                      ["/input/thumbstick/x"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY_RIGHT.value,
                                 ["/user/hand/left"],
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
                                      VRDefaultActionbindings.HUAWEI.value,
                                      VRDefaultActionprofiles.HUAWEI.value,
                                      ["/input/trackpad/x"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.INDEX.value,
                                      VRDefaultActionprofiles.INDEX.value,
                                      ["/input/thumbstick/x"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.OCULUS.value,
                                      VRDefaultActionprofiles.OCULUS.value,
                                      ["/input/thumbstick/x"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.REVERB_G2.value,
                                      VRDefaultActionprofiles.REVERB_G2.value,
                                      ["/input/thumbstick/x"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE.value,
                                      VRDefaultActionprofiles.VIVE.value,
                                      ["/input/trackpad/x"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE_COSMOS.value,
                                      VRDefaultActionprofiles.VIVE_COSMOS.value,
                                      ["/input/thumbstick/x"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE_FOCUS.value,
                                      VRDefaultActionprofiles.VIVE_FOCUS.value,
                                      ["/input/thumbstick/x"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.WMR.value,
                                      VRDefaultActionprofiles.WMR.value,
                                      ["/input/thumbstick/x"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY_UP.value,
                                 ["/user/hand/right"],
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
                                      VRDefaultActionbindings.HUAWEI.value,
                                      VRDefaultActionprofiles.HUAWEI.value,
                                      ["/input/trackpad/y"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.INDEX.value,
                                      VRDefaultActionprofiles.INDEX.value,
                                      ["/input/thumbstick/y"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.OCULUS.value,
                                      VRDefaultActionprofiles.OCULUS.value,
                                      ["/input/thumbstick/y"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.REVERB_G2.value,
                                      VRDefaultActionprofiles.REVERB_G2.value,
                                      ["/input/thumbstick/y"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE.value,
                                      VRDefaultActionprofiles.VIVE.value,
                                      ["/input/trackpad/y"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE_COSMOS.value,
                                      VRDefaultActionprofiles.VIVE_COSMOS.value,
                                      ["/input/thumbstick/y"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE_FOCUS.value,
                                      VRDefaultActionprofiles.VIVE_FOCUS.value,
                                      ["/input/thumbstick/y"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.WMR.value,
                                      VRDefaultActionprofiles.WMR.value,
                                      ["/input/thumbstick/y"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY_DOWN.value,
                                 ["/user/hand/right"],
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
                                      VRDefaultActionbindings.HUAWEI.value,
                                      VRDefaultActionprofiles.HUAWEI.value,
                                      ["/input/trackpad/y"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.INDEX.value,
                                      VRDefaultActionprofiles.INDEX.value,
                                      ["/input/thumbstick/y"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.OCULUS.value,
                                      VRDefaultActionprofiles.OCULUS.value,
                                      ["/input/thumbstick/y"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.REVERB_G2.value,
                                      VRDefaultActionprofiles.REVERB_G2.value,
                                      ["/input/thumbstick/y"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE.value,
                                      VRDefaultActionprofiles.VIVE.value,
                                      ["/input/trackpad/y"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE_COSMOS.value,
                                      VRDefaultActionprofiles.VIVE_COSMOS.value,
                                      ["/input/thumbstick/y"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE_FOCUS.value,
                                      VRDefaultActionprofiles.VIVE_FOCUS.value,
                                      ["/input/thumbstick/y"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.WMR.value,
                                      VRDefaultActionprofiles.WMR.value,
                                      ["/input/thumbstick/y"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY_TURNLEFT.value,
                                 ["/user/hand/right"],
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
                                      VRDefaultActionbindings.HUAWEI.value,
                                      VRDefaultActionprofiles.HUAWEI.value,
                                      ["/input/trackpad/x"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.INDEX.value,
                                      VRDefaultActionprofiles.INDEX.value,
                                      ["/input/thumbstick/x"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.OCULUS.value,
                                      VRDefaultActionprofiles.OCULUS.value,
                                      ["/input/thumbstick/x"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.REVERB_G2.value,
                                      VRDefaultActionprofiles.REVERB_G2.value,
                                      ["/input/thumbstick/x"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE.value,
                                      VRDefaultActionprofiles.VIVE.value,
                                      ["/input/trackpad/x"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE_COSMOS.value,
                                      VRDefaultActionprofiles.VIVE_COSMOS.value,
                                      ["/input/thumbstick/x"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE_FOCUS.value,
                                      VRDefaultActionprofiles.VIVE_FOCUS.value,
                                      ["/input/thumbstick/x"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.WMR.value,
                                      VRDefaultActionprofiles.WMR.value,
                                      ["/input/thumbstick/x"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY_TURNRIGHT.value,
                                 ["/user/hand/right"],
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
                                      VRDefaultActionbindings.HUAWEI.value,
                                      VRDefaultActionprofiles.HUAWEI.value,
                                      ["/input/trackpad/x"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.INDEX.value,
                                      VRDefaultActionprofiles.INDEX.value,
                                      ["/input/thumbstick/x"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.OCULUS.value,
                                      VRDefaultActionprofiles.OCULUS.value,
                                      ["/input/thumbstick/x"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.REVERB_G2.value,
                                      VRDefaultActionprofiles.REVERB_G2.value,
                                      ["/input/thumbstick/x"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE.value,
                                      VRDefaultActionprofiles.VIVE.value,
                                      ["/input/trackpad/x"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE_COSMOS.value,
                                      VRDefaultActionprofiles.VIVE_COSMOS.value,
                                      ["/input/thumbstick/x"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE_FOCUS.value,
                                      VRDefaultActionprofiles.VIVE_FOCUS.value,
                                      ["/input/thumbstick/x"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.WMR.value,
                                      VRDefaultActionprofiles.WMR.value,
                                      ["/input/thumbstick/x"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.NAV_RESET.value,
                                 ["/user/hand/left",
                                 "/user/hand/right"],
                                 "wm.xr_navigation_reset",
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
                                      VRDefaultActionbindings.HUAWEI.value,
                                      VRDefaultActionprofiles.HUAWEI.value,
                                      ["/input/home/click",
                                      "/input/home/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.INDEX.value,
                                      VRDefaultActionprofiles.INDEX.value,
                                      ["/input/thumbstick/click",
                                      "/input/thumbstick/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.OCULUS.value,
                                      VRDefaultActionprofiles.OCULUS.value,
                                      ["/input/thumbstick/click",
                                      "/input/thumbstick/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.REVERB_G2.value,
                                      VRDefaultActionprofiles.REVERB_G2.value,
                                      ["/input/thumbstick/click",
                                      "/input/thumbstick/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE.value,
                                      VRDefaultActionprofiles.VIVE.value,
                                      ["/input/trackpad/click",
                                      "/input/trackpad/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE_COSMOS.value,
                                      VRDefaultActionprofiles.VIVE_COSMOS.value,
                                      ["/input/thumbstick/click",
                                      "/input/thumbstick/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE_FOCUS.value,
                                      VRDefaultActionprofiles.VIVE_FOCUS.value,
                                      ["/input/thumbstick/click",
                                      "/input/thumbstick/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.WMR.value,
                                      VRDefaultActionprofiles.WMR.value,
                                      ["/input/thumbstick/click",
                                      "/input/thumbstick/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.SELECT.value,
                                 ["/user/hand/right"],
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
                                      VRDefaultActionbindings.HUAWEI.value,
                                      VRDefaultActionprofiles.HUAWEI.value,
                                      ["/input/trigger/value"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.INDEX.value,
                                      VRDefaultActionprofiles.INDEX.value,
                                      ["/input/trigger/value"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.OCULUS.value,
                                      VRDefaultActionprofiles.OCULUS.value,
                                      ["/input/trigger/value"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.REVERB_G2.value,
                                      VRDefaultActionprofiles.REVERB_G2.value,
                                      ["/input/trigger/value"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.SIMPLE.value,
                                      VRDefaultActionprofiles.SIMPLE.value,
                                      ["/input/select/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE.value,
                                      VRDefaultActionprofiles.VIVE.value,
                                      ["/input/trigger/value"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE_COSMOS.value,
                                      VRDefaultActionprofiles.VIVE_COSMOS.value,
                                      ["/input/trigger/value"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE_FOCUS.value,
                                      VRDefaultActionprofiles.VIVE_FOCUS.value,
                                      ["/input/trigger/value"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.WMR.value,
                                      VRDefaultActionprofiles.WMR.value,
                                      ["/input/trigger/value"],
                                      0.3,
                                      'ANY',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.TRANSFORM.value,
                                 ["/user/hand/left",
                                 "/user/hand/right"],
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
                                      VRDefaultActionbindings.HUAWEI.value,
                                      VRDefaultActionprofiles.HUAWEI.value,
                                      ["/input/back/click",
                                      "/input/back/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.INDEX.value,
                                      VRDefaultActionprofiles.INDEX.value,
                                      ["/input/a/click",
                                      "/input/a/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.OCULUS.value,
                                      VRDefaultActionprofiles.OCULUS.value,
                                      ["/input/x/click",
                                      "/input/a/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.REVERB_G2.value,
                                      VRDefaultActionprofiles.REVERB_G2.value,
                                      ["/input/x/click",
                                      "/input/a/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE.value,
                                      VRDefaultActionprofiles.VIVE.value,
                                      ["/input/menu/click",
                                      "/input/menu/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE_COSMOS.value,
                                      VRDefaultActionprofiles.VIVE_COSMOS.value,
                                      ["/input/x/click",
                                      "/input/a/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE_FOCUS.value,
                                      VRDefaultActionprofiles.VIVE_FOCUS.value,
                                      ["/input/x/click",
                                      "/input/a/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.WMR.value,
                                      VRDefaultActionprofiles.WMR.value,
                                      ["/input/menu/click",
                                      "/input/menu/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.UNDO.value,
                                 ["/user/hand/left"],
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
                                      VRDefaultActionbindings.HUAWEI.value,
                                      VRDefaultActionprofiles.HUAWEI.value,
                                      ["/input/volume_down/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.INDEX.value,
                                      VRDefaultActionprofiles.INDEX.value,
                                      ["/input/b/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.OCULUS.value,
                                      VRDefaultActionprofiles.OCULUS.value,
                                      ["/input/y/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.REVERB_G2.value,
                                      VRDefaultActionprofiles.REVERB_G2.value,
                                      ["/input/y/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE_COSMOS.value,
                                      VRDefaultActionprofiles.VIVE_COSMOS.value,
                                      ["/input/y/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE_FOCUS.value,
                                      VRDefaultActionprofiles.VIVE_FOCUS.value,
                                      ["/input/y/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.WMR.value,
                                      VRDefaultActionprofiles.WMR.value,
                                      ["/input/trackpad/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.REDO.value,
                                 ["/user/hand/right"],
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
                                      VRDefaultActionbindings.HUAWEI.value,
                                      VRDefaultActionprofiles.HUAWEI.value,
                                      ["/input/volume_up/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.INDEX.value,
                                      VRDefaultActionprofiles.INDEX.value,
                                      ["/input/b/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.OCULUS.value,
                                      VRDefaultActionprofiles.OCULUS.value,
                                      ["/input/b/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.REVERB_G2.value,
                                      VRDefaultActionprofiles.REVERB_G2.value,
                                      ["/input/b/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE_COSMOS.value,
                                      VRDefaultActionprofiles.VIVE_COSMOS.value,
                                      ["/input/b/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.VIVE_FOCUS.value,
                                      VRDefaultActionprofiles.VIVE_FOCUS.value,
                                      ["/input/b/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')
        vr_defaults_actionbinding_add(ami,
                                      VRDefaultActionbindings.WMR.value,
                                      VRDefaultActionprofiles.WMR.value,
                                      ["/input/trackpad/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')

    ami = vr_defaults_haptic_action_add(am,
                                        VRDefaultActions.HAPTIC.value,
                                        ["/user/hand/left",
                                        "/user/hand/right"])
    if ami:
        vr_defaults_haptic_actionbinding_add(ami,
                                             VRDefaultActionbindings.HUAWEI.value,
                                             VRDefaultActionprofiles.HUAWEI.value,
                                             ["/output/haptic",
                                             "/output/haptic"])
        vr_defaults_haptic_actionbinding_add(ami,
                                             VRDefaultActionbindings.INDEX.value,
                                             VRDefaultActionprofiles.INDEX.value,
                                             ["/output/haptic",
                                             "/output/haptic"])
        vr_defaults_haptic_actionbinding_add(ami,
                                             VRDefaultActionbindings.OCULUS.value,
                                             VRDefaultActionprofiles.OCULUS.value,
                                             ["/output/haptic",
                                             "/output/haptic"])
        vr_defaults_haptic_actionbinding_add(ami,
                                             VRDefaultActionbindings.REVERB_G2.value,
                                             VRDefaultActionprofiles.REVERB_G2.value,
                                             ["/output/haptic",
                                             "/output/haptic"])
        vr_defaults_haptic_actionbinding_add(ami,
                                             VRDefaultActionbindings.SIMPLE.value,
                                             VRDefaultActionprofiles.SIMPLE.value,
                                             ["/output/haptic",
                                             "/output/haptic"])
        vr_defaults_haptic_actionbinding_add(ami,
                                             VRDefaultActionbindings.VIVE.value,
                                             VRDefaultActionprofiles.VIVE.value,
                                             ["/output/haptic",
                                             "/output/haptic"])
        vr_defaults_haptic_actionbinding_add(ami,
                                             VRDefaultActionbindings.VIVE_COSMOS.value,
                                             VRDefaultActionprofiles.VIVE_COSMOS.value,
                                             ["/output/haptic",
                                             "/output/haptic"])
        vr_defaults_haptic_actionbinding_add(ami,
                                             VRDefaultActionbindings.VIVE_FOCUS.value,
                                             VRDefaultActionprofiles.VIVE_FOCUS.value,
                                             ["/output/haptic",
                                             "/output/haptic"])
        vr_defaults_haptic_actionbinding_add(ami,
                                             VRDefaultActionbindings.WMR.value,
                                             VRDefaultActionprofiles.WMR.value,
                                             ["/output/haptic",
                                             "/output/haptic"])


def vr_defaults_create_default_gamepad(session_settings):
    am = vr_defaults_actionmap_add(session_settings,
                                   VRDefaultActionmaps.GAMEPAD.value)

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.TELEPORT.value,
                                 ["/user/gamepad"],
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
                                      ["/input/trigger_left/value"],
                                      0.3,
                                      'ANY',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY.value,
                                 ["/user/gamepad"],
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
                                      ["/input/a/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY_FORWARD.value,
                                 ["/user/gamepad"],
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
                                      ["/input/thumbstick_left/y"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY_BACK.value,
                                 ["/user/gamepad"],
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
                                      ["/input/thumbstick_left/y"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY_LEFT.value,
                                 ["/user/gamepad"],
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
                                      ["/input/thumbstick_left/x"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY_RIGHT.value,
                                 ["/user/gamepad"],
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
                                      ["/input/thumbstick_left/x"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY_UP.value,
                                 ["/user/gamepad"],
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
                                      ["/input/thumbstick_right/y"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY_DOWN.value,
                                 ["/user/gamepad"],
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
                                      ["/input/thumbstick_right/y"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY_TURNLEFT.value,
                                 ["/user/gamepad"],
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
                                      ["/input/thumbstick_right/x"],
                                      0.3,
                                      'NEGATIVE',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.FLY_TURNRIGHT.value,
                                 ["/user/gamepad"],
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
                                      ["/input/thumbstick_right/x"],
                                      0.3,
                                      'POSITIVE',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.NAV_RESET.value,
                                 ["/user/gamepad"],
                                 "wm.xr_navigation_reset",
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
                                      ["/input/y/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.SELECT.value,
                                 ["/user/gamepad"],
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
                                      ["/input/trigger_right/value"],
                                      0.3,
                                      'ANY',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.UNDO.value,
                                 ["/user/gamepad"],
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
                                      ["/input/x/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')

    ami = vr_defaults_action_add(am,
                                 VRDefaultActions.REDO.value,
                                 ["/user/gamepad"],
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
                                      ["/input/b/click"],
                                      0.3,
                                      'ANY',
                                      'ANY')

    ami =vr_defaults_haptic_action_add(am,
                                       VRDefaultActions.HAPTIC_LEFT.value,
                                       ["/user/gamepad"])
    if ami:
        vr_defaults_haptic_actionbinding_add(ami,
                                             VRDefaultActionbindings.GAMEPAD.value,
                                             VRDefaultActionprofiles.GAMEPAD.value,
                                             ["/output/haptic_left"])

    ami =vr_defaults_haptic_action_add(am,
                                       VRDefaultActions.HAPTIC_RIGHT.value,
                                       ["/user/gamepad"])
    if ami:
        vr_defaults_haptic_actionbinding_add(ami,
                                             VRDefaultActionbindings.GAMEPAD.value,
                                             VRDefaultActionprofiles.GAMEPAD.value,
                                             ["/output/haptic_right"])

    ami = vr_defaults_haptic_action_add(am,
                                        VRDefaultActions.HAPTIC_LEFTTRIGGER.value,
                                        ["/user/gamepad"])
    if ami:
        vr_defaults_haptic_actionbinding_add(ami,
                                             VRDefaultActionbindings.GAMEPAD.value,
                                             VRDefaultActionprofiles.GAMEPAD.value,
                                             ["/output/haptic_left_trigger"])

    ami = vr_defaults_haptic_action_add(am,
                                        VRDefaultActions.HAPTIC_RIGHTTRIGGER.value,
                                        ["/user/gamepad"])
    if ami:
        vr_defaults_haptic_actionbinding_add(ami,
                                             VRDefaultActionbindings.GAMEPAD.value,
                                             VRDefaultActionprofiles.GAMEPAD.value,
                                             ["/output/haptic_right_trigger"])


def vr_defaults_create_default_tracker(session_settings):
    am = vr_defaults_actionmap_add(session_settings,
                                   VRDefaultActionmaps.TRACKER.value)
    if not am:
        return

    ami = vr_defaults_pose_action_add(am,
                                      VRDefaultActions.CONTROLLER_GRIP.value,
                                      ["/user/hand/left",
                                      "/user/hand/right"],
                                      True,
                                      False,
                                      False)
    if ami:
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.HUAWEI.value,
                                           VRDefaultActionprofiles.HUAWEI.value,
                                           ["/input/grip/pose",
                                           "/input/grip/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.INDEX.value,
                                           VRDefaultActionprofiles.INDEX.value,
                                           ["/input/grip/pose",
                                           "/input/grip/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.OCULUS.value,
                                           VRDefaultActionprofiles.OCULUS.value,
                                           ["/input/grip/pose",
                                           "/input/grip/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.REVERB_G2.value,
                                           VRDefaultActionprofiles.REVERB_G2.value,
                                           ["/input/grip/pose",
                                           "/input/grip/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.SIMPLE.value,
                                           VRDefaultActionprofiles.SIMPLE.value,
                                           ["/input/grip/pose",
                                           "/input/grip/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.VIVE.value,
                                           VRDefaultActionprofiles.VIVE.value,
                                           ["/input/grip/pose",
                                           "/input/grip/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.VIVE_COSMOS.value,
                                           VRDefaultActionprofiles.VIVE_COSMOS.value,
                                           ["/input/grip/pose",
                                           "/input/grip/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.VIVE_FOCUS.value,
                                           VRDefaultActionprofiles.VIVE_FOCUS.value,
                                           ["/input/grip/pose",
                                           "/input/grip/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.WMR.value,
                                           VRDefaultActionprofiles.WMR.value,
                                           ["/input/grip/pose",
                                           "/input/grip/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))

    ami = vr_defaults_pose_action_add(am,
                                      VRDefaultActions.CONTROLLER_AIM.value,
                                      ["/user/hand/left",
                                      "/user/hand/right"],
                                      False,
                                      True,
                                      False)
    if ami:
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.HUAWEI.value,
                                           VRDefaultActionprofiles.HUAWEI.value,
                                           ["/input/aim/pose",
                                           "/input/aim/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.INDEX.value,
                                           VRDefaultActionprofiles.INDEX.value,
                                           ["/input/aim/pose",
                                           "/input/aim/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.OCULUS.value,
                                           VRDefaultActionprofiles.OCULUS.value,
                                           ["/input/aim/pose",
                                           "/input/aim/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.REVERB_G2.value,
                                           VRDefaultActionprofiles.REVERB_G2.value,
                                           ["/input/aim/pose",
                                           "/input/aim/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.SIMPLE.value,
                                           VRDefaultActionprofiles.SIMPLE.value,
                                           ["/input/aim/pose",
                                           "/input/aim/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.VIVE.value,
                                           VRDefaultActionprofiles.VIVE.value,
                                           ["/input/aim/pose",
                                           "/input/aim/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.VIVE_COSMOS.value,
                                           VRDefaultActionprofiles.VIVE_COSMOS.value,
                                           ["/input/aim/pose",
                                           "/input/aim/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.VIVE_FOCUS.value,
                                           VRDefaultActionprofiles.VIVE_FOCUS.value,
                                           ["/input/aim/pose",
                                           "/input/aim/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.WMR.value,
                                           VRDefaultActionprofiles.WMR.value,
                                           ["/input/aim/pose",
                                           "/input/aim/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))

    # SteamVR (1.21) fails to assign interaction profile.
#    ami = vr_defaults_pose_action_add(am,
#                                      VRDefaultActions.TRACKER_HANDHELD_OBJECT.value,
#                                      ["/user/vive_tracker_htcx/role/handheld_object"],
#                                      False,
#                                      False,
#                                      True)
#    if ami:
#        vr_defaults_pose_actionbinding_add(ami,
#                                           VRDefaultActionbindings.VIVE_TRACKER.value,
#                                           VRDefaultActionprofiles.VIVE_TRACKER.value,
#                                           ["/input/grip/pose"],
#                                           (0, 0, 0),
#                                           (0, 0, 0))

    ami = vr_defaults_pose_action_add(am,
                                      VRDefaultActions.TRACKER_LEFT_FOOT.value,
                                      ["/user/vive_tracker_htcx/role/left_foot"],
                                      False,
                                      False,
                                      True)
    if ami:
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.VIVE_TRACKER.value,
                                           VRDefaultActionprofiles.VIVE_TRACKER.value,
                                           ["/input/grip/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))

    ami = vr_defaults_pose_action_add(am,
                                      VRDefaultActions.TRACKER_RIGHT_FOOT.value,
                                      ["/user/vive_tracker_htcx/role/right_foot"],
                                      False,
                                      False,
                                      True)
    if ami:
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.VIVE_TRACKER.value,
                                           VRDefaultActionprofiles.VIVE_TRACKER.value,
                                           ["/input/grip/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))

    ami = vr_defaults_pose_action_add(am,
                                      VRDefaultActions.TRACKER_LEFT_SHOULDER.value,
                                      ["/user/vive_tracker_htcx/role/left_shoulder"],
                                      False,
                                      False,
                                      True)
    if ami:
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.VIVE_TRACKER.value,
                                           VRDefaultActionprofiles.VIVE_TRACKER.value,
                                           ["/input/grip/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))

    ami = vr_defaults_pose_action_add(am,
                                      VRDefaultActions.TRACKER_RIGHT_SHOULDER.value,
                                      ["/user/vive_tracker_htcx/role/right_shoulder"],
                                      False,
                                      False,
                                      True)
    if ami:
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.VIVE_TRACKER.value,
                                           VRDefaultActionprofiles.VIVE_TRACKER.value,
                                           ["/input/grip/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))

    ami = vr_defaults_pose_action_add(am,
                                      VRDefaultActions.TRACKER_LEFT_ELBOW.value,
                                      ["/user/vive_tracker_htcx/role/left_elbow"],
                                      False,
                                      False,
                                      True)
    if ami:
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.VIVE_TRACKER.value,
                                           VRDefaultActionprofiles.VIVE_TRACKER.value,
                                           ["/input/grip/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))

    ami = vr_defaults_pose_action_add(am,
                                      VRDefaultActions.TRACKER_RIGHT_ELBOW.value,
                                      ["/user/vive_tracker_htcx/role/right_elbow"],
                                      False,
                                      False,
                                      True)
    if ami:
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.VIVE_TRACKER.value,
                                           VRDefaultActionprofiles.VIVE_TRACKER.value,
                                           ["/input/grip/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))

    ami = vr_defaults_pose_action_add(am,
                                      VRDefaultActions.TRACKER_LEFT_KNEE.value,
                                      ["/user/vive_tracker_htcx/role/left_knee"],
                                      False,
                                      False,
                                      True)
    if ami:
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.VIVE_TRACKER.value,
                                           VRDefaultActionprofiles.VIVE_TRACKER.value,
                                           ["/input/grip/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))

    ami = vr_defaults_pose_action_add(am,
                                      VRDefaultActions.TRACKER_RIGHT_KNEE.value,
                                      ["/user/vive_tracker_htcx/role/right_knee"],
                                      False,
                                      False,
                                      True)
    if ami:
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.VIVE_TRACKER.value,
                                           VRDefaultActionprofiles.VIVE_TRACKER.value,
                                           ["/input/grip/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))

    ami = vr_defaults_pose_action_add(am,
                                      VRDefaultActions.TRACKER_WAIST.value,
                                      ["/user/vive_tracker_htcx/role/waist"],
                                      False,
                                      False,
                                      True)
    if ami:
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.VIVE_TRACKER.value,
                                           VRDefaultActionprofiles.VIVE_TRACKER.value,
                                           ["/input/grip/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))

    ami = vr_defaults_pose_action_add(am,
                                      VRDefaultActions.TRACKER_CHEST.value,
                                      ["/user/vive_tracker_htcx/role/chest"],
                                      False,
                                      False,
                                      True)
    if ami:
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.VIVE_TRACKER.value,
                                           VRDefaultActionprofiles.VIVE_TRACKER.value,
                                           ["/input/grip/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))

    ami = vr_defaults_pose_action_add(am,
                                      VRDefaultActions.TRACKER_CAMERA.value,
                                      ["/user/vive_tracker_htcx/role/camera"],
                                      False,
                                      False,
                                      True)
    if ami:
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.VIVE_TRACKER.value,
                                           VRDefaultActionprofiles.VIVE_TRACKER.value,
                                           ["/input/grip/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))

    ami = vr_defaults_pose_action_add(am,
                                      VRDefaultActions.TRACKER_KEYBOARD.value,
                                      ["/user/vive_tracker_htcx/role/keyboard"],
                                      False,
                                      False,
                                      True)
    if ami:
        vr_defaults_pose_actionbinding_add(ami,
                                           VRDefaultActionbindings.VIVE_TRACKER.value,
                                           VRDefaultActionprofiles.VIVE_TRACKER.value,
                                           ["/input/grip/pose"],
                                           (0, 0, 0),
                                           (0, 0, 0))


def vr_get_default_config_path():
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs")
    return os.path.join(filepath, "default.py")


def vr_ensure_default_actionmaps(session_settings):
    loaded = True

    for name in VRDefaultActionmaps:
        if not session_settings.actionmaps.find(name.value):
            loaded = False
            break

    if loaded:
        return loaded

    # Load default action maps.
    filepath = vr_get_default_config_path()

    if not os.path.exists(filepath):
        # Create and save default action maps.
        vr_defaults_create_default(session_settings)
        vr_defaults_create_default_gamepad(session_settings)
        vr_defaults_create_default_tracker(session_settings)

        action_map.vr_save_actionmaps(session_settings, filepath, sort=False)

    loaded = action_map.vr_load_actionmaps(session_settings, filepath)

    return loaded
