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

# By CoDEmanX

import bpy
from bpy.types import (
        Panel,
        Operator,
        )


class DATA_PT_info_panel(Panel):
    """Creates a face info / select panel in the Object properties window"""
    bl_label = "Face Info / Select"
    bl_idname = "DATA_PT_face_info"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        return (context.active_object is not None and
                context.active_object.type == 'MESH')

    def draw(self, context):
        layout = self.layout

        ob = context.active_object

        info_str = ""
        tris = quads = ngons = 0

        for p in ob.data.polygons:
            count = p.loop_total
            if count == 3:
                tris += 1
            elif count == 4:
                quads += 1
            else:
                ngons += 1

        info_str = "  Ngons: %i  Quads: %i  Tris: %i" % (ngons, quads, tris)

        col = layout.column()
        split = col.split(0.9)

        split.label(info_str, icon='MESH_DATA')
        split.operator("mesh.refresh_info_panel", text="", icon="FILE_REFRESH")

        col = layout.column()
        col.label("Select faces by type:")

        row = layout.row()
        row.operator("data.facetype_select", text="Ngons").face_type = "5"
        row.operator("data.facetype_select", text="Quads").face_type = "4"
        row.operator("data.facetype_select", text="Tris").face_type = "3"


class MESH_OT_refresh_info_panel(Operator):
    bl_idname = "mesh.refresh_info_panel"
    bl_label = "Refresh"
    bl_description = ("Refresh the info panel by switching to Object mode and back\n"
                      "Limitation: the information doesn't account modifiers\n"
                      "Be careful with usage if you need the Redo History in Edit Mode")
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(self, context):
        return (context.active_object is not None and
                context.active_object.type == 'MESH')

    def invoke(self, context, event):
        return self.execute(context)

    def execute(self, context):
        try:
            mode = bpy.context.active_object.mode

            # switch to Object mode and restore selection
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.mode_set(mode=mode)

            return {'FINISHED'}
        except:
            import traceback
            traceback.print_exc()

            self.report({'WARNING'},
                        "The refresh could not be performed (Check the console for more info)")

            return {'CANCELLED'}
