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
)
from bpy.props import(
    CollectionProperty,
    IntProperty,
)
from bl_ui.space_view3d import (
    VIEW3D_PT_shading_lighting,
    VIEW3D_PT_shading_color,
    VIEW3D_PT_shading_options,
)

bl_info = {
    "name": "Basic VR Viewer",
    "author": "Julian Eisel (Severin)",
    "version": (0, 0, 2),
    "blender": (2, 83, 2),
    "location": "3D View > Sidebar > VR",
    "description": ("View the viewport with virtual reality glasses "
                    "(head-mounted displays)"),
    "support": "OFFICIAL",
    "warning": "This is an early, limited preview of in development "
               "VR support for Blender.",
    "category": "3D View",
}


def xr_pose_bookmark_type_update(self, context):
    wm = context.window_manager
    session_settings = wm.xr_session_settings
    bookmark_active = VRPoseBookmark.get_active_bookmark(context)

    if not bookmark_active:
        return

    # Update session's base pose type to the matching type.
    if bookmark_active.type == 'SCENE_CAMERA':
        session_settings.base_pose_type = 'SCENE_CAMERA'
    elif bookmark_active.type == 'USER_CAMERA':
        session_settings.base_pose_type = 'OBJECT'
    elif bookmark_active.type == 'CUSTOM':
        session_settings.base_pose_type = 'CUSTOM'


def xr_pose_bookmark_camera_update(self, context):
    session_settings = context.window_manager.xr_session_settings
    bookmark_active = VRPoseBookmark.get_active_bookmark(context)

    if bookmark_active:
        # Update the anchor object to the (new) camera of this bookmark.
        session_settings.base_pose_object = bookmark_active.base_pose_camera


def xr_pose_bookmark_base_pose_location_update(self, context):
    session_settings = context.window_manager.xr_session_settings
    bookmark_active = VRPoseBookmark.get_active_bookmark(context)

    if bookmark_active:
        session_settings.base_pose_location = bookmark_active.base_pose_location


def xr_pose_bookmark_base_pose_angle_update(self, context):
    session_settings = context.window_manager.xr_session_settings
    bookmark_active = VRPoseBookmark.get_active_bookmark(context)

    if bookmark_active:
        session_settings.base_pose_angle = bookmark_active.base_pose_angle


def xr_pose_bookmark_camera_object_poll(self, object):
    return object.type == 'CAMERA'


def xr_pose_bookmark_active_update(self, context):
    xr_pose_bookmark_type_update(self, context)
    xr_pose_bookmark_camera_update(self, context)


