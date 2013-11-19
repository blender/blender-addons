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

import xmlrpc.client
import imp
import time
import bpy

from .exceptions import LoginFailedException, SessionCancelFailedException, \
                        GetSessionsFailedException
from .utils import _read_credentials, _xmlsessions_to_oresessions, \
                    update_complete_session_list

def _is_dev():
    is_dev = False
    pwfile = bpy.utils.user_resource('CONFIG', 'rffi', True)
    pwmod = None
    try:
        pwmod = imp.find_module('rffi_dev',[pwfile])
        try:
            user_creds = imp.load_module('rffi_dev', pwmod[0], pwmod[1], pwmod[2])
            if 'dev' in dir(user_creds) and user_creds.dev:
                is_dev = True
        except ImportError:
            is_dev = False
        finally:
            if pwmod and pwmod[0]: pwmod[0].close()
    except ImportError:
        is_dev = False
    finally:
        if pwmod and pwmod[0]: pwmod[0].close()

    return is_dev

def _be_verbose():
    be_verbose = False
    pwfile = bpy.utils.user_resource('CONFIG', 'rffi', True)
    pwmod = None
    try:
        pwmod = imp.find_module('rffi_dev',[pwfile])
        try:
            user_creds = imp.load_module('rffi_dev', pwmod[0], pwmod[1], pwmod[2])
            if 'verbose' in dir(user_creds) and user_creds.verbose:
                be_verbose = True
        except ImportError:
            be_verbose = False
        finally:
            if pwmod and pwmod[0]: pwmod[0].close()
    except ImportError:
        be_verbose = False
    finally:
        if pwmod and pwmod[0]: pwmod[0].close()

    return be_verbose

RFFI_DEV = _is_dev()
RFFI_VERBOSE = _be_verbose()

if RFFI_DEV:
    print("DEVELOPER MODE")
    rffi_xmlrpc_secure = r'http://renderfarm.server/burp/xmlrpc'
    rffi_xmlrpc = r'http://renderfarm.server/burp/xmlrpc'
    rffi_xmlrpc_upload = 'renderfarm.server'
else:
    rffi_xmlrpc_secure = r'http://xmlrpc.renderfarm.fi/burp/xmlrpc'
    rffi_xmlrpc = r'http://xmlrpc.renderfarm.fi/burp/xmlrpc'
    rffi_xmlrpc_upload = 'xmlrpc.renderfarm.fi'


def _get_proxy():
    proxy = xmlrpc.client.ServerProxy(rffi_xmlrpc, verbose=RFFI_VERBOSE)
    return proxy

def _get_secure_proxy():
    proxy = xmlrpc.client.ServerProxy(rffi_xmlrpc_secure, verbose=RFFI_VERBOSE)
    return proxy

def _do_refresh(op, rethrow=False, print_errors=True):
    sce = bpy.context.scene
    ore = sce.ore_render

    if _read_credentials():
        try:
            bpy.ore_sessions = []
            bpy.ore_pending_sessions = []
            bpy.ore_active_sessions = []
            bpy.ore_completed_sessions = []
            bpy.ore_cancelled_sessions = []
            update_complete_session_list(ore)

            res = rffi.login(op, True, print_errors)
            userid = res['userID']

            sessions = rffi.get_sessions(userid, 'accept', 0, 100, 'full')
            bpy.ore_sessions = _xmlsessions_to_oresessions(sessions, stage='Pending')
            bpy.ore_pending_sessions = bpy.ore_sessions

            sessions = rffi.get_sessions(userid, 'completed', 0, 100, 'full')
            bpy.ore_sessions = _xmlsessions_to_oresessions(sessions, stage='Completed')
            bpy.ore_completed_sessions = bpy.ore_sessions

            sessions = rffi.get_sessions(userid, 'cancelled', 0, 100, 'full')
            bpy.ore_sessions = _xmlsessions_to_oresessions(sessions, stage='Cancelled')
            bpy.ore_cancelled_sessions = bpy.ore_sessions

            sessions = rffi.get_sessions(userid, 'render', 0, 100, 'full')
            bpy.ore_sessions = _xmlsessions_to_oresessions(sessions, stage='Rendering')
            bpy.ore_active_sessions = bpy.ore_sessions

            update_complete_session_list(ore)

            return 0
        except LoginFailedException as lfe:
            if print_errors: print("_do_refresh login failed", lfe)
            if rethrow:
                raise lfe
            return 1
    else:
        return 1


class RffiRpc(object):
    def __init__(self):
        self.proxy = _get_proxy()
        self.sproxy = _get_secure_proxy()
        self.res = None

    def login(self, op, rethrow=False, print_errors=True):
        self.res = None

        if bpy.rffi_user=='':
            raise LoginFailedException("No email address given")

        if bpy.rffi_hash=='':
            raise LoginFailedException("No password given")

        try:
            self.res = self.sproxy.auth.getSessionKey(bpy.rffi_user, bpy.rffi_hash)
        except xmlrpc.client.Error as v:
            if op: op.report({'WARNING'}, "Error at login : " + str(type(v)) + " -> " + str(v.faultCode) + ": " + v.faultString)
            if print_errors: print("Error at login: ",v)
            if rethrow:
                vstr = str(v)
                if "Failed to invoke method getSessionKey" in vstr:
                    raise LoginFailedException('User '+bpy.rffi_user+' doesn\'t exist')
                raise LoginFailedException(v.faultString)
            return None
        except Exception as v:
            if op: op.report({'WARNING'}, "Non XMLRPC Error at login: " + str(v))
            if print_errors: print(v)
            if rethrow:
                raise LoginFailedException(str(v))
            return None
        return self.res

    def get_sessions(self, user, queue, start, end, level):
        try:
            sessions = self.proxy.session.getSessions(user, queue, start, end, level)
        except xmlrpc.client.Error as v:
            raise GetSessionsFailedException(str(v))
        return sessions

    def cancel_session(self, op, session):
        res = self.login(op)
        if res:
            try:
                key = res['key']
                userid = res['userId']
                res = self.proxy.session.cancelSession(userid, key, session.id)
                _do_refresh(op, True)
                op.report({'INFO'}, 'Session ' + session.title + ' with id ' + str(session.id) + ' cancelled')
            except xmlrpc.client.Error as v:
                op.report({'ERROR'}, 'Could not cancel session ' + session.title + ' with id ' + str(session.id))
                bpy.cancelError = True
                bpy.errorStartTime = time.time()
                raise SessionCancelFailedException(str(v))

    def check_status(self):
        res = self.proxy.service.motd()
        bpy.rffi_accepting = res['accepting']
        bpy.rffi_motd = res['motd']

rffi = RffiRpc()
