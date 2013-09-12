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
import os

def hasSSSMaterial():
    for m in bpy.data.materials:
        if m.subsurface_scattering.use:
            return True
        return False

def tuneParticles():
    for p in bpy.data.particles:
        if (p.type == 'EMITTER'):
            bpy.particleBakeWarning = True
        if (p.type == 'HAIR'):
            if (p.child_type == 'SIMPLE'):
                p.child_type = 'INTERPOLATED'
                bpy.childParticleWarning = True

def hasParticleSystem():
    if (len(bpy.data.particles) > 0):
        print("Found particle system")
        return True
    return False

def hasSimulation(t):
    for o in bpy.data.objects:
        for m in o.modifiers:
            if isinstance(m, t):
                print("Found simulation: " + str(t))
                return True
        return False

def hasFluidSimulation():
    return hasSimulation(bpy.types.FluidSimulationModifier)

def hasSmokeSimulation():
    return hasSimulation(bpy.types.SmokeModifier)

def hasClothSimulation():
    return hasSimulation(bpy.types.ClothModifier)

def hasCollisionSimulation():
    return hasSimulation(bpy.types.CollisionModifier)

def hasSoftbodySimulation():
    return hasSimulation(bpy.types.SoftBodyModifier)

def hasUnsupportedSimulation():
    return hasSoftbodySimulation() or hasCollisionSimulation() or hasClothSimulation() or hasSmokeSimulation() or hasFluidSimulation()

def isFilterNode(node):
    t = type(node)
    return t==bpy.types.CompositorNodeBlur or t==bpy.types.CompositorNodeDBlur

def changeSettings():

    sce = bpy.context.scene
    rd = sce.render
    ore = sce.ore_render

    # Necessary settings for BURP
    rd.resolution_x = ore.resox
    rd.resolution_y = ore.resoy
    sce.frame_start = ore.start
    sce.frame_end = ore.end
    rd.fps = ore.fps

    bpy.file_format_warning = False
    bpy.simulationWarning = False
    bpy.texturePackError = False
    bpy.particleBakeWarning = False
    bpy.childParticleWarning = False

    if (rd.image_settings.file_format == 'HDR'):
        rd.image_settings.file_format = 'PNG'
        bpy.file_format_warning = True

    # Convert between Blender's image format and BURP's formats
    if (rd.image_settings.file_format == 'PNG'):
        ore.file_format = 'PNG_FORMAT'
    elif (rd.image_settings.file_format == 'OPEN_EXR'):
        ore.file_format = 'EXR_FORMAT'
    elif (rd.image_settings.file_format == 'OPEN_EXR_MULTILAYER'):
        ore.file_format = 'EXR_MULTILAYER_FORMAT'
    elif (rd.image_settings.file_format == 'HDR'):
        ore.file_format = 'PNG_FORMAT'
    else:
        ore.file_format = 'PNG_FORMAT'

    if (ore.engine == 'cycles'):
        bpy.context.scene.cycles.samples = ore.samples

    if (ore.subsamples <= 0):
        ore.subsamples = 1

    if (ore.samples / ore.subsamples < 100.0):
        ore.subsamples = float(ore.samples) / 100.0

    # Multipart support doesn' work if SSS is used
    if ((rd.use_sss == True and hasSSSMaterial()) and ore.parts > 1):
        ore.parts = 1;

    if (hasParticleSystem()):
        tuneParticles()
    else:
        bpy.particleBakeWarning = False
        bpy.childParticleWarning = False

    if (hasUnsupportedSimulation()):
        bpy.simulationWarning = True
    else:
        bpy.simulationWarning = False

def _prepare_scene():
    changeSettings()

    print("Packing external textures...")
    try:
        bpy.ops.file.pack_all()
        bpy.texturePackError = False
    except Exception as e:
        bpy.texturePackError = True
        print(e)

    linkedData = bpy.utils.blend_paths()
    if (len(linkedData) > 0):
        print("Appending linked .blend files...")
        try:
            bpy.ops.object.make_local(type='ALL')
            bpy.linkedFileError = False
        except Exception as e:
            bpy.linkedFileError = True
            print(e)
    else:
        print("No external .blends used, skipping...")

    # Save with a different name
    print("Saving into a new file...")
    try:
        bpy.originalFileName = bpy.data.filepath
    except:
        bpy.originalFileName = 'untitled.blend'
    print("Original path is " + bpy.originalFileName)
    try:
        # If the filename is empty, we'll make one from the path of the user's resource folder
        if (len(bpy.originalFileName) == 0):
            print("No existing file path found, saving to autosave directory")
            savePath = bpy.utils.user_resource("AUTOSAVE")
            try:
                os.mkdir(savePath)
            except Exception as ex:
                print(ex)
            try:
                savePath = savePath + "_renderfarm"
            except Exception as ex:
                print(ex)
            try:
                bpy.ops.wm.save_mainfile(filepath=savePath)
            except Exception as ex:
                print(ex)
        else:
            print("Saving to current .blend directory")
            savePath = bpy.originalFileName
            savePath = savePath + "_renderfarm.blend"
            bpy.ops.wm.save_mainfile(filepath=savePath)
    except Exception as e:
        print(e)

    print(".blend prepared")


