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

bl_addon_info = {
	'name': 'Import Autocad DXF (.dxf)',
	'author': 'Thomas Larsson',
	'version': '0.1',
	'blender': (2, 5, 3),
	'location': 'File > Import',
	'description': 'Import files in the Autocad DXF format (.dxf)',
	'wiki_url': 'http://wiki.blender.org/index.php/Extensions:Py/Scripts',
	'category': 'Import/Export'}

"""
Place this file in the .blender/scripts/addons dir
You have to activated the script in the "Add-Ons" tab (user preferences).
Access from the File > Import menu.
"""

import os
import codecs
import math
import bpy
import mathutils
from mathutils import Vector

#
#	Global flags
#

T_Merge = 0x01
T_Replace = 0x02
T_Curves = 0x04
T_Verbose = 0x08
T_Debug = 0x10

toggle = T_Merge | T_Replace 

theMergeLimit = 1e-5

#
#	class CSection:
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
#	class CTable:
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
#	class CEntity:
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
		self.extrusion = Vector()

	def display(self):
		print("Entity %s %s %s %s %s %s %x" % 
			(self.type, self.handle, self.owner, self.subclass, self.layer, self.color, self.invisible))

	def build(self, vn):
		global toggle
		if toggle & T_Debug:
			raise NameError("Cannot build %s yet" % self.type)
		return(([], [], vn)) 

	def draw(self):
		global toggle
		if toggle & T_Debug:
			raise NameError("Cannot draw %s yet" % self.type)
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
	210 : 'extrusion.x', 220 : 'extrusion.y', 230 : 'extrusion.z', 
}

#
#	class C3dFace(CEntity):
#	10 : 'point0.x', 20 : 'point0.y', 30 : 'point0.z', 
#	11 : 'point1.x', 21 : 'point1.y', 31 : 'point1.z', 
#	12 : 'point2.x', 22 : 'point2.y', 32 : 'point2.z', 
#	13 : 'point3.x', 23 : 'point3.y', 33 : 'point3.z', 
#	70 : 'flags',
#

class C3dFace(CEntity):
	def __init__(self):
		CEntity.__init__(self, '3DFACE', 'Face')
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

	def build(self, vn):
		verts = [self.point0, self.point1, self.point2]
		if self.point2 == self.point3:
			face = (vn, vn+1, vn+2)
			vn += 3
		else:
			verts.append( self.point3 )
			face = (vn, vn+1, vn+2, vn+3)
			vn += 4			
		return((verts, [face], vn))

#
#	class C3dSolid(CEntity):
#	1 : 'data', 3 : 'more', 70 : 'version',
#

class C3dSolid(CEntity):
	def __init__(self):
		CEntity.__init__(self, '3DSOLID', 'Face')
		self.data = None
		self.more = None
		self.version = 0

#
#	class CAcadProxyEntity(CEntity):
#	70 : 'format',
#	90 : 'id', 91 : 'class', 92 : 'graphics_size', 93 : 'entity_size', 95: 'format',
#	310 : 'data', 330 : 'id1', 340 : 'id2', 350 : 'id3', 360 : 'id4', 
#

class CAcadProxyEntity(CEntity):
	def __init__(self):
		CEntity.__init__(self, 'ACAD_PROXY_ENTITY', None)


#
#	class CArc(CEntity):
#	10 : 'center.x', 20 : 'center.y', 30 : 'center.z', 
#	40 : 'radius',
#	50 : 'start_angle', 51 : 'end_angle'
#

class CArc(CEntity):
	def __init__(self):
		CEntity.__init__(self, 'ARC', 'Edge')
		self.center = Vector()
		self.radius = 0.0
		self.start_angle = 0.0
		self.end_angle = 0.0
		
	def display(self):
		CEntity.display(self)
		print(self.center)
		print("%.4f %.4f %.4f " % (self.radius, self.start_angle, self.end_angle))

	def build(self, vn):
		dphi = (self.end_angle - self.start_angle)*math.pi/180
		phi0 = self.start_angle*math.pi/180
		w = dphi/32
		r = self.radius
		center = self.center
		verts = []
		edges = []
		for n in range(32):
			s = math.sin(n*w + phi0)
			c = math.cos(n*w + phi0)
			v = (center.x + r*c, center.y + r*s, center.z)
			verts.append(v)
			edges.append((vn,vn+1))
			vn += 1
		edges.pop()
		return( (verts, edges, vn) )

#
#	class CArcAlignedText(CEntity):
#	1 : 'text', 2 : 'font', 3 : 'bigfont', 7 : 'style',
#	10 : 'center.x', 20 : 'center.y', 30 : 'center.z', 
#	40 : 'radius', 41 : 'width', 42 : 'height', 43 : 'spacing', 
#	44 : 'offset', 45 : 'right_offset', 46 : 'left_offset', 
#	50 : 'start_angle', 51 : 'end_angle',
#	70 : 'order', 71 : 'direction', 72 : 'alignment', 73 : 'side', 
#	74 : 'bold', 75 : 'italic', 76 : 'underline',
#	77 : 'character_set', 78 : 'pitch', 79 'fonttype',
#	90 : 'color',
#	280 : 'wizard', 330 : 'id'
#

class CArcAlignedText(CEntity):
	def __init__(self):
		CEntity.__init__(self, 'ARCALIGNEDTEXT', 'Edge')
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


#
#	class CAttdef(CEntity):
#	1 : 'text', 2 : 'tag', 3 : 'prompt', 7 : 'style',
#	10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
#	11 : 'alignment_point.x', 21 : 'alignment_point.y', 31 : 'alignment_point.z', 
#	40 : 'height', 41 : 'x_scale', 
#	50 : 'rotation_angle', 51 : 'oblique_angle', 
#	70 : 'flags', 71 : 'text_generation_flags', 
#	72 : 'horizontal_justification',  74 : 'vertical_justification',	
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

	def draw(self):
		drawText(self.text,  self.insertion_point, self.height, self.x_scale, self.rotation_angle, self.oblique_angle)
		return

