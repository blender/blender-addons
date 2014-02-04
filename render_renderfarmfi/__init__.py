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
    "author": "Nathan Letwory <nathan@letworyinteractive.com>, "
        "Jesse Kaukonen <jesse.kaukonen@gmail.com>",
    "version": (23,),
    "blender": (2, 63, 0),
    "location": "Render > Engine > Renderfarm.fi",
    "description": "Send .blend as session to http://www.renderfarm.fi to render",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"
        "Scripts/Render/Renderfarm.fi",
    "tracker_url": "https://developer.blender.org/T22927",
    "category": "Render"}

"""
Copyright 2009-2013 Laurea University of Applied Sciences
Authors: Nathan Letwory, Jesse Kaukonen
"""

import bpy
import hashlib
import http.client
import math
from os.path import isabs, isfile, join, exists
import os
import time

from bpy.props import PointerProperty, StringProperty, BoolProperty, EnumProperty, IntProperty, CollectionProperty

from .panels import *
from .operators import *
from .rpc import RffiRpc

bpy.CURRENT_VERSION = bl_info["version"][0]
bpy.found_newer_version = False
bpy.up_to_date = False
bpy.download_location = 'http://www.renderfarm.fi/blender'

bpy.rffi_creds_found = False
bpy.rffi_user = ''
bpy.rffi_hash = ''
bpy.passwordCorrect = False
bpy.loginInserted = False
bpy.rffi_accepting = False
bpy.rffi_motd = ''

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
try:
    bpy.originalFileName = bpy.data.filepath
except:
    bpy.originalFileName = 'untitled.blend'
bpy.particleBakeWarning = False
bpy.childParticleWarning = False
bpy.simulationWarning = False
bpy.file_format_warning = False
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

    shortdesc = StringProperty(name='Short description', description='A short description of the scene (100 characters)', maxlen=101, default='-')
    tags = StringProperty(name='Tags', description='A list of tags that best suit the animation', maxlen=102, default='')
    longdesc = StringProperty(name='Description', description='Description of the scene (2k)', maxlen=2048, default='')
    title = StringProperty(name='Title', description='Title for this session (128 characters)', maxlen=128, default='')
    url = StringProperty(name='Project URL', description='Project URL. Leave empty if not applicable', maxlen=256, default='')
    engine = StringProperty(name='Engine', description='The rendering engine that is used for rendering', maxlen=64, default='blender')
    samples = IntProperty(name='Samples', description='Number of samples that is used (Cycles only)', min=1, max=1000000, soft_min=1, soft_max=100000, default=100)
    subsamples = IntProperty(name='Subsample Frames', description='Number of subsample frames that is used (Cycles only)', min=1, max=1000000, soft_min=1, soft_max=1000, default=10)
    file_format = StringProperty(name='File format', description='File format used for the rendering', maxlen=30, default='PNG_FORMAT')

    parts = IntProperty(name='Parts/Frame', description='', min=1, max=1000, soft_min=1, soft_max=64, default=1)
    resox = IntProperty(name='Resolution X', description='X of render', min=1, max=10000, soft_min=1, soft_max=10000, default=1920)
    resoy = IntProperty(name='Resolution Y', description='Y of render', min=1, max=10000, soft_min=1, soft_max=10000, default=1080)
    memusage = IntProperty(name='Memory Usage', description='Estimated maximum memory usage during rendering in MB', min=1, max=6*1024, soft_min=1, soft_max=3*1024, default=256)
    start = IntProperty(name='Start Frame', description='Start Frame', default=1)
    end = IntProperty(name='End Frame', description='End Frame', default=250)
    fps = IntProperty(name='FPS', description='FPS', min=1, max=120, default=25)

    prepared = BoolProperty(name='Prepared', description='Set to True if preparation has been run', default=False)
    debug = BoolProperty(name='Debug', description='Verbose output in console', default=False)
    selected_session = IntProperty(name='Selected Session', description='The selected session', default=0)
    hasUnsupportedSimulation = BoolProperty(name='HasSimulation', description='Set to True if therea re unsupported simulations', default=False)

    inlicense = EnumProperty(items=licenses, name='Scene license', description='License speficied for the source files', default='1')
    outlicense = EnumProperty(items=licenses, name='Product license', description='License speficied for the output files', default='1')
    sessions = CollectionProperty(type=ORESession, name='Sessions', description='Sessions on Renderfarm.fi')
    completed_sessions = CollectionProperty(type=ORESession, name='Completed sessions', description='Sessions that have been already rendered')
    rejected_sessions = CollectionProperty(type=ORESession, name='Rejected sessions', description='Sessions that have been rejected')
    pending_sessions = CollectionProperty(type=ORESession, name='Pending sessions', description='Sessions that are waiting for approval')
    active_sessions = CollectionProperty(type=ORESession, name='Active sessions', description='Sessions that are currently rendering')
    all_sessions = CollectionProperty(type=ORESession, name='All sessions', description='List of all of the users sessions')

# session struct


class RENDERFARM_MT_Session(bpy.types.Menu):
    bl_label = "Show Session"

    def draw(self, context):
        layout = self.layout
        ore = context.scene.ore_render

        if (bpy.loginInserted == True):
            layout.operator('ore.completed_sessions')
            layout.operator('ore.accept_sessions')
            layout.operator('ore.active_sessions')
            layout.separator()
            layout.operator('ore.cancelled_sessions')
        else:
            row = layout.row()
            row.label(text="You must login first")


class RenderfarmFi(bpy.types.RenderEngine):
    bl_idname = 'RENDERFARMFI_RENDER'
    bl_label = "Renderfarm.fi"

    def render(self, scene):
        print('Do test renders with Blender Render')

def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.ore_render = PointerProperty(type=ORESettings, name='ORE Render', description='ORE Render Settings')

def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()

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
