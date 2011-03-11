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

# <pep8 compliant>

import bpy
import subprocess
import os
import sys
import time
from math import atan, pi, degrees, sqrt

##############################SF###########################
##############find image texture


def splitExt(path):
    dotidx = path.rfind(".")
    if dotidx == -1:
        return path, ""
    else:
        return path[dotidx:].upper().replace(".", "")


def imageFormat(imgF):
    ext = ""
    ext_orig = splitExt(imgF)
    if ext_orig == 'JPG' or ext_orig == 'JPEG':
        ext = "jpeg"
    elif ext_orig == 'GIF':
        ext = "gif"
    elif ext_orig == 'TGA':
        ext = "tga"
    elif ext_orig == 'IFF':
        ext = "iff"
    elif ext_orig == 'PPM':
        ext = "ppm"
    elif ext_orig == 'PNG':
        ext = "png"
    elif ext_orig == 'SYS':
        ext = "sys"
    elif ext_orig in ('TIFF', 'TIF'):
        ext = "tiff"
    elif ext_orig == 'EXR':
        ext = "exr"  # POV3.7 Only!
    elif ext_orig == 'HDR':
        ext = "hdr"  # POV3.7 Only! --MR

    print(imgF)
    if not ext:
        print(" WARNING: texture image format not supported ")  # % (imgF , "")) #(ext_orig)))

    return ext


def imgMap(ts):
    image_map = ""
    if ts.mapping == 'FLAT':
        image_map = "map_type 0 "
    elif ts.mapping == 'SPHERE':
        image_map = "map_type 1 "  # map_type 7 in megapov
    elif ts.mapping == 'TUBE':
        image_map = "map_type 2 "
    #elif ts.mapping=="?":
    #    image_map = " map_type 3 "  # map_type 3 and 4 in development (?) for POV-Ray, currently they just seem to default back to Flat (type 0)
    #elif ts.mapping=="?":
    #    image_map = " map_type 4 "  # map_type 3 and 4 in development (?) for POV-Ray, currently they just seem to default back to Flat (type 0)
    if ts.texture.use_interpolation:
        image_map += " interpolate 2 "
    if ts.texture.extension == 'CLIP':
        image_map += " once "
    #image_map += "}"
    #if ts.mapping=='CUBE':
    #    image_map+= "warp { cubic } rotate <-90,0,180>"  # no direct cube type mapping. Though this should work in POV 3.7 it doesn't give that good results(best suited to environment maps?)
    #if image_map == "":
    #    print(" No texture image  found ")
    return image_map


def imgMapBG(wts):
    image_mapBG = ""
    if wts.texture_coords == 'VIEW':
        image_mapBG = " map_type 0 "  # texture_coords refers to the mapping of world textures
    elif wts.texture_coords == 'ANGMAP':
        image_mapBG = " map_type 1 "
    elif wts.texture_coords == 'TUBE':
        image_mapBG = " map_type 2 "

    if wts.texture.use_interpolation:
        image_mapBG += " interpolate 2 "
    if wts.texture.extension == 'CLIP':
        image_mapBG += " once "
    #image_mapBG += "}"
    #if wts.mapping == 'CUBE':
    #   image_mapBG += "warp { cubic } rotate <-90,0,180>"  # no direct cube type mapping. Though this should work in POV 3.7 it doesn't give that good results(best suited to environment maps?)
    #if image_mapBG == "":
    #    print(" No background texture image  found ")
    return image_mapBG


def splitFile(path):
    idx = path.rfind("/")
    if idx == -1:
        idx = path.rfind("\\")
    return path[idx:].replace("/", "").replace("\\", "")


def splitPath(path):
    idx = path.rfind("/")
    if idx == -1:
        return path, ""
    else:
        return path[:idx]


def findInSubDir(filename, subdirectory=""):
    pahFile = ""
    if subdirectory:
        path = subdirectory
    else:
        path = os.getcwd()
    try:
        for root, dirs, names in os.walk(path):
            if filename in names:
                pahFile = os.path.join(root, filename)
        return pahFile
    except OSError:
        return ""


def path_image(image):
    import os
    fn = bpy.path.abspath(image)
    fn_strip = os.path.basename(fn)
    if not os.path.isfile(fn):
        fn = findInSubDir(splitFile(fn), splitPath(bpy.data.filepath))
    fn = os.path.realpath(fn)
    return fn

##############end find image texture


def splitHyphen(name):
    hyphidx = name.find("-")
    if hyphidx == -1:
        return name
    else:
        return name[hyphidx:].replace("-", "")


def safety(name, Level):
    # safety string name material
    #
    # Level=1 is for texture with No specular nor Mirror reflection
    # Level=2 is for texture with translation of spec and mir levels for when no map influences them
    # Level=3 is for texture with Maximum Spec and Mirror

    try:
        if int(name) > 0:
            prefix = "shader"
    except:
        prefix = ""
    prefix = "shader_"
    name = splitHyphen(name)
    if Level == 2:
        return prefix + name
    elif Level == 1:
        return prefix + name + "0"  # used for 0 of specular map
    elif Level == 3:
        return prefix + name + "1"  # used for 1 of specular map


##############end safety string name material
##############################EndSF###########################


tabLevel = 0


