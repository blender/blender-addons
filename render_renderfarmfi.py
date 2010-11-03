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

bl_addon_info = {
    "name": "Renderfarm.fi",
    "author": "Nathan Letwory <nathan@letworyinteractive.com>, Jesse Kaukonen <jesse.kaukonen@gmail.com>",
    "version": (3,),
    "blender": (2, 5, 3),
    "api": 31847,
    "location": "Render > Engine > Renderfarm.fi",
    "description": "Send .blend as session to http://www.renderfarm.fi to render",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"\
        "Scripts/Render/Renderfarm.fi",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=22927&group_id=153&atid=469",
    "category": "Render"}

"""
Copyright 2009-2010 Laurea University of Applied Sciences
Authors: Nathan Letwory, Jesse Kaukonen
"""

import bpy
import hashlib
import http.client
import xmlrpc.client
import math
from os.path import abspath, isabs, join, isfile

from bpy.props import PointerProperty, StringProperty, BoolProperty, EnumProperty, IntProperty, CollectionProperty

bpy.CURRENT_VERSION = bl_addon_info["version"][0]
bpy.found_newer_version = False
bpy.up_to_date = False
bpy.download_location = 'http://www.renderfarm.fi/blender'

bpy.errorMessages = {
    'missing_desc': 'You need to enter a title, short and long description',
    'missing_creds': 'You haven\'t entered your credentials yet'
}

bpy.statusMessage = {
    'title': 'TRIA_RIGHT',
    'shortdesc': 'TRIA_RIGHT',
    'longdesc': 'TRIA_RIGHT',
    'username': 'TRIA_RIGHT',
    'password': 'TRIA_RIGHT'
}

bpy.errors = []
bpy.ore_sessions = []
bpy.queue_selected = -1

def renderEngine(render_engine):
    bpy.types.register(render_engine)
    return render_engine


class ORESession(bpy.types.IDPropertyGroup):
    pass

class ORESettings(bpy.types.IDPropertyGroup):
    pass

# entry point for settings collection
bpy.types.Scene.ore_render = PointerProperty(type=ORESettings, name='ORE Render', description='ORE Render Settings')

# fill the new struct
ORESettings.username = StringProperty(name='E-mail', description='E-mail for Renderfarm.fi', maxlen=256, default='')
ORESettings.password = StringProperty(name='Password', description='Renderfarm.fi password', maxlen=256, default='')
ORESettings.hash = StringProperty(name='Hash', description='hash calculated out of credentials', maxlen=33, default='')

ORESettings.shortdesc = StringProperty(name='Short description', description='A short description of the scene (100 characters)', maxlen=101, default='')
ORESettings.longdesc = StringProperty(name='Long description', description='A more elaborate description of the scene (2k)', maxlen=2048, default='')
ORESettings.title = StringProperty(name='Title', description='Title for this session (128 characters)', maxlen=128, default='')
ORESettings.url = StringProperty(name='Project URL', description='Project URL. Leave empty if not applicable', maxlen=256, default='')

ORESettings.parts = IntProperty(name='Parts/Frame', description='', min=1, max=1000, soft_min=1, soft_max=64, default=1)
ORESettings.resox = IntProperty(name='Resolution X', description='X of render', min=1, max=10000, soft_min=1, soft_max=10000, default=1920)
ORESettings.resoy = IntProperty(name='Resolution Y', description='Y of render', min=1, max=10000, soft_min=1, soft_max=10000, default=1080)
ORESettings.memusage = IntProperty(name='Memory Usage', description='Estimated maximum memory usage during rendering in MB', min=1, max=6*1024, soft_min=1, soft_max=3*1024, default=256)
ORESettings.start = IntProperty(name='Start Frame', description='Start Frame', default=1)
ORESettings.end = IntProperty(name='End Frame', description='End Frame', default=250)
ORESettings.fps = IntProperty(name='FPS', description='FPS', min=1, max=256, default=25)

ORESettings.prepared = BoolProperty(name='Prepared', description='Set to True if preparation has been run', default=False)
ORESettings.debug = BoolProperty(name='Debug', description='Verbose output in console', default=False)
ORESettings.selected_session = IntProperty(name='Selected Session', description='The selected session', default=0)

