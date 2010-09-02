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

bl_addon_info = {
    "name": "Import MakeHuman (.mhx)",
    "author": "Thomas Larsson",
    "version": (0,9,5),
    "blender": (2, 5, 3),
    "api": 31667,
    "location": "File > Import",
    "description": "Import files in the MakeHuman eXchange format (.mhx)",
    "warning": "Alpha version",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"
        "Scripts/File_I-O/Make_Human",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"
        "func=detail&aid=21872&group_id=153&atid=469",
    "category": "Import/Export"}

""" 
**Project Name:**      MakeHuman

**Product Home Page:** http://www.makehuman.org/

**Code Home Page:**    http://code.google.com/p/makehuman/

**Authors:**           Thomas Larsson

**Copyright(c):**      MakeHuman Team 2001-2010

**Licensing:**         GPL3 (see also http://sites.google.com/site/makehumandocs/licensing)

**Coding Standards:**  See http://sites.google.com/site/makehumandocs/developers-guide

Abstract
MHX (MakeHuman eXchange format) importer for Blender 2.5x.
Version 0.9

"""

"""
Place this file in the .blender/scripts/addons dir
You have to activated the script in the "Add-Ons" tab (user preferences).
Access from the File > Import menu.
"""

#
#
#

import bpy
import os
import time
import mathutils
from mathutils import *
import geometry
import string

MAJOR_VERSION = 0
MINOR_VERSION = 9
MHX249 = False
Blender24 = False
Blender25 = True
TexDir = "~/makehuman/exports"

#
#
#

theScale = 1.0
useMesh = 1
doSmash = 1
verbosity = 2
warnedTextureDir = False
warnedVersion = False

true = True
false = False
Epsilon = 1e-6
nErrors = 0
theTempDatum = None

todo = []

#
#    toggle flags
#

T_ArmIK = 0x01
T_LegIK = 0x02
T_Replace = 0x20
T_Face = 0x40
T_Shape = 0x80
T_Mesh = 0x100
T_Armature = 0x200
T_Proxy = 0x400
T_Panel = 0x800

T_Rigify = 0x1000
T_Preset = 0x2000
T_Symm = 0x4000
T_MHX = 0x8000

toggle = T_Replace + T_ArmIK + T_LegIK + T_Mesh + T_Armature + T_Face

#
#    setFlagsAndFloats(rigFlags):
#
#    Global floats
fLegIK = 0.0
fArmIK = 0.0
fFingerPanel = 0.0
fFingerIK = 0.0
fFingerCurl = 0.0

#    rigLeg and rigArm flags
T_Toes = 0x0001
T_GoboFoot = 0x0002
T_InvFoot = 0x0004

T_FingerPanel = 0x100
T_FingerCurl = 0x0200
T_FingerIK = 0x0400


T_LocalFKIK = 0x8000

rigLeg = 0
rigArm = 0

def setFlagsAndFloats(rigFlags):
    global toggle, rigLeg, rigArm

    (footRig, fingerRig) = rigFlags
    rigLeg = 0
    rigArm = 0
    if footRig == 'Reverse foot': rigLeg |= T_InvFoot
    elif footRig == 'Gobo': rigLeg |= T_GoboFoot

    if fingerRig == 'Panel': rigArm |= T_FingerPanel
    elif fingerRig == 'IK': rigArm |= T_FingerIK
    elif fingerRig == 'Curl': rigArm |= T_FingerCurl

    toggle |= T_Panel

    # Global floats, used as influences
    global fFingerCurl, fLegIK, fArmIK, fFingerIK

    fFingerCurl = 1.0 if rigArm&T_FingerCurl else 0.0
    fLegIK = 1.0 if toggle&T_LegIK else 0.0
    fArmIK = 1.0 if toggle&T_ArmIK else 0.0
    fFingerIK = 1.0 if rigArm&T_FingerIK else 0.0

    return


#
#    Dictionaries
#

loadedData = {
    'NONE' : {},

    'Object' : {},
    'Mesh' : {},
    'Armature' : {},
    'Lamp' : {},
    'Camera' : {},
    'Lattice' : {},
    'Curve' : {},

    'Material' : {},
    'Image' : {},
    'MaterialTextureSlot' : {},
    'Texture' : {},
    
    'Bone' : {},
    'BoneGroup' : {},
    'Rigify' : {},

    'Action' : {},
    'Group' : {},

    'MeshTextureFaceLayer' : {},
    'MeshColorLayer' : {},
    'VertexGroup' : {},
    'ShapeKey' : {},
    'ParticleSystem' : {},

    'ObjectConstraints' : {},
    'ObjectModifiers' : {},
    'MaterialSlot' : {},
}

Plural = {
    'Object' : 'objects',
    'Mesh' : 'meshes',
    'Lattice' : 'lattices',
    'Curve' : 'curves',
    'Group' : 'groups',
    'Empty' : 'empties',
    'Armature' : 'armatures',
    'Bone' : 'bones',
    'BoneGroup' : 'bone_groups',
    'Pose' : 'poses',
    'PoseBone' : 'pose_bones',
    'Material' : 'materials',
    'Texture' : 'textures',
    'Image' : 'images',
    'Camera' : 'cameras',
    'Lamp' : 'lamps',
    'World' : 'worlds',
}

#
#    Creators
#

def uvtexCreator(me, name):
    print("uvtexCreator", me, name)
    return me.uv_textures.new(name)


def vertcolCreator(me, name):
    print("vertcolCreator", me, name)
    return me.vertex_colors.new(name)


#
#    loadMhx(filePath, context, flags):
#

def loadMhx(filePath, context, flags):
    global toggle
    toggle = flags
    readMhxFile(filePath)
    return

#
#    readMhxFile(filePath, rigFlags):
#

def readMhxFile(filePath, rigFlags):
    global todo, nErrors
    
    fileName = os.path.expanduser(filePath)
    (shortName, ext) = os.path.splitext(fileName)
    if ext != ".mhx":
        print("Error: Not a mhx file: " + fileName)
        return
    print( "Opening MHX file "+ fileName )
    time1 = time.clock()

    ignore = False
    stack = []
    tokens = []
    key = "toplevel"
    level = 0
    nErrors = 0

    setFlagsAndFloats(rigFlags)

    file= open(fileName, "rU")
    print( "Tokenizing" )
    lineNo = 0
    for line in file: 
        # print(line)
        lineSplit= line.split()
        lineNo += 1
        if len(lineSplit) == 0:
            pass
        elif lineSplit[0] == '#':
            pass
        elif lineSplit[0] == 'end':
            try:
                sub = tokens
                tokens = stack.pop()
                if tokens:
                    tokens[-1][2] = sub
                level -= 1
            except:
                print( "Tokenizer error at or before line %d" % lineNo )
                print( line )
                dummy = stack.pop()
        elif lineSplit[-1] == ';':
            if lineSplit[0] == '\\':
                key = lineSplit[1]
                tokens.append([key,lineSplit[2:-1],[]])
            else:
                key = lineSplit[0]
                tokens.append([key,lineSplit[1:-1],[]])
        else:
            key = lineSplit[0]
            tokens.append([key,lineSplit[1:],[]])
            stack.append(tokens)
            level += 1
            tokens = []
    file.close()

    if level != 0:
        raise NameError("Tokenizer out of kilter %d" % level)    
    clearScene()
    print( "Parsing" )
    parse(tokens)
    
    for (expr, glbals, lcals) in todo:
        try:
            # print("Doing %s" % expr)
            exec(expr, glbals, lcals)
        except:
            msg = "Failed: "+expr
            print( msg )
            nErrors += 1
            #raise NameError(msg)

    print("Postprocess")
    postProcess()
    print("HideLayers")
    hideLayers()
    time2 = time.clock()
    print("toggle = %x" % toggle)
    msg = "File %s loaded in %g s" % (fileName, time2-time1)
    if nErrors:
        msg += " but there where %d errors. " % (nErrors)
    print(msg)
    return    # loadMhx

#
#    getObject(name, var, glbals, lcals):
#

def getObject(name, var, glbals, lcals):
    try:
        ob = loadedData['Object'][name]
    except:
        if name != "None":
            expr = "%s = loadedData['Object'][name]" % var
            print("Todo ", expr)
            todo.append((expr, glbals, lcals))
        ob = None
    return ob

