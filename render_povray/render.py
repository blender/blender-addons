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
import subprocess
import os
import sys
import time
import math
from math import atan, pi, degrees, sqrt

import platform as pltfrm
if pltfrm.architecture()[0] == '64bit':
    bitness = 64
else:
    bitness = 32

##############################SF###########################
##############find image texture 
def splitExt(path):
    dotidx = path.rfind('.')
    if dotidx == -1:
        return path, ''
    else:
        return (path[dotidx:]).upper().replace('.','')

def imageFormat(imgF):
    ext = ""
    ext_orig = splitExt(imgF)
    if ext_orig == 'JPG' or ext_orig == 'JPEG': ext='jpeg'
    if ext_orig == 'GIF': ext = 'gif'
    if ext_orig == 'TGA': ext = 'tga'
    if ext_orig == 'IFF': ext = 'iff'
    if ext_orig == 'PPM': ext = 'ppm'
    if ext_orig == 'PNG': ext = 'png'
    if ext_orig == 'SYS': ext = 'sys' 
    if ext_orig in ('TIFF', 'TIF'): ext = 'tiff'
    if ext_orig == 'EXR': ext = 'exr'#POV3.7 Only! 
    if ext_orig == 'HDR': ext = 'hdr'#POV3.7 Only! --MR
    print(imgF)
    if not ext: print(' WARNING: texture image  format not supported ') # % (imgF , '')) #(ext_orig)))
    return ext

def imgMap(ts):
    image_map=''
    if ts.mapping=='FLAT':image_map= ' map_type 0 ' 
    if ts.mapping=='SPHERE':image_map= ' map_type 1 '# map_type 7 in megapov
    if ts.mapping=='TUBE':image_map= ' map_type 2 '
    #if ts.mapping=='?':image_map= ' map_type 3 '# map_type 3 and 4 in development (?) for Povray, currently they just seem to default back to Flat (type 0)
    #if ts.mapping=='?':image_map= ' map_type 4 '# map_type 3 and 4 in development (?) for Povray, currently they just seem to default back to Flat (type 0)
    if ts.texture.use_interpolation: image_map+= " interpolate 2 "
    if ts.texture.extension == 'CLIP': image_map+=' once '
    #image_map+='}'
    #if ts.mapping=='CUBE':image_map+= 'warp { cubic } rotate <-90,0,180>' #no direct cube type mapping. Though this should work in POV 3.7 it doesn't give that good results(best suited to environment maps?)
    #if image_map=='': print(' No texture image  found ')
    return image_map

def imgMapBG(wts):
    image_mapBG=''
    if wts.texture_coords== 'VIEW':image_mapBG= ' map_type 0 ' #texture_coords refers to the mapping of world textures
    if wts.texture_coords=='ANGMAP':image_mapBG= ' map_type 1 '
    if wts.texture_coords=='TUBE':image_mapBG= ' map_type 2 '
    if wts.texture.use_interpolation: image_mapBG+= " interpolate 2 "
    if wts.texture.extension == 'CLIP': image_mapBG+=' once '
    #image_mapBG+='}'
    #if wts.mapping=='CUBE':image_mapBG+= 'warp { cubic } rotate <-90,0,180>' #no direct cube type mapping. Though this should work in POV 3.7 it doesn't give that good results(best suited to environment maps?)
    #if image_mapBG=='': print(' No background texture image  found ')
    return image_mapBG

def splitFile(path):
    idx = path.rfind('/')
    if idx == -1:
        idx = path.rfind('\\')
    return path[idx:].replace("/", "").replace("\\", "")

def splitPath(path):
    idx = path.rfind('/')
    if idx == -1:
        return path, ''
    else:
        return path[:idx]

def findInSubDir(filename, subdirectory=''):
    pahFile=''
    if subdirectory:
        path = subdirectory
    else:
        path = os.getcwd()
    try:
        for root, dirs, names in os.walk(path):
            if filename in names:
                pahFile = os.path.join(root, filename)
        return pahFile
    except: return ''

def path_image(image):
    import os
    fn = bpy.path.abspath(image)
    fn_strip = os.path.basename(fn)
    if not os.path.isfile(fn):
        fn=(findInSubDir(splitFile(fn),splitPath(bpy.data.filepath)))
        ()
    return fn

##############end find image texture 


##############safety string name material
def safety(name):
    try:
        if int(name) > 0: prefix='shader'
    except: prefix=''
    prefix='shader_'
    return prefix+name

def safety0(name): #used for 0 of specular map
    try:
        if int(name) > 0: prefix='shader'
    except: prefix=''
    prefix='shader_'
    return prefix+name+'0'

def safety1(name): #used for 1 of specular map
    try:
        if int(name) > 0: prefix='shader'
    except: prefix=''
    prefix='shader_'
    return prefix+name+'1'
##############end safety string name material
##############################EndSF###########################

