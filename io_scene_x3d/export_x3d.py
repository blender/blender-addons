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

# Contributors: bart:neeneenee*de, http://www.neeneenee.de/vrml, Campbell Barton

"""
This script exports to X3D format.

Usage:
Run this script from "File->Export" menu.  A pop-up will ask whether you
want to export only selected or all relevant objects.

Known issues:
    Doesn't handle multiple materials (don't use material indices);<br>
    Doesn't handle multiple UV textures on a single mesh (create a mesh for each texture);<br>
    Can't get the texture array associated with material * not the UV ones;
"""

import math
import os

import bpy
import mathutils

from bpy_extras.io_utils import create_derived_objects, free_derived_objects

x3d_names_reserved = {"Anchor", "Appearance", "Arc2D", "ArcClose2D", "AudioClip", "Background", "Billboard",
                      "BooleanFilter", "BooleanSequencer", "BooleanToggle", "BooleanTrigger", "Box", "Circle2D",
                      "Collision", "Color", "ColorInterpolator", "ColorRGBA", "component", "Cone", "connect",
                      "Contour2D", "ContourPolyline2D", "Coordinate", "CoordinateDouble", "CoordinateInterpolator",
                      "CoordinateInterpolator2D", "Cylinder", "CylinderSensor", "DirectionalLight", "Disk2D",
                      "ElevationGrid", "EspduTransform", "EXPORT", "ExternProtoDeclare", "Extrusion", "field",
                      "fieldValue", "FillProperties", "Fog", "FontStyle", "GeoCoordinate", "GeoElevationGrid",
                      "GeoLocationLocation", "GeoLOD", "GeoMetadata", "GeoOrigin", "GeoPositionInterpolator",
                      "GeoTouchSensor", "GeoViewpoint", "Group", "HAnimDisplacer", "HAnimHumanoid", "HAnimJoint",
                      "HAnimSegment", "HAnimSite", "head", "ImageTexture", "IMPORT", "IndexedFaceSet",
                      "IndexedLineSet", "IndexedTriangleFanSet", "IndexedTriangleSet", "IndexedTriangleStripSet",
                      "Inline", "IntegerSequencer", "IntegerTrigger", "IS", "KeySensor", "LineProperties", "LineSet",
                      "LoadSensor", "LOD", "Material", "meta", "MetadataDouble", "MetadataFloat", "MetadataInteger",
                      "MetadataSet", "MetadataString", "MovieTexture", "MultiTexture", "MultiTextureCoordinate",
                      "MultiTextureTransform", "NavigationInfo", "Normal", "NormalInterpolator", "NurbsCurve",
                      "NurbsCurve2D", "NurbsOrientationInterpolator", "NurbsPatchSurface",
                      "NurbsPositionInterpolator", "NurbsSet", "NurbsSurfaceInterpolator", "NurbsSweptSurface",
                      "NurbsSwungSurface", "NurbsTextureCoordinate", "NurbsTrimmedSurface", "OrientationInterpolator",
                      "PixelTexture", "PlaneSensor", "PointLight", "PointSet", "Polyline2D", "Polypoint2D",
                      "PositionInterpolator", "PositionInterpolator2D", "ProtoBody", "ProtoDeclare", "ProtoInstance",
                      "ProtoInterface", "ProximitySensor", "ReceiverPdu", "Rectangle2D", "ROUTE", "ScalarInterpolator",
                      "Scene", "Script", "Shape", "SignalPdu", "Sound", "Sphere", "SphereSensor", "SpotLight", "StaticGroup",
                      "StringSensor", "Switch", "Text", "TextureBackground", "TextureCoordinate", "TextureCoordinateGenerator",
                      "TextureTransform", "TimeSensor", "TimeTrigger", "TouchSensor", "Transform", "TransmitterPdu",
                      "TriangleFanSet", "TriangleSet", "TriangleSet2D", "TriangleStripSet", "Viewpoint", "VisibilitySensor",
                      "WorldInfo", "X3D", "XvlShell", "VertexShader", "FragmentShader", "MultiShaderAppearance", "ShaderAppearance"}


def clamp_color(col):
    return tuple([max(min(c, 1.0), 0.0) for c in col])


def matrix_direction_neg_z(mtx):
    return (mathutils.Vector((0.0, 0.0, -1.0)) * mtx.to_3x3()).normalized()[:]