# session struct
ORESession.name = StringProperty(name='Name', description='Name of the session', maxlen=128, default='[session]')

licenses =  (
        ('1', 'CC by-nc-nd', 'Creative Commons: Attribution Non-Commercial No Derivatives'),
        ('2', 'CC by-nc-sa', 'Creative Commons: Attribution Non-Commercial Share Alike'),
        ('3', 'CC by-nd', 'Creative Commons: Attribution No Derivatives'),
        ('4', 'CC by-nc', 'Creative Commons: Attribution Non-Commercial'),
        ('5', 'CC by-sa', 'Creative Commons: Attribution Share Alike'),
        ('6', 'CC by', 'Creative Commons: Attribution'),
        ('7', 'Copyright', 'Copyright, no license specified'),
        )
ORESettings.inlicense = EnumProperty(items=licenses, name='source license', description='license speficied for the source files', default='1')
ORESettings.outlicense = EnumProperty(items=licenses, name='output license', description='license speficied for the output files', default='1')

ORESettings.sessions = CollectionProperty(type=ORESession, name='Sessions', description='Sessions on Renderfarm.fi')
        
# all panels, except render panel
# Example of wrapping every class 'as is'
import properties_scene
for member in dir(properties_scene):
    subclass = getattr(properties_scene, member)
    try:        subclass.COMPAT_ENGINES.add('RENDERFARMFI_RENDER')
    except:    pass
del properties_scene

import properties_world
for member in dir(properties_world):
    subclass = getattr(properties_world, member)
    try:        subclass.COMPAT_ENGINES.add('RENDERFARMFI_RENDER')
    except:    pass
del properties_world

import properties_material
for member in dir(properties_material):
    subclass = getattr(properties_material, member)
    try:        subclass.COMPAT_ENGINES.add('RENDERFARMFI_RENDER')
    except:    pass
del properties_material

import properties_object
for member in dir(properties_object):
    subclass = getattr(properties_object, member)
    try:        subclass.COMPAT_ENGINES.add('RENDERFARMFI_RENDER')
    except:    pass
del properties_object

class RenderButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    # COMPAT_ENGINES must be defined in each subclass, external engines can add themselves here
    

class RENDERFARM_MT_Session(bpy.types.Menu):
    bl_label = "Show Session"

    def draw(self, context):
        layout = self.layout

        layout.operator('ore.completed_sessions')
        layout.operator('ore.accept_sessions')
        layout.operator('ore.active_sessions')
        layout.separator()
        layout.operator('ore.cancelled_sessions')

