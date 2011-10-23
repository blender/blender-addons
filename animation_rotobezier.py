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
    'name': 'RotoBezier',
    'author': 'Daniel Salazar <zanqdo@gmail.com>',
    'version': (0, 8),
    "blender": (2, 5, 7),
    "api": 35622,
    'location': 'Select a Curve: Tool Shelf > RotoBezier Panel',
    'description': 'Allows animation of Bezier and NURBS curves',
    'warning': '',
    'wiki_url': 'http://wiki.blender.org/index.php/Extensions:2.5/Py/'\
        'Scripts/Animation/RotoBezier',
    'tracker_url': 'http://projects.blender.org/tracker/index.php?'\
        'func=detail&aid=24839',
    'category': 'Animation'}

'''
-------------------------------------------------------------------------
Thanks to Campbell Barton for his API additions and fixes
Daniel Salazar - ZanQdo

Rev 0.1 Initial release
Rev 0.2 New make matte object tools and convenient display toggles
Rev 0.3 Tool to clear all animation from the curve
Rev 0.4 Moved from curve properties to toolbar
Rev 0.5 Added pass index property
Rev 0.6 Re-arranged UI
Rev 0.7 Adding options for what properties to keyframe
Rev 0.8 Allowing to key NURBS
-------------------------------------------------------------------------
'''

import bpy
from bpy.props import *


