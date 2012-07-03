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

bl_info = {
    "name": "Import Unreal Skeleton Mesh (.psk)",
    "author": "Darknet",
    "version": (2, 1),
    "blender": (2, 6, 3),
    "location": "File > Import > Skeleton Mesh (.psk)",
    "description": "Import Skeleleton Mesh",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
        "Scripts/Import-Export/Unreal_psk_psa",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=21366",
    "category": "Import-Export"}

"""
Version': '2.0' ported by Darknet

Unreal Tournament PSK file to Blender mesh converter V1.0
Author: 
-Darknet (Redesign and reworked)
-D.M. Sturgeon (camg188 at the elYsium forum)
-#2011-01-20 MARIUSZ SZKARADEK GLOGOW POLAND 

Imports a *psk file to a new mesh

-No UV Texutre
-No Weight
-No Armature Bones
-No Material ID
"""

import bpy
import bmesh
import mathutils
import math
from string import *
from struct import *
import struct
from math import *
from bpy.props import *
from bpy_extras.io_utils import unpack_list, unpack_face_list

Quaternion = mathutils.Quaternion

bpy.types.Scene.unrealbonesize = FloatProperty(
    name="Bone Length",
    description="Bone Length from head to tail distance",
    default=1,min=0.001,max=1000)

#output log in to txt file
DEBUGLOG = False

scale = 1.0
bonesize = 1.0
skala = 1
flipyz = False   
flipuv = True

#pack read words	
def word(long): 
   s=''
   for j in range(0,long): 
       lit =  struct.unpack('c',plik.read(1))[0]
       #print(">",lit)
       #print(">",bytes.decode(lit))
       if ord(lit)!=0:
           #print(lit)
           s+=bytes.decode(lit)
           if len(s)>100:
               break
   return s
#pack read data   
def b(n):
    return struct.unpack(n*'b', plik.read(n))
def B(n):
    return struct.unpack(n*'B', plik.read(n))
def h(n):
    return struct.unpack(n*'h', plik.read(n*2))
def H(n):
    return struct.unpack(n*'H', plik.read(n*2))
def i(n):
    return struct.unpack(n*'i', plik.read(n*4))
def f(n):
    return struct.unpack(n*'f', plik.read(n*4))

#work in progress
#bmesh
#tess function prefix
def drawmesh():
    global DEBUGLOG, plik,vertexes,uvcoord,faceslist,num_faces,facemat,facesmooth,m
    global vertexes_ids,bonesdata,meshesdata,groups,num_materials,skala,flipyz,flipuv,mat_faceslist
    global vertices,faces
    print(faces[0])
    print("[CREATING MESH:]")
    me_ob = bpy.data.meshes.new('testmesh')
    #create mesh
    print("-Vertices count:",len(vertices))
    me_ob.vertices.add(len(vertices))
    print("-Faces count:",len(faces))
    me_ob.tessfaces.add(len(faces))
    print("-Creating vertices points...")
    me_ob.vertices.foreach_set("co", unpack_list(vertices))
    print("-Creating faces idx...")
    me_ob.tessfaces.foreach_set("vertices_raw",unpack_list( faces))
    for face in me_ob.tessfaces:
        print(dir(face))
        face.use_smooth = facesmooth[face.index]
        #face.material_index = facemat[face.index]#not yet working
    print("-Creating UV Texture...")
    me_ob.tessface_uv_textures.new('uvtexture')
    #uvtex = me_ob.tessface_uv_textures[0]
    for uv in me_ob.tessface_uv_textures:
        for face in me_ob.tessfaces:
            #uv.data[face.index].uv1.x = 
            
            #print(uv.data[face.index].uv1)
            #uv.data[face.index].uv1 = Vector(uvcoord[faces[face.index]][0],uvcoord[face.index][1])
            print(face.vertices_raw[0],face.vertices_raw[1],face.vertices_raw[2])
            uv.data[face.index].uv1 = mathutils.Vector((uvcoord[face.vertices_raw[0]][0],uvcoord[face.vertices_raw[0]][1]))
            uv.data[face.index].uv2 = mathutils.Vector((uvcoord[face.vertices_raw[1]][0],uvcoord[face.vertices_raw[1]][1]))
            uv.data[face.index].uv3 = mathutils.Vector((uvcoord[face.vertices_raw[2]][0],uvcoord[face.vertices_raw[2]][1]))

    ob = bpy.data.objects.new("TestObject",me_ob)
    #create vertex group
    for bone_id in range(len(bonesdata)):
        bonedata = bonesdata[str(bone_id)]
        namebone = bonedata[0]#.strip()[-25:]
        #print("NAME:",namebone)
        ob.vertex_groups.new(namebone)
    me_ob.update()
    bpy.context.scene.objects.link(ob) 

