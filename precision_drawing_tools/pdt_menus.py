# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****
#
# -----------------------------------------------------------------------
# Author: Alan Odom (Clockmender), Rune Morling (ermo) Copyright (c) 2019
# -----------------------------------------------------------------------
#
from bpy.types import Panel
from .pdt_msg_strings import (
    PDT_LAB_ABS,
    PDT_LAB_AD2D,
    PDT_LAB_AD3D,
    PDT_LAB_ALLACTIVE,
    PDT_LAB_ANGLEVALUE,
    PDT_LAB_ARCCENTRE,
    PDT_LAB_BISECT,
    PDT_LAB_CVALUE,
    PDT_LAB_DEL,
    PDT_LAB_DIR,
    PDT_LAB_DISVALUE,
    PDT_LAB_EDGETOEFACE,
    PDT_LAB_FILLET,
    PDT_LAB_FLIPANGLE,
    PDT_LAB_FLIPPERCENT,
    PDT_LAB_INTERSECT,
    PDT_LAB_INTERSETALL,
    PDT_LAB_JOIN2VERTS,
    PDT_LAB_MODE,
    PDT_LAB_NOR,
    PDT_LAB_OPERATION,
    PDT_LAB_ORDER,
    PDT_LAB_ORIGINCURSOR,
    PDT_LAB_PERCENT,
    PDT_LAB_PERCENTS,
    PDT_LAB_PIVOTALPHA,
    PDT_LAB_PIVOTLOC,
    PDT_LAB_PIVOTLOCH,
    PDT_LAB_PIVOTSIZE,
    PDT_LAB_PIVOTWIDTH,
    PDT_LAB_PLANE,
    PDT_LAB_PROFILE,
    PDT_LAB_RADIUS,
    PDT_LAB_SEGMENTS,
    PDT_LAB_TAPER,
    PDT_LAB_TAPERAXES,
    PDT_LAB_TOOLS,
    PDT_LAB_USEVERTS,
    PDT_LAB_VARIABLES
)


