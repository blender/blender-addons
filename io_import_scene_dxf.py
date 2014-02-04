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
    "name": "Import Autocad DXF Format (.dxf)",
    "author": "Thomas Larsson, Remigiusz Fiedler",
    "version": (0, 1, 6),
    "blender": (2, 63, 0),
    "location": "File > Import > Autocad (.dxf)",
    "description": "Import files in the Autocad DXF format (.dxf)",
    "warning": "Under construction! Visit Wiki for details.",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/Import-Export/DXF_Importer",
    "tracker_url": "https://developer.blender.org/T23480",
    "support": "OFFICIAL",
    "category": "Import-Export",
    }

"""
Release note by migius (DXF support maintainer) 2011.01.02:
Script supports only a small part of DXF specification:
- imports LINE, ARC, CIRCLE, ELLIPSE, SOLID, TRACE, POLYLINE, LWPOLYLINE
- imports TEXT, MTEXT
- supports 3d-rotation of entities (210 group)
- supports THICKNESS for SOLID, TRACE, LINE, ARC, CIRCLE, ELLIPSE
- ignores WIDTH, THICKNESS, BULGE in POLYLINE/LWPOLYLINE
- ignores face-data in POLYFACE / POLYMESH
- ignores TEXT 2d-rotation
- ignores hierarchies (BLOCK, INSERT, GROUP)
- ignores LAYER
- ignores COLOR, LINEWIDTH, LINESTYLE

This script is a temporary solution.
No functionality improvements are planed for this version.
The advanced importer from 2.49 will replace it in the future.

Installation:
Place this file to Blender addons directory
  (on Windows it is %Blender_directory%\2.53\scripts\addons\)
The script must be activated in "Addons" tab (user preferences).
Access it from File > Import menu.

History:
ver 0.1.6 - 2012.01.03 by migius and trumanblending for r.42615
- modified for recent changes to matrix indexing
ver 0.1.5 - 2011.02.05 by migius for r.34661
- changed support level to OFFICIAL
- fixed missing last point at building Mesh-ARCs (by pildanovak)
- fixed for changes in API and mathutils by campbell
ver 0.1.4 - 2011.01.13 by migius
- modified for latest API in rev.34300 (by Filiciss Muhgue)
ver 0.1.3 - 2011.01.02 by migius
- added draw curves as sequence for "Draw_as_Curve"
- added toggle "Draw as one" as user preset in UI
- added draw POINT as mesh-vertex
- added draw_THICKNESS for LINE, ARC, CIRCLE, ELLIPSE, LWPOLYLINE and POLYLINE
- added draw_THICKNESS for SOLID, TRACE
ver 0.1.2 - 2010.12.27 by migius
- added draw() for TRACE
- fixed wrong vertex order in SOLID
- added CIRCLE resolution as user preset in UI
- added closing segment for circular LWPOLYLINE and POLYLINE
- fixed registering for 2.55beta
ver 0.1.1 - 2010.09.07 by migius
- fixed dxf-file names recognition limited to ".dxf"
- fixed registering for 2.53beta
ver 0.1 - 2010.06.10 by Thomas Larsson
"""

__version__ = '.'.join([str(s) for s in bl_info['version']])

import os
import codecs
import math
from math import sin, cos, radians
import bpy
from mathutils import Vector, Matrix

#
#    Global flags
#

T_Merge = 0x01
T_NewScene = 0x02
T_Curves = 0x04
T_DrawOne = 0x08
T_Debug = 0x10
T_Verbose = 0x20
T_ThicON = 0x40

toggle = T_Merge | T_NewScene | T_DrawOne | T_ThicON
theCircleRes = 32
theMergeLimit = 1e-4

#
#    class CSection:
#

class CSection:
    type = None

    def __init__(self):
        self.data = []

    def display(self):
        print("Section", self.type)
        for datum in self.data:
            datum.display()

#
#    class CTable:
#

class CTable:
    def __init__(self):
        self.type = None
        self.name = None
        self.handle = None
        self.owner = None
        self.subclass = None
        self.nEntries = 0
    def display(self):
        print("Table %s %s %s %s %s %d" % (self.type, self.name, self.handle, self.owner, self.subclass, self.nEntries))

#
#    class CEntity:
#
class CEntity:
    def __init__(self, typ, drawtype):
        self.type = typ
        self.drawtype = drawtype
        self.handle = None
        self.owner = None
        self.subclass = None
        self.layer = 0
        self.color = 0
        self.invisible = 0
        self.linetype_name = ''
        self.linetype_scale = 1.0
        self.paperspace = 0
        #self.normal = Vector((0,0,1))

    def display(self):
        print("Entity %s %s %s %s %s %s %x" % 
            (self.type, self.handle, self.owner, self.subclass, self.layer, self.color, self.invisible))

    def build(self, vn=0):
        global toggle
        if toggle & T_Debug:
            raise NameError("Warning: can not build - unsupported entity type: %s" % self.type)
        return(([], [], [], vn)) 

    def draw(self):
        global toggle
        if toggle & T_Debug:
            raise NameError("Warning: can not draw - unsupported entity type: %s" % self.type)
        return


DxfCommonAttributes = {
    5 : 'handle',
    6 : 'linetype_name',
    8 : 'layer',
    48 : 'linetype_scale',
    60 : 'invisible',
    62 : 'color',
    67 : 'paperspace',
    100 : 'subclass',
    330 : 'owner',
    360 : 'owner',
}

#
#    class C3dFace(CEntity):
#    10 : 'point0.x', 20 : 'point0.y', 30 : 'point0.z', 
#    11 : 'point1.x', 21 : 'point1.y', 31 : 'point1.z', 
#    12 : 'point2.x', 22 : 'point2.y', 32 : 'point2.z', 
#    13 : 'point3.x', 23 : 'point3.y', 33 : 'point3.z', 
#    70 : 'flags',
#

class C3dFace(CEntity):
    def __init__(self):
        CEntity.__init__(self, '3DFACE', 'Mesh')
        self.point0 = Vector()
        self.point1 = Vector()
        self.point2 = Vector()
        self.point3 = Vector()

    def display(self):
        CEntity.display(self)
        print(self.point0)
        print(self.point1)
        print(self.point2)
        print(self.point3)

    def build(self, vn=0):
        verts = [self.point0, self.point1, self.point2]
        if self.point3 == Vector((0,0,0)) or self.point2 == self.point3:
            faces = [(vn+0, vn+1, vn+2)]
            vn += 3
        else:
            verts.append( self.point3 )
            faces = [(vn+0, vn+1, vn+2, vn+3)]
            vn += 4            
        return((verts, [], faces, vn))

#
#    class C3dSolid(CEntity):
#    1 : 'data', 3 : 'more', 70 : 'version',
#

class C3dSolid(CEntity):
    def __init__(self):
        CEntity.__init__(self, '3DSOLID', 'Mesh')
        self.data = None
        self.more = None
        self.version = 0

#
#    class CAcadProxyEntity(CEntity):
#    70 : 'format',
#    90 : 'id', 91 : 'class', 92 : 'graphics_size', 93 : 'entity_size', 95: 'format',
#    310 : 'data', 330 : 'id1', 340 : 'id2', 350 : 'id3', 360 : 'id4', 
#

class CAcadProxyEntity(CEntity):
    def __init__(self):
        CEntity.__init__(self, 'ACAD_PROXY_ENTITY', None)


#
#    class CArc(CEntity):
#    10 : 'center.x', 20 : 'center.y', 30 : 'center.z', 
#    40 : 'radius',
#    50 : 'start_angle', 51 : 'end_angle'
#

class CArc(CEntity):
    def __init__(self):
        CEntity.__init__(self, 'ARC', 'Mesh')
        self.center = Vector()
        self.radius = 0.0
        self.start_angle = 0.0
        self.end_angle = 0.0
        self.thickness = 0.0
        self.normal = Vector((0,0,1))
        
    def display(self):
        CEntity.display(self)
        print(self.center)
        print("%.4f %.4f %.4f " % (self.radius, self.start_angle, self.end_angle))

    def build(self, vn=0):
        start, end = self.start_angle, self.end_angle
        if end > 360: end = end % 360.0
        if end < start: end +=360.0
        # angle = end - start  # UNUSED

        deg2rad = math.pi/180.0
        start *= deg2rad
        end *= deg2rad
        dphi = end - start
        phi0 = start
        w = dphi/theCircleRes
        r = self.radius
        center = self.center
        v0 = vn
        points = []
        edges, faces = [], []
        for n in range(theCircleRes + 1):
            s = math.sin(n*w + phi0)
            c = math.cos(n*w + phi0)
            v = center + Vector((r*c, r*s, 0.0))
            points.append(v)
        pn = len(points)
        thic = self.thickness
        t_vector = Vector((0, 0, thic))
        if thic != 0 and (toggle & T_ThicON):
            thic_points = [v + t_vector for v in points]
            if thic < 0.0:
                thic_points.extend(points)
                points = thic_points
            else:
                points.extend(thic_points)
            faces = [(v0+nr+0,v0+nr+1,v0+pn+nr+1,v0+pn+nr+0) for nr in range(pn)]
            faces.pop()
            self.drawtype = 'Mesh'
            vn += 2*pn
        else:
            edges = [(v0+nr+0,v0+nr+1) for nr in range(pn)]
            edges.pop()
            vn += pn

        if self.normal!=Vector((0,0,1)):
            ma = getOCS(self.normal)
            if ma:
                #ma.invert()
                points = [ma * v for v in points]
        #print ('arc vn=', vn)
        #print ('faces=', len(faces))
        return ((points, edges, faces, vn))

#
#    class CArcAlignedText(CEntity):
#    1 : 'text', 2 : 'font', 3 : 'bigfont', 7 : 'style',
#    10 : 'center.x', 20 : 'center.y', 30 : 'center.z', 
#    40 : 'radius', 41 : 'width', 42 : 'height', 43 : 'spacing', 
#    44 : 'offset', 45 : 'right_offset', 46 : 'left_offset', 
#    50 : 'start_angle', 51 : 'end_angle',
#    70 : 'order', 71 : 'direction', 72 : 'alignment', 73 : 'side', 
#    74 : 'bold', 75 : 'italic', 76 : 'underline',
#    77 : 'character_set', 78 : 'pitch', 79 'fonttype',
#    90 : 'color',
#    280 : 'wizard', 330 : 'id'
#