#Create Armature
def check_armature():
    global DEBUGLOG, plik,vertexes,uvcoord,faceslist,num_faces,facemat,facesmooth,m
    global vertexes_ids,bonesdata,meshesdata,groups,num_materials,skala,flipyz,flipuv,amt
    
    #create Armature
    bpy.ops.object.mode_set(mode='OBJECT')
    for i in bpy.context.scene.objects: i.select = False #deselect all objects

    bpy.ops.object.add(
     type='ARMATURE', 
     enter_editmode=True,
     location=(0,0,0))
    ob = bpy.context.object
    ob.show_x_ray = True
    ob.name = "ARM"
    amt = ob.data
    amt.name = 'Amt'
    amt.show_axes = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.update()
#Create bones
def make_bone():    
    global DEBUGLOG, plik,vertexes,uvcoord,faceslist,num_faces,facemat,facesmooth,m
    global vertexes_ids,bonesdata,meshesdata,groups,num_materials,skala,flipyz,flipuv,amt
    global bonenames
    bonenames = []
    
    print ('make bone')
    
    for bone_id in range(len(bonesdata)):
       bonedata = bonesdata[str(bone_id)]
       namebone = bonedata[0]#.strip()[-25:]
       newbone = amt.edit_bones.new(namebone)
       #those are need to show in the scene
       newbone.head = (0,0,0)
       newbone.tail = (0,0,1)
       bonenames.append(namebone)
    bpy.context.scene.update()
#Make bone parent
def make_bone_parent():    
    global DEBUGLOG, plik,vertexes,uvcoord,faceslist,num_faces,facemat,facesmooth,m
    global vertexes_ids,bonesdata,meshesdata,groups,num_materials,skala,flipyz,flipuv,amt    
    global children
    children = {}
    
    print ('make bone parent')
    for bone_id in range(len(bonesdata)):
        bonedata = bonesdata[str(bone_id)]
        namebone  = bonenames[bone_id]
        nameparent = bonenames[bonedata[1][2]]
        #print(nameparent)
        if nameparent != None:#make sure it has name
           parentbone = amt.edit_bones[nameparent]
           bonecurrnet = amt.edit_bones[namebone]
           bonecurrnet.parent = parentbone
    bpy.context.scene.update()

#make bone martix set    
def bones_matrix():    
    global DEBUGLOG, plik,vertexes,uvcoord,faceslist,num_faces,facemat,facesmooth,m
    global vertexes_ids,bonesdata,meshesdata,groups,num_materials,skala,flipyz,flipuv,amt
    
    for bone_id in range(len(bonesdata)):
        bonedata = bonesdata[str(bone_id)]
        namebone = bonedata[0]#.strip()[-25:]
        nameparent = bonenames[bonedata[1][2]]
        pos = bonedata[2][4:7] 
        rot = bonedata[2][0:4] 
        qx,qy,qz,qw = rot[0],rot[1],rot[2],rot[3]
        #print("Quaternion:",qx,qy,qz,qw)
        if bone_id==0:
            rot =  mathutils.Quaternion((qw,-qx,-qy,-qz))
        if bone_id!=0:
            rot =  mathutils.Quaternion((qw,qx,qy,qz))
        matrix = mathutils.Matrix()
        rot = rot.to_matrix().inverted()
        #print(rot)
        matrix[0][:3] = rot[0]
        matrix[1][:3] = rot[1]
        matrix[2][:3] = rot[2]
        matrix[3][:3] = pos
        if bone_id>0:
            bonedata.append(matrix*bonesdata[str(bonedata[1][2])][3])
        else:
            bonedata.append(matrix)
    bpy.context.scene.update()

