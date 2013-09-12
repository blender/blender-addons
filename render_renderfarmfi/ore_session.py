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

from math import floor

class OreSession:

    def __init__(self, id, title):
        self.id = id
        self.title = title
        self.frames = 0
        self.startframe = 0
        self.endframe = 0
        self.rendertime = 0
        self.percentage = 0

    def percentageComplete(self):
        totFrames = self.endframe - self.startframe
        done = 0
        if totFrames != 0:
            done = floor((self.frames / totFrames)*100)

        if done > 100:
            done = 100
        return done
