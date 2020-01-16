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
import math
from math import sqrt, tan, pi
import numpy as np
from mathutils import Vector
from mathutils.geometry import intersect_point_line
from .pdt_functions import (
    set_mode,
    oops,
    get_percent,
    dis_ang,
    check_selection,
    arc_centre,
    intersection,
    view_coords_i,
    view_coords,
    view_dir,
    set_axis,
)
from .pdt_msg_strings import (
    PDT_ERR_BAD3VALS,
    PDT_ERR_BAD2VALS,
    PDT_ERR_BAD1VALS,
    PDT_ERR_CONNECTED,
    PDT_ERR_SEL_2_VERTS,
    PDT_ERR_EDOB_MODE,
    PDT_ERR_NO_ACT_OBJ,
    PDT_ERR_VERT_MODE,
    PDT_ERR_SEL_3_VERTS,
    PDT_ERR_SEL_3_OBJS,
    PDT_ERR_EDIT_MODE,
    PDT_ERR_NON_VALID,
    PDT_LAB_NOR,
    PDT_ERR_STRIGHT_LINE,
    PDT_LAB_ARCCENTRE,
    PDT_ERR_SEL_4_VERTS,
    PDT_ERR_INT_NO_ALL,
    PDT_LAB_INTERSECT,
    PDT_ERR_SEL_4_OBJS,
    PDT_INF_OBJ_MOVED,
    PDT_ERR_SEL_2_VERTIO,
    PDT_ERR_SEL_2_OBJS,
    PDT_ERR_SEL_3_VERTIO,
    PDT_ERR_TAPER_ANG,
    PDT_ERR_TAPER_SEL,
)


def command_maths(self, context, pg, expression, output_target):
    if output_target not in {"x", "y", "z", "d", "a", "p", "o"}:
        pg.error = f"{mode} {PDT_ERR_NON_VALID} Maths)"
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return
    namespace = {}
    namespace.update(vars(math))
    try:
        maths_result = eval(expression, namespace, namespace)
    except ValueError:
        pg.error = PDT_ERR_BADMATHS
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return
    if output_target == "x":
        pg.cartesian_coords.x = maths_result
    elif output_target == "y":
        pg.cartesian_coords.y = maths_result
    elif output_target == "z":
        pg.cartesian_coords.z = maths_result
    elif output_target == "d":
        pg.distance = maths_result
    elif output_target == "a":
        pg.angle = maths_result
    elif output_target == "p":
        pg.percent = maths_result
    elif output_target == "o":
        pg.maths_output = maths_result
    return

def vector_build(self, context, pg, obj, operation, values, num_values):
    """Build Movement Vector from input Fields.

    Args:
        context: Blender bpy.context instance.
        PDT parameter group as pg, object, operation,
        command line values, required number of values.

    Returns:
        Vector to position, or offset items.
    """

    scene = context.scene
    plane = pg.plane
    flip_a = pg.flip_angle
    flip_p = pg.flip_percent

    if num_values == 3:
        if len(values) != 3:
            pg.error = PDT_ERR_BAD3VALS
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return None
        return Vector((float(values[0]), float(values[1]), float(values[2])))
    elif num_values == 2:
        if len(values) != 2:
            pg.error = PDT_ERR_BAD2VALS
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        return dis_ang(values, flip_a, plane, scene)
    elif num_values == 1:
        if len(values) != 1:
            pg.error = PDT_ERR_BAD1VALS
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        return get_percent(obj, flip_p, float(values[0]), operation, scene)