def write_pov(filename, scene=None, info_callback=None):
    import mathutils
    #file = filename
    file = open(filename, "w")

    # Only for testing
    if not scene:
        scene = bpy.data.scenes[0]

    render = scene.render
    world = scene.world
    global_matrix = mathutils.Matrix.Rotation(-pi / 2.0, 4, 'X')

    def setTab(tabtype, spaces):
        TabStr = ""
        if tabtype == '0':
            TabStr = ""
        elif tabtype == '1':
            TabStr = "\t"
        elif tabtype == '2':
            TabStr = spaces * " "
        return TabStr

    tab = setTab(scene.pov_indentation_character, scene.pov_indentation_spaces)

    def tabWrite(str_o):
        if not scene.pov_tempfiles_enable:
            global tabLevel
            brackets = str_o.count("{") - str_o.count("}") + str_o.count("[") - str_o.count("]")
            if brackets < 0:
                tabLevel = tabLevel + brackets
            if tabLevel < 0:
                print("Indentation Warning: tabLevel = %s" % tabLevel)
                tabLevel = 0
            if tabLevel >= 1:
                file.write("%s" % tab * tabLevel)
            file.write(str_o)
            if brackets > 0:
                tabLevel = tabLevel + brackets
        else:
            file.write(str_o)

    def uniqueName(name, nameSeq):

        if name not in nameSeq:
            return name

        name_orig = name
        i = 1
        while name in nameSeq:
            name = "%s_%.3d" % (name_orig, i)
            i += 1
        name = splitHyphen(name)
        return name

    def writeMatrix(matrix):
        tabWrite("matrix <%.6f, %.6f, %.6f,  %.6f, %.6f, %.6f,  %.6f, %.6f, %.6f,  %.6f, %.6f, %.6f>\n" %\
        (matrix[0][0], matrix[0][1], matrix[0][2], matrix[1][0], matrix[1][1], matrix[1][2], matrix[2][0], matrix[2][1], matrix[2][2], matrix[3][0], matrix[3][1], matrix[3][2]))

    def writeObjectMaterial(material, ob):

        # DH - modified some variables to be function local, avoiding RNA write
        # this should be checked to see if it is functionally correct

        if material:  # and material.transparency_method == 'RAYTRACE':  # Commented out: always write IOR to be able to use it for SSS, Fresnel reflections...
            # But there can be only one!
            if material.subsurface_scattering.use:  # SSS IOR get highest priority
                tabWrite("interior {\n")
                tabWrite("ior %.6f\n" % material.subsurface_scattering.ior)
            elif material.pov_mirror_use_IOR:  # Then the raytrace IOR taken from raytrace transparency properties and used for reflections if IOR Mirror option is checked
                tabWrite("interior {\n")
                tabWrite("ior %.6f\n" % material.raytrace_transparency.ior)
            else:
                tabWrite("interior {\n")
                tabWrite("ior %.6f\n" % material.raytrace_transparency.ior)

            pov_fake_caustics = False
            pov_photons_refraction = False
            pov_photons_reflection = False

            if material.pov_photons_reflection:
                pov_photons_reflection = True
            if material.pov_refraction_type == "0":
                pov_fake_caustics = False
                pov_photons_refraction = False
            elif material.pov_refraction_type == "1":
                pov_fake_caustics = True
                pov_photons_refraction = False
            elif material.pov_refraction_type == "2":
                pov_fake_caustics = False
                pov_photons_refraction = True

            #If only Raytrace transparency is set, its IOR will be used for refraction, but user can set up 'un-physical' fresnel reflections in raytrace mirror parameters.
            #Last, if none of the above is specified, user can set up 'un-physical' fresnel reflections in raytrace mirror parameters. And pov IOR defaults to 1.
            if material.pov_caustics_enable:
                if pov_fake_caustics:
                    tabWrite("caustics %.3g\n" % material.pov_fake_caustics_power)
                if pov_photons_refraction:
                    tabWrite("dispersion %.3g\n" % material.pov_photons_dispersion)  # Default of 1 means no dispersion
            #TODO
            # Other interior args
            if material.use_transparency and material.transparency_method == 'RAYTRACE':
                # fade_distance
                # In Blender this value has always been reversed compared to what tooltip says. 100.001 rather than 100 so that it does not get to 0
                # which deactivates the feature in POV
                tabWrite("fade_distance %.3g\n" % (100.001 - material.raytrace_transparency.depth_max))
                # fade_power
                tabWrite("fade_power %.3g\n" % material.raytrace_transparency.falloff)
                # fade_color
                tabWrite("fade_color <%.3g, %.3g, %.3g>\n" % material.pov_interior_fade_color[:])

            # (variable) dispersion_samples (constant count for now)
            tabWrite("}\n")
            if not ob.pov_collect_photons:
                tabWrite("photons{collect off}\n")

            if pov_photons_refraction or pov_photons_reflection:
                tabWrite("photons{\n")
                tabWrite("target\n")
                if pov_photons_refraction:
                    tabWrite("refraction on\n")
                if pov_photons_reflection:
                    tabWrite("reflection on\n")
                tabWrite("}\n")

    materialNames = {}
    DEF_MAT_NAME = "Default"

    def writeMaterial(material):
        # Assumes only called once on each material
        if material:
            name_orig = material.name
        else:
            name_orig = DEF_MAT_NAME

        name = materialNames[name_orig] = uniqueName(bpy.path.clean_name(name_orig), materialNames)
        comments = scene.pov_comments_enable

        ##################Several versions of the finish: Level conditions are variations for specular/Mirror texture channel map with alternative finish of 0 specular and no mirror reflection
        # Level=1 Means No specular nor Mirror reflection
        # Level=2 Means translation of spec and mir levels for when no map influences them
        # Level=3 Means Maximum Spec and Mirror

        def povHasnoSpecularMaps(Level):
            if Level == 1:
                tabWrite("#declare %s = finish {" % safety(name, Level=1))
                if not scene.pov_tempfiles_enable and comments:
                    file.write("  //No specular nor Mirror reflection\n")
                else:
                    tabWrite("\n")
            elif Level == 2:
                tabWrite("#declare %s = finish {" % safety(name, Level=2))
                if not scene.pov_tempfiles_enable and comments:
                    file.write("  //translation of spec and mir levels for when no map influences them\n")
                else:
                    tabWrite("\n")
            elif Level == 3:
                tabWrite("#declare %s = finish {" % safety(name, Level=3))
                if not scene.pov_tempfiles_enable and comments:
                    file.write("  //Maximum Spec and Mirror\n")
                else:
                    tabWrite("\n")

            if material:
                #POV-Ray 3.7 now uses two diffuse values respectively for front and back shading (the back diffuse is like blender translucency)
                frontDiffuse = material.diffuse_intensity
                backDiffuse = material.translucency

                if material.pov_conserve_energy:

                    #Total should not go above one
                    if (frontDiffuse + backDiffuse) <= 1.0:
                        pass
                    elif frontDiffuse == backDiffuse:
                        frontDiffuse = backDiffuse = 0.5  # Try to respect the user's 'intention' by comparing the two values but bringing the total back to one
                    elif frontDiffuse > backDiffuse:  # Let the highest value stay the highest value
                        backDiffuse = min(backDiffuse, (1.0 - frontDiffuse))  # clamps the sum below 1
                    else:
                        frontDiffuse = min(frontDiffuse, (1.0 - backDiffuse))

                # map hardness between 0.0 and 1.0
                roughness = ((1.0 - ((material.specular_hardness - 1.0) / 510.0)))
                ## scale from 0.0 to 0.1
                roughness *= 0.1
                # add a small value because 0.0 is invalid
                roughness += (1.0 / 511.0)

                #####################################Diffuse Shader######################################
                # Not used for Full spec (Level=3) of the shader
                if material.diffuse_shader == 'OREN_NAYAR' and Level != 3:
                    tabWrite("brilliance %.3g\n" % (0.9 + material.roughness))  # blender roughness is what is generally called oren nayar Sigma, and brilliance in POV-Ray

                if material.diffuse_shader == 'TOON' and Level != 3:
                    tabWrite("brilliance %.3g\n" % (0.01 + material.diffuse_toon_smooth * 0.25))
                    frontDiffuse *= 0.5  # Lower diffuse and increase specular for toon effect seems to look better in POV-Ray

                if material.diffuse_shader == 'MINNAERT' and Level != 3:
                    #tabWrite("aoi %.3g\n" % material.darkness)
                    pass  # let's keep things simple for now
                if material.diffuse_shader == 'FRESNEL' and Level != 3:
                    #tabWrite("aoi %.3g\n" % material.diffuse_fresnel_factor)
                    pass  # let's keep things simple for now
                if material.diffuse_shader == 'LAMBERT' and Level != 3:
                    tabWrite("brilliance 1.8\n")  # trying to best match lambert attenuation by that constant brilliance value

                if Level == 2:
                    ####################################Specular Shader######################################
                    if material.specular_shader == 'COOKTORR' or material.specular_shader == 'PHONG':  # No difference between phong and cook torrence in blender HaHa!
                        tabWrite("phong %.3g\n" % (material.specular_intensity))
                        tabWrite("phong_size %.3g\n" % (material.specular_hardness / 2 + 0.25))

                    elif material.specular_shader == 'BLINN':  # POV-Ray 'specular' keyword corresponds to a Blinn model, without the ior.
                        tabWrite("specular %.3g\n" % (material.specular_intensity * (material.specular_ior / 4.0)))  # Use blender Blinn's IOR just as some factor for spec intensity
                        tabWrite("roughness %.3g\n" % roughness)
                        #Could use brilliance 2(or varying around 2 depending on ior or factor) too.

                    elif material.specular_shader == 'TOON':
                        tabWrite("phong %.3g\n" % (material.specular_intensity * 2))
                        tabWrite("phong_size %.3g\n" % (0.1 + material.specular_toon_smooth / 2))  # use extreme phong_size

                    elif material.specular_shader == 'WARDISO':
                        tabWrite("specular %.3g\n" % (material.specular_intensity / (material.specular_slope + 0.0005)))  # find best suited default constant for brilliance Use both phong and specular for some values.
                        tabWrite("roughness %.4g\n" % (0.0005 + material.specular_slope / 10.0))  # find best suited default constant for brilliance Use both phong and specular for some values.
                        tabWrite("brilliance %.4g\n" % (1.8 - material.specular_slope * 1.8))  # find best suited default constant for brilliance Use both phong and specular for some values.

                #########################################################################################
                elif Level == 1:
                    tabWrite("specular 0\n")
                elif Level == 3:
                    tabWrite("specular 1\n")
                tabWrite("diffuse %.3g %.3g\n" % (frontDiffuse, backDiffuse))

                tabWrite("ambient %.3g\n" % material.ambient)
                #tabWrite("ambient rgb <%.3g, %.3g, %.3g>\n" % tuple([c*material.ambient for c in world.ambient_color])) # POV-Ray blends the global value
                tabWrite("emission %.3g\n" % material.emit)  # New in POV-Ray 3.7

                #tabWrite("roughness %.3g\n" % roughness) #POV-Ray just ignores roughness if there's no specular keyword

                if material.pov_conserve_energy:
                    tabWrite("conserve_energy\n")  # added for more realistic shading. Needs some checking to see if it really works. --Maurice.

                # 'phong 70.0 '
                if Level != 1:
                    if material.raytrace_mirror.use:
                        raytrace_mirror = material.raytrace_mirror
                        if raytrace_mirror.reflect_factor:
                            tabWrite("reflection {\n")
                            tabWrite("rgb <%.3g, %.3g, %.3g>" % material.mirror_color[:])
                            if material.pov_mirror_metallic:
                                tabWrite("metallic %.3g" % (raytrace_mirror.reflect_factor))
                            if material.pov_mirror_use_IOR:  # WORKING ?
                                tabWrite("fresnel 1 ")  # Removed from the line below: gives a more physically correct material but needs proper IOR. --Maurice
                            tabWrite("falloff %.3g exponent %.3g} " % (raytrace_mirror.fresnel, raytrace_mirror.fresnel_factor))

                if material.subsurface_scattering.use:
                    subsurface_scattering = material.subsurface_scattering
                    tabWrite("subsurface { <%.3g, %.3g, %.3g>, <%.3g, %.3g, %.3g> }\n" % (
                             sqrt(subsurface_scattering.radius[0]) * 1.5,
                             sqrt(subsurface_scattering.radius[1]) * 1.5,
                             sqrt(subsurface_scattering.radius[2]) * 1.5,
                             1.0 - subsurface_scattering.color[0],
                             1.0 - subsurface_scattering.color[1],
                             1.0 - subsurface_scattering.color[2],
                             )
                            )

                if material.pov_irid_enable:
                    tabWrite("irid { %.4g thickness %.4g turbulence %.4g }" % (material.pov_irid_amount, material.pov_irid_thickness, material.pov_irid_turbulence))

            else:
                tabWrite("diffuse 0.8\n")
                tabWrite("phong 70.0\n")

                #tabWrite("specular 0.2\n")

            # This is written into the object
            '''
            if material and material.transparency_method=='RAYTRACE':
                'interior { ior %.3g} ' % material.raytrace_transparency.ior
            '''

            #tabWrite("crand 1.0\n") # Sand granyness
            #tabWrite("metallic %.6f\n" % material.spec)
            #tabWrite("phong %.6f\n" % material.spec)
            #tabWrite("phong_size %.6f\n" % material.spec)
            #tabWrite("brilliance %.6f " % (material.specular_hardness/256.0) # Like hardness

            tabWrite("}\n\n")

        # Level=2 Means translation of spec and mir levels for when no map influences them
        povHasnoSpecularMaps(Level=2)

        if material:
            special_texture_found = False
            for t in material.texture_slots:
                if t and t.texture.type == 'IMAGE' and t.use and t.texture.image and (t.use_map_specular or t.use_map_raymir or t.use_map_normal or t.use_map_alpha):
                    special_texture_found = True
                    continue  # Some texture found

            if special_texture_found:
                # Level=1 Means No specular nor Mirror reflection
                povHasnoSpecularMaps(Level=1)

                # Level=3 Means Maximum Spec and Mirror
                povHasnoSpecularMaps(Level=3)

    def exportCamera():
        camera = scene.camera

        # DH disabled for now, this isn't the correct context
        active_object = None  # bpy.context.active_object # does not always work  MR
        matrix = global_matrix * camera.matrix_world
        focal_point = camera.data.dof_distance

        # compute resolution
        Qsize = float(render.resolution_x) / float(render.resolution_y)
        tabWrite("#declare camLocation  = <%.6f, %.6f, %.6f>;\n" % (matrix[3][0], matrix[3][1], matrix[3][2]))
        tabWrite("#declare camLookAt = <%.6f, %.6f, %.6f>;\n" % tuple([degrees(e) for e in matrix.to_3x3().to_euler()]))

        tabWrite("camera {\n")
        if scene.pov_baking_enable and active_object and active_object.type == 'MESH':
            tabWrite("mesh_camera{ 1 3\n")  # distribution 3 is what we want here
            tabWrite("mesh{%s}\n" % active_object.name)
            tabWrite("}\n")
            tabWrite("location <0,0,.01>")
            tabWrite("direction <0,0,-1>")
        # Using standard camera otherwise
        else:
            tabWrite("location  <0, 0, 0>\n")
            tabWrite("look_at  <0, 0, -1>\n")
            tabWrite("right <%s, 0, 0>\n" % - Qsize)
            tabWrite("up <0, 1, 0>\n")
            tabWrite("angle  %f\n" % (360.0 * atan(16.0 / camera.data.lens) / pi))

            tabWrite("rotate  <%.6f, %.6f, %.6f>\n" % tuple([degrees(e) for e in matrix.to_3x3().to_euler()]))
            tabWrite("translate <%.6f, %.6f, %.6f>\n" % (matrix[3][0], matrix[3][1], matrix[3][2]))
            if camera.data.pov_dof_enable and focal_point != 0:
                tabWrite("aperture %.3g\n" % camera.data.pov_dof_aperture)
                tabWrite("blur_samples %d %d\n" % (camera.data.pov_dof_samples_min, camera.data.pov_dof_samples_max))
                tabWrite("variance 1/%d\n" % camera.data.pov_dof_variance)
                tabWrite("confidence %.3g\n" % camera.data.pov_dof_confidence)
                tabWrite("focal_point <0, 0, %f>\n" % focal_point)
        tabWrite("}\n")

    def exportLamps(lamps):
        # Get all lamps
        for ob in lamps:
            lamp = ob.data

            matrix = global_matrix * ob.matrix_world

            color = tuple([c * lamp.energy * 2.0 for c in lamp.color])  # Colour is modified by energy #muiltiplie by 2 for a better match --Maurice

            tabWrite("light_source {\n")
            tabWrite("< 0,0,0 >\n")
            tabWrite("color rgb<%.3g, %.3g, %.3g>\n" % color)

            if lamp.type == 'POINT':
                pass
            elif lamp.type == 'SPOT':
                tabWrite("spotlight\n")

                # Falloff is the main radius from the centre line
                tabWrite("falloff %.2f\n" % (degrees(lamp.spot_size) / 2.0))  # 1 TO 179 FOR BOTH
                tabWrite("radius %.6f\n" % ((degrees(lamp.spot_size) / 2.0) * (1.0 - lamp.spot_blend)))

                # Blender does not have a tightness equivilent, 0 is most like blender default.
                tabWrite("tightness 0\n")  # 0:10f

                tabWrite("point_at  <0, 0, -1>\n")
            elif lamp.type == 'SUN':
                tabWrite("parallel\n")
                tabWrite("point_at  <0, 0, -1>\n")  # *must* be after 'parallel'

            elif lamp.type == 'AREA':
                tabWrite("fade_distance %.6f\n" % (lamp.distance / 5.0))
                tabWrite("fade_power %d\n" % 2)  # Area lights have no falloff type, so always use blenders lamp quad equivalent for those?
                size_x = lamp.size
                samples_x = lamp.shadow_ray_samples_x
                if lamp.shape == 'SQUARE':
                    size_y = size_x
                    samples_y = samples_x
                else:
                    size_y = lamp.size_y
                    samples_y = lamp.shadow_ray_samples_y

                tabWrite("area_light <%d,0,0>,<0,0,%d> %d, %d\n" % (size_x, size_y, samples_x, samples_y))
                if lamp.shadow_ray_sample_method == 'CONSTANT_JITTERED':
                    if lamp.jitter:
                        tabWrite("jitter\n")
                else:
                    tabWrite("adaptive 1\n")
                    tabWrite("jitter\n")

            if not scene.render.use_shadows or lamp.type == 'HEMI' or (lamp.type != 'HEMI' and lamp.shadow_method == 'NOSHADOW'):  # HEMI never has any shadow_method attribute
                tabWrite("shadowless\n")

            if lamp.type not in ('SUN', 'AREA', 'HEMI'):  # Sun shouldn't be attenuated. Hemi and area lights have no falloff attribute so they are put to type 2 attenuation a little higher above.
                tabWrite("fade_distance %.6f\n" % (lamp.distance / 5.0))
                if lamp.falloff_type == 'INVERSE_SQUARE':
                    tabWrite("fade_power %d\n" % 2)  # Use blenders lamp quad equivalent
                elif lamp.falloff_type == 'INVERSE_LINEAR':
                    tabWrite("fade_power %d\n" % 1)  # Use blenders lamp linear
                elif lamp.falloff_type == 'CONSTANT':  # upposing using no fade power keyword would default to constant, no attenuation.
                    pass
                elif lamp.falloff_type == 'CUSTOM_CURVE':  # Using Custom curve for fade power 3 for now.
                    tabWrite("fade_power %d\n" % 4)

            writeMatrix(matrix)

            tabWrite("}\n")
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
##    file.write("\n#declare lampTarget= vrotate(<%.4g,%.4g,%.4g>,<%.4g,%.4g,%.4g>);" % (-(averageLampLocation[0]-averageLampDistance), -(averageLampLocation[1]-averageLampDistance), -(averageLampLocation[2]-averageLampDistance), averageLampRotation[0], averageLampRotation[1], averageLampRotation[2]))
##    #v(A,B) rotates vector A about origin by vector B.
##
####################################################################################################################################

    def exportMeta(metas):

        # TODO - blenders 'motherball' naming is not supported.

        if not scene.pov_tempfiles_enable and scene.pov_comments_enable and len(metas) >= 1:
            file.write("//--Blob objects--\n\n")

        for ob in metas:
            meta = ob.data

            # important because no elements will break parsing.
            elements = [elem for elem in meta.elements if elem.type in ('BALL', 'ELLIPSOID')]

            if elements:
                tabWrite("blob {\n")
                tabWrite("threshold %.4g\n" % meta.threshold)
                importance = ob.pov_importance_value

                try:
                    material = meta.materials[0]  # lame! - blender cant do enything else.
                except:
                    material = None

                for elem in elements:
                    loc = elem.co

                    stiffness = elem.stiffness
                    if elem.use_negative:
                        stiffness = - stiffness

                    if elem.type == 'BALL':

                        tabWrite("sphere { <%.6g, %.6g, %.6g>, %.4g, %.4g }\n" % (loc.x, loc.y, loc.z, elem.radius, stiffness))

                        # After this wecould do something simple like...
                        # 	"pigment {Blue} }"
                        # except we'll write the color

                    elif elem.type == 'ELLIPSOID':
                        # location is modified by scale
                        tabWrite("sphere { <%.6g, %.6g, %.6g>, %.4g, %.4g }\n" % (loc.x / elem.size_x, loc.y / elem.size_y, loc.z / elem.size_z, elem.radius, stiffness))
                        tabWrite("scale <%.6g, %.6g, %.6g> \n" % (elem.size_x, elem.size_y, elem.size_z))

                if material:
                    diffuse_color = material.diffuse_color
                    trans = 1.0 - material.alpha
                    if material.use_transparency and material.transparency_method == 'RAYTRACE':
                        povFilter = material.raytrace_transparency.filter * (1.0 - material.alpha)
                        trans = (1.0 - material.alpha) - povFilter
                    else:
                        povFilter = 0.0

                    material_finish = materialNames[material.name]

                    tabWrite("pigment {rgbft<%.3g, %.3g, %.3g, %.3g, %.3g>} \n" % (diffuse_color[0], diffuse_color[1], diffuse_color[2], povFilter, trans))
                    tabWrite("finish {%s}\n" % safety(material_finish, Level=2))

                else:
                    tabWrite("pigment {rgb<1 1 1>} \n")
                    tabWrite("finish {%s}\n" % (safety(DEF_MAT_NAME, Level=2)))		# Write the finish last.

                writeObjectMaterial(material, ob)

                writeMatrix(global_matrix * ob.matrix_world)
                #Importance for radiosity sampling added here:
                tabWrite("radiosity { \n")
                tabWrite("importance %3g \n" % importance)
                tabWrite("}\n")

                tabWrite("}\n")  # End of Metaball block

                if not scene.pov_tempfiles_enable and scene.pov_comments_enable and len(metas) >= 1:
                    file.write("\n")

    objectNames = {}
    DEF_OBJ_NAME = "Default"

    def exportMeshs(scene, sel):

        ob_num = 0

        for ob in sel:
            ob_num += 1
