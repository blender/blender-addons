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
from bl_ui.space_view3d import (
    VIEW3D_PT_shading_lighting,
    VIEW3D_PT_shading_color,
    VIEW3D_PT_shading_options,
)

bl_info = {
    "name": "Basic VR Viewer",
    "author": "Julian Eisel (Severin)",
    "version": (0, 0, 1),
    "blender": (2, 81, 0),
    "location": "Window > Toggle VR Session",
    "description": ("View the viewport with virtual reality glasses "
                    "(head-mounted displays)"),
    "support": "OFFICIAL",
    "warning": "This is an early, limited preview of in development "
               "VR support for Blender.",
    "category": "3D View",
}


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
    bl_options = {'3D', 'PERSISTENT', 'SCALE'}

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

    VIEW3D_GT_vr_camera_cone,
    VIEW3D_GGT_vr_viewer,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
