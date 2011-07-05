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

def line_point_side_v2(l1, l2, pt):
    return (((l1[0] - pt[0]) * (l2[1] - pt[1])) -
            ((l2[0] - pt[0]) * (l1[1] - pt[1])))


def shell_angle_to_dist(angle):
    from math import cos
    return 1.0 if (angle < 0.0001) else abs(1.0 / cos(angle))


def vis_curve_object():
    scene = bpy.data.scenes[0] # weak!
    cu = bpy.data.curves.new(name="Line", type='CURVE')
    ob = bpy.data.objects.new(name="Test", object_data=cu)
    ob.layers = [True] * 20
    base = scene.objects.link(ob)
    return ob


def vis_curve_spline(p1, h1, p2, h2):
    ob = vis_curve_object()
    spline = ob.data.splines.new(type='BEZIER')
    spline.bezier_points.add(1)
    spline.bezier_points[0].co = p1.to_3d()
    spline.bezier_points[1].co = p2.to_3d()

    spline.bezier_points[0].handle_right = h1.to_3d()
    spline.bezier_points[1].handle_left = h2.to_3d()


def vis_circle_object(co, rad=1.0):
    import math
    scene = bpy.data.scenes[0] # weak!
    ob = bpy.data.objects.new(name="Circle", object_data=None)
    ob.rotation_euler.x = math.pi / 2
    ob.location = co.to_3d()
    ob.empty_draw_size = rad
    ob.layers = [True] * 20
    base = scene.objects.link(ob)
    return ob


def visualize_line(p1, p2, p3=None, rad=None):
    pair = p1.to_3d(), p2.to_3d()

    ob = vis_curve_object()
    spline = ob.data.splines.new(type='POLY')
    spline.points.add(1)
    for co, v in zip((pair), spline.points):
        v.co.xyz = co
    
    if p3:
        spline = ob.data.splines.new(type='POLY')
        spline.points[0].co.xyz = p3.to_3d()
        print(rad)
        if rad is not None:
            vis_circle_object(p3, rad)


def treat_points(points,
                 double_limit=0.0001,
                 ):

    # first remove doubles
    tot_len = 0.0
    if double_limit != 0.0:
        i = len(points) - 1
        while i > 0:
            length = (points[i] - points[i - 1]).length
            if length < double_limit:
                del points[i]
                if i >= len(points):
                    i -= 1
            else:
                tot_len += length
                i -= 1
    return tot_len


def solve_curvature_2d(p1, p2, n1, n2, fac, fallback):
    """ Add a nice circular curvature on 
    """
    from mathutils import Vector
    from mathutils.geometry import (barycentric_transform,
                                    intersect_line_line,
                                    intersect_point_line,
                                    )

    p1_a = p1 + n1
    p2_a = p2 - n2

    isect = intersect_line_line(p1.to_3d(),
                                p1_a.to_3d(),
                                p2.to_3d(),
                                p2_a.to_3d(),
                                )

    if isect:
        corner = isect[0]
    else:
        corner = None

    if corner:
        corner = corner.xy
        p1_first_order = p1.lerp(corner, fac)
        p2_first_order = corner.lerp(p2, fac)
        co = p1_first_order.lerp(p2_first_order, fac)
        
        return co.xy
    else:
        # cant interpolate. just return interpolated value
        return fallback.copy() # p1.lerp(p2, fac)


