# -*- coding:utf-8 -*-

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
    "name": "Delaunay Voronoi",
    "description": "Points cloud Delaunay triangulation in 2.5D "
                  "(suitable for terrain modelling) or Voronoi diagram in 2D",
    "author": "Domlysz, Oscurart",
    "version": (1, 3),
    "blender": (2, 7, 0),
    "location": "View3D > Tools > GIS",
    "warning": "",
    "wiki_url": "https://github.com/domlysz/BlenderGIS/wiki",
    "tracker_url": "",
    "category": ""
    }

if "bpy" in locals():
    import importlib
    importlib.reload(oscurart_constellation)

else:
    from . import oscurart_constellation

import bpy
from .delaunayVoronoiBlender import ToolsPanelDelaunay


# Register
def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)