def clean_str(name, prefix='rsvd_'):
    """cleanStr(name,prefix) - try to create a valid VRML DEF name from object name"""

    newName = name

    if newName in x3d_names_reserved:
        newName = '%s%s' % (prefix, newName)

    if newName[0].isdigit():
        newName = "%s%s" % ("_", newName)

    for bad in [' ', '"', '#', "'", ', ', '.', '[', '\\', ']', '{', '}']:
        newName = newName.replace(bad, "_")
    return newName


##########################################################
# Functions for writing output file
##########################################################


def export(file,
           global_matrix,
           scene,
           use_apply_modifiers=False,
           use_selection=True,
           use_triangulate=False,
           use_normals=False,
           ):

    fw = file.write

##########################################################
# Writing nodes routines
##########################################################

    def writeHeader(ident):
        filepath = fw.__self__.name
        #bfile = sys.expandpath( Blender.Get('filepath') ).replace('<', '&lt').replace('>', '&gt')
        bfile = repr(os.path.basename(filepath).replace('<', '&lt').replace('>', '&gt'))[1:-1]  # use outfile name
        fw("%s<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" % ident)
        fw("%s<!DOCTYPE X3D PUBLIC \"ISO//Web3D//DTD X3D 3.0//EN\" \"http://www.web3d.org/specifications/x3d-3.0.dtd\">\n" % ident)
        fw("%s<X3D version=\"3.0\" profile=\"Immersive\" xmlns:xsd=\"http://www.w3.org/2001/XMLSchema-instance\" xsd:noNamespaceSchemaLocation=\"http://www.web3d.org/specifications/x3d-3.0.xsd\">\n" % ident)
        ident += "\t"
        fw("%s<head>\n" % ident)
        ident += "\t"
        fw("%s<meta name=\"filename\" content=\"%s\" />\n" % (ident, bfile))
        fw("%s<meta name=\"generator\" content=\"Blender %s\" />\n" % (ident, bpy.app.version_string))
        fw("%s<meta name=\"translator\" content=\"X3D exporter v1.55 (2006/01/17)\" />\n" % ident)
        ident = ident[:-1]
        fw("%s</head>\n" % ident)
        fw("%s<Scene>\n" % ident)
        ident += "\t"
        return ident

    def writeFooter(ident):
        ident = ident[:-1]
        fw("%s</Scene>\n" % ident)
        ident = ident[:-1]
        fw("%s</X3D>" % ident)
        return ident

    def writeViewpoint(ident, ob, mat, scene):
        loc, quat, scale = mat.decompose()
        fw("%s<Viewpoint DEF=\"%s\" " % (ident, clean_str(ob.name)))
        fw("description=\"%s\" " % ob.name)
        fw("centerOfRotation=\"0 0 0\" ")
        fw("position=\"%3.2f %3.2f %3.2f\" " % loc[:])
        fw("orientation=\"%3.2f %3.2f %3.2f %3.2f\" " % (quat.axis[:] + (quat.angle, )))
        fw("fieldOfView=\"%.3g\" " % ob.data.angle)
        fw(" />\n")

    def writeFog(ident, world):
        if world:
            mtype = world.mist_settings.falloff
            mparam = world.mist_settings
        else:
            return

        if mparam.use_mist:
            fw("%s<Fog fogType=\"%s\" " % (ident, "LINEAR" if (mtype == 'LINEAR') else "EXPONENTIAL"))
            fw("color=\"%.3g %.3g %.3g\" " % clamp_color(world.horizon_color))
            fw("visibilityRange=\"%.3g\" />\n" % mparam.depth)
        else:
            return

    def writeNavigationInfo(ident, scene):
        fw('%s<NavigationInfo headlight="false" visibilityLimit="0.0" type=\'"EXAMINE","ANY"\' avatarSize="0.25, 1.75, 0.75" />\n' % ident)

    def writeSpotLight(ident, ob, mtx, lamp, world):
        safeName = clean_str(ob.name)
        if world:
            ambi = world.ambient_color
            amb_intensity = ((ambi[0] + ambi[1] + ambi[2]) / 3.0) / 2.5
            del ambi
        else:
            amb_intensity = 0.0

        # compute cutoff and beamwidth
        intensity = min(lamp.energy / 1.75, 1.0)
        beamWidth = lamp.spot_size * 0.37
        # beamWidth=((lamp.spotSize*math.pi)/180.0)*.37
        cutOffAngle = beamWidth * 1.3

        orientation = matrix_direction_neg_z(mtx)

        location = mtx.to_translation()[:]

        radius = lamp.distance * math.cos(beamWidth)
        # radius = lamp.dist*math.cos(beamWidth)
        fw("%s<SpotLight DEF=\"%s\" " % (ident, safeName))
        fw("radius=\"%.4g\" " % radius)
        fw("ambientIntensity=\"%.4g\" " % amb_intensity)
        fw("intensity=\"%.4g\" " % intensity)
        fw("color=\"%.4g %.4g %.4g\" " % clamp_color(lamp.color))
        fw("beamWidth=\"%.4g\" " % beamWidth)
        fw("cutOffAngle=\"%.4g\" " % cutOffAngle)
        fw("direction=\"%.4g %.4g %.4g\" " % orientation)
        fw("location=\"%.4g %.4g %.4g\" />\n" % location)

    def writeDirectionalLight(ident, ob, mtx, lamp, world):
        safeName = clean_str(ob.name)
        if world:
            ambi = world.ambient_color
            # ambi = world.amb
            amb_intensity = ((float(ambi[0] + ambi[1] + ambi[2])) / 3.0) / 2.5
        else:
            ambi = 0
            amb_intensity = 0.0

        intensity = min(lamp.energy / 1.75, 1.0)

        orientation = matrix_direction_neg_z(mtx)

        fw("%s<DirectionalLight DEF=\"%s\" " % (ident, safeName))
        fw("ambientIntensity=\"%.4g\" " % amb_intensity)
        fw("color=\"%.4g %.4g %.4g\" " % clamp_color(lamp.color))
        fw("intensity=\"%.4g\" " % intensity)
        fw("direction=\"%.4g %.4g %.4g\" />\n" % orientation)

    def writePointLight(ident, ob, mtx, lamp, world):

        safeName = clean_str(ob.name)
        if world:
            ambi = world.ambient_color
            # ambi = world.amb
            amb_intensity = ((float(ambi[0] + ambi[1] + ambi[2])) / 3.0) / 2.5
        else:
            ambi = 0.0
            amb_intensity = 0.0

        intensity = min(lamp.energy / 1.75, 1.0)
        location = mtx.to_translation()[:]

        fw("%s<PointLight DEF=\"%s\" " % (ident, safeName))
        fw("ambientIntensity=\"%.4g\" " % amb_intensity)
        fw("color=\"%.4g %.4g %.4g\" " % clamp_color(lamp.color))

        fw("intensity=\"%.4g\" " % intensity)
        fw("radius=\"%.4g\" " % lamp.distance)
        fw("location=\"%.4g %.4g %.4g\" />\n" % location)

    def secureName(name):
        name = name + str(secureName.nodeID)
        secureName.nodeID += 1
        if len(name) <= 3:
            newname = "_" + str(secureName.nodeID)
            return "%s" % (newname)
        else:
            for bad in ('"', '#', "'", ', ', '.', '[', '\\', ']', '{', '}'):
                name = name.replace(bad, "_")
            if name in x3d_names_reserved:
                newname = name[0:3] + "_" + str(secureName.nodeID)
                return "%s" % (newname)
            elif name[0].isdigit():
                newname = "_" + name + str(secureName.nodeID)
                return "%s" % (newname)
            else:
                newname = name
                return "%s" % (newname)
    secureName.nodeID = 0

    def writeIndexedFaceSet(ident, ob, mesh, mtx, world):

        shape_name_x3d = clean_str(ob.name)
        mesh_name_x3d = clean_str(mesh.name)

        if not mesh.faces:
            return

        texface_use_halo = 0
        texface_use_billboard = 0
        texface_use_collision = 0

        use_halonode = False
        use_billnode = False
        use_collnode = False

        if mesh.uv_textures.active:  # if mesh.faceUV:
            for face in mesh.uv_textures.active.data:  # for face in mesh.faces:
                texface_use_halo |= face.use_halo
                texface_use_billboard |= face.use_billboard
                texface_use_collision |= face.use_collision
                # texface_use_object_color |= face.use_object_color

        if texface_use_halo:
            fw("%s<Billboard axisOfRotation=\"0 0 0\">\n" % ident)
            use_halonode = True
            ident += "\t"
        elif texface_use_billboard:
            fw("%s<Billboard axisOfRotation=\"0 1 0\">\n" % ident)
            use_billnode = True
            ident += "\t"
        elif texface_use_collision:
            fw("%s<Collision enabled=\"false\">\n" % ident)
            use_collnode = True
            ident += "\t"

        del texface_use_halo
        del texface_use_billboard
        del texface_use_collision
        # del texface_use_object_color

        loc, quat, sca = mtx.decompose()

        fw("%s<Transform DEF=\"%s\" " % (ident, shape_name_x3d))
        fw("translation=\"%.6g %.6g %.6g\" " % loc[:])
        fw("scale=\"%.6g %.6g %.6g\" " % sca[:])
        fw("rotation=\"%.6g %.6g %.6g %.6g\" " % (quat.axis[:] + (quat.angle, )))
        fw(">\n")
        ident += "\t"

        if mesh.tag:
            fw("%s<Group USE=\"G_%s\" />\n" % (ident, mesh_name_x3d))
        else:
            mesh.tag = True

            fw("%s<Group DEF=\"G_%s\">\n" % (ident, mesh_name_x3d))
            ident += "\t"

            is_uv = bool(mesh.uv_textures.active)
            # is_col, defined for each material

            is_coords_written = False

            mesh_materials = mesh.materials[:]
            if not mesh_materials:
                mesh_materials = [None]

            mesh_material_tex = [None] * len(mesh_materials)
            mesh_material_mtex = [None] * len(mesh_materials)
            mesh_material_images = [None] * len(mesh_materials)

            for i, material in enumerate(mesh_materials):
                if material:
                    for mtex in material.texture_slots:
                        if mtex:
                            tex = mtex.texture
                            if tex and tex.type == 'IMAGE':
                                image = tex.image
                                if image:
                                    mesh_material_tex[i] = tex
                                    mesh_material_mtex[i] = mtex
                                    mesh_material_images[i] = image
                                    break

            mesh_materials_use_face_texture = [getattr(material, "use_face_texture", True) for material in mesh_materials]

            # fast access!
            mesh_vertices = mesh.vertices[:]
            mesh_faces = mesh.faces[:]
            mesh_faces_materials = [f.material_index for f in mesh_faces]
            mesh_faces_vertices = [f.vertices[:] for f in mesh_faces]

            if is_uv and True in mesh_materials_use_face_texture:
                mesh_faces_image = [(fuv.image if (mesh_materials_use_face_texture[mesh_faces_materials[i]] and fuv.use_image) else mesh_material_images[mesh_faces_materials[i]]) for i, fuv in enumerate(mesh.uv_textures.active.data)]
                mesh_faces_image_unique = set(mesh_faces_image)
            elif len(set(mesh_material_images) | {None}) > 1:  # make sure there is at least one image
                mesh_faces_image = [mesh_material_images[material_index] for material_index in mesh_faces_materials]
                mesh_faces_image_unique = set(mesh_faces_image)
            else:
                mesh_faces_image = [None] * len(mesh_faces)
                mesh_faces_image_unique = {None}

            # group faces
            face_groups = {}
            for material_index in range(len(mesh_materials)):
                for image in mesh_faces_image_unique:
                    face_groups[material_index, image] = []
            del mesh_faces_image_unique

            for i, (material_index, image) in enumerate(zip(mesh_faces_materials, mesh_faces_image)):
                face_groups[material_index, image].append(i)

            # same as face_groups.items() but sorted so we can get predictable output.
            face_groups_items = list(face_groups.items())
            face_groups_items.sort(key=lambda m: (m[0][0], getattr(m[0][1], "name", "")))

            for (material_index, image), face_group in face_groups_items:  # face_groups.items()
                if face_group:
                    material = mesh_materials[material_index]

                    fw("%s<Shape>\n" % ident)
                    ident += "\t"

                    is_smooth = False
                    is_col = (mesh.vertex_colors.active and (material is None or material.use_vertex_color_paint))

                    # kludge but as good as it gets!
                    for i in face_group:
                        if mesh_faces[i].use_smooth:
                            is_smooth = True
                            break

                    fw("%s<Appearance>\n" % ident)
                    ident += "\t"

                    if image:
                        writeImageTexture(ident, image)

                        if mesh_materials_use_face_texture[material_index]:
                            if image.use_tiles:
                                fw("%s<TextureTransform scale=\"%s %s\" />\n" % (ident, image.tiles_x, image.tiles_y))
                        else:
                            # transform by mtex
                            loc = mesh_material_mtex[material_index].offset[:2]

                            # mtex_scale * tex_repeat
                            sca_x, sca_y = mesh_material_mtex[material_index].scale[:2]

                            sca_x *= mesh_material_tex[material_index].repeat_x
                            sca_y *= mesh_material_tex[material_index].repeat_y

                            # flip x/y is a sampling feature, convert to transform
                            if mesh_material_tex[material_index].use_flip_axis:
                                rot = math.pi / -2.0
                                sca_x, sca_y = sca_y, -sca_x
                            else:
                                rot = 0.0

                            fw("%s<TextureTransform " % ident)
                            # fw("center=\"%.6g %.6g\" " % (0.0, 0.0))
                            fw("translation=\"%.6g %.6g\" " % loc)
                            fw("scale=\"%.6g %.6g\" " % (sca_x, sca_y))
                            fw("rotation=\"%.6g\" " % rot)
                            fw("/>\n")

                    if material:
                        writeMaterial(ident, material, clean_str(material.name, ""), world)

                    ident = ident[:-1]
                    fw("%s</Appearance>\n" % ident)

                    mesh_faces_col = mesh.vertex_colors.active.data if is_col else None
                    mesh_faces_uv = mesh.uv_textures.active.data if is_uv else None

                    #-- IndexedFaceSet or IndexedLineSet
                    if use_triangulate:
                        fw("%s<IndexedTriangleSet " % ident)
                        ident += "\t"

                        # --- Write IndexedTriangleSet Attributes (same as IndexedFaceSet)
                        fw("solid=\"%s\" " % ("true" if mesh.show_double_sided else "false"))
                        if is_smooth:
                            fw("creaseAngle=\"%.4g\" " % mesh.auto_smooth_angle)

                        if use_normals:
                            # currently not optional, could be made so:
                            fw("normalPerVertex=\"true\" ")

                        slot_uv = None
                        slot_col = None

                        if is_uv and is_col:
                            slot_uv = 0
                            slot_col = 1

                            def vertex_key(fidx, f_cnr_idx):
                                return (
                                    mesh_faces_uv[fidx].uv[f_cnr_idx][:],
                                    getattr(mesh_faces_col[fidx], "color%d" % (f_cnr_idx + 1))[:],
                                )
                        elif is_uv:
                            slot_uv = 0

                            def vertex_key(fidx, f_cnr_idx):
                                return (
                                    mesh_faces_uv[fidx].uv[f_cnr_idx].to_tuple(4),
                                )
                        elif is_col:
                            slot_col = 0

                            def vertex_key(fidx, f_cnr_idx):
                                return (
                                    getattr(mesh_faces_col[fidx], "color%d" % (f_cnr_idx))[:],
                                )
                        else:
                            # ack, not especially efficient in this case
                            def vertex_key(fidx, f_cnr_idx):
                                return None

                        # build a mesh mapping dict
                        vertex_hash = [{} for i in range(len(mesh.vertices))]
                        # worst case every face is a quad
                        face_tri_list = [[None, None, None] for i in range(len(mesh.faces) * 2)]
                        vert_tri_list = []
                        totvert = 0
                        totface = 0
                        temp_face = [None] * 4
                        for i in face_group:
                            fv = mesh_faces_vertices[i]
                            for j, v_idx in enumerate(fv):
                                key = vertex_key(i, j)
                                vh = vertex_hash[v_idx]
                                x3d_v = vh.get(key)
                                if x3d_v is None:
                                    x3d_v = key, v_idx, totvert
                                    vh[key] = x3d_v
                                    # key / original_vertex / new_vertex
                                    vert_tri_list.append(x3d_v)
                                    totvert += 1
                                temp_face[j] = x3d_v

                            if len(fv) == 4:
                                f_iter = ((0, 1, 2), (0, 2, 3))
                            else:
                                f_iter = ((0, 1, 2), )

                            for f_it in f_iter:
                                # loop over a quad as 2 tris
                                f_tri = face_tri_list[totface]
                                for ji, j in enumerate(f_it):
                                    f_tri[ji] = temp_face[j]
                                # quads run this twice
                                totface += 1

                        # clear unused faces
                        face_tri_list[totface:] = []

                        fw("index=\"")
                        for x3d_f in face_tri_list:
                            fw("%i %i %i " % (x3d_f[0][2], x3d_f[1][2], x3d_f[2][2]))
                        fw("\" ")

                        # close IndexedTriangleSet
                        fw(">\n")

                        fw("%s<Coordinate " % ident)
                        fw("point=\"")
                        for x3d_v in vert_tri_list:
                            fw("%.6g %.6g %.6g " % mesh_vertices[x3d_v[1]].co[:])
                        fw("\" />\n")

                        if use_normals:
                            fw("%s<Normal " % ident)
                            fw("vector=\"")
                            for x3d_v in vert_tri_list:
                                fw("%.6g %.6g %.6g " % mesh_vertices[x3d_v[1]].normal[:])
                            fw("\" />\n")

                        if is_uv:
                            fw("%s<TextureCoordinate point=\"" % ident)
                            for x3d_v in vert_tri_list:
                                fw("%.4g %.4g " % x3d_v[0][slot_uv])
                            fw("\" />\n")

                        if is_col:
                            fw("%s<Color color=\"" % ident)
                            for x3d_v in vert_tri_list:
                                fw("%.3g %.3g %.3g " % x3d_v[0][slot_col])
                            fw("\" />\n")

                        fw("%s</IndexedTriangleSet>\n" % ident)

                    else:
                        fw("%s<IndexedFaceSet " % ident)
                        ident += "\t"

                        # --- Write IndexedFaceSet Attributes (same as IndexedTriangleSet)
                        fw("solid=\"%s\" " % ("true" if mesh.show_double_sided else "false"))
                        if is_smooth:
                            fw("creaseAngle=\"%.4g\" " % mesh.auto_smooth_angle)

                        if use_normals:
                            # currently not optional, could be made so:
                            fw("normalPerVertex=\"true\" ")

                        # IndexedTriangleSet assumes true
                        if is_col:
                            fw("colorPerVertex=\"false\" ")

                        # for IndexedTriangleSet we use a uv per vertex so this isnt needed.
                        if is_uv:
                            fw("texCoordIndex=\"")

                            j = 0
                            for i in face_group:
                                if len(mesh_faces_vertices[i]) == 4:
                                    fw("%d %d %d %d -1 " % (j, j + 1, j + 2, j + 3))
                                    j += 4
                                else:
                                    fw("%d %d %d -1 " % (j, j + 1, j + 2))
                                    j += 3
                            fw("\" ")
                            # --- end texCoordIndex

                        if True:
                            fw("coordIndex=\"")
                            for i in face_group:
                                fv = mesh_faces_vertices[i]
                                if len(fv) == 3:
                                    fw("%i %i %i -1 " % fv)
                                else:
                                    fw("%i %i %i %i -1 " % fv)

                            fw("\" ")
                            # --- end coordIndex

                        # close IndexedFaceSet
                        fw(">\n")

                        # --- Write IndexedFaceSet Elements
                        if True:
                            if is_coords_written:
                                fw("%s<Coordinate USE=\"%s%s\" />\n" % (ident, "coord_", mesh_name_x3d))
                                if use_normals:
                                    fw("%s<Normal USE=\"%s%s\" />\n" % (ident, "normals_", mesh_name_x3d))
                            else:
                                fw("%s<Coordinate DEF=\"%s%s\" " % (ident, "coord_", mesh_name_x3d))
                                fw("point=\"")
                                for v in mesh.vertices:
                                    fw("%.6g %.6g %.6g " % v.co[:])
                                fw("\" />\n")
                                is_coords_written = True

                                if use_normals:
                                    fw("%s<Normal DEF=\"%s%s\" " % (ident, "normals_", mesh_name_x3d))
                                    fw("vector=\"")
                                    for v in mesh.vertices:
                                        fw("%.6g %.6g %.6g " % v.normal[:])
                                    fw("\" />\n")

                        if is_uv:
                            fw("%s<TextureCoordinate point=\"" % ident)
                            for i in face_group:
                                for uv in mesh_faces_uv[i].uv:
                                    fw("%.4g %.4g " % uv[:])
                            del mesh_faces_uv
                            fw("\" />\n")

                        if is_col:
                            fw("%s<Color color=\"" % ident)
                            # XXX, 1 color per face, only
                            for i in face_group:
                                fw("%.3g %.3g %.3g " % mesh_faces_col[i].color1[:])
                            fw("\" />\n")

                        #--- output vertexColors

                        #--- output closing braces
                        ident = ident[:-1]

                        fw("%s</IndexedFaceSet>\n" % ident)

                    ident = ident[:-1]
                    fw("%s</Shape>\n" % ident)

            ident = ident[:-1]
            fw("%s</Group>\n" % ident)

        ident = ident[:-1]
        fw("%s</Transform>\n" % ident)

        if use_halonode:
            ident = ident[:-1]
            fw("%s</Billboard>\n" % ident)
        elif use_billnode:
            ident = ident[:-1]
            fw("%s</Billboard>\n" % ident)
        elif use_collnode:
            ident = ident[:-1]
            fw("%s</Collision>\n" % ident)

    def writeMaterial(ident, mat, matName, world):
        # look up material name, use it if available
        if mat.tag:
            fw("%s<Material USE=\"MA_%s\" />\n" % (ident, matName))
        else:
            mat.tag = True

            emit = mat.emit
            ambient = mat.ambient / 3.0
            diffuseColor = tuple(mat.diffuse_color)
            if world:
                ambiColor = tuple(((c * mat.ambient) * 2.0) for c in world.ambient_color)
            else:
                ambiColor = 0.0, 0.0, 0.0

            emitColor = tuple(((c * emit) + ambiColor[i]) / 2.0 for i, c in enumerate(diffuseColor))
            shininess = mat.specular_hardness / 512.0
            specColor = tuple((c + 0.001) / (1.25 / (mat.specular_intensity + 0.001)) for c in mat.specular_color)
            transp = 1.0 - mat.alpha

            if mat.use_shadeless:
                ambient = 1.0
                shininess = 0.0
                specColor = emitColor = diffuseColor

            fw("%s<Material DEF=\"MA_%s\" " % (ident, matName))
            fw("diffuseColor=\"%.3g %.3g %.3g\" " % clamp_color(diffuseColor))
            fw("specularColor=\"%.3g %.3g %.3g\" " % clamp_color(specColor))
            fw("emissiveColor=\"%.3g %.3g %.3g\" " % clamp_color(emitColor))
            fw("ambientIntensity=\"%.3g\" " % ambient)
            fw("shininess=\"%.3g\" " % shininess)
            fw("transparency=\"%s\" />\n" % transp)

    def writeImageTexture(ident, image):
        name = image.name

        if image.tag:
            fw("%s<ImageTexture USE=\"%s\" />\n" % (ident, clean_str(name)))
        else:
            image.tag = True

            fw("%s<ImageTexture DEF=\"%s\" " % (ident, clean_str(name)))
            filepath = image.filepath
            relpath = os.path.dirname(fw.__self__.name)  # could cache
            filepath_full = bpy.path.abspath(filepath)
            # collect image paths, can load multiple
            # [relative, name-only, absolute]
            images = []

            if bpy.path.is_subdir(filepath_full, relpath):
                images.append(os.path.relpath(filepath_full, relpath))

            images.append(os.path.basename(filepath_full))
            images.append(filepath_full)

            fw("url='%s' />\n" % " ".join(["\"%s\"" % f.replace("\\", "/") for f in images]))

    def writeBackground(ident, world):

        if world:
            worldname = world.name
        else:
            return

        blending = world.use_sky_blend, world.use_sky_paper, world.use_sky_real

        grd_triple = clamp_color(world.horizon_color)
        sky_triple = clamp_color(world.zenith_color)
        mix_triple = clamp_color((grd_triple[i] + sky_triple[i]) / 2.0 for i in range(3))

        fw("%s<Background DEF=\"%s\" " % (ident, secureName(worldname)))
        # No Skytype - just Hor color
        if blending == (False, False, False):
            fw("groundColor=\"%.3g %.3g %.3g\" " % grd_triple)
            fw("skyColor=\"%.3g %.3g %.3g\" " % grd_triple)
        # Blend Gradient
        elif blending == (True, False, False):
            fw("groundColor=\"%.3g %.3g %.3g, " % grd_triple)
            fw("%.3g %.3g %.3g\" groundAngle=\"1.57, 1.57\" " % mix_triple)
            fw("skyColor=\"%.3g %.3g %.3g, " % sky_triple)
            fw("%.3g %.3g %.3g\" skyAngle=\"1.57, 1.57\" " % mix_triple)
        # Blend+Real Gradient Inverse
        elif blending == (True, False, True):
            fw("groundColor=\"%.3g %.3g %.3g, %.3g %.3g %.3g\" " % (sky_triple + grd_triple))
            fw("groundAngle=\"1.57\" ")
            fw("skyColor=\"%.3g %.3g %.3g, %.3g %.3g %.3g, %.3g %.3g %.3g\" " % (sky_triple + grd_triple + sky_triple))
            fw("skyAngle=\"1.57, 3.14159\" ")
        # Paper - just Zen Color
        elif blending == (False, False, True):
            fw("groundColor=\"%.3g %.3g %.3g\" " % sky_triple)
            fw("skyColor=\"%.3g %.3g %.3g\" " % sky_triple)
        # Blend+Real+Paper - komplex gradient
        elif blending == (True, True, True):
            fw("groundColor=\"%.3g %.3g %.3g, " % sky_triple)
            fw("%.3g %.3g %.3g\" groundAngle=\"1.57, 1.57\" " % grd_triple)
            fw("skyColor=\"%.3g %.3g %.3g, " % sky_triple)
            fw("%.3g %.3g %.3g\" skyAngle=\"1.57, 1.57\" " % grd_triple)
        # Any Other two colors
        else:
            fw("groundColor=\"%.3g %.3g %.3g\" " % grd_triple)
            fw("skyColor=\"%.3g %.3g %.3g\" " % sky_triple)

        for tex in bpy.data.textures:
            if tex.type == 'IMAGE' and tex.image:
                namemat = tex.name
                pic = tex.image
                basename = os.path.basename(bpy.path.abspath(pic.filepath))

                if namemat == "back":
                    fw("\n\tbackUrl=\"%s\" " % basename)
                elif namemat == "bottom":
                    fw("bottomUrl=\"%s\" " % basename)
                elif namemat == "front":
                    fw("frontUrl=\"%s\" " % basename)
                elif namemat == "left":
                    fw("leftUrl=\"%s\" " % basename)
                elif namemat == "right":
                    fw("rightUrl=\"%s\" " % basename)
                elif namemat == "top":
                    fw("topUrl=\"%s\" " % basename)

        fw("/>\n")

