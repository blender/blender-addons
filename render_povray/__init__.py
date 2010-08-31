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
    "name": "PovRay",
    "author": "Campbell Barton",
    "version": (0,1),
    "blender": (2, 5, 4),
    "api": 31667,
    "location": "Info Header (engine dropdown)",
    "description": "Basic povray integration for blender",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"\
        "Scripts/Render/PovRay",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=23145&group_id=153&atid=469",
    "category": "Render"}

try:
    init_data

    reload(render)
    reload(ui)
except:
    from render_povray import render
    from render_povray import ui

init_data = True

def register():
    pass


def unregister():
    pass


if __name__ == "__main__":
    register()
