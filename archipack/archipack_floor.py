# -*- coding:utf-8 -*-

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
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110- 1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

# ----------------------------------------------------------
# Base code inspired by JARCH Vis
# Original Author: Jacob Morris
# Author : Stephen Leger (s-leger)
# ----------------------------------------------------------

import bpy
from bpy.types import Operator, PropertyGroup, Mesh, Panel
from bpy.props import (
    BoolProperty, EnumProperty, FloatProperty,
    IntProperty, CollectionProperty
    )
from random import uniform, randint
from math import tan, pi, sqrt
from mathutils import Vector
from .bmesh_utils import BmeshEdit as bmed
from .archipack_manipulator import Manipulable
from .archipack_preset import ArchipackPreset, PresetMenuOperator
from .archipack_object import ArchipackCreateTool, ArchipackObject


def create_flooring(if_tile, over_width, over_length, b_width, b_length, b_length2, is_length_vary,
                    length_vary, num_boards, space_l, space_w, spacing, t_width, t_length, is_offset, offset,
                    is_ran_offset, offset_vary, t_width2, is_width_vary, width_vary, max_boards, is_ran_thickness,
                    ran_thickness, th, hb_dir):

    # create siding
    if if_tile == "1":  # Tiles Regular
        return tile_regular(over_width, over_length, t_width, t_length, spacing, is_offset, offset,
                                    is_ran_offset, offset_vary, th)
    elif if_tile == "2":  # Large + Small
        return tile_ls(over_width, over_length, t_width, t_length, spacing, th)
    elif if_tile == "3":  # Large + Many Small
        return tile_lms(over_width, over_length, t_width, spacing, th)
    elif if_tile == "4":  # Hexagonal
        return tile_hexagon(over_width, over_length, t_width2, spacing, th)
    elif if_tile == "21":  # Planks
        return wood_regular(over_width, over_length, b_width, b_length, space_l, space_w,
                                    is_length_vary, length_vary,
                                    is_width_vary, width_vary,
                                    is_offset, offset,
                                    is_ran_offset, offset_vary,
                                    max_boards, is_ran_thickness,
                                    ran_thickness, th)
    elif if_tile == "22":  # Parquet
        return wood_parquet(over_width, over_length, b_width, spacing, num_boards, th)
    elif if_tile == "23":  # Herringbone Parquet
        return wood_herringbone(over_width, over_length, b_width, b_length2, spacing, th, hb_dir, True)
    elif if_tile == "24":  # Herringbone
        return wood_herringbone(over_width, over_length, b_width, b_length2, spacing, th, hb_dir, False)

    return [], []


