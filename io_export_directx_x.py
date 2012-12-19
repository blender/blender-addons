#  ***** GPL LICENSE BLOCK *****
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#  All rights reserved.
#  ***** GPL LICENSE BLOCK *****

bl_info = {
    "name": "DirectX Model Format (.x)",
    "author": "Chris Foster (Kira Vakaan)",
    "version": (2, 1, 3),
    "blender": (2, 63, 0),
    "location": "File > Export > DirectX (.x)",
    "description": "Export DirectX Model Format (.x)",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"\
        "Scripts/Import-Export/DirectX_Exporter",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=22795",
    "category": "Import-Export"}

import os
from math import radians

import bpy
from mathutils import *

#Container for the exporter settings
class DirectXExporterSettings:
    def __init__(self,
                 context,
                 FilePath,
                 CoordinateSystem=1,
                 RotateX=True,
                 FlipNormals=False,
                 ApplyModifiers=False,
                 IncludeFrameRate=False,
                 ExportTextures=True,
                 ExportArmatures=False,
                 ExportAnimation=0,
                 ExportMode=1,
                 Verbose=False):
        self.context = context
        self.FilePath = FilePath
        self.CoordinateSystem = int(CoordinateSystem)
        self.RotateX = RotateX
        self.FlipNormals = FlipNormals
        self.ApplyModifiers = ApplyModifiers
        self.IncludeFrameRate = IncludeFrameRate
        self.ExportTextures = ExportTextures
        self.ExportArmatures = ExportArmatures
        self.ExportAnimation = int(ExportAnimation)
        self.ExportMode = int(ExportMode)
        self.Verbose = Verbose


def LegalName(Name):
    
    def ReplaceSet(String, OldSet, NewChar):
        for OldChar in OldSet:
            String = String.replace(OldChar, NewChar)
        return String
    
    import string
    
    NewName = ReplaceSet(Name, string.punctuation + " ", "_")
    if NewName[0].isdigit() or NewName in ["ARRAY",
                                           "DWORD",
                                           "UCHAR",
                                           "BINARY",
                                           "FLOAT",
                                           "ULONGLONG",
                                           "BINARY_RESOURCE",
                                           "SDWORD",
                                           "UNICODE",
                                           "CHAR",
                                           "STRING",
                                           "WORD",
                                           "CSTRING",
                                           "SWORD",
                                           "DOUBLE",
                                           "TEMPLATE"]:
        NewName = "_" + NewName
    return NewName


def ExportDirectX(Config):
    print("----------\nExporting to {}".format(Config.FilePath))
    if Config.Verbose:
        print("Opening File...")
    Config.File = open(Config.FilePath, "w")
    if Config.Verbose:
        print("Done")

    if Config.Verbose:
        print("Generating Object list for export... (Root parents only)")
    if Config.ExportMode == 1:
        Config.ExportList = [Object for Object in Config.context.scene.objects
                             if Object.type in {'ARMATURE', 'EMPTY', 'MESH'}
                             and Object.parent is None]
    else:
        ExportList = [Object for Object in Config.context.selected_objects
                      if Object.type in {'ARMATURE', 'EMPTY', 'MESH'}]
        Config.ExportList = [Object for Object in ExportList
                             if Object.parent not in ExportList]
    if Config.Verbose:
        print("  List: {}\nDone".format(Config.ExportList))

    if Config.Verbose:
        print("Setting up...")
    Config.SystemMatrix = Matrix()
    if Config.RotateX:
        Config.SystemMatrix *= Matrix.Rotation(radians(-90), 4, "X")
    if Config.CoordinateSystem == 1:
        Config.SystemMatrix *= Matrix.Scale(-1, 4, Vector((0, 1, 0)))

    if Config.ExportAnimation:
        CurrentFrame = bpy.context.scene.frame_current
        bpy.context.scene.frame_current = bpy.context.scene.frame_current
    if Config.Verbose:
        print("Done")

    if Config.Verbose:
        print("Writing Header...")
    WriteHeader(Config)
    if Config.Verbose:
        print("Done")

    Config.Whitespace = 0
    if Config.Verbose:
        print("Writing Root Frame...")
    WriteRootFrame(Config)
    if Config.Verbose:
        print("Done")
    
    Config.ObjectList = []
    if Config.Verbose:
        print("Writing Objects...")
    WriteObjects(Config, Config.ExportList)
    if Config.Verbose:
        print("Done")
    
    Config.Whitespace -= 1
    Config.File.write("{}}} //End of Root Frame\n".format("  " * Config.Whitespace))
    
    if Config.Verbose:
        print("Objects Exported: {}".format(Config.ExportList))

    if Config.ExportAnimation:
        if Config.IncludeFrameRate:
            if Config.Verbose:
                print("Writing Frame Rate...")
            Config.File.write("{}AnimTicksPerSecond {{\n".format("  " * Config.Whitespace))
            Config.Whitespace += 1
            Config.File.write("{}{};\n".format("  " * Config.Whitespace, int(bpy.context.scene.render.fps / bpy.context.scene.render.fps_base)))
            Config.Whitespace -= 1
            Config.File.write("{}}}\n".format("  " * Config.Whitespace))
            if Config.Verbose:
                print("Done")
        if Config.Verbose:
            print("Writing Animation...")
        if Config.ExportAnimation==1:
            WriteKeyedAnimationSet(Config)
        else:
            WriteFullAnimationSet(Config)
        bpy.context.scene.frame_current = CurrentFrame
        if Config.Verbose:
            print("Done")

    CloseFile(Config)
    print("Finished")


def GetObjectChildren(Parent):
    return [Object for Object in Parent.children
            if Object.type in {'ARMATURE', 'EMPTY', 'MESH'}]

#Returns the vertex count of Mesh, counting each vertex for every face.
def GetMeshVertexCount(Mesh):
    VertexCount = 0
    for Polygon in Mesh.polygons:
        VertexCount += len(Polygon.vertices)
    return VertexCount

#Returns the file path of first image texture from Material.
def GetMaterialTextureFileName(Material):
    if Material:
        #Create a list of Textures that have type "IMAGE"
        ImageTextures = [Material.texture_slots[TextureSlot].texture for TextureSlot in Material.texture_slots.keys() if Material.texture_slots[TextureSlot].texture.type == "IMAGE"]
        #Refine a new list with only image textures that have a file source
        ImageFiles = [bpy.path.basename(Texture.image.filepath) for Texture in ImageTextures if getattr(Texture.image, "source", "") == "FILE"]
        if ImageFiles:
            return ImageFiles[0]
    return None


def WriteHeader(Config):
    Config.File.write("xof 0303txt 0032\n\n")
    
    if Config.IncludeFrameRate:
        Config.File.write("template AnimTicksPerSecond {\n\
  <9E415A43-7BA6-4a73-8743-B73D47E88476>\n\
  DWORD AnimTicksPerSecond;\n\
}\n\n")

    if Config.ExportArmatures:
        Config.File.write("template XSkinMeshHeader {\n\
  <3cf169ce-ff7c-44ab-93c0-f78f62d172e2>\n\
  WORD nMaxSkinWeightsPerVertex;\n\
  WORD nMaxSkinWeightsPerFace;\n\
  WORD nBones;\n\
}\n\n\
template SkinWeights {\n\
  <6f0d123b-bad2-4167-a0d0-80224f25fabb>\n\
  STRING transformNodeName;\n\
  DWORD nWeights;\n\
  array DWORD vertexIndices[nWeights];\n\
  array float weights[nWeights];\n\
  Matrix4x4 matrixOffset;\n\
}\n\n")