#not working    
def make_bone_position():
    print ('make bone position')
    bpy.ops.object.mode_set(mode='EDIT')
    for bone_id in range(len(bonesdata)):
        bonedata = bonesdata[str(bone_id)]
        namebone = bonedata[0]#.strip()[-25:]
        bone = amt.edit_bones[namebone]
        bone.transform(bonedata[3], scale=True, roll=True)
        bvec = bone.tail- bone.head
        bvec.normalize()
        bone.tail = bone.head + 0.1 * bvec
        #bone.tail = bone.head + 1 * bvec
    bpy.context.scene.update()    
        
#not working  
def make_bone_position1():    
    print ('make bone position')
    bpy.ops.object.mode_set(mode='EDIT')
    for bone_id in range(len(bonesdata)):
        bonedata = bonesdata[str(bone_id)]
        namebone = bonedata[0]#.strip()[-25:]
        pos = bonedata[2][4:7] 
        pos1 = pos[0]*skala  
        pos2 = pos[1]*skala  
        pos3 = pos[2]*skala 
        if flipyz == False:
            pos = [pos1,pos2,pos3]
        if flipyz == True:
            pos = [pos1,-pos3,pos2]
        rot = bonedata[2][0:4] 
        qx,qy,qz,qw = rot[0],rot[1],rot[2],rot[3]
        if bone_id==0:
            rot = mathutils.Quaternion((qw,-qx,-qy,-qz))
        if bone_id!=0:
            rot = mathutils.Quaternion((qw,qx,qy,qz))
        #rot = rot.toMatrix().invert() 	
        rot = rot.to_matrix().inverted() 	
        bone = amt.edit_bones[namebone]
        #print("BONES:",amt.bones[0])
        
        if bone_id!=0:
            bone.head = bone.parent.head+mathutils.Vector(pos) * bone.parent.matrix
            #print(dir(rot))
            #print("rot:",rot)
            #print("matrix:",bone.parent.matrix)
            
            tempM = rot.to_4x4()*bone.parent.matrix
            #bone.matrix = tempM
            bone.transform(tempM, scale=False, roll=True)
            #bone.matrix_local = tempM
        else:
            bone.head = mathutils.Vector(pos)
            #bone.matrix = rot
            bone.transform(rot, scale=False, roll=True)
            #bone.matrix_local = rot
        bvec = bone.tail- bone.head
        bvec.normalize()
        bone.tail = bone.head + 0.1 * bvec
        #bone.tail = bone.head + 1 * bvec
    

#http://www.blender.org/forum/viewtopic.php?t=13340&sid=8b17d5de07b17960021bbd72cac0495f            
def fixRollZ(b):
    v = (b.tail-b.head)/b.length
    b.roll -= math.degrees(math.atan2(v[0]*v[2]*(1 - v[1]),v[0]*v[0] + v[1]*v[2]*v[2])) 
def fixRoll(b):
    v = (b.tail-b.head)/b.length
    if v[2]*v[2] > .5:
        #align X-axis
        b.roll += math.degrees(math.atan2(v[0]*v[2]*(1 - v[1]),v[2]*v[2] + v[1]*v[0]*v[0]))
    else:
        #align Z-axis
        b.roll -= math.degrees(math.atan2(v[0]*v[2]*(1 - v[1]),v[0]*v[0] + v[1]*v[2]*v[2])) 
