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
import math
from enum import Enum


def vr_defaults_actionmap_add(ac, name, profile):
    am = ac.actionmaps.new(name)    
    if am:
        am.profile = profile

    return am


def vr_defaults_actionmap_item_add(am,
                                   name,
                                   user_path0,
                                   component_path0,
                                   user_path1,
                                   component_path1,
                                   threshold,
                                   op,
                                   op_flag):

    ami = am.actionmap_items.new(name)
    if ami:        
        ami.type = 'BUTTON'
        ami.user_path0 = user_path0
        ami.component_path0 = component_path0
        ami.user_path1 = user_path1
        ami.component_path1 = component_path1
        ami.threshold = threshold
        ami.op = op
        ami.op_flag = op_flag

    return ami


def vr_defaults_pose_actionmap_item_add(am,
                                        name,
                                        user_path0,
                                        component_path0,
                                        user_path1,
                                        component_path1,
                                        is_controller,
                                        location,
                                        rotation):
    ami = am.actionmap_items.new(name)
    if ami:             
        ami.type = 'POSE'
        ami.user_path0 = user_path0
        ami.component_path0 = component_path0
        ami.user_path1 = user_path1
        ami.component_path1 = component_path1
        ami.pose_is_controller = is_controller
        ami.pose_location = location
        ami.pose_rotation = rotation

    return ami


def vr_defaults_haptic_actionmap_item_add(am,
                                          name,
                                          user_path0,
                                          component_path0,
                                          user_path1,
                                          component_path1,
                                          duration,
                                          frequency,
                                          amplitude):
    ami = am.actionmap_items.new(name)
    if ami:        
        ami.type = 'HAPTIC'
        ami.user_path0 = user_path0
        ami.component_path0 = component_path0
        ami.user_path1 = user_path1
        ami.component_path1 = component_path1
        ami.duration = duration
        ami.frequency = frequency
        ami.amplitude = amplitude
    
    return ami


# Default actionmaps.
class VRDefaultActionmapNames(Enum):
    OCULUS = "default_oculus"
    WMR = "default_wmr"
    VIVE = "default_vive"
    INDEX = "default_index"

# Default actionmap items.
class VRDefaultActionmapItemNames(Enum):
    CONTROLLER_POSE = "controller_pose"
    RAYCAST_SELECT = "raycast_select"
    GRAB = "grab"
    UNDO = "undo"
    REDO = "redo"


def vr_defaults_create_oculus(ac):
    am = vr_defaults_actionmap_add(ac,
                                   VRDefaultActionmapNames.OCULUS.value,
                                   "/interaction_profiles/oculus/touch_controller")
    if not am:
        return

    vr_defaults_pose_actionmap_item_add(am,
                                        VRDefaultActionmapItemNames.CONTROLLER_POSE.value,
                                        "/user/hand/left",
                                        "/input/grip/pose",
                                        "/user/hand/right",
                                        "/input/grip/pose",
                                        True,
                                        (0, 0, 0),
                                        (math.radians(-50), 0, 0)) 
    vr_defaults_actionmap_item_add(am,
                                   VRDefaultActionmapItemNames.RAYCAST_SELECT.value,
                                   "/user/hand/left",
                                   "/input/trigger/value",
                                   "/user/hand/right",
                                   "/input/trigger/value",
                                   0.3,
                                   "wm.xr_select_raycast",
                                   'MODAL')      
    vr_defaults_actionmap_item_add(am,
                                   VRDefaultActionmapItemNames.GRAB.value,
                                   "/user/hand/left",
                                   "/input/squeeze/value",
                                   "/user/hand/right",
                                   "/input/squeeze/value",
                                   0.3,
                                   "wm.xr_grab",
                                   'MODAL')
    vr_defaults_actionmap_item_add(am,
                                   VRDefaultActionmapItemNames.UNDO.value,
                                   "/user/hand/left",
                                   "/input/x/click",
                                   "",
                                   "",
                                   0.3,
                                   "ed.undo",
                                   'PRESS')        
    vr_defaults_actionmap_item_add(am,
                                   VRDefaultActionmapItemNames.REDO.value,
                                   "/user/hand/right",
                                   "/input/a/click",
                                   "",
                                   "",
                                   0.3,
                                   "ed.redo",
                                   'PRESS')


def vr_defaults_create_wmr(ac):
    am = vr_defaults_actionmap_add(ac,
                                   VRDefaultActionmapNames.WMR.value,
                                   "/interaction_profiles/microsoft/motion_controller")
    if not am:
        return

    vr_defaults_pose_actionmap_item_add(am,
                                        VRDefaultActionmapItemNames.CONTROLLER_POSE.value,
                                        "/user/hand/left",
                                        "/input/grip/pose",
                                        "/user/hand/right",
                                        "/input/grip/pose",
                                        True,
                                        (0, 0, 0),
                                        (math.radians(-45), 0, 0)) 
    vr_defaults_actionmap_item_add(am,
                                   VRDefaultActionmapItemNames.RAYCAST_SELECT.value,
                                   "/user/hand/left",
                                   "/input/trigger/value",
                                   "/user/hand/right",
                                   "/input/trigger/value",
                                   0.3,
                                   "wm.xr_select_raycast",
                                   'MODAL')      
    vr_defaults_actionmap_item_add(am,
                                   VRDefaultActionmapItemNames.GRAB.value,
                                   "/user/hand/left",
                                   "/input/squeeze/click",
                                   "/user/hand/right",
                                   "/input/squeeze/click",
                                   0.3,
                                   "wm.xr_grab",
                                   'MODAL')
    vr_defaults_actionmap_item_add(am,
                                   VRDefaultActionmapItemNames.UNDO.value,
                                   "/user/hand/left",
                                   "/input/menu/click",
                                   "",
                                   "",
                                   0.3,
                                   "ed.undo",
                                   'PRESS')        
    vr_defaults_actionmap_item_add(am,
                                   VRDefaultActionmapItemNames.REDO.value,
                                   "/user/hand/right",
                                   "/input/menu/click",
                                   "",
                                   "",
                                   0.3,
                                   "ed.redo",
                                   'PRESS')