def move_cursor_pivot(self, context, pg, obj, sel_verts, operation,
        mode_op, vector_delta):
    """Move Cursor or Pivot Point.

    Args:
        context: Blender bpy.context instance.
        PDT parameter group as pg, active object, selected vertices,
        operation, operational mode as mode_op, movement vector.

    Returns:
        Nothing.
    """
    scene = context.scene
    mode_sel = pg.select
    obj_loc = obj.matrix_world.decompose()[0]

    if mode_op == "a":
        if operation == "C":
            scene.cursor.location = vector_delta
        elif operation == "P":
            pg.pivot_loc = vector_delta
    elif mode_op in {"d","i"}:
        if mode_sel == "REL":
            if operation == "C":
                scene.cursor.location = scene.cursor.location + vector_delta
            else:
                pg.pivot_loc = pg.pivot_loc + vector_delta
        elif mode_sel == "SEL":
            if obj.mode == "EDIT":
                if operation == "C":
                    scene.cursor.location = (
                        sel_verts[-1].co + obj_loc + vector_delta
                    )
                else:
                    pg.pivot_loc = verts[-1].co + obj_loc + vector_delta
            elif obj.mode == "OBJECT":
                if operation == "C":
                    scene.cursor.location = obj_loc + vector_delta
                else:
                    pg.pivot_loc = obj_loc + vector_delta
    elif mode_op == "p":
        if obj.mode == "EDIT":
            if operation == "C":
                scene.cursor.location = obj_loc + vector_delta
            else:
                pg.pivot_loc = obj_loc + vector_delta
        elif obj.mode == "OBJECT":
            if operation == "C":
                scene.cursor.location = vector_delta
            else:
                pg.pivot_loc = vector_delta
    return


def placement_normal(self, context, operation):
    """Manipulates Geometry, or Objects by Normal Intersection between 3 points.

    -- set position of CUrsor       (CU)
    -- set position of Pivot Point  (PP)
    -- MoVe geometry/objects        (MV)
    -- Extrude Vertices             (EV)
    -- Split Edges                  (SE)
    -- add a New Vertex             (NV)

    Invalid Options result in "oops" Error.

    Local vector variable 'vector_delta' used to reposition features.

    Args:
        context: Blender bpy.context instance.

    Returns:
        Status Set.
    """

    scene = context.scene
    pg = scene.pdt_pg
    ext_a = pg.extend
    obj = context.view_layer.objects.active
    if obj is None:
        pg.error = PDT_ERR_NO_ACT_OBJ
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return
    obj_loc = obj.matrix_world.decompose()[0]
    if obj.mode == "EDIT":
        bm = bmesh.from_edit_mesh(obj.data)
        if len(bm.select_history) == 3:
            actV, othV, lstV = check_selection(3, bm, obj)
            if actV is None:
                pg.error = PDT_ERR_VERT_MODE
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
        else:
            pg.error = f"{PDT_ERR_SEL_3_VERTS} {len(bm.select_history)})"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
    elif obj.mode == "OBJECT":
        objs = context.view_layer.objects.selected
        if len(objs) != 3:
            pg.error = f"{PDT_ERR_SEL_3_OBJS} {len(objs)})"
            scontext.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        else:
            objs_s = [ob for ob in objs if ob.name != obj.name]
            actV = obj.matrix_world.decompose()[0]
            othV = objs_s[-1].matrix_world.decompose()[0]
            lstV = objs_s[-2].matrix_world.decompose()[0]
    vector_delta = intersect_point_line(actV, othV, lstV)[0]
    if operation == "C":
        if obj.mode == "EDIT":
            scene.cursor.location = obj_loc + vector_delta
        elif obj.mode == "OBJECT":
            scene.cursor.location = vector_delta
    elif operation.upper == "P":
        if obj.mode == "EDIT":
            pg.pivot_loc = obj_loc + vector_delta
        elif obj.mode == "OBJECT":
            pg.pivot_loc = vector_delta
    elif operation == "G":
        if obj.mode == "EDIT":
            if ext_a:
                for v in [v for v in bm.verts if v.select]:
                    v.co = vector_delta
                bm.select_history.clear()
                bmesh.ops.remove_doubles(
                    bm, verts=[v for v in bm.verts if v.select], dist=0.0001
                )
            else:
                bm.select_history[-1].co = vector_delta
                bm.select_history.clear()
            bmesh.update_edit_mesh(obj.data)
        elif obj.mode == "OBJECT":
            context.view_layer.objects.active.location = vector_delta
    elif operation == "N":
        if obj.mode == "EDIT":
            nVert = bm.verts.new(vector_delta)
            bmesh.update_edit_mesh(obj.data)
            bm.select_history.clear()
            for v in [v for v in bm.verts if v.select]:
                v.select_set(False)
            nVert.select_set(True)
        else:
            pg.error = f"{PDT_ERR_EDIT_MODE} {obj.mode})"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
    elif operation == "V" and obj.mode == "EDIT":
        vNew = vector_delta
        nVert = bm.verts.new(vNew)
        if ext_a:
            for v in [v for v in bm.verts if v.select]:
                bm.edges.new([v, nVert])
        else:
            bm.edges.new([bm.select_history[-1], nVert])
        for v in [v for v in bm.verts if v.select]:
            v.select_set(False)
        nVert.select_set(True)
        bmesh.update_edit_mesh(obj.data)
        bm.select_history.clear()
    else:
        pg.error = f"{operation} {PDT_ERR_NON_VALID} {PDT_LAB_NOR}"
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
    return

