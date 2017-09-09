# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####


import bgl
import bmesh
import numpy as np
from mathutils import Matrix

from .bgl_ext import VoidBufValue, np_array_as_bgl_Buffer, bgl_Buffer_reshape
from .utils_shader import Shader


def load_shader(shadername):
    from os import path
    with open(path.join(path.dirname(__file__), 'resources', shadername), 'r') as f:
        return f.read()


def get_mesh_vert_co_array(me):
    tot_vco = len(me.vertices)
    if tot_vco:
        verts_co = bgl.Buffer(bgl.GL_FLOAT, (tot_vco * 3))
        me.vertices.foreach_get("co", verts_co)
        bgl_Buffer_reshape(verts_co, (tot_vco, 3))
        return verts_co
    return None


def get_bmesh_vert_co_array(bm):
    tot_vco = len(bm.verts)
    if tot_vco:
        return bgl.Buffer(bgl.GL_FLOAT, (tot_vco, 3), [v.co for v in bm.verts])
    return None


def get_mesh_tri_verts_array(me):
    num_tris = len(me.loops) - 2 * len(me.polygons)
    if num_tris:
        bm = bmesh.new()
        bm.from_mesh(me, face_normals=False)
        ltris = bm.calc_tessface()
        tris = bgl.Buffer(bgl.GL_INT, (num_tris, 3))
        for i, ltri in enumerate(ltris):
            tris[i] = ltri[0].vert.index, ltri[1].vert.index, ltri[2].vert.index
        bm.free()
        return tris
    return None


def get_mesh_tri_co_array(me, tri_verts):
    num_tris = len(tri_verts)
    if num_tris:
        verts = me.vertices
        tris = bgl.Buffer(bgl.GL_FLOAT, (num_tris, 3, 3))
        for i, tri in enumerate(tri_verts):
            tris[i] = verts[tri[0]].co, verts[tri[1]].co, verts[tri[2]].co
        return tris
    return None


def get_bmesh_tri_verts_array(bm):
    ltris = bm.calc_tessface()
    tris = [[ltri[0].vert.index, ltri[1].vert.index, ltri[2].vert.index] for ltri in ltris if not ltri[0].face.hide]
    if tris:
        return bgl.Buffer(bgl.GL_INT, (len(tris), 3), tris)
    return None


def get_bmesh_tri_co_array(bm, tri_verts):
    num_tris = len(tri_verts)
    if num_tris:
        verts = bm.verts
        tris = bgl.Buffer(bgl.GL_FLOAT, (num_tris, 3, 3))
        for i, tri in enumerate(tri_verts):
            tris[i] = verts[tri[0]].co, verts[tri[1]].co, verts[tri[2]].co
        return tris
    return None


def get_mesh_edge_verts_array(me):
    tot_edges = len(me.edges)
    if tot_edges:
        edge_verts = np.empty(tot_edges * 2, 'i4')
        me.edges.foreach_get("vertices", edge_verts)
        edge_verts.shape = tot_edges, 2
        return np_array_as_bgl_Buffer(edge_verts)
    return None


def get_mesh_edge_co_array(me, edge_verts):
    if edge_verts:
        edges_co = bgl.Buffer(bgl.GL_FLOAT, (len(edge_verts), 2, 3))
        verts = me.vertices
        for i, (v0, v1) in enumerate(edge_verts):
            edges_co[i][0] = verts[v0].co
            edges_co[i][1] = verts[v1].co
        return edges_co
    return None


def get_bmesh_edge_verts_array(bm):
    bm.edges.ensure_lookup_table()
    edges = [[e.verts[0].index, e.verts[1].index] for e in bm.edges if not e.hide]
    if edges:
        return bgl.Buffer(bgl.GL_INT, (len(edges), 2), edges)
    return None


def get_bmesh_edge_co_array(bm, edge_verts):
    if edge_verts:
        edges_co = bgl.Buffer(bgl.GL_FLOAT, (len(edge_verts), 2, 3))
        verts = bm.verts
        for i, (v0, v1) in enumerate(edge_verts):
            edges_co[i][0] = verts[v0].co
            edges_co[i][1] = verts[v1].co
        return edges_co
    return None