def write_pov(filename, scene=None, info_callback=None):
    file = open(filename, 'w')

    # Only for testing
    if not scene:
        scene = bpy.data.scenes[0]

    render = scene.render
    world = scene.world

    def uniqueName(name, nameSeq):

        if name not in nameSeq:
            return name

        name_orig = name
        i = 1
        while name in nameSeq:
            name = '%s_%.3d' % (name_orig, i)
            i += 1

        return name

    def writeMatrix(matrix):
        file.write('\tmatrix <%.6f, %.6f, %.6f,  %.6f, %.6f, %.6f,  %.6f, %.6f, %.6f,  %.6f, %.6f, %.6f>\n' %\
        (matrix[0][0], matrix[0][1], matrix[0][2], matrix[1][0], matrix[1][1], matrix[1][2], matrix[2][0], matrix[2][1], matrix[2][2], matrix[3][0], matrix[3][1], matrix[3][2]))

    def writeObjectMaterial(material):
        if material: #and material.transparency_method == 'RAYTRACE':#Commented out: always write IOR to be able to use it for SSS, Fresnel reflections...
            #But there can be only one!
            if material.subsurface_scattering.use:#SSS IOR get highest priority
                file.write('\tinterior { ior %.6f\n' % material.subsurface_scattering.ior)
            elif material.pov_mirror_use_IOR:#Then the raytrace IOR taken from raytrace transparency properties and used for reflections if IOR Mirror option is checked
                file.write('\tinterior { ior %.6f\n' % material.raytrace_transparency.ior)
            else:
                file.write('\tinterior { ior %.6f\n' % material.raytrace_transparency.ior)



            #If only Raytrace transparency is set, its IOR will be used for refraction, but user can set up "un-physical" fresnel reflections in raytrace mirror parameters. 
            #Last, if none of the above is specified, user can set up "un-physical" fresnel reflections in raytrace mirror parameters. And pov IOR defaults to 1. 
            if material.pov_caustics_enable:
                if material.pov_fake_caustics:
                    file.write('\tcaustics %.3g\n' % material.pov_fake_caustics_power)
                    #material.pov_photons_refraction=0
                if material.pov_photons_refraction:
                    material.pov_fake_caustics=0 #How to deactivate fake caustics when refr photons on?

                    file.write('\tdispersion %.3g\n' % material.pov_photons_dispersion) #Default of 1 means no dispersion
                    
                #bpy.types.MATERIAL_PT_povray_caustics.Display = 1 - bpy.types.MATERIAL_PT_povray_caustics.Display
        #mat = context.material
            # Other interior args
            # fade_distance 2
            # fade_power [Value]
            # fade_color

            # (variable) dispersion_samples (constant count for now)
            file.write('\t}\n')
            if material.pov_photons_refraction or material.pov_photons_reflection:
                file.write('\tphotons{\n')
                file.write('\t\ttarget\n')
                if material.pov_photons_refraction:
                    file.write('\t\trefraction on\n')
                if material.pov_photons_reflection:
                    file.write('\t\treflection on\n')
                file.write('\t}\n')
                
    materialNames = {}
    DEF_MAT_NAME = 'Default'

    def writeMaterial(material):
        # Assumes only called once on each material

        if material:
            name_orig = material.name
        else:
            name_orig = DEF_MAT_NAME

        name = materialNames[name_orig] = uniqueName(bpy.path.clean_name(name_orig), materialNames)

        file.write('#declare %s = finish {\n' % safety0(name))

        if material:

            #Povray 3.7 now uses two diffuse values respectively for front and back shading (the back diffuse is like blender translucency)
            frontDiffuse=material.diffuse_intensity
            backDiffuse=material.translucency
            
        
            if material.pov_conserve_energy:

                #Total should not go above one
                if (frontDiffuse + backDiffuse) <= 1.0:
                    pass
                elif frontDiffuse==backDiffuse:
                    frontDiffuse = backDiffuse = 0.5 # Try to respect the user's "intention" by comparing the two values but bringing the total back to one
                elif frontDiffuse>backDiffuse:       # Let the highest value stay the highest value
                    backDiffuse = 1-(1-frontDiffuse)
                else:
                    frontDiffuse = 1-(1-backDiffuse)
                

            # map hardness between 0.0 and 1.0
            roughness = ((1.0 - ((material.specular_hardness - 1.0) / 510.0)))
            ## scale from 0.0 to 0.1
            roughness *= 0.1
            # add a small value because 0.0 is invalid
            roughness += (1 / 511.0)

            #####################################Diffuse Shader######################################
            if material.diffuse_shader == 'OREN_NAYAR':
                file.write('\tbrilliance %.3g\n' % (0.9+material.roughness))#blender roughness is what is generally called oren nayar Sigma, and brilliance in povray

            if material.diffuse_shader == 'TOON':
                file.write('\tbrilliance %.3g\n' % (0.01+material.diffuse_toon_smooth*0.25))
                frontDiffuse*=0.5 #Lower diffuse and increase specular for toon effect seems to look better in povray
            
            if material.diffuse_shader == 'MINNAERT':
                #file.write('\taoi %.3g\n' % material.darkness) #not real syntax, aoi is a pattern.
                pass # Have to put this in texture since AOI and slope map are patterns
            if material.diffuse_shader == 'FRESNEL':
                #file.write('\taoi %.3g\n' % material.diffuse_fresnel_factor) #not real syntax, aoi is a pattern.
                pass # Have to put this in texture since AOI and slope map are patterns
            if material.diffuse_shader == 'LAMBERT':
                file.write('\tbrilliance 1.8\n') #trying to best match lambert attenuation by that constant brilliance value
                
            
            #########################################################################################

            file.write('\tdiffuse %.3g %.3g\n' % (frontDiffuse, backDiffuse))

                
            file.write('\tspecular 0\n')

            file.write('\tambient %.3g\n' % material.ambient)
            #file.write('\tambient rgb <%.3g, %.3g, %.3g>\n' % tuple([c*material.ambient for c in world.ambient_color])) # povray blends the global value
            file.write('\temission %.3g\n' % material.emit) #New in povray 3.7

            if material.pov_conserve_energy:
                file.write('\tconserve_energy\n')#added for more realistic shading. Needs some checking to see if it really works. --Maurice.

            # 'phong 70.0 '

            if material.subsurface_scattering.use:
                subsurface_scattering = material.subsurface_scattering
                file.write('\tsubsurface { <%.3g, %.3g, %.3g>, <%.3g, %.3g, %.3g> }\n' % (sqrt(subsurface_scattering.radius[0])*1.5, sqrt(subsurface_scattering.radius[1])*1.5, sqrt(subsurface_scattering.radius[2])*1.5, 1-subsurface_scattering.color[0], 1-subsurface_scattering.color[1], 1-subsurface_scattering.color[2]))

            if material.pov_irid_enable:
                file.write('\tirid { %.4g thickness %.4g turbulence %.4g }' % (material.pov_irid_amount, material.pov_irid_thickness, material.pov_irid_turbulence))

        file.write('}\n')
        ##################Plain version of the finish (previous ones are variations for specular/Mirror texture channel map with alternative finish of 0 specular and no mirror reflection###
        file.write('#declare %s = finish {\n' % safety(name))

        if material:
            #Povray 3.7 now uses two diffuse values respectively for front and back shading (the back diffuse is like blender translucency)
            frontDiffuse=material.diffuse_intensity
            backDiffuse=material.translucency
            
        
            if material.pov_conserve_energy:

                #Total should not go above one
                if (frontDiffuse + backDiffuse) <= 1.0:
                    pass
                elif frontDiffuse==backDiffuse:
                    frontDiffuse = backDiffuse = 0.5 # Try to respect the user's "intention" by comparing the two values but bringing the total back to one
                elif frontDiffuse>backDiffuse:       # Let the highest value stay the highest value
                    backDiffuse = 1-(1-frontDiffuse)
                else:
                    frontDiffuse = 1-(1-backDiffuse)
                

            # map hardness between 0.0 and 1.0
            roughness = ((1.0 - ((material.specular_hardness - 1.0) / 510.0)))
            ## scale from 0.0 to 0.1
            roughness *= 0.1 
            # add a small value because 0.0 is invalid
            roughness += (1 / 511.0)

            #####################################Diffuse Shader######################################
            if material.diffuse_shader == 'OREN_NAYAR':
                file.write('\tbrilliance %.3g\n' % (0.9+material.roughness))#blender roughness is what is generally called oren nayar Sigma, and brilliance in povray

            if material.diffuse_shader == 'TOON':
                file.write('\tbrilliance %.3g\n' % (0.01+material.diffuse_toon_smooth*0.25))
                frontDiffuse*=0.5 #Lower diffuse and increase specular for toon effect seems to look better in povray
            
            if material.diffuse_shader == 'MINNAERT':
                #file.write('\taoi %.3g\n' % material.darkness)
                pass #let's keep things simple for now
            if material.diffuse_shader == 'FRESNEL':
                #file.write('\taoi %.3g\n' % material.diffuse_fresnel_factor)
                pass #let's keep things simple for now
            if material.diffuse_shader == 'LAMBERT':
                file.write('\tbrilliance 1.8\n') #trying to best match lambert attenuation by that constant brilliance value
                
            ####################################Specular Shader######################################
            if material.specular_shader == 'COOKTORR' or material.specular_shader == 'PHONG':#No difference between phong and cook torrence in blender HaHa!
                file.write('\tphong %.3g\n' % (material.specular_intensity))
                file.write('\tphong_size %.3g\n'% (material.specular_hardness / 2 + 0.25)) 

            if material.specular_shader == 'BLINN':#Povray "specular" keyword corresponds to a Blinn model, without the ior.
                file.write('\tspecular %.3g\n' % (material.specular_intensity * (material.specular_ior/4))) #Use blender Blinn's IOR just as some factor for spec intensity
                file.write('\troughness %.3g\n' % roughness) 
                #Could use brilliance 2(or varying around 2 depending on ior or factor) too.


            if material.specular_shader == 'TOON':
                file.write('\tphong %.3g\n' % (material.specular_intensity * 2))
                file.write('\tphong_size %.3g\n' % (0.1+material.specular_toon_smooth / 2)) #use extreme phong_size


            if material.specular_shader == 'WARDISO':
                file.write('\tspecular %.3g\n' % (material.specular_intensity / (material.specular_slope+0.0005))) #find best suited default constant for brilliance Use both phong and specular for some values.
                file.write('\troughness %.4g\n' % (0.0005+material.specular_slope/10)) #find best suited default constant for brilliance Use both phong and specular for some values.
                file.write('\tbrilliance %.4g\n' % (1.8-material.specular_slope*1.8)) #find best suited default constant for brilliance Use both phong and specular for some values.
                

            
            #########################################################################################

            file.write('\tdiffuse %.3g %.3g\n' % (frontDiffuse, backDiffuse))


            file.write('\tambient %.3g\n' % material.ambient)
            #file.write('\tambient rgb <%.3g, %.3g, %.3g>\n' % tuple([c*material.ambient for c in world.ambient_color])) # povray blends the global value
            file.write('\temission %.3g\n' % material.emit) #New in povray 3.7
            
            #file.write('\troughness %.3g\n' % roughness) #povray just ignores roughness if there's no specular keyword
            
            if material.pov_conserve_energy:
                file.write('\tconserve_energy\n')#added for more realistic shading. Needs some checking to see if it really works. --Maurice.

            # 'phong 70.0 '

            if material.raytrace_mirror.use:
                raytrace_mirror = material.raytrace_mirror
                if raytrace_mirror.reflect_factor:
                    file.write('\treflection {\n')
                    file.write('\t\trgb <%.3g, %.3g, %.3g>' % tuple(material.mirror_color))
                    if material.pov_mirror_metallic:
                        file.write('\t\tmetallic %.3g' % (raytrace_mirror.reflect_factor))
                    if material.pov_mirror_use_IOR: #WORKING ?
                        file.write('\t\tfresnel 1 ')#Removed from the line below: gives a more physically correct material but needs proper IOR. --Maurice
                    file.write('\t\tfalloff %.3g exponent %.3g} ' % (raytrace_mirror.fresnel, raytrace_mirror.fresnel_factor))

            if material.subsurface_scattering.use:
                subsurface_scattering = material.subsurface_scattering
                file.write('\tsubsurface { <%.3g, %.3g, %.3g>, <%.3g, %.3g, %.3g> }\n' % (sqrt(subsurface_scattering.radius[0])*1.5, sqrt(subsurface_scattering.radius[1])*1.5, sqrt(subsurface_scattering.radius[2])*1.5, 1-subsurface_scattering.color[0], 1-subsurface_scattering.color[1], 1-subsurface_scattering.color[2]))

            if material.pov_irid_enable:
                file.write('\tirid { %.4g thickness %.4g turbulence %.4g }' % (material.pov_irid_amount, material.pov_irid_thickness, material.pov_irid_turbulence))

        file.write('}\n')
        ##################Full specular version of the finish an increased roughness seems necessary here to perceive anything###
        file.write('#declare %s = finish {\n' % safety1(name))

        if material:
            #Povray 3.7 now uses two diffuse values respectively for front and back shading (the back diffuse is like blender translucency)
            frontDiffuse=material.diffuse_intensity
            backDiffuse=material.translucency
            if material.pov_conserve_energy:

                #Total should not go above one
                if (frontDiffuse + backDiffuse) <= 1.0:
                    pass
                elif frontDiffuse==backDiffuse:
                    frontDiffuse = backDiffuse = 0.5 # Try to respect the user's "intention" by comparing the two values but bringing the total back to one
                elif frontDiffuse>backDiffuse:       # Let the highest value stay the highest value
                    backDiffuse = 1-(1-frontDiffuse)
                else:
                    frontDiffuse = 1-(1-backDiffuse)

            # map hardness between 0.0 and 1.0
            roughness = ((1.0 - ((material.specular_hardness - 1.0) / 510.0)))
            ## scale from 0.0 to 0.1
            roughness *= 0.1 
            # add a small value because 0.0 is invalid
            roughness += (1 / 511.0)

 
                
            ####################################Specular Shader######################################
            if material.specular_shader == 'COOKTORR' or material.specular_shader == 'PHONG':#No difference between phong and cook torrence in blender HaHa!
                file.write('\tphong %.3g\n' % (material.specular_intensity*3))#Multiplied for max value of Textured Spec.
                file.write('\tphong_size %.3g\n'% (material.specular_hardness /100 + 0.0005)) # /2-->/500; 0.25-->0.0025 Larger highlight for max value of Textured Spec.

            if material.specular_shader == 'BLINN':#Povray "specular" keyword corresponds to a Blinn model, hmhmmmm...
                file.write('\tspecular %.3g\n' % (material.specular_intensity * 5)) #Multiplied for max value of Textured Spec.
                file.write('\troughness %.3g\n' % (roughness*10)) #Multiplied for max value of Textured Spec.



            if material.specular_shader == 'TOON':
                file.write('\tphong %.3g\n' % (material.specular_intensity*3))#Multiplied for max value of Textured Spec.
                file.write('\tphong_size %.3g\n' % (0.1+material.specular_toon_smooth / 10)) #use extreme phong_size


            if material.specular_shader == 'WARDISO':
                file.write('\tspecular %.3g\n' % (material.specular_intensity / (material.specular_slope+0.0005))) #find best suited default constant for brilliance Use both phong and specular for some values.
                file.write('\troughness %.4g\n' % (0.0005+material.specular_slope*5)) #Multiplied for max value of Textured Spec.
                file.write('\tbrilliance %.4g\n' % (1.8-material.specular_slope*1.8)) #find best suited default constant for brilliance Use both phong and specular for some values.


            
            #########################################################################################
                
            file.write('\tdiffuse %.3g %.3g\n' % (frontDiffuse, backDiffuse))

            file.write('\tambient %.3g\n' % material.ambient)
            #file.write('\tambient rgb <%.3g, %.3g, %.3g>\n' % tuple([c*material.ambient for c in world.ambient_color])) # povray blends the global value
            file.write('\temission %.3g\n' % material.emit) #New in povray 3.7
            
            if material.pov_conserve_energy:
                file.write('\tconserve_energy\n')#added for more realistic shading. Needs some checking to see if it really works. --Maurice.

            # 'phong 70.0 '

            if material.raytrace_mirror.use:
                raytrace_mirror = material.raytrace_mirror
                if raytrace_mirror.reflect_factor:
                    file.write('\treflection {\n')
                    file.write('\t\trgb <%.3g, %.3g, %.3g>' % tuple(material.mirror_color))
                    if material.pov_mirror_metallic:
                        file.write('\t\tmetallic %.3g' % (raytrace_mirror.reflect_factor))
                    if material.pov_mirror_use_IOR: #WORKING ?
                        file.write('\t\tfresnel 1 ')#Removed from the line below: gives a more physically correct material but needs proper IOR. --Maurice
                    file.write('\t\tfalloff %.3g exponent %.3g} ' % (raytrace_mirror.fresnel, raytrace_mirror.fresnel_factor))

            if material.subsurface_scattering.use:
                subsurface_scattering = material.subsurface_scattering
                file.write('\tsubsurface { <%.3g, %.3g, %.3g>, <%.3g, %.3g, %.3g> }\n' % (sqrt(subsurface_scattering.radius[0])*1.5, sqrt(subsurface_scattering.radius[1])*1.5, sqrt(subsurface_scattering.radius[2])*1.5, 1-subsurface_scattering.color[0], 1-subsurface_scattering.color[1], 1-subsurface_scattering.color[2]))
                ##sqrt(subsurface_scattering.radius[1] above is just some non linear relation to keep "proportions" between blender presets values and povray. The following paper has samples of sigma numbers we can put directly into pov to get good results:
                ##http://graphics.stanford.edu/papers/bssrdf/bssrdf.pdf
                ##Whereas Blender probably uses That:
                ##http://graphics.stanford.edu/papers/fast_bssrdf/fast_bssrdf.pdf

            if material.pov_irid_enable:
                file.write('\tirid { %.4g thickness %.4g turbulence %.4g }' % (material.pov_irid_amount, material.pov_irid_thickness, material.pov_irid_turbulence))

        else:
            file.write('\tdiffuse 0.8\n')
            file.write('\tphong 70.0\n')
            
            #file.write('\tspecular 0.2\n')


        # This is written into the object
        '''
        if material and material.transparency_method=='RAYTRACE':
            'interior { ior %.3g} ' % material.raytrace_transparency.ior
        '''

        #file.write('\t\t\tcrand 1.0\n') # Sand granyness
        #file.write('\t\t\tmetallic %.6f\n' % material.spec)
        #file.write('\t\t\tphong %.6f\n' % material.spec)
        #file.write('\t\t\tphong_size %.6f\n' % material.spec)
        #file.write('\t\t\tbrilliance %.6f ' % (material.specular_hardness/256.0) # Like hardness

        file.write('}\n')

    def exportCamera():
        camera = scene.camera
        matrix = camera.matrix_world

        # compute resolution
        Qsize = float(render.resolution_x) / float(render.resolution_y)
        file.write('#declare camLocation  = <%.6f, %.6f, %.6f>;\n' % (matrix[3][0], matrix[3][1], matrix[3][2]))
        file.write('#declare camLookAt = <%.6f, %.6f, %.6f>;\n' % tuple([degrees(e) for e in matrix.rotation_part().to_euler()]))

        file.write('camera {\n')
        file.write('\tlocation  <0, 0, 0>\n')
        file.write('\tlook_at  <0, 0, -1>\n')
        file.write('\tright <%s, 0, 0>\n' % - Qsize)
        file.write('\tup <0, 1, 0>\n')
        file.write('\tangle  %f \n' % (360.0 * atan(16.0 / camera.data.lens) / pi))

        file.write('\trotate  <%.6f, %.6f, %.6f>\n' % tuple([degrees(e) for e in matrix.rotation_part().to_euler()]))
        file.write('\ttranslate <%.6f, %.6f, %.6f>\n' % (matrix[3][0], matrix[3][1], matrix[3][2]))
        file.write('}\n')

    def exportLamps(lamps):
        # Get all lamps
        for ob in lamps:
            lamp = ob.data

            matrix = ob.matrix_world

            color = tuple([c * lamp.energy *2 for c in lamp.color]) # Colour is modified by energy #muiltiplie by 2 for a better match --Maurice

            file.write('light_source {\n')
            file.write('\t< 0,0,0 >\n')
            file.write('\tcolor rgb<%.3g, %.3g, %.3g>\n' % color)

            if lamp.type == 'POINT': # Point Lamp
                pass
            elif lamp.type == 'SPOT': # Spot
                file.write('\tspotlight\n')

                # Falloff is the main radius from the centre line
                file.write('\tfalloff %.2f\n' % (degrees(lamp.spot_size) / 2.0)) # 1 TO 179 FOR BOTH
                file.write('\tradius %.6f\n' % ((degrees(lamp.spot_size) / 2.0) * (1.0 - lamp.spot_blend)))

                # Blender does not have a tightness equivilent, 0 is most like blender default.
                file.write('\ttightness 0\n') # 0:10f

                file.write('\tpoint_at  <0, 0, -1>\n')
            elif lamp.type == 'SUN':
                file.write('\tparallel\n')
                file.write('\tpoint_at  <0, 0, -1>\n') # *must* be after 'parallel'

            elif lamp.type == 'AREA':
                file.write('\tfade_distance %.6f\n' % (lamp.distance / 5) )
                file.write('\tfade_power %d\n' % 2) #  Area lights have no falloff type, so always use blenders lamp quad equivalent for those?
                size_x = lamp.size
                samples_x = lamp.shadow_ray_samples_x
                if lamp.shape == 'SQUARE':
                    size_y = size_x
                    samples_y = samples_x
                else:
                    size_y = lamp.size_y
                    samples_y = lamp.shadow_ray_samples_y

                file.write('\tarea_light <%d,0,0>,<0,0,%d> %d, %d\n' % (size_x, size_y, samples_x, samples_y))
                if lamp.shadow_ray_sample_method == 'CONSTANT_JITTERED':
                    if lamp.jitter:
                        file.write('\tjitter\n')
                else:
                    file.write('\tadaptive 1\n')
                    file.write('\tjitter\n')

            if lamp.shadow_method == 'NOSHADOW':
                file.write('\tshadowless\n')

            if lamp.type != 'SUN' and lamp.type!='AREA':#Sun shouldn't be attenuated. and area lights have no falloff attribute so they are put to type 2 attenuation a little higher above.
                file.write('\tfade_distance %.6f\n' % (lamp.distance / 5) )
                if lamp.falloff_type == 'INVERSE_SQUARE':
                    file.write('\tfade_power %d\n' % 2) # Use blenders lamp quad equivalent
                elif lamp.falloff_type == 'INVERSE_LINEAR':
                    file.write('\tfade_power %d\n' % 1) # Use blenders lamp linear
                elif lamp.falloff_type == 'CONSTANT': #Supposing using no fade power keyword would default to constant, no attenuation.
                    pass
                elif lamp.falloff_type == 'CUSTOM_CURVE': #Using Custom curve for fade power 3 for now.
                    file.write('\tfade_power %d\n' % 4)

            writeMatrix(matrix)

            file.write('}\n')
