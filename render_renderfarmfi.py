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
    "name": "Renderfarm.fi",
    "author": "Nathan Letwory <nathan@letworyinteractive.com>, Jesse Kaukonen <jesse.kaukonen@gmail.com>",
    "version": (12,),
    "blender": (2, 6, 0),
    "api": 41934,
    "location": "Render > Engine > Renderfarm.fi",
    "description": "Send .blend as session to http://www.renderfarm.fi to render",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"\
        "Scripts/Render/Renderfarm.fi",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=22927",
    "category": "Render"}

"""
Copyright 2009-2011 Laurea University of Applied Sciences
Authors: Nathan Letwory, Jesse Kaukonen
"""

import bpy
import hashlib
import http.client
import xmlrpc.client
import math
from os.path import isabs, isfile
import time

from bpy.props import PointerProperty, StringProperty, BoolProperty, EnumProperty, IntProperty, CollectionProperty

bpy.CURRENT_VERSION = bl_info["version"][0]
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
    'tags': 'TRIA_RIGHT',
    'longdesc': 'TRIA_RIGHT',
    'username': 'TRIA_RIGHT',
    'password': 'TRIA_RIGHT'
}

bpy.errors = []
bpy.ore_sessions = []
bpy.ore_completed_sessions = []
bpy.ore_active_sessions = []
bpy.ore_rejected_sessions = []
bpy.ore_pending_sessions = []
bpy.ore_active_session_queue = []
bpy.ore_complete_session_queue = []
bpy.queue_selected = -1
bpy.errorStartTime = -1.0
bpy.infoError = False
bpy.cancelError = False
bpy.texturePackError = False
bpy.linkedFileError = False
bpy.uploadInProgress = False
bpy.originalFileName = bpy.path.display_name_from_filepath(bpy.data.filepath)
bpy.particleBakeWarning = False
bpy.childParticleWarning = False
bpy.simulationWarning = False
bpy.ready = False

def renderEngine(render_engine):
    bpy.utils.register_class(render_engine)
    return render_engine

licenses =  (
        ('1', 'CC by-nc-nd', 'Creative Commons: Attribution Non-Commercial No Derivatives'),
        ('2', 'CC by-nc-sa', 'Creative Commons: Attribution Non-Commercial Share Alike'),
        ('3', 'CC by-nd', 'Creative Commons: Attribution No Derivatives'),
        ('4', 'CC by-nc', 'Creative Commons: Attribution Non-Commercial'),
        ('5', 'CC by-sa', 'Creative Commons: Attribution Share Alike'),
        ('6', 'CC by', 'Creative Commons: Attribution'),
        ('7', 'Copyright', 'Copyright, no license specified'),
        )

class ORESession(bpy.types.PropertyGroup):
    name = StringProperty(name='Name', description='Name of the session', maxlen=128, default='[session]')

