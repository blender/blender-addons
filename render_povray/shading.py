# For BI > POV shaders emulation
import bpy

def writeMaterial(DEF_MAT_NAME, scene, tabWrite, safety, comments, uniqueName, materialNames, material):
    # Assumes only called once on each material
    if material:
        name_orig = material.name
        name = materialNames[name_orig] = uniqueName(bpy.path.clean_name(name_orig), materialNames)
    else:
        name = name_orig = DEF_MAT_NAME


    if material:
        # If saturation(.s) is not zero, then color is not grey, and has a tint
        colored_specular_found = (material.specular_color.s > 0.0)

    ##################
    # Several versions of the finish: Level conditions are variations for specular/Mirror
    # texture channel map with alternative finish of 0 specular and no mirror reflection.
    # Level=1 Means No specular nor Mirror reflection
    # Level=2 Means translation of spec and mir levels for when no map influences them
    # Level=3 Means Maximum Spec and Mirror

    def povHasnoSpecularMaps(Level):
        if Level == 1:
            tabWrite("#declare %s = finish {" % safety(name, Level=1))
            if comments:
                file.write("  //No specular nor Mirror reflection\n")
            else:
                tabWrite("\n")
        elif Level == 2:
            tabWrite("#declare %s = finish {" % safety(name, Level=2))
            if comments:
                file.write("  //translation of spec and mir levels for when no map " \
                           "influences them\n")
            else:
                tabWrite("\n")
        elif Level == 3:
            tabWrite("#declare %s = finish {" % safety(name, Level=3))
            if comments:
                file.write("  //Maximum Spec and Mirror\n")
            else:
                tabWrite("\n")

        if material:
            # POV-Ray 3.7 now uses two diffuse values respectively for front and back shading
            # (the back diffuse is like blender translucency)
            frontDiffuse = material.diffuse_intensity
            backDiffuse = material.translucency

            if material.pov.conserve_energy:

                #Total should not go above one
                if (frontDiffuse + backDiffuse) <= 1.0:
                    pass
                elif frontDiffuse == backDiffuse:
                    # Try to respect the user's 'intention' by comparing the two values but
                    # bringing the total back to one.
                    frontDiffuse = backDiffuse = 0.5
                # Let the highest value stay the highest value.
                elif frontDiffuse > backDiffuse:
                    # clamps the sum below 1
                    backDiffuse = min(backDiffuse, (1.0 - frontDiffuse))
                else:
                    frontDiffuse = min(frontDiffuse, (1.0 - backDiffuse))

            # map hardness between 0.0 and 1.0
            roughness = ((1.0 - ((material.specular_hardness - 1.0) / 510.0)))
            ## scale from 0.0 to 0.1
            roughness *= 0.1
            # add a small value because 0.0 is invalid.
            roughness += (1.0 / 511.0)

            ################################Diffuse Shader######################################
            # Not used for Full spec (Level=3) of the shader.
            if material.diffuse_shader == 'OREN_NAYAR' and Level != 3:
                # Blender roughness is what is generally called oren nayar Sigma,
                # and brilliance in POV-Ray.
                tabWrite("brilliance %.3g\n" % (0.9 + material.roughness))

            if material.diffuse_shader == 'TOON' and Level != 3:
                tabWrite("brilliance %.3g\n" % (0.01 + material.diffuse_toon_smooth * 0.25))
                # Lower diffuse and increase specular for toon effect seems to look better
                # in POV-Ray.
                frontDiffuse *= 0.5

            if material.diffuse_shader == 'MINNAERT' and Level != 3:
                #tabWrite("aoi %.3g\n" % material.darkness)
                pass  # let's keep things simple for now
            if material.diffuse_shader == 'FRESNEL' and Level != 3:
                #tabWrite("aoi %.3g\n" % material.diffuse_fresnel_factor)
                pass  # let's keep things simple for now
            if material.diffuse_shader == 'LAMBERT' and Level != 3:
                # trying to best match lambert attenuation by that constant brilliance value
                tabWrite("brilliance 1.8\n")

            if Level == 2:
                ###########################Specular Shader######################################
                # No difference between phong and cook torrence in blender HaHa!
                if (material.specular_shader == 'COOKTORR' or
                    material.specular_shader == 'PHONG'):
                    tabWrite("phong %.3g\n" % (material.specular_intensity))
                    tabWrite("phong_size %.3g\n" % (material.specular_hardness / 2 + 0.25))

                # POV-Ray 'specular' keyword corresponds to a Blinn model, without the ior.
                elif material.specular_shader == 'BLINN':
                    # Use blender Blinn's IOR just as some factor for spec intensity
                    tabWrite("specular %.3g\n" % (material.specular_intensity *
                                                  (material.specular_ior / 4.0)))
                    tabWrite("roughness %.3g\n" % roughness)
                    #Could use brilliance 2(or varying around 2 depending on ior or factor) too.

                elif material.specular_shader == 'TOON':
                    tabWrite("phong %.3g\n" % (material.specular_intensity * 2.0))
                    # use extreme phong_size
                    tabWrite("phong_size %.3g\n" % (0.1 + material.specular_toon_smooth / 2.0))

                elif material.specular_shader == 'WARDISO':
                    # find best suited default constant for brilliance Use both phong and
                    # specular for some values.
                    tabWrite("specular %.3g\n" % (material.specular_intensity /
                                                  (material.specular_slope + 0.0005)))
                    # find best suited default constant for brilliance Use both phong and
                    # specular for some values.
                    tabWrite("roughness %.4g\n" % (0.0005 + material.specular_slope / 10.0))
                    # find best suited default constant for brilliance Use both phong and
                    # specular for some values.
                    tabWrite("brilliance %.4g\n" % (1.8 - material.specular_slope * 1.8))

            ####################################################################################
            elif Level == 1:
                tabWrite("specular 0\n")
            elif Level == 3:
                tabWrite("specular 1\n")
            tabWrite("diffuse %.3g %.3g\n" % (frontDiffuse, backDiffuse))

            tabWrite("ambient %.3g\n" % material.ambient)
            # POV-Ray blends the global value
            #tabWrite("ambient rgb <%.3g, %.3g, %.3g>\n" % \
            #         tuple([c*material.ambient for c in world.ambient_color]))
            tabWrite("emission %.3g\n" % material.emit)  # New in POV-Ray 3.7

            #POV-Ray just ignores roughness if there's no specular keyword
            #tabWrite("roughness %.3g\n" % roughness)

            if material.pov.conserve_energy:
                # added for more realistic shading. Needs some checking to see if it
                # really works. --Maurice.
                tabWrite("conserve_energy\n")

            if colored_specular_found == True:
                 tabWrite("metallic\n")          

            # 'phong 70.0 '
            if Level != 1:
                if material.raytrace_mirror.use:
                    raytrace_mirror = material.raytrace_mirror
                    if raytrace_mirror.reflect_factor:
                        tabWrite("reflection {\n")
                        tabWrite("rgb <%.3g, %.3g, %.3g>\n" % material.mirror_color[:])                          
                        if material.pov.mirror_metallic:
                            tabWrite("metallic %.3g\n" % (raytrace_mirror.reflect_factor))
                        # Blurry reflections for UberPOV
                        if using_uberpov and raytrace_mirror.gloss_factor < 1.0:
                            #tabWrite("#ifdef(unofficial) #if(unofficial = \"patch\") #if(patch(\"upov-reflection-roughness\") > 0)\n")
                            tabWrite("roughness %.6f\n" % \
                                     (0.000001/raytrace_mirror.gloss_factor))
                            #tabWrite("#end #end #end\n") # This and previous comment for backward compatibility, messier pov code
                        if material.pov.mirror_use_IOR:  # WORKING ?
                            # Removed from the line below: gives a more physically correct
                            # material but needs proper IOR. --Maurice
                            tabWrite("fresnel 1 ")
                        tabWrite("falloff %.3g exponent %.3g} " % \
                                 (raytrace_mirror.fresnel, raytrace_mirror.fresnel_factor))
                            
            if material.subsurface_scattering.use:
                subsurface_scattering = material.subsurface_scattering
                tabWrite("subsurface { translucency <%.3g, %.3g, %.3g> }\n" % (
                         (subsurface_scattering.radius[0]),
                         (subsurface_scattering.radius[1]),
                         (subsurface_scattering.radius[2]),
                         )
                        )

            if material.pov.irid_enable:
                tabWrite("irid { %.4g thickness %.4g turbulence %.4g }" % \
                         (material.pov.irid_amount, material.pov.irid_thickness,
                          material.pov.irid_turbulence))

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
            if t and t.use:
                if (t.texture.type == 'IMAGE' and t.texture.image) or t.texture.type != 'IMAGE':
                    validPath=True
            else:
                validPath=False
            if(t and t.use and validPath and
               (t.use_map_specular or t.use_map_raymir or t.use_map_normal or t.use_map_alpha)):
                special_texture_found = True
                continue  # Some texture found

        if special_texture_found or colored_specular_found:
            # Level=1 Means No specular nor Mirror reflection
            povHasnoSpecularMaps(Level=1)

            # Level=3 Means Maximum Spec and Mirror
            povHasnoSpecularMaps(Level=3)