def placement_centre(self, context, operation):
    """Manipulates Geometry, or Objects to an Arc Centre defined by 3 points on an Imaginary Arc.

    -- set position of CUrsor       (CU)
    -- set position of Pivot Point  (PP)
    -- MoVe geometry/objects        (MV)
    -- Extrude Vertices             (EV)
    -- add a New vertex             (NV)

    Invalid Options result in self.report Error.

    Local vector variable 'vector_delta' used to reposition features.

    Args:
        context: Blender bpy.context instance.

    Returns:
        Status Set.
    """

    scene = context.scene
    pg = scene.pdt_pg
    ext_a = pg.extend
    obj = context.view_layer.objects.active

    if obj is None:
        pg.error = PDT_ERR_NO_ACT_OBJ
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return
    if obj.mode == "EDIT":
        obj = context.view_layer.objects.active
        obj_loc = obj.matrix_world.decompose()[0]
        bm = bmesh.from_edit_mesh(obj.data)
        verts = [v for v in bm.verts if v.select]
        if len(verts) == 3:
            actV = verts[0].co
            othV = verts[1].co
            lstV = verts[2].co
        else:
            pg.error = f"{PDT_ERR_SEL_3_VERTS} {len(verts)})"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        vector_delta, radius = arc_centre(actV, othV, lstV)
        if str(radius) == "inf":
            pg.error = PDT_ERR_STRIGHT_LINE
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        pg.distance = radius
        if operation == "C":
            scene.cursor.location = obj_loc + vector_delta
        elif operation == "P":
            pg.pivot_loc = obj_loc + vector_delta
        elif operation == "N":
            vNew = vector_delta
            nVert = bm.verts.new(vNew)
            for v in [v for v in bm.verts if v.select]:
                v.select_set(False)
            nVert.select_set(True)
            bmesh.update_edit_mesh(obj.data)
            bm.select_history.clear()
            nVert.select_set(True)
        elif operation == "G":
            if obj.mode == "EDIT":
                if ext_a:
                    for v in [v for v in bm.verts if v.select]:
                        v.co = vector_delta
                    bm.select_history.clear()
                    bmesh.ops.remove_doubles(
                        bm, verts=[v for v in bm.verts if v.select], dist=0.0001
                    )
                else:
                    bm.select_history[-1].co = vector_delta
                    bm.select_history.clear()
                bmesh.update_edit_mesh(obj.data)
            elif obj.mode == "OBJECT":
                context.view_layer.objects.active.location = vector_delta
        elif operation == "V":
            nVert = bm.verts.new(vector_delta)
            if ext_a:
                for v in [v for v in bm.verts if v.select]:
                    bm.edges.new([v, nVert])
                    v.select_set(False)
                nVert.select_set(True)
                bm.select_history.clear()
                bmesh.ops.remove_doubles(
                    bm, verts=[v for v in bm.verts if v.select], dist=0.0001
                )
                bmesh.update_edit_mesh(obj.data)
            else:
                bm.edges.new([bm.select_history[-1], nVert])
                bmesh.update_edit_mesh(obj.data)
                bm.select_history.clear()
        else:
            pg.error = f"{operation} {PDT_ERR_NON_VALID} {PDT_LAB_ARCCENTRE}"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return
    elif obj.mode == "OBJECT":
        if len(context.view_layer.objects.selected) != 3:
            pg.error = f"{PDT_ERR_SEL_3_OBJS} {len(context.view_layer.objects.selected)})"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        else:
            actV = context.view_layer.objects.selected[0].matrix_world.decompose()[0]
            othV = context.view_layer.objects.selected[1].matrix_world.decompose()[0]
            lstV = context.view_layer.objects.selected[2].matrix_world.decompose()[0]
            vector_delta, radius = arc_centre(actV, othV, lstV)
            pg.distance = radius
            if operation == "C":
                scene.cursor.location = vector_delta
            elif operation == "P":
                pg.pivot_loc = vector_delta
            elif operation == "G":
                context.view_layer.objects.active.location = vector_delta
            else:
                pg.error = f"{operation} {PDT_ERR_NON_VALID} {PDT_LAB_ARCCENTRE}"
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return