#
#	class CAttrib(CEntity):
#	1 : 'text', 2 : 'tag', 3 : 'prompt', 7 : 'style',
#	10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
#	11 : 'alignment_point.x', 21 : 'alignment_point.y', 31 : 'alignment_point.z', 
#	40 : 'height', 41 : 'x_scale', 
#	50 : 'rotation_angle', 51 : 'oblique_angle', 
#	70 : 'flags', 73 : 'length', 
#	71 : 'text_generation_flags', 72 : 'horizontal_justification',  74 : 'vertical_justification', 	
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

	def draw(self):
		drawText(self.text,  self.insertion_point, self.height, self.x_scale, self.rotation_angle, self.oblique_angle)
		return


#
#	class CBlock(CEntity):
#	1 : 'xref', 2 : 'name', 3 : 'also_name', 
#	10 : 'base_point.x', 20 : 'base_point.y', 30 : 'base_point.z', 
#	40 : 'size', 41 : 'x_scale', 
#	50 : 'rotation_angle', 51 : 'oblique_angle', 	
#	70 : 'flags', 
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

	def display(self):
		CEntity.display(self)
		print("%s %s %s " % (self.xref, self.name, self.also_name))
		print(self.base_point)

	def draw(self):
		# Todo
		return

#
#	class CCircle(CEntity):
#	10 : 'center.x', 20 : 'center.y', 30 : 'center.z', 
#	40 : 'radius'
#

class CCircle(CEntity):
	def __init__(self):
		CEntity.__init__(self, 'CIRCLE', 'Edge')
		self.center = Vector()
		self.radius = 0.0

	def display(self):
		CEntity.display(self)
		print(self.center)
		print("%.4f" % self.radius)

	def build(self, vn):
		w = 2*math.pi/32
		r = self.radius
		center = self.center
		verts = []
		edges = []
		v0 = vn
		for n in range(32):
			s = math.sin(n*w)
			c = math.cos(n*w)
			v = (center.x + r*c, center.y + r*s, center.z)
			verts.append(v)
			edges.append((vn,vn+1))
			vn += 1
		edges.pop()
		edges.append((v0,vn-1))
		return( (verts, edges, vn) )
			
#
#	class CDimension(CEntity):
#	1 : 'text', 2 : 'name', 3 : 'style',
#	10 : 'def_point.x', 20 : 'def_point.y', 30 : 'def_point.z', 
#	11 : 'mid_point.x', 21 : 'mid_point.y', 31 : 'mid_point.z', 
#	12 : 'vector.x', 22 : 'vector.y', 32 : 'vector.z', 
#	13 : 'def_point2.x', 23 : 'def_point2.y', 33 : 'def_point2.z', 
#	14 : 'vector2.x', 24 : 'vector2.y', 34 : 'vector2.z', 
#	15 : 'vector3.x', 25 : 'vector3.y', 35 : 'vector3.z', 
#	16 : 'vector4.x', 26 : 'vector4.y', 36 : 'vector4.z', 
#	70 : 'dimtype',
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

	def draw(self):
		return

#
#	class CEllipse(CEntity):
#	10 : 'center.x', 20 : 'center.y', 30 : 'center.z', 
#	11 : 'end_point.x', 21 : 'end_point.y', 31 : 'end_point.z', 
#	40 : 'ratio', 41 : 'start', 42 : 'end',
#

class CEllipse(CEntity):
	def __init__(self):
		CEntity.__init__(self, 'ELLIPSE', 'Edge')
		self.center = Vector()
		self.end_point = Vector()
		self.ratio = 1.0
		self.start = 0.0
		self.end = 2*math.pi

	def display(self):
		CEntity.display(self)
		print(self.center)
		print("%.4f" % self.ratio)
				
	def build(self, vn):
		dphi = (self.end - self.start)
		phi0 = self.start
		w = dphi/32
		r = self.end_point.length
		f = self.ratio
		a = self.end_point.x/r
		b = self.end_point.y/r
		center = self.center
		verts = []
		edges = []
		for n in range(32):
			x = r*math.sin(n*w + phi0)
			y = f*r*math.cos(n*w + phi0)
			v = (center.x - a*x + b*y, center.y - a*y - b*x, center.z)
			verts.append(v)
			edges.append((vn,vn+1))
			vn += 1
		edges.pop()
		return( (verts, edges, vn) )

#
#	class CHatch(CEntity):
#	2 : 'pattern',
#	10 : 'point.x', 20 : 'point.y', 30 : 'point.z', 
#	41 : 'scale', 47 : 'pixelsize', 52 : 'angle',
#	70 : 'fill', 71 : 'associativity', 75: 'style', 77 : 'double', 
#	78 : 'numlines', 91 : 'numpaths', 98 : 'numseeds',
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


#	class CImage(CEntity):
#	10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
#	11 : 'u_vector.x', 21 : 'u_vector.y', 31 : 'u_vector.z', 
#	12 : 'v_vector.x', 22 : 'v_vector.y', 32 : 'v_vector.z', 
#	13 : 'size.x', 23 : 'size.y', 33 : 'size.z', 
#	14 : 'clip.x', 24 : 'clip.y', 34 : 'clip.z', 
#	70 : 'display', 71 : 'cliptype', 
#	90 : 'version',
#	280 : 'clipstate', 281 : 'brightness', 282 : 'contrast', 283 : 'fade', 
#	340 : 'image', 360 : 'reactor'
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

#
#	class CInsert(CEntity):
#	1 : 'attributes_follow', 2 : 'name',
#	10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
#	41 : 'x_scale', 42 : 'y_scale', 43 : 'z_scale', 
#	44 : 'column_spacing', 45 : 'row_spacing', 
#	50 : 'rotation_angle', 66 : 'attributes_follow',
#	70 : 'column_count', 71 : 'row_count', 
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

	def display(self):
		CEntity.display(self)
		print(self.insertion_point)

	def draw(self):
		# Todo
		return

