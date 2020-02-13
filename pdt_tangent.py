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
import bpy
import bmesh
from math import sqrt
from mathutils import Vector
from bpy.types import Operator

from .pdt_functions import (
    oops,
    arc_centre,
)

from .pdt_msg_strings import (
    PDT_OBJ_MODE_ERROR,
    PDT_ERR_NO_ACT_OBJ,
    PDT_ERR_SEL_3_VERTS,
)

from . import pdt_exception
PDT_ObjectModeError = pdt_exception.ObjectModeError
PDT_NoObjectError = pdt_exception.NoObjectError
PDT_SelectionError = pdt_exception.SelectionError


def get_tangent_intersect_outer(xloc_0, yloc_0, xloc_1, yloc_1, radius_0, radius_1):
    xloc_p = ((xloc_1 * radius_0) - (xloc_0 * radius_1)) / (radius_0 - radius_1)
    yloc_p = ((yloc_1 * radius_0) - (yloc_0 * radius_1)) / (radius_0 - radius_1)

    return xloc_p, yloc_p


def get_tangent_intersect_inner(xloc_0, yloc_0, xloc_1, yloc_1, radius_0, radius_1):
    xloc_p = ((xloc_1 * radius_0) + (xloc_0 * radius_1)) / (radius_0 + radius_1)
    yloc_p = ((yloc_1 * radius_0) + (yloc_0 * radius_1)) / (radius_0 + radius_1)

    return xloc_p, yloc_p


def get_tangent_points(xloc_0, yloc_0, radius_0, xloc_p, yloc_p):
    numerator = (radius_0 ** 2 * (xloc_p - xloc_0)) + (
        radius_0
        * (yloc_p - yloc_0)
        * sqrt((xloc_p - xloc_0) ** 2 + (yloc_p - yloc_0) ** 2 - radius_0 ** 2)
    )
    denominator = (xloc_p - xloc_0) ** 2 + (yloc_p - yloc_0) ** 2
    xloc_t1 = round((numerator / denominator) + xloc_0, 5)

    numerator = (radius_0 ** 2 * (xloc_p - xloc_0)) - (
        radius_0
        * (yloc_p - yloc_0)
        * sqrt((xloc_p - xloc_0) ** 2 + (yloc_p - yloc_0) ** 2 - radius_0 ** 2)
    )
    denominator = (xloc_p - xloc_0) ** 2 + (yloc_p - yloc_0) ** 2
    xloc_t2 = round((numerator / denominator) + xloc_0, 5)

    # Get Y values
    numerator = (radius_0 ** 2 * (yloc_p - yloc_0)) - (
        radius_0
        * (xloc_p - xloc_0)
        * sqrt((xloc_p - xloc_0) ** 2 + (yloc_p - yloc_0) ** 2 - radius_0 ** 2)
    )
    denominator = (xloc_p - xloc_0) ** 2 + (yloc_p - yloc_0) ** 2
    yloc_t1 = round((numerator / denominator) + yloc_0, 5)

    numerator = (radius_0 ** 2 * (yloc_p - yloc_0)) + (
        radius_0
        * (xloc_p - xloc_0)
        * sqrt((xloc_p - xloc_0) ** 2 + (yloc_p - yloc_0) ** 2 - radius_0 ** 2)
    )
    denominator = (xloc_p - xloc_0) ** 2 + (yloc_p - yloc_0) ** 2
    yloc_t2 = round((numerator / denominator) + yloc_0, 5)

    return xloc_t1, xloc_t2, yloc_t1, yloc_t2


def draw_tangents(
    xloc_to1, xloc_to2, yloc_to1, yloc_to2, xloc_to3, xloc_to4, yloc_to3, yloc_to4, bm, obj, obj_loc
):
    tangent_vector_o1 = Vector((xloc_to1, 0, yloc_to1))
    tangent_vertex_o1 = bm.verts.new(tangent_vector_o1 - obj_loc)
    tangent_vector_o2 = Vector((xloc_to2, 0, yloc_to2))
    tangent_vertex_o2 = bm.verts.new(tangent_vector_o2 - obj_loc)
    tangent_vector_o3 = Vector((xloc_to3, 0, yloc_to3))
    tangent_vertex_o3 = bm.verts.new(tangent_vector_o3 - obj_loc)
    tangent_vector_o4 = Vector((xloc_to4, 0, yloc_to4))
    tangent_vertex_o4 = bm.verts.new(tangent_vector_o4 - obj_loc)
    # Add Edges
    bm.edges.new([tangent_vertex_o1, tangent_vertex_o3])
    bm.edges.new([tangent_vertex_o2, tangent_vertex_o4])
    bmesh.update_edit_mesh(obj.data)


def analyse_arc(context, pg):
    obj = context.view_layer.objects.active
    if obj is None:
        pg.error = PDT_ERR_NO_ACT_OBJ
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        raise PDT_ObjectModeError
    if obj.mode == "EDIT":
        obj_loc = obj.matrix_world.decompose()[0]
        bm = bmesh.from_edit_mesh(obj.data)
        verts = [v for v in bm.verts if v.select]
        if len(verts) != 3:
            pg.error = f"{PDT_ERR_SEL_3_VERTS} {len(verts)})"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            raise PDT_SelectionError
        vector_a = verts[0].co
        vector_b = verts[1].co
        vector_c = verts[2].co
        vector_delta, radius = arc_centre(vector_a, vector_b, vector_c)

        return vector_delta, radius
        

