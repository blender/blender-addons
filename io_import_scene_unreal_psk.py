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
    "version": (2, 0),
    "blender": (2, 5, 9),
    "api": 41077,
    "location": "File > Import > Skeleton Mesh (.psk)",
    "description": "Import Skeleleton Mesh",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"
        "Scripts/Import-Export/Unreal_psk_psa",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=21366",
    "category": "Import-Export"}

"""
Version': '2.0' ported by Darknet

Unreal Tournament PSK file to Blender mesh converter V1.0
Author: D.M. Sturgeon (camg188 at the elYsium forum), ported by Darknet
Imports a *psk file to a new mesh

-No UV Texutre
-No Weight
-No Armature Bones
-No Material ID
-Export Text Log From Current Location File (Bool )
"""

import bpy
import mathutils
import math
from string import *
from struct import *
from math import *
from bpy.props import *

bpy.types.Scene.unrealbonesize = FloatProperty(
    name="Bone Length",
    description="Bone Length from head to tail distance",
    default=1,min=0.001,max=1000)

#output log in to txt file
DEBUGLOG = False

scale = 1.0
bonesize = 1.0
md5_bones=[]

def unpack_list(list_of_tuples):
    l = []
    for t in list_of_tuples:
        l.extend(t)
    return l
"""
class md5_bone:
    bone_index=0
    name=""
    bindpos=[]
    bindmat = mathutils.Quaternion()
    parent=""
    parent_index=0
    blenderbone=None
    roll=0

    def __init__(self):
        self.bone_index=0
        self.name=""
        self.bindpos=[0.0]*3
        self.bindmat=[None]*3  #is this how you initilize a 2d-array
        for i in range(3): self.bindmat[i] = [0.0]*3
        self.parent=""
        self.parent_index=0
        self.blenderbone=None

    def dump(self):
        print ("bone index: ", self.bone_index)
        print ("name: ", self.name)
        print ("bind position: ", self.bindpos)
        print ("bind translation matrix: ", self.bindmat)
        print ("parent: ", self.parent)
        print ("parent index: ", self.parent_index)
        print ("blenderbone: ", self.blenderbone)
"""
class md5_bone:
    bone_index=0
    name=""
    bindpos=[]
    bindmat=[]
    scale = []
    parent=""
    parent_index=0
    blenderbone=None
    roll=0

    def __init__(self):
        self.bone_index=0
        self.name=""
        self.bindpos=[0.0]*3
        self.scale=[0.0]*3
        self.bindmat=[None]*3  #is this how you initilize a 2d-array
        for i in range(3): self.bindmat[i] = [0.0]*3
        self.parent=""
        self.parent_index=0
        self.blenderbone=None

    def dump(self):
        print ("bone index: ", self.bone_index)
        print ("name: ", self.name)
        print ("bind position: ", self.bindpos)
        print ("bind translation matrix: ", self.bindmat)
        print ("parent: ", self.parent)
        print ("parent index: ", self.parent_index)
        print ("blenderbone: ", self.blenderbone)
        
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
        
