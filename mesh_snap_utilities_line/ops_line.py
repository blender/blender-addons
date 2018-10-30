### BEGIN GPL LICENSE BLOCK #####
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

import bpy, bmesh

from bpy.props import FloatProperty

from mathutils import Vector

from mathutils.geometry import intersect_point_line

from .common_classes import (
    SnapDrawn,
    CharMap,
    SnapNavigation,
    )

from .common_utilities import (
    get_units_info,
    convert_distance,
    snap_utilities,
    )

if not __package__:
    __package__ = "mesh_snap_utilities"


def Bpy_Area_header_text_clear(area):
    #HACK
    import ctypes
    func = area.header_text_set
    c_func = ctypes.c_void_p.from_address(id(func) + 56).value
    c_param = ctypes.c_void_p.from_address(c_func + 24).value
    flag_parameter = ctypes.c_void_p.from_address(c_param + 40)
    previous_value = flag_parameter.value
    flag_parameter.value = 0
    func()
    flag_parameter.value = previous_value


def get_closest_edge(bm, point, dist):
    r_edge = None
    for edge in bm.edges:
        v1 = edge.verts[0].co
        v2 = edge.verts[1].co
        # Test the BVH (AABB) first
        for i in range(3):
            if v1[i] <= v2[i]:
                isect = v1[i] - dist <= point[i] <= v2[i] + dist
            else:
                isect = v2[i] - dist <= point[i] <= v1[i] + dist

            if not isect:
                break
        else:
            ret = intersect_point_line(point, v1, v2)

            if ret[1] < 0.0:
                tmp = v1
            elif ret[1] > 1.0:
                tmp = v2
            else:
                tmp = ret[0]

            new_dist = (point - tmp).length
            if new_dist <= dist:
                dist = new_dist
                r_edge = edge

    return r_edge


def get_loose_linked_edges(bmvert):
    linked = [e for e in bmvert.link_edges if not e.link_faces]
    for e in linked:
        linked += [le for v in e.verts if not v.link_faces for le in v.link_edges if le not in linked]
    return linked


def draw_line(self, bm_geom, location):
    obj = self.main_snap_obj.data[0]
    bm = self.main_bm
    split_faces = set()

    drawing_is_dirt = False
    update_edit_mesh = False

    if bm_geom is None:
        vert = bm.verts.new(location)
        self.list_verts.append(vert)

    elif isinstance(bm_geom, bmesh.types.BMVert):
        if (bm_geom.co - location).length_squared < .001:
            if self.list_verts == [] or self.list_verts[-1] != bm_geom:
                self.list_verts.append(bm_geom)
        else:
            vert = bm.verts.new(location)
            self.list_verts.append(vert)
            drawing_is_dirt = True

    elif isinstance(bm_geom, bmesh.types.BMEdge):
        self.list_edges.append(bm_geom)
        ret = intersect_point_line(location, bm_geom.verts[0].co, bm_geom.verts[1].co)

        if (ret[0] - location).length_squared < .001:
            if ret[1] == 0.0:
                vert = bm_geom.verts[0]
            elif ret[1] == 1.0:
                vert = bm_geom.verts[1]
            else:
                edge, vert = bmesh.utils.edge_split(bm_geom, bm_geom.verts[0], ret[1])
                drawing_is_dirt = True
            self.list_verts.append(vert)
            self.geom = vert # hack to highlight in the drawing
            # self.list_edges.append(edge)

        else:  # constrain point is near
            vert = bm.verts.new(location)
            self.list_verts.append(vert)
            drawing_is_dirt = True

    elif isinstance(bm_geom, bmesh.types.BMFace):
        split_faces.add(bm_geom)
        vert = bm.verts.new(location)
        self.list_verts.append(vert)
        drawing_is_dirt = True

    # draw, split and create face
    if len(self.list_verts) >= 2:
        v1, v2 = self.list_verts[-2:]
        # v2_link_verts = [x for y in [a.verts for a in v2.link_edges] for x in y if x != v2]
        edge = bm.edges.get([v1, v2])
        if edge:
                self.list_edges.append(edge)

        else:  # if v1 not in v2_link_verts:
            if not v2.link_edges:
                edge = bm.edges.new([v1, v2])
                self.list_edges.append(edge)
                drawing_is_dirt = True
            else:  # split face
                v1_link_faces = v1.link_faces
                v2_link_faces = v2.link_faces
                if v1_link_faces and v2_link_faces:
                    split_faces.update(set(v1_link_faces).intersection(v2_link_faces))

                else:
                    if v1_link_faces:
                        faces = v1_link_faces
                        co2 = v2.co.copy()
                    else:
                        faces = v2_link_faces
                        co2 = v1.co.copy()

                    for face in faces:
                        if bmesh.geometry.intersect_face_point(face, co2):
                            co = co2 - face.calc_center_median()
                            if co.dot(face.normal) < 0.001:
                                split_faces.add(face)

                if split_faces:
                    edge = bm.edges.new([v1, v2])
                    self.list_edges.append(edge)
                    ed_list = get_loose_linked_edges(v2)
                    for face in split_faces:
                        facesp = bmesh.utils.face_split_edgenet(face, ed_list)
                    del split_faces
                    update_edit_mesh = True
                else:
                    if self.intersect:
                        facesp = bmesh.ops.connect_vert_pair(bm, verts=[v1, v2], verts_exclude=bm.verts)
                        # print(facesp)
                    if not self.intersect or not facesp['edges']:
                        edge = bm.edges.new([v1, v2])
                        self.list_edges.append(edge)
                        drawing_is_dirt = True
                    else:
                        for edge in facesp['edges']:
                            self.list_edges.append(edge)
                            update_edit_mesh = True

        # create face
        if self.create_face:
            ed_list = set(self.list_edges)
            for edge in v2.link_edges:
                for vert in edge.verts:
                    if vert != v2 and vert in self.list_verts:
                        ed_list.add(edge)
                        break
                else:
                    continue
                # Inner loop had a break, break the outer
                break

            ed_list.update(get_loose_linked_edges(v2))

            bmesh.ops.edgenet_fill(bm, edges=list(ed_list))
            update_edit_mesh = True
            # print('face created')
    if update_edit_mesh or drawing_is_dirt:
        obj.data.update_gpu_tag()
        obj.data.update_tag()
        obj.update_from_editmode()
        obj.update_tag()
        bmesh.update_edit_mesh(obj.data)
        self.sctx.tag_update_drawn_snap_object(self.main_snap_obj)
        #bm.verts.index_update()

    return [obj.matrix_world @ v.co for v in self.list_verts]