#
#    parse(tokens):
#

ifResult = False

def parse(tokens):
    global warnedVersion, MHX249, ifResult
    
    for (key, val, sub) in tokens:    
        # print("Parse %s" % key)
        data = None
        if key == 'MHX':
            if int(val[0]) != MAJOR_VERSION and int(val[1]) != MINOR_VERSION and not warnedVersion:
                print("Warning: \nThis file was created with another version of MHX\n")
                warnedVersion = True

        elif key == 'MHX249':
            MHX249 = eval(val[0])
            print("Blender 2.49 compatibility mode is %s\n" % MHX249)

        elif key == 'if':
            try:
                ifResult = eval(val[0])
            except:
                ifResult = False
            if ifResult:
                parse(sub)
                
        elif key == 'elif':
            if not ifResult:
                try:
                    ifResult = eval(val[0])
                except:
                    ifResult = False
                if ifResult:
                    parse(sub)
        
        elif key == 'else':
            if not ifResult:
                parse(sub)
        

        elif MHX249:
            pass

        elif key == 'print':
            msg = concatList(val)
            print(msg)
        elif key == 'warn':
            msg = concatList(val)
            print(msg)
        elif key == 'error':
            msg = concatList(val)
            raise NameError(msg)            
        elif key == "Object":
            parseObject(val, sub)
        elif key == "Mesh":
            data = parseMesh(val, sub)
        elif key == "Curve":
            data = parseCurve(val, sub)
        elif key == "Lattice":
            data = parseLattice(val, sub)
        elif key == "Group":
            data = parseGroup(val, sub)
        elif key == "Armature":
            data = parseArmature(val, sub)
        elif key == "Pose":
            data = parsePose(val, sub)
        elif key == "Action":
            data = parseAction(val, sub)
        elif key == "Material":
            data = parseMaterial(val, sub)
        elif key == "Texture":
            data = parseTexture(val, sub)
        elif key == "Image":
            data = parseImage(val, sub)
        elif key == "Process":
            parseProcess(val, sub)
        elif key == 'AnimationData':
            try:
                ob = loadedData['Object'][val[0]]
            except:
                ob = None
            if ob:
                bpy.context.scene.objects.active = ob
                parseAnimationData(ob, sub)
        elif key == 'ShapeKeys':
            try:
                ob = loadedData['Object'][val[0]]
            except:
                ob = None
            if ob:
                bpy.context.scene.objects.active = ob
                parseShapeKeys(ob, ob.data, val, sub)
        else:
            data = parseDefaultType(key, val, sub)                

        if data and key != 'Mesh':
            print( data )
    return

#
#    parseDefaultType(typ, args, tokens):
#

def parseDefaultType(typ, args, tokens):
    global todo

    name = args[0]
    data = None
    expr = "bpy.data.%s.new('%s')" % (Plural[typ], name)
    print(expr)
    data = eval(expr)
    print("  ok", data)

    bpyType = typ.capitalize()
    print(bpyType, name, data)
    loadedData[bpyType][name] = data
    if data == None:
        return None

    for (key, val, sub) in tokens:
        #print("%s %s" % (key, val))
        defaultKey(key, val, sub, 'data', [], globals(), locals())
    print("Done ", data)
    return data
    
#
#    concatList(elts)
#

def concatList(elts):
    string = ""
    for elt in elts:
        string += " %s" % elt
    return string

#
#    parseAction(args, tokens):
#    parseFCurve(fcu, args, tokens):
#    parseKeyFramePoint(pt, args, tokens):
#

def parseAction(args, tokens):
    name = args[0]
    if invalid(args[1]):
        return

    ob = bpy.context.object
    bpy.ops.object.mode_set(mode='POSE')
    if ob.animation_data:
        ob.animation_data.action = None
    created = {}
    for (key, val, sub) in tokens:
        if key == 'FCurve':
            prepareActionFCurve(ob, created, val, sub)
        
    act = ob.animation_data.action
    loadedData['Action'][name] = act
    if act == None:
        print("Ignoring action %s" % name)
        return act
    act.name = name
    print("Action", name, act, ob)
    
    for (key, val, sub) in tokens:
        if key == 'FCurve':
            fcu = parseActionFCurve(act, ob, val, sub)
        else:
            defaultKey(key, val, sub, 'act', [], globals(), locals())
    ob.animation_data.action = None
    bpy.ops.object.mode_set(mode='OBJECT')
    return act

def prepareActionFCurve(ob, created, args, tokens):            
    dataPath = args[0]
    index = args[1]
    (expr, channel) = channelFromDataPath(dataPath, index)
    try:
        if channel in created[expr]:
            return
        else:
            created[expr].append(channel)
    except:
        created[expr] = [channel]

    times = []
    for (key, val, sub) in tokens:
        if key == 'kp':
            times.append(int(val[0]))

    try:
        data = eval(expr)
    except:
        print("Ignoring illegal expression: %s" % expr)
        return

    n = 0
    for t in times:
        #bpy.context.scene.current_frame = t
        bpy.ops.anim.change_frame(frame = t)
        try:
            data.keyframe_insert(channel)
            n += 1
        except:
            pass
            #print("failed", data, expr, channel)
    if n != len(times):
        print("Mismatch", n, len(times), expr, channel)
    return

def channelFromDataPath(dataPath, index):
    words = dataPath.split(']')
    if len(words) == 1:
        # location
        expr = "ob"
        channel = dataPath
    elif len(words) == 2:
        # pose.bones["tongue"].location
        expr = "ob.%s]" % (words[0])
        cwords = words[1].split('.')
        channel = cwords[1]
    elif len(words) == 3:
        # pose.bones["brow.R"]["mad"]
        expr = "ob.%s]" % (words[0])
        cwords = words[1].split('"')
        channel = cwords[1]
    # print(expr, channel, index)
    return (expr, channel)

def parseActionFCurve(act, ob, args, tokens):
    dataPath = args[0]
    index = args[1]
    (expr, channel) = channelFromDataPath(dataPath, index)
    index = int(args[1])

    success = False
    for fcu in act.fcurves:
        (expr1, channel1) = channelFromDataPath(fcu.data_path, fcu.array_index)
        if expr1 == expr and channel1 == channel and fcu.array_index == index:
            success = True
            break
    if not success:
        return None

    n = 0
    for (key, val, sub) in tokens:
        if key == 'kp':
            try:
                pt = fcu.keyframe_points[n]
                pt.use_interpolation = 'LINEAR'
                pt = parseKeyFramePoint(pt, val, sub)
                n += 1
            except:
                pass
                #print(tokens)
                #raise NameError("kp", fcu, n, len(fcu.keyframe_points), val)
        else:
            defaultKey(key, val, sub, 'fcu', [], globals(), locals())
    return fcu

def parseKeyFramePoint(pt, args, tokens):
    pt.co = (float(args[0]), float(args[1]))
    if len(args) > 2:
        pt.handle_left = (float(args[2]), float(args[3]))
        pt.handle_right = (float(args[3]), float(args[5]))
    return pt

#
#    parseAnimationData(rna, tokens):
#    parseDriver(drv, args, tokens):
#    parseDriverVariable(var, args, tokens):
#

def parseAnimationData(rna, tokens):
    if 0 and toggle & T_MHX:
        return
    if rna.animation_data == None:    
        rna.animation_data_create()
    adata = rna.animation_data
    for (key, val, sub) in tokens:
        if key == 'FCurve':
            fcu = parseAnimDataFCurve(adata, rna, val, sub)
        else:
            defaultKey(key, val, sub, 'adata', [], globals(), locals())
    return adata

def parseAnimDataFCurve(adata, rna, args, tokens):
    if invalid(args[2]):
        return
    dataPath = args[0]
    index = int(args[1])
    # print("parseAnimDataFCurve", adata, dataPath, index)
    for (key, val, sub) in tokens:
        if key == 'Driver':
            fcu = parseDriver(adata, dataPath, index, rna, val, sub)
        elif key == 'FModifier':
            parseFModifier(fcu, val, sub)
        else:
            defaultKey(key, val, sub, 'fcu', [], globals(), locals())
    return fcu

