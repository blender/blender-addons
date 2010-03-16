# add_mesh_gem.py Copyright (C) 2010, Dreampainter
#
# add gem to the blender 2.50 add->mesh menu
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
    'name': 'Add Mesh: Gem',
    'author': 'Dreampainter',
    'version': '1.0.1',
    'blender': '2.5.3',
    'location': 'View3D > Add > Mesh ',
    'url': 'http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/Add_Gem',
    'category': 'Add Mesh'}

"""
Name: 'Gem'
Blender: 250.1
Group: 'AddMesh'
Tip: 'Add Gem Object...'
__author__ = ["Dreampainter"]
__version__ = '1.0.1'
__url__ = ["http://blenderartists.org/forum/showpost.php?p=1564840&postcount=173"]
email__=["n/a"]


Usage:

* Launch from Add Mesh menu

* Modify parameters as desired or keep defaults

"""

import bpy
import Mathutils
from math import cos,sin,pi
from bpy.props import IntProperty, FloatProperty, BoolProperty
def add_gem(r1, r2, seg, h1, h2):
    """
    r1 = pavillion radius
    r2 = crown radius
    seg = number of segments
    h1 = pavillion height
    h2 = crown height
    Generates the vertices and faces of the gem
    """
    
    tot_verts = 2 + 4 * seg
    tot_faces = 6 * seg
    a = 2*pi/seg                   # angle between segments
    offset = a/2.0                 # middle between segments
    
    r3 = ((r1+r2)/2.0)/cos(offset) # middle of crown
    r4 = (r1/2.0)/cos(offset)      # middle of pavillion
    h3 = h2/2.0                    # middle of crown height
    h4 = -h1/2.0                   # middle of pavillion height
    verts = [0,0,-h1,0,0,h2]
    for i in range(seg):
        s1 = sin(i*a)
        s2 = sin(offset+i*a)
        c1 = cos(i*a)
        c2 = cos(offset+i*a)
        verts.extend([ r4*s1,r4*c1,h4,r1*s2,r1*c2,0, 
                       r3*s1,r3*c1,h3,r2*s2,r2*c2,h2 ])  
    faces = []
    
    for index in range(seg):
        i = index*4
        j = ((index+1)%seg)*4
        faces.extend([0,   j+2, i+3, i+2])
        faces.extend([i+3, j+2, j+3, i+3])
        faces.extend([i+3, j+3, j+4, i+3])
        faces.extend([i+3, j+4, i+5, i+4])
        faces.extend([i+5, j+4, j+5, i+5])
        faces.extend([i+5, j+5, 1  , i+5])
    return verts, faces, tot_verts, tot_faces
       