##################################################################################################################################
#Wip to be Used for fresnel, but not tested yet.
##################################################################################################################################
##    lampLocation=[0,0,0]
##    lampRotation=[0,0,0]
##    lampDistance=0.00
##    averageLampLocation=[0,0,0]
##    averageLampRotation=[0,0,0]
##    averageLampDistance=0.00
##    lamps=[]
##    for l in scene.objects:
##        if l.type == 'LAMP':#get all lamps
##            lamps += [l]
##    for ob in lamps:
##        lamp = ob.data
##        lampLocation[0]+=ob.location[0]
##        lampLocation[1]+=ob.location[1]
##        lampLocation[2]+=ob.location[2]
##        lampRotation[0]+=ob.rotation_euler[0]
##        lampRotation[1]+=ob.rotation_euler[1]
##        lampRotation[2]+=ob.rotation_euler[2]
##        lampDistance+=ob.data.distance
##        averageLampRotation[0]=lampRotation[0] / len(lamps)#create an average direction for all lamps.
##        averageLampRotation[1]=lampRotation[1] / len(lamps)#create an average direction for all lamps.
##        averageLampRotation[2]=lampRotation[2] / len(lamps)#create an average direction for all lamps.
##
##        averageLampLocation[0]=lampLocation[0] / len(lamps)#create an average position for all lamps.
##        averageLampLocation[1]=lampLocation[1] / len(lamps)#create an average position for all lamps.
##        averageLampLocation[2]=lampLocation[2] / len(lamps)#create an average position for all lamps.
##        
##        averageLampDistance=lampDistance / len(lamps)#create an average distance for all lamps.
##    file.write('\n#declare lampTarget= vrotate(<%.4g,%.4g,%.4g>,<%.4g,%.4g,%.4g>);' % (-(averageLampLocation[0]-averageLampDistance), -(averageLampLocation[1]-averageLampDistance), -(averageLampLocation[2]-averageLampDistance), averageLampRotation[0], averageLampRotation[1], averageLampRotation[2]))
##    #v(A,B) rotates vector A about origin by vector B.    
##
####################################################################################################################################

    def exportMeta(metas):

        # TODO - blenders 'motherball' naming is not supported.

        for ob in metas:
            meta = ob.data

            file.write('blob {\n')
            file.write('\t\tthreshold %.4g\n' % meta.threshold)

            try:
                material = meta.materials[0] # lame! - blender cant do enything else.
            except:
                material = None

            for elem in meta.elements:

                if elem.type not in ('BALL', 'ELLIPSOID'):
                    continue # Not supported

                loc = elem.co

                stiffness = elem.stiffness
                if elem.use_negative:
                    stiffness = - stiffness

                if elem.type == 'BALL':

                    file.write('\tsphere { <%.6g, %.6g, %.6g>, %.4g, %.4g ' % (loc.x, loc.y, loc.z, elem.radius, stiffness))

                    # After this wecould do something simple like...
                    # 	"pigment {Blue} }"
                    # except we'll write the color

                elif elem.type == 'ELLIPSOID':
                    # location is modified by scale
                    file.write('\tsphere { <%.6g, %.6g, %.6g>, %.4g, %.4g ' % (loc.x / elem.size_x, loc.y / elem.size_y, loc.z / elem.size_z, elem.radius, stiffness))
                    file.write('scale <%.6g, %.6g, %.6g> ' % (elem.size_x, elem.size_y, elem.size_z))

                if material:
                    diffuse_color = material.diffuse_color

                    if material.use_transparency and material.transparency_method == 'RAYTRACE':
                        trans = 1.0 - material.raytrace_transparency.filter
                    else:
                        trans = 0.0

                    file.write('pigment {rgbft<%.3g, %.3g, %.3g, %.3g, %.3g>} finish {%s} }\n' % \
                        (diffuse_color[0], diffuse_color[1], diffuse_color[2], 1.0 - material.alpha, trans, materialNames[material.name]))

                else:
                    file.write('pigment {rgb<1 1 1>} finish {%s} }\n' % DEF_MAT_NAME)		# Write the finish last.

            writeObjectMaterial(material)

            writeMatrix(ob.matrix_world)

            file.write('}\n')

    def exportMeshs(scene, sel):

        ob_num = 0

        for ob in sel:
            ob_num += 1

            if ob.type in ('LAMP', 'CAMERA', 'EMPTY', 'META', 'ARMATURE', 'LATTICE'):
                continue

            me = ob.data
            me_materials = me.materials

            me = ob.create_mesh(scene, True, 'RENDER')

            if not me or not me.faces:
                continue

            if info_callback:
                info_callback('Object %2.d of %2.d (%s)' % (ob_num, len(sel), ob.name))

            #if ob.type!='MESH':
            #	continue
            # me = ob.data

            matrix = ob.matrix_world
            try:
                uv_layer = me.uv_textures.active.data
            except:
                uv_layer = None

            try:
                vcol_layer = me.vertex_colors.active.data
            except:
                vcol_layer = None

            faces_verts = [f.vertices[:] for f in me.faces]
            faces_normals = [tuple(f.normal) for f in me.faces]
            verts_normals = [tuple(v.normal) for v in me.vertices]

            # quads incur an extra face
            quadCount = sum(1 for f in faces_verts if len(f) == 4)

            file.write('mesh2 {\n')
            file.write('\tvertex_vectors {\n')
            file.write('\t\t%s' % (len(me.vertices))) # vert count
            for v in me.vertices:
                file.write(',\n\t\t<%.6f, %.6f, %.6f>' % tuple(v.co)) # vert count
            file.write('\n  }\n')


            # Build unique Normal list
            uniqueNormals = {}
            for fi, f in enumerate(me.faces):
                fv = faces_verts[fi]
                # [-1] is a dummy index, use a list so we can modify in place
                if f.use_smooth: # Use vertex normals
                    for v in fv:
                        key = verts_normals[v]
                        uniqueNormals[key] = [-1]
                else: # Use face normal
                    key = faces_normals[fi]
                    uniqueNormals[key] = [-1]

            file.write('\tnormal_vectors {\n')
            file.write('\t\t%d' % len(uniqueNormals)) # vert count
            idx = 0
            for no, index in uniqueNormals.items():
                file.write(',\n\t\t<%.6f, %.6f, %.6f>' % no) # vert count
                index[0] = idx
                idx += 1
            file.write('\n  }\n')


            # Vertex colours
            vertCols = {} # Use for material colours also.

            if uv_layer:
                # Generate unique UV's
                uniqueUVs = {}

                for fi, uv in enumerate(uv_layer):

                    if len(faces_verts[fi]) == 4:
                        uvs = uv.uv1, uv.uv2, uv.uv3, uv.uv4
                    else:
                        uvs = uv.uv1, uv.uv2, uv.uv3

                    for uv in uvs:
                        uniqueUVs[tuple(uv)] = [-1]

                file.write('\tuv_vectors {\n')
                #print unique_uvs
                file.write('\t\t%s' % (len(uniqueUVs))) # vert count
                idx = 0
                for uv, index in uniqueUVs.items():
                    file.write(',\n\t\t<%.6f, %.6f>' % uv)
                    index[0] = idx
                    idx += 1
                '''
                else:
                    # Just add 1 dummy vector, no real UV's
                    file.write('\t\t1') # vert count
                    file.write(',\n\t\t<0.0, 0.0>')
                '''
                file.write('\n  }\n')


            if me.vertex_colors:

                for fi, f in enumerate(me.faces):
                    material_index = f.material_index
                    material = me_materials[material_index]

                    if material and material.use_vertex_color_paint:

                        col = vcol_layer[fi]

                        if len(faces_verts[fi]) == 4:
                            cols = col.color1, col.color2, col.color3, col.color4
                        else:
                            cols = col.color1, col.color2, col.color3

                        for col in cols:
                            key = col[0], col[1], col[2], material_index # Material index!
                            vertCols[key] = [-1]

                    else:
                        if material:
                            diffuse_color = tuple(material.diffuse_color)
                            key = diffuse_color[0], diffuse_color[1], diffuse_color[2], material_index
                            vertCols[key] = [-1]


            else:
                # No vertex colours, so write material colours as vertex colours
                for i, material in enumerate(me_materials):

                    if material:
                        diffuse_color = tuple(material.diffuse_color)
                        key = diffuse_color[0], diffuse_color[1], diffuse_color[2], i # i == f.mat
                        vertCols[key] = [-1]


            # Vert Colours
            file.write('\ttexture_list {\n')
            file.write('\t\t%s' % (len(vertCols))) # vert count
            idx = 0
            for col, index in vertCols.items():

                if me_materials:
                    material = me_materials[col[3]]
                    material_finish = materialNames[material.name]

                    if material.use_transparency and material.transparency_method == 'RAYTRACE':
                        trans = 1.0 - material.raytrace_transparency.filter
                    else:
                        trans = 0.0

                else:
                    material_finish = DEF_MAT_NAME # not working properly,
                    trans = 0.0

                ##############SF
                texturesDif=''
                texturesSpec=''
                texturesNorm=''
                texturesAlpha=''
                for t in material.texture_slots:
                    if t and t.texture.type == 'IMAGE' and t.use and t.texture.image: 
                        image_filename = path_image(t.texture.image.filepath)
                        if image_filename:
                            if t.use_map_color_diffuse: 
                                texturesDif = image_filename
                                colvalue = t.default_value
                                t_dif = t
                            if t.use_map_specular or t.use_map_raymir: 
                                texturesSpec = image_filename
                                colvalue = t.default_value
                                t_spec = t
                            if t.use_map_normal: 
                                texturesNorm = image_filename
                                colvalue = t.normal_factor * 10.0
                                #textNormName=t.texture.image.name + '.normal'
                                #was the above used? --MR
                                t_nor = t
                            if t.use_map_alpha: 
                                texturesAlpha = image_filename
                                colvalue = t.alpha_factor * 10.0
                                #textDispName=t.texture.image.name + '.displ'
                                #was the above used? --MR
                                t_alpha = t




                ##############################################################################################################
                file.write('\n\t\ttexture {') #THIS AREA NEEDS TO LEAVE THE TEXTURE OPEN UNTIL ALL MAPS ARE WRITTEN DOWN.   --MR                      


                ##############################################################################################################
                if material.diffuse_shader == 'MINNAERT':
                    file.write('\n\t\t\taoi')
                    file.write('\n\t\t\ttexture_map {')
                    file.write('\n\t\t\t\t[%.3g finish {diffuse %.3g}]' % ((material.darkness/2), (2-material.darkness)))
                    file.write('\n\t\t\t\t[%.3g' % (1-(material.darkness/2)))
