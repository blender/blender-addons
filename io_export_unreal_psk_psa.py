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
    "name": "Export Skeleletal Mesh/Animation Data",
    "author": "Darknet/Optimus_P-Fat/Active_Trash/Sinsoft/VendorX",
    "version": (2, 2),
    "blender": (2, 5, 6),
    "api": 31847,
    "location": "File > Export > Skeletal Mesh/Animation Data (.psk/.psa)",
    "description": "Export Unreal Engine (.psk)",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"\
        "Scripts/Import-Export/Unreal_psk_psa",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=21366",
    "category": "Import-Export"}

"""
-- Unreal Skeletal Mesh and Animation Export (.psk  and .psa) export script v0.0.1 --<br> 

- NOTES:
- This script Exports To Unreal's PSK and PSA file formats for Skeletal Meshes and Animations. <br>
- This script DOES NOT support vertex animation! These require completely different file formats. <br>

- v0.0.1
- Initial version

- v0.0.2
- This version adds support for more than one material index!

[ - Edit by: Darknet
- v0.0.3 - v0.0.12
- This will work on UT3 and it is a stable version that work with vehicle for testing. 
- Main Bone fix no dummy needed to be there.
- Just bone issues position, rotation, and offset for psk.
- The armature bone position, rotation, and the offset of the bone is fix. It was to deal with skeleton mesh export for psk.
- Animation is fix for position, offset, rotation bone support one rotation direction when armature build. 
- It will convert your mesh into triangular when exporting to psk file.
- Did not work with psa export yet.

- v0.0.13
- The animatoin will support different bone rotations when export the animation.

- v0.0.14
- Fixed Action set keys frames when there is no pose keys and it will ignore it.

- v0.0.15
- Fixed multiple objects when exporting to psk. Select one mesh to export to psk.
- ]

- v0.1.1
- Blender 2.50 svn (Support)

Credit to:
- export_cal3d.py (Position of the Bones Format)
- blender2md5.py (Animation Translation Format)
- export_obj.py (Blender 2.5/Pyhton 3.x Format)

- freenode #blendercoder -> user -> ideasman42

- Give Credit to those who work on this script.

- http://sinsoft.com
"""

import os
import time
import datetime
import bpy
import mathutils
import operator

from struct import pack, calcsize


# REFERENCE MATERIAL JUST IN CASE:
# 
# U = x / sqrt(x^2 + y^2 + z^2)
# V = y / sqrt(x^2 + y^2 + z^2)
#
# Triangles specifed counter clockwise for front face
#
#defines for sizeofs
SIZE_FQUAT = 16
SIZE_FVECTOR = 12
SIZE_VJOINTPOS = 44
SIZE_ANIMINFOBINARY = 168
SIZE_VCHUNKHEADER = 32
SIZE_VMATERIAL = 88
SIZE_VBONE = 120
SIZE_FNAMEDBONEBINARY = 120
SIZE_VRAWBONEINFLUENCE = 12
SIZE_VQUATANIMKEY = 32
SIZE_VVERTEX = 16
SIZE_VPOINT = 12
SIZE_VTRIANGLE = 12
MaterialName = []

########################################################################
# Generic Object->Integer mapping
# the object must be usable as a dictionary key
class ObjMap:
    def __init__(self):
        self.dict = {}
        self.next = 0
    def get(self, obj):
        if obj in self.dict:
            return self.dict[obj]
        else:
            id = self.next
            self.next = self.next + 1
            self.dict[obj] = id
            return id
        
    def items(self):
        getval = operator.itemgetter(0)
        getkey = operator.itemgetter(1)
        return map(getval, sorted(self.dict.items(), key=getkey))

########################################################################
# RG - UNREAL DATA STRUCTS - CONVERTED FROM C STRUCTS GIVEN ON UDN SITE 
# provided here: http://udn.epicgames.com/Two/BinaryFormatSpecifications.html
# updated UDK (Unreal Engine 3): http://udn.epicgames.com/Three/BinaryFormatSpecifications.html
class FQuat:
    def __init__(self): 
        self.X = 0.0
        self.Y = 0.0
        self.Z = 0.0
        self.W = 1.0
        
    def dump(self):
        data = pack('ffff', self.X, self.Y, self.Z, self.W)
        return data
        
    def __cmp__(self, other):
        return cmp(self.X, other.X) \
            or cmp(self.Y, other.Y) \
            or cmp(self.Z, other.Z) \
            or cmp(self.W, other.W)
        
    def __hash__(self):
        return hash(self.X) ^ hash(self.Y) ^ hash(self.Z) ^ hash(self.W)
        
    def __str__(self):
        return "[%f,%f,%f,%f](FQuat)" % (self.X, self.Y, self.Z, self.W)
        
class FVector(object):
    def __init__(self, X=0.0, Y=0.0, Z=0.0):
        self.X = X
        self.Y = Y
        self.Z = Z
        
    def dump(self):
        data = pack('fff', self.X, self.Y, self.Z)
        return data
        
    def __cmp__(self, other):
        return cmp(self.X, other.X) \
            or cmp(self.Y, other.Y) \
            or cmp(self.Z, other.Z)
        
    def _key(self):
        return (type(self).__name__, self.X, self.Y, self.Z)
        
    def __hash__(self):
        return hash(self._key())
        
    def __eq__(self, other):
        if not hasattr(other, '_key'):
            return False
        return self._key() == other._key() 
        
    def dot(self, other):
        return self.X * other.X + self.Y * other.Y + self.Z * other.Z
    
    def cross(self, other):
        return FVector(self.Y * other.Z - self.Z * other.Y,
                self.Z * other.X - self.X * other.Z,
                self.X * other.Y - self.Y * other.X)
                
    def sub(self, other):
        return FVector(self.X - other.X,
            self.Y - other.Y,
            self.Z - other.Z)

class VJointPos:
    def __init__(self):
        self.Orientation = FQuat()
        self.Position = FVector()
        self.Length = 0.0
        self.XSize = 0.0
        self.YSize = 0.0
        self.ZSize = 0.0
        
    def dump(self):
        data = self.Orientation.dump() + self.Position.dump() + pack('4f', self.Length, self.XSize, self.YSize, self.ZSize)
        return data
            
class AnimInfoBinary:
    def __init__(self):
        self.Name = "" # length=64
        self.Group = ""    # length=64
        self.TotalBones = 0
        self.RootInclude = 0
        self.KeyCompressionStyle = 0
        self.KeyQuotum = 0
        self.KeyPrediction = 0.0
        self.TrackTime = 0.0
        self.AnimRate = 0.0
        self.StartBone = 0
        self.FirstRawFrame = 0
        self.NumRawFrames = 0
        
    def dump(self):
        data = pack('64s64siiiifffiii', self.Name, self.Group, self.TotalBones, self.RootInclude, self.KeyCompressionStyle, self.KeyQuotum, self.KeyPrediction, self.TrackTime, self.AnimRate, self.StartBone, self.FirstRawFrame, self.NumRawFrames)
        return data

class VChunkHeader:
    def __init__(self, name, type_size):
        self.ChunkID = name # length=20
        self.TypeFlag = 1999801 # special value
        self.DataSize = type_size
        self.DataCount = 0
        
    def dump(self):
        data = pack('20siii', self.ChunkID, self.TypeFlag, self.DataSize, self.DataCount)
        return data
        
class VMaterial:
    def __init__(self):
        self.MaterialName = "" # length=64
        self.TextureIndex = 0
        self.PolyFlags = 0 # DWORD
        self.AuxMaterial = 0
        self.AuxFlags = 0 # DWORD
        self.LodBias = 0
        self.LodStyle = 0
        
    def dump(self):
        data = pack('64siLiLii', self.MaterialName, self.TextureIndex, self.PolyFlags, self.AuxMaterial, self.AuxFlags, self.LodBias, self.LodStyle)
        return data

class VBone:
    def __init__(self):
        self.Name = "" # length = 64
        self.Flags = 0 # DWORD
        self.NumChildren = 0
        self.ParentIndex = 0
        self.BonePos = VJointPos()
        
    def dump(self):
        data = pack('64sLii', self.Name, self.Flags, self.NumChildren, self.ParentIndex) + self.BonePos.dump()
        return data

#same as above - whatever - this is how Epic does it...        
class FNamedBoneBinary:
    def __init__(self):
        self.Name = "" # length = 64
        self.Flags = 0 # DWORD
        self.NumChildren = 0
        self.ParentIndex = 0
        self.BonePos = VJointPos()
        
        self.IsRealBone = 0  # this is set to 1 when the bone is actually a bone in the mesh and not a dummy
        
    def dump(self):
        data = pack('64sLii', self.Name, self.Flags, self.NumChildren, self.ParentIndex) + self.BonePos.dump()
        return data
    
class VRawBoneInfluence:
    def __init__(self):
        self.Weight = 0.0
        self.PointIndex = 0
        self.BoneIndex = 0
        
    def dump(self):
        data = pack('fii', self.Weight, self.PointIndex, self.BoneIndex)
        return data
        
