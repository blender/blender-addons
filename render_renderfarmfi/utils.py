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

import imp

from os.path import join

import bpy

from .ore_session import OreSession

def _write_credentials(hash, user):
    with open(join(bpy.utils.user_resource('CONFIG', 'rffi', True), 'rffi_credentials.py'), 'w') as pwfile:
        pwfile.write('hash=\''+hash+'\'\n')
        pwfile.write('user=\''+user+'\'')


def _read_credentials():
    bpy.rffi_creds_found = False
    bpy.rffi_user = ''
    bpy.rffi_hash = ''

    pwfile = bpy.utils.user_resource('CONFIG', 'rffi', True)
    try:
        pwmod = imp.find_module('rffi_credentials',[pwfile])
    except ImportError:
        _write_credentials('', '')
        pwmod = imp.find_module('rffi_credentials',[pwfile])
    try:
        user_creds = imp.load_module('rffi_credentials', pwmod[0], pwmod[1], pwmod[2])
        bpy.rffi_user = user_creds.user
        bpy.rffi_hash = user_creds.hash
        bpy.rffi_creds_found = True
    except ImportError:
        # doesn't exist yet, write template
        _write_credentials('', '')
        pwfile = bpy.utils.user_resource('CONFIG', 'rffi', True)
        pwmod = imp.find_module('rffi_credentials',[pwfile])
        try:
            user_creds = imp.load_module('rffi_credentials', pwmod[0], pwmod[1], pwmod[2])
            bpy.rffi_user = user_creds.user
            bpy.rffi_hash = user_creds.hash
            bpy.rffi_creds_found = True
        except Exception as e2:
            print("Couldn't write rffi_credentials.py", e2)
    finally:
        if pwmod and pwmod[0]: pwmod[0].close()

    return bpy.rffi_creds_found


def _xmlsessions_to_oresessions(sessions, stage=None):
    output = []
    for session in sessions:
        s = session['title']
        if stage:
            s = s + ' (' + stage + ')'
        sinfo = OreSession(session['sessionId'], s)
        if stage in {'Rendering', 'Completed', 'Active'}:
            sinfo.frames = session['framesRendered']
        sinfo.startframe = session['startFrame']
        sinfo.endframe = session['endFrame']
        output.append(sinfo)
    return output


def update_session_list(session_list, ore):
    while(len(session_list) > 0):
        session_list.remove(0)

    for s in bpy.ore_active_session_queue:
        session_list.add()
        session = session_list[-1]
        session.name = s.title + ' [' + str(s.percentageComplete()) + '% complete]'

def update_complete_session_list(ore):
    bpy.ore_active_session_queue = bpy.ore_cancelled_sessions
    update_session_list(ore.rejected_sessions, ore)
    bpy.ore_active_session_queue = bpy.ore_active_sessions
    update_session_list(ore.active_sessions, ore)
    bpy.ore_active_session_queue = bpy.ore_pending_sessions
    update_session_list(ore.pending_sessions, ore)
    bpy.ore_active_session_queue = bpy.ore_completed_sessions
    update_session_list(ore.completed_sessions, ore)

    bpy.ore_complete_session_queue = []
    bpy.ore_complete_session_queue.extend(bpy.ore_pending_sessions)
    bpy.ore_complete_session_queue.extend(bpy.ore_active_sessions)
    bpy.ore_complete_session_queue.extend(bpy.ore_completed_sessions)
    bpy.ore_complete_session_queue.extend(bpy.ore_cancelled_sessions)

    bpy.ore_active_session_queue = bpy.ore_complete_session_queue
    update_session_list(ore.all_sessions, ore)

def check_status(ore):
    bpy.errors = []

    if bpy.rffi_creds_found == False and bpy.rffi_hash == '':
        bpy.errors.append('missing_creds')

    if '' in {ore.title, ore.longdesc, ore.shortdesc}:
        bpy.errors.append('missing_desc')
        bpy.infoError = True

    set_status('username', bpy.rffi_hash=='' and ore.username=='')
    set_status('password', bpy.rffi_hash=='' and ore.password=='')

    set_status('title', ore.title=='')
    set_status('longdesc', ore.longdesc=='')
    set_status('shortdesc', ore.shortdesc=='')


def set_status(property, status):
    if status:
        bpy.statusMessage[property] = 'ERROR'
    else:
        bpy.statusMessage[property] = 'TRIA_RIGHT'

def show_status(layoutform, property, message):
    if bpy.statusMessage[property] == 'ERROR':
        layoutform.label(text='', icon='ERROR')

