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

import json
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import requests
import threading
import blenderkit
from blenderkit import tasks_queue, utils, paths, search

CLIENT_ID = "IdFRwa3SGA8eMpzhRVFMg5Ts8sPK93xBjif93x0F"
PORTS = [62485, 1234]


class SimpleOAuthAuthenticator(object):
    def __init__(self, server_url, client_id, ports):
        self.server_url = server_url
        self.client_id = client_id
        self.ports = ports

    def _get_tokens(self, authorization_code=None, refresh_token=None, grant_type="authorization_code"):
        data = {
            "grant_type": grant_type,
            "state": "random_state_string",
            "client_id": self.client_id,
            "scopes": "read write",
        }
        if authorization_code:
            data['code'] = authorization_code
        if refresh_token:
            data['refresh_token'] = refresh_token

        response = requests.post(
            '%s/o/token/' % self.server_url,
            data=data
        )
        if response.status_code != 200:
            return None, None
        refresh_token = json.loads(response.content)['refresh_token']
        access_token = json.loads(response.content)['access_token']
        return access_token, refresh_token

    def get_new_token(self):
        class HTTPServerHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                if 'code' in self.path:
                    self.auth_code = self.path.split('=')[1]
                    # Display to the user that they no longer need the browser window
                    self.wfile.write(bytes('<html><h1>You may now close this window.</h1></html>', 'utf-8'))
                    qs = parse_qs(urlparse(self.path).query)
                    self.server.authorization_code = qs['code'][0]

        for port in self.ports:
            try:
                httpServer = HTTPServer(('localhost', port), HTTPServerHandler)
            except OSError:
                continue
            break
        webbrowser.open_new(
            "%s/o/authorize?client_id=%s&state=random_state_string&response_type=code&"
            "redirect_uri=http://localhost:%s/consumer/exchange/" % (self.server_url, self.client_id, port),
        )

        httpServer.handle_request()
        authorization_code = httpServer.authorization_code
        return self._get_tokens(authorization_code=authorization_code)

    def get_refreshed_token(self, refresh_token):
        return self._get_tokens(refresh_token=refresh_token, grant_type="refresh_token")


def login_thread():
    thread = threading.Thread(target=login, args=([]), daemon=True)
    thread.start()


def login():
    authenticator = SimpleOAuthAuthenticator(server_url=paths.get_bkit_url(), client_id=CLIENT_ID, ports=PORTS)
    auth_token, refresh_token = authenticator.get_new_token()
    utils.p('tokens retrieved')
    tasks_queue.add_task((write_tokens , (auth_token, refresh_token)))


def refresh_token_thread():
    preferences = bpy.context.preferences.addons['blenderkit'].preferences
    if len(preferences.api_key_refresh) > 0:
        thread = threading.Thread(target=refresh_token, args=([preferences.api_key_refresh]), daemon=True)
        thread.start()


def refresh_token(api_key_refresh):
    authenticator = SimpleOAuthAuthenticator(server_url=paths.get_bkit_url(), client_id=CLIENT_ID, ports=PORTS)
    auth_token, refresh_token = authenticator.get_refreshed_token(api_key_refresh)
    if auth_token is not None and refresh_token is not None:
        tasks_queue.add_task((blenderkit.oauth.write_tokens , (auth_token, refresh_token)))


def write_tokens(auth_token, refresh_token):
    utils.p('writing tokens')
    preferences = bpy.context.preferences.addons['blenderkit'].preferences
    preferences.api_key_refresh = refresh_token
    preferences.api_key = auth_token
    preferences.login_attempt = False
    props = utils.get_search_props()
    props.report = 'Login success!'
    search.get_profile()


class RegisterLoginOnline(bpy.types.Operator):
    """Bring linked object hierarchy to scene and make it editable."""

    bl_idname = "wm.blenderkit_login"
    bl_label = "BlenderKit login or signup"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        preferences = bpy.context.preferences.addons['blenderkit'].preferences
        preferences.login_attempt = True
        login_thread()
        return {'FINISHED'}


class Logout(bpy.types.Operator):
    """Bring linked object hierarchy to scene and make it editable."""

    bl_idname = "wm.blenderkit_logout"
    bl_label = "BlenderKit logout"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        preferences = bpy.context.preferences.addons['blenderkit'].preferences
        preferences.login_attempt = False
        preferences.api_key_refresh = ''
        preferences.api_key = ''
        return {'FINISHED'}


class CancelLoginOnline(bpy.types.Operator):
    """Cancel login attempt."""

    bl_idname = "wm.blenderkit_login_cancel"
    bl_label = "BlenderKit login cancel"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        preferences = bpy.context.preferences.addons['blenderkit'].preferences
        preferences.login_attempt = False
        return {'FINISHED'}

classess = (
    RegisterLoginOnline,
    CancelLoginOnline,
    Logout,
)


def register():
    for c in classess:
        bpy.utils.register_class(c)


def unregister():
    for c in classess:
        bpy.utils.unregister_class(c)