def WriteRootFrame(Config):
    Config.File.write("{}Frame Root {{\n".format("  " * Config.Whitespace))
    Config.Whitespace += 1
    
    Config.File.write("{}FrameTransformMatrix {{\n".format("  " * Config.Whitespace))
    Config.Whitespace += 1
    Config.File.write("{}{:9f},{:9f},{:9f},{:9f},\n".format("  " * Config.Whitespace, Config.SystemMatrix[0][0], Config.SystemMatrix[1][0], Config.SystemMatrix[2][0], Config.SystemMatrix[3][0]))
    Config.File.write("{}{:9f},{:9f},{:9f},{:9f},\n".format("  " * Config.Whitespace, Config.SystemMatrix[0][1], Config.SystemMatrix[1][1], Config.SystemMatrix[2][1], Config.SystemMatrix[3][1]))
    Config.File.write("{}{:9f},{:9f},{:9f},{:9f},\n".format("  " * Config.Whitespace, Config.SystemMatrix[0][2], Config.SystemMatrix[1][2], Config.SystemMatrix[2][2], Config.SystemMatrix[3][2]))
    Config.File.write("{}{:9f},{:9f},{:9f},{:9f};;\n".format("  " * Config.Whitespace, Config.SystemMatrix[0][3], Config.SystemMatrix[1][3], Config.SystemMatrix[2][3], Config.SystemMatrix[3][3]))
    Config.Whitespace -= 1
    Config.File.write("{}}}\n".format("  " * Config.Whitespace))

def WriteObjects(Config, ObjectList):
    Config.ObjectList += ObjectList

    for Object in ObjectList:
        if Config.Verbose:
            print("  Writing Object: {}...".format(Object.name))
        Config.File.write("{}Frame {} {{\n".format("  " * Config.Whitespace, LegalName(Object.name)))

        Config.Whitespace += 1
        if Config.Verbose:
            print("    Writing Local Matrix...")
        WriteLocalMatrix(Config, Object)
        if Config.Verbose:
            print("    Done")

        if Config.ExportArmatures and Object.type == "ARMATURE":
            Armature = Object.data
            ParentList = [Bone for Bone in Armature.bones if Bone.parent is None]
            if Config.Verbose:
                print("    Writing Armature Bones...")
            WriteArmatureBones(Config, Object, ParentList)
            if Config.Verbose:
                print("    Done")
        
        ChildList = GetObjectChildren(Object)
        if Config.ExportMode == 2: #Selected Objects Only
            ChildList = [Child for Child in ChildList
                         if Child in Config.context.selected_objects]
        if Config.Verbose:
            print("    Writing Children...")
        WriteObjects(Config, ChildList)
        if Config.Verbose:
            print("    Done Writing Children")

        if Object.type == "MESH":
            if Config.Verbose:
                print("    Generating Mesh...")
            if Config.ApplyModifiers:
                if Config.ExportArmatures:
                    #Create a copy of the object and remove all armature modifiers so an unshaped
                    #mesh can be created from it.
                    Object2 = Object.copy()
                    for Modifier in [Modifier for Modifier in Object2.modifiers if Modifier.type == "ARMATURE"]:
                        Object2.modifiers.remove(Modifier)
                    Mesh = Object2.to_mesh(bpy.context.scene, True, "PREVIEW")
                else:
                    Mesh = Object.to_mesh(bpy.context.scene, True, "PREVIEW")
            else:
                Mesh = Object.to_mesh(bpy.context.scene, False, "PREVIEW")
            if Config.Verbose:
                print("    Done")
                print("    Writing Mesh...")
            WriteMesh(Config, Object, Mesh)
            if Config.Verbose:
                print("    Done")
            if Config.ApplyModifiers and Config.ExportArmatures:
                bpy.data.objects.remove(Object2)
            bpy.data.meshes.remove(Mesh)

        Config.Whitespace -= 1
        Config.File.write("{}}} //End of {}\n".format("  " * Config.Whitespace, LegalName(Object.name)))
        if Config.Verbose:
            print("  Done Writing Object: {}".format(Object.name))


def WriteLocalMatrix(Config, Object):
    LocalMatrix = Object.matrix_local

    Config.File.write("{}FrameTransformMatrix {{\n".format("  " * Config.Whitespace))
    Config.Whitespace += 1
    Config.File.write("{}{:9f},{:9f},{:9f},{:9f},\n".format("  " * Config.Whitespace, LocalMatrix[0][0], LocalMatrix[1][0], LocalMatrix[2][0], LocalMatrix[3][0]))
    Config.File.write("{}{:9f},{:9f},{:9f},{:9f},\n".format("  " * Config.Whitespace, LocalMatrix[0][1], LocalMatrix[1][1], LocalMatrix[2][1], LocalMatrix[3][1]))
    Config.File.write("{}{:9f},{:9f},{:9f},{:9f},\n".format("  " * Config.Whitespace, LocalMatrix[0][2], LocalMatrix[1][2], LocalMatrix[2][2], LocalMatrix[3][2]))
    Config.File.write("{}{:9f},{:9f},{:9f},{:9f};;\n".format("  " * Config.Whitespace, LocalMatrix[0][3], LocalMatrix[1][3], LocalMatrix[2][3], LocalMatrix[3][3]))
    Config.Whitespace -= 1
    Config.File.write("{}}}\n".format("  " * Config.Whitespace))


def WriteArmatureBones(Config, Object, ChildList):
    PoseBones = Object.pose.bones
    for Bone in ChildList:
        if Config.Verbose:
            print("      Writing Bone: {}...".format(Bone.name))
        Config.File.write("{}Frame {} {{\n".format("  " * Config.Whitespace, LegalName(Object.name) + "_" + LegalName(Bone.name)))
        Config.Whitespace += 1

        PoseBone = PoseBones[Bone.name]

        if Bone.parent:
            BoneMatrix = PoseBone.parent.matrix.inverted()
        else:
            BoneMatrix = Matrix()

        BoneMatrix *= PoseBone.matrix
        
        Config.File.write("{}FrameTransformMatrix {{\n".format("  " * Config.Whitespace))
        Config.Whitespace += 1
        Config.File.write("{}{:9f},{:9f},{:9f},{:9f},\n".format("  " * Config.Whitespace, BoneMatrix[0][0], BoneMatrix[1][0], BoneMatrix[2][0], BoneMatrix[3][0]))
        Config.File.write("{}{:9f},{:9f},{:9f},{:9f},\n".format("  " * Config.Whitespace, BoneMatrix[0][1], BoneMatrix[1][1], BoneMatrix[2][1], BoneMatrix[3][1]))
        Config.File.write("{}{:9f},{:9f},{:9f},{:9f},\n".format("  " * Config.Whitespace, BoneMatrix[0][2], BoneMatrix[1][2], BoneMatrix[2][2], BoneMatrix[3][2]))
        Config.File.write("{}{:9f},{:9f},{:9f},{:9f};;\n".format("  " * Config.Whitespace, BoneMatrix[0][3], BoneMatrix[1][3], BoneMatrix[2][3], BoneMatrix[3][3]))
        Config.Whitespace -= 1
        Config.File.write("{}}}\n".format("  " * Config.Whitespace))

        if Config.Verbose:
            print("      Done")
        WriteArmatureBones(Config, Object, Bone.children)
        Config.Whitespace -= 1

        Config.File.write("{}}} //End of {}\n".format("  " * Config.Whitespace, LegalName(Object.name) + "_" + LegalName(Bone.name)))