"""
        fcurve = con.driver_add("influence", 0)
        driver = fcurve.driver
        driver.type = 'AVERAGE'
"""
def parseDriver(adata, dataPath, index, rna, args, tokens):
    if dataPath[-1] == ']':
        words = dataPath.split(']')
        expr = "rna." + words[0] + ']'
        pwords = words[1].split('"')
        prop = pwords[1]
        # print("prop", expr, prop)
        bone = eval(expr)
        return None
    else:
        words = dataPath.split('.')
        channel = words[-1]
        expr = "rna"
        for n in range(len(words)-1):
            expr += "." + words[n]
        expr += ".driver_add('%s', index)" % channel
    
    # print("expr", rna, expr)
    fcu = eval(expr)
    drv = fcu.driver
    drv.type = args[0]
    for (key, val, sub) in tokens:
        if key == 'DriverVariable':
            var = parseDriverVariable(drv, rna, val, sub)
        else:
            defaultKey(key, val, sub, 'drv', [], globals(), locals())
    return fcu

def parseDriverVariable(drv, rna, args, tokens):
    var = drv.variables.new()
    var.name = args[0]
    var.type = args[1]
    nTarget = 0
    # print("var", var, var.name, var.type)
    for (key, val, sub) in tokens:
        if key == 'Target':
            parseDriverTarget(var, nTarget, rna, val, sub)
            nTarget += 1
        else:
            defaultKey(key, val, sub, 'var', [], globals(), locals())
    return var

def parseFModifier(fcu, args, tokens):
    #fmod = fcu.modifiers.new()
    fmod = fcu.modifiers[0]
    #fmod.type = args[0]
    #print("fmod", fmod, fmod.type)
    for (key, val, sub) in tokens:
        defaultKey(key, val, sub, 'fmod', [], globals(), locals())
    return fmod

"""
        var = driver.variables.new()
        var.name = target_bone
        var.targets[0].id_type = 'OBJECT'
        var.targets[0].id = obj
        var.targets[0].rna_path = driver_path
"""
def parseDriverTarget(var, nTarget, rna, args, tokens):
    targ = var.targets[nTarget]
    # targ.rna_path = args[0]
    # targ.id_type = args[1]
    targ.id = loadedData['Object'][args[0]]
    for (key, val, sub) in tokens:
        defaultKey(key, val, sub, 'targ', [], globals(), locals())
    #print("Targ", targ, targ.id, targ.data_path, targ.id_type, targ.bone_target, targ.use_local_space_transform)
    return targ

    
#
#    parseMaterial(args, ext, tokens):
#    parseMTex(mat, args, tokens):
#    parseTexture(args, tokens):
#

def parseMaterial(args, tokens):
    global todo
    name = args[0]
    #print("Parse material "+name)
    mat = bpy.data.materials.new(name)
    if mat == None:
        return None
    loadedData['Material'][name] = mat
    #print("Material %s %s %s" % (mat, name, loadedData['Material'][name]))
    for (key, val, sub) in tokens:
        if key == 'MTex':
            parseMTex(mat, val, sub)
        elif key == 'Ramp':
            parseRamp(mat, val, sub)
        elif key == 'SSS':
            parseSSS(mat, val, sub)
        elif key == 'Strand':
            parseStrand(mat, val, sub)
        else:
            exclude = ['specular_intensity', 'use_tangent_shading']
            defaultKey(key, val, sub, 'mat', [], globals(), locals())
    #print("Done ", mat)
    
    return mat

def parseMTex(mat, args, tokens):
    global todo
    index = int(args[0])
    texname = args[1]
    texco = args[2]
    mapto = args[3]

    mat.add_texture(texture = loadedData['Texture'][texname], texture_coordinates = texco, map_to = mapto)
    mtex = mat.texture_slots[index]
    #mat.use_textures[index] = Bool(use)

    for (key, val, sub) in tokens:
        defaultKey(key, val, sub, "mtex", [], globals(), locals())

    return mtex

def parseTexture(args, tokens):
    global todo
    if verbosity > 2:
        print( "Parsing texture %s" % args )
    tex = bpy.data.textures.new(name=args[0], type=args[1])
    loadedData['Texture'][name] = tex
    
    for (key, val, sub) in tokens:
        if key == 'Image':
            try:
                imgName = val[0]
                img = loadedData['Image'][imgName]
                tex.image = img
            except:
                msg = "Unable to load image '%s'" % val[0]
        elif key == 'Ramp':
            parseRamp(tex, val, sub)
        else:
            defaultKey(key, val,  sub, "tex", ['use_nodes', 'use_textures', 'contrast'], globals(), locals())

    return tex

def parseRamp(data, args, tokens):
    nvar = "data.%s" % args[0]
    use = "data.use_%s = True" % args[0]
    exec(use)
    ramp = eval(nvar)
    elts = ramp.elements
    n = 0
    for (key, val, sub) in tokens:
        # print("Ramp", key, val)
        if key == 'Element':
            elts[n].color = eval(val[0])
            elts[n].position = eval(val[1])
            n += 1
        else:
            defaultKey(key, val,  sub, "tex", ['use_nodes', 'use_textures', 'contrast'], globals(), locals())
    
def parseSSS(mat, args, tokens):
    sss = mat.subsurface_scattering
    for (key, val, sub) in tokens:
        defaultKey(key, val, sub, "sss", [], globals(), locals())

def parseStrand(mat, args, tokens):
    strand = mat.strand
    for (key, val, sub) in tokens:
        defaultKey(key, val, sub, "strand", [], globals(), locals())

#
#    doLoadImage(filepath):
#    loadImage(filepath):
#    parseImage(args, tokens):
#

def doLoadImage(filepath):        
    path1 = os.path.expanduser(filepath)
    file1 = os.path.realpath(path1)
    if os.path.isfile(file1):
        print( "Found file "+file1 )
        try:
            img = bpy.data.images.load(file1)
            return img
        except:
            print( "Cannot read image" )
            return None
    else:
        print( "No file "+file1 )
        return None


def loadImage(filepath):
    global TexDir, warnedTextureDir, loadedData

    texDir = os.path.expanduser(TexDir)
    path1 = os.path.expanduser(filepath)
    file1 = os.path.realpath(path1)
    (path, filename) = os.path.split(file1)
    (name, ext) = os.path.splitext(filename)
    print( "Loading ", filepath, " = ", filename )

    # img = doLoadImage(texDir+"/"+name+".png")
    # if img:
    #    return img

    img = doLoadImage(texDir+"/"+filename)
    if img:
        return img

    # img = doLoadImage(path+"/"+name+".png")
    # if img:
    #    return img

    img = doLoadImage(path+"/"+filename)
    if img:
        return img

    if warnedTextureDir:
        return None
    warnedTextureDir = True
    return None
    TexDir = Draw.PupStrInput("TexDir? ", path, 100)

    texDir = os.path.expanduser(TexDir)
    img =  doLoadImage(texDir+"/"+name+".png")
    if img:
        return img

    img = doLoadImage(TexDir+"/"+filename)
    return img
    
def parseImage(args, tokens):
    global todo
    imgName = args[0]
    img = None
    for (key, val, sub) in tokens:
        if key == 'Filename':
            filename = val[0]
            for n in range(1,len(val)):
                filename += " " + val[n]
            img = loadImage(filename)
            if img == None:
                return None
            img.name = imgName
        else:
            defaultKey(key, val,  sub, "img", ['depth', 'is_dirty', 'has_data', 'size', 'type'], globals(), locals())
    print ("Image %s" % img )
    loadedData['Image'][imgName] = img
    return img

#
#    parseObject(args, tokens):
#    createObject(type, name, data, datName):
#    createObjectAndData(args, typ):
#
    