class CArcAlignedText(CEntity):
    def __init__(self):
        CEntity.__init__(self, 'ARCALIGNEDTEXT', 'Mesh')
        self.text = ""
        self.style = ""
        self.center = Vector()
        self.radius = 0.0
        self.width = 1.0
        self.height = 1.0
        self.spacing = 1.0
        self.offset = 0.0
        self.right_offset = 0.0
        self.left_offset = 0.0
        self.start_angle = 0.0
        self.end_angle = 0.0
        self.order = 0
        self.directions = 0
        self.alignment = 0
        self.side = 0
        self.bold = 0
        self.italic = 0
        self.underline = 0
        self.character_set = 0
        self.pitch = 0
        self.fonttype = 0
        self.color = 0
        self.wizard = None
        self.id = None
        self.normal = Vector((0,0,1))


#
#    class CAttdef(CEntity):
#    1 : 'text', 2 : 'tag', 3 : 'prompt', 7 : 'style',
#    10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
#    11 : 'alignment_point.x', 21 : 'alignment_point.y', 31 : 'alignment_point.z', 
#    40 : 'height', 41 : 'x_scale', 
#    50 : 'rotation_angle', 51 : 'oblique_angle', 
#    70 : 'flags', 71 : 'text_generation_flags', 
#    72 : 'horizontal_justification',  74 : 'vertical_justification',    
#

class CAttdef(CEntity):
    def __init__(self):
        CEntity.__init__(self, 'ATTDEF', None)
        self.value = ""
        self.tag = ""
        self.prompt = ""
        self.style = ""
        self.insertion_point = Vector()
        self.alignment_point = Vector()
        self.height = 1.0
        self.x_scale = 1.0
        self.rotation_angle = 0.0
        self.oblique_angle = 0.0
        self.flags = 0
        self.text_generation_flags = 0
        self.horizontal_justification = 0.0
        self.vertical_justification = 0.0
        self.normal = Vector((0,0,1))

    def draw(self):
        drawText(self.text,  self.insertion_point, self.height, self.x_scale, self.rotation_angle, self.oblique_angle, self.normal)
        return

#
#    class CAttrib(CEntity):
#    1 : 'text', 2 : 'tag', 3 : 'prompt', 7 : 'style',
#    10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
#    11 : 'alignment_point.x', 21 : 'alignment_point.y', 31 : 'alignment_point.z', 
#    40 : 'height', 41 : 'x_scale', 
#    50 : 'rotation_angle', 51 : 'oblique_angle', 
#    70 : 'flags', 73 : 'length', 
#    71 : 'text_generation_flags', 72 : 'horizontal_justification',  74 : 'vertical_justification',     
#

class CAttrib(CEntity):
    def __init__(self):
        CEntity.__init__(self, 'ATTRIB', None)
        self.text = ""
        self.tag = ""
        self.prompt = ""

        self.style = ""
        self.insertion_point = Vector()
        self.alignment_point = Vector()
        self.height = 1.0
        self.x_scale = 1.0
        self.rotation_angle = 0.0
        self.oblique_angle = 0.0
        self.flags = 0
        self.length = 1.0
        self.text_generation_flags = 0
        self.horizontal_justification = 0.0
        self.vertical_justification = 0.0
        self.normal = Vector((0,0,1))

    def draw(self):
        drawText(self.text,  self.insertion_point, self.height, self.x_scale, self.rotation_angle, self.oblique_angle, self.normal)
        return


#
#    class CBlock(CEntity):
#    1 : 'xref', 2 : 'name', 3 : 'also_name', 
#    10 : 'base_point.x', 20 : 'base_point.y', 30 : 'base_point.z', 
#    40 : 'size', 41 : 'x_scale', 
#    50 : 'rotation_angle', 51 : 'oblique_angle',     
#    70 : 'flags', 
#

class CBlock(CEntity):
    def __init__(self):
        CEntity.__init__(self, 'BLOCK', None)
        self.xref = ""
        self.name = ""
        self.also_name = ""
        self.base_point = Vector()
        self.size = 1.0
        self.x_scale = 1.0
        self.rotation_angle = 0.0
        self.oblique_angle = 0.0
        self.flags = 0
        self.normal = Vector((0,0,1))

    def display(self):
        CEntity.display(self)
        print("%s %s %s " % (self.xref, self.name, self.also_name))
        print(self.base_point)

    def draw(self):
        # Todo
        return

#
#    class CCircle(CEntity):
#    10 : 'center.x', 20 : 'center.y', 30 : 'center.z', 
#    40 : 'radius'
#

class CCircle(CEntity):
    def __init__(self):
        CEntity.__init__(self, 'CIRCLE', 'Mesh')
        self.center = Vector()
        self.radius = 0.0
        self.thickness = 0.0
        self.normal = Vector((0,0,1))

    def display(self):
        CEntity.display(self)
        print(self.center)
        print("%.4f" % self.radius)

    def build(self, vn=0):
        w = 2*math.pi/theCircleRes
        r = self.radius
        center = self.center
        points = []
        edges, faces = [], []
        v0 = vn
        for n in range(theCircleRes):
            s = math.sin(n*w)
            c = math.cos(n*w)
            v = center + Vector((r*c, r*s, 0))
            points.append(v)

        pn = len(points)
        thic = self.thickness
        t_vector = Vector((0, 0, thic))
        if thic != 0 and (toggle & T_ThicON):
            thic_points = [v + t_vector for v in points]
            if thic < 0.0:
                thic_points.extend(points)
                points = thic_points
            else:
                points.extend(thic_points)
            faces = [(v0+nr,v0+nr+1,pn+v0+nr+1,pn+v0+nr) for nr in range(pn)]
            nr = pn -1
            faces[-1] = (v0+nr,v0,pn+v0,pn+v0+nr)
            self.drawtype = 'Mesh'
            vn += 2*pn
        else:
            edges = [(v0+nr,v0+nr+1) for nr in range(pn)]
            nr = pn -1
            edges[-1] = (v0+nr,v0)
            vn += pn
        if self.normal!=Vector((0,0,1)):
            ma = getOCS(self.normal)
            if ma:
                #ma.invert()
                points = [ma * v for v in points]
        #print ('cir vn=', vn)
        #print ('faces=',len(faces))
        return( (points, edges, faces, vn) )
            
#
#    class CDimension(CEntity):
#    1 : 'text', 2 : 'name', 3 : 'style',
#    10 : 'def_point.x', 20 : 'def_point.y', 30 : 'def_point.z', 
#    11 : 'mid_point.x', 21 : 'mid_point.y', 31 : 'mid_point.z', 
#    12 : 'vector.x', 22 : 'vector.y', 32 : 'vector.z', 
#    13 : 'def_point2.x', 23 : 'def_point2.y', 33 : 'def_point2.z', 
#    14 : 'vector2.x', 24 : 'vector2.y', 34 : 'vector2.z', 
#    15 : 'vector3.x', 25 : 'vector3.y', 35 : 'vector3.z', 
#    16 : 'vector4.x', 26 : 'vector4.y', 36 : 'vector4.z', 
#    70 : 'dimtype',
#

class CDimension(CEntity):
    def __init__(self):
        CEntity.__init__(self, 'DIMENSION', None)
        self.text = ""
        self.name = ""
        self.style = ""
        self.def_point = Vector()
        self.mid_point = Vector()
        self.vector = Vector()
        self.def_point2 = Vector()
        self.vector2 = Vector()
        self.vector3 = Vector()
        self.vector4 = Vector()
        self.dimtype = 0
        self.normal = Vector((0,0,1))

    def draw(self):
        return

#
#    class CEllipse(CEntity):
#    10 : 'center.x', 20 : 'center.y', 30 : 'center.z', 
#    11 : 'end_point.x', 21 : 'end_point.y', 31 : 'end_point.z', 
#    40 : 'ratio', 41 : 'start', 42 : 'end',
#

class CEllipse(CEntity):
    def __init__(self):
        CEntity.__init__(self, 'ELLIPSE', 'Mesh')
        self.center = Vector()
        self.end_point = Vector()
        self.ratio = 1.0
        self.start = 0.0
        self.end = 2*math.pi
        self.thickness = 0.0
        self.normal = Vector((0,0,1))

    def display(self):
        CEntity.display(self)
        print(self.center)
        print("%.4f" % self.ratio)
                
    def build(self, vn=0):
        dphi = (self.end - self.start)
        phi0 = self.start
        w = dphi/theCircleRes
        r = self.end_point.length
        f = self.ratio
        a = self.end_point.x/r
        b = self.end_point.y/r
        center = self.center
        v0 = vn
        points = []
        edges, faces = [], []
        for n in range(theCircleRes):
            x = r*math.sin(n*w + phi0)
            y = f*r*math.cos(n*w + phi0)
            v = (center.x - a*x + b*y, center.y - a*y - b*x, center.z)
            points.append(v)

        pn = len(points)
        thic = self.thickness
        t_vector = Vector((0, 0, thic))
        if thic != 0 and (toggle & T_ThicON):
            thic_points = [v + t_vector for v in points]
            if thic < 0.0:
                thic_points.extend(points)
                points = thic_points
            else:
                points.extend(thic_points)
            faces = [(v0+nr,v0+nr+1,pn+v0+nr+1,pn+v0+nr) for nr in range(pn)]
            nr = pn -1
            faces[-1] = (v0+nr,v0,pn+v0,pn+v0+nr)
            #self.drawtype = 'Mesh'
            vn += 2*pn
        else:
            edges = [(v0+nr,v0+nr+1) for nr in range(pn)]
            nr = pn -1
            edges[-1] = (v0+nr,v0)
            vn += pn


        if thic != 0 and (toggle & T_ThicON):
            pass
        if self.normal!=Vector((0,0,1)):
            ma = getOCS(self.normal)
            if ma:
                #ma.invert()
                points = [ma * v for v in points]
        return ((points, edges, faces, vn))

#
#    class CHatch(CEntity):
#    2 : 'pattern',
#    10 : 'point.x', 20 : 'point.y', 30 : 'point.z', 
#    41 : 'scale', 47 : 'pixelsize', 52 : 'angle',
#    70 : 'fill', 71 : 'associativity', 75: 'style', 77 : 'double', 
#    78 : 'numlines', 91 : 'numpaths', 98 : 'numseeds',
#