##########################################################
# export routine
##########################################################
    def export_main():
        world = scene.world

        # tag un-exported IDs
        bpy.data.meshes.tag(False)
        bpy.data.materials.tag(False)
        bpy.data.images.tag(False)

        print("Info: starting X3D export to %r..." % file.name)
        ident = ""
        ident = writeHeader(ident)

        writeNavigationInfo(ident, scene)
        writeBackground(ident, world)
        writeFog(ident, world)

        ident = "\t\t"

        if use_selection:
            objects = (o for o in scene.objects if o.is_visible(scene) and o.select)
        else:
            objects = (o for o in scene.objects if o.is_visible(scene))

        for ob_main in objects:

            free, derived = create_derived_objects(scene, ob_main)

            if derived is None:
                continue

            for ob, ob_mat in derived:
                objType = ob.type
                objName = ob.name
                ob_mat = global_matrix * ob_mat

                if objType == 'CAMERA':
                    writeViewpoint(ident, ob, ob_mat, scene)
                elif objType in ('MESH', 'CURVE', 'SURF', 'FONT'):
                    if (objType != 'MESH') or (use_apply_modifiers and ob.is_modified(scene, 'PREVIEW')):
                        try:
                            me = ob.to_mesh(scene, use_apply_modifiers, 'PREVIEW')
                        except:
                            me = None
                    else:
                        me = ob.data

                    if me is not None:
                        writeIndexedFaceSet(ident, ob, me, ob_mat, world)

                        # free mesh created with create_mesh()
                        if me != ob.data:
                            bpy.data.meshes.remove(me)

                elif objType == 'LAMP':
                    data = ob.data
                    datatype = data.type
                    if datatype == 'POINT':
                        writePointLight(ident, ob, ob_mat, data, world)
                    elif datatype == 'SPOT':
                        writeSpotLight(ident, ob, ob_mat, data, world)
                    elif datatype == 'SUN':
                        writeDirectionalLight(ident, ob, ob_mat, data, world)
                    else:
                        writeDirectionalLight(ident, ob, ob_mat, data, world)
                else:
                    #print "Info: Ignoring [%s], object type [%s] not handle yet" % (object.name,object.getType)
                    pass

            if free:
                free_derived_objects(ob_main)

        ident = writeFooter(ident)

    export_main()
    file.close()
    print("Info: finished X3D export to %r" % file.name)


##########################################################
# Callbacks, needed before Main
##########################################################


def save(operator, context, filepath="",
         use_selection=True,
         use_apply_modifiers=False,
         use_triangulate=False,
         use_normals=False,
         use_compress=False,
         global_matrix=None,
         ):

    if use_compress:
        if not filepath.lower().endswith('.x3dz'):
            filepath = '.'.join(filepath.split('.')[:-1]) + '.x3dz'
    else:
        if not filepath.lower().endswith('.x3d'):
            filepath = '.'.join(filepath.split('.')[:-1]) + '.x3d'

    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')

    file = None
    if filepath.lower().endswith('.x3dz'):
        try:
            import gzip
            file = gzip.open(filepath, "w")
        except:
            print("failed to import compression modules, exporting uncompressed")
            filepath = filepath[:-1]  # remove trailing z

    if file is None:
        file = open(filepath, "w")

    if global_matrix is None:
        global_matrix = mathutils.Matrix()

    export(file,
           global_matrix,
           context.scene,
           use_apply_modifiers=use_apply_modifiers,
           use_selection=use_selection,
           use_triangulate=use_triangulate,
           use_normals=use_normals,
           )

    return {'FINISHED'}
