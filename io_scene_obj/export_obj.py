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

import os
import time

import bpy
import mathutils
import bpy_extras.io_utils


def name_compat(name):
    if name is None:
        return 'None'
    else:
        return name.replace(' ', '_')


def write_mtl(scene, filepath, path_mode, copy_set, mtl_dict):
    from mathutils import Color

    world = scene.world
    if world:
        world_amb = world.ambient_color
    else:
        world_amb = Color((0.0, 0.0, 0.0))

    source_dir = os.path.dirname(bpy.data.filepath)
    dest_dir = os.path.dirname(filepath)

    file = open(filepath, "w", encoding="utf8", newline="\n")
    fw = file.write

    fw('# Blender MTL File: %r\n' % (os.path.basename(bpy.data.filepath) or "None"))
    fw('# Material Count: %i\n' % len(mtl_dict))

    mtl_dict_values = list(mtl_dict.values())
    mtl_dict_values.sort(key=lambda m: m[0])

    # Write material/image combinations we have used.
    # Using mtl_dict.values() directly gives un-predictable order.
    for mtl_mat_name, mat, face_img in mtl_dict_values:

        # Get the Blender data for the material and the image.
        # Having an image named None will make a bug, dont do it :)

        fw('\nnewmtl %s\n' % mtl_mat_name)  # Define a new material: matname_imgname

        if mat:
            # convert from blenders spec to 0 - 1000 range.
            if mat.specular_shader == 'WARDISO':
                tspec = (0.4 - mat.specular_slope) / 0.0004
            else:
                tspec = (mat.specular_hardness - 1) * 1.9607843137254901
            fw('Ns %.6f\n' % tspec)
            del tspec

            fw('Ka %.6f %.6f %.6f\n' % (mat.ambient * world_amb)[:])  # Ambient, uses mirror color,
            fw('Kd %.6f %.6f %.6f\n' % (mat.diffuse_intensity * mat.diffuse_color)[:])  # Diffuse
            fw('Ks %.6f %.6f %.6f\n' % (mat.specular_intensity * mat.specular_color)[:])  # Specular
            if hasattr(mat, "ior"):
                fw('Ni %.6f\n' % mat.ior)  # Refraction index
            else:
                fw('Ni %.6f\n' % 1.0)
            fw('d %.6f\n' % mat.alpha)  # Alpha (obj uses 'd' for dissolve)

            # 0 to disable lighting, 1 for ambient & diffuse only (specular color set to black), 2 for full lighting.
            if mat.use_shadeless:
                fw('illum 0\n')  # ignore lighting
            elif mat.specular_intensity == 0:
                fw('illum 1\n')  # no specular.
            else:
                fw('illum 2\n')  # light normaly

        else:
            #write a dummy material here?
            fw('Ns 0\n')
            fw('Ka %.6f %.6f %.6f\n' % world_amb[:])  # Ambient, uses mirror color,
            fw('Kd 0.8 0.8 0.8\n')
            fw('Ks 0.8 0.8 0.8\n')
            fw('d 1\n')  # No alpha
            fw('illum 2\n')  # light normaly

        # Write images!
        if face_img:  # We have an image on the face!
            filepath = face_img.filepath
            if filepath:  # may be '' for generated images
                # write relative image path
                filepath = bpy_extras.io_utils.path_reference(filepath, source_dir, dest_dir,
                                                              path_mode, "", copy_set, face_img.library)
                fw('map_Kd %s\n' % filepath)  # Diffuse mapping image
                del filepath
            else:
                # so we write the materials image.
                face_img = None

        if mat:  # No face image. if we havea material search for MTex image.
            image_map = {}
            # backwards so topmost are highest priority
            for mtex in reversed(mat.texture_slots):
                if mtex and mtex.texture.type == 'IMAGE':
                    image = mtex.texture.image
                    if image:
                        # texface overrides others
                        if      (mtex.use_map_color_diffuse and
                                (face_img is None) and
                                (mtex.use_map_warp is False) and
                                (mtex.texture_coords != 'REFLECTION')):
                            image_map["map_Kd"] = image
                        if mtex.use_map_ambient:
                            image_map["map_Ka"] = image
                        # this is the Spec intensity channel but Ks stands for specular Color
                        '''
                        if mtex.use_map_specular:
                            image_map["map_Ks"] = image
                        '''
                        if mtex.use_map_color_spec:  # specular color
                            image_map["map_Ks"] = image
                        if mtex.use_map_hardness:  # specular hardness/glossiness
                            image_map["map_Ns"] = image
                        if mtex.use_map_alpha:
                            image_map["map_d"] = image
                        if mtex.use_map_translucency:
                            image_map["map_Tr"] = image
                        if mtex.use_map_normal and (mtex.texture.use_normal_map is True):
                            image_map["map_Bump"] = image
                        if mtex.use_map_normal and (mtex.texture.use_normal_map is False):
                            image_map["map_Disp"] = image                      
                        if mtex.use_map_color_diffuse and (mtex.texture_coords == 'REFLECTION'):
                            image_map["map_refl"] = image
                        if mtex.use_map_emit:
                            image_map["map_Ke"] = image

            for key, image in image_map.items():
                filepath = bpy_extras.io_utils.path_reference(image.filepath, source_dir, dest_dir,
                                                              path_mode, "", copy_set, image.library)
                fw('%s %s\n' % (key, repr(filepath)[1:-1]))

    file.close()