######TO OPTIMIZE? or present a more elegant way? At least make it work!##################################################################
                #If Fresnel gets removed from 2.5, why bother?
                if material.diffuse_shader == 'FRESNEL':
                    
######END of part TO OPTIMIZE? or present a more elegant way?##################################################################

##                        #lampLocation=lamp.position
##                        lampRotation=
##                        a=lamp.Rotation[0]
##                        b=lamp.Rotation[1]
##                        c=lamp.Rotation[2]
##                        lampLookAt=tuple (x,y,z)
##                        lampLookAt[3]= 0.0 #Put "target" of the lamp on the floor plane to elimianate one unknown value
##                                   degrees(atan((lampLocation - lampLookAt).y/(lampLocation - lampLookAt).z))=lamp.rotation[0]
##                                   degrees(atan((lampLocation - lampLookAt).z/(lampLocation - lampLookAt).x))=lamp.rotation[1]
##                                   degrees(atan((lampLocation - lampLookAt).x/(lampLocation - lampLookAt).y))=lamp.rotation[2]
##                        degrees(atan((lampLocation - lampLookAt).y/(lampLocation.z))=lamp.rotation[0]
##                        degrees(atan((lampLocation.z/(lampLocation - lampLookAt).x))=lamp.rotation[1]
##                        degrees(atan((lampLocation - lampLookAt).x/(lampLocation - lampLookAt).y))=lamp.rotation[2]
                     

                                #color = tuple([c * lamp.energy for c in lamp.color]) # Colour is modified by energy                        
                        

                    file.write('\n\t\t\tslope { lampTarget }')
                    file.write('\n\t\t\ttexture_map {')
                    file.write('\n\t\t\t\t[%.3g finish {diffuse %.3g}]' % ((material.diffuse_fresnel/2), (2-material.diffuse_fresnel_factor)))
                    file.write('\n\t\t\t\t[%.3g' % (1-(material.diffuse_fresnel/2)))
              
                
                #if material.diffuse_shader == 'FRESNEL': pigment pattern aoi pigment and texture map above, the rest below as one of its entry
                ##########################################################################################################################            
                if texturesSpec !='':
                    file.write('\n\t\t\t\tpigment_pattern {')
                    mappingSpec = (" translate <%.4g-0.75,%.4g-0.75,%.4g-0.75> scale <%.4g,%.4g,%.4g>" % (t_spec.offset.x / 10 ,t_spec.offset.y / 10 ,t_spec.offset.z / 10, t_spec.scale.x / 2.25, t_spec.scale.y / 2.25, t_spec.scale.z / 2.25)) #strange that the translation factor for scale is not the same as for translate. ToDo: verify both matches with blender internal. 
                    file.write('\n\t\t\t\t\tuv_mapping image_map{%s \"%s\" %s}%s}' % (imageFormat(texturesSpec) ,texturesSpec ,imgMap(t_spec),mappingSpec))
                    file.write('\n\t\t\t\t\t\ttexture_map {')
                    file.write('\n\t\t\t\t\t\t\t[0 ')

                if texturesDif == '':
                    if texturesAlpha !='':
                        mappingAlpha = (" translate <%.4g-0.75,%.4g-0.75,%.4g-0.75> scale <%.4g,%.4g,%.4g>" % (t_alpha.offset.x / 10 ,t_alpha.offset.y / 10 ,t_alpha.offset.z / 10, t_alpha.scale.x / 2.25, t_alpha.scale.y / 2.25, t_alpha.scale.z / 2.25)) #strange that the translation factor for scale is not the same as for translate. ToDo: verify both matches with blender internal. 
                        file.write('\n\t\t\t\tpigment {pigment_pattern {uv_mapping image_map{%s \"%s\" %s}%s}' % (imageFormat(texturesAlpha) ,texturesAlpha ,imgMap(t_alpha),mappingAlpha))
                        file.write('\n\t\t\t\t\tpigment_map {')
                        file.write('\n\t\t\t\t\t\t[0 color rgbft<0,0,0,1,1>]')
                        file.write('\n\t\t\t\t\t\t[1 color rgbft<%.3g, %.3g, %.3g, %.3g, %.3g>]\n\t\t\t\t\t}' % (col[0], col[1], col[2], 1.0 - material.alpha, trans))
                        file.write('\n\t\t\t\t}')

                    else:

                        file.write('\n\t\t\t\tpigment {rgbft<%.3g, %.3g, %.3g, %.3g, %.3g>}' % (col[0], col[1], col[2], 1.0 - material.alpha, trans))

                    if texturesSpec !='':
                        file.write('finish {%s}' % (safety0(material_finish)))
                        
                    else:
                        file.write('finish {%s}' % (safety(material_finish)))

                else:
                    mappingDif = (" translate <%.4g-0.75,%.4g-0.75,%.4g-0.75> scale <%.4g,%.4g,%.4g>" % (t_dif.offset.x / 10 ,t_dif.offset.y / 10 ,t_dif.offset.z / 10, t_dif.scale.x / 2.25, t_dif.scale.y / 2.25, t_dif.scale.z / 2.25)) #strange that the translation factor for scale is not the same as for translate. ToDo: verify both matches with blender internal. 

                    if texturesAlpha !='':
                        mappingAlpha = (" translate <%.4g-0.75,%.4g-0.75,%.4g-0.75> scale <%.4g,%.4g,%.4g>" % (t_alpha.offset.x / 10 ,t_alpha.offset.y / 10 ,t_alpha.offset.z / 10, t_alpha.scale.x / 2.25, t_alpha.scale.y / 2.25, t_alpha.scale.z / 2.25)) #strange that the translation factor for scale is not the same as for translate. ToDo: verify both matches with blender internal. 
                        file.write('\n\t\t\t\tpigment {pigment_pattern {uv_mapping image_map{%s \"%s\" %s}%s}' % (imageFormat(texturesAlpha),texturesAlpha,imgMap(t_alpha),mappingAlpha))
                        file.write('\n\t\t\t\t\tpigment_map {\n\t\t\t\t\t\t[0 color rgbft<0,0,0,1,1>]')
                        file.write('\n\t\t\t\t\t\t[1 uv_mapping image_map {%s \"%s\" %s}%s]\n\t\t\t\t}' % (imageFormat(texturesDif),texturesDif,imgMap(t_dif),mappingDif))
                        file.write('\n\t\t\t\t}')

                    else:
                        file.write("\n\t\t\t\tpigment {uv_mapping image_map {%s \"%s\" %s}%s}" % (imageFormat(texturesDif),texturesDif,imgMap(t_dif),mappingDif))

                    if texturesSpec !='':
                        file.write('finish {%s}' % (safety0(material_finish)))
                            
                    else:
                        file.write('finish {%s}' % (safety(material_finish)))

                    ## scale 1 rotate y*0
                    #imageMap = ("{image_map {%s \"%s\" %s }" % (imageFormat(textures),textures,imgMap(t_dif)))
                    #file.write("\n\t\t\tuv_mapping pigment %s} %s finish {%s}" % (imageMap,mapping,safety(material_finish)))
                    #file.write("\n\t\t\tpigment {uv_mapping image_map {%s \"%s\" %s}%s} finish {%s}" % (imageFormat(texturesDif),texturesDif,imgMap(t_dif),mappingDif,safety(material_finish)))
                if texturesNorm !='':
                    ## scale 1 rotate y*0
                    mappingNor = (" translate <%.4g-0.75,%.4g-0.75,%.4g-0.75> scale <%.4g,%.4g,%.4g>" % (t_nor.offset.x / 10 ,t_nor.offset.y / 10 ,t_nor.offset.z / 10, t_nor.scale.x / 2.25, t_nor.scale.y / 2.25, t_nor.scale.z / 2.25))
                    #imageMapNor = ("{bump_map {%s \"%s\" %s mapping}" % (imageFormat(texturesNorm),texturesNorm,imgMap(t_nor)))
                    #We were not using the above maybe we should?
                    file.write("\n\t\t\t\tnormal {uv_mapping bump_map {%s \"%s\" %s  bump_size %.4g }%s}" % (imageFormat(texturesNorm),texturesNorm,imgMap(t_nor),(t_nor.normal_factor * 10),mappingNor))
                if texturesSpec !='':                
                    file.write('\n\t\t\t\t\t\t\t]')
                ################################Second index for mapping specular max value##################################################################################################
                    file.write('\n\t\t\t\t\t\t\t[1 ')

                if texturesDif == '':
                    if texturesAlpha !='':
                        mappingAlpha = (" translate <%.4g-0.75,%.4g-0.75,%.4g-0.75> scale <%.4g,%.4g,%.4g>" % (t_alpha.offset.x / 10 ,t_alpha.offset.y / 10 ,t_alpha.offset.z / 10, t_alpha.scale.x / 2.25, t_alpha.scale.y / 2.25, t_alpha.scale.z / 2.25)) #strange that the translation factor for scale is not the same as for translate. ToDo: verify both matches with blender internal. 
                        file.write('\n\t\t\t\tpigment {pigment_pattern {uv_mapping image_map{%s \"%s\" %s}%s}' % (imageFormat(texturesAlpha) ,texturesAlpha ,imgMap(t_alpha),mappingAlpha))
                        file.write('\n\t\t\t\t\tpigment_map {')
                        file.write('\n\t\t\t\t\t\t[0 color rgbft<0,0,0,1,1>]')
                        file.write('\n\t\t\t\t\t\t[1 color rgbft<%.3g, %.3g, %.3g, %.3g, %.3g>]\n\t\t\t\t\t}' % (col[0], col[1], col[2], 1.0 - material.alpha, trans))
                        file.write('\n\t\t\t\t}')

                    else:
                        file.write('\n\t\t\t\tpigment {rgbft<%.3g, %.3g, %.3g, %.3g, %.3g>}' % (col[0], col[1], col[2], 1.0 - material.alpha, trans))

                    if texturesSpec !='':
                        file.write('finish {%s}' % (safety1(material_finish)))
                        
                    else:
                        file.write('finish {%s}' % (safety(material_finish)))

                else:
                    mappingDif = (" translate <%.4g-0.75,%.4g-0.75,%.4g-0.75> scale <%.4g,%.4g,%.4g>" % (t_dif.offset.x / 10 ,t_dif.offset.y / 10 ,t_dif.offset.z / 10, t_dif.scale.x / 2.25, t_dif.scale.y / 2.25, t_dif.scale.z / 2.25)) #strange that the translation factor for scale is not the same as for translate. ToDo: verify both matches with blender internal. 

                    if texturesAlpha !='':
                        mappingAlpha = (" translate <%.4g-0.75,%.4g-0.75,%.4g-0.75> scale <%.4g,%.4g,%.4g>" % (t_alpha.offset.x / 10 ,t_alpha.offset.y / 10 ,t_alpha.offset.z / 10, t_alpha.scale.x / 2.25, t_alpha.scale.y / 2.25, t_alpha.scale.z / 2.25)) #strange that the translation factor for scale is not the same as for translate. ToDo: verify both matches with blender internal. 
                        file.write('\n\t\t\t\tpigment {pigment_pattern {uv_mapping image_map{%s \"%s\" %s}%s}' % (imageFormat(texturesAlpha),texturesAlpha,imgMap(t_alpha),mappingAlpha))
                        file.write('\n\t\t\t\tpigment_map {\n\t\t\t\t\t[0 color rgbft<0,0,0,1,1>]')
                        file.write('\n\t\t\t\t\t\t[1 uv_mapping image_map {%s \"%s\" %s}%s]\n\t\t\t\t\t}' % (imageFormat(texturesDif),texturesDif,imgMap(t_dif),mappingDif))
                        file.write('\n\t\t\t\t}')

                    else:
                        file.write("\n\t\t\tpigment {uv_mapping image_map {%s \"%s\" %s}%s}" % (imageFormat(texturesDif),texturesDif,imgMap(t_dif),mappingDif))
                    if texturesSpec !='':
                        file.write('finish {%s}' % (safety1(material_finish)))
                    else:
                        file.write('finish {%s}' % (safety(material_finish)))

                    ## scale 1 rotate y*0
                    #imageMap = ("{image_map {%s \"%s\" %s }" % (imageFormat(textures),textures,imgMap(t_dif)))
                    #file.write("\n\t\t\tuv_mapping pigment %s} %s finish {%s}" % (imageMap,mapping,safety(material_finish)))
                    #file.write("\n\t\t\tpigment {uv_mapping image_map {%s \"%s\" %s}%s} finish {%s}" % (imageFormat(texturesDif),texturesDif,imgMap(t_dif),mappingDif,safety(material_finish)))
                if texturesNorm !='':
                    ## scale 1 rotate y*0
                    mappingNor = (" translate <%.4g-0.75,%.4g-0.75,%.4g-0.75> scale <%.4g,%.4g,%.4g>" % (t_nor.offset.x / 10 ,t_nor.offset.y / 10 ,t_nor.offset.z / 10, t_nor.scale.x / 2.25, t_nor.scale.y / 2.25, t_nor.scale.z / 2.25))
                    #imageMapNor = ("{bump_map {%s \"%s\" %s mapping}" % (imageFormat(texturesNorm),texturesNorm,imgMap(t_nor)))
                    #We were not using the above maybe we should?
                    file.write("\n\t\t\t\tnormal {uv_mapping bump_map {%s \"%s\" %s  bump_size %.4g }%s}" % (imageFormat(texturesNorm),texturesNorm,imgMap(t_nor),(t_nor.normal_factor * 10),mappingNor))
                if texturesSpec !='':                
                    file.write('\n\t\t\t\t\t\t\t]')

                    file.write('\n\t\t\t\t}') 

                #End of slope/ior texture_map
                if material.diffuse_shader == 'MINNAERT' or material.diffuse_shader == 'FRESNEL':
                    file.write('\n\t\t\t\t]')
                    file.write('\n\t\t\t}')                          
                file.write('\n\t\t}') #THEN IT CAN CLOSE IT   --MR
                

                ############################################################################################################

                index[0] = idx
                idx += 1

            file.write('\n\t}\n')

            # Face indicies
            file.write('\tface_indices {\n')
            file.write('\t\t%d' % (len(me.faces) + quadCount)) # faces count
            for fi, f in enumerate(me.faces):
                fv = faces_verts[fi]
                material_index = f.material_index
                if len(fv) == 4:
                    indicies = (0, 1, 2), (0, 2, 3)
                else:
                    indicies = ((0, 1, 2),)

                if vcol_layer:
                    col = vcol_layer[fi]

                    if len(fv) == 4:
                        cols = col.color1, col.color2, col.color3, col.color4
                    else:
                        cols = col.color1, col.color2, col.color3


                if not me_materials or me_materials[material_index] is None: # No materials
                    for i1, i2, i3 in indicies:
                        file.write(',\n\t\t<%d,%d,%d>' % (fv[i1], fv[i2], fv[i3])) # vert count
                else:
                    material = me_materials[material_index]
                    for i1, i2, i3 in indicies:
                        if me.vertex_colors and material.use_vertex_color_paint:
                            # Colour per vertex - vertex colour

                            col1 = cols[i1]
                            col2 = cols[i2]
                            col3 = cols[i3]

                            ci1 = vertCols[col1[0], col1[1], col1[2], material_index][0]
                            ci2 = vertCols[col2[0], col2[1], col2[2], material_index][0]
                            ci3 = vertCols[col3[0], col3[1], col3[2], material_index][0]
                        else:
                            # Colour per material - flat material colour
                            diffuse_color = material.diffuse_color
                            ci1 = ci2 = ci3 = vertCols[diffuse_color[0], diffuse_color[1], diffuse_color[2], f.material_index][0]

                        file.write(',\n\t\t<%d,%d,%d>, %d,%d,%d' % (fv[i1], fv[i2], fv[i3], ci1, ci2, ci3)) # vert count


            file.write('\n  }\n')

            # normal_indices indicies
            file.write('\tnormal_indices {\n')
            file.write('\t\t%d' % (len(me.faces) + quadCount)) # faces count
            for fi, fv in enumerate(faces_verts):

                if len(fv) == 4:
                    indicies = (0, 1, 2), (0, 2, 3)
                else:
                    indicies = ((0, 1, 2),)

                for i1, i2, i3 in indicies:
                    if f.use_smooth:
                        file.write(',\n\t\t<%d,%d,%d>' %\
                        (uniqueNormals[verts_normals[fv[i1]]][0],\
                         uniqueNormals[verts_normals[fv[i2]]][0],\
                         uniqueNormals[verts_normals[fv[i3]]][0])) # vert count
                    else:
                        idx = uniqueNormals[faces_normals[fi]][0]
                        file.write(',\n\t\t<%d,%d,%d>' % (idx, idx, idx)) # vert count

            file.write('\n  }\n')

            if uv_layer:
                file.write('\tuv_indices {\n')
                file.write('\t\t%d' % (len(me.faces) + quadCount)) # faces count
                for fi, fv in enumerate(faces_verts):

                    if len(fv) == 4:
                        indicies = (0, 1, 2), (0, 2, 3)
                    else:
                        indicies = ((0, 1, 2),)

                    uv = uv_layer[fi]
                    if len(faces_verts[fi]) == 4:
                        uvs = tuple(uv.uv1), tuple(uv.uv2), tuple(uv.uv3), tuple(uv.uv4)
                    else:
                        uvs = tuple(uv.uv1), tuple(uv.uv2), tuple(uv.uv3)

                    for i1, i2, i3 in indicies:
                        file.write(',\n\t\t<%d,%d,%d>' %\
                        (uniqueUVs[uvs[i1]][0],\
                         uniqueUVs[uvs[i2]][0],\
                         uniqueUVs[uvs[i3]][0]))
                file.write('\n  }\n')

            if me.materials:
                try:
                    material = me.materials[0] # dodgy
                    writeObjectMaterial(material)
                except IndexError:
                    print(me)

            writeMatrix(matrix)
            file.write('}\n')

            bpy.data.meshes.remove(me)

    def exportWorld(world):
        camera = scene.camera
        matrix = camera.matrix_world
        if not world:
            return
        #############Maurice#################################### 
        #These lines added to get sky gradient (visible with PNG output)
        if world:
            #For simple flat background:
            if not world.use_sky_blend:
                file.write('background {rgbt<%.3g, %.3g, %.3g, 1>}\n' % (tuple(world.horizon_color)))#Non fully transparent background could premultiply alpha and avoid anti-aliasing problem. Put transmit to 1 reveals pov problem with nonpremult antialiased.

            #For Background image textures
            for t in world.texture_slots: #risk to write several sky_spheres but maybe ok.
                if t and t.texture.type == 'IMAGE': #and t.use: #No enable checkbox for world textures yet (report it?)
                    image_filename  = path_image(t.texture.image.filepath)
                    if t.texture.image.filepath != image_filename: t.texture.image.filepath = image_filename
                    if image_filename != '' and t.use_map_blend: 
                        texturesBlend = image_filename
                        #colvalue = t.default_value
                        t_blend = t
                    #commented below was an idea to make the Background image oriented as camera taken here: http://news.povray.org/povray.newusers/thread/%3Cweb.4a5cddf4e9c9822ba2f93e20@news.povray.org%3E/
                    #mappingBlend = (" translate <%.4g,%.4g,%.4g> rotate z*degrees(atan((camLocation - camLookAt).x/(camLocation - camLookAt).y)) rotate x*degrees(atan((camLocation - camLookAt).y/(camLocation - camLookAt).z)) rotate y*degrees(atan((camLocation - camLookAt).z/(camLocation - camLookAt).x)) scale <%.4g,%.4g,%.4g>b" % (t_blend.offset.x / 10 ,t_blend.offset.y / 10 ,t_blend.offset.z / 10, t_blend.scale.x ,t_blend.scale.y ,t_blend.scale.z))#replace 4/3 by the ratio of each image found by some custom or existing function
                    #using camera rotation valuesdirectly from blender seems much easier
                    mappingBlend = (" translate <%.4g-0.5,%.4g-0.5,%.4g-0.5> rotate<%.4g,%.4g,%.4g>  scale <%.4g,%.4g,%.4g>" % (t_blend.offset.x / 10 ,t_blend.offset.y / 10 ,t_blend.offset.z / 10, degrees(camera.rotation_euler[0]), degrees(camera.rotation_euler[1]), degrees(camera.rotation_euler[2]), t_blend.scale.x*0.85 , t_blend.scale.y*0.85 , t_blend.scale.z*0.85 ))
                    #Putting the map on a plane would not introduce the skysphere distortion and allow for better image scale matching but also some waay to chose depth and size of the plane relative to camera.
                    file.write('sky_sphere {\n')            
                    file.write('\tpigment {\n')
                    file.write("\t\timage_map{%s \"%s\" %s}\n\t}\n\t%s\n" % (imageFormat(texturesBlend),texturesBlend,imgMapBG(t_blend),mappingBlend))
                    file.write('}\n')  
                    #file.write('\t\tscale 2\n')
                    #file.write('\t\ttranslate -1\n')
      
            #For only Background gradient        
        
            if not t:
                if world.use_sky_blend:
                    file.write('sky_sphere {\n')            
                    file.write('\tpigment {\n')
                    file.write('\t\tgradient z\n')#maybe Should follow the advice of POV doc about replacing gradient for skysphere..5.5
                    file.write('\t\tcolor_map {\n')
                    file.write('\t\t\t[0.0 rgbt<%.3g, %.3g, %.3g, 1>]\n' % (tuple(world.zenith_color)))           
                    file.write('\t\t\t[1.0 rgbt<%.3g, %.3g, %.3g, 0.99>]\n' % (tuple(world.horizon_color))) #aa premult not solved with transmit 1
                    file.write('\t\t}\n')
                    file.write('\t}\n')
                    file.write('}\n')
                    #problem with sky_sphere alpha (transmit) not translating into image alpha as well as "background" replace 0.75 by 1 when solved and later by some variable linked to background alpha state

            if world.light_settings.use_indirect_light:
                scene.pov_radio_enable=1
                



        ###############################################################

        mist = world.mist_settings

        if mist.use_mist:
            file.write('fog {\n')
            file.write('\tdistance %.6f\n' % mist.depth)
            file.write('\tcolor rgbt<%.3g, %.3g, %.3g, %.3g>\n' % (tuple(world.horizon_color) + (1 - mist.intensity,)))
            #file.write('\tfog_offset %.6f\n' % mist.start)
            #file.write('\tfog_alt 5\n')
            #file.write('\tturbulence 0.2\n')
            #file.write('\tturb_depth 0.3\n')
            file.write('\tfog_type 1\n')
            file.write('}\n')

    def exportGlobalSettings(scene):

        file.write('global_settings {\n')
        file.write('\tmax_trace_level 7\n')

        if scene.pov_radio_enable:
            file.write('\tradiosity {\n')
            file.write("\t\tadc_bailout %.4g\n" % scene.pov_radio_adc_bailout)
            file.write("\t\talways_sample %d\n" % scene.pov_radio_always_sample)
            file.write("\t\tbrightness %.4g\n" % scene.pov_radio_brightness)
            file.write("\t\tcount %d\n" % scene.pov_radio_count)
            file.write("\t\terror_bound %.4g\n" % scene.pov_radio_error_bound)
            file.write("\t\tgray_threshold %.4g\n" % scene.pov_radio_gray_threshold)
            file.write("\t\tlow_error_factor %.4g\n" % scene.pov_radio_low_error_factor)
            file.write("\t\tmedia %d\n" % scene.pov_radio_media)
            file.write("\t\tminimum_reuse %.4g\n" % scene.pov_radio_minimum_reuse)
            file.write("\t\tnearest_count %d\n" % scene.pov_radio_nearest_count)
            file.write("\t\tnormal %d\n" % scene.pov_radio_normal)
            file.write("\t\trecursion_limit %d\n" % scene.pov_radio_recursion_limit)
            file.write('\t}\n')
        once=1
        for material in bpy.data.materials:
            if material.subsurface_scattering.use and once:
                file.write("\tmm_per_unit %.6f\n" % (material.subsurface_scattering.scale * (-100) + 15))#In pov, the scale has reversed influence compared to blender. these number should correct that
                once=0 #In povray, the scale factor for all subsurface shaders needs to be the same

        if world: 
            file.write("\tambient_light rgb<%.3g, %.3g, %.3g>\n" % tuple(world.ambient_color))

        if material.pov_photons_refraction or material.pov_photons_reflection:
            file.write("\tphotons {\n")
            file.write("\t\tspacing 0.003\n")
            file.write("\t\tmax_trace_level 4\n")
            file.write("\t\tadc_bailout 0.1\n")
            file.write("\t\tgather 30, 150\n")

            
            file.write("\t}\n")

        file.write('}\n')


    # Convert all materials to strings we can access directly per vertex.
    writeMaterial(None) # default material

    for material in bpy.data.materials:
        writeMaterial(material)

    exportCamera()
    #exportMaterials()
    sel = scene.objects
    exportLamps([l for l in sel if l.type == 'LAMP'])
    exportMeta([l for l in sel if l.type == 'META'])
    exportMeshs(scene, sel)
    exportWorld(scene.world)
    exportGlobalSettings(scene)

    file.close()
    


