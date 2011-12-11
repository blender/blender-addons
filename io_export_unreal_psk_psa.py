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
    "name": "Export Unreal Engine Format(.psk/.psa)",
    "author": "Darknet/Optimus_P-Fat/Active_Trash/Sinsoft/VendorX",
    "version": (2, 4),
    "blender": (2, 6, 0),
    "api": 36079,
    "location": "File > Export > Skeletal Mesh/Animation Data (.psk/.psa)",
    "description": "Export Skeleletal Mesh/Animation Data",
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
import bpy
import mathutils
import random
import operator

from struct import pack

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

# ======================================================================
# TODO: remove this 1am hack
nbone = 0
bDeleteMergeMesh = False
exportmessage = "Export Finish" 

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
        data = pack('64s64siiiifffiii', str.encode(self.Name), str.encode(self.Group), self.TotalBones, self.RootInclude, self.KeyCompressionStyle, self.KeyQuotum, self.KeyPrediction, self.TrackTime, self.AnimRate, self.StartBone, self.FirstRawFrame, self.NumRawFrames)
        return data

class VChunkHeader:
    def __init__(self, name, type_size):
        self.ChunkID = str.encode(name) # length=20
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
        print("DATA MATERIAL:",self.MaterialName)
        data = pack('64siLiLii', str.encode(self.MaterialName), self.TextureIndex, self.PolyFlags, self.AuxMaterial, self.AuxFlags, self.LodBias, self.LodStyle)
        return data

class VBone:
    def __init__(self):
        self.Name = "" # length = 64
        self.Flags = 0 # DWORD
        self.NumChildren = 0
        self.ParentIndex = 0
        self.BonePos = VJointPos()
        
    def dump(self):
        data = pack('64sLii', str.encode(self.Name), self.Flags, self.NumChildren, self.ParentIndex) + self.BonePos.dump()
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
        data = pack('64sLii', str.encode(self.Name), self.Flags, self.NumChildren, self.ParentIndex) + self.BonePos.dump()
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
    global bDeleteMergeMesh
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
        if bDeleteMergeMesh == True:
            print("Remove Merge tmp Mesh [ " ,object.name, " ] from scene!" )
            bpy.ops.object.mode_set(mode='OBJECT') # set it in object
            bpy.context.scene.objects.unlink(object)
    else:
        bpy.context.scene.unrealtriangulatebool = False
        print("No need to convert tri mesh.")
        me_ob = object
    return me_ob