class CHatch(CEntity):
    def __init__(self):
        CEntity.__init__(self, 'HATCH', None)
        self.pattern = 0
        self.point = Vector()
        self.scale = 1.0
        self.pixelsize = 1.0
        self.angle = 0.0
        self.fill = 0
        self.associativity = 0
        self.style = 0
        self.double = 0
        self.numlines = 0
        self.numpaths = 0
        self.numseeds = 0
        self.normal = Vector((0,0,1))


#    class CImage(CEntity):
#    10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
#    11 : 'u_vector.x', 21 : 'u_vector.y', 31 : 'u_vector.z', 
#    12 : 'v_vector.x', 22 : 'v_vector.y', 32 : 'v_vector.z', 
#    13 : 'size.x', 23 : 'size.y', 33 : 'size.z', 
#    14 : 'clip.x', 24 : 'clip.y', 34 : 'clip.z', 
#    70 : 'display', 71 : 'cliptype', 
#    90 : 'version',
#    280 : 'clipstate', 281 : 'brightness', 282 : 'contrast', 283 : 'fade', 
#    340 : 'image', 360 : 'reactor'
#

class CImage(CEntity):
    def __init__(self):
        CEntity.__init__(self, 'IMAGE', None)
        self.insertion_point = Vector()
        self.u_vector = Vector()
        self.v_vector = Vector()
        self.size = Vector()
        self.clip = Vector()
        self.display = 0
        self.cliptype = 0
        self.version = 1
        self.clipstate = 0
        self.brightness = 0
        self.constrast = 0
        self.fade = 0
        self.image = None
        self.reactor = None
        self.normal = Vector((0,0,1))

#
#    class CInsert(CEntity):
#    1 : 'attributes_follow', 2 : 'name',
#    10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
#    41 : 'x_scale', 42 : 'y_scale', 43 : 'z_scale', 
#    44 : 'column_spacing', 45 : 'row_spacing', 
#    50 : 'rotation_angle', 66 : 'attributes_follow',
#    70 : 'column_count', 71 : 'row_count', 
#

class CInsert(CEntity):
    def __init__(self):
        CEntity.__init__(self, 'INSERT', None)
        self.attributes_follow = 1
        self.name = ""
        self.insertion_point = Vector()
        self.x_scale = 1.0
        self.y_scale = 1.0
        self.z_scale = 1.0
        self.column_spacing = 1.0
        self.row_spacing = 1.0
        self.rotation_angle = 0.0
        self.column_count = 1
        self.row_count = 1
        self.attributes_follow = 0
        self.normal = Vector((0,0,1))

    def display(self):
        CEntity.display(self)
        print(self.insertion_point)

    def draw(self):
        # Todo
        return

#
#    class CLeader(CEntity):
#    3 : 'style',
#    10 : ['new_vertex(data)'], 20 : 'vertex.y', 30 : 'vertex.z', 
#    40 : 'height', 41 : 'width',
#    71 : 'arrowhead', 72 : 'pathtype', 73 : 'creation', 
#    74 : 'hookdir', 75 : 'hookline', 76 : 'numverts', 77 : 'color',
#    210 : 'normal.x', 220 : 'normal.y', 230 : 'normal.z', 
#    211 : 'horizon.x', 221 : 'horizon.y', 231 : 'horizon.z', 
#    212 : 'offset_ins.x', 222 : 'offset_ins.y', 232 : 'offset_ins.z', 
#    213 : 'offset_ann.x', 223 : 'offset_ann.y', 233 : 'offset_ann.z', 
#

class CLeader(CEntity):
    def __init__(self):
        CEntity.__init__(self, 'LEADER', 'Mesh')
        self.style = ""
        self.vertex = None
        self.verts = []
        self.height = 1.0
        self.width = 1.0
        self.arrowhead = 0
        self.pathtype = 0
        self.creation = 0
        self.hookdir = 0
        self.hookline = 0
        self.numverts = 0
        self.color = 0
        self.normal = Vector((0,0,1))
        self.horizon = Vector()
        self.offset_ins = Vector()
        self.offset_ann = Vector()

    def new_vertex(self, data):
        self.vertex = Vector()
        self.vertex.x = data
        self.verts.append(self.vertex)

    def build(self, vn=0):
        edges = []
        for v in self.verts:
            edges.append((vn, vn+1))
            vn += 1
        edges.pop()
        return (self.verts, edges, [], vn)

#    class CLwPolyLine(CEntity):
#    10 : ['new_vertex(data)'], 20 : 'vertex.y', 30 : 'vertex.z', 
#    38 : 'elevation', 39 : 'thickness',
#    40 : 'start_width', 41 : 'end_width', 42 : 'bulge', 43 : 'constant_width',
#    70 : 'flags', 90 : 'numverts'
#

class CLWPolyLine(CEntity):
    def __init__(self):
        CEntity.__init__(self, 'LWPOLYLINE', None)
        self.vertex = None
        self.verts = []
        self.elevation = 0
        self.thickness = 0.0
        self.start_width = 0.0
        self.end_width = 0.0
        self.bulge = 0.0
        self.constant_width = 0.0
        self.flags = 0
        self.numverts = 0
        self.normal = Vector((0,0,1))

    def new_vertex(self, data):
        self.vertex = Vector()
        self.vertex.x = data
        self.verts.append(self.vertex)

    def build(self, vn=0):
        edges = []
        v_start = vn
        for v in self.verts:
            edges.append((vn, vn+1))
            vn += 1
        if self.flags & PL_CLOSED:
            edges[-1] = (vn-1, v_start)
        else:
            edges.pop()
        verts = self.verts
        if self.normal!=Vector((0,0,1)):
            ma = getOCS(self.normal)
            if ma:
                #ma.invert()
                verts = [ma * v for v in verts]
        return (verts, edges, [], vn-1)
        
#
#    class CLine(CEntity):
#    10 : 'start_point.x', 20 : 'start_point.y', 30 : 'start_point.z', 
#    11 : 'end_point.x', 21 : 'end_point.y', 31 : 'end_point.z', 
#    39 : 'thickness',
#

class CLine(CEntity):
    def __init__(self):
        CEntity.__init__(self, 'LINE', 'Mesh')
        self.start_point = Vector()
        self.end_point = Vector()
        self.thickness = 0.0
        self.normal = Vector((0,0,1))

    def display(self):
        CEntity.display(self)
        print(self.start_point)
        print(self.end_point)

    def build(self, vn=0):
        points = [self.start_point, self.end_point]
        faces, edges = [], []
        n = vn
        thic = self.thickness
        if thic != 0 and (toggle & T_ThicON):
            t_vector = thic * self.normal
            #print 'deb:thic_vector: ', t_vector #---------------------
            points.extend([v + t_vector for v in points])
            faces = [[0+n, 1+n, 3+n, 2+n]]
            self.drawtype = 'Mesh'
        else:
            edges = [[0+n, 1+n]]
        vn +=2
        return((points, edges, faces, vn))

#    class CMLine(CEntity):
#    10 : 'start_point.x', 20 : 'start_point.y', 30 : 'start_point.z', 
#    11 : ['new_vertex(data)'], 21 : 'vertex.y', 31 : 'vertex.z', 
#    12 : ['new_seg_dir(data)'], 22 : 'seg_dir.y', 32 : 'seg_dir.z', 
#    13 : ['new_miter_dir(data)'], 23 : 'miter_dir.y', 33 : 'miter_dir.z', 
#    40 : 'scale', 41 : 'elem_param', 42 : 'fill_param',
#    70 : 'justification', 71 : 'flags'
#    72 : 'numverts', 73 : 'numelems', 74 : 'numparam', 75 : 'numfills',
#    340 : 'id'
#

class CMLine(CEntity):
    def __init__(self):
        CEntity.__init__(self, 'MLINE', None)
        self.start_point = Vector()
        self.vertex = None
        self.seg_dir = None
        self.miter_dir = None
        self.verts = []
        self.seg_dirs = []
        self.miter_dirs = []
        self.scale = 1.0
        self.elem_param = 0
        self.fill_param = 0
        self.justification = 0
        self.flags = 0
        self.numverts = 0
        self.numelems = 0
        self.numparam = 0
        self.numfills = 0
        self.id = 0
        self.normal = Vector((0,0,1))

    def new_vertex(self, data):
        self.vertex = Vector()
        self.vertex.x = data
        self.verts.append(self.vertex)

    def new_seg_dir(self, data):
        self.seg_dir = Vector()
        self.seg_dir.x = data
        self.seg_dirs.append(self.seg_dir)

    def new_miter_dir(self, data):
        self.miter_dir = Vector()
        self.miter_dir.x = data
        self.miter_dirs.append(self.miter_dir)



#
#    class CMText(CText):
#    1 : 'text', 3: 'more_text', 7 : 'style',
#    10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
#    11 : 'alignment_point.x', 21 : 'alignment_point.y', 31 : 'alignment_point.z', 
#    40 : 'nominal_height', 41 : 'reference_width', 42: 'width', 43 : 'height', 44 : 'line_spacing',
#    50 : 'rotation_angle', 
#    71 : 'attachment_point', 72 : 'drawing_direction',  73 : 'spacing_style',    
#

class CMText(CEntity):
    def __init__(self):
        CEntity.__init__(self, 'MTEXT', 'Text')
        self.text = ""
        self.more_text = ""
        self.style = ""
        self.insertion_point = Vector()
        self.alignment_point = Vector()
        self.nominal_height = 1.0
        self.reference_width = 1.0
        self.width = 1.0
        self.height = 1.0
        self.rotation_angle = 0.0
        self.attachment_point = 0
        self.drawing_direction = 0
        self.spacing_style = 0
        self.normal = Vector((0,0,1))

    def display(self):
        CEntity.display(self)
        print("%s %s" % (self.text, self.style))
        print('MTEXTinsertion_point=',self.insertion_point)
        print('MTEXTalignment_point=',self.alignment_point)

    def draw(self):
        drawText(self.text,  self.insertion_point, self.height, self.width, self.rotation_angle, 0.0, self.normal)
        return

