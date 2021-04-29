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

#mainly update functions and callbacks for ratings properties, here to avoid circular imports.
import bpy

def update_ratings_quality(self, context):
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    api_key = user_preferences.api_key

    headers = utils.get_headers(api_key)
    asset = self.id_data
    if asset:
        bkit_ratings = asset.bkit_ratings
        url = paths.get_api_url() + 'assets/' + asset['asset_data']['id'] + '/rating/'
    else:
        # this part is for operator rating:
        bkit_ratings = self
        url = paths.get_api_url() + f'assets/{self.asset_id}/rating/'

    if bkit_ratings.rating_quality > 0.1:
        ratings = [('quality', bkit_ratings.rating_quality)]
        tasks_queue.add_task((send_rating_to_thread_quality, (url, ratings, headers)), wait=2.5, only_last=True)


def update_ratings_work_hours(self, context):
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    api_key = user_preferences.api_key
    headers = utils.get_headers(api_key)
    asset = self.id_data
    if asset:
        bkit_ratings = asset.bkit_ratings
        url = paths.get_api_url() + 'assets/' + asset['asset_data']['id'] + '/rating/'
    else:
        # this part is for operator rating:
        bkit_ratings = self
        url = paths.get_api_url() + f'assets/{self.asset_id}/rating/'

    if bkit_ratings.rating_work_hours > 0.45:
        ratings = [('working_hours', round(bkit_ratings.rating_work_hours, 1))]
        tasks_queue.add_task((send_rating_to_thread_work_hours, (url, ratings, headers)), wait=2.5, only_last=True)

def update_quality_ui(self, context):
    '''Converts the _ui the enum into actual quality number.'''
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    if user_preferences.api_key == '':
        # ui_panels.draw_not_logged_in(self, message='Please login/signup to rate assets.')
        # bpy.ops.wm.call_menu(name='OBJECT_MT_blenderkit_login_menu')
        # return
        bpy.ops.wm.blenderkit_login('INVOKE_DEFAULT',
                                    message='Please login/signup to rate assets. Clicking OK takes you to web login.')
        # self.rating_quality_ui = '0'
    self.rating_quality = int(self.rating_quality_ui)


def update_ratings_work_hours_ui(self, context):
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    if user_preferences.api_key == '':
        # ui_panels.draw_not_logged_in(self, message='Please login/signup to rate assets.')
        # bpy.ops.wm.call_menu(name='OBJECT_MT_blenderkit_login_menu')
        # return
        bpy.ops.wm.blenderkit_login('INVOKE_DEFAULT',
                                    message='Please login/signup to rate assets. Clicking OK takes you to web login.')
        # self.rating_work_hours_ui = '0'
    self.rating_work_hours = float(self.rating_work_hours_ui)


def update_ratings_work_hours_ui_1_5(self, context):
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    if user_preferences.api_key == '':
        # ui_panels.draw_not_logged_in(self, message='Please login/signup to rate assets.')
        # bpy.ops.wm.call_menu(name='OBJECT_MT_blenderkit_login_menu')
        # return
        bpy.ops.wm.blenderkit_login('INVOKE_DEFAULT',
                                    message='Please login/signup to rate assets. Clicking OK takes you to web login.')
        # self.rating_work_hours_ui_1_5 = '0'
    # print('updating 1-5')
    # print(float(self.rating_work_hours_ui_1_5))
    self.rating_work_hours = float(self.rating_work_hours_ui_1_5)


def update_ratings_work_hours_ui_1_10(self, context):
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    if user_preferences.api_key == '':
        # ui_panels.draw_not_logged_in(self, message='Please login/signup to rate assets.')
        # bpy.ops.wm.call_menu(name='OBJECT_MT_blenderkit_login_menu')
        # return
        bpy.ops.wm.blenderkit_login('INVOKE_DEFAULT',
                                    message='Please login/signup to rate assets. Clicking OK takes you to web login.')
        # self.rating_work_hours_ui_1_5 = '0'
    # print('updating 1-5')
    # print(float(self.rating_work_hours_ui_1_5))
    self.rating_work_hours = float(self.rating_work_hours_ui_1_10)


def stars_enum_callback(self, context):
    '''regenerates the enum property used to display rating stars, so that there are filled/empty stars correctly.'''
    items = []
    for a in range(0, 10):
        if self.rating_quality < a + 1:
            icon = 'SOLO_OFF'
        else:
            icon = 'SOLO_ON'
        # has to have something before the number in the value, otherwise fails on registration.
        items.append((f'{a + 1}', f'{a + 1}', '', icon, a + 1))
    return items