# Actual object parsing functions
def parse_meshes(blender_meshes, psk_file):
    #this is use to call the bone name and the index array for group index matches
    global bDeleteMergeMesh
    print ("----- parsing meshes -----")
    print("Number of Object Meshes:",len(blender_meshes))
    for current_obj in blender_meshes: #number of mesh that should be one mesh here
        #bpy.ops.object.mode_set(mode='EDIT')
        current_obj = triangulateNMesh(current_obj)
        #print(dir(current_obj))
        print("Mesh Name:",current_obj.name)
        current_mesh = current_obj.data
        
        #collect a list of the material names
        print("== MATERIAL EXPORT LIST & INDEX")
        if len(current_obj.material_slots) > 0:
            counter = 0
            
            while counter < len(current_obj.material_slots):
                print("[MATERIAL IDX:",counter,"=]")
                MaterialName.append(current_obj.material_slots[counter].name)
                #print("Material Name:",current_obj.material_slots[counter].name)
                #print("Material Name:",dir(current_obj.material_slots[counter].material))                
                #print("TEXTURE:",dir(current_obj.material_slots[counter].material.texture_slots[0].texture.image.filepath))
                #print("Imagepath:",(current_obj.material_slots[counter].material.texture_slots[0].texture.image.filepath))
                #print("TEXTURES:",len(current_obj.material_slots[counter].material.texture_slots))
                #while slot in current_obj.material_slots[counter].material.texture_slots:
                    #print(dir(slot))
                    #if slot.texture.image.filepath != None:
                        #print("file path:",slot.texture.image.filepath)
                if current_obj.material_slots[counter].material.texture_slots[0] != None:
                    if current_obj.material_slots[counter].material.texture_slots[0].texture.image.filepath != None:
                        print("TEXTURE PATH:",current_obj.material_slots[counter].material.texture_slots[0].texture.image.filepath)
                #print("Imagepath:",(current_obj.material_slots[counter].material.texture_slots[0].texture.image.filepath_raw))
                #print("Imagepath2:",dir(current_obj.material_slots[counter].material.texture_slots[0].texture.image))				
                #create the current material
                matdata = psk_file.GetMatByIndex(counter)
                matdata.MaterialName = current_obj.material_slots[counter].name
                matdata.TextureIndex = counter
                matdata.AuxMaterial = counter
                #print("materials: ",MaterialName[counter])
                counter += 1
                print("PSK INDEX:",matdata.TextureIndex)
                print("=====")
                print("")
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
                psk_file.GetMatByIndex(object_material_index)

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
                    #check if limit boolean
                    #if value is over the set limit it will null the uv texture
                    if bpy.context.scene.limituv:
                        if (uv[0] > 1):
                            uv[0] = 1
                        if (uv[0] < 0):
                            uv[0] = 0
                        if (uv[1] > 1):
                            uv[1] = 1
                        if (uv[1] < 0):
                            uv[1] = 0
                        #print("limited on")
                    #else:
                        #print("limited off")
                    
                    # RE - Append untransformed vector (for normal calc below)
                    # TODO: convert to Blender.Mathutils
                    vect_list.append(FVector(vert.co.x, vert.co.y, vert.co.z))
                    
                    # Transform position for export
                    #vpos = vert.co * object_material_index
                    vpos = current_obj.matrix_local * vert.co
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
                #print("smooth:",(current_face.use_smooth))
                #not sure if this right
                #tri.SmoothingGroups
                if current_face.use_smooth == True:
                    tri.SmoothingGroups = 1
                else:
                    tri.SmoothingGroups = 0
                #tri.SmoothingGroups = 1
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

        #vertex group
        for obvgroup in current_obj.vertex_groups:
            #print("bone gourp build:",obvgroup.name)#print bone name
            #print(dir(obvgroup))
            vert_list = []
            for current_vert in current_mesh.vertices:
                #print("INDEX V:",current_vert.index)
                vert_index = current_vert.index
                for vgroup in current_vert.groups:#vertex groupd id
                    vert_weight = vgroup.weight
                    if(obvgroup.index == vgroup.group):
                        p = VPoint()
                        vpos = current_obj.matrix_local * current_vert.co
                        p.Point.X = vpos.x
                        p.Point.Y = vpos.y 
                        p.Point.Z = vpos.z
                        #print(current_vert.co)
                        point_index = points.get(p) #point index
                        v_item = (point_index, vert_weight)
                        vert_list.append(v_item)
            #bone name, [point id and wieght]
            #print("Add Vertex Group:",obvgroup.name, " No. Points:",len(vert_list))
            psk_file.VertexGroups[obvgroup.name] = vert_list
        
        #unrealtriangulatebool #this will remove the mesh from the scene
        '''
        if (bpy.context.scene.unrealtriangulatebool == True) and (bDeleteMergeMesh == True):
            #if bDeleteMergeMesh == True:
            #    print("Removing merge mesh.")
            print("Remove tmp Mesh [ " ,current_obj.name, " ] from scene >"  ,(bpy.context.scene.unrealtriangulatebool ))
            bpy.ops.object.mode_set(mode='OBJECT') # set it in object
            bpy.context.scene.objects.unlink(current_obj)
        el
        '''
        if bDeleteMergeMesh == True:
            print("Remove Merge tmp Mesh [ " ,current_obj.name, " ] from scene >"  ,(bpy.context.scene.unrealtriangulatebool ))
            bpy.ops.object.mode_set(mode='OBJECT') # set it in object
            bpy.context.scene.objects.unlink(current_obj)
        elif bpy.context.scene.unrealtriangulatebool == True:
            print("Remove tri tmp Mesh [ " ,current_obj.name, " ] from scene >"  ,(bpy.context.scene.unrealtriangulatebool ))
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
        parent_head = quat_parent * child_parent.head
        parent_tail = quat_parent * child_parent.tail
        
        set_position = (parent_tail - parent_head) + blender_bone.head
    else:
        # ROOT BONE
        #This for root 
        set_position = parent_matrix * blender_bone.head #ARMATURE OBJECT Locction
        rot_mat = blender_bone.matrix * parent_matrix.to_3x3() #ARMATURE OBJECT Rotation
        #print(dir(rot_mat))
        
        quat = make_fquat_default(rot_mat.to_quaternion())
        
    #print ("[[======= FINAL POSITION:", set_position)
    final_parent_id = parent_id
    
    #RG/RE -
    #if we are not separated by a small distance, create a dummy bone for the displacement
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
    if (bpy.context.scene.UEActionSetSettings == '1') or (bpy.context.scene.UEActionSetSettings == '2'):
        print("Action Set(s) Settings Idx:",bpy.context.scene.UEActionSetSettings)
        print("[==== Action list ====]")
        
        print("Number of Action set(s):",len(bpy.data.actions))
        
        for action in bpy.data.actions:#current number action sets
            print("+Action Name:",action.name)
            print("Group Count:",len(action.groups))
            #print("Groups:")
            #for bone in action.groups:
                #print("> Name: ",bone.name)
                #print(dir(bone))

        amatureobject = None #this is the armature set to none
        bonenames = [] #bone name of the armature bones list
        
        for arm in blender_armatures:
            amatureobject = arm
        #print(dir(amatureobject))
        collection = amatureobject.myCollectionUEA #collection of the object
        print("\n[==== Armature Object ====]")
        if amatureobject != None:
            print("+Name:",amatureobject.name)
            print("+Number of bones:", len(amatureobject.pose.bones),"\n")
            for bone in amatureobject.pose.bones:
                bonenames.append(bone.name)
        
        for ActionNLA in bpy.data.actions:
            FoundAction = True
            if bpy.context.scene.UEActionSetSettings == '2':                
                for c in collection:
                    if c.name == ActionNLA.name:
                        if c.mybool == True:
                            FoundAction = True
                        else:
                            FoundAction = False
                        break
                if FoundAction == False:
                    print("========================================")
                    print("Skipping Action Set!",ActionNLA.name)
                    print("Action Group Count:", len(ActionNLA.groups))
                    print("Bone Group Count:", len(amatureobject.pose.bones))
                    print("========================================")
                    #break
            
            nobone = 0
            nomatchbone = 0
			
            baction = True
            #print("\nChecking actions matching groups with bone names...")
            #Check if the bone names matches the action groups names
            print("=================================")
            print("=================================")
            for abone in bonenames:         
                #print("bone name:",abone)
                bfound = False
                for group in ActionNLA.groups:
                    #print("name:>>",abone)
                    if abone == group.name:
                        nobone += 1
                        bfound = True
                        break
                if bfound == False:
                    #print("Not Found!:",abone)
                    nomatchbone += 1
                #else:
                    #print("Found!:",abone)
            
            print("Armature Bones Count:",nobone , " Action Groups Counts:",len(ActionNLA.groups)," Left Out Count:",nomatchbone)
            #if the bones are less some missing bones that were added to the action group names than export this
            if (nobone <= len(ActionNLA.groups)) and (bpy.context.scene.unrealignoreactionmatchcount == True) :
                #print("Action Set match: Pass")
                print("Ingore Action groups Count from Armature bones.")
                baction = True
            #if action groups matches the bones length and names matching the gourps do something
            elif ((len(ActionNLA.groups) == len(bonenames)) and (nobone == len(ActionNLA.groups))):
                #print("Action Set match: Pass")
                baction = True
            else:
                print("Action Set match: Fail")
                #print("Action Name:",ActionNLA.name)
                baction = False
            
            if (baction == True) and (FoundAction == True):
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
                #print("Last Action Name:",arm.animation_data.action.name)
                arm.animation_data.action = ActionNLA
                #print("Set Action Name:",arm.animation_data.action.name)
                bpy.context.scene.update()
                act = arm.animation_data.action
                action_name = act.name
                
                if not len(act.fcurves):
                    print("//===========================================================")
                    print("// None bone pose set keys for this action set... skipping...")
                    print("//===========================================================")
                    bHaveAction = False
                    
                #this deal with action export control
                if bHaveAction == True:
                    #print("------------------------------------")
                    print("[==== Action Set ====]")
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
                    # count_previous_keys = len(psa_file.RawKeys.Data)  # UNUSED
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
                            # blender_bone = bones_lookup[pose_bone.name]  # UNUSED
                            
                            #just need the total unique bones used, later for this AnimInfoBinary
                            unique_bone_indexes[bone_index] = bone_index
                            #LOUD
                            #print ("-------------------", pose_bone.name)
                            head = pose_bone.head
                            
                            posebonemat = mathutils.Matrix(pose_bone.matrix)
                            #print(dir(posebonemat))

                            #print("quat",posebonemat)
                            #
                            # Error looop action get None in matrix
                            # looping on each armature give invert and normalize for None
                            #
                            parent_pose = pose_bone.parent
                            
                            if parent_pose != None:
                                parentposemat = mathutils.Matrix(parent_pose.matrix)
                                posebonemat = parentposemat.inverted() * posebonemat
                                    
                            head = posebonemat.to_translation()
                            quat = posebonemat.to_quaternion().normalized()

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
                print("------------------------------------\n")
            else:
                print("[==== Action Set ====]")
                print("Action Name:",ActionNLA.name)
                print("Action Group Count:", len(ActionNLA.groups))
                print("Bone Group Count:", len(amatureobject.pose.bones))
                print("Action set Skip!")
                print("------------------------------------\n")
        print("==== Finish Action Build(s) ====")
    else:
        print("[==== Action Set Single Export====]")
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
                print("---- Action Start ----")
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
                # count_previous_keys = len(psa_file.RawKeys.Data)  # UNUSED
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
                        # blender_bone = bones_lookup[pose_bone.name]  # UNUSED
                        
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
                        head = posebonemat.to_translation()
                        quat = posebonemat.to_quaternion().normalized()
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
                print("---- Action End ----")
                print("==== Finish Action Build ====")
    