def pskimport(infile,importmesh,importbone,bDebugLogPSK,importmultiuvtextures):
    global DEBUGLOG
    DEBUGLOG = bDebugLogPSK
    print ("--------------------------------------------------")
    print ("---------SCRIPT EXECUTING PYTHON IMPORTER---------")
    print ("--------------------------------------------------")
    print (" DEBUG Log:",bDebugLogPSK)
    print ("Importing file: ", infile)
    
    md5_bones=[]
    pskfile = open(infile,'rb')
    if (DEBUGLOG):
        logpath = infile.replace(".psk", ".txt")
        print("logpath:",logpath)
        logf = open(logpath,'w')
        
    def printlog(strdata):
        if (DEBUGLOG):
            logf.write(strdata)
    
    objName = infile.split('\\')[-1].split('.')[0]
    
    me_ob = bpy.data.meshes.new(objName)
    print("objName:",objName)
    printlog(("New Mesh = " + me_ob.name + "\n"))
    #read general header
    indata = unpack('20s3i',pskfile.read(32))
    #not using the general header at this time
    #================================================================================================== 
    # vertex point
    #================================================================================================== 
    #read the PNTS0000 header
    indata = unpack('20s3i',pskfile.read(32))
    recCount = indata[3]
    printlog(( "Nbr of PNTS0000 records: " + str(recCount) + "\n"))
    counter = 0
    verts = []
    while counter < recCount:
        counter = counter + 1
        indata = unpack('3f',pskfile.read(12))
        #print(indata[0],indata[1],indata[2])
        verts.extend([(indata[0],indata[1],indata[2])])
        printlog(str(indata[0]) + "|" +str(indata[1]) + "|" +str(indata[2]) + "\n")
        #Tmsh.vertices.append(NMesh.Vert(indata[0],indata[1],indata[2]))
        
    #================================================================================================== 
    # UV
    #================================================================================================== 
    #read the VTXW0000 header
    indata = unpack('20s3i',pskfile.read(32))
    recCount = indata[3]
    printlog( "Nbr of VTXW0000 records: " + str(recCount)+ "\n")
    counter = 0
    UVCoords = []
    #UVCoords record format = [index to PNTS, U coord, v coord]
    printlog("[index to PNTS, U coord, v coord]\n");
    while counter < recCount:
        counter = counter + 1
        indata = unpack('hhffhh',pskfile.read(16))
        UVCoords.append([indata[0],indata[2],indata[3]])
        printlog(str(indata[0]) + "|" +str(indata[2]) + "|" +str(indata[3])+"\n")
        #print([indata[0],indata[2],indata[3]])
        #print([indata[1],indata[2],indata[3]])
        
    #================================================================================================== 
    # Face
    #================================================================================================== 
    #read the FACE0000 header
    indata = unpack('20s3i',pskfile.read(32))
    recCount = indata[3]
    printlog( "Nbr of FACE0000 records: "+ str(recCount) + "\n")
    #PSK FACE0000 fields: WdgIdx1|WdgIdx2|WdgIdx3|MatIdx|AuxMatIdx|SmthGrp
    #associate MatIdx to an image, associate SmthGrp to a material
    SGlist = []
    counter = 0
    faces = []
    faceuv = []
    #the psk values are: nWdgIdx1|WdgIdx2|WdgIdx3|MatIdx|AuxMatIdx|SmthGrp
    printlog("nWdgIdx1|WdgIdx2|WdgIdx3|MatIdx|AuxMatIdx|SmthGrp \n")
    while counter < recCount:
        counter = counter + 1
        indata = unpack('hhhbbi',pskfile.read(12))        
        printlog(str(indata[0]) + "|" +str(indata[1]) + "|" +str(indata[2])+ "|" +str(indata[3])+ "|" +str(indata[4])+ "|" +str(indata[5]) + "\n")
        #indata[0] = index of UVCoords
        #UVCoords[indata[0]]=[index to PNTS, U coord, v coord]
        #UVCoords[indata[0]][0] = index to PNTS
        PNTSA = UVCoords[indata[0]][0]
        PNTSB = UVCoords[indata[1]][0]
        PNTSC = UVCoords[indata[2]][0]
        #print(PNTSA,PNTSB,PNTSC) #face id vertex
        #faces.extend([0,1,2,0])
        faces.extend([PNTSA,PNTSB,PNTSC,0])
        uv = []
        u0 = UVCoords[indata[0]][1]
        v0 = UVCoords[indata[0]][2]
        uv.append([u0,v0])
        u1 = UVCoords[indata[1]][1]
        v1 = UVCoords[indata[1]][2]
        uv.append([u1,v1])
        u2 = UVCoords[indata[2]][1]
        v2 = UVCoords[indata[2]][2]
        uv.append([u2,v2])
        faceuv.append([uv,indata[3],indata[4],indata[5]])
        
        #print("material:",indata[3])
        #print("UV: ",u0,v0)
        #update the uv var of the last item in the Tmsh.faces list
        # which is the face just added above
        ##Tmsh.faces[-1].uv = [(u0,v0),(u1,v1),(u2,v2)]
        #print("smooth:",indata[5])
        #collect a list of the smoothing groups
        if SGlist.count(indata[5]) == 0:
            SGlist.append(indata[5])
            print("smooth:",indata[5])
        #assign a material index to the face
        #Tmsh.faces[-1].materialIndex = SGlist.index(indata[5])
    printlog( "Using Materials to represent PSK Smoothing Groups...\n")
    #==========
    # skip something...
    #==========
    
    #================================================================================================== 
    # Material
    #================================================================================================== 
    ##
    #read the MATT0000 header
    indata = unpack('20s3i',pskfile.read(32))
    recCount = indata[3]
    printlog("Nbr of MATT0000 records: " +  str(recCount) + "\n" )
    printlog(" - Not importing any material data now. PSKs are texture wrapped! \n")
    counter = 0
    materialcount = 0
    while counter < recCount:
        counter = counter + 1
        indata = unpack('64s6i',pskfile.read(88))
        materialcount += 1
        print("Material",counter)		
    ##
    
    #================================================================================================== 
    # Bones (Armature)
    #================================================================================================== 
    #read the REFSKEL0 header
    indata = unpack('20s3i',pskfile.read(32))
    recCount = indata[3]
    printlog( "Nbr of REFSKEL0 records: " + str(recCount) + "\n")
    #REFSKEL0 fields - Name|Flgs|NumChld|PrntIdx|Qw|Qx|Qy|Qz|LocX|LocY|LocZ|Lngth|XSize|YSize|ZSize
    
    Bns = []
    bone = []
    #================================================================================================== 
    # Bone Data 
    #==================================================================================================
    counter = 0
    print ("---PRASE--BONES---")
    printlog("Name|Flgs|NumChld|PrntIdx|Qw|Qx|Qy|Qz|LocX|LocY|LocZ|Lngth|XSize|YSize|ZSize\n")
    while counter < recCount:
        indata = unpack('64s3i11f',pskfile.read(120))
        #print( "DATA",str(indata))
        
        bone.append(indata)
        
        createbone = md5_bone()
        #temp_name = indata[0][:30]
        temp_name = indata[0]
        
        temp_name = bytes.decode(temp_name)
        temp_name = temp_name.lstrip(" ")
        temp_name = temp_name.rstrip(" ")
        temp_name = temp_name.strip()
        temp_name = temp_name.strip( bytes.decode(b'\x00'))
        printlog(temp_name + "|" +str(indata[1]) + "|" +str(indata[2])+ "|" +str(indata[3])+ "|" +str(indata[4])+ "|" +str(indata[5]) +str(indata[6]) + "|" +str(indata[7]) + "|" +str(indata[8])+ "|" +str(indata[9])+ "|" +str(indata[10])+ "|" +str(indata[11]) +str(indata[12]) + "|" +str(indata[13]) + "|" +str(indata[14])+ "\n")
        print ("temp_name:", temp_name, "||")
        createbone.name = temp_name
        createbone.bone_index = counter
        createbone.parent_index = indata[3]
        createbone.bindpos[0] = indata[8]
        createbone.bindpos[1] = indata[9]
        createbone.bindpos[2] = indata[10]
        createbone.scale[0] = indata[12]
        createbone.scale[1] = indata[13]
        createbone.scale[2] = indata[14]
        
        #w,x,y,z
        if (counter == 0):#main parent
            print("no parent bone")
            createbone.bindmat = mathutils.Quaternion((indata[7],indata[4],indata[5],indata[6]))#default
            #createbone.bindmat = mathutils.Quaternion((indata[7],-indata[4],-indata[5],-indata[6]))
        else:#parent
            print("parent bone")
            createbone.bindmat = mathutils.Quaternion((indata[7],-indata[4],-indata[5],-indata[6]))#default
            #createbone.bindmat = mathutils.Quaternion((indata[7],indata[4],indata[5],indata[6]))
            
        md5_bones.append(createbone)
        counter = counter + 1
        bnstr = (str(indata[0]))
        Bns.append(bnstr)
        
    for pbone in md5_bones:
        pbone.parent =  md5_bones[pbone.parent_index].name
            
    bonecount = 0
    for armbone in bone:
        temp_name = armbone[0][:30]
        #print ("BONE NAME: ",len(temp_name))
        temp_name=str((temp_name))
        #temp_name = temp_name[1]
        #print ("BONE NAME: ",temp_name)
        bonecount +=1
    print ("-------------------------")
    print ("----Creating--Armature---")
    print ("-------------------------")
    
    #================================================================================================
    #Check armature if exist if so create or update or remove all and addnew bone
    #================================================================================================
    #bpy.ops.object.mode_set(mode='OBJECT')
    meshname ="ArmObject"
    objectname = "armaturedata"
    # arm = None  # UNUSED
    if importbone:
        obj = bpy.data.objects.get(meshname)
        # arm = obj  # UNUSED

        if not obj:
            '''
            armdata = bpy.data.armatures.new(objectname)
            ob_new = bpy.data.objects.new(meshname, armdata)
            #ob_new = bpy.data.objects.new(meshname, 'ARMATURE')
            #ob_new.data = armdata
            bpy.context.scene.objects.link(ob_new)
            #bpy.ops.object.mode_set(mode='OBJECT')
            for i in bpy.context.scene.objects: i.select = False #deselect all objects
            ob_new.select = True
            #set current armature to edit the bone
            bpy.context.scene.objects.active = ob_new
            #set mode to able to edit the bone
            bpy.ops.object.mode_set(mode='EDIT')

            #newbone = ob_new.data.edit_bones.new('test')
            #newbone.tail.y = 1
            print("creating bone(s)")
            for bone in md5_bones:
                #print(dir(bone))
                bpy.ops.object.mode_set(mode='EDIT')
                newbone = ob_new.data.edit_bones.new(bone.name)
            '''		


            armdata = bpy.data.armatures.new(objectname)
            ob_new = bpy.data.objects.new(meshname, armdata)
            #ob_new = bpy.data.objects.new(meshname, 'ARMATURE')
            #ob_new.data = armdata
            bpy.context.scene.objects.link(ob_new)
            #bpy.ops.object.mode_set(mode='OBJECT')
            for i in bpy.context.scene.objects: i.select = False #deselect all objects
            ob_new.select = True
            #set current armature to edit the bone
            bpy.context.scene.objects.active = ob_new
            #set mode to able to edit the bone
            bpy.ops.object.mode_set(mode='EDIT')

            #newbone = ob_new.data.edit_bones.new('test')
            #newbone.tail.y = 1
            print("creating bone(s)")
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
                    newbone.tail.x = parentbone.head.x + (pos_x + bonesize * rotmatrix[1][0])
                    newbone.tail.y = parentbone.head.y + (pos_y + bonesize * rotmatrix[1][1])
                    newbone.tail.z = parentbone.head.z + (pos_z + bonesize * rotmatrix[1][2])
                    #newbone.roll = fixRoll(newbone)
                else:
                    #print("rotmatrix:",dir(bone.bindmat.to_matrix().resize_4x4()))
                    #rotmatrix = bone.bindmat.to_matrix().resize_4x4().to_3x3()  # XXX, redundant matrix conversion?
                    rotmatrix = bone.bindmat.to_matrix().to_3x3()  # XXX, redundant matrix conversion?
                    #newbone.transform(bone.bindmat.to_matrix(),True,True)
                    newbone.head.x = bone.bindpos[0]
                    newbone.head.y = bone.bindpos[1]
                    newbone.head.z = bone.bindpos[2]
                    newbone.tail.x = bone.bindpos[0] + bonesize * rotmatrix[1][0]
                    newbone.tail.y = bone.bindpos[1] + bonesize * rotmatrix[1][1]
                    newbone.tail.z = bone.bindpos[2] + bonesize * rotmatrix[1][2]
                    #newbone.roll = fixRoll(newbone)
                    #print("no parent")
            
    bpy.context.scene.update()
    
    #==================================================================================================
    #END BONE DATA BUILD
    #==================================================================================================
    VtxCol = []
    for x in range(len(Bns)):
        #change the overall darkness of each material in a range between 0.1 and 0.9
        tmpVal = ((float(x)+1.0)/(len(Bns))*0.7)+0.1
        tmpVal = int(tmpVal * 256)
        tmpCol = [tmpVal,tmpVal,tmpVal,0]
        #Change the color of each material slightly
        if x % 3 == 0:
            if tmpCol[0] < 128: tmpCol[0] += 60
            else: tmpCol[0] -= 60
        if x % 3 == 1:
            if tmpCol[1] < 128: tmpCol[1] += 60
            else: tmpCol[1] -= 60
        if x % 3 == 2:
            if tmpCol[2] < 128: tmpCol[2] += 60
            else: tmpCol[2] -= 60
        #Add the material to the mesh
        VtxCol.append(tmpCol)
    
    #================================================================================================== 
    # Bone Weight
    #================================================================================================== 
    #read the RAWW0000 header
    indata = unpack('20s3i',pskfile.read(32))
    recCount = indata[3]
    printlog( "Nbr of RAWW0000 records: " + str(recCount) +"\n")
    #RAWW0000 fields: Weight|PntIdx|BoneIdx
    RWghts = []
    counter = 0
    while counter < recCount:
        counter = counter + 1
        indata = unpack('fii',pskfile.read(12))
        RWghts.append([indata[1],indata[2],indata[0]])
        #print("weight:",[indata[1],indata[2],indata[0]])
    #RWghts fields = PntIdx|BoneIdx|Weight
    RWghts.sort()
    printlog( "Vertex point and groups count =" + str(len(RWghts)) + "\n")
    printlog("PntIdx|BoneIdx|Weight")
    for vg in RWghts:
        printlog( str(vg[0]) + "|" + str(vg[1]) + "|" + str(vg[2]) + "\n")
        
    #Tmsh.update_tag()
    
    #set the Vertex Colors of the faces
    #face.v[n] = RWghts[0]
    #RWghts[1] = index of VtxCol
    """
    for x in range(len(Tmsh.faces)):
        for y in range(len(Tmsh.faces[x].v)):
            #find v in RWghts[n][0]
            findVal = Tmsh.faces[x].v[y].index
            n = 0
            while findVal != RWghts[n][0]:
                n = n + 1
            TmpCol = VtxCol[RWghts[n][1]]
            #check if a vertex has more than one influence
            if n != len(RWghts)-1:
                if RWghts[n][0] == RWghts[n+1][0]:
                    #if there is more than one influence, use the one with the greater influence
                    #for simplicity only 2 influences are checked, 2nd and 3rd influences are usually very small
                    if RWghts[n][2] < RWghts[n+1][2]:
                        TmpCol = VtxCol[RWghts[n+1][1]]
        Tmsh.faces[x].col.append(NMesh.Col(TmpCol[0],TmpCol[1],TmpCol[2],0))
    """
    if (DEBUGLOG):
        logf.close()
    #================================================================================================== 
    #Building Mesh
    #================================================================================================== 
    print("vertex:",len(verts),"faces:",len(faces))
    me_ob.vertices.add(len(verts))
    me_ob.faces.add(len(faces)//4)

    me_ob.vertices.foreach_set("co", unpack_list(verts))
    
    me_ob.faces.foreach_set("vertices_raw", faces)
    me_ob.faces.foreach_set("use_smooth", [False] * len(me_ob.faces))
    me_ob.update_tag()
    
    """
    Material setup coding.
    First the mesh has to be create first to get the uv texture setup working.
    -Create material(s) list in the psk pack data from the list.(to do list)
    -Append the material to the from create the mesh object.
    -Create Texture(s)
    -fae loop for uv assign and assign material index
    
    """
    bpy.ops.object.mode_set(mode='OBJECT')
    #===================================================================================================
    #Material Setup
    #===================================================================================================
    print ("-------------------------")
    print ("----Creating--Materials--")
    print ("-------------------------")
    materialname = "pskmat"
    materials = []

    for matcount in range(materialcount):
        #if texturedata != None:
        matdata = bpy.data.materials.new(materialname + str(matcount))
        #mtex = matdata.texture_slots.new()
        #mtex.texture = texture[matcount].data
        #print(type(texture[matcount].data))
        #print(dir(mtex))
        #print(dir(matdata))
        #for texno in range(len( bpy.data.textures)):
            #print((bpy.data.textures[texno].name))		
            #print(dir(bpy.data.textures[texno]))
        #matdata.active_texture = bpy.data.textures[matcount-1]
        #matdata.texture_coords = 'UV'
        #matdata.active_texture = texturedata
        materials.append(matdata)

    for material in materials:
        #add material to the mesh list of materials
        me_ob.materials.append(material)
    #===================================================================================================
    #UV Setup
    #===================================================================================================
    print ("-------------------------")
    print ("-- Creating UV Texture --")
    print ("-------------------------") 
    texture = []
    # texturename = "text1"  # UNUSED
    countm = 0
    #for countm in range(materialcount):
        #psktexname="psk" + str(countm)
        #me_ob.uv_textures.new(name=psktexname)
    if importmultiuvtextures == True:
        me_ob.uv_textures.new(name="pskuvtexture")
        #print(dir(bpy.data))
        if (len(faceuv) > 0):
            for countm in range(len(me_ob.uv_textures)):
                me_ob.update()
                uvtex = me_ob.uv_textures[countm] #add one uv texture
                me_ob.update()
                #print("UV TEXTURE NAME:",uvtex.name)
                for i, face in enumerate(me_ob.faces):
                    blender_tface = uvtex.data[i] #face
                    mfaceuv = faceuv[i]
                    #print("---------------------------------------")
                    #print(faceuv[i][1])
                    #print(dir(face))
                    face.material_index = faceuv[i][1]
                    blender_tface.uv1 = mfaceuv[0][0] #uv = (0,0)
                    blender_tface.uv2 = mfaceuv[0][1] #uv = (0,0)
                    blender_tface.uv3 = mfaceuv[0][2] #uv = (0,0)
                texture.append(uvtex)
    else:
        for countm in range(materialcount):
            psktexname="psk" + str(countm)
            me_ob.uv_textures.new(name=psktexname)
            #psktexname="psk" + str(countm)
        #me_ob.uv_textures.new(name=psktexname)
        for countm in range(len(me_ob.uv_textures)):
            me_ob.update()
            #print(dir(me_ob.uv_textures))
            #psktexname="psk" + str(countm)
            uvtex = me_ob.uv_textures[countm] #add one uv texture
            me_ob.update()
            #print("UV TEXTURE NAME:",uvtex.name)
            if (len(faceuv) > 0):
                # counttex = 0  # UNUSED
                countm = 0
                for countm in range(len(me_ob.uv_textures)):
                    me_ob.update()
                    #print(dir(me_ob.uv_textures))
                    psktexname="psk" + str(countm)
                    uvtex = me_ob.uv_textures[countm] #add one uv texture
                    me_ob.update()
                    #print("UV TEXTURE NAME:",uvtex.name)
                    for i, face in enumerate(me_ob.faces):
                        blender_tface = uvtex.data[i] #face
                        mfaceuv = faceuv[i]
                        #print("---------------------------------------")
                        #print(faceuv[i][1])
                        #print(dir(face))
                        face.material_index = faceuv[i][1]
                        if countm == faceuv[i][1]:
                            face.material_index = faceuv[i][1]
                            blender_tface.uv1 = mfaceuv[0][0] #uv = (0,0)
                            blender_tface.uv2 = mfaceuv[0][1] #uv = (0,0)
                            blender_tface.uv3 = mfaceuv[0][2] #uv = (0,0)
                        else:
                            #set uv to zero (0,0)
                            #print("--------------------")
                            #print(blender_tface.uv1)
                            #print(blender_tface.uv2)
                            #print(blender_tface.uv2)
                            blender_tface.uv1 = [0,0]
                            #print(blender_tface.uv1)
                            blender_tface.uv2 = [0,0]
                            blender_tface.uv3 = [0,0]
                
            texture.append(uvtex)
    print("UV TEXTURE LEN:",len(texture))
        #for tex in me_ob.uv_textures:
            #print("mesh tex:",dir(tex))
            #print((tex.name))
    
    #for face in me_ob.faces:
        #print(dir(face))


    '''
    matdata = bpy.data.materials.new(materialname)
    #color is 0 - 1 not in 0 - 255
    #matdata.mirror_color=(float(0.04),float(0.08),float(0.44))
    matdata.diffuse_color=(float(0.04),float(0.08),float(0.44))#blue color
    #print(dir(me_ob.uv_textures[0].data))
    texdata = None
    texdata = bpy.data.textures[len(bpy.data.textures)-1]
    if (texdata != None):
        #print(texdata.name)
        #print(dir(texdata))
        texdata.name = "texturelist1"
        matdata.active_texture = texdata
    materials.append(matdata)
    #matdata = bpy.data.materials.new(materialname)
    #materials.append(matdata)
    #= make sure the list isnt too big
    for material in materials:
        #add material to the mesh list of materials
        me_ob.materials.append(material)
    '''
    #===================================================================================================
    #
    #===================================================================================================
    obmesh = bpy.data.objects.new(objName,me_ob)
    #===================================================================================================
    #Mesh Vertex Group bone weight
    #===================================================================================================
    print("---- building bone weight mesh ----")
    #print(dir(ob_new.data.bones))
    #create bone vertex group #deal with bone id for index number
    for bone in ob_new.data.bones:
        #print("names:",bone.name,":",dir(bone))
        #print("names:",bone.name)
        group = obmesh.vertex_groups.new(bone.name)
    for vgroup in obmesh.vertex_groups:
        #print(vgroup.name,":",vgroup.index)
        for vgp in RWghts:
            #bone index
            if vgp[1] == vgroup.index:
                #print(vgp)
                #[vertex id],weight
                vgroup.add([vgp[0]], vgp[2], 'ADD')

    #check if there is a material to set to
    if len(materials) > 0:
        obmesh.active_material = materials[0] #material setup tmp
    print("---- adding mesh to the scene ----")    
    bpy.context.scene.objects.link(obmesh)    
    bpy.context.scene.update()
    
    print ("PSK2Blender completed")
#End of def pskimport#########################

def getInputFilename(self,filename,importmesh,importbone,bDebugLogPSK,importmultiuvtextures):
    checktype = filename.split('\\')[-1].split('.')[1]
    print ("------------",filename)
    if checktype.lower() != 'psk':
        print ("  Selected file = ",filename)
        raise (IOError, "The selected input file is not a *.psk file")
        #self.report({'INFO'}, ("Selected file:"+ filename))
    else:
        pskimport(filename,importmesh,importbone,bDebugLogPSK,importmultiuvtextures)

class IMPORT_OT_psk(bpy.types.Operator):
    '''Load a skeleton mesh psk File'''
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
