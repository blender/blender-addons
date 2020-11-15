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
from bpy.types import (
    Gizmo,
    GizmoGroup,
    PropertyGroup,
    UIList,
    Menu,
    Panel,
    Operator,
)
from bpy.props import (
    CollectionProperty,
    IntProperty,
    BoolProperty,
)
from bpy.app.handlers import persistent
import mathutils
from mathutils import Quaternion

bl_info = {
    "name": "VR Scene Inspection",
    "author": "Julian Eisel (Severin), Sebastian Koenig",
    "version": (0, 9, 0),
    "blender": (2, 90, 0),
    "location": "3D View > Sidebar > VR",
    "description": ("View the viewport with virtual reality glasses "
                    "(head-mounted displays)"),
    "support": "OFFICIAL",
    "warning": "This is an early, limited preview of in development "
               "VR support for Blender.",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/3d_view/vr_scene_inspection.html",
    "category": "3D View",
}

# Key maps.
@persistent
def vr_load_action_properties(context: bpy.context):
    # Load operator properties for scene action sets.
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.user
    kc_addon = wm.keyconfigs.addon
    if not (kc and kc_addon):
        return

    km_addon = kc_addon.keymaps.find("XR Session", space_type='EMPTY', region_type='XR')
    if not km_addon:
        return

    km = kc.keymaps.find("XR", space_type='EMPTY', region_type='XR')
    km_session = kc.keymaps.find("XR Session", space_type='EMPTY', region_type='XR')
    if not (km or km_session):
        return
    
    for action_set in bpy.context.scene.vr_action_sets:
        for action in action_set.actions:
            if (action.type != 'BUTTON' and action.type != 'AXIS') or not action.op:
                continue

            kmi_addon = km_addon.keymap_items.from_xr(action_set.name, action.name)
            if kmi_addon:
                continue

            kmi = None
            if km_session:
                # 1. Check XR Session key map.
                kmi = km_session.keymap_items.from_xr(action_set.name, action.name)

            if not kmi and km:
                # 2. Check XR key map.
                kmi = km.keymap_items.from_xr(action_set.name, action.name)

            if kmi:
                kmi_addon = km_addon.keymap_items.new_from_item(kmi)
                kmi_addon.active = True
                kmi_addon.idname = action.op
                kmi_addon.xr_action_set = action_set.name
                kmi_addon.xr_action = action.name


def vr_get_keymap(context, from_prefs):
    if from_prefs:
        kc = context.window_manager.keyconfigs.user
        return (
            None if (not kc)
                else kc.keymaps.find("XR", space_type='EMPTY', region_type='XR')
        )
    else:
        kc = context.window_manager.keyconfigs.addon
        return (
            None if (not kc)
                else kc.keymaps.find("XR Session", space_type='EMPTY', region_type='XR')
        )


def vr_indented_layout(layout, level):
    indentpx = 16
    if level == 0:
        level = 0.0001
    indent = level * indentpx / bpy.context.region.width

    split = layout.split(factor=indent)
    col = split.column()
    col = split.column()
    return col


# Similar to draw_kmi() from release/scripts/modules/rna_keymap_ui.py
# but only displays operator properties.
def vr_draw_kmi(display_keymaps, kc, km, kmi, layout, level):
    map_type = kmi.map_type

    col = vr_indented_layout(layout, level)

    if kmi.show_expanded:
        col = col.column(align=True)
        box = col.box()
    else:
        box = col.column()

    split = box.split()

    # Header bar.
    row = split.row(align=True)
    row.prop(kmi, "show_expanded", text="", emboss=False)

    row.label(text="Operator Properties")
    if km.is_modal:
        row.separator()
        row.prop(kmi, "propvalue", text="")
    else:
        row.label(text=kmi.name)

    # Expanded, additional event settings.
    if kmi.show_expanded:
        box = col.box()
        
        # Operator properties.
        box.template_keymap_item_properties(kmi)

       # # TODO_XR
       # # Modal keymaps attached to this operator.
       # if not km.is_modal:
           # kmm = kc.keymaps.find_modal(kmi.idname)
           # if kmm:
               # draw_km(display_keymaps, kc, kmm, None, layout, level + 1)
               # layout.context_pointer_set("keymap", km)


@persistent
def vr_ensure_default_landmark(context: bpy.context):
    # Ensure there's a default landmark (scene camera by default).
    landmarks = bpy.context.scene.vr_landmarks
    if not landmarks:
        landmarks.add()
        landmarks[0].type = 'SCENE_CAMERA'


def xr_landmark_active_type_update(self, context):
    wm = context.window_manager
    session_settings = wm.xr_session_settings
    landmark_active = VRLandmark.get_active_landmark(context)

    # Update session's base pose type to the matching type.
    if landmark_active.type == 'SCENE_CAMERA':
        session_settings.base_pose_type = 'SCENE_CAMERA'
    elif landmark_active.type == 'OBJECT':
        session_settings.base_pose_type = 'OBJECT'
    elif landmark_active.type == 'CUSTOM':
        session_settings.base_pose_type = 'CUSTOM'


def xr_landmark_active_base_pose_object_update(self, context):
    session_settings = context.window_manager.xr_session_settings
    landmark_active = VRLandmark.get_active_landmark(context)

    # Update the anchor object to the (new) camera of this landmark.
    session_settings.base_pose_object = landmark_active.base_pose_object


def xr_landmark_active_base_pose_location_update(self, context):
    session_settings = context.window_manager.xr_session_settings
    landmark_active = VRLandmark.get_active_landmark(context)

    session_settings.base_pose_location = landmark_active.base_pose_location


def xr_landmark_active_base_pose_angle_update(self, context):
    session_settings = context.window_manager.xr_session_settings
    landmark_active = VRLandmark.get_active_landmark(context)

    session_settings.base_pose_angle = landmark_active.base_pose_angle


def xr_landmark_type_update(self, context):
    landmark_selected = VRLandmark.get_selected_landmark(context)
    landmark_active = VRLandmark.get_active_landmark(context)

    # Only update session settings data if the changed landmark is actually
    # the active one.
    if landmark_active == landmark_selected:
        xr_landmark_active_type_update(self, context)


def xr_landmark_base_pose_object_update(self, context):
    landmark_selected = VRLandmark.get_selected_landmark(context)
    landmark_active = VRLandmark.get_active_landmark(context)

    # Only update session settings data if the changed landmark is actually
    # the active one.
    if landmark_active == landmark_selected:
        xr_landmark_active_base_pose_object_update(self, context)


def xr_landmark_base_pose_location_update(self, context):
    landmark_selected = VRLandmark.get_selected_landmark(context)
    landmark_active = VRLandmark.get_active_landmark(context)

    # Only update session settings data if the changed landmark is actually
    # the active one.
    if landmark_active == landmark_selected:
        xr_landmark_active_base_pose_location_update(self, context)


def xr_landmark_base_pose_angle_update(self, context):
    landmark_selected = VRLandmark.get_selected_landmark(context)
    landmark_active = VRLandmark.get_active_landmark(context)

    # Only update session settings data if the changed landmark is actually
    # the active one.
    if landmark_active == landmark_selected:
        xr_landmark_active_base_pose_angle_update(self, context)


def xr_landmark_active_update(self, context):
    wm = context.window_manager

    xr_landmark_active_type_update(self, context)
    xr_landmark_active_base_pose_object_update(self, context)
    xr_landmark_active_base_pose_location_update(self, context)
    xr_landmark_active_base_pose_angle_update(self, context)

    if wm.xr_session_state:
        wm.xr_session_state.reset_to_base_pose(context)


class VIEW3D_MT_vr_landmark_menu(Menu):
    bl_label = "Landmark Controls"

    def draw(self, _context):
        layout = self.layout

        layout.operator("view3d.vr_landmark_from_camera")
        layout.operator("view3d.update_vr_landmark")
        layout.separator()
        layout.operator("view3d.cursor_to_vr_landmark")
        layout.operator("view3d.camera_to_vr_landmark")
        layout.operator("view3d.add_camera_from_vr_landmark")


