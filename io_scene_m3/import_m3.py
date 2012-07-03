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

__author__ = "Cory Perry (muraj)"
__version__ = "0.2.1"
__bpydoc__ = """\
This script imports m3 format files to Blender.

The m3 file format, used by Blizzard in several games, is based around the
mdx and m2 file format.  Thanks to the efforts of Volcore, madyavic and the
people working on libm3, the file format has been reversed engineered
enough to make this script possible (Thanks guys!).

This script currently imports the following:<br>
 - Geometry data (vertices, faces, submeshes [in vertex groups])
 - Model Textures (currently only the first material is supported)

   Blender supports the DDS file format and needs the image in the same
   directory.  This script will notify you of any missing textures.

TODO:<br>
 - Documentation & clean up
 - Full MD34 and MD33 testing (possibly batch importing for a testing suite)
 - Import *ALL* materials and bind accordingly (currently supports diffuse,
    specular, and normal.
 - Adjust vertices to bind pose (import IREF matrices)
 - Import Bone data
 - Import Animation data

Usage:<br>
    Execute this script from the "File->Import" menu and choose a m3 file to
open.

Notes:<br>
    Known issue with Thor.m3, seems to add a lot of unecessary verts.
    Generates the standard verts and faces lists.
"""

import bpy
import struct
import os.path
from bpy.props import *
from bpy_extras.image_utils import load_image

##################
## Struct setup ##
##################
verFlag = False        # Version flag (MD34 == True, MD33 == False)


class ref:
    fmt = 'LL'

    def __init__(self, file):
        global verFlag
        if verFlag:
            self.fmt += 'L'    # Extra unknown...
        _s = file.read(struct.calcsize(self.fmt))
        self.entries, self.refid = struct.unpack(self.fmt, _s)[:2]

    @classmethod
    def size(cls):
        global verFlag
        return struct.calcsize(cls.fmt + ('L' if verFlag else ''))


class animref:
    fmt = 'HHL'

    def __init__(self, file):
        _s = file.read(struct.calcsize(self.fmt))
        self.flags, self.animflags, self.animid = struct.unpack(self.fmt, _s)


class Tag:
    fmt = '4sLLL'

    def __init__(self, file):
        _s = file.read(struct.calcsize(self.fmt))
        self.name, self.ofs, self.nTag, self.version = \
            struct.unpack(self.fmt, _s)


class matrix:
    fmt = 'f' * 16

    def __init__(self, file):
        _s = file.read(struct.calcsize(self.fmt))
        self.mat = struct.unpack(self.fmt, _s)


class vect:
    fmt = 'fff'

    def __init__(self, file):
        _s = file.read(struct.calcsize(self.fmt))
        self.v = struct.unpack(self.fmt, _s)


class vertex:
    fmt = "4B4b4B%dH4B"
    ver = {0x020000: 2, 0x060000: 4, 0x0A0000: 6, 0x120000: 8}

    def __init__(self, file, flag):
        self.pos = vect(file)
        _fmt = self.fmt % (self.ver[flag])
        _s = file.read(struct.calcsize(_fmt))
        _s = struct.unpack(_fmt, _s)
        self.boneWeight = _s[0:4]
        self.boneIndex = _s[4:8]
        self.normal = _s[8:12]
        self.uv = _s[12:14]
        self.tan = _s[-4:]    # Skipping the middle ukn value if needed
        self.boneWeight = [b / 255.0 for b in self.boneWeight]
        self.normal = [x * 2.0 / 255.0 - 1.0 for x in self.normal]
        self.tan = [x * 2.0 / 255.0 - 1.0 for x in self.tan]
        self.uv = [x / 2046.0 for x in self.uv]
        self.uv[1] = 1.0 - self.uv[1]

    @classmethod
    def size(cls, flag=0x020000):
        return struct.calcsize('fff' + cls.fmt % (cls.ver[flag]))