def test_nurbs_compat(ob):
    if ob.type != 'CURVE':
        return False

    for nu in ob.data.splines:
        if nu.point_count_v == 1 and nu.type != 'BEZIER':  # not a surface and not bezier
            return True

    return False


def write_nurb(fw, ob, ob_mat):
    tot_verts = 0
    cu = ob.data

    # use negative indices
    for nu in cu.splines:
        if nu.type == 'POLY':
            DEG_ORDER_U = 1
        else:
            DEG_ORDER_U = nu.order_u - 1  # odd but tested to be correct

        if nu.type == 'BEZIER':
            print("\tWarning, bezier curve:", ob.name, "only poly and nurbs curves supported")
            continue

        if nu.point_count_v > 1:
            print("\tWarning, surface:", ob.name, "only poly and nurbs curves supported")
            continue

        if len(nu.points) <= DEG_ORDER_U:
            print("\tWarning, order_u is lower then vert count, skipping:", ob.name)
            continue

        pt_num = 0
        do_closed = nu.use_cyclic_u
        do_endpoints = (do_closed == 0) and nu.use_endpoint_u

        for pt in nu.points:
            fw('v %.6f %.6f %.6f\n' % (ob_mat * pt.co.to_3d())[:])
            pt_num += 1
        tot_verts += pt_num

        fw('g %s\n' % (name_compat(ob.name)))  # name_compat(ob.getData(1)) could use the data name too
        fw('cstype bspline\n')  # not ideal, hard coded
        fw('deg %d\n' % DEG_ORDER_U)  # not used for curves but most files have it still

        curve_ls = [-(i + 1) for i in range(pt_num)]

        # 'curv' keyword
        if do_closed:
            if DEG_ORDER_U == 1:
                pt_num += 1
                curve_ls.append(-1)
            else:
                pt_num += DEG_ORDER_U
                curve_ls = curve_ls + curve_ls[0:DEG_ORDER_U]

        fw('curv 0.0 1.0 %s\n' % (" ".join([str(i) for i in curve_ls])))  # Blender has no U and V values for the curve

        # 'parm' keyword
        tot_parm = (DEG_ORDER_U + 1) + pt_num
        tot_parm_div = float(tot_parm - 1)
        parm_ls = [(i / tot_parm_div) for i in range(tot_parm)]

        if do_endpoints:  # end points, force param
            for i in range(DEG_ORDER_U + 1):
                parm_ls[i] = 0.0
                parm_ls[-(1 + i)] = 1.0

        fw("parm u %s\n" % " ".join(["%.6f" % i for i in parm_ls]))

        fw('end\n')

    return tot_verts


