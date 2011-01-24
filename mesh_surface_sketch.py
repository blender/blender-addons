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

bl_info = {
    "name": "Surface Sketch",
    "author": "Eclectiel",
    "version": (0,8),
    "blender": (2, 5, 3),
    "api": 31847,
    "location": "View3D > EditMode > ToolShelf",
    "description": "Draw meshes and re-topologies with Grease Pencil",
    "warning": "Beta",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"\
        "Scripts/Mesh/Surface_Sketch",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=22062",
    "category": "Mesh"}


import bpy
import math

from math import *
   

class VIEW3D_PT_tools_SURF_SKETCH(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    bl_context = "mesh_edit"
    bl_label = "Surface Sketching"
    
    @classmethod
    def poll(cls, context):
        return context.active_object

    def draw(self, context):
        layout = self.layout
        
        scn = context.scene
        ob = context.object
        
        col = layout.column(align=True)
        row = layout.row()
        row.separator()
        col.operator(GPENCIL_OT_surfsk_surface_add.bl_idname, text="Add Surface")
        col.prop(scn, "SURFSK_edges_U")
        col.prop(scn, "SURFSK_edges_V")
        row.separator()
        col.prop(scn, "SURFSK_keep_strokes")
        col.separator()
        row.separator()
        col.operator(GPENCIL_OT_surfsk_strokes_to_curves.bl_idname, text="Strokes to curves")
        


class GPENCIL_OT_surfsk_surface_add(bpy.types.Operator):
    bl_idname = "gpencil.surfsk_surface_add"
    bl_label = "Surface generation from grease pencil strokes"
    bl_description = "Surface generation from grease pencil strokes"
    
    
    #### Get an ordered list of a chain of vertices.
    def get_ordered_verts(self, ob, all_selected_edges_idx, all_selected_verts_idx, first_vert_idx, middle_vertex_idx):
        # Order selected vertexes.
        verts_ordered = []
        verts_ordered.append(self.main_object.data.vertices[first_vert_idx])
        prev_v = first_vert_idx
        prev_ed = None
        finish_while = False
        while True:
            edges_non_matched = 0
            for i in all_selected_edges_idx:
                if ob.data.edges[i] != prev_ed and ob.data.edges[i].vertices[0] == prev_v and ob.data.edges[i].vertices[1] in all_selected_verts_idx:
                    verts_ordered.append(self.main_object.data.vertices[ob.data.edges[i].vertices[1]])
                    prev_v = ob.data.edges[i].vertices[1]
                    prev_ed = ob.data.edges[i]
                elif ob.data.edges[i] != prev_ed and ob.data.edges[i].vertices[1] == prev_v and ob.data.edges[i].vertices[0] in all_selected_verts_idx:
                    verts_ordered.append(self.main_object.data.vertices[ob.data.edges[i].vertices[0]])
                    prev_v = ob.data.edges[i].vertices[0]
                    prev_ed = ob.data.edges[i]
                else:
                    edges_non_matched += 1
                    
                    if edges_non_matched == len(all_selected_edges_idx):
                        finish_while = True
                    
            if finish_while:
                break
        
        if middle_vertex_idx != None:
            verts_ordered.append(self.main_object.data.vertices[middle_vertex_idx])
            verts_ordered.reverse()
        
        return verts_ordered
    
    
    #### Calculates length of a chain of points.
    def get_chain_length(self, verts_ordered):
        edges_lengths = []
        edges_lengths_sum = 0
        for i in range(0, len(verts_ordered)):
            if i == 0:
                prev_v = verts_ordered[i]
            else:
                v = verts_ordered[i]
                
                v_difs = [prev_v.co[0] - v.co[0], prev_v.co[1] - v.co[1], prev_v.co[2] - v.co[2]]
                edge_length = abs(sqrt(v_difs[0] * v_difs[0] + v_difs[1] * v_difs[1] + v_difs[2] * v_difs[2]))
                
                edges_lengths.append(edge_length)
                edges_lengths_sum += edge_length
                
                prev_v = v
        
        return edges_lengths, edges_lengths_sum
    
    
    #### Calculates the proportion of the edges of a chain of edges, relative to the full chain length.
    def get_edges_proportions(self, edges_lengths, edges_lengths_sum, use_boundaries, fixed_edges_num):
        edges_proportions = []
        if use_boundaries:
            verts_count = 1
            for l in edges_lengths:
                edges_proportions.append(l / edges_lengths_sum)
                verts_count += 1
        else:
            verts_count = 1
            for n in range(0, fixed_edges_num):
                edges_proportions.append(1 / fixed_edges_num)
                verts_count += 1
        
        return edges_proportions
    
    
    #### Calculates the angle between two pairs of points in space.
    def orientation_difference(self, points_A_co, points_B_co): # each parameter should be a list with two elements, and each element should be a x,y,z coordinate.
        vec_A = points_A_co[0] - points_A_co[1]
        vec_B = points_B_co[0] - points_B_co[1]
        
        angle = vec_A.angle(vec_B)
        
        if angle > 0.5 * math.pi:
            angle = abs(angle - math.pi)
        
        return angle
        
    
    #### Calculate distance between two points
    def pts_distance(self, p1_co, p2_co):
        p_difs = [p1_co[0] - p2_co[0], p1_co[1] - p2_co[1], p1_co[2] - p2_co[2]]
        distance = abs(sqrt(p_difs[0] * p_difs[0] + p_difs[1] * p_difs[1] + p_difs[2] * p_difs[2]))
        
        return distance
        
    
    def execute(self, context):
        #### Selected edges.
        all_selected_edges_idx = []
        all_selected_verts = []
        all_verts_idx = []
        for ed in self.main_object.data.edges:
            if ed.select:
                all_selected_edges_idx.append(ed.index)
                
                # Selected vertexes.
                if not ed.vertices[0] in all_selected_verts:
                    all_selected_verts.append(self.main_object.data.vertices[ed.vertices[0]])
                if not ed.vertices[1] in all_selected_verts:
                    all_selected_verts.append(self.main_object.data.vertices[ed.vertices[1]])
                    
                # All verts (both from each edge) to determine later which are at the tips (those not repeated twice).
                all_verts_idx.append(ed.vertices[0])
                all_verts_idx.append(ed.vertices[1])
        
        
        #### Identify the tips and "middle-vertex" that separates U from V, if there is one.
        all_chains_tips_idx = []
        for v_idx in all_verts_idx:
            if all_verts_idx.count(v_idx) < 2:
                all_chains_tips_idx.append(v_idx)
        
        edges_connected_to_tips = []
        for ed in self.main_object.data.edges:
            if (ed.vertices[0] in all_chains_tips_idx or ed.vertices[1] in all_chains_tips_idx) and not (ed.vertices[0] in all_verts_idx and ed.vertices[1] in all_verts_idx):
                edges_connected_to_tips.append(ed)
        
        middle_vertex_idx = None
        tips_to_discard_idx = []
        for ed_tips in edges_connected_to_tips:
            for ed_tips_b in edges_connected_to_tips:
                if (ed_tips != ed_tips_b):
                    if ed_tips.vertices[0] in all_verts_idx and (((ed_tips.vertices[1] == ed_tips_b.vertices[0]) or ed_tips.vertices[1] == ed_tips_b.vertices[1])):
                        middle_vertex_idx = ed_tips.vertices[1]
                        tips_to_discard_idx.append(ed_tips.vertices[0])
                    elif ed_tips.vertices[1] in all_verts_idx and (((ed_tips.vertices[0] == ed_tips_b.vertices[0]) or ed_tips.vertices[0] == ed_tips_b.vertices[1])):
                        middle_vertex_idx = ed_tips.vertices[0]
                        tips_to_discard_idx.append(ed_tips.vertices[1])
        
        
        #### List with pairs of verts that belong to the tips of each selection chain (row).
        verts_tips_same_chain_idx = []
        if len(all_chains_tips_idx) >= 2:
            checked_v = []
            for i in range(0, len(all_chains_tips_idx)):
                if all_chains_tips_idx[i] not in checked_v:
                    v_chain = self.get_ordered_verts(self.main_object, all_selected_edges_idx, all_verts_idx, all_chains_tips_idx[i], middle_vertex_idx)
                    
                    verts_tips_same_chain_idx.append([v_chain[0].index, v_chain[len(v_chain) - 1].index])
                    
                    checked_v.append(v_chain[0].index)
                    checked_v.append(v_chain[len(v_chain) - 1].index)
        
        
        #### Selection tips (vertices)
        verts_tips_parsed_idx = []
        if len(all_chains_tips_idx) >= 2:
            for spec_v_idx in all_chains_tips_idx:
                if (spec_v_idx not in tips_to_discard_idx):
                    verts_tips_parsed_idx.append(spec_v_idx)
        
        
        #### Identify the type of selection made by the user.
        if middle_vertex_idx != None:
            if len(all_chains_tips_idx) == 4: # If there are 4 tips (two selection chains)
                selection_type = "TWO_CONNECTED"
            else:
                # The type of the selection was not identified, so the script stops.
                return
        else:
            if len(all_chains_tips_idx) == 2: # If there are 2 tips (one selection chain)
                selection_type = "SINGLE"
            elif len(all_chains_tips_idx) == 4: # If there are 4 tips (two selection chains)
                selection_type = "TWO_NOT_CONNECTED"
            elif len(all_chains_tips_idx) == 0:
                selection_type = "NO_SELECTION"
            else:
                # The type of the selection was not identified, so the script stops.
                return
        
        
        #### Check if it will be used grease pencil strokes or curves.
        selected_objs = bpy.context.selected_objects
        if len(selected_objs) > 1:
            for ob in selected_objs:
                if ob != bpy.context.scene.objects.active:
                    ob_gp_strokes = ob
            using_external_curves = True
            
            bpy.ops.object.editmode_toggle()
        else:
            #### Convert grease pencil strokes to curve.
            bpy.ops.gpencil.convert(type='CURVE')
            ob_gp_strokes = bpy.context.object
            using_external_curves = False
            
            bpy.ops.object.editmode_toggle()
        
        ob_gp_strokes.name = "SURFSK_temp_strokes"
        
        bpy.ops.object.select_name(name = ob_gp_strokes.name)
        bpy.context.scene.objects.active = bpy.context.scene.objects[ob_gp_strokes.name]
        
        
        #### If "Keep strokes" is active make a duplicate of the original strokes, which will be intact
        if bpy.context.scene.SURFSK_keep_strokes:
            bpy.ops.object.duplicate_move()
            bpy.context.object.name = "SURFSK_used_strokes"
            bpy.ops.object.editmode_toggle()
            bpy.ops.curve.smooth()
            bpy.ops.curve.smooth()
            bpy.ops.curve.smooth()
            bpy.ops.curve.smooth()
            bpy.ops.curve.smooth()
            bpy.ops.curve.smooth()
            bpy.ops.object.editmode_toggle()
            
            bpy.ops.object.select_name(name = ob_gp_strokes.name)
            bpy.context.scene.objects.active = bpy.context.scene.objects[ob_gp_strokes.name]
        
        
        #### Enter editmode for the new curve (converted from grease pencil strokes).
        bpy.ops.object.editmode_toggle()
        bpy.ops.curve.smooth()
        bpy.ops.curve.smooth()
        bpy.ops.curve.smooth()
        bpy.ops.curve.smooth()
        bpy.ops.curve.smooth()
        bpy.ops.curve.smooth()
        bpy.ops.object.editmode_toggle()
        
        
        selection_U_exists = False
        selection_U2_exists = False
        selection_V_exists = False
        selection_V2_exists = False
        #### Define what vertexes are at the tips of each selection and are not the middle-vertex.
        if selection_type == "TWO_CONNECTED":
            selection_U_exists = True
            selection_V_exists = True
            
            # Determine which selection is Selection-U and which is Selection-V.
            points_A = []
            points_B = []
            points_first_stroke_tips = []
            
            points_A.append(self.main_object.data.vertices[verts_tips_parsed_idx[0]].co)
            points_A.append(self.main_object.data.vertices[middle_vertex_idx].co)
            
            points_B.append(self.main_object.data.vertices[verts_tips_parsed_idx[1]].co)
            points_B.append(self.main_object.data.vertices[middle_vertex_idx].co)
            
            points_first_stroke_tips.append(ob_gp_strokes.data.splines[0].bezier_points[0].co)
            points_first_stroke_tips.append(ob_gp_strokes.data.splines[0].bezier_points[len(ob_gp_strokes.data.splines[0].bezier_points) - 1].co)
            
            angle_A = self.orientation_difference(points_A, points_first_stroke_tips)
            angle_B = self.orientation_difference(points_B, points_first_stroke_tips)
            
            if angle_A < angle_B:
                first_vert_U_idx = verts_tips_parsed_idx[0]
                first_vert_V_idx = verts_tips_parsed_idx[1]
            else:
                first_vert_U_idx = verts_tips_parsed_idx[1]
                first_vert_V_idx = verts_tips_parsed_idx[0]
                
        elif selection_type == "SINGLE" or selection_type == "TWO_NOT_CONNECTED":
            first_sketched_point_first_stroke_co = ob_gp_strokes.data.splines[0].bezier_points[0].co
            last_sketched_point_first_stroke_co = ob_gp_strokes.data.splines[0].bezier_points[len(ob_gp_strokes.data.splines[0].bezier_points) - 1].co
            
            first_sketched_point_last_stroke_co = ob_gp_strokes.data.splines[len(ob_gp_strokes.data.splines) - 1].bezier_points[0].co
            
            # The tip of the selected vertices nearest to the first point of the first sketched stroke.
            prev_dist = 999999999999
            for i in range(0, len(verts_tips_same_chain_idx)):
                for v_idx in range(0, len(verts_tips_same_chain_idx[i])):
                    dist = self.pts_distance(first_sketched_point_first_stroke_co, self.main_object.data.vertices[verts_tips_same_chain_idx[i][v_idx]].co)
                    if dist < prev_dist:
                        prev_dist = dist
                        
                        nearest_tip_first_st_first_pt_idx = i
                        
                        nearest_tip_first_pair_first_pt_idx = v_idx
                        
                        # Shortest distance to the first point of the first stroke  
                        shortest_distance_to_first_stroke = dist
            
            
            # The tip of the selected vertices nearest to the last point of the first sketched stroke.
            prev_dist = 999999999999
            for i in range(0, len(verts_tips_same_chain_idx)):
                for v_idx in range(0, len(verts_tips_same_chain_idx[i])):
                    dist = self.pts_distance(last_sketched_point_first_stroke_co, self.main_object.data.vertices[verts_tips_same_chain_idx[i][v_idx]].co)
                    if dist < prev_dist:
                        prev_dist = dist
                        
                        nearest_tip_first_st_last_pt_pair_idx = i
                        nearest_tip_first_st_last_pt_point_idx = v_idx
            
            
            # The tip of the selected vertices nearest to the first point of the last sketched stroke.
            prev_dist = 999999999999
            for i in range(0, len(verts_tips_same_chain_idx)):
                for v_idx in range(0, len(verts_tips_same_chain_idx[i])):
                    dist = self.pts_distance(first_sketched_point_last_stroke_co, self.main_object.data.vertices[verts_tips_same_chain_idx[i][v_idx]].co)
                    if dist < prev_dist:
                        prev_dist = dist
                        
                        nearest_tip_last_st_first_pt_pair_idx = i
                        nearest_tip_last_st_first_pt_point_idx = v_idx
            
            
            points_tips = []
            points_first_stroke_tips = []
            
            # Determine if the single selection will be treated as U or as V.
            edges_sum = 0
            for i in all_selected_edges_idx:
                edges_sum += self.pts_distance(self.main_object.data.vertices[self.main_object.data.edges[i].vertices[0]].co, self.main_object.data.vertices[self.main_object.data.edges[i].vertices[1]].co)
            
            average_edge_length = edges_sum / len(all_selected_edges_idx)
            
            
            
            # If the beginning of the first stroke is near enough to interpret things as an "extrude along strokes" instead of "extrude through strokes"
            if shortest_distance_to_first_stroke < average_edge_length / 3:
                selection_U_exists = False
                selection_V_exists = True
                
                first_vert_V_idx = verts_tips_same_chain_idx[nearest_tip_first_st_first_pt_idx][nearest_tip_first_pair_first_pt_idx]
                
                if selection_type == "TWO_NOT_CONNECTED":
                    selection_V2_exists = True
                    
                    first_vert_V2_idx = verts_tips_same_chain_idx[nearest_tip_first_st_last_pt_pair_idx][nearest_tip_first_st_last_pt_point_idx]
                    
                else:
                    selection_V2_exists = False
                
            else:
                selection_U_exists = True
                selection_V_exists = False
                
                points_tips.append(self.main_object.data.vertices[verts_tips_same_chain_idx[nearest_tip_first_st_first_pt_idx][0]].co)
                points_tips.append(self.main_object.data.vertices[verts_tips_same_chain_idx[nearest_tip_first_st_first_pt_idx][1]].co)
                
                points_first_stroke_tips.append(ob_gp_strokes.data.splines[0].bezier_points[0].co)
                points_first_stroke_tips.append(ob_gp_strokes.data.splines[0].bezier_points[len(ob_gp_strokes.data.splines[0].bezier_points) - 1].co)
                
                vec_A = points_tips[0] - points_tips[1]
                vec_B = points_first_stroke_tips[0] - points_first_stroke_tips[1]
                
                # Compare the direction of the selection and the first grease pencil stroke to determine which is the "first" vertex of the selection.
                if vec_A.dot(vec_B) < 0:
                    first_vert_U_idx = verts_tips_same_chain_idx[nearest_tip_first_st_first_pt_idx][1]
                else:
                    first_vert_U_idx = verts_tips_same_chain_idx[nearest_tip_first_st_first_pt_idx][0]
            
                if selection_type == "TWO_NOT_CONNECTED":
                    selection_U2_exists = True
                    
                    first_vert_U2_idx = verts_tips_same_chain_idx[nearest_tip_last_st_first_pt_pair_idx][nearest_tip_last_st_first_pt_point_idx]
                else:
                    selection_U2_exists = False
                
        elif selection_type == "NO_SELECTION":
            selection_U_exists = False
            selection_V_exists = False
        
        
        #### Get an ordered list of the vertices of Selection-U.
        if selection_U_exists:
            verts_ordered_U = self.get_ordered_verts(self.main_object, all_selected_edges_idx, all_verts_idx, first_vert_U_idx, middle_vertex_idx)
            
        #### Get an ordered list of the vertices of Selection-U.
        if selection_U2_exists:
            verts_ordered_U2 = self.get_ordered_verts(self.main_object, all_selected_edges_idx, all_verts_idx, first_vert_U2_idx, middle_vertex_idx)
        
        #### Get an ordered list of the vertices of Selection-V.
        if selection_V_exists:
            verts_ordered_V = self.get_ordered_verts(self.main_object, all_selected_edges_idx, all_verts_idx, first_vert_V_idx, middle_vertex_idx)
        
        #### Get an ordered list of the vertices of Selection-U.
        if selection_V2_exists:
            verts_ordered_V2 = self.get_ordered_verts(self.main_object, all_selected_edges_idx, all_verts_idx, first_vert_V2_idx, middle_vertex_idx)
        
        
        #### Calculate edges U proportions.
        
        # Sum selected edges U lengths.
        edges_lengths_U = []
        edges_lengths_sum_U = 0
        
        if selection_U_exists:
            edges_lengths_U, edges_lengths_sum_U = self.get_chain_length(verts_ordered_U)
        
        # Sum selected edges V lengths.
        edges_lengths_V = []
        edges_lengths_sum_V = 0
        
        if selection_V_exists:
            edges_lengths_V, edges_lengths_sum_V = self.get_chain_length(verts_ordered_V)
        
        bpy.ops.object.editmode_toggle()
        for i in range(0, int(bpy.context.scene.SURFSK_precision)):
          bpy.ops.curve.subdivide()
        bpy.ops.object.editmode_toggle()

        # Proportions U.
        edges_proportions_U = []
        edges_proportions_U = self.get_edges_proportions(edges_lengths_U, edges_lengths_sum_U, selection_U_exists, bpy.context.scene.SURFSK_edges_U)
        verts_count_U = len(edges_proportions_U) + 1
        
        # Proportions V.
        edges_proportions_V = []
        edges_proportions_V = self.get_edges_proportions(edges_lengths_V, edges_lengths_sum_V, selection_V_exists, bpy.context.scene.SURFSK_edges_V)
        verts_count_V = len(edges_proportions_V) + 1
        
        
        
        #### Get ordered lists of points on each sketched curve that mimics the proportions of the edges in the vertex selection.
        sketched_splines = ob_gp_strokes.data.splines
        sketched_splines_lengths = []
        sketched_splines_parsed = []
        for sp_idx in range(0, len(sketched_splines)):
            # Calculate spline length
            sketched_splines_lengths.append(0)
            for i in range(0, len(sketched_splines[sp_idx].bezier_points)):
                if i == 0:
                    prev_p = sketched_splines[sp_idx].bezier_points[i]
                else:
                    p = sketched_splines[sp_idx].bezier_points[i]
                    
                    p_difs = [prev_p.co[0] - p.co[0], prev_p.co[1] - p.co[1], prev_p.co[2] - p.co[2]]
                    edge_length = abs(sqrt(p_difs[0] * p_difs[0] + p_difs[1] * p_difs[1] + p_difs[2] * p_difs[2]))
                    
                    sketched_splines_lengths[sp_idx] += edge_length
                    
                    prev_p = p
            
            # Calculate vertex positions with apropriate edge proportions, and ordered, for each spline.
            sketched_splines_parsed.append([])
            partial_spline_length = 0
            related_edge_U = 0
            edges_proportions_sum_U = 0
            edges_lengths_sum_U = 0
            for i in range(0, len(sketched_splines[sp_idx].bezier_points)):
                if i == 0:
                    prev_p = sketched_splines[sp_idx].bezier_points[i]
                    sketched_splines_parsed[sp_idx].append(prev_p.co)
                elif i != len(sketched_splines[sp_idx].bezier_points) - 1:
                    p = sketched_splines[sp_idx].bezier_points[i]
                    
                    p_difs = [prev_p.co[0] - p.co[0], prev_p.co[1] - p.co[1], prev_p.co[2] - p.co[2]]
                    edge_length = abs(sqrt(p_difs[0] * p_difs[0] + p_difs[1] * p_difs[1] + p_difs[2] * p_difs[2]))
                    
                    
                    if edges_proportions_sum_U + edges_proportions_U[related_edge_U] - ((edges_lengths_sum_U + partial_spline_length + edge_length) / sketched_splines_lengths[sp_idx]) > 0: # comparing proportions to see if the proportion in the selection is found in the spline.
                        partial_spline_length += edge_length
                    elif related_edge_U < len(edges_proportions_U) - 1:
                        sketched_splines_parsed[sp_idx].append(prev_p.co)
                        
                        edges_proportions_sum_U += edges_proportions_U[related_edge_U]
                        related_edge_U += 1
                        
                        edges_lengths_sum_U += partial_spline_length
                        partial_spline_length = edge_length
                    
                    prev_p = p
                else: # last point of the spline for the last edge
                    p = sketched_splines[sp_idx].bezier_points[len(sketched_splines[sp_idx].bezier_points) - 1]
                    sketched_splines_parsed[sp_idx].append(p.co)
        
        
        #### If the selection type is "TWO_NOT_CONNECTED" replace the last point of each spline with the points in the "target" selection.
        if selection_type == "TWO_NOT_CONNECTED":
            if selection_U2_exists:
                for i in range(0, len(sketched_splines_parsed[len(sketched_splines_parsed) - 1])):
                    sketched_splines_parsed[len(sketched_splines_parsed) - 1][i] = verts_ordered_U2[i].co
                
        
        #### Create temporary curves along the "control-points" found on the sketched curves and the mesh selection.
        mesh_ctrl_pts_name = "SURFSK_ctrl_pts"
        me = bpy.data.meshes.new(mesh_ctrl_pts_name)
        ob_ctrl_pts = bpy.data.objects.new(mesh_ctrl_pts_name, me)
        ob_ctrl_pts.data = me
        bpy.context.scene.objects.link(ob_ctrl_pts)
        
        
        for i in range(0, verts_count_U):
            vert_num_in_spline = 1
            
            if selection_U_exists:
                ob_ctrl_pts.data.vertices.add(1)
                last_v = ob_ctrl_pts.data.vertices[len(ob_ctrl_pts.data.vertices) - 1]
                last_v.co = verts_ordered_U[i].co
                
                vert_num_in_spline += 1
                
            for sp in sketched_splines_parsed:
                ob_ctrl_pts.data.vertices.add(1)
                v = ob_ctrl_pts.data.vertices[len(ob_ctrl_pts.data.vertices) - 1]
                v.co = sp[i]
                
                if vert_num_in_spline > 1:
                    ob_ctrl_pts.data.edges.add(1)
                    ob_ctrl_pts.data.edges[len(ob_ctrl_pts.data.edges) - 1].vertices[0] = len(ob_ctrl_pts.data.vertices) - 2
                    ob_ctrl_pts.data.edges[len(ob_ctrl_pts.data.edges) - 1].vertices[1] = len(ob_ctrl_pts.data.vertices) - 1

                last_v = v
                
                vert_num_in_spline += 1

        bpy.ops.object.select_name(name = ob_ctrl_pts.name)
        bpy.context.scene.objects.active = bpy.data.objects[ob_ctrl_pts.name]
        
        
        # Create curves from control points.
        bpy.ops.object.convert(target='CURVE', keep_original=False)
        ob_curves_surf = bpy.context.scene.objects.active
        bpy.ops.object.editmode_toggle()
        bpy.ops.curve.spline_type_set(type='BEZIER')
        bpy.ops.curve.handle_type_set(type='AUTOMATIC')
        for i in range(0, int(bpy.context.scene.SURFSK_precision)):
          bpy.ops.curve.subdivide()
        bpy.ops.object.editmode_toggle()
        
        
        # Calculate the length of each final surface spline.
        surface_splines = ob_curves_surf.data.splines
        surface_splines_lengths = []
        surface_splines_parsed = []
        for sp_idx in range(0, len(surface_splines)):
            # Calculate spline length
            surface_splines_lengths.append(0)
            for i in range(0, len(surface_splines[sp_idx].bezier_points)):
                if i == 0:
                    prev_p = surface_splines[sp_idx].bezier_points[i]
                else:
                    p = surface_splines[sp_idx].bezier_points[i]
                    
                    edge_length = self.pts_distance(prev_p.co, p.co)
                    
                    surface_splines_lengths[sp_idx] += edge_length
                    
                    prev_p = p
        
        bpy.ops.object.editmode_toggle()
        for i in range(0, int(bpy.context.scene.SURFSK_precision)):
          bpy.ops.curve.subdivide()
        bpy.ops.object.editmode_toggle()

        for sp_idx in range(0, len(surface_splines)):
            # Calculate vertex positions with apropriate edge proportions, and ordered, for each spline.
            surface_splines_parsed.append([])
            partial_spline_length = 0
            related_edge_V = 0
            edges_proportions_sum_V = 0
            edges_lengths_sum_V = 0
            for i in range(0, len(surface_splines[sp_idx].bezier_points)):
                if i == 0:
                    prev_p = surface_splines[sp_idx].bezier_points[i]
                    surface_splines_parsed[sp_idx].append(prev_p.co)
                elif i != len(surface_splines[sp_idx].bezier_points) - 1:
                    p = surface_splines[sp_idx].bezier_points[i]
                    
                    edge_length = self.pts_distance(prev_p.co, p.co)
                    
                    if edges_proportions_sum_V + edges_proportions_V[related_edge_V] - ((edges_lengths_sum_V + partial_spline_length + edge_length) / surface_splines_lengths[sp_idx]) > 0: # comparing proportions to see if the proportion in the selection is found in the spline.
                        partial_spline_length += edge_length
                    elif related_edge_V < len(edges_proportions_V) - 1:
                        surface_splines_parsed[sp_idx].append(prev_p.co)
                        
                        edges_proportions_sum_V += edges_proportions_V[related_edge_V]
                        related_edge_V += 1
                        
                        edges_lengths_sum_V += partial_spline_length
                        partial_spline_length = edge_length
                    
                    prev_p = p
                else: # last point of the spline for the last edge
                    p = surface_splines[sp_idx].bezier_points[len(surface_splines[sp_idx].bezier_points) - 1]
                    surface_splines_parsed[sp_idx].append(p.co)
        
        # Set the first and last verts of each spline to the locations of the respective verts in the selections.
        if selection_V_exists:
            for i in range(0, len(surface_splines_parsed[0])):
                surface_splines_parsed[len(surface_splines_parsed) - 1][i] = verts_ordered_V[i].co
        
        if selection_type == "TWO_NOT_CONNECTED":
            if selection_V2_exists:
                for i in range(0, len(surface_splines_parsed[0])):
                    surface_splines_parsed[0][i] = verts_ordered_V2[i].co
        
        
        #### Delete object with control points and object from grease pencil convertion.
        bpy.ops.object.select_name(name = ob_ctrl_pts.name)
        bpy.context.scene.objects.active = bpy.data.objects[ob_ctrl_pts.name]
        bpy.ops.object.delete()
        
        bpy.ops.object.select_name(name = ob_gp_strokes.name)
        bpy.context.scene.objects.active = bpy.data.objects[ob_gp_strokes.name]
        bpy.ops.object.delete()
            
        
        
        #### Generate surface.
        
        # Get all verts coords.
        all_surface_verts_co = []
        for i in range(0, len(surface_splines_parsed)):
            # Get coords of all verts and make a list with them
            for pt_co in surface_splines_parsed[i]:
                all_surface_verts_co.append(pt_co)
        
        
        # Define verts for each face.
        all_surface_faces = []
        for i in range(0, len(all_surface_verts_co) - len(surface_splines_parsed[0])):
            if ((i + 1) / len(surface_splines_parsed[0]) != int((i + 1) / len(surface_splines_parsed[0]))):
                all_surface_faces.append([i+1, i , i + len(surface_splines_parsed[0]), i + len(surface_splines_parsed[0]) + 1])
        
        
        # Build the mesh.
        surf_me_name = "SURFSK_surface"
        me_surf = bpy.data.meshes.new(surf_me_name)
        
        me_surf.from_pydata(all_surface_verts_co, [], all_surface_faces)
        
        me_surf.update()
        
        ob_surface = bpy.data.objects.new(surf_me_name, me_surf)
        bpy.context.scene.objects.link(ob_surface)
        
        
        #### Join the new mesh to the main object.
        ob_surface.select = True
        self.main_object.select = True
        bpy.context.scene.objects.active = bpy.data.objects[self.main_object.name]
        bpy.ops.object.join()
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(limit=0.0001)
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.mesh.select_all(action='DESELECT')
        
        #### Delete grease pencil strokes
        bpy.ops.gpencil.active_frame_delete()
        
        
    def invoke (self, context, event):
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()
        self.main_object = bpy.context.scene.objects.active
        
        self.execute(context)
        
        return {"FINISHED"}




class GPENCIL_OT_surfsk_strokes_to_curves(bpy.types.Operator):
    bl_idname = "gpencil.surfsk_strokes_to_curves"
    bl_label = "Convert grease pencil strokes into curves and enter edit mode"
    bl_description = "Convert grease pencil strokes into curves and enter edit mode"

    def execute(self, context):
        #### Convert grease pencil strokes to curve.
        bpy.ops.gpencil.convert(type='CURVE')
        ob_gp_strokes = bpy.context.object
        ob_gp_strokes.name = "SURFSK_strokes"
        
        #### Delete grease pencil strokes.
        bpy.ops.object.select_name(name = self.main_object.name)
        bpy.context.scene.objects.active = bpy.data.objects[self.main_object.name]
        bpy.ops.gpencil.active_frame_delete()
        
        
        bpy.ops.object.select_name(name = ob_gp_strokes.name)
        bpy.context.scene.objects.active = bpy.data.objects[ob_gp_strokes.name]
        
        
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()
        bpy.ops.curve.smooth()
        bpy.ops.curve.smooth()
        bpy.ops.curve.smooth()
        bpy.ops.curve.smooth()
        bpy.ops.curve.smooth()
        bpy.ops.curve.smooth()
        bpy.ops.curve.smooth()
        bpy.ops.curve.smooth()
        bpy.ops.curve.smooth()
        bpy.ops.curve.smooth()
        bpy.ops.curve.smooth()
        bpy.ops.curve.smooth()
        
        curve_crv = ob_gp_strokes.data
        bpy.ops.curve.spline_type_set(type="BEZIER")
        bpy.ops.curve.handle_type_set(type="AUTOMATIC")
        bpy.data.curves[curve_crv.name].show_handles = False
        bpy.data.curves[curve_crv.name].show_normal_face = False
       
       
    def invoke (self, context, event):
        self.main_object = bpy.context.object
        
        
        self.execute(context)
        
        return {"FINISHED"}


def register():
    bpy.types.Scene.SURFSK_edges_U = bpy.props.IntProperty(name="Cross", description="Number of edge rings crossing the strokes (perpendicular to strokes direction)", default=10, min=0, max=100000)
    bpy.types.Scene.SURFSK_edges_V = bpy.props.IntProperty(name="Follow", description="Number of edge rings following the strokes (parallel to strokes direction)", default=10, min=0, max=100000)
    bpy.types.Scene.SURFSK_precision = bpy.props.IntProperty(name="Precision", description="Precision level of the surface calculation", default=4, min=0, max=100000)
    bpy.types.Scene.SURFSK_keep_strokes = bpy.props.BoolProperty(name="Keep strokes", description="Keeps the sketched strokes after adding the surface", default=False)

    kc = bpy.data.window_managers[0].keyconfigs.default
    km = kc.keymaps.get("3D View")
    if km is None:
        km = kc.keymaps.new(name="3D View")
    keymap_item_add_surf = km.items.new(GPENCIL_OT_surfsk_surface_add.bl_idname,"E","PRESS", key_modifier="D")
    keymap_item_stroke_to_curve = km.items.new(GPENCIL_OT_surfsk_strokes_to_curves.bl_idname,"C","PRESS", key_modifier="D")


def unregister():
    del bpy.types.Scene.SURFSK_edges_U
    del bpy.types.Scene.SURFSK_edges_V
    del bpy.types.Scene.SURFSK_precision
    del bpy.types.Scene.SURFSK_keep_strokes

    kc = bpy.data.window_managers[0].keyconfigs.default
    km = kc.keymaps["3D View"]
    for kmi in km.items:
        if kmi.idname == 'wm.call_menu':
            if kmi.properties.name == GPENCIL_OT_surfsk_surface_add.bl_idname:
                km.items.remove(kmi)
            elif kmi.properties.name == GPENCIL_OT_surfsk_strokes_to_curves.bl_idname:
                km.items.remove(kmi)   
            else:
                continue


if __name__ == "__main__":
    register()