# PDT Panel menus
#
class PDT_PT_PanelDesign(Panel):
    bl_idname = "PDT_PT_PanelDesign"
    bl_label = "PDT Design"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "PDT"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        pdt_pg = context.scene.pdt_pg
        row = layout.row()
        col = row.column()
        col.prop(pdt_pg, "plane", text=PDT_LAB_PLANE)
        col = row.column()
        col.prop(pdt_pg, "select", text=PDT_LAB_MODE)
        box = layout.box()
        row = box.row()
        row.prop(pdt_pg, "operation", text=PDT_LAB_OPERATION)
        row = box.row()
        col = row.column()
        col.operator("pdt.absolute", icon="EMPTY_AXIS", text=PDT_LAB_ABS)
        col = row.column()
        col.operator("pdt.delta", icon="EMPTY_AXIS", text=PDT_LAB_DEL)
        col = row.column()
        col.operator("pdt.distance", icon="EMPTY_AXIS", text=PDT_LAB_DIR)
        row = box.row()
        col = row.column()
        col.operator("pdt.percent", text=PDT_LAB_PERCENT)
        col = row.column()
        col.operator("pdt.normal", text=PDT_LAB_NOR)
        col = row.column()
        col.operator("pdt.centre", text=PDT_LAB_ARCCENTRE)
        row = box.row()
        col = row.column()
        col.operator("pdt.intersect", text=PDT_LAB_INTERSECT)
        col = row.column()
        col.prop(pdt_pg, "object_search_string", text=PDT_LAB_ORDER)
        row = box.row()
        col = row.column()
        col.prop(pdt_pg, "flip_angle", text=PDT_LAB_FLIPANGLE)
        col = row.column()
        col.prop(pdt_pg, "flip_percent", text=PDT_LAB_FLIPPERCENT)
        col = row.column()
        col.prop(pdt_pg, "extend", text=PDT_LAB_ALLACTIVE)
        box = layout.box()
        row = box.row()
        row.label(text=PDT_LAB_VARIABLES)
        row = box.row()
        row.prop(pdt_pg, "cartesian_coords", text=PDT_LAB_CVALUE)
        row = box.row()
        col = row.column()
        col.prop(pdt_pg, "distance", text=PDT_LAB_DISVALUE)
        col = row.column()
        col.prop(pdt_pg, "angle", text=PDT_LAB_ANGLEVALUE)
        col = row.column()
        col.prop(pdt_pg, "percent", text=PDT_LAB_PERCENTS)
        box = layout.box()
        row = box.row()
        row.label(text=PDT_LAB_TOOLS)
        row = box.row()
        col = row.column()
        col.operator("pdt.angle2", text=PDT_LAB_AD2D)
        col = row.column()
        col.operator("pdt.angle3", text=PDT_LAB_AD3D)
        row = box.row()
        col = row.column()
        col.operator("pdt.join", text=PDT_LAB_JOIN2VERTS)
        col = row.column()
        col.operator("pdt.origin", text=PDT_LAB_ORIGINCURSOR)
        row = box.row()
        col = row.column()
        col.prop(pdt_pg, "taper", text=PDT_LAB_TAPERAXES)
        col = row.column()
        col.operator("pdt.taper", text=PDT_LAB_TAPER)
        # New for 1.1.5
        row = box.row()
        col = row.column()
        col.operator("pdt.intersectall", text=PDT_LAB_INTERSETALL)
        col = row.column()
        col.operator("pdt.linetobisect", text=PDT_LAB_BISECT)
        col = row.column()
        col.operator("pdt.edge_to_face", text=PDT_LAB_EDGETOEFACE)
        #
        # Add Fillet Tool
        row = box.row()
        col = row.column()
        col.operator("pdt.fillet", text=PDT_LAB_FILLET)
        col = row.column()
        col.prop(pdt_pg, "fillet_segments", text=PDT_LAB_SEGMENTS)
        col = row.column()
        col.prop(pdt_pg, "fillet_vertices_only", text=PDT_LAB_USEVERTS)
        row = box.row()
        col = row.column()
        col.prop(pdt_pg, "fillet_radius", text=PDT_LAB_RADIUS)
        col = row.column()
        col.prop(pdt_pg, "fillet_profile", text=PDT_LAB_PROFILE)


class PDT_PT_PanelPivotPoint(Panel):
    bl_idname = "PDT_PT_PanelPivotPoint"
    bl_label = "PDT Pivot Point"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "PDT"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        pdt_pg = context.scene.pdt_pg
        layout = self.layout
        row = layout.row()
        split = row.split(factor=0.4, align=True)
        if context.window_manager.pdt_run_opengl is False:
            icon = "PLAY"
            txt = "Show"
        else:
            icon = "PAUSE"
            txt = "Hide"
        split.operator("pdt.modaldraw", icon=icon, text=txt)
        split.prop(pdt_pg, "pivot_size", text=PDT_LAB_PIVOTSIZE)
        split.prop(pdt_pg, "pivot_width", text=PDT_LAB_PIVOTWIDTH)
        split.prop(pdt_pg, "pivot_alpha", text=PDT_LAB_PIVOTALPHA)
        row = layout.row()
        row.label(text=PDT_LAB_PIVOTLOCH)
        row = layout.row()
        row.prop(pdt_pg, "pivot_loc", text=PDT_LAB_PIVOTLOC)
        row = layout.row()
        col = row.column()
        col.operator("pdt.pivotselected", icon="EMPTY_AXIS", text="Selection")
        col = row.column()
        col.operator("pdt.pivotcursor", icon="EMPTY_AXIS", text="Cursor")
        col = row.column()
        col.operator("pdt.pivotorigin", icon="EMPTY_AXIS", text="Origin")
        row = layout.row()
        col = row.column()
        col.operator("pdt.viewplanerot", icon="EMPTY_AXIS", text="Rotate")
        col = row.column()
        col.prop(pdt_pg, "pivot_ang", text="Angle")
        row = layout.row()
        col = row.column()
        col.operator("pdt.viewscale", icon="EMPTY_AXIS", text="Scale")
        col = row.column()
        col.operator("pdt.cursorpivot", icon="EMPTY_AXIS", text="Cursor To Pivot")
        row = layout.row()
        col = row.column()
        col.prop(pdt_pg, "pivot_dis", text="Scale Distance")
        col = row.column()
        col.prop(pdt_pg, "distance", text="System Distance")
        row = layout.row()
        row.label(text="Pivot Point Scale Factors")
        row = layout.row()
        row.prop(pdt_pg, "pivot_scale", text="")
        row = layout.row()
        col = row.column()
        col.operator("pdt.pivotwrite", icon="FILE_TICK", text="PP Write")
        col = row.column()
        col.operator("pdt.pivotread", icon="FILE", text="PP Read")