class LOGIN_PT_RenderfarmFi(RenderButtonsPanel, bpy.types.Panel):
    bl_label = 'Login to Renderfarm.fi'
    COMPAT_ENGINES = set(['RENDERFARMFI_RENDER'])

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return (rd.use_game_engine==False) and (rd.engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout
        # XXX layout.operator('ore.check_update')
        ore = context.scene.ore_render
        updateSessionList(ore)
        checkStatus(ore)

        if ore.hash=='':
            col = layout.column()
            if ore.hash=='':
                col.prop(ore, 'username', icon=bpy.statusMessage['username'])
                col.prop(ore, 'password', icon=bpy.statusMessage['password'])
            layout.operator('ore.login')
        else:
            layout.label(text='E-mail and password entered.', icon='INFO')
            layout.operator('ore.change_user')

class CHECK_PT_RenderfarmFi(RenderButtonsPanel, bpy.types.Panel):
    bl_label = 'Check for updates'
    COMPAT_ENGINES = set(['RENDERFARMFI_RENDER'])

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return (rd.use_game_engine==False) and (rd.engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout
        ore = context.scene.ore_render

        if bpy.found_newer_version == True:
            layout.operator('ore.open_download_location')
        else:
            if bpy.up_to_date == True:
                layout.label(text='You have the latest version')
            layout.operator('ore.check_update')

class SESSIONS_PT_RenderfarmFi(RenderButtonsPanel, bpy.types.Panel):
    bl_label = 'Sessions'
    COMPAT_ENGINES = set(['RENDERFARMFI_RENDER'])

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return (rd.use_game_engine==False) and (rd.engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout
        ore = context.scene.ore_render
        
        layout.menu("RENDERFARM_MT_Session")
        if bpy.queue_selected == 1:
            layout.label(text='Completed Sessions')
        elif bpy.queue_selected == 2:
            layout.label(text='Rendering Sessions')
        elif bpy.queue_selected == 3:
            layout.label(text='Pending Sessions')
        elif bpy.queue_selected == 4:
            layout.label(text='Cancelled and Rejected Sessions')
        layout.template_list(ore, 'sessions', ore, 'selected_session', rows=2)
        if bpy.queue_selected == 3:
            layout.operator('ore.cancel_session')

class RENDER_PT_RenderfarmFi(RenderButtonsPanel, bpy.types.Panel):
    bl_label = "Scene Settings"
    COMPAT_ENGINES = set(['RENDERFARMFI_RENDER'])

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return (rd.use_game_engine==False) and (rd.engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout
        sce = context.scene
        ore = sce.ore_render

        if ore.prepared and ore.hash!='':
            layout.prop(ore, 'memusage')
            
            layout.separator()
            row = layout.row()
            row.label(text='Resolution: '+str(ore.resox)+'x'+str(ore.resoy))
            
            layout.separator()
            row = layout.row()
            row.prop(ore, 'inlicense')
            row.prop(ore, 'outlicense')
            
            layout.separator()
            row = layout.row()
            row.operator('ore.upload')
            row.operator('ore.reset', icon='FILE_REFRESH')
        else:
            layout.prop(ore, 'title', icon=bpy.statusMessage['title'])
            layout.prop(ore, 'shortdesc', icon=bpy.statusMessage['shortdesc'])
            layout.prop(ore, 'longdesc', icon=bpy.statusMessage['longdesc'])
            layout.prop(ore, 'url')
            layout.separator()
            layout.operator('ore.use_scene_settings', icon='HAND')
            row = layout.row()
            row.prop(ore, 'resox')
            row.prop(ore, 'resoy')
            layout.separator()
            layout.prop(ore, 'parts')
            row = layout.row()
            row.prop(ore, 'start')
            row.prop(ore, 'end')
            layout.prop(ore, 'fps')
            
            layout.separator()
            layout.operator('ore.prepare', icon='INFO')

def random_string(length):
    import string
    import random
    return ''.join(random.choice(string.ascii_letters) for ii in range(length + 1))

def encode_multipart_data(data, files):
    boundary = random_string(30)

    def get_content_type(filename):
        return 'application/octet-stream' # default this

    def encode_field(field_name):
        return ('--' + boundary,
                'Content-Disposition: form-data; name="%s"' % field_name,
                '', str(data[field_name]))

    def encode_file(field_name):
        import codecs
        filename = files [field_name]
        return ('--' + boundary,
                'Content-Disposition: form-data; name="%s"; filename="%s"' % (field_name, filename),
                'Content-Type: %s' % get_content_type(filename),
                '', str(open(filename, 'rb').read(), encoding='iso-8859-1'))

    lines = []
    for name in data:
        lines.extend(encode_field(name))
    for name in files:
        lines.extend(encode_file(name))
    lines.extend(('--%s--' % boundary, ''))
    body = '\r\n'.join(lines)

    headers = {'content-type': 'multipart/form-data; boundary=' + boundary,
               'content-length': str(len(body))}

    return body, headers

def send_post(url, data, files):
    connection = http.client.HTTPConnection('xmlrpc.renderfarm.fi')
    connection.request('POST', '/file', *encode_multipart_data(data, files))
    response = connection.getresponse()
    res = response.read()
    return res

def md5_for_file(filepath):
    md5hash = hashlib.md5()
    blocksize = 0x10000
    f = open(filepath, "rb")
    while True:
        data = f.read(blocksize)
        if not data:
            break
        md5hash.update(data)
    return md5hash.hexdigest()

def upload_file(key, userid, sessionid, server, path):
    assert isabs(path)
    assert isfile(path)

    data = {
        'userId': str(userid),
        'sessionKey': key,
        'sessionId': sessionid,
        'md5sum': md5_for_file(path)
    }
    files = {
        'blenderfile': path
    }

    r = send_post(server, data, files)

    #print 'Uploaded %r' % (path)
    
    return r

def run_upload(key, userid, sessionid, path):
    #print('Upload', path)
    r = upload_file(key, userid, sessionid, r'http://xmlrpc.renderfarm.fi/file', path)
    o = xmlrpc.client.loads(r)
    #print('Done!')
    
    return o[0][0]

def ore_upload(op, context):
    sce = context.scene
    ore = sce.ore_render
    if not ore.prepared:
        op.report(set(['ERROR']), 'Your user or scene information is not complete')
        return {'CANCELLED'}
    try:
        authproxy = xmlrpc.client.ServerProxy(r'https://xmlrpc.renderfarm.fi/auth')
        res = authproxy.auth.getSessionKey(ore.username, ore.hash)
        key = res['key']
        userid = res['userId']
        
        proxy = xmlrpc.client.ServerProxy(r'http://xmlrpc.renderfarm.fi/session')
        proxy._ServerProxy__transport.user_agent = 'Renderfarm.fi Uploader/%s' % (bpy.CURRENT_VERSION)
        res = proxy.session.createSession(userid, key)
        sessionid = res['sessionId']
        key = res['key']
        res = run_upload(key, userid, sessionid, bpy.data.filepath)
        fileid = int(res['fileId'])
        
        res = proxy.session.setTitle(userid, res['key'], sessionid, ore.title)
        res = proxy.session.setLongDescription(userid, res['key'], sessionid, ore.longdesc)
        res = proxy.session.setShortDescription(userid, res['key'], sessionid, ore.shortdesc)
        if len(ore.url)>0:
            res = proxy.session.setExternalURLs(userid, res['key'], sessionid, ore.url)
        res = proxy.session.setStartFrame(userid, res['key'], sessionid, ore.start)
        res = proxy.session.setEndFrame(userid, res['key'], sessionid, ore.end)
        res = proxy.session.setSplit(userid, res['key'], sessionid, ore.parts)
        res = proxy.session.setMemoryLimit(userid, res['key'], sessionid, ore.memusage)
        res = proxy.session.setXSize(userid, res['key'], sessionid, ore.resox)
        res = proxy.session.setYSize(userid, res['key'], sessionid, ore.resoy)
        res = proxy.session.setFrameRate(userid, res['key'], sessionid, ore.fps)
        res = proxy.session.setOutputLicense(userid, res['key'], sessionid, int(ore.outlicense))
        res = proxy.session.setInputLicense(userid, res['key'], sessionid, int(ore.inlicense))
        res = proxy.session.setPrimaryInputFile(userid, res['key'], sessionid, fileid)
        res = proxy.session.submit(userid, res['key'], sessionid)
        op.report(set(['INFO']), 'Submission sent to Renderfarm.fi')
    except xmlrpc.client.Error as v:
        print('ERROR:', v)
        op.report(set(['ERROR']), 'An error occurred while sending submission to Renderfarm.fi')
    except Exception as e:
        print('Unhandled error:', e)
        op.report(set(['ERROR']), 'An error occurred while sending submission to Renderfarm.fi')
    
    return {'FINISHED'}

def setStatus(property, status):
    if status:
        bpy.statusMessage[property] = 'ERROR'
    else:
        bpy.statusMessage[property] = 'TRIA_RIGHT'

def showStatus(layoutform, property, message):
    if bpy.statusMessage[property] == 'ERROR':
        layoutform.label(text='', icon='ERROR')

def checkStatus(ore):
    bpy.errors = []
        
    if ore.hash=='' and (ore.username=='' or ore.password==''):
        bpy.errors.append('missing_creds')
    
    if '' in (ore.title, ore.longdesc, ore.shortdesc):
        bpy.errors.append('missing_desc')
    
    setStatus('username', ore.hash=='' and ore.username=='')
    setStatus('password', ore.hash=='' and ore.password=='')

    setStatus('title', ore.title=='')
    setStatus('longdesc', ore.longdesc=='')
    setStatus('shortdesc', ore.shortdesc=='')

class OreSession:

    def __init__(self, id, title):
        self.id = id
        self.title = title
        self.frames = 0
        self.startframe = 0
        self.endframe = 0
        self.rendertime = 0
        self.percentage = 0

    def percentageComplete(self):
        totFrames = self.endframe - self.startframe
        if totFrames != 0:
            done = math.floor((self.frames / totFrames)*100)
        else:
            done = math.floor((self.frames / (totFrames+0.01))*100)
        
        if done > 100:
            done = 100
        return done

def xmlSessionsToOreSessions(sessions, queue):
    bpy.ore_sessions = []
    completed = sessions[queue]
    for sid in completed:
        s = completed[sid]['title']
        t = completed[sid]['timestamps']
        sinfo = OreSession(sid, s) 
        if queue in ('completed', 'active'):
            sinfo.frames = completed[sid]['framesRendered']
        sinfo.startframe = completed[sid]['startFrame']
        sinfo.endframe = completed[sid]['endFrame']
        bpy.ore_sessions.append(sinfo)

def updateSessionList(ore):
    while(len(ore.sessions) > 0):
        ore.sessions.remove(0)

    for s in bpy.ore_sessions:
        ore.sessions.add()
        session = ore.sessions[-1]
        session.name = s.title + ' [' + str(s.percentageComplete()) + '% complete]'

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
        userproxy = xmlrpc.client.ServerProxy(r'https://xmlrpc.renderfarm.fi/user')
        if len(bpy.ore_sessions)>0:
            s = bpy.ore_sessions[ore.selected_session]
            try:
                res = userproxy.user.cancelSession(ore.username, ore.hash, int(s.id))
                self.report(set(['INFO']), 'Session ' + s.title + ' with id ' + s.id + ' cancelled')
            except:
                self.report(set(['ERROR']), 'Could not cancel session ' + s.title + ' with id ' + s.id)

        return {'FINISHED'}

class ORE_GetCompletedSessions(bpy.types.Operator):
    bl_idname = 'ore.completed_sessions'
    bl_label = 'Complete'

    def execute(self, context):
        sce = context.scene
        ore = sce.ore_render
        bpy.queue_selected = 1
        userproxy = xmlrpc.client.ServerProxy(r'https://xmlrpc.renderfarm.fi/user')

        sessions = userproxy.user.getAllSessions(ore.username, ore.hash, 'completed')

        xmlSessionsToOreSessions(sessions, 'completed')

        updateSessionList(ore)

        return {'FINISHED'}

class ORE_GetCancelledSessions(bpy.types.Operator):
    bl_idname = 'ore.cancelled_sessions'
    bl_label = 'Cancelled'

    def execute(self, context):
        sce = context.scene
        ore = sce.ore_render
        bpy.queue_selected = 4
        userproxy = xmlrpc.client.ServerProxy(r'https://xmlrpc.renderfarm.fi/user')

        sessions = userproxy.user.getAllSessions(ore.username, ore.hash, 'completed')

        xmlSessionsToOreSessions(sessions, 'canceled')

        updateSessionList(ore)

        return {'FINISHED'}

class ORE_GetActiveSessions(bpy.types.Operator):
    bl_idname = 'ore.active_sessions'
    bl_label = 'Rendering'

    def execute(self, context):
        sce = context.scene
        ore = sce.ore_render
        bpy.queue_selected = 2
        userproxy = xmlrpc.client.ServerProxy(r'https://xmlrpc.renderfarm.fi/user')

        sessions = userproxy.user.getAllSessions(ore.username, ore.hash, 'active')

        xmlSessionsToOreSessions(sessions, 'active')
    
        updateSessionList(ore)

        return {'FINISHED'}

class ORE_GetPendingSessions(bpy.types.Operator):
    bl_idname = 'ore.accept_sessions' # using ORE lingo in API. acceptQueue is session waiting for admin approval
    bl_label = 'Pending'

    def execute(self, context):
        sce = context.scene
        ore = sce.ore_render
        bpy.queue_selected = 3
        userproxy = xmlrpc.client.ServerProxy(r'https://xmlrpc.renderfarm.fi/user')

        sessions = userproxy.user.getAllSessions(ore.username, ore.hash, 'accept')

        xmlSessionsToOreSessions(sessions, 'accept')
    
        updateSessionList(ore)

        return {'FINISHED'}

class ORE_CheckUpdate(bpy.types.Operator):
    bl_idname = 'ore.check_update'
    bl_label = 'Check for new version'

    def execute(self, context):
        sce = context.scene
        ore = sce.ore_render
        blenderproxy = xmlrpc.client.ServerProxy(r'http://xmlrpc.renderfarm.fi/blender')
        try:
            self.report(set(['INFO']), 'Checking for newer version on Renderfarm.fi')
            dl_url = blenderproxy.blender.getCurrentVersion(bpy.CURRENT_VERSION)
            if len(dl_url['url']) > 0:
                self.report(set(['INFO']), 'Found a newer version on Renderfarm.fi ' + dl_url['url'])
                bpy.download_location = dl_url['url']
                bpy.found_newer_version = True
            else:
                bpy.up_to_date = True
            self.report(set(['INFO']), 'Done checking for newer version on Renderfarm.fi')
        except xmlrpc.client.Fault as f:
            print('ERROR:', f)
            self.report(set(['ERROR']), 'An error occurred while checking for newer version on Renderfarm.fi')

        return {'FINISHED'}

class ORE_LoginOp(bpy.types.Operator):
    bl_idname = 'ore.login'
    bl_label = 'Confirm credentials'

    def execute(self, context):
        sce = context.scene
        ore = sce.ore_render

        if ore.hash=='':
            if ore.password != '' and ore.username != '':
                ore.hash = hashlib.md5(ore.password.encode() + ore.username.encode()).hexdigest()
                ore.password = ''

        checkStatus(ore)
        
        if len(bpy.errors) > 0:
            ore.prepared = False
            return {'CANCELLED'}

        return {'FINISHED'}

class ORE_PrepareOp(bpy.types.Operator):
    '''Checking the scene will also save to the current file when successful!'''
    bl_idname = 'ore.prepare'
    bl_label = 'Check scene'
    
    def execute(self, context):
        def hasSSSMaterial():
            for m in bpy.data.materials:
                if m.subsurface_scattering.enabled:
                    return True
            return False

        def hasParticleSystem():
            if len(bpy.data.particles) > 0:
                self.report({'WARNING'}, "Found particle system")
                print("Found particle system")
                return True
            return False

        def hasSimulation(t):
            for o in bpy.data.objects:
                for m in o.modifiers:
                    if isinstance(m, t):
                        self.report({'WARNING'}, "Found simulation: " + str(t))
                        print("Found simulation: " + str(t))
                        return True
            return False

        def hasFluidSimulation():
            return hasSimulation(bpy.types.FluidSimulationModifier)

        def hasSmokeSimulation():
            return hasSimulation(bpy.types.SmokeModifier)

        def hasClothSimulation():
            return hasSimulation(bpy.types.ClothModifier)

        def hasCollisionSimulation():
            return hasSimulation(bpy.types.CollisionModifier)

        def hasSoftbodySimulation():
            return hasSimulation(bpy.types.SoftBodyModifier)

        def hasUnsupportedSimulation():
            return hasSoftbodySimulation() or hasCollisionSimulation() or hasClothSimulation() or hasSmokeSimulation or hasFluidSimulation() or hasParticleSystem()

        def isFilterNode(node):
            t = type(node)
            return t==bpy.types.CompositorNodeBlur or t==bpy.types.CompositorNodeDBlur

        def hasCompositingErrors(use_nodes, nodetree, parts):
            if not use_nodes: # no nodes in use, ignore check
                return False

            for node in nodetree.nodes:
                # output file absolutely forbidden
                if type(node)==bpy.types.CompositorNodeOutputFile:
                    self.report({'ERROR'}, 'File output node is disallowed, remove them from your compositing nodetrees.')
                    return True
                # blur et al are problematic when rendering ore.parts>1
                if isFilterNode(node) and parts>1:
                    self.report({'WARNING'}, 'A filtering node found and parts > 1. This combination will give bad output.')
                    return True

            return False

        sce = context.scene
        ore = sce.ore_render
        
        errors = False
        
        checkStatus(ore)
        
        if len(bpy.errors) > 0:
            ore.prepared = False
            return {'CANCELLED'}

        rd = sce.render
        print("=============================================")
        rd.threads_mode = 'FIXED'
        rd.threads = 1
        rd.resolution_x = ore.resox
        rd.resolution_y = ore.resoy
        if (rd.resolution_percentage != 100):
            print("Resolution percentage is not 100. Changing to 100%")
            self.report({'WARNING'}, "Resolution percentage is not 100. Changing to 100%")
            errors = True
        rd.resolution_percentage = 100
        if rd.file_format != 'PNG':
            print("Renderfarm.fi always uses PNG for output. Changing to PNG.")
            self.report({'WARNING'}, "Renderfarm.fi always uses PNG for output. Changing to PNG.")
            errors = True
        rd.file_format = 'PNG'
        if (rd.use_sss == True or hasSSSMaterial()) and ore.parts > 1:
            print("Subsurface Scattering is not supported when rendering with parts > 1. Disabling")
            self.report({'WARNING'}, "Subsurface Scattering is not supported when rendering with parts > 1. Disabling")
            rd.use_sss = False # disabling because ore.parts > 1. It's ok to use SSS with 1part/frame
            errors = True
        if hasUnsupportedSimulation() == True:
            print("An unsupported simulation was detected. Please check your settings and remove them")
            self.report({'WARNING'}, "An unsupported simulation was detected. Please check your settings and remove them")
            errors = True
        rd.use_save_buffers = False
        rd.use_free_image_textures = True
        if rd.use_compositing:
            if hasCompositingErrors(sce.use_nodes, sce.node_tree, ore.parts):
                print("Found disallowed nodes or problematic setup")
                self.report({'WARNING'}, "Found disallowed nodes or problematic setup")
                errors = True
        print("Done checking the scene. Now do a test render")
        self.report({'INFO'}, "Done checking the scene. Now do a test render")
        print("=============================================")
        
        # if errors found, don't allow to upload, instead have user
        # go through this until everything is ok
        if errors:
            self.report({'WARNING'}, "Settings were changed or other issues found. Check console and do a test render to make sure everything works.")
            ore.prepared = False
        else:
            ore.prepared = True
            rd.engine = 'BLENDER_RENDER'
            bpy.ops.wm.save_mainfile()
            rd.engine = 'RENDERFARMFI_RENDER'
            
        return {'FINISHED'}

class ORE_ResetOp(bpy.types.Operator):
    bl_idname = "ore.reset"
    bl_label = "Reset Preparation"
    
    def execute(self, context):
        sce = context.scene
        sce.ore_render.prepared = False
        return {'FINISHED'}

class ORE_UploaderOp(bpy.types.Operator):
    bl_idname = "ore.upload"
    bl_label = "Render on Renderfarm.fi"
    
    def execute(self, context):
        rd = context.scene.render
        rd.engine = 'BLENDER_RENDER'
        bpy.ops.wm.save_mainfile()
        return ore_upload(self, context)

class ORE_UseBlenderReso(bpy.types.Operator):
    bl_idname = "ore.use_scene_settings"
    bl_label = "Use Scene resolution"
    
    def execute(self, context):
        sce = context.scene
        ore = sce.ore_render
        
        ore.resox = sce.render.resolution_x
        ore.resoy = sce.render.resolution_y
        
        return {'FINISHED'}

class ORE_ChangeUser(bpy.types.Operator):
    bl_idname = "ore.change_user"
    bl_label = "Change user"
    
    def execute(self, context):
        ore = context.scene.ore_render
        ore.password = ''
        ore.hash = ''
        
        return {'FINISHED'}

class RenderfarmFi(bpy.types.RenderEngine):
    bl_idname = 'RENDERFARMFI_RENDER'
    bl_label = "Renderfarm.fi"

    def render(self, scene):
        print('Do test renders with Blender Render')

def menu_export(self, context):
    import os
    default_path = os.path.splitext(bpy.data.filepath)[0] + ".py"
    self.layout.operator(RenderfarmFi.bl_idname, text=RenderfarmFi.bl_label)

def register():
    bpy.types.INFO_MT_render.append(menu_export)

def unregister():
    bpy.types.INFO_MT_render.remove(menu_export)

if __name__ == "__main__":
    register()