def write_file(filepath, objects, scene,
               EXPORT_TRI=False,
               EXPORT_EDGES=False,
               EXPORT_NORMALS=False,
               EXPORT_UV=True,
               EXPORT_MTL=True,
               EXPORT_APPLY_MODIFIERS=True,
               EXPORT_BLEN_OBS=True,
               EXPORT_GROUP_BY_OB=False,
               EXPORT_GROUP_BY_MAT=False,
               EXPORT_KEEP_VERT_ORDER=False,
               EXPORT_POLYGROUPS=False,
               EXPORT_CURVE_AS_NURBS=True,
               EXPORT_GLOBAL_MATRIX=None,
               EXPORT_PATH_MODE='AUTO',
               ):
    """
    Basic write function. The context and options must be already set
    This can be accessed externaly
    eg.
    write( 'c:\\test\\foobar.obj', Blender.Object.GetSelected() ) # Using default options.
    """

    if EXPORT_GLOBAL_MATRIX is None:
        EXPORT_GLOBAL_MATRIX = mathutils.Matrix()

    def veckey3d(v):
        return round(v.x, 6), round(v.y, 6), round(v.z, 6)

    def veckey2d(v):
        return round(v[0], 6), round(v[1], 6)

    def findVertexGroupName(face, vWeightMap):
        """
        Searches the vertexDict to see what groups is assigned to a given face.
        We use a frequency system in order to sort out the name because a given vetex can
        belong to two or more groups at the same time. To find the right name for the face
        we list all the possible vertex group names with their frequency and then sort by
        frequency in descend order. The top element is the one shared by the highest number
        of vertices is the face's group
        """
        weightDict = {}
        for vert_index in face.vertices:
            vWeights = vWeightMap[vert_index]
            for vGroupName, weight in vWeights:
                weightDict[vGroupName] = weightDict.get(vGroupName, 0.0) + weight

        if weightDict:
            return max((weight, vGroupName) for vGroupName, weight in weightDict.items())[1]
        else:
            return '(null)'

    print('OBJ Export path: %r' % filepath)

    time1 = time.time()

    file = open(filepath, "w", encoding="utf8", newline="\n")
    fw = file.write

    # Write Header
    fw('# Blender v%s OBJ File: %r\n' % (bpy.app.version_string, os.path.basename(bpy.data.filepath)))
    fw('# www.blender.org\n')

    # Tell the obj file what material file to use.
    if EXPORT_MTL:
        mtlfilepath = os.path.splitext(filepath)[0] + ".mtl"
        fw('mtllib %s\n' % repr(os.path.basename(mtlfilepath))[1:-1])  # filepath can contain non utf8 chars, use repr

    # Initialize totals, these are updated each object
    totverts = totuvco = totno = 1

    face_vert_index = 1

    globalNormals = {}

    # A Dict of Materials
    # (material.name, image.name):matname_imagename # matname_imagename has gaps removed.
    mtl_dict = {}
    # Used to reduce the usage of matname_texname materials, which can become annoying in case of
    # repeated exports/imports, yet keeping unique mat names per keys!
    # mtl_name: (material.name, image.name)
    mtl_rev_dict = {}

    copy_set = set()

    # Get all meshes
    for ob_main in objects:

        # ignore dupli children
        if ob_main.parent and ob_main.parent.dupli_type in {'VERTS', 'FACES'}:
            # XXX
            print(ob_main.name, 'is a dupli child - ignoring')
            continue

        obs = []
        if ob_main.dupli_type != 'NONE':
            # XXX
            print('creating dupli_list on', ob_main.name)
            ob_main.dupli_list_create(scene)

            obs = [(dob.object, dob.matrix) for dob in ob_main.dupli_list]

            # XXX debug print
            print(ob_main.name, 'has', len(obs), 'dupli children')
        else:
            obs = [(ob_main, ob_main.matrix_world)]

        for ob, ob_mat in obs:

            # Nurbs curve support
            if EXPORT_CURVE_AS_NURBS and test_nurbs_compat(ob):
                ob_mat = EXPORT_GLOBAL_MATRIX * ob_mat
                totverts += write_nurb(fw, ob, ob_mat)
                continue
            # END NURBS

            try:
                me = ob.to_mesh(scene, EXPORT_APPLY_MODIFIERS, 'PREVIEW')
            except RuntimeError:
                me = None

            if me is None:
                continue

            me.transform(EXPORT_GLOBAL_MATRIX * ob_mat)

            if EXPORT_UV:
                faceuv = len(me.uv_textures) > 0
                if faceuv:
                    uv_layer = me.tessface_uv_textures.active.data[:]
            else:
                faceuv = False

            me_verts = me.vertices[:]

            # Make our own list so it can be sorted to reduce context switching
            face_index_pairs = [(face, index) for index, face in enumerate(me.tessfaces)]
            # faces = [ f for f in me.tessfaces ]

            if EXPORT_EDGES:
                edges = me.edges
            else:
                edges = []

            if not (len(face_index_pairs) + len(edges) + len(me.vertices)):  # Make sure there is somthing to write

                # clean up
                bpy.data.meshes.remove(me)

                continue  # dont bother with this mesh.

            if EXPORT_NORMALS and face_index_pairs:
                me.calc_normals()

            materials = me.materials[:]
            material_names = [m.name if m else None for m in materials]

            # avoid bad index errors
            if not materials:
                materials = [None]
                material_names = [name_compat(None)]

            # Sort by Material, then images
            # so we dont over context switch in the obj file.
            if EXPORT_KEEP_VERT_ORDER:
                pass
            elif faceuv:
                face_index_pairs.sort(key=lambda a: (a[0].material_index, hash(uv_layer[a[1]].image), a[0].use_smooth))
            elif len(materials) > 1:
                face_index_pairs.sort(key=lambda a: (a[0].material_index, a[0].use_smooth))
            else:
                # no materials
                face_index_pairs.sort(key=lambda a: a[0].use_smooth)

            # Set the default mat to no material and no image.
            contextMat = 0, 0  # Can never be this, so we will label a new material the first chance we get.
            contextSmooth = None  # Will either be true or false,  set bad to force initialization switch.

            if EXPORT_BLEN_OBS or EXPORT_GROUP_BY_OB:
                name1 = ob.name
                name2 = ob.data.name
                if name1 == name2:
                    obnamestring = name_compat(name1)
                else:
                    obnamestring = '%s_%s' % (name_compat(name1), name_compat(name2))

                if EXPORT_BLEN_OBS:
                    fw('o %s\n' % obnamestring)  # Write Object name
                else:  # if EXPORT_GROUP_BY_OB:
                    fw('g %s\n' % obnamestring)

            # Vert
            for v in me_verts:
                fw('v %.6f %.6f %.6f\n' % v.co[:])

            # UV
            if faceuv:
                # in case removing some of these dont get defined.
                uv = uvkey = uv_dict = f_index = uv_index = None

                uv_face_mapping = [[0, 0, 0, 0] for i in range(len(face_index_pairs))]  # a bit of a waste for tri's :/

                uv_dict = {}  # could use a set() here
                uv_layer = me.tessface_uv_textures.active.data
                for f, f_index in face_index_pairs:
                    for uv_index, uv in enumerate(uv_layer[f_index].uv):
                        uvkey = veckey2d(uv)
                        try:
                            uv_face_mapping[f_index][uv_index] = uv_dict[uvkey]
                        except:
                            uv_face_mapping[f_index][uv_index] = uv_dict[uvkey] = len(uv_dict)
                            fw('vt %.6f %.6f\n' % uv[:])

                uv_unique_count = len(uv_dict)

                del uv, uvkey, uv_dict, f_index, uv_index
                # Only need uv_unique_count and uv_face_mapping

            # NORMAL, Smooth/Non smoothed.
            if EXPORT_NORMALS:
                for f, f_index in face_index_pairs:
                    if f.use_smooth:
                        for v_idx in f.vertices:
                            v = me_verts[v_idx]
                            noKey = veckey3d(v.normal)
                            if noKey not in globalNormals:
                                globalNormals[noKey] = totno
                                totno += 1
                                fw('vn %.6f %.6f %.6f\n' % noKey)
                    else:
                        # Hard, 1 normal from the face.
                        noKey = veckey3d(f.normal)
                        if noKey not in globalNormals:
                            globalNormals[noKey] = totno
                            totno += 1
                            fw('vn %.6f %.6f %.6f\n' % noKey)

            if not faceuv:
                f_image = None

            # XXX
            if EXPORT_POLYGROUPS:
                # Retrieve the list of vertex groups
                vertGroupNames = ob.vertex_groups.keys()
                if vertGroupNames:
                    currentVGroup = ''
                    # Create a dictionary keyed by face id and listing, for each vertex, the vertex groups it belongs to
                    vgroupsMap = [[] for _i in range(len(me_verts))]
                    for v_idx, v_ls in enumerate(vgroupsMap):
                        v_ls[:] = [(vertGroupNames[g.group], g.weight) for g in me_verts[v_idx].groups]

            for f, f_index in face_index_pairs:
                f_smooth = f.use_smooth
                f_mat = min(f.material_index, len(materials) - 1)

                if faceuv:
                    tface = uv_layer[f_index]
                    f_image = tface.image

                # MAKE KEY
                if faceuv and f_image:  # Object is always true.
                    key = material_names[f_mat], f_image.name
                else:
                    key = material_names[f_mat], None  # No image, use None instead.

                # Write the vertex group
                if EXPORT_POLYGROUPS:
                    if vertGroupNames:
                        # find what vertext group the face belongs to
                        vgroup_of_face = findVertexGroupName(f, vgroupsMap)
                        if vgroup_of_face != currentVGroup:
                            currentVGroup = vgroup_of_face
                            fw('g %s\n' % vgroup_of_face)

                # CHECK FOR CONTEXT SWITCH
                if key == contextMat:
                    pass  # Context already switched, dont do anything
                else:
                    if key[0] is None and key[1] is None:
                        # Write a null material, since we know the context has changed.
                        if EXPORT_GROUP_BY_MAT:
                            # can be mat_image or (null)
                            fw("g %s_%s\n" % (name_compat(ob.name), name_compat(ob.data.name)))  # can be mat_image or (null)
                        if EXPORT_MTL:
                            fw("usemtl (null)\n")  # mat, image

                    else:
                        mat_data = mtl_dict.get(key)
                        if not mat_data:
                            # First add to global dict so we can export to mtl
                            # Then write mtl

                            # Make a new names from the mat and image name,
                            # converting any spaces to underscores with name_compat.

                            # If none image dont bother adding it to the name
                            # Try to avoid as much as possible adding texname (or other things)
                            # to the mtl name (see [#32102])...
                            mtl_name = "%s" % name_compat(key[0])
                            if mtl_rev_dict.get(mtl_name, None) not in {key, None}:
                                if key[1] is None:
                                    tmp_ext = "_NONE"
                                else:
                                    tmp_ext = "_%s" % name_compat(key[1])
                                i = 0
                                while mtl_rev_dict.get(mtl_name + tmp_ext, None) not in {key, None}:
                                    i += 1
                                    tmp_ext = "_%3d" % i
                                mtl_name += tmp_ext
                            mat_data = mtl_dict[key] = mtl_name, materials[f_mat], f_image
                            mtl_rev_dict[mtl_name] = key

                        if EXPORT_GROUP_BY_MAT:
                            fw("g %s_%s_%s\n" % (name_compat(ob.name), name_compat(ob.data.name), mat_data[0]))  # can be mat_image or (null)
                        if EXPORT_MTL:
                            fw("usemtl %s\n" % mat_data[0])  # can be mat_image or (null)

                contextMat = key
                if f_smooth != contextSmooth:
                    if f_smooth:  # on now off
                        fw('s 1\n')
                        contextSmooth = f_smooth
                    else:  # was off now on
                        fw('s off\n')
                        contextSmooth = f_smooth

                f_v_orig = [(vi, me_verts[v_idx]) for vi, v_idx in enumerate(f.vertices)]

                if not EXPORT_TRI or len(f_v_orig) == 3:
                    f_v_iter = (f_v_orig, )
                else:
                    f_v_iter = (f_v_orig[0], f_v_orig[1], f_v_orig[2]), (f_v_orig[0], f_v_orig[2], f_v_orig[3])

                # support for triangulation
                for f_v in f_v_iter:
                    fw('f')

                    if faceuv:
                        if EXPORT_NORMALS:
                            if f_smooth:  # Smoothed, use vertex normals
                                for vi, v in f_v:
                                    fw(" %d/%d/%d" %
                                               (v.index + totverts,
                                                totuvco + uv_face_mapping[f_index][vi],
                                                globalNormals[veckey3d(v.normal)],
                                                ))  # vert, uv, normal

                            else:  # No smoothing, face normals
                                no = globalNormals[veckey3d(f.normal)]
                                for vi, v in f_v:
                                    fw(" %d/%d/%d" %
                                               (v.index + totverts,
                                                totuvco + uv_face_mapping[f_index][vi],
                                                no,
                                                ))  # vert, uv, normal
                        else:  # No Normals
                            for vi, v in f_v:
                                fw(" %d/%d" % (
                                           v.index + totverts,
                                           totuvco + uv_face_mapping[f_index][vi],
                                           ))  # vert, uv

                        face_vert_index += len(f_v)

                    else:  # No UV's
                        if EXPORT_NORMALS:
                            if f_smooth:  # Smoothed, use vertex normals
                                for vi, v in f_v:
                                    fw(" %d//%d" % (
                                               v.index + totverts,
                                               globalNormals[veckey3d(v.normal)],
                                               ))
                            else:  # No smoothing, face normals
                                no = globalNormals[veckey3d(f.normal)]
                                for vi, v in f_v:
                                    fw(" %d//%d" % (v.index + totverts, no))
                        else:  # No Normals
                            for vi, v in f_v:
                                fw(" %d" % (v.index + totverts))

                    fw('\n')

            # Write edges.
            if EXPORT_EDGES:
                for ed in edges:
                    if ed.is_loose:
                        fw('f %d %d\n' % (ed.vertices[0] + totverts, ed.vertices[1] + totverts))

            # Make the indices global rather then per mesh
            totverts += len(me_verts)
            if faceuv:
                totuvco += uv_unique_count

            # clean up
            bpy.data.meshes.remove(me)

        if ob_main.dupli_type != 'NONE':
            ob_main.dupli_list_clear()

    file.close()

    # Now we have all our materials, save them
    if EXPORT_MTL:
        write_mtl(scene, mtlfilepath, EXPORT_PATH_MODE, copy_set, mtl_dict)

    # copy all collected files.
    bpy_extras.io_utils.path_reference_copy(copy_set)

    print("OBJ Export time: %.2f" % (time.time() - time1))