def points_to_bezier(points_orig,
                     double_limit=0.0001,
                     kink_tolerance=0.25,
                     bezier_tolerance=0.1,  # error distance, scale dependant
                     subdiv=8,
                     angle_span=0.95,  # 1.0 tries to evaluate splines of 180d
                     ):

    import math
    from mathutils import Vector

    class Point(object):
        __slots__ = ("co",
                     "angle",
                     "no",
                     "is_joint",
                     "next",
                     "prev",
                     )

        def __init__(self, co):
            self.co = co
            self.is_joint = False

        def calc_angle(self):
            if self.prev is None or self.next is None:
                self.angle = 0.0
            else:
                va = self.co - self.prev.co
                vb = self.next.co - self.co
                self.angle = va.angle(vb, 0.0)
                
                # XXX 2D
                if line_point_side_v2(self.prev.co,
                                      self.co,
                                      self.next.co,
                                      ) < 0.0:

                    self.angle = -self.angle

        def angle_diff(self):
            """ use for detecting joints, detect difference in angle from
                surrounding points.
            """
            if self.prev is None or self.next is None:
                return 0.0
            else:
                if (self.angle > self.prev.angle and
                            self.angle > self.next.angle):
                    return abs(self.angle - self.prev.angle) / math.pi
                else:
                    return 0.0
        
        def angle_filter(self):
            tot = 1
            a = self.angle
            if self.prev:
                tot += 1
                a += self.prev.angle

            if self.next:
                tot += 1
                a += self.next.angle
            
            a = a / tot
            return 0.0 if abs(a) < 0.01 else a
        
        def calc_normal(self):
            v1 = v2 = None
            if self.prev and not self.prev.is_joint:
                v1 = (self.co - self.prev.co).normalized()
            if self.next and not self.next.is_joint:
                v2 = (self.next.co - self.co).normalized()
            
            if v1 and v2:
                self.no = (v1 + v2).normalized()
            elif v1:
                self.no = v1
            elif v2:
                self.no = v2
            else:
                print("Warning, assigning dummy normal")
                self.no = Vector(0, 1)


    class Spline(object):
        __slots__ = ("points",
                     "handle_left",
                     "handle_right",
                     "next",
                     "prev",
                     )

        def __init__(self, points):
            self.points = points

        def link_points(self):

            if hasattr(self.points[0], "prev"):
                raise Exception("already linked")

            p_prev = None
            for p in self.points:
                p.prev = p_prev
                p_prev = p

            p_prev = None
            for p in reversed(self.points):
                p.next = p_prev
                p_prev = p

        def split(self, i, is_joint=False):
            prev = self.prev
            next = self.next

            if is_joint:
                self.points[i].is_joint = True

            # share a point
            spline_a = Spline(self.points[:i + 1])
            spline_b = Spline(self.points[i:])

            # invalidate self, dont reuse!
            self.points = None
            
            spline_a.next = spline_b
            spline_b.prev = spline_a
    
            spline_a.prev = prev
            spline_b.next = next
            if prev:
                prev.next = spline_a
            if next:
                next.prev = spline_b

            return spline_a, spline_b

        def calc_angle(self):
            for p in self.points:
                p.calc_angle()

        def calc_normal(self):
            for p in self.points:
                p.calc_normal()

        def calc_all(self):
            self.link_points()
            self.calc_angle()
            self.calc_normal()

        def total_angle(self):
            return abs(sum((p.angle for p in self.points)))

        def redistribute(self, segment_length, smooth=False):
            if len(self.points) == 1:
                return

            from mathutils.geometry import intersect_line_sphere_2d

            p_line = p = self.points[0]
            points = [(p.co.copy(), p.co.copy())]
            p = p.next

            def point_add(co, p=None):
                co = co.copy()
                co_smooth = co.copy()

                if smooth:
                    if p is None:
                        pass # works ok but no smoothing
                    elif (p.prev.no - p.no).length < 0.001:
                        pass # normals are too similar, paralelle
                    elif (p.angle > 0.0) != (p.prev.angle > 0.0):
                        pass
                    else:
                        # visualize_line(p.co, p.co + p.no)
                        
                        # this assumes co is on the line
                        fac = ((p.prev.co - co).length /
                               (p.prev.co - p.co).length)

                        assert(fac >= 0.0 and fac <= 1.0)

                        co_smooth = solve_curvature_2d(p.prev.co,
                                                       p.co,
                                                       p.prev.no,
                                                       p.no,
                                                       fac,
                                                       co,
                                                       )

                points.append((co, co_smooth))

            def point_step(p):
                if p.is_joint or p.next is None:
                    point_add(p.co)
                    return None
                else:
                    return p.next

            print("START")
            while p:
                # we want the first pont past the segment size
                
                #if p.is_joint:
                #    vis_circle_object(p.co)

                length = (points[-1][0] - p.co).length
                
                if abs(length - segment_length) < 0.00001:
                    # close enough to be considered on the circle bounds
                    point_add(p.co)
                    p_line = p
                    p = point_step(p)
                elif length < segment_length:
                    p = point_step(p)
                else:
                    # the point is further then the segment width
                    p_start = points[-1][0] if p.prev is p_line else p.prev.co
                    
                    if (p_start - points[-1][0]).length > segment_length:
                        raise Exception("eek2")
                    if (p.co - points[-1][0]).length < segment_length:
                        raise Exception("eek3")

                    # print(p_start, p.co, points[-1][0], segment_length)
                    i1, i2 = intersect_line_sphere_2d(p_start,
                                                      p.co,
                                                      points[-1][0],
                                                      segment_length,
                                                      )
                    # print()
                    # print(i1, i2)
                    # assert(i1 is not None)
                    if i1 is not None:
                        point_add(i1, p)
                        p_line = p.prev
                    elif i2:
                        raise Exception("err")
                    
                    
                    elif i1 is None and i2 is None:
                        visualize_line(p_start,
                                       p.co,
                                       points[-1][0],
                                       segment_length,
                                       )

                        # XXX FIXME
                        # raise Exception("BAD!s")
                        point_add(p.co)
                        p_line = p
                        p = point_step(p)
                
            joint = self.points[0].is_joint, self.points[-1].is_joint

            self.points = [Point(p[1]) for p in points]

            self.points[0].is_joint, self.points[-1].is_joint = joint
            
            self.calc_all()
            # raise Exception("END")

        def bezier_solve(self):
            """ Calculate bezier handles,
                assume the splines have been broken up.

                
            """

            from mathutils.geometry import (intersect_point_line,
                                            intersect_line_line,
                                            )

            # get a line
            p1 = self.points[0]
            p2 = self.points[-1]

            # since we have even spacing we can just pick the middle point
            # p_mid = self.points[len(self.points) // 2]

            # vec, fac = mathutils.geometry.intersect_point_line(m_mid, p1, p2)
            

            # TODO, ensure < 180d curves
            
            p1_a, p1_b = p1.co, p1.co + p1.no
            p2_a, p2_b = p2.co, p2.co - p2.no

            isect = intersect_line_line(p1_a.to_3d(),
                                        p1_b.to_3d(),
                                        p2_a.to_3d(),
                                        p2_b.to_3d(),
                                        )


            if isect is None:
                # if isect is None, the line is paralelle
                # just add simple handles
                self.bezier_h1 = p1.co.lerp(p2.co, 1.0 / 3.0)
                self.bezier_h2 = p2.co.lerp(p1.co, 1.0 / 3.0)
                return

            corner = isect[0].xy

            p_mid = p1.co.lerp(p2.co, 0.5)
            dist_best = 10000000.0
            p_best = None
            side = (line_point_side_v2(p_mid, corner, p1.co) < 0.0)
            ok = False
            for p_apex in self.points:
                if (line_point_side_v2(p_mid,
                                       corner,
                                       p_apex.co,
                                       ) < 0.0) != side:

                    # find the exact point on the line between the apex and
                    # the middle
                    p_test_1 = intersect_point_line(p_apex.co,
                                                    p_mid,
                                                    corner)[0].xy
                    p_test_2 = intersect_point_line(p_apex.prev.co,
                                                    p_mid,
                                                    corner)[0].xy
                    
                    w1 = (p_test_1 - p_apex.co).length
                    w2 = (p_test_2 - p_apex.prev.co).length
                    fac = w1 / (w1 + w2)
                    
                    p_apex_co = p_apex.co.lerp(p_apex.prev.co, fac)
                    p_apex_no = p_apex.no.lerp(p_apex.prev.no, fac)
                    p_apex_no.normalize()
                    
                    # visualize_line(p_mid.to_3d(), corner.to_3d())
                    # visualize_line(p_apex.co.to_3d(), p_apex_co.to_3d())

                    ok = True
                    break

            del p_apex, w1, w2, fac, p_test_1, p_test_2

            assert(ok == True)

            v1 = (p2.co - p1.co).normalized()
            v2 = p_apex_no.copy()
            
            # find the point on the line which aligns with the apex point.
            # first place handles, must be distance to apex * 1.333...
            if 1:
                p_mid_apex_align = intersect_point_line(p_apex_co,
                                                        p1.co,
                                                        p2.co)[0]
            else:
                p_mid_apex_align = p_mid

            # visualize_line(p_mid_apex_align.to_3d(), p_apex_co.to_3d())

            # The point is always 75% of the handle distance
            # here we extend the distance from the line to the curve apex
            # by 33.33..% to compensate for this.
            h_sca = 1 # (p_apex_co - p_mid_apex_align.xy).length / 0.75


            from math import pi

            # -1.0 - 1.0
            bias = v1.angle(v2) / (pi / 2)
            print(bias)
            if abs(bias) < 0.001:
                h_sca_1 = h_sca
                h_sca_2 = h_sca
            elif line_point_side_v2(Vector((0.0, 0.0)), v2, v1) < 0:
                h_sca_1 = h_sca / (1.0 + bias)
                h_sca_2 = h_sca * (1.0 + bias)
            else:
                h_sca_1 = h_sca * (1.0 + bias)
                h_sca_2 = h_sca / (1.0 + bias)


            # find the factor 
            fac = intersect_point_line(p_apex_co, p_mid, corner)[1]
            # assert(fac >= 0.0)

            h_sca_1 = 1
            h_sca_2 = 1

            h1 = p1.co.lerp(corner, (fac / 0.75) * h_sca_1)
            h2 = p2.co.lerp(corner, (fac / 0.75) * h_sca_2)


            # rare cases this can mess up, because of almost straight lines
    

            # good for debugging single splines
            # vis_curve_spline(p1.co, h1, p2.co, h2)
            
            
            self.handle_left = h1
            self.handle_right = h2

        def bezier_error(self):
            from mathutils.geometry import interpolate_bezier

            test_points = interpolate_bezier(self.points[0].co.to_3d(),
                                             self.handle_left,
                                             self.handle_right,
                                             self.points[-1].co.to_3d(),
                                             8,
                                             )

            from mathutils.geometry import intersect_point_line

            error = 0.0

            # this is a rough method measuring the error but should be good enough
            # TODO. dont test against every single point.
            for co in test_points:
                co = co.xy
                # initial values
                co_best = self.points[0].co

                length_best = (co - co_best).length
                for p in self.points[1:]:
                    # dist to point
                    length = (co - p.co).length
                    if length < length_best:
                        length_best = length
                        co_best = p.co
                    
                    p_ix, fac = intersect_point_line(co, p.co, p.prev.co)
                    p_ix = p_ix.xy
                    if fac >= 0.0 and fac <= 1.0:
                        length = (co - p_ix).length
                        if length < length_best:
                            length_best = length
                            co_best = p_ix
                
                error += length_best

            return error

    class Curve(object):
        __slots__ = ("splines",
                     )

        def __init__(self, splines):
            self.splines = splines

        def link_splines(self):
            s_prev = None
            for s in self.splines:
                s.prev = s_prev
                s_perv = s

            s_prev = None
            for s in reversed(self.splines):
                s.next = s_prev
                s_perv = s

        def calc_data(self):
            for s in self.splines:
                s.calc_all()

            self.link_splines()

        def split_func_map_point(self, func, is_joint=False):
            """ func takes a point and returns true on split

                return True if any splits are made.
            """
            s_index = 0
            s = self.splines[s_index]
            while s:
                assert(self.splines[s_index] == s)
                
                for i, p in enumerate(s.points):

                    if i == 0 or i >= len(s.points) - 1:
                        continue

                    if func(p):
                        split_pair = s.split(i, is_joint=is_joint)
                        # keep list in sync
                        self.splines[s_index:s_index + 1] = split_pair
                        
                        # advance on main while loop
                        s = split_pair[0]
                        assert(self.splines[s_index] == s)
                        break

                s = s.next
                s_index += 1


        def split_func_spline(self, func, is_joint=False, recursive=False):
            """ func takes a spline and returns the point index on split or -1

                return True if any splits are made.
            """
            s_index = 0
            s = self.splines[s_index]
            while s:
                assert(self.splines[s_index] == s)
                
                i = func(s)

                if i != -1:
                    split_pair = s.split(i, is_joint=is_joint)
                    # keep list in sync
                    self.splines[s_index:s_index + 1] = split_pair

                    # advance on main while loop
                    s = split_pair[0]
                    assert(self.splines[s_index] == s)
                    
                    if recursive:
                        continue

                s = s.next
                s_index += 1

        def validate(self):
            s_prev = None
            iii = 0
            for s in self.splines:
                print(iii)
                assert(s.prev == s_prev)
                if s_prev:
                    print()
                    assert(s_prev.next == s)
                s_prev = s
                iii += 1

        def redistribute(self, segment_length, smooth=False):
            for s in self.splines:
                s.redistribute(segment_length, smooth)

        def to_blend_data(self):
            """ Points to blender data, debugging only
            """
            scene = bpy.data.scenes[0] # weak!
            for base in scene.object_bases:
                base.select = False
            cu = bpy.data.curves.new(name="Test", type='CURVE')
            for s in self.splines:
                spline = cu.splines.new(type='POLY')
                spline.points.add(len(s.points) - 1)
                for p, v in zip(s.points, spline.points):
                    v.co.xy = p.co
                    
            
            
            ob = bpy.data.objects.new(name="Test", object_data=cu)
            ob.layers = [True] * 20
            base = scene.objects.link(ob)
            scene.objects.active = ob
            base.select = True
            # base.layers = [True] * 20
            print(ob, "Done")
        
        def to_blend_curve(self, cu=None, cu_matrix=None):
            """ return new bezier spline datablock or add to an existing
            """
            if not cu:
                cu = bpy.data.curves.new(name="Curve", type='CURVE')

            spline = cu.splines.new(type='BEZIER')
            spline.bezier_points.add(len(self.splines))

            s_prev = None
            for i, bp in enumerate(spline.bezier_points):
                if i < len(self.splines):
                    s = self.splines[i]
                else:
                    s = None

                if s_prev and s:
                    pt = s.points[0]
                    hl = s_prev.handle_right
                    hr = s.handle_left
                elif s:
                    pt = s.points[0]
                    hr = s.handle_left
                    hl = (pt.co.xy + (pt.co.xy - hr.xy))
                elif s_prev:
                    pt = s_prev.points[-1]
                    hl = s_prev.handle_right
                    hr = (pt.co.xy + (pt.co.xy - hl.xy))
                else:
                    assert(0)

                bp.co.xy = pt.co
                bp.handle_left.xy = hl
                bp.handle_right.xy = hr

                handle_type = 'FREE'

                if pt.is_joint == False or (s_prev and s) == False:
                    
                    # XXX, this should not happen, but since it can 
                    # at least dont allow allignment to break the curve output
                    if (pt.co - hl).angle(hr - pt.co, 0.0) < 0.1:

                        handle_type = 'ALIGNED'

                bp.handle_left_type = bp.handle_right_type = handle_type
                s_prev = s

            scene = bpy.data.scenes[0] # weak!
            ob = bpy.data.objects.new(name="Test", object_data=cu)
            ob.layers = [True] * 20
            base = scene.objects.link(ob)
            scene.objects.active = ob
            base.select = True

            return cu
            
            



    points = list(points_orig)
    
    # remove doubles
    tot_length = treat_points(points)

    # calculate segment spacing
    segment_length = (tot_length / len(points)) / subdiv 


    curve = Curve([Spline([Point(p) for p in points])])

    curve.calc_data()

    if kink_tolerance != 0.0:
        pass

    curve.split_func_map_point(lambda p: p.angle_diff() > kink_tolerance,
                               is_joint=True,
                               )

    # return
    # curve.validate()

    curve.redistribute(segment_length / 4.0, smooth=True)
    curve.redistribute(segment_length, smooth=False)

    def swap_side(p):
        angle = p.angle_filter()
        if p.prev.prev is None:
            swap_side.last = angle
        else:
            if (swap_side.last > 0.0) != (angle > 0.0):
                if abs(p.angle) > 0.025:
                    swap_side.last = p.angle
                    return True

        return False


    #curve.split_func_map_point(lambda p: (p.angle_filter() >= 0) != \
    #                              (p.prev.angle_filter() >= 0))
    curve.split_func_map_point(swap_side)


    # now split based on total spline angle.
    import math
    angle_span_rad = angle_span * math.pi
    curve.split_func_spline(lambda s:
                                len(s.points) // 2
                                if (s.total_angle() > angle_span_rad and
                                    len(s.points) > 2)
                                else -1,
                            recursive=True,
                            )


    curve.split_func_spline(lambda s:
                                len(s.points) // 2
                                if ((s.bezier_solve(), s.bezier_error())[1] >
                                     bezier_tolerance) and (len(s.points) > 2)
                                else -1,
                            recursive=True,
                            )
    
    '''
    for s in curve.splines:
        s.bezier_solve()
        print(s.bezier_error())
    '''
    # VISUALIZE
    # curve.to_blend_data()
    curve.to_blend_curve()


if __name__ == "__main__":
    print("A")
    bpy.ops.wm.open_mainfile(filepath="/root/curve_test.blend")
    
    ob = bpy.data.objects["Curve"]
    points = [p.co.xy for s in ob.data.splines for p in s.points]

    print("points_to_bezier 1")
    points_to_bezier(points)
    print("points_to_bezier 2")

    bpy.ops.wm.save_as_mainfile(filepath="/root/curve_test_edit.blend",
                                copy=True)
    print("done!")