class VQuatAnimKey:
    def __init__(self):
        self.Position = FVector()
        self.Orientation = FQuat()
        self.Time = 0.0
        
    def dump(self):
        data = self.Position.dump() + self.Orientation.dump() + pack('f', self.Time)
        return data
        
class VVertex(object):
    def __init__(self):
        self.PointIndex = 0 # WORD
        self.U = 0.0
        self.V = 0.0
        self.MatIndex = 0 #BYTE
        self.Reserved = 0 #BYTE
        
    def dump(self):
        data = pack('HHffBBH', self.PointIndex, 0, self.U, self.V, self.MatIndex, self.Reserved, 0)
        return data
        
    def __cmp__(self, other):
        return cmp(self.PointIndex, other.PointIndex) \
            or cmp(self.U, other.U) \
            or cmp(self.V, other.V) \
            or cmp(self.MatIndex, other.MatIndex) \
            or cmp(self.Reserved, other.Reserved)
    
    def _key(self):
        return (type(self).__name__,self.PointIndex, self.U, self.V,self.MatIndex,self.Reserved)
        
    def __hash__(self):
        return hash(self._key())
        
    def __eq__(self, other):
        if not hasattr(other, '_key'):
            return False
        return self._key() == other._key()
        
class VPoint(object):
    def __init__(self):
        self.Point = FVector()
        
    def dump(self):
        return self.Point.dump()
        
    def __cmp__(self, other):
        return cmp(self.Point, other.Point)
    
    def _key(self):
        return (type(self).__name__, self.Point)
    
    def __hash__(self):
        return hash(self._key())
        
    def __eq__(self, other):
        if not hasattr(other, '_key'):
            return False
        return self._key() == other._key() 
        
class VTriangle:
    def __init__(self):
        self.WedgeIndex0 = 0 # WORD
        self.WedgeIndex1 = 0 # WORD
        self.WedgeIndex2 = 0 # WORD
        self.MatIndex = 0 # BYTE
        self.AuxMatIndex = 0 # BYTE
        self.SmoothingGroups = 0 # DWORD
        
    def dump(self):
        data = pack('HHHBBL', self.WedgeIndex0, self.WedgeIndex1, self.WedgeIndex2, self.MatIndex, self.AuxMatIndex, self.SmoothingGroups)
        return data

# END UNREAL DATA STRUCTS
########################################################################

########################################################################
#RG - helper class to handle the normal way the UT files are stored 
#as sections consisting of a header and then a list of data structures
class FileSection:
    def __init__(self, name, type_size):
        self.Header = VChunkHeader(name, type_size)
        self.Data = [] # list of datatypes
        
    def dump(self):
        data = self.Header.dump()
        for i in range(len(self.Data)):
            data = data + self.Data[i].dump()
        return data
        
    def UpdateHeader(self):
        self.Header.DataCount = len(self.Data)
        
class PSKFile:
    def __init__(self):
        self.GeneralHeader = VChunkHeader("ACTRHEAD", 0)
        self.Points = FileSection("PNTS0000", SIZE_VPOINT)        #VPoint
        self.Wedges = FileSection("VTXW0000", SIZE_VVERTEX)        #VVertex
        self.Faces = FileSection("FACE0000", SIZE_VTRIANGLE)        #VTriangle
        self.Materials = FileSection("MATT0000", SIZE_VMATERIAL)    #VMaterial
        self.Bones = FileSection("REFSKELT", SIZE_VBONE)        #VBone
        self.Influences = FileSection("RAWWEIGHTS", SIZE_VRAWBONEINFLUENCE)    #VRawBoneInfluence
        
        #RG - this mapping is not dumped, but is used internally to store the new point indices 
        # for vertex groups calculated during the mesh dump, so they can be used again
        # to dump bone influences during the armature dump
        #
        # the key in this dictionary is the VertexGroup/Bone Name, and the value
        # is a list of tuples containing the new point index and the weight, in that order
        #
        # Layout:
        # { groupname : [ (index, weight), ... ], ... }
        #
        # example: 
        # { 'MyVertexGroup' : [ (0, 1.0), (5, 1.0), (3, 0.5) ] , 'OtherGroup' : [(2, 1.0)] }
        
        self.VertexGroups = {} 
        
    def AddPoint(self, p):
        #print ('AddPoint')
        self.Points.Data.append(p)
        
    def AddWedge(self, w):
        #print ('AddWedge')
        self.Wedges.Data.append(w)
    
    def AddFace(self, f):
        #print ('AddFace')
        self.Faces.Data.append(f)
        
    def AddMaterial(self, m):
        #print ('AddMaterial')
        self.Materials.Data.append(m)
        
    def AddBone(self, b):
        #print ('AddBone [%s]: Position: (x=%f, y=%f, z=%f) Rotation=(%f,%f,%f,%f)'  % (b.Name, b.BonePos.Position.X, b.BonePos.Position.Y, b.BonePos.Position.Z, b.BonePos.Orientation.X,b.BonePos.Orientation.Y,b.BonePos.Orientation.Z,b.BonePos.Orientation.W))
        self.Bones.Data.append(b)
        
    def AddInfluence(self, i):
        #print ('AddInfluence')
        self.Influences.Data.append(i)
        
    def UpdateHeaders(self):
        self.Points.UpdateHeader()
        self.Wedges.UpdateHeader()
        self.Faces.UpdateHeader()
        self.Materials.UpdateHeader()
        self.Bones.UpdateHeader()
        self.Influences.UpdateHeader()
        
    def dump(self):
        self.UpdateHeaders()
        data = self.GeneralHeader.dump() + self.Points.dump() + self.Wedges.dump() + self.Faces.dump() + self.Materials.dump() + self.Bones.dump() + self.Influences.dump()
        return data
        
    def GetMatByIndex(self, mat_index):
        if mat_index >= 0 and len(self.Materials.Data) > mat_index:
            return self.Materials.Data[mat_index]
        else:
            m = VMaterial()
            # modified by VendorX
            m.MaterialName = MaterialName[mat_index]
            self.AddMaterial(m)
            return m
        
    def PrintOut(self):
        print ("--- PSK FILE EXPORTED ---")
        print ('point count: %i' % len(self.Points.Data))
        print ('wedge count: %i' % len(self.Wedges.Data))
        print ('face count: %i' % len(self.Faces.Data))
        print ('material count: %i' % len(self.Materials.Data))
        print ('bone count: %i' % len(self.Bones.Data))
        print ('inlfuence count: %i' % len(self.Influences.Data))
        print ('-------------------------')

# PSA FILE NOTES FROM UDN:
#
#    The raw key array holds all the keys for all the bones in all the specified sequences, 
#    organized as follows:
#    For each AnimInfoBinary's sequence there are [Number of bones] times [Number of frames keys] 
#    in the VQuatAnimKeys, laid out as tracks of [numframes] keys for each bone in the order of 
#    the bones as defined in the array of FnamedBoneBinary in the PSA. 
#
#    Once the data from the PSK (now digested into native skeletal mesh) and PSA (digested into 
#    a native animation object containing one or more sequences) are associated together at runtime, 
#    bones are linked up by name. Any bone in a skeleton (from the PSK) that finds no partner in 
#    the animation sequence (from the PSA) will assume its reference pose stance ( as defined in 
#    the offsets & rotations that are in the VBones making up the reference skeleton from the PSK)