def wood_herringbone(ow, ol, bw, bl, s, th, hb_dir, stepped):
    verts = []
    faces = []
    an_45 = 0.5 * sqrt(2)
    x, y, z = 0.0, 0.0, th
    x_off, y_off = 0.0, 0.0  # used for finding farther forwards points when stepped
    ang_s = s * an_45
    s45 = s / an_45

    # step variables
    if stepped:
        x_off = an_45 * bw
        y_off = an_45 * bw

    wid_off = an_45 * bl  # offset from one end of the board to the other inline with width
    len_off = an_45 * bl  # offset from one end of the board to the other inline with length
    w = bw / an_45  # width adjusted for 45 degree rotation

    # figure out starting position
    if hb_dir == "1":
        y = -wid_off

    elif hb_dir == "2":
        x = ow
        y = ol + wid_off

    elif hb_dir == "3":
        x = -wid_off
        y = ol

    elif hb_dir == "4":
        x = ow + wid_off

    # loop going forwards
    while (hb_dir == "1" and y < ol + wid_off) or (hb_dir == "2" and y > 0 - wid_off) or \
            (hb_dir == "3" and x < ow + wid_off) or (hb_dir == "4" and x > 0 - wid_off):
        going_forwards = True

        # loop going right
        while (hb_dir == "1" and x < ow) or (hb_dir == "2" and x > 0) or (hb_dir == "3" and y > 0 - y_off) or \
                (hb_dir == "4" and y < ol + y_off):
            p = len(verts)

            # add verts
            # forwards
            verts.append((x, y, z))

            if hb_dir == "1":

                if stepped and x != 0:
                    verts.append((x - x_off, y + y_off, z))
                else:
                    verts.append((x, y + w, z))

                if going_forwards:
                    y += wid_off
                else:
                    y -= wid_off
                x += len_off

                verts.append((x, y, z))
                if stepped:
                    verts.append((x - x_off, y + y_off, z))
                    x -= x_off - ang_s
                    if going_forwards:
                        y += y_off + ang_s
                    else:
                        y -= y_off + ang_s
                else:
                    verts.append((x, y + w, z))
                    x += s

            # backwards
            elif hb_dir == "2":

                if stepped and x != ow:
                    verts.append((x + x_off, y - y_off, z))
                else:
                    verts.append((x, y - w, z))

                if going_forwards:
                    y -= wid_off
                else:
                    y += wid_off
                x -= len_off

                verts.append((x, y, z))
                if stepped:
                    verts.append((x + x_off, y - y_off, z))
                    x += x_off - ang_s
                    if going_forwards:
                        y -= y_off + ang_s
                    else:
                        y += y_off + ang_s
                else:
                    verts.append((x, y - w, z))
                    x -= s
            # right
            elif hb_dir == "3":

                if stepped and y != ol:
                    verts.append((x + y_off, y + x_off, z))
                else:
                    verts.append((x + w, y, z))

                if going_forwards:
                    x += wid_off
                else:
                    x -= wid_off
                y -= len_off

                verts.append((x, y, z))
                if stepped:
                    verts.append((x + y_off, y + x_off, z))
                    y += x_off - ang_s
                    if going_forwards:
                        x += y_off + ang_s
                    else:
                        x -= y_off + ang_s
                else:
                    verts.append((x + w, y, z))
                    y -= s
            # left
            else:

                if stepped and y != 0:
                    verts.append((x - y_off, y - x_off, z))
                else:
                    verts.append((x - w, y, z))

                if going_forwards:
                    x -= wid_off
                else:
                    x += wid_off
                y += len_off

                verts.append((x, y, z))
                if stepped:
                    verts.append((x - y_off, y - x_off, z))
                    y -= x_off - ang_s
                    if going_forwards:
                        x -= y_off + ang_s
                    else:
                        x += y_off + ang_s
                else:
                    verts.append((x - w, y, z))
                    y += s

            # faces
            faces.append((p, p + 2, p + 3, p + 1))

            # flip going_right
            going_forwards = not going_forwards
            x_off *= -1

        # if not in forwards position, then move back before adjusting values for next row
        if not going_forwards:
            x_off = abs(x_off)
            if hb_dir == "1":
                y -= wid_off
                if stepped:
                    y -= y_off + ang_s
            elif hb_dir == "2":
                y += wid_off
                if stepped:
                    y += y_off + ang_s
            elif hb_dir == "3":
                x -= wid_off
                if stepped:
                    x -= y_off + ang_s
            else:
                x += wid_off
                if stepped:
                    x += y_off + ang_s

        # adjust forwards
        if hb_dir == "1":
            y += w + s45
            x = 0
        elif hb_dir == "2":
            y -= w + s45
            x = ow
        elif hb_dir == "3":
            x += w + s45
            y = ol
        else:
            x -= w + s45
            y = 0

    return verts, faces