def placement_intersect(self, context, operation):
    """Manipulates Geometry, or Objects by Convergance Intersection between 4 points, or 2 Edges.

    - Reads pg.plane scene variable and operates in Working Plane to:
    -- set position of CUrsor       (CU)
    -- set position of Pivot Point  (PP)
    -- MoVe geometry/objects        (MV)
    -- Extrude Vertices             (EV)
    -- add a New vertex             (NV)

    Invalid Options result in "oops" Error.

    Local vector variable 'vector_delta' used to reposition features.

    Args:
        context: Blender bpy.context instance.

    Returns:
        Status Set.
    """

    scene = context.scene
    pg = scene.pdt_pg
    plane = pg.plane
    obj = context.view_layer.objects.active
    if obj is None:
        pg.error = PDT_ERR_NO_ACT_OBJ
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return
    if obj.mode == "EDIT":
        obj_loc = obj.matrix_world.decompose()[0]
        bm = bmesh.from_edit_mesh(obj.data)
        edges = [e for e in bm.edges if e.select]
        if len(bm.select_history) == 4:
            ext_a = pg.extend
            v_active = bm.select_history[-1]
            v_other = bm.select_history[-2]
            v_last = bm.select_history[-3]
            v_first = bm.select_history[-4]
            actV, othV, lstV, fstV = check_selection(4, bm, obj)
            if actV is None:
                pg.error = PDT_ERR_VERT_MODE
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
        elif len(edges) == 2:
            ext_a = pg.extend
            v_active = edges[0].verts[0]
            v_other = edges[0].verts[1]
            v_last = edges[1].verts[0]
            v_first = edges[1].verts[1]
        else:
            pg.error = (
                PDT_ERR_SEL_4_VERTS
                + str(len(bm.select_history))
                + " Vertices/"
                + str(len(edges))
                + " Edges)"
            )
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        vector_delta, done = intersection(v_active.co,
            v_other.co,
            v_last.co,
            v_first.co,
            plane
            )
        if not done:
            pg.error = f"{PDT_ERR_INT_LINES} {plane}  {PDT_LAB_PLANE}"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return

        if operation == "C":
            scene.cursor.location = obj_loc + vector_delta
        elif operation == "P":
            pg.pivot_loc = obj_loc + vector_delta
        elif operation == "N":
            vNew = vector_delta
            nVert = bm.verts.new(vNew)
            for v in [v for v in bm.verts if v.select]:
                v.select_set(False)
            for f in bm.faces:
                f.select_set(False)
            for e in bm.edges:
                e.select_set(False)
            nVert.select_set(True)
            bmesh.update_edit_mesh(obj.data)
            bm.select_history.clear()
        elif operation in {"G", "V"}:
            nVert = None
            proc = False

            if (v_active.co - vector_delta).length < (v_other.co - vector_delta).length:
                if operation == "G":
                    v_active.co = vector_delta
                    proc = True
                elif operation == "V":
                    nVert = bm.verts.new(vector_delta)
                    bm.edges.new([va, nVert])
                    proc = True
            else:
                if operation == "G" and ext_a:
                    v_other.co = vector_delta
                elif operation == "V" and ext_a:
                    nVert = bm.verts.new(vector_delta)
                    bm.edges.new([vo, nVert])

            if (v_last.co - vector_delta).length < (v_first.co - vector_delta).length:
                if operation == "G" and ext_a:
                    v_last.co = vector_delta
                elif operation == "V" and ext_a:
                    bm.edges.new([vl, nVert])
            else:
                if operation == "G" and ext_a:
                    v_first.co = vector_delta
                elif operation == "V" and ext_a:
                    bm.edges.new([vf, nVert])
            bm.select_history.clear()
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)

            if not proc and not ext_a:
                pg.error = PDT_ERR_INT_NO_ALL
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                bmesh.update_edit_mesh(obj.data)
                return
            else:
                for v in bm.verts:
                    v.select_set(False)
                for f in bm.faces:
                    f.select_set(False)
                for e in bm.edges:
                    e.select_set(False)

                if nVert is not None:
                    nVert.select_set(True)
                for v in bm.select_history:
                    if v is not None:
                        v.select_set(True)
                bmesh.update_edit_mesh(obj.data)
        else:
            pg.error = f"{operation} {PDT_ERR_NON_VALID} {PDT_LAB_INTERSECT}"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return
    elif obj.mode == "OBJECT":
        if len(context.view_layer.objects.selected) != 4:
            pg.error = f"{PDT_ERR_SEL_4_OBJS} {len(context.view_layer.objects.selected)})"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        else:
            order = pg.object_order.split(",")
            objs = sorted(
                [ob for ob in context.view_layer.objects.selected], key=lambda x: x.name
            )
            message = (
                "Original Object Order was: "
                + objs[0].name
                + ", "
                + objs[1].name
                + ", "
                + objs[2].name
                + ", "
                + objs[3].name
            )
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")

            actV = objs[int(order[0]) - 1].matrix_world.decompose()[0]
            othV = objs[int(order[1]) - 1].matrix_world.decompose()[0]
            lstV = objs[int(order[2]) - 1].matrix_world.decompose()[0]
            fstV = objs[int(order[3]) - 1].matrix_world.decompose()[0]
        vector_delta, done = intersection(actV, othV, lstV, fstV, plane)
        if not done:
            pg.error = f"{PDT_ERR_INT_LINES} {plane}  {PDT_LAB_PLANE}"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        if operation == "CU":
            scene.cursor.location = vector_delta
        elif operation == "PP":
            pg.pivot_loc = vector_delta
        elif operation == "MV":
            context.view_layer.objects.active.location = vector_delta
            pg.error = PDT_INF_OBJ_MOVED + message
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        else:
            pg.error = f"{operation} {PDT_ERR_NON_VALID} {PDT_LAB_INTERSECT}"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return


