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

import re
import xml.dom.minidom
from math import cos, sin, tan, atan2, pi, ceil

import bpy
from mathutils import Vector, Matrix

from . import svg_colors

#### Common utilities ####

# TODO: 'em' and 'ex' aren't actually supported
SVGUnits = {'': 1.0,
            'px': 1.0,
            'in': 90,
            'mm': 90 * 0.254,
            'cm': 90 * 2.54,
            'pt': 1.25,
            'pc': 15.0,
            'em': 1.0,
            'ex': 1.0}


def SVGCreateCurve():
    """
    Create new curve object to hold splines in
    """

    cu = bpy.data.curves.new("Curve", 'CURVE')
    obj = bpy.data.objects.new("Curve", cu)
    bpy.context.scene.objects.link(obj)

    return obj


def SVGFinishCurve():
    """
    Finish curve creation
    """

    pass


def SVGFlipHandle(x, y, x1, y1):
    """
    Flip handle around base point
    """

    x = x + (x - x1)
    y = y + (y - y1)

    return x, y


def SVGParseCoord(coord, size):
    """
    Parse coordinate component to common basis

    Needed to handle coordinates set in cm, mm, iches..
    """

    r = re.compile('([0-9\\-\\+\\.])([A-z%]*)')
    val = float(r.sub('\\1', coord))
    unit = r.sub('\\2', coord).lower()

    if unit == '%':
        return float(size) / 100.0 * val
    else:
        global SVGUnits

        return val * SVGUnits[unit]

    return val


def SVGRectFromNode(node, context):
    """
    Get display rectangle from node
    """

    w = context['rect'][0]
    h = context['rect'][1]

    if node.getAttribute('viewBox'):
        viewBox = node.getAttribute('viewBox').split()
        w = SVGParseCoord(viewBox[2], w)
        h = SVGParseCoord(viewBox[3], h)
    else:
        if node.getAttribute('width'):
            w = SVGParseCoord(node.getAttribute('width'), w)

        if node.getAttribute('height'):
            h = SVGParseCoord(node.getAttribute('height'), h)
    

    return (w, h)


def SVGMatrixFromNode(node, context):
    """
    Get transformation matrix from given node
    """

    rect = context['rect']

    m = Matrix()
    x = SVGParseCoord(node.getAttribute('x') or '0', rect[0])
    y = SVGParseCoord(node.getAttribute('y') or '0', rect[1])
    w = SVGParseCoord(node.getAttribute('width') or str(rect[0]), rect[0])
    h = SVGParseCoord(node.getAttribute('height') or str(rect[1]), rect[1])

    m = m.Translation(Vector((x, y, 0.0)))
    if len(context['rects']) > 1:
        m = m * m.Scale(w / rect[0], 4, Vector((1.0, 0.0, 0.0)))
        m = m * m.Scale(h / rect[1], 4, Vector((0.0, 1.0, 0.0)))

    if node.getAttribute('viewBox'):
        viewBox = node.getAttribute('viewBox').split()
        vx = SVGParseCoord(viewBox[0], w)
        vy = SVGParseCoord(viewBox[1], h)
        vw = SVGParseCoord(viewBox[2], w)
        vh = SVGParseCoord(viewBox[3], h)

        m = m * m.Translation(Vector((-vx, -vy, 0.0)))
        m = m * m.Scale(w / vw, 4, Vector((1.0, 0.0, 0.0)))
        m = m * m.Scale(h / vh, 4, Vector((0.0, 1.0, 0.0)))

    return m


def SVGParseTransform(transform):
    """
    Parse transform string and return transformation matrix
    """

    m = Matrix()
    r = re.compile('\s*([A-z]+)\s*\((.*?)\)')

    for match in r.finditer(transform):
        func = match.group(1)
        params = match.group(2)
        params = params.replace(',', ' ').split()

        proc = SVGTransforms.get(func)
        if proc is None:
            raise Exception('Unknown trasnform function: ' + func)

        m = m * proc(params)

    return m