def tile_ls(ow, ol, tw, tl, s, z):
    """
        pattern:
         _____
        |   |_|
        |___|

        x and y are axis of big one
    """

    verts = []
    faces = []

    # big half size
    hw = (tw / 2) - (s / 2)
    hl = (tl / 2) - (s / 2)
    # small half size
    hws = (tw / 4) - (s / 2)
    hls = (tl / 4) - (s / 2)

    # small, offset from big x,y
    xo = 0.75 * tw
    yo = 0.25 * tl

    # offset for pattern
    rx = 2.5 * tw
    ry = 0.5 * tl

    # width and a half of big
    ow_x = ow + 0.5 * tw
    ol_y = ol + 0.5 * tl

    # start pattern with big one
    x = tw
    y = -tl

    while y < ol_y:

        while x < ow_x:

            p = len(verts)

            # Large
            x0 = max(0, x - hw)
            y0 = max(0, y - hl)
            x1 = min(ow, x + hw)
            y1 = min(ol, y + hl)
            if y1 > 0:
                if x1 > 0 and x0 < ow and y0 < ol:

                    verts.extend([(x0, y1, z), (x1, y1, z), (x1, y0, z), (x0, y0, z)])
                    faces.append((p, p + 1, p + 2, p + 3))
                    p = len(verts)

                # Small
                x0 = x + xo - hws
                y0 = y + yo - hls
                x1 = min(ow, x + xo + hws)

                if x1 > 0 and x0 < ow and y0 < ol:

                    y1 = min(ol, y + yo + hls)
                    verts.extend([(x0, y1, z), (x1, y1, z), (x1, y0, z), (x0, y0, z)])
                    faces.append((p, p + 1, p + 2, p + 3))

            x += rx

        y += ry
        x = x % rx - tw
        if x < -tw:
            x += rx

    return verts, faces


def tile_hexagon(ow, ol, tw, s, z):
    verts = []
    faces = []
    offset = False

    w = tw / 2
    y = 0.0
    h = w * tan(pi / 6)
    r = sqrt((w * w) + (h * h))

    while y < ol + tw:
        if not offset:
            x = 0.0
        else:
            x = w + (s / 2)

        while x < ow + tw:
            p = len(verts)

            verts.extend([(x + w, y + h, z), (x, y + r, z), (x - w, y + h, z),
                          (x - w, y - h, z), (x, y - r, z), (x + w, y - h, z)])
            faces.extend([(p, p + 1, p + 2, p + 3), (p + 3, p + 4, p + 5, p)])

            x += tw + s

        y += r + h + s
        offset = not offset

    return verts, faces


def tile_lms(ow, ol, tw, s, z):
    verts = []
    faces = []
    small = True

    y = 0.0
    ref = (tw - s) / 2

    while y < ol:
        x = 0.0
        large = False
        while x < ow:
            if small:
                x1 = min(x + ref, ow)
                y1 = min(y + ref, ol)
                p = len(verts)
                verts.extend([(x, y1, z), (x, y, z)])
                verts.extend([(x1, y1, z), (x1, y, z)])
                faces.append((p, p + 1, p + 3, p + 2))
                x += ref
            else:
                if not large:
                    x1 = min(x + ref, ow)
                    for i in range(2):
                        y0 = y + i * (ref + s)
                        if x < ow and y0 < ol:
                            y1 = min(y0 + ref, ol)
                            p = len(verts)
                            verts.extend([(x, y1, z), (x, y0, z)])
                            verts.extend([(x1, y1, z), (x1, y0, z)])
                            faces.append((p, p + 1, p + 3, p + 2))
                    x += ref
                else:
                    x1 = min(x + tw, ow)
                    y1 = min(y + tw, ol)
                    p = len(verts)
                    verts.extend([(x, y1, z), (x, y, z)])
                    verts.extend([(x1, y1, z), (x1, y, z)])
                    faces.append((p, p + 1, p + 3, p + 2))
                    x += tw
                large = not large
            x += s
        if small:
            y += ref + s
        else:
            y += tw + s
        small = not small

    return verts, faces


def tile_regular(ow, ol, tw, tl, s, is_offset, offset, is_ran_offset, offset_vary, z):
    verts = []
    faces = []
    off = False
    o = 1 / (100 / offset)
    y = 0.0

    while y < ol:

        tw2 = 0
        if is_offset:
            if is_ran_offset:
                v = tw * 0.0049 * offset_vary
                tw2 = uniform((tw / 2) - v, (tw / 2) + v)
            elif off:
                tw2 = o * tw
        x = -tw2
        y1 = min(ol, y + tl)

        while x < ow:
            p = len(verts)
            x0 = max(0, x)
            x1 = min(ow, x + tw)

            verts.extend([(x0, y1, z), (x0, y, z), (x1, y, z), (x1, y1, z)])
            faces.append((p, p + 1, p + 2, p + 3))
            x = x1 + s

        y += tl + s
        off = not off

    return verts, faces