def write_pov_ini(filename_ini, filename_pov, filename_image):
    scene = bpy.data.scenes[0]
    render = scene.render

    x = int(render.resolution_x * render.resolution_percentage * 0.01)
    y = int(render.resolution_y * render.resolution_percentage * 0.01)

    file = open(filename_ini, 'w')

    file.write('Input_File_Name="%s"\n' % filename_pov)
    file.write('Output_File_Name="%s"\n' % filename_image)

    file.write('Width=%d\n' % x)
    file.write('Height=%d\n' % y)

    # Needed for border render.
    '''
    file.write('Start_Column=%d\n' % part.x)
    file.write('End_Column=%d\n' % (part.x+part.w))

    file.write('Start_Row=%d\n' % (part.y))
    file.write('End_Row=%d\n' % (part.y+part.h))
    '''

    file.write('Bounding_method=2\n')#The new automatic BSP is faster in most scenes

    file.write('Display=1\n')#Activated (turn this back off when better live exchange is done between the two programs (see next comment)
    file.write('Pause_When_Done=0\n')
    file.write('Output_File_Type=N\n') # PNG, with POV 3.7, can show background color with alpha. In the long run using the Povray interactive preview like bishop 3D could solve the preview for all formats. 
    #file.write('Output_File_Type=T\n') # TGA, best progressive loading
    file.write('Output_Alpha=1\n')

    if render.use_antialiasing:
        aa_mapping = {'5': 2, '8': 3, '11': 4, '16': 5} # method 2 (recursive) with higher max subdiv forced because no mipmapping in povray needs higher sampling.
        file.write('Antialias=1\n')
        file.write('Sampling_Method=2n')
        file.write('Antialias_Depth=%d\n' % aa_mapping[render.antialiasing_samples])
        file.write('Antialias_Threshold=0.1\n')#rather high settings but necessary.
        file.write('Jitter=off\n')#prevent animation flicker
 
    else:
        file.write('Antialias=0\n')

    file.close()


