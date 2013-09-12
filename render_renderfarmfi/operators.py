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

import hashlib

import bpy

from .utils import _write_credentials, _read_credentials
from .prepare import _prepare_scene
from .upload import _ore_upload
from .rpc import rffi, _do_refresh
from .exceptions import LoginFailedException, SessionCancelFailedException

class OpSwitchRenderfarm(bpy.types.Operator):
    bl_label = "Switch to Renderfarm.fi"
    bl_idname = "ore.switch_to_renderfarm_render"

    def execute(self, context):
        ore = bpy.context.scene.ore_render
        rd = bpy.context.scene.render

        ore.resox = rd.resolution_x
        ore.resoy = rd.resolution_y
        ore.fps = rd.fps
        ore.start = bpy.context.scene.frame_start
        ore.end = bpy.context.scene.frame_end
        if (rd.engine == 'CYCLES'):
            ore.samples = bpy.context.scene.cycles.samples
            ore.engine = 'cycles'
        else:
            ore.engine = 'blender'
        bpy.context.scene.render.engine = 'RENDERFARMFI_RENDER'
        return {'FINISHED'}

class OpSwitchBlenderRender(bpy.types.Operator):
    bl_label = "Switch to local render"
    bl_idname = "ore.switch_to_local_render"

    def execute(self, context):
        rd = bpy.context.scene.render
        ore = bpy.context.scene.ore_render
        rd.resolution_x = ore.resox
        rd.resolution_y = ore.resoy
        rd.fps = ore.fps
        bpy.context.scene.frame_start = ore.start
        bpy.context.scene.frame_end = ore.end
        if (bpy.context.scene.ore_render.engine == 'cycles'):
            rd.engine = 'CYCLES'
            bpy.context.scene.cycles.samples = ore.samples
        else:
            bpy.context.scene.render.engine = 'BLENDER_RENDER'
        return {'FINISHED'}

# Copies start & end frame + others from render settings to ore settings
class OpCopySettings(bpy.types.Operator):
    bl_label = "Copy settings from current scene"
    bl_idname = "ore.copy_settings"

    def execute(self, context):
        sce = bpy.context.scene
        rd = sce.render
        ore = sce.ore_render
        ore.resox = rd.resolution_x
        ore.resoy = rd.resolution_y
        ore.start = sce.frame_start
        ore.end = sce.frame_end
        ore.fps = rd.fps
        return {'FINISHED'}

class ORE_RefreshOp(bpy.types.Operator):
    bl_idname = 'ore.refresh_session_list'
    bl_label = 'Refresh'

    def execute(self, context):
        result = _do_refresh(self)
        if (result == 0):
            return {'FINISHED'}
        else:
            return {'CANCELLED'}

class ORE_OpenDownloadLocation(bpy.types.Operator):
    bl_idname = 'ore.open_download_location'
    bl_label = 'Download new version for your platform'

    def execute(self, context):
        import webbrowser
        webbrowser.open(bpy.download_location)
        return {'FINISHED'}

class ORE_CancelSession(bpy.types.Operator):
    bl_idname = 'ore.cancel_session'
    bl_label = 'Cancel Session'

    def execute(self, context):
        sce = context.scene
        ore = sce.ore_render
        if len(bpy.ore_complete_session_queue)>0:
            s = bpy.ore_complete_session_queue[ore.selected_session]
            try:
                rffi.cancel_session(self, s)
            except SessionCancelFailedException as scfe:
                print("sessioncancelfailedexception", scfe)

        return {'FINISHED'}

class ORE_GetCompletedSessions(bpy.types.Operator):
    bl_idname = 'ore.completed_sessions'
    bl_label = 'Completed sessions'

    def execute(self, context):
        sce = context.scene
        ore = sce.ore_render
        bpy.queue_selected = 1
        bpy.ore_active_session_queue = bpy.ore_completed_sessions
        update_session_list(completed_sessions, ore)

        return {'FINISHED'}

class ORE_GetCancelledSessions(bpy.types.Operator):
    bl_idname = 'ore.cancelled_sessions'
    bl_label = 'Cancelled sessions'

    def execute(self, context):
        sce = context.scene
        ore = sce.ore_render
        bpy.queue_selected = 4
        bpy.ore_active_session_queue = bpy.ore_cancelled_sessions
        update_session_list(cancelled_sessions, ore)

        return {'FINISHED'}

class ORE_GetActiveSessions(bpy.types.Operator):
    bl_idname = 'ore.active_sessions'
    bl_label = 'Rendering sessions'

    def execute(self, context):
        sce = context.scene
        ore = sce.ore_render
        bpy.queue_selected = 2
        bpy.ore_active_session_queue = bpy.ore_active_sessions
        update_session_list(active_sessions, ore)

        return {'FINISHED'}

class ORE_GetPendingSessions(bpy.types.Operator):
    bl_idname = 'ore.accept_sessions' # using ORE lingo in API. acceptQueue is session waiting for admin approval
    bl_label = 'Pending sessions'

    def execute(self, context):
        sce = context.scene
        ore = sce.ore_render
        bpy.queue_selected = 3
        bpy.ore_active_session_queue = bpy.ore_pending_sessions
        update_session_list(pending_sessions, ore)

        return {'FINISHED'}