def wood_parquet(ow, ol, bw, s, num_boards, z):
    verts = []
    faces = []
    x = 0.0

    start_orient_length = True

    # figure board length
    bl = (bw * num_boards) + (s * (num_boards - 1))
    while x < ow:

        y = 0.0

        orient_length = start_orient_length

        while y < ol:

            if orient_length:
                y0 = y
                y1 = min(y + bl, ol)

                for i in range(num_boards):

                    bx = x + i * (bw + s)

                    if bx < ow and y < ol:

                        # make sure board should be placed
                        x0 = bx
                        x1 = min(bx + bw, ow)

                        p = len(verts)
                        verts.extend([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)])
                        faces.append((p, p + 1, p + 2, p + 3))

            else:
                x0 = x
                x1 = min(x + bl, ow)

                for i in range(num_boards):

                    by = y + i * (bw + s)

                    if x < ow and by < ol:
                        y0 = by
                        y1 = min(by + bw, ol)
                        p = len(verts)

                        verts.extend([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)])
                        faces.append((p, p + 1, p + 2, p + 3))

            y += bl + s

            orient_length = not orient_length

        start_orient_length = not start_orient_length

        x += bl + s

    return verts, faces


def wood_regular(ow, ol, bw, bl, s_l, s_w,
                 is_length_vary, length_vary,
                 is_width_vary, width_vary,
                 is_offset, offset,
                 is_ran_offset, offset_vary,
                 max_boards, is_r_h,
                 r_h, th):
    verts = []
    faces = []
    x = 0.0
    row = 0
    while x < ow:

        if is_width_vary:
            v = bw * (width_vary / 100) * 0.499
            bw2 = uniform(bw / 2 - v, bw / 2 + v)
        else:
            bw2 = bw

        x1 = min(x + bw2, ow)
        if is_offset:
            if is_ran_offset:
                v = bl * (offset_vary / 100) * 0.5
                y = -uniform(bl / 2 - v, bl / 2 + v)
            else:
                y = -(row % 2) * bl * (offset / 100)
        else:
            y = 0

        row += 1
        counter = 1

        while y < ol:

            z = th

            if is_r_h:
                v = z * 0.5 * (r_h / 100)
                z = uniform(z / 2 - v, z / 2 + v)

            bl2 = bl

            if is_length_vary:
                if (counter >= max_boards):
                    bl2 = ol
                else:
                    v = bl * (length_vary / 100) * 0.5
                    bl2 = uniform(bl / 2 - v, bl / 2 + v)

            y0 = max(0, y)
            y1 = min(y + bl2, ol)

            if y1 > y0:
                p = len(verts)

                verts.extend([(x, y0, z), (x1, y0, z), (x1, y1, z), (x, y1, z)])
                faces.append((p, p + 1, p + 2, p + 3))

                y += bl2 + s_l

            counter += 1

        x += bw2 + s_w

    return verts, faces


def tile_grout(ow, ol, depth, th):
    z = min(th - 0.001, max(0.001, th - depth))
    x = ow
    y = ol

    verts = [(0.0, 0.0, 0.0), (0.0, 0.0, z), (x, 0.0, z), (x, 0.0, 0.0),
             (0.0, y, 0.0), (0.0, y, z), (x, y, z), (x, y, 0.0)]

    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (3, 7, 6, 2), (0, 4, 7, 3)]

    return verts, faces


def update(self, context):
    self.update(context)


