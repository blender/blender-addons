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
    'name': 'AnimAll',
    'author': 'Daniel Salazar <zanqdo@gmail.com>',
    'version': (0, 5),
    "blender": (2, 63, 0),
    'location': 'Select a Mesh/Lattice/Curve: Tool Shelf > AnimAll panel',
    'description': 'Allows animation of mesh, lattice and curve data (Shape Keys, VCols, VGroups, UVs, Points, Radius, Tilt)',
    'warning': '',
    'wiki_url': 'http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Animation/AnimAll',
    'tracker_url': 'http://projects.blender.org/tracker/index.php?'\
        'func=detail&aid=24874',
    'category': 'Animation'}

"""-------------------------------------------------------------------------
Thanks to Campbell Barton and Joshua Leung for hes API additions and fixes
Daniel 'ZanQdo' Salazar

Rev 0.1 initial release (animate Mesh points)
Rev 0.2 added support for animating UVs, VCols, VGroups
Rev 0.3 added support for animating Lattice points
Rev 0.4 added support for ShapeKey layer animation, removed support
for direct point animation since this new aproach is much stronger
and inline with the animation system
Rev 0.5 merged curve animation features from rotobezier and ported to new bmesh API
-------------------------------------------------------------------------"""

import bpy
from bpy.props import *


#
# Property Definitions
#
bpy.types.WindowManager.key_shape = BoolProperty(
    name="Shape",
    description="Insert keyframes on active Shape Key layer",
    default=True)

bpy.types.WindowManager.key_uvs = BoolProperty(
    name="UVs",
    description="Insert keyframes on active UV coordinates",
    default=False)

bpy.types.WindowManager.key_vcols = BoolProperty(
    name="VCols",
    description="Insert keyframes on active Vertex Color values",
    default=False)

bpy.types.WindowManager.key_vgroups = BoolProperty(
    name="VGroups",
    description="Insert keyframes on active Vertex Group values",
    default=False)

bpy.types.WindowManager.key_points = BoolProperty(
    name="Points",
    description="Insert keyframes on point locations",
    default=True)

bpy.types.WindowManager.key_radius = BoolProperty(
    name="Radius",
    description="Insert keyframes on point radius (Shrink/Fatten)",
    default=False)

bpy.types.WindowManager.key_tilt = BoolProperty(
    name="Tilt",
    description="Insert keyframes on point tilt",
    default=False)

#
# GUI (Panel)
#
class VIEW3D_PT_animall(bpy.types.Panel):

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = 'AnimAll'
    bl_options = {'DEFAULT_CLOSED'}
    # show this addon only in the Camera-Data-Panel
    @classmethod
    def poll(self, context):
        if context.active_object:
            return context.active_object.type  == 'MESH'\
				or context.active_object.type  == 'LATTICE'\
                or context.active_object.type  == 'CURVE'
    
    # draw the gui
    def draw(self, context):
        
        Obj = context.active_object
        
        layout = self.layout
        col = layout.column(align=True)
        row = col.row()
        
        if Obj.type == 'LATTICE':
            row.prop(context.window_manager, "key_shape")
            
        elif Obj.type == 'MESH':
            row.prop(context.window_manager, "key_shape")
            row.prop(context.window_manager, "key_uvs")
            row = col.row()
            row.prop(context.window_manager, "key_vcols")
            row.prop(context.window_manager, "key_vgroups")
            
        elif Obj.type == 'CURVE':
            row.prop(context.window_manager, "key_points")
            row.prop(context.window_manager, "key_radius")
            row = col.row()
            row.prop(context.window_manager, "key_tilt")
        
        row = col.row()
        row.operator('anim.insert_keyframe_animall', icon='KEY_HLT')
        row.operator('anim.delete_keyframe_animall', icon='KEY_DEHLT')
        row = layout.row()
        row.operator('anim.clear_animation_animall', icon='X')
        
        if Obj.type != 'CURVE' and context.window_manager.key_shape:
            
            ShapeKey = Obj.active_shape_key
            
            split = layout.split()
            row = split.row()
            
            if ShapeKey:
                row.label(ShapeKey.name, icon='SHAPEKEY_DATA')
                row.prop(ShapeKey, "value", text="")
                row.prop(Obj, "show_only_shape_key", text="")
            else:
                row.label('No active ShapeKey', icon='INFO')


