keyconfig_version = (2, 93, 5)
keyconfig_data = \
[("XR Session",
  {"space_type": 'EMPTY', "region_type": 'XR'},
  {"items":
   [("wm.xr_select_raycast",
     {"type": 'XR_ACTION', "value": 'ANY', "xr_action_set": 'default_oculus', "xr_action": 'raycast_select'},
     {"properties":
      [("deselect_all", True),
       ],
      },
     ),
    ("wm.xr_select_raycast",
     {"type": 'XR_ACTION', "value": 'ANY', "xr_action_set": 'default_vive', "xr_action": 'raycast_select'},
     {"properties":
      [("deselect_all", True),
       ],
      },
     ),
    ("wm.xr_grab", {"type": 'XR_ACTION', "value": 'ANY', "xr_action_set": 'default_vive', "xr_action": 'grab'}, None),
    ("wm.xr_grab", {"type": 'XR_ACTION', "value": 'ANY', "xr_action_set": 'default_oculus', "xr_action": 'grab'}, None),
    ("wm.xr_select_raycast",
     {"type": 'XR_ACTION', "value": 'ANY', "xr_action_set": 'default_wmr', "xr_action": 'raycast_select'},
     {"properties":
      [("deselect_all", True),
       ],
      },
     ),
    ("wm.xr_grab", {"type": 'XR_ACTION', "value": 'ANY', "xr_action_set": 'default_wmr', "xr_action": 'grab'}, None),
    ("wm.xr_select_raycast",
     {"type": 'XR_ACTION', "value": 'ANY', "xr_action_set": 'default_index', "xr_action": 'raycast_select'},
     {"properties":
      [("deselect_all", True),
       ],
      },
     ),
    ("wm.xr_grab", {"type": 'XR_ACTION', "value": 'ANY', "xr_action_set": 'default_index', "xr_action": 'grab'}, None),
    ("ed.undo", {"type": 'XR_ACTION', "value": 'ANY', "xr_action_set": 'default_vive', "xr_action": 'undo'}, None),
    ("ed.redo", {"type": 'XR_ACTION', "value": 'ANY', "xr_action_set": 'default_vive', "xr_action": 'redo'}, None),
    ("ed.undo", {"type": 'XR_ACTION', "value": 'ANY', "xr_action_set": 'default_oculus', "xr_action": 'undo'}, None),
    ("ed.redo", {"type": 'XR_ACTION', "value": 'ANY', "xr_action_set": 'default_oculus', "xr_action": 'redo'}, None),
    ("ed.undo", {"type": 'XR_ACTION', "value": 'ANY', "xr_action_set": 'default_wmr', "xr_action": 'undo'}, None),
    ("ed.redo", {"type": 'XR_ACTION', "value": 'ANY', "xr_action_set": 'default_wmr', "xr_action": 'redo'}, None),
    ("ed.undo", {"type": 'XR_ACTION', "value": 'ANY', "xr_action_set": 'default_index', "xr_action": 'undo'}, None),
    ("ed.redo", {"type": 'XR_ACTION', "value": 'ANY', "xr_action_set": 'default_index', "xr_action": 'redo'}, None),
    ],
   },
  ),
 ]


if __name__ == "__main__":
    # Only add keywords that are supported.
    from bpy.app import version as blender_version
    keywords = {}
    if blender_version >= (2, 92, 0):
        keywords["keyconfig_version"] = keyconfig_version
    import os
    from bl_keymap_utils.io import keyconfig_import_from_data
    keyconfig_import_from_data(
        os.path.splitext(os.path.basename(__file__))[0],
        keyconfig_data,
        **keywords,
    )