class PSAFile:
    def __init__(self):
        self.GeneralHeader = VChunkHeader("ANIMHEAD", 0)
        self.Bones = FileSection("BONENAMES", SIZE_FNAMEDBONEBINARY)    #FNamedBoneBinary
        self.Animations = FileSection("ANIMINFO", SIZE_ANIMINFOBINARY)    #AnimInfoBinary
        self.RawKeys = FileSection("ANIMKEYS", SIZE_VQUATANIMKEY)    #VQuatAnimKey
        
        # this will take the format of key=Bone Name, value = (BoneIndex, Bone Object)
        # THIS IS NOT DUMPED
        self.BoneLookup = {} 
        
    def dump(self):
        data = self.Generalheader.dump() + self.Bones.dump() + self.Animations.dump() + self.RawKeys.dump()
        return data
    
    def AddBone(self, b):
        #LOUD
        #print "AddBone: " + b.Name
        self.Bones.Data.append(b)
        
    def AddAnimation(self, a):
        #LOUD
        #print "AddAnimation: %s, TotalBones: %i, AnimRate: %f, NumRawFrames: %i, TrackTime: %f" % (a.Name, a.TotalBones, a.AnimRate, a.NumRawFrames, a.TrackTime)
        self.Animations.Data.append(a)
        
    def AddRawKey(self, k):
        #LOUD
        #print "AddRawKey [%i]: Time: %f, Quat: x=%f, y=%f, z=%f, w=%f, Position: x=%f, y=%f, z=%f" % (len(self.RawKeys.Data), k.Time, k.Orientation.X, k.Orientation.Y, k.Orientation.Z, k.Orientation.W, k.Position.X, k.Position.Y, k.Position.Z)
        self.RawKeys.Data.append(k)
        
    def UpdateHeaders(self):
        self.Bones.UpdateHeader()
        self.Animations.UpdateHeader()
        self.RawKeys.UpdateHeader()
        
    def GetBoneByIndex(self, bone_index):
        if bone_index >= 0 and len(self.Bones.Data) > bone_index:
            return self.Bones.Data[bone_index]
    
    def IsEmpty(self):
        return (len(self.Bones.Data) == 0 or len(self.Animations.Data) == 0)
    
    def StoreBone(self, b):
        self.BoneLookup[b.Name] = [-1, b]
                    
    def UseBone(self, bone_name):
        if bone_name in self.BoneLookup:
            bone_data = self.BoneLookup[bone_name]
            
            if bone_data[0] == -1:
                bone_data[0] = len(self.Bones.Data)
                self.AddBone(bone_data[1])
                #self.Bones.Data.append(bone_data[1])
            
            return bone_data[0]
            
    def GetBoneByName(self, bone_name):
        if bone_name in self.BoneLookup:
            bone_data = self.BoneLookup[bone_name]
            return bone_data[1]
        
    def GetBoneIndex(self, bone_name):
        if bone_name in self.BoneLookup:
            bone_data = self.BoneLookup[bone_name]
            return bone_data[0]
        
    def dump(self):
        self.UpdateHeaders()
        data = self.GeneralHeader.dump() + self.Bones.dump() + self.Animations.dump() + self.RawKeys.dump()
        return data
        
    def PrintOut(self):
        print ('--- PSA FILE EXPORTED ---')
        print ('bone count: %i' % len(self.Bones.Data))
        print ('animation count: %i' % len(self.Animations.Data))
        print ('rawkey count: %i' % len(self.RawKeys.Data))
        print ('-------------------------')
        
####################################    
# helpers to create bone structs
def make_vbone(name, parent_index, child_count, orientation_quat, position_vect):
    bone = VBone()
    bone.Name = name
    bone.ParentIndex = parent_index
    bone.NumChildren = child_count
    bone.BonePos.Orientation = orientation_quat
    bone.BonePos.Position.X = position_vect.x
    bone.BonePos.Position.Y = position_vect.y
    bone.BonePos.Position.Z = position_vect.z
    
    #these values seem to be ignored?
    #bone.BonePos.Length = tail.length
    #bone.BonePos.XSize = tail.x
    #bone.BonePos.YSize = tail.y
    #bone.BonePos.ZSize = tail.z

    return bone

def make_namedbonebinary(name, parent_index, child_count, orientation_quat, position_vect, is_real):
    bone = FNamedBoneBinary()
    bone.Name = name
    bone.ParentIndex = parent_index
    bone.NumChildren = child_count
    bone.BonePos.Orientation = orientation_quat
    bone.BonePos.Position.X = position_vect.x
    bone.BonePos.Position.Y = position_vect.y
    bone.BonePos.Position.Z = position_vect.z
    bone.IsRealBone = is_real
    return bone    
    
##################################################
#RG - check to make sure face isnt a line
#The face has to be triangle not a line
def is_1d_face(blender_face,mesh):
    #ID Vertex of id point
    v0 = blender_face.vertices[0]
    v1 = blender_face.vertices[1]
    v2 = blender_face.vertices[2]
    
    return (mesh.vertices[v0].co == mesh.vertices[v1].co or \
    mesh.vertices[v1].co == mesh.vertices[v2].co or \
    mesh.vertices[v2].co == mesh.vertices[v0].co)
    return False

##################################################
# http://en.wikibooks.org/wiki/Blender_3D:_Blending_Into_Python/Cookbook#Triangulate_NMesh

#blender 2.50 format using the Operators/command convert the mesh to tri mesh
def triangulateNMesh(object):
    bneedtri = False
    scene = bpy.context.scene
    bpy.ops.object.mode_set(mode='OBJECT')
    for i in scene.objects: i.select = False #deselect all objects
    object.select = True
    scene.objects.active = object #set the mesh object to current
    bpy.ops.object.mode_set(mode='OBJECT')
    print("Checking mesh if needs to convert quad to Tri...")
    for face in object.data.faces:
        if (len(face.vertices) > 3):
            bneedtri = True
            break
    
    bpy.ops.object.mode_set(mode='OBJECT')
    if bneedtri == True:
        print("Converting quad to tri mesh...")
        me_da = object.data.copy() #copy data
        me_ob = object.copy() #copy object
        #note two copy two types else it will use the current data or mesh
        me_ob.data = me_da
        bpy.context.scene.objects.link(me_ob)#link the object to the scene #current object location
        for i in scene.objects: i.select = False #deselect all objects
        me_ob.select = True
        scene.objects.active = me_ob #set the mesh object to current
        bpy.ops.object.mode_set(mode='EDIT') #Operators
        bpy.ops.mesh.select_all(action='SELECT')#select all the face/vertex/edge
        bpy.ops.mesh.quads_convert_to_tris() #Operators
        bpy.context.scene.update()
        bpy.ops.object.mode_set(mode='OBJECT') # set it in object
        bpy.context.scene.unrealtriangulatebool = True
        print("Triangulate Mesh Done!")
    else:
        bpy.context.scene.unrealtriangulatebool = False
        print("No need to convert tri mesh.")
        me_ob = object
    return me_ob

#Blender Bone Index
class BBone:
    def __init__(self):
        self.bone = ""
        self.index = 0
bonedata = []
BBCount = 0    
#deal with mesh bones groups vertex point
def BoneIndex(bone):
    global BBCount, bonedata
    #print("//==============")
    #print(bone.name , "ID:",BBCount)
    BB = BBone()
    BB.bone = bone.name
    BB.index = BBCount
    bonedata.append(BB)
    BBCount += 1
    for current_child_bone in bone.children:
        BoneIndex(current_child_bone)

def BoneIndexArmature(blender_armature):
    global BBCount
    #print("\n Buildng bone before mesh \n")
    #objectbone = blender_armature.pose #Armature bone
    #print(blender_armature)
    objectbone = blender_armature[0].pose 
    #print(dir(ArmatureData))
    
    for bone in objectbone.bones:
        if(bone.parent is None):
            BoneIndex(bone)
            #BBCount += 1
            break
    