def SVGGetMaterial(color, context):
    """
    Get material for specified color
    """

    materials = context['materials']

    if color in materials:
        return materials[color]

    diff = None
    if color.startswith('#'):
        color = color[1:]

        if len(color) == 3:
            color = color[0] * 2 + color[1] * 2 + color[2] * 2

        diff = (int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16))
    elif color in svg_colors.SVGColors:
        diff = svg_colors.SVGColors[color]
    else:
        return None

    mat = bpy.data.materials.new(name='SVGMat')
    mat.diffuse_color = diff

    materials[color] = mat

    return mat


def SVGTransformTranslate(params):
    """
    translate SVG transform command
    """

    tx = float(params[0])
    ty = float(params[1])
    return Matrix.Translation(Vector((tx, ty, 0.0)))


def SVGTransformMatrix(params):
    """
    matrix SVG transform command
    """

    a = float(params[0])
    b = float(params[1])
    c = float(params[2])
    d = float(params[3])
    e = float(params[4])
    f = float(params[5])

    return Matrix(((a, c, 0.0, 0.0),
                   (b, d, 0.0, 0.0),
                   (0, 0, 1.0, 0.0),
                   (e, f, 0.0, 1.0)))


def SVGTransformScale(params):
    """
    scale SVG transform command
    """

    sx = sy = float(params[0])
    if len(params) > 1:
        sy = float(params[1])

    m = Matrix()

    m = m * m.Scale(sx, 4, Vector((1.0, 0.0, 0.0)))
    m = m * m.Scale(sy, 4, Vector((0.0, 1.0, 0.0)))

    return m


def SVGTransformSkewX(params):
    """
    skewX SVG transform command
    """

    ang = float(params[0]) * pi / 180.0

    return Matrix(((1.0, 0.0, 0.0),
                  (tan(ang), 1.0, 0.0),
                  (0.0, 0.0, 1.0))).to_4x4()


def SVGTransformSkewY(params):
    """
    skewX SVG transform command
    """

    ang = float(params[0]) * pi / 180.0

    return Matrix(((1.0, tan(ang), 0.0),
                  (0.0, 1.0, 0.0),
                  (0.0, 0.0, 1.0))).to_4x4()


def SVGTransformRotate(params):
    """
    skewX SVG transform command
    """

    ang = float(params[0]) * pi / 180.0
    cx = cy = 0.0
    if len(params) >= 3:
        cx = float(params[1])
        cy = float(params[2])

    tm = Matrix.Translation(Vector((cx, cy, 0.0)))
    rm = Matrix.Rotation(ang, 4, Vector((0.0, 0.0, 1.0)))

    return tm * rm * tm.inverted()

SVGTransforms = {'translate': SVGTransformTranslate,
                 'scale': SVGTransformScale,
                 'skewX': SVGTransformSkewX,
                 'skewY': SVGTransformSkewY,
                 'matrix': SVGTransformMatrix,
                 'rotate': SVGTransformRotate}

#### SVG path helpers ####


class SVGPathData:
    """
    SVG Path data token supplier
    """

    __slots__ = ('_data',  # List of tokens
                 '_index',  # Index of current token in tokens list
                 '_len')  # Lenght og tokens list

    def __init__(self, d):
        """
        Initialize new path data supplier

        d - the definition of the outline of a shape
        """

        # Convert to easy-to-parse format
        d = d.replace(',', ' ')
        d = re.sub('([A-z])', ' \\1 ', d)

        self._data = d.split()
        self._index = 0
        self._len = len(self._data)

    def eof(self):
        """
        Check if end of data reached
        """

        return self._index >= self._len

    def cur(self):
        """
        Return current token
        """

        if self.eof():
            return None

        return self._data[self._index]

    def next(self):
        """
        Return current token and go to next one
        """

        if self.eof():
            return None

        token = self._data[self._index]
        self._index += 1

        return token

    def nextCoord(self):
        """
        Return coordinate created from current token and move to next token
        """

        token = self.next()

        if token is None:
            return None

        return float(token)