#
#    class CPoint(CEntity):
#    10 : 'point.x', 20 : 'point.y', 30 : 'point.z', 
#    39 : 'thickness', 50 : 'orientation'
#

class CPoint(CEntity):
    def __init__(self):
        CEntity.__init__(self, 'POINT', 'Mesh')
        self.point = Vector()
        self.thickness = 0.0
        self.orientation = 0.0

    def display(self):
        CEntity.display(self)
        print(self.point)
        print("%.4f" % self.orientation)

    def build(self, vn=0):
        # draw as mesh-vertex
        verts = [self.point]
        return((verts, [], [], vn+1))

    def draw(self):
        #todo
        # draw as empty-object
        # loc = self.point  # UNUSED
        #bpy.ops.object.new('DXFpoint')
        pass

#
#    class CPolyLine(CEntity):
#    1 : 'verts_follow', 2 : 'name',
#    10 : 'elevation.x', 20 : 'elevation.y', 30 : 'elevation.z', 
#    40 : 'start_width', 41 : 'end_width', 
#    66 : 'verts_follow_flag',
#    70 : 'flags', 71 : 'row_count', 72 : 'column_count', 
#    73 : 'row_density', 74 : 'column_density', 75 : 'linetype',
#

class CPolyLine(CEntity):
    def __init__(self):
        CEntity.__init__(self, 'POLYLINE', 'Mesh')
        self.verts = []
        self.verts_follow = 1
        self.name = ""
        self.elevation = Vector()
        self.thickness = 0.0
        self.start_width = 0.0
        self.end_width = 0.0
        self.verts_follow_flags = 0
        self.flags = 0
        self.row_count = 1
        self.column_count = 1
        self.row_density = 1.0
        self.column_density = 1.0
        self.linetype = 1
        self.normal = Vector((0,0,1))

    def display(self):
        CEntity.display(self)
        print("VERTS")
        for v in self.verts:
            print(v.location)
        print("END VERTS")

    def build(self, vn=0):
        verts = []
        lines = []
        v_start = vn
        for vert in self.verts:
            verts.append(vert.location)
            lines.append((vn, vn+1))
            vn += 1
        if self.flags & PL_CLOSED:
            lines[-1] = (vn-1, v_start)
        else:
            lines.pop()
        if self.normal!=Vector((0,0,1)):
            ma = getOCS(self.normal)
            if ma:
                verts = [ma * v for v in verts]
        return((verts, lines, [], vn-1))

#
#    class CShape(CEntity):
#    2 : 'name', 
#    10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
#    39 : 'thickness',
#    40 : 'size', 41 : 'x_scale', 
#    50 : 'rotation_angle', 51 : 'oblique_angle',     
#

class CShape(CEntity):
    def __init__(self):
        CEntity.__init__(self, 'SHAPE', None)
        self.name = ""
        self.insertion_point = Vector()
        self.thickness = 0.0
        self.size = 1.0
        self.x_scale = 1.0
        self.rotation_angle = 0.0
        self.oblique_angle = 0.0

    def display(self):
        CEntity.display(self)
        print("%s" % (self.name))
        print(self.insertion_point)

#
#    class CSpline(CEntity):
#    10 : ['new_control_point(data)'], 20 : 'control_point.y', 30 : 'control_point.z', 
#    11 : ['new_fit_point(data)'], 21 : 'fit_point.y', 31 : 'fit_point.z', 
#    40 : ['new_knot_value(data)'], 
#    12 : 'start_tangent.x', 22 : 'start_tangent.y', 32 : 'start_tangent.z', 
#    13 : 'end_tangent.x', 23 : 'end_tangent.y', 33 : 'end_tangent.z', 
#    41 : 'weight', 42 : 'knot_tol', 43 : 'control_point_tol', 44 : 'fit_tol',
#    70 : 'flag', 71 : 'degree', 
#    72 : 'num_knots', 73 : 'num_control_points', 74 : 'num_fit_points',
#    210 : 'normal.x', 220 : 'normal.y', 230 : 'normal.z', 
#

class CSpline(CEntity):
    def __init__(self):
        CEntity.__init__(self, 'SPLINE', 'Mesh')
        self.control_points = []
        self.fit_points = []
        self.knot_values = []
        self.control_point = None
        self.fit_point = None
        self.knot_value = None
        self.start_tangent = Vector()
        self.end_tangent = Vector()
        self.weight = 1.0
        self.knot_tol = 1e-6
        self.control_point_tol = 1e-6
        self.fit_tol = 1e-6
        self.flag = 0
        self.degree = 3
        self.num_knots = 0
        self.num_control_points = 0
        self.num_fit_points = 0
        self.thickness = 0.0
        self.normal = Vector((0,0,1))
        
    def new_control_point(self, data):
        self.control_point = Vector()
        self.control_point.x = data
        self.control_points.append(self.control_point)
        
    def new_fit_point(self, data):
        self.fit_point = Vector()
        self.fit_point.x = data
        self.fit_points.append(self.fit_point)

    def new_knot_value(self, data):
        self.knot_value = data
        self.knot_values.append(self.knot_value)
        
    def display(self):
        #not testet yet (migius)
        CEntity.display(self)
        print("CONTROL")
        for p in self.control_points:
            print(p)
        print("FIT")
        for p in self.fit_points:
            print(p)
        print("KNOT")
        for v in self.knot_values:
            print(v)

    def build(self, vn=0):
        verts = []
        lines = []
        for vert in self.control_points:
            verts.append(vert)
            lines.append((vn, vn+1))
            vn += 1
        lines.pop()
        return((verts, lines, [], vn))


#
#    class CSolid(CEntity):
#    10 : 'point0.x', 20 : 'point0.y', 30 : 'point0.z', 
#    11 : 'point1.x', 21 : 'point1.y', 31 : 'point1.z', 
#    12 : 'point2.x', 22 : 'point2.y', 32 : 'point2.z', 
#    13 : 'point3.x', 23 : 'point3.y', 33 : 'point3.z', 
#    39 : 'thickness',
#

class CSolid(CEntity):
    def __init__(self):
        CEntity.__init__(self, 'SOLID', 'Mesh')
        self.point0 = Vector()
        self.point1 = Vector()
        self.point2 = Vector()
        self.point3 = Vector()
        self.normal = Vector((0,0,1))
        self.thickness = 0.0
        
    def display(self):
        CEntity.display(self)
        print(self.point0)
        print(self.point1)
        print(self.point2)
        print(self.point3)

    def build(self, vn=0):
        points, edges, faces = [],[],[]
        if self.point2 == self.point3:
            points = [self.point0, self.point1, self.point2]
        else:
            points = [self.point0, self.point1, self.point2, self.point3]
        pn = len(points)
        v0 = vn
        
        thic = self.thickness
        t_vector = Vector((0, 0, thic))
        if thic != 0 and (toggle & T_ThicON):
            thic_points = [v + t_vector for v in points]
            if thic < 0.0:
                thic_points.extend(points)
                points = thic_points
            else:
                points.extend(thic_points)

            if   pn == 4:
                faces = [[0,1,3,2], [4,6,7,5], [0,4,5,1],
                         [1,5,7,3], [3,7,6,2], [2,6,4,0]]
            elif pn == 3:
                faces = [[0,1,2], [3,5,4], [0,3,4,1], [1,4,5,2], [2,5,3,0]]
            elif pn == 2: faces = [[0,1,3,2]]
            vn += 2*pn
        else:
            if   pn == 4: faces = [[0,2,3,1]]
            elif pn == 3: faces = [[0,2,1]]
            elif pn == 2:
                edges = [[0,1]]
                self.drawtype = 'Mesh'
            vn += pn
        if self.normal!=Vector((0,0,1)):
            ma = getOCS(self.normal)
            if ma:
                points = [ma * v for v in points]
        return((points, edges, faces, vn))
        
#
#    class CText(CEntity):
#    1 : 'text', 7 : 'style',
#    10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
#    11 : 'alignment_point.x', 21 : 'alignment_point.y', 31 : 'alignment_point.z', 
#    40 : 'height', 41 : 'x_scale', 
#    50 : 'rotation_angle', 51 : 'oblique_angle', 
#    71 : 'flags', 72 : 'horizontal_justification',  73 : 'vertical_justification',    
#

class CText(CEntity):
    def __init__(self):
        CEntity.__init__(self, 'TEXT', 'Text')
        self.text = ""
        self.style = ""
        self.insertion_point = Vector()
        self.alignment_point = Vector()
        self.height = 1.0
        self.x_scale = 1.0
        self.rotation_angle = 0.0
        self.oblique_angle = 0.0
        self.flags = 0
        self.horizontal_justification = 0.0
        self.vertical_justification = 0.0
        self.thickness = 0.0
        self.normal = Vector((0,0,1))
       
    def display(self):
        CEntity.display(self)
        print("%s %s" % (self.text, self.style))
        print(self.insertion_point)
        print(self.alignment_point)
        
    def draw(self):
        drawText(self.text,  self.insertion_point, self.height, self.x_scale, self.rotation_angle, self.oblique_angle, self.normal)
        return


def drawText(text, loc, size, spacing, angle, shear, normal=Vector((0,0,1))):
    #print('angle_deg=',angle)
    bpy.ops.object.text_add(
        view_align=False, 
        enter_editmode=False, 
        location= loc, 
        #rotation=(0, 0, angle), #need radians here
        )
    cu = bpy.context.object.data
    cu.body = text
    cu.size = size #up 2.56
    cu.space_word = spacing #up 2.56
    cu.shear = shear
    if angle!=0.0 or normal!=Vector((0,0,1)):
        obj = bpy.context.object
        transform(normal, angle, obj)
    return

#
#    class CTolerance(CEntity):
#    3 : 'style',
#    10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
#    11 : 'direction.x', 21 : 'direction.y', 31 : 'direction.z', 
#

class CTolerance(CEntity):
    def __init__(self):
        CEntity.__init__(self, 'TOLERANCE', None)
        self.stype = ""
        self.insertion_point = Vector()
        self.direction = Vector()

#
#    class CTrace(CEntity):
#    10 : 'point0.x', 20 : 'point0.y', 30 : 'point0.z', 
#    11 : 'point1.x', 21 : 'point1.y', 31 : 'point1.z', 
#    12 : 'point2.x', 22 : 'point2.y', 32 : 'point2.z', 
#    13 : 'point3.x', 23 : 'point3.y', 33 : 'point3.z', 
#    39 : 'thickness',
#