bDeleteMergeMesh = False
# Actual object parsing functions
def parse_meshes(blender_meshes, psk_file):
    #this is use to call the bone name and the index array for group index matches
    global bonedata,bDeleteMergeMesh
    #print("BONE DATA",len(bonedata))
    print ("----- parsing meshes -----")
    print("Number of Object Meshes:",len(blender_meshes))
    for current_obj in blender_meshes: #number of mesh that should be one mesh here
        #bpy.ops.object.mode_set(mode='EDIT')
        current_obj = triangulateNMesh(current_obj)
        #print(dir(current_obj))
        print("Mesh Name:",current_obj.name)
        current_mesh = current_obj.data
        
        #collect a list of the material names
        if len(current_obj.material_slots) > 0:
            counter = 0
            while counter < len(current_obj.material_slots):
                MaterialName.append(current_obj.material_slots[counter].name)
                print("Material Name:",current_obj.material_slots[counter].name)
                #create the current material
                psk_file.GetMatByIndex(counter)
                #print("materials: ",MaterialName[counter])
                counter += 1
        #    object_mat = current_obj.materials[0]
        object_material_index = current_obj.active_material_index
    
        points = ObjMap()
        wedges = ObjMap()
        
        discarded_face_count = 0
        print (" -- Dumping Mesh Faces -- LEN:", len(current_mesh.faces))
        for current_face in current_mesh.faces:
            #print ' -- Dumping UVs -- '
            #print current_face.uv_textures
            # modified by VendorX
            object_material_index = current_face.material_index
            
            if len(current_face.vertices) != 3:
                raise RuntimeError("Non-triangular face (%i)" % len(current_face.vertices))
            
            #No Triangulate Yet
            #            if len(current_face.vertices) != 3:
            #                raise RuntimeError("Non-triangular face (%i)" % len(current_face.vertices))
            #                #TODO: add two fake faces made of triangles?
            
            #RG - apparently blender sometimes has problems when you do quad to triangle 
            #    conversion, and ends up creating faces that have only TWO points -
            #     one of the points is simply in the vertex list for the face twice. 
            #    This is bad, since we can't get a real face normal for a LINE, we need 
            #    a plane for this. So, before we add the face to the list of real faces, 
            #    ensure that the face is actually a plane, and not a line. If it is not 
            #    planar, just discard it and notify the user in the console after we're
            #    done dumping the rest of the faces
            
            if not is_1d_face(current_face,current_mesh):
                #print("faces")
                wedge_list = []
                vect_list = []
                
                #get or create the current material
                m = psk_file.GetMatByIndex(object_material_index)

                face_index = current_face.index
                has_UV = False
                faceUV = None
                
                if len(current_mesh.uv_textures) > 0:
                    has_UV = True    
                    #print("face index: ",face_index)
                    #faceUV = current_mesh.uv_textures.active.data[face_index]#UVs for current face
                    #faceUV = current_mesh.uv_textures.active.data[0]#UVs for current face
                    #print(face_index,"<[FACE NUMBER")
                    uv_layer = current_mesh.uv_textures.active
                    faceUV = uv_layer.data[face_index]
                    #print("============================")
                    #size(data) is number of texture faces. Each face has UVs
                    #print("DATA face uv: ",len(faceUV.uv), " >> ",(faceUV.uv[0][0]))
                
                for i in range(3):
                    vert_index = current_face.vertices[i]
                    vert = current_mesh.vertices[vert_index]
                    uv = []
                    #assumes 3 UVs Per face (for now).
                    if (has_UV):
                        if len(faceUV.uv) != 3:
                            print ("WARNING: Current face is missing UV coordinates - writing 0,0...")
                            print ("WARNING: Face has more than 3 UVs - writing 0,0...")
                            uv = [0.0, 0.0]
                        else:
                            #uv.append(faceUV.uv[i][0])
                            #uv.append(faceUV.uv[i][1])
                            uv = [faceUV.uv[i][0],faceUV.uv[i][1]] #OR bottom works better # 24 for cube
                            #uv = list(faceUV.uv[i]) #30 just cube    
                    else:
                        #print ("No UVs?")
                        uv = [0.0, 0.0]
                    #print("UV >",uv)
                    #uv = [0.0, 0.0] #over ride uv that is not fixed
                    #print(uv)
                    #flip V coordinate because UEd requires it and DOESN'T flip it on its own like it
                    #does with the mesh Y coordinates.
                    #this is otherwise known as MAGIC-2
                    uv[1] = 1.0 - uv[1]
                    
                    #deal with the min and max value
                    #if value is over the set limit it will null the uv texture
                    if (uv[0] > 1):
                        uv[0] = 1
                    if (uv[0] < 0):
                        uv[0] = 0
                    if (uv[1] > 1):
                        uv[1] = 1
                    if (uv[1] < 0):
                        uv[1] = 0

                    
                    # RE - Append untransformed vector (for normal calc below)
                    # TODO: convert to Blender.Mathutils
                    vect_list.append(FVector(vert.co.x, vert.co.y, vert.co.z))
                    
                    # Transform position for export
                    #vpos = vert.co * object_material_index
                    vpos = vert.co * current_obj.matrix_local
                    # Create the point
                    p = VPoint()
                    p.Point.X = vpos.x
                    p.Point.Y = vpos.y
                    p.Point.Z = vpos.z
                    
                    # Create the wedge
                    w = VVertex()
                    w.MatIndex = object_material_index
                    w.PointIndex = points.get(p) # get index from map
                    #Set UV TEXTURE
                    w.U = uv[0]
                    w.V = uv[1]
                    index_wedge = wedges.get(w)
                    wedge_list.append(index_wedge)
                    
                    #print results
                    #print 'result PointIndex=%i, U=%f, V=%f, wedge_index=%i' % (
                    #    w.PointIndex,
                    #    w.U,
                    #    w.V,
                    #    wedge_index)
                
                # Determine face vertex order
                # get normal from blender
                no = current_face.normal
                
                # TODO: convert to Blender.Mathutils
                # convert to FVector
                norm = FVector(no[0], no[1], no[2])
                
                # Calculate the normal of the face in blender order
                tnorm = vect_list[1].sub(vect_list[0]).cross(vect_list[2].sub(vect_list[1]))
                
                # RE - dot the normal from blender order against the blender normal
                # this gives the product of the two vectors' lengths along the blender normal axis
                # all that matters is the sign
                dot = norm.dot(tnorm)

                # print results
                #print 'face norm: (%f,%f,%f), tnorm=(%f,%f,%f), dot=%f' % (
                #    norm.X, norm.Y, norm.Z,
                #    tnorm.X, tnorm.Y, tnorm.Z,
                #    dot)

                tri = VTriangle()
                # RE - magic: if the dot product above > 0, order the vertices 2, 1, 0
                #        if the dot product above < 0, order the vertices 0, 1, 2
                #        if the dot product is 0, then blender's normal is coplanar with the face
                #        and we cannot deduce which side of the face is the outside of the mesh
                if (dot > 0):
                    (tri.WedgeIndex2, tri.WedgeIndex1, tri.WedgeIndex0) = wedge_list
                elif (dot < 0):
                    (tri.WedgeIndex0, tri.WedgeIndex1, tri.WedgeIndex2) = wedge_list
                else:
                    dindex0 = current_face.vertices[0];
                    dindex1 = current_face.vertices[1];
                    dindex2 = current_face.vertices[2];

                    current_mesh.vertices[dindex0].select = True
                    current_mesh.vertices[dindex1].select = True
                    current_mesh.vertices[dindex2].select = True
                    
                    raise RuntimeError("normal vector coplanar with face! points:", current_mesh.vertices[dindex0].co, current_mesh.vertices[dindex1].co, current_mesh.vertices[dindex2].co)
                #print(dir(current_face))
                current_face.select = True
                #print((current_face.use_smooth))
                #not sure if this right
                #tri.SmoothingGroups
                if current_face.use_smooth == True:
                    tri.SmoothingGroups = 1
                else:
                    tri.SmoothingGroups = 0
                
                tri.MatIndex = object_material_index
                
                
                #print(tri)
                psk_file.AddFace(tri)
                
            else:
                discarded_face_count = discarded_face_count + 1
                
        print (" -- Dumping Mesh Points -- LEN:",len(points.dict))
        for point in points.items():
            psk_file.AddPoint(point)
        if len(points.dict) > 32767:
           raise RuntimeError("Vertex point reach max limited 32767 in pack data. Your",len(points.dict))
        print (" -- Dumping Mesh Wedge -- LEN:",len(wedges.dict))
        		
        for wedge in wedges.items():
            psk_file.AddWedge(wedge)
            
        #RG - if we happend upon any non-planar faces above that we've discarded, 
        #    just let the user know we discarded them here in case they want 
        #    to investigate
    
        if discarded_face_count > 0: 
            print ("INFO: Discarded %i non-planar faces." % (discarded_face_count))
        
        #RG - walk through the vertex groups and find the indexes into the PSK points array 
        #for them, then store that index and the weight as a tuple in a new list of 
        #verts for the group that we can look up later by bone name, since Blender matches
        #verts to bones for influences by having the VertexGroup named the same thing as
        #the bone

        #vertex group.
        for bonegroup in bonedata:
            #print("bone gourp build:",bonegroup.bone)
            vert_list = []
            for current_vert in current_mesh.vertices:
                #print("INDEX V:",current_vert.index)
                vert_index = current_vert.index
                for vgroup in current_vert.groups:#vertex groupd id
                    vert_weight = vgroup.weight
                    if(bonegroup.index == vgroup.group):
                        p = VPoint()
                        vpos = current_vert.co * current_obj.matrix_local
                        p.Point.X = vpos.x
                        p.Point.Y = vpos.y 
                        p.Point.Z = vpos.z
                        #print(current_vert.co)
                        point_index = points.get(p) #point index
                        v_item = (point_index, vert_weight)
                        vert_list.append(v_item)
            #bone name, [point id and wieght]
            #print("Add Vertex Group:",bonegroup.bone, " No. Points:",len(vert_list))
            psk_file.VertexGroups[bonegroup.bone] = vert_list
        
        #unrealtriangulatebool #this will remove the mesh from the scene
        if (bpy.context.scene.unrealtriangulatebool == True)or (bDeleteMergeMesh == True):
            if bDeleteMergeMesh == True:
                print("Removing merge mesh.")
            print("Remove tmp Mesh [ " ,current_obj.name, " ] from scene >"  ,(bpy.context.scene.unrealtriangulatebool ))
            bpy.ops.object.mode_set(mode='OBJECT') # set it in object
            bpy.context.scene.objects.unlink(current_obj)
        #if bDeleteMergeMesh == True:
            #print("Remove merge Mesh [ " ,current_obj.name, " ] from scene")
            #bpy.ops.object.mode_set(mode='OBJECT') # set it in object
            #bpy.context.scene.objects.unlink(current_obj)
        
def make_fquat(bquat):
    quat = FQuat()
    
    #flip handedness for UT = set x,y,z to negative (rotate in other direction)
    quat.X = -bquat.x
    quat.Y = -bquat.y
    quat.Z = -bquat.z

    quat.W = bquat.w
    return quat
    
def make_fquat_default(bquat):
    quat = FQuat()
    #print(dir(bquat))
    quat.X = bquat.x
    quat.Y = bquat.y
    quat.Z = bquat.z
    
    quat.W = bquat.w
    return quat