class SVGPathParser:
    """
    Parser of SVG path data
    """

    __slots__ = ('_data',  # Path data supplird
                 '_point',  # Current point coorfinate
                 '_handle',  # Last handle coordinate
                 '_splines',  # List of all splies created during parsing
                 '_spline',  # Currently handling spline
                 '_commands')  # Hash of all supported path commands

    def __init__(self, d):
        """
        Initialize path parser

        d - the definition of the outline of a shape
        """

        self._data = SVGPathData(d)
        self._point = None   # Current point
        self._handle = None  # Last handle
        self._splines = []   # List of splines in path
        self._spline = None  # Current spline

        self._commands = {'M': self._pathMoveTo,
                          'L': self._pathLineTo,
                          'H': self._pathLineTo,
                          'V': self._pathLineTo,
                          'C': self._pathCurveToCS,
                          'S': self._pathCurveToCS,
                          'Q': self._pathCurveToQT,
                          'T': self._pathCurveToQT,
                          'A': self._pathCurveToA,
                          'Z': self._pathClose,

                          'm': self._pathMoveTo,
                          'l': self._pathLineTo,
                          'h': self._pathLineTo,
                          'v': self._pathLineTo,
                          'c': self._pathCurveToCS,
                          's': self._pathCurveToCS,
                          'q': self._pathCurveToQT,
                          't': self._pathCurveToQT,
                          'a': self._pathCurveToA,
                          'z': self._pathClose}

    def _getCoordPair(self, relative, point):
        """
        Get next coordinate pair
        """

        x = self._data.nextCoord()
        y = self._data.nextCoord()

        if relative and point is not None:
            x += point[0]
            y += point[1]

        return x, y

    def _appendPoint(self, x, y, handle_left=None, handle_left_type='VECTOR',
                    handle_right=None, handle_right_type='VECTOR'):
        """
        Append point to spline

        If there's no active spline, create one and set it's first point
        to current point coordinate
        """

        if self._spline is None:
            self._spline = {'points': [],
                            'closed': False}

            self._splines.append(self._spline)

        point = {'x': x,
                 'y': y,

                 'handle_left': handle_left,
                 'handle_left_type': handle_left_type,

                 'handle_right': handle_right,
                 'handle_right_type': handle_right_type}

        self._spline['points'].append(point)

    def _updateHandle(self, handle=None, handle_type=None):
        """
        Update right handle of previous point when adding new point to spline
        """

        point = self._spline['points'][-1]

        if handle_type is not None:
            point['handle_right_type'] = handle_type

        if handle is not None:
            point['handle_right'] = handle

    def _pathMoveTo(self, code):
        """
        MoveTo path command
        """

        relative = code.islower()
        x, y = self._getCoordPair(relative, self._point)

        self._spline = None  # Flag to start new spline
        self._point = (x, y)

        cur = self._data.cur()
        while  cur is not None and not cur.isalpha():
            x, y = self._getCoordPair(relative, self._point)

            if self._spline is None:
                self._appendPoint(self._point[0], self._point[1])

            self._appendPoint(x, y)

            self._point = (x, y)
            cur = self._data.cur()

        self._handle = None

    def _pathLineTo(self, code):
        """
        LineTo path command
        """

        c = code.lower()

        cur = self._data.cur()
        while cur is not None and not cur.isalpha():
            if c == 'l':
                x, y = self._getCoordPair(code == 'l', self._point)
            elif c == 'h':
                x = self._data.nextCoord()
                y = self._point[1]
            else:
                x = self._point[0]
                y = self._data.nextCoord()

            if code == 'h':
                x += self._point[0]
            elif code == 'v':
                y += self._point[1]

            if self._spline is None:
                self._appendPoint(self._point[0], self._point[1])

            self._appendPoint(x, y)

            self._point = (x, y)
            cur = self._data.cur()

        self._handle = None

    def _pathCurveToCS(self, code):
        """
        Cubic BEZIER CurveTo  path command
        """

        c = code.lower()
        cur = self._data.cur()
        while cur is not None and not cur.isalpha():
            if c == 'c':
                x1, y1 = self._getCoordPair(code.islower(), self._point)
                x2, y2 = self._getCoordPair(code.islower(), self._point)
            else:
                if self._handle is not None:
                    x1, y1 = SVGFlipHandle(self._point[0], self._point[1],
                                        self._handle[0], self._handle[1])
                else:
                    x1, y1 = self._point

                x2, y2 = self._getCoordPair(code.islower(), self._point)

            x, y = self._getCoordPair(code.islower(), self._point)

            if self._spline is None:
                self._appendPoint(self._point[0], self._point[1],
                    handle_left_type='FREE', handle_left=self._point,
                    handle_right_type='FREE', handle_right=(x1, y1))
            else:
                self._updateHandle(handle=(x1, y1), handle_type='FREE')

            self._appendPoint(x, y,
                handle_left_type='FREE', handle_left=(x2, y2),
                handle_right_type='FREE', handle_right=(x, y))

            self._point = (x, y)
            self._handle = (x2, y2)
            cur = self._data.cur()

    def _pathCurveToQT(self, code):
        """
        Qyadracic BEZIER CurveTo  path command
        """

        c = code.lower()
        cur = self._data.cur()

        while cur is not None and not cur.isalpha():
            if c == 'q':
                x1, y1 = self._getCoordPair(code.islower(), self._point)
            else:
                if self._handle is not None:
                    x1, y1 = SVGFlipHandle(self._point[0], self._point[1],
                                        self._handle[0], self._handle[1])
                else:
                    x1, y1 = self._point

            x, y = self._getCoordPair(code.islower(), self._point)

            if self._spline is None:
                self._appendPoint(self._point[0], self._point[1],
                    handle_left_type='FREE', handle_left=self._point,
                    handle_right_type='FREE', handle_right=self._point)

            self._appendPoint(x, y,
                handle_left_type='FREE', handle_left=(x1, y1),
                handle_right_type='FREE', handle_right=(x, y))

            self._point = (x, y)
            self._handle = (x1, y1)
            cur = self._data.cur()

    def _calcArc(self, rx, ry,  ang, fa, fs, x, y):
        """
        Calc arc paths

        Copied and adoptedfrom paths_svg2obj.py scring for Blender 2.49
        which is Copyright (c) jm soler juillet/novembre 2004-april 2009,
        """

        cpx = self._point[0]
        cpy = self._point[1]
        rx = abs(rx)
        ry = abs(ry)
        px = abs((cos(ang) * (cpx - x) + sin(ang) * (cpy - y)) * 0.5) ** 2.0
        py = abs((cos(ang) * (cpy - y) - sin(ang) * (cpx - x)) * 0.5) ** 2.0
        rpx = rpy = 0.0

        if abs(rx) > 0.0:
            px = px / (rx ** 2.0)

        if abs(ry) > 0.0:
            rpy = py / (ry ** 2.0)

        pl = rpx + rpy
        if pl > 1.0:
            pl = pl ** 0.5
            rx *= pl
            ry *= pl

        carx = sarx = cary = sary = 0.0

        if abs(rx) > 0.0:
            carx = cos(ang) / rx
            sarx = sin(ang) / rx

        if abs(ry) > 0.0:
            cary = cos(ang) / ry
            sary = sin(ang) / ry

        x0 = carx * cpx + sarx * cpy
        y0 = -sary * cpx + cary * cpy
        x1 = carx * x + sarx * y
        y1 = -sary * x + cary * y
        d = (x1 - x0) * (x1 - x0) + (y1 - y0) * (y1 - y0)

        if abs(d) > 0.0:
            sq = 1.0 / d - 0.25
        else:
            sq = -0.25

        if sq < 0.0:
            sq = 0.0

        sf = sq ** 0.5
        if fs == fa:
            sf = -sf

        xc = 0.5 * (x0 + x1) - sf * (y1 - y0)
        yc = 0.5 * (y0 + y1) + sf * (x1 - x0)
        ang_0 = atan2(y0 - yc, x0 - xc)
        ang_1 = atan2(y1 - yc, x1 - xc)
        ang_arc = ang_1 - ang_0

        if ang_arc < 0.0 and fs == 1:
            ang_arc += 2.0 * pi
        elif ang_arc > 0.0 and fs == 0:
            ang_arc -= 2.0 * pi

        n_segs = int(ceil(abs(ang_arc * 2.0 / (pi * 0.5 + 0.001))))

        if self._spline is None:
            self._appendPoint(cpx, cpy,
                handle_left_type='FREE', handle_left=(cpx, cpy),
                handle_right_type='FREE', handle_right=(cpx, cpy))

        for i in range(n_segs):
            ang0 = ang_0 + i * ang_arc / n_segs
            ang1 = ang_0 + (i + 1) * ang_arc / n_segs
            ang_demi = 0.25 * (ang1 - ang0)
            t = 2.66666 * sin(ang_demi) * sin(ang_demi) / sin(ang_demi * 2.0)
            x1 = xc + cos(ang0) - t * sin(ang0)
            y1 = yc + sin(ang0) + t * cos(ang0)
            x2 = xc + cos(ang1)
            y2 = yc + sin(ang1)
            x3 = x2 + t * sin(ang1)
            y3 = y2 - t * cos(ang1)

            coord1 = ((cos(ang) * rx) * x1 + (-sin(ang) * ry) * y1,
                      (sin(ang) * rx) * x1 + (cos(ang) * ry) * y1)
            coord2 = ((cos(ang) * rx) * x3 + (-sin(ang) * ry) * y3,
                      (sin(ang) * rx) * x3 + (cos(ang) * ry) * y3)
            coord3 = ((cos(ang) * rx) * x2 + (-sin(ang) * ry) * y2,
                      (sin(ang) * rx) * x2 + (cos(ang) * ry) * y2)

            self._updateHandle(handle=coord1, handle_type='FREE')

            self._appendPoint(coord3[0], coord3[1],
                handle_left_type='FREE', handle_left=coord2,
                handle_right_type='FREE', handle_right=coord3)

    def _pathCurveToA(self, code):
        """
        Elliptical arc CurveTo path command
        """

        c = code.lower()
        cur = self._data.cur()

        while cur is not None and not cur.isalpha():
            rx = float(self._data.next())
            ry = float(self._data.next())
            ang = float(self._data.next()) / 180 * pi
            fa = float(self._data.next())
            fs = float(self._data.next())
            x, y = self._getCoordPair(code.islower(), self._point)

            self._calcArc(rx, ry,  ang, fa, fs, x, y)

            self._point = (x, y)
            self._handle = None
            cur = self._data.cur()

    def _pathClose(self, code):
        """
        Close path command
        """

        if self._spline:
            self._spline['closed'] = True

    def parse(self):
        """
        Execute parser
        """

        while not self._data.eof():
            code = self._data.next()
            cmd = self._commands.get(code)

            if cmd is None:
                raise Exception('Unknown path command: {0}' . format(code))

            cmd(code)

    def getSplines(self):
        """
        Get splines definitions
        """

        return self._splines