class quat:
    fmt = 'ffff'

    def __init__(self, file):
        _s = file.read(struct.calcsize(self.fmt))
        self.v = struct.unpack(self.fmt, _s)
        #Quats are stored x,y,z,w - this fixes it
        self.v = [self.v[-1], self.v[0], self.v[1], self.v[2]]


class bone:

    def __init__(self, file):
        file.read(4)    # ukn1
        self.name = ref(file)
        self.flag, self.parent, _ = struct.unpack('LhH', file.read(8))
        self.posid = animref(file)
        self.pos = vect(file)
        file.read(4 * 4)    # ukn
        self.rotid = animref(file)
        self.rot = quat(file)
        file.read(4 * 5)    # ukn
        self.scaleid = animref(file)
        self.scale = vect(file)
        vect(file)          # ukn
        file.read(4 * 6)    # ukn


class div:

    def __init__(self, file):
        self.faces = ref(file)
        self.regn = ref(file)
        self.bat = ref(file)
        self.msec = ref(file)
        file.read(4)    # ukn


class regn:
    fmt = 'L2H2L6H'

    def __init__(self, file):
        _s = file.read(struct.calcsize(self.fmt))
        _ukn1, self.ofsVert, self.nVerts, self.ofsIndex, self.nIndex, \
            self.boneCount, self.indBone, self.nBone = \
            struct.unpack(self.fmt, _s)[:8]


class mat:

    def __init__(self, file):
        self.name = ref(file)
        file.read(4 * 10)    # ukn
        self.layers = [ref(file) for _ in range(13)]
        file.read(4 * 15)    # ukn


class layr:

    def __init__(self, file):
        file.read(4)
        self.name = ref(file)
        #Rest not implemented.


class hdr:
    fmt = '4sLL'

    def __init__(self, file):
        _s = file.read(struct.calcsize(self.fmt))
        self.magic, self.ofsTag, self.nTag = struct.unpack(self.fmt, _s)
        self.MODLref = ref(file)


class MODL:

    def __init__(self, file, flag=20):
        global verFlag
        self.name = ref(file)
        self.ver = struct.unpack('L', file.read(4))[0]
        self.seqHdr = ref(file)
        self.seqData = ref(file)
        self.seqLookup = ref(file)
        file.read(0x1C if verFlag else 0x14)            # ukn1
        self.bones = ref(file)
        file.read(4)            # ukn2
        self.flags = struct.unpack('L', file.read(4))[0]
        self.vert = ref(file)
        self.views = ref(file)
        self.boneLookup = ref(file)
        self.extents = [vect(file), vect(file)]
        self.radius = struct.unpack('f', file.read(4))[0]
        if verFlag:
            file.read(4)            # ukn MD34 addition
        if not verFlag:
            if flag == 20:
                file.read(0x2C)
            else:
                file.read(0x34)
        else:
            if flag == 20:
                file.read(0x30)
            else:
                file.read(0x3C)
        self.attach = ref(file)
        file.read(5 * ref.size())
        self.materialsLookup = ref(file)
        self.materials = ref(file)
        file.read(ref.size())
        if not verFlag:
            file.read(0x90)
        else:
            file.read(0xD8)
        self.iref = ref(file)


