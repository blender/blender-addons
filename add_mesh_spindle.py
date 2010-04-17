# add_mesh_spindle.py Copyright (C) 2008-2009, FourMadMen.com
#
# add spindle to the blender 2.50 add->mesh menu
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

bl_addon_info = {
    'name': 'Add Mesh: Spindle',
    'author': 'fourmadmen',
    'version': '2.0',
    'blender': (2, 5, 3),
    'location': 'View3D > Add > Mesh ',
    'description': 'Adds a mesh Spindle to the Add Mesh menu',
    'url': 'http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/Add_Spindle',
    'category': 'Add Mesh'}

"""
Name: 'Spindle'
Blender: 250
Group: 'AddMesh'
Tip: 'Add Spindle Object...'
__author__ = ["Four Mad Men", "FourMadMen.com"]
__version__ = '0.10'
__url__ = [""]
email__=["bwiki {at} fourmadmen {dot} com"]

Usage:

* Launch from Add Mesh menu

* Modify parameters as desired or keep defaults

"""


import bpy
import mathutils
from math import pi


def add_spindle( spindle_segments, spindle_radius, spindle_height, spindle_cap_height):

    Vector = mathutils.Vector
    RotationMatrix = mathutils.RotationMatrix

    verts = []
    faces = []

    tot_verts = spindle_segments * 2 + 2

    half_height = spindle_height * .5

    verts.extend( Vector(0, 0, half_height + spindle_cap_height) )
    verts.extend( Vector(0, 0, -half_height - spindle_cap_height) )

    i = 2
    for index in range(spindle_segments):
        mtx = RotationMatrix( 2 * pi * float(index)/spindle_segments, 3, 'Z' )

        verts.extend( Vector(spindle_radius, 0, half_height) * mtx )
        it1 = i
        i+=1

        verts.extend( Vector(spindle_radius, 0, -half_height) * mtx )
        ib1 = i
        i+=1

        if i>4:
            faces.extend( (it2, it1, 0, it2) )
            faces.extend( (it1, it2, ib2, ib1) )
            faces.extend( (ib1, ib2, 1, ib1) )

        it2 = it1
        ib2 = ib1

    faces.extend( (tot_verts-2, 2, 0, tot_verts-2) )
    faces.extend( (3, 2, tot_verts-2, tot_verts-1) )
    faces.extend( (3, tot_verts-1, 1, 3) )

    return verts, faces

from bpy.props import FloatProperty
from bpy.props import IntProperty

class AddSpindle(bpy.types.Operator):
    '''Add a spindle mesh.'''
    bl_idname = "mesh.spindle_add"
    bl_label = "Add Spindle"
    bl_options = {'REGISTER', 'UNDO'}

    spindle_segments = IntProperty(name="Segments",
        description="Number of segments of the spindle",
        default=32, min=3, max=256)
    spindle_radius = FloatProperty(name="Radius",
        description="Radius of the spindle",
        default=1.00, min=0.01, max=100.00)
    spindle_height = FloatProperty(name="Height",
        description="Height of the spindle",
        default=1.00, min=0.01, max=100.00)
    spindle_cap_height = FloatProperty(name="Cap Height",
        description="Cap height of the spindle",
        default=0.50, min=0.01, max=100.00)

    def execute(self, context):

        verts_loc, faces = add_spindle(self.properties.spindle_segments, self.properties.spindle_radius, self.properties.spindle_height, self.properties.spindle_cap_height)

        mesh = bpy.data.meshes.new("Spindle")

        mesh.add_geometry(int(len(verts_loc) / 3), 0, int(len(faces) / 4))
        mesh.verts.foreach_set("co", verts_loc)
        mesh.faces.foreach_set("verts_raw", faces)
        mesh.faces.foreach_set("smooth", [False] * len(mesh.faces))

        scene = context.scene

        # ugh
        for ob in scene.objects:
            ob.selected = False

        mesh.update()
        ob_new = bpy.data.objects.new("Spindle", mesh)
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

menu_func = (lambda self, context: self.layout.operator(AddSpindle.bl_idname, text="Add Spindle", icon='PLUGIN'))

def register():
    bpy.types.register(AddSpindle)
    bpy.types.INFO_MT_mesh_add.append(menu_func)

def unregister():
    bpy.types.unregister(AddSpindle)
    bpy.types.INFO_MT_mesh_add.remove(menu_func)

# Remove "Spindle" menu from the "Add Mesh" menu.
#space_info.INFO_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
    register()