class ORESettings(bpy.types.PropertyGroup):
    username = StringProperty(name='E-mail', description='E-mail for Renderfarm.fi', maxlen=256, default='')
    password = StringProperty(name='Password', description='Renderfarm.fi password', maxlen=256, default='')
    hash = StringProperty(name='Hash', description='hash calculated out of credentials', maxlen=33, default='')
    
    shortdesc = StringProperty(name='Short description', description='A short description of the scene (100 characters)', maxlen=101, default='-')
    tags = StringProperty(name='Tags', description='A list of tags that best suit the animation', maxlen=102, default='')
    longdesc = StringProperty(name='Description', description='Description of the scene (2k)', maxlen=2048, default='')
    title = StringProperty(name='Title', description='Title for this session (128 characters)', maxlen=128, default='')
    url = StringProperty(name='Project URL', description='Project URL. Leave empty if not applicable', maxlen=256, default='')
    
    parts = IntProperty(name='Parts/Frame', description='', min=1, max=1000, soft_min=1, soft_max=64, default=1)
    resox = IntProperty(name='Resolution X', description='X of render', min=1, max=10000, soft_min=1, soft_max=10000, default=1920)
    resoy = IntProperty(name='Resolution Y', description='Y of render', min=1, max=10000, soft_min=1, soft_max=10000, default=1080)
    memusage = IntProperty(name='Memory Usage', description='Estimated maximum memory usage during rendering in MB', min=1, max=6*1024, soft_min=1, soft_max=3*1024, default=256)
    start = IntProperty(name='Start Frame', description='Start Frame', default=1)
    end = IntProperty(name='End Frame', description='End Frame', default=250)
    fps = IntProperty(name='FPS', description='FPS', min=1, max=256, default=25)
    
    prepared = BoolProperty(name='Prepared', description='Set to True if preparation has been run', default=False)
    loginInserted = BoolProperty(name='LoginInserted', description='Set to True if user has logged in', default=False)
    passwordCorrect = BoolProperty(name='PasswordCorrect', description='Set to False if the password is incorrect', default=True)
    debug = BoolProperty(name='Debug', description='Verbose output in console', default=False)
    selected_session = IntProperty(name='Selected Session', description='The selected session', default=0)
    hasUnsupportedSimulation = BoolProperty(name='HasSimulation', description='Set to True if therea re unsupported simulations', default=False)
    
    inlicense = EnumProperty(items=licenses, name='source license', description='license speficied for the source files', default='1')
    outlicense = EnumProperty(items=licenses, name='output license', description='license speficied for the output files', default='1')
    sessions = CollectionProperty(type=ORESession, name='Sessions', description='Sessions on Renderfarm.fi')
    completed_sessions = CollectionProperty(type=ORESession, name='Completed sessions', description='Sessions that have been already rendered')
    rejected_sessions = CollectionProperty(type=ORESession, name='Rejected sessions', description='Sessions that have been rejected')
    pending_sessions = CollectionProperty(type=ORESession, name='Pending sessions', description='Sessions that are waiting for approval')
    active_sessions = CollectionProperty(type=ORESession, name='Active sessions', description='Sessions that are currently rendering')
    all_sessions = CollectionProperty(type=ORESession, name='All sessions', description='List of all of the users sessions')

# session struct

# all panels, except render panel
# Example of wrapping every class 'as is'
from bl_ui import properties_scene
for member in dir(properties_scene):
    subclass = getattr(properties_scene, member)
    try:        subclass.COMPAT_ENGINES.add('RENDERFARMFI_RENDER')
    except:    pass
del properties_scene

from bl_ui import properties_world
for member in dir(properties_world):
    subclass = getattr(properties_world, member)
    try:        subclass.COMPAT_ENGINES.add('RENDERFARMFI_RENDER')
    except:    pass
del properties_world

from bl_ui import properties_material
for member in dir(properties_material):
    subclass = getattr(properties_material, member)
    try:        subclass.COMPAT_ENGINES.add('RENDERFARMFI_RENDER')
    except:    pass
del properties_material

from bl_ui import properties_object
for member in dir(properties_object):
    subclass = getattr(properties_object, member)
    try:        subclass.COMPAT_ENGINES.add('RENDERFARMFI_RENDER')
    except:    pass
del properties_object

def hasSSSMaterial():
    for m in bpy.data.materials:
        if m.subsurface_scattering.use:
            return True
        return False

def tuneParticles():
    for p in bpy.data.particles:
        if (p.type == 'EMITTER'):
            bpy.particleBakeWarning = True
        if (p.type == 'HAIR'):
            if (p.child_type == 'SIMPLE'):
                p.child_type = 'INTERPOLATED'
                bpy.childParticleWarning = True

def hasParticleSystem():
    if (len(bpy.data.particles) > 0):
        print("Found particle system")
        return True
    return False

def hasSimulation(t):
    for o in bpy.data.objects:
        for m in o.modifiers:
            if isinstance(m, t):
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
    return hasSoftbodySimulation() or hasCollisionSimulation() or hasClothSimulation() or hasSmokeSimulation() or hasFluidSimulation()

def isFilterNode(node):
    t = type(node)
    return t==bpy.types.CompositorNodeBlur or t==bpy.types.CompositorNodeDBlur

def changeSettings():
    
    sce = bpy.context.scene
    rd = sce.render
    ore = sce.ore_render
    
    # Necessary settings for BURP
    ore.resox = rd.resolution_x
    ore.resoy = rd.resolution_y
    ore.start = sce.frame_start
    ore.end = sce.frame_end
    ore.fps = rd.fps
    
    # Multipart support doesn' work if SSS is used
    if ((rd.use_sss == True and hasSSSMaterial()) and ore.parts > 1):
        ore.parts = 1;
    
    if (hasParticleSystem()):
        tuneParticles()
    else:
        bpy.particleBakeWarning = False
        bpy.childParticleWarning = False
    
    if (hasUnsupportedSimulation()):
        simulationWarning = True
    else:
        bpy.simulationWarning = False