class CTrace(CEntity):
    def __init__(self):
        CEntity.__init__(self, 'TRACE', 'Mesh')
        self.point0 = Vector()
        self.point1 = Vector()
        self.point2 = Vector()
        self.point3 = Vector()
        self.normal = Vector((0,0,1))
        self.thickness = 0.0
    
    def display(self):
        CEntity.display(self)
        print(self.point0)
        print(self.point1)
        print(self.point2)
        print(self.point3)
   
    def build(self, vn=0):
        points, edges, faces = [],[],[]
        if self.point2 == self.point3:
            points = [self.point0, self.point2, self.point1]
        else:
            points = [self.point0, self.point2, self.point1, self.point3]
        pn = len(points)
        v0 = vn
        thic = self.thickness
        t_vector = Vector((0, 0, thic))
        if thic != 0 and (toggle & T_ThicON):
            thic_points = [v + t_vector for v in points]
            if thic < 0.0:
                thic_points.extend(points)
                points = thic_points
            else:
                points.extend(thic_points)

            if   pn == 4:
                faces = [[0,1,3,2], [4,6,7,5], [0,4,5,1],
                         [1,5,7,3], [3,7,6,2], [2,6,4,0]]
            elif pn == 3:
                faces = [[0,1,2], [3,5,4], [0,3,4,1], [1,4,5,2], [2,5,3,0]]
            elif pn == 2: faces = [[0,1,3,2]]
            vn += 2*pn
        else:
            if   pn == 4: faces = [[0,2,3,1]]
            elif pn == 3: faces = [[0,2,1]]
            elif pn == 2:
                edges = [[0,1]]
                self.drawtype = 'Mesh'
        if self.normal!=Vector((0,0,1)):
            ma = getOCS(self.normal)
            if ma:
                points = [ma * v for v in points]
        return ((points, edges, faces, vn))

#
#    class CVertex(CEntity):
#    10 : 'location.x', 20 : 'location.y', 30 : 'location.z', 
#    40 : 'start_width', 41 : 'end_width', 42 : 'bulge', 
#    50 : 'tangent',
#    70 : 'flags',
#    71 : 'index1', 72 : 'index2', 73 : 'index3', 74 : 'index4', 
#

class CVertex(CEntity):
    def __init__(self):
        CEntity.__init__(self, 'VERTEX', None)
        self.location = Vector()
        self.start_width = 0.0
        self.end_width = 0.0
        self.bulge = 0.0
        self.tangent = 0.0
        self.flags = 0

    def display(self):
        return

    def draw(self):
        return

#            
#    class CViewPort(CEntity):
#    10 : 'center.x', 20 : 'center.y', 30 : 'center.z', 
#    12 : 'view_center.x', 22 : 'view_center.y', 32 : 'view_center.z', 
#    13 : 'snap_base.x', 23 : 'snap_base.y', 33 : 'snap_base.z', 
#    14 : 'snap_spacing.x', 24 : 'snap_spacing.y', 34 : 'snap_spacing.z', 
#    15 : 'grid_spacing.x', 25 : 'grid_spacing.y', 35 : 'grid_spacing.z', 
#    16 : 'view_direction.x', 26 : 'view_direction.y', 36 : 'view_direction.z', 
#    40 : 'width', 41 : 'height',
#    68 : 'status', 69 : 'id',
#

class CViewPort(CEntity):
    def __init__(self):
        CEntity.__init__(self, 'VIEWPORT', None)
        self.center = Vector()
        self.view_center = Vector()
        self.snap_base = Vector()
        self.snap_spacing = Vector()
        self.grid_spacing = Vector()
        self.view_direction = Vector()
        self.width = 1.0
        self.height = 1.0
        self.status = 0
        self.id = 0

    def draw(self):
        # Todo
        return

#
#    class CWipeOut(CEntity):
#    10 : 'point.x', 20 : 'point.y', 30 : 'point.z', 
#    11 : 'direction.x', 21 : 'direction.y', 31 : 'direction.z', 
#

class CWipeOut(CEntity):
    def __init__(self):
        CEntity.__init__(self, 'WIPEOUT', None)
        self.point = Vector()
        self.direction = Vector()

#
#
#
WORLDX = Vector((1.0,0.0,0.0))
WORLDY = Vector((0.0,1.0,0.0))
WORLDZ = Vector((0.0,0.0,1.0))


def getOCS(az):  #-----------------------------------------------------------------
    """An implimentation of the Arbitrary Axis Algorithm.
    """
    #decide if we need to transform our coords
    #if az[0] == 0 and az[1] == 0: 
    if abs(az.x) < 0.00001 and abs(az.y) < 0.00001:
        if az.z > 0.0:
            return False
        elif az.z < 0.0:
            return Matrix((-WORLDX, WORLDY*1, -WORLDZ)).transposed()

    cap = 0.015625 # square polar cap value (1/64.0)
    if abs(az.x) < cap and abs(az.y) < cap:
        ax = WORLDY.cross(az)
    else:
        ax = WORLDZ.cross(az)
    ax.normalize()
    ay = az.cross(ax)
    ay.normalize()
    # Matrices are now constructed from rows, transpose to make the rows into cols
    return Matrix((ax, ay, az)).transposed()



def transform(normal, rotation, obj):  #--------------------------------------------
    """Use the calculated ocs to determine the objects location/orientation in space.
    """
    ma = Matrix()
    o = Vector(obj.location)
    ma_new = getOCS(normal)
    if ma_new:
        ma_new.resize_4x4()
        ma = ma_new
        o = ma * o

    if rotation != 0:
        rmat = Matrix.Rotation(radians(rotation), 4, 'Z')
        ma = ma * rmat

    obj.matrix_world = ma
    obj.location = o


