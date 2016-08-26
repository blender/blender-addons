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

# <pep8 compliant>

bl_info = {
    "name": "Hotkey: 'Tab'",
    "description": "Switch between 3d view object/edit modes",
    #    "author": "pitiwazou, meta-androcto",
    #    "version": (0, 1, 0),
    "blender": (2, 77, 0),
    "location": "3D View",
    "warning": "",
    "wiki_url": "",
    "category": "Mode Switch Pie"
    }

import bpy
from bpy.types import (
        Menu,
        Operator,
        )

# Define Class Object Mode


class ClassObject(Operator):
    bl_idname = "class.object"
    bl_label = "Class Object"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Edit/Object Mode Switch"

    def execute(self, context):

        if context.object.mode == "OBJECT":
            bpy.ops.object.mode_set(mode="EDIT")
        else:
            bpy.ops.object.mode_set(mode="OBJECT")
        return {'FINISHED'}

# Define Class Vertex


class ClassVertex(Operator):
    bl_idname = "class.vertex"
    bl_label = "Class Vertex"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Vert Select"

    def execute(self, context):

        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        if bpy.ops.mesh.select_mode != "EDGE, FACE":
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
            return {'FINISHED'}

# Define Class Edge


class ClassEdge(Operator):
    bl_idname = "class.edge"
    bl_label = "Class Edge"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Edge Select"

    def execute(self, context):

        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        if bpy.ops.mesh.select_mode != "VERT, FACE":
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
            return {'FINISHED'}

# Define Class Face


class ClassFace(Operator):
    bl_idname = "class.face"
    bl_label = "Class Face"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Face Select"

    def execute(self, context):

        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
        if bpy.ops.mesh.select_mode != "VERT, EDGE":
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
            return {'FINISHED'}
# Define Class Texture Paint


class ClassTexturePaint(Operator):
    bl_idname = "class.pietexturepaint"
    bl_label = "Class Texture Paint"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Texture Paint"

    def execute(self, context):

        if context.object.mode == "EDIT":
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.paint.texture_paint_toggle()
        else:
            bpy.ops.paint.texture_paint_toggle()
        return {'FINISHED'}

# Define Class Weight Paint


class ClassWeightPaint(Operator):
    bl_idname = "class.pieweightpaint"
    bl_label = "Class Weight Paint"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Weight Paint"

    def execute(self, context):

        if context.object.mode == "EDIT":
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.paint.weight_paint_toggle()
        else:
            bpy.ops.paint.weight_paint_toggle()
        return {'FINISHED'}

# Define Class Vertex Paint


class ClassVertexPaint(Operator):
    bl_idname = "class.pievertexpaint"
    bl_label = "Class Vertex Paint"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Vertex Paint"

    def execute(self, context):

        if context.object.mode == "EDIT":
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.paint.vertex_paint_toggle()
        else:
            bpy.ops.paint.vertex_paint_toggle()
        return {'FINISHED'}

# Define Class Particle Edit


class ClassParticleEdit(Operator):
    bl_idname = "class.pieparticleedit"
    bl_label = "Class Particle Edit"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Particle Edit (must have active particle system)"

    def execute(self, context):

        if context.object.mode == "EDIT":
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.particle.particle_edit_toggle()
        else:
            bpy.ops.particle.particle_edit_toggle()

        return {'FINISHED'}

# Components Selection Mode


class VertsEdges(Operator):
    bl_idname = "verts.edges"
    bl_label = "Verts Edges"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Vert/Edge Select"

    def execute(self, context):
        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            context.tool_settings.mesh_select_mode = (True, True, False)
        if context.object.mode == "EDIT":
            context.tool_settings.mesh_select_mode = (True, True, False)
            return {'FINISHED'}


class EdgesFaces(Operator):
    bl_idname = "edges.faces"
    bl_label = "EdgesFaces"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Edge/Face Select"

    def execute(self, context):
        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            context.tool_settings.mesh_select_mode = (False, True, True)
        if context.object.mode == "EDIT":
            context.tool_settings.mesh_select_mode = (False, True, True)
            return {'FINISHED'}


class VertsFaces(Operator):
    bl_idname = "verts.faces"
    bl_label = "Verts Faces"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Vert/Face Select"

    def execute(self, context):
        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            context.tool_settings.mesh_select_mode = (True, False, True)
        if context.object.mode == "EDIT":
            context.tool_settings.mesh_select_mode = (True, False, True)
            return {'FINISHED'}


class VertsEdgesFaces(Operator):
    bl_idname = "verts.edgesfaces"
    bl_label = "Verts Edges Faces"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Vert/Edge/Face Select"

    def execute(self, context):
        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            context.tool_settings.mesh_select_mode = (True, True, True)
        if context.object.mode == "EDIT":
            context.tool_settings.mesh_select_mode = (True, True, True)
            return {'FINISHED'}

# Pie Edit/Object Others modes - Tab


class PieObjectEditotherModes(Menu):
    bl_idname = "pie.objecteditmodeothermodes"
    bl_label = "Edit Selection Modes"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator("verts.faces", text="Vertex/Faces", icon='LOOPSEL')
        # 6 - RIGHT
        pie.operator("edges.faces", text="Edges/Faces", icon='FACESEL')
        # 2 - BOTTOM
        pie.operator("wm.context_toggle", text="Limit to Visible",
                     icon="ORTHO").data_path = "space_data.use_occlude_geometry"
        # 8 - TOP
        pie.operator("class.edge", text="Edge", icon='EDGESEL')
        # 7 - TOP - LEFT
        pie.operator("class.vertex", text="Vertex", icon='VERTEXSEL')
        # 9 - TOP - RIGHT
        pie.operator("class.face", text="Face", icon='FACESEL')
        # 1 - BOTTOM - LEFT
        pie.operator("verts.edges", text="Vertex/Edges", icon='VERTEXSEL')
        # 3 - BOTTOM - RIGHT
        pie.operator("verts.edgesfaces", text="Vertex/Edges/Faces", icon='OBJECT_DATAMODE')

