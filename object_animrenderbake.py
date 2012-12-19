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
    "name": "Animated Render Baker",
    "author": "Janne Karhu (jahka)",
    "version": (1, 0),
    "blender": (2, 58, 0),
    "location": "Properties > Render > Bake Panel",
    "description": "Renderbakes a series of frames",
    "category": "Object",
    'wiki_url': 'http://wiki.blender.org/index.php/Extensions:2.6/Py/' \
        'Scripts/Object/Animated_Render_Baker',
    'tracker_url': 'https://projects.blender.org/tracker/index.php?'\
        'func=detail&aid=24836'}

import bpy
from bpy.props import *

class OBJECT_OT_animrenderbake(bpy.types.Operator):
    bl_label = "Animated Render Bake"
    bl_description= "Bake animated image textures of selected objects"
    bl_idname = "object.anim_bake_image"
    bl_register = True

    def framefile(self, orig, frame):
        """
        Set frame number to file name image.png -> image0013.png
        """
        dot = orig.rfind(".")
        return orig[:dot] + ('%04d' % frame) + orig[dot:]
    
    def invoke(self, context, event):
        import bpy
        import shutil
        
        scene = context.scene
        
        start = scene.animrenderbake_start
        end = scene.animrenderbake_end

        # Check for errors before starting
        if start >= end:
            self.report({'ERROR'}, "Start frame must be smaller than end frame")
            return {'CANCELLED'}
            
        selected = context.selected_objects

        # Only single object baking for now
        if scene.render.use_bake_selected_to_active:
            if len(selected) > 2:
                self.report({'ERROR'}, "Select only two objects for animated baking")
                return {'CANCELLED'}
        elif len(selected) > 1:
            self.report({'ERROR'}, "Select only one object for animated baking")
            return {'CANCELLED'}

        if context.active_object.type != 'MESH':
            self.report({'ERROR'}, "The baked object must be a mesh object")
            return {'CANCELLED'}

        img = None

        #find the image that's used for rendering
        for uvtex in context.active_object.data.uv_textures:
            if uvtex.active_render == True:
                for uvdata in uvtex.data:
                    if uvdata.image != None:
                        img = uvdata.image
                        break

        if img is None:
            self.report({'ERROR'}, "No valid image found to bake to")
            return {'CANCELLED'}

        if img.is_dirty:
            self.report({'ERROR'}, "Save the image that's used for baking before use")
            return {'CANCELLED'}

        # make sure we have an absolute path so that copying works for sure
        absp = bpy.path.abspath(img.filepath, library=img.library)

        print("Animated baking for frames " + str(start) + " - " + str(end))

        for cfra in range(start, end+1):
            print("Baking frame " + str(cfra))

            # update scene to new frame and bake to template image
            scene.frame_set(cfra)
            ret = bpy.ops.object.bake_image()
            if 'CANCELLED' in ret:
                return {'CANCELLED'}

            #currently the api doesn't allow img.save_as(), so just save the template image as usual for every frame and copy to a file with frame specific filename
            img.save()
            shutil.copyfile(absp, self.framefile(absp, cfra))

            print("Saved " + self.framefile(absp, cfra))
        print("Baking done!")

        return{'FINISHED'}

# modified copy of original bake panel draw function
def draw_animrenderbake(self, context):
    layout = self.layout

    rd = context.scene.render

    row = layout.row()
    row.operator("object.bake_image", icon='RENDER_STILL')
    
    #----------- beginning of modifications ----------------
    row.operator("object.anim_bake_image", text="Animated Bake", icon="RENDER_ANIMATION")
    row = layout.row(align=True)
    row.prop(context.scene, "animrenderbake_start")
    row.prop(context.scene, "animrenderbake_end")
    #-------------- end of modifications ---------------------

    layout.prop(rd, "bake_type")

    multires_bake = False
    if rd.bake_type in ['NORMALS', 'DISPLACEMENT']:
        layout.prop(rd, 'use_bake_multires')
        multires_bake = rd.use_bake_multires

    if not multires_bake:
        if rd.bake_type == 'NORMALS':
            layout.prop(rd, "bake_normal_space")
        elif rd.bake_type in {'DISPLACEMENT', 'AO'}:
            layout.prop(rd, "use_bake_normalize")

        # col.prop(rd, "bake_aa_mode")
        # col.prop(rd, "use_bake_antialiasing")

        layout.separator()

        split = layout.split()

        col = split.column()
        col.prop(rd, "use_bake_clear")
        col.prop(rd, "bake_margin")
        col.prop(rd, "bake_quad_split", text="Split")

        col = split.column()
        col.prop(rd, "use_bake_selected_to_active")
        sub = col.column()
        sub.active = rd.use_bake_selected_to_active
        sub.prop(rd, "bake_distance")
        sub.prop(rd, "bake_bias")
    else:
        if rd.bake_type == 'DISPLACEMENT':
            layout.prop(rd, "use_bake_lores_mesh")

        layout.prop(rd, "use_bake_clear")
        layout.prop(rd, "bake_margin")

def register():
    bpy.utils.register_module(__name__)

    bpy.types.Scene.animrenderbake_start = IntProperty(
        name="Start",
        description="Start frame of the animated bake",
        default=1)

    bpy.types.Scene.animrenderbake_end = IntProperty(
        name="End",
        description="End frame of the animated bake",
        default=250)

    # replace original panel draw function with modified one
    panel = bpy.types.RENDER_PT_bake
    panel.old_draw = panel.draw
    panel.draw = draw_animrenderbake

def unregister():
    bpy.utils.unregister_module(__name__)

    # restore original panel draw function
    bpy.types.RENDER_PT_bake.draw = bpy.types.RENDER_PT_bake.old_draw
    del bpy.types.RENDER_PT_bake.old_draw
    del bpy.types.Scene.animrenderbake_start
    del bpy.types.Scene.animrenderbake_end

if __name__ == "__main__":
    register()