#############################################
            #Generating a name for object just like materials to be able to use it (baking for now or anything else).
            if sel:
                name_orig = ob.name
            else:
                name_orig = DEF_OBJ_NAME
            name = objectNames[name_orig] = uniqueName(bpy.path.clean_name(name_orig), objectNames)
#############################################
            if ob.type in ('LAMP', 'CAMERA', 'EMPTY', 'META', 'ARMATURE', 'LATTICE'):
                continue

            try:
                me = ob.create_mesh(scene, True, 'RENDER')
            except:
                # happens when curves cant be made into meshes because of no-data
                continue

            importance = ob.pov_importance_value
            me_materials = me.materials
            me_faces = me.faces[:]

            if not me or not me_faces:
                continue

            if info_callback:
                info_callback("Object %2.d of %2.d (%s)" % (ob_num, len(sel), ob.name))

            #if ob.type != 'MESH':
            #	continue
            # me = ob.data

            matrix = global_matrix * ob.matrix_world
            try:
                uv_layer = me.uv_textures.active.data
            except AttributeError:
                uv_layer = None

            try:
                vcol_layer = me.vertex_colors.active.data
            except AttributeError:
                vcol_layer = None

            faces_verts = [f.vertices[:] for f in me_faces]
            faces_normals = [f.normal[:] for f in me_faces]
            verts_normals = [v.normal[:] for v in me.vertices]

            # quads incur an extra face
            quadCount = sum(1 for f in faces_verts if len(f) == 4)

            # Use named declaration to allow reference e.g. for baking. MR
            file.write("\n")
            tabWrite("#declare %s =\n" % name)
            tabWrite("mesh2 {\n")
            tabWrite("vertex_vectors {\n")
            tabWrite("%d" % len(me.vertices))  # vert count

            tabStr = tab * tabLevel
            for v in me.vertices:
                if not scene.pov_tempfiles_enable and scene.pov_list_lf_enable:
                    file.write(",\n")
                    file.write(tabStr + "<%.6f, %.6f, %.6f>" % v.co[:])  # vert count
                else:
                    file.write(", ")
                    file.write("<%.6f, %.6f, %.6f>" % v.co[:])  # vert count
                #tabWrite("<%.6f, %.6f, %.6f>" % v.co[:])  # vert count
            file.write("\n")
            tabWrite("}\n")

            # Build unique Normal list
            uniqueNormals = {}
            for fi, f in enumerate(me_faces):
                fv = faces_verts[fi]
                # [-1] is a dummy index, use a list so we can modify in place
                if f.use_smooth:  # Use vertex normals
                    for v in fv:
                        key = verts_normals[v]
                        uniqueNormals[key] = [-1]
                else:  # Use face normal
                    key = faces_normals[fi]
                    uniqueNormals[key] = [-1]

            tabWrite("normal_vectors {\n")
            tabWrite("%d" % len(uniqueNormals))  # vert count
            idx = 0
            tabStr = tab * tabLevel
            for no, index in uniqueNormals.items():
                if not scene.pov_tempfiles_enable and scene.pov_list_lf_enable:
                    file.write(",\n")
                    file.write(tabStr + "<%.6f, %.6f, %.6f>" % no)  # vert count
                else:
                    file.write(", ")
                    file.write("<%.6f, %.6f, %.6f>" % no)  # vert count
                index[0] = idx
                idx += 1
            file.write("\n")
            tabWrite("}\n")

            # Vertex colours
            vertCols = {}  # Use for material colours also.

            if uv_layer:
                # Generate unique UV's
                uniqueUVs = {}

                for fi, uv in enumerate(uv_layer):

                    if len(faces_verts[fi]) == 4:
                        uvs = uv.uv1, uv.uv2, uv.uv3, uv.uv4
                    else:
                        uvs = uv.uv1, uv.uv2, uv.uv3

                    for uv in uvs:
                        uniqueUVs[uv[:]] = [-1]

                tabWrite("uv_vectors {\n")
                #print unique_uvs
                tabWrite("%d" % len(uniqueUVs))  # vert count
                idx = 0
                tabStr = tab * tabLevel
                for uv, index in uniqueUVs.items():
                    if not scene.pov_tempfiles_enable and scene.pov_list_lf_enable:
                        file.write(",\n")
                        file.write(tabStr + "<%.6f, %.6f>" % uv)
                    else:
                        file.write(", ")
                        file.write("<%.6f, %.6f>" % uv)
                    index[0] = idx
                    idx += 1
                '''
                else:
                    # Just add 1 dummy vector, no real UV's
                    tabWrite('1') # vert count
                    file.write(',\n\t\t<0.0, 0.0>')
                '''
                file.write("\n")
                tabWrite("}\n")

            if me.vertex_colors:

                for fi, f in enumerate(me_faces):
                    material_index = f.material_index
                    material = me_materials[material_index]

                    if material and material.use_vertex_color_paint:

                        col = vcol_layer[fi]

                        if len(faces_verts[fi]) == 4:
                            cols = col.color1, col.color2, col.color3, col.color4
                        else:
                            cols = col.color1, col.color2, col.color3

                        for col in cols:
                            key = col[0], col[1], col[2], material_index  # Material index!
                            vertCols[key] = [-1]

                    else:
                        if material:
                            diffuse_color = material.diffuse_color[:]
                            key = diffuse_color[0], diffuse_color[1], diffuse_color[2], material_index
                            vertCols[key] = [-1]

            else:
                # No vertex colours, so write material colours as vertex colours
                for i, material in enumerate(me_materials):

                    if material:
                        diffuse_color = material.diffuse_color[:]
                        key = diffuse_color[0], diffuse_color[1], diffuse_color[2], i  # i == f.mat
                        vertCols[key] = [-1]

            # Vert Colours
            tabWrite("texture_list {\n")
            file.write(tabStr + "%s" % (len(vertCols)))  # vert count
            idx = 0

            for col, index in vertCols.items():
                if me_materials:
                    material = me_materials[col[3]]
                    material_finish = materialNames[material.name]

                    if material.use_transparency:
                        trans = 1.0 - material.alpha
                    else:
                        trans = 0.0

                    if material.use_transparency and material.transparency_method == 'RAYTRACE':
                        povFilter = material.raytrace_transparency.filter * (1.0 - material.alpha)
                        trans = (1.0 - material.alpha) - povFilter
                    else:
                        povFilter = 0.0
                else:
                    material_finish = DEF_MAT_NAME  # not working properly,
                    trans = 0.0

                ##############SF
                texturesDif = ""
                texturesSpec = ""
                texturesNorm = ""
                texturesAlpha = ""
                for t in material.texture_slots:
                    if t and t.texture.type == 'IMAGE' and t.use and t.texture.image:
                        image_filename = path_image(t.texture.image.filepath)
                        imgGamma = ""
                        if image_filename:
                            if t.use_map_color_diffuse:
                                texturesDif = image_filename
                                colvalue = t.default_value
                                t_dif = t
                                if t_dif.texture.pov_tex_gamma_enable:
                                    imgGamma = (" gamma %.3g " % t_dif.texture.pov_tex_gamma_value)
                            if t.use_map_specular or t.use_map_raymir:
                                texturesSpec = image_filename
                                colvalue = t.default_value
                                t_spec = t
                            if t.use_map_normal:
                                texturesNorm = image_filename
                                colvalue = t.normal_factor * 10.0
                                #textNormName=t.texture.image.name + ".normal"
                                #was the above used? --MR
                                t_nor = t
                            if t.use_map_alpha:
                                texturesAlpha = image_filename
                                colvalue = t.alpha_factor * 10.0
                                #textDispName=t.texture.image.name + ".displ"
                                #was the above used? --MR
                                t_alpha = t

                ##############################################################################################################

                if material.pov_replacement_text != "":
                    file.write("\n")
                    file.write(" texture{%s}\n" % material.pov_replacement_text)

                else:
                    file.write("\n")
                    tabWrite("texture {\n")  # THIS AREA NEEDS TO LEAVE THE TEXTURE OPEN UNTIL ALL MAPS ARE WRITTEN DOWN.   --MR

                    ##############################################################################################################
                    if material.diffuse_shader == 'MINNAERT':
                        tabWrite("\n")
                        tabWrite("aoi\n")
                        tabWrite("texture_map {\n")
                        tabWrite("[%.3g finish {diffuse %.3g}]\n" % (material.darkness / 2.0, 2.0 - material.darkness))
                        tabWrite("[%.3g" % (1.0 - (material.darkness / 2.0)))
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
    ##                        lampLookAt[3]= 0.0 #Put 'target' of the lamp on the floor plane to elimianate one unknown value
    ##                                   degrees(atan((lampLocation - lampLookAt).y/(lampLocation - lampLookAt).z))=lamp.rotation[0]
    ##                                   degrees(atan((lampLocation - lampLookAt).z/(lampLocation - lampLookAt).x))=lamp.rotation[1]
    ##                                   degrees(atan((lampLocation - lampLookAt).x/(lampLocation - lampLookAt).y))=lamp.rotation[2]
    ##                        degrees(atan((lampLocation - lampLookAt).y/(lampLocation.z))=lamp.rotation[0]
    ##                        degrees(atan((lampLocation.z/(lampLocation - lampLookAt).x))=lamp.rotation[1]
    ##                        degrees(atan((lampLocation - lampLookAt).x/(lampLocation - lampLookAt).y))=lamp.rotation[2]

                                    #color = tuple([c * lamp.energy for c in lamp.color]) # Colour is modified by energy

                        tabWrite("\n")
                        tabWrite("slope { lampTarget }\n")
                        tabWrite("texture_map {\n")
                        tabWrite("[%.3g finish {diffuse %.3g}]\n" % (material.diffuse_fresnel / 2, 2.0 - material.diffuse_fresnel_factor))
                        tabWrite("[%.3g\n" % (1 - (material.diffuse_fresnel / 2.0)))

                    #if material.diffuse_shader == 'FRESNEL': pigment pattern aoi pigment and texture map above, the rest below as one of its entry
                    ##########################################################################################################################

                    #special_texture_found = False
                    #for t in material.texture_slots:
                    #    if t and t.texture.type == 'IMAGE' and t.use and t.texture.image and (t.use_map_specular or t.use_map_raymir or t.use_map_normal or t.use_map_alpha):
                    #        special_texture_found = True
                    #        continue # Some texture found
                    #if special_texture_found:

                    if texturesSpec != "" or texturesAlpha != "":
                        if texturesSpec != "":
                            # tabWrite("\n")
                            tabWrite("pigment_pattern {\n")
                            # POV-Ray "scale" is not a number of repetitions factor, but its inverse, a standard scale factor.
                            # Offset seems needed relatively to scale so probably center of the scale is not the same in blender and POV
                            mappingSpec = "translate <%.4g,%.4g,%.4g> scale <%.4g,%.4g,%.4g>\n" % (-t_spec.offset.x, t_spec.offset.y, t_spec.offset.z, 1.0 / t_spec.scale.x, 1.0 / t_spec.scale.y, 1.0 / t_spec.scale.z)
                            tabWrite("uv_mapping image_map{%s \"%s\" %s}\n" % (imageFormat(texturesSpec), texturesSpec, imgMap(t_spec)))
                            tabWrite("%s\n" % mappingSpec)
                            tabWrite("}\n")
                            tabWrite("texture_map {\n")
                            tabWrite("[0 \n")

                        if texturesDif == "":
                            if texturesAlpha != "":
                                tabWrite("\n")
                                # POV-Ray "scale" is not a number of repetitions factor, but its inverse, a standard scale factor.
                                # Offset seems needed relatively to scale so probably center of the scale is not the same in blender and POV
                                mappingAlpha = " translate <%.4g,%.4g,%.4g> scale <%.4g,%.4g,%.4g>\n" % (-t_alpha.offset.x, -t_alpha.offset.y, t_alpha.offset.z, 1.0 / t_alpha.scale.x, 1.0 / t_alpha.scale.y, 1.0 / t_alpha.scale.z)
                                tabWrite("pigment {pigment_pattern {uv_mapping image_map{%s \"%s\" %s}%s" % (imageFormat(texturesAlpha), texturesAlpha, imgMap(t_alpha), mappingAlpha))
                                tabWrite("}\n")
                                tabWrite("pigment_map {\n")
                                tabWrite("[0 color rgbft<0,0,0,1,1>]\n")
                                tabWrite("[1 color rgbft<%.3g, %.3g, %.3g, %.3g, %.3g>]\n" % (col[0], col[1], col[2], povFilter, trans))
                                tabWrite("}\n")
                                tabWrite("}\n")

                            else:

                                tabWrite("pigment {rgbft<%.3g, %.3g, %.3g, %.3g, %.3g>}\n" % (col[0], col[1], col[2], povFilter, trans))

                            if texturesSpec != "":
                                tabWrite("finish {%s}\n" % (safety(material_finish, Level=1)))  # Level 1 is no specular

                            else:
                                tabWrite("finish {%s}\n" % (safety(material_finish, Level=2)))  # Level 2 is translated spec

                        else:
                            # POV-Ray "scale" is not a number of repetitions factor, but its inverse, a standard scale factor.
                            # Offset seems needed relatively to scale so probably center of the scale is not the same in blender and POV
                            mappingDif = ("translate <%.4g,%.4g,%.4g> scale <%.4g,%.4g,%.4g>" % (-t_dif.offset.x, -t_dif.offset.y, t_dif.offset.z, 1.0 / t_dif.scale.x, 1.0 / t_dif.scale.y, 1.0 / t_dif.scale.z))
                            if texturesAlpha != "":
                                # POV-Ray "scale" is not a number of repetitions factor, but its inverse, a standard scale factor.
                                # Offset seems needed relatively to scale so probably center of the scale is not the same in blender and POV
                                mappingAlpha = " translate <%.4g,%.4g,%.4g> scale <%.4g,%.4g,%.4g>" % (-t_alpha.offset.x, -t_alpha.offset.y, t_alpha.offset.z, 1.0 / t_alpha.scale.x, 1.0 / t_alpha.scale.y, 1.0 / t_alpha.scale.z)
                                tabWrite("pigment {\n")
                                tabWrite("pigment_pattern {\n")
                                tabWrite("uv_mapping image_map{%s \"%s\" %s}%s}\n" % (imageFormat(texturesAlpha), texturesAlpha, imgMap(t_alpha), mappingAlpha))
                                tabWrite("pigment_map {\n")
                                tabWrite("[0 color rgbft<0,0,0,1,1>]\n")
                                tabWrite("[1 uv_mapping image_map {%s \"%s\" %s} %s]\n" % (imageFormat(texturesDif), texturesDif, (imgGamma + imgMap(t_dif)), mappingDif))
                                tabWrite("}\n")
                                tabWrite("}\n")

                            else:
                                tabWrite("pigment {uv_mapping image_map {%s \"%s\" %s}%s}\n" % (imageFormat(texturesDif), texturesDif, (imgGamma + imgMap(t_dif)), mappingDif))

                            if texturesSpec != "":
                                tabWrite("finish {%s}\n" % (safety(material_finish, Level=1)))  # Level 1 is no specular

                            else:
                                tabWrite("finish {%s}\n" % (safety(material_finish, Level=2)))  # Level 2 is translated specular

                            ## scale 1 rotate y*0
                            #imageMap = ("{image_map {%s \"%s\" %s }\n" % (imageFormat(textures),textures,imgMap(t_dif)))
                            #tabWrite("uv_mapping pigment %s} %s finish {%s}\n" % (imageMap,mapping,safety(material_finish)))
                            #tabWrite("pigment {uv_mapping image_map {%s \"%s\" %s}%s} finish {%s}\n" % (imageFormat(texturesDif),texturesDif,imgMap(t_dif),mappingDif,safety(material_finish)))
                        if texturesNorm != "":
                            ## scale 1 rotate y*0
                            # POV-Ray "scale" is not a number of repetitions factor, but its inverse, a standard scale factor.
                            # Offset seems needed relatively to scale so probably center of the scale is not the same in blender and POV
                            mappingNor = " translate <%.4g,%.4g,%.4g> scale <%.4g,%.4g,%.4g>" % (-t_nor.offset.x, -t_nor.offset.y, t_nor.offset.z, 1.0 / t_nor.scale.x, 1.0 / t_nor.scale.y, 1.0 / t_nor.scale.z)
                            #imageMapNor = ("{bump_map {%s \"%s\" %s mapping}" % (imageFormat(texturesNorm),texturesNorm,imgMap(t_nor)))
                            #We were not using the above maybe we should?
                            tabWrite("normal {uv_mapping bump_map {%s \"%s\" %s  bump_size %.4g }%s}\n" % (imageFormat(texturesNorm), texturesNorm, imgMap(t_nor), t_nor.normal_factor * 10, mappingNor))
                        if texturesSpec != "":
                            tabWrite("]\n")
                        ################################Second index for mapping specular max value##################################################################################################
                            tabWrite("[1 \n")

                if texturesDif == "" and material.pov_replacement_text == "":
                    if texturesAlpha != "":
                        # POV-Ray "scale" is not a number of repetitions factor, but its inverse, a standard scale factor.
                        # Offset seems needed relatively to scale so probably center of the scale is not the same in blender and POV
                        mappingAlpha = " translate <%.4g,%.4g,%.4g> scale <%.4g,%.4g,%.4g>\n" % (-t_alpha.offset.x, -t_alpha.offset.y, t_alpha.offset.z, 1.0 / t_alpha.scale.x, 1.0 / t_alpha.scale.y, 1.0 / t_alpha.scale.z)  # strange that the translation factor for scale is not the same as for translate. ToDo: verify both matches with blender internal.
                        tabWrite("pigment {pigment_pattern {uv_mapping image_map{%s \"%s\" %s}%s}\n" % (imageFormat(texturesAlpha), texturesAlpha, imgMap(t_alpha), mappingAlpha))
                        tabWrite("pigment_map {\n")
                        tabWrite("[0 color rgbft<0,0,0,1,1>]\n")
                        tabWrite("[1 color rgbft<%.3g, %.3g, %.3g, %.3g, %.3g>]\n" % (col[0], col[1], col[2], povFilter, trans))
                        tabWrite("}\n")
                        tabWrite("}\n")

                    else:
                        tabWrite("pigment {rgbft<%.3g, %.3g, %.3g, %.3g, %.3g>}\n" % (col[0], col[1], col[2], povFilter, trans))

                    if texturesSpec != "":
                        tabWrite("finish {%s}\n" % (safety(material_finish, Level=3)))  # Level 3 is full specular

                    else:
                        tabWrite("finish {%s}\n" % (safety(material_finish, Level=2)))  # Level 2 is translated specular

                elif material.pov_replacement_text == "":
                    # POV-Ray "scale" is not a number of repetitions factor, but its inverse, a standard scale factor.
                    # Offset seems needed relatively to scale so probably center of the scale is not the same in blender and POV
                    mappingDif = ("translate <%.4g,%.4g,%.4g> scale <%.4g,%.4g,%.4g>" % (-t_dif.offset.x, -t_dif.offset.y, t_dif.offset.z, 1.0 / t_dif.scale.x, 1.0 / t_dif.scale.y, 1.0 / t_dif.scale.z))  # strange that the translation factor for scale is not the same as for translate. ToDo: verify both matches with blender internal.
                    if texturesAlpha != "":
                        mappingAlpha = "translate <%.4g,%.4g,%.4g> scale <%.4g,%.4g,%.4g>" % (-t_alpha.offset.x, -t_alpha.offset.y, t_alpha.offset.z, 1.0 / t_alpha.scale.x, 1.0 / t_alpha.scale.y, 1.0 / t_alpha.scale.z)  # strange that the translation factor for scale is not the same as for translate. ToDo: verify both matches with blender internal.
                        tabWrite("pigment {pigment_pattern {uv_mapping image_map{%s \"%s\" %s}%s}\n" % (imageFormat(texturesAlpha), texturesAlpha, imgMap(t_alpha), mappingAlpha))
                        tabWrite("pigment_map {\n")
                        tabWrite("[0 color rgbft<0,0,0,1,1>]\n")
                        tabWrite("[1 uv_mapping image_map {%s \"%s\" %s} %s]\n" % (imageFormat(texturesDif), texturesDif, (imgMap(t_dif) + imgGamma), mappingDif))
                        tabWrite("}\n")
                        tabWrite("}\n")

                    else:
                        tabWrite("pigment {\n")
                        tabWrite("uv_mapping image_map {\n")
                        #tabWrite("%s \"%s\" %s}%s\n" % (imageFormat(texturesDif),texturesDif,(imgGamma + imgMap(t_dif)),mappingDif))
                        tabWrite("%s \"%s\" \n" % (imageFormat(texturesDif), texturesDif))
                        tabWrite("%s\n" % (imgGamma + imgMap(t_dif)))
                        tabWrite("}\n")
                        tabWrite("%s\n" % mappingDif)
                        tabWrite("}\n")
                    if texturesSpec != "":
                        tabWrite("finish {%s}\n" % (safety(material_finish, Level=3)))  # Level 3 is full specular
                    else:
                        tabWrite("finish {%s}\n" % (safety(material_finish, Level=2)))  # Level 2 is translated specular

                    ## scale 1 rotate y*0
                    #imageMap = ("{image_map {%s \"%s\" %s }" % (imageFormat(textures),textures,imgMap(t_dif)))
                    #file.write("\n\t\t\tuv_mapping pigment %s} %s finish {%s}" % (imageMap,mapping,safety(material_finish)))
                    #file.write("\n\t\t\tpigment {uv_mapping image_map {%s \"%s\" %s}%s} finish {%s}" % (imageFormat(texturesDif),texturesDif,imgMap(t_dif),mappingDif,safety(material_finish)))
                if texturesNorm != "" and material.pov_replacement_text == "":
                    ## scale 1 rotate y*0
                    # POV-Ray "scale" is not a number of repetitions factor, but its inverse, a standard scale factor.
                    # Offset seems needed relatively to scale so probably center of the scale is not the same in blender and POV
                    mappingNor = (" translate <%.4g,%.4g,%.4g> scale <%.4g,%.4g,%.4g>" % (-t_nor.offset.x, -t_nor.offset.y, t_nor.offset.z, 1.0 / t_nor.scale.x, 1.0 / t_nor.scale.y, 1.0 / t_nor.scale.z))
                    #imageMapNor = ("{bump_map {%s \"%s\" %s mapping}" % (imageFormat(texturesNorm),texturesNorm,imgMap(t_nor)))
                    #We were not using the above maybe we should?
                    tabWrite("normal {uv_mapping bump_map {%s \"%s\" %s  bump_size %.4g }%s}\n" % (imageFormat(texturesNorm), texturesNorm, imgMap(t_nor), t_nor.normal_factor * 10.0, mappingNor))
                if texturesSpec != "" and material.pov_replacement_text == "":
                    tabWrite("]\n")

                    tabWrite("}\n")

                #End of slope/ior texture_map
                if material.diffuse_shader in ('MINNAERT', 'FRESNEL') and material.pov_replacement_text == "":
                    tabWrite("]\n")
                    tabWrite("}\n")

                if material.pov_replacement_text == "":
                    tabWrite("}\n")  # THEN IT CAN CLOSE IT   --MR

                ############################################################################################################
                index[0] = idx
                idx += 1

            tabWrite("}\n")

            # Face indices
            tabWrite("face_indices {\n")
            tabWrite("%d" % (len(me_faces) + quadCount))  # faces count
            tabStr = tab * tabLevel

            for fi, f in enumerate(me_faces):
                fv = faces_verts[fi]
                material_index = f.material_index
                if len(fv) == 4:
                    indices = (0, 1, 2), (0, 2, 3)
                else:
                    indices = ((0, 1, 2),)

                if vcol_layer:
                    col = vcol_layer[fi]

                    if len(fv) == 4:
                        cols = col.color1, col.color2, col.color3, col.color4
                    else:
                        cols = col.color1, col.color2, col.color3

                if not me_materials or me_materials[material_index] is None:  # No materials
                    for i1, i2, i3 in indices:
                        if not scene.pov_tempfiles_enable and scene.pov_list_lf_enable:
                            file.write(",\n")
                            file.write(tabStr + "<%d,%d,%d>" % (fv[i1], fv[i2], fv[i3]))  # vert count
                        else:
                            file.write(", ")
                            file.write("<%d,%d,%d>" % (fv[i1], fv[i2], fv[i3]))  # vert count
                else:
                    material = me_materials[material_index]
                    for i1, i2, i3 in indices:
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

                        if not scene.pov_tempfiles_enable and scene.pov_list_lf_enable:
                            file.write(",\n")
                            file.write(tabStr + "<%d,%d,%d>, %d,%d,%d" % (fv[i1], fv[i2], fv[i3], ci1, ci2, ci3))  # vert count
                        else:
                            file.write(", ")
                            file.write("<%d,%d,%d>, %d,%d,%d" % (fv[i1], fv[i2], fv[i3], ci1, ci2, ci3))  # vert count

            file.write("\n")
            tabWrite("}\n")

            # normal_indices indices
            tabWrite("normal_indices {\n")
            tabWrite("%d" % (len(me_faces) + quadCount))  # faces count
            tabStr = tab * tabLevel
            for fi, fv in enumerate(faces_verts):

                if len(fv) == 4:
                    indices = (0, 1, 2), (0, 2, 3)
                else:
                    indices = ((0, 1, 2),)

                for i1, i2, i3 in indices:
                    if me_faces[fi].use_smooth:
                        if not scene.pov_tempfiles_enable and scene.pov_list_lf_enable:
                            file.write(",\n")
                            file.write(tabStr + "<%d,%d,%d>" %\
                            (uniqueNormals[verts_normals[fv[i1]]][0],\
                             uniqueNormals[verts_normals[fv[i2]]][0],\
                             uniqueNormals[verts_normals[fv[i3]]][0]))  # vert count
                        else:
                            file.write(", ")
                            file.write("<%d,%d,%d>" %\
                            (uniqueNormals[verts_normals[fv[i1]]][0],\
                             uniqueNormals[verts_normals[fv[i2]]][0],\
                             uniqueNormals[verts_normals[fv[i3]]][0]))  # vert count
                    else:
                        idx = uniqueNormals[faces_normals[fi]][0]
                        if not scene.pov_tempfiles_enable and scene.pov_list_lf_enable:
                            file.write(",\n")
                            file.write(tabStr + "<%d,%d,%d>" % (idx, idx, idx))  # vert count
                        else:
                            file.write(", ")
                            file.write("<%d,%d,%d>" % (idx, idx, idx))  # vert count

            file.write("\n")
            tabWrite("}\n")

            if uv_layer:
                tabWrite("uv_indices {\n")
                tabWrite("%d" % (len(me_faces) + quadCount))  # faces count
                tabStr = tab * tabLevel
                for fi, fv in enumerate(faces_verts):

                    if len(fv) == 4:
                        indices = (0, 1, 2), (0, 2, 3)
                    else:
                        indices = ((0, 1, 2),)

                    uv = uv_layer[fi]
                    if len(faces_verts[fi]) == 4:
                        uvs = uv.uv1[:], uv.uv2[:], uv.uv3[:], uv.uv4[:]
                    else:
                        uvs = uv.uv1[:], uv.uv2[:], uv.uv3[:]

                    for i1, i2, i3 in indices:
                        if not scene.pov_tempfiles_enable and scene.pov_list_lf_enable:
                            file.write(",\n")
                            file.write(tabStr + "<%d,%d,%d>" % (
                                     uniqueUVs[uvs[i1]][0],\
                                     uniqueUVs[uvs[i2]][0],\
                                     uniqueUVs[uvs[i3]][0]))
                        else:
                            file.write(", ")
                            file.write("<%d,%d,%d>" % (
                                     uniqueUVs[uvs[i1]][0],\
                                     uniqueUVs[uvs[i2]][0],\
                                     uniqueUVs[uvs[i3]][0]))

                file.write("\n")
                tabWrite("}\n")

            if me.materials:
                try:
                    material = me.materials[0]  # dodgy
                    writeObjectMaterial(material, ob)
                except IndexError:
                    print(me)

            writeMatrix(matrix)

            #Importance for radiosity sampling added here:
            tabWrite("radiosity { \n")
            tabWrite("importance %3g \n" % importance)
            tabWrite("}\n")

            tabWrite("}\n")  # End of mesh block
            tabWrite("%s\n" % name)  # Use named declaration to allow reference e.g. for baking. MR

            bpy.data.meshes.remove(me)

    def exportWorld(world):
        render = scene.render
        camera = scene.camera
        matrix = global_matrix * camera.matrix_world
        if not world:
            return
        #############Maurice####################################
        #These lines added to get sky gradient (visible with PNG output)
        if world:
            #For simple flat background:
            if not world.use_sky_blend:
                #Non fully transparent background could premultiply alpha and avoid anti-aliasing display issue:
                if render.alpha_mode == 'PREMUL':
                    tabWrite("background {rgbt<%.3g, %.3g, %.3g, 0.75>}\n" % (world.horizon_color[:]))
                #Currently using no alpha with Sky option:
                elif render.alpha_mode == 'SKY':
                    tabWrite("background {rgbt<%.3g, %.3g, %.3g, 0>}\n" % (world.horizon_color[:]))
                #StraightAlpha:
                else:
                    tabWrite("background {rgbt<%.3g, %.3g, %.3g, 1>}\n" % (world.horizon_color[:]))

            worldTexCount = 0
            #For Background image textures
            for t in world.texture_slots:  # risk to write several sky_spheres but maybe ok.
                if t and t.texture.type is not None:
                    worldTexCount += 1
                if t and t.texture.type == 'IMAGE':  # and t.use: #No enable checkbox for world textures yet (report it?)
                    image_filename = path_image(t.texture.image.filepath)
                    if t.texture.image.filepath != image_filename:
                        t.texture.image.filepath = image_filename
                    if image_filename != "" and t.use_map_blend:
                        texturesBlend = image_filename
                        #colvalue = t.default_value
                        t_blend = t
                    #commented below was an idea to make the Background image oriented as camera taken here: http://news.povray.org/povray.newusers/thread/%3Cweb.4a5cddf4e9c9822ba2f93e20@news.povray.org%3E/
                    #mappingBlend = (" translate <%.4g,%.4g,%.4g> rotate z*degrees(atan((camLocation - camLookAt).x/(camLocation - camLookAt).y)) rotate x*degrees(atan((camLocation - camLookAt).y/(camLocation - camLookAt).z)) rotate y*degrees(atan((camLocation - camLookAt).z/(camLocation - camLookAt).x)) scale <%.4g,%.4g,%.4g>b" % (t_blend.offset.x / 10 ,t_blend.offset.y / 10 ,t_blend.offset.z / 10, t_blend.scale.x ,t_blend.scale.y ,t_blend.scale.z))#replace 4/3 by the ratio of each image found by some custom or existing function
                    #using camera rotation valuesdirectly from blender seems much easier
                    if t_blend.texture_coords == 'ANGMAP':
                        mappingBlend = ""
                    else:
                        mappingBlend = " translate <%.4g-0.5,%.4g-0.5,%.4g-0.5> rotate<0,0,0>  scale <%.4g,%.4g,%.4g>" % (
                                       t_blend.offset.x / 10.0, t_blend.offset.y / 10.0, t_blend.offset.z / 10.0,
                                       t_blend.scale.x * 0.85, t_blend.scale.y * 0.85, t_blend.scale.z * 0.85,
                                       )

                        #The initial position and rotation of the pov camera is probably creating the rotation offset should look into it someday but at least background won't rotate with the camera now.
                    #Putting the map on a plane would not introduce the skysphere distortion and allow for better image scale matching but also some waay to chose depth and size of the plane relative to camera.
                    tabWrite("sky_sphere {\n")
                    tabWrite("pigment {\n")
                    tabWrite("image_map{%s \"%s\" %s}\n" % (imageFormat(texturesBlend), texturesBlend, imgMapBG(t_blend)))
                    tabWrite("}\n")
                    tabWrite("%s\n" % (mappingBlend))
                    tabWrite("}\n")
                    #tabWrite("scale 2\n")
                    #tabWrite("translate -1\n")

            #For only Background gradient

            if worldTexCount == 0:
                if world.use_sky_blend:
                    tabWrite("sky_sphere {\n")
                    tabWrite("pigment {\n")
                    tabWrite("gradient y\n")  # maybe Should follow the advice of POV doc about replacing gradient for skysphere..5.5
                    tabWrite("color_map {\n")
                    if render.alpha_mode == 'STRAIGHT':
                        tabWrite("[0.0 rgbt<%.3g, %.3g, %.3g, 1>]\n" % (world.horizon_color[:]))
                        tabWrite("[1.0 rgbt<%.3g, %.3g, %.3g, 1>]\n" % (world.zenith_color[:]))
                    elif render.alpha_mode == 'PREMUL':
                        tabWrite("[0.0 rgbt<%.3g, %.3g, %.3g, 0.99>]\n" % (world.horizon_color[:]))
                        tabWrite("[1.0 rgbt<%.3g, %.3g, %.3g, 0.99>]\n" % (world.zenith_color[:]))  # aa premult not solved with transmit 1
                    else:
                        tabWrite("[0.0 rgbt<%.3g, %.3g, %.3g, 0>]\n" % (world.horizon_color[:]))
                        tabWrite("[1.0 rgbt<%.3g, %.3g, %.3g, 0>]\n" % (world.zenith_color[:]))
                    tabWrite("}\n")
                    tabWrite("}\n")
                    tabWrite("}\n")
                    #sky_sphere alpha (transmit) is not translating into image alpha the same way as 'background'

            #if world.light_settings.use_indirect_light:
            #    scene.pov_radio_enable=1

            #Maybe change the above to a funtion copyInternalRenderer settings when user pushes a button, then:
            #scene.pov_radio_enable = world.light_settings.use_indirect_light
            #and other such translations but maybe this would not be allowed either?

        ###############################################################

        mist = world.mist_settings

        if mist.use_mist:
            tabWrite("fog {\n")
            tabWrite("distance %.6f\n" % mist.depth)
            tabWrite("color rgbt<%.3g, %.3g, %.3g, %.3g>\n" % (world.horizon_color[:] + (1.0 - mist.intensity,)))
            #tabWrite("fog_offset %.6f\n" % mist.start)
            #tabWrite("fog_alt 5\n")
            #tabWrite("turbulence 0.2\n")
            #tabWrite("turb_depth 0.3\n")
            tabWrite("fog_type 1\n")
            tabWrite("}\n")
        if scene.pov_media_enable:
            tabWrite("media {\n")
            tabWrite("scattering { 1, rgb <%.4g, %.4g, %.4g>}\n" % scene.pov_media_color[:])
            tabWrite("samples %.d\n" % scene.pov_media_samples)
            tabWrite("}\n")

    def exportGlobalSettings(scene):

        tabWrite("global_settings {\n")
        tabWrite("assumed_gamma 1.0\n")
        tabWrite("max_trace_level %d\n" % scene.pov_max_trace_level)

        if scene.pov_radio_enable:
            tabWrite("radiosity {\n")
            tabWrite("adc_bailout %.4g\n" % scene.pov_radio_adc_bailout)
            tabWrite("always_sample %d\n" % scene.pov_radio_always_sample)
            tabWrite("brightness %.4g\n" % scene.pov_radio_brightness)
            tabWrite("count %d\n" % scene.pov_radio_count)
            tabWrite("error_bound %.4g\n" % scene.pov_radio_error_bound)
            tabWrite("gray_threshold %.4g\n" % scene.pov_radio_gray_threshold)
            tabWrite("low_error_factor %.4g\n" % scene.pov_radio_low_error_factor)
            tabWrite("media %d\n" % scene.pov_radio_media)
            tabWrite("minimum_reuse %.4g\n" % scene.pov_radio_minimum_reuse)
            tabWrite("nearest_count %d\n" % scene.pov_radio_nearest_count)
            tabWrite("normal %d\n" % scene.pov_radio_normal)
            tabWrite("pretrace_start %.3g\n" % scene.pov_radio_pretrace_start)
            tabWrite("pretrace_end %.3g\n" % scene.pov_radio_pretrace_end)
            tabWrite("recursion_limit %d\n" % scene.pov_radio_recursion_limit)
            tabWrite("}\n")
        once = 1
        for material in bpy.data.materials:
            if material.subsurface_scattering.use and once:
                tabWrite("mm_per_unit %.6f\n" % (material.subsurface_scattering.scale * (-100.0) + 15.0))  # In pov, the scale has reversed influence compared to blender. these number should correct that
                once = 0  # In POV-Ray, the scale factor for all subsurface shaders needs to be the same

        if world:
            tabWrite("ambient_light rgb<%.3g, %.3g, %.3g>\n" % world.ambient_color[:])

        if material.pov_photons_refraction or material.pov_photons_reflection:
            tabWrite("photons {\n")
            tabWrite("spacing %.6f\n" % scene.pov_photon_spacing)
            tabWrite("max_trace_level %d\n" % scene.pov_photon_max_trace_level)
            tabWrite("adc_bailout %.3g\n" % scene.pov_photon_adc_bailout)
            tabWrite("gather %d, %d\n" % (scene.pov_photon_gather_min, scene.pov_photon_gather_max))
            tabWrite("}\n")

        tabWrite("}\n")

    def exportCustomCode():

        for txt in bpy.data.texts:
            if txt.pov_custom_code:
                # Why are the newlines needed?
                file.write("\n")
                file.write(txt.as_string())
                file.write("\n")

    sel = scene.objects
    comments = scene.pov_comments_enable
    if not scene.pov_tempfiles_enable and comments:
        file.write("//---------------------------------------------\n//--Exported with POV-Ray exporter for Blender--\n//---------------------------------------------\n\n")
    file.write("#version 3.7;\n")

    if not scene.pov_tempfiles_enable and comments:
        file.write("\n//--CUSTOM CODE--\n\n")
    exportCustomCode()

    if not scene.pov_tempfiles_enable and comments:
        file.write("\n//--Global settings and background--\n\n")

    exportGlobalSettings(scene)

    if not scene.pov_tempfiles_enable and comments:
        file.write("\n")

    exportWorld(scene.world)

    if not scene.pov_tempfiles_enable and comments:
        file.write("\n//--Cameras--\n\n")

    exportCamera()

    if not scene.pov_tempfiles_enable and comments:
        file.write("\n//--Lamps--\n\n")

    exportLamps([l for l in sel if l.type == 'LAMP'])

    if not scene.pov_tempfiles_enable and comments:
        file.write("\n//--Material Definitions--\n\n")

    # Convert all materials to strings we can access directly per vertex.
    #exportMaterials()
    writeMaterial(None)  # default material
    for material in bpy.data.materials:
        if material.users > 0:
            writeMaterial(material)
    if not scene.pov_tempfiles_enable and comments:
        file.write("\n")

    exportMeta([l for l in sel if l.type == 'META'])

    if not scene.pov_tempfiles_enable and comments:
        file.write("//--Mesh objects--\n")

    exportMeshs(scene, sel)
    #What follow used to happen here:
    #exportCamera()
    #exportWorld(scene.world)
    #exportGlobalSettings(scene)
    # MR:..and the order was important for an attempt to implement pov 3.7 baking (mesh camera) comment for the record
    # CR: Baking should be a special case than. If "baking", than we could change the order.

    #print("pov file closed %s" % file.closed)
    file.close()
    #print("pov file closed %s" % file.closed)