class VRLandmark(PropertyGroup):
    name: bpy.props.StringProperty(
        name="VR Landmark",
        default="Landmark"
    )
    type: bpy.props.EnumProperty(
        name="Type",
        items=[
            ('SCENE_CAMERA', "Scene Camera",
             "Use scene's currently active camera to define the VR view base "
             "location and rotation"),
            ('OBJECT', "Custom Object",
             "Use an existing object to define the VR view base location and "
             "rotation"),
            ('CUSTOM', "Custom Pose",
             "Allow a manually defined position and rotation to be used as "
             "the VR view base pose"),
        ],
        default='SCENE_CAMERA',
        update=xr_landmark_type_update,
    )
    base_pose_object: bpy.props.PointerProperty(
        name="Object",
        type=bpy.types.Object,
        update=xr_landmark_base_pose_object_update,
    )
    base_pose_location: bpy.props.FloatVectorProperty(
        name="Base Pose Location",
        subtype='TRANSLATION',
        update=xr_landmark_base_pose_location_update,
    )
    base_pose_angle: bpy.props.FloatProperty(
        name="Base Pose Angle",
        subtype='ANGLE',
        update=xr_landmark_base_pose_angle_update,
    )

    @staticmethod
    def get_selected_landmark(context):
        scene = context.scene
        landmarks = scene.vr_landmarks

        return (
            None if (len(landmarks) <
                     1) else landmarks[scene.vr_landmarks_selected]
        )

    @staticmethod
    def get_active_landmark(context):
        scene = context.scene
        landmarks = scene.vr_landmarks

        return (
            None if (len(landmarks) <
                     1) else landmarks[scene.vr_landmarks_active]
        )


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
        landmark_selected = VRLandmark.get_selected_landmark(context)

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
            elif landmark_selected.type == 'CUSTOM':
                layout.prop(landmark_selected,
                            "base_pose_location", text="Location")
                layout.prop(landmark_selected,
                            "base_pose_angle", text="Angle")


@persistent
def vr_create_actions(context: bpy.context):
    # Create all vr action sets and actions.
    context = bpy.context
    wm = context.window_manager
    scene = context.scene
    action_sets = scene.vr_action_sets

    if wm.xr_session_state and action_sets:
        for action_set in action_sets:    
            if len(action_set.actions) > 0:
                ok = wm.xr_session_state.create_action_set(context, action_set.name)
                if not ok:
                    return
                actions = action_set.actions 

                interaction_path0 = ""
                interaction_path1 = ""

                for action in actions:
                    ok = wm.xr_session_state.create_action(context, action_set.name, action.name, action.type,
                                                           action.user_path0, action.user_path1, action.threshold, action.op, action.op_flag)
                    if not ok:
                        return

                    if action.type == 'POSE':
                        ok = wm.xr_session_state.create_action_space(context, action_set.name, action.name,
                                                                     action.user_path0, action.user_path1,
                                                                     action.pose_location, action.pose_rotation)
                        if not ok:
                            return
                        
                        if action.pose_is_controller:
                            ok = wm.xr_session_state.set_controller_pose_action(context, action_set.name, action.name)
                            if not ok:
                                return

                    interaction_path0 = action.user_path0 + action.component_path0
                    interaction_path1 = action.user_path1 + action.component_path1

                    ok = wm.xr_session_state.create_action_binding(context, action_set.name, action_set.profile, action.name,
                                                                   interaction_path0, interaction_path1)
                    if not ok:
                        return

        # Set active action set.
        active_action_set = action_sets[scene.vr_action_sets_active]
        if active_action_set and len(active_action_set.actions) > 0:                        
            wm.xr_session_state.set_active_action_set(context, active_action_set.name)


def xr_action_set_active_update(self, context):
    wm = context.window_manager
    if wm.xr_session_state:
        action_set = VRActionSet.get_active_action_set(context)
        if action_set:
            wm.xr_session_state.set_active_action_set(context, action_set.name)


class VRAction(PropertyGroup):
    # Update key map item on operator / name change.
    def update_kmi(self, context):
        if self.ignore_update:
            return

        action_renamed = (self.name != self.name_prev)
        action_name = ""
        if action_renamed:
            action_name = self.name_prev
            self.name_prev = self.name
        else:
            action_name = self.name
 
        action_set = VRActionSet.get_selected_action_set(context, self.from_prefs)
        if action_set:
            action_set_renamed = (action_set.name != action_set.name_prev)
            action_set_name = ""
            if action_set_renamed:
                action_set_name = action_set.name_prev
                # Don't update prev action set name (will be updated in VRActionSet.update_kmis())
                #action_set.name_prev = action_set.name
            else:
                action_set_name = action_set.name
            
            km = vr_get_keymap(context, self.from_prefs)
            if km:
                kmi = km.keymap_items.from_xr(action_set_name, action_name)

                if (self.type != 'BUTTON' and self.type != 'AXIS') or not self.op:
                    if kmi:
                        # Remove any existing key map item.
                        km.keymap_items.remove(kmi)
                    return

                if not kmi:
                    if action_set_renamed or action_renamed:
                        return
                    # Add key map item.
                    kmi = km.keymap_items.new(self.op, 'XR_ACTION', 'ANY',
                                              xr_action_set=action_set.name, xr_action=self.name)
                    kmi.active = True
                else:
                    kmi.idname = self.op
                    kmi.xr_action_set = action_set.name
                    kmi.xr_action = self.name

    def update_name(self, context):
        if self.ignore_update:
            return
        
        action_set = VRActionSet.get_selected_action_set(context, self.from_prefs)
        if not action_set:
            return
        
        self.ignore_update = True # Prevent circular calling on name assignment.

        # Ensure unique name.
        idx = 1
        name_base = self.name
        name = self.name
        while True:
            exists = False
            
            for action in action_set.actions:
                if (action.name == name) and (action.name_prev != self.name_prev):                   
                    name = name_base + str(idx)
                    if len(name) > 64:
                        # Generate random base name.
                        name_base = str(mathutils.noise.random())
                        name = name_base
                        idx = 1
                    else:
                        idx += 1
                        
                    exists = True
                    break
                    
            if not exists:
                break
            
        if self.name != name:
            self.name = name

        self.ignore_update = False
    

    def update_name_and_kmi(self, context):
        if self.ignore_update:
            return

        self.update_name(context)
        self.update_kmi(context)

    name: bpy.props.StringProperty(
        name="VR action",
        description= "Must not contain upper case letters or special characters other than '-', '_', or '.'",
        default="action",
        maxlen=64,
        update=update_name_and_kmi,
    )
    name_prev: bpy.props.StringProperty(
        maxlen=64,
    )
    type: bpy.props.EnumProperty(
        name="Action Type",
        items=[
            ('BUTTON', "Button", "Button input"),
            ('AXIS', "Axis", "2D axis input"),
            ('POSE', "Pose", "3D pose input"),
            ('HAPTIC', "Haptic", "Haptic output"),
        ],
        default='BUTTON',
        update=update_kmi,
    )
    user_path0: bpy.props.StringProperty(
        name="OpenXR user path",
        maxlen=64,
    )
    component_path0: bpy.props.StringProperty(
        name="OpenXR component path",
        maxlen=192,
    )
    user_path1: bpy.props.StringProperty(
        name="OpenXR user path",
        maxlen=64,
    )
    component_path1: bpy.props.StringProperty(
        name="OpenXR component path",
        maxlen=192,
    )
    threshold: bpy.props.FloatProperty(
        name="Input threshold",
        default=0.3,
        min=0.0,
        max=1.0,
    )
    op: bpy.props.StringProperty(
        name="Operator",
        maxlen=64,
        update=update_kmi,
    )
    op_flag: bpy.props.EnumProperty(
        name="Operator Flag",
        items=[
            ('PRESS', "Press",
             "Execute operator on press "
             "(non-modal operators only)"),
            ('RELEASE', "Release",
             "Execute operator on release "
             "(non-modal operators only)"),
            ('MODAL', "Modal",
             "Use modal execution "
             "(modal operators only)"),
        ],
        default='PRESS',
    )
    pose_is_controller: bpy.props.BoolProperty(
        name="Pose will be used for the VR controllers",
    )	
    pose_location: bpy.props.FloatVectorProperty(
        name="Pose location offset",
        subtype='TRANSLATION',
    )
    pose_rotation: bpy.props.FloatVectorProperty(
        name="Pose rotation offset",
        subtype='EULER',
    )
    haptic_duration: bpy.props.FloatProperty(
        name="Haptic duration in seconds",
    )
    haptic_frequency: bpy.props.FloatProperty(
        name="Haptic frequency",
    )
    haptic_amplitude: bpy.props.FloatProperty(
        name="Haptic amplitude",
    )
    from_prefs: BoolProperty(
        # Whether this action is a prefs (or scene) action. 		
    )                   
    ignore_update: BoolProperty(		
        default=False
    )        

    def copy_from(self, o, from_prefs):
        self.ignore_update = True # Prevent update on prop assignment.

        self.name = o.name
        self.name_prev = o.name_prev
        self.type = o.type
        self.user_path0 = o.user_path0
        self.component_path0 = o.component_path0
        self.user_path1 = o.user_path1
        self.component_path1 = o.component_path1
        self.threshold = o.threshold
        self.op = o.op
        self.op_flag = o.op_flag
        self.pose_is_controller = o.pose_is_controller
        self.pose_location = o.pose_location
        self.pose_rotation = o.pose_rotation
        self.haptic_duration = o.haptic_duration
        self.haptic_frequency = o.haptic_frequency
        self.haptic_amplitude = o.haptic_amplitude
        self.from_prefs = from_prefs

        self.ignore_update = False