def get_mesh_loosevert_array(me, edges):
    verts = np.arange(len(me.vertices))

    mask = np.in1d(verts, edges, invert=True)

    verts = verts[mask]
    if len(verts):
        return bgl.Buffer(bgl.GL_INT, len(verts), verts)
    return None


def get_bmesh_loosevert_array(bm):
    looseverts = [v.index for v in bm.verts if not (v.link_edges or v.hide)]
    if looseverts:
        return bgl.Buffer(bgl.GL_INT, len(looseverts), looseverts)
    return None


class _Mesh_Arrays():
    def __init__(self, obj, create_tris, create_edges, create_looseverts):
        self.tri_verts = self.edge_verts = self.looseverts = None
        self.tris_co = self.edges_co = self.looseverts_co = None
        if obj.type == 'MESH':
            me = obj.data
            if me.is_editmode:
                bm = bmesh.from_edit_mesh(me)
                bm.verts.ensure_lookup_table()

                if False: #Blender 2.8
                    self.verts = get_bmesh_vert_co_array(bm)
                if create_tris:
                    self.tri_verts = get_bmesh_tri_verts_array(bm)
                    self.tris_co = get_bmesh_tri_co_array(bm, self.tri_verts)
                if create_edges:
                    self.edge_verts = get_bmesh_edge_verts_array(bm)
                    self.edges_co = get_bmesh_edge_co_array(bm, self.edge_verts)
                if create_looseverts:
                    self.looseverts = get_bmesh_loosevert_array(bm)
                    if self.looseverts:
                        self.looseverts_co = bgl.Buffer(bgl.GL_FLOAT, (len(self.looseverts), 3), [bm.verts[i].co for i in self.looseverts])
            else:
                if False: #Blender 2.8
                    self.verts = get_mesh_vert_co_array(me)
                if create_tris:
                    self.tri_verts = get_mesh_tri_verts_array(me)
                    self.tris_co = get_mesh_tri_co_array(me, self.tri_verts)
                if create_edges or create_looseverts:
                    self.edge_verts = get_mesh_edge_verts_array(me)

                    if create_edges:
                        self.edges_co = get_mesh_edge_co_array(me, self.edge_verts)
                    if create_looseverts:
                        self.looseverts = get_mesh_loosevert_array(me, self.edge_verts)
                        if self.looseverts:
                            self.looseverts_co = bgl.Buffer(bgl.GL_FLOAT, (len(self.looseverts), 3), [me.vertices[i].co for i in self.looseverts])

        else: #TODO
            self.looseverts = bgl.Buffer(bgl.GL_INT, 1)
            self.looseverts_co = bgl.Buffer(bgl.GL_FLOAT, (1, 3))

    def __del__(self):
        del self.tri_verts, self.edge_verts, self.looseverts
        del self.tris_co, self.edges_co, self.looseverts_co