def join_two_vertices(self, context):
    """Joins 2 Free Vertices that do not form part of a Face.

    Joins two vertices that do not form part of a single face
    It is designed to close open Edge Loops, where a face is not required
    or to join two disconnected Edges.

    Args:
        context: Blender bpy.context instance.

    Returns:
        Status Set.
    """

    scene = context.scene
    pg = scene.pdt_pg
    obj = context.view_layer.objects.active
    if all([bool(obj), obj.type == "MESH", obj.mode == "EDIT"]):
        bm = bmesh.from_edit_mesh(obj.data)
        verts = [v for v in bm.verts if v.select]
        if len(verts) == 2:
            try:
                bm.edges.new([verts[-1], verts[-2]])
                bmesh.update_edit_mesh(obj.data)
                bm.select_history.clear()
                return
            except ValueError:
                pg.error = PDT_ERR_CONNECTED
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
        else:
            pg.error = f"{PDT_ERR_SEL_2_VERTS} {len(verts)})"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
    else:
        pg.error = f"{PDT_ERR_EDOB_MODE},{obj.mode})"
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return

def set_angle_distance_two(self, context):
    """Measures Angle and Offsets between 2 Points in View Plane.

    Uses 2 Selected Vertices to set pg.angle and pg.distance scene variables
    also sets delta offset from these 2 points using standard Numpy Routines
    Works in Edit and Oject Modes.

    Args:
        context: Blender bpy.context instance.

    Returns:
        Status Set.
    """

    scene = context.scene
    pg = scene.pdt_pg
    plane = pg.plane
    flip_a = pg.flip_angle
    obj = context.view_layer.objects.active
    if obj is None:
        pg.error = PDT_ERR_NO_ACT_OBJ
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return
    if obj.mode == "EDIT":
        bm = bmesh.from_edit_mesh(obj.data)
        verts = [v for v in bm.verts if v.select]
        if len(verts) == 2:
            if len(bm.select_history) == 2:
                actV, othV = check_selection(2, bm, obj)
                if actV is None:
                    errmsg = PDT_ERR_VERT_MODE
                    self.report({"ERROR"}, errmsg)
                    return {"FINISHED"}
            else:
                pg.error = f"{PDT_ERR_SEL_2_VERTIO} {len(bm.select_history)})"
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
        else:
            pg.error = f"{PDT_ERR_SEL_2_VERTIO} {len(verts)})"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
    elif obj.mode == "OBJECT":
        objs = context.view_layer.objects.selected
        if len(objs) < 2:
            pg.error = f"{PDT_ERR_SEL_2_OBJS} {len(objs)})"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        objs_s = [ob for ob in objs if ob.name != obj.name]
        actV = obj.matrix_world.decompose()[0]
        othV = objs_s[-1].matrix_world.decompose()[0]
    if plane == "LO":
        disV = othV - actV
        othV = view_coords_i(disV.x, disV.y, disV.z)
        actV = Vector((0, 0, 0))
        v0 = np.array([actV.x + 1, actV.y]) - np.array([actV.x, actV.y])
        v1 = np.array([othV.x, othV.y]) - np.array([actV.x, actV.y])
    else:
        a1, a2, _ = set_mode(plane)
        v0 = np.array([actV[a1] + 1, actV[a2]]) - np.array([actV[a1], actV[a2]])
        v1 = np.array([othV[a1], othV[a2]]) - np.array([actV[a1], actV[a2]])
    ang = np.rad2deg(np.arctan2(np.linalg.det([v0, v1]), np.dot(v0, v1)))
    if flip_a:
        if ang > 0:
            pg.angle = ang - 180
        else:
            pg.angle = ang + 180
    else:
        pg.angle = ang
    if plane == "LO":
        pg.distance = sqrt((actV.x - othV.x) ** 2 + (actV.y - othV.y) ** 2)
    else:
        pg.distance = sqrt((actV[a1] - othV[a1]) ** 2 + (actV[a2] - othV[a2]) ** 2)
    pg.cartesian_coords = othV - actV
    return