class VRActionSet(PropertyGroup):
    # Update key map items on name change.
    def update_kmis(self, context):
        action_set_renamed = (self.name != self.name_prev)

        for action in self.actions:
            action.update_kmi(context)

        if action_set_renamed:
            self.name_prev = self.name

    def update_name(self, context):
        if self.ignore_update:
            return

        action_sets = None
        if self.from_prefs:
            prefs = context.preferences.addons[__name__].preferences
            action_sets = prefs.action_sets
        else:
            scene = context.scene
            action_sets = scene.vr_action_sets
        if not action_sets:
            return
        
        self.ignore_update = True # Prevent circular calling on name assignment.

        # Ensure unique name.
        idx = 1
        name_base = self.name
        name = self.name
        while True:
            exists = False
            
            for action_set in action_sets:
                if (action_set.name == name) and (action_set.name_prev != self.name_prev):                   
                    name = name_base + str(idx)
                    if len(name) > 64:
                        # Generate random base name.
                        name_base = str(mathutils.noise.random())
                        name = name_base
                        idx = 1
                    else:
                        idx += 1
                        
                    exists = True
                    break
                    
            if not exists:
                break
            
        if self.name != name:
            self.name = name

        self.ignore_update = False
    

    def update_name_and_kmis(self, context):
        if self.ignore_update:
            return

        self.update_name(context)
        self.update_kmis(context)

    name: bpy.props.StringProperty(
        name="VR action set",
        description="Must not contain upper case letters or special characters other than '-', '_', or '.'",
        default="action_set",
        maxlen=64,
        update=update_name_and_kmis,
    )
    name_prev: bpy.props.StringProperty(
        maxlen=64,
    )
    profile: bpy.props.StringProperty(
        name="OpenXR interaction profile path",
        maxlen=256,
    )
    actions: CollectionProperty(
        name="Actions",
        type=VRAction,
    )
    actions_selected: IntProperty(
        name="Selected Action",		
    )
    from_prefs: BoolProperty(
        # Whether this action set is a prefs (or scene) action set. 		
    )  
    ignore_update: BoolProperty(		
        default=False
    )   
    
    @staticmethod
    def get_active_action_set(context):
        scene = context.scene
        action_sets = scene.vr_action_sets

        return (
            None if (len(action_sets) <
                     1) else action_sets[scene.vr_action_sets_active]
        )

    @staticmethod
    def get_selected_action_set(context, from_prefs):
        action_sets = None
        action_set_selected_idx = 0

        if from_prefs:
            prefs = context.preferences.addons[__name__].preferences
            action_sets = prefs.action_sets
            action_set_selected_idx = prefs.action_sets_selected
        else:
            scene = context.scene
            action_sets = scene.vr_action_sets
            action_set_selected_idx = scene.vr_action_sets_selected

        return (
            None if (len(action_sets) <
                     1) else action_sets[action_set_selected_idx]
        )

    def get_selected_action(self):
        actions = self.actions

        return (
            None if (len(actions) <
                     1) else actions[self.actions_selected]
        )

    def copy_from(self, o, from_prefs):
        self.ignore_update = True # Prevent update on prop assignment.

        self.name = o.name
        self.name_prev = o.name_prev
        self.profile = o.profile

        self.actions.clear()
        idx = 0
        for action in o.actions:
            self.actions.add()
            self.actions[idx].copy_from(action, from_prefs)
            idx += 1

        self.actions_selected = o.actions_selected
        self.from_prefs = from_prefs

        self.ignore_update = False


class VIEW3D_UL_vr_action_sets(UIList):
    def draw_item(self, context, layout, _data, item, icon, _active_data,
                  _active_propname, index):
        action_set = item
        action_set_active_idx = context.scene.vr_action_sets_active

        layout.emboss = 'NONE'

        layout.prop(action_set, "name", text="")

        icon = (
            'RADIOBUT_ON' if (index == action_set_active_idx) else 'RADIOBUT_OFF'
        )
        props = layout.operator(
            "view3d.vr_action_set_activate", text="", icon=icon)
        props.index = index


class VIEW3D_MT_vr_action_set_menu(Menu):
    bl_label = "Action Set Controls"

    def draw(self, _context):
        layout = self.layout

        layout.operator("view3d.vr_action_sets_load_from_prefs")
        layout.operator("view3d.vr_action_set_save_to_prefs")
        layout.operator("view3d.vr_action_sets_clear")


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

        layout.operator("view3d.vr_actions_clear")