class SVGGeometry:
    """
    Abstract SVG geometry
    """

    __slots__ = ('_node',  # XML node for geometry
                 '_context',  # Global SVG context (holds matrices stack, i.e.)
                 '_creating')  # Flag if geometry is already creating for this node
                               # need to detect cycles for USE node

    def __init__(self, node, context):
        """
        Initialize SVG geometry
        """

        self._node = node
        self._context = context
        self._creating = False

        if hasattr(node, 'getAttribute'):
            defs = context['defines']

            id = node.getAttribute('id')
            if id and defs.get('#' + id) is None:
                defs['#' + id] = self

            className = node.getAttribute('class')
            if className and defs.get(className) is None:
                defs[className] = self

    def _pushRect(self, rect):
        """
        Push display rectangle
        """

        self._context['rects'].append(rect)
        self._context['rect'] = rect

    def _popRect(self):
        """
        Pop display rectangle
        """

        self._context['rects'].pop
        self._context['rect'] = self._context['rects'][-1]

    def _pushMatrix(self, matrix):
        """
        Push transformation matrix
        """

        self._context['transform'].append(matrix)
        self._context['matrix'] = self._context['matrix'] * matrix

    def _popMatrix(self):
        """
        Pop transformation matrix
        """

        matrix = self._context['transform'].pop()
        self._context['matrix'] = self._context['matrix'] * matrix.inverted()

    def _transformCoord(self, point):
        """
        Transform SVG-file coords
        """

        v = Vector((point[0], point[1], 0.0))

        return v * self._context['matrix']

    def getNodeMatrix(self):
        """
        Get transformation matrix of node
        """

        return SVGMatrixFromNode(self._node, self._context)

    def parse(self):
        """
        Parse XML node to memory
        """

        pass

    def _doCreateGeom(self):
        """
        Internal handler to create real geometries
        """

        pass

    def _getTranformMatrix(self):
        """
        Get matrix created from "transform" attribute
        """

        if not hasattr(self._node, 'getAttribute'):
            return None

        transform = self._node.getAttribute('transform')

        if transform:
            return SVGParseTransform(transform)

        return None

    def createGeom(self):
        """
        Create real geometries
        """

        if self._creating:
            return

        self._creating = True

        matrix = self._getTranformMatrix()
        if matrix is not None:
            self._pushMatrix(matrix)

        self._doCreateGeom()

        if matrix is not None:
            self._popMatrix()

        self._creating = False


