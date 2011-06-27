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
    'name': 'Save As Runtime',
    'author': 'Mitchell Stokes (Moguri)',
    'version': (0, 3, 1),
    "blender": (2, 5, 8),
    "api": 37846,
    'location': 'File > Export',
    'description': 'Bundle a .blend file with the Blenderplayer',
    'warning': '',
    'wiki_url': 'http://wiki.blender.org/index.php/Extensions:2.5/Py/'\
        'Scripts/Game_Engine/Save_As_Runtime',
    'tracker_url': 'https://projects.blender.org/tracker/index.php?'\
        'func=detail&aid=23564',
    'category': 'Game Engine'}

import bpy
import os
import sys
import shutil


def WriteAppleRuntime(player_path, output_path, copy_python, overwrite_lib):
    # Enforce the extension
    if not output_path.endswith('.app'):
        output_path += '.app'

    # Use the system's cp command to preserve some meta-data
    os.system('cp -R "%s" "%s"' % (player_path, output_path))
    
    bpy.ops.wm.save_as_mainfile(filepath=output_path+"/Contents/Resources/game.blend", copy=True)
    
    # Copy bundled Python
    blender_dir = os.path.dirname(bpy.app.binary_path)
    
    if copy_python:
        print("Copying Python files...", end=" ")
        src = os.path.join(blender_dir, bpy.app.version_string.split()[0], "python", "lib")
        dst = os.path.join(output_path, "..")
        
        if os.path.exists(dst):
            if overwrite_lib:
                shutil.rmtree(dst)
                shutil.copytree(src, dst, ignore=lambda dir, contents: [i for i in contents if i.endswith('.pyc')])
        else:
            shutil.copytree(src, dst, ignore=lambda dir, contents: [i for i in contents if i.endswith('.pyc')])
        
        print("done")


def WriteRuntime(player_path, output_path, copy_python, overwrite_lib, copy_dlls):
    import struct

    # Check the paths
    if not os.path.isfile(player_path) and not(os.path.exists(player_path) and player_path.endswith('.app')):
        print("The player could not be found! Runtime not saved.")
        return
    
    # Check if we're bundling a .app
    if player_path.endswith('.app'):
        WriteAppleRuntime(player_path, output_path, copy_python, overwrite_lib)
        return
        
    # Enforce "exe" extension on Windows
    if player_path.endswith('.exe') and not output_path.endswith('.exe'):
        output_path += '.exe'
    
    # Get the player's binary and the offset for the blend
    file = open(player_path, 'rb')
    player_d = file.read()
    offset = file.tell()
    file.close()
    
    # Create a tmp blend file (Blenderplayer doesn't like compressed blends)
    blend_path = bpy.path.clean_name(output_path)
    bpy.ops.wm.save_as_mainfile(filepath=blend_path, compress=False, copy=True)
    blend_path += '.blend'
    
    # Get the blend data
    blend_file = open(blend_path, 'rb')
    blend_d = blend_file.read()
    blend_file.close()

    # Get rid of the tmp blend, we're done with it
    os.remove(blend_path)
    
    # Create a new file for the bundled runtime
    output = open(output_path, 'wb')
    
    # Write the player and blend data to the new runtime
    print("Writing runtime...", end=" ")
    output.write(player_d)
    output.write(blend_d)
    
    # Store the offset (an int is 4 bytes, so we split it up into 4 bytes and save it)
    output.write(struct.pack('B', (offset>>24)&0xFF))
    output.write(struct.pack('B', (offset>>16)&0xFF))
    output.write(struct.pack('B', (offset>>8)&0xFF))
    output.write(struct.pack('B', (offset>>0)&0xFF))
    
    # Stuff for the runtime
    output.write(b'BRUNTIME')
    output.close()
    
    print("done")
    
    # Make the runtime executable on Linux
    if os.name == 'posix':
        os.chmod(output_path, 0o755)
        
    # Copy bundled Python
    blender_dir = os.path.dirname(bpy.app.binary_path)
    runtime_dir = os.path.dirname(output_path)
    
    if copy_python:
        print("Copying Python files...", end=" ")
        py_folder = os.path.join(bpy.app.version_string.split()[0], "python", "lib")
        src = os.path.join(blender_dir, py_folder)
        dst = os.path.join(runtime_dir, py_folder)
        
        if os.path.exists(dst):
            if overwrite_lib:
                shutil.rmtree(dst)
                shutil.copytree(src, dst, ignore=lambda dir, contents: [i for i in contents if i == '__pycache__'])
        else:
            shutil.copytree(src, dst, ignore=lambda dir, contents: [i for i in contents if i == '__pycache__'])
        
        print("done")

    # And DLLs
    if copy_dlls:
        print("Copying DLLs...", end=" ")
        for file in [i for i in os.listdir(blender_dir) if i.endswith('.dll')]:
            src = os.path.join(blender_dir, file)
            dst = os.path.join(runtime_dir, file)
            shutil.copy2(src, dst)

        print("done")

from bpy.props import *


class SaveAsRuntime(bpy.types.Operator):
    bl_idname = "wm.save_as_runtime"
    bl_label = "Save As Runtime"
    bl_options = {'REGISTER'}
    
    if sys.platform == 'darwin':
        blender_bin_dir = '/'+os.path.join(*bpy.app.binary_path.split('/')[0:-4])
        ext = '.app'
    else:
        blender_bin_path = bpy.app.binary_path
        blender_bin_dir = os.path.dirname(blender_bin_path)
        ext = os.path.splitext(blender_bin_path)[-1]
    
    default_player_path = os.path.join(blender_bin_dir, 'blenderplayer' + ext)
    player_path = StringProperty(name="Player Path", description="The path to the player to use", default=default_player_path)
    filepath = StringProperty(name="Output Path", description="Where to save the runtime", default="")
    copy_python = BoolProperty(name="Copy Python", description="Copy bundle Python with the runtime", default=True)
    overwrite_lib = BoolProperty(name="Overwrite 'lib' folder", description="Overwrites the lib folder (if one exists) with the bundled Python lib folder", default=False)

    # Only Windows has dlls to copy
    if ext == '.exe':
        copy_dlls = BoolProperty(name="Copy DLLs", description="Copy all needed DLLs with the runtime", default=True)
    else:
        copy_dlls = False
    
    def execute(self, context):
        import time
        start_time = time.clock()
        print("Saving runtime to", self.properties.filepath)
        WriteRuntime(self.properties.player_path,
                    self.properties.filepath,
                    self.properties.copy_python,
                    self.properties.overwrite_lib,
                    self.copy_dlls)
        print("Finished in %.4fs" % (time.clock()-start_time))
        return {'FINISHED'}
                    
    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


def menu_func(self, context):

    ext = '.app' if sys.platform == 'darwin' else os.path.splitext(bpy.app.binary_path)[-1]
    default_blend_path = bpy.data.filepath.replace(".blend", ext)
    self.layout.operator(SaveAsRuntime.bl_idname, text=SaveAsRuntime.bl_label).filepath = default_blend_path


def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_export.append(menu_func)


def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_export.remove(menu_func)


if __name__ == "__main__":
    register()