def prepareScene():
    sce = bpy.context.scene
    rd = sce.render
    ore = sce.ore_render
    
    changeSettings()
    
    print("Packing external textures...")
    # Pack all external textures
    try:
        bpy.ops.file.pack_all()
        bpy.texturePackError = False
    except Exception as e:
        bpy.texturePackError = True
        print(e)
    
    linkedData = bpy.utils.blend_paths()
    if (len(linkedData) > 0):
        print("Appending linked .blend files...")
        try:
            bpy.ops.object.make_local(type='ALL')
            bpy.linkedFileError = False
        except Exception as e:
            bpy.linkedFileError = True
            print(e)
    else:
        print("No external .blends used, skipping...")
    
    # Save with a different name
    print("Saving into a new file...")
    try:
        # If the filename is empty, we'll make one from the path of the Blender installation
        if (len(bpy.originalFileName) == 0):
            bpy.originalFileName = bpy.utils.resource_path(type='LOCAL') + "renderfarm.blend"
            bpy.ops.wm.save_mainfile(filepath=bpy.originalFileName)
        else:
            savePath = bpy.originalFileName
            savePath = savePath + "_renderfarm"
            bpy.ops.wm.save_mainfile(filepath=savePath)
    except Exception as e:
        print(e)
    
    print(".blend prepared")

class RenderButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    # COMPAT_ENGINES must be defined in each subclass, external engines can add themselves here    

class OpSwitchRenderfarm(bpy.types.Operator):
    bl_label = "Switch to Renderfarm.fi"
    bl_idname = "ore.switch_to_renderfarm_render"
    
    def execute(self, context):
        changeSettings()
        bpy.context.scene.render.engine = 'RENDERFARMFI_RENDER'
        return {'FINISHED'}

class OpSwitchBlenderRender(bpy.types.Operator):
    bl_label = "Switch to Blender Render"
    bl_idname = "ore.switch_to_blender_render"
    
    def execute(self, context):
        bpy.context.scene.render.engine = 'BLENDER_RENDER'
        return {'FINISHED'}  

# Copies start & end frame + others from render settings to ore settings
class OpCopySettings(bpy.types.Operator):
    bl_label = "Copy from Blender Render settings"
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

# We re-write the default render panel (not enabled, breaks Cycles)
'''class RENDER_PT_render(RenderButtonsPanel, bpy.types.Panel):
    bl_label = "Render"
    COMPAT_ENGINES = {'BLENDER_RENDER'}
    
    def draw(self, context):
        layout = self.layout
        rd = context.scene.render
        row = layout.row()
        row.operator("ore.switch_to_renderfarm_render", text="Renderfarm.fi", icon='WORLD')
        row.operator("ore.switch_to_blender_render", text="Blender Render", icon='BLENDER')
        row = layout.row()
        if (bpy.context.scene.render.engine == 'BLENDER_RENDER'):
            row.operator("render.render", text="Image", icon='RENDER_STILL')
            row.operator("render.render", text="Animation", icon='RENDER_ANIMATION').animation = True
            layout.prop(rd, "display_mode", text="Display")
        else:
            if bpy.found_newer_version == True:
                layout.operator('ore.open_download_location')
            else:
                if bpy.up_to_date == True:
                    layout.label(text='You have the latest version')
                layout.operator('ore.check_update')
'''

class EngineSelectPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_engineSelectPanel"
    bl_label = "Choose rendering mode"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    
    def draw(self, context):
        layout = self.layout
        rd = context.scene.render
        row = layout.row()
        row.operator("ore.switch_to_renderfarm_render", text="Renderfarm.fi", icon='WORLD')
        row.operator("ore.switch_to_blender_render", text="Blender Render", icon='BLENDER')
        row = layout.row()
        if (bpy.context.scene.render.engine == 'RENDERFARMFI_RENDER'):
            if bpy.found_newer_version == True:
                layout.operator('ore.open_download_location')
            else:
                if bpy.up_to_date == True:
                    layout.label(text='You have the latest version')
                layout.operator('ore.check_update')
                