""" #did not port this yet unstable but work in some ways
def make_bone_position3():    
            for bone in md5_bones:
                #print(dir(bone))
                bpy.ops.object.mode_set(mode='EDIT')
                newbone = ob_new.data.edit_bones.new(bone.name)
                #parent the bone
                print("DRI:",dir(newbone))
                parentbone = None
                print("bone name:",bone.name)
                #note bone location is set in the real space or global not local
                bonesize = bpy.types.Scene.unrealbonesize
                if bone.name != bone.parent:

                    pos_x = bone.bindpos[0]
                    pos_y = bone.bindpos[1]
                    pos_z = bone.bindpos[2]
                    
                    #print( "LINKING:" , bone.parent ,"j")
                    parentbone = ob_new.data.edit_bones[bone.parent]
                    newbone.parent = parentbone
                    
                    rotmatrix = bone.bindmat.to_matrix().to_4x4().to_3x3()  # XXX, redundant matrix conversion?
                    newbone.transform(bone.bindmat.to_matrix().to_4x4(),True,True)
                    #parent_head = parentbone.matrix.to_quaternion().inverse() * parentbone.head
                    #parent_tail = parentbone.matrix.to_quaternion().inverse() * parentbone.tail
                    #location=Vector(pos_x,pos_y,pos_z)
                    #set_position = (parent_tail - parent_head) + location
                    #print("tmp head:",set_position)

                    #pos_x = set_position.x
                    #pos_y = set_position.y
                    #pos_z = set_position.z
                    
                 
                    newbone.head.x = parentbone.head.x + pos_x
                    newbone.head.y = parentbone.head.y + pos_y
                    newbone.head.z = parentbone.head.z + pos_z
                    #print("head:",newbone.head)
                    newbone.tail.x = parentbone.head.x + (pos_x + bonesize * rotmatrix[0][1])
                    newbone.tail.y = parentbone.head.y + (pos_y + bonesize * rotmatrix[1][1])
                    newbone.tail.z = parentbone.head.z + (pos_z + bonesize * rotmatrix[2][1])
                    #newbone.roll = fixRoll(newbone)
                else:
                    #print("rotmatrix:",dir(bone.bindmat.to_matrix().resize_4x4()))
                    #rotmatrix = bone.bindmat.to_matrix().resize_4x4().to_3x3()  # XXX, redundant matrix conversion?
                    rotmatrix = bone.bindmat.to_matrix().to_3x3()  # XXX, redundant matrix conversion?
                    #newbone.transform(bone.bindmat.to_matrix(),True,True)
                    newbone.head.x = bone.bindpos[0]
                    newbone.head.y = bone.bindpos[1]
                    newbone.head.z = bone.bindpos[2]
                    newbone.tail.x = bone.bindpos[0] + bonesize * rotmatrix[0][1]
                    newbone.tail.y = bone.bindpos[1] + bonesize * rotmatrix[1][1]
                    newbone.tail.z = bone.bindpos[2] + bonesize * rotmatrix[2][1]
                    #newbone.roll = fixRoll(newbone)
                    #print("no parent")    
""" 
    