def write_pov_ini(filename_ini, filename_pov, filename_image):
    scene = bpy.data.scenes[0]
    render = scene.render

    x = int(render.resolution_x * render.resolution_percentage * 0.01)
    y = int(render.resolution_y * render.resolution_percentage * 0.01)

    file = open(filename_ini, "w")
    file.write("Version=3.7\n")
    file.write("Input_File_Name='%s'\n" % filename_pov)
    file.write("Output_File_Name='%s'\n" % filename_image)

    file.write("Width=%d\n" % x)
    file.write("Height=%d\n" % y)

    # Border render.
    if render.use_border:
        file.write("Start_Column=%4g\n" % render.border_min_x)
        file.write("End_Column=%4g\n" % (render.border_max_x))

        file.write("Start_Row=%4g\n" % (render.border_min_y))
        file.write("End_Row=%4g\n" % (render.border_max_y))

    file.write("Bounding_Method=2\n")  # The new automatic BSP is faster in most scenes

    file.write("Display=1\n")  # Activated (turn this back off when better live exchange is done between the two programs (see next comment)
    file.write("Pause_When_Done=0\n")
    file.write("Output_File_Type=N\n")  # PNG, with POV-Ray 3.7, can show background color with alpha. In the long run using the POV-Ray interactive preview like bishop 3D could solve the preview for all formats.
    #file.write("Output_File_Type=T\n") # TGA, best progressive loading
    file.write("Output_Alpha=1\n")

    if scene.pov_antialias_enable:
        # aa_mapping = {"5": 2, "8": 3, "11": 4, "16": 5} # method 2 (recursive) with higher max subdiv forced because no mipmapping in POV-Ray needs higher sampling.
        method = {"0": 1, "1": 2}
        file.write("Antialias=on\n")
        file.write("Sampling_Method=%s\n" % method[scene.pov_antialias_method])
        file.write("Antialias_Depth=%d\n" % scene.pov_antialias_depth)
        file.write("Antialias_Threshold=%.3g\n" % scene.pov_antialias_threshold)
        file.write("Antialias_Gamma=%.3g\n" % scene.pov_antialias_gamma)
        if scene.pov_jitter_enable:
            file.write("Jitter=on\n")
            file.write("Jitter_Amount=%3g\n" % scene.pov_jitter_amount)
        else:
            file.write("Jitter=off\n")  # prevent animation flicker

    else:
        file.write("Antialias=off\n")
    #print("ini file closed %s" % file.closed)
    file.close()
    #print("ini file closed %s" % file.closed)