def meshmerge(selectedobjects):
    bpy.ops.object.mode_set(mode='OBJECT')
    cloneobjects = []
    if len(selectedobjects) > 1:
        print("selectedobjects:",len(selectedobjects))
        count = 0 #reset count
        for count in range(len( selectedobjects)):
            #print("Index:",count)
            if selectedobjects[count] != None:
                me_da = selectedobjects[count].data.copy() #copy data
                me_ob = selectedobjects[count].copy() #copy object
                #note two copy two types else it will use the current data or mesh
                me_ob.data = me_da
                bpy.context.scene.objects.link(me_ob)#link the object to the scene #current object location
                print("Index:",count,"clone object",me_ob.name)
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
    global nbone, exportmessage, bDeleteMergeMesh
    nbone = 0
    
    start_time = time.clock()
    
    print ("========EXPORTING TO UNREAL SKELETAL MESH FORMATS========\r\n")
    print("Blender Version:", bpy.app.version[1],"-")
    
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
            print("Center Object Found!")
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
            print("Center Object Not Found")
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
    if blender_armature and blender_armature[0] is not None:
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

bpy.types.Scene.unrealfpsrate = IntProperty(
    name="fps rate",
    description="Set the frame per second (fps) for unreal",
    default=24,min=1,max=100)
    