class SnapUtilitiesLine(bpy.types.Operator):
    """Make Lines. Connect them to split faces"""
    bl_idname = "mesh.make_line"
    bl_label = "Line Tool"
    bl_options = {'REGISTER'}

    constrain_keys = {
        'X': Vector((1,0,0)),
        'Y': Vector((0,1,0)),
        'Z': Vector((0,0,1)),
        'RIGHT_SHIFT': 'shift',
        'LEFT_SHIFT': 'shift',
    }

    def modal(self, context, event):
        if self.navigation_ops.run(context, event, self.prevloc if self.vector_constrain else self.location):
            return {'RUNNING_MODAL'}

        context.area.tag_redraw()

        if event.ctrl and event.type == 'Z' and event.value == 'PRESS':
            del self.bm
            del self.main_bm
            bpy.ops.ed.undo()
            self.vector_constrain = None
            self.list_verts_co = []
            self.list_verts = []
            self.list_edges = []
            bpy.ops.object.mode_set(mode='EDIT') # just to be sure
            self.main_bm = bmesh.from_edit_mesh(self.main_snap_obj.data[0])
            self.sctx.tag_update_drawn_snap_object(self.main_snap_obj)
            return {'RUNNING_MODAL'}

        is_making_lines = bool(self.list_verts_co)

        if event.type == 'MOUSEMOVE' or self.bool_update:
            if self.rv3d.view_matrix != self.rotMat:
                self.rotMat = self.rv3d.view_matrix.copy()
                self.bool_update = True
                snap_utilities.cache.snp_obj = None # hack for snap edge elemens update
            else:
                self.bool_update = False

            mval = Vector((event.mouse_region_x, event.mouse_region_y))

            self.snap_obj, self.prevloc, self.location, self.type, self.bm, self.geom, self.len = snap_utilities(
                    self.sctx,
                    self.main_snap_obj,
                    mval,
                    constrain=self.vector_constrain,
                    previous_vert=(self.list_verts[-1] if self.list_verts else None),
                    increment=self.incremental
            )

            if self.snap_to_grid and self.type == 'OUT':
                loc = self.location / self.rd
                self.location = Vector((round(loc.x),
                                        round(loc.y),
                                        round(loc.z))) * self.rd

            if self.keyf8 and is_making_lines:
                lloc = self.list_verts_co[-1]
                view_vec, orig = self.sctx.last_ray
                location = intersect_point_line(lloc, orig, (orig + view_vec))
                vec = (location[0] - lloc)
                ax, ay, az = abs(vec.x), abs(vec.y), abs(vec.z)
                vec.x = ax > ay > az or ax > az > ay
                vec.y = ay > ax > az or ay > az > ax
                vec.z = az > ay > ax or az > ax > ay
                if vec == Vector():
                    self.vector_constrain = None
                else:
                    vc = lloc + vec
                    try:
                        if vc != self.vector_constrain[1]:
                            type = 'X' if vec.x else 'Y' if vec.y else 'Z' if vec.z else 'shift'
                            self.vector_constrain = [lloc, vc, type]
                    except:
                        type = 'X' if vec.x else 'Y' if vec.y else 'Z' if vec.z else 'shift'
                        self.vector_constrain = [lloc, vc, type]

        if event.value == 'PRESS':
            if is_making_lines and (event.ascii in CharMap.ascii or event.type in CharMap.type):
                CharMap.modal(self, context, event)

            elif event.type in self.constrain_keys:
                self.bool_update = True
                self.keyf8 = False

                if self.vector_constrain and self.vector_constrain[2] == event.type:
                    self.vector_constrain = ()

                else:
                    if event.shift:
                        if isinstance(self.geom, bmesh.types.BMEdge):
                            if is_making_lines:
                                loc = self.list_verts_co[-1]
                                self.vector_constrain = (loc, loc + self.geom.verts[1].co -
                                                         self.geom.verts[0].co, event.type)
                            else:
                                self.vector_constrain = [self.main_snap_obj.mat @ v.co for
                                                         v in self.geom.verts] + [event.type]
                    else:
                        if is_making_lines:
                            loc = self.list_verts_co[-1]
                        else:
                            loc = self.location
                        self.vector_constrain = [loc, loc + self.constrain_keys[event.type], event.type]

            elif event.type == 'LEFTMOUSE':
                if not is_making_lines and self.bm:
                    self.main_snap_obj = self.snap_obj
                    self.main_bm = self.bm

                mat_inv = self.main_snap_obj.mat.inverted_safe()
                point = mat_inv @ self.location
                # with constraint the intersection can be in a different element of the selected one
                geom2 = self.geom
                if geom2:
                    geom2.select = False

                if self.vector_constrain:
                    geom2 = get_closest_edge(self.main_bm, point, .001)

                self.vector_constrain = None
                self.list_verts_co = draw_line(self, geom2, point)
                bpy.ops.ed.undo_push(message="Undo draw line*")

            elif event.type == 'TAB':
                self.keytab = self.keytab is False
                if self.keytab:
                    self.sctx.set_snap_mode(False, False, True)
                    context.tool_settings.mesh_select_mode = (False, False, True)
                else:
                    self.sctx.set_snap_mode(True, True, True)
                    context.tool_settings.mesh_select_mode = (True, True, self.snap_face)

            elif event.type == 'F8':
                self.vector_constrain = None
                self.keyf8 = self.keyf8 is False

        elif event.value == 'RELEASE':
            if event.type in {'RET', 'NUMPAD_ENTER'}:
                if self.length_entered != "" and self.list_verts_co:
                    try:
                        text_value = bpy.utils.units.to_value(self.unit_system, 'LENGTH', self.length_entered)
                        vector = (self.location - self.list_verts_co[-1]).normalized()
                        location = (self.list_verts_co[-1] + (vector * text_value))

                        mat_inv = self.main_snap_obj.mat.inverted_safe()
                        self.list_verts_co = draw_line(self, self.geom, mat_inv @ location)
                        self.length_entered = ""
                        self.vector_constrain = None

                    except:  # ValueError:
                        self.report({'INFO'}, "Operation not supported yet")

            elif event.type in {'RIGHTMOUSE', 'ESC'}:
                if not is_making_lines or event.type == 'ESC':
                    del self.main_bm #avoids unpredictable crashs
                    del self.bm
                    del self.list_edges
                    del self.list_verts
                    del self.list_verts_co

                    bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                    Bpy_Area_header_text_clear(context.area)
                    #context.area.header_text_set(text = "")
                    self.sctx.free()
                    del self.draw_cache

                    #Restore initial state
                    context.tool_settings.mesh_select_mode = self.select_mode
                    context.user_preferences.view.use_rotate_around_active = self.use_rotate_around_active
                    context.space_data.overlay.show_face_center = self.show_face_center
                    if not self.is_editmode:
                        bpy.ops.object.editmode_toggle()

                    return {'FINISHED'}
                else:
                    snap_utilities.cache.snp_obj = None # hack for snap edge elemens update
                    self.vector_constrain = None
                    self.list_edges = []
                    self.list_verts = []
                    self.list_verts_co = []

        a = ""
        if is_making_lines:
            if self.length_entered:
                pos = self.line_pos
                a = 'length: ' + self.length_entered[:pos] + '|' + self.length_entered[pos:]
            else:
                length = self.len
                length = convert_distance(length, self.uinfo)
                a = 'length: ' + length

        context.area.header_text_set(text = "hit: %.3f %.3f %.3f %s" % (*self.location, a))

        if True or is_making_lines:
            return {'RUNNING_MODAL'}

        return {'PASS_THROUGH'}

    def draw_callback_px(self):
        if self.bm:
            self.draw_cache.draw_elem(self.snap_obj, self.bm, self.geom)
        self.draw_cache.draw(self.type, self.location, self.list_verts_co, self.vector_constrain, self.prevloc)

    def invoke(self, context, event):
        if context.space_data.type == 'VIEW_3D':
            # print('name', __name__, __package__)
            preferences = context.user_preferences.addons[__package__].preferences

            #Store the preferences that will be used in modal
            self.intersect = preferences.intersect
            self.create_face = preferences.create_face
            self.outer_verts = preferences.outer_verts
            self.snap_to_grid = preferences.increments_grid

            self.draw_cache = SnapDrawn(
                preferences.out_color,
                preferences.face_color,
                preferences.edge_color,
                preferences.vert_color,
                preferences.center_color,
                preferences.perpendicular_color,
                preferences.constrain_shift_color,
                tuple(context.user_preferences.themes[0].user_interface.axis_x) + (1.0,),
                tuple(context.user_preferences.themes[0].user_interface.axis_y) + (1.0,),
                tuple(context.user_preferences.themes[0].user_interface.axis_z) + (1.0,)
            )

            obj = context.active_object

            #Create a new object
            if obj is None or obj.type != 'MESH':
                mesh = bpy.data.meshes.new("")
                obj = bpy.data.objects.new("", mesh)
                context.scene.objects.link(obj)
                context.scene.objects.active = obj
            else:
                mesh = obj.data

            #Store current state
            self.is_editmode = mesh.is_editmode
            self.use_rotate_around_active = context.user_preferences.view.use_rotate_around_active
            self.select_mode = context.tool_settings.mesh_select_mode[:]
            self.show_face_center = context.space_data.overlay.show_face_center

            #Modify the current state
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            context.user_preferences.view.use_rotate_around_active = True
            context.tool_settings.mesh_select_mode = (True, True, True)
            context.space_data.overlay.show_face_center = True
            context.scene.update_tag()

            #Configure the unit of measure
            scale = context.scene.unit_settings.scale_length
            self.unit_system = context.scene.unit_settings.system
            separate_units = context.scene.unit_settings.use_separate
            self.uinfo = get_units_info(scale, self.unit_system, separate_units)

            scale /= context.space_data.overlay.grid_scale * preferences.relative_scale
            self.rd = bpy.utils.units.to_value(self.unit_system, 'LENGTH', str(1 / scale))

            self.incremental = bpy.utils.units.to_value(self.unit_system, 'LENGTH', str(preferences.incremental))

            #Store values from 3d view context
            self.rv3d = context.region_data
            self.rotMat = self.rv3d.view_matrix.copy()
            # self.obj_glmatrix = bgl.Buffer(bgl.GL_FLOAT, [4, 4], self.obj_matrix.transposed())
            self.main_bm = self.bm = bmesh.from_edit_mesh(mesh) #remove at end

            #init these variables to avoid errors
            self.prevloc = Vector()
            self.location = Vector()
            self.list_verts = []
            self.list_edges = []
            self.list_verts_co = []
            self.bool_update = False
            self.vector_constrain = ()
            self.navigation_ops = SnapNavigation(context, True)
            self.type = 'OUT'
            self.len = 0
            self.length_entered = ""
            self.line_pos = 0
            self.geom = None

            #Init event variables
            self.keytab = False
            self.keyf8 = False

            #Init Snap Context
            from .snap_context_l import SnapContext

            self.sctx = SnapContext(context.region, context.space_data)
            self.sctx.set_pixel_dist(12)
            self.sctx.use_clip_planes(True)

            act_base = context.active_base

            if self.outer_verts:
                for base in context.visible_bases:
                    if base != act_base:
                        self.sctx.add_obj(base.object, base.object.matrix_world)

            self.main_snap_obj = self.snap_obj = self.sctx.add_obj(act_base.object, act_base.object.matrix_world)

            self.snap_face = True
            self.sctx.set_snap_mode(True, True, self.snap_face)

            #modals
            self._handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, (), 'WINDOW', 'POST_VIEW')
            context.window_manager.modal_handler_add(self)

            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}

def register():
    bpy.utils.register_class(SnapUtilitiesLine)

if __name__ == "__main__":
    register()