class SVGGeometryContainer(SVGGeometry):
    """
    Container of SVG geometries
    """

    __slots__ = ('_geometries')  # List of chold geometries

    def __init__(self, node, context):
        """
        Initialize SVG geometry container
        """

        super().__init__(node, context)

        self._geometries = []

    def parse(self):
        """
        Parse XML node to memory
        """

        for node in self._node.childNodes:
            if type(node) is not xml.dom.minidom.Element:
                continue

            ob = parseAbstractNode(node, self._context)
            if ob is not None:
                self._geometries.append(ob)

    def _doCreateGeom(self):
        """
        Create real geometries
        """

        for geom in self._geometries:
            geom.createGeom()

    def getGeometries(self):
        """
        Get list of parsed geometries
        """

        return self._geometries


class SVGGeometryPATH(SVGGeometry):
    """
    SVG path geometry
    """

    __slots__ = ('_splines',  # List of splines after parsing
                 '_useFill',  # Should path be filled?
                 '_fill')  # Material used for filling

    def __init__(self, node, context):
        """
        Initialize SVG path
        """

        super().__init__(node, context)

        self._splines = []
        self._fill = None
        self._useFill = False

    def parse(self):
        """
        Parse SVG path node
        """

        d = self._node.getAttribute('d')

        pathParser = SVGPathParser(d)
        pathParser.parse()

        self._splines = pathParser.getSplines()
        self._fill = None
        self._useFill = False

        fill = self._node.getAttribute('fill')
        if fill:
            self._useFill = True
            self._fill = SVGGetMaterial(fill, self._context)

    def _doCreateGeom(self):
        """
        Create real geometries
        """

        ob = SVGCreateCurve()
        cu = ob.data

        if self._useFill:
            cu.dimensions = '2D'
            cu.materials.append(self._fill)
        else:
            cu.dimensions = '3D'

        for spline in self._splines:
            act_spline = None
            for point in spline['points']:
                loc = self._transformCoord((point['x'], point['y']))

                if act_spline is None:
                    cu.splines.new('BEZIER')

                    act_spline = cu.splines[-1]
                    act_spline.use_cyclic_u = spline['closed']
                else:
                    act_spline.bezier_points.add()

                bezt = act_spline.bezier_points[-1]
                bezt.select_control_point = True
                bezt.select_left_handle = True
                bezt.select_right_handle = True
                bezt.co = loc

                bezt.handle_left_type = point['handle_left_type']
                if point['handle_left'] is not None:
                    handle = point['handle_left']
                    bezt.handle_left = self._transformCoord(handle)

                bezt.handle_right_type = point['handle_right_type']
                if point['handle_right'] is not None:
                    handle = point['handle_right']
                    bezt.handle_right = self._transformCoord(handle)

        SVGFinishCurve()