class ANIM_OT_insert_keyframe_animall(bpy.types.Operator):
    bl_label = 'Insert'
    bl_idname = 'anim.insert_keyframe_animall'
    bl_description = 'Insert a Keyframe'
    bl_options = {'REGISTER', 'UNDO'}
    
    
    # on mouse up:
    def invoke(self, context, event):
        
        self.execute(context)
        
        return {'FINISHED'}


    def execute(op, context):
        
        Obj = context.active_object
        
        if Obj.type == 'MESH':
            Mode = False
            if context.mode == 'EDIT_MESH':
                Mode = not Mode
                bpy.ops.object.editmode_toggle()
            
            Data = Obj.data
            
            if context.window_manager.key_shape:
                if Obj.active_shape_key:
                    for Point in Obj.active_shape_key.data:
                        Point.keyframe_insert('co')
            
            if context.window_manager.key_vgroups:
                for Vert in Data.vertices:
                    for Group in Vert.groups:
                        Group.keyframe_insert('weight')
                    
            if context.window_manager.key_uvs:
                for UV in Data.uv_layers.active.data:
                    UV.keyframe_insert('uv')

            if context.window_manager.key_vcols:
                for VColLayer in Data.vertex_colors:
                    if VColLayer.active: # only insert in active VCol layer
                        for Data in VColLayer.data:
                            Data.keyframe_insert('color')
            
            if Mode:
                bpy.ops.object.editmode_toggle()
        
        if Obj.type == 'LATTICE':
            Mode = False
            if context.mode != 'OBJECT':
                Mode = not Mode
                bpy.ops.object.editmode_toggle()
            
            if context.window_manager.key_shape:
                if Obj.active_shape_key:
                    for Point in Obj.active_shape_key.data:
                        Point.keyframe_insert('co')
            
            if Mode:
                bpy.ops.object.editmode_toggle()
        
        if Obj.type == 'CURVE':
            Mode = False
            if context.mode != 'OBJECT':
                Mode = not Mode
                bpy.ops.object.editmode_toggle()
            
            Data = Obj.data
            
            for Spline in Data.splines:
                if Spline.type == 'BEZIER':
                    for CV in Spline.bezier_points:
                        if context.window_manager.key_points:
                            CV.keyframe_insert('co')
                            CV.keyframe_insert('handle_left')
                            CV.keyframe_insert('handle_right')
                        if context.window_manager.key_radius:
                            CV.keyframe_insert('radius')
                        if context.window_manager.key_tilt:
                            CV.keyframe_insert('tilt')
                        
                elif Spline.type == 'NURBS':
                    for CV in Spline.points:
                        if context.window_manager.key_points:
                            CV.keyframe_insert('co')
                        if context.window_manager.key_radius:
                            CV.keyframe_insert('radius')
                        if context.window_manager.key_tilt:
                            CV.keyframe_insert('tilt')
                
            if Mode:
                bpy.ops.object.editmode_toggle()


        return {'FINISHED'}


class ANIM_OT_delete_keyframe_animall(bpy.types.Operator):
    bl_label = 'Delete'
    bl_idname = 'anim.delete_keyframe_animall'
    bl_description = 'Delete a Keyframe'
    bl_options = {'REGISTER', 'UNDO'}
    
    
    # on mouse up:
    def invoke(self, context, event):

        self.execute(context)

        return {'FINISHED'}


    def execute(op, context):
        
        Obj = context.active_object
        
        if Obj.type == 'MESH':
            Mode = False
            if context.mode == 'EDIT_MESH':
                Mode = not Mode
                bpy.ops.object.editmode_toggle()
            
            Data = Obj.data
            
            if context.window_manager.key_shape:
                if Obj.active_shape_key:
                    for Point in Obj.active_shape_key.data:
                        Point.keyframe_delete('co')
            
            if context.window_manager.key_vgroups:
                for Vert in Data.vertices:
                    for Group in Vert.groups:
                        Group.keyframe_delete('weight')
            
            if context.window_manager.key_uvs:
                for UV in Data.uv_layers.active.data:
                    UV.keyframe_delete('uv')
            
            if context.window_manager.key_vcols:
                for VColLayer in Data.vertex_colors:
                    if VColLayer.active: # only delete in active VCol layer
                        for Data in VColLayer.data:
                            Data.keyframe_delete('color')
            
            
            if Mode:
                bpy.ops.object.editmode_toggle()

        if Obj.type == 'LATTICE':
            if context.window_manager.key_shape:
                if Obj.active_shape_key:
                    for Point in Obj.active_shape_key.data:
                        Point.keyframe_delete('co')
        
        if Obj.type == 'CURVE':
            Mode = False
            if context.mode != 'OBJECT':
                Mode = not Mode
                bpy.ops.object.editmode_toggle()
            
            Data = Obj.data
            
            for Spline in Data.splines:
                if Spline.type == 'BEZIER':
                    for CV in Spline.bezier_points:
                        if context.window_manager.key_points:
                            CV.keyframe_delete('co')
                            CV.keyframe_delete('handle_left')
                            CV.keyframe_delete('handle_right')
                        if context.window_manager.key_radius:
                            CV.keyframe_delete('radius')
                        if context.window_manager.key_tilt:
                            CV.keyframe_delete('tilt')
                        
                elif Spline.type == 'NURBS':
                    for CV in Spline.points:
                        if context.window_manager.key_points:
                            CV.keyframe_delete('co')
                        if context.window_manager.key_radius:
                            CV.keyframe_delete('radius')
                        if context.window_manager.key_tilt:
                            CV.keyframe_delete('tilt')
                
            if Mode:
                bpy.ops.object.editmode_toggle()


        return {'FINISHED'}


class ANIM_OT_clear_animation_animall(bpy.types.Operator):
    bl_label = 'Clear Animation'
    bl_idname = 'anim.clear_animation_animall'
    bl_description = 'Clear all animation'
    bl_options = {'REGISTER', 'UNDO'}

    # on mouse up:
    def invoke(self, context, event):
        
        wm = context.window_manager
        return wm.invoke_confirm(self, event)
    
    
    def execute(op, context):
        
        Data = context.active_object.data
        Data.animation_data_clear()
        
        return {'FINISHED'}


def register():
    bpy.utils.register_module(__name__)

    pass
    
def unregister():
    bpy.utils.unregister_module(__name__)

    pass
    
if __name__ == "__main__":
    register()