class PDT_PT_PanelPartsLibrary(Panel):
    bl_idname = "PDT_PT_PanelPartsLibrary"
    bl_label = "PDT Parts Library"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "PDT"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        pdt_pg = context.scene.pdt_pg
        row = layout.row()
        col = row.column()
        col.operator("pdt.append", text="Append")
        col = row.column()
        col.operator("pdt.link", text="Link")
        col = row.column()
        col.prop(pdt_pg, "lib_mode", text="")
        box = layout.box()
        row = box.row()
        col = row.column()
        col.label(text="Objects")
        col = row.column()
        col.prop(pdt_pg, "object_search_string")
        row = box.row()
        row.prop(pdt_pg, "lib_objects", text="")
        box = layout.box()
        row = box.row()
        col = row.column()
        col.label(text="Collections")
        col = row.column()
        col.prop(pdt_pg, "collection_search_string")
        row = box.row()
        row.prop(pdt_pg, "lib_collections", text="")
        box = layout.box()
        row = box.row()
        col = row.column()
        col.label(text="Materials")
        col = row.column()
        col.prop(pdt_pg, "material_search_string")
        row = box.row()
        row.prop(pdt_pg, "lib_materials", text="")
        row = box.row()
        row.operator("pdt.lib_show", text="Show Library File", icon='INFO')


class PDT_PT_PanelViewControl(Panel):
    bl_idname = "PDT_PT_PanelViewControl"
    bl_label = "PDT View Control"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "PDT"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        pdt_pg = context.scene.pdt_pg
        box = layout.box()
        row = box.row()
        col = row.column()
        col.label(text="View Rotation")
        col = row.column()
        col.operator("pdt.viewrot", text="Rotate Abs")
        row = box.row()
        row.prop(pdt_pg, "rotation_coords", text="Rotation")
        row = box.row()
        col = row.column()
        col.prop(pdt_pg, "vrotangle", text="Angle")
        col = row.column()
        col.operator("pdt.viewleft", text="", icon="TRIA_LEFT")
        col = row.column()
        col.operator("pdt.viewright", text="", icon="TRIA_RIGHT")
        col = row.column()
        col.operator("pdt.viewup", text="", icon="TRIA_UP")
        col = row.column()
        col.operator("pdt.viewdown", text="", icon="TRIA_DOWN")
        col = row.column()
        col.operator("pdt.viewroll", text="", icon="RECOVER_LAST")
        row = box.row()
        row.operator("pdt.viewiso", text="Isometric View")


class PDT_PT_PanelCommandLine(Panel):
    bl_idname = "PDT_PT_PanelCommandLine"
    bl_label = "PDT Command Line (? for help)"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "PDT"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        pdt_pg = context.scene.pdt_pg
        row = layout.row()
        col = row.column()
        col.prop(pdt_pg, "plane", text="Plane")
        col = row.column()
        col.prop(pdt_pg, "select", text="Mode")
        row = layout.row()
        row.label(text="Comand Line, uses Plane & Mode Options")
        row = layout.row()
        row.prop(pdt_pg, "command", text="")
