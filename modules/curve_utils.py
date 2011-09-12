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


def vis_curve_object():
    scene = bpy.data.scenes[0]  # weak!
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
    scene = bpy.data.scenes[0]  # weak!
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


def solve_curvature(p1, p2, n1, n2, fac, fallback):
    """ Add a nice circular curvature on
    """
    from mathutils.geometry import (intersect_line_line,
                                    )

    p1_a = p1 + n1
    p2_a = p2 - n2

    isect = intersect_line_line(p1,
                                p1_a,
                                p2,
                                p2_a,
                                )

    if isect:
        corner = isect[0].lerp(isect[1], 0.5)
    else:
        corner = None

    if corner:
        p1_first_order = p1.lerp(corner, fac)
        p2_first_order = corner.lerp(p2, fac)
        co = p1_first_order.lerp(p2_first_order, fac)

        return co
    else:
        # cant interpolate. just return interpolated value
        return fallback.copy()  # p1.lerp(p2, fac)


def points_to_bezier(points_orig,
                     double_limit=0.0001,
                     kink_tolerance=0.25,
                     bezier_tolerance=0.05,  # error distance, scale dependant
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
                self.no = Vector((0.0, 1, 0.0))

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

        #~ def total_angle(self):
            #~ return abs(sum((p.angle for p in self.points)))

        def redistribute(self, segment_length, smooth=False):
            if len(self.points) == 1:
                return

            from mathutils.geometry import intersect_line_sphere

            p_line = p = self.points[0]
            points = [(p.co.copy(), p.co.copy())]
            p = p.next

            def point_add(co, p=None):
                co = co.copy()
                co_smooth = co.copy()

                if smooth:
                    if p is None:
                        pass  # works ok but no smoothing
                    elif (p.prev.no - p.no).length < 0.001:
                        pass  # normals are too similar, paralelle
                    elif (p.angle > 0.0) != (p.prev.angle > 0.0):
                        pass
                    else:
                        # visualize_line(p.co, p.co + p.no)

                        # this assumes co is on the line
                        fac = ((p.prev.co - co).length /
                               (p.prev.co - p.co).length)

                        assert(fac >= 0.0 and fac <= 1.0)

                        co_smooth = solve_curvature(p.prev.co,
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
                    i1, i2 = intersect_line_sphere(p_start,
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

        def intersect_line(self, l1, l2, reverse=False):
            """ Spectial kind of intersection, works in 3d on the plane
                defimed by the points normal and the line.
            """

            from mathutils.geometry import (intersect_point_line,
                                            )

            if reverse:
                p_first = self.points[-1]
                no = -self.points[-1].no
                point_iter = reversed(self.points[:-1])
            else:
                p_first = self.points[0]
                no = self.points[0].no
                point_iter = self.points[1:]

            # calculate the line right angles to the line
            bi_no = (no - no.project(l2 - l1)).normalized()

            bi_l1 = p_first.co
            bi_l2 = p_first.co + bi_no

            for p_apex in point_iter:
                ix, fac = intersect_point_line(p_apex.co, bi_l1, bi_l2)

                if fac < 0.0001:

                    if reverse:
                        p_apex_other = p_apex.next
                    else:
                        p_apex_other = p_apex.prev

                    # find the exact point on the line between the apex and
                    # the middle
                    p_test_1 = intersect_point_line(p_apex.co,
                                                    l1,
                                                    l2)[0]
                    p_test_2 = intersect_point_line(p_apex_other.co,
                                                    l1,
                                                    l2)[0]

                    w1 = (p_test_1 - p_apex.co).length
                    w2 = (p_test_2 - p_apex_other.co).length

                    #assert(w1 + w2 != 0)
                    try:
                        fac = w1 / (w1 + w2)
                    except ZeroDivisionError:
                        fac = 0.5
                    assert(fac >= 0.0 and fac <= 1.0)

                    p_apex_co = p_apex.co.lerp(p_apex_other.co, fac)
                    p_apex_no = p_apex.no.lerp(p_apex_other.no, fac)
                    p_apex_no.normalize()

                    # visualize_line(p_mid.to_3d(), corner.to_3d())
                    # visualize_line(p_apex.co.to_3d(), p_apex_co.to_3d())

                    return p_apex_co, p_apex_no, p_apex

            # intersection not found
            return None, None, None


        @staticmethod
        def bez_solve(p0, p1, p2, p3, u, v):
            ui = 1.0 - u
            vi = 1.0 - v
            u_p3 = u * u * u
            v_p3 = v * v * v
            ui_p3 = ui * ui * ui
            vi_p3 = vi * vi * vi

            a = 3.0 * ui * ui * u
            b = 3.0 * ui * u * u
            c = 3.0 * vi * vi * v
            d = 3.0 * vi * v * v
            det = a * d - b * c

            if det == 0.0:
                assert(0)
                return 0

            q1 = p1 - (ui_p3 * p0 + u_p3 * p3)
            q2 = p2 - (vi_p3 * p0 + v_p3 * p3)

            return ((d * q1 - b * q2) / det,
                    (-c * q1 + a * q2) / det
                    )

        def bezier_solve__math1(self):
            """ Calculate bezier handles,
                assume the splines have been broken up.

                http://polymathprogrammer.com/
            """

            def get(f, min=0.0, max=1.0):
                f = (f * (max - min) + min)
                return self.points[int((len(self.points) - 1) * f)].co
            
            
            p1 = get(0.0)
            p2 = get(1.0)
            i1 = get(1/3)
            i2 = get(2/3)

            pos = __class__.bez_solve(p1, i1, i2, p2, 1.0 / 3.0, 2.0 / 3.0)
            self.handle_left = self.points[0].co + (pos[0] - self.points[0].co)
            self.handle_right = self.points[-1].co + (pos[1] - self.points[-1].co)
        
        def bezier_solve__math2(self):

            def get(f, min=0.0, max=1.0):
                f = (f * (max - min) + min)
                return self.points[int((len(self.points) - 1) * f)].co

            p1 = get(0.0, min=0.0, max=0.5)
            p2 = get(1.0, min=0.0, max=0.5)
            i1 = get(1/3, min=0.0, max=0.5)
            i2 = get(2/3, min=0.0, max=0.5)
            
            pos_a = __class__.bez_solve(p1, i1, i2, p2, 1.0 / 3.0, 2.0 / 3.0)
            
            p1 = get(0.0, min=0.5, max=1.0)
            p2 = get(1.0, min=0.5, max=1.0)
            i1 = get(1/3, min=0.5, max=1.0)
            i2 = get(2/3, min=0.5, max=1.0)
            
            pos_b = __class__.bez_solve(p1, i1, i2, p2, 1.0 / 3.0, 2.0 / 3.0)

            self.handle_left = self.points[0].co + (pos_a[0] - self.points[0].co) * 2
            self.handle_right = self.points[-1].co + (pos_b[1] - self.points[-1].co) * 2

        def bezier_solve__inkscape(self):
                        
            # static void
            # estimate_bi(Point bezier[4], unsigned const ei,
            #             Point const data[], double const u[], unsigned const len)
            def estimate_bi(bezier, ei, data, u):

                def B0(u): return ( ( 1.0 - u )  *  ( 1.0 - u )  *  ( 1.0 - u ) )
                def B1(u): return ( 3 * u  *  ( 1.0 - u )  *  ( 1.0 - u ) )
                def B2(u): return ( 3 * u * u  *  ( 1.0 - u ) )
                def B3(u): return ( u * u * u )

                # assert( not (1 <= ei and ei <= 2))
                oi = 3 - ei
                num = [0.0, 0.0, 0.0]
                den = 0.0
                
                for i in range(len(data)):
                    ui = u[i];
                    b = [
                        B0(ui),
                        B1(ui),
                        B2(ui),
                        B3(ui)
                    ]

                    for d in range(3):
                        num[d] += (b[ei] * (b[0]  * bezier[0][d] +
                                           b[oi] * bezier[oi][d] +
                                           b[3]  * bezier[3][d] +
                                           - data[i][d]))

                    den -= b[ei] * b[ei]

                if den:
                    for d in range(3):
                        bezier[ei][d] = num[d] / den
                else:
                    bezier[ei] = (oi * bezier[0] + ei * bezier[3]) / 3.0
            bezier = [
                self.points[0].co,
                self.points[0].co.lerp(self.points[-1].co, 1/3),
                self.points[0].co.lerp(self.points[-1].co, 2/3),
                self.points[-1].co,
            ]
            data = [p.co for p in self.points]
            u = [i / len(self.points) for i in range(len(self.points))]
            estimate_bi(bezier, 1, data, u)
            estimate_bi(bezier, 2, data, u)
            estimate_bi(bezier, 1, data, u)
            estimate_bi(bezier, 2, data, u)
            estimate_bi(bezier, 1, data, u)
            estimate_bi(bezier, 2, data, u)
            estimate_bi(bezier, 1, data, u)
            estimate_bi(bezier, 2, data, u)
            
            self.handle_left = bezier[1]
            self.handle_right = bezier[2]

        def bezier_solve_ideasman42(self):
            from mathutils.geometry import (intersect_point_line,
                                            intersect_line_line,
                                            )

            # get a line
            p1 = self.points[0]
            p2 = self.points[-1]

            # ------
            # take 2
            p_vec = (p2.co - p1.co).normalized()

            # vector between line and point directions
            l1_no = (p1.no + p_vec).normalized()
            l2_no = ((-p2.no) - p_vec).normalized()

            l1_co = p1.co + l1_no
            l2_co = p2.co + l2_no

            # visualize_line(p1.co, l1_co)
            # visualize_line(p2.co, l2_co)

            line_ix_p1_co, line_ix_p1_no, line_ix_p1 = \
                    self.intersect_line(p1.co,
                                        l1_co,
                                        )
            line_ix_p2_co, line_ix_p2_no, line_ix_p2 = \
                    self.intersect_line(p2.co,
                                        l2_co,
                                        reverse=True,
                                        )
            if line_ix_p1_co is None:
                line_ix_p1_co, line_ix_p1_no, line_ix_p1 = \
                        p1.next.co, p1.next.no, p1.next
            if line_ix_p2_co is None:
                line_ix_p2_co, line_ix_p2_no, line_ix_p2 = \
                        p2.prev.co, p2.prev.no, p2.prev

            # vis_circle_object(line_ix_p1_co)
            # vis_circle_object(line_ix_p2_co)

            l1_max = 0.0
            p1_apex_co = None
            p = self.points[1]
            while p and (not p.is_joint) and p != line_ix_p1:
                ix = intersect_point_line(p.co, p1.co, l1_co)[0]
                length = (ix - p.co).length
                if length > l1_max:
                    l1_max = length
                    p1_apex_co = p.co
                p = p.next

            l2_max = 0.0
            p2_apex_co = None
            p = self.points[-2]
            while p and (not p.is_joint) and p != line_ix_p2:
                ix = intersect_point_line(p.co, p2.co, l2_co)[0]
                length = (ix - p.co).length
                if length > l2_max:
                    l2_max = length
                    p2_apex_co = p.co
                p = p.prev

            if p1_apex_co is None:
                p1_apex_co = p1.next.co
            if p2_apex_co is None:
                p2_apex_co = p2.prev.co

            l1_tan = (p1.no - p1.no.project(l1_no)).normalized()
            l2_tan = -(p2.no - p2.no.project(l2_no)).normalized()

            # values are good!
            visualize_line(p1.co, p1.co + l1_tan)
            visualize_line(p2.co, p2.co + l2_tan)

            visualize_line(p1.co, p1.co + l1_no)
            visualize_line(p2.co, p2.co + l2_no)

            # calculate bias based on the position of the other point allong
            # the tangent.

            # first need to reflect the second normal for angle comparison
            # first fist need the reflection normal
            
            # angle between - 0 - 1
            from math import pi
            no_ref = p_vec.cross(p2.no).cross(p_vec).normalized()
            l2_no_ref = p2.no.reflect(no_ref).normalized()
            no_angle = p1.no.angle(l2_no_ref) / pi
            del no_ref

            # This could be tweaked but seems to work well

            # fac_fac = 1.0

            print("angle", "%.6f" % no_angle)

            fac_1 = intersect_point_line(p2_apex_co,
                                         p1.co,
                                         p1.co + l1_tan * (p1.co - p1_apex_co).length,
                                         )[1] * (1.0 + no_angle)
            fac_2 = intersect_point_line(p1_apex_co,
                                         p2.co,
                                         p2.co + l2_tan * (p2.co - p2_apex_co).length,
                                         )[1] * (1.0 + no_angle)

            h1_fac = abs(fac_1)
            h2_fac = abs(fac_2)

            h1 = p1.co + (p1.no * h1_fac)
            h2 = p2.co - (p2.no * h2_fac)

            self.handle_left = h1
            self.handle_right = h2

            '''
            visualize_line(p1.co, p1_apex_co)
            visualize_line(p1_apex_co, p2_apex_co)
            visualize_line(p2.co, p2_apex_co)
            visualize_line(p1.co, p2.co)
            '''

        def bezier_solve(self):
            return self.bezier_solve__inkscape()

        def bezier_error(self, error_max=-1.0, test_count=8):
            from mathutils.geometry import interpolate_bezier

            test_points = interpolate_bezier(self.points[0].co,
                                             self.handle_left,
                                             self.handle_right,
                                             self.points[-1].co,
                                             test_count,
                                             )

            from mathutils.geometry import intersect_point_line

            error = 0.0

            # this is a rough method measuring the error but should be ok
            # TODO. dont test against every single point.
            for co in test_points:
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
                    p_ix = p_ix
                    if fac >= 0.0 and fac <= 1.0:
                        length = (co - p_ix).length
                        if length < length_best:
                            length_best = length
                            co_best = p_ix

                error += length_best / test_count

                if error_max != -1.0 and error > error_max:
                    return True

            if error_max != -1.0:
                return False
            else:
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
                assert(s.prev == s_prev)
                if s_prev:
                    assert(s_prev.next == s)
                s_prev = s
                iii += 1

        def redistribute(self, segment_length, smooth=False):
            for s in self.splines:
                s.redistribute(segment_length, smooth)

        def to_blend_data(self):
            """ Points to blender data, debugging only
            """
            scene = bpy.data.scenes[0]  # weak!
            for base in scene.object_bases:
                base.select = False
            cu = bpy.data.curves.new(name="Test", type='CURVE')
            for s in self.splines:
                spline = cu.splines.new(type='POLY')
                spline.points.add(len(s.points) - 1)
                for p, v in zip(s.points, spline.points):
                    v.co.xyz = p.co

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
                    hl = (pt.co + (pt.co - hr))
                elif s_prev:
                    pt = s_prev.points[-1]
                    hl = s_prev.handle_right
                    hr = (pt.co + (pt.co - hl))
                else:
                    assert(0)

                bp.co.xyz = pt.co
                bp.handle_left.xyz = hl
                bp.handle_right.xyz = hr

                handle_type = 'FREE'

                if pt.is_joint == False or (s_prev and s) == False:

                    # XXX, this should not happen, but since it can
                    # at least dont allow allignment to break the curve output
                    if (pt.co - hl).angle(hr - pt.co, 0.0) < 0.1:

                        handle_type = 'ALIGNED'

                bp.handle_left_type = bp.handle_right_type = handle_type
                s_prev = s

            scene = bpy.data.scenes[0]  # weak!
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

    # higher quality but not really needed
    '''
    curve.redistribute(segment_length / 4.0, smooth=True)
    curve.redistribute(segment_length, smooth=False)
    '''
    curve.redistribute(segment_length, smooth=True)

    # debug only!
    # to test how good the bezier spline fitting is without corrections

    '''
    for s in curve.splines:
        s.bezier_solve()
    '''
    
    '''
    def angle_point(s):
        a = 0.0
        a_best = len(s.points) // 2
        i = 1
        for p in s.points[2:-2]:
            if p.angle > a:
                a = p.angle
                a_best = i
            i += 1
        return a_best
    '''

    # or recursively subdivide...
    curve.split_func_spline(lambda s:
                                len(s.points) // 2  # angle_point(s)
                                if ((s.bezier_solve(),
                                    s.bezier_error(bezier_tolerance))[1]
                                    and (len(s.points)))
                                else -1,
                            recursive=True,
                            )

    
    error = 0.0
    for s in curve.splines:
        error += s.bezier_error()
    print("%d :: %.6f" % (len(curve.splines), error))

    # VISUALIZE
    # curve.to_blend_data()
    curve.to_blend_curve()


if __name__ == "__main__":
    if 0:
        bpy.ops.wm.open_mainfile(filepath="/root/curve_test3.blend")

        for c in "Curve Curve.001 Curve.002 Curve.003 Curve.004 Curve.005".split():
            print("---", c)
            ob = bpy.data.objects[c]
            points = [p.co.xyz for s in ob.data.splines for p in s.points]

            print("points_to_bezier 1")
            points_to_bezier(points)
            print("points_to_bezier 2")
    else:
        bpy.ops.wm.open_mainfile(filepath="/root/curve_test2.blend")

        ob = bpy.data.objects['Curve']
        points = [p.co.xyz for s in ob.data.splines for p in s.points]

        print("points_to_bezier 1")
        points_to_bezier(points)
        print("points_to_bezier 2")

    bpy.ops.wm.save_as_mainfile(filepath="/root/curve_test_edit.blend",
                                copy=True)
    print("done!")
