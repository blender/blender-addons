# mesh_relax.py Copyright (C) 2010, Fabian Fricke
#
# Relaxes selected vertices while retaining the shape as much as possible
#
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
    'name': 'Mesh: Relax',
    'author': 'Fabian Fricke',
    'version': '1.0  2010/04/03',
    'blender': (2, 5, 3),
    'location': 'View3D > Specials > Relax ',
    'description': 'Relax the selected verts while retaining the shape',
    'url': 'http://wiki.blender.org/index.php/Extensions:2.5/Py/' \
	    'Scripts/Modeling/Relax',
    'category': 'Mesh'}

"""

Usage:

Launch from "W-menu" or from "Mesh -> Vertices -> Relax"


Additional links:
    Author Site: http://frigi.designdevil.de
    e-mail: frigi.f {at} gmail {dot} com

"""


import bpy
from bpy.props import IntProperty

def relax_mesh(self, context):
    
    # get active object and remember some of its mesh info
    obj = context.active_object
    me_old = obj.data
    me_name = me_old.name

    # deselect everything that's not related
    if bpy.context.selected_objects:
        for o in bpy.context.selected_objects:
            o.selected = False

    # duplicate the object so it can be used for the shrinkwrap modifier
    obj.selected = True # make sure the object is selected!
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.duplicate()
    target = context.active_object
    bpy.context.scene.objects.active = obj
    
    sw = obj.modifiers.new(type='SHRINKWRAP', name='target')
    sw.target = target
    
    # run smooth operator to relax the mesh
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.vertices_smooth()
    bpy.ops.object.mode_set(mode='OBJECT')

    # apply and remove the modifier
    me = obj.create_mesh(context.scene, True, 'PREVIEW')
    obj.data = me
    obj.modifiers.remove(sw)

    # clean up the old mesh and rename the new one
    bpy.data.meshes.remove(me_old)
    obj.data.name = me_name
    
    # delete the target object
    obj.selected = False
    target.selected = True
    bpy.ops.object.delete()
    
    # go back to initial state
    obj.selected = True
    bpy.ops.object.mode_set(mode='EDIT')

class Relax(bpy.types.Operator):
    '''Relaxes selected vertices while retaining the shape as much as possible'''
    bl_idname = 'mesh.relax'
    bl_label = 'Relax'
    bl_options = {'REGISTER', 'UNDO'}

    iterations = IntProperty(name="Relax iterations",
                default=1, min=0, max=10, soft_min=0, soft_max=10)

    def poll(self, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    def execute(self, context):
        for i in range(0,self.properties.iterations):
            relax_mesh(self, context)
        return {'FINISHED'}

menu_func = (lambda self, context: self.layout.operator(Relax.bl_idname, text="Relax"))

def register():
    bpy.types.register(Relax)
    bpy.types.VIEW3D_MT_edit_mesh_specials.append(menu_func)
    bpy.types.VIEW3D_MT_edit_mesh_vertices.append(menu_func)

def unregister():
    bpy.types.unregister(Relax)
    bpy.types.VIEW3D_MT_edit_mesh_specials.remove(menu_func)
    bpy.types.VIEW3D_MT_edit_mesh_vertices.remove(menu_func)

if __name__ == "__main__":
    register()
