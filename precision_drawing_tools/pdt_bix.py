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
#
# <pep8 compliant>
#
# ----------------------------------------------------------
# Author: Zeffii
# Modified by: Alan Odom (Clockmender) & Rune Morling (ermo)
# ----------------------------------------------------------
#
#
import bpy
import bmesh
from . import pdt_cad_module as cm
from .pdt_msg_strings import (
    PDT_ERR_2CPNPE,
    PDT_ERR_NCEDGES,
    PDT_ERR_EDOB_MODE,
)
from .pdt_functions import debug, oops

def add_line_to_bisection(self, context):
    """Computes Bisector of 2 Co-Planar Edges.

    Args:
        context: Blender bpy.context instance

    Returns:
        Nothing.
    """

    obj = context.object
    if all([bool(obj), obj.type == "MESH", obj.mode == "EDIT"]):
        pg = scene.pdt_pg
        me = obj.data
        bm = bmesh.from_edit_mesh(me)

        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()

        edges = [e for e in bm.edges if e.select and not e.hide]

        if not len(edges) == 2:
            pg.error = f"{PDT_ERR_2CPNPE}"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return

        [[v1, v2], [v3, v4]] = [[v.co for v in e.verts] for e in edges]
        debug(f"vectors found:\n {v1}\n {v2}\n {v3}\n {v4}")

        dist1 = (v1 - v2).length
        dist2 = (v3 - v4).length
        bdist = min([dist1, dist2])
        edge1 = (v1, v2)
        edge2 = (v3, v4)

        if not cm.test_coplanar(edge1, edge2):
            msg = PDT_ERR_NCEDGES
            self.report({"ERROR"}, msg)
            return

        # get pt and pick farthest vertex from (projected) intersections
        pt = cm.get_intersection(edge1, edge2)
        far1 = v2 if (v1 - pt).length < (v2 - pt).length else v1
        far2 = v4 if (v3 - pt).length < (v4 - pt).length else v3

        dex1 = far1 - pt
        dex2 = far2 - pt
        dex1 = dex1 * (bdist / dex1.length)
        dex2 = dex2 * (bdist / dex2.length)
        pt2 = pt + (dex1).lerp(dex2, 0.5)
        pt3 = pt2.lerp(pt, 2.0)

        vec1 = bm.verts.new(pt2)
        vec2 = bm.verts.new(pt)
        vec3 = bm.verts.new(pt3)
        bm.edges.new((vec1, vec2))
        bm.edges.new((vec2, vec3))
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
        bmesh.update_edit_mesh(me)
    else:
        pg.error = f"{PDT_ERR_EDOB_MODE},{obj.mode})"
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return


class PDT_OT_LineOnBisection(bpy.types.Operator):
    """Create Bisector between 2 Selected Edges."""

    bl_idname = "pdt.linetobisect"
    bl_label = "Add Edges Bisector"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """Only allow operation on a mesh object in EDIT mode."""
        ob = context.active_object
        if ob is None:
            return False
        return all([ob is not None, ob.type == "MESH", ob.mode == "EDIT"])

    def execute(self, context):
        """Computes Bisector of 2 Co-Planar Edges.

        Args:
            context: Blender bpy.context instance.

        Returns:
            Status Set.
        """

        pg = context.scene.pdt_pg
        pg.command = f"bis"
        return {"FINISHED"}