bpy.types.Scene.unrealexport_settings = EnumProperty(
    name="Export:",
    description="Select a export settings (psk/psa/all)...",
    items = [("0","PSK","Export PSK"),
             ("1","PSA","Export PSA"),
             ("2","ALL","Export ALL")],
    default = '0')

bpy.types.Scene.UEActionSetSettings = EnumProperty(
    name="Action Set(s) Export Type",
    description="For Exporting Single, All, and Select Action Set(s)",
    items = [("0","Single","Single Action Set Export"),
             ("1","All","All Action Sets Export"),
             ("2","Select","Select Action Set(s) Export")],
    default = '0')        

bpy.types.Scene.unrealtriangulatebool = BoolProperty(
    name="Triangulate Mesh",
    description="Convert Quad to Tri Mesh Boolean...",
    default=False)

bpy.types.Scene.unrealignoreactionmatchcount = BoolProperty(
    name="Acion Group Ignore Count",
    description="It will ingore Action group count as long is matches the " \
                "Armature bone count to match and over ride the armature " \
                "animation data",
    default=False)
    
bpy.types.Scene.unrealdisplayactionsets = BoolProperty(
    name="Show Action Set(s)",
    description="Display Action Sets Information",
    default=False)    
    
bpy.types.Scene.unrealexportpsk = BoolProperty(
    name="bool export psa",
    description="bool for exporting this psk format",
    default=True)
    
bpy.types.Scene.unrealexportpsa = BoolProperty(
    name="bool export psa",
    description="bool for exporting this psa format",
    default=True)

bpy.types.Scene.limituv = BoolProperty(
    name="bool limit UV",
    description="limit UV co-ordinates to [0-1]",
    default=False)
	
class UEAPropertyGroup(bpy.types.PropertyGroup):
    ## create Properties for the collection entries:
    mystring = bpy.props.StringProperty()
    mybool = bpy.props.BoolProperty(
        name="Export",
        description="Check if you want to export the action set",
        default = False)

bpy.utils.register_class(UEAPropertyGroup)

## create CollectionProperty and link it to the property class
bpy.types.Object.myCollectionUEA = bpy.props.CollectionProperty(type = UEAPropertyGroup)
bpy.types.Object.myCollectionUEA_index = bpy.props.IntProperty(min = -1, default = -1)