def WriteMesh(Config, Object, Mesh):
    Config.File.write("{}Mesh {{ //{} Mesh\n".format("  " * Config.Whitespace, LegalName(Mesh.name)))
    Config.Whitespace += 1

    if Config.Verbose:
        print("      Writing Mesh Vertices...")
    WriteMeshVertices(Config, Mesh)
    if Config.Verbose:
        print("      Done\n      Writing Mesh Normals...")
    WriteMeshNormals(Config, Mesh)
    if Config.Verbose:
        print("      Done\n      Writing Mesh Materials...")
    WriteMeshMaterials(Config, Mesh)
    if Config.Verbose:
        print("      Done")
    if Mesh.uv_textures:
        if Config.Verbose:
            print("      Writing Mesh UV Coordinates...")
        WriteMeshUVCoordinates(Config, Mesh)
        if Config.Verbose:
            print("      Done")
    if Config.ExportArmatures:
        if Config.Verbose:
            print("      Writing Mesh Skin Weights...")
        WriteMeshSkinWeights(Config, Object, Mesh)
        if Config.Verbose:
            print("      Done")

    Config.Whitespace -= 1
    Config.File.write("{}}} //End of {} Mesh\n".format("  " * Config.Whitespace, LegalName(Mesh.name)))


def WriteMeshVertices(Config, Mesh):
    Index = 0
    VertexCount = GetMeshVertexCount(Mesh)
    Config.File.write("{}{};\n".format("  " * Config.Whitespace, VertexCount))

    for Polygon in Mesh.polygons:
        Vertices = list(Polygon.vertices)

        if Config.CoordinateSystem == 1:
            Vertices = Vertices[::-1]

        for Vertex in [Mesh.vertices[Vertex] for Vertex in Vertices]:
            Position = Vertex.co
            Config.File.write("{}{:9f};{:9f};{:9f};".format("  " * Config.Whitespace, Position[0], Position[1], Position[2]))
            Index += 1
            if Index == VertexCount:
                Config.File.write(";\n")
            else:
                Config.File.write(",\n")

    Index = 0
    Config.File.write("{}{};\n".format("  " * Config.Whitespace, len(Mesh.polygons)))

    for Polygon in Mesh.polygons:
        Config.File.write("{}{};".format("  " * Config.Whitespace, len(Polygon.vertices)))
        for Vertex in Polygon.vertices:
            Config.File.write("{};".format(Index))
            Index += 1
        if Index == VertexCount:
            Config.File.write(";\n")
        else:
            Config.File.write(",\n")


def WriteMeshNormals(Config, Mesh):
    Config.File.write("{}MeshNormals {{ //{} Normals\n".format("  " * Config.Whitespace, LegalName(Mesh.name)))
    Config.Whitespace += 1

    Index = 0
    VertexCount = GetMeshVertexCount(Mesh)
    Config.File.write("{}{};\n".format("  " * Config.Whitespace, VertexCount))

    for Polygon in Mesh.polygons:
        Vertices = list(Polygon.vertices)

        if Config.CoordinateSystem == 1:
            Vertices = Vertices[::-1]
        for Vertex in [Mesh.vertices[Vertex] for Vertex in Vertices]:
            if Polygon.use_smooth:
                Normal = Vertex.normal
            else:
                Normal = Polygon.normal
            if Config.FlipNormals:
                Normal = -Normal
            Config.File.write("{}{:9f};{:9f};{:9f};".format("  " * Config.Whitespace, Normal[0], Normal[1], Normal[2]))
            Index += 1
            if Index == VertexCount:
                Config.File.write(";\n")
            else:
                Config.File.write(",\n")

    Index = 0
    Config.File.write("{}{};\n".format("  " * Config.Whitespace, len(Mesh.polygons)))

    for Polygon in Mesh.polygons:
        Config.File.write("{}{};".format("  " * Config.Whitespace, len(Polygon.vertices)))
        for Vertex in Polygon.vertices:
            Config.File.write("{};".format(Index))
            Index += 1
        if Index == VertexCount:
            Config.File.write(";\n")
        else:
            Config.File.write(",\n")
    Config.Whitespace -= 1
    Config.File.write("{}}} //End of {} Normals\n".format("  " * Config.Whitespace, LegalName(Mesh.name)))


def WriteMeshMaterials(Config, Mesh):
    Config.File.write("{}MeshMaterialList {{ //{} Material List\n".format("  " * Config.Whitespace, LegalName(Mesh.name)))
    Config.Whitespace += 1

    Materials = Mesh.materials
    if Materials.keys():
        MaterialIndexes = {}
        for Polygon in Mesh.polygons:
            if Materials[Polygon.material_index] not in MaterialIndexes:
                MaterialIndexes[Materials[Polygon.material_index]] = len(MaterialIndexes)

        PolygonCount = len(Mesh.polygons)
        Index = 0
        Config.File.write("{}{};\n{}{};\n".format("  " * Config.Whitespace, len(MaterialIndexes), "  " * Config.Whitespace, PolygonCount))
        for Polygon in Mesh.polygons:
            Config.File.write("{}{}".format("  " * Config.Whitespace, MaterialIndexes[Materials[Polygon.material_index]]))
            Index += 1
            if Index == PolygonCount:
                Config.File.write(";;\n")
            else:
                Config.File.write(",\n")

        Materials = [Item[::-1] for Item in MaterialIndexes.items()]
        Materials.sort()
        for Material in Materials:
            WriteMaterial(Config, Material[1])
    else:
        Config.File.write("{}1;\n{}1;\n{}0;;\n".format("  " * Config.Whitespace, "  " * Config.Whitespace, "  " * Config.Whitespace))
        WriteMaterial(Config)

    Config.Whitespace -= 1
    Config.File.write("{}}} //End of {} Material List\n".format("  " * Config.Whitespace, LegalName(Mesh.name)))


def WriteMaterial(Config, Material=None):
    if Material:
        Config.File.write("{}Material {} {{\n".format("  " * Config.Whitespace, LegalName(Material.name)))
        Config.Whitespace += 1

        Diffuse = list(Vector(Material.diffuse_color) * Material.diffuse_intensity)
        Diffuse.append(Material.alpha)
        Specularity = 1000 * (Material.specular_hardness - 1.0) / (511.0 - 1.0) # Map Blender's range of 1 - 511 to 0 - 1000
        Specular = list(Vector(Material.specular_color) * Material.specular_intensity)

        Config.File.write("{}{:9f};{:9f};{:9f};{:9f};;\n".format("  " * Config.Whitespace, Diffuse[0], Diffuse[1], Diffuse[2], Diffuse[3]))
        Config.File.write("{} {:9f};\n".format("  " * Config.Whitespace, Specularity))
        Config.File.write("{}{:9f};{:9f};{:9f};;\n".format("  " * Config.Whitespace, Specular[0], Specular[1], Specular[2]))
    else:
        Config.File.write("{}Material Default_Material {{\n".format("  " * Config.Whitespace))
        Config.Whitespace += 1
        Config.File.write("{} 0.800000; 0.800000; 0.800000; 0.800000;;\n".format("  " * Config.Whitespace))
        Config.File.write("{} 96.078431;\n".format("  " * Config.Whitespace)) # 1000 * (50 - 1) / (511 - 1)
        Config.File.write("{} 0.500000; 0.500000; 0.500000;;\n".format("  " * Config.Whitespace))
    Config.File.write("{} 0.000000; 0.000000; 0.000000;;\n".format("  " * Config.Whitespace))
    if Config.ExportTextures:
        TextureFileName = GetMaterialTextureFileName(Material)
        if TextureFileName:
            Config.File.write("{}TextureFilename {{\"{}\";}}\n".format("  " * Config.Whitespace, TextureFileName))
    Config.Whitespace -= 1
    Config.File.write("{}}}\n".format("  " * Config.Whitespace))


