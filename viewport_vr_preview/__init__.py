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

bl_info = {
    "name": "VR Scene Inspection",
    "author": "Julian Eisel (Severin), Sebastian Koenig, Peter Kim (muxed-reality)",
    "version": (0, 10, 0),
    "blender": (2, 93, 0),
    "location": "3D View > Sidebar > VR",
    "description": ("View the viewport with virtual reality glasses "
                    "(head-mounted displays)"),
    "support": "OFFICIAL",
    "warning": "This is an early, limited preview of in development "
               "VR support for Blender.",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/3d_view/vr_scene_inspection.html",
    "category": "3D View",
}


if "bpy" in locals():
    import importlib
    importlib.reload(main)
    importlib.reload(defaults)
else:
    from . import main, defaults

import bpy


classes = (
    main.VIEW3D_PT_vr_session,
    main.VIEW3D_PT_vr_session_view,
    main.VIEW3D_PT_vr_landmarks,
    main.VIEW3D_PT_vr_actions,
    main.VIEW3D_PT_vr_motion_capture,
    main.VIEW3D_PT_vr_viewport_feedback,

    main.VRLandmark,
    main.VIEW3D_UL_vr_landmarks,
    main.VIEW3D_MT_vr_landmark_menu,

    main.VIEW3D_OT_vr_landmark_add,
    main.VIEW3D_OT_vr_landmark_remove,
    main.VIEW3D_OT_vr_landmark_activate,
    main.VIEW3D_OT_vr_landmark_from_session,
    main.VIEW3D_OT_add_camera_from_vr_landmark,
    main.VIEW3D_OT_camera_to_vr_landmark,
    main.VIEW3D_OT_vr_landmark_from_camera,
    main.VIEW3D_OT_cursor_to_vr_landmark,
    main.VIEW3D_OT_update_vr_landmark,

    main.VIEW3D_UL_vr_action_sets,
    main.VIEW3D_MT_vr_action_set_menu,
    main.VIEW3D_UL_vr_actions,
    main.VIEW3D_MT_vr_action_menu,

    main.VIEW3D_OT_vr_action_set_add,
    main.VIEW3D_OT_vr_action_set_remove,
    main.VIEW3D_OT_vr_action_set_activate,
    main.VIEW3D_OT_vr_action_sets_import,
    main.VIEW3D_OT_vr_action_sets_export,
    main.VIEW3D_OT_vr_action_set_copy,
    main.VIEW3D_OT_vr_action_sets_clear,
    main.VIEW3D_OT_vr_action_add,
    main.VIEW3D_OT_vr_action_remove,
    main.VIEW3D_OT_vr_action_copy,
    main.VIEW3D_OT_vr_actions_clear,

    main.VIEW3D_GT_vr_camera_cone,
    main.VIEW3D_GT_vr_controller_axes,
    main.VIEW3D_GGT_vr_viewer_pose,
    main.VIEW3D_GGT_vr_controller_poses,
    main.VIEW3D_GGT_vr_landmarks,
)


def register():
    if not bpy.app.build_options.xr_openxr:
        bpy.utils.register_class(main.VIEW3D_PT_vr_info)
        return

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.vr_landmarks = bpy.props.CollectionProperty(
        name="Landmark",
        type=main.VRLandmark,
    )
    bpy.types.Scene.vr_landmarks_selected = bpy.props.IntProperty(
        name="Selected Landmark"
    )
    bpy.types.Scene.vr_landmarks_active = bpy.props.IntProperty(
        update=main.vr_landmark_active_update,
    )
    bpy.types.Scene.vr_headset_object = bpy.props.PointerProperty(
        name="Headset Object",
        type=bpy.types.Object,
        update=main.vr_headset_object_update,
    )
    bpy.types.Scene.vr_controller0_object = bpy.props.PointerProperty(
        name="Controller 0 Object",
        type=bpy.types.Object,
        update=main.vr_controller0_object_update,
    )
    bpy.types.Scene.vr_controller1_object = bpy.props.PointerProperty(
        name="Controller 1 Object",
        type=bpy.types.Object,
        update=main.vr_controller1_object_update,
    )
    # View3DShading is the only per 3D-View struct with custom property
    # support, so "abusing" that to get a per 3D-View option.
    bpy.types.View3DShading.vr_show_virtual_camera = bpy.props.BoolProperty(
        name="Show VR Camera"
    )
    bpy.types.View3DShading.vr_show_controllers = bpy.props.BoolProperty(
        name="Show VR Controllers"
    )
    bpy.types.View3DShading.vr_show_landmarks = bpy.props.BoolProperty(
        name="Show Landmarks"
    )

    bpy.app.handlers.load_post.append(main.vr_ensure_default_landmark)
    bpy.app.handlers.load_post.append(defaults.vr_load_default_actionmaps)
    bpy.app.handlers.xr_session_start_pre.append(main.vr_create_actions)


def unregister():
    if not bpy.app.build_options.xr_openxr:
        bpy.utils.unregister_class(main.VIEW3D_PT_vr_info)
        return

    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.vr_landmarks
    del bpy.types.Scene.vr_landmarks_selected
    del bpy.types.Scene.vr_landmarks_active
    del bpy.types.Scene.vr_headset_object
    del bpy.types.Scene.vr_controller0_object
    del bpy.types.Scene.vr_controller1_object
    del bpy.types.View3DShading.vr_show_virtual_camera
    del bpy.types.View3DShading.vr_show_controllers
    del bpy.types.View3DShading.vr_show_landmarks

    bpy.app.handlers.load_post.remove(main.vr_ensure_default_landmark)
    bpy.app.handlers.load_post.remove(defaults.vr_load_default_actionmaps)
    bpy.app.handlers.xr_session_start_pre.remove(main.vr_create_actions)
