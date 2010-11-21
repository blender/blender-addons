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

#-------------------------------------------------------------------------
# WARNING: Currently adding new CVs to an already animated curve isn't safe
# Thanks to Campbell Barton for hes API additions and fixes
# Daniel Salazar - ZanQdo
#-------------------------------------------------------------------------

bl_addon_info = {
    'name': 'RotoBezier',
    'author': 'Daniel Salazar <zanqdo@gmail.com>',
    'version': (0,1),
    'blender': (2, 5, 5),
    'api': 33198,
    'location': 'Select a Curve > Properties > Curve > RotoBezier',
    'description': 'Allows animation of bezier curves for rotoscoping',
    'warning': '', 
    'wiki_url': 'http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/Animation/RotoBezier',
    'tracker_url': '',
    'category': 'Animation'}


import bpy

#
# GUI (Panel)
#
class OBJECT_PT_rotobezier(bpy.types.Panel):

    bl_label = "RotoBezier"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"

    # show this add-on only in the Camera-Data-Panel
    @classmethod
    def poll(self, context):
        return context.active_object.type  == 'CURVE'

    # draw the gui
    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator('curve.insert_keyframe_rotobezier')
        row.operator('curve.delete_keyframe_rotobezier')


class CURVE_OT_insert_keyframe_rotobezier(bpy.types.Operator):
    bl_label = 'Insert Keyframe'
    bl_idname = 'curve.insert_keyframe_rotobezier'
    bl_description = 'Insert a RotoBezier Keyframe'
    bl_options = {'REGISTER', 'UNDO'}

    # on mouse up:
    def invoke(self, context, event):

        self.insert_keyframe(context)

        return {'FINISHED'}


    def insert_keyframe(op, context):
        
        import bpy

        Obj = bpy.context.active_object

        if Obj.type == 'CURVE':
            Mode = False
            if bpy.context.mode != 'OBJECT':
                Mode = not Mode
                bpy.ops.object.editmode_toggle()
            Data = Obj.data
            
            for Splines in Data.splines:
                for CVs in Splines.bezier_points:
                    CVs.keyframe_insert('co')
                    CVs.keyframe_insert('handle_left')
                    CVs.keyframe_insert('handle_right')
            
            if Mode:
                bpy.ops.object.editmode_toggle()


        return {'FINISHED'} 


class CURVE_OT_delete_keyframe_rotobezier(bpy.types.Operator):
    bl_label = 'Delete Keyframe'
    bl_idname = 'curve.delete_keyframe_rotobezier'
    bl_description = 'Delete a RotoBezier Keyframe'

    # on mouse up:
    def invoke(self, context, event):

        self.delete_keyframe(context)

        return {'FINISHED'}


    def delete_keyframe(op, context):
        
        import bpy

        Obj = bpy.context.active_object

        if Obj.type == 'CURVE':
            Mode = False
            if bpy.context.mode != 'OBJECT':
                Mode = not Mode
                bpy.ops.object.editmode_toggle()
            Data = Obj.data
            
            for Splines in Data.splines:
                for CVs in Splines.bezier_points:
                    CVs.keyframe_delete('co')
                    CVs.keyframe_delete('handle_left')
                    CVs.keyframe_delete('handle_right')
            
            if Mode:
                bpy.ops.object.editmode_toggle()


        return {'FINISHED'} 



def register():
    pass
    
def unregister():
    pass
    
if __name__ == "__main__":
    register()