#
#	class CLeader(CEntity):
#	3 : 'style',
#	10 : ['new_vertex(data)'], 20 : 'vertex.y', 30 : 'vertex.z', 
#	40 : 'height', 41 : 'width',
#	71 : 'arrowhead', 72 : 'pathtype', 73 : 'creation', 
#	74 : 'hookdir', 75 : 'hookline', 76 : 'numverts', 77 : 'color',
#	210 : 'normal.x', 220 : 'normal.y', 230 : 'normal.z', 
#	211 : 'horizon.x', 221 : 'horizon.y', 231 : 'horizon.z', 
#	212 : 'offset_ins.x', 222 : 'offset_ins.y', 232 : 'offset_ins.z', 
#	213 : 'offset_ann.x', 223 : 'offset_ann.y', 233 : 'offset_ann.z', 
#

class CLeader(CEntity):
	def __init__(self):
		CEntity.__init__(self, 'LEADER', 'Edge')
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
		self.normal = Vector()
		self.horizon = Vector()
		self.offset_ins = Vector()
		self.offset_ann = Vector()

	def new_vertex(self, data):
		self.vertex = Vector()
		self.vertex.x = data
		self.verts.append(self.vertex)

	def build(self, vn):
		edges = []
		for v in self.verts:
			edges.append((vn, vn+1))
			vn += 1
		edges.pop()
		return (self.verts, edges, vn)

#	class CLwPolyLine(CEntity):
#	10 : ['new_vertex(data)'], 20 : 'vertex.y', 30 : 'vertex.z', 
#	38 : 'elevation', 39 : 'thickness',
#	40 : 'start_width', 41 : 'end_width', 42 : 'bulge', 43 : 'constant_width',
#	70 : 'flags', 90 : 'numverts'
#

class CLwPolyLine(CEntity):
	def __init__(self):
		CEntity.__init__(self, 'LWPOLYLINE', None)
		self.vertex = None
		self.verts = []
		self.elevation = 0
		self.thickness = 1.0
		self.start_width = 1.0
		self.end_width = 1.0
		self.bulge = 0.0
		self.constant_width = 1.0
		self.flags = 0
		self.numverts = 0

	def new_vertex(self, data):
		self.vertex = Vector()
		self.vertex.x = data
		self.verts.append(self.vertex)

	def build(self, vn):
		edges = []
		for v in self.verts:
			edges.append((vn, vn+1))
			vn += 1
		edges.pop()
		return (self.verts, edges, vn)
		
#
#	class CLine(CEntity):
#	10 : 'start_point.x', 20 : 'start_point.y', 30 : 'start_point.z', 
#	11 : 'end_point.x', 21 : 'end_point.y', 31 : 'end_point.z', 
#	39 : 'thickness',
#

class CLine(CEntity):
	def __init__(self):
		CEntity.__init__(self, 'LINE', 'Edge')
		self.start_point = Vector()
		self.end_point = Vector()
		self.thickness = 1.0

	def display(self):
		CEntity.display(self)
		print(self.start_point)
		print(self.end_point)

	def build(self, vn):
		verts = [self.start_point, self.end_point]
		line = (vn, vn+1)
		return((verts, [line], vn+2))

#	class CMLine(CEntity):
#	10 : 'start_point.x', 20 : 'start_point.y', 30 : 'start_point.z', 
#	11 : ['new_vertex(data)'], 21 : 'vertex.y', 31 : 'vertex.z', 
#	12 : ['new_seg_dir(data)'], 22 : 'seg_dir.y', 32 : 'seg_dir.z', 
#	13 : ['new_miter_dir(data)'], 23 : 'miter_dir.y', 33 : 'miter_dir.z', 
#	40 : 'scale', 41 : 'elem_param', 42 : 'fill_param',
#	70 : 'justification', 71 : 'flags'
#	72 : 'numverts', 73 : 'numelems', 74 : 'numparam', 75 : 'numfills',
#	340 : 'id'
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
#	class CMText(CText):
#	1 : 'text', 3: 'more_text', 7 : 'style',
#	10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
#	11 : 'alignment_point.x', 21 : 'alignment_point.y', 31 : 'alignment_point.z', 
#	40 : 'nominal_height', 41 : 'reference_width', 42: 'width', 43 : 'height', 44 : 'line_spacing',
#	50 : 'rotation_angle', 
#	71 : 'attachment_point', 72 : 'drawing_direction',  73 : 'spacing_style',	
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

	def display(self):
		CEntity.display(self)
		print("%s %s" % (self.text, self.style))
		print(self.insertion_point)
		print(self.alignment_point)

	def draw(self):
		drawText(self.text,  self.insertion_point, self.height, self.width, self.rotation_angle, 0.0)
		return

#
#	class CPoint(CEntity):
#	10 : 'point.x', 20 : 'point.y', 30 : 'point.z', 
#	39 : 'thickness', 50 : 'orientation'
#

class CPoint(CEntity):
	def __init__(self):
		CEntity.__init__(self, 'POINT', 'Edge')
		self.point = Vector()
		self.thickness = 1.0
		self.orientation = 0.0

	def display(self):
		CEntity.display(self)
		print(self.point)
		print("%.4f" % self.orientation)

	def build(self, vn):
		verts = [self.point]
		return((verts, [], vn+1))

#
#	class CPolyLine(CEntity):
#	1 : 'verts_follow', 2 : 'name',
#	10 : 'elevation.x', 20 : 'elevation.y', 30 : 'elevation.z', 
#	40 : 'start_width', 41 : 'end_width', 
#	66 : 'verts_follow_flag',
#	70 : 'flags', 71 : 'row_count', 72 : 'column_count', 
#	73 : 'row_density', 74 : 'column_density', 75 : 'linetype',
#

class CPolyLine(CEntity):
	def __init__(self):
		CEntity.__init__(self, 'POLYLINE', 'Edge')
		self.verts = []
		self.verts_follow = 1
		self.name = ""
		self.elevation = Vector()
		self.start_width = 1.0
		self.end_width = 1.0
		self.verts_follow_flags = 0
		self.flags = 0
		self.row_count = 1
		self.column_count = 1
		self.row_density = 1.0
		self.column_density = 1.0
		self.linetype = 1

	def display(self):
		CEntity.display(self)
		print("VERTS")
		for v in self.verts:
			print(v.location)
		print("END VERTS")

	def build(self, vn):
		verts = []
		lines = []
		for vert in self.verts:
			verts.append(vert.location)
			lines.append((vn, vn+1))
			vn += 1
		lines.pop()
		return((verts, lines, vn))