def WriteMeshUVCoordinates(Config, Mesh):
    Config.File.write("{}MeshTextureCoords {{ //{} UV Coordinates\n".format("  " * Config.Whitespace, LegalName(Mesh.name)))
    Config.Whitespace += 1

    UVCoordinates = Mesh.uv_layers.active.data

    Index = 0
    VertexCount = GetMeshVertexCount(Mesh)
    Config.File.write("{}{};\n".format("  " * Config.Whitespace, VertexCount))

    for Polygon in Mesh.polygons:
        Vertices = []
        for Vertex in [UVCoordinates[Vertex] for Vertex in Polygon.loop_indices]:
            Vertices.append(tuple(Vertex.uv))
        if Config.CoordinateSystem == 1:
            Vertices = Vertices[::-1]
        for Vertex in Vertices:
            Config.File.write("{}{:9f};{:9f};".format("  " * Config.Whitespace, Vertex[0], 1 - Vertex[1]))
            Index += 1
            if Index == VertexCount:
                Config.File.write(";\n")
            else:
                Config.File.write(",\n")
    
    Config.Whitespace -= 1
    Config.File.write("{}}} //End of {} UV Coordinates\n".format("  " * Config.Whitespace, LegalName(Mesh.name)))


def WriteMeshSkinWeights(Config, Object, Mesh):
    ArmatureList = [Modifier for Modifier in Object.modifiers if Modifier.type == "ARMATURE"]
    if ArmatureList:
        ArmatureObject = ArmatureList[0].object
        ArmatureBones = ArmatureObject.data.bones

        PoseBones = ArmatureObject.pose.bones

        MaxInfluences = 0
        UsedBones = set()
        #Maps bones to a list of vertices they affect
        VertexGroups = {}
        ObjectVertexGroups = {i: Group.name for (i, Group) in enumerate(Object.vertex_groups)}
        for Vertex in Mesh.vertices:
            #BoneInfluences contains the bones of the armature that affect the current vertex
            BoneInfluences = [PoseBone for Group in Vertex.groups
                              for PoseBone in (PoseBones.get(ObjectVertexGroups.get(Group.group, "")), )
                              if PoseBone is not None
                              ]

            if len(BoneInfluences) > MaxInfluences:
                MaxInfluences = len(BoneInfluences)
            for Bone in BoneInfluences:
                UsedBones.add(Bone)
                if Bone not in VertexGroups:
                    VertexGroups[Bone] = [Vertex]
                else:
                    VertexGroups[Bone].append(Vertex)
        BoneCount = len(UsedBones)

        Config.File.write("{}XSkinMeshHeader {{\n".format("  " * Config.Whitespace))
        Config.Whitespace += 1
        Config.File.write("{}{};\n{}{};\n{}{};\n".format("  " * Config.Whitespace, MaxInfluences, "  " * Config.Whitespace, MaxInfluences * 3, "  " * Config.Whitespace, BoneCount))
        Config.Whitespace -= 1
        Config.File.write("{}}}\n".format("  " * Config.Whitespace))

        for Bone in UsedBones:
            VertexCount = 0
            VertexIndexes = [Vertex.index for Vertex in VertexGroups[Bone]]
            for Polygon in Mesh.polygons:
                for Vertex in Polygon.vertices:
                    if Vertex in VertexIndexes:
                        VertexCount += 1

            Config.File.write("{}SkinWeights {{\n".format("  " * Config.Whitespace))
            Config.Whitespace += 1
            Config.File.write("{}\"{}\";\n{}{};\n".format("  " * Config.Whitespace, LegalName(ArmatureObject.name) + "_" + LegalName(Bone.name), "  " * Config.Whitespace, VertexCount))

            VertexWeights = []
            Index = 0
            WrittenIndexes = 0
            for Polygon in Mesh.polygons:
                PolygonVertices = list(Polygon.vertices)
                if Config.CoordinateSystem == 1:
                    PolygonVertices = PolygonVertices[::-1]
                for Vertex in PolygonVertices:
                    if Vertex in VertexIndexes:
                        Config.File.write("{}{}".format("  " * Config.Whitespace, Index))

                        GroupIndexes = {ObjectVertexGroups.get(Group.group): Index
                                        for Index, Group in enumerate(Mesh.vertices[Vertex].groups)
                                        if ObjectVertexGroups.get(Group.group, "") in PoseBones}

                        WeightTotal = 0.0
                        for Weight in (Group.weight for Group in Mesh.vertices[Vertex].groups if ObjectVertexGroups.get(Group.group, "") in PoseBones):
                            WeightTotal += Weight

                        if WeightTotal:
                            VertexWeights.append(Mesh.vertices[Vertex].groups[GroupIndexes[Bone.name]].weight / WeightTotal)
                        else:
                            VertexWeights.append(0.0)

                        WrittenIndexes += 1
                        if WrittenIndexes == VertexCount:
                            Config.File.write(";\n")
                        else:
                            Config.File.write(",\n")
                    Index += 1

            for Index, Weight in enumerate(VertexWeights):
                Config.File.write("{}{:8f}".format("  " * Config.Whitespace, Weight))
                if Index == (VertexCount - 1):
                    Config.File.write(";\n")
                else:
                    Config.File.write(",\n")
            
            RestBone = ArmatureBones[Bone.name]
            
            #BoneMatrix transforms mesh vertices into the space of the bone.
            #Here are the final transformations in order:
            #  - Object Space to World Space
            #  - World Space to Armature Space
            #  - Armature Space to Bone Space (The bone matrix needs to be rotated 90 degrees to align with Blender's world axes)
            #This way, when BoneMatrix is transformed by the bone's Frame matrix, the vertices will be in their final world position.
            
            BoneMatrix = RestBone.matrix_local.inverted()
            BoneMatrix *= ArmatureObject.matrix_world.inverted()
            BoneMatrix *= Object.matrix_world
            
            Config.File.write("{}{:9f},{:9f},{:9f},{:9f},\n".format("  " * Config.Whitespace, BoneMatrix[0][0], BoneMatrix[1][0], BoneMatrix[2][0], BoneMatrix[3][0]))
            Config.File.write("{}{:9f},{:9f},{:9f},{:9f},\n".format("  " * Config.Whitespace, BoneMatrix[0][1], BoneMatrix[1][1], BoneMatrix[2][1], BoneMatrix[3][1]))
            Config.File.write("{}{:9f},{:9f},{:9f},{:9f},\n".format("  " * Config.Whitespace, BoneMatrix[0][2], BoneMatrix[1][2], BoneMatrix[2][2], BoneMatrix[3][2]))
            Config.File.write("{}{:9f},{:9f},{:9f},{:9f};;\n".format("  " * Config.Whitespace, BoneMatrix[0][3], BoneMatrix[1][3], BoneMatrix[2][3], BoneMatrix[3][3]))
            Config.Whitespace -= 1
            Config.File.write("{}}}  //End of {} Skin Weights\n".format("  " * Config.Whitespace, LegalName(ArmatureObject.name) + "_" + LegalName(Bone.name)))