class SVGGeometryDEFS(SVGGeometryContainer):
    """
    Container for referenced elements
    """

    def _doCreateGeom(self):
        """
        Create real geometries
        """

        pass


class SVGGeometrySYMBOL(SVGGeometryContainer):
    """
    Referenced element
    """

    def _doCreateGeom(self):
        """
        Create real geometries
        """

        pass


class SVGGeometryG(SVGGeometryContainer):
    """
    Geometry group
    """

    pass


class SVGGeometryUSE(SVGGeometry):
    """
    User of referenced elements
    """

    def _doCreateGeom(self):
        """
        Create real geometries
        """

        geometries = []
        ref = self._node.getAttribute('xlink:href')
        geom = self._context['defines'].get(ref)

        if geom is not None:
            self._pushMatrix(self.getNodeMatrix())
            self._pushMatrix(geom.getNodeMatrix())

            if isinstance(geom, SVGGeometryContainer):
                geometries = geom.getGeometries()
            else:
                geometries = [geom]

            for g in geometries:
                g.createGeom()

            self._popMatrix()
            self._popMatrix()


class SVGGeometrySVG(SVGGeometryContainer):
    """
    Main geometry holder
    """

    def _doCreateGeom(self):
        """
        Create real geometries
        """

        rect = SVGRectFromNode(self._node, self._context)

        self._pushMatrix(self.getNodeMatrix())
        self._pushRect(rect)

        super()._doCreateGeom()

        self._popRect()
        self._popMatrix()


