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

import bpy
import time

from .utils import _read_credentials, check_status
from .rpc import rffi
from .exceptions import LoginFailedException

class RenderButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    # COMPAT_ENGINES must be defined in each subclass, external engines can add themselves here

class EngineSelectPanel(RenderButtonsPanel, bpy.types.Panel):
    bl_idname = "OBJECT_PT_engineSelectPanel"
    bl_label = "Choose rendering mode"
    COMPAT_ENGINES = set(['RENDERFARMFI_RENDER'])

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("ore.switch_to_renderfarm_render", text="Renderfarm.fi", icon='WORLD')
        row.operator("ore.switch_to_local_render", text="Local computer", icon='BLENDER')

class LOGIN_PT_RenderfarmFi(RenderButtonsPanel, bpy.types.Panel):
    bl_label = 'Login to Renderfarm.fi'
    COMPAT_ENGINES = set(['RENDERFARMFI_RENDER'])

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return (rd.use_game_engine==False) and (rd.engine in cls.COMPAT_ENGINES)

    def draw(self, context):

        # login
        if not bpy.loginInserted:
            if _read_credentials():
                try:
                    if rffi.login(None, True, False):
                        bpy.passwordCorrect = True
                        bpy.loginInserted = True
                except LoginFailedException:
                    bpy.passwordCorrect = False
                    bpy.loginInserted = False

        layout = self.layout
        ore = context.scene.ore_render
        check_status(ore)

        if bpy.passwordCorrect == False:
            row = layout.row()
            row.label(text="Email or password missing/incorrect", icon='ERROR')
            col = layout.column()
            col.prop(ore, 'username', icon=bpy.statusMessage['username'])
            col.prop(ore, 'password', icon=bpy.statusMessage['password'])
            layout.operator('ore.login')
        else:
            layout.label(text='Successfully logged in as:', icon='INFO')
            layout.label(text=bpy.rffi_user)
            layout.operator('ore.change_user')

        layout.label(text='Message from Renderfarm.fi', icon='INFO')
        layout.label(text=bpy.rffi_motd)
        if bpy.rffi_accepting:
            layout.label(text='Accepting sessions', icon='FILE_TICK')
        else:
            layout.label(text='Not accepting sessions', icon='ERROR')
        layout.operator('ore.check_status')