bpy.utils.register_class(EngineSelectPanel)

class RENDERFARM_MT_Session(bpy.types.Menu):
    bl_label = "Show Session"
    
    def draw(self, context):
        layout = self.layout
        ore = context.scene.ore_render
        
        if (ore.loginInserted == True):
            layout.operator('ore.completed_sessions')
            layout.operator('ore.accept_sessions')
            layout.operator('ore.active_sessions')
            layout.separator()
            layout.operator('ore.cancelled_sessions')
        else:
            row = layout.row()
            row.label(text="You must login first")

class LOGIN_PT_RenderfarmFi(RenderButtonsPanel, bpy.types.Panel):
    bl_label = 'Login to Renderfarm.fi'
    COMPAT_ENGINES = set(['RENDERFARMFI_RENDER'])
    
    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return (rd.use_game_engine==False) and (rd.engine in cls.COMPAT_ENGINES)
    
    def draw(self, context):
        layout = self.layout
        ore = context.scene.ore_render
        checkStatus(ore)
        
        if (ore.passwordCorrect == False):
            row = layout.row()
            row.label(text="Email or password missing/incorrect", icon='ERROR')
        if ore.hash=='':
            col = layout.column()
            if ore.hash=='':
                col.prop(ore, 'username', icon=bpy.statusMessage['username'])
                col.prop(ore, 'password', icon=bpy.statusMessage['password'])
            layout.operator('ore.login')
        else:
            layout.label(text='Successfully logged in', icon='INFO')
            layout.operator('ore.change_user')

class SESSIONS_PT_RenderfarmFi(RenderButtonsPanel, bpy.types.Panel):
    bl_label = 'My sessions'
    COMPAT_ENGINES = set(['RENDERFARMFI_RENDER'])
    
    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return (rd.use_game_engine==False) and (rd.engine in cls.COMPAT_ENGINES)
    
    def draw(self, context):
        ore = context.scene.ore_render
        if (ore.passwordCorrect == True and ore.loginInserted == True):
            layout = self.layout
            
            layout.template_list(ore, 'all_sessions', ore, 'selected_session', rows=5)
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
        rd = sce.render
        
        if (ore.passwordCorrect == False or ore.loginInserted == False):
            layout.label(text='You must login first')
        else:
            layout.prop(ore, 'title', icon=bpy.statusMessage['title'])
            layout.label(text="Example: Blue Skies project, scene 8")
            # layout.prop(ore, 'shortdesc', icon=bpy.statusMessage['shortdesc'])
            layout.prop(ore, 'longdesc', icon=bpy.statusMessage['longdesc'])
            layout.label(text="Example: In this shot the main hero is running across a flowery field towards the castle.")
            layout.prop(ore, 'tags', icon=bpy.statusMessage['tags'])
            layout.label(text="Example: blue skies hero castle flowers grass particles")
            layout.prop(ore, 'url')
            layout.label(text="Example: www.sintel.org")
            checkStatus(ore)
            if (len(bpy.errors) > 0):
                bpy.ready = False
            else:
                bpy.ready = True