# =================================================================================================
# TODO: remove this 1am hack
nbone = 0
def parse_bone(blender_bone, psk_file, psa_file, parent_id, is_root_bone, parent_matrix, parent_root):
    global nbone     # look it's evil!
    #print '-------------------- Dumping Bone ---------------------- '

    #If bone does not have parent that mean it the root bone
    if blender_bone.parent is None:
        parent_root = blender_bone
    
    
    child_count = len(blender_bone.children)
    #child of parent
    child_parent = blender_bone.parent
    
    if child_parent != None:
        print ("--Bone Name:",blender_bone.name ," parent:" , blender_bone.parent.name, "ID:", nbone)
    else:
        print ("--Bone Name:",blender_bone.name ," parent: None" , "ID:", nbone)
    
    if child_parent != None:
        quat_root = blender_bone.matrix
        quat = make_fquat(quat_root.to_quaternion())
        #print("DIR:",dir(child_parent.matrix.to_quaternion()))
        quat_parent = child_parent.matrix.to_quaternion().inverted()
        parent_head = child_parent.head * quat_parent
        parent_tail = child_parent.tail * quat_parent
        
        set_position = (parent_tail - parent_head) + blender_bone.head
    else:
        # ROOT BONE
        #This for root 
        set_position = blender_bone.head * parent_matrix #ARMATURE OBJECT Locction
        rot_mat = blender_bone.matrix * parent_matrix.to_3x3() #ARMATURE OBJECT Rotation
        #print(dir(rot_mat))
        
        quat = make_fquat_default(rot_mat.to_quaternion())
        
    #print ("[[======= FINAL POSITION:", set_position)
    final_parent_id = parent_id
    
    #RG/RE -
    #if we are not seperated by a small distance, create a dummy bone for the displacement
    #this is only needed for root bones, since UT assumes a connected skeleton, and from here
    #down the chain we just use "tail" as an endpoint
    #if(head.length > 0.001 and is_root_bone == 1):
    if(0):    
        pb = make_vbone("dummy_" + blender_bone.name, parent_id, 1, FQuat(), tail)
        psk_file.AddBone(pb)
        pbb = make_namedbonebinary("dummy_" + blender_bone.name, parent_id, 1, FQuat(), tail, 0)
        psa_file.StoreBone(pbb)
        final_parent_id = nbone
        nbone = nbone + 1
        #tail = tail-head
        
    my_id = nbone
    
    pb = make_vbone(blender_bone.name, final_parent_id, child_count, quat, set_position)
    psk_file.AddBone(pb)
    pbb = make_namedbonebinary(blender_bone.name, final_parent_id, child_count, quat, set_position, 1)
    psa_file.StoreBone(pbb)

    nbone = nbone + 1
    
    #RG - dump influences for this bone - use the data we collected in the mesh dump phase
    # to map our bones to vertex groups
    #print("///////////////////////")
    #print("set influence")
    if blender_bone.name in psk_file.VertexGroups:
        vertex_list = psk_file.VertexGroups[blender_bone.name]
        #print("vertex list:", len(vertex_list), " of >" ,blender_bone.name )
        for vertex_data in vertex_list:
            #print("set influence vettex")
            point_index = vertex_data[0]
            vertex_weight = vertex_data[1]
            influence = VRawBoneInfluence()
            influence.Weight = vertex_weight
            influence.BoneIndex = my_id
            influence.PointIndex = point_index
            #print ('Adding Bone Influence for [%s] = Point Index=%i, Weight=%f' % (blender_bone.name, point_index, vertex_weight))
            #print("adding influence")
            psk_file.AddInfluence(influence)
    
    #blender_bone.matrix_local
    #recursively dump child bones
    mainparent = parent_matrix
    #if len(blender_bone.children) > 0:
    for current_child_bone in blender_bone.children:
        parse_bone(current_child_bone, psk_file, psa_file, my_id, 0, mainparent, parent_root)

def parse_armature(blender_armature, psk_file, psa_file):
    print ("----- parsing armature -----")
    print ('blender_armature length: %i' % (len(blender_armature)))
    
    #magic 0 sized root bone for UT - this is where all armature dummy bones will attach
    #dont increment nbone here because we initialize it to 1 (hackity hackity hack)

    #count top level bones first. NOT EFFICIENT.
    child_count = 0
    for current_obj in blender_armature: 
        current_armature = current_obj.data
        bones = [x for x in current_armature.bones if not x.parent is None]
        child_count += len(bones)

    for current_obj in blender_armature:
        print ("Current Armature Name: " + current_obj.name)
        current_armature = current_obj.data
        #armature_id = make_armature_bone(current_obj, psk_file, psa_file)
        
        #we dont want children here - only the top level bones of the armature itself
        #we will recursively dump the child bones as we dump these bones
        """
        bones = [x for x in current_armature.bones if not x.parent is None]
        #will ingore this part of the ocde
        """
        if len(current_armature.bones) == 0:
            raise RuntimeError("Warning add two bones else it will crash the unreal editor.")
        if len(current_armature.bones) == 1:
            raise RuntimeError("Warning add one more bone else it will crash the unreal editor.")
		
        mainbonecount = 0;
        for current_bone in current_armature.bones: #list the bone. #note this will list all the bones.
            if(current_bone.parent is None):
                mainbonecount += 1
        print("Main Bone",mainbonecount)
        if mainbonecount > 1:
           #print("Warning there no main bone.")
           raise RuntimeError("There too many Main bones. Number main bones:",mainbonecount)
        for current_bone in current_armature.bones: #list the bone. #note this will list all the bones.
            if(current_bone.parent is None):
                parse_bone(current_bone, psk_file, psa_file, 0, 0, current_obj.matrix_local, None)
                break

# get blender objects by type        
def get_blender_objects(objects, intype):
    return [x for x in objects if x.type == intype]
            
#strips current extension (if any) from filename and replaces it with extension passed in
def make_filename_ext(filename, extension):
    new_filename = ''
    extension_index = filename.find('.')
    
    if extension_index == -1:
        new_filename = filename + extension
    else:
        new_filename = filename[0:extension_index] + extension
        
    return new_filename

# returns the quaternion Grassman product a*b
# this is the same as the rotation a(b(x)) 
# (ie. the same as B*A if A and B are matrices representing 
# the rotations described by quaternions a and b)
def grassman(a, b):    
    return mathutils.Quaternion(
        a.w*b.w - a.x*b.x - a.y*b.y - a.z*b.z,
        a.w*b.x + a.x*b.w + a.y*b.z - a.z*b.y,
        a.w*b.y - a.x*b.z + a.y*b.w + a.z*b.x,
        a.w*b.z + a.x*b.y - a.y*b.x + a.z*b.w)
        