class PovrayRender(bpy.types.RenderEngine):
    bl_idname = 'POVRAY_RENDER'
    bl_label = "POV-Ray 3.7"
    DELAY = 0.5

    def _export(self, scene, povPath, renderImagePath):
        import tempfile

        if scene.pov_tempfiles_enable:
            self._temp_file_in = tempfile.NamedTemporaryFile(suffix=".pov", delete=False).name
            self._temp_file_out = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name  # PNG with POV 3.7, can show the background color with alpha. In the long run using the POV-Ray interactive preview like bishop 3D could solve the preview for all formats.
            #self._temp_file_out = tempfile.NamedTemporaryFile(suffix=".tga", delete=False).name
            self._temp_file_ini = tempfile.NamedTemporaryFile(suffix=".ini", delete=False).name
        else:
            self._temp_file_in = povPath + ".pov"
            self._temp_file_out = renderImagePath + ".png"  # PNG with POV-Ray 3.7, can show the background color with alpha. In the long run using the POV-Ray interactive preview like bishop 3D could solve the preview for all formats.
            #self._temp_file_out = renderImagePath + ".tga"
            self._temp_file_ini = povPath + ".ini"
            '''
            self._temp_file_in = "/test.pov"
            self._temp_file_out = "/test.png"  # PNG with POV-Ray 3.7, can show the background color with alpha. In the long run using the POV-Ray interactive preview like bishop 3D could solve the preview for all formats.
            #self._temp_file_out = "/test.tga"
            self._temp_file_ini = "/test.ini"
            '''

        def info_callback(txt):
            self.update_stats("", "POV-Ray 3.7: " + txt)

        write_pov(self._temp_file_in, scene, info_callback)

    def _render(self, scene):

        try:
            os.remove(self._temp_file_out)  # so as not to load the old file
        except OSError:
            pass

        write_pov_ini(self._temp_file_ini, self._temp_file_in, self._temp_file_out)

        print ("***-STARTING-***")

        pov_binary = "povray"

        extra_args = []

        if scene.pov_command_line_switches != "":
            for newArg in scene.pov_command_line_switches.split(" "):
                extra_args.append(newArg)

        if sys.platform[:3] == "win":
            import winreg
            import platform as pltfrm
            if pltfrm.architecture()[0] == "64bit":
                bitness = 64
            else:
                bitness = 32

            regKey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\POV-Ray\\v3.7\\Windows")

            #64 bits blender
            if bitness == 64:
                try:
                    pov_binary = winreg.QueryValueEx(regKey, "Home")[0] + "\\bin\\pvengine64"
                except OSError:
                    # someone might run povray 32 bits on a 64 bits blender machine
                    try:
                        pov_binary = winreg.QueryValueEx(regKey, "Home")[0] + "\\bin\\pvengine"
                    except OSError:
                        print("POV-Ray 3.7: could not execute '%s', possibly POV-Ray isn't installed" % pov_binary)
                    else:
                        print("POV-Ray 3.7 64 bits could not execute, running 32 bits instead")
                else:
                    print("POV-Ray 3.7 64 bits found")

            #32 bits blender
            else:
                try:
                    pov_binary = winreg.QueryValueEx(regKey, "Home")[0] + "\\bin\\pvengine"
                # someone might also run povray 64 bits with a 32 bits build of blender.
                except OSError:
                    try:
                        pov_binary = winreg.QueryValueEx(regKey, "Home")[0] + "\\bin\\pvengine64"
                    except OSError:
                        print("POV-Ray 3.7: could not execute '%s', possibly POV-Ray isn't installed" % pov_binary)
                    else:
                        print("Running POV-Ray 3.7 64 bits build with 32 bits Blender, \nYou might want to run Blender 64 bits as well.")
                else:
                    print("POV-Ray 3.7 32 bits found")

        else:
            # DH - added -d option to prevent render window popup which leads to segfault on linux
            extra_args.append("-d")

        # print("Extra Args: " + str(extra_args))

        if 1:
            # TODO, when POV-Ray isn't found this gives a cryptic error, would be nice to be able to detect if it exists
            try:
                self._process = subprocess.Popen([pov_binary, self._temp_file_ini] + extra_args)  # stdout=subprocess.PIPE, stderr=subprocess.PIPE
            except OSError:
                # TODO, report api
                print("POV-Ray 3.7: could not execute '%s', possibly POV-Ray isn't installed" % pov_binary)
                import traceback
                traceback.print_exc()
                print ("***-DONE-***")
                return False

        else:
            # This works too but means we have to wait until its done
            os.system("%s %s" % (pov_binary, self._temp_file_ini))

        # print ("***-DONE-***")
        return True

    def _cleanup(self):
        for f in (self._temp_file_in, self._temp_file_ini, self._temp_file_out):
            try:
                os.unlink(f)
            except OSError:  # was that the proper error type?
                #print("POV-Ray 3.7: could not remove/unlink TEMP file %s" % f.name)
                pass
            #print("")

        self.update_stats("", "")

    def render(self, scene):
        import tempfile

        print("***INITIALIZING***")