## create operator to add or remove entries to/from  the Collection
class OBJECT_OT_add_remove_Collection_Items_UE(bpy.types.Operator):
    bl_label = "Add or Remove"
    bl_idname = "collection.add_remove_ueactions"
    __doc__ = """Button for Add, Remove, Refresh Action Set(s) list."""
    set = bpy.props.StringProperty()
 
    def invoke(self, context, event):
        obj = context.object
        collection = obj.myCollectionUEA
        if self.set == "remove":
            print("remove")
            index = obj.myCollectionUEA_index
            collection.remove(index)       # This remove on item in the collection list function of index value
        if self.set == "add":
            print("add")
            added = collection.add()        # This add at the end of the collection list
            added.name = "Action"+ str(random.randrange(0, 101, 2))
        if self.set == "refresh":
            print("refresh")
            # ArmatureSelect = None  # UNUSED
            ActionNames = []
            BoneNames = []
            for obj in bpy.data.objects:
                if obj.type == 'ARMATURE' and obj.select == True:
                    print("Armature Name:",obj.name)
                    # ArmatureSelect = obj  # UNUSED
                    for bone in obj.pose.bones:
                        BoneNames.append(bone.name)
                    break
            actionsetmatchcount = 0	
            for ActionNLA in bpy.data.actions:
                nobone = 0
                for group in ActionNLA.groups:	
                    for abone in BoneNames:
                        if abone == group.name:
                            nobone += 1
                            break
                    if (len(ActionNLA.groups) == len(BoneNames)) and (nobone == len(ActionNLA.groups)):
                        actionsetmatchcount += 1
                        ActionNames.append(ActionNLA.name)
            #print(dir(collection))
            #print("collection:",len(collection))
            print("action list check")
            for action in ActionNames:
                BfoundAction = False
                #print("action:",action)
                for c in collection:
                    #print(c.name)
                    if c.name == action:
                        BfoundAction = True
                        break
                if BfoundAction == False:
                    added = collection.add()        # This add at the end of the collection list
                    added.name = action
        #print("finish...")
        return {'FINISHED'} 

class ExportUDKAnimData(bpy.types.Operator):
    global exportmessage
    '''Export Skeleton Mesh / Animation Data file(s)'''
    bl_idname = "export_anim.udk" # this is important since its how bpy.ops.export.udk_anim_data is constructed
    bl_label = "Export PSK/PSA"
    __doc__ = """One mesh and one armature else select one mesh or armature to be exported."""

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.

    filepath = StringProperty(
            subtype='FILE_PATH',
            )
    filter_glob = StringProperty(
            default="*.psk;*.psa",
            options={'HIDDEN'},
            )
    pskexportbool = BoolProperty(
            name="Export PSK",
            description="Export Skeletal Mesh",
            default= True,
            )
    psaexportbool = BoolProperty(
            name="Export PSA",
            description="Export Action Set (Animation Data)",
            default= True,
            )
    actionexportall = BoolProperty(
            name="All Actions",
            description="This will export all the actions that matches the " \
                        "current armature",
            default=False,
            )
    ignoreactioncountexportbool = BoolProperty(
            name="Ignore Action Group Count",
            description="It will ignore action group count but as long it " \
                        "matches the armature bone count to over ride the " \
                        "animation data",
            default= False,
            )
    limituvbool = BoolProperty(
            name="Limit UV Co-ordinates",
            description="Limit UV co-ordinates to [0-1]",
            default= False,
            ) 

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
            bpy.context.scene.UEActionSetSettings = '1'#export one action set
        else:
            bpy.context.scene.UEActionSetSettings = '0'#export all action sets
        
        if(self.ignoreactioncountexportbool):
            bpy.context.scene.unrealignoreactionmatchcount = True
        else:
            bpy.context.scene.unrealignoreactionmatchcount = False

        if(self.limituvbool):
            bpy.types.Scene.limituv = True
        else:
            bpy.types.Scene.limituv = False
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
        layout.prop(rd, "UEActionSetSettings")
        layout.prop(rd, "unrealignoreactionmatchcount")
        
        #FPS #it use the real data from your scene
        layout.prop(rd.render, "fps")
        layout.prop(rd, "limituv")
        layout.operator(OBJECT_OT_UnrealExport.bl_idname)
        
        layout.prop(rd, "unrealdisplayactionsets")
        
        ArmatureSelect = None
        for obj in bpy.data.objects:
            if obj.type == 'ARMATURE' and obj.select == True:
                #print("Armature Name:",obj.name)
                ArmatureSelect = obj
                break
        #display armature actions list
        if ArmatureSelect != None and rd.unrealdisplayactionsets == True:
            layout.label(("Selected: "+ArmatureSelect.name))
            row = layout.row()
            row.template_list(obj, "myCollectionUEA", obj, "myCollectionUEA_index")                        # This show list for the collection
            col = row.column(align=True)
            col.operator("collection.add_remove_ueactions", icon="ZOOMIN", text="").set = "add"            # This show a plus sign button
            col.operator("collection.add_remove_ueactions", icon="ZOOMOUT", text="").set = "remove"        # This show a minus sign button        
            col.operator("collection.add_remove_ueactions", icon="FILE_REFRESH", text="").set = "refresh"  # This show a refresh sign button
            
            ##change name of Entry:
            if obj.myCollectionUEA:
                entry = obj.myCollectionUEA[obj.myCollectionUEA_index]
                layout.prop(entry, "name")
                layout.prop(entry, "mybool")
        layout.operator(OBJECT_OT_UTSelectedFaceSmooth.bl_idname)        
        layout.operator(OBJECT_OT_UTRebuildArmature.bl_idname)
        layout.operator(OBJECT_OT_UTRebuildMesh.bl_idname)
        layout.operator(OBJECT_OT_ToggleConsle.bl_idname)
        layout.operator(OBJECT_OT_DeleteActionSet.bl_idname)
        layout.operator(OBJECT_OT_MeshClearWeights.bl_idname)
        