class SESSIONS_PT_RenderfarmFi(RenderButtonsPanel, bpy.types.Panel):
    bl_label = 'My sessions'
    COMPAT_ENGINES = set(['RENDERFARMFI_RENDER'])

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return (rd.use_game_engine==False) and (rd.engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        ore = context.scene.ore_render
        if (bpy.passwordCorrect == True and bpy.loginInserted == True):
            layout = self.layout

            layout.template_list("UI_UL_list", "rederfarmfi_render", ore, 'all_sessions', ore, 'selected_session', rows=5)
            layout.operator('ore.cancel_session')
            if (bpy.cancelError == True):
                layout.label("This session cannot be cancelled")
                errorTime = time.time() - bpy.errorStartTime
                if (errorTime > 4):
                    bpy.cancelError = False
                    bpy.errorStartTime = -1
            layout.operator('ore.refresh_session_list')
        else:
            layout = self.layout
            layout.label(text="You must login first")

class RENDER_PT_RenderfarmFi(RenderButtonsPanel, bpy.types.Panel):
    bl_label = "Settings"
    COMPAT_ENGINES = set(['RENDERFARMFI_RENDER'])

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return (rd.use_game_engine==False) and (rd.engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout
        sce = context.scene
        ore = sce.ore_render

        if not bpy.rffi_accepting:
            layout.label(text="Renderfarm.fi is currently not accepting sessions.")
            return

        if (bpy.passwordCorrect == False or bpy.loginInserted == False):
            layout.label(text='You must login first')
        else:
            layout.prop(ore, 'title', icon=bpy.statusMessage['title'])
            layout.label(text="Example: Blue Skies project, scene 8")
            layout.row()
            layout.label(text="The description *MUST* mention some project")
            layout.label(text="The project can be a film, commercial work, portfolio or something similar")
            layout.label(text="We render only animation projects. Test renders are rejected.")
            # layout.prop(ore, 'shortdesc', icon=bpy.statusMessage['shortdesc'])
            layout.prop(ore, 'longdesc', icon=bpy.statusMessage['longdesc'])
            layout.label(text="Example: In this shot the main hero is running across a flowery field towards the castle.")
            layout.prop(ore, 'tags', icon=bpy.statusMessage['tags'])
            layout.label(text="Example: blue skies hero castle flowers grass particles")
            layout.prop(ore, 'url')
            layout.label(text="Example: www.sintel.org")

            #layout.label(text="Please verify your settings", icon='MODIFIER')
            row = layout.row()
            row = layout.row()
            #row.operator('ore.copy_settings')
            #row = layout.row()

            layout.label(text="Rendering engine")
            row = layout.row()
            if (ore.engine == 'blender'):
                row.operator('ore.use_blender_render', icon='FILE_TICK')
                row.operator('ore.use_cycles_render')
            elif (ore.engine == 'cycles' ):
                row.operator('ore.use_blender_render')
                row.operator('ore.use_cycles_render', icon='FILE_TICK')
            else:
                row.operator('ore.use_blender_render', icon='FILE_TICK')
                row.operator('ore.use_cycles_render')

            row = layout.row()

            layout.separator()
            row = layout.row()
            row.prop(ore, 'resox')
            row.prop(ore, 'resoy')
            row = layout.row()
            row.prop(ore, 'start')
            row.prop(ore, 'end')
            row = layout.row()
            row.prop(ore, 'fps')
            row = layout.row()
            if (ore.engine == 'cycles'):
                row.prop(ore, 'samples')
                row.prop(ore, 'subsamples')
            row = layout.row()
            row.prop(ore, 'memusage')
            #row.prop(ore, 'parts')
            layout.separator()
            row = layout.row()

            layout.label(text="Licenses", icon='FILE_REFRESH')
            row = layout.row()
            row.prop(ore, 'inlicense')
            row = layout.row()
            row.prop(ore, 'outlicense')

            check_status(ore)
            if (len(bpy.errors) > 0):
                bpy.ready = False
            else:
                bpy.ready = True

class UPLOAD_PT_RenderfarmFi(RenderButtonsPanel, bpy.types.Panel):
    bl_label = "Upload to www.renderfarm.fi"
    COMPAT_ENGINES = set(['RENDERFARMFI_RENDER'])

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return (rd.use_game_engine==False) and (rd.engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        if not bpy.rffi_accepting:
            layout.label(text="Renderfarm.fi is currently not accepting sessions.")
            return

        if (bpy.passwordCorrect == False or bpy.loginInserted == False):
            layout.label(text="You must login first")
        else:
            if (bpy.ready):
                layout.label(text="Policies", icon='LAMP')
                layout.label(text="- The animation must be at least 20 frames long")
                layout.label(text="- No still renders")
                layout.label(text="- No Python scripts")
                layout.label(text="- Memory usage max 4GB")
                layout.label(text="- If your render takes more than an hour / frame:")
                layout.label(text="   * No filter type composite nodes (blur, glare etc.)")
                layout.label(text="   * No SSS")
                layout.label(text="   * No Motion Blur")

                layout.separator()

                row = layout.row()
                if (bpy.uploadInProgress == True):
                    layout.label(text="------------------------")
                    layout.label(text="- Attempting upload... -")
                    layout.label(text="------------------------")
                if (bpy.file_format_warning == True):
                    layout.label(text="Your output format is HDR", icon='ERROR')
                    layout.label(text="Right now we don't support this file format")
                    layout.label(text="File format will be changed to PNG")
                if (bpy.texturePackError):
                    layout.label(text="There was an error in packing external textures", icon='ERROR')
                    layout.label(text="Make sure that all your textures exist on your computer")
                    layout.label(text="The render will still work, but won't have the missing textures")
                    layout.label(text="You may want to cancel your render above in \"My sessions\"")
                if (bpy.linkedFileError):
                    layout.label(text="There was an error in appending linked .blend files", icon='ERROR')
                    layout.label(text="Your render might not have all the external content")
                    layout.label(text="You may want to cancel your render above in \"My sessions\"")
                if (bpy.particleBakeWarning):
                    layout.label(text="You have a particle simulation", icon='ERROR')
                    layout.label(text="All Emitter type particles must be baked")
                if (bpy.childParticleWarning):
                    layout.label(text="Child particle mode changed!", icon='ERROR')
                    layout.label(text="Renderfarm.fi requires that you use 'Interpolated'")
                if (bpy.simulationWarning):
                    layout.label(text="There is a simulation!", icon='ERROR')
                    layout.label(text="- Fluid simulations aren't supported")
                    layout.label(text="- Collision simulations must be baked")
                row = layout.row()
                row.operator('ore.upload', icon='FILE_TICK')
                if (bpy.infoError == True):
                    layout.label("You must fill in the scene info first", icon='ERROR')
                    errorTime = time.time() - bpy.errorStartTime
                    if (errorTime > 4):
                        bpy.infoError = False
                        bpy.errorStartTime = -1
                layout.label(text="Warning:", icon='LAMP')
                layout.label(text="Blender may seem frozen during the upload!")
                row.operator('ore.reset', icon='FILE_REFRESH')
            else:
                layout.label(text="Fill the scene information first")