def parseObject(args, tokens):
    if verbosity > 2:
        print( "Parsing object %s" % args )
    name = args[0]
    typ = args[1]
    datName = args[2]
    try:
        data = loadedData[typ.capitalize()][datName]    
    except:
        data = None

    if data == None and typ != 'EMPTY':
        print("Failed to find data: %s %s %s" % (name, typ, datName))
        return

    try:
        ob = loadedData['Object'][name]
        bpy.context.scene.objects.active = ob
        #print("Found data")
    except:
        ob = createObject(typ, name, data, datName)
    if bpy.context.object != ob:
        print("Context", ob, bpy.context.object, bpy.context.scene.objects.active)
        # ob = foo 

    for (key, val, sub) in tokens:
        if key == 'Modifier':
            parseModifier(ob, val, sub)
        elif key == 'Constraint':
            parseConstraint(ob.constraints, val, sub)
        elif key == 'AnimationData':
            if eval(val[0]):
                parseAnimationData(ob, sub)
        elif key == 'ParticleSystem':
            parseParticleSystem(ob, val, sub)
        else:
            defaultKey(key, val, sub, "ob", ['type', 'data'], globals(), locals())

    # Needed for updating layers
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.object.mode_set(mode='OBJECT')
    return

def createObject(typ, name, data, datName):
    #print( "Creating object %s %s %s" % (typ, name, data) )    
    ob = bpy.data.objects.new(name, data)
    loadedData[typ][datName] = data
    loadedData['Object'][name] = ob
    return ob
    
def linkObject(ob, data):
    #print("Data", data, ob.data)
    if data and ob.data == None:
        ob.data = data
    scn = bpy.context.scene
    scn.objects.link(ob)
    scn.objects.active = ob
    #print("Linked object", ob)
    #print("Scene", scn)
    #print("Active", scn.objects.active)
    #print("Context", bpy.context.object)
    return ob

def createObjectAndData(args, typ):
    datName = args[0]
    obName = args[1]
    bpy.ops.object.add(type=typ.upper())
    ob = bpy.context.object
    ob.name = obName
    ob.data.name = datName
    loadedData[typ][datName] = ob.data
    loadedData['Object'][obName] = ob
    return ob.data


#
#    parseModifier(ob, args, tokens):
#

def parseModifier(ob, args, tokens):
    name = args[0]
    typ = args[1]
    if typ == 'PARTICLE_SYSTEM':
        return None
    mod = ob.modifiers.new(name, typ)
    for (key, val, sub) in tokens:
        defaultKey(key, val, sub, 'mod', [], globals(), locals())
    return mod

#
#    parseParticleSystem(ob, args, tokens):
#    parseParticles(particles, args, tokens):
#    parseParticle(par, args, tokens):
#

def parseParticleSystem(ob, args, tokens):
    print(ob, bpy.context.object)
    pss = ob.particle_systems
    print(pss, pss.values())
    name = args[0]
    typ = args[1]
    #psys = pss.new(name, typ)
    bpy.ops.object.particle_system_add()
    print(pss, pss.values())
    psys = pss[-1]
    psys.name = name
    psys.settings.type = typ
    loadedData['ParticleSystem'][name] = psys
    print("Psys", psys)

    for (key, val, sub) in tokens:
        if key == 'Particles':
            parseParticles(psys, val, sub)
        else:
            defaultKey(key, val, sub, 'psys', [], globals(), locals())
    return psys

def parseParticles(psys, args, tokens):
    particles = psys.particles
    bpy.ops.particle.particle_edit_toggle()
    n = 0
    for (key, val, sub) in tokens:
        if key == 'Particle':
            parseParticle(particles[n], val, sub)
            n += 1
        else:
            for par in particles:
                defaultKey(key, val, sub, 'par', [], globals(), locals())
    bpy.ops.particle.particle_edit_toggle()
    return particles

def parseParticle(par, args, tokens):
    n = 0
    for (key, val, sub) in tokens:
        if key == 'h':
            h = par.is_hair[n]
            h.location = eval(val[0])
            h.time = int(val[1])
            h.weight = float(val[2])
            n += 1
        elif key == 'location':
            par.location = eval(val[0])
    return

#
#    unpackList(list_of_tuples):
#

def unpackList(list_of_tuples):
    l = []
    for t in list_of_tuples:
        l.extend(t)
    return l

#
#    parseMesh (args, tokens):
#

def parseMesh (args, tokens):
    global todo
    if verbosity > 2:
        print( "Parsing mesh %s" % args )

    mename = args[0]
    obname = args[1]
    me = bpy.data.meshes.new(mename)
    ob = createObject('Mesh', obname, me, mename)

    verts = []
    edges = []
    faces = []
    vertsTex = []
    texFaces = []

    for (key, val, sub) in tokens:
        if key == 'Verts':
            verts = parseVerts(sub)
        elif key == 'Edges':
            edges = parseEdges(sub)
        elif key == 'Faces':
            faces = parseFaces(sub)

    if faces:
        #x = me.from_pydata(verts, [], faces)
        me.vertices.add(len(verts))
        me.faces.add(len(faces))
        me.vertices.foreach_set("co", unpackList(verts))
        me.faces.foreach_set("vertices_raw", unpackList(faces))
    else:
        #x = me.from_pydata(verts, edges, [])
        me.vertices.add(len(verts))
        me.edges.add(len(edges))
        me.vertices.foreach_set("co", unpackList(verts))
        me.edges.foreach_set("vertices", unpackList(edges))
    #print(x)
    me.update()
    #print(me)
    linkObject(ob, me)
        
    mats = []
    for (key, val, sub) in tokens:
        if key in ('Verts', 'Edges'):
            pass
        elif key == 'Faces':
            parseFaces2(sub, me)
        elif key == 'MeshTextureFaceLayer':
            parseUvTexture(val, sub, me)
        elif key == 'MeshColorLayer':
            parseVertColorLayer(val, sub, me)
        elif key == 'VertexGroup':
            parseVertexGroup(ob, me, val, sub)
        elif key == 'ShapeKeys':
            parseShapeKeys(ob, me, val, sub)
        elif key == 'Material':
            try:
                me.materials.link(loadedData['Material'][val[0]])
            except:
                print("Could not add material", val[0])
        else:
            defaultKey(key, val,  sub, "me", [], globals(), locals())

    return me

#
#    parseVerts(tokens):
#    parseEdges(tokens):
#    parseFaces(tokens):
#    parseFaces2(tokens, me):        
#

def parseVerts(tokens):
    verts = []
    for (key, val, sub) in tokens:
        if key == 'v':
            verts.append( (float(val[0]), float(val[1]), float(val[2])) )
    return verts

def parseEdges(tokens):
    edges = []
    for (key, val, sub) in tokens:
        if key == 'e':
            edges.append((int(val[0]), int(val[1])))
    return edges
    
def parseFaces(tokens):    
    faces = []
    for (key, val, sub) in tokens:
        if key == 'f':
            if len(val) == 3:
                face = [int(val[0]), int(val[1]), int(val[2]), 0]
            elif len(val) == 4:
                face = [int(val[0]), int(val[1]), int(val[2]), int(val[3])]
            faces.append(face)
    return faces

def parseFaces2(tokens, me):    
    n = 0
    for (key, val, sub) in tokens:
        if key == 'ft':
            f = me.faces[n]
            f.material_index = int(val[0])
            f.use_smooth = int(val[1])
            n += 1
        elif key == 'ftall':
            mat = int(val[0])
            smooth = int(val[1])
            for f in me.faces:
                f.material_index = mat
                f.use_smooth = smooth
    return


#
#    parseUvTexture(args, tokens, me):
#    parseUvTexData(args, tokens, uvdata):
#

def parseUvTexture(args, tokens, me):
    name = args[0]
    uvtex = me.uv_textures.new(name)
    loadedData['MeshTextureFaceLayer'][name] = uvtex
    for (key, val, sub) in tokens:
        if key == 'Data':
            parseUvTexData(val, sub, uvtex.data)
        else:
            defaultKey(key, val,  sub, "uvtex", [], globals(), locals())
    return

def parseUvTexData(args, tokens, data):
    n = 0
    for (key, val, sub) in tokens:
        if key == 'vt':
            data[n].uv1 = (float(val[0]), float(val[1]))
            data[n].uv2 = (float(val[2]), float(val[3]))
            data[n].uv3 = (float(val[4]), float(val[5]))
            if len(val) > 6:
                data[n].uv4 = (float(val[6]), float(val[7]))
            n += 1    
        else:
            pass
            #for i in range(n):
            #    defaultKey(key, val,  sub, "data[i]", [], globals(), locals())
    return