def parse_animation(blender_scene, blender_armatures, psa_file):
    #to do list:
    #need to list the action sets
    #need to check if there animation
    #need to check if animation is has one frame then exit it
    print ('\n----- parsing animation -----')
    render_data = blender_scene.render
    bHaveAction = True
    
    anim_rate = render_data.fps
    
    print("==== Blender Settings ====")
    print ('Scene: %s Start Frame: %i, End Frame: %i' % (blender_scene.name, blender_scene.frame_start, blender_scene.frame_end))
    print ('Frames Per Sec: %i' % anim_rate)
    print ("Default FPS: 24" )
    
    cur_frame_index = 0
    
    if bpy.context.scene.unrealactionexportall :#if exporting all actions is ture then go do some work.
        print("Exporting all action:",bpy.context.scene.unrealactionexportall)
        print("[==== Action list Start====]")
        
        print("Number of Action set(s):",len(bpy.data.actions))
        
        for action in bpy.data.actions:#current number action sets
            print("========>>>>>")
            print("Action Name:",action.name)
            #print("Groups:")
            #for bone in action.groups:
                #print("> Name: ",bone.name)
                #print(dir(bone))
            
        print("[==== Action list End ====]")
        
        amatureobject = None #this is the armature set to none
        bonenames = [] #bone name of the armature bones list
        
        for arm in blender_armatures:
            amatureobject = arm
            
        print("\n[==== Armature Object ====]")
        if amatureobject != None:
            print("Name:",amatureobject.name)
            print("Number of bones:", len(amatureobject.pose.bones))
            for bone in amatureobject.pose.bones:
                bonenames.append(bone.name)
        print("[=========================]")
        
        for ActionNLA in bpy.data.actions:
            print("\n==== Action Set ====")
            nobone = 0
            baction = True
            #print("\nChecking actions matching groups with bone names...")
            #Check if the bone names matches the action groups names
            for group in ActionNLA.groups:
                for abone in bonenames:
                    #print("name:>>",abone)
                    if abone == group.name:
                        nobone += 1
                        break
            #if action groups matches the bones length and names matching the gourps do something
            if (len(ActionNLA.groups) == len(bonenames)) and (nobone == len(ActionNLA.groups)):
                print("Action Set match: Pass")
                baction = True
            else:
                print("Action Set match: Fail")
                print("Action Name:",ActionNLA.name)
                baction = False
            
            if baction == True:
                arm = amatureobject #set armature object
                if not arm.animation_data:
                    print("======================================")
                    print("Check Animation Data: None")
                    print("Armature has no animation, skipping...")
                    print("======================================")
                    break
                    
                if not arm.animation_data.action:
                    print("======================================")
                    print("Check Action: None")
                    print("Armature has no animation, skipping...")
                    print("======================================")
                    break
                arm.animation_data.action = ActionNLA
                act = arm.animation_data.action
                action_name = act.name
                
                if not len(act.fcurves):
                    print("//===========================================================")
                    print("// None bone pose set keys for this action set... skipping...")
                    print("//===========================================================")
                    bHaveAction = False
                    
                #this deal with action export control
                if bHaveAction == True:
                    
                    print("Action Name:",action_name)
                    #look for min and max frame that current set keys
                    framemin, framemax = act.frame_range
                    #print("max frame:",framemax)
                    start_frame = int(framemin)
                    end_frame = int(framemax)
                    scene_frames = range(start_frame, end_frame+1)
                    frame_count = len(scene_frames)
                    #===================================================
                    anim = AnimInfoBinary()
                    anim.Name = action_name
                    anim.Group = "" #what is group?
                    anim.NumRawFrames = frame_count
                    anim.AnimRate = anim_rate
                    anim.FirstRawFrame = cur_frame_index
                    #===================================================
                    count_previous_keys = len(psa_file.RawKeys.Data)
                    print("Frame Key Set Count:",frame_count, "Total Frame:",frame_count)
                    #print("init action bones...")
                    unique_bone_indexes = {}
                    # bone lookup table
                    bones_lookup =  {}
                
                    #build bone node for animation keys needed to be set
                    for bone in arm.data.bones:
                        bones_lookup[bone.name] = bone
                    #print("bone name:",bone.name)
                    frame_count = len(scene_frames)
                    #print ('Frame Count: %i' % frame_count)
                    pose_data = arm.pose
                
                    #these must be ordered in the order the bones will show up in the PSA file!
                    ordered_bones = {}
                    ordered_bones = sorted([(psa_file.UseBone(x.name), x) for x in pose_data.bones], key=operator.itemgetter(0))
                    
                    #############################
                    # ORDERED FRAME, BONE
                    #for frame in scene_frames:
                    
                    for i in range(frame_count):
                        frame = scene_frames[i]
                        #LOUD
                        #print ("==== outputting frame %i ===" % frame)
                        
                        if frame_count > i+1:
                            next_frame = scene_frames[i+1]
                            #print "This Frame: %i, Next Frame: %i" % (frame, next_frame)
                        else:
                            next_frame = -1
                            #print "This Frame: %i, Next Frame: NONE" % frame
                        
                        #frame start from 1 as number one from blender
                        blender_scene.frame_set(frame)
                        
                        cur_frame_index = cur_frame_index + 1
                        for bone_data in ordered_bones:
                            bone_index = bone_data[0]
                            pose_bone = bone_data[1]
                            #print("[=====POSE NAME:",pose_bone.name)
                            
                            #print("LENG >>.",len(bones_lookup))
                            blender_bone = bones_lookup[pose_bone.name]
                            
                            #just need the total unique bones used, later for this AnimInfoBinary
                            unique_bone_indexes[bone_index] = bone_index
                            #LOUD
                            #print ("-------------------", pose_bone.name)
                            head = pose_bone.head
                            
                            posebonemat = mathutils.Matrix(pose_bone.matrix)
                            parent_pose = pose_bone.parent
                            if parent_pose != None:
                                parentposemat = mathutils.Matrix(parent_pose.matrix)
                                #blender 2.4X it been flip around with new 2.50 (mat1 * mat2) should now be (mat2 * mat1)
                                posebonemat = parentposemat.invert() * posebonemat
                            head = posebonemat.to_translation()
                            quat = posebonemat.to_quaternion().normalize()
                            vkey = VQuatAnimKey()
                            vkey.Position.X = head.x
                            vkey.Position.Y = head.y
                            vkey.Position.Z = head.z
                            
                            if parent_pose != None:
                                quat = make_fquat(quat)
                            else:
                                quat = make_fquat_default(quat)
                            
                            vkey.Orientation = quat
                            #print("Head:",head)
                            #print("Orientation",quat)
                            
                            #time from now till next frame = diff / framesPerSec
                            if next_frame >= 0:
                                diff = next_frame - frame
                            else:
                                diff = 1.0
                            
                            #print ("Diff = ", diff)
                            vkey.Time = float(diff)/float(anim_rate)
                            
                            psa_file.AddRawKey(vkey)
                            
                    #done looping frames
                    #done looping armatures
                    #continue adding animInfoBinary counts here
                
                    anim.TotalBones = len(unique_bone_indexes)
                    print("Bones Count:",anim.TotalBones)
                    anim.TrackTime = float(frame_count) / anim.AnimRate
                    print("Time Track Frame:",anim.TrackTime)
                    psa_file.AddAnimation(anim)
        print("==== Finish Action Build(s) ====")
    else:
        print("Exporting one action:",bpy.context.scene.unrealactionexportall)
        #list of armature objects
        for arm in blender_armatures:
            #check if there animation data from armature or something
            
            if not arm.animation_data:
                print("======================================")
                print("Check Animation Data: None")
                print("Armature has no animation, skipping...")
                print("======================================")
                break
                
            if not arm.animation_data.action:
                print("======================================")
                print("Check Action: None")
                print("Armature has no animation, skipping...")
                print("======================================")
                break
            act = arm.animation_data.action
            #print(dir(act))
            action_name = act.name
            
            if not len(act.fcurves):
                print("//===========================================================")
                print("// None bone pose set keys for this action set... skipping...")
                print("//===========================================================")
                bHaveAction = False
                
            #this deal with action export control
            if bHaveAction == True:
                print("")
                print("==== Action Set ====")
                print("Action Name:",action_name)
                #look for min and max frame that current set keys
                framemin, framemax = act.frame_range
                #print("max frame:",framemax)
                start_frame = int(framemin)
                end_frame = int(framemax)
                scene_frames = range(start_frame, end_frame+1)
                frame_count = len(scene_frames)
                #===================================================
                anim = AnimInfoBinary()
                anim.Name = action_name
                anim.Group = "" #what is group?
                anim.NumRawFrames = frame_count
                anim.AnimRate = anim_rate
                anim.FirstRawFrame = cur_frame_index
                #===================================================
                count_previous_keys = len(psa_file.RawKeys.Data)
                print("Frame Key Set Count:",frame_count, "Total Frame:",frame_count)
                #print("init action bones...")
                unique_bone_indexes = {}
                # bone lookup table
                bones_lookup =  {}
            
                #build bone node for animation keys needed to be set
                for bone in arm.data.bones:
                    bones_lookup[bone.name] = bone
                #print("bone name:",bone.name)
                frame_count = len(scene_frames)
                #print ('Frame Count: %i' % frame_count)
                pose_data = arm.pose
            
                #these must be ordered in the order the bones will show up in the PSA file!
                ordered_bones = {}
                ordered_bones = sorted([(psa_file.UseBone(x.name), x) for x in pose_data.bones], key=operator.itemgetter(0))
                
                #############################
                # ORDERED FRAME, BONE
                #for frame in scene_frames:
                
                for i in range(frame_count):
                    frame = scene_frames[i]
                    #LOUD
                    #print ("==== outputting frame %i ===" % frame)
                    
                    if frame_count > i+1:
                        next_frame = scene_frames[i+1]
                        #print "This Frame: %i, Next Frame: %i" % (frame, next_frame)
                    else:
                        next_frame = -1
                        #print "This Frame: %i, Next Frame: NONE" % frame
                    
                    #frame start from 1 as number one from blender
                    blender_scene.frame_set(frame)
                    
                    cur_frame_index = cur_frame_index + 1
                    for bone_data in ordered_bones:
                        bone_index = bone_data[0]
                        pose_bone = bone_data[1]
                        #print("[=====POSE NAME:",pose_bone.name)
                        
                        #print("LENG >>.",len(bones_lookup))
                        blender_bone = bones_lookup[pose_bone.name]
                        
                        #just need the total unique bones used, later for this AnimInfoBinary
                        unique_bone_indexes[bone_index] = bone_index
                        #LOUD
                        #print ("-------------------", pose_bone.name)
                        head = pose_bone.head
                        
                        posebonemat = mathutils.Matrix(pose_bone.matrix)
                        parent_pose = pose_bone.parent
                        if parent_pose != None:
                            parentposemat = mathutils.Matrix(parent_pose.matrix)
                            #blender 2.4X it been flip around with new 2.50 (mat1 * mat2) should now be (mat2 * mat1)
                            posebonemat = parentposemat.inverted() * posebonemat
                            #print("parentposemat ::::",parentposemat)
                        #print("parentposemat ::::",dir(posebonemat.to_quaternion()))
                        head = posebonemat.to_translation()
                        quat = posebonemat.to_quaternion().normalized()
                        #print("position :",posebonemat.to_translation(),"quat",posebonemat.to_quaternion().normalized())
                        #print("posebonemat",posebonemat)
                        vkey = VQuatAnimKey()
                        vkey.Position.X = head.x
                        vkey.Position.Y = head.y
                        vkey.Position.Z = head.z
                        #print("quat:",quat)
                        if parent_pose != None:
                            quat = make_fquat(quat)
                        else:
                            quat = make_fquat_default(quat)
                        
                        vkey.Orientation = quat
                        #print("Head:",head)
                        #print("Orientation",quat)
                        
                        #time from now till next frame = diff / framesPerSec
                        if next_frame >= 0:
                            diff = next_frame - frame
                        else:
                            diff = 1.0
                        
                        #print ("Diff = ", diff)
                        vkey.Time = float(diff)/float(anim_rate)
                        
                        psa_file.AddRawKey(vkey)
                        
                #done looping frames
                #done looping armatures
                #continue adding animInfoBinary counts here
            
                anim.TotalBones = len(unique_bone_indexes)
                print("Bones Count:",anim.TotalBones)
                anim.TrackTime = float(frame_count) / anim.AnimRate
                print("Time Track Frame:",anim.TrackTime)
                psa_file.AddAnimation(anim)
                print("==== Finish Action Build(s) ====")
    