class PDT_OT_TangentOperate(Operator):
    """Calculate Tangents."""

    bl_idname = "pdt.tangentoperate"
    bl_label = "Calculate Tangents"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Calculate Tangents to Arcs from Points or Other Arcs"

    @classmethod
    def poll(cls, context):
        ob = context.object
        if ob is None:
            return False
        return all([bool(ob), ob.type == "MESH", ob.mode == "EDIT"])

    def execute(self, context):
        scene = context.scene
        pg = scene.pdt_pg
        centre_0 = pg.tangent_point0
        radius_0 = pg.tangent_radius0
        centre_1 = pg.tangent_point1
        radius_1 = pg.tangent_radius1
        centre_2 = pg.tangent_point2
        distance = (centre_0 - centre_1).length
        if distance > radius_0 + radius_1:
            mode = "inner"
        elif distance > radius_0 and distance > radius_1:
            mode = "outer"
        else:
            # Cannot execute, centres are too close.
            print("Execution Error")
            return {"FINISHED"}

        # Get Object
        obj = context.view_layer.objects.active
        if obj is not None:
            if obj.mode not in {"EDIT"} or obj.type != "MESH":
                pg.error = PDT_OBJ_MODE_ERROR
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                raise PDT_ObjectModeError
        else:
            pg.error = PDT_ERR_NO_ACT_OBJ
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            raise PDT_NoObjectError
        bm = bmesh.from_edit_mesh(obj.data)
        obj_loc = obj.matrix_world.decompose()[0]

        if pg.tangent_from_point:
            # FIXME Get Proper Axes Values
            xloc_to1, xloc_to2, yloc_to1, yloc_to2 = get_tangent_points(
                centre_0.x, centre_0.z, radius_0, centre_2.x, centre_2.z
            )
            # Point Tangents
            point_vector_outer = Vector((centre_2.x, 0, centre_2.z))
            point_vertex_outer = bm.verts.new(point_vector_outer - obj_loc)
            tangent_vector_o1 = Vector((xloc_to1, 0, yloc_to1))
            tangent_vertex_o1 = bm.verts.new(tangent_vector_o1 - obj_loc)
            tangent_vector_o2 = Vector((xloc_to2, 0, yloc_to2))
            tangent_vertex_o2 = bm.verts.new(tangent_vector_o2 - obj_loc)
            bm.edges.new([tangent_vertex_o1, point_vertex_outer])
            bm.edges.new([tangent_vertex_o2, point_vertex_outer])
            bmesh.update_edit_mesh(obj.data)
            return {"FINISHED"}

        if mode in {"outer", "inner"}:
            # FIXME Get Proper Axes Values
            xloc_po, yloc_po = get_tangent_intersect_outer(
                centre_0.x, centre_0.z, centre_1.x, centre_1.z, radius_0, radius_1
            )
            # Outer Tangents
            xloc_to1, xloc_to2, yloc_to1, yloc_to2 = get_tangent_points(
                centre_0.x, centre_0.z, radius_0, xloc_po, yloc_po
            )
            xloc_to3, xloc_to4, yloc_to3, yloc_to4 = get_tangent_points(
                centre_1.x, centre_1.z, radius_1, xloc_po, yloc_po
            )

            # Add Outer Tangent Vertices
            draw_tangents(
                xloc_to1,
                xloc_to2,
                yloc_to1,
                yloc_to2,
                xloc_to3,
                xloc_to4,
                yloc_to3,
                yloc_to4,
                bm,
                obj,
                obj_loc,
            )

        if mode == "inner":
            # FIXME Get Proper Axes Values
            xloc_pi, yloc_pi = get_tangent_intersect_inner(
                centre_0.x, centre_0.z, centre_1.x, centre_1.z, radius_0, radius_1
            )
            # Inner Tangents
            xloc_to1, xloc_to2, yloc_to1, yloc_to2 = get_tangent_points(
                centre_0.x, centre_0.z, radius_0, xloc_pi, yloc_pi
            )
            xloc_to3, xloc_to4, yloc_to3, yloc_to4 = get_tangent_points(
                centre_1.x, centre_1.z, radius_1, xloc_pi, yloc_pi
            )
            # Add Inner Tangent Vertices
            draw_tangents(
                xloc_to1,
                xloc_to2,
                yloc_to1,
                yloc_to2,
                xloc_to3,
                xloc_to4,
                yloc_to3,
                yloc_to4,
                bm,
                obj,
                obj_loc,
            )

        return {"FINISHED"}


class PDT_OT_TangentSet1(Operator):
    """Calculates Centres & Radii from 3 Vectors."""

    bl_idname = "pdt.tangentset1"
    bl_label = "Calculate Centres & Radii"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Calculate Centres & Radii from Selected Vertices"

    @classmethod
    def poll(cls, context):
        ob = context.object
        if ob is None:
            return False
        return all([bool(ob), ob.type == "MESH", ob.mode == "EDIT"])

    def execute(self, context):
        scene = context.scene
        pg = scene.pdt_pg
        vector_delta, radius = analyse_arc(context, pg)
        pg.tangent_point0 = vector_delta
        pg.tangent_radius0 = radius
        return {"FINISHED"}


class PDT_OT_TangentSet2(Operator):
    """Calculates Centres & Radii from 3 Vectors."""

    bl_idname = "pdt.tangentset2"
    bl_label = "Calculate Centres & Radii"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Calculate Centres & Radii from Selected Vertices"

    @classmethod
    def poll(cls, context):
        ob = context.object
        if ob is None:
            return False
        return all([bool(ob), ob.type == "MESH", ob.mode == "EDIT"])

    def execute(self, context):
        scene = context.scene
        pg = scene.pdt_pg
        vector_delta, radius = analyse_arc(context, pg)
        pg.tangent_point1 = vector_delta
        pg.tangent_radius1 = radius
        return {"FINISHED"}