#
#    parseVertColorLayer(args, tokens, me):
#    parseVertColorData(args, tokens, data):
#

def parseVertColorLayer(args, tokens, me):
    name = args[0]
    print("VertColorLayer", name)
    vcol = me.vertex_colors.new(name)
    loadedData['MeshColorLayer'][name] = vcol
    for (key, val, sub) in tokens:
        if key == 'Data':
            parseVertColorData(val, sub, vcol.data)
        else:
            defaultKey(key, val,  sub, "vcol", [], globals(), locals())
    return

def parseVertColorData(args, tokens, data):
    n = 0
    for (key, val, sub) in tokens:
        if key == 'cv':
            data[n].color1 = eval(val[0])
            data[n].color2 = eval(val[1])
            data[n].color3 = eval(val[2])
            data[n].color4 = eval(val[3])
            n += 1    
    return


#
#    parseVertexGroup(ob, me, args, tokens):
#

def parseVertexGroup(ob, me, args, tokens):
    global toggle
    if verbosity > 2:
        print( "Parsing vertgroup %s" % args )
    grpName = args[0]
    try:
        res = eval(args[1])
    except:
        res = True
    if not res:
        return

    if (toggle & T_Armature) or (grpName in ['Eye_L', 'Eye_R', 'Gums', 'Head', 'Jaw', 'Left', 'Middle', 'Right', 'Scalp']):
        group = ob.vertex_groups.new(grpName)
        group.name = grpName
        loadedData['VertexGroup'][grpName] = group
        ob.vertex_groups.assign([int(val[0]) for (key, val, sub) in tokens if key == 'wv'], group, float(val[1]), 'REPLACE')
    return


#
#    parseShapeKeys(ob, me, args, tokens):
#    parseShapeKey(ob, me, args, tokens):
#    addShapeKey(ob, name, vgroup, tokens):
#    doShape(name):
#

def doShape(name):
    if (toggle & T_Shape+T_Face) and (name == 'Basis'):
        return True
    else:
        return (toggle & T_Face)

def parseShapeKeys(ob, me, args, tokens):
    if bpy.context.object == None:
        return
    for (key, val, sub) in tokens:
        if key == 'ShapeKey':
            parseShapeKey(ob, me, val, sub)
        elif key == 'AnimationData':
            if me.shape_keys:
                parseAnimationData(me.shape_keys, sub)
    return


def parseShapeKey(ob, me, args, tokens):
    if verbosity > 0:
        print( "Parsing ob %s shape %s" % (bpy.context.object, args[0] ))
    name = args[0]
    lr = args[1]
    if invalid(args[2]):
        return

    if lr == 'Sym' or toggle & T_Symm:
        addShapeKey(ob, name, None, tokens)
    elif lr == 'LR':
        addShapeKey(ob, name+'_L', 'Left', tokens)
        addShapeKey(ob, name+'_R', 'Right', tokens)
    else:
        raise NameError("ShapeKey L/R %s" % lr)
    return

def addShapeKey(ob, name, vgroup, tokens):
    bpy.ops.object.shape_key_add(False)
    skey = ob.active_shape_key
    if name != 'Basis':
        skey.relative_key = loadedData['ShapeKey']['Basis']
    skey.name = name
    if vgroup:
        skey.vertex_group = vgroup
    loadedData['ShapeKey'][name] = skey

    for (key, val, sub) in tokens:
        if key == 'sv':
            index = int(val[0])
            pt = skey.data[index].co
            pt[0] += float(val[1])
            pt[1] += float(val[2])
            pt[2] += float(val[3])
        else:
            defaultKey(key, val,  sub, "skey", [], globals(), locals())

    return    

    
#
#    parseArmature (obName, args, tokens)
#

def parseArmature (args, tokens):
    global toggle,  theScale
    if verbosity > 2:
        print( "Parsing armature %s" % args )
    
    amtname = args[0]
    obname = args[1]
    mode = args[2]
    
    if mode == 'Rigify':
        toggle |= T_Rigify
        theScale = 0.1
        return parseRigify(amtname, obname, tokens)

    toggle &= ~T_Rigify
    theScale = 1.0
    amt = bpy.data.armatures.new(amtname)
    ob = createObject('Armature', obname, amt, amtname)    

    linkObject(ob, amt)
    print("Linked")

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')

    heads = {}
    tails = {}
    for (key, val, sub) in tokens:
        if key == 'Bone':
            bname = val[0]
            if not invalid(val[1]):
                bone = amt.edit_bones.new(bname)
                parseBone(bone, amt.edit_bones, sub, heads, tails)
                loadedData['Bone'][bname] = bone
        else:
            defaultKey(key, val,  sub, "amt", ['MetaRig'], globals(), locals())
    bpy.ops.object.mode_set(mode='OBJECT')
    return amt

#
#    parseRigify(amtname, obname, tokens):        
#

def parseRigify(amtname, obname, tokens):        
    (key,val,sub) = tokens[0]
    if key != 'MetaRig':
        raise NameError("Expected MetaRig")
    typ = val[0]
    if typ == "human":
        bpy.ops.object.armature_human_advanced_add()
    else:
        bpy.ops.pose.metarig_sample_add(type = typ)
    ob = bpy.context.scene.objects.active
    amt = ob.data
    loadedData['Rigify'][obname] = ob
    loadedData['Armature'][amtname] = amt
    loadedData['Object'][obname] = ob
    print("Rigify object", ob, amt)

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')

    heads = {}
    tails = {}
    for (bname, bone) in amt.edit_bones.items():
        heads[bname] = 10*theScale*bone.head
        tails[bname] = 10*theScale*bone.tail

    for (key, val, sub) in tokens:
        if key == 'Bone':
            bname = val[0]
            print("Bone", bname)
            try:
                bone = amt.edit_bones[bname]
            except:
                print("Did not find bone %s" % bname)
                bone = None
            print(" -> ", bone)
            if bone:
                parseBone(bone, amt.edit_bones, sub, heads, tails)
        else:
            defaultKey(key, val,  sub, "amt", ['MetaRig'], globals(), locals())
    bpy.ops.object.mode_set(mode='OBJECT')
    return amt
        
#
#    parseBone(bone, bones, tokens, heads, tails):
#

def parseBone(bone, bones, tokens, heads, tails):
    global todo

    for (key, val, sub) in tokens:
        if key == "head":
            bone.head = (float(val[0]), float(val[1]), float(val[2]))
        elif key == "tail":
            bone.tail = (float(val[0]), float(val[1]), float(val[2]))
        elif key == "head-as":
            target = val[0]
            if val[1] == 'head':
                bone.head = heads[bone.name] + bones[target].head - heads[target]
            elif val[1] == 'tail':
                bone.head = heads[bone.name] + bones[target].tail - tails[target]
            else:
                raise NameError("head-as %s" % val)
        elif key == "tail-as":
            target = val[0]
            if val[1] == 'head':
                bone.tail = tails[bone.name] + bones[target].head - heads[target]
            elif val[1] == 'tail':
                bone.tail = tails[bone.name] + bones[target].tail - tails[target]
            else:
                raise NameError("tail-as %s" % val)
        elif key == 'hide_select':
            pass
        else:
            defaultKey(key, val,  sub, "bone", [], globals(), locals())

    return bone

#
#    parsePose (args, tokens):
#

def parsePose (args, tokens):
    global todo
    if toggle & T_Rigify:
        return
    name = args[0]
    ob = loadedData['Object'][name]
    bpy.context.scene.objects.active = ob
    bpy.ops.object.mode_set(mode='POSE')
    pbones = ob.pose.bones    
    nGrps = 0
    for (key, val, sub) in tokens:
        if key == 'Posebone':
            parsePoseBone(pbones, ob, val, sub)
        elif key == 'BoneGroup':
            parseBoneGroup(ob.pose, nGrps, val, sub)
            nGrps += 1
        elif key == 'SetProp':
            bone = val[0]
            prop = val[1]
            value = eval(val[2])
            pb = pbones[bone]
            print("Setting", pb, prop, val)
            pb[prop] = value
            print("Prop set", pb[prop])
        else:
            defaultKey(key, val,  sub, "ob.pose", [], globals(), locals())
    bpy.ops.object.mode_set(mode='OBJECT')
    return ob