class PovrayRender(bpy.types.RenderEngine):
    bl_idname = 'POVRAY_RENDER'
    bl_label = "Povray 3.7"
    DELAY = 0.02

    def _export(self, scene):
        import tempfile

        self._temp_file_in = tempfile.mktemp(suffix='.pov')
        self._temp_file_out = tempfile.mktemp(suffix='.png')#PNG with POV 3.7, can show the background color with alpha. In the long run using the Povray interactive preview like bishop 3D could solve the preview for all formats.
        #self._temp_file_out = tempfile.mktemp(suffix='.tga')
        self._temp_file_ini = tempfile.mktemp(suffix='.ini')
        '''
        self._temp_file_in = '/test.pov'
        self._temp_file_out = '/test.png'#PNG with POV 3.7, can show the background color with alpha. In the long run using the Povray interactive preview like bishop 3D could solve the preview for all formats.
        #self._temp_file_out = '/test.tga'
        self._temp_file_ini = '/test.ini'
        '''

        def info_callback(txt):
            self.update_stats("", "POVRAY 3.7: " + txt)

        write_pov(self._temp_file_in, scene, info_callback)

    def _render(self):

        try:
            os.remove(self._temp_file_out) # so as not to load the old file
        except:
            pass

        write_pov_ini(self._temp_file_ini, self._temp_file_in, self._temp_file_out)

        print ("***-STARTING-***")

        pov_binary = "povray"

        if sys.platform == 'win32':
            import winreg
            regKey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Software\\POV-Ray\\v3.7\\Windows')

            if bitness == 64:
                pov_binary = winreg.QueryValueEx(regKey, 'Home')[0] + '\\bin\\pvengine64'
            else:
                pov_binary = winreg.QueryValueEx(regKey, 'Home')[0] + '\\bin\\pvengine'

        if 1:
            # TODO, when povray isnt found this gives a cryptic error, would be nice to be able to detect if it exists
            try:
                self._process = subprocess.Popen([pov_binary, self._temp_file_ini]) # stdout=subprocess.PIPE, stderr=subprocess.PIPE
            except OSError:
                # TODO, report api
                print("POVRAY 3.7: could not execute '%s', possibly povray isn't installed" % pov_binary)
                import traceback
                traceback.print_exc()
                print ("***-DONE-***")
                return False

        else:
            # This works too but means we have to wait until its done
            os.system('%s %s' % (pov_binary, self._temp_file_ini))

        print ("***-DONE-***")
        return True

    def _cleanup(self):
        for f in (self._temp_file_in, self._temp_file_ini, self._temp_file_out):
            try:
                os.remove(f)
            except:
                pass

        self.update_stats("", "")

    def render(self, scene):

        self.update_stats("", "POVRAY 3.7: Exporting data from Blender")
        self._export(scene)
        self.update_stats("", "POVRAY 3.7: Parsing File")

        if not self._render():
            self.update_stats("", "POVRAY 3.7: Not found")
            return

        r = scene.render