def WriteKeyedAnimationSet(Config):
    Config.File.write("{}AnimationSet {{\n".format("  " * Config.Whitespace))
    Config.Whitespace += 1
    for Object in [Object for Object in Config.ObjectList if Object.animation_data]:
        if Config.Verbose:
            print("  Writing Animation Data for Object: {}".format(Object.name))
        Action = Object.animation_data.action
        if Action:
            PositionFCurves = [None, None, None]
            RotationFCurves = [None, None, None]
            ScaleFCurves = [None, None, None]
            for FCurve in Action.fcurves:
                if FCurve.data_path == "location":
                    PositionFCurves[FCurve.array_index] = FCurve
                elif FCurve.data_path == "rotation_euler":
                    RotationFCurves[FCurve.array_index] = FCurve
                elif FCurve.data_path == "scale":
                    ScaleFCurves[FCurve.array_index] = FCurve
            if [FCurve for FCurve in PositionFCurves + RotationFCurves + ScaleFCurves if FCurve]:
                Config.File.write("{}Animation {{\n".format("  " * Config.Whitespace))
                Config.Whitespace += 1
                Config.File.write("{}{{{}}}\n".format("  " * Config.Whitespace, LegalName(Object.name)))

                #Position
                if Config.Verbose:
                    print("    Writing Position...")
                AllKeyframes = set()
                for Index, FCurve in enumerate(PositionFCurves):
                    if FCurve:
                        Keyframes = []
                        for Keyframe in FCurve.keyframe_points:
                            if Keyframe.co[0] < bpy.context.scene.frame_start:
                                AllKeyframes.add(bpy.context.scene.frame_start)
                            elif Keyframe.co[0] > bpy.context.scene.frame_end:
                                AllKeyframes.add(bpy.context.scene.frame_end)
                            else:
                                Keyframes.append(Keyframe.co)
                                AllKeyframes.add(int(Keyframe.co[0]))
                        PositionFCurves[Index] = {int(Keyframe): Value for Keyframe, Value in Keyframes}
                Config.File.write("{}AnimationKey {{ //Position\n".format("  " * Config.Whitespace))
                Config.Whitespace += 1
                AllKeyframes = list(AllKeyframes)
                AllKeyframes.sort()
                if len(AllKeyframes):
                    Config.File.write("{}2;\n{}{};\n".format("  " * Config.Whitespace, "  " * Config.Whitespace, len(AllKeyframes)))
                    for Keyframe in AllKeyframes:
                        bpy.context.scene.frame_set(Keyframe)
                        Position = Vector()
                        Position[0] = ((PositionFCurves[0][Keyframe] if Keyframe in PositionFCurves[0] else Object.location[0]) if PositionFCurves[0] else Object.location[0])
                        Position[1] = ((PositionFCurves[1][Keyframe] if Keyframe in PositionFCurves[1] else Object.location[1]) if PositionFCurves[1] else Object.location[1])
                        Position[2] = ((PositionFCurves[2][Keyframe] if Keyframe in PositionFCurves[2] else Object.location[2]) if PositionFCurves[2] else Object.location[2])
                        Config.File.write("{}{}{:9f},{:9f},{:9f};;".format("  " * Config.Whitespace, (str(Keyframe - bpy.context.scene.frame_start) + ";3;").ljust(8), Position[0], Position[1], Position[2]))
                        if Keyframe == AllKeyframes[-1]:
                            Config.File.write(";\n")
                        else:
                            Config.File.write(",\n")
                        
                else:
                    Config.File.write("{}2;\n{}1;\n".format("  " * Config.Whitespace, "  " * Config.Whitespace))
                    bpy.context.scene.frame_set(bpy.context.scene.frame_start)
                    Position = Object.matrix_local.to_translation()
                    Config.File.write("{}{}{:9f},{:9f},{:9f};;;\n".format("  " * Config.Whitespace, ("0;3;").ljust(8), Position[0], Position[1], Position[2]))
                Config.Whitespace -= 1
                Config.File.write("{}}}\n".format("  " * Config.Whitespace))
                if Config.Verbose:
                    print("    Done")

                #Rotation
                if Config.Verbose:
                    print("    Writing Rotation...")
                AllKeyframes = set()
                for Index, FCurve in enumerate(RotationFCurves):
                    if FCurve:
                        Keyframes = []
                        for Keyframe in FCurve.keyframe_points:
                            if Keyframe.co[0] < bpy.context.scene.frame_start:
                                AllKeyframes.add(bpy.context.scene.frame_start)
                            elif Keyframe.co[0] > bpy.context.scene.frame_end:
                                AllKeyframes.add(bpy.context.scene.frame_end)
                            else:
                                Keyframes.append(Keyframe.co)
                                AllKeyframes.add(int(Keyframe.co[0]))
                        RotationFCurves[Index] = {int(Keyframe): Value for Keyframe, Value in Keyframes}
                Config.File.write("{}AnimationKey {{ //Rotation\n".format("  " * Config.Whitespace))
                Config.Whitespace += 1
                AllKeyframes = list(AllKeyframes)
                AllKeyframes.sort()
                if len(AllKeyframes):
                    Config.File.write("{}0;\n{}{};\n".format("  " * Config.Whitespace, "  " * Config.Whitespace, len(AllKeyframes)))
                    for Keyframe in AllKeyframes:
                        bpy.context.scene.frame_set(Keyframe)
                        Rotation = Euler()
                        Rotation[0] = ((RotationFCurves[0][Keyframe] if Keyframe in RotationFCurves[0] else Object.rotation_euler[0]) if RotationFCurves[0] else Object.rotation_euler[0])
                        Rotation[1] = ((RotationFCurves[1][Keyframe] if Keyframe in RotationFCurves[1] else Object.rotation_euler[1]) if RotationFCurves[1] else Object.rotation_euler[1])
                        Rotation[2] = ((RotationFCurves[2][Keyframe] if Keyframe in RotationFCurves[2] else Object.rotation_euler[2]) if RotationFCurves[2] else Object.rotation_euler[2])
                        Rotation = Rotation.to_quaternion()
                        Config.File.write("{}{}{:9f},{:9f},{:9f},{:9f};;".format("  " * Config.Whitespace, (str(Keyframe - bpy.context.scene.frame_start) + ";4;").ljust(8), -Rotation[0], Rotation[1], Rotation[2], Rotation[3]))
                        if Keyframe == AllKeyframes[-1]:
                            Config.File.write(";\n")
                        else:
                            Config.File.write(",\n")
                else:
                    Config.File.write("{}0;\n{}1;\n".format("  " * Config.Whitespace, "  " * Config.Whitespace))
                    bpy.context.scene.frame_set(bpy.context.scene.frame_start)
                    Rotation = Object.rotation_euler.to_quaternion()
                    Config.File.write("{}{}{:9f},{:9f},{:9f},{:9f};;;\n".format("  " * Config.Whitespace, ("0;4;").ljust(8), -Rotation[0], Rotation[1], Rotation[2], Rotation[3]))
                Config.Whitespace -= 1
                Config.File.write("{}}}\n".format("  " * Config.Whitespace))
                if Config.Verbose:
                    print("    Done")

                #Scale
                if Config.Verbose:
                    print("    Writing Scale...")
                AllKeyframes = set()
                for Index, FCurve in enumerate(ScaleFCurves):
                    if FCurve:
                        Keyframes = []
                        for Keyframe in FCurve.keyframe_points:
                            if Keyframe.co[0] < bpy.context.scene.frame_start:
                                AllKeyframes.add(bpy.context.scene.frame_start)
                            elif Keyframe.co[0] > bpy.context.scene.frame_end:
                                AllKeyframes.add(bpy.context.scene.frame_end)
                            else:
                                Keyframes.append(Keyframe.co)
                                AllKeyframes.add(int(Keyframe.co[0]))
                        ScaleFCurves[Index] = {int(Keyframe): Value for Keyframe, Value in Keyframes}
                Config.File.write("{}AnimationKey {{ //Scale\n".format("  " * Config.Whitespace))
                Config.Whitespace += 1
                AllKeyframes = list(AllKeyframes)
                AllKeyframes.sort()
                if len(AllKeyframes):
                    Config.File.write("{}1;\n{}{};\n".format("  " * Config.Whitespace, "  " * Config.Whitespace, len(AllKeyframes)))
                    for Keyframe in AllKeyframes:
                        bpy.context.scene.frame_set(Keyframe)
                        Scale = Vector()
                        Scale[0] = ((ScaleFCurves[0][Keyframe] if Keyframe in ScaleFCurves[0] else Object.scale[0]) if ScaleFCurves[0] else Object.scale[0])
                        Scale[1] = ((ScaleFCurves[1][Keyframe] if Keyframe in ScaleFCurves[1] else Object.scale[1]) if ScaleFCurves[1] else Object.scale[1])
                        Scale[2] = ((ScaleFCurves[2][Keyframe] if Keyframe in ScaleFCurves[2] else Object.scale[2]) if ScaleFCurves[2] else Object.scale[2])
                        Config.File.write("{}{}{:9f},{:9f},{:9f};;".format("  " * Config.Whitespace, (str(Keyframe - bpy.context.scene.frame_start) + ";3;").ljust(8), Scale[0], Scale[1], Scale[2]))
                        if Keyframe == AllKeyframes[-1]:
                            Config.File.write(";\n")
                        else:
                            Config.File.write(",\n")
                else:
                    Config.File.write("{}1;\n{}1;\n".format("  " * Config.Whitespace, "  " * Config.Whitespace))
                    bpy.context.scene.frame_set(bpy.context.scene.frame_start)
                    Scale = Object.matrix_local.to_scale()
                    Config.File.write("{}{}{:9f},{:9f},{:9f};;;\n".format("  " * Config.Whitespace, ("0;3;").ljust(8), Scale[0], Scale[1], Scale[2]))
                Config.Whitespace -= 1
                Config.File.write("{}}}\n".format("  " * Config.Whitespace))
                if Config.Verbose:
                    print("    Done")

                Config.Whitespace -= 1
                Config.File.write("{}}}\n".format("  " * Config.Whitespace))
            else:
                if Config.Verbose:
                    print("    Object has no useable animation data.")

            if Config.ExportArmatures and Object.type == "ARMATURE":
                if Config.Verbose:
                    print("    Writing Armature Bone Animation Data...")
                PoseBones = Object.pose.bones
                for Bone in PoseBones:
                    if Config.Verbose:
                        print("      Writing Bone: {}...".format(Bone.name))
                    PositionFCurves = [None, None, None]
                    RotationFCurves = [None, None, None, None]
                    ScaleFCurves = [None, None, None]
                    for FCurve in Action.fcurves:
                        if FCurve.data_path == "pose.bones[\"{}\"].location".format(Bone.name):
                            PositionFCurves[FCurve.array_index] = FCurve
                        elif FCurve.data_path == "pose.bones[\"{}\"].rotation_quaternion".format(Bone.name):
                            RotationFCurves[FCurve.array_index] = FCurve
                        elif FCurve.data_path == "pose.bones[\"{}\"].scale".format(Bone.name):
                            ScaleFCurves[FCurve.array_index] = FCurve
                    if not [FCurve for FCurve in PositionFCurves + RotationFCurves + ScaleFCurves if FCurve]:
                        if Config.Verbose:
                            print("        Bone has no useable animation data.\n      Done")
                        continue

                    Config.File.write("{}Animation {{\n".format("  " * Config.Whitespace))
                    Config.Whitespace += 1
                    Config.File.write("{}{{{}}}\n".format("  " * Config.Whitespace, LegalName(Object.name) + "_" + LegalName(Bone.name)))

                    #Position
                    if Config.Verbose:
                        print("        Writing Position...")
                    AllKeyframes = set()
                    for Index, FCurve in enumerate(PositionFCurves):
                        if FCurve:
                            Keyframes = []
                            for Keyframe in FCurve.keyframe_points:
                                if Keyframe.co[0] < bpy.context.scene.frame_start:
                                    AllKeyframes.add(bpy.context.scene.frame_start)
                                elif Keyframe.co[0] > bpy.context.scene.frame_end:
                                    AllKeyframes.add(bpy.context.scene.frame_end)
                                else:
                                    Keyframes.append(Keyframe.co)
                                    AllKeyframes.add(int(Keyframe.co[0]))
                            PositionFCurves[Index] = {int(Keyframe): Value for Keyframe, Value in Keyframes}
                    Config.File.write("{}AnimationKey {{ //Position\n".format("  " * Config.Whitespace))
                    Config.Whitespace += 1
                    AllKeyframes = list(AllKeyframes)
                    AllKeyframes.sort()
                    if not len(AllKeyframes):
                        AllKeyframes = [bpy.context.scene.frame_start]
                    Config.File.write("{}2;\n{}{};\n".format("  " * Config.Whitespace, "  " * Config.Whitespace, len(AllKeyframes)))
                    for Keyframe in AllKeyframes:
                        bpy.context.scene.frame_set(Keyframe)
                        
                        if Bone.parent:
                            PoseMatrix = Bone.parent.matrix.inverted()
                        else:
                            PoseMatrix = Matrix()
                        PoseMatrix *= Bone.matrix
                        
                        Position = PoseMatrix.to_translation()
                        Config.File.write("{}{}{:9f},{:9f},{:9f};;".format("  " * Config.Whitespace, (str(Keyframe - bpy.context.scene.frame_start) + ";3;").ljust(8), Position[0], Position[1], Position[2]))
                        if Keyframe == AllKeyframes[-1]:
                            Config.File.write(";\n")
                        else:
                            Config.File.write(",\n")
                    Config.Whitespace -= 1
                    Config.File.write("{}}}\n".format("  " * Config.Whitespace))
                    if Config.Verbose:
                        print("        Done")

                    #Rotation
                    if Config.Verbose:
                        print("        Writing Rotation...")
                    AllKeyframes = set()
                    for Index, FCurve in enumerate(RotationFCurves):
                        if FCurve:
                            Keyframes = []
                            for Keyframe in FCurve.keyframe_points:
                                if Keyframe.co[0] < bpy.context.scene.frame_start:
                                    AllKeyframes.add(bpy.context.scene.frame_start)
                                elif Keyframe.co[0] > bpy.context.scene.frame_end:
                                    AllKeyframes.add(bpy.context.scene.frame_end)
                                else:
                                    Keyframes.append(Keyframe.co)
                                    AllKeyframes.add(int(Keyframe.co[0]))
                            RotationFCurves[Index] = {int(Keyframe): Value for Keyframe, Value in Keyframes}
                    Config.File.write("{}AnimationKey {{ //Rotation\n".format("  " * Config.Whitespace))
                    Config.Whitespace += 1
                    AllKeyframes = list(AllKeyframes)
                    AllKeyframes.sort()
                    if not len(AllKeyframes):
                        AllKeyframes = [bpy.context.scene.frame_start]
                    Config.File.write("{}0;\n{}{};\n".format("  " * Config.Whitespace, "  " * Config.Whitespace, len(AllKeyframes)))
                    for Keyframe in AllKeyframes:
                        bpy.context.scene.frame_set(Keyframe)
                        
                        if Bone.parent:
                            PoseMatrix = Bone.parent.matrix.inverted()
                        else:
                            PoseMatrix = Matrix()
                        PoseMatrix *= Bone.matrix
                        
                        Rotation = PoseMatrix.to_3x3().to_quaternion()
                        Config.File.write("{}{}{:9f},{:9f},{:9f},{:9f};;".format("  " * Config.Whitespace, (str(Keyframe - bpy.context.scene.frame_start) + ";4;").ljust(8), -Rotation[0], Rotation[1], Rotation[2], Rotation[3]))
                        if Keyframe == AllKeyframes[-1]:
                            Config.File.write(";\n")
                        else:
                            Config.File.write(",\n")
                    Config.Whitespace -= 1
                    Config.File.write("{}}}\n".format("  " * Config.Whitespace))
                    if Config.Verbose:
                        print("        Done")

                    #Scale
                    if Config.Verbose:
                        print("        Writing Scale...")
                    AllKeyframes = set()
                    for Index, FCurve in enumerate(ScaleFCurves):
                        if FCurve:
                            Keyframes = []
                            for Keyframe in FCurve.keyframe_points:
                                if Keyframe.co[0] < bpy.context.scene.frame_start:
                                    AllKeyframes.add(bpy.context.scene.frame_start)
                                elif Keyframe.co[0] > bpy.context.scene.frame_end:
                                    AllKeyframes.add(bpy.context.scene.frame_end)
                                else:
                                    Keyframes.append(Keyframe.co)
                                    AllKeyframes.add(int(Keyframe.co[0]))
                            ScaleFCurves[Index] = {int(Keyframe): Value for Keyframe, Value in Keyframes}
                    Config.File.write("{}AnimationKey {{ //Scale\n".format("  " * Config.Whitespace))
                    Config.Whitespace += 1
                    AllKeyframes = list(AllKeyframes)
                    AllKeyframes.sort()
                    if not len(AllKeyframes):
                        AllKeyframes = [bpy.context.scene.frame_start]
                    Config.File.write("{}1;\n{}{};\n".format("  " * Config.Whitespace, "  " * Config.Whitespace, len(AllKeyframes)))
                    for Keyframe in AllKeyframes:
                        bpy.context.scene.frame_set(Keyframe)
                        
                        if Bone.parent:
                            PoseMatrix = Bone.parent.matrix.inverted()
                        else:
                            PoseMatrix = Matrix()
                        PoseMatrix *= Bone.matrix
                        
                        Scale = PoseMatrix.to_scale()
                        Config.File.write("{}{}{:9f},{:9f},{:9f};;".format("  " * Config.Whitespace, (str(Keyframe - bpy.context.scene.frame_start) + ";3;").ljust(8), Scale[0], Scale[1], Scale[2]))
                        if Keyframe == AllKeyframes[-1]:
                            Config.File.write(";\n")
                        else:
                            Config.File.write(",\n")
                    Config.Whitespace -= 1
                    Config.File.write("{}}}\n".format("  " * Config.Whitespace))
                    if Config.Verbose:
                        print("        Done")

                    Config.Whitespace -= 1
                    Config.File.write("{}}}\n".format("  " * Config.Whitespace))
                    if Config.Verbose:
                        print("      Done") #Done with Armature Bone
                if Config.Verbose:
                    print("    Done") #Done with Armature Bone data
        if Config.Verbose:
            print("  Done") #Done with Object

    Config.Whitespace -= 1
    Config.File.write("{}}} //End of AnimationSet\n".format("  " * Config.Whitespace))