class OBJECT_OT_UnrealExport(bpy.types.Operator):
    global exportmessage
    bl_idname = "export_mesh.udk"  # XXX, name???
    bl_label = "Unreal Export"
    __doc__ = """Select export setting for .psk/.psa or both."""
    
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

class OBJECT_OT_ToggleConsle(bpy.types.Operator):
    global exportmessage
    bl_idname = "object.toggleconsle"  # XXX, name???
    bl_label = "Toggle Console"
    __doc__ = "Show or Hide Console."
    
    def invoke(self, context, event):
        bpy.ops.wm.console_toggle()
        return{'FINISHED'} 

class OBJECT_OT_UTSelectedFaceSmooth(bpy.types.Operator):
    bl_idname = "object.utselectfacesmooth"  # XXX, name???
    bl_label = "Select Smooth faces"
    __doc__ = """It will only select smooth faces that is select mesh."""
    
    def invoke(self, context, event):
        print("----------------------------------------")
        print("Init Select Face(s):")
        bselected = False
        for obj in bpy.data.objects:
            if obj.type == 'MESH' and obj.select == True:
                smoothcount = 0
                flatcount = 0
                bpy.ops.object.mode_set(mode='OBJECT')#it need to go into object mode to able to select the faces
                for i in bpy.context.scene.objects: i.select = False #deselect all objects
                obj.select = True #set current object select
                bpy.context.scene.objects.active = obj #set active object
                for face in obj.data.faces:
                    if face.use_smooth == True:
                        face.select = True
                        smoothcount += 1
                    else:
                        flatcount += 1
                        face.select = False
                    #print("selected:",face.select)
                    #print(("smooth:",face.use_smooth))
                bpy.context.scene.update()
                bpy.ops.object.mode_set(mode='EDIT')
                print("Select Smooth Count(s):",smoothcount," Flat Count(s):",flatcount)
                bselected = True
                break
        if bselected:
            print("Selected Face(s) Exectue!")
            self.report({'INFO'}, "Selected Face(s) Exectue!")
        else:
            print("Didn't select Mesh Object!")
            self.report({'INFO'}, "Didn't Select Mesh Object!")
        print("----------------------------------------")        
        return{'FINISHED'}
		
class OBJECT_OT_DeleteActionSet(bpy.types.Operator):
    bl_idname = "object.deleteactionset"  # XXX, name???
    bl_label = "Delete Action Set"
    __doc__ = """It will remove the first top of the index of the action list. Reload file to remove it. It used for unable to delete action set. """
    
    def invoke(self, context, event):
        if len(bpy.data.actions) > 0:
            for action in bpy.data.actions:
                print("Action:",action.name)
                action.user_clear()
                break
            #bpy.data.actions.remove(act)
        print("finish")
        return{'FINISHED'}
			
class OBJECT_OT_MeshClearWeights(bpy.types.Operator):
    bl_idname = "object.meshclearweights"  # XXX, name???
    bl_label = "Mesh Clear Weights"
    __doc__ = """Clear selected mesh vertex group weights for the bones. Be sure you unparent the armature."""
    
    def invoke(self, context, event):
        for obj in bpy.data.objects:
            if obj.type == 'MESH' and obj.select == True:
                for vg in obj.vertex_groups:
                    obj.vertex_groups.remove(vg)
                break			
        return{'FINISHED'}
		
