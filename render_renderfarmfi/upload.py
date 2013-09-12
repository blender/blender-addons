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
import http.client
import hashlib
from os.path import isabs, isfile
import time

import bpy

from .utils import _read_credentials
from .rpc import rffi, _do_refresh, rffi_xmlrpc_upload, rffi_xmlrpc, RFFI_VERBOSE

def _random_string(length):
    import string
    import random
    return ''.join(random.choice(string.ascii_letters) for ii in range(length + 1))

def _encode_multipart_data(data, files):
    boundary = _random_string(30)

    def get_content_type(filename):
        return 'application/octet-stream' # default this

    def encode_field(field_name):
        return ('--' + boundary,
                'Content-Disposition: form-data; name="%s"' % field_name,
                '', str(data[field_name]))

    def encode_file(field_name):
        filename = files [field_name]
        fcontent = None
        print('encoding', field_name)
        try:
            fcontent = str(open(filename, 'rb').read(), encoding='iso-8859-1')
        except Exception as e:
            print('Trouble in paradise', e)
        return ('--' + boundary,
                'Content-Disposition: form-data; name="%s"; filename="%s"' % (field_name, filename),
                'Content-Type: %s' % get_content_type(filename),
                '', fcontent)

    lines = []
    for name in data:
        lines.extend(encode_field(name))
    for name in files:
        lines.extend(encode_file(name))
    lines.extend(('--%s--' % boundary, ''))
    print("joining lines into body")
    body = '\r\n'.join(lines)

    headers = {'content-type': 'multipart/form-data; boundary=' + boundary,
               'content-length': str(len(body))}

    print("headers and body ready")

    return body, headers

def _send_post(data, files):
    print("Forming connection for post")
    connection = http.client.HTTPConnection(rffi_xmlrpc_upload)
    print("Requesting")
    connection.request('POST', '/burp/storage', *_encode_multipart_data(data, files)) # was /file
    print("Getting response")
    response = connection.getresponse()
    print("Reading response")
    res = response.read()
    return res

def _md5_for_file(filepath):
    md5hash = hashlib.md5()
    blocksize = 0x10000
    f = open(filepath, "rb")
    while True:
        data = f.read(blocksize)
        if not data:
            break
        md5hash.update(data)
    return md5hash.hexdigest()

def _upload_file(key, userid, sessionid, path):
    print("Asserting absolute path")
    assert isabs(path)
    print("Asserting path is a file")
    assert isfile(path)
    data = {
        'userId': str(userid),
        'sessionKey': key,
        'sessionId': sessionid,
        'md5sum': _md5_for_file(path)
    }
    files = {
        'blenderfile': path
    }
    r = _send_post(data, files)

    return r

def _run_upload(key, userid, sessionid, path):
    print("Starting upload");
    r = _upload_file(key, userid, sessionid, path)
    print("Upload finished")
    o = xmlrpc.client.loads(r)
    print("Loaded xmlrpc response")
    return o[0][0]

def _ore_upload(op, context):
    sce = context.scene
    ore = sce.ore_render

    if not bpy.ready:
        op.report({'ERROR'}, 'Your user or scene information is not complete')
        bpy.infoError = True
        bpy.errorStartTime = time.time()
        bpy.context.scene.render.engine = 'RENDERFARMFI_RENDER'
        return {'CANCELLED'}
    try:
        _read_credentials()
        res = rffi.login(op, True)
        key = res['key']
        userid = res['userId']
        print("Creating server proxy")
        proxy = xmlrpc.client.ServerProxy(rffi_xmlrpc, verbose=RFFI_VERBOSE)
        proxy._ServerProxy__transport.user_agent = 'Renderfarm.fi Uploader/%s' % (bpy.CURRENT_VERSION)
        print("Creating a new session")
        res = proxy.session.createSession(userid, key)  # This may use an existing, non-rendered session. Prevents spamming in case the upload fails for some reason
        sessionid = res['sessionId']
        key = res['key']
        print("Session id is " + str(sessionid))
        res = _run_upload(key, userid, sessionid, bpy.data.filepath)
        print("Getting fileid from xmlrpc response data")
        fileid = int(res['fileId'])
        print("Sending session details for session " + str(sessionid) + " with fileid " + str(fileid))
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
        res = proxy.session.setFrameFormat(userid, res['key'], sessionid, ore.file_format)
        res = proxy.session.setRenderer(userid, res['key'], sessionid, ore.engine)
        res = proxy.session.setSamples(userid, res['key'], sessionid, ore.samples)
        res = proxy.session.setSubSamples(userid, res['key'], sessionid, ore.subsamples)
        if (ore.engine == 'cycles'):
            res = proxy.session.setReplication(userid, res['key'], sessionid, 1)
            if ore.subsamples > 1:
                res = proxy.session.setStitcher(userid, res['key'], sessionid, 'AVERAGE')
        else:
            res = proxy.session.setReplication(userid, res['key'], sessionid, 3)
        res = proxy.session.setOutputLicense(userid, res['key'], sessionid, int(ore.outlicense))
        res = proxy.session.setInputLicense(userid, res['key'], sessionid, int(ore.inlicense))
        print("Setting primary input file")
        res = proxy.session.setPrimaryInputFile(userid, res['key'], sessionid, fileid)
        print("Submitting session")
        res = proxy.session.submit(userid, res['key'], sessionid)
        print("Session submitted")
        op.report({'INFO'}, 'Submission sent to Renderfarm.fi')
    except xmlrpc.client.Error as v:
        bpy.context.scene.render.engine = 'RENDERFARMFI_RENDER'
        print('ERROR:', v)
        op.report({'ERROR'}, 'An XMLRPC error occurred while sending submission to Renderfarm.fi')
    except Exception as e:
        bpy.context.scene.render.engine = 'RENDERFARMFI_RENDER'
        print('Unhandled error:', e)
        op.report({'ERROR'}, 'A generic error occurred while sending submission to Renderfarm.fi')

    bpy.context.scene.render.engine = 'RENDERFARMFI_RENDER'
    _do_refresh(op)
    return {'FINISHED'}