class archipack_floor(ArchipackObject, Manipulable, PropertyGroup):
    tile_types = EnumProperty(
                items=(
                    ("1", "Tiles", ""),
                    ("2", "Large + Small", ""),
                    ("3", "Large + Many Small", ""),
                    ("4", "Hexagonal", ""),
                    ("21", "Planks", ""),
                    ("22", "Parquet", ""),
                    ("23", "Herringbone Parquet", ""),
                    ("24", "Herringbone", "")
                ),
                default="1",
                description="Tile Type",
                update=update,
                name="")
    b_length_s = FloatProperty(
                name="Board Length",
                min=0.01,
                default=2.0,
                unit='LENGTH', subtype='DISTANCE',
                description="Board Length",
                update=update)
    hb_direction = EnumProperty(
                items=(
                    ("1", "Forwards (+y)", ""),
                    ("2", "Backwards (-y)", ""),
                    ("3", "Right (+x)", ""),
                    ("4", "Left (-x)", "")
                ),
                name="Direction",
                description="Herringbone Direction",
                update=update)
    thickness = FloatProperty(
                name="Floor Thickness",
                min=0.01,
                default=0.1,
                unit='LENGTH', subtype='DISTANCE',
                description="Thickness Of Flooring",
                update=update)
    num_boards = IntProperty(
                name="# Of Boards",
                min=2,
                max=6,
                default=4,
                description="Number Of Boards In Square",
                update=update)
    space_l = FloatProperty(
                name="Length Spacing",
                min=0.001,
                default=0.005,
                step=0.01,
                unit='LENGTH', subtype='DISTANCE',
                description="Space Between Boards Length Ways",
                update=update)
    space_w = FloatProperty(
                name="Width Spacing",
                min=0.001,
                default=0.005,
                step=0.01,
                unit='LENGTH', subtype='DISTANCE',
                description="Space Between Boards Width Ways",
                update=update)
    spacing = FloatProperty(
                name="Spacing",
                min=0.001,
                default=0.005,
                step=0.01,
                unit='LENGTH', subtype='DISTANCE',
                description="Space Between Tiles/Boards",
                update=update)
    is_bevel = BoolProperty(
                name="Bevel?",
                default=False,
                update=update)
    bevel_res = IntProperty(
                name="Bevel Resolution",
                min=1,
                max=10,
                default=1,
                update=update)
    bevel_amo = FloatProperty(
                name="Bevel Amount",
                min=0.001,
                default=0.0015,
                step=0.01,
                unit='LENGTH', subtype='DISTANCE',
                description="Bevel Amount",
                update=update)
    is_ran_thickness = BoolProperty(
                name="Random Thickness?",
                default=False,
                update=update)
    ran_thickness = FloatProperty(
                name="Thickness Variance",
                min=0.1,
                max=100.0,
                default=50.0,
                subtype="PERCENTAGE",
                update=update)
    is_floor_bottom = BoolProperty(
                name="Floor bottom",
                default=True,
                update=update)
    t_width = FloatProperty(
                name="Tile Width",
                min=0.01,
                default=0.3,
                unit='LENGTH', subtype='DISTANCE',
                description="Tile Width",
                update=update)
    t_length = FloatProperty(
                name="Tile Length",
                min=0.01,
                default=0.3,
                unit='LENGTH', subtype='DISTANCE',
                description="Tile Length",
                update=update)
    is_grout = BoolProperty(
                name="Grout",
                default=False,
                description="Enable grout",
                update=update)
    grout_depth = FloatProperty(
                name="Grout Depth",
                min=0.001,
                default=0.005,
                step=0.01,
                unit='LENGTH', subtype='DISTANCE',
                description="Grout Depth",
                update=update)
    is_offset = BoolProperty(
                name="Offset ?",
                default=False,
                description="Offset Rows",
                update=update)
    offset = FloatProperty(
                name="Offset",
                min=0.001,
                max=100.0,
                default=50.0,
                subtype="PERCENTAGE",
                description="Tile Offset Amount",
                update=update)
    is_random_offset = BoolProperty(
                name="Random Offset?",
                default=False,
                description="Offset Tile Rows Randomly",
                update=update)
    offset_vary = FloatProperty(
                name="Offset Variance",
                min=0.001,
                max=100.0,
                default=50.0,
                subtype="PERCENTAGE",
                description="Offset Variance",
                update=update)
    t_width_s = FloatProperty(
                name="Small Tile Width",
                min=0.02,
                default=0.2,
                unit='LENGTH', subtype='DISTANCE',
                description="Small Tile Width",
                update=update)
    over_width = FloatProperty(
                name="Overall Width",
                min=0.02,
                default=4,
                unit='LENGTH', subtype='DISTANCE',
                description="Overall Width",
                update=update)
    over_length = FloatProperty(
                name="Overall Length",
                min=0.02,
                default=4,
                unit='LENGTH', subtype='DISTANCE',
                description="Overall Length",
                update=update)
    b_width = FloatProperty(
                name="Board Width",
                min=0.01,
                default=0.2,
                unit='LENGTH', subtype='DISTANCE',
                description="Board Width",
                update=update)
    b_length = FloatProperty(
                name="Board Length",
                min=0.01,
                default=0.8,
                unit='LENGTH', subtype='DISTANCE',
                description="Board Length",
                update=update)
    is_length_vary = BoolProperty(
                name="Vary Length?",
                default=False,
                description="Vary Lengths?",
                update=update)
    length_vary = FloatProperty(
                name="Length Variance",
                min=1.00,
                max=100.0,
                default=50.0,
                subtype="PERCENTAGE",
                description="Length Variance",
                update=update)
    max_boards = IntProperty(
                name="Max # Of Boards",
                min=2,
                default=2,
                description="Maximum Number Of Boards Possible In One Length",
                update=update)
    is_width_vary = BoolProperty(
                name="Vary Width?",
                default=False,
                description="Vary Widths?",
                update=update)
    width_vary = FloatProperty(
                name="Width Variance",
                min=1.00,
                max=100.0,
                default=50.0,
                subtype="PERCENTAGE",
                description="Width Variance",
                update=update)
    is_mat_vary = BoolProperty(
                name="Vary Material?",
                default=False,
                description="Vary Material indexes",
                update=update)
    mat_vary = IntProperty(
                name="#variations",
                min=1,
                max=10,
                default=1,
                description="Material index maxi",
                update=update)
    auto_update = BoolProperty(
            options={'SKIP_SAVE'},
            default=True,
            update=update
            )

    def setup_manipulators(self):
        if len(self.manipulators) < 1:
            # add manipulator for x property
            s = self.manipulators.add()
            s.prop1_name = "over_width"
            # s.prop2_name = "x"
            s.type_key = 'SIZE'

            # add manipulator for y property
            s = self.manipulators.add()
            s.prop1_name = "over_length"
            # s.prop2_name = "y"
            s.type_key = 'SIZE'

    def update(self, context):

        o = self.find_in_selection(context, self.auto_update)

        if o is None:
            return

        self.setup_manipulators()

        verts, faces = create_flooring(self.tile_types, self.over_width,
                            self.over_length, self.b_width, self.b_length, self.b_length_s,
                            self.is_length_vary, self.length_vary, self.num_boards, self.space_l,
                            self.space_w, self.spacing, self.t_width, self.t_length, self.is_offset,
                            self.offset, self.is_random_offset, self.offset_vary, self.t_width_s,
                            self.is_width_vary, self.width_vary, self.max_boards, self.is_ran_thickness,
                            self.ran_thickness, self.thickness, self.hb_direction)

        if self.is_mat_vary:
            # hexagon made of 2 faces
            if self.tile_types == '4':
                matids = []
                for i in range(int(len(faces) / 2)):
                    id = randint(1, self.mat_vary)
                    matids.extend([id, id])
            else:
                matids = [randint(1, self.mat_vary) for i in faces]
        else:
            matids = [1 for i in faces]

        uvs = [[(0, 0), (0, 1), (1, 1), (1, 0)] for i in faces]

        bmed.buildmesh(context,
                       o,
                       verts,
                       faces,
                       matids=matids,
                       uvs=uvs,
                       weld=False,
                       auto_smooth=False)

        # cut hexa and herringbone wood
        # disable when boolean modifier is found
        enable_bissect = True
        for m in o.modifiers:
            if m.type == 'BOOLEAN':
                enable_bissect = False

        if enable_bissect and self.tile_types in ('4', '23', '24'):
            bmed.bissect(context, o, Vector((0, 0, 0)), Vector((0, -1, 0)))
            # Up
            bmed.bissect(context, o, Vector((0, self.over_length, 0)), Vector((0, 1, 0)))
            # left
            bmed.bissect(context, o, Vector((0, 0, 0)), Vector((-1, 0, 0)))
            # right
            bmed.bissect(context, o, Vector((self.over_width, 0, 0)), Vector((1, 0, 0)))

        if self.is_bevel:
            bevel = self.bevel_amo
        else:
            bevel = 0

        if self.is_grout:
            th = min(self.grout_depth + bevel, self.thickness - 0.001)
            bottom = th
        else:
            th = self.thickness
            bottom = 0

        bmed.solidify(context,
                        o,
                        th,
                        floor_bottom=(
                            self.is_floor_bottom and
                            self.is_ran_thickness and
                            self.tile_types in ('21')
                            ),
                        altitude=bottom)

        # bevel mesh
        if self.is_bevel:
            bmed.bevel(context, o, self.bevel_amo, segments=self.bevel_res)

        # create grout
        if self.is_grout:
            verts, faces = tile_grout(self.over_width, self.over_length, self.grout_depth, self.thickness)
            matids = [0 for i in faces]
            uvs = [[(0, 0), (0, 1), (1, 1), (1, 0)] for i in faces]
            bmed.addmesh(context,
                           o,
                           verts,
                           faces,
                           matids=matids,
                           uvs=uvs,
                           weld=False,
                           auto_smooth=False)

        x, y = self.over_width, self.over_length
        self.manipulators[0].set_pts([(0, 0, 0), (x, 0, 0), (1, 0, 0)])
        self.manipulators[1].set_pts([(0, 0, 0), (0, y, 0), (-1, 0, 0)])

        self.restore_context(context)


