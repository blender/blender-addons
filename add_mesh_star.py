# add_mesh_star.py Copyright (C) 2008-2009, FourMadMen.com
#
# add star to the blender 2.50 add->mesh menu
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****

bl_addon_info = {
    'name': 'Add Mesh: Star',
    'author': 'fourmadmen',
    'version': '2.0',
    'blender': (2, 5, 3),
    'location': 'View3D > Add > Mesh ',
    'description': 'Adds a mesh Star to the Add Mesh menu',
    'url': 'http://wiki.blender.org/index.php/Extensions:2.5/Py/' \
	    'Scripts/Add_Mesh/Add_Star',
    'category': 'Add Mesh'}


import bpy
import mathutils


def add_star(points, outer_radius, inner_radius, depth):
    from mathutils import Vector, Quaternion
    from math import pi

    PI_2 = pi * 2
    z_axis = (0, 0, 1)

    verts = []
    faces = []

    segments = points * 2
    tot_verts = segments * 2 + 2

    half_height = depth * 0.5

    verts.extend(Vector(0.0, 0.0, -half_height))
    verts.extend(Vector(0.0, 0.0, half_height))

    i = 2
    alt_idx = 0
    for index in range(segments):
        quat = Quaternion(z_axis, (index / segments) * PI_2)

        radius = alt_idx and inner_radius or outer_radius

        vec = Vector(radius, 0, -half_height) * quat
        verts.extend([vec.x, vec.y, vec.z])
        it1 = i
        i += 1

        vec = Vector(radius, 0, half_height) * quat
        verts.extend([vec.x, vec.y, vec.z])
        ib1 = i
        i += 1

        if i > 4:
            faces.extend([0, it1 - 2, it1, 0])
            faces.extend([it1, it1 - 2, ib1 - 2, ib1])
            faces.extend([1, ib1, ib1 - 2, 1])

        alt_idx = 1 - alt_idx

    faces.extend([0, it1, 2, 0])
    faces.extend([2, it1, ib1, 3])
    faces.extend([1, 3, ib1, 1])

    return verts, faces

from bpy.props import IntProperty, FloatProperty


class AddStar(bpy.types.Operator):
    '''Add a star mesh.'''
    bl_idname = "mesh.primitive_star_add"
    bl_label = "Add Star"
    bl_options = {'REGISTER', 'UNDO'}

    points = IntProperty(name="Points",
        description="Number of points for the star",
        default=5, min=2, max=256)
    outer_radius = FloatProperty(name="Outer Radius",
        description="Outer radius of the star",
        default=1.0, min=0.01, max=100.0)
    innter_radius = FloatProperty(name="Inner Radius",
        description="Inner radius of the star",
        default=0.5, min=0.01, max=100.0)
    depth = FloatProperty(name="Depth",
        description="Depth of the star",
        default=0.5, min=0.01, max=100.0)

    def execute(self, context):
        verts_loc, faces = add_star(self.properties.points,
            self.properties.outer_radius,
            self.properties.innter_radius,
            self.properties.depth)

        mesh = bpy.data.meshes.new("Star")

        mesh.add_geometry(int(len(verts_loc) / 3), 0, int(len(faces) / 4))
        mesh.verts.foreach_set("co", verts_loc)
        mesh.faces.foreach_set("verts_raw", faces)

        scene = context.scene

        # ugh
        for ob in scene.objects:
            ob.selected = False

        mesh.update()

        ob_new = bpy.data.objects.new("Star", mesh)
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

menu_func = (lambda self, context: self.layout.operator(AddStar.bl_idname,
                                        text="Star", icon='PLUGIN'))


def register():
    bpy.types.register(AddStar)
    bpy.types.INFO_MT_mesh_add.append(menu_func)


def unregister():
    bpy.types.unregister(AddStar)
    bpy.types.INFO_MT_mesh_add.remove(menu_func)

    # Remove "Star" menu from the "Add Mesh" menu.
    #space_info.INFO_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
    register()