def vr_defaults_create_vive(ac):
    am = vr_defaults_actionmap_add(ac,
                                   VRDefaultActionmapNames.VIVE.value,
                                   "/interaction_profiles/htc/vive_controller")
    if not am:
        return

    vr_defaults_pose_actionmap_item_add(am,
                                        VRDefaultActionmapItemNames.CONTROLLER_POSE.value,
                                        "/user/hand/left",
                                        "/input/grip/pose",
                                        "/user/hand/right",
                                        "/input/grip/pose",
                                        True,
                                        (0, 0, 0),
                                        (0, 0, 0)) 
    vr_defaults_actionmap_item_add(am,
                                   VRDefaultActionmapItemNames.RAYCAST_SELECT.value,
                                   "/user/hand/left",
                                   "/input/trigger/value",
                                   "/user/hand/right",
                                   "/input/trigger/value",
                                   0.3,
                                   "wm.xr_select_raycast",
                                   'MODAL')      
    vr_defaults_actionmap_item_add(am,
                                   VRDefaultActionmapItemNames.GRAB.value,
                                   "/user/hand/left",
                                   "/input/squeeze/click",
                                   "/user/hand/right",
                                   "/input/squeeze/click",
                                   0.3,
                                   "wm.xr_grab",
                                   'MODAL')
    vr_defaults_actionmap_item_add(am,
                                   VRDefaultActionmapItemNames.UNDO.value,
                                   "/user/hand/left",
                                   "/input/menu/click",
                                   "",
                                   "",
                                   0.3,
                                   "ed.undo",
                                   'PRESS')        
    vr_defaults_actionmap_item_add(am,
                                   VRDefaultActionmapItemNames.REDO.value,
                                   "/user/hand/right",
                                   "/input/menu/click",
                                   "",
                                   "",
                                   0.3,
                                   "ed.redo",
                                   'PRESS')


def vr_defaults_create_index(ac):
    am = vr_defaults_actionmap_add(ac,
                                   VRDefaultActionmapNames.INDEX.value,
                                   "/interaction_profiles/valve/index_controller")
    if not am:
        return

    vr_defaults_pose_actionmap_item_add(am,
                                        VRDefaultActionmapItemNames.CONTROLLER_POSE.value,
                                        "/user/hand/left",
                                        "/input/grip/pose",
                                        "/user/hand/right",
                                        "/input/grip/pose",
                                        True,
                                        (0, 0, 0),
                                        (0, 0, 0)) 
    vr_defaults_actionmap_item_add(am,
                                   VRDefaultActionmapItemNames.RAYCAST_SELECT.value,
                                   "/user/hand/left",
                                   "/input/trigger/value",
                                   "/user/hand/right",
                                   "/input/trigger/value",
                                   0.3,
                                   "wm.xr_select_raycast",
                                   'MODAL')      
    vr_defaults_actionmap_item_add(am,
                                   VRDefaultActionmapItemNames.GRAB.value,
                                   "/user/hand/left",
                                   "/input/squeeze/value",
                                   "/user/hand/right",
                                   "/input/squeeze/value",
                                   0.3,
                                   "wm.xr_grab",
                                   'MODAL')
    vr_defaults_actionmap_item_add(am,
                                   VRDefaultActionmapItemNames.UNDO.value,
                                   "/user/hand/left",
                                   "/input/a/click",
                                   "",
                                   "",
                                   0.3,
                                   "ed.undo",
                                   'PRESS')        
    vr_defaults_actionmap_item_add(am,
                                   VRDefaultActionmapItemNames.REDO.value,
                                   "/user/hand/right",
                                   "/input/a/click",
                                   "",
                                   "",
                                   0.3,
                                   "ed.redo",
                                   'PRESS')
    

@persistent
def vr_load_default_actionmaps(context: bpy.context):
    context = bpy.context

    actionconfigs = context.window_manager.xr_session_settings.actionconfigs
    if not actionconfigs:
        return
    ac = actionconfigs.default
    if not ac:
        return

    # Set default action config as active. 
    actionconfigs.active = ac

    if len(ac.actionmaps) > 0:
        # Don't load defaults for scenes that already contain actionmaps.
        return

    # Set default action config as active. 
    #actionconfigs.active = ac

    # Load default actionmaps.
    loaded = main.vr_load_actionmaps(context)
    
    if not loaded:
        # Create and save default actionmaps.
        vr_defaults_create_oculus(ac)
        vr_defaults_create_wmr(ac)
        vr_defaults_create_vive(ac)
        vr_defaults_create_index(ac)

        main.vr_save_actionmaps(context, sort=False)