class ARCHIPACK_PT_floor(Panel):
    bl_idname = "ARCHIPACK_PT_floor"
    bl_label = "Flooring"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Archipack"

    @classmethod
    def poll(cls, context):
        # ensure your object panel only show when active object is the right one
        return archipack_floor.filter(context.active_object)

    def draw(self, context):
        o = context.active_object
        if not archipack_floor.filter(o):
            return
        layout = self.layout

        # retrieve datablock of your object
        props = archipack_floor.datablock(o)

        # Manipulate mode operator
        layout.operator('archipack.floor_manipulate', icon='HAND')

        box = layout.box()
        row = box.row(align=True)

        # Presets operators
        row.operator("archipack.floor_preset_menu",
                     text=bpy.types.ARCHIPACK_OT_floor_preset_menu.bl_label)
        row.operator("archipack.floor_preset",
                      text="",
                      icon='ZOOMIN')
        row.operator("archipack.floor_preset",
                      text="",
                      icon='ZOOMOUT').remove_active = True

        layout.prop(props, "tile_types", icon="OBJECT_DATA")

        layout.separator()

        layout.prop(props, "over_width")
        layout.prop(props, "over_length")
        layout.separator()

        # width and lengths
        layout.prop(props, "thickness")

        type = int(props.tile_types)

        if type > 20:
            # Wood types
            layout.prop(props, "b_width")
        else:
            # Tiles types
            if type != 4:
                # Not hexagonal
                layout.prop(props, "t_width")
                layout.prop(props, "t_length")
            else:
                layout.prop(props, "t_width_s")

        # Herringbone
        if type in (23, 24):
            layout.prop(props, "b_length_s")
            layout.prop(props, "hb_direction")

        # Parquet
        if type == 22:
            layout.prop(props, "num_boards")

        # Planks
        if type == 21:
            layout.prop(props, "b_length")
            layout.prop(props, "space_w")
            layout.prop(props, "space_l")

            layout.separator()
            layout.prop(props, "is_length_vary", icon="NLA")
            if props.is_length_vary:
                layout.prop(props, "length_vary")
                layout.prop(props, "max_boards")

            layout.separator()
            layout.prop(props, "is_width_vary", icon="UV_ISLANDSEL")
            if props.is_width_vary:
                layout.prop(props, "width_vary")

            layout.separator()
            layout.prop(props, "is_ran_thickness", icon="RNDCURVE")
            if props.is_ran_thickness:
                layout.prop(props, "ran_thickness")
                layout.prop(props, "is_floor_bottom", icon="MOVE_DOWN_VEC")
        else:
            layout.prop(props, "spacing")

        # Planks and tiles
        if type in (1, 21):
            layout.separator()
            layout.prop(props, "is_offset", icon="OOPS")
            if props.is_offset:
                layout.prop(props, "is_random_offset", icon="NLA")
                if not props.is_random_offset:
                    layout.prop(props, "offset")
                else:
                    layout.prop(props, "offset_vary")

        # bevel
        layout.separator()
        layout.prop(props, "is_bevel", icon="MOD_BEVEL")
        if props.is_bevel:
            layout.prop(props, "bevel_res", icon="OUTLINER_DATA_CURVE")
            layout.prop(props, "bevel_amo")

        # Grout
        layout.separator()
        layout.prop(props, "is_grout", icon="OBJECT_DATA")
        if props.is_grout:
            layout.prop(props, "grout_depth")

        layout.separator()
        layout.prop(props, "is_mat_vary", icon="MATERIAL")
        if props.is_mat_vary:
            layout.prop(props, "mat_vary")