class UPLOAD_PT_RenderfarmFi(RenderButtonsPanel, bpy.types.Panel):
    bl_label = "Upload"
    COMPAT_ENGINES = set(['RENDERFARMFI_RENDER'])
    
    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return (rd.use_game_engine==False) and (rd.engine in cls.COMPAT_ENGINES)
    
    def draw(self, context):
        layout = self.layout
        sce = context.scene
        ore = sce.ore_render
        rd = sce.render
        if (ore.passwordCorrect == False or ore.loginInserted == False):
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
                
                layout.label(text="Please verify your settings", icon='MODIFIER')
                row = layout.row()
                row.operator('ore.copy_settings')
                row = layout.row()
                row.label(text="Resolution: " + str(ore.resox) + "x" + str(ore.resoy))
                row = layout.row()
                row.label(text="Frames: " + str(ore.start) + " - " + str(ore.end))
                row = layout.row()
                if (ore.start == ore.end):
                    row.label(text="You have selected only 1 frame to be rendered", icon='ERROR')
                    row = layout.row()
                    row.label(text="Renderfarm.fi does not render stills - only animations")
                row = layout.row()
                row.label(text="Frame rate: " + str(ore.fps))
                row = layout.row()
                
                layout.separator()
                
                layout.label(text="Optional advanced settings", icon='MODIFIER')
                row = layout.row()
                row.prop(ore, 'memusage')
                row.prop(ore, 'parts')
                layout.separator()
                row = layout.row()
                
                layout.label(text="Licenses", icon='FILE_REFRESH')
                row = layout.row()
                row.prop(ore, 'inlicense')  
                row.prop(ore, 'outlicense')
                
                row = layout.row()
                if (bpy.uploadInProgress == True):
                    layout.label(text="Attempting upload...")
                if (bpy.texturePackError):
                    layout.label(text="There was an error in packing external textures", icon='ERROR')
                    layout.label(text="Make sure that all your textures exist on your computer")
                    layout.label(text="The render will still work, but won't have the missing textures")
                    layout.label(text="You may want to cancel your render above")
                if (bpy.linkedFileError):
                    layout.label(text="There was an error in appending linked .blend files", icon='ERROR')
                    layout.label(text="Your render might not have all the external content")
                    layout.label(text="You may want to cancel your render above")
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
                layout.label(text="Blender may seem frozen during the upload!", icon='LAMP')
                row.operator('ore.reset', icon='FILE_REFRESH')
            else:
                layout.label(text="Fill the scene information first")

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
    print("Done!")
    return o[0][0]

def ore_upload(op, context):
    sce = context.scene
    ore = sce.ore_render
    
    if not bpy.ready:
        op.report(set(['ERROR']), 'Your user or scene information is not complete')
        bpy.infoError = True
        bpy.errorStartTime = time.time()
        bpy.context.scene.render.engine = 'RENDERFARMFI_RENDER'
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
        bpy.context.scene.render.engine = 'RENDERFARMFI_RENDER'
        print('ERROR:', v)
        op.report(set(['ERROR']), 'An error occurred while sending submission to Renderfarm.fi')
    except Exception as e:
        bpy.context.scene.render.engine = 'RENDERFARMFI_RENDER'
        print('Unhandled error:', e)
        op.report(set(['ERROR']), 'An error occurred while sending submission to Renderfarm.fi')
    
    bpy.context.scene.render.engine = 'RENDERFARMFI_RENDER'
    doRefresh()
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
    
    if '' in {ore.title, ore.longdesc, ore.shortdesc}:
        bpy.errors.append('missing_desc')
        bpy.infoError = True
    
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
    #bpy.ore_sessions = []
    output = []
    sessionFilter = []
    sessionFilter = sessions[queue]
    for sid in sessionFilter:
        s = sessionFilter[sid]['title']
        t = sessionFilter[sid]['timestamps']
        sinfo = OreSession(sid, s) 
        if queue in ('completed', 'active'):
            sinfo.frames = sessionFilter[sid]['framesRendered']
        sinfo.startframe = sessionFilter[sid]['startFrame']
        sinfo.endframe = sessionFilter[sid]['endFrame']
        #bpy.ore_sessions.append(sinfo)
        output.append(sinfo)
    return output

def doRefresh():
    sce = bpy.context.scene
    ore = sce.ore_render
    try:
        userproxy = xmlrpc.client.ServerProxy(r'https://xmlrpc.renderfarm.fi/user')
        sessions = userproxy.user.getAllSessions(ore.username, ore.hash, 'completed')
        bpy.ore_sessions = []
        bpy.ore_sessions = xmlSessionsToOreSessions(sessions, 'completed')
        bpy.ore_completed_sessions = bpy.ore_sessions
        bpy.ore_cancelled_sessions = xmlSessionsToOreSessions(sessions, 'canceled')
        sessions = userproxy.user.getAllSessions(ore.username, ore.hash, 'accept')
        bpy.ore_pending_sessions = xmlSessionsToOreSessions(sessions, 'accept')
        sessions = userproxy.user.getAllSessions(ore.username, ore.hash, 'active')
        bpy.ore_active_sessions = xmlSessionsToOreSessions(sessions, 'active')
        
        updateCompleteSessionList(ore)
        
        return 0
    except xmlrpc.client.Error as v:
        self.report({'WARNING'}, "Error at refresh")
        print(v)
        return 1