class OBJECT_OT_UTRebuildArmature(bpy.types.Operator):
    bl_idname = "object.utrebuildarmature"  # XXX, name???
    bl_label = "Rebuild Armature"
    __doc__ = """If mesh is deform when importing to unreal engine try this. It rebuild the bones one at the time by select one armature object scrape to raw setup build. Note the scale will be 1:1 for object mode. To keep from deforming."""
    
    def invoke(self, context, event):
        print("----------------------------------------")
        print("Init Rebuild Armature...")
        bselected = False
        for obj in bpy.data.objects:
            if obj.type == 'ARMATURE' and obj.select == True:
                currentbone = [] #select armature for roll copy
                print("Armature Name:",obj.name)
                objectname = "ArmatureDataPSK"
                meshname ="ArmatureObjectPSK"
                armdata = bpy.data.armatures.new(objectname)
                ob_new = bpy.data.objects.new(meshname, armdata)
                bpy.context.scene.objects.link(ob_new)
                bpy.ops.object.mode_set(mode='OBJECT')
                for i in bpy.context.scene.objects: i.select = False #deselect all objects
                ob_new.select = True
                bpy.context.scene.objects.active = obj
                
                bpy.ops.object.mode_set(mode='EDIT')
                for bone in obj.data.edit_bones:
                    if bone.parent != None:
                        currentbone.append([bone.name,bone.roll])
                    else:
                        currentbone.append([bone.name,bone.roll])
                bpy.ops.object.mode_set(mode='OBJECT')
                for i in bpy.context.scene.objects: i.select = False #deselect all objects
                bpy.context.scene.objects.active = ob_new
                bpy.ops.object.mode_set(mode='EDIT')
                
                for bone in obj.data.bones:
                    bpy.ops.object.mode_set(mode='EDIT')
                    newbone = ob_new.data.edit_bones.new(bone.name)
                    newbone.head = bone.head_local
                    newbone.tail = bone.tail_local
                    for bonelist in currentbone:
                        if bone.name == bonelist[0]:
                            newbone.roll = bonelist[1]
                            break
                    if bone.parent != None:
                        parentbone = ob_new.data.edit_bones[bone.parent.name]
                        newbone.parent = parentbone
                print("Bone Count:",len(obj.data.bones))
                print("Hold Bone Count",len(currentbone))
                print("New Bone Count",len(ob_new.data.edit_bones))
                print("Rebuild Armture Finish:",ob_new.name)
                bpy.context.scene.update()
                bselected = True
                break
        if bselected:
            self.report({'INFO'}, "Rebuild Armature Finish!")
        else:
            self.report({'INFO'}, "Didn't Select Armature Object!")
        print("End of Rebuild Armature.")
        print("----------------------------------------")
        return{'FINISHED'}
		
# rounded the vert locations to save a bit of blurb.. change the round value or remove for accuracy i suppose
def rounded_tuple(tup):
    return tuple(round(value,4) for value in tup)
	
def unpack_list(list_of_tuples):
    l = []
    for t in list_of_tuples:
        l.extend(t)
    return l
	
