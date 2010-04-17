# add_mesh_wedge.py Copyright (C) 2008-2009, FourMadMen.com
#
# add wedge to the blender 2.50 add->mesh menu
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
    'name': 'Add Mesh: Wedge',
    'author': 'fourmadmen',
    'version': '1.1',
    'blender': (2, 5, 3),
    'location': 'View3D > Add > Mesh ',
    'description': 'Adds a mesh Wedge to the Add Mesh menu',
    'url': 'http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/Add_Wedge',
    'category': 'Add Mesh'}


"""
Name: 'Wedge'
Blender: 250
Group: 'AddMesh'
Tip: 'Add Wedge Object...'
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


def add_wedge( wedge_width, wedge_height, wedge_depth):

    Vector = mathutils.Vector

    verts = []
    faces = []

    half_width = wedge_width * .5
    half_height = wedge_height * .5
    half_depth = wedge_depth * .5
  
    verts.extend( Vector(-half_width, -half_height, half_depth) )
    verts.extend( Vector(-half_width, -half_height, -half_depth) )

    verts.extend( Vector(half_width, -half_height, half_depth) )
    verts.extend( Vector(half_width, -half_height, -half_depth) )

    verts.extend( Vector(-half_width, half_height, half_depth) )
    verts.extend( Vector(-half_width, half_height, -half_depth) )

    faces.extend( [0, 2, 4, 0] )
    faces.extend( [1, 3, 5, 1] )
    faces.extend( [0, 1, 3, 2] )
    faces.extend( [0, 4, 5, 1] )
    faces.extend( [2, 3, 5, 4] )

    return verts, faces

from bpy.props import FloatProperty

class AddWedge(bpy.types.Operator):
    '''Add a wedge mesh.'''
    bl_idname = "mesh.wedge_add"
    bl_label = "Add Wedge"
    bl_options = {'REGISTER', 'UNDO'}

    wedge_width = FloatProperty(name="Width",
        description="Width of Wedge",
        default=2.00, min=0.01, max=100.00)
    wedge_height = FloatProperty(name="Height",
        description="Height of Wedge",
        default=2.00, min=0.01, max=100.00)
    wedge_depth = FloatProperty(name="Depth",
        description="Depth of Wedge",
        default=2.00, min=0.01, max=100.00)

    def execute(self, context):

        verts_loc, faces = add_wedge(self.properties.wedge_width, self.properties.wedge_height, self.properties.wedge_depth)

        mesh = bpy.data.meshes.new("Wedge")

        mesh.add_geometry(int(len(verts_loc) / 3), 0, int(len(faces) / 4))
        mesh.verts.foreach_set("co", verts_loc)
        mesh.faces.foreach_set("verts_raw", faces)
        mesh.faces.foreach_set("smooth", [False] * len(mesh.faces))

        scene = context.scene

        # ugh
        for ob in scene.objects:
            ob.selected = False

        mesh.update()
        ob_new = bpy.data.objects.new("Wedge", mesh)
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

menu_func = (lambda self, context: self.layout.operator(AddWedge.bl_idname, text="Add Wedge", icon='PLUGIN'))

def register():
    bpy.types.register(AddWedge)
    bpy.types.INFO_MT_mesh_add.append(menu_func)

def unregister():
    bpy.types.unregister(AddWedge)
    bpy.types.INFO_MT_mesh_add.remove(menu_func)

# Remove "Wedge" menu from the "Add Mesh" menu.
#space_info.INFO_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
    register()