class ORE_RefreshOp(bpy.types.Operator):
    bl_idname = 'ore.refresh_session_list'
    bl_label = 'Refresh'
    
    def execute(self, context):
        result = doRefresh()
        if (result == 0):
            return {'FINISHED'}
        else:
            return {'CANCELLED'}

def updateSessionList(session_list, ore):
    while(len(session_list) > 0):
        session_list.remove(0)
    
    for s in bpy.ore_active_session_queue:
        session_list.add()
        session = session_list[-1]
        session.name = s.title + ' [' + str(s.percentageComplete()) + '% complete]'

def updateCompleteSessionList(ore):
    all_sessions = []
    
    bpy.ore_active_session_queue = bpy.ore_cancelled_sessions
    updateSessionList(ore.rejected_sessions, ore)
    bpy.ore_active_session_queue = bpy.ore_active_sessions
    updateSessionList(ore.active_sessions, ore)
    bpy.ore_active_session_queue = bpy.ore_pending_sessions
    updateSessionList(ore.pending_sessions, ore)
    bpy.ore_active_session_queue = bpy.ore_completed_sessions
    updateSessionList(ore.completed_sessions, ore)
    
    bpy.ore_complete_session_queue = []
    bpy.ore_complete_session_queue.extend(bpy.ore_pending_sessions)
    bpy.ore_complete_session_queue.extend(bpy.ore_active_sessions)
    #bpy.ore_complete_session_queue.extend(bpy.ore_completed_sessions)
    #bpy.ore_complete_session_queue.extend(bpy.ore_cancelled_sessions)
    
    bpy.ore_active_session_queue = bpy.ore_complete_session_queue
    updateSessionList(ore.all_sessions, ore)

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
        if len(bpy.ore_complete_session_queue)>0:
            s = bpy.ore_complete_session_queue[ore.selected_session]
            try:
                userproxy.user.cancelSession(ore.username, ore.hash, int(s.id))
                doRefresh()
                self.report(set(['INFO']), 'Session ' + s.title + ' with id ' + s.id + ' cancelled')
            except:
                self.report(set(['ERROR']), 'Could not cancel session ' + s.title + ' with id ' + s.id)
                bpy.cancelError = True
                bpy.errorStartTime = time.time()
        
        return {'FINISHED'}

class ORE_GetCompletedSessions(bpy.types.Operator):
    bl_idname = 'ore.completed_sessions'
    bl_label = 'Completed sessions'
    
    def execute(self, context):
        sce = context.scene
        ore = sce.ore_render
        bpy.queue_selected = 1
        bpy.ore_active_session_queue = bpy.ore_completed_sessions
        updateSessionList(completed_sessions, ore)
        
        return {'FINISHED'}

class ORE_GetCancelledSessions(bpy.types.Operator):
    bl_idname = 'ore.cancelled_sessions'
    bl_label = 'Cancelled sessions'
    
    def execute(self, context):
        sce = context.scene
        ore = sce.ore_render
        bpy.queue_selected = 4
        bpy.ore_active_session_queue = bpy.ore_cancelled_sessions
        updateSessionList(cancelled_sessions, ore)
        
        return {'FINISHED'}

class ORE_GetActiveSessions(bpy.types.Operator):
    bl_idname = 'ore.active_sessions'
    bl_label = 'Rendering sessions'
    
    def execute(self, context):
        sce = context.scene
        ore = sce.ore_render
        bpy.queue_selected = 2
        bpy.ore_active_session_queue = bpy.ore_active_sessions
        updateSessionList(active_sessions, ore)
        
        return {'FINISHED'}

class ORE_GetPendingSessions(bpy.types.Operator):
    bl_idname = 'ore.accept_sessions' # using ORE lingo in API. acceptQueue is session waiting for admin approval
    bl_label = 'Pending sessions'
    
    def execute(self, context):
        sce = context.scene
        ore = sce.ore_render
        bpy.queue_selected = 3
        bpy.ore_active_session_queue = bpy.ore_pending_sessions
        updateSessionList(pending_sessions, ore)
        
        return {'FINISHED'}

