
import math
from math import sin, cos, pi


def angle_point(center, angle, distance):
    cx, cy = center
    x = cos(angle) * distance
    y = sin(angle) * distance
    return x + cx, y + cy


def flat_hump(strands, mx=1, my=1, mz=1, resolution=2):
    num = 4 * resolution
    dy = 2 * pi / num
    dz = 2 * pi * (strands - 1) / num
    for i in range(num):
        x = i * mx
        y = cos(i * dy) * my
        z = sin(i * dz) * mz
        # print(i, x, y, z)
        yield x, y, z


def circle_hump(pos, strands, humps, radius=1, mr=1, mz=.2, resolution=2):
    num = 5 * resolution
    dt = 2 * pi / humps * strands / num
    dr = 2 * pi * (strands - 1) / num
    dz = 2 * pi / num
    t0 = 2 * pi / humps * pos
    # print('ds', dt, dr, dz)
    for i in range(num):
        # i += pos
        rdi = sin(i * dr) * mr
        # print('rdi', rdi, radius, i*dt, i*dz, cos(i*dz) * mz)
        x, y = angle_point((0, 0), i * dt + t0, radius + sin(i * dr) * mr)
        z = cos(i * dz) * mz
        yield x, y, z


def strands(strands, humps, radius=1, mr=1, mz=.2, resolution=2):
    positions = [0 for x in range(humps)]
    made = 0
    last = None
    lines = []
    at = 0
    while 0 in positions:
        if positions[at]:
            at = positions.index(0)
            last = None
        hump = list(circle_hump(at, strands, humps, radius, mr, mz, resolution))
        if last is None:
            last = hump
            lines.append(last)
        else:
            last.extend(hump)
        positions[at] = 1
        at += strands
        at %= humps
    return lines
