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

# mainly update functions and callbacks for ratings properties, here to avoid circular imports.
import bpy
from blenderkit import utils, paths, tasks_queue, rerequests



from blenderkit import rerequests
user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
api_key = user_preferences.api_key
headers = utils.get_headers(api_key)
r = rerequests.get(f"{api_url}/comments/assets-uuidasset/{asset_data['assetBaseId']}/", headers = headers)
r= r.json()
print(r)


def store_comments_local(asset_id, type='quality', value=0):
    context = bpy.context
    ar   = context.window_manager['asset comments']
    ar[asset_id] = ar.get(asset_id, {})
    ar[asset_id][type] = value

def get_comments(asset_id, headers):
    '''
    Retrieve ratings from BlenderKit server. Can be run from a thread
    Parameters
    ----------
    asset_id
    headers

    Returns
    -------
    ratings - dict of type:value ratings
    '''
    url = paths.get_api_url() + 'comments/assets-uuidasset/' + asset_id + '/'
    params = {}
    r = rerequests.get(url, params=params, verify=True, headers=headers)
    if r is None:
        return
    if r.status_code == 200:
        rj = r.json()
        comments = []
        # store comments - send them to task queue

        tasks_queue.add_task((store_comments_local,(asset_id, rj['results'])))

        # if len(rj['results'])==0:
        #     # store empty ratings too, so that server isn't checked repeatedly
        #     tasks_queue.add_task((store_rating_local_empty,(asset_id,)))
        # return ratings
