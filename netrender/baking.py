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
import sys, subprocess

BLENDER_PATH = sys.argv[0]

def bake(job, tasks):
    main_file = job.files[0]
    job_full_path = main_file.filepath
    
    task_commands = []
    for task in tasks:
        task_commands.extend(task)
    
    process = subprocess.Popen([BLENDER_PATH, "-b", "-noaudio", job_full_path, "-P", __file__, "--"] + task_commands, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    
    return process

def process_cache(obj, point_cache):
    if point_cache.is_baked:
        bpy.ops.ptcache.free_bake({"point_cache": point_cache})
        
    point_cache.use_disk_cache = True
    
    bpy.ops.ptcache.bake({"point_cache": point_cache}, bake=True)

def process_generic(obj, index):
    modifier = obj.modifiers[index]
    point_cache = modifier.point_cache
    process_cache(obj, point_cache)

def process_smoke(obj, index):
    modifier = obj.modifiers[index]
    point_cache = modifier.domain_settings.point_cache
    process_cache(obj, point_cache)

def process_particle(obj, index):
    psys = obj.particle_systems[index]
    point_cache = psys.point_cache
    process_cache(obj, point_cache)

def process_paint(obj, index):
    modifier = obj.modifiers[index]
    for surface in modifier.canvas_settings.canvas_surfaces:
        process_cache(obj, surface.point_cache)

def process_null(obj, index):
    raise ValueException("No baking possible with arguments: " + " ".join(sys.argv))

bake_funcs = {}
bake_funcs["CLOTH"] = process_generic
bake_funcs["SOFT_BODY"] = process_generic
bake_funcs["PARTICLE_SYSTEM"] = process_particle
bake_funcs["SMOKE"] = process_smoke
bake_funcs["DYNAMIC_PAINT"] = process_paint

if __name__ == "__main__":
    try:
        i = sys.argv.index("--")
    except:
        i = 0
    
    if i:
        task_args = sys.argv[i+1:]
        for i in range(0, len(task_args), 3):
            bake_type = task_args[i]
            obj = bpy.data.objects[task_args[i+1]]
            index = int(task_args[i+2])
            
            bake_funcs.get(bake_type, process_null)(obj, index)