#
#    parsePoseBone(pbones, args, tokens):
#    parseArray(data, exts, args):
#

def parseBoneGroup(pose, nGrps, args, tokens):
    global todo
    return
    print( "Parsing bonegroup %s" % args )
    name = args[0]
    print(dir(pose.bone_groups))
    bg = pose.bone_groups.add()
    print("Created", bg)
    loadedData['BoneGroup'][name] = bg
    for (key, val, sub) in tokens:
        defaultKey(key, val,  sub, "bg", [], globals(), locals())
    return

def parsePoseBone(pbones, ob, args, tokens):
    global todo
    #print( "Parsing posebone %s" % args )
    if invalid(args[1]):
        return
    name = args[0]
    pb = pbones[name]

    # Make posebone active - don't know how to do this in pose mode
    bpy.ops.object.mode_set(mode='OBJECT')
    ob.data.bones.active = pb.bone
    bpy.ops.object.mode_set(mode='POSE')

    for (key, val, sub) in tokens:
        if key == 'Constraint':
            cns = parseConstraint(pb.constraints, val, sub)
        elif key == 'bpyops':
            expr = "bpy.ops.%s" % val[0]
            print(expr)
            print("ob", bpy.context.active_object)
            print("b", bpy.context.active_bone)
            print("pb", bpy.context.active_pose_bone)
            print("md", bpy.context.mode)
            exec(expr)
            print("show_alive")
        elif key == 'ik_dof':
            parseArray(pb, ["lock_ik_x", "lock_ik_y", "lock_ik_z"], val)
        elif key == 'ik_limit':
            parseArray(pb, ["use_ik_limit_x", "use_ik_limit_y", "use_ik_limit_z"], val)
        elif key == 'ik_max':
            parseArray(pb, ["ik_max_x", "ik_max_y", "ik_max_z"], val)
        elif key == 'ik_min':
            parseArray(pb, ["ik_min_x", "ik_min_y", "ik_min_z"], val)
        elif key == 'ik_stiffness':
            parseArray(pb, ["ik_stiffness_x", "ik_stiffness_y", "ik_stiffness_z"], val)
        else:
            defaultKey(key, val,  sub, "pb", [], globals(), locals())
    #print("pb %s done" % name)
    return

def parseArray(data, exts, args):
    n = 1
    for ext in exts:
        expr = "data.%s = %s" % (ext, args[n])
        # print(expr)
        exec(expr)
        n += 1
    return
        
#
#    parseConstraint(constraints, args, tokens)
#

def parseConstraint(constraints, args, tokens):
    if invalid(args[2]):
        return None
    cns = constraints.new(args[1])
    #bpy.ops.pose.constraint_add(type=args[1])
    #cns = pb.constraints[-1]

    cns.name = args[0]
    #print("cns", cns.name)
    for (key,val,sub) in tokens:
        if key == 'invert':
            parseArray(cns, ["invert_x", "invert_y", "invert_z"], val)
        elif key == 'use':
            parseArray(cns, ["use_x", "use_y", "use_z"], val)
        elif key == 'pos_lock':
            parseArray(cns, ["lock_location_x", "lock_location_y", "lock_location_z"], val)
        elif key == 'rot_lock':
            parseArray(cns, ["lock_rotation_x", "lock_rotation_y", "lock_rotation_z"], val)
        else:
            defaultKey(key, val,  sub, "cns", [], globals(), locals())
    #print("cns %s done" % cns.name)
    return cns
    
def insertInfluenceIpo(cns, bone):
    global todo
    if bone != 'PArmIK_L' and bone != 'PArmIK_R' and bone != 'PLegIK_L' and bone != 'PLegIK_R':
        return False

    if (toggle & T_FKIK):
        fcurve = cns.driver_add("influence", 0)
        fcurve.driver.type = 'AVERAGE'

        var = fcurve.driver.variables.new()
        var.name = bone
        var.targets[0].id_type = 'OBJECT'
        var.targets[0].id = getObject('HumanRig', 'var.targets[0].id', globals(), locals())
        var.targets[0].bone_target = bone
        var.targets[0].transform_type = 'LOC_X'
        # controller_path = fk_chain.arm_p.path_to_id()
        #var.targets[0].data_path = controller_path + '["use_hinge"]'

        mod = fcurve.modifiers[0]
        mod.poly_order = 2
        mod.coefficients[0] = 0.0
        mod.coefficients[1] = 1.0
    elif bone == 'PArmIK_L' or bone == 'PArmIK_R':
        if toggle & T_ArmIK:
            cns.influence = 1.0
        else:
            cns.influence = 0.0
    elif bone == 'PLegIK_L' or bone == 'PLegIK_R':
        if toggle & T_LegIK:
            cns.influence = 1.0
        else:
            cns.influence = 0.0

    return True

#
#    parseCurve (args, tokens):
#    parseNurb(cu, nNurbs, args, tokens):
#    parseBezier(nurb, n, args, tokens):
#

def parseCurve (args, tokens):
    global todo
    if verbosity > 2:
        print( "Parsing curve %s" % args )
    cu = createObjectAndData(args, 'Curve')

    nNurbs = 0
    for (key, val, sub) in tokens:
        if key == 'Nurb':
            parseNurb(cu, nNurbs, val, sub)
            nNurbs += 1
        else:
            defaultKey(key, val, sub, "cu", [], globals(), locals())
    return

def parseNurb(cu, nNurbs, args, tokens):
    if nNurbs > 0:
        bpy.ops.object.curve_add(type='BEZIER_CURVE')
    print(cu.splines, list(cu.splines), nNurbs)
    nurb = cu.splines[nNurbs]
    nPoints = int(args[0])
    print(nurb, nPoints)
    for n in range(2, nPoints):
        bpy.ops.curve.extrude(mode=1)        

    n = 0
    for (key, val, sub) in tokens:
        if key == 'bz':
            parseBezier(nurb, n, val, sub)
            n += 1
        elif key == 'pt':
            parsePoint(nurb, n, val, sub)
            n += 1
        else:
            defaultKey(key, val, sub, "nurb", [], globals(), locals())
    return
    
def parseBezier(nurb, n, args, tokens):
    bez = nurb[n]
    bez.co = eval(args[0])    
    bez.handle_left = eval(args[1])    
    bez.handle_left_type = args[2]
    bez.handle_right = eval(args[3])    
    bez.handle_right_type = args[4]
    return

def parsePoint(nurb, n, args, tokens):
    pt = nurb[n]
    pt.co = eval(args[0])
    return

#
#    parseLattice (args, tokens):
#

def parseLattice (args, tokens):
    global todo
    if verbosity > 2:
        print( "Parsing lattice %s" % args )
    lat = createObjectAndData(args, 'Lattice')    
    for (key, val, sub) in tokens:
        if key == 'Points':
            parseLatticePoints(val, sub, lat.points)
        else:
            defaultKey(key, val, sub, "lat", [], globals(), locals())
    return

def parseLatticePoints(args, tokens, points):
    global todo
    n = 0
    for (key, val, sub) in tokens:
        if key == 'pt':
            v = points[n].co
            (x,y,z) = eval(val[0])
            v.x = x
            v.y = y
            v.z = z

            v = points[n].co_deform
            (x,y,z) = eval(val[1])
            v.x = x
            v.y = y
            v.z = z

            n += 1
    return

#
#    parseGroup (args, tokens):
#

def parseGroup (args, tokens):
    global todo
    if verbosity > 2:
        print( "Parsing group %s" % args )

    grpName = args[0]
    grp = bpy.data.groups.new(grpName)
    loadedData['Group'][grpName] = grp
    for (key, val, sub) in tokens:
        if key == 'Objects':
            parseGroupObjects(val, sub, grp)
        else:
            defaultKey(key, val, sub, "grp", [], globals(), locals())
    return

def parseGroupObjects(args, tokens, grp):
    global todo
    for (key, val, sub) in tokens:
        if key == 'ob':
            try:
                ob = loadedData['Object'][val[0]]
                grp.objects.link(ob)
            except:
                pass
    return