#import psk file
def pskimport(filename,importmesh,importbone,bDebugLogPSK,importmultiuvtextures):
    global DEBUGLOG, plik,vertexes,uvcoord,faceslist,num_faces,facemat,facesmooth,m
    global vertexes_ids,bonesdata,meshesdata,groups,num_materials,skala,flipyz,flipuv,amt,vertices,faces
    points = []
    vertexes = []
    vertices = []
    uvcoord = []
    faceslist = []
    datafaces = []
    faces = []
    facemat = []
    facesmooth = []
    groups = []
    vertexes_ids = []
    bonesdata = {}
    meshesdata ={}
	
    DEBUGLOG = bDebugLogPSK
    print ("--------------------------------------------------")
    print ("---------SCRIPT EXECUTING PYTHON IMPORTER---------")
    print ("--------------------------------------------------")
    print (" DEBUG Log:",bDebugLogPSK)
    print ("Importing file: ", filename)
    
    plik = open(filename,'rb')
    word(20),i(3)
    
    #------POINTS------
    print ('reading points')
    word(20)
    data = i(3)
    num_points = data[2]    
    for m in range(num_points):
        v=f(3)
        v1 =v[0]*skala
        v2 =v[1]*skala
        v3 =v[2]*skala
        if flipyz == False:
            points.append([v1,v2,v3])
        if flipyz == True:
            points.append([v1,-v3,v2])
        vertexes_ids.append([])
    
    #------VERTEXES----
    print ('reading vertexes')
    word(20)
    data = i(3)
    num_vertexes = data[2]
    for m in range(num_vertexes):
        data1 = H(2)
        vertexes.append(points[data1[0]])
        vertices.append(points[data1[0]])
        #vertices.extend(points[data1[0]])
        #vertices.extend([(points[data1[0]][0],points[data1[0]][1],points[data1[0]][2] )])
        #vertices.extend([(points[data1[0]][0],points[data1[0]][1],points[data1[0]][2] )])
        #print(points[data1[0]])
        if flipuv == False:
            uvcoord.append([f(1)[0],1-f(1)[0]])
        if flipuv == True:
            uvcoord.append([f(1)[0],f(1)[0]])
        vertexes_ids[data1[0]].append(m)
        b(2),h(1)
    
    
    #------FACES-------
    print ('reading faces')
    word(20)
    data = i(3)
    num_faces = data[2]
    for m in range(num_faces):
        v0=H(1)[0]
        v1=H(1)[0]
        v2=H(1)[0]
        faceslist.append([v1,v0,v2])
        faces.extend([(v1,v0,v2,0)])
        #faces.append([v1,v0,v2])
        #print((v1,v0,v2,0))
        mat_ids = B(2) 
        facemat.append(mat_ids)
        if str(mat_ids[0]) not in meshesdata:
            meshesdata[str(mat_ids[0])] = []          
        meshesdata[str(mat_ids[0])].append(m)
        facesmooth.append(i(1)[0])
        #datafaces.append([v1,v0,v2],mat_ids
    
    #------MATERIALS---
    print ('making materials')
    word(20)
    data = i(3)
    num_materials = data[2]
    for m in range(num_materials):
        name = word(64)
        print ('read materials from',name)
        matdata = bpy.data.materials.new(name)
        #try:
            #mat = Material.Get(namemodel+'-'+str(m))
            #mat = Material.Get(name)
        #except:
            #mat = Material.New(namemodel+'-'+str(m))
            #mat = Material.New(name)
        i(6)
        #make_materials(name,mat)
    
    #-------BONES------
    print ('reading bones')
    #check_armature()
    check_armature()
    word(20)
    data = i(3)
    num_bones = data[2]
    for m in range(num_bones):
        #print(str(m)) #index
        bonesdata[str(m)] = []
        bonename = word(64)
        bonename = bonename#.strip() 
        bonename = bonename.strip() 
        #print(bonename)#bone name
        bonesdata[str(m)].append(bonename)
        bonesdata[str(m)].append(i(3))
        bonesdata[str(m)].append(f(11))
    make_bone()
    make_bone_parent()
    bones_matrix()
    make_bone_position1()

    
     #-------SKINNING---
    print ('making skinning')
    word(20)
    data = i(3)
    num_groups = data[2]
    
    for m in range(num_groups):
        w = f(1)[0]
        v_id  = i(1)[0]         
        gr = i(1)[0]
        groups.append([w,v_id,gr]) 
    #create Mesh
    drawmesh()

    print ("IMPORTER PSK Blender 2.6 completed")
#End of def pskimport#########################