class ARCHIPACK_OT_floor(ArchipackCreateTool, Operator):
    bl_idname = "archipack.floor"
    bl_label = "Floor"
    bl_description = "Create Floor"
    bl_category = 'Archipack'
    bl_options = {'REGISTER', 'UNDO'}

    def create(self, context):

        # Create an empty mesh datablock
        m = bpy.data.meshes.new("Floor")

        # Create an object using the mesh datablock
        o = bpy.data.objects.new("Floor", m)

        # Add your properties on mesh datablock
        d = m.archipack_floor.add()

        # Link object into scene
        context.scene.objects.link(o)

        # select and make active
        o.select = True
        context.scene.objects.active = o

        # Load preset into datablock
        self.load_preset(d)

        # add a material
        self.add_material(o)
        return o

    def execute(self, context):
        if context.mode == "OBJECT":
            bpy.ops.object.select_all(action="DESELECT")
            o = self.create(context)
            o.location = bpy.context.scene.cursor_location
            o.select = True
            context.scene.objects.active = o

            # Start manipulate mode
            self.manipulate()
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Archipack: Option only valid in Object mode")
            return {'CANCELLED'}


class ARCHIPACK_OT_floor_preset_menu(PresetMenuOperator, Operator):
    bl_idname = "archipack.floor_preset_menu"
    bl_label = "Floor preset"
    preset_subdir = "archipack_floor"