#
# Property Definitions
#
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
class VIEW3D_PT_rotobezier(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = 'RotoBezier'

    # show this addon only in the Camera-Data-Panel
    @classmethod
    def poll(self, context):
        if context.active_object:
            return context.active_object.type  == 'CURVE'
    
    # draw the gui
    def draw(self, context):
        layout = self.layout
        
        ob = context.active_object
        
        col = layout.column(align=True)
        col.label(text="Keyframing:")
        row = col.row()
        row.prop(context.window_manager, "key_points")
        row.prop(context.window_manager, "key_radius")
        row.prop(context.window_manager, "key_tilt")
        
        row = col.row()
        row.operator('curve.insert_keyframe_rotobezier', icon='KEY_HLT')
        row.operator('curve.delete_keyframe_rotobezier', icon='KEY_DEHLT')

        layout.operator('curve.clear_animation_rotobezier', icon='X')
        
        col = layout.column()
        col.label(text="Display:")
        col.operator('curve.toggle_draw_rotobezier', icon='MESH_CIRCLE')
        
        if context.mode == 'EDIT_CURVE':
            col.operator('curve.toggle_handles_rotobezier', icon='CURVE_BEZCIRCLE')
        
        col = layout.column(align=True)
        
        col.label(text="Tools:")
        row = col.row()
        row.operator('curve.make_white_matte_rotobezier')
        row.operator('curve.make_black_matte_rotobezier')
        
        layout.prop(ob, "pass_index")


class CURVE_OT_insert_keyframe_rotobezier(bpy.types.Operator):
    bl_label = 'Insert'
    bl_idname = 'curve.insert_keyframe_rotobezier'
    bl_description = 'Insert/Replace all Keyframes in current frame'
    bl_options = {'REGISTER', 'UNDO'}
    
    # on mouse up:
    def invoke(self, context, event):
        self.execute(context)
        return {'FINISHED'}
    
    @classmethod
    def poll(cls, context):
        return (context.active_object.type == 'CURVE')
    
    def execute(op, context):
        
        Obj = context.active_object
        
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


class CURVE_OT_delete_keyframe_rotobezier(bpy.types.Operator):
    bl_label = 'Delete'
    bl_idname = 'curve.delete_keyframe_rotobezier'
    bl_description = 'Delete all keyframes in current frame'
    bl_options = {'REGISTER', 'UNDO'}
    
    # on mouse up:
    def invoke(self, context, event):
        self.execute(context)
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return (context.active_object.type == 'CURVE')

    def execute(op, context):
        
        Obj = context.active_object

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


class CURVE_OT_clear_animation_rotobezier(bpy.types.Operator):
    bl_label = 'Clear Animation'
    bl_idname = 'curve.clear_animation_rotobezier'
    bl_description = 'Clear all animation from the curve'
    bl_options = {'REGISTER', 'UNDO'}

    # on mouse up:
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_confirm(self, event)
    
    def execute(op, context):
        Data = context.active_object.data
        Data.animation_data_clear()
        return {'FINISHED'}


def MakeMatte (Type):
    '''
    Matte Material Assignment Function
    '''
    
    Obj = bpy.context.active_object
    
    # Material
    
    if Type == 'White':
        MatName = 'RotoBezier_WhiteMatte'
        MatCol = (1,1,1)

    elif Type == 'Black':
        MatName = 'RotoBezier_BlackMatte'
        MatCol = (0,0,0)

    if bpy.data.materials.get(MatName):
        Mat = bpy.data.materials[MatName]
        if not Obj.material_slots:
            bpy.ops.object.material_slot_add()
        Obj.material_slots[0].material = Mat
    
    else:
        Mat = bpy.data.materials.new(MatName)
        Mat.diffuse_color = MatCol
        Mat.use_shadeless = True
        Mat.use_raytrace = False
        Mat.use_shadows = False
        Mat.use_cast_buffer_shadows = False
        Mat.use_cast_approximate = False
        
        if not Obj.material_slots:
            bpy.ops.object.material_slot_add()
            
        Obj.material_slots[0].material = Mat
    
    # Settings
    Curve = Obj.data
    
    Curve.dimensions = '2D'
    Curve.fill_mode = 'NONE'


class CURVE_OT_make_white_matte_rotobezier(bpy.types.Operator):
    bl_label = 'White Matte'
    bl_idname = 'curve.make_white_matte_rotobezier'
    bl_description = 'Make this curve a white matte'
    bl_options = {'REGISTER', 'UNDO'}

    # on mouse up:
    def invoke(self, context, event):
        self.execute(context)
        return {'FINISHED'}

    def execute(op, context):
        MakeMatte('White')
        return {'FINISHED'}


class CURVE_OT_make_black_matte_rotobezier(bpy.types.Operator):
    bl_label = 'Black Matte'
    bl_idname = 'curve.make_black_matte_rotobezier'
    bl_description = 'Make this curve a black matte'
    bl_options = {'REGISTER', 'UNDO'}

    # on mouse up:
    def invoke(self, context, event):
        self.execute(context)
        return {'FINISHED'}

    def execute(op, context):
        MakeMatte('Black')
        return {'FINISHED'}


class CURVE_OT_toggle_handles_rotobezier(bpy.types.Operator):
    bl_label = 'Handles'
    bl_idname = 'curve.toggle_handles_rotobezier'
    bl_description = 'Toggle the curve handles display in edit mode'
    bl_options = {'REGISTER', 'UNDO'}

    # on mouse up:
    def invoke(self, context, event):
        self.execute(context)
        return {'FINISHED'}
    
    def execute(op, context):
        Obj = context.active_object
        Curve = Obj.data
        if Curve.show_handles:
            Curve.show_handles = False
        else:
            Curve.show_handles = True
        return {'FINISHED'}


class CURVE_OT_toggle_draw_rotobezier(bpy.types.Operator):
    bl_label = 'Filling'
    bl_idname = 'curve.toggle_draw_rotobezier'
    bl_description = 'Toggle the curve display mode between Wire and Solid'
    bl_options = {'REGISTER', 'UNDO'}

    # on mouse up:
    def invoke(self, context, event):
        self.execute(context)
        return {'FINISHED'}
    
    def execute(op, context):
        Obj = context.active_object
        
        if Obj.draw_type == 'SOLID':
            Obj.draw_type = 'WIRE'
            
        elif Obj.draw_type == 'WIRE':
            Obj.draw_type = 'SOLID'
            
        else:
            Obj.draw_type = 'WIRE'
        
        return {'FINISHED'}


def register():
    bpy.utils.register_module(__name__)

    pass
    
def unregister():
    bpy.utils.unregister_module(__name__)

    pass
    
if __name__ == "__main__":
    register()
