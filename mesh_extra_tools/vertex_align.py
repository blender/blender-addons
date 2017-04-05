# -*- coding: utf-8 -*-

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
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

# ------ ------
bl_info = {
    'name': 'vertex align',
    'author': '',
    'version': (0, 1, 6),
    'blender': (2, 6, 1),
    'location': 'View3D > Tool Shelf',
    'description': '',
    'warning': '',
    'wiki_url': '',
    'tracker_url': '',
    'category': 'Mesh' }

# ------ ------
import bpy
from bpy.props import (
        BoolProperty,
        EnumProperty,
        PointerProperty,
        FloatProperty,
        )

from mathutils import Vector
from mathutils.geometry import (
        intersect_point_line,
        intersect_line_plane,
        )
from bpy.types import (
        PropertyGroup,
        )

# ------ Edit Mode Toggle------
def edit_mode_out():
    bpy.ops.object.mode_set(mode = 'OBJECT')

def edit_mode_in():
    bpy.ops.object.mode_set(mode = 'EDIT')

# ------ ------
def get_mesh_data_():
    edit_mode_out()
    ob_act = bpy.context.active_object
    me = ob_act.data
    edit_mode_in()
    return me

def list_clear_(l):
    l[:] = []
    return l

# -- -- Prpoerty Group-- --
class va_property_group(PropertyGroup):

    en0 = EnumProperty( items =( ('vertex', 'Original vertex', ''),
                                 ('coordinates', 'Custom coordinates', '')),

                        name = 'Align to',
                        default = 'vertex' )

    en1 = EnumProperty( items =( ('en1_opt0', 'x', ''),
                                 ('en1_opt1', 'y', ''),
                                 ('en1_opt2', 'z', '')),
                        name = 'Axis',
                        default = 'en1_opt0' )

# ------ ------
class va_buf():
    list_v = []
    list_f = []
    list_0 = []

# ------ operator 0 Store The Vert------
class va_op0_store(bpy.types.Operator):
    bl_idname = 'va.op0_store_id'
    bl_label = ''
    bl_description = "Store single vert as align point"

    def execute(self, context):
        me = get_mesh_data_()
        list_clear_(va_buf.list_v)
        for v in me.vertices:
            if v.select:
                va_buf.list_v.append(v.index)
                bpy.ops.mesh.select_all(action = 'DESELECT')
        return {'FINISHED'}

# ------ operator 1 Append to list------
class va_op1_list(bpy.types.Operator):
    bl_idname = 'va.op1_id'
    bl_label = ''
    bl_description = "test2"

    def execute(self, context):
        me = get_mesh_data_()
        list_clear_(va_buf.list_f)
        for f in me.faces:
            if f.select:
                va_buf.list_f.append(f.index)
                bpy.ops.mesh.select_all(action = 'DESELECT')
        return {'FINISHED'}

# ------ operator 2 ------ align to original
class va_op2_align(bpy.types.Operator):
    bl_idname = 'va.op2_align_id'
    bl_label = 'Align to original'
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Align selection to stored single vert"


    def draw(self, context):
        layout = self.layout
        layout.label('Axis:')
        layout.prop(context.scene.va_custom_props, 'en1', expand = True)

    def execute(self, context):

        edit_mode_out()
        ob_act = context.active_object
        me = ob_act.data
        cen1 = context.scene.va_custom_props.en1
        list_0 = [v.index for v in me.vertices if v.select]

        if len(va_buf.list_v) == 0:
            self.report({'INFO'}, 'Original vertex not stored in memory')
            edit_mode_in()
            return {'CANCELLED'}
        elif len(va_buf.list_v) != 0:
            if len(list_0) == 0:
                self.report({'INFO'}, 'No vertices selected')
                edit_mode_in()
                return {'CANCELLED'}
            elif len(list_0) != 0:
                vo = (me.vertices[va_buf.list_v[0]].co).copy()
                if cen1 == 'en1_opt0':
                    for i in list_0:
                        v = (me.vertices[i].co).copy()
                        me.vertices[i].co = Vector(( vo[0], v[1], v[2] ))
                elif cen1 == 'en1_opt1':
                    for i in list_0:
                        v = (me.vertices[i].co).copy()
                        me.vertices[i].co = Vector(( v[0], vo[1], v[2] ))
                elif cen1 == 'en1_opt2':
                    for i in list_0:
                        v = (me.vertices[i].co).copy()
                        me.vertices[i].co = Vector(( v[0], v[1], vo[2] ))
        edit_mode_in()
        return {'FINISHED'}

