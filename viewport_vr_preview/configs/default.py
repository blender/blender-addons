actionconfig_version = (3, 0, 1)
actionconfig_data = \
[("blender_oculus",
  {"profile": '/interaction_profiles/oculus/touch_controller'},
  {"items":
   [("controller_pose", {"type": 'POSE', "user_path0": '/user/hand/left', "component_path0": '/input/grip/pose', "user_path1": '/user/hand/right', "component_path1": '/input/grip/pose', "pose_is_controller": 'True', "pose_location": '(0.0, 0.0, 0.0)', "pose_rotation": '(-0.8726646304130554, 0.0, 0.0)'}, None),
    ("teleport",
     {"type": 'BUTTON', "user_path0": '/user/hand/left', "component_path0": '/input/trigger/value', "user_path1": '/user/hand/right', "component_path1": '/input/trigger/value', "threshold": '0.30000001192092896', "op": 'wm.xr_navigation_teleport', "op_flag": 'MODAL'},
     {"op_properties":
      [("color", (0.0, 1.0, 1.0, 1.0)),
       ],
      },
     ),
    ("raycast_select", {"type": 'BUTTON', "user_path0": '/user/hand/left', "component_path0": '/input/x/click', "user_path1": '/user/hand/right', "component_path1": '/input/a/click', "threshold": '0.30000001192092896', "op": 'wm.xr_select_raycast', "op_flag": 'MODAL'}, None),
    ("grab", {"type": 'BUTTON', "user_path0": '/user/hand/left', "component_path0": '/input/squeeze/value', "user_path1": '/user/hand/right', "component_path1": '/input/squeeze/value', "threshold": '0.30000001192092896', "op": 'wm.xr_grab', "op_flag": 'MODAL'}, None),
    ("undo", {"type": 'BUTTON', "user_path0": '/user/hand/left', "component_path0": '/input/y/click', "user_path1": '', "component_path1": '', "threshold": '0.30000001192092896', "op": 'ed.undo', "op_flag": 'PRESS'}, None),
    ("redo", {"type": 'BUTTON', "user_path0": '/user/hand/right', "component_path0": '/input/b/click', "user_path1": '', "component_path1": '', "threshold": '0.30000001192092896', "op": 'ed.redo', "op_flag": 'PRESS'}, None),
    ("haptic", {"type": 'HAPTIC', "user_path0": '/user/hand/left', "component_path0": '/output/haptic', "user_path1": '/user/hand/right', "component_path1": '/output/haptic', "haptic_duration": '0.30000001192092896', "haptic_frequency": '3000.0', "haptic_amplitude": '0.5'}, None),
    ],
   },
  ),
 ("blender_wmr",
  {"profile": '/interaction_profiles/microsoft/motion_controller'},
  {"items":
   [("controller_pose", {"type": 'POSE', "user_path0": '/user/hand/left', "component_path0": '/input/grip/pose', "user_path1": '/user/hand/right', "component_path1": '/input/grip/pose', "pose_is_controller": 'True', "pose_location": '(0.0, 0.0, 0.0)', "pose_rotation": '(-0.7853981852531433, 0.0, 0.0)'}, None),
    ("teleport",
     {"type": 'BUTTON', "user_path0": '/user/hand/left', "component_path0": '/input/trigger/value', "user_path1": '/user/hand/right', "component_path1": '/input/trigger/value', "threshold": '0.30000001192092896', "op": 'wm.xr_navigation_teleport', "op_flag": 'MODAL'},
     {"op_properties":
      [("color", (0.0, 1.0, 1.0, 1.0)),
       ],
      },
     ),
    ("raycast_select", {"type": 'BUTTON', "user_path0": '/user/hand/left', "component_path0": '/input/trackpad/click', "user_path1": '/user/hand/right', "component_path1": '/input/trackpad/click', "threshold": '0.30000001192092896', "op": 'wm.xr_select_raycast', "op_flag": 'MODAL'}, None),
    ("grab", {"type": 'BUTTON', "user_path0": '/user/hand/left', "component_path0": '/input/squeeze/click', "user_path1": '/user/hand/right', "component_path1": '/input/squeeze/click', "threshold": '0.30000001192092896', "op": 'wm.xr_grab', "op_flag": 'MODAL'}, None),
    ("undo", {"type": 'BUTTON', "user_path0": '/user/hand/left', "component_path0": '/input/menu/click', "user_path1": '', "component_path1": '', "threshold": '0.30000001192092896', "op": 'ed.undo', "op_flag": 'PRESS'}, None),
    ("redo", {"type": 'BUTTON', "user_path0": '/user/hand/right', "component_path0": '/input/menu/click', "user_path1": '', "component_path1": '', "threshold": '0.30000001192092896', "op": 'ed.redo', "op_flag": 'PRESS'}, None),
    ("haptic", {"type": 'HAPTIC', "user_path0": '/user/hand/left', "component_path0": '/output/haptic', "user_path1": '/user/hand/right', "component_path1": '/output/haptic', "haptic_duration": '0.30000001192092896', "haptic_frequency": '3000.0', "haptic_amplitude": '0.5'}, None),
    ],
   },
  ),
 ("blender_vive",
  {"profile": '/interaction_profiles/htc/vive_controller'},
  {"items":
   [("controller_pose", {"type": 'POSE', "user_path0": '/user/hand/left', "component_path0": '/input/grip/pose', "user_path1": '/user/hand/right', "component_path1": '/input/grip/pose', "pose_is_controller": 'True', "pose_location": '(0.0, 0.0, 0.0)', "pose_rotation": '(0.0, 0.0, 0.0)'}, None),
    ("teleport",
     {"type": 'BUTTON', "user_path0": '/user/hand/left', "component_path0": '/input/trigger/value', "user_path1": '/user/hand/right', "component_path1": '/input/trigger/value', "threshold": '0.30000001192092896', "op": 'wm.xr_navigation_teleport', "op_flag": 'MODAL'},
     {"op_properties":
      [("color", (0.0, 1.0, 1.0, 1.0)),
       ],
      },
     ),
    ("raycast_select", {"type": 'BUTTON', "user_path0": '/user/hand/left', "component_path0": '/input/trackpad/click', "user_path1": '/user/hand/right', "component_path1": '/input/trackpad/click', "threshold": '0.30000001192092896', "op": 'wm.xr_select_raycast', "op_flag": 'MODAL'}, None),
    ("grab", {"type": 'BUTTON', "user_path0": '/user/hand/left', "component_path0": '/input/squeeze/click', "user_path1": '/user/hand/right', "component_path1": '/input/squeeze/click', "threshold": '0.30000001192092896', "op": 'wm.xr_grab', "op_flag": 'MODAL'}, None),
    ("undo", {"type": 'BUTTON', "user_path0": '/user/hand/left', "component_path0": '/input/menu/click', "user_path1": '', "component_path1": '', "threshold": '0.30000001192092896', "op": 'ed.undo', "op_flag": 'PRESS'}, None),
    ("redo", {"type": 'BUTTON', "user_path0": '/user/hand/right', "component_path0": '/input/menu/click', "user_path1": '', "component_path1": '', "threshold": '0.30000001192092896', "op": 'ed.redo', "op_flag": 'PRESS'}, None),
    ("haptic", {"type": 'HAPTIC', "user_path0": '/user/hand/left', "component_path0": '/output/haptic', "user_path1": '/user/hand/right', "component_path1": '/output/haptic', "haptic_duration": '0.30000001192092896', "haptic_frequency": '3000.0', "haptic_amplitude": '0.5'}, None),
    ],
   },
  ),
 ("blender_index",
  {"profile": '/interaction_profiles/valve/index_controller'},
  {"items":
   [("controller_pose", {"type": 'POSE', "user_path0": '/user/hand/left', "component_path0": '/input/grip/pose', "user_path1": '/user/hand/right', "component_path1": '/input/grip/pose', "pose_is_controller": 'True', "pose_location": '(0.0, 0.0, 0.0)', "pose_rotation": '(0.0, 0.0, 0.0)'}, None),
    ("teleport",
     {"type": 'BUTTON', "user_path0": '/user/hand/left', "component_path0": '/input/trigger/value', "user_path1": '/user/hand/right', "component_path1": '/input/trigger/value', "threshold": '0.30000001192092896', "op": 'wm.xr_navigation_teleport', "op_flag": 'MODAL'},
     {"op_properties":
      [("color", (0.0, 1.0, 1.0, 1.0)),
       ],
      },
     ),
    ("raycast_select", {"type": 'BUTTON', "user_path0": '/user/hand/left', "component_path0": '/input/a/click', "user_path1": '/user/hand/right', "component_path1": '/input/a/click', "threshold": '0.30000001192092896', "op": 'wm.xr_select_raycast', "op_flag": 'MODAL'}, None),
    ("grab", {"type": 'BUTTON', "user_path0": '/user/hand/left', "component_path0": '/input/squeeze/value', "user_path1": '/user/hand/right', "component_path1": '/input/squeeze/value', "threshold": '0.30000001192092896', "op": 'wm.xr_grab', "op_flag": 'MODAL'}, None),
    ("undo", {"type": 'BUTTON', "user_path0": '/user/hand/left', "component_path0": '/input/b/click', "user_path1": '', "component_path1": '', "threshold": '0.30000001192092896', "op": 'ed.undo', "op_flag": 'PRESS'}, None),
    ("redo", {"type": 'BUTTON', "user_path0": '/user/hand/right', "component_path0": '/input/b/click', "user_path1": '', "component_path1": '', "threshold": '0.30000001192092896', "op": 'ed.redo', "op_flag": 'PRESS'}, None),
    ("haptic", {"type": 'HAPTIC', "user_path0": '/user/hand/left', "component_path0": '/output/haptic', "user_path1": '/user/hand/right', "component_path1": '/output/haptic', "haptic_duration": '0.30000001192092896', "haptic_frequency": '3000.0', "haptic_amplitude": '0.5'}, None),
    ],
   },
  ),
 ]


if __name__ == "__main__":
    # Only add keywords that are supported.
    from bpy.app import version as blender_version
    keywords = {}
    if blender_version >= (3, 0, 0):
        keywords["actionconfig_version"] = actionconfig_version
    import os
    from viewport_vr_preview.io import actionconfig_import_from_data
    actionconfig_import_from_data(
        os.path.splitext(os.path.basename(__file__))[0],
        actionconfig_data,
        **keywords,
    )