exportmessage = "Export Finish" 

def meshmerge(selectedobjects):
    bpy.ops.object.mode_set(mode='OBJECT')
    cloneobjects = []
    if len(selectedobjects) > 1:
        print("selectedobjects:",len(selectedobjects))
        count = 0 #reset count
        for count in range(len( selectedobjects)):
            print("Index:",count)
            if selectedobjects[count] != None:
                me_da = selectedobjects[count].data.copy() #copy data
                me_ob = selectedobjects[count].copy() #copy object
                #note two copy two types else it will use the current data or mesh
                me_ob.data = me_da
                bpy.context.scene.objects.link(me_ob)#link the object to the scene #current object location
                print("clone object",me_ob.name)
                cloneobjects.append(me_ob)
        #bpy.ops.object.mode_set(mode='OBJECT')
        for i in bpy.data.objects: i.select = False #deselect all objects
        count = 0 #reset count
        #bpy.ops.object.mode_set(mode='OBJECT')
        for count in range(len( cloneobjects)):
            if count == 0:
                bpy.context.scene.objects.active = cloneobjects[count]
                print("Set Active Object:",cloneobjects[count].name)
            cloneobjects[count].select = True
        bpy.ops.object.join()
        return cloneobjects[0]
        
def fs_callback(filename, context):
    #this deal with repeat export and the reset settings
    global bonedata, BBCount, nbone, exportmessage,bDeleteMergeMesh
    bonedata = []#clear array
    BBCount = 0
    nbone = 0
    
    start_time = time.clock()
    
    print ("========EXPORTING TO UNREAL SKELETAL MESH FORMATS========\r\n")
    print("Blender Version:", bpy.app.version_string)
    
    psk = PSKFile()
    psa = PSAFile()
    
    #sanity check - this should already have the extension, but just in case, we'll give it one if it doesn't
    psk_filename = make_filename_ext(filename, '.psk')
    
    #make the psa filename
    psa_filename = make_filename_ext(filename, '.psa')
    
    print ('PSK File: ' +  psk_filename)
    print ('PSA File: ' +  psa_filename)
    
    barmature = True
    bmesh = True
    blender_meshes = []
    blender_armature = []
    selectmesh = []
    selectarmature = []
    
    current_scene = context.scene
    cur_frame = current_scene.frame_current #store current frame before we start walking them during animation parse
    objects = current_scene.objects
    
    print("Checking object count...")
    for next_obj in objects:
        if next_obj.type == 'MESH':
            blender_meshes.append(next_obj)
            if (next_obj.select):
                #print("mesh object select")
                selectmesh.append(next_obj)
        if next_obj.type == 'ARMATURE':
            blender_armature.append(next_obj)
            if (next_obj.select):
                #print("armature object select")
                selectarmature.append(next_obj)
    
    print("Mesh Count:",len(blender_meshes)," Armature Count:",len(blender_armature))
    print("====================================")
    print("Checking Mesh Condtion(s):")
    #if there 1 mesh in scene add to the array
    if len(blender_meshes) == 1:
        print(" - One Mesh Scene")
    #if there more than one mesh and one mesh select add to array
    elif (len(blender_meshes) > 1) and (len(selectmesh) == 1):
        blender_meshes = []
        blender_meshes.append(selectmesh[0])
        print(" - One Mesh [Select]")
    elif (len(blender_meshes) > 1) and (len(selectmesh) >= 1):
        #code build check for merge mesh before ops
        print("More than one mesh is selected!")
        centermesh = []
        notcentermesh = []
        countm = 0
        for countm in range(len(selectmesh)):
            #selectmesh[]
            if selectmesh[countm].location.x == 0 and selectmesh[countm].location.y == 0 and selectmesh[countm].location.z == 0:
                centermesh.append(selectmesh[countm])
            else:
                notcentermesh.append(selectmesh[countm])
        if len(centermesh) > 0:
            print("center object found")
            blender_meshes = []
            selectmesh = []
            countm = 0
            for countm in range(len(centermesh)):
                selectmesh.append(centermesh[countm])
            for countm in range(len(notcentermesh)):
                selectmesh.append(notcentermesh[countm])
            blender_meshes.append(meshmerge(selectmesh))
            bDeleteMergeMesh = True
        else:
            bDeleteMergeMesh = False
            bmesh = False
            print("center object not found")
    else:
        print(" - Too Many Meshes!")
        print(" - Select One Mesh Object!")
        bmesh = False
        bDeleteMergeMesh = False
		
    print("====================================")
    print("Checking Armature Condtion(s):")
    if len(blender_armature) == 1:
        print(" - One Armature Scene")
    elif (len(blender_armature) > 1) and (len(selectarmature) == 1):
        print(" - One Armature [Select]")
    else:
        print(" - Too Armature Meshes!")
        print(" - Select One Armature Object Only!")
        barmature = False
    bMeshScale = True
    bMeshCenter = True
    if len(blender_meshes) > 0:
        if blender_meshes[0].scale.x == 1 and blender_meshes[0].scale.y == 1 and blender_meshes[0].scale.z == 1:
            #print("Okay")
            bMeshScale = True
        else:
            print("Error, Mesh Object not scale right should be (1,1,1).")
            bMeshScale = False
        if blender_meshes[0].location.x == 0 and blender_meshes[0].location.y == 0 and blender_meshes[0].location.z == 0:
            #print("Okay")
            bMeshCenter = True
        else:
            print("Error, Mesh Object not center.",blender_meshes[0].location)
            bMeshCenter = False
    else:
        bmesh = False
    bArmatureScale = True
    bArmatureCenter = True
    if blender_armature[0] !=None:
        if blender_armature[0].scale.x == 1 and blender_armature[0].scale.y == 1 and blender_armature[0].scale.z == 1:
            #print("Okay")
            bArmatureScale = True
        else:
            print("Error, Armature Object not scale right should be (1,1,1).")            
            bArmatureScale = False
        if blender_armature[0].location.x == 0 and blender_armature[0].location.y == 0 and blender_armature[0].location.z == 0:
            #print("Okay")
            bArmatureCenter = True
        else:
            print("Error, Armature Object not center.",blender_armature[0].location)
            bArmatureCenter = False
			
		
			
    #print("location:",blender_armature[0].location.x)
    
    if (bmesh == False) or (barmature == False) or (bArmatureCenter == False) or (bArmatureScale == False)or (bMeshScale == False) or (bMeshCenter == False):
        exportmessage = "Export Fail! Check Log."
        print("=================================")
        print("= Export Fail!                  =")
        print("=================================")
    else:
        exportmessage = "Export Finish!"
        #print("blender_armature:",dir(blender_armature[0]))
        #print(blender_armature[0].scale)
        #need to build a temp bone index for mesh group vertex
        BoneIndexArmature(blender_armature)

        try:
            #######################
            # STEP 1: MESH DUMP
            # we build the vertexes, wedges, and faces in here, as well as a vertexgroup lookup table
            # for the armature parse
            print("//===============================")
            print("// STEP 1")
            print("//===============================")
            parse_meshes(blender_meshes, psk)
        except:
            context.scene.frame_set(cur_frame) #set frame back to original frame
            print ("Exception during Mesh Parse")
            raise
        
        try:
            #######################
            # STEP 2: ARMATURE DUMP
            # IMPORTANT: do this AFTER parsing meshes - we need to use the vertex group data from 
            # the mesh parse in here to generate bone influences
            print("//===============================")
            print("// STEP 2")
            print("//===============================")
            parse_armature(blender_armature, psk, psa) 
            
        except:
            context.scene.frame_set(cur_frame) #set frame back to original frame
            print ("Exception during Armature Parse")
            raise

        try:
            #######################
            # STEP 3: ANIMATION DUMP
            # IMPORTANT: do AFTER parsing bones - we need to do bone lookups in here during animation frames
            print("//===============================")
            print("// STEP 3")
            print("//===============================")
            parse_animation(current_scene, blender_armature, psa) 
            
        except:
            context.scene.frame_set(cur_frame) #set frame back to original frame
            print ("Exception during Animation Parse")
            raise

        # reset current frame
        
        context.scene.frame_set(cur_frame) #set frame back to original frame
        
        ##########################
        # FILE WRITE
        print("//===========================================")
        print("// bExportPsk:",bpy.context.scene.unrealexportpsk," bExportPsa:",bpy.context.scene.unrealexportpsa)
        print("//===========================================")
        if bpy.context.scene.unrealexportpsk == True:
            print("Writing Skeleton Mesh Data...")
            #RG - dump psk file
            psk.PrintOut()
            file = open(psk_filename, "wb") 
            file.write(psk.dump())
            file.close() 
            print ("Successfully Exported File: " + psk_filename)
        if bpy.context.scene.unrealexportpsa == True:
            print("Writing Animaiton Data...")
            #RG - dump psa file
            if not psa.IsEmpty():
                psa.PrintOut()
                file = open(psa_filename, "wb") 
                file.write(psa.dump())
                file.close() 
                print ("Successfully Exported File: " + psa_filename)
            else:
                print ("No Animations (.psa file) to Export")

        print ('PSK/PSA Export Script finished in %.2f seconds' % (time.clock() - start_time))
        print( "Current Script version: ",bl_info['version'])
        #MSG BOX EXPORT COMPLETE
        #...

        #DONE
        print ("PSK/PSA Export Complete")