DxfEntityAttributes = {
'3DFACE'    : {
    10 : 'point0.x', 20 : 'point0.y', 30 : 'point0.z', 
    11 : 'point1.x', 21 : 'point1.y', 31 : 'point1.z', 
    12 : 'point2.x', 22 : 'point2.y', 32 : 'point2.z', 
    13 : 'point3.x', 23 : 'point3.y', 33 : 'point3.z', 
    70 : 'flags',
    },

'3DSOLID'    : {
    1 : 'data', 3 : 'more', 70 : 'version',
    },

'ACAD_PROXY_ENTITY'    : {
    70 : 'format',
    90 : 'id', 91 : 'class', 92 : 'graphics_size', 93 : 'entity_size', 95: 'format',
    310 : 'data', 330 : 'id1', 340 : 'id2', 350 : 'id3', 360 : 'id4', 
    },

'ARC'        : {
    10 : 'center.x', 20 : 'center.y', 30 : 'center.z', 
    40 : 'radius',
    50 : 'start_angle', 51 : 'end_angle',
    39 : 'thickness',
    210 : 'normal.x', 220 : 'normal.y', 230 : 'normal.z', 
    },

'ARCALIGNEDTEXT'    : {
    1 : 'text', 2 : 'font', 3 : 'bigfont', 7 : 'style',
    10 : 'center.x', 20 : 'center.y', 30 : 'center.z', 
    40 : 'radius', 41 : 'width', 42 : 'height', 43 : 'spacing', 
    44 : 'offset', 45 : 'right_offset', 46 : 'left_offset', 
    50 : 'start_angle', 51 : 'end_angle',
    70 : 'order', 71 : 'direction', 72 : 'alignment', 73 : 'side', 
    74 : 'bold', 75 : 'italic', 76 : 'underline',
    77 : 'character_set', 78 : 'pitch', 79 : 'fonttype',
    90 : 'color',
    280 : 'wizard', 330 : 'id'
    },

'ATTDEF'    : {
    1 : 'text', 2 : 'tag', 3 : 'prompt', 7 : 'style',
    10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
    11 : 'alignment_point.x', 21 : 'alignment_point.y', 31 : 'alignment_point.z', 
    40 : 'height', 41 : 'x_scale', 
    50 : 'rotation_angle', 51 : 'oblique_angle', 
    70 : 'flags', 71 : 'text_generation_flags', 
    72 : 'horizontal_justification',  74 : 'vertical_justification',    
    },


'ATTRIB'    : {
    1 : 'text', 2 : 'tag', 3 : 'prompt', 7 : 'style',
    10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
    11 : 'alignment_point.x', 21 : 'alignment_point.y', 31 : 'alignment_point.z', 
    40 : 'height', 41 : 'x_scale', 
    50 : 'rotation_angle', 51 : 'oblique_angle', 
    70 : 'flags', 73 : 'length', 
    71 : 'text_generation_flags', 72 : 'horizontal_justification',  74 : 'vertical_justification',     
    },

'BLOCK'        : {
    1 : 'xref', 2 : 'name', 3 : 'also_name', 
    10 : 'base_point.x', 20 : 'base_point.y', 30 : 'base_point.z', 
    40 : 'size', 41 : 'x_scale', 
    50 : 'rotation_angle', 51 : 'oblique_angle',     
    70 : 'flags', 
    },

'CIRCLE'    : {
    10 : 'center.x', 20 : 'center.y', 30 : 'center.z', 
    40 : 'radius',
    39 : 'thickness',
    210 : 'normal.x', 220 : 'normal.y', 230 : 'normal.z', 
    },

'DIMENSION'    : {
    1 : 'text', 2 : 'name', 3 : 'style',
    10 : 'def_point.x', 20 : 'def_point.y', 30 : 'def_point.z', 
    11 : 'mid_point.x', 21 : 'mid_point.y', 31 : 'mid_point.z', 
    12 : 'vector.x', 22 : 'vector.y', 32 : 'vector.z', 
    13 : 'def_point2.x', 23 : 'def_point2.y', 33 : 'def_point2.z', 
    14 : 'vector2.x', 24 : 'vector2.y', 34 : 'vector2.z', 
    15 : 'vector3.x', 25 : 'vector3.y', 35 : 'vector3.z', 
    16 : 'vector4.x', 26 : 'vector4.y', 36 : 'vector4.z', 
    70 : 'dimtype',
    },

'ELLIPSE'    : {
    10 : 'center.x', 20 : 'center.y', 30 : 'center.z', 
    11 : 'end_point.x', 21 : 'end_point.y', 31 : 'end_point.z', 
    40 : 'ratio', 41 : 'start', 42 : 'end',
    39 : 'thickness',
    210 : 'normal.x', 220 : 'normal.y', 230 : 'normal.z', 
    },

'HATCH'        : {
    2 : 'pattern',
    10 : 'point.x', 20 : 'point.y', 30 : 'point.z', 
    41 : 'scale', 47 : 'pixelsize', 52 : 'angle',
    70 : 'fill', 71 : 'associativity', 75: 'style', 77 : 'double', 
    78 : 'numlines', 91 : 'numpaths', 98 : 'numseeds',
    210 : 'normal.x', 220 : 'normal.y', 230 : 'normal.z', 
    },

'IMAGE'        : {
    10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
    11 : 'u_vector.x', 21 : 'u_vector.y', 31 : 'u_vector.z', 
    12 : 'v_vector.x', 22 : 'v_vector.y', 32 : 'v_vector.z', 
    13 : 'size.x', 23 : 'size.y', 33 : 'size.z', 
    14 : 'clip.x', 24 : 'clip.y', 34 : 'clip.z', 
    70 : 'display', 71 : 'cliptype', 
    90 : 'version',
    280 : 'clipstate', 281 : 'brightness', 282 : 'contrast', 283 : 'fade', 
    340 : 'image', 360 : 'reactor',
    },

'INSERT'    : {
    1 : 'attributes_follow', 2 : 'name',
    10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
    41 : 'x_scale', 42 : 'y_scale', 43 : 'z_scale', 
    44 : 'column_spacing', 45 : 'row_spacing', 
    50 : 'rotation_angle', 66 : 'attributes_follow',
    70 : 'column_count', 71 : 'row_count', 
    210 : 'normal.x', 220 : 'normal.y', 230 : 'normal.z', 
    },

'LEADER'    : {
    3 : 'style',
    10 : ['new_vertex(data)'], 20 : 'vertex.y', 30 : 'vertex.z', 
    40 : 'height', 41 : 'width',
    71 : 'arrowhead', 72 : 'pathtype', 73 : 'creation', 
    74 : 'hookdir', 75 : 'hookline', 76 : 'numverts', 77 : 'color',
    210 : 'normal.x', 220 : 'normal.y', 230 : 'normal.z', 
    211 : 'horizon.x', 221 : 'horizon.y', 231 : 'horizon.z', 
    212 : 'offset_ins.x', 222 : 'offset_ins.y', 232 : 'offset_ins.z', 
    213 : 'offset_ann.x', 223 : 'offset_ann.y', 233 : 'offset_ann.z', 
    },

'LINE'        : {
    10 : 'start_point.x', 20 : 'start_point.y', 30 : 'start_point.z', 
    11 : 'end_point.x', 21 : 'end_point.y', 31 : 'end_point.z', 
    39 : 'thickness',
    210 : 'normal.x', 220 : 'normal.y', 230 : 'normal.z', 
    },

'LWPOLYLINE'    : {
    10 : ['new_vertex(data)'], 20 : 'vertex.y', 30 : 'vertex.z', 
    38 : 'elevation', 39 : 'thickness',
    40 : 'start_width', 41 : 'end_width', 42 : 'bulge', 43 : 'constant_width',
    70 : 'flags', 90 : 'numverts',
    210 : 'normal.x', 220 : 'normal.y', 230 : 'normal.z', 
    },
        
'MLINE'    : {
    10 : 'start_point.x', 20 : 'start_point.y', 30 : 'start_point.z', 
    11 : ['new_vertex(data)'], 21 : 'vertex.y', 31 : 'vertex.z', 
    12 : ['new_seg_dir(data)'], 22 : 'seg_dir.y', 32 : 'seg_dir.z', 
    13 : ['new_miter_dir(data)'], 23 : 'miter_dir.y', 33 : 'miter_dir.z', 
    39 : 'thickness',
    40 : 'scale', 41 : 'elem_param', 42 : 'fill_param',
    70 : 'justification', 71 : 'flags',
    72 : 'numverts', 73 : 'numelems', 74 : 'numparam', 75 : 'numfills',
    340 : 'id',
    210 : 'normal.x', 220 : 'normal.y', 230 : 'normal.z', 
    },
        
'MTEXT'        : {
    1 : 'text', 3: 'more_text', 7 : 'style',
    10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
    11 : 'alignment_point.x', 21 : 'alignment_point.y', 31 : 'alignment_point.z', 
    40 : 'nominal_height', 41 : 'reference_width', 42: 'width', 43 : 'height', 44 : 'line_spacing',
    50 : 'rotation_angle', 
    71 : 'attachment_point', 72 : 'drawing_direction',  73 : 'spacing_style',    
    210 : 'normal.x', 220 : 'normal.y', 230 : 'normal.z', 
    },

'POINT'        : {
    10 : 'point.x', 20 : 'point.y', 30 : 'point.z', 
    39 : 'thickness', 50 : 'orientation',
    },

'POLYLINE'    : {
    1 : 'verts_follow', 2 : 'name',
    10 : 'elevation.x', 20 : 'elevation.y', 30 : 'elevation.z', 
    39 : 'thickness',
    40 : 'start_width', 41 : 'end_width', 
    66 : 'verts_follow_flag',
    70 : 'flags', 71 : 'row_count', 72 : 'column_count', 
    73 : 'row_density', 74 : 'column_density', 75 : 'linetype',
    210 : 'normal.x', 220 : 'normal.y', 230 : 'normal.z', 
    },

'RAY'        : {
    10 : 'point.x', 20 : 'point.y', 30 : 'point.z', 
    11 : 'direction.x', 21 : 'direction.y', 31 : 'direction.z', 
    },

'RTEXT'        : {
    1 : 'text', 7 : 'style',
    10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
    39 : 'thickness',
    40 : 'height', 
    50 : 'rotation_angle',
    70 : 'flags',
    210 : 'normal.x', 220 : 'normal.y', 230 : 'normal.z', 
    },

'SHAPE'        : {
    2 : 'name', 
    10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
    39 : 'thickness',
    40 : 'size', 41 : 'x_scale', 
    50 : 'rotation_angle', 51 : 'oblique_angle',     
    39 : 'thickness',
    },

'SOLID'        : {
    10 : 'point0.x', 20 : 'point0.y', 30 : 'point0.z', 
    11 : 'point1.x', 21 : 'point1.y', 31 : 'point1.z', 
    12 : 'point2.x', 22 : 'point2.y', 32 : 'point2.z', 
    13 : 'point3.x', 23 : 'point3.y', 33 : 'point3.z', 
    39 : 'thickness',
    210 : 'normal.x', 220 : 'normal.y', 230 : 'normal.z', 
    },

'SPLINE'    : {
    10 : ['new_control_point(data)'], 20 : 'control_point.y', 30 : 'control_point.z', 
    11 : ['new_fit_point(data)'], 21 : 'fit_point.y', 31 : 'fit_point.z', 
    40 : ['new_knot_value(data)'], 
    12 : 'start_tangent.x', 22 : 'start_tangent.y', 32 : 'start_tangent.z', 
    13 : 'end_tangent.x', 23 : 'end_tangent.y', 33 : 'end_tangent.z', 
    39 : 'thickness',
    41 : 'weight', 42 : 'knot_tol', 43 : 'control_point_tol', 44 : 'fit_tol',
    70 : 'flag', 71 : 'degree', 
    72 : 'num_knots', 73 : 'num_control_points', 74 : 'num_fit_points',
    210 : 'normal.x', 220 : 'normal.y', 230 : 'normal.z', 
    },

'TEXT'        : {
    1 : 'text', 7 : 'style',
    10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
    11 : 'alignment_point.x', 21 : 'alignment_point.y', 31 : 'alignment_point.z', 
    40 : 'height', 41 : 'x_scale', 
    50 : 'rotation_angle', 51 : 'oblique_angle', 
    71 : 'flags', 72 : 'horizontal_justification',  73 : 'vertical_justification',    
    210 : 'normal.x', 220 : 'normal.y', 230 : 'normal.z', 
    },

'TOLERANCE'    : {
    3 : 'style',
    10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
    11 : 'direction.x', 21 : 'direction.y', 31 : 'direction.z', 
    },

'TRACE'        : {
    10 : 'point0.x', 20 : 'point0.y', 30 : 'point0.z', 
    11 : 'point1.x', 21 : 'point1.y', 31 : 'point1.z', 
    12 : 'point2.x', 22 : 'point2.y', 32 : 'point2.z', 
    13 : 'point3.x', 23 : 'point3.y', 33 : 'point3.z', 
    39 : 'thickness',
    210 : 'normal.x', 220 : 'normal.y', 230 : 'normal.z', 
    },

'VERTEX'    : {
    10 : 'location.x', 20 : 'location.y', 30 : 'location.z', 
    40 : 'start_width', 41 : 'end_width', 42 : 'bulge', 
    50 : 'tangent',
    70 : 'flags',
    71 : 'index1', 72 : 'index2', 73 : 'index3', 74 : 'index4', 
    },

'VIEWPORT'    : {
    10 : 'center.x', 20 : 'center.y', 30 : 'center.z', 
    12 : 'view_center.x', 22 : 'view_center.y', 32 : 'view_center.z', 
    13 : 'snap_base.x', 23 : 'snap_base.y', 33 : 'snap_base.z', 
    14 : 'snap_spacing.x', 24 : 'snap_spacing.y', 34 : 'snap_spacing.z', 
    15 : 'grid_spacing.x', 25 : 'grid_spacing.y', 35 : 'grid_spacing.z', 
    16 : 'view_direction.x', 26 : 'view_direction.y', 36 : 'view_direction.z', 
    40 : 'width', 41 : 'height',
    68 : 'status', 69 : 'id',
    },

'WIPEOUT'    : {
    10 : 'point.x', 20 : 'point.y', 30 : 'point.z', 
    11 : 'direction.x', 21 : 'direction.y', 31 : 'direction.z', 
    },

}


#
#    Flags
#