class ORE_CheckUpdate(bpy.types.Operator):
    bl_idname = 'ore.check_update'
    bl_label = 'Check for a new version'
    
    def execute(self, context):
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
    bl_label = 'Login'
    
    def execute(self, context):
        sce = context.scene
        ore = sce.ore_render
        
        if ore.hash=='':
            if ore.password != '' and ore.username != '':
                ore.hash = hashlib.md5(ore.password.encode() + ore.username.encode()).hexdigest()
                ore.password = ''
                ore.loginInserted = False
        
        try:
            userproxy = xmlrpc.client.ServerProxy(r'https://xmlrpc.renderfarm.fi/user')
            sessions = userproxy.user.getAllSessions(ore.username, ore.hash, 'completed')
            bpy.ore_sessions = xmlSessionsToOreSessions(sessions, 'completed')
            bpy.ore_completed_sessions = bpy.ore_sessions
            bpy.ore_cancelled_sessions = xmlSessionsToOreSessions(sessions, 'canceled')
            sessions = userproxy.user.getAllSessions(ore.username, ore.hash, 'accept')
            bpy.ore_pending_sessions = xmlSessionsToOreSessions(sessions, 'accept')
            sessions = userproxy.user.getAllSessions(ore.username, ore.hash, 'active')
            bpy.ore_active_sessions = xmlSessionsToOreSessions(sessions, 'active')
            
            bpy.ore_active_session_queue = bpy.ore_completed_sessions
            updateSessionList(ore.completed_sessions, ore)
            
            bpy.ore_active_session_queue = bpy.ore_pending_sessions
            updateSessionList(ore.pending_sessions, ore)
            
            bpy.ore_active_session_queue = bpy.ore_active_sessions
            updateSessionList(ore.active_sessions, ore)
            
            bpy.ore_active_session_queue = bpy.ore_cancelled_sessions
            updateSessionList(ore.rejected_sessions, ore)
            
            ore.passwordCorrect = True
            ore.loginInserted = True
            
        except xmlrpc.client.Error as v:
            bpy.ready = False
            ore.loginInserted = False
            ore.passwordCorrect = False
            ore.hash = ''
            ore.password = ''
            self.report({'WARNING'}, "Incorrect login")
            print(v)
            return {'CANCELLED'}
        
        all_sessions = []
        bpy.ore_complete_session_queue = []
        
        bpy.ore_complete_session_queue.extend(bpy.ore_pending_sessions)
        bpy.ore_complete_session_queue.extend(bpy.ore_active_sessions)
        #bpy.ore_complete_session_queue.extend(bpy.ore_completed_sessions)
        #bpy.ore_complete_session_queue.extend(bpy.ore_cancelled_sessions)
        
        bpy.ore_active_session_queue = bpy.ore_complete_session_queue
        updateSessionList(ore.all_sessions, ore)
        
        return {'FINISHED'}

class ORE_ResetOp(bpy.types.Operator):
    bl_idname = "ore.reset"
    bl_label = "Reset Preparation"
    
    def execute(self, context):
        sce = context.scene
        ore = sce.ore_render
        ore.prepared = False
        ore.loginInserted = False
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
        prepareScene()
        
        returnValue = ore_upload(self, context)
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

class ORE_ChangeUser(bpy.types.Operator):
    bl_idname = "ore.change_user"
    bl_label = "Change user"
    
    def execute(self, context):
        ore = context.scene.ore_render
        ore.password = ''
        ore.hash = ''
        ore.passwordCorrect = False
        ore.loginInserted = False
        
        return {'FINISHED'}

class RenderfarmFi(bpy.types.RenderEngine):
    bl_idname = 'RENDERFARMFI_RENDER'
    bl_label = "Renderfarm.fi"

    def render(self, scene):
        print('Do test renders with Blender Render')


#~ def menu_export(self, context):
    #~ import os
    #~ default_path = os.path.splitext(bpy.data.filepath)[0] + ".py"
    #~ self.layout.operator(RenderfarmFi.bl_idname, text=RenderfarmFi.bl_label)


def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.ore_render = PointerProperty(type=ORESettings, name='ORE Render', description='ORE Render Settings')

    #~ bpy.types.INFO_MT_render.append(menu_export)

def unregister():
    bpy.utils.unregister_module(__name__)

    #~ bpy.types.INFO_MT_render.remove(menu_export)

if __name__ == "__main__":
    register()