def _write(context, filepath,
              EXPORT_TRI,  # ok
              EXPORT_EDGES,
              EXPORT_NORMALS,  # not yet
              EXPORT_UV,  # ok
              EXPORT_MTL,
              EXPORT_APPLY_MODIFIERS,  # ok
              EXPORT_BLEN_OBS,
              EXPORT_GROUP_BY_OB,
              EXPORT_GROUP_BY_MAT,
              EXPORT_KEEP_VERT_ORDER,
              EXPORT_POLYGROUPS,
              EXPORT_CURVE_AS_NURBS,
              EXPORT_SEL_ONLY,  # ok
              EXPORT_ANIMATION,
              EXPORT_GLOBAL_MATRIX,
              EXPORT_PATH_MODE,
              ):  # Not used

    base_name, ext = os.path.splitext(filepath)
    context_name = [base_name, '', '', ext]  # Base name, scene name, frame number, extension

    scene = context.scene

    # Exit edit mode before exporting, so current object states are exported properly.
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')

    orig_frame = scene.frame_current

    # Export an animation?
    if EXPORT_ANIMATION:
        scene_frames = range(scene.frame_start, scene.frame_end + 1)  # Up to and including the end frame.
    else:
        scene_frames = [orig_frame]  # Dont export an animation.

    # Loop through all frames in the scene and export.
    for frame in scene_frames:
        if EXPORT_ANIMATION:  # Add frame to the filepath.
            context_name[2] = '_%.6d' % frame

        scene.frame_set(frame, 0.0)
        if EXPORT_SEL_ONLY:
            objects = context.selected_objects
        else:
            objects = scene.objects

        full_path = ''.join(context_name)

        # erm... bit of a problem here, this can overwrite files when exporting frames. not too bad.
        # EXPORT THE FILE.
        write_file(full_path, objects, scene,
                   EXPORT_TRI,
                   EXPORT_EDGES,
                   EXPORT_NORMALS,
                   EXPORT_UV,
                   EXPORT_MTL,
                   EXPORT_APPLY_MODIFIERS,
                   EXPORT_BLEN_OBS,
                   EXPORT_GROUP_BY_OB,
                   EXPORT_GROUP_BY_MAT,
                   EXPORT_KEEP_VERT_ORDER,
                   EXPORT_POLYGROUPS,
                   EXPORT_CURVE_AS_NURBS,
                   EXPORT_GLOBAL_MATRIX,
                   EXPORT_PATH_MODE,
                   )

    scene.frame_set(orig_frame, 0.0)

    # Restore old active scene.