##WIP output format
##        if r.file_format == 'OPENEXR':
##            fformat = 'EXR'
##            render.color_mode = 'RGBA'
##        else:
##            fformat = 'TGA'
##            r.file_format = 'TARGA'
##            r.color_mode = 'RGBA'

        blendSceneName = bpy.data.filepath.split(os.path.sep)[-1].split(".")[0]
        povSceneName = ""
        povPath = ""
        renderImagePath = ""

        scene.frame_set(scene.frame_current)  # has to be called to update the frame on exporting animations

        if not scene.pov_tempfiles_enable:

            # check paths
            povPath = bpy.path.abspath(scene.pov_scene_path).replace('\\', '/')
            if povPath == "":
                if bpy.path.abspath("//") != "":
                    povPath = bpy.path.abspath("//")
                else:
                    povPath = tempfile.gettempdir()
            elif povPath.endswith("/"):
                if povPath == "/":
                    povPath = bpy.path.abspath("//")
                else:
                    povPath = bpy.path.abspath(scene.pov_scene_path)

            if not os.path.exists(povPath):
                try:
                    os.makedirs(povPath)
                except:
                    import traceback
                    traceback.print_exc()

                    print("POV-Ray 3.7: Cannot create scenes directory: %r" % povPath)
                    self.update_stats("", "POV-Ray 3.7: Cannot create scenes directory %r" % povPath)
                    time.sleep(2.0)
                    return

            '''
            # Bug in POV-Ray RC3
            renderImagePath = bpy.path.abspath(scene.pov_renderimage_path).replace('\\','/')
            if renderImagePath == "":
                if bpy.path.abspath("//") != "":
                    renderImagePath = bpy.path.abspath("//")
                else:
                    renderImagePath = tempfile.gettempdir()
                #print("Path: " + renderImagePath)
            elif path.endswith("/"):
                if renderImagePath == "/":
                    renderImagePath = bpy.path.abspath("//")
                else:
                    renderImagePath = bpy.path.abspath(scene.pov_renderimage_path)
            if not os.path.exists(path):
                print("POV-Ray 3.7: Cannot find render image directory")
                self.update_stats("", "POV-Ray 3.7: Cannot find render image directory")
                time.sleep(2.0)
                return
            '''

            # check name
            if scene.pov_scene_name == "":
                if blendSceneName != "":
                    povSceneName = blendSceneName
                else:
                    povSceneName = "untitled"
            else:
                povSceneName = scene.pov_scene_name
                if os.path.isfile(povSceneName):
                    povSceneName = os.path.basename(povSceneName)
                povSceneName = povSceneName.split('/')[-1].split('\\')[-1]
                if not povSceneName:
                    print("POV-Ray 3.7: Invalid scene name")
                    self.update_stats("", "POV-Ray 3.7: Invalid scene name")
                    time.sleep(2.0)
                    return
                povSceneName = os.path.splitext(povSceneName)[0]

            print("Scene name: " + povSceneName)
            print("Export path: " + povPath)
            povPath = os.path.join(povPath, povSceneName)
            povPath = os.path.realpath(povPath)

            # renderImagePath = renderImagePath + "\\" + povSceneName  # for now this has to be the same like the pov output. Bug in POV-Ray RC3.
            renderImagePath = povPath  # Bugfix for POV-Ray RC3 bug
            # renderImagePath = os.path.realpath(renderImagePath)  # Bugfix for POV-Ray RC3 bug

            #print("Export path: %s" % povPath)
            #print("Render Image path: %s" % renderImagePath)

        # start export
        self.update_stats("", "POV-Ray 3.7: Exporting data from Blender")
        self._export(scene, povPath, renderImagePath)
        self.update_stats("", "POV-Ray 3.7: Parsing File")

        if not self._render(scene):
            self.update_stats("", "POV-Ray 3.7: Not found")
            return

        r = scene.render
        # compute resolution
        x = int(r.resolution_x * r.resolution_percentage * 0.01)
        y = int(r.resolution_y * r.resolution_percentage * 0.01)

        # Wait for the file to be created
        while not os.path.exists(self._temp_file_out):
            # print("***POV WAITING FOR FILE***")
            if self.test_break():
                try:
                    self._process.terminate()
                    print("***POV INTERRUPTED***")
                except OSError:
                    pass
                break

            poll_result = self._process.poll()
            if poll_result is not None:
                print("***POV PROCESS FAILED : %s ***" % poll_result)
                self.update_stats("", "POV-Ray 3.7: Failed")
                break

            time.sleep(self.DELAY)

        if os.path.exists(self._temp_file_out):
            # print("***POV FILE OK***")
            self.update_stats("", "POV-Ray 3.7: Rendering")

            prev_size = -1

            def update_image():
                xmin = int(r.border_min_x * x)
                ymin = int(r.border_min_y * y)
                xmax = int(r.border_max_x * x)
                ymax = int(r.border_max_y * y)

                # print("***POV UPDATING IMAGE***")
                result = self.begin_result(0, 0, x, y)
                #result = self.begin_result(xmin, ymin, xmax - xmin, ymax - ymin)  # XXX, test for border render.
                lay = result.layers[0]
                # possible the image wont load early on.
                try:
                    lay.load_from_file(self._temp_file_out)
                    #lay.load_from_file(self._temp_file_out, xmin, ymin)  # XXX, test for border render.
                except RuntimeError:
                    pass
                self.end_result(result)

            # Update while POV-Ray renders
            while True:
                # print("***POV RENDER LOOP***")

                # test if POV-Ray exists
                if self._process.poll() is not None:
                    print("***POV PROCESS FINISHED***")
                    update_image()
                    break

                # user exit
                if self.test_break():
                    try:
                        self._process.terminate()
                        print("***POV PROCESS INTERRUPTED***")
                    except OSError:
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
        else:
            print("***POV FILE NOT FOUND***")

        print("***POV FINISHED***")
        #time.sleep(self.DELAY)
        if scene.pov_tempfiles_enable or scene.pov_deletefiles_enable:
            self._cleanup()
