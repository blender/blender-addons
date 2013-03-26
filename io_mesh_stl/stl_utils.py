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

"""
Import and export STL files

Used as a blender script, it load all the stl files in the scene:

blender --python stl_utils.py -- file1.stl file2.stl file3.stl ...
"""

import struct
import mmap
import contextlib
import itertools

# TODO: endien


@contextlib.contextmanager
def mmap_file(filename):
    """
    Context manager over the data of an mmap'ed file (Read ONLY).


    Example:

    with mmap_file(filename) as m:
        m.read()
        print m[10:50]
    """
    with open(filename, 'rb') as file:
        # check http://bugs.python.org/issue8046 to have mmap context
        # manager fixed in python
        mem_map = mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ)
        yield mem_map
        mem_map.close()


class ListDict(dict):
    """
    Set struct with order.

    You can:
       - insert data into without doubles
       - get the list of data in insertion order with self.list

    Like collections.OrderedDict, but quicker, can be replaced if
    ODict is optimised.
    """

    def __init__(self):
        dict.__init__(self)
        self.list = []
        self._len = 0

    def add(self, item):
        """
        Add a value to the Set, return its position in it.
        """
        value = self.setdefault(item, self._len)
        if value == self._len:
            self.list.append(item)
            self._len += 1

        return value

BINARY_HEADER = 80
BINARY_STRIDE = 12 * 4 + 2


def _header_version():
    import bpy
    return "Exported from Blender-" + bpy.app.version_string


def _is_ascii_file(data):
    """
    This function returns True if the data represents an ASCII file.

    Please note that a False value does not necessary means that the data
    represents a binary file. It can be a (very *RARE* in real life, but
    can easily be forged) ascii file.
    """
    size = struct.unpack_from('<I', data, BINARY_HEADER)[0]

    return not data.size() == BINARY_HEADER + 4 + BINARY_STRIDE * size


def _binary_read(data):
    # an stl binary file is
    # - 80 bytes of description
    # - 4 bytes of size (unsigned int)
    # - size triangles :
    #
    #   - 12 bytes of normal
    #   - 9 * 4 bytes of coordinate (3*3 floats)
    #   - 2 bytes of garbage (usually 0)

    # OFFSET for the first byte of coordinate (headers + first normal bytes)
    # STRIDE between each triangle (first normal + coordinates + garbage)
    OFFSET = BINARY_HEADER + 4 + 12

    # read header size, ignore description
    size = struct.unpack_from('<I', data, BINARY_HEADER)[0]
    unpack = struct.Struct('<9f').unpack_from

    for i in range(size):
        # read the points coordinates of each triangle
        pt = unpack(data, OFFSET + BINARY_STRIDE * i)
        yield pt[:3], pt[3:6], pt[6:]


def _ascii_read(data):
    # an stl ascii file is like
    # HEADER: solid some name
    # for each face:
    #
    #     facet normal x y z
    #     outerloop
    #          vertex x y z
    #          vertex x y z
    #          vertex x y z
    #     endloop
    #     endfacet

    # strip header
    data.readline()

    while True:
        l = data.readline()
        if not l:
            break

        # if we encounter a vertex, read next 2
        l = l.lstrip()
        if l.startswith(b'vertex'):
            yield [tuple(map(float, l_item.split()[1:]))
                   for l_item in (l, data.readline(), data.readline())]


def _binary_write(filename, faces):
    with open(filename, 'wb') as data:
        # header
        # we write padding at header beginning to avoid to
        # call len(list(faces)) which may be expensive
        data.write(struct.calcsize('<80sI') * b'\0')

        # 3 vertex == 9f
        pack = struct.Struct('<9f').pack
        # pad is to remove normal, we do use them
        pad = b'\0' * struct.calcsize('<3f')

        nb = 0
        for verts in faces:
            # write pad as normal + vertexes + pad as attributes
            data.write(pad + pack(*itertools.chain.from_iterable(verts)))
            data.write(b'\0\0')
            nb += 1

        # header, with correct value now
        data.seek(0)
        data.write(struct.pack('<80sI', _header_version().encode('ascii'), nb))


def _ascii_write(filename, faces):
    with open(filename, 'w') as data:
        header = _header_version()
        data.write('solid %s\n' % header)

        for face in faces:
            data.write('''facet normal 0 0 0\nouter loop\n''')
            for vert in face:
                data.write('vertex %f %f %f\n' % vert[:])
            data.write('endloop\nendfacet\n')

        data.write('endsolid %s\n' % header)


def write_stl(filename, faces, ascii=False):
    """
    Write a stl file from faces,

    filename
       output filename

    faces
       iterable of tuple of 3 vertex, vertex is tuple of 3 coordinates as float

    ascii
       save the file in ascii format (very huge)
    """
    (_ascii_write if ascii else _binary_write)(filename, faces)


def read_stl(filename):
    """
    Return the triangles and points of an stl binary file.

    Please note that this process can take lot of time if the file is
    huge (~1m30 for a 1 Go stl file on an quad core i7).

    - returns a tuple(triangles, points).

      triangles
          A list of triangles, each triangle as a tuple of 3 index of
          point in *points*.

      points
          An indexed list of points, each point is a tuple of 3 float
          (xyz).

    Example of use:

       >>> tris, pts = read_stl(filename, lambda x:)
       >>> pts = list(pts)
       >>>
       >>> # print the coordinate of the triangle n
       >>> print(pts[i] for i in tris[n])
    """

    tris, pts = [], ListDict()

    with mmap_file(filename) as data:
        # check for ascii or binary
        gen = _ascii_read if _is_ascii_file(data) else _binary_read

        for pt in gen(data):
            # Add the triangle and the point.
            # If the point is allready in the list of points, the
            # index returned by pts.add() will be the one from the
            # first equal point inserted.
            tris.append([pts.add(p) for p in pt])

    return tris, pts.list


if __name__ == '__main__':
    import sys
    import bpy
    from io_mesh_stl import blender_utils

    filenames = sys.argv[sys.argv.index('--') + 1:]

    for filename in filenames:
        objName = bpy.path.display_name(filename)
        tris, pts = read_stl(filename)

        blender_utils.create_and_link_mesh(objName, tris, pts)