# Pie Modes Switch- Tab key


class PieObjectEditMode(Menu):
    bl_idname = "pie.objecteditmode"
    bl_label = "Modes Menu (Tab)"

    def draw(self, context):
        layout = self.layout
        ob = context.object

        if ob and ob.type == 'MESH' and ob.mode in {'OBJECT', 'SCULPT', 'VERTEX_PAINT', 'WEIGHT_PAINT', 'TEXTURE_PAINT', 'PARTICLE'}:
            pie = layout.menu_pie()
            # 4 - LEFT
            pie.operator("class.pievertexpaint", text="Vertex Paint", icon='VPAINT_HLT')
            # 6 - RIGHT
            pie.operator("class.pietexturepaint", text="Texture Paint", icon='TPAINT_HLT')
            # 2 - BOTTOM
            pie.operator("class.pieweightpaint", text="Weight Paint", icon='WPAINT_HLT')
            # 8 - TOP
            pie.operator("class.object", text="Edit/Object Toggle", icon='OBJECT_DATAMODE')
            # 7 - TOP - LEFT
            pie.operator("sculpt.sculptmode_toggle", text="Sculpt", icon='SCULPTMODE_HLT')
            # 9 - TOP - RIGHT
            pie.operator("wm.call_menu_pie", text="Edit Modes",
                         icon='EDITMODE_HLT').name = "pie.objecteditmodeothermodes"
            # 1 - BOTTOM - LEFT
            if context.object.particle_systems:
                pie.operator("class.pieparticleedit", text="Particle Edit", icon='PARTICLEMODE')
            # 3 - BOTTOM - RIGHT

        if ob and ob.type == 'MESH' and ob.mode in {'EDIT'}:
            pie = layout.menu_pie()
            # 4 - LEFT
            pie.operator("class.pievertexpaint", text="Vertex Paint", icon='VPAINT_HLT')
            # 6 - RIGHT
            pie.operator("class.pietexturepaint", text="Texture Paint", icon='TPAINT_HLT')
            # 2 - BOTTOM
            pie.operator("class.pieweightpaint", text="Weight Paint", icon='WPAINT_HLT')
            # 8 - TOP
            pie.operator("class.object", text="Edit/Object Toggle", icon='OBJECT_DATAMODE')
            # 7 - TOP - LEFT
            pie.operator("sculpt.sculptmode_toggle", text="Sculpt", icon='SCULPTMODE_HLT')
            # 9 - TOP - RIGHT
            pie.operator("wm.call_menu_pie", text="Edit Modes",
                         icon='TPAINT_HLT').name = "pie.objecteditmodeothermodes"
            # 1 - BOTTOM - LEFT
            if context.object.particle_systems:
                pie.operator("class.pieparticleedit", text="Particle Edit", icon='PARTICLEMODE')
            # 3 - BOTTOM - RIGHT

        if ob and ob.type == 'CURVE':
            pie = layout.menu_pie()
            pie.operator("object.editmode_toggle", text="Edit/Object", icon='OBJECT_DATAMODE')

        if ob and ob.type == 'ARMATURE':
            pie = layout.menu_pie()
            pie.operator("object.editmode_toggle", text="Edit Mode", icon='OBJECT_DATAMODE')
            pie.operator("object.posemode_toggle", text="Pose", icon='POSE_HLT')
            pie.operator("class.object", text="Object Mode", icon='OBJECT_DATAMODE')

        if ob and ob.type == 'FONT':
            pie = layout.menu_pie()
            pie.operator("object.editmode_toggle", text="Edit/Object Toggle", icon='OBJECT_DATAMODE')

        if ob and ob.type == 'SURFACE':
            pie = layout.menu_pie()
            pie.operator("object.editmode_toggle", text="Edit/Object Toggle", icon='OBJECT_DATAMODE')

        if ob and ob.type == 'META':
            pie = layout.menu_pie()
            pie.operator("object.editmode_toggle", text="Edit/Object Toggle", icon='OBJECT_DATAMODE')

        if ob and ob.type == 'LATTICE':
            pie = layout.menu_pie()
            pie.operator("object.editmode_toggle", text="Edit/Object Toggle", icon='OBJECT_DATAMODE')

classes = (
    PieObjectEditMode,
    ClassObject,
    ClassVertex,
    ClassEdge,
    ClassFace,
    PieObjectEditotherModes,
    ClassTexturePaint,
    ClassWeightPaint,
    ClassVertexPaint,
    ClassParticleEdit,
    VertsEdges,
    EdgesFaces,
    VertsFaces,
    VertsEdgesFaces
    )

addon_keymaps = []


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    wm = bpy.context.window_manager

    if wm.keyconfigs.addon:
        # Select Mode
        km = wm.keyconfigs.addon.keymaps.new(name='Object Non-modal')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'TAB', 'PRESS')
        kmi.properties.name = "pie.objecteditmode"
#        kmi.active = True
        addon_keymaps.append((km, kmi))


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    wm = bpy.context.window_manager

    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps['Object Non-modal']
        for kmi in km.keymap_items:
            if kmi.idname == 'wm.call_menu_pie':
                if kmi.properties.name == "pie.objecteditmode":
                    km.keymap_items.remove(kmi)

if __name__ == "__main__":
    register()