class VRPoseBookmark(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(
        name="VR Pose Bookmark",
        default="VR Pose"
    )
    type: bpy.props.EnumProperty(
        name="Type",
        items=[
            ('SCENE_CAMERA', "Scene Camera",
             "Use scene's currently active camera to define the VR view base pose"),
            ('USER_CAMERA', "Custom Camera",
             "Use an existing camera to define the VR view base pose"),
            ('CUSTOM', "Custom Pose",
             "Allow a manually definied position and rotation to be used as the VR view base pose"),
        ],
        default='SCENE_CAMERA',
        update=xr_pose_bookmark_type_update,
    )
    base_pose_camera: bpy.props.PointerProperty(
        name="Camera",
        type=bpy.types.Object,
        poll=xr_pose_bookmark_camera_object_poll,
        update=xr_pose_bookmark_camera_update,
    )
    base_pose_location: bpy.props.FloatVectorProperty(
        name="Base Pose Location",
        subtype='TRANSLATION',
        update=xr_pose_bookmark_base_pose_location_update,
    )

    base_pose_angle: bpy.props.FloatProperty(
        name="Base Pose Angle",
        subtype='ANGLE',
        update=xr_pose_bookmark_base_pose_angle_update,
    )

    @staticmethod
    def get_active_bookmark(context):
        wm = context.window_manager
        bookmarks = wm.vr_pose_bookmarks

        return None if len(bookmarks) < 1 else bookmarks[wm.vr_pose_bookmarks_active]


class VIEW3D_UL_vr_pose_bookmarks(bpy.types.UIList):
    def draw_item(self, _context, layout, _data, item, icon, _active_data, _active_propname, _index):
        bookmark = item

        layout.emboss = 'NONE'
        layout.prop(bookmark, "name", text="")


class VIEW3D_PT_vr_pose_bookmarks(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VR"
    bl_label = "Pose Bookmarks"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        bookmark_active = VRPoseBookmark.get_active_bookmark(context)

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        row = layout.row()

        row.template_list("VIEW3D_UL_vr_pose_bookmarks", "", wm, "vr_pose_bookmarks",
                          wm, "vr_pose_bookmarks_active", rows=3)

        col = row.column(align=True)
        col.operator("view3d.vr_pose_bookmark_add", icon='ADD', text="")
        col.operator("view3d.vr_pose_bookmark_remove", icon='REMOVE', text="")

        if bookmark_active:
            layout.prop(bookmark_active, "type")

            if bookmark_active.type == 'USER_CAMERA':
                layout.prop(bookmark_active, "base_pose_camera")
            elif bookmark_active.type == 'CUSTOM':
                layout.prop(bookmark_active,
                            "base_pose_location", text="Location")
                layout.prop(bookmark_active,
                            "base_pose_angle", text="Angle")


class VIEW3D_PT_vr_session(bpy.types.Panel):
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

        # Using SNAP_FACE because it looks like a stop icon -- I shouldn't have commit rights...
        toggle_info = ("Start VR Session", 'PLAY') if not is_session_running else (
            "Stop VR Session", 'SNAP_FACE')
        layout.operator("wm.xr_session_toggle",
                        text=toggle_info[0], icon=toggle_info[1])

        layout.separator()

        layout.prop(session_settings, "show_floor", text="Floor")
        layout.prop(session_settings, "show_annotation", text="Annotations")

        layout.separator()

        col = layout.column(align=True)
        col.prop(session_settings, "clip_start", text="Clip Start")
        col.prop(session_settings, "clip_end", text="End")

        layout.separator()

        layout.prop(session_settings, "use_positional_tracking")


class VIEW3D_OT_vr_pose_bookmark_add(bpy.types.Operator):
    bl_idname = "view3d.vr_pose_bookmark_add"
    bl_label = "Add VR Pose Bookmark"
    bl_description = "Add a new VR pose bookmark to the list and select it"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        wm = context.window_manager
        bookmarks = wm.vr_pose_bookmarks

        bookmarks.add()

        # select newly created set
        wm.vr_pose_bookmarks_active = len(bookmarks) - 1

        return {'FINISHED'}


class VIEW3D_OT_vr_pose_bookmark_remove(bpy.types.Operator):
    bl_idname = "view3d.vr_pose_bookmark_remove"
    bl_label = "Remove VR Pose Bookmark"
    bl_description = "Delete the selected VR pose bookmark from the list"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        wm = context.window_manager
        bookmarks = wm.vr_pose_bookmarks
        bookmark_active_idx = wm.vr_pose_bookmarks_active

        bookmarks.remove(bookmark_active_idx)

        return {'FINISHED'}


class VIEW3D_PT_vr_session_shading(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VR"
    bl_label = "Shading"

    def draw(self, context):
        layout = self.layout
        session_settings = context.window_manager.xr_session_settings
        shading = session_settings.shading

        layout.prop(shading, "type", text="")


class VIEW3D_PT_vr_session_shading_lighting(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VR"
    bl_label = VIEW3D_PT_shading_lighting.bl_label
    bl_parent_id = "VIEW3D_PT_vr_session_shading"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        session_settings = context.window_manager.xr_session_settings
        shading = session_settings.shading

        if VIEW3D_PT_shading_lighting.poll_ex(context, shading):
            VIEW3D_PT_shading_lighting.draw_ex(self, context, shading)


class VIEW3D_PT_vr_session_shading_color(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VR"
    bl_label = VIEW3D_PT_shading_color.bl_label
    bl_parent_id = "VIEW3D_PT_vr_session_shading"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        session_settings = context.window_manager.xr_session_settings
        shading = session_settings.shading

        if VIEW3D_PT_shading_color.poll_ex(context, shading):
            VIEW3D_PT_shading_color.draw_ex(self, context, shading)


class VIEW3D_PT_vr_session_shading_options(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VR"
    bl_label = VIEW3D_PT_shading_options.bl_label
    bl_parent_id = "VIEW3D_PT_vr_session_shading"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        session_settings = context.window_manager.xr_session_settings
        shading = session_settings.shading

        if VIEW3D_PT_shading_options.poll_ex(context, shading):
            VIEW3D_PT_shading_options.draw_ex(self, context, shading)


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


class VIEW3D_GGT_vr_viewer(GizmoGroup):
    bl_idname = "VIEW3D_GGT_vr_viewer"
    bl_label = "VR Viewer Indicator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT', 'SCALE', 'CONTINUOUS_REDRAW'}

    @classmethod
    def poll(cls, context):
        return bpy.types.XrSessionState.is_running(context)

    def _get_viewer_matrix(self, context):
        from mathutils import Matrix, Quaternion

        wm = context.window_manager

        loc = wm.xr_session_state.viewer_location
        rot = wm.xr_session_state.viewer_rotation

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
        self.gizmo.matrix_basis = self._get_viewer_matrix(context)


classes = (
    VIEW3D_PT_vr_session,
    VIEW3D_PT_vr_session_shading,
    VIEW3D_PT_vr_session_shading_lighting,
    VIEW3D_PT_vr_session_shading_color,
    VIEW3D_PT_vr_session_shading_options,
    VIEW3D_PT_vr_pose_bookmarks,

    VRPoseBookmark,
    VIEW3D_UL_vr_pose_bookmarks,

    VIEW3D_OT_vr_pose_bookmark_add,
    VIEW3D_OT_vr_pose_bookmark_remove,

    VIEW3D_GT_vr_camera_cone,
    VIEW3D_GGT_vr_viewer,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.WindowManager.vr_pose_bookmarks = CollectionProperty(
        name="Pose Bookmarks",
        type=VRPoseBookmark,
    )
    bpy.types.WindowManager.vr_pose_bookmarks_active = IntProperty(
        update=xr_pose_bookmark_active_update,
    )


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.WindowManager.vr_pose_bookmarks
    del bpy.types.WindowManager.vr_pose_bookmarks_active


if __name__ == "__main__":
    register()
