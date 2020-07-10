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
"name": "Grease Pencil Tools",
"description": "Pack of tools for Grease pencil drawing",
"author": "Samuel Bernou",
"version": (0, 0, 5),
"blender": (2, 83, 0),
"location": "sidebar (N) > Grease pencil > Grease pencil",
"warning": "",
"doc_url": "https://github.com/Pullusb/greasepencil-addon",
"tracker_url": "https://github.com/Pullusb/greasepencil-addon/issues",
"category": "Object",
# "support": "COMMUNITY",
}


from .  import (prefs,
                box_deform,
                line_reshape,
                ui_panels,
                )

def register():
    prefs.register()
    box_deform.register()
    line_reshape.register()
    ui_panels.register()

def unregister():
    ui_panels.unregister()
    box_deform.unregister()
    line_reshape.unregister()
    prefs.unregister()

if __name__ == "__main__":
    register()