def psaimport(filename):
    global plik,bonesdata,animdata,anim_offset,animation_names
    bonesdata = {}
    animation_names = []
    animation_num_bones = []
    animation_num_keys = []
    animation_loc_keys = []
    animation_rot_keys = []
    animdata = {}
    plik = open(filename,'rb')
    print (word(20),i(3))

    #-------BONES------
    #check_armature_for_psa()
    print (word(20))
    data = i(3)
    #print data
    num_bones = data[2]
    for m in range(num_bones):
        bonesdata[str(m)] = []
        name = word(64)
        bonesdata[str(m)].append(name)
        bonesdata[str(m)].append(i(3))
        bonesdata[str(m)].append(f(11))


    #--------ANIMATIONS-INFO
    print (word(20))
    data = i(3)
    #print data
    for m in range(data[2]):
        name_animation = word(64)#name animation
        print("NAME:",name_animation)
        animation_names.append(name_animation)
        word(64)#name of owner of animation ?
        data = i(4)#num bones - 0 - 0 - num keys for all bones for this animation
        num_bones = data[0] 
        animation_num_bones.append(num_bones)
        f(3)
        data = i(3) 
        num_keys = data[2]
        animation_num_keys.append(num_keys)
    print (plik.tell())

    #--------ANIMATIONS-KEYS
    print (word(20))
    data = i(3)
    #print data
    anim_offset = {}
    seek = plik.tell()
    for m in range(len(animation_names)):
        anim_name = animation_names[m]
        anim_bones = animation_num_bones[m]
        anim_keys = animation_num_keys[m]
        anim_offset[anim_name] = []
        anim_offset[anim_name].append(seek)
        anim_offset[anim_name].append(anim_keys)
        anim_offset[anim_name].append(anim_bones)
        seek+=anim_keys*anim_bones*32
    
    
def getInputFilename(self,filename,importmesh,importbone,bDebugLogPSK,importmultiuvtextures):
    checktype = filename.split('\\')[-1].split('.')[1]
    print ("------------",filename)
    if checktype.lower() != 'psk':
        print ("  Selected file = ",filename)
        raise (IOError, "The selected input file is not a *.psk file")
        #self.report({'INFO'}, ("Selected file:"+ filename))
    else:
        pskimport(filename,importmesh,importbone,bDebugLogPSK,importmultiuvtextures)
#import panel
class IMPORT_OT_psk(bpy.types.Operator):
    """Load a skeleton mesh psk File"""
    bl_idname = "import_scene.psk"
    bl_label = "Import PSK"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {'UNDO'}

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    filepath = StringProperty(
            subtype='FILE_PATH',
            )
    filter_glob = StringProperty(
            default="*.psk",
            options={'HIDDEN'},
            )
    importmesh = BoolProperty(
            name="Mesh",
            description="Import mesh only. (not yet build.)",
            default=True,
            )
    importbone = BoolProperty(
            name="Bones",
            description="Import bones only. Current not working yet",
            default=True,
            )
    importmultiuvtextures = BoolProperty(
            name="Single UV Texture(s)",
            description="Single or Multi uv textures",
            default=True,
            )
    bDebugLogPSK = BoolProperty(
            name="Debug Log.txt",
            description="Log the output of raw format. It will save in " \
                        "current file dir. Note this just for testing",
            default=False,
            )
    unrealbonesize = FloatProperty(
            name="Bone Length",
            description="Bone Length from head to tail distance",
            default=1,
            min=0.001,
            max=1000,
            )

    def execute(self, context):
        bpy.types.Scene.unrealbonesize = self.unrealbonesize
        getInputFilename(self,self.filepath,self.importmesh,self.importbone,self.bDebugLogPSK,self.importmultiuvtextures)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}  
#import panel psk	
class OBJECT_OT_PSKPath(bpy.types.Operator):
    bl_idname = "object.pskpath"
    bl_label = "PSK Path"
    __doc__ = ""

    filepath = StringProperty(
            subtype='FILE_PATH',
            )
    filter_glob = StringProperty(
            default="*.psk",
            options={'HIDDEN'},
            )
    importmesh = BoolProperty(
            name="Mesh",
            description="Import mesh only. (not yet build.)",
            default=True,
            )
    importbone = BoolProperty(
            name="Bones",
            description="Import bones only. Current not working yet",
            default=True,
            )
    importmultiuvtextures = BoolProperty(
            name="Single UV Texture(s)",
            description="Single or Multi uv textures",
            default=True,
            )
    bDebugLogPSK = BoolProperty(
            name="Debug Log.txt",
            description="Log the output of raw format. It will save in " \
                        "current file dir. Note this just for testing",
            default=False,
            )
    unrealbonesize = FloatProperty(
            name="Bone Length",
            description="Bone Length from head to tail distance",
            default=1,
            min=0.001,
            max=1000,
            )
    
    def execute(self, context):
        #context.scene.importpskpath = self.properties.filepath
        bpy.types.Scene.unrealbonesize = self.unrealbonesize
        getInputFilename(self,self.filepath,self.importmesh,self.importbone,self.bDebugLogPSK,self.importmultiuvtextures)
        return {'FINISHED'}
        
    def invoke(self, context, event):
        #bpy.context.window_manager.fileselect_add(self)
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}
#import panel psa		
class OBJECT_OT_PSAPath(bpy.types.Operator):
    bl_idname = "object.psapath"
    bl_label = "PSA Path"
    __doc__ = ""

    filepath = StringProperty(name="PSA File Path", description="Filepath used for importing the PSA file", maxlen= 1024, default= "")
    filter_glob = StringProperty(
            default="*.psa",
            options={'HIDDEN'},
            )
    def execute(self, context):
        #context.scene.importpsapath = self.properties.filepath
        psaimport(self.filepath)
        return {'FINISHED'}
        
    def invoke(self, context, event):
        bpy.context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
		
class OBJECT_OT_Path(bpy.types.Operator):
    bl_idname = "object.path"
    bl_label = "MESH BUILD TEST"
    __doc__ = ""
    # generic transform props
    view_align = BoolProperty(
            name="Align to View",
            default=False,
            )
    location = FloatVectorProperty(
            name="Location",
            subtype='TRANSLATION',
            )
    rotation = FloatVectorProperty(
            name="Rotation",
            subtype='EULER',
            )
    def execute(self, context):
        return {'FINISHED'}
        
    def invoke(self, context, event):
        me = bpy.data.meshes.new("test")
        obmade = bpy.data.objects.new("TestObject",me)
        print("Create Simple Mesh")
        bpy.data.scenes[0].objects.link(obmade)
        for i in bpy.context.scene.objects: i.select = False #deselect all objects
        obmade.select = True
        bpy.context.scene.objects.active = obmade
        
        verts = [(0,0,0),(2,0,0),(2,0,2)]
        edges = [(0,1),(1,2),(2,0)]
        faces = []
        faces.extend([(0,1,2,0)])
        #me.vertices.add(len(verts))
        #print(dir(me))
        me.vertices.add(len(verts))
        me.tessfaces.add(len(faces))
        for face in me.tessfaces:
            print(dir(face))
        
        me.vertices.foreach_set("co", unpack_list(verts))
        me.tessfaces.foreach_set("vertices_raw", unpack_list(faces))
        me.edges.add(len(edges))
        me.edges.foreach_set("vertices", unpack_list(edges))
        
        #print(len(me.tessfaces))
        me.tessface_uv_textures.new("uvtexture")
        #for uv in me.tessface_uv_textures:
            #print(len(uv.data))
            #print(dir(uv.data[0]))
            #print(dir(uv.data[0].uv1))
        return {'RUNNING_MODAL'}

#import menu panel tool bar
class VIEW3D_PT_unrealimport_objectmode(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label = "Import PSK/PSA"
    
    @classmethod
    def poll(cls, context):
        return context.active_object

    def draw(self, context):
        layout = self.layout
        rd = context.scene

        row2 = layout.row(align=True)
        row2.operator(OBJECT_OT_PSKPath.bl_idname)                
        row2.operator(OBJECT_OT_PSAPath.bl_idname)        
        row2.operator(OBJECT_OT_Path.bl_idname)        
#import panel
def menu_func(self, context):
    self.layout.operator(IMPORT_OT_psk.bl_idname, text="Skeleton Mesh (.psk)")

def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(menu_func)
    
def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_import.remove(menu_func)

if __name__ == "__main__":
    register()

#note this only read the data and will not be place in the scene    
#getInputFilename('C:\\blenderfiles\\BotA.psk') 
#getInputFilename('C:\\blenderfiles\\AA.PSK')
#getInputFilename('C:\\blender26x\\blender-2.psk')