#
#    postProcess()
#    setInfluence(bones, cnsName, w):
#

def postProcess():
    if not toggle & T_MHX:
        return
    if toggle & T_Rigify:
        return
        for rig in loadedData['Rigify'].values():
            bpy.context.scene.objects.active = rig
            print("Rigify", rig)
            bpy.ops.pose.metarig_generate()
            print("Metarig generated")
            #bpy.context.scene.objects.unlink(rig)
            rig = bpy.context.scene.objects.active
            print("Rigged", rig, bpy.context.object)
            ob = loadedData['Object']['Human']
            mod = ob.modifiers[0]
            print(ob, mod, mod.object)
            mod.object = rig
            print("Rig changed", mod.object)
    return            
        
#
#    parseProcess(args, tokens):
#

def parseProcess(args, tokens):
    return
    rig = loadedData['Object'][args[0]]
    parents = {}
    objects = []

    for (key, val, sub) in tokens:
        if key == 'Reparent':
            bname = val[0]
            try:
                eb = ebones[bname]
                parents[bname] = eb.parent.name
                eb.parent = ebones[val[1]]
            except:
                pass
        elif key == 'Bend':
            print(val)
            axis = val[1]
            angle = float(val[2])
            mat = mathutils.Matrix.Rotation(angle, 4, axis)
            try:
                pb = pbones[val[0]]
                prod = pb.matrix_local * mat
                for i in range(4):
                    for j in range(4):
                        pb.matrix_local[i][j] = prod[i][j]
                print("Done", pb.matrix_local)
            except:
                pass
        elif key == 'Pose':
            bpy.context.scene.objects.active = rig
            bpy.ops.object.mode_set(mode='POSE')
            pbones = rig.pose.bones    
        elif key == 'Edit':
            bpy.context.scene.objects.active = rig
            bpy.ops.object.mode_set(mode='EDIT')
            ebones = rig.data.edit_bones    
        elif key == 'Object':
            bpy.ops.object.mode_set(mode='OBJECT')
            try:
                ob = loadedData['Object'][val[0]]
                objects.append((ob,sub))
            except:
                ob = None
            if ob:
                bpy.context.scene.objects.active = ob
                mod = ob.modifiers[0]
                ob.modifiers.remove(mod)
                for (key1, val1, sub1) in sub:
                    if key1 == 'Modifier':
                        parseModifier(ob, val1, sub1)

    for (ob,tokens) in objects:
        bpy.context.scene.objects.active = ob
        bpy.ops.object.visual_transform_apply()
        #print("vis", list(ob.modifiers))
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier='Armature')
        #print("app", list(ob.modifiers))

    bpy.context.scene.objects.active = rig
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.armature_apply()
    bpy.ops.object.mode_set(mode='EDIT')
    ebones = rig.data.edit_bones
    for (bname, pname) in parents.items():
        eb = ebones[bname]
        par = ebones[pname]
        if eb.use_connect:
            par.tail = eb.head
        eb.parent = par
    bpy.ops.object.mode_set(mode='OBJECT')

    for (ob,tokens) in objects:
        bpy.context.scene.objects.active = ob
        for (key, val, sub) in tokens:
            if key == 'Modifier':
                parseModifier(ob, val, sub)

    return            

#
#    defaultKey(ext, args, tokens, var, exclude, glbals, lcals):
#

def defaultKey(ext, args, tokens, var, exclude, glbals, lcals):
    global todo

    if ext == 'Property':
        expr = "%s['%s'] = %s" % (var, args[0], args[1])
        print("Property", expr)
        exec(expr, glbals, lcals)
        #print("execd")
        return
        
    nvar = "%s.%s" % (var, ext)
    # print(ext)
    if ext in exclude:
        return
    #print("D", nvar)

    if len(args) == 0:
        raise NameError("Key length 0: %s" % ext)
        
    rnaType = args[0]
    if rnaType == 'Add':
        print("*** Cannot Add yet ***")
        return

    elif rnaType == 'Refer':
        typ = args[1]
        name = args[2]
        data = "loadedData['%s']['%s']" % (typ, name)

    elif rnaType == 'Struct' or rnaType == 'Define':
        typ = args[1]
        name = args[2]
        try:
            data = eval(nvar, glbals, lcals)
        except:
            data = None            
        # print("Old structrna", nvar, data)

        if data == None:
            try:
                creator = args[3]
            except:
                creator = None
            # print("Creator", creator, eval(var,glbals,lcals))

            try:
                rna = eval(var,glbals,lcals)
                data = eval(creator)
            except:
                data = None    
            # print("New struct", nvar, typ, data)

        if rnaType == 'Define':
            loadedData[typ][name] = data

        if data:
            for (key, val, sub) in tokens:
                defaultKey(key, val, sub, "data", [], globals(), locals())

        print("Struct done", nvar)
        return

    elif rnaType == 'PropertyRNA':
        raise NameError("PropertyRNA!")
        #print("PropertyRNA ", ext, var)
        for (key, val, sub) in tokens:
            defaultKey(ext, val, sub, nvar, [], glbals, lcals)
        return

    elif rnaType == 'Array':
        for n in range(1, len(args)):
            expr = "%s[%d] = %s" % (nvar, n-1, args[n])
            exec(expr, glbals, lcals)
        if len(args) > 0:
            expr = "%s[0] = %s" % (nvar, args[1])
            exec(expr, glbals, lcals)            
        return
        
    elif rnaType == 'List':
        data = []
        for (key, val, sub) in tokens:
            elt = eval(val[1], glbals, lcals)
            data.append(elt)

    elif rnaType == 'Matrix':
        return
        i = 0
        n = len(tokens)
        for (key, val, sub) in tokens:
            if key == 'row':    
                for j in range(n):
                    expr = "%s[%d][%d] = %g" % (nvar, i, j, float(val[j]))
                    exec(expr, glbals, lcals)
                i += 1
        return

    else:
        try:
            data = loadedData[rnaType][args[1]]
            #print("From loaded", rnaType, args[1], data)
            return data
        except:
            data = rnaType

    #print(var, ext, data)
    expr = "%s = %s" % (nvar, data)
    try:
        exec(expr, glbals, lcals)
    except:
        #print("Failed ",expr)
        todo.append((expr, glbals, lcals))
    return
            
#
#    parseBoolArray(mask):
#

def parseBoolArray(mask):
    list = []
    for c in mask:
        if c == '0':            
            list.append(False)
        else:
            list.append(True)
    return list

#    parseMatrix(args, tokens)
#

def parseMatrix(args, tokens):
    matrix = Matrix( [1,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,1] )
    i = 0
    for (key, val, sub) in tokens:
        if key == 'row':    
            matrix[i][0] = float(val[0])
            matrix[i][1] = float(val[1])
            matrix[i][2] = float(val[2])
            matrix[i][3] = float(val[3])
            i += 1
    return matrix

#
#    parseDefault(data, tokens, exclude):
#

def parseDefault(data, tokens):
    for (key, val, sub) in tokens:    
        defaultKey(key, val, sub, "data", exclude, globals(), locals())


#
#    Utilities    
#

#
#    extractBpyType(data):
#

def extractBpyType(data):
    typeSplit = str(type(data)).split("'")
    if typeSplit[0] != '<class ':
        return None
    classSplit = typeSplit[1].split(".")
    if classSplit[0] == 'bpy' and classSplit[1] == 'types':
        return classSplit[2]
    elif classSplit[0] == 'bpy_types':
        return classSplit[1]
    else:
        return None

#
#    Bool(string):
#

def Bool(string):
    if string == 'True':
        return True
    elif string == 'False':
        return False
    else:
        raise NameError("Bool %s?" % string)
        
#
#    invalid(condition):
#

def invalid(condition):
    global rigLeg, rigArm, toggle
    res = eval(condition, globals())
    try:
        res = eval(condition, globals())
        #print("%s = %s" % (condition, res))
        return not res
    except:
        #print("%s invalid!" % condition)
        return True
    
#
#    clearScene(context):
#    hideLayers():
#
    