def write_data(path, context):
    print("//============================")
    print("// running psk/psa export...")
    print("//============================")
    fs_callback(path, context)
    pass

from bpy.props import *

exporttypedata = []

# [index,text field,0] #or something like that
exporttypedata.append(("0","PSK","Export PSK"))
exporttypedata.append(("1","PSA","Export PSA"))
exporttypedata.append(("2","ALL","Export ALL"))

bpy.types.Scene.unrealfpsrate = IntProperty(
    name="fps rate",
    description="Set the frame per second (fps) for unreal.",
    default=24,min=1,max=100)
    
bpy.types.Scene.unrealexport_settings = EnumProperty(
    name="Export:",
    description="Select a export settings (psk/psa/all)...",
    items = exporttypedata, default = '0')
        
bpy.types.Scene.unrealtriangulatebool = BoolProperty(
    name="Triangulate Mesh",
    description="Convert Quad to Tri Mesh Boolean...",
    default=False)
    
bpy.types.Scene.unrealactionexportall = BoolProperty(
    name="All Actions",
    description="This let you export all the actions from current armature that matches bone name in action groups names.",
    default=False)

bpy.types.Scene.unrealdisplayactionsets = BoolProperty(
    name="Show Action Set(s)",
    description="Display Action Sets Information.",
    default=False)    
    
bpy.types.Scene.unrealexportpsk = BoolProperty(
    name="bool export psa",
    description="bool for exporting this psk format",
    default=True)
    
bpy.types.Scene.unrealexportpsa = BoolProperty(
    name="bool export psa",
    description="bool for exporting this psa format",
    default=True)

class ExportUDKAnimData(bpy.types.Operator):
    global exportmessage
    '''Export Skeleton Mesh / Animation Data file(s)'''
    bl_idname = "export_anim.udk" # this is important since its how bpy.ops.export.udk_anim_data is constructed
    bl_label = "Export PSK/PSA"
    __doc__ = "One mesh and one armature else select one mesh or armature to be exported."

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.

    filepath = StringProperty(name="File Path", description="Filepath used for exporting the PSA file", maxlen= 1024, default= "", subtype='FILE_PATH')
    pskexportbool = BoolProperty(name="Export PSK", description="Export Skeletal Mesh", default= True)
    psaexportbool = BoolProperty(name="Export PSA", description="Export Action Set (Animation Data)", default= True)
    actionexportall = BoolProperty(name="All Actions", description="This will export all the actions that matches the current armature.", default=False)

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        #check if  skeleton mesh is needed to be exported
        if (self.pskexportbool):
            bpy.context.scene.unrealexportpsk = True
        else:
            bpy.context.scene.unrealexportpsk = False
        #check if  animation data is needed to be exported
        if (self.psaexportbool):
            bpy.context.scene.unrealexportpsa = True
        else:
            bpy.context.scene.unrealexportpsa = False
            
        if (self.actionexportall):
            bpy.context.scene.unrealactionexportall = True
        else:
            bpy.context.scene.unrealactionexportall = False
        
        write_data(self.filepath, context)
        
        self.report({'WARNING', 'INFO'}, exportmessage)
        return {'FINISHED'}
        
    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

class VIEW3D_PT_unrealtools_objectmode(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label = "Unreal Tools"
    
    @classmethod
    def poll(cls, context):
        return context.active_object

    def draw(self, context):
        layout = self.layout
        rd = context.scene
        layout.prop(rd, "unrealexport_settings",expand=True)        
        #layout.operator("object.UnrealExport")#button#blender 2.55 version
        layout.operator(OBJECT_OT_UnrealExport.bl_idname)#button blender #2.56 version
        #print("Button Name:",OBJECT_OT_UnrealExport.bl_idname) #2.56 version
        #FPS #it use the real data from your scene
        layout.prop(rd.render, "fps")
        
        layout.prop(rd, "unrealactionexportall")
        layout.prop(rd, "unrealdisplayactionsets")
        #print("unrealdisplayactionsets:",rd.unrealdisplayactionsets)
        if rd.unrealdisplayactionsets:
            layout.label(text="Total Action Set(s):" + str(len(bpy.data.actions)))
		    #armature data
            amatureobject = None
            bonenames = [] #bone name of the armature bones list 
            #layout.label(text="object(s):" + str(len(bpy.data.objects)))
            
            for obj in bpy.data.objects:
                if obj.type == 'ARMATURE' and obj.select == True:
                    #print(dir(obj))
                    amatureobject = obj
                    break
                elif obj.type == 'ARMATURE':
                    amatureobject = obj
        
            if amatureobject != None:
                layout.label(text="Armature: " + amatureobject.name)
                #print("Armature:",amatureobject.name)
                boxactionset = layout.box()
                for bone in amatureobject.pose.bones:
                    bonenames.append(bone.name)
                actionsetmatchcount = 0	
                for ActionNLA in bpy.data.actions:
                    nobone = 0
                    for group in ActionNLA.groups:	
                        for abone in bonenames:
                            #print("name:>>",abone)
                            if abone == group.name:
                                nobone += 1
                                break
                    if (len(ActionNLA.groups) == len(bonenames)) and (nobone == len(ActionNLA.groups)):
                        actionsetmatchcount += 1
                        #print("Action Set match: Pass")
                        boxactionset.label(text="Action Name: " + ActionNLA.name)
                layout.label(text="Match Found: " + str(actionsetmatchcount))
		
        #row = layout.row()
        #row.label(text="Action Set(s)(not build)")
        #for action in  bpy.data.actions:
            #print(dir( action))
            #print(action.frame_range)
            #row = layout.row()
            #row.prop(action, "name")
            
            #print(dir(action.groups[0]))
            #for g in action.groups:#those are bones
                #print("group...")
                #print(dir(g))
                #print("////////////")
                #print((g.name))
                #print("////////////")
            
            #row.label(text="Active:" + action.select)
        btrimesh = False
        
class OBJECT_OT_UnrealExport(bpy.types.Operator):
    global exportmessage
    bl_idname = "export_mesh.udk"  # XXX, name???
    bl_label = "Unreal Export"
    __doc__ = "Select export setting for .psk/.psa or both."
    
    def invoke(self, context, event):
        print("Init Export Script:")
        if(int(bpy.context.scene.unrealexport_settings) == 0):
            bpy.context.scene.unrealexportpsk = True
            bpy.context.scene.unrealexportpsa = False
            print("Exporting PSK...")
        if(int(bpy.context.scene.unrealexport_settings) == 1):
            bpy.context.scene.unrealexportpsk = False
            bpy.context.scene.unrealexportpsa = True
            print("Exporting PSA...")
        if(int(bpy.context.scene.unrealexport_settings) == 2):
            bpy.context.scene.unrealexportpsk = True
            bpy.context.scene.unrealexportpsa = True
            print("Exporting ALL...")

        default_path = os.path.splitext(bpy.data.filepath)[0] + ".psk"
        fs_callback(default_path, bpy.context)
        
        #self.report({'WARNING', 'INFO'}, exportmessage)
        self.report({'INFO'}, exportmessage)
        return{'FINISHED'}    

def menu_func(self, context):
    #bpy.context.scene.unrealexportpsk = True
    #bpy.context.scene.unrealexportpsa = True
    default_path = os.path.splitext(bpy.data.filepath)[0] + ".psk"
    self.layout.operator(ExportUDKAnimData.bl_idname, text="Skeleton Mesh / Animation Data (.psk/.psa)").filepath = default_path

def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_export.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_export.remove(menu_func)

if __name__ == "__main__":
    register()