#
#	class CShape(CEntity):
#	2 : 'name', 
#	10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
#	39 : 'thickness',
#	40 : 'size', 41 : 'x_scale', 
#	50 : 'rotation_angle', 51 : 'oblique_angle', 	
#

class CShape(CEntity):
	def __init__(self):
		CEntity.__init__(self, 'SHAPE', None)
		self.name = ""
		self.insertion_point = Vector()
		self.thickness = 1.0
		self.size = 1.0
		self.x_scale = 1.0
		self.rotation_angle = 0.0
		self.oblique_angle = 0.0
	def display(self):
		CEntity.display(self)
		print("%s" % (self.name))
		print(self.insertion_point)

#
#	class CSpline(CEntity):
#	10 : ['new_control_point(data)'], 20 : 'control_point.y', 30 : 'control_point.z', 
#	11 : ['new_fit_point(data)'], 21 : 'fit_point.y', 31 : 'fit_point.z', 
#	40 : ['new_knot_value(data)'], 
#	12 : 'start_tangent.x', 22 : 'start_tangent.y', 32 : 'start_tangent.z', 
#	13 : 'end_tangent.x', 23 : 'end_tangent.y', 33 : 'end_tangent.z', 
#	41 : 'weight', 42 : 'knot_tol', 43 : 'control_point_tol', 44 : 'fit_tol',
#	70 : 'flag', 71 : 'degree', 
#	72 : 'num_knots', 73 : 'num_control_points', 74 : 'num_fit_points',
#	210 : 'normal.x', 220 : 'normal.y', 230 : 'normal.z', 
#

class CSpline(CEntity):
	def __init__(self):
		CEntity.__init__(self, 'SPLINE', 'Edge')
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

		self.normal = Vector()
		
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

	def build(self, vn):
		verts = []
		lines = []
		for vert in self.control_points:
			verts.append(vert)
			lines.append((vn, vn+1))
			vn += 1
		lines.pop()
		return((verts, lines, vn))


#
#	class CSolid(CEntity):
#	10 : 'point0.x', 20 : 'point0.y', 30 : 'point0.z', 
#	11 : 'point1.x', 21 : 'point1.y', 31 : 'point1.z', 
#	12 : 'point2.x', 22 : 'point2.y', 32 : 'point2.z', 
#	13 : 'point3.x', 23 : 'point3.y', 33 : 'point3.z', 
#	39 : 'thickness',
#

class CSolid(CEntity):
	def __init__(self):
		CEntity.__init__(self, 'SOLID', 'Face')
		self.point0 = Vector()
		self.point1 = Vector()
		self.point2 = Vector()
		self.point3 = Vector()
		self.thickness = 1.0
		
	def display(self):
		CEntity.display(self)
		print(self.point0)
		print(self.point1)
		print(self.point2)
		print(self.point3)

	def build(self, vn):
		verts = [self.point0, self.point1, self.point2]
		if self.point2 == self.point3:
			face = (vn, vn+1, vn+2)
			vn += 3
		else:
			verts.append( self.point3 )
			face = (vn, vn+1, vn+2, vn+3)
			vn += 4			
		return((verts, [face], vn))
		
#
#	class CText(CEntity):
#	1 : 'text', 7 : 'style',
#	10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
#	11 : 'alignment_point.x', 21 : 'alignment_point.y', 31 : 'alignment_point.z', 
#	40 : 'height', 41 : 'x_scale', 
#	50 : 'rotation_angle', 51 : 'oblique_angle', 
#	71 : 'flags', 72 : 'horizontal_justification',  73 : 'vertical_justification',	
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
		
	def display(self):
		CEntity.display(self)
		print("%s %s" % (self.text, self.style))
		print(self.insertion_point)
		print(self.alignment_point)
		
	def draw(self):
		drawText(self.text,  self.insertion_point, self.height, self.x_scale, self.rotation_angle, self.oblique_angle)
		return


def drawText(text, loc, size, spacing, angle, shear):
		bpy.ops.object.text_add(
			view_align=False, 
			enter_editmode=False, 
			location= loc, 
			rotation=(0, 0, angle))
		cu = bpy.context.object.data
		cu.body = text
		cu.text_size = size
		cu.word_spacing = spacing
		cu.shear = shear
		return

#
#	class CTolerance(CEntity):
#	3 : 'style',
#	10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
#	11 : 'direction.x', 21 : 'direction.y', 31 : 'direction.z', 
#

class CTolerance(CEntity):
	def __init__(self):
		CEntity.__init__(self, 'TOLERANCE', None)
		self.stype = ""
		self.insertion_point = Vector()
		self.direction = Vector()

#
#	class CTrace(CEntity):
#	10 : 'point0.x', 20 : 'point0.y', 30 : 'point0.z', 
#	11 : 'point1.x', 21 : 'point1.y', 31 : 'point1.z', 
#	12 : 'point2.x', 22 : 'point2.y', 32 : 'point2.z', 
#	13 : 'point3.x', 23 : 'point3.y', 33 : 'point3.z', 
#	39 : 'thickness',
#

class CTrace(CEntity):
	def __init__(self):
		CEntity.__init__(self, 'TRACE', 'Edge')
		self.point0 = Vector()
		self.point1 = Vector()
		self.point2 = Vector()
		self.point3 = Vector()
		self.thickness = 1.0
	def display(self):
		CEntity.display(self)
		print(self.point0)
		print(self.point1)
		print(self.point2)
		print(self.point3)

#
#	class CVertex(CEntity):
#	10 : 'location.x', 20 : 'location.y', 30 : 'location.z', 
#	40 : 'start_width', 41 : 'end_width', 42 : 'bulge', 
#	50 : 'tangent',
#	70 : 'flags',
#	71 : 'index1', 72 : 'index2', 73 : 'index3', 74 : 'index4', 
#

class CVertex(CEntity):
	def __init__(self):
		CEntity.__init__(self, 'VERTEX', None)
		self.location = Vector()
		self.start_width = 1.0
		self.end_width = 1.0
		self.bulge = 0.0
		self.tangent = 0.0
		self.flags = 0

	def display(self):
		return

	def draw(self):
		return