class SVGLoader(SVGGeometryContainer):
    """
    SVG file loader
    """

    def __init__(self, filepath):
        """
        Initialize SVG loader
        """

        node = xml.dom.minidom.parse(filepath)

        m = Matrix()
        m = m * m.Scale(1.0 / 90.0, 4, Vector((1.0, 0.0, 0.0)))
        m = m * m.Scale(-1.0 / 90.0, 4, Vector((0.0, 1.0, 0.0)))

        rect = (1, 1)

        self._context = {'defines': {},
                         'transform': [],
                         'rects': [rect],
                         'rect': rect,
                         'matrix': m,
                         'materials': {}}

        super().__init__(node, self._context)


svgGeometryClasses = {
    'svg': SVGGeometrySVG,
    'path': SVGGeometryPATH,
    'defs': SVGGeometryDEFS,
    'symbol': SVGGeometrySYMBOL,
    'use': SVGGeometryUSE,
    'g': SVGGeometryG}


def parseAbstractNode(node, context):
    name = node.tagName.lower()
    geomClass = svgGeometryClasses.get(name)

    if geomClass is not None:
        ob = geomClass(node, context)
        ob.parse()

        return ob

    return None


def load_svg(filepath):
    """
    Load specified SVG file
    """

    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')

    loader = SVGLoader(filepath)
    loader.parse()
    loader.createGeom()


def load(operator, context, filepath=""):

    load_svg(filepath)

    return {'FINISHED'}