class OBJECT_OT_UTRebuildMesh(bpy.types.Operator):
    bl_idname = "object.utrebuildmesh"  # XXX, name???
    bl_label = "Rebuild Mesh"
    __doc__ = """It rebuild the mesh from scrape from the selected mesh object. Note the scale will be 1:1 for object mode. To keep from deforming."""
    
    def invoke(self, context, event):
        print("----------------------------------------")
        print("Init Mesh Bebuild...")
        bselected = False
        for obj in bpy.data.objects:
            if obj.type == 'MESH' and obj.select == True:
                for i in bpy.context.scene.objects: i.select = False #deselect all objects
                obj.select = True
                bpy.context.scene.objects.active = obj
                bpy.ops.object.mode_set(mode='OBJECT')
                me_ob = bpy.data.meshes.new(("Re_"+obj.name))
                mesh = obj.data
                faces = []
                verts = []
                smoothings = []
                uvfaces = []
                #print(dir(mesh))
                print("creating array build mesh...")
                uv_layer = mesh.uv_textures.active
                for face in mesh.faces:
                    smoothings.append(face.use_smooth)#smooth or flat in boolean
                    if uv_layer != None:#check if there texture data exist
                        faceUV = uv_layer.data[face.index]
                        #print(len(faceUV.uv))
                        uvs = []
                        for uv in faceUV.uv:
                            #vert = mesh.vertices[videx]
                            #print("UV:",uv[0],":",uv[1])
                            uvs.append((uv[0],uv[1]))
                        #print(uvs)
                        uvfaces.append(uvs)
                    faces.append(face.vertices[:])           
                #vertex positions
                for vertex in mesh.vertices:
                    verts.append(vertex.co.to_tuple())				
                #vertices weight groups into array
                vertGroups = {} #array in strings
                for vgroup in obj.vertex_groups:
                    #print(dir(vgroup))
                    #print("name:",(vgroup.name),"index:",vgroup.index)
                    #vertex in index and weight
                    vlist = []
                    for v in mesh.vertices:
                        for vg in v.groups:
                            if vg.group == vgroup.index:
                                vlist.append((v.index,vg.weight))
                                #print((v.index,vg.weight))
                    vertGroups[vgroup.name] = vlist					
                '''
				#Fail for this method
				#can't covert the tri face plogyon
                for face in mesh.faces:
                    x = [f for f in face.vertices]
                    faces.extend(x)
                    smoothings.append(face.use_smooth)
                for vertex in mesh.vertices:
                    verts.append(vertex.co.to_tuple())
                me_ob.vertices.add(len(verts))
                me_ob.faces.add(len(faces)//4)
                me_ob.vertices.foreach_set("co", unpack_list(verts))
                me_ob.faces.foreach_set("vertices_raw", faces)
                me_ob.faces.foreach_set("use_smooth", smoothings)
                '''
                #test dummy mesh
                #verts = [(-1,1,0),(1,1,0),(1,-1,0),(-1,-1,0),(0,1,1),(0,-1,1)]
                #faces = [(0,1,2,3),(1,2,5,4),(0,3,5,4),(0,1,4),(2,3,5)]
                #for f in faces:
                    #print("face",f)
                #for v in verts:
                    #print("vertex",v)
                #me_ob = bpy.data.objects.new("ReBuildMesh",me_ob)
                print("creating mesh object...")
                me_ob.from_pydata(verts, [], faces)
                me_ob.faces.foreach_set("use_smooth", smoothings)#smooth array from face
                me_ob.update()
                #check if there is uv faces
                if len(uvfaces) > 0:
                    uvtex = me_ob.uv_textures.new(name="retex")
                    for i, face in enumerate(me_ob.faces):
                        blender_tface = uvtex.data[i] #face
                        mfaceuv = uvfaces[i]
                        if len(mfaceuv) == 3:
                            blender_tface.uv1 = mfaceuv[0];
                            blender_tface.uv2 = mfaceuv[1];
                            blender_tface.uv3 = mfaceuv[2];
                        if len(mfaceuv) == 4:
                            blender_tface.uv1 = mfaceuv[0];
                            blender_tface.uv2 = mfaceuv[1];
                            blender_tface.uv3 = mfaceuv[2];
                            blender_tface.uv4 = mfaceuv[3];
                
                obmesh = bpy.data.objects.new(("Re_"+obj.name),me_ob)
                bpy.context.scene.update()
                #Build tmp materials
                materialname = "ReMaterial"
                for matcount in mesh.materials:
                    matdata = bpy.data.materials.new(materialname)
                    me_ob.materials.append(matdata)
                #assign face to material id
                for face in mesh.faces:
                    #print(dir(face))
                    me_ob.faces[face.index].material_index = face.material_index
                #vertices weight groups
                for vgroup in vertGroups:
                    #print("vgroup",vgroup)#name of group
                    #print(dir(vgroup))
                    #print(vertGroups[vgroup])
                    group = obmesh.vertex_groups.new(vgroup)
                    #print("group index",group.index)
                    for v in vertGroups[vgroup]:
                        group.add([v[0]], v[1], 'ADD')# group.add(array[vertex id],weight,add)
                        #print("[vertex id, weight]",v) #array (0,0)
                        #print("[vertex id, weight]",v[0],":",v[1]) #array (0,0)
                bpy.context.scene.objects.link(obmesh)
                print("Mesh Material Count:",len(me_ob.materials))
                matcount = 0
                print("MATERIAL ID OREDER:")
                for mat in me_ob.materials:
                    print("-Material:",mat.name,"INDEX:",matcount)
                    matcount += 1
                print("")
                print("Object Name:",obmesh.name)
                bpy.context.scene.update()
                #bpy.ops.wm.console_toggle()
                bselected = True
                break
        if bselected:
            self.report({'INFO'}, "Rebuild Mesh Finish!")
            print("Finish Mesh Build...")
        else:
            self.report({'INFO'}, "Didn't Select Mesh Object!")
            print("Didn't Select Mesh Object!")
        print("----------------------------------------")
        
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