class ORE_CheckUpdate(bpy.types.Operator):
    bl_idname = 'ore.check_update'
    bl_label = 'Check for a new version'

    def execute(self, context):
        blenderproxy = xmlrpc.client.ServerProxy(r'http://xmlrpc.renderfarm.fi/renderfarmfi/blender', verbose=bpy.RFFI_VERBOSE)
        try:
            self.report({'INFO'}, 'Checking for newer version on Renderfarm.fi')
            dl_url = blenderproxy.blender.getCurrentVersion(bpy.CURRENT_VERSION)
            if len(dl_url['url']) > 0:
                self.report({'INFO'}, 'Found a newer version on Renderfarm.fi ' + dl_url['url'])
                bpy.download_location = dl_url['url']
                bpy.found_newer_version = True
            else:
                bpy.up_to_date = True
            self.report({'INFO'}, 'Done checking for newer version on Renderfarm.fi')
        except xmlrpc.client.Fault as f:
            print('ERROR:', f)
            self.report({'ERROR'}, 'An error occurred while checking for newer version on Renderfarm.fi: ' + f.faultString)
        except xmlrpc.client.ProtocolError as e:
            print('ERROR:', e)
            self.report({'ERROR'}, 'An HTTP error occurred while checking for newer version on Renderfarm.fi: ' + str(e.errcode) + ' ' + e.errmsg)

        return {'FINISHED'}

class ORE_LoginOp(bpy.types.Operator):
    bl_idname = 'ore.login'
    bl_label = 'Login'

    def execute(self, context):
        sce = context.scene
        ore = sce.ore_render

        ore.password = ore.password.strip()
        ore.username = ore.username.strip()

        print("writing new credentials")
        _write_credentials(hashlib.md5(ore.password.encode() + ore.username.encode()).hexdigest(),ore.username)
        _read_credentials()
        ore.password = ''
        ore.username = ''
        bpy.loginInserted = False
        bpy.passwordCorrect = False

        try:
            _do_refresh(self, True)

            bpy.passwordCorrect = True
            bpy.loginInserted = True

        except LoginFailedException as v:
            bpy.ready = False
            bpy.loginInserted = False
            bpy.passwordCorrect = False
            ore.username = bpy.rffi_user
            _write_credentials('', '')
            _read_credentials()
            ore.hash = ''
            ore.password = ''
            self.report({'WARNING'}, "Incorrect login: " + str(v))
            print(v)
            return {'CANCELLED'}

        return {'FINISHED'}

class ORE_ResetOp(bpy.types.Operator):
    bl_idname = "ore.reset"
    bl_label = "Reset Preparation"

    def execute(self, context):
        sce = context.scene
        ore = sce.ore_render
        ore.prepared = False
        bpy.loginInserted = False
        bpy.prepared = False
        ore.hash = ''
        ore.username = ''
        ore.passowrd = ''
        ore.longdesc = ''
        ore.shortdesc = '-'
        ore.tags = ''
        ore.title = ''
        ore.url = ''

        return {'FINISHED'}

class ORE_TestRenderOp(bpy.types.Operator):
    bl_idname = "ore.test_render"
    bl_label = "Run a test render"

    def execute(self, context):
        rd = context.scene.render
        rd.engine = 'BLENDER_RENDER'
        rd.threads_mode = 'AUTO'
        rd.threads = 1
        bpy.ops.render.render()
        rd.threads_mode = 'FIXED'
        rd.threads = 1
        rd.engine = 'RENDERFARMFI_RENDER'
        return {'FINISHED'}

class ORE_UploaderOp(bpy.types.Operator):
    bl_idname = "ore.upload"
    bl_label = "Render on Renderfarm.fi"

    def execute(self, context):

        bpy.uploadInProgress = True
        _prepare_scene()

        returnValue = _ore_upload(self, context)
        bpy.uploadInProgress = False
        return returnValue

class ORE_UseBlenderReso(bpy.types.Operator):
    bl_idname = "ore.use_scene_settings"
    bl_label = "Use Scene settings"

    def execute(self, context):
        sce = context.scene
        ore = sce.ore_render
        rd = context.scene.render

        ore.resox = rd.resolution_x
        ore.resoy = rd.resolution_y
        ore.start = sce.frame_start
        ore.end = sce.frame_end
        ore.fps = rd.fps

        return {'FINISHED'}

class ORE_UseCyclesRender(bpy.types.Operator):
    bl_idname = "ore.use_cycles_render"
    bl_label = "Cycles"

    def execute(self, context):
        context.scene.ore_render.engine = 'cycles'
        return {'FINISHED'}

class ORE_UseBlenderRender(bpy.types.Operator):
    bl_idname = "ore.use_blender_render"
    bl_label = "Blender Internal"

    def execute(self, context):
        context.scene.ore_render.engine = 'blender'
        return {'FINISHED'}

class ORE_ChangeUser(bpy.types.Operator):
    bl_idname = "ore.change_user"
    bl_label = "Change user"

    def execute(self, context):
        ore = context.scene.ore_render
        _write_credentials('', '')
        _read_credentials()
        ore.password = ''
        bpy.ore_sessions = []
        ore.hash = ''
        bpy.rffi_user = ''
        bpy.rffi_hash = ''
        bpy.rffi_creds_found = False
        bpy.passwordCorrect = False
        bpy.loginInserted = False
        bpy.rffi_accepts = False
        bpy.rffi_motd = ''

        return {'FINISHED'}

class ORE_CheckStatus(bpy.types.Operator):
    bl_idname = "ore.check_status"
    bl_label = "Check Renderfarm.fi Accept status"

    def execute(self, context):
        rffi.check_status()
        return {'FINISHED'}