def set_angle_distance_three(self, context):
    """Measures Angle and Offsets between 3 Points in World Space, Also sets Deltas.

    Uses 3 Selected Vertices to set pg.angle and pg.distance scene variables
    also sets delta offset from these 3 points using standard Numpy Routines
    Works in Edit and Oject Modes.

    Args:
        context: Blender bpy.context instance.

    Returns:
        Status Set.
    """

    pg = context.scene.pdt_pg
    flip_a = pg.flip_angle
    obj = context.view_layer.objects.active
    if obj is None:
        pg.error = PDT_ERR_NO_ACT_OBJ
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return
    if obj.mode == "EDIT":
        bm = bmesh.from_edit_mesh(obj.data)
        verts = [v for v in bm.verts if v.select]
        if len(verts) == 3:
            if len(bm.select_history) == 3:
                actV, othV, lstV = check_selection(3, bm, obj)
                if actV is None:
                    pg.error = PDT_ERR_VERT_MODE
                    context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                    return
            else:
                pg.error = f"{PDT_ERR_SEL_3_VERTIO} {len(bm.select_history)})"
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
        else:
            pg.error = f"{PDT_ERR_SEL_3_VERTIO} {len(verts)})"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
    elif obj.mode == "OBJECT":
        objs = context.view_layer.objects.selected
        if len(objs) < 3:
            pg.error = PDT_ERR_SEL_3_OBJS + str(len(objs))
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        objs_s = [ob for ob in objs if ob.name != obj.name]
        actV = obj.matrix_world.decompose()[0]
        othV = objs_s[-1].matrix_world.decompose()[0]
        lstV = objs_s[-2].matrix_world.decompose()[0]
    ba = np.array([othV.x, othV.y, othV.z]) - np.array([actV.x, actV.y, actV.z])
    bc = np.array([lstV.x, lstV.y, lstV.z]) - np.array([actV.x, actV.y, actV.z])
    cosA = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    ang = np.degrees(np.arccos(cosA))
    if flip_a:
        if ang > 0:
            pg.angle = ang - 180
        else:
            pg.angle = ang + 180
    else:
        pg.angle = ang
    pg.distance = (actV - othV).length
    pg.cartesian_coords = othV - actV
    return