##WIP output format 
##        if r.file_format == 'OPENEXR':
##            fformat = 'EXR'
##            render.color_mode = 'RGBA'
##        else:
##            fformat = 'TGA'
##            r.file_format = 'TARGA'            
##            r.color_mode = 'RGBA'

        # compute resolution
        x = int(r.resolution_x * r.resolution_percentage * 0.01)
        y = int(r.resolution_y * r.resolution_percentage * 0.01)

        # Wait for the file to be created
        while not os.path.exists(self._temp_file_out):
            if self.test_break():
                try:
                    self._process.terminate()
                except:
                    pass
                break

            if self._process.poll() != None:
                self.update_stats("", "POVRAY 3.7: Failed")
                break

            time.sleep(self.DELAY)

        if os.path.exists(self._temp_file_out):

            self.update_stats("", "POVRAY 3.7: Rendering")

            prev_size = -1

            def update_image():
                result = self.begin_result(0, 0, x, y)
                lay = result.layers[0]
                # possible the image wont load early on.
                try:
                    lay.load_from_file(self._temp_file_out)
                except:
                    pass
                self.end_result(result)

            # Update while povray renders
            while True:

                # test if povray exists
                if self._process.poll() is not None:
                    update_image()
                    break

                # user exit
                if self.test_break():
                    try:
                        self._process.terminate()
                    except:
                        pass

                    break

                # Would be nice to redirect the output
                # stdout_value, stderr_value = self._process.communicate() # locks


                # check if the file updated
                new_size = os.path.getsize(self._temp_file_out)

                if new_size != prev_size:
                    update_image()
                    prev_size = new_size

                time.sleep(self.DELAY)

        self._cleanup()