class Parameter_Panel_Gem(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"
    bl_label = "Gem parameters"
    def poll(self, context):
        # only show this panel if the object selected has propertie "Gem"
        try:
            return "Gem" in context.object
        except TypeError: return False
    def draw(self,context):
        layout = self.layout
        layout.operator("Gem_Parameter_Edit", text="Edit")
class EditGem(bpy.types.Operator):
    """Reapply the operator"""
    bl_idname = "Gem_Parameter_Edit"
    bl_label = "Edit Gem"
    def invoke(self,context,event):
        # invoke the adding operator again,
        #  only this time with the Edit property = true
        ob = context.active_object    
        bpy.ops.mesh.primitive_gem_add(Edit = True, 
                   segments=ob["Segments"],
                   pav_radius = ob["pav_radius"],
                   crown_radius = ob["tab_radius"],
                   crown_height = ob["tab_height"],
                   pav_height = ob["pav_height"])
        return {'FINISHED'}
class AddGem(bpy.types.Operator):
    """Add a diamond gem"""
    bl_idname = "mesh.primitive_gem_add"
    bl_label = "Add Gem"
    bl_description = "Create an offset faceted gem."
    bl_options = {'REGISTER', 'UNDO'}
    Edit = BoolProperty(name = "", description = "", 
           default = False, options = {'HIDDEN'})   # whether to add or update
    segments = IntProperty(name = "Segments", 
           description="Longitudial segmentation", 
           default=8, min=3, max=265)
    pav_radius = FloatProperty(name = "Radius",
           description="Radius of the gem",
           default = 1.0, min = 0.01, max = 100.0)
    crown_radius = FloatProperty(name = "Table Radius",
           description = "Radius of the table(top).",
           default = 0.6, min = 0.01, max = 100.0)
    crown_height = FloatProperty(name = "Table height",
           description = "Height of the top half.",
           default = 0.35, min = 0.01, max = 100.0)
    pav_height = FloatProperty(name = "Pavillion height",
           description = "Height of bottom half.",
           default = 0.8, min = 0.01, max = 100.0)
        
    def execute(self, context):
        # create mesh
        verts, faces, nV, nF = add_gem(self.properties.pav_radius,
               self.properties.crown_radius,
               self.properties.segments,
               self.properties.pav_height,
               self.properties.crown_height)
    
        mesh = bpy.data.meshes.new("Gem")
        mesh.add_geometry(nV,0,nF)
        mesh.verts.foreach_set("co",verts)
        mesh.faces.foreach_set("verts_raw",faces)
        mesh.update()
        if self.properties.Edit:
            # only update
            ob_new = context.active_object
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.delete(type = 'VERT')
            bpy.ops.object.mode_set(mode='OBJECT')
            
            ob_new.data = mesh
            
            scene = context.scene
    
            # ugh
            for ob in scene.objects:
                ob.selected = False
            
            ob_new.selected = True
            scene.objects.active = ob_new
            bpy.ops.object.shade_flat()
        else:
            # create new object
            scene = context.scene
    
            # ugh
            for ob in scene.objects:
                ob.selected = False
    
            ob_new = bpy.data.objects.new("Gem", mesh)
            ob_new.data = mesh
            scene.objects.link(ob_new)
            ob_new.selected = True
    
            ob_new.location = scene.cursor_location
    
            obj_act = scene.objects.active
    
            if obj_act and obj_act.mode == 'EDIT':
                # if the mesh is added in edit mode, add the mesh to the
                #  excisting mesh
                bpy.ops.object.mode_set(mode='OBJECT')
    
                obj_act.selected = True
                scene.update() # apply location
    
                bpy.ops.object.join() # join into the active.
    
                bpy.ops.object.mode_set(mode='EDIT')
            else:
                # add new object and make faces flat
                scene.objects.active = ob_new
                bpy.ops.object.shade_flat()
                if context.user_preferences.edit.enter_edit_mode:
                    bpy.ops.object.mode_set(mode='EDIT')
        # add custom properties to the object to make the edit parameters
        #  thingy work
        ob_new["Gem"] = 1
        ob_new["Segments"] = self.properties.segments
        ob_new["pav_radius"] = self.properties.pav_radius 
        ob_new["tab_radius"] = self.properties.crown_radius
        ob_new["pav_height"] = self.properties.pav_height
        ob_new["tab_height"] = self.properties.crown_height
        return {'FINISHED'}

# register all operators and panels


menu_func = (lambda self, context: self.layout.operator(AddGem.bl_idname,
                                        text="Gem", icon='PLUGIN'))

def register():
    bpy.types.register(AddGem)
    bpy.types.register(Parameter_Panel_Gem)
    bpy.types.register(EditGem)
    bpy.types.INFO_MT_mesh_add.append(menu_func)

def unregister():
    bpy.types.unregister(AddGem)
    bpy.types.unregister(Parameter_Panel_Gem)
    bpy.types.unregister(EditGem)
    bpy.types.INFO_MT_mesh_add.remove(menu_func)
    # Remove "Gem" menu from the "Add Mesh" menu.
    #space_info.INFO_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
    register()