class VIEW3D_PT_vr_actions(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VR"
    bl_label = "Actions"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        action_set_selected = VRActionSet.get_selected_action_set(context, False)

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        row0 = layout.row()
        col = row0.column(align=True)
        col.label(text="Action Sets")

        row1 = layout.row()
        row1.template_list("VIEW3D_UL_vr_action_sets", "", scene, "vr_action_sets",
                          scene, "vr_action_sets_selected", rows=3)

        col = row1.column(align=True)
        col.operator("view3d.vr_action_set_add", icon='ADD', text="")
        col.operator("view3d.vr_action_set_remove", icon='REMOVE', text="")

        col.menu("VIEW3D_MT_vr_action_set_menu", icon='DOWNARROW_HLT', text="")

        if action_set_selected:
            action_selected = action_set_selected.get_selected_action()

            row = row0.split()
            col = row.column(align=True)
            col.label(text="Actions")

            row = layout.row()
            col0 = row.column(align=True)
            row = row.split()
            col1 = row.column(align=True)

            col0.prop(action_set_selected, "name", text="Action Set")
            col0.prop(action_set_selected, "profile", text="Profile")

            row1.template_list("VIEW3D_UL_vr_actions", "", action_set_selected, "actions",
                                              action_set_selected, "actions_selected", rows=3)

            col = row1.column(align=True)
            col.operator("view3d.vr_action_add", icon='ADD', text="")
            col.operator("view3d.vr_action_remove", icon='REMOVE', text="")

            col.menu("VIEW3D_MT_vr_action_menu", icon='DOWNARROW_HLT', text="")

            if action_selected:
                col1.prop(action_selected, "name", text="Action")
                col1.prop(action_selected, "type", text="Type")
                col1.prop(action_selected, "user_path0", text="User Path 0")
                col1.prop(action_selected, "component_path0", text="Component Path 0")
                col1.prop(action_selected, "user_path1", text="User Path 1")
                col1.prop(action_selected, "component_path1", text="Component Path 1")

                if action_selected.type == 'BUTTON' or action_selected.type == 'AXIS':
                    col1.prop(action_selected, "threshold", text="Threshold")
                    col1.prop(action_selected, "op", text="Operator")
                    col1.prop(action_selected, "op_flag", text="Operator Flag")
                    # Properties.
                    kc = bpy.context.window_manager.keyconfigs.addon
                    if kc:
                        km = kc.keymaps.find(name="XR Session", space_type='EMPTY', region_type='XR')
                        if km:
                            kmi = km.keymap_items.from_xr(action_set_selected.name, action_selected.name)
                            if kmi:
                                km = km.active()
                                col1.context_pointer_set("keymap", km)
                                vr_draw_kmi([], kc, km, kmi, col1, 0)
                elif action_selected.type == 'POSE':
                    col1.prop(action_selected, "pose_is_controller", text="Use for Controller Poses")
                    col1.prop(action_selected, "pose_location", text="Location Offset")
                    col1.prop(action_selected, "pose_rotation", text="Rotation Offset") 
                elif action_selected.type == 'HAPTIC':
                    col1.prop(action_selected, "haptic_duration", text="Duration")
                    col1.prop(action_selected, "haptic_frequency", text="Frequency")
                    col1.prop(action_selected, "haptic_amplitude", text="Amplitude")


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
        col.prop(session_settings, "show_controllers", text="Controllers")
        col.prop(session_settings, "show_custom_overlays", text="Custom Overlays")
        col.prop(session_settings, "show_selection", text="Selection")
        col.prop(session_settings, "selection_eye", text="Selection Eye")

        col = layout.column(align=True)
        col.prop(session_settings, "clip_start", text="Clip Start")
        col.prop(session_settings, "clip_end", text="End")


class VIEW3D_PT_vr_session(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VR"
    bl_label = "VR Session"

    def draw(self, context):
        layout = self.layout
        session_settings = context.window_manager.xr_session_settings

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

        layout.prop(session_settings, "use_positional_tracking")
        layout.prop(session_settings, "use_absolute_tracking")


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
        layout.label(icon='ERROR', text="Built without VR/OpenXR features.")


class VIEW3D_OT_vr_landmark_add(Operator):
    bl_idname = "view3d.vr_landmark_add"
    bl_label = "Add VR Landmark"
    bl_description = "Add a new VR landmark to the list and select it"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        scene = context.scene
        landmarks = scene.vr_landmarks

        landmarks.add()

        # select newly created set
        scene.vr_landmarks_selected = len(landmarks) - 1

        return {'FINISHED'}


class VIEW3D_OT_vr_landmark_from_camera(Operator):
    bl_idname = "view3d.vr_landmark_from_camera"
    bl_label = "Add VR Landmark from Camera"
    bl_description = "Add a new VR landmark from the active camera object to the list and select it"
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        cam_selected = False

        vl_objects = bpy.context.view_layer.objects
        if vl_objects.active and vl_objects.active.type == 'CAMERA':
            cam_selected = True
        return cam_selected

    def execute(self, context):
        scene = context.scene
        landmarks = scene.vr_landmarks
        cam = context.view_layer.objects.active
        lm = landmarks.add()
        lm.type = 'OBJECT'
        lm.base_pose_object = cam
        lm.name = "LM_" + cam.name

        # select newly created set
        scene.vr_landmarks_selected = len(landmarks) - 1

        return {'FINISHED'}


class VIEW3D_OT_vr_landmark_from_session(Operator):
    bl_idname = "view3d.vr_landmark_from_session"
    bl_label = "Add VR Landmark from session"
    bl_description = "Add VR landmark from the viewer pose of the running VR session to the list and select it"
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        return bpy.types.XrSessionState.is_running(context)

    def execute(self, context):
        scene = context.scene
        landmarks = scene.vr_landmarks
        wm = context.window_manager

        lm = landmarks.add()
        lm.type = "CUSTOM"
        scene.vr_landmarks_selected = len(landmarks) - 1

        loc = wm.xr_session_state.viewer_pose_location
        rot = wm.xr_session_state.viewer_pose_rotation.to_euler()

        lm.base_pose_location = loc
        lm.base_pose_angle = rot[2]

        return {'FINISHED'}


class VIEW3D_OT_update_vr_landmark(Operator):
    bl_idname = "view3d.update_vr_landmark"
    bl_label = "Update Custom VR Landmark"
    bl_description = "Update the selected landmark from the current viewer pose in the VR session"
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        selected_landmark = VRLandmark.get_selected_landmark(context)
        return bpy.types.XrSessionState.is_running(context) and selected_landmark.type == 'CUSTOM'

    def execute(self, context):
        wm = context.window_manager

        lm = VRLandmark.get_selected_landmark(context)

        loc = wm.xr_session_state.viewer_pose_location
        rot = wm.xr_session_state.viewer_pose_rotation.to_euler()

        lm.base_pose_location = loc
        lm.base_pose_angle = rot

        # Re-activate the landmark to trigger viewer reset and flush landmark settings to the session settings.
        xr_landmark_active_update(None, context)

        return {'FINISHED'}


class VIEW3D_OT_vr_landmark_remove(Operator):
    bl_idname = "view3d.vr_landmark_remove"
    bl_label = "Remove VR Landmark"
    bl_description = "Delete the selected VR landmark from the list"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        scene = context.scene
        landmarks = scene.vr_landmarks

        if len(landmarks) > 1:
            landmark_selected_idx = scene.vr_landmarks_selected
            landmarks.remove(landmark_selected_idx)

            scene.vr_landmarks_selected -= 1

        return {'FINISHED'}


class VIEW3D_OT_cursor_to_vr_landmark(Operator):
    bl_idname = "view3d.cursor_to_vr_landmark"
    bl_label = "Cursor to VR Landmark"
    bl_description = "Move the 3D Cursor to the selected VR Landmark"
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        lm = VRLandmark.get_selected_landmark(context)
        if lm.type == 'SCENE_CAMERA':
            return context.scene.camera is not None
        elif lm.type == 'OBJECT':
            return lm.base_pose_object is not None

        return True

    def execute(self, context):
        scene = context.scene
        lm = VRLandmark.get_selected_landmark(context)
        if lm.type == 'SCENE_CAMERA':
            lm_pos = scene.camera.location
        elif lm.type == 'OBJECT':
            lm_pos = lm.base_pose_object.location
        else:
            lm_pos = lm.base_pose_location
        scene.cursor.location = lm_pos

        return{'FINISHED'}


class VIEW3D_OT_add_camera_from_vr_landmark(Operator):
    bl_idname = "view3d.add_camera_from_vr_landmark"
    bl_label = "New Camera from VR Landmark"
    bl_description = "Create a new Camera from the selected VR Landmark"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        import math

        scene = context.scene
        lm = VRLandmark.get_selected_landmark(context)

        cam = bpy.data.cameras.new("Camera_" + lm.name)
        new_cam = bpy.data.objects.new("Camera_" + lm.name, cam)
        scene.collection.objects.link(new_cam)
        angle = lm.base_pose_angle
        new_cam.location = lm.base_pose_location
        new_cam.rotation_euler = (math.pi, 0, angle)

        return {'FINISHED'}


class VIEW3D_OT_camera_to_vr_landmark(Operator):
    bl_idname = "view3d.camera_to_vr_landmark"
    bl_label = "Scene Camera to VR Landmark"
    bl_description = "Position the scene camera at the selected landmark"
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.scene.camera is not None

    def execute(self, context):
        import math

        scene = context.scene
        lm = VRLandmark.get_selected_landmark(context)

        cam = scene.camera
        angle = lm.base_pose_angle
        cam.location = lm.base_pose_location
        cam.rotation_euler = (math.pi / 2, 0, angle)

        return {'FINISHED'}


class VIEW3D_OT_vr_landmark_activate(Operator):
    bl_idname = "view3d.vr_landmark_activate"
    bl_label = "Activate VR Landmark"
    bl_description = "Change to the selected VR landmark from the list"
    bl_options = {'UNDO', 'REGISTER'}

    index: IntProperty(
        name="Index",
        options={'HIDDEN'},
    )

    def execute(self, context):
        scene = context.scene

        if self.index >= len(scene.vr_landmarks):
            return {'CANCELLED'}

        scene.vr_landmarks_active = (
            self.index if self.properties.is_property_set(
                "index") else scene.vr_landmarks_selected
        )

        return {'FINISHED'}


class VIEW3D_OT_vr_action_set_add(Operator):
    bl_idname = "view3d.vr_action_set_add"
    bl_label = "Add VR Action Set"
    bl_description = "Add a new VR action set to the scene"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        scene = context.scene
        action_sets = scene.vr_action_sets

        action_sets.add()
        idx = len(action_sets) - 1
        action_sets[idx].from_prefs = False
        action_sets[idx].update_name(context)
        action_sets[idx].name_prev = action_sets[idx].name

        # Select newly created set.
        scene.vr_action_sets_selected = idx

        return {'FINISHED'}


class VIEW3D_OT_vr_action_set_remove(Operator):
    bl_idname = "view3d.vr_action_set_remove"
    bl_label = "Remove VR Action Set"
    bl_description = "Delete the selected VR action set from the scene"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        scene = context.scene
        action_sets = scene.vr_action_sets

        if len(action_sets) > 0:
            action_set_selected_idx = scene.vr_action_sets_selected
            action_set = action_sets[action_set_selected_idx]

            # Remove key map items.
            km = vr_get_keymap(context, False)
            if km:
                for action in action_set.actions:
                    kmi = km.keymap_items.from_xr(action_set.name, action.name)
                    if kmi:
                        km.keymap_items.remove(kmi)

            action_sets.remove(action_set_selected_idx)

            scene.vr_action_sets_selected -= 1
            if scene.vr_action_sets_selected < 1:
                scene.vr_action_sets_active = 0

        return {'FINISHED'}


class VIEW3D_OT_vr_action_set_activate(Operator):
    bl_idname = "view3d.vr_action_set_activate"
    bl_label = "Activate VR Action Set"
    bl_description = "Set the VR action set to use for the session"
    bl_options = {'UNDO', 'REGISTER'}

    index: IntProperty(
        name="Index",
        options={'HIDDEN'},
    )

    def execute(self, context):
        scene = context.scene

        if self.index >= len(scene.vr_action_sets):
            return {'CANCELLED'}

        scene.vr_action_sets_active = (
            self.index if self.properties.is_property_set(
                "index") else scene.vr_action_sets.selected
        )

        return {'FINISHED'}


class VIEW3D_OT_vr_action_sets_load_from_prefs(Operator):
    bl_idname = "view3d.vr_action_sets_load_from_prefs"
    bl_label = "Load from Preferences"
    bl_description = "Add VR action sets from user preferences to the scene"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        scene = context.scene
        prefs = context.preferences.addons[__name__].preferences
		
        scene_action_sets = scene.vr_action_sets
        prefs_action_sets = prefs.action_sets

        idx = len(scene_action_sets) - 1
        idx_prev = idx

        scene_km = vr_get_keymap(context, False)
        prefs_km = vr_get_keymap(context, True)

        for action_set in prefs_action_sets:
            # Check if action set with same name already exists.
            exists = False
            for _set in scene_action_sets:
                if (_set.name == action_set.name):
                    exists = True
                    break
            if not exists:
                scene_action_sets.add()
                idx += 1

                # Update key map.
                if scene_km and prefs_km:
                    for action in action_set.actions:
                        if (action.type != 'BUTTON' and action.type != 'AXIS') or not action.op:
                            continue
                        prefs_kmi = prefs_km.keymap_items.from_xr(action_set.name, action.name)
                        if prefs_kmi:
                            kmi = scene_km.keymap_items.new_from_item(prefs_kmi)
                            kmi.active = True                   
                            kmi.idname = action.op
                            kmi.xr_action_set = action_set.name
                            kmi.xr_action = action.name

                scene_action_sets[idx].copy_from(action_set, False)

        if (idx != idx_prev):
            # Select first newly-added action set.
            scene.vr_action_sets_selected = idx_prev + 1

        return {'FINISHED'}


class VIEW3D_OT_vr_action_set_save_to_prefs(Operator):
    bl_idname = "view3d.vr_action_set_save_to_prefs"
    bl_label = "Save to Preferences"
    bl_description = "Save selected VR action set to user preferences"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        scene = context.scene
        prefs = context.preferences.addons[__name__].preferences

        scene_action_set = VRActionSet.get_selected_action_set(context, False)
        if not scene_action_set:
            return {'CANCELLED'}
        prefs_action_sets = prefs.action_sets

        # Check if action set with same name already exists.
        for action_set in prefs_action_sets:
            if (action_set.name == scene_action_set.name):
                return {'CANCELLED'}

        prefs_action_sets.add()
        idx = len(prefs_action_sets) - 1

        # Update key map.
        scene_km = vr_get_keymap(context, False)
        prefs_km = vr_get_keymap(context, True)		
        if scene_km and prefs_km:
            for action in scene_action_set.actions:
                if (action.type != 'BUTTON' and action.type != 'AXIS') or not action.op:
                    continue
                scene_kmi = scene_km.keymap_items.from_xr(scene_action_set.name, action.name)
                if scene_kmi:
                    kmi = prefs_km.keymap_items.new_from_item(scene_kmi)
                    kmi.active = True
                    kmi.idname = action.op
                    kmi.xr_action_set = scene_action_set.name
                    kmi.xr_action = action.name

        prefs_action_sets[idx].copy_from(scene_action_set, True)

        prefs.action_sets_selected = idx

        return {'FINISHED'}


class VIEW3D_OT_vr_action_sets_clear(Operator):
    bl_idname = "view3d.vr_action_sets_clear"
    bl_label = "Clear VR Action Sets"
    bl_description = "Delete all VR action sets from the scene"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        scene = context.scene
        action_sets = scene.vr_action_sets

        if len(action_sets) > 0:
            # Remove key map items.
            km = vr_get_keymap(context, False)
            if km:
                for action_set in action_sets:
                    for action in action_set.actions:
                        kmi = km.keymap_items.from_xr(action_set.name, action.name)
                        if kmi:
                            km.keymap_items.remove(kmi)

            action_sets.clear()

            scene.vr_action_sets_selected = 0
            scene.vr_action_sets_active = 0

        return {'FINISHED'}


class VIEW3D_OT_vr_action_add(Operator):
    bl_idname = "view3d.vr_action_add"
    bl_label = "Add VR Action"
    bl_description = "Add a new VR action to the list and select it"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        action_set = VRActionSet.get_selected_action_set(context, False)

        if action_set:
            actions = action_set.actions

            actions.add()
            idx = len(actions) - 1
            actions[idx].from_prefs = False
            actions[idx].update_name(context)
            actions[idx].name_prev = actions[idx].name

            # Select newly created action.
            action_set.actions_selected = idx

        return {'FINISHED'}


class VIEW3D_OT_vr_action_remove(Operator):
    bl_idname = "view3d.vr_action_remove"
    bl_label = "Remove VR Action"
    bl_description = "Delete the selected VR action from the list"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        action_set = VRActionSet.get_selected_action_set(context, False)

        if action_set:
            actions = action_set.actions

            if len(actions) > 0:
                action_selected_idx = action_set.actions_selected
                action = actions[action_selected_idx]

                # Remove key map item.
                km = vr_get_keymap(context, False)
                if km:
                    kmi = km.keymap_items.from_xr(action_set.name, action.name)
                    if kmi:
                        km.keymap_items.remove(kmi)

                actions.remove(action_selected_idx)

                action_set.actions_selected -= 1

        return {'FINISHED'}


class VIEW3D_OT_vr_actions_clear(Operator):
    bl_idname = "view3d.vr_actions_clear"
    bl_label = "Clear VR Actions"
    bl_description = "Delete all VR actions for the selected action set"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        action_set = VRActionSet.get_selected_action_set(context, False)

        if action_set:
            actions = action_set.actions

            if len(actions) > 0:
                # Remove key map items.
                km = vr_get_keymap(context, False)
                if km:
                    for action in actions:
                        kmi = km.keymap_items.from_xr(action_set.name, action.name)
                        if kmi:
                            km.keymap_items.remove(kmi)

                actions.clear()

            action_set.actions_selected = 0

        return {'FINISHED'}


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
        layout.prop(scene, "vr_headset_ob_ui_expand",
            icon="TRIA_DOWN" if scene.vr_headset_ob_ui_expand else "TRIA_RIGHT",
            text="Headset Object", emboss=False
        )
        if scene.vr_headset_ob_ui_expand:
            row = layout.row()
            row.separator()
            row.prop(session_settings, "headset_object", text="")
            row.prop(session_settings, "headset_object_enable", text="Enable")
            row.prop(session_settings, "headset_object_autokey", text="Auto Key")

        layout.prop(view3d.shading, "vr_show_controllers")
        layout.prop(scene, "vr_controller0_ob_ui_expand",
            icon="TRIA_DOWN" if scene.vr_controller0_ob_ui_expand else "TRIA_RIGHT",
            text="Controller 0 Object", emboss=False
        )
        if scene.vr_controller0_ob_ui_expand:
            row = layout.row()
            row.separator()
            row.prop(session_settings, "controller0_object", text="")
            row.prop(session_settings, "controller0_object_enable", text="Enable")
            row.prop(session_settings, "controller0_object_autokey", text="Auto Key")

        layout.prop(scene, "vr_controller1_ob_ui_expand",
            icon="TRIA_DOWN" if scene.vr_controller1_ob_ui_expand else "TRIA_RIGHT",
            text="Controller 1 Object", emboss=False
        )
        if scene.vr_controller1_ob_ui_expand:
            row = layout.row()
            row.separator()
            row.prop(session_settings, "controller1_object", text="")
            row.prop(session_settings, "controller1_object_enable", text="Enable")
            row.prop(session_settings, "controller1_object_autokey", text="Auto Key")

        layout.prop(view3d.shading, "vr_show_landmarks")
        layout.prop(view3d, "mirror_xr_session")


class VIEW3D_GT_vr_camera_cone(Gizmo):
    bl_idname = "VIEW_3D_GT_vr_camera_cone"

    aspect = 1.0, 1.0

    def draw(self, context):
        import bgl

        if not hasattr(self, "frame_shape"):
            aspect = self.aspect

            frame_shape_verts = (
                (-aspect[0], -aspect[1], -1.0),
                (aspect[0], -aspect[1], -1.0),
                (aspect[0], aspect[1], -1.0),
                (-aspect[0], aspect[1], -1.0),
            )
            lines_shape_verts = (
                (0.0, 0.0, 0.0),
                frame_shape_verts[0],
                (0.0, 0.0, 0.0),
                frame_shape_verts[1],
                (0.0, 0.0, 0.0),
                frame_shape_verts[2],
                (0.0, 0.0, 0.0),
                frame_shape_verts[3],
            )

            self.frame_shape = self.new_custom_shape(
                'LINE_LOOP', frame_shape_verts)
            self.lines_shape = self.new_custom_shape(
                'LINES', lines_shape_verts)

        # Ensure correct GL state (otherwise other gizmos might mess that up)
        bgl.glLineWidth(1)
        bgl.glEnable(bgl.GL_BLEND)

        self.draw_custom_shape(self.frame_shape)
        self.draw_custom_shape(self.lines_shape)


class VIEW3D_GT_vr_controller_axes(Gizmo):
    bl_idname = "VIEW_3D_GT_vr_controller_axes"

    def draw(self, context):
        import bgl

        bgl.glLineWidth(1)
        bgl.glEnable(bgl.GL_BLEND)

        self.color = 1.0, 0.2, 0.322
        self.draw_preset_arrow(self.matrix_basis, axis='POS_X')
        self.color = 0.545, 0.863, 0.0
        self.draw_preset_arrow(self.matrix_basis, axis='POS_Y')
        self.color = 0.157, 0.565, 1.0
        self.draw_preset_arrow(self.matrix_basis, axis='POS_Z')


class VIEW3D_GGT_vr_viewer_pose(GizmoGroup):
    bl_idname = "VIEW3D_GGT_vr_viewer_pose"
    bl_label = "VR Viewer Pose Indicator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT', 'SCALE', 'VR_REDRAWS'}

    @classmethod
    def poll(cls, context):
        view3d = context.space_data
        return (
            view3d.shading.vr_show_virtual_camera and
            bpy.types.XrSessionState.is_running(context) and
            not view3d.mirror_xr_session
        )

    @staticmethod
    def _get_viewer_pose_matrix(context):
        from mathutils import Matrix

        wm = context.window_manager

        loc = wm.xr_session_state.viewer_pose_location
        rot = wm.xr_session_state.viewer_pose_rotation

        rotmat = Matrix.Identity(3)
        rotmat.rotate(rot)
        rotmat.resize_4x4()
        transmat = Matrix.Translation(loc)

        return transmat @ rotmat

    def setup(self, context):
        gizmo = self.gizmos.new(VIEW3D_GT_vr_camera_cone.bl_idname)
        gizmo.aspect = 1 / 3, 1 / 4

        gizmo.color = gizmo.color_highlight = 0.2, 0.6, 1.0
        gizmo.alpha = 1.0

        self.gizmo = gizmo

    def draw_prepare(self, context):
        self.gizmo.matrix_basis = self._get_viewer_pose_matrix(context)


class VIEW3D_GGT_vr_controller_poses(GizmoGroup):
    bl_idname = "VIEW3D_GGT_vr_controller_poses"
    bl_label = "VR Controller Poses Indicator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT', 'SCALE', 'VR_REDRAWS'}

    @classmethod
    def poll(cls, context):
        view3d = context.space_data
        return (
            view3d.shading.vr_show_controllers and
            bpy.types.XrSessionState.is_running(context) and
            not view3d.mirror_xr_session
        )

    @staticmethod
    def _get_controller_pose_matrix(context, idx, scale):
        from mathutils import Matrix

        wm = context.window_manager

        loc = None
        rot = None
        if idx == 0:
            loc = wm.xr_session_state.controller_pose0_location
            rot = wm.xr_session_state.controller_pose0_rotation
        elif idx == 1:
            loc = wm.xr_session_state.controller_pose1_location
            rot = wm.xr_session_state.controller_pose1_rotation
        else:
            return Matrix.Identity(4);

        rotmat = Matrix.Identity(3)
        rotmat.rotate(rot)
        rotmat.resize_4x4()
        transmat = Matrix.Translation(loc)
        scalemat = Matrix.Scale(scale, 4)

        return transmat @ rotmat @ scalemat

    def setup(self, context):
        for idx in range(2):
            gizmo = self.gizmos.new(VIEW3D_GT_vr_controller_axes.bl_idname)
            gizmo.aspect = 1 / 3, 1 / 4
 
            gizmo.color = gizmo.color_highlight = 1.0, 1.0, 1.0
            gizmo.alpha = 1.0

        self.gizmo = gizmo

    def draw_prepare(self, context):
        view3d = context.space_data
        scale = 0.5
        if view3d.mirror_xr_session:
            scale = 0.1
        idx = 0
        for gizmo in self.gizmos:
            gizmo.matrix_basis = self._get_controller_pose_matrix(context, idx, scale)
            idx += 1


class VIEW3D_GGT_vr_landmarks(GizmoGroup):
    bl_idname = "VIEW3D_GGT_vr_landmarks"
    bl_label = "VR Landmark Indicators"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT', 'SCALE'}

    @classmethod
    def poll(cls, context):
        view3d = context.space_data
        return (
            view3d.shading.vr_show_landmarks
        )

    def setup(self, context):
        pass

    def draw_prepare(self, context):
        # first delete the old gizmos
        for g in self.gizmos:
            self.gizmos.remove(g)

        from math import radians
        from mathutils import Matrix, Euler
        scene = context.scene
        landmarks = scene.vr_landmarks

        for lm in landmarks:
            if ((lm.type == 'SCENE_CAMERA' and not scene.camera) or
                    (lm.type == 'OBJECT' and not lm.base_pose_object)):
                continue

            gizmo = self.gizmos.new(VIEW3D_GT_vr_camera_cone.bl_idname)
            gizmo.aspect = 1 / 3, 1 / 4

            gizmo.color = gizmo.color_highlight = 0.2, 1.0, 0.6
            gizmo.alpha = 1.0

            self.gizmo = gizmo

            if lm.type == 'SCENE_CAMERA':
                cam = scene.camera
                lm_mat = cam.matrix_world if cam else Matrix.Identity(4)
            elif lm.type == 'OBJECT':
                lm_mat = lm.base_pose_object.matrix_world
            else:
                angle = lm.base_pose_angle
                raw_rot = Euler((radians(90.0), 0, angle))

                rotmat = Matrix.Identity(3)
                rotmat.rotate(raw_rot)
                rotmat.resize_4x4()

                transmat = Matrix.Translation(lm.base_pose_location)

                lm_mat = transmat @ rotmat

            self.gizmo.matrix_basis = lm_mat


class VRPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    action_sets: CollectionProperty(
        name="Action Sets",
        type=VRActionSet,
    )	
    action_sets_selected: IntProperty(
        name="Selected Action Set",		
    )

    def draw(self, context):
        PREFERENCES_PT_vr_actions.draw(self, context)


class PREFERENCES_UL_vr_action_sets(UIList):
    def draw_item(self, context, layout, _data, item, icon, _active_data,
                  _active_propname, index):
        action_set = item

        layout.emboss = 'NONE'

        layout.prop(action_set, "name", text="")


class PREFERENCES_MT_vr_action_set_menu(Menu):
    bl_label = "Action Set Controls"

    def draw(self, _context):
        layout = self.layout

        layout.operator("preferences.vr_action_sets_clear")


class PREFERENCES_UL_vr_actions(UIList):
    def draw_item(self, context, layout, _data, item, icon, _active_data,
                  _active_propname, index):
        action = item

        layout.emboss = 'NONE'

        layout.prop(action, "name", text="")


class PREFERENCES_MT_vr_action_menu(Menu):
    bl_label = "Action Controls"

    def draw(self, _context):
        layout = self.layout

        layout.operator("preferences.vr_actions_clear")


class PREFERENCES_PT_vr_actions(Panel):
    bl_space_type = 'PREFERENCES'
    bl_region_type = 'WINDOW'
    bl_category = "VR"
    bl_label = "Actions"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        prefs = context.preferences.addons[__name__].preferences

        action_set_selected = VRActionSet.get_selected_action_set(context, True)

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        row0 = layout.row()
        col = row0.column(align=True)
        col.label(text="Action Sets")
        
        row1 = layout.row()
        row1.template_list("PREFERENCES_UL_vr_action_sets", "", prefs, "action_sets",
                          prefs, "action_sets_selected", rows=3)

        col = row1.column(align=True)
        col.operator("preferences.vr_action_set_add", icon='ADD', text="")
        col.operator("preferences.vr_action_set_remove", icon='REMOVE', text="")

        col.menu("PREFERENCES_MT_vr_action_set_menu", icon='DOWNARROW_HLT', text="")

        if action_set_selected:
            action_selected = action_set_selected.get_selected_action()

            row = row0.split()
            col = row.column(align=True)
            col.label(text="Actions")

            row = layout.row()
            col0 = row.column(align=True)
            row = row.split()
            col1 = row.column(align=True)

            col0.prop(action_set_selected, "name", text="Action Set")
            col0.prop(action_set_selected, "profile", text="Profile")

            row1.template_list("PREFERENCES_UL_vr_actions", "", action_set_selected, "actions",
                                              action_set_selected, "actions_selected", rows=3)

            col = row1.column(align=True)
            col.operator("preferences.vr_action_add", icon='ADD', text="")
            col.operator("preferences.vr_action_remove", icon='REMOVE', text="")

            col.menu("PREFERENCES_MT_vr_action_menu", icon='DOWNARROW_HLT', text="")

            if action_selected:
                col1.prop(action_selected, "name", text="Action")
                col1.prop(action_selected, "type", text="Type")
                col1.prop(action_selected, "user_path0", text="User Path 0")
                col1.prop(action_selected, "component_path0", text="Component Path 0")
                col1.prop(action_selected, "user_path1", text="User Path 1")
                col1.prop(action_selected, "component_path1", text="Component Path 1")

                if action_selected.type == 'BUTTON' or action_selected.type == 'AXIS':
                    col1.prop(action_selected, "threshold", text="Threshold")
                    col1.prop(action_selected, "op", text="Operator")
                    col1.prop(action_selected, "op_flag", text="Operator Flag")
                    # Properties.
                    kc = bpy.context.window_manager.keyconfigs.user
                    if kc:
                        km = kc.keymaps.find(name="XR", space_type='EMPTY', region_type='XR')
                        if km:
                            kmi = km.keymap_items.from_xr(action_set_selected.name, action_selected.name)
                            if kmi:
                                km = km.active()
                                col1.context_pointer_set("keymap", km)
                                vr_draw_kmi([], kc, km, kmi, col1, 0)
                elif action_selected.type == 'POSE':
                    col1.prop(action_selected, "pose_is_controller", text="Use for Controller Poses")
                    col1.prop(action_selected, "pose_location", text="Location Offset")
                    col1.prop(action_selected, "pose_rotation", text="Rotation Offset")  
                elif action_selected.type == 'HAPTIC':
                    col1.prop(action_selected, "haptic_duration", text="Duration")
                    col1.prop(action_selected, "haptic_frequency", text="Frequency")
                    col1.prop(action_selected, "haptic_amplitude", text="Amplitude")


class PREFERENCES_OT_vr_action_set_add(Operator):
    bl_idname = "preferences.vr_action_set_add"
    bl_label = "Add VR Action Set"
    bl_description = "Add a new VR action set to user preferences"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        prefs = context.preferences.addons[__name__].preferences
        action_sets = prefs.action_sets

        action_sets.add()
        idx = len(action_sets) - 1
        action_sets[idx].from_prefs = True
        action_sets[idx].update_name(context)
        action_sets[idx].name_prev = action_sets[idx].name

        # Select newly created set.
        prefs.action_sets_selected = idx

        return {'FINISHED'}


class PREFERENCES_OT_vr_action_set_remove(Operator):
    bl_idname = "preferences.vr_action_set_remove"
    bl_label = "Remove VR Action Set"
    bl_description = "Delete the selected VR action set from user preferences"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        prefs = context.preferences.addons[__name__].preferences
        action_sets = prefs.action_sets

        if len(action_sets) > 0:
            action_set_selected_idx = prefs.action_sets_selected
            action_set = action_sets[action_set_selected_idx]

            # Remove key map items.
            km = vr_get_keymap(context, True)
            if km:
                for action in action_set.actions:
                    kmi = km.keymap_items.from_xr(action_set.name, action.name)
                    if kmi:
                        km.keymap_items.remove(kmi)

            action_sets.remove(action_set_selected_idx)

            prefs.action_sets_selected -= 1

        return {'FINISHED'}


class PREFERENCES_OT_vr_action_sets_clear(Operator):
    bl_idname = "preferences.vr_action_sets_clear"
    bl_label = "Clear VR Action Sets"
    bl_description = "Delete all VR action sets from user preferences"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        prefs = context.preferences.addons[__name__].preferences
        action_sets = prefs.action_sets

        if len(action_sets) > 0:
            # Remove key map items.
            km = vr_get_keymap(context, True)
            if km:
                for action_set in action_sets:
                    for action in action_set.actions:
                        kmi = km.keymap_items.from_xr(action_set.name, action.name)
                        if kmi:
                            km.keymap_items.remove(kmi)

            action_sets.clear()

            prefs.action_sets_selected = 0

        return {'FINISHED'}


class PREFERENCES_OT_vr_action_add(Operator):
    bl_idname = "preferences.vr_action_add"
    bl_label = "Add VR Action"
    bl_description = "Add a new VR action to the list and select it"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        action_set = VRActionSet.get_selected_action_set(context, True)

        if action_set:
            actions = action_set.actions

            actions.add()
            idx = len(actions) - 1
            actions[idx].from_prefs = True
            actions[idx].update_name(context)
            actions[idx].name_prev = actions[idx].name

            # Select newly created action.
            action_set.actions_selected = idx

        return {'FINISHED'}


class PREFERENCES_OT_vr_action_remove(Operator):
    bl_idname = "preferences.vr_action_remove"
    bl_label = "Remove VR Action"
    bl_description = "Delete the selected VR action from the list"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        action_set = VRActionSet.get_selected_action_set(context, True)

        if action_set:
            actions = action_set.actions

            if len(actions) > 0:
                action_selected_idx = action_set.actions_selected
                action = actions[action_selected_idx]

                # Remove key map item.
                km = vr_get_keymap(context, True)
                if km:
                    kmi = km.keymap_items.from_xr(action_set.name, action.name)
                    if kmi:
                        km.keymap_items.remove(kmi)

                actions.remove(action_selected_idx)

                action_set.actions_selected -= 1

        return {'FINISHED'}


class PREFERENCES_OT_vr_actions_clear(Operator):
    bl_idname = "preferences.vr_actions_clear"
    bl_label = "Clear VR Actions"
    bl_description = "Delete all VR actions for the selected action set"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        action_set = VRActionSet.get_selected_action_set(context, True)

        if action_set:
            actions = action_set.actions

            if len(actions) > 0:
                # Remove key map items.
                km = vr_get_keymap(context, True)
                if km:
                    for action in actions:
                        kmi = km.keymap_items.from_xr(action_set.name, action.name)
                        if kmi:
                            km.keymap_items.remove(kmi)                   

                actions.clear()

            action_set.actions_selected = 0

        return {'FINISHED'}


classes = (
    VIEW3D_PT_vr_session,
    VIEW3D_PT_vr_session_view,
    VIEW3D_PT_vr_landmarks,
    VIEW3D_PT_vr_actions,
    VIEW3D_PT_vr_viewport_feedback,

    VRLandmark,
    VIEW3D_UL_vr_landmarks,
    VIEW3D_MT_vr_landmark_menu,

    VIEW3D_OT_vr_landmark_add,
    VIEW3D_OT_vr_landmark_remove,
    VIEW3D_OT_vr_landmark_activate,
    VIEW3D_OT_vr_landmark_from_session,
    VIEW3D_OT_add_camera_from_vr_landmark,
    VIEW3D_OT_camera_to_vr_landmark,
    VIEW3D_OT_vr_landmark_from_camera,
    VIEW3D_OT_cursor_to_vr_landmark,
    VIEW3D_OT_update_vr_landmark,

    VRAction,
    VRActionSet,
    VIEW3D_UL_vr_action_sets,
    VIEW3D_MT_vr_action_set_menu,
    VIEW3D_UL_vr_actions,
    VIEW3D_MT_vr_action_menu,

    VIEW3D_OT_vr_action_set_add,
    VIEW3D_OT_vr_action_set_remove,
    VIEW3D_OT_vr_action_set_activate,
    VIEW3D_OT_vr_action_sets_load_from_prefs,
    VIEW3D_OT_vr_action_set_save_to_prefs,
    VIEW3D_OT_vr_action_sets_clear,
    VIEW3D_OT_vr_action_add,
    VIEW3D_OT_vr_action_remove,
    VIEW3D_OT_vr_actions_clear,

    VIEW3D_GT_vr_camera_cone,
    VIEW3D_GT_vr_controller_axes,
    VIEW3D_GGT_vr_viewer_pose,
    VIEW3D_GGT_vr_controller_poses,
    VIEW3D_GGT_vr_landmarks,

    VRPreferences,
    #PREFERENCES_PT_vr_actions,
    PREFERENCES_UL_vr_action_sets,
    PREFERENCES_MT_vr_action_set_menu,
    PREFERENCES_UL_vr_actions,
    PREFERENCES_MT_vr_action_menu,

    PREFERENCES_OT_vr_action_set_add,
    PREFERENCES_OT_vr_action_set_remove,
    PREFERENCES_OT_vr_action_sets_clear,
    PREFERENCES_OT_vr_action_add,
    PREFERENCES_OT_vr_action_remove,
    PREFERENCES_OT_vr_actions_clear,
)


def register():
    if not bpy.app.build_options.xr_openxr:
        bpy.utils.register_class(VIEW3D_PT_vr_info)
        return

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.vr_landmarks = CollectionProperty(
        name="Landmark",
        type=VRLandmark,
    )
    bpy.types.Scene.vr_landmarks_selected = IntProperty(
        name="Selected Landmark"
    )
    bpy.types.Scene.vr_landmarks_active = IntProperty(
        update=xr_landmark_active_update,
    )
    bpy.types.Scene.vr_action_sets = CollectionProperty(
        name="Action Set",
        type=VRActionSet,
    )	
    bpy.types.Scene.vr_action_sets_selected = IntProperty(
        name="Selected Action Set",
    )	
    bpy.types.Scene.vr_action_sets_active = IntProperty(
        default=0,
        update=xr_action_set_active_update,
    )
    # View3DShading is the only per 3D-View struct with custom property
    # support, so "abusing" that to get a per 3D-View option.
    bpy.types.View3DShading.vr_show_virtual_camera = BoolProperty(
        name="Show VR Camera"
    )
    bpy.types.View3DShading.vr_show_controllers = BoolProperty(
        name="Show VR Controllers"
    )
    bpy.types.View3DShading.vr_show_landmarks = BoolProperty(
        name="Show Landmarks"
    )
    bpy.types.Scene.vr_headset_ob_ui_expand = BoolProperty(
        name="",
        default=False,
    )
    bpy.types.Scene.vr_controller0_ob_ui_expand = BoolProperty(
        name="",
        default=False,
    )
    bpy.types.Scene.vr_controller1_ob_ui_expand = BoolProperty(
        name="",
        default=False,
    )

    bpy.app.handlers.load_post.append(vr_ensure_default_landmark)
    bpy.app.handlers.load_post.append(vr_load_action_properties)
    bpy.app.handlers.xr_session_start_pre.append(vr_create_actions)

    # Register add-on key map.
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        kc.keymaps.new(name="XR Session", space_type='EMPTY', region_type='XR')


def unregister():
    if not bpy.app.build_options.xr_openxr:
        bpy.utils.unregister_class(VIEW3D_PT_vr_info)
        return

    # Unregister add-on key map.
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.find("XR Session", space_type='EMPTY', region_type='XR')
        if km:
            kc.keymaps.remove(km)

    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.vr_landmarks
    del bpy.types.Scene.vr_landmarks_selected
    del bpy.types.Scene.vr_landmarks_active
    del bpy.types.Scene.vr_action_sets
    del bpy.types.Scene.vr_action_sets_selected
    del bpy.types.Scene.vr_action_sets_active
    del bpy.types.View3DShading.vr_show_virtual_camera
    del bpy.types.View3DShading.vr_show_controllers
    del bpy.types.View3DShading.vr_show_landmarks
    del bpy.types.Scene.vr_headset_ob_ui_expand
    del bpy.types.Scene.vr_controller0_ob_ui_expand
    del bpy.types.Scene.vr_controller1_ob_ui_expand

    bpy.app.handlers.load_post.remove(vr_ensure_default_landmark)
    bpy.app.handlers.load_post.remove(vr_load_action_properties)
    bpy.app.handlers.xr_session_start_pre.remove(vr_create_actions)


if __name__ == "__main__":
    register()
