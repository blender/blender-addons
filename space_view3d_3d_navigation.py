# 3D NAVIGATION TOOLBAR v1.2 - 3Dview Addon - Blender 2.5x
#
# THIS SCRIPT IS LICENSED UNDER GPL, 
# please read the license block.
#
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
#  Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_addon_info = {
    "name": "3D Navigation",
    "author": "Demohero, uriel",
    "version": (1, 2),
    "blender": (2, 5, 4),
    "api": 32411,
    "location": "View3D > Toolbar",
    "description": "Navigate the Camera & 3d Views",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"\
        "Scripts/3D_interaction/3D_Navigation",
    "tracker_url": "http://projects.blender.org/tracker/index.php?"\
	    "func=detail&aid=23530",
    "category": "3D View"}

# import the basic library
import bpy

# main class of this toolbar
class VIEW3D_PT_3dnavigationPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label = "3D Views "

    def draw(self, context):
        layout = self.layout
        view = context.space_data

# Triple boutons        
        col = layout.column(align=True)
        row = col.row()
        row.operator("view3d.viewnumpad", text="View Camera", icon='CAMERA_DATA').type='CAMERA'
        row = col.row()
        row.operator("view3d.localview", text="View Global/Local")
        row = col.row()
        row.operator("view3d.view_persportho", text="View Persp/Ortho")  

# group of 6 buttons
        col = layout.column(align=True)
        col.label(text="Align view from:")
        row = col.row()
        row.operator("view3d.viewnumpad", text="Front").type='FRONT'
        row.operator("view3d.viewnumpad", text="Back").type='BACK'
        row = col.row()
        row.operator("view3d.viewnumpad", text="Left").type='LEFT'
        row.operator("view3d.viewnumpad", text="Right").type='RIGHT'
        row = col.row()
        row.operator("view3d.viewnumpad", text="Top").type='TOP'
        row.operator("view3d.viewnumpad", text="Bottom").type='BOTTOM'
        row = col.row()

# group of 2 buttons
        col = layout.column(align=True)
        col.label(text="View to Object:")
        col.prop(view, "lock_object", text="")
        row = col.row()
        row.operator("view3d.view_selected", text="View to Selected") 
        col = layout.column(align=True)
        col.label(text="Cursor:")
        row = col.row()
        row.operator("view3d.snap_cursor_to_center", text="Center")
        row.operator("view3d.view_center_cursor", text="View")
        row = col.row()
        row.operator("view3d.snap_cursor_to_selected", text="Cursor to Selected")

# register the class
def register(): 
    pass 

def unregister(): 
    pass 

if __name__ == "__main__": 
    register()