class GPU_Indices_Mesh():
    shader = Shader(
        load_shader('3D_vert.glsl'),
        None,
        load_shader('primitive_id_frag.glsl'),
    )

    unif_use_clip_planes = bgl.glGetUniformLocation(shader.program, 'use_clip_planes')
    unif_clip_plane = bgl.glGetUniformLocation(shader.program, 'clip_plane')

    unif_MVP = bgl.glGetUniformLocation(shader.program, 'MVP')
    unif_MV = bgl.glGetUniformLocation(shader.program, 'MV')
    unif_offset = bgl.glGetUniformLocation(shader.program, 'offset')

    attr_pos = bgl.glGetAttribLocation(shader.program, 'pos')
    attr_primitive_id = bgl.glGetAttribLocation(shader.program, 'primitive_id')

    P = bgl.Buffer(bgl.GL_FLOAT, (4, 4))
    MV = bgl.Buffer(bgl.GL_FLOAT, (4, 4))

    # returns of public API #
    vert_index = bgl.Buffer(bgl.GL_INT, 1)

    tri_co = bgl.Buffer(bgl.GL_FLOAT, (3, 3))
    edge_co = bgl.Buffer(bgl.GL_FLOAT, (2, 3))
    vert_co = bgl.Buffer(bgl.GL_FLOAT, 3)

    def __init__(self, obj, draw_tris, draw_edges, draw_verts):
        self._NULL = VoidBufValue(0)

        self.MVP = bgl.Buffer(bgl.GL_FLOAT, (4, 4))

        self.obj = obj
        self.draw_tris = draw_tris
        self.draw_edges = draw_edges
        self.draw_verts = draw_verts

        self.vbo = None
        self.vbo_tris = None
        self.vbo_edges = None
        self.vbo_verts = None

        ## Create VAO ##
        self.vao = bgl.Buffer(bgl.GL_INT, 1)
        bgl.glGenVertexArrays(1, self.vao)
        bgl.glBindVertexArray(self.vao[0])

        ## Init Array ##
        mesh_arrays = _Mesh_Arrays(obj, draw_tris, draw_edges, draw_verts)

        ## Create VBO for vertices ##
        if False: # Blender 2.8
            if not mesh_arrays.verts:
                self.draw_tris = False
                self.draw_edges = False
                self.draw_verts = False
                return

            self.vbo_len = len(mesh_arrays.verts)

            self.vbo = bgl.Buffer(bgl.GL_INT, 1)
            bgl.glGenBuffers(1, self.vbo)
            bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vbo[0])
            bgl.glBufferData(bgl.GL_ARRAY_BUFFER, self.vbo_len * 12, mesh_arrays.verts, bgl.GL_STATIC_DRAW)

        ## Create VBO for Tris ##
        if mesh_arrays.tri_verts:
            self.tri_verts = mesh_arrays.tri_verts
            self.num_tris = len(self.tri_verts)

            self.vbo_tris = bgl.Buffer(bgl.GL_INT, 1)
            bgl.glGenBuffers(1, self.vbo_tris)
            bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vbo_tris[0])
            bgl.glBufferData(bgl.GL_ARRAY_BUFFER, self.num_tris * 36, mesh_arrays.tris_co, bgl.GL_STATIC_DRAW)

            tri_indices = np.repeat(np.arange(self.num_tris, dtype = 'f4'), 3)
            self.vbo_tri_indices = bgl.Buffer(bgl.GL_INT, 1)
            bgl.glGenBuffers(1, self.vbo_tri_indices)
            bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vbo_tri_indices[0])
            bgl.glBufferData(bgl.GL_ARRAY_BUFFER, self.num_tris * 12, np_array_as_bgl_Buffer(tri_indices), bgl.GL_STATIC_DRAW)
            del tri_indices

        else:
            self.num_tris = 0
            self.draw_tris = False

        ## Create VBO for Edges ##
        if mesh_arrays.edge_verts:
            self.edge_verts = mesh_arrays.edge_verts
            self.num_edges = len(self.edge_verts)

            self.vbo_edges = bgl.Buffer(bgl.GL_INT, 1)
            bgl.glGenBuffers(1, self.vbo_edges)
            bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vbo_edges[0])
            bgl.glBufferData(bgl.GL_ARRAY_BUFFER, self.num_edges * 24, mesh_arrays.edges_co, bgl.GL_STATIC_DRAW)

            edge_indices = np.repeat(np.arange(self.num_edges, dtype = 'f4'),2)
            self.vbo_edge_indices = bgl.Buffer(bgl.GL_INT, 1)
            bgl.glGenBuffers(1, self.vbo_edge_indices)
            bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vbo_edge_indices[0])
            bgl.glBufferData(bgl.GL_ARRAY_BUFFER, self.num_edges * 8, np_array_as_bgl_Buffer(edge_indices), bgl.GL_STATIC_DRAW)
            del edge_indices
        else:
            self.num_edges = 0
            self.draw_edges = False

        ## Create EBO for Loose Verts ##
        if mesh_arrays.looseverts:
            self.looseverts = mesh_arrays.looseverts
            self.num_verts = len(mesh_arrays.looseverts)

            self.vbo_verts = bgl.Buffer(bgl.GL_INT, 1)
            bgl.glGenBuffers(1, self.vbo_verts)
            bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vbo_verts[0])
            bgl.glBufferData(bgl.GL_ARRAY_BUFFER, self.num_verts * 12, mesh_arrays.looseverts_co, bgl.GL_STATIC_DRAW)

            looseverts_indices = np.arange(self.num_verts, dtype = 'f4')
            self.vbo_looseverts_indices = bgl.Buffer(bgl.GL_INT, 1)
            bgl.glGenBuffers(1, self.vbo_looseverts_indices)
            bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vbo_looseverts_indices[0])
            bgl.glBufferData(bgl.GL_ARRAY_BUFFER, self.num_verts * 4, np_array_as_bgl_Buffer(looseverts_indices), bgl.GL_STATIC_DRAW)
            del looseverts_indices
        else:
            self.num_verts = 0
            self.draw_verts = False

        del mesh_arrays

        bgl.glBindVertexArray(0)


    def get_tot_elems(self):
        tot = 0

        if self.draw_tris:
            tot += self.num_tris

        if self.draw_edges:
            tot += self.num_edges

        if self.draw_verts:
            tot += self.num_verts

        return tot


    def set_draw_mode(self, draw_tris, draw_edges, draw_verts):
        self.draw_tris = draw_tris and self.vbo_tris
        self.draw_edges = draw_edges and self.vbo_edges
        self.draw_verts = draw_verts and self.vbo_verts


    @classmethod
    def set_ProjectionMatrix(cls, P):
        cls.P[:] = P


    def set_ModelViewMatrix(self, MV):
        self.MV[:] = MV[:]
        self.MVP[:] = Matrix(self.P) * MV


    def Draw(self, index_offset):
        self.first_index = index_offset
        bgl.glUseProgram(self.shader.program)
        bgl.glBindVertexArray(self.vao[0])

        bgl.glUniformMatrix4fv(self.unif_MV, 1, bgl.GL_TRUE, self.MV)
        bgl.glUniformMatrix4fv(self.unif_MVP, 1, bgl.GL_TRUE, self.MVP)

        if self.draw_tris:
            bgl.glUniform1f(self.unif_offset, float(index_offset)) # bgl has no glUniform1ui :\

            bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vbo_tris[0])
            bgl.glEnableVertexAttribArray(self.attr_pos)
            bgl.glVertexAttribPointer(self.attr_pos, 3, bgl.GL_FLOAT, bgl.GL_FALSE, 0, self._NULL.buf)

            bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vbo_tri_indices[0])
            bgl.glEnableVertexAttribArray(self.attr_primitive_id)
            bgl.glVertexAttribPointer(self.attr_primitive_id, 1, bgl.GL_FLOAT, bgl.GL_FALSE, 0, self._NULL.buf)

            bgl.glDrawArrays(bgl.GL_TRIANGLES, 0, self.num_tris * 3)

            index_offset += self.num_tris
            bgl.glDepthRange(-0.00005, 0.99995)

        if self.draw_edges:
            bgl.glUniform1f(self.unif_offset, float(index_offset)) #TODO: use glUniform1ui

            bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vbo_edges[0])
            bgl.glVertexAttribPointer(self.attr_pos, 3, bgl.GL_FLOAT, bgl.GL_FALSE, 0, self._NULL.buf)
            bgl.glEnableVertexAttribArray(self.attr_pos)

            bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vbo_edge_indices[0])
            bgl.glVertexAttribPointer(self.attr_primitive_id, 1, bgl.GL_FLOAT, bgl.GL_FALSE, 0, self._NULL.buf)
            bgl.glEnableVertexAttribArray(self.attr_primitive_id)

            bgl.glDrawArrays(bgl.GL_LINES, 0, self.num_edges * 2)

            index_offset += self.num_edges

        if self.draw_verts:
            bgl.glUniform1f(self.unif_offset, float(index_offset)) #TODO: use glUniform1ui

            bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vbo_verts[0])
            bgl.glVertexAttribPointer(self.attr_pos, 3, bgl.GL_FLOAT, bgl.GL_FALSE, 0, self._NULL.buf)
            bgl.glEnableVertexAttribArray(self.attr_pos)

            bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vbo_looseverts_indices[0])
            bgl.glVertexAttribPointer(self.attr_primitive_id, 1, bgl.GL_FLOAT, bgl.GL_FALSE, 0, self._NULL.buf)
            bgl.glEnableVertexAttribArray(self.attr_primitive_id)

            bgl.glDrawArrays(bgl.GL_POINTS, 0, self.num_verts)

        bgl.glDepthRange(0.0, 1.0)


    def get_tri_co(self, index):
        bgl.glBindVertexArray(self.vao[0])
        bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vbo_tris[0])
        bgl.glGetBufferSubData(bgl.GL_ARRAY_BUFFER, index * 36, 36, self.tri_co)
        bgl.glBindVertexArray(0)
        return self.tri_co


    def get_edge_co(self, index):
        bgl.glBindVertexArray(self.vao[0])
        bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vbo_edges[0])
        bgl.glGetBufferSubData(bgl.GL_ARRAY_BUFFER, index * 24, 24, self.edge_co)
        bgl.glBindVertexArray(0)
        return self.edge_co


    def get_loosevert_co(self, index):
        bgl.glBindVertexArray(self.vao[0])
        bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vbo_verts[0])
        bgl.glGetBufferSubData(bgl.GL_ARRAY_BUFFER, index * 12, 12, self.vert_co)
        bgl.glBindVertexArray(0)
        return self.vert_co


    def get_tri_verts(self, index):
        return self.tri_verts[index]


    def get_edge_verts(self, index):
        return self.edge_verts[index]


    def get_loosevert_index(self, index):
        return self.looseverts[index]


    def __del__(self):
        del self._NULL

        if self.vbo_tris:
            bgl.glDeleteBuffers(1, self.vbo_tris)
            bgl.glDeleteBuffers(1, self.vbo_tri_indices)
            del self.tri_verts

        if self.vbo_edges:
            bgl.glDeleteBuffers(1, self.vbo_edges)
            bgl.glDeleteBuffers(1, self.vbo_edge_indices)
            del self.edge_verts

        if self.vbo_verts:
            bgl.glDeleteBuffers(1, self.vbo_verts)
            bgl.glDeleteBuffers(1, self.vbo_looseverts_indices)
            del self.looseverts

        bgl.glDeleteVertexArrays(1, self.vao)
        #print('mesh_del', self.obj.name)


