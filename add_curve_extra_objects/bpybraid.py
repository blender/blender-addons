
from math import sin, cos, pi

from . import braid
from .braid import angle_point

import bpy


def poly_line(curve, points, join=True, type='NURBS'):
    polyline = curve.splines.new(type)
    polyline.points.add(len(points) - 1)
    for num in range(len(points)):
        polyline.points[num].co = (points[num]) + (1,)

    polyline.order_u = len(polyline.points) - 1
    if join:
        polyline.use_cyclic_u = True


def poly_lines(objname, curvename, lines, bevel=None, joins=False, ctype='NURBS'):
    curve = bpy.data.curves.new(name=curvename, type='CURVE')
    curve.dimensions = '3D'

    obj = bpy.data.objects.new(objname, curve)
    obj.location = (0, 0, 0)  # object origin
    # ctx.scene.objects.link(obj)

    for i, line in enumerate(lines):
        poly_line(curve, line, joins if type(joins) == bool else joins[i], type=ctype)

    if bevel:
        curve.bevel_object = bpy.data.objects[bevel]
    return obj


def nurbs_circle(name, w, h):
    pts = [(-w / 2, 0, 0), (0, -h / 2, 0), (w / 2, 0, 0), (0, h / 2, 0)]
    return poly_lines(name, name + '_curve', [pts], joins=True)


def star_pts(r=1, ir=None, points=5, center=(0, 0)):
    '''Create points for a star. They are 2d - z is always zero

    r: the outer radius
    ir: the inner radius
    '''
    if not ir:
        ir = r / 5
    pts = []
    dt = pi * 2 / points
    for i in range(points):
        t = i * dt
        ti = (i + .5) * dt
        pts.append(angle_point(center, t, r) + (0,))
        pts.append(angle_point(center, ti, ir) + (0,))
    return pts


def clear():
    for obj in bpy.data.objects:
        if obj.type not in ('CAMERA', 'LAMP'):
            obj.select = True
        else:
            obj.select = False
    bpy.ops.object.delete()


def defaultCircle(w=.6):
    circle = nurbs_circle('braid_circle', w, w)
    circle.hide = True
    return circle


def defaultStar():
    star = poly_lines('star', 'staz', [tuple(star_pts(points=5, r=.5, ir=.05))], type='NURBS')
    star.hide = True
    return star


def awesome_braid(strands=3, sides=5, bevel='braid_circle', pointy=False, **kwds):
    lines = braid.strands(strands, sides, **kwds)
    type = {True: 'POLY', False: 'NURBS'}[pointy]
    return poly_lines('Braid', 'Braid_c', lines, bevel=bevel, joins=True, ctype=type)
