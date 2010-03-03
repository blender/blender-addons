# add_mesh_diamond.py Copyright (C) 2008-2009, FourMadMen.com
#
# add diamond to the blender 2.50 add->mesh menu
# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****

# blender Extensions menu registration (in user Prefs)
"Add Diamond (View3D > Add > Mesh > Diamond)"

"""
Name: 'Diamond'
Blender: 250
Group: 'AddMesh'
Tip: 'Add Diamond Object...'
__author__ = ["Four Mad Men", "FourMadMen.com"]
__version__ = '2.00'
__url__ = [
	"Script, http://www.fourmadmen.com/blender/scripts/AddMesh/diamond/add_mesh_diamond.py", 
	"Script Index, http://www.fourmadmen.com/blender/scripts/index.html", 
	"Author Site , http://www.fourmadmen.com"]
email__=["bwiki {at} fourmadmen {dot} com"]

Usage:

* Launch from Add Mesh menu

* Modify parameters as desired or keep defaults

"""



import bpy
import Mathutils
from math import pi

def add_diamond(segments, girdle_radius, table_radius, crown_height, pavillion_height):
	Vector = Mathutils.Vector
	Quaternion = Mathutils.Quaternion
	
	PI_2 = pi * 2
	z_axis = (0, 0, -1)

	verts = []
	faces = []
	
	tot_verts = segments * 2 + 2
	
	height = crown_height + pavillion_height
	half_height = height * .5
	
	verts.extend( Vector(0, 0, -half_height) )
	verts.extend( Vector(0, 0, half_height) )
	
	i = 2
	for index in range(segments):
		quat = Quaternion(z_axis, (index / segments) * PI_2)
		
		angle = PI_2 * index / segments
		
		vec = Vector(table_radius, 0, -half_height) * quat
		verts.extend([vec.x, vec.y, vec.z])
		it1 = i
		i+=1
		
		vec = Vector(girdle_radius, 0, half_height-pavillion_height) * quat
		verts.extend([vec.x, vec.y, vec.z])
		ib1 = i
		i+=1
		
		if i>4:
			faces.extend( [0, it1, it1-2, 0] )
			faces.extend( [it1, ib1, ib1-2, it1-2] )
			faces.extend( [1, ib1-2, ib1, 1] )
	
	faces.extend( [0, 2, it1, 0] )
	faces.extend( [it1, 2, 3, ib1] )
	faces.extend( [1, ib1, 3, 1] )
	
	return verts, faces

from bpy.props import IntProperty, FloatProperty

class AddDiamond(bpy.types.Operator):
	'''Add a diamond mesh.'''
	bl_idname = "mesh.diamond_add"
	bl_label = "Add Diamond"
	bl_options = {'REGISTER', 'UNDO'}

	segments = IntProperty(name="Segments",
		description="Number of segments for the diamond",
		default=32, min=3, max=256)
	girdle_radius = FloatProperty(name="Girdle Radius",
		description="Girdle radius of the diamond",
		default=1.0, min=0.01, max=100.0)
	table_radius = FloatProperty(name="Table Radius",
		description="Girdle radius of the diamond",
		default=0.8, min=0.01, max=100.0)
	crown_height = FloatProperty(name="Crown Height",
		description="Crown height of the diamond",
		default=0.25, min=0.01, max=100.0)
	pavillion_height = FloatProperty(name="Pavillion Height",
		description="pavillion height of the diamond",
		default=1.0, min=0.01, max=100.0)

	def execute(self, context):
    
		verts_loc, faces = add_diamond(self.properties.segments,
			self.properties.girdle_radius,
			self.properties.table_radius,
			self.properties.crown_height,
			self.properties.pavillion_height)

		mesh = bpy.data.meshes.new("Diamond")
		
		mesh.add_geometry(int(len(verts_loc) / 3), 0, int(len(faces) / 4))
		mesh.verts.foreach_set("co", verts_loc)
		mesh.faces.foreach_set("verts_raw", faces)
		
		scene = context.scene

		# ugh
		for ob in scene.objects:
			ob.selected = False

		mesh.update()
		ob_new = bpy.data.objects.new("Diamond", mesh)
		ob_new.data = mesh
		scene.objects.link(ob_new)
		scene.objects.active = ob_new
		ob_new.selected = True
		
		ob_new.location = tuple(context.scene.cursor_location)
		
		return {'FINISHED'}


# Register the operator
# Add to a menu, reuse an icon used elsewhere that happens to have fitting name
# unfortunately, the icon shown is the one I expected from looking at the
# blenderbuttons file from the release/datafiles directory

menu_func = (lambda self, context: self.layout.operator(AddDiamond.bl_idname,
                                        text="Add Diamond", icon='PLUGIN'))

def register():
    bpy.types.register(AddDiamond)
    bpy.types.INFO_MT_mesh_add.append(menu_func)

def unregister():
    bpy.types.unregister(AddDiamond)
    bpy.types.INFO_MT_mesh_add.remove(menu_func)
