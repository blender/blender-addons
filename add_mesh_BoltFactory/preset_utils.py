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

import os


def getPresets():

    scriptPath = os.path.dirname(__file__)
    presetPath = os.path.join(scriptPath, "presets")
    presetFiles = os.listdir(presetPath)
    #presetFiles.sort()

    presets = [(presetFile, presetFile.rpartition(".")[0], presetFile)
                for i, presetFile in enumerate(presetFiles) if presetFile.endswith(".py")]

    #print(presets)
    return presets, presetPath


#presets = getPresets()



def setProps(props, preset, presetsPath):
    
    #bpy.ops.script.python_file_run(filepath=presetsPath + '\\' + preset)

    file = open(os.path.join(presetsPath, preset))

    for line in file:
        exec(line)

    file.close()

    return