# Polyline flags
PL_CLOSED         = 0x01
PL_CURVE_FIT_VERTS    = 0x02
PL_SPLINE_FIT_VERTS    = 0x04
PL_3D_POLYLINE        = 0x08
PL_3D_POLYGON_MESH    = 0x10
PL_CLOSED_IN_N_DIR    = 0x20
PL_POLYFACE_MESH    = 0x40
PL_CONTINUOUS        = 0x80


# Vertex flags
VX_EXTRA_FLAG_CREATED        = 0x01
VX_CURVE_FIT_TANGENT_DEFINED    = 0x02
VX_SPLINE_VERTEX_CREATED    = 0x08
VX_SPLINE_FRAME_CONTROL_POINT    = 0x10
VX_3D_POLYLINE_VERTEX        = 0x20
VX_3D_POLYGON_MESH_VERTEX    = 0x40
VX_POLYFACE_MESH_VERTEX        = 0x80

# 3DFACE flags

F3D_EDGE0_INVISIBLE = 0x01
F3D_EDGE1_INVISIBLE = 0x02
F3D_EDGE2_INVISIBLE = 0x04
F3D_EDGE3_INVISIBLE = 0x08

#
#    readDxfFile(filePath):
#

def readDxfFile(fileName):    
    global toggle, theCodec

    print( "Opening DXF file "+ fileName )

    # fp= open(fileName, "rU")
    fp = codecs.open(fileName, "r", encoding=theCodec)
    first = True
    statements = []
    no = 0
    for line in fp: 
        word = line.strip()
        no += 1
        if first:
            if word:
                code = int(word)
                first = False
        else:
            if toggle & T_Verbose:
                print("%4d: %4d %s" % (no, code, word))
            if code < 10:
                data = word
            elif code < 60:
                data = float(word)
            elif code < 100:
                data = int(word)
            elif code < 140:
                data = word
            elif code < 150:
                data = float(word)
            elif code < 200:
                data = int(word)
            elif code < 300:
                data = float(word)
            elif code < 370:
                data = word
            elif code < 390:
                data = int(word)
            elif code < 400:
                data = word
            elif code < 410:
                data = int(word)
            elif code < 1010:
                data = word
            elif code < 1060:
                data = float(word)
            elif code < 1080:
                data = int(word)

            statements.append((code,data))
            first = True
    fp.close()

    statements.reverse()
    sections = {}
    handles = {}
    while statements:
        (code,data) = statements.pop()
        if code == 0:
            if data == 'SECTION':
                section = CSection()
        elif code == 2:
            section.type = data
            if data == 'HEADER':
                parseHeader(section, statements, handles)
                known = False
            elif data == 'CLASSES':
                parseClasses(section, statements, handles)
                known = False
            elif data == 'TABLES':
                parseTables(section, statements, handles)
                known = False
            elif data == 'BLOCKS':
                parseBlocks(section, statements, handles)
                known = False
            elif data == 'ENTITIES':
                parseEntities(section, statements, handles)
                known = False
            elif data == 'OBJECTS':
                parseObjects(section, statements, handles)
            elif data == 'THUMBNAILIMAGE':
                parseThumbnail(section, statements, handles)
            sections[data] = section
        elif code == 999:
            pass
        else:
            raise NameError("Unexpected code in SECTION context: %d %s" % (code,data))

    if toggle & T_Verbose:
        for (typ,section) in sections.items():
            section.display()
    return sections
    

#
#     0
#    SECTION
#      2
#    HEADER
#    
#      9
#    $<variable>
#    <group code>
#    <value>
#    
#      0
#    ENDSEC

    
def parseHeader(section, statements, handles):
    while statements:
        (code,data) = statements.pop()
        if code == 0:
            if data == 'ENDSEC':
                return

    return


#      0
#    SECTION
#      2
#    CLASSES
#    
#      0
#    CLASS
#      1
#    <class dxf record>
#      2
#    <class name>
#      3
#    <app name>
#    90
#    <flag>
#    280
#    <flag>
#    281
#    <flag>
#    
#      0
#    ENDSEC         

def parseClasses(section, statements, handles):
    while statements:
        (code,data) = statements.pop()
        if code == 0:
            if data == 'ENDSEC':
                return

    return
    

#      0
#    SECTION
#      2
#    TABLES
#    
#      0
#    TABLE
#      2
#    <table type>
#      5
#    <handle>
#    100
#    AcDbSymbolTable
#    70
#    <max. entries>
#    
#      0
#    <table type>
#      5
#    <handle>
#    100
#    AcDbSymbolTableRecord
#    .
#    . <data>
#    .
#    
#      0
#    ENDTAB
#    
#      0
#    ENDSEC 

#
#      APPID (application identification table)
#
#      BLOCK_RECORD (block reference table)
#
#      DIMSTYLE (dimension style table)
#
#      LAYER (layer table)
#
#      LTYPE (linetype table)
#
#      STYLE (text style table)
#
#      UCS (User Coordinate System table)
#
#      VIEW (view table)
#
#      VPORT (viewport configuration table)


def parseTables(section, statements, handles):
    tables = []
    section.data = tables
    while statements:
        (code,data) = statements.pop()
        if code == 0:
            if data == 'ENDSEC':
                return
    '''
                known = False
            elif data == 'TABLE':
                table = CTable()
                tables.append(table)
                known = False
            elif data == 'ENDTAB':
                pass
                known = False
            elif data == table.type:
                parseTableType
                table = CTable()
                tables.append(table)
                table.type = word
        elif code == 2:
            table.type = word
        elif code == 5:
            table.handle = word
            handles[word] = table
        elif code == 330:
            table.owner = word
        elif code == 100:
            table.subclass = word
        elif code == 70:
            table.nEntries = int(word)
    '''
    return
    
#      0
#    SECTION
#      2
#    BLOCKS
#    
#      0
#    BLOCK
#      5
#    <handle>
#    100
#    AcDbEntity
#      8
#    <layer>
#    100
#    AcDbBlockBegin
#      2
#    <block name>
#    70
#    <flag>
#    10
#    <X value>
#    20
#    <Y value>
#    30
#    <Z value>
#      3
#    <block name>
#      1
#    <xref path>
#    
#      0
#    <entity type>
#    .
#    . <data>
#    .
#    
#      0
#    ENDBLK
#      5
#    <handle>
#    100
#    AcDbBlockEnd
#    
#      0
#    ENDSEC 

def parseBlocks(section, statements, handles):
    while statements:
        (code,data) = statements.pop()
        if code == 0:
            if data == 'ENDSEC':
                return

    return

#      0
#    SECTION
#      2
#    ENTITIES
#    
#      0
#    <entity type>
#      5
#    <handle>
#    330
#    <pointer to owner>
#    100
#    AcDbEntity
#      8
#    <layer>
#    100
#    AcDb<classname>
#    .
#    . <data>
#    .
#    
#      0
#    ENDSEC

Ignorables = ['DIMENSION', 'TEXT', 'VIEWPORT']

ClassCreators = {
    '3DFACE':         'C3dFace()', 
    '3DSOLID':        'C3dSolid()',
    'ACAD_PROXY_ENTITY':    'CAcadProxyEntity()',
    'ACAD_ZOMBIE_ENTITY':    0,
    'ARC':            'CArc()',
    'ARCALIGNEDTEXT':    'CArcAlignedText()',
    'ATTDEF':        'CAttdef()',
    'ATTRIB':        'CAttrib()',
    'BODY':            0,
    'CIRCLE':        'CCircle()',
    'DIMENSION':        'CDimension()',
    'ELLIPSE':        'CEllipse()',
    'HATCH':        'CHatch()',
    'IMAGE':        'CImage()',
    'INSERT':        'CInsert()',
    'LEADER':        'CLeader()',
    'LINE':            'CLine()',
    'LWPOLYLINE':        'CLWPolyLine()',
    'MLINE':        'CMLine()',
    'MTEXT':        'CMText()',
    'OLEFRAME':        0,
    'OLE2FRAME':        0,
    'POINT':        'CPoint()',
    'POLYLINE':        'CPolyLine()',
    'RAY':            'CRay()',
    'REGION':        0,
    'RTEXT':        'CRText',
    'SEQEND':        0,
    'SHAPE':        'CShape()',
    'SOLID':        'CSolid()',
    'SPLINE':        'CSpline()',
    'TEXT':            'CText()',
    'TOLERANCE':        'CTolerance()',
    'TRACE':        'CTrace()',
    'VERTEX':        'CVertex()',
    'VIEWPORT':        'CViewPort()',
    'WIPEOUT':        'CWipeOut()',
    'XLINE':        'CXLine()',
}

def parseEntities(section, statements, handles):
    entities = []
    section.data = entities
    while statements:
        (code,data) = statements.pop()
        if toggle & T_Verbose:
            print("ent", code,data)
        if code == 0:
            known = True
            if data in Ignorables:
                ignore = True
            else:
                ignore = False

            try:
                creator = ClassCreators[data]
            except:
                creator = None
                
            if creator:
                entity = eval(creator)
            elif data == 'ENDSEC':
                return
            else:
                known = False
                
            if data == 'POLYLINE':
                verts = entity.verts
            elif data == 'VERTEX':
                verts.append(entity)
            
            if data == 'SEQEND':
                attributes = []
                known = False
            elif creator == 0:
                ignore = True
            elif known:
                entities.append(entity)
                attributes = DxfEntityAttributes[data]
            else:
                raise NameError("Unknown data %s" % data)

        elif not known:
            pass
        else:
            expr = getAttribute(attributes, code)
            if expr:
                exec(expr)
            else:
                expr = getAttribute(DxfCommonAttributes, code)
                if expr:
                    exec(expr)
                elif code >= 1000 or ignore:
                    pass
                elif toggle & T_Debug:
                    raise NameError("Unknown code %d for %s" % (code, entity.type))
                
    return

def getAttribute(attributes, code):
    try:
        ext = attributes[code]
        if type(ext) == str:
            expr = "entity.%s = data" % ext
        else:
            name = ext[0]
            expr = "entity.%s" % name
    except:
        expr = None
    return expr


#      0
#    SECTION
#      2
#    OBJECTS
#    
#      0
#    DICTIONARY
#      5
#    <handle>
#    100
#    AcDbDictionary
#    
#      3
#    <dictionary name>
#    350
#    <handle of child>
#    
#      0
#    <object type>
#    .
#    . <data>
#    .
#    
#      0
#    ENDSEC 