def clearScene():
    global toggle
    scn = bpy.context.scene
    for n in range(len(scn.layers)):
        scn.layers[n] = True
    print("clearScene %s %s" % (toggle & T_Replace, scn))
    if not toggle & T_Replace:
        return scn

    for ob in scn.objects:
        if ob.type == "MESH" or ob.type == "ARMATURE":
            scn.objects.active = ob
            bpy.ops.object.mode_set(mode='OBJECT')
            scn.objects.unlink(ob)
            del ob
    #print(scn.objects)
    return scn

def hideLayers():
    scn = bpy.context.scene
    for n in range(len(scn.layers)):
        if n < 3:
            scn.layers[n] = True
        else:
            scn.layers[n] = False
    return

#
#    User interface
#

DEBUG= False
from bpy.props import *

class IMPORT_OT_makehuman_mhx(bpy.types.Operator):
    '''Import from MHX file format (.mhx)'''
    bl_idname = "import_scene.makehuman_mhx"
    bl_description = 'Import from MHX file format (.mhx)'
    bl_label = "Import MHX"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"

    filepath = StringProperty(name="File Path", description="Filepath used for importing the MHX file", maxlen= 1024, default= "")

    #preset = BoolProperty(name="Use rig preset", description="Use rig preset (Classic/Gobo)?", default=True)
    #presetRig = EnumProperty(name="Rig", description="Choose preset rig", 
    #    items = [('Classic','Classic','Classic'), ('Gobo','Gobo','Gobo')], default = '1')
    footRig = EnumProperty(name="Foot rig", description="Foot rig", 
        items = [('Reverse foot','Reverse foot','Reverse foot'), ('Gobo','Gobo','Gobo')], default = '1')
    fingerRig = EnumProperty(name="Finger rig", description="Finger rig", 
        items = [('Panel','Panel','Panel'), ('Curl','Curl','Curl'), ('IK','IK','IK')], default = '1')

    mesh = BoolProperty(name="Mesh", description="Use main mesh", default=toggle&T_Mesh)
    armature = BoolProperty(name="Armature", description="Use armature", default=toggle&T_Armature)
    proxy = BoolProperty(name="Proxy", description="Use proxy object", default=toggle&T_Proxy)
    replace = BoolProperty(name="Replace scene", description="Replace scene", default=toggle&T_Replace)
    face = BoolProperty(name="Face shapes", description="Include facial shapekeys", default=toggle&T_Face)
    shape = BoolProperty(name="Body shapes", description="Include body shapekeys", default=toggle&T_Shape)
    symm = BoolProperty(name="Symmetric shapes", description="Keep shapekeys symmetric", default=toggle&T_Symm)
        
    def execute(self, context):
        global toggle
        O_Mesh = T_Mesh if self.properties.mesh else 0
        O_Armature = T_Armature if self.properties.armature else 0
        O_Proxy = T_Proxy if self.properties.proxy else 0
        O_Replace = T_Replace if self.properties.replace else 0
        O_Face = T_Face if self.properties.face else 0
        O_Shape = T_Shape if self.properties.shape else 0
        O_Symm = T_Symm if self.properties.symm else 0
        #O_Preset = T_Preset if self.properties.preset else 0
        toggle =  O_Mesh | O_Armature | O_Proxy | T_ArmIK | T_LegIK | O_Replace | O_Face | O_Shape | O_Symm | T_MHX 

        
        readMhxFile(self.properties.filepath,     
            (self.properties.footRig, 
            self.properties.fingerRig))
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.add_fileselect(self)
        return {'RUNNING_MODAL'}

'''
class MakeHumanFKIKPanel(bpy.types.Panel):
    bl_label = "MakeHuman FK/IK"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    
    def draw(self, context):
        layout = self.layout
        ob = bpy.context.active_object
        if ob.type == 'ARMATURE':
            layout.row().prop(ob, "PArmIK_L")
            layout.row().prop(ob, "PArmIK_R")
            layout.row().prop(ob, "PLegIK_L")
            layout.row().prop(ob, "PLegIK_R")

            layout.row().prop(ob, "PHandLocal_L")
            layout.row().prop(ob, "PHandLocal_R")
            layout.row().prop(ob, "PFootLocal_L")
            layout.row().prop(ob, "PFootLocal_R")
        return
          
class MakeHumanFingerPanel(bpy.types.Panel):
    bl_label = "MakeHuman Fingers"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    
    def draw(self, context):
        layout = self.layout
        pb = bpy.context.active_pose_bone
        layout.row().prop(pb, "MHRelax")
        layout.row().prop(pb, "MHCurl")
        layout.row().prop(pb, "MHCone")
        layout.row().prop(pb, "MHSpread")
        layout.row().prop(pb, "MHScrunch")
        layout.row().prop(pb, "MHLean")
        return
          

def registerPanels():
    bpy.types.Object.FloatProperty(attr="PArmIK_L", name="L arm - IK", default = 0, min = 0.0, max = 1.0)
    bpy.types.Object.FloatProperty(attr="PArmIK_R", name="R arm - IK", default = 0, min = 0.0, max = 1.0)
    bpy.types.Object.FloatProperty(attr="PLegIK_L", name="L leg - IK", default = 0, min = 0.0, max = 1.0)
    bpy.types.Object.FloatProperty(attr="PLegIK_R", name="R leg - IK", default = 0, min = 0.0, max = 1.0)

    bpy.types.Object.FloatProperty(attr="PHandLocal_L", name="L hand - Loc", default = 0, min = 0.0, max = 1.0)
    bpy.types.Object.FloatProperty(attr="PHandLocal_R", name="R hand - Loc", default = 0, min = 0.0, max = 1.0)
    bpy.types.Object.FloatProperty(attr="PFootLocal_L", name="L foot - Loc", default = 0, min = 0.0, max = 1.0)
    bpy.types.Object.FloatProperty(attr="PFootLocal_R", name="R foot - Loc", default = 0, min = 0.0, max = 1.0)

    bpy.types.PoseBone.FloatProperty(attr="MHCone", name="Cone", default = 0, min = -0.5, max = 1.0)
    bpy.types.PoseBone.FloatProperty(attr="MHRelax", name="Relax", default = 0, min = -0.5, max = 1.0)
    bpy.types.PoseBone.FloatProperty(attr="MHCurl", name="Curl", default = 0, min = -0.5, max = 1.0)
    bpy.types.PoseBone.FloatProperty(attr="MHLean", name="Lean", default = 0, min = -1.0, max = 1.0)
    bpy.types.PoseBone.FloatProperty(attr="MHScrunch", name="Scrunch", default = 0, min = -0.5, max = 1.0)
    bpy.types.PoseBone.FloatProperty(attr="MHSpread", name="Spread", default = 0, min = -0.5, max = 1.0)

    bpy.types.register(MakeHumanFKIKPanel)
    bpy.types.register(MakeHumanFingerPanel)

def unregisterPanels():
    bpy.types.unregister(MakeHumanFKIKPanel)
    bpy.types.unregister(MakeHumanFingerPanel)
    '''


def menu_func(self, context):
    self.layout.operator(IMPORT_OT_makehuman_mhx.bl_idname, text="MakeHuman (.mhx)...")


def register():
    bpy.types.INFO_MT_file_import.append(menu_func)


def unregister():
    bpy.types.INFO_MT_file_import.remove(menu_func)

if __name__ == "__main__":
    register()

#
#    Testing
#
"""
theScale = 1.0

toggle = T_Replace + T_Mesh + T_Armature + T_MHX + T_ArmIK + T_LegIK
#rigLeg = T_Toes + T_GoboFoot
#rigArm = T_ElbowPT + T_FingerCurl

#readMhxFile("/home/thomas/makehuman/exports/foo-25.mhx")

#toggle = T_Replace + T_Armature 
#readMhxFile("/home/thomas/makehuman/exports/foo-sintel-25.mhx")

readMhxFile("C:/Documents and Settings/xxxxxxxxxxxxxxxxxxxx/Mina dokument/makehuman/exports/foo-25.mhx", 'Classic')
#readMhxFile("/home/thomas/mhx5/test1.mhx")
#readMhxFile("/home/thomas/myblends/gobo/gobo.mhx")
#readMhxFile("/home/thomas/myblends/sintel/simple.mhx")
"""