def read(file, context, op):
    """Imports as an m3 file"""
    global verFlag
    h = hdr(file)
    if h.magic[::-1] == b'MD34':
        print('m3_import: !WARNING! MD34 files not full tested...')
        verFlag = True
    elif h.magic[::-1] == b'MD33':
        verFlag = False
    else:
        raise Exception('m3_import: !ERROR! Not a valid or supported m3 file')
    file.seek(h.ofsTag)    # Jump to the Tag table
    print('m3_import: !INFO! Reading TagTable...')
    tagTable = [Tag(file) for _ in range(h.nTag)]
    file.seek(tagTable[h.MODLref.refid].ofs)
    m = MODL(file, tagTable[h.MODLref.refid].version)
    if not m.flags & 0x20000:
        raise Exception('m3_import: !ERROR! Model doesn\'t have any vertices')
    print('m3_import: !INFO! Reading Vertices...')
    vert_flags = m.flags & 0x1E0000        # Mask out the vertex version
    file.seek(tagTable[m.views.refid].ofs)
    d = div(file)
    file.seek(tagTable[m.vert.refid].ofs)
    verts = [vertex(file, vert_flags) \
       for _ in range(tagTable[m.vert.refid].nTag // vertex.size(vert_flags))]
    file.seek(tagTable[d.faces.refid].ofs)
    print('m3_import: !INFO! Reading Faces...')
    rawfaceTable = struct.unpack('H' * (tagTable[d.faces.refid].nTag), \
                    file.read(tagTable[d.faces.refid].nTag * 2))
    faceTable = []
    for i in range(1, len(rawfaceTable) + 1):
        faceTable.append(rawfaceTable[i - 1])
        if i % 3 == 0:    # Add a zero for the fourth index to the face.
            faceTable.append(0)
    print("m3_import: !INFO! Read %d vertices and %d faces" \
            % (len(verts), len(faceTable)))
    print('m3_import: !INFO! Adding Geometry...')
    mesh = bpy.data.meshes.new(os.path.basename(op.properties.filepath))
    mobj = bpy.data.objects.new(os.path.basename(op.properties.filepath), mesh)
    context.scene.objects.link(mobj)
    v, n = [], []
    for vert in verts:        # "Flatten" the vertex array...
        v.extend(vert.pos.v)
        n.extend(vert.normal)
    mesh.vertices.add(len(verts))
    mesh.faces.add(len(rawfaceTable) // 3)
    mesh.vertices.foreach_set('co', v)
    mesh.vertices.foreach_set('normal', n)
    mesh.faces.foreach_set('vertices_raw', faceTable)
    uvtex = mesh.uv_textures.new()
    for i, face in enumerate(mesh.faces):
        uf = uvtex.data[i]
        uf.uv1 = verts[faceTable[i * 4 + 0]].uv
        uf.uv2 = verts[faceTable[i * 4 + 1]].uv
        uf.uv3 = verts[faceTable[i * 4 + 2]].uv
        uf.uv4 = (0, 0)
    print('m3_import: !INFO! Importing materials...')
    material = bpy.data.materials.new('Mat00')
    mesh.materials.append(material)
    file.seek(tagTable[m.materials.refid].ofs)
    mm = mat(file)
    tex_map = [('use_map_color_diffuse', 0), ('use_map_specular', 2),\
                ('use_map_normal', 9)]
    for map, i in tex_map:
        file.seek(tagTable[mm.layers[i].refid].ofs)
        nref = layr(file).name
        file.seek(tagTable[nref.refid].ofs)
        name = bytes.decode(file.read(nref.entries - 1))
        name = os.path.basename(str(name))
        tex = bpy.data.textures.new(name=name, type='IMAGE')
        tex.image = load_image(name, os.path.dirname(op.filepath))
        if tex.image != None:
            print("m3_import: !INFO! Loaded %s" % (name))
        else:
            print("m3_import: !WARNING! Cannot find texture \"%s\"" % (name))
        mtex = material.texture_slots.add()
        mtex.texture = tex
        mtex.texture_coords = 'UV'
        if i == 9:
            mtex.normal_factor = 0.1    # Just a guess, seems to look nice
        mtex.use_map_color_diffuse = (i == 0)
        setattr(mtex, map, True)


class M3Importer(bpy.types.Operator):
    """Import from M3 file format (.m3)"""
    bl_idname = "import_mesh.blizzard_m3"
    bl_label = 'Import M3'
    bl_options = {'UNDO'}

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.

    filepath = StringProperty(
                subtype='FILE_PATH',
                )

    def execute(self, context):
        t = time.mktime(datetime.datetime.now().timetuple())
        with open(self.properties.filepath, 'rb') as file:
            print('Importing file', self.properties.filepath)
            read(file, context, self)
        t = time.mktime(datetime.datetime.now().timetuple()) - t
        print('Finished importing in', t, 'seconds')
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.add_fileselect(self)
        return {'RUNNING_MODAL'}
