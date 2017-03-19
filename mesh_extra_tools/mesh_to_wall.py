# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; version 2
#  of the License.
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


bl_info = {
    "name": "Mesh to wall",
    "author": "luxuy_BlenderCN",
    "version": (0.8),
    "blender": (2, 71, 0),
    "location": "View3D > EditMode > Mesh",
    "description": "Make wall from single mesh lines.",
    "url": "https://luxuy.github.io/BlenderAddons/Mesh-to-wall/Mesh_to_wall.html",
    "category": "Mesh"}

import bpy
import bmesh
from bpy.types import Operator
from bpy.props import FloatProperty
from math import sin, radians
from mathutils import Vector, Quaternion


def link_verts(bm, ver_index):
    linked_verts = []
    bm.verts.ensure_lookup_table()
    v = bm.verts[ver_index]
    for e in v.link_edges:
        linked_verts.append(e.verts[1].index)
        linked_verts.append(e.verts[0].index)

    linked_verts = list(set(linked_verts) - set([ver_index]))

    return linked_verts


def qq_sort(bm, ver_index, vm, wm):
    verts = link_verts(bm, ver_index)
    pt0 = bm.verts[ver_index].co

    def ang_2d_sort(x):
        pt1 = bm.verts[x].co
        vec = vm * wm * pt1 - vm * wm * pt0
        vec = Vector(vec[0:2])
        ang = vec.angle_signed(Vector((1, 0)))

        if ang < 0:
            return ang + 3.1415926 * 2
        else:
            return ang
    verts = sorted(verts, key=ang_2d_sort)

    return verts


def turn_left(bm, v1, v2, vm, wm):
    links = [v1, v2]

    verts = qq_sort(bm, links[-1], vm, wm)
    v = verts.index(links[-2])
    if v == 0:
        v_nxt = verts[-1]
    else:
        v_nxt = verts[v - 1]

    links.append(v_nxt)

    while not(links[-1] == links[1] and links[-2] == links[0]):

        verts = qq_sort(bm, links[-1], vm, wm)
        v = verts.index(links[-2])
        if v == 0:
            v_nxt = verts[-1]
        else:
            v_nxt = verts[v - 1]

        links.append(v_nxt)
    links.pop()

    return links


def lp_left(bm, lp, wid, vm, wm):
    size = len(lp)
    up = wm.inverted() * vm.inverted() * Vector((0, 0, 1))
    lp_off = []
    faces = []
    for i in range(size - 1):
        if i == 0:
            pt = bm.verts[lp[i]].co
            pre = bm.verts[lp[-2]].co
            nxt = bm.verts[lp[1]].co
            pre_ind = lp[size - 2]
            nxt_ind = lp[1]
        else:
            bm.verts.ensure_lookup_table()
            pt = bm.verts[lp[i]].co
            pre = bm.verts[lp[i - 1]].co
            nxt = bm.verts[lp[i + 1]].co
            pre_ind = lp[i - 1]
            nxt_ind = lp[i + 1]

        vec1 = pt - pre
        vec2 = pt - nxt

        mid = vec1.normalized() + vec2.normalized()
        if mid.length < 10e-4:

            up2 = Vector((0, 0, 1))
            mid = up2.cross(vec1)

        else:
            xx = mid.cross(vec1).dot(up)

            if xx > 0:
                mid.negate()

        mid.normalize()
        if pre_ind == nxt_ind:
            mid = (pt - pre).normalized()
            q_a = Quaternion((0.0, 0.0, 1.0), radians(90.0))
            q_b = Quaternion((0.0, 0.0, 1.0), radians(-180.0))
            mid.rotate(q_a)
            pt1 = pt + mid * wid
            mid.rotate(q_b)
            pt2 = pt + mid * wid
            new_vert_1 = bm.verts.new(pt1)
            new_vert_2 = bm.verts.new(pt2)
            lp_off.append([new_vert_1, new_vert_2])
        else:
            ang = mid.angle(pre - pt)

            vec_len = wid / (sin(ang))
            pt = pt + mid * vec_len
            new_vert = bm.verts.new(pt)
            lp_off.append(new_vert)
    lp_off.append(lp_off[0])
    bm.verts.index_update()
    for i in range(len(lp_off) - 1):
        bm.verts.ensure_lookup_table()
        p1 = bm.verts[lp[i]]
        p2 = bm.verts[lp[i + 1]]
        p3 = lp_off[i + 1]
        p4 = lp_off[i]

        if isinstance(p3, list):

            faces.append((p1, p2, p3[0], p4))
            # faces.append((p3[0],p2,p3[1]))
        elif isinstance(p4, list):

            faces.append((p1, p2, p3, p4[1]))
        else:
            faces.append((p1, p2, p3, p4))

    return faces


# Operators

class MeshtoWall(Operator):
    bl_idname = "bpt.mesh_to_wall"
    bl_label = "Edge(s) to Wall"
    bl_description = "Top View, Extrude Flat Along Edges"
    bl_options = {'REGISTER', 'UNDO'}

    wid = FloatProperty(
                name='Wall width:',
                default=0.1,
                min=0.001, max=10
                )

    def check_vert(self, context):
        obj = bpy.context.object
        if len(obj.data.vertices) <= 1:
            return False
        return True

    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')
        if self.check_vert(context):
            bpy.ops.object.mode_set(mode='EDIT')
            ob = bpy.context.object
            bm = bmesh.from_edit_mesh(ob.data)
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.003)
            bmesh.ops.delete(bm, geom=bm.faces, context=3)
            context.tool_settings.mesh_select_mode = (True, True, False)

            v3d = context.space_data
            rv3d = v3d.region_3d
            vm = rv3d.view_matrix
            wm = ob.matrix_world
            faces = []
            sel = []
            for v in bm.verts:
                sel.append(v.index)
            bpy.ops.mesh.select_all(action='DESELECT')

            for j in sel:
                verts = link_verts(bm, j)

                if len(verts) > 1:
                    for i in verts:
                        lp = turn_left(bm, j, i, vm, wm)

                        bpy.ops.mesh.select_all(action='DESELECT')

                        faces += lp_left(bm, lp, self.wid * 0.5, vm, wm)
                        lp = [bm.verts[i] for i in lp]

                        lp = lp[1:]

                        bpy.ops.mesh.select_all(action='DESELECT')
            for f in faces:
                try:
                    bm.faces.new(f)
                except:
                    pass
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.003)
            bm = bmesh.update_edit_mesh(ob.data, 1, 1)
        else:
            bpy.ops.object.mode_set(mode='EDIT')
            self.report({'WARNING'}, "None or a single vertex found, cancelling the operation")
            return {'CANCELLED'}

        return {'FINISHED'}


def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