def parseObjects(data, statements, handles):
    while statements:
        (code,data) = statements.pop()
        if code == 0:
            if data == 'ENDSEC':
                return

    return

#    
#    THUMBNAILIMAGE
#     90
#        45940
#    310
#    28000000B40000005500000001001800000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
#    310
#    FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
#    310
#    .......
#      0
#    ENDSEC

def parseThumbnail(section, statements, handles):
    """ Just skip these """
    while statements:
        (code,data) = statements.pop()
        if code == 0:
            if data == 'ENDSEC':
                return

    return

#
#    buildGeometry(entities):
#    addMesh(name, verts, edges, faces):                            
#

def buildGeometry(entities):
    try: bpy.ops.object.mode_set(mode='OBJECT')
    except: pass
    v_verts = []
    v_vn = 0
    e_verts = []
    e_edges = []
    e_vn = 0
    f_verts = []
    f_edges = []
    f_faces = []
    f_vn = 0
    for ent in entities:
        if ent.drawtype in {'Mesh', 'Curve'}:
            (verts, edges, faces, vn) = ent.build()
            if not toggle & T_DrawOne:
                drawGeometry(verts, edges, faces)
            else:
                if verts:
                    if faces:
                        for i,f in enumerate(faces):
                            #print ('face=', f)
                            faces[i] = tuple(it+f_vn for it in f)
                        for i,e in enumerate(edges):
                            edges[i] = tuple(it+f_vn for it in e)
                        f_verts.extend(verts)
                        f_edges.extend(edges)
                        f_faces.extend(faces)
                        f_vn += len(verts)
                    elif edges:
                        for i,e in enumerate(edges):
                            edges[i] = tuple(it+e_vn for it in e)
                        e_verts.extend(verts)
                        e_edges.extend(edges)
                        e_vn += len(verts)
                    else:
                        v_verts.extend(verts)
                        v_vn += len(verts)
        else:
            ent.draw()
                    
    if toggle & T_DrawOne:
        drawGeometry(f_verts, f_edges, f_faces)
        drawGeometry(e_verts, e_edges)
        drawGeometry(v_verts)



def drawGeometry(verts, edges=[], faces=[]):
    if verts:
        if edges and (toggle & T_Curves):
            print ('draw Curve')
            cu = bpy.data.curves.new('DXFlines', 'CURVE')
            cu.dimensions = '3D'
            buildSplines(cu, verts, edges)
            ob = addObject('DXFlines', cu)
        else:
            #for v in verts: print(v)
            #print ('draw Mesh with %s vertices' %(len(verts)))
            #for e in edges: print(e)
            #print ('draw Mesh with %s edges' %(len(edges)))
            #for f in faces: print(f)
            #print ('draw Mesh with %s faces' %(len(faces)))
            me = bpy.data.meshes.new('DXFmesh')
            me.from_pydata(verts, edges, faces)
            ob = addObject('DXFmesh', me)
            removeDoubles(ob)
    return



def buildSplines(cu, verts, edges):
    if edges:
        point_list = []
        (v0,v1) = edges.pop()
        v1_old = v1
        newPoints = [tuple(verts[v0]),tuple(verts[v1])]
        for (v0,v1) in edges:
            if v0==v1_old:
                newPoints.append(tuple(verts[v1]))
            else:
                #print ('newPoints=', newPoints)
                point_list.append(newPoints)
                newPoints = [tuple(verts[v0]),tuple(verts[v1])]
            v1_old = v1
        point_list.append(newPoints)
        for points in point_list:
            spline = cu.splines.new('POLY')
            #spline = cu.splines.new('BEZIER')
            #spline.use_endpoint_u = True
            #spline.order_u = 2
            #spline.resolution_u = 1
            #spline.bezier_points.add(2)

            spline.points.add(len(points)-1)
            #spline.points.foreach_set('co', points)
            for i,p in enumerate(points):
                spline.points[i].co = (p[0],p[1],p[2],0)
                
        #print ('spline.type=', spline.type)
        #print ('spline number=', len(cu.splines))
    
    
def addObject(name, data):
    ob = bpy.data.objects.new(name, data)
    scn = bpy.context.scene
    scn.objects.link(ob)
    return ob


def removeDoubles(ob):
    global theMergeLimit
    if toggle & T_Merge:
        scn = bpy.context.scene
        scn.objects.active = ob
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.remove_doubles(threshold=theMergeLimit)
        bpy.ops.object.mode_set(mode='OBJECT')



#
#    clearScene(context):
#
    
def clearScene():
    global toggle
    scn = bpy.context.scene
    print("clearScene %s %s" % (toggle & T_NewScene, scn))
    if not toggle & T_NewScene:
        return scn

    for ob in scn.objects:
        if ob.type in ["MESH", "CURVE", "TEXT"]:
            scn.objects.active = ob
            bpy.ops.object.mode_set(mode='OBJECT')
            scn.objects.unlink(ob)
            del ob
    return scn

#
#    readAndBuildDxfFile(filepath):
#

def readAndBuildDxfFile(filepath):
    fileName = os.path.expanduser(filepath)
    if fileName:
        (shortName, ext) = os.path.splitext(fileName)
        #print("filepath: ", filepath)
        #print("fileName: ", fileName)
        #print("shortName: ", shortName)
        if ext.lower() != ".dxf":
            print("Error: Not a dxf file: " + fileName)
            return
        if toggle & T_NewScene:
            clearScene()
            if 0: # how to switch to the new scene?? (migius)
                new_scn = bpy.data.scenes.new(shortName[-20:])
                #new_scn.layers = (1<<20) -1
                #new_scn_name = new_scn.name  # UNUSED
                bpy.data.screens.scene = new_scn
                #print("newScene: %s" % (new_scn))
        sections = readDxfFile(fileName)
        print("Building geometry")
        buildGeometry(sections['ENTITIES'].data)
        print("Done")
        return
    print("Error: Not a dxf file: " + filepath)
    return

#
#    User interface
#

DEBUG= False
from bpy.props import *

def tripleList(list1):
    list3 = []
    for elt in list1:
        list3.append((elt,elt,elt))
    return list3

class IMPORT_OT_autocad_dxf(bpy.types.Operator):
    """Import from DXF file format (.dxf)"""
    bl_idname = "import_scene.autocad_dxf"
    bl_description = 'Import from DXF file format (.dxf)'
    bl_label = "Import DXF" +' v.'+ __version__
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {'UNDO'}

    filepath = StringProperty(
            subtype='FILE_PATH',
            )
    new_scene = BoolProperty(
            name="Replace scene",
            description="Replace scene",
            default=toggle & T_NewScene,
            )
    #~ new_scene = BoolProperty(
            #~ name="New scene",
            #~ description="Create new scene",
            #~ default=toggle & T_NewScene,
            #~ )
    curves = BoolProperty(
            name="Draw curves",
            description="Draw entities as curves",
            default=toggle & T_Curves,
            )
    thic_on = BoolProperty(
            name="Thick ON",
            description="Support THICKNESS",
            default=toggle & T_ThicON,
            )
    merge = BoolProperty(
            name="Remove doubles",
            description="Merge coincident vertices",
            default=toggle & T_Merge,
            )
    mergeLimit = FloatProperty(
            name="Limit",
            description="Merge limit * 0.0001",
            default=theMergeLimit * 1e4,
            min=1.0,
            soft_min=1.0,
            max=1000.0,
            soft_max=1000.0,
            )
    draw_one = BoolProperty(
            name="Merge all",
            description="Draw all into one mesh object",
            default=toggle & T_DrawOne,
            )
    circleResolution = IntProperty(
            name="Circle resolution",
            description="Circle/Arc are approximated with this factor",
            default=theCircleRes,
            min=4,
            soft_min=4,
            max=360,
            soft_max=360,
            )
    codecs = tripleList(['iso-8859-15', 'utf-8', 'ascii'])
    codec = EnumProperty(name="Codec",
            description="Codec",
            items=codecs,
            default='ascii',
            )
    debug = BoolProperty(
            name="Debug",
            description="Unknown DXF-codes generate errors",
            default=toggle & T_Debug,
            )
    verbose = BoolProperty(
            name="Verbose",
            description="Print debug info",
            default=toggle & T_Verbose,
            )

    ##### DRAW #####
    def draw(self, context):
        layout0 = self.layout
        #layout0.enabled = False

        #col = layout0.column_flow(2,align=True)
        layout = layout0.box()
        col = layout.column()
        #col.prop(self, 'KnotType') waits for more knottypes
        #col.label(text="import Parameters")
        #col.prop(self, 'replace')
        col.prop(self, 'new_scene')
        
        row = layout.row(align=True)
        row.prop(self, 'curves')
        row.prop(self, 'circleResolution')

        row = layout.row(align=True)
        row.prop(self, 'merge')
        if self.merge:
            row.prop(self, 'mergeLimit')
 
        row = layout.row(align=True)
        #row.label('na')
        row.prop(self, 'draw_one')
        row.prop(self, 'thic_on')

        col = layout.column()
        col.prop(self, 'codec')
 
        row = layout.row(align=True)
        row.prop(self, 'debug')
        if self.debug:
            row.prop(self, 'verbose')
         
    def execute(self, context):
        global toggle, theMergeLimit, theCodec, theCircleRes
        O_Merge = T_Merge if self.merge else 0
        #O_Replace = T_Replace if self.replace else 0
        O_NewScene = T_NewScene if self.new_scene else 0
        O_Curves = T_Curves if self.curves else 0
        O_ThicON = T_ThicON if self.thic_on else 0
        O_DrawOne = T_DrawOne if self.draw_one else 0
        O_Debug = T_Debug if self.debug else 0
        O_Verbose = T_Verbose if self.verbose else 0

        toggle =  O_Merge | O_DrawOne | O_NewScene | O_Curves | O_ThicON | O_Debug | O_Verbose
        theMergeLimit = self.mergeLimit*1e-4
        theCircleRes = self.circleResolution
        theCodec = self.codec

        readAndBuildDxfFile(self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


def menu_func(self, context):
    self.layout.operator(IMPORT_OT_autocad_dxf.bl_idname, text="Autocad (.dxf)")


def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_import.append(menu_func)

 
def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_import.remove(menu_func)


if __name__ == "__main__":
    register()