def origin_to_cursor(self, context):
    """Sets Object Origin in Edit Mode to Cursor Location.

    Keeps geometry static in World Space whilst moving Object Origin
    Requires cursor location
    Works in Edit and Object Modes.

    Args:
        context: Blender bpy.context instance.

    Returns:
        Status Set.
    """

    scene = context.scene
    obj = context.view_layer.objects.active
    if obj is None:
        pg.error = PDT_ERR_NO_ACT_OBJ
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return
    obj_loc = obj.matrix_world.decompose()[0]
    cur_loc = scene.cursor.location
    diff_v = obj_loc - cur_loc
    if obj.mode == "EDIT":
        bm = bmesh.from_edit_mesh(obj.data)
        for v in bm.verts:
            v.co = v.co + diff_v
        obj.location = cur_loc
        bmesh.update_edit_mesh(obj.data)
        bm.select_history.clear()
    elif obj.mode == "OBJECT":
        for v in obj.data.vertices:
            v.co = v.co + diff_v
        obj.location = cur_loc
    else:
        pg.error = f"{PDT_ERR_EDOB_MODE} {obj.mode})"
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return
    return

def taper(self, context):
    """Taper Geometry along World Axes.

    Similar to Shear command except that it shears by angle rather than displacement.
    Rotates about World Axes and displaces along World Axes, angle must not exceed +-80 degrees.
    Rotation axis is centred on Active Vertex.
    Works only in Edit mode.

    Args:
        context: Blender bpy.context instance.

    Note:
        Uses pg.taper & pg.angle scene variables

    Returns:
        Status Set.
    """

    scene = context.scene
    pg = scene.pdt_pg
    tap_ax = pg.taper
    ang_v = pg.angle
    obj = context.view_layer.objects.active
    if all([bool(obj), obj.type == "MESH", obj.mode == "EDIT"]):
        if ang_v > 80 or ang_v < -80:
            errmsg = f"{PDT_ERR_TAPER_ANG} {ang_v})"
            self.report({"ERROR"}, errmsg)
            return {"FINISHED"}
        if obj is None:
            pg.error = PDT_ERR_NO_ACT_OBJ
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        _, a2, a3 = set_axis(tap_ax)
        bm = bmesh.from_edit_mesh(obj.data)
        if len(bm.select_history) >= 1:
            rotV = bm.select_history[-1]
            viewV = view_coords(rotV.co.x, rotV.co.y, rotV.co.z)
        else:
            pg.error = f"{PDT_ERR_TAPER_SEL} {len(bm.select_history)})"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        for v in [v for v in bm.verts if v.select]:
            if pg.plane == "LO":
                v_loc = view_coords(v.co.x, v.co.y, v.co.z)
                dis_v = sqrt((viewV.x - v_loc.x) ** 2 + (viewV.y - v_loc.y) ** 2)
                x_loc = dis_v * tan(ang_v * pi / 180)
                vm = view_dir(x_loc, 0)
                v.co = v.co - vm
            else:
                dis_v = sqrt((rotV.co[a3] - v.co[a3]) ** 2 + (rotV.co[a2] - v.co[a2]) ** 2)
                v.co[a2] = v.co[a2] - (dis_v * tan(ang_v * pi / 180))
        bmesh.update_edit_mesh(obj.data)
        bm.select_history.clear()
        return
    else:
        pg.error = f"{PDT_ERR_EDOB_MODE},{obj.mode})"
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return