class PreviousGLState:
    buf = bgl.Buffer(bgl.GL_INT, (4, 1))
    cur_program = buf[0]
    cur_vao = buf[1]
    cur_vbo = buf[2]
    cur_ebo = buf[3]


def _store_current_shader_state(cls):
    bgl.glGetIntegerv(bgl.GL_CURRENT_PROGRAM, cls.cur_program)
    bgl.glGetIntegerv(bgl.GL_VERTEX_ARRAY_BINDING, cls.cur_vao)
    bgl.glGetIntegerv(bgl.GL_ARRAY_BUFFER_BINDING, cls.cur_vbo)
    bgl.glGetIntegerv(bgl.GL_ELEMENT_ARRAY_BUFFER_BINDING, cls.cur_ebo)


def _restore_shader_state(cls):
    bgl.glUseProgram(cls.cur_program[0])
    bgl.glBindVertexArray(cls.cur_vao[0])
    bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, cls.cur_vbo[0])
    bgl.glBindBuffer(bgl.GL_ELEMENT_ARRAY_BUFFER, cls.cur_ebo[0])


def gpu_Indices_enable_state():
    _store_current_shader_state(PreviousGLState)

    bgl.glUseProgram(GPU_Indices_Mesh.shader.program)
    #bgl.glBindVertexArray(GPU_Indices_Mesh.vao[0])

def gpu_Indices_restore_state():
    bgl.glBindVertexArray(0)
    _restore_shader_state(PreviousGLState)