class ARCHIPACK_OT_floor_preset(ArchipackPreset, Operator):
    """Add a Floor Preset"""
    bl_idname = "archipack.floor_preset"
    bl_label = "Add Floor preset"
    preset_menu = "ARCHIPACK_OT_floor_preset_menu"

    @property
    def blacklist(self):
        return ['manipulators', 'over_length', 'over_width']


class ARCHIPACK_OT_floor_manipulate(Operator):
    bl_idname = "archipack.floor_manipulate"
    bl_label = "Manipulate"
    bl_description = "Manipulate"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        return archipack_floor.filter(context.active_object)

    def invoke(self, context, event):
        d = archipack_floor.datablock(context.active_object)
        d.manipulable_invoke(context)
        return {'FINISHED'}


def register():
    bpy.utils.register_class(archipack_floor)
    Mesh.archipack_floor = CollectionProperty(type=archipack_floor)
    bpy.utils.register_class(ARCHIPACK_PT_floor)
    bpy.utils.register_class(ARCHIPACK_OT_floor)
    bpy.utils.register_class(ARCHIPACK_OT_floor_preset_menu)
    bpy.utils.register_class(ARCHIPACK_OT_floor_preset)
    bpy.utils.register_class(ARCHIPACK_OT_floor_manipulate)


def unregister():
    bpy.utils.unregister_class(archipack_floor)
    del Mesh.archipack_floor
    bpy.utils.unregister_class(ARCHIPACK_PT_floor)
    bpy.utils.unregister_class(ARCHIPACK_OT_floor)
    bpy.utils.unregister_class(ARCHIPACK_OT_floor_preset_menu)
    bpy.utils.unregister_class(ARCHIPACK_OT_floor_preset)
    bpy.utils.unregister_class(ARCHIPACK_OT_floor_manipulate)