def WriteFullAnimationSet(Config):
    Config.File.write("{}AnimationSet {{\n".format("  " * Config.Whitespace))
    Config.Whitespace += 1
    
    KeyframeCount = bpy.context.scene.frame_end - bpy.context.scene.frame_start + 1
    
    for Object in Config.ObjectList:
        if Config.Verbose:
            print("  Writing Animation Data for Object: {}".format(Object.name))
        
        Config.File.write("{}Animation {{\n".format("  " * Config.Whitespace))
        Config.Whitespace += 1
        Config.File.write("{}{{{}}}\n".format("  " * Config.Whitespace, LegalName(Object.name)))
        
        #Position
        if Config.Verbose:
            print("    Writing Position...")
        Config.File.write("{}AnimationKey {{ //Position\n".format("  " * Config.Whitespace))
        Config.Whitespace += 1
        Config.File.write("{}2;\n{}{};\n".format("  " * Config.Whitespace, "  " * Config.Whitespace, KeyframeCount))
        for Frame in range(0, KeyframeCount):
            bpy.context.scene.frame_set(Frame + bpy.context.scene.frame_start)
            Position = Object.matrix_local.to_translation()
            Config.File.write("{}{}{:9f},{:9f},{:9f};;".format("  " * Config.Whitespace, (str(Frame) + ";3;").ljust(8), Position[0], Position[1], Position[2]))
            if Frame == KeyframeCount-1:
                Config.File.write(";\n")
            else:
                Config.File.write(",\n")
        Config.Whitespace -= 1
        Config.File.write("{}}}\n".format("  " * Config.Whitespace))
        if Config.Verbose:
            print("    Done")
        
        #Rotation
        if Config.Verbose:
            print("    Writing Rotation...")
        Config.File.write("{}AnimationKey {{ //Rotation\n".format("  " * Config.Whitespace))
        Config.Whitespace += 1
        Config.File.write("{}0;\n{}{};\n".format("  " * Config.Whitespace, "  " * Config.Whitespace, KeyframeCount))
        for Frame in range(0, KeyframeCount):
            bpy.context.scene.frame_set(Frame + bpy.context.scene.frame_start)
            Rotation = Object.rotation_euler.to_quaternion()
            Config.File.write("{}{}{:9f},{:9f},{:9f},{:9f};;".format("  " * Config.Whitespace, (str(Frame) + ";4;").ljust(8), -Rotation[0], Rotation[1], Rotation[2], Rotation[3]))
            if Frame == KeyframeCount-1:
                Config.File.write(";\n")
            else:
                Config.File.write(",\n")
        Config.Whitespace -= 1
        Config.File.write("{}}}\n".format("  " * Config.Whitespace))
        if Config.Verbose:
            print("    Done")
        
        #Scale
        if Config.Verbose:
            print("    Writing Scale...")
        Config.File.write("{}AnimationKey {{ //Scale\n".format("  " * Config.Whitespace))
        Config.Whitespace += 1
        Config.File.write("{}1;\n{}{};\n".format("  " * Config.Whitespace, "  " * Config.Whitespace, KeyframeCount))
        for Frame in range(0, KeyframeCount):
            bpy.context.scene.frame_set(Frame + bpy.context.scene.frame_start)
            Scale = Object.matrix_local.to_scale()
            Config.File.write("{}{}{:9f},{:9f},{:9f};;".format("  " * Config.Whitespace, (str(Frame) + ";3;").ljust(8), Scale[0], Scale[1], Scale[2]))
            if Frame == KeyframeCount-1:
                Config.File.write(";\n")
            else:
                Config.File.write(",\n")
        Config.Whitespace -= 1
        Config.File.write("{}}}\n".format("  " * Config.Whitespace))
        if Config.Verbose:
            print("    Done")
        
        Config.Whitespace -= 1
        Config.File.write("{}}}\n".format("  " * Config.Whitespace))
        
        if Config.ExportArmatures and Object.type == "ARMATURE":
            if Config.Verbose:
                print("    Writing Armature Bone Animation Data...")
            PoseBones = Object.pose.bones
            Bones = Object.data.bones
            for Bone in PoseBones:
                if Config.Verbose:
                    print("      Writing Bone: {}...".format(Bone.name))
                
                Config.File.write("{}Animation {{\n".format("  " * Config.Whitespace))
                Config.Whitespace += 1
                Config.File.write("{}{{{}}}\n".format("  " * Config.Whitespace, LegalName(Object.name) + "_" + LegalName(Bone.name)))
                
                #Position
                if Config.Verbose:
                    print("        Writing Position...")
                Config.File.write("{}AnimationKey {{ //Position\n".format("  " * Config.Whitespace))
                Config.Whitespace += 1
                Config.File.write("{}2;\n{}{};\n".format("  " * Config.Whitespace, "  " * Config.Whitespace, KeyframeCount))
                for Frame in range(0, KeyframeCount):
                    bpy.context.scene.frame_set(Frame + bpy.context.scene.frame_start)
                    
                    if Bone.parent:
                        PoseMatrix = Bone.parent.matrix.inverted()
                    else:
                        PoseMatrix = Matrix()
                    PoseMatrix *= Bone.matrix
                    
                    Position = PoseMatrix.to_translation()
                    Config.File.write("{}{}{:9f},{:9f},{:9f};;".format("  " * Config.Whitespace, (str(Frame) + ";3;").ljust(8), Position[0], Position[1], Position[2]))
                    if Frame == KeyframeCount-1:
                        Config.File.write(";\n")
                    else:
                        Config.File.write(",\n")
                Config.Whitespace -= 1
                Config.File.write("{}}}\n".format("  " * Config.Whitespace))
                if Config.Verbose:
                    print("        Done")
                
                #Rotation
                if Config.Verbose:
                    print("        Writing Rotation...")
                Config.File.write("{}AnimationKey {{ //Rotation\n".format("  " * Config.Whitespace))
                Config.Whitespace += 1
                Config.File.write("{}0;\n{}{};\n".format("  " * Config.Whitespace, "  " * Config.Whitespace, KeyframeCount))
                for Frame in range(0, KeyframeCount):
                    bpy.context.scene.frame_set(Frame + bpy.context.scene.frame_start)
                    
                    Rotation = Bones[Bone.name].matrix.to_quaternion() * Bone.rotation_quaternion
                    
                    Config.File.write("{}{}{:9f},{:9f},{:9f},{:9f};;".format("  " * Config.Whitespace, (str(Frame) + ";4;").ljust(8), -Rotation[0], Rotation[1], Rotation[2], Rotation[3]))
                    if Frame == KeyframeCount-1:
                        Config.File.write(";\n")
                    else:
                        Config.File.write(",\n")
                Config.Whitespace -= 1
                Config.File.write("{}}}\n".format("  " * Config.Whitespace))
                if Config.Verbose:
                    print("        Done")
                
                #Scale
                if Config.Verbose:
                    print("        Writing Scale...")
                Config.File.write("{}AnimationKey {{ //Scale\n".format("  " * Config.Whitespace, KeyframeCount))
                Config.Whitespace += 1
                Config.File.write("{}1;\n{}{};\n".format("  " * Config.Whitespace, "  " * Config.Whitespace, KeyframeCount))
                for Frame in range(0, KeyframeCount):
                    bpy.context.scene.frame_set(Frame + bpy.context.scene.frame_start)
                    
                    if Bone.parent:
                        PoseMatrix = Bone.parent.matrix.inverted()
                    else:
                        PoseMatrix = Matrix()
                    PoseMatrix *= Bone.matrix
                    
                    Scale = PoseMatrix.to_scale()
                    Config.File.write("{}{}{:9f},{:9f},{:9f};;".format("  " * Config.Whitespace, (str(Frame) + ";3;").ljust(8), Scale[0], Scale[1], Scale[2]))
                    if Frame == KeyframeCount-1:
                        Config.File.write(";\n")
                    else:
                        Config.File.write(",\n")
                Config.Whitespace -= 1
                Config.File.write("{}}}\n".format("  " * Config.Whitespace))
                if Config.Verbose:
                    print("        Done")
                
                Config.Whitespace -= 1
                Config.File.write("{}}}\n".format("  " * Config.Whitespace))
                if Config.Verbose:
                    print("      Done") #Done with Armature Bone
            if Config.Verbose:
                print("    Done") #Done with Armature Bone data
        if Config.Verbose:
            print("  Done")  #Done with Object
    
    Config.Whitespace -= 1
    Config.File.write("{}}} //End of AnimationSet\n".format("  " * Config.Whitespace))