#   orig_scene.makeCurrent()
#   Window.WaitCursor(0)


"""
Currently the exporter lacks these features:
* multiple scene export (only active scene is written)
* particles
"""


def save(operator, context, filepath="",
         use_triangles=False,
         use_edges=True,
         use_normals=False,
         use_uvs=True,
         use_materials=True,
         use_apply_modifiers=True,
         use_blen_objects=True,
         group_by_object=False,
         group_by_material=False,
         keep_vertex_order=False,
         use_vertex_groups=False,
         use_nurbs=True,
         use_selection=True,
         use_animation=False,
         global_matrix=None,
         path_mode='AUTO'
         ):

    _write(context, filepath,
           EXPORT_TRI=use_triangles,
           EXPORT_EDGES=use_edges,
           EXPORT_NORMALS=use_normals,
           EXPORT_UV=use_uvs,
           EXPORT_MTL=use_materials,
           EXPORT_APPLY_MODIFIERS=use_apply_modifiers,
           EXPORT_BLEN_OBS=use_blen_objects,
           EXPORT_GROUP_BY_OB=group_by_object,
           EXPORT_GROUP_BY_MAT=group_by_material,
           EXPORT_KEEP_VERT_ORDER=keep_vertex_order,
           EXPORT_POLYGROUPS=use_vertex_groups,
           EXPORT_CURVE_AS_NURBS=use_nurbs,
           EXPORT_SEL_ONLY=use_selection,
           EXPORT_ANIMATION=use_animation,
           EXPORT_GLOBAL_MATRIX=global_matrix,
           EXPORT_PATH_MODE=path_mode,
           )

    return {'FINISHED'}