# ------ operator 3 ------ align to custom coordinates
class va_op3_coord_list(bpy.types.Operator):
    bl_idname = 'va.op3_coord_list_id'
    bl_label = ''
    bl_description = "Align to custom coordinates"

    def execute(self, context):
        edit_mode_out()
        ob_act = context.active_object
        me = ob_act.data
        list_clear_(va_buf.list_0)
        va_buf.list_0 = [v.index for v in me.vertices if v.select][:]
        if len(va_buf.list_0) == 0:
            self.report({'INFO'}, 'No vertices selected')
            edit_mode_in()
            return {'CANCELLED'}
        elif len(va_buf.list_0) != 0:
            bpy.ops.va.op4_id('INVOKE_DEFAULT')
        edit_mode_in()
        return {'FINISHED'}

# ------ operator 4 ------ align to custom coordinates menu
class va_op4_coord_menu(bpy.types.Operator):
    bl_idname = 'va.op4_id'
    bl_label = 'Align to custom coordinates'
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Align to custom coordinates2"

    x = y = z = FloatProperty( name = '',
                               default = 0.0,
                               min = -100.0,
                               max = 100.0,
                               step = 1,
                               precision = 3 )
    b_x = b_y = b_z = BoolProperty()

    def draw(self, context):
        layout = self.layout
        row = layout.split(0.25)
        row.prop(self, 'b_x', text = 'x')
        row.prop(self, 'x')
        row = layout.split(0.25)
        row.prop(self, 'b_y', text = 'y')
        row.prop(self, 'y')
        row = layout.split(0.25)
        row.prop(self, 'b_z', text = 'z')
        row.prop(self, 'z')

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width = 200)

    def execute(self, context):
        edit_mode_out()
        ob_act = context.active_object
        me = ob_act.data

        for i in va_buf.list_0:
            v = (me.vertices[i].co).copy()
            tmp = Vector((v[0], v[1], v[2]))
            if self.b_x == True:
                tmp[0] = self.x
            if self.b_y == True:
                tmp[1] = self.y
            if self.b_z == True:
                tmp[2] = self.z
            me.vertices[i].co = tmp
        edit_mode_in()
        return {'FINISHED'}

# ------ operator 7 Help------
class va_op7_help(bpy.types.Operator):

    bl_idname = 'va.op7_help_id'
    bl_label = ''
    bl_description = "Info"

    def draw(self, context):
        layout = self.layout
        layout.label('Help:')
        layout.label('To use select whatever you want vertices to be aligned to ')
        layout.label('and click button next to store data label. ')
        layout.label('Select vertices that you want to align and click Align button. ')

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width = 400)

# ------ operator 8 ------
class va_op8_execute(bpy.types.Operator):
    bl_idname = 'va.op8_id'
    bl_label = ''
    bl_description = "Executs"
    def execute(self, context):
        bpy.ops.va.op7_id('INVOKE_DEFAULT')
        return {'FINISHED'}

# ------ Classes ------

classes = (
    va_property_group,
    va_op0_store,
    va_op1_list,
    va_op2_align,
    va_op3_coord_list,
    va_op4_coord_menu,
    va_op7_help,
    va_op8_execute,
    )
# ------ Register ------
def register():
    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.Scene.va_custom_props = PointerProperty(type = va_property_group)

# ------ ------
def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

    del bpy.context.scene['va_custom_props']

# ------ ------
if __name__ == "__main__":
    register()