def CloseFile(Config):
    if Config.Verbose:
        print("Closing File...")
    Config.File.close()
    if Config.Verbose:
        print("Done")


CoordinateSystems = (
    ("1", "Left-Handed", ""),
    ("2", "Right-Handed", ""),
    )


AnimationModes = (
    ("0", "None", ""),
    ("1", "Keyframes Only", ""),
    ("2", "Full Animation", ""),
    )

ExportModes = (
    ("1", "All Objects", ""),
    ("2", "Selected Objects", ""),
    )


from bpy.props import StringProperty, EnumProperty, BoolProperty


class DirectXExporter(bpy.types.Operator):
    """Export to the DirectX model format (.x)"""

    bl_idname = "export.directx"
    bl_label = "Export DirectX"

    filepath = StringProperty(subtype='FILE_PATH')

    #Coordinate System
    CoordinateSystem = EnumProperty(
        name="System",
        description="Select a coordinate system to export to",
        items=CoordinateSystems,
        default="1")

    #General Options
    RotateX = BoolProperty(
        name="Rotate X 90 Degrees",
        description="Rotate the entire scene 90 degrees around the X axis so Y is up",
        default=True)
    FlipNormals = BoolProperty(
        name="Flip Normals",
        description="",
        default=False)
    ApplyModifiers = BoolProperty(
        name="Apply Modifiers",
        description="Apply object modifiers before export",
        default=False)
    IncludeFrameRate = BoolProperty(
        name="Include Frame Rate",
        description="Include the AnimTicksPerSecond template which is used by " \
                    "some engines to control animation speed",
        default=False)
    ExportTextures = BoolProperty(
        name="Export Textures",
        description="Reference external image files to be used by the model",
        default=True)
    ExportArmatures = BoolProperty(
        name="Export Armatures",
        description="Export the bones of any armatures to deform meshes",
        default=False)
    ExportAnimation = EnumProperty(
        name="Animations",
        description="Select the type of animations to export. Only object " \
                    "and armature bone animations can be exported. Full " \
                    "Animation exports every frame",
        items=AnimationModes,
        default="0")

    #Export Mode
    ExportMode = EnumProperty(
        name="Export",
        description="Select which objects to export. Only Mesh, Empty, " \
                    "and Armature objects will be exported",
        items=ExportModes,
        default="1")

    Verbose = BoolProperty(
        name="Verbose",
        description="Run the exporter in debug mode. Check the console for output",
        default=False)

    def execute(self, context):
        #Append .x
        FilePath = bpy.path.ensure_ext(self.filepath, ".x")

        Config = DirectXExporterSettings(context,
                                         FilePath,
                                         CoordinateSystem=self.CoordinateSystem,
                                         RotateX=self.RotateX,
                                         FlipNormals=self.FlipNormals,
                                         ApplyModifiers=self.ApplyModifiers,
                                         IncludeFrameRate=self.IncludeFrameRate,
                                         ExportTextures=self.ExportTextures,
                                         ExportArmatures=self.ExportArmatures,
                                         ExportAnimation=self.ExportAnimation,
                                         ExportMode=self.ExportMode,
                                         Verbose=self.Verbose)

        ExportDirectX(Config)
        return {'FINISHED'}

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = bpy.path.ensure_ext(bpy.data.filepath, ".x")
        WindowManager = context.window_manager
        WindowManager.fileselect_add(self)
        return {"RUNNING_MODAL"}


def menu_func(self, context):
    self.layout.operator(DirectXExporter.bl_idname, text="DirectX (.x)")


def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_export.append(menu_func)


def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_export.remove(menu_func)


if __name__ == "__main__":
    register()
