# SPDX-License-Identifier: GPL-2.0-or-later

# <pep8 compliant>

if "bpy" in locals():
    import importlib
    importlib.reload(action_map)
    importlib.reload(properties)
else:
    from . import action_map, properties

import bpy
from bpy.types import (
    Menu,
    Panel,
    UIList,
)

### Session.
class VIEW3D_PT_vr_session(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VR"
    bl_label = "VR Session"

    def draw(self, context):
        layout = self.layout
        session_settings = context.window_manager.xr_session_settings
        scene = context.scene

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        is_session_running = bpy.types.XrSessionState.is_running(context)

        # Using SNAP_FACE because it looks like a stop icon -- I shouldn't
        # have commit rights...
        toggle_info = (
            ("Start VR Session", 'PLAY') if not is_session_running else (
                "Stop VR Session", 'SNAP_FACE')
        )
        layout.operator("wm.xr_session_toggle",
                        text=toggle_info[0], icon=toggle_info[1])

        layout.separator()

        col = layout.column(align=True, heading="Tracking")
        col.prop(session_settings, "use_positional_tracking", text="Positional")
        col.prop(session_settings, "use_absolute_tracking", text="Absolute")

        col = layout.column(align=True, heading="Actions")
        col.prop(scene, "vr_actions_enable")


### View.
class VIEW3D_PT_vr_session_view(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VR"
    bl_label = "View"

    def draw(self, context):
        layout = self.layout
        session_settings = context.window_manager.xr_session_settings

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        col = layout.column(align=True, heading="Show")
        col.prop(session_settings, "show_floor", text="Floor")
        col.prop(session_settings, "show_annotation", text="Annotations")
        col.prop(session_settings, "show_selection", text="Selection")
        col.prop(session_settings, "show_controllers", text="Controllers")
        col.prop(session_settings, "show_custom_overlays", text="Custom Overlays")

        col = layout.column(align=True)
        col.prop(session_settings, "controller_draw_style", text="Controller Style")

        col = layout.column(align=True)
        col.prop(session_settings, "clip_start", text="Clip Start")
        col.prop(session_settings, "clip_end", text="End")


### Landmarks.
class VIEW3D_MT_vr_landmark_menu(Menu):
    bl_label = "Landmark Controls"

    def draw(self, _context):
        layout = self.layout

        layout.operator("view3d.vr_camera_landmark_from_session")
        layout.operator("view3d.vr_landmark_from_camera")
        layout.operator("view3d.update_vr_landmark")
        layout.separator()
        layout.operator("view3d.cursor_to_vr_landmark")
        layout.operator("view3d.camera_to_vr_landmark")
        layout.operator("view3d.add_camera_from_vr_landmark")


class VIEW3D_UL_vr_landmarks(UIList):
    def draw_item(self, context, layout, _data, item, icon, _active_data,
                  _active_propname, index):
        landmark = item
        landmark_active_idx = context.scene.vr_landmarks_active

        layout.emboss = 'NONE'

        layout.prop(landmark, "name", text="")

        icon = (
            'RADIOBUT_ON' if (index == landmark_active_idx) else 'RADIOBUT_OFF'
        )
        props = layout.operator(
            "view3d.vr_landmark_activate", text="", icon=icon)
        props.index = index


class VIEW3D_PT_vr_landmarks(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VR"
    bl_label = "Landmarks"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        landmark_selected = properties.VRLandmark.get_selected_landmark(context)

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        row = layout.row()

        row.template_list("VIEW3D_UL_vr_landmarks", "", scene, "vr_landmarks",
                          scene, "vr_landmarks_selected", rows=3)

        col = row.column(align=True)
        col.operator("view3d.vr_landmark_add", icon='ADD', text="")
        col.operator("view3d.vr_landmark_remove", icon='REMOVE', text="")
        col.operator("view3d.vr_landmark_from_session", icon='PLUS', text="")

        col.menu("VIEW3D_MT_vr_landmark_menu", icon='DOWNARROW_HLT', text="")

        if landmark_selected:
            layout.prop(landmark_selected, "type")

            if landmark_selected.type == 'OBJECT':
                layout.prop(landmark_selected, "base_pose_object")
                layout.prop(landmark_selected, "base_scale", text="Scale")
            elif landmark_selected.type == 'CUSTOM':
                layout.prop(landmark_selected,
                            "base_pose_location", text="Location")
                layout.prop(landmark_selected,
                            "base_pose_angle", text="Angle")
                layout.prop(landmark_selected,
                            "base_scale", text="Scale")


### Actions.
def vr_indented_layout(layout, level):
    # Same as _indented_layout() from rna_keymap_ui.py.
    indentpx = 16
    if level == 0:
        level = 0.0001   # Tweak so that a percentage of 0 won't split by half
    indent = level * indentpx / bpy.context.region.width

    split = layout.split(factor=indent)
    col = split.column()
    col = split.column()
    return col


def vr_draw_ami(ami, layout, level):
    # Similar to draw_kmi() from rna_keymap_ui.py.
    col = vr_indented_layout(layout, level)

    if ami.op:
        col = col.column(align=True)
        box = col.box()
    else:
        box = col.column()

    split = box.split()

    # Header bar.
    row = split.row(align=True)
    #row.prop(ami, "show_expanded", text="", emboss=False)

    row.label(text="Operator Properties")
    row.label(text=ami.op_name)

    # Expanded, additional event settings.
    if ami.op:
        box = col.box()
        
        # Operator properties.
        box.template_xr_actionmap_item_properties(ami)


class VIEW3D_UL_vr_actionmaps(UIList):
    def draw_item(self, context, layout, _data, item, icon, _active_data,
                  _active_propname, index):
        session_settings = context.window_manager.xr_session_settings

        am_active_idx = session_settings.active_actionmap
        am = item

        layout.emboss = 'NONE'

        layout.prop(am, "name", text="")

        icon = (
            'RADIOBUT_ON' if (index == am_active_idx) else 'RADIOBUT_OFF'
        )
        props = layout.operator(
            "view3d.vr_actionmap_activate", text="", icon=icon)
        props.index = index


class VIEW3D_MT_vr_actionmap_menu(Menu):
    bl_label = "Action Map Controls"

    def draw(self, _context):
        layout = self.layout

        layout.operator("view3d.vr_actionmaps_defaults_load")
        layout.operator("view3d.vr_actionmaps_import")
        layout.operator("view3d.vr_actionmaps_export")
        layout.operator("view3d.vr_actionmap_copy")
        layout.operator("view3d.vr_actionmaps_clear")


class VIEW3D_UL_vr_actions(UIList):
    def draw_item(self, context, layout, _data, item, icon, _active_data,
                  _active_propname, index):
        action = item

        layout.emboss = 'NONE'

        layout.prop(action, "name", text="")


class VIEW3D_MT_vr_action_menu(Menu):
    bl_label = "Action Controls"

    def draw(self, _context):
        layout = self.layout

        layout.operator("view3d.vr_action_copy")
        layout.operator("view3d.vr_actions_clear")


class VIEW3D_UL_vr_action_user_paths(UIList):
    def draw_item(self, context, layout, _data, item, icon, _active_data,
                  _active_propname, index):
        user_path = item

        layout.emboss = 'NONE'

        layout.prop(user_path, "path", text="")


class VIEW3D_MT_vr_action_user_path_menu(Menu):
    bl_label = "User Path Controls"

    def draw(self, _context):
        layout = self.layout

        layout.operator("view3d.vr_action_user_paths_clear")


class VIEW3D_UL_vr_actionbindings(UIList):
    def draw_item(self, context, layout, _data, item, icon, _active_data,
                  _active_propname, index):
        amb = item

        layout.emboss = 'NONE'

        layout.prop(amb, "name", text="")


class VIEW3D_MT_vr_actionbinding_menu(Menu):
    bl_label = "Action Binding Controls"

    def draw(self, _context):
        layout = self.layout

        layout.operator("view3d.vr_actionbinding_copy")
        layout.operator("view3d.vr_actionbindings_clear")


class VIEW3D_UL_vr_actionbinding_component_paths(UIList):
    def draw_item(self, context, layout, _data, item, icon, _active_data,
                  _active_propname, index):
        component_path = item

        layout.emboss = 'NONE'

        layout.prop(component_path, "path", text="")


class VIEW3D_MT_vr_actionbinding_component_path_menu(Menu):
    bl_label = "Component Path Controls"

    def draw(self, _context):
        layout = self.layout

        layout.operator("view3d.vr_actionbinding_component_paths_clear")


class VRActionsPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VR"
    bl_options = {'DEFAULT_CLOSED'}


class VIEW3D_PT_vr_actions_actionmaps(VRActionsPanel, Panel):
    bl_label = "Action Maps"

    def draw(self, context):
        session_settings = context.window_manager.xr_session_settings

        scene = context.scene

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        row = layout.row()
        row.template_list("VIEW3D_UL_vr_actionmaps", "", session_settings, "actionmaps",
                          session_settings, "selected_actionmap", rows=3)

        col = row.column(align=True)
        col.operator("view3d.vr_actionmap_add", icon='ADD', text="")
        col.operator("view3d.vr_actionmap_remove", icon='REMOVE', text="")

        col.menu("VIEW3D_MT_vr_actionmap_menu", icon='DOWNARROW_HLT', text="")

        am = action_map.vr_actionmap_selected_get(session_settings)

        if am:
            row = layout.row()
            col = row.column(align=True)

            col.prop(am, "name", text="Action Map")


class VIEW3D_PT_vr_actions_actions(VRActionsPanel, Panel):
    bl_label = "Actions"
    bl_parent_id = "VIEW3D_PT_vr_actions_actionmaps"

    def draw(self, context):
        session_settings = context.window_manager.xr_session_settings

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
		
        am = action_map.vr_actionmap_selected_get(session_settings)

        if am:
            col = vr_indented_layout(layout, 1)
            row = col.row()
            row.template_list("VIEW3D_UL_vr_actions", "", am, "actionmap_items",
                              am, "selected_item", rows=3)

            col = row.column(align=True)
            col.operator("view3d.vr_action_add", icon='ADD', text="")
            col.operator("view3d.vr_action_remove", icon='REMOVE', text="")

            col.menu("VIEW3D_MT_vr_action_menu", icon='DOWNARROW_HLT', text="")

            ami = action_map.vr_actionmap_item_selected_get(am)

            if ami:
                row = layout.row()
                col = row.column(align=True)

                col.prop(ami, "name", text="Action")
                col.prop(ami, "type", text="Type")

                if ami.type == 'FLOAT' or ami.type == 'VECTOR2D':
                    col.prop(ami, "op", text="Operator")
                    col.prop(ami, "op_mode", text="Operator Mode")
                    col.prop(ami, "bimanual", text="Bimanual")
                    # Properties.
                    vr_draw_ami(ami, col, 1)
                elif ami.type == 'POSE':
                    col.prop(ami, "pose_is_controller_grip", text="Use for Controller Grips")
                    col.prop(ami, "pose_is_controller_aim", text="Use for Controller Aims")
                    col.prop(ami, "pose_is_tracker", text="Tracker")


class VIEW3D_PT_vr_actions_user_paths(VRActionsPanel, Panel):
    bl_label = "User Paths"
    bl_parent_id = "VIEW3D_PT_vr_actions_actions"

    def draw(self, context):
        session_settings = context.window_manager.xr_session_settings

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        am = action_map.vr_actionmap_selected_get(session_settings)

        if am:
            ami = action_map.vr_actionmap_item_selected_get(am)

            if ami:
                col = vr_indented_layout(layout, 2)
                row = col.row()
                row.template_list("VIEW3D_UL_vr_action_user_paths", "", ami, "user_paths",
                                  ami, "selected_user_path", rows=2)

                col = row.column(align=True)
                col.operator("view3d.vr_action_user_path_add", icon='ADD', text="")
                col.operator("view3d.vr_action_user_path_remove", icon='REMOVE', text="")

                col.menu("VIEW3D_MT_vr_action_user_path_menu", icon='DOWNARROW_HLT', text="")


class VIEW3D_PT_vr_actions_haptics(VRActionsPanel, Panel):
    bl_label = "Haptics"
    bl_parent_id = "VIEW3D_PT_vr_actions_actions"

    def draw(self, context):
        session_settings = context.window_manager.xr_session_settings

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        am = action_map.vr_actionmap_selected_get(session_settings)

        if am:
            ami = action_map.vr_actionmap_item_selected_get(am)

            if ami:
                row = layout.row()
                col = row.column(align=True)

                if ami.type == 'FLOAT' or ami.type == 'VECTOR2D':
                    col.prop(ami, "haptic_name", text="Haptic Action")
                    col.prop(ami, "haptic_match_user_paths", text="Match User Paths")
                    col.prop(ami, "haptic_duration", text="Duration")
                    col.prop(ami, "haptic_frequency", text="Frequency")
                    col.prop(ami, "haptic_amplitude", text="Amplitude")
                    col.prop(ami, "haptic_mode", text="Haptic Mode")


class VIEW3D_PT_vr_actions_bindings(VRActionsPanel, Panel):
    bl_label = "Bindings"
    bl_parent_id = "VIEW3D_PT_vr_actions_actions"

    def draw(self, context):
        session_settings = context.window_manager.xr_session_settings

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        am = action_map.vr_actionmap_selected_get(session_settings)

        if am:
            ami = action_map.vr_actionmap_item_selected_get(am)

            if ami:
                col = vr_indented_layout(layout, 2)
                row = col.row()
                row.template_list("VIEW3D_UL_vr_actionbindings", "", ami, "bindings",
                                  ami, "selected_binding", rows=3)

                col = row.column(align=True)
                col.operator("view3d.vr_actionbinding_add", icon='ADD', text="")
                col.operator("view3d.vr_actionbinding_remove", icon='REMOVE', text="")

                col.menu("VIEW3D_MT_vr_actionbinding_menu", icon='DOWNARROW_HLT', text="")

                amb = action_map.vr_actionmap_binding_selected_get(ami)

                if amb:
                    row = layout.row()
                    col = row.column(align=True)

                    col.prop(amb, "name", text="Binding")
                    col.prop(amb, "profile", text="Profile")

                    if ami.type == 'FLOAT' or ami.type == 'VECTOR2D':
                        col.prop(amb, "threshold", text="Threshold")
                        if ami.type == 'FLOAT':
                            col.prop(amb, "axis0_region", text="Axis Region")
                        else: # ami.type == 'VECTOR2D'
                            col.prop(amb, "axis0_region", text="Axis 0 Region")
                            col.prop(amb, "axis1_region", text="Axis 1 Region")
                    elif ami.type == 'POSE':
                        col.prop(amb, "pose_location", text="Location Offset")
                        col.prop(amb, "pose_rotation", text="Rotation Offset")


class VIEW3D_PT_vr_actions_component_paths(VRActionsPanel, Panel):
    bl_label = "Component Paths"
    bl_parent_id = "VIEW3D_PT_vr_actions_bindings"

    def draw(self, context):
        session_settings = context.window_manager.xr_session_settings

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        am = action_map.vr_actionmap_selected_get(session_settings)

        if am:
            ami = action_map.vr_actionmap_item_selected_get(am)

            if ami:
                amb = action_map.vr_actionmap_binding_selected_get(ami)

                if amb:
                    col = vr_indented_layout(layout, 3)
                    row = col.row()
                    row.template_list("VIEW3D_UL_vr_actionbinding_component_paths", "", amb, "component_paths",
                                      amb, "selected_component_path", rows=2)

                    col = row.column(align=True)
                    col.operator("view3d.vr_actionbinding_component_path_add", icon='ADD', text="")
                    col.operator("view3d.vr_actionbinding_component_path_remove", icon='REMOVE', text="")

                    col.menu("VIEW3D_MT_vr_actionbinding_component_path_menu", icon='DOWNARROW_HLT', text="")


class VIEW3D_PT_vr_actions_extensions(VRActionsPanel, Panel):
    bl_label = "Extensions"
    bl_parent_id = "VIEW3D_PT_vr_actions_actionmaps"

    def draw(self, context):
        scene = context.scene
        session_settings = context.window_manager.xr_session_settings

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        col = layout.column(align=True)
        col.prop(scene, "vr_actions_enable_reverb_g2", text="HP Reverb G2")
        col.prop(scene, "vr_actions_enable_vive_cosmos", text="HTC Vive Cosmos")
        col.prop(scene, "vr_actions_enable_vive_focus", text="HTC Vive Focus")
        col.prop(session_settings, "enable_vive_tracker_extension", text="HTC Vive Tracker")
        #col.prop(scene, "vr_actions_enable_vive_tracker", text="HTC Vive Tracker")
        col.prop(scene, "vr_actions_enable_huawei", text="Huawei")


### Motion capture.
class VIEW3D_UL_vr_mocap_objects(UIList):
    def draw_item(self, context, layout, _data, item, icon, _active_data,
                  _active_propname, index):
        scene_mocap_ob = item

        layout.emboss = 'NONE'

        if scene_mocap_ob.object:
            layout.prop(scene_mocap_ob.object, "name", text="")
        else:
            layout.label(icon='X')


class VIEW3D_MT_vr_mocap_object_menu(Menu):
    bl_label = "Motion Capture Object Controls"

    def draw(self, _context):
        layout = self.layout

        layout.operator("view3d.vr_mocap_objects_enable")
        layout.operator("view3d.vr_mocap_objects_disable")
        layout.operator("view3d.vr_mocap_objects_clear")
        layout.operator("view3d.vr_mocap_object_help")


class VIEW3D_PT_vr_motion_capture(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VR"
    bl_label = "Motion Capture"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        session_settings = context.window_manager.xr_session_settings
        scene = context.scene

        col = layout.column(align=True)
        col.label(icon='ERROR', text="Note:")
        col.label(text="Settings here may have a significant")
        col.label(text="performance impact!")

        layout.separator()

        row = layout.row()
        row.template_list("VIEW3D_UL_vr_mocap_objects", "", scene, "vr_mocap_objects",
                          session_settings, "selected_mocap_object", rows=3)

        col = row.column(align=True)
        col.operator("view3d.vr_mocap_object_add", icon='ADD', text="")
        col.operator("view3d.vr_mocap_object_remove", icon='REMOVE', text="")

        col.menu("VIEW3D_MT_vr_mocap_object_menu", icon='DOWNARROW_HLT', text="")

        mocap_ob = properties.vr_mocap_object_selected_get(session_settings)
        scene_mocap_ob = properties.vr_scene_mocap_object_selected_get(scene, session_settings)

        if mocap_ob and scene_mocap_ob:
            row = layout.row()
            col = row.column(align=True)

            col.prop(scene_mocap_ob, "object", text="Object")
            col.prop(mocap_ob, "user_path", text="User Path")
            col.prop(mocap_ob, "enable", text="Enable")
            col.prop(mocap_ob, "autokey", text="Auto Key")
            col.prop(mocap_ob, "location_offset", text="Location Offset")
            col.prop(mocap_ob, "rotation_offset", text="Rotation Offset")


### Viewport feedback.
class VIEW3D_PT_vr_viewport_feedback(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VR"
    bl_label = "Viewport Feedback"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        view3d = context.space_data
        session_settings = context.window_manager.xr_session_settings

        col = layout.column(align=True)
        col.label(icon='ERROR', text="Note:")
        col.label(text="Settings here may have a significant")
        col.label(text="performance impact!")

        layout.separator()

        layout.prop(view3d.shading, "vr_show_virtual_camera")
        layout.prop(view3d.shading, "vr_show_controllers")
        layout.prop(view3d.shading, "vr_show_landmarks")
        layout.prop(view3d, "mirror_xr_session")


### Info.
class VIEW3D_PT_vr_info(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VR"
    bl_label = "VR Info"

    @classmethod
    def poll(cls, context):
        return not bpy.app.build_options.xr_openxr

    def draw(self, context):
        layout = self.layout
        layout.label(icon='ERROR', text="Built without VR/OpenXR features")


classes = (
    VIEW3D_PT_vr_session,
    VIEW3D_PT_vr_session_view,
    VIEW3D_PT_vr_landmarks,
    VIEW3D_PT_vr_actions_actionmaps,
    VIEW3D_PT_vr_actions_actions,
    VIEW3D_PT_vr_actions_user_paths,
    VIEW3D_PT_vr_actions_haptics,
    VIEW3D_PT_vr_actions_bindings,
    VIEW3D_PT_vr_actions_component_paths,
    VIEW3D_PT_vr_actions_extensions,
    VIEW3D_PT_vr_motion_capture,
    VIEW3D_PT_vr_viewport_feedback,

    VIEW3D_UL_vr_landmarks,
    VIEW3D_MT_vr_landmark_menu,

    VIEW3D_UL_vr_actionmaps,
    VIEW3D_MT_vr_actionmap_menu,
    VIEW3D_UL_vr_actions,
    VIEW3D_MT_vr_action_menu,
    VIEW3D_UL_vr_action_user_paths,
    VIEW3D_MT_vr_action_user_path_menu,
    VIEW3D_UL_vr_actionbindings,
    VIEW3D_MT_vr_actionbinding_menu,
    VIEW3D_UL_vr_actionbinding_component_paths,
    VIEW3D_MT_vr_actionbinding_component_path_menu,

    VIEW3D_UL_vr_mocap_objects,
    VIEW3D_MT_vr_mocap_object_menu,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

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


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.View3DShading.vr_show_virtual_camera
    del bpy.types.View3DShading.vr_show_controllers
    del bpy.types.View3DShading.vr_show_landmarks