#			
#	class CViewPort(CEntity):
#	10 : 'center.x', 20 : 'center.y', 30 : 'center.z', 
#	12 : 'view_center.x', 22 : 'view_center.y', 32 : 'view_center.z', 
#	13 : 'snap_base.x', 23 : 'snap_base.y', 33 : 'snap_base.z', 
#	14 : 'snap_spacing.x', 24 : 'snap_spacing.y', 34 : 'snap_spacing.z', 
#	15 : 'grid_spacing.x', 25 : 'grid_spacing.y', 35 : 'grid_spacing.z', 
#	16 : 'view_direction.x', 26 : 'view_direction.y', 36 : 'view_direction.z', 
#	40 : 'width', 41 : 'height',
#	68 : 'status', 69 : 'id',
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
#	class CWipeOut(CEntity):
#	10 : 'point.x', 20 : 'point.y', 30 : 'point.z', 
#	11 : 'direction.x', 21 : 'direction.y', 31 : 'direction.z', 
#

class CWipeOut(CEntity):
	def __init__(self):
		CEntity.__init__(self, 'WIPEOUT', None)
		self.point = Vector()
		self.direction = Vector()

#
#
#

DxfEntityAttributes = {
'3DFACE'	: {
	10 : 'point0.x', 20 : 'point0.y', 30 : 'point0.z', 
	11 : 'point1.x', 21 : 'point1.y', 31 : 'point1.z', 
	12 : 'point2.x', 22 : 'point2.y', 32 : 'point2.z', 
	13 : 'point3.x', 23 : 'point3.y', 33 : 'point3.z', 
	70 : 'flags',
	},

'3DSOLID'	: {
	1 : 'data', 3 : 'more', 70 : 'version',
	},

'ACAD_PROXY_ENTITY'	: {
	70 : 'format',
	90 : 'id', 91 : 'class', 92 : 'graphics_size', 93 : 'entity_size', 95: 'format',
	310 : 'data', 330 : 'id1', 340 : 'id2', 350 : 'id3', 360 : 'id4', 
	},

'ARC'		: {
	10 : 'center.x', 20 : 'center.y', 30 : 'center.z', 
	40 : 'radius',
	50 : 'start_angle', 51 : 'end_angle'
	},

'ARCALIGNEDTEXT'	: {
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

'ATTDEF'	: {
	1 : 'text', 2 : 'tag', 3 : 'prompt', 7 : 'style',
	10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
	11 : 'alignment_point.x', 21 : 'alignment_point.y', 31 : 'alignment_point.z', 
	40 : 'height', 41 : 'x_scale', 
	50 : 'rotation_angle', 51 : 'oblique_angle', 
	70 : 'flags', 71 : 'text_generation_flags', 
	72 : 'horizontal_justification',  74 : 'vertical_justification',	
	},


'ATTRIB'	: {
	1 : 'text', 2 : 'tag', 3 : 'prompt', 7 : 'style',
	10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
	11 : 'alignment_point.x', 21 : 'alignment_point.y', 31 : 'alignment_point.z', 
	40 : 'height', 41 : 'x_scale', 
	50 : 'rotation_angle', 51 : 'oblique_angle', 
	70 : 'flags', 73 : 'length', 
	71 : 'text_generation_flags', 72 : 'horizontal_justification',  74 : 'vertical_justification', 	
	},

'BLOCK'		: {
	1 : 'xref', 2 : 'name', 3 : 'also_name', 
	10 : 'base_point.x', 20 : 'base_point.y', 30 : 'base_point.z', 
	40 : 'size', 41 : 'x_scale', 
	50 : 'rotation_angle', 51 : 'oblique_angle', 	
	70 : 'flags', 
	},

'CIRCLE'	: {
	10 : 'center.x', 20 : 'center.y', 30 : 'center.z', 
	40 : 'radius'
	},

'DIMENSION'	: {
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

'ELLIPSE'	: {
	10 : 'center.x', 20 : 'center.y', 30 : 'center.z', 
	11 : 'end_point.x', 21 : 'end_point.y', 31 : 'end_point.z', 
	40 : 'ratio', 41 : 'start', 42 : 'end',
	},

'HATCH'		: {
	2 : 'pattern',
	10 : 'point.x', 20 : 'point.y', 30 : 'point.z', 
	41 : 'scale', 47 : 'pixelsize', 52 : 'angle',
	70 : 'fill', 71 : 'associativity', 75: 'style', 77 : 'double', 
	78 : 'numlines', 91 : 'numpaths', 98 : 'numseeds',
	},

'IMAGE'		: {
	10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
	11 : 'u_vector.x', 21 : 'u_vector.y', 31 : 'u_vector.z', 
	12 : 'v_vector.x', 22 : 'v_vector.y', 32 : 'v_vector.z', 
	13 : 'size.x', 23 : 'size.y', 33 : 'size.z', 
	14 : 'clip.x', 24 : 'clip.y', 34 : 'clip.z', 
	70 : 'display', 71 : 'cliptype', 
	90 : 'version',
	280 : 'clipstate', 281 : 'brightness', 282 : 'contrast', 283 : 'fade', 
	340 : 'image', 360 : 'reactor'
	},

'INSERT'	: {
	1 : 'attributes_follow', 2 : 'name',
	10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
	41 : 'x_scale', 42 : 'y_scale', 43 : 'z_scale', 
	44 : 'column_spacing', 45 : 'row_spacing', 
	50 : 'rotation_angle', 66 : 'attributes_follow',
	70 : 'column_count', 71 : 'row_count', 
	},

'LEADER'	: {
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

'LINE'		: {
	10 : 'start_point.x', 20 : 'start_point.y', 30 : 'start_point.z', 
	11 : 'end_point.x', 21 : 'end_point.y', 31 : 'end_point.z', 
	39 : 'thickness',
	},

'LWPOLYLINE'	: {
	10 : ['new_vertex(data)'], 20 : 'vertex.y', 30 : 'vertex.z', 
	38 : 'elevation', 39 : 'thickness',
	40 : 'start_width', 41 : 'end_width', 42 : 'bulge', 43 : 'constant_width',
	70 : 'flags', 90 : 'numverts'
	},
		
'MLINE'	: {
	10 : 'start_point.x', 20 : 'start_point.y', 30 : 'start_point.z', 
	11 : ['new_vertex(data)'], 21 : 'vertex.y', 31 : 'vertex.z', 
	12 : ['new_seg_dir(data)'], 22 : 'seg_dir.y', 32 : 'seg_dir.z', 
	13 : ['new_miter_dir(data)'], 23 : 'miter_dir.y', 33 : 'miter_dir.z', 
	40 : 'scale', 41 : 'elem_param', 42 : 'fill_param',
	70 : 'justification', 71 : 'flags',
	72 : 'numverts', 73 : 'numelems', 74 : 'numparam', 75 : 'numfills',
	340 : 'id'
	},
		
'MTEXT'		: {
	1 : 'text', 3: 'more_text', 7 : 'style',
	10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
	11 : 'alignment_point.x', 21 : 'alignment_point.y', 31 : 'alignment_point.z', 
	40 : 'nominal_height', 41 : 'reference_width', 42: 'width', 43 : 'height', 44 : 'line_spacing',
	50 : 'rotation_angle', 
	71 : 'attachment_point', 72 : 'drawing_direction',  73 : 'spacing_style',	
	},

'POINT'		: {
	10 : 'point.x', 20 : 'point.y', 30 : 'point.z', 
	39 : 'thickness', 50 : 'orientation'
	},

'POLYLINE'	: {
	1 : 'verts_follow', 2 : 'name',
	10 : 'elevation.x', 20 : 'elevation.y', 30 : 'elevation.z', 
	40 : 'start_width', 41 : 'end_width', 
	66 : 'verts_follow_flag',
	70 : 'flags', 71 : 'row_count', 72 : 'column_count', 
	73 : 'row_density', 74 : 'column_density', 75 : 'linetype',
	},

'RAY'		: {
	10 : 'point.x', 20 : 'point.y', 30 : 'point.z', 
	11 : 'direction.x', 21 : 'direction.y', 31 : 'direction.z', 
	},

'RTEXT'		: {
	1 : 'text', 7 : 'style',
	10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
	40 : 'height', 
	50 : 'rotation_angle',
	70 : 'flags',
	},

'SHAPE'		: {
	2 : 'name', 
	10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
	39 : 'thickness',
	40 : 'size', 41 : 'x_scale', 
	50 : 'rotation_angle', 51 : 'oblique_angle', 	
	},

'SOLID'		: {
	10 : 'point0.x', 20 : 'point0.y', 30 : 'point0.z', 
	11 : 'point1.x', 21 : 'point1.y', 31 : 'point1.z', 
	12 : 'point2.x', 22 : 'point2.y', 32 : 'point2.z', 
	13 : 'point3.x', 23 : 'point3.y', 33 : 'point3.z', 
	39 : 'thickness',
	},

'SPLINE'	: {
	10 : ['new_control_point(data)'], 20 : 'control_point.y', 30 : 'control_point.z', 
	11 : ['new_fit_point(data)'], 21 : 'fit_point.y', 31 : 'fit_point.z', 
	40 : ['new_knot_value(data)'], 
	12 : 'start_tangent.x', 22 : 'start_tangent.y', 32 : 'start_tangent.z', 
	13 : 'end_tangent.x', 23 : 'end_tangent.y', 33 : 'end_tangent.z', 
	41 : 'weight', 42 : 'knot_tol', 43 : 'control_point_tol', 44 : 'fit_tol',
	70 : 'flag', 71 : 'degree', 
	72 : 'num_knots', 73 : 'num_control_points', 74 : 'num_fit_points',
	210 : 'normal.x', 220 : 'normal.y', 230 : 'normal.z', 
	},

'TEXT'		: {
	1 : 'text', 7 : 'style',
	10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
	11 : 'alignment_point.x', 21 : 'alignment_point.y', 31 : 'alignment_point.z', 
	40 : 'height', 41 : 'x_scale', 
	50 : 'rotation_angle', 51 : 'oblique_angle', 
	71 : 'flags', 72 : 'horizontal_justification',  73 : 'vertical_justification',	
	},

'TOLERANCE'	: {
	3 : 'style',
	10 : 'insertion_point.x', 20 : 'insertion_point.y', 30 : 'insertion_point.z', 
	11 : 'direction.x', 21 : 'direction.y', 31 : 'direction.z', 
	},

'TRACE'		: {
	10 : 'point0.x', 20 : 'point0.y', 30 : 'point0.z', 
	11 : 'point1.x', 21 : 'point1.y', 31 : 'point1.z', 
	12 : 'point2.x', 22 : 'point2.y', 32 : 'point2.z', 
	13 : 'point3.x', 23 : 'point3.y', 33 : 'point3.z', 
	39 : 'thickness',
	},

'VERTEX'	: {
	10 : 'location.x', 20 : 'location.y', 30 : 'location.z', 
	40 : 'start_width', 41 : 'end_width', 42 : 'bulge', 
	50 : 'tangent',
	70 : 'flags',
	71 : 'index1', 72 : 'index2', 73 : 'index3', 74 : 'index4', 
	},

'VIEWPORT'	: {
	10 : 'center.x', 20 : 'center.y', 30 : 'center.z', 
	12 : 'view_center.x', 22 : 'view_center.y', 32 : 'view_center.z', 
	13 : 'snap_base.x', 23 : 'snap_base.y', 33 : 'snap_base.z', 
	14 : 'snap_spacing.x', 24 : 'snap_spacing.y', 34 : 'snap_spacing.z', 
	15 : 'grid_spacing.x', 25 : 'grid_spacing.y', 35 : 'grid_spacing.z', 
	16 : 'view_direction.x', 26 : 'view_direction.y', 36 : 'view_direction.z', 
	40 : 'width', 41 : 'height',
	68 : 'status', 69 : 'id',
	},

'WIPEOUT'	: {
	10 : 'point.x', 20 : 'point.y', 30 : 'point.z', 
	11 : 'direction.x', 21 : 'direction.y', 31 : 'direction.z', 
	},

}


#
#	Flags
#

# Polyline flags
PL_CLOSED 		= 0x01
PL_CURVE_FIT_VERTS	= 0x02
PL_SPLINE_FIT_VERTS	= 0x04
PL_3D_POLYLINE		= 0x08
PL_3D_POLYGON_MESH	= 0x10
PL_CLOSED_IN_N_DIR	= 0x20
PL_POLYFACE_MESH	= 0x40
PL_CONTINUOUS		= 0x80


# Vertex flags
VX_EXTRA_FLAG_CREATED		= 0x01
VX_CURVE_FIT_TANGENT_DEFINED	= 0x02
VX_SPLINE_VERTEX_CREATED	= 0x08
VX_SPLINE_FRAME_CONTROL_POINT	= 0x10
VX_3D_POLYLINE_VERTEX		= 0x20
VX_3D_POLYGON_MESH_VERTEX	= 0x40
VX_POLYFACE_MESH_VERTEX		= 0x80

# 3DFACE flags

F3D_EDGE0_INVISIBLE = 0x01
F3D_EDGE1_INVISIBLE = 0x02
F3D_EDGE2_INVISIBLE = 0x04
F3D_EDGE3_INVISIBLE = 0x08

#
#	readDxfFile(filePath):
#

def readDxfFile(filePath):	
	global toggle, theCodec

	fileName = os.path.expanduser(filePath)
	(shortName, ext) = os.path.splitext(fileName)
	if ext != ".dxf":
		print("Error: Not a dxf file: " + fileName)
		return
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
#	 0
#	SECTION
#	  2
#	HEADER
#	
#	  9
#	$<variable>
#	<group code>
#	<value>
#	
#	  0
#	ENDSEC

	
def parseHeader(section, statements, handles):
	while statements:
		(code,data) = statements.pop()
		if code == 0:
			if data == 'ENDSEC':
				return

	return


#	  0
#	SECTION
#	  2
#	CLASSES
#	
#	  0
#	CLASS
#	  1
#	<class dxf record>
#	  2
#	<class name>
#	  3
#	<app name>
#	90
#	<flag>
#	280
#	<flag>
#	281
#	<flag>
#	
#	  0
#	ENDSEC 		

def parseClasses(section, statements, handles):
	while statements:
		(code,data) = statements.pop()
		if code == 0:
			if data == 'ENDSEC':
				return

	return
	

#	  0
#	SECTION
#	  2
#	TABLES
#	
#	  0
#	TABLE
#	  2
#	<table type>
#	  5
#	<handle>
#	100
#	AcDbSymbolTable
#	70
#	<max. entries>
#	
#	  0
#	<table type>
#	  5
#	<handle>
#	100
#	AcDbSymbolTableRecord
#	.
#	. <data>
#	.
#	
#	  0
#	ENDTAB
#	
#	  0
#	ENDSEC 

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
	
#	  0
#	SECTION
#	  2
#	BLOCKS
#	
#	  0
#	BLOCK
#	  5
#	<handle>
#	100
#	AcDbEntity
#	  8
#	<layer>
#	100
#	AcDbBlockBegin
#	  2
#	<block name>
#	70
#	<flag>
#	10
#	<X value>
#	20
#	<Y value>
#	30
#	<Z value>
#	  3
#	<block name>
#	  1
#	<xref path>
#	
#	  0
#	<entity type>
#	.
#	. <data>
#	.
#	
#	  0
#	ENDBLK
#	  5
#	<handle>
#	100
#	AcDbBlockEnd
#	
#	  0
#	ENDSEC 

def parseBlocks(section, statements, handles):
	while statements:
		(code,data) = statements.pop()
		if code == 0:
			if data == 'ENDSEC':
				return

	return

#	  0
#	SECTION
#	  2
#	ENTITIES
#	
#	  0
#	<entity type>
#	  5
#	<handle>
#	330
#	<pointer to owner>
#	100
#	AcDbEntity
#	  8
#	<layer>
#	100
#	AcDb<classname>
#	.
#	. <data>
#	.
#	
#	  0
#	ENDSEC

Ignorables = ['DIMENSION', 'TEXT', 'VIEWPORT']

ClassCreators = {
	'3DFACE': 		'C3dFace()', 
	'3DSOLID':		'C3dSolid()',
	'ACAD_PROXY_ENTITY':	'CAcadProxyEntity()',
	'ACAD_ZOMBIE_ENTITY':	0,
	'ARC':			'CArc()',
	'ARCALIGNEDTEXT':	'CArcAlignedText()',
	'ATTDEF':		'CAttdef()',
	'ATTRIB':		'CAttrib()',
	'BODY':			0,
	'CIRCLE':		'CCircle()',
	'DIMENSION':		'CDimension()',
	'ELLIPSE':		'CEllipse()',
	'HATCH':		'CHatch()',
	'IMAGE':		'CImage()',
	'INSERT':		'CInsert()',
	'LEADER':		'CLeader()',
	'LINE':			'CLine()',
	'LWPOLYLINE':		'CLWPolyLine()',
	'MLINE':		'CMLine()',
	'MTEXT':		'CMText()',
	'OLEFRAME':		0,
	'OLE2FRAME':		0,
	'POINT':		'CPoint()',
	'POLYLINE':		'CPolyLine()',
	'RAY':			'CRay()',
	'REGION':		0,
	'RTEXT':		'CRText',
	'SEQEND':		0,
	'SHAPE':		'CShape()',
	'SOLID':		'CSolid()',
	'SPLINE':		'CSpline()',
	'TEXT':			'CText()',
	'TOLERANCE':		'CTolerance()',
	'TRACE':		'CTrace()',
	'VERTEX':		'CVertex()',
	'VIEWPORT':		'CViewPort()',
	'WIPEOUT':		'CWipeOut()',
	'XLINE':		'CXLine()',
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


#	  0
#	SECTION
#	  2
#	OBJECTS
#	
#	  0
#	DICTIONARY
#	  5
#	<handle>
#	100
#	AcDbDictionary
#	
#	  3
#	<dictionary name>
#	350
#	<handle of child>
#	
#	  0
#	<object type>
#	.
#	. <data>
#	.
#	
#	  0
#	ENDSEC 

def parseObjects(data, statements, handles):
	while statements:
		(code,data) = statements.pop()
		if code == 0:
			if data == 'ENDSEC':
				return

	return
			
#
#	buildGeometry(entities):
#	buildGeometryType(entities, drawtype):
#	addMesh(name, verts, edges, faces):							
#

def buildGeometry(entities):
	(verts, faces) = buildGeometryType(entities, 'Face')
	if verts:
		me = bpy.data.meshes.new('FaceMesh')
		me.from_pydata(verts, [], faces)
		ob = addObject('Solid', me)
		removeDoubles(ob)
	
	(verts, edges) = buildGeometryType(entities, 'Edge')
	if verts:
		if toggle & T_Curves:
			cu = bpy.data.curves.new('Lines', 'CURVE')
			cu.dimensions = '3D'
			buildSplines(cu, verts, edges)
			ob = addObject('Lines', cu)
		else:
			me = bpy.data.meshes.new('EdgeMesh')
			me.from_pydata(verts, edges, [])
			ob = addObject('Wires', me)
			removeDoubles(ob)

	for ent in entities:
		if ent.drawtype in ['Face', 'Edge']:
			pass
		else:
			ent.draw()

	return

def buildSplines(cu, verts, edges):
	points = []
	for v in verts:
		pt = list(v)
		points.append(pt)

	for (v0,v1) in edges:
		spline = cu.splines.new('BEZIER')
		spline.bezier_points.add(1)
		#spline.endpoint_u = True
		#spline.order_u = 2
		spline.resolution_u = 1
		
		spline.bezier_points[0].co = verts[v0]
		spline.bezier_points[1].co = verts[v1]
	
def buildGeometryType(entities, drawtype):
	verts = []
	faces = []
	vn = 0
	for ent in entities:
		if ent.drawtype == drawtype:
			(vrts, fcs, vn) = ent.build(vn)
			verts.extend(vrts)
			faces.extend(fcs)
	return (verts, faces)
	
def addObject(name, data):
	ob = bpy.data.objects.new(name, data)
	scn = bpy.context.scene
	scn.objects.link(ob)
	scn.objects.active = ob
	return ob


def removeDoubles(ob):
	global theMergeLimit
	if toggle & T_Merge:
		bpy.ops.object.mode_set(mode='EDIT')
		bpy.ops.mesh.remove_doubles(limit=theMergeLimit)
		bpy.ops.object.mode_set(mode='OBJECT')


#
#	clearScene(context):
#
	
def clearScene():
	global toggle
	scn = bpy.context.scene
	print("clearScene %s %s" % (toggle & T_Replace, scn))
	if not toggle & T_Replace:
		return scn

	for ob in scn.objects:
		if ob.type in ["MESH", "CURVE", "TEXT"]:
			scn.objects.active = ob
			bpy.ops.object.mode_set(mode='OBJECT')
			scn.objects.unlink(ob)
			del ob
	return scn

#
#	readAndBuildDxfFile(filepath):
#

def readAndBuildDxfFile(filepath):
	if toggle & T_Replace:
		clearScene()
	sections = readDxfFile(filepath)
	print("Building geometry")
	buildGeometry(sections['ENTITIES'].data)
	print("Done")
	return

#
#	User interface
#

DEBUG= False
from bpy.props import *

def tripleList(list1):
	list3 = []
	for elt in list1:
		list3.append((elt,elt,elt))
	return list3

class IMPORT_OT_autocad_dxf(bpy.types.Operator):
	'''Import from DXF file format (.dxf)'''
	bl_idname = "import_scene.autocad_dxf"
	bl_description = 'Import from DXF file format (.dxf)'
	bl_label = "Import DXF"
	bl_space_type = "PROPERTIES"
	bl_region_type = "WINDOW"

	filepath = StringProperty(name="File Path", description="Filepath used for importing the DXF file", maxlen= 1024, default= "")

	merge = BoolProperty(name="Remove doubles", description="Merge coincident vertices", default=toggle&T_Merge)
	mergeLimit = FloatProperty(name="Merge limit", description="Merge limit", default = theMergeLimit*1e4)

	replace = BoolProperty(name="Replace scene", description="Replace scene", default=toggle&T_Replace)
	curves = BoolProperty(name="Lines as curves", description="Lines as curves", default=toggle&T_Curves)
	debug = BoolProperty(name="Debug", description="Unknown codes generate errors", default=toggle&T_Debug)
	verbose = BoolProperty(name="Verbose", description="Print debug info", default=toggle&T_Verbose)

	codecs = tripleList(['iso-8859-15', 'utf-8', 'ascii'])
	codec = EnumProperty(name="Codec", description="Codec",  items=codecs, default = '1')

		
	def execute(self, context):
		global toggle, theMergeLimit, theCodec
		O_Merge = T_Merge if self.properties.merge else 0
		O_Replace = T_Replace if self.properties.replace else 0
		O_Curves = T_Curves if self.properties.curves else 0
		O_Debug = T_Debug if self.properties.debug else 0
		O_Verbose = T_Verbose if self.properties.verbose else 0

		toggle =  O_Merge | O_Replace | O_Curves | O_Debug | O_Verbose
		theMergeLimit = self.properties.mergeLimit*1e-4
		theCodec = self.properties.codec

		readAndBuildDxfFile(self.properties.filepath)
		return {'FINISHED'}

	def invoke(self, context, event):
		wm = context.manager
		wm.add_fileselect(self)
		return {'RUNNING_MODAL'}

def register():
	# registerPanels()
	bpy.types.register(IMPORT_OT_autocad_dxf)
	menu_func = lambda self, context: self.layout.operator(IMPORT_OT_autocad_dxf.bl_idname, text="Autocad (.dxf)...")
	bpy.types.INFO_MT_file_import.append(menu_func)
	return
 
def unregister():
	# unregisterPanels()
	bpy.types.unregister(IMPORT_OT_autocad_dxf)
	menu_func = lambda self, context: self.layout.operator(IMPORT_OT_autocad_dxf.bl_idname, text="Autocad (.dxf)...")
	bpy.types.INFO_MT_file_import.remove(menu_func)

if __name__ == "__main__":
	register()


