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

# Project Name:        MakeHuman
# Product Home Page:   http://www.makehuman.org/
# Code Home Page:      http://code.google.com/p/makehuman/
# Authors:             Thomas Larsson
# Script copyright (C) MakeHuman Team 2001-2011
# Coding Standards:    See http://sites.google.com/site/makehumandocs/developers-guide

"""
Abstract
MHX (MakeHuman eXchange format) importer for Blender 2.5x.
Version 1.9.0

This script should be distributed with Blender.
If not, place it in the .blender/scripts/addons dir
Activate the script in the "Addons" tab (user preferences).
Access from the File > Import menu.

Alternatively, run the script in the script editor (Alt-P), and access from the File > Import menu
"""

bl_info = {
    'name': 'Import: MakeHuman (.mhx)',
    'author': 'Thomas Larsson',
    'version': (1, 9, 1),
    "blender": (2, 5, 9),
    "api": 40335,
    'location': "File > Import > MakeHuman (.mhx)",
    'description': 'Import files in the MakeHuman eXchange format (.mhx)',
    'warning': '',
    'wiki_url': 'http://sites.google.com/site/makehumandocs/blender-export-and-mhx',
    'tracker_url': 'https://projects.blender.org/tracker/index.php?'\
        'func=detail&aid=21872',
    'category': 'Import-Export'}

MAJOR_VERSION = 1
MINOR_VERSION = 9
SUB_VERSION = 0
BLENDER_VERSION = (2, 59, 2)

#
#
#

import bpy
import os
import time
import mathutils
from bpy.props import *

MHX249 = False
Blender24 = False
Blender25 = True
TexDir = "~/makehuman/exports"

#
#
#

theScale = 1.0
One = 1.0/theScale
useMesh = 1
verbosity = 2
warnedTextureDir = False
warnedVersion = False

true = True
false = False
Epsilon = 1e-6
nErrors = 0
theTempDatum = None
theMessage = ""
theMhxFile = ""

todo = []

#
#    toggle flags
#

T_EnforceVersion = 0x01
T_Clothes = 0x02
T_Stretch = 0x04

T_Diamond = 0x10
T_Replace = 0x20
T_Face = 0x40
T_Shape = 0x80

T_Mesh = 0x100
T_Armature = 0x200
T_Proxy = 0x400
T_Cage = 0x800

T_Rigify = 0x1000
T_Opcns = 0x2000
T_Symm = 0x4000

toggle = (T_EnforceVersion + T_Replace + T_Mesh + T_Armature + 
        T_Face + T_Shape + T_Proxy + T_Clothes + T_Rigify)

#
#    setFlagsAndFloats(rigFlags):
#
#    Global floats
#fFingerPanel = 0.0
#fFingerIK = 0.0
fNoStretch = 0.0

#    rigLeg and rigArm flags
T_Toes = 0x0001
#T_GoboFoot = 0x0002

#T_InvFoot = 0x0010
#T_InvFootPT = 0x0020
#T_InvFootNoPT = 0x0040

#T_FingerPanel = 0x100
#T_FingerRot = 0x0200
#T_FingerIK = 0x0400


#T_LocalFKIK = 0x8000

#rigLeg = 0
#rigArm = 0

def setFlagsAndFloats():
    '''
    global toggle, rigLeg, rigArm

    (footRig, fingerRig) = rigFlags
    rigLeg = 0
    if footRig == 'Reverse foot': 
        rigLeg |= T_InvFoot
        if toggle & T_PoleTar:
            rigLeg |= T_InvFootPT
        else:
            rigLeg |= T_InvFootNoPT
    elif footRig == 'Gobo': rigLeg |= T_GoboFoot        

    rigArm = 0
    if fingerRig == 'Panel': rigArm |= T_FingerPanel
    elif fingerRig == 'Rotation': rigArm |= T_FingerRot
    elif fingerRig == 'IK': rigArm |= T_FingerIK

    toggle |= T_Panel
    '''
    global fNoStretch
    if toggle&T_Stretch: fNoStretch == 0.0
    else: fNoStretch = 1.0

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
    'Text' : {},

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
    'Text' : 'texts',
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
#    checkBlenderVersion()
#

def checkBlenderVersion():
    print("Found Blender", bpy.app.version)
    (A, B, C) = bpy.app.version
    (a, b, c) = BLENDER_VERSION
    if a <= A: return
    if b <= B: return
    if c <= C: return
    msg = (
"This version of the MHX importer only works with \n" +
"Blender (%d, %d, %d) or later.\n" % (a, b, c) +
"Download a more recent Blender from \n" +
"www.blender.org or www.graphicall.org.\n"
    )
    MyError(msg)
    return

#
#    readMhxFile(filePath):
#

def readMhxFile(filePath):
    global todo, nErrors, theScale, defaultScale, One, toggle, warnedVersion

    #checkBlenderVersion()    
    
    defaultScale = theScale
    One = 1.0/theScale
    warnedVersion = False

    fileName = os.path.expanduser(filePath)
    (shortName, ext) = os.path.splitext(fileName)
    if ext.lower() != ".mhx":
        print("Error: Not a mhx file: " + fileName)
        return
    print( "Opening MHX file "+ fileName )
    time1 = time.clock()

    # ignore = False  # UNUSED
    stack = []
    tokens = []
    key = "toplevel"
    level = 0
    nErrors = 0
    comment = 0
    nesting = 0

    setFlagsAndFloats()

    file= open(fileName, "rU")
    print( "Tokenizing" )
    lineNo = 0
    for line in file: 
        # print(line)
        lineSplit= line.split()
        lineNo += 1
        if len(lineSplit) == 0:
            pass
        elif lineSplit[0][0] == '#':
            if lineSplit[0] == '#if':
                if comment == nesting:
                    try:
                        res = eval(lineSplit[1])
                    except:
                        res = False
                    if res:
                        comment += 1
                nesting += 1
            elif lineSplit[0] == '#else':
                if comment == nesting-1:
                    comment += 1
                elif comment == nesting:
                    comment -= 1
            elif lineSplit[0] == '#endif':
                if comment == nesting:
                    comment -= 1
                nesting -= 1
        elif comment < nesting:
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
                stack.pop()
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
        MyError("Tokenizer out of kilter %d" % level)    
    clearScene()
    print( "Parsing" )
    parse(tokens)
    
    for (expr, glbals, lcals) in todo:
        try:
            print("Doing %s" % expr)
            exec(expr, glbals, lcals)
        except:
            msg = "Failed: \n"+expr
            print( msg )
            nErrors += 1
            #MyError(msg)

    time2 = time.clock()
    print("toggle = %x" % toggle)
    msg = "File %s loaded in %g s" % (fileName, time2-time1)
    if nErrors:
        msg += " but there where %d errors. " % (nErrors)
    print(msg)
    return

#
#    getObject(name, var, glbals, lcals):
#

def getObject(name, var, glbals, lcals):
    try:
        ob = loadedData['Object'][name]
    except:
        if name != "None":
            pushOnTodoList(None, "ob = loadedData['Object'][name]" % globals(), locals())
        ob = None
    return ob

#
#    checkMhxVersion(major, minor):
#

def checkMhxVersion(major, minor):
    global warnedVersion
    print("MHX", (major,minor), (MAJOR_VERSION, MINOR_VERSION), warnedVersion)
    if  major != MAJOR_VERSION or minor != MINOR_VERSION:
        if warnedVersion:
            return
        else:
            msg = (
"Wrong MHX version\n" +
"Expected MHX %d.%d but the loaded file " % (MAJOR_VERSION, MINOR_VERSION) +
"has version MHX %d.%d\n" % (major, minor))
            if minor < MINOR_VERSION:
                msg += (
"You can disable this error message by deselecting the \n" +
"Enforce version option when importing. Better:\n" +
"Export the MHX file again with an updated version of MakeHuman.\n" +
"The most up-to-date version of MakeHuman is the nightly build.\n")
            else:
                msg += (
"Download the most recent Blender build from www.graphicall.org. \n" +
"The most up-to-date version of the import script is distributed\n" +
"with Blender. It can also be downloaded from MakeHuman. \n" +
"It is located in the importers/mhx/blender25x \n" +
"folder and is called import_scene_mhx.py. \n")
        if (toggle & T_EnforceVersion or minor > MINOR_VERSION):
            MyError(msg)
        else:
            print(msg)
            warnedVersion = True
    return

#
#    parse(tokens):
#

ifResult = False

def parse(tokens):
    global MHX249, ifResult, theScale, defaultScale, One
    
    for (key, val, sub) in tokens:    
        print("Parse %s" % key)
        data = None
        if key == 'MHX':
            checkMhxVersion(int(val[0]), int(val[1]))
        elif key == 'MHX249':
            MHX249 = eval(val[0])
            print("Blender 2.49 compatibility mode is %s\n" % MHX249)
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
            MyError(msg)    
        elif key == 'NoScale':
            if eval(val[0]):
                theScale = 1.0
            else:
                theScale = defaultScale        
            One = 1.0/theScale
        elif key == "Object":
            parseObject(val, sub)
        elif key == "Mesh":
            data = parseMesh(val, sub)
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
        elif key == "Curve":
            data = parseCurve(val, sub)
        elif key == "TextCurve":
            data = parseTextCurve(val, sub)
        elif key == "Lattice":
            data = parseLattice(val, sub)
        elif key == "Group":
            data = parseGroup(val, sub)
        elif key == "Lamp":
            data = parseLamp(val, sub)
        elif key == "World":
            data = parseWorld(val, sub)
        elif key == "Scene":
            data = parseScene(val, sub)
        elif key == "DefineProperty":
            parseDefineProperty(val, sub)
        elif key == "Process":
            parseProcess(val, sub)
        elif key == "PostProcess":
            postProcess(val)
            hideLayers(val)
        elif key == "CorrectRig":
            correctRig(val)
        elif key == "Rigify":
            if toggle & T_Rigify:
                rigifyMhx(bpy.context, val[0])
        elif key == 'AnimationData':
            try:
                ob = loadedData['Object'][val[0]]
            except:
                ob = None
            if ob:
                bpy.context.scene.objects.active = ob
                parseAnimationData(ob, val, sub)
        elif key == 'MaterialAnimationData':
            try:
                ob = loadedData['Object'][val[0]]
            except:
                ob = None
            if ob:
                bpy.context.scene.objects.active = ob
                mat = ob.data.materials[int(val[2])]
                print("matanim", ob, mat)
                parseAnimationData(mat, val, sub)
        elif key == 'ShapeKeys':
            try:
                ob = loadedData['Object'][val[0]]
            except:
                MyError("ShapeKeys object %s does not exist" % val[0])
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
    # print(expr)
    data = eval(expr)
    # print("  ok", data)

    bpyType = typ.capitalize()
    print(bpyType, name, data)
    loadedData[bpyType][name] = data
    if data is None:
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
    if act is None:
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
                pt.interpolation = 'LINEAR'
                pt = parseKeyFramePoint(pt, val, sub)
                n += 1
            except:
                pass
                #print(tokens)
                #MyError("kp", fcu, n, len(fcu.keyframe_points), val)
        else:
            defaultKey(key, val, sub, 'fcu', [], globals(), locals())
    return fcu

def parseKeyFramePoint(pt, args, tokens):
    pt.co = (float(args[0]), float(args[1]))
    if len(args) > 2:
        pt.handle1 = (float(args[2]), float(args[3]))
        pt.handle2 = (float(args[3]), float(args[5]))
    return pt

#
#    parseAnimationData(rna, args, tokens):
#    parseDriver(drv, args, tokens):
#    parseDriverVariable(var, args, tokens):
#

def parseAnimationData(rna, args, tokens):
    if not eval(args[1]):
        return
    print("Parse Animation data")
    if rna.animation_data is None:    
        rna.animation_data_create()
    adata = rna.animation_data
    for (key, val, sub) in tokens:
        if key == 'FCurve':
            fcu = parseAnimDataFCurve(adata, rna, val, sub)            
        else:
            defaultKey(key, val, sub, 'adata', [], globals(), locals())
    print(adata)
    return adata

def parseAnimDataFCurve(adata, rna, args, tokens):
    if invalid(args[2]):
        return
    dataPath = args[0]
    index = int(args[1])
    n = 1
    for (key, val, sub) in tokens:
        if key == 'Driver':
            fcu = parseDriver(adata, dataPath, index, rna, val, sub)
            fmod = fcu.modifiers[0]
            fcu.modifiers.remove(fmod)
        elif key == 'FModifier':
            parseFModifier(fcu, val, sub)
        elif key == 'kp':
            pt = fcu.keyframe_points.insert(n, 0)
            pt.interpolation = 'LINEAR'
            pt = parseKeyFramePoint(pt, val, sub)
            n += 1
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
        #print("prop", expr, prop)
        bone = eval(expr)
        return None
    else:
        words = dataPath.split('.')
        channel = words[-1]
        expr = "rna"
        for n in range(len(words)-1):
            expr += "." + words[n]
        expr += ".driver_add('%s', index)" % channel
    
    #print("expr", rna, expr)
    fcu = eval(expr)
    drv = fcu.driver
    #print("   Driver type", drv, args[0])
    drv.type = args[0]
    #print("   ->", drv.type)
    for (key, val, sub) in tokens:
        if key == 'DriverVariable':
            var = parseDriverVariable(drv, rna, val, sub)
        else:
            defaultKey(key, val, sub, 'drv', [], globals(), locals())
    return fcu

def parseDriverVariable(drv, rna, args, tokens):
    var = drv.variables.new()
    var.name = args[0]
    #print("   Var type", var, args[1])
    var.type = args[1]
    #print("   ->", var.type)
    nTarget = 0
    for (key, val, sub) in tokens:
        if key == 'Target':
            parseDriverTarget(var, nTarget, rna, val, sub)
            nTarget += 1
        else:
            defaultKey(key, val, sub, 'var', [], globals(), locals())
    return var

def parseFModifier(fcu, args, tokens):
    fmod = fcu.modifiers.new(args[0])
    #fmod = fcu.modifiers[0]
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
    name = args[0]
    #targ.id_type = args[1]
    dtype = args[1].capitalize()
    dtype = 'Object'
    targ.id = loadedData[dtype][name]
    #print("    ->", targ.id)
    for (key, val, sub) in tokens:
        defaultKey(key, val, sub, 'targ', [], globals(), locals())
    return targ

    
#
#    parseMaterial(args, ext, tokens):
#    parseMTex(mat, args, tokens):
#    parseTexture(args, tokens):
#

def parseMaterial(args, tokens):
    global todo
    name = args[0]
    mat = bpy.data.materials.new(name)
    if mat is None:
        return None
    loadedData['Material'][name] = mat
    for (key, val, sub) in tokens:
        if key == 'MTex':
            parseMTex(mat, val, sub)
        elif key == 'Ramp':
            parseRamp(mat, val, sub)
        elif key == 'RaytraceTransparency':
            parseDefault(mat.raytrace_transparency, sub, {}, [])
        elif key == 'Halo':
            parseDefault(mat.halo, sub, {}, [])
        elif key == 'SSS':
            parseDefault(mat.subsurface_scattering, sub, {}, [])
        elif key == 'Strand':
            parseDefault(mat.strand, sub, {}, [])
        elif key == 'NodeTree':
            mat.use_nodes = True
            parseNodeTree(mat.node_tree, val, sub)
        elif key == 'AnimationData':
            parseAnimationData(mat, val, sub)
        else:
            exclude = ['specular_intensity', 'tangent_shading']
            defaultKey(key, val, sub, 'mat', [], globals(), locals())
    
    return mat

def parseMTex(mat, args, tokens):
    global todo
    index = int(args[0])
    texname = args[1]
    texco = args[2]
    mapto = args[3]
    tex = loadedData['Texture'][texname]
    mtex = mat.texture_slots.add()
    mtex.texture_coords = texco
    mtex.texture = tex

    for (key, val, sub) in tokens:
        defaultKey(key, val, sub, "mtex", [], globals(), locals())

    return mtex

def parseTexture(args, tokens):
    global todo
    if verbosity > 2:
        print( "Parsing texture %s" % args )
    name = args[0]
    tex = bpy.data.textures.new(name=name, type=args[1])
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
        elif key == 'NodeTree':
            tex.use_nodes = True
            parseNodeTree(tex.node_tree, val, sub)
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
#    parseNodeTree(tree, args, tokens):
#    parseNode(node, args, tokens):
#    parseSocket(socket, args, tokens):
#

def parseNodeTree(tree, args, tokens):
    return
    print("Tree", tree, args)
    print(list(tree.nodes))
    tree.name = args[0]
    for (key, val, sub) in tokens:
        if key == 'Node':
            parseNodes(tree.nodes, val, sub)
        else:
            defaultKey(key, val, sub, "tree", [], globals(), locals())

def parseNodes(nodes, args, tokens):
    print("Nodes", nodes, args)
    print(list(nodes))
    node.name = args[0]
    for (key, val, sub) in tokens:
        if key == 'Inputs':
            parseSocket(node.inputs, val, sub)
        elif key == 'Outputs':
            parseSocket(node.outputs, val, sub)
        else:
            defaultKey(key, val, sub, "node", [], globals(), locals())

def parseNode(node, args, tokens):
    print("Node", node, args)
    print(list(node.inputs), list(node.outputs))
    node.name = args[0]
    for (key, val, sub) in tokens:
        if key == 'Inputs':
            parseSocket(node.inputs, val, sub)
        elif key == 'Outputs':
            parseSocket(node.outputs, val, sub)
        else:
            defaultKey(key, val, sub, "node", [], globals(), locals())

def parseSocket(socket, args, tokens):
    print("Socket", socket, args)
    socket.name = args[0]
    for (key, val, sub) in tokens:
        if key == 'Node':
            parseNode(tree.nodes, val, sub)
        else:
            defaultKey(key, val, sub, "tree", [], globals(), locals())



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
            if img is None:
                return None
            img.name = imgName
        else:
            defaultKey(key, val,  sub, "img", ['depth', 'dirty', 'has_data', 'size', 'type'], globals(), locals())
    print ("Image %s" % img )
    loadedData['Image'][imgName] = img
    return img

#
#    parseObject(args, tokens):
#    createObject(type, name, data, datName):
#    setObjectAndData(args, typ):
#
    
def parseObject(args, tokens):
    if verbosity > 2:
        print( "Parsing object %s" % args )
    name = args[0]
    typ = args[1]
    datName = args[2]

    if typ == 'EMPTY':
        ob = bpy.data.objects.new(name, None)
        loadedData['Object'][name] = ob
        linkObject(ob, None)
    else:
        try:
            data = loadedData[typ.capitalize()][datName]    
        except:
            MyError("Failed to find data: %s %s %s" % (name, typ, datName))
            return

    try:
        ob = loadedData['Object'][name]
        bpy.context.scene.objects.active = ob
        #print("Found data", ob)
    except:
        ob = None

    if ob is None:
        print("Create", name, data, datName)
        ob = createObject(typ, name, data, datName)
        print("created", ob)
        linkObject(ob, data)

    for (key, val, sub) in tokens:
        if key == 'Modifier':
            parseModifier(ob, val, sub)
        elif key == 'Constraint':
            parseConstraint(ob.constraints, None, val, sub)
        elif key == 'AnimationData':
            parseAnimationData(ob, val, sub)
        elif key == 'ParticleSystem':
            parseParticleSystem(ob, val, sub)
        elif key == 'FieldSettings':
            parseDefault(ob.field, sub, {}, [])
        else:
            defaultKey(key, val, sub, "ob", ['type', 'data'], globals(), locals())

    # Needed for updating layers
    if bpy.context.object == ob:
        pass
        '''
        if ob.data in ['MESH', 'ARMATURE']:
            print(ob, ob.data)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.mode_set(mode='OBJECT')
        '''
    else:
        print("Context", ob, bpy.context.object, bpy.context.scene.objects.active)
    return

def createObject(typ, name, data, datName):
    # print( "Creating object %s %s %s" % (typ, name, data) )    
    ob = bpy.data.objects.new(name, data)
    if data:
        loadedData[typ.capitalize()][datName] = data
    loadedData['Object'][name] = ob
    return ob
    
def linkObject(ob, data):
    #print("Data", data, ob.data)
    if data and ob.data is None:
        ob.data = data
        print("Data linked", ob, ob.data)
    scn = bpy.context.scene
    scn.objects.link(ob)
    scn.objects.active = ob
    #print("Linked object", ob)
    #print("Scene", scn)
    #print("Active", scn.objects.active)
    #print("Context", bpy.context.object)
    return ob

def setObjectAndData(args, typ):
    datName = args[0]
    obName = args[1]
    #bpy.ops.object.add(type=typ)
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
        if key == 'HookAssignNth':
            if val[0] == 'CURVE':
                hookAssignNth(mod, int(val[1]), True, ob.data.splines[0].points)
            elif val[0] == 'LATTICE':
                hookAssignNth(mod, int(val[1]), False, ob.data.points)
            elif val[0] == 'MESH':
                hookAssignNth(mod, int(val[1]), True, ob.data.vertices)
            else:
                MyError("Unknown hook %s" % val)
        else:            
            defaultKey(key, val, sub, 'mod', [], globals(), locals())
    return mod

def hookAssignNth(mod, n, select, points):
    if select:
        for pt in points:
            pt.select = False
        points[n].select = True
        sel = []
        for pt in points:
            sel.append(pt.select)
        #print(mod, sel, n, points)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.object.hook_reset(modifier=mod.name)
    bpy.ops.object.hook_select(modifier=mod.name)
    bpy.ops.object.hook_assign(modifier=mod.name)
    bpy.ops.object.mode_set(mode='OBJECT')
    return

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
            h = par.hair[n]
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
    ob = createObject('MESH', obname, me, mename)

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
        me.from_pydata(verts, [], faces)
    else:
        me.from_pydata(verts, edges, [])
    me.update()
    linkObject(ob, me)
        
    mats = []
    for (key, val, sub) in tokens:
        if key == 'Verts' or key == 'Edges' or key == 'Faces':
            pass
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
                mat = loadedData['Material'][val[0]]
            except:
                mat = None
            if mat:
                me.materials.append(mat)
        else:
            defaultKey(key, val,  sub, "me", [], globals(), locals())

    for (key, val, sub) in tokens:
        if key == 'Faces':
            parseFaces2(sub, me)
    print(me)
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
            verts.append( (theScale*float(val[0]), theScale*float(val[1]), theScale*float(val[2])) )
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
                face = [int(val[0]), int(val[1]), int(val[2])]
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
        elif key == 'ftn':
            mn = int(val[1])
            us = int(val[2])
            npts = int(val[0])
            for i in range(npts):
                f = me.faces[n]
                f.material_index = mn
                f.use_smooth = us
                n += 1
        elif key == 'mn':
            fn = int(val[0])
            mn = int(val[1])
            f = me.faces[fn]
            f.material_index = mn
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
    me.uv_textures.new(name = name)
    uvtex = me.uv_textures[-1]
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
        loadedData['VertexGroup'][grpName] = group
        for (key, val, sub) in tokens:
            if key == 'wv':
                group.add( [int(val[0])], float(val[1]), 'REPLACE' )
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
    for (key, val, sub) in tokens:
        if key == 'ShapeKey':
            parseShapeKey(ob, me, val, sub)
        elif key == 'AnimationData':
            if me.shape_keys:
                parseAnimationData(me.shape_keys, val, sub)
    ob.active_shape_key_index = 0
    print("Shapekeys parsed")
    return


def parseShapeKey(ob, me, args, tokens):
    if verbosity > 2:
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
        MyError("ShapeKey L/R %s" % lr)
    return

def addShapeKey(ob, name, vgroup, tokens):
    skey = ob.shape_key_add(name=name, from_mix=False)
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
            pt[0] += theScale*float(val[1])
            pt[1] += theScale*float(val[2])
            pt[2] += theScale*float(val[3])
        else:
            defaultKey(key, val,  sub, "skey", [], globals(), locals())

    return    

    
#
#    parseArmature (obName, args, tokens)
#

def parseArmature (args, tokens):
    global toggle
    if verbosity > 2:
        print( "Parsing armature %s" % args )
    
    amtname = args[0]
    obname = args[1]
    mode = args[2]
    
    amt = bpy.data.armatures.new(amtname)
    ob = createObject('ARMATURE', obname, amt, amtname)    

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
                parseBone(bone, amt, sub, heads, tails)
                loadedData['Bone'][bname] = bone
        elif key == 'RecalcRoll':
            rolls = {}
            for bone in amt.edit_bones:
                bone.select = False
            blist = eval(val[0])
            for name in blist:
                bone = amt.edit_bones[name]
                bone.select = True
            bpy.ops.armature.calculate_roll(type='Z')
            for bone in amt.edit_bones:
                rolls[bone.name] = bone.roll
            bpy.ops.object.mode_set(mode='OBJECT')
            for bone in amt.bones:
                bone['Roll'] = rolls[bone.name]
            bpy.ops.object.mode_set(mode='EDIT')
        else:
            defaultKey(key, val,  sub, "amt", ['MetaRig'], globals(), locals())
    bpy.ops.object.mode_set(mode='OBJECT')
    return amt
        
#
#    parseBone(bone, amt, tokens, heads, tails):
#

def parseBone(bone, amt, tokens, heads, tails):
    global todo

    for (key, val, sub) in tokens:
        if key == "head":
            bone.head = (theScale*float(val[0]), theScale*float(val[1]), theScale*float(val[2]))
        elif key == "tail":
            bone.tail = (theScale*float(val[0]), theScale*float(val[1]), theScale*float(val[2]))
        #elif key == 'restrict_select':
        #    pass
        elif key == 'hide' and val[0] == 'True':
            name = bone.name
            '''
            #bpy.ops.object.mode_set(mode='OBJECT')
            pbone = amt.bones[name]
            pbone.hide = True
            print("Hide", pbone, pbone.hide)
            #bpy.ops.object.mode_set(mode='EDIT')            
            '''
        else:
            defaultKey(key, val,  sub, "bone", [], globals(), locals())
    return bone

#
#    parsePose (args, tokens):
#

def parsePose (args, tokens):
    global todo
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
    if verbosity > 2:
        print( "Parsing bonegroup %s" % args )
    name = args[0]
    bpy.ops.pose.group_add()
    bg = pose.bone_groups.active
    loadedData['BoneGroup'][name] = bg
    for (key, val, sub) in tokens:
        defaultKey(key, val,  sub, "bg", [], globals(), locals())
    return

def parsePoseBone(pbones, ob, args, tokens):
    global todo
    if invalid(args[1]):
        return
    name = args[0]
    pb = pbones[name]
    amt = ob.data
    amt.bones.active = pb.bone 

    for (key, val, sub) in tokens:
        if key == 'Constraint':
            amt.bones.active = pb.bone 
            cns = parseConstraint(pb.constraints, pb, val, sub)
        elif key == 'bpyops':
            amt.bones.active = pb.bone 
            expr = "bpy.ops.%s" % val[0]
            print(expr)
            exec(expr)
        elif key == 'ik_dof':
            parseArray(pb, ["ik_dof_x", "ik_dof_y", "ik_dof_z"], val)
        elif key == 'ik_limit':
            parseArray(pb, ["ik_limit_x", "ik_limit_y", "ik_limit_z"], val)
        elif key == 'ik_max':
            parseArray(pb, ["ik_max_x", "ik_max_y", "ik_max_z"], val)
        elif key == 'ik_min':
            parseArray(pb, ["ik_min_x", "ik_min_y", "ik_min_z"], val)
        elif key == 'ik_stiffness':
            parseArray(pb, ["ik_stiffness_x", "ik_stiffness_y", "ik_stiffness_z"], val)
        elif key == 'hide':
            #bpy.ops.object.mode_set(mode='OBJECT')
            amt.bones[name].hide = eval(val[0])
            #bpy.ops.object.mode_set(mode='POSE')
            
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
#    parseConstraint(constraints, pb, args, tokens)
#

def parseConstraint(constraints, pb, args, tokens):
    if invalid(args[2]):
        return None
    if (toggle&T_Opcns and pb):
        print("Active")
        aob = bpy.context.object
        print("ob", aob)
        aamt = aob.data
        print("amt", aamt)
        apose = aob.pose
        print("pose", apose)
        abone = aamt.bones.active
        print("bone", abone)
        print('Num cns before', len(list(constraints)))
        bpy.ops.pose.constraint_add(type=args[1])
        cns = constraints.active
        print('and after', pb, cns, len(list(constraints)))
    else:
        cns = constraints.new(args[1])

    cns.name = args[0]
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

#


#    parseCurve (args, tokens):
#    parseSpline(cu, args, tokens):
#    parseBezier(spline, n, args, tokens):
#

def parseCurve (args, tokens):
    global todo
    if verbosity > 2:
        print( "Parsing curve %s" % args )
    bpy.ops.object.add(type='CURVE')
    cu = setObjectAndData(args, 'Curve')

    for (key, val, sub) in tokens:
        if key == 'Spline':
            parseSpline(cu, val, sub)
        else:
            defaultKey(key, val, sub, "cu", [], globals(), locals())
    return

def parseTextCurve (args, tokens):
    global todo
    if verbosity > 2:
        print( "Parsing text curve %s" % args )
    bpy.ops.object.text_add()
    txt = setObjectAndData(args, 'Text')

    for (key, val, sub) in tokens:
        if key == 'Spline':
            parseSpline(txt, val, sub)
        elif key == 'BodyFormat':
            parseCollection(txt.body_format, sub, [])
        elif key == 'EditFormat':
            parseDefault(txt.edit_format, sub, {}, [])
        elif key == 'Font':
            parseDefault(txt.font, sub, {}, [])
        elif key == 'TextBox':
            parseCollection(txt.body_format, sub, [])
        else:
            defaultKey(key, val, sub, "txt", [], globals(), locals())
    return


def parseSpline(cu, args, tokens):
    typ = args[0]
    spline = cu.splines.new(typ)
    nPointsU = int(args[1])
    nPointsV = int(args[2])
    #spline.point_count_u = nPointsU
    #spline.point_count_v = nPointsV
    if typ == 'BEZIER' or typ == 'BSPLINE':
        spline.bezier_points.add(nPointsU)
    else:
        spline.points.add(nPointsU)

    n = 0
    for (key, val, sub) in tokens:
        if key == 'bz':
            parseBezier(spline.bezier_points[n], val, sub)
            n += 1
        elif key == 'pt':
            parsePoint(spline.points[n], val, sub)
            n += 1
        else:
            defaultKey(key, val, sub, "spline", [], globals(), locals())
    return
    
def parseBezier(bez, args, tokens):
    bez.co = eval(args[0])
    bez.co = theScale*bez.co    
    bez.handle1 = eval(args[1])    
    bez.handle1_type = args[2]
    bez.handle2 = eval(args[3])    
    bez.handle2_type = args[4]
    return

def parsePoint(pt, args, tokens):
    pt.co = eval(args[0])
    pt.co = theScale*pt.co
    print(" pt", pt.co)
    return

#
#    parseLattice (args, tokens):
#

def parseLattice (args, tokens):
    global todo
    if verbosity > 2:
        print( "Parsing lattice %s" % args )
    bpy.ops.object.add(type='LATTICE')
    lat = setObjectAndData(args, 'Lattice')    
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
            v = points[n].co_deform
            v.x = theScale*float(val[0])
            v.y = theScale*float(val[1])
            v.z = theScale*float(val[2])
            n += 1
    return

#
#    parseLamp (args, tokens):
#    parseFalloffCurve(focu, args, tokens):
#

def parseLamp (args, tokens):
    global todo
    if verbosity > 2:
        print( "Parsing lamp %s" % args )
    bpy.ops.object.add(type='LAMP')
    lamp = setObjectAndData(args, 'Lamp')    
    for (key, val, sub) in tokens:
        if key == 'FalloffCurve':
            parseFalloffCurve(lamp.falloff_curve, val, sub)
        else:
            defaultKey(key, val, sub, "lamp", [], globals(), locals())
    return

def parseFalloffCurve(focu, args, tokens):
    return

#
#    parseGroup (args, tokens):
#    parseGroupObjects(args, tokens, grp):
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
    rig = None
    for (key, val, sub) in tokens:
        if key == 'ob':
            try:
                ob = loadedData['Object'][val[0]]
                grp.objects.link(ob)
            except:
                ob = None
            if ob:
                print(ob, ob.type, rig, ob.parent)
                if ob.type == 'ARMATURE':
                    rig = ob
                elif ob.type == 'EMPTY' and rig and not ob.parent:
                    ob.parent = rig
                    print("SSS")
    return

#
#    parseWorld (args, tokens):
#

def parseWorld (args, tokens):
    global todo
    if verbosity > 2:
        print( "Parsing world %s" % args )
    world = bpy.context.scene.world
    for (key, val, sub) in tokens:
        if key == 'Lighting':
            parseDefault(world.lighting, sub, {}, [])
        elif key == 'Mist':
            parseDefault(world.mist, sub, {}, [])
        elif key == 'Stars':
            parseDefault(world.stars, sub, {}, [])
        else:
            defaultKey(key, val, sub, "world", [], globals(), locals())
    return

#
#    parseScene (args, tokens):
#    parseRenderSettings(render, args, tokens):
#    parseToolSettings(tool, args, tokens):
#

def parseScene (args, tokens):
    global todo
    if verbosity > 2:
        print( "Parsing scene %s" % args )
    scn = bpy.context.scene
    for (key, val, sub) in tokens:
        if key == 'NodeTree':
            scn.use_nodes = True
            parseNodeTree(scn, val, sub)
        elif key == 'GameData':
            parseDefault(scn.game_data, sub, {}, [])
        elif key == 'KeyingSet':
            pass
            #parseDefault(scn.keying_sets, sub, {}, [])
        elif key == 'ObjectBase':
            pass
            #parseDefault(scn.bases, sub, {}, [])
        elif key == 'RenderSettings':
            parseRenderSettings(scn.render, sub, [])
        elif key == 'ToolSettings':
            subkeys = {'ImagePaint' : "image_paint",  
                'Sculpt' : "sculpt",  
                'VertexPaint' : "vertex_paint",  
                'WeightPaint' : "weight_paint" }
            parseDefault(scn.tool_settings, sub, subkeys, [])
        elif key == 'UnitSettings':
            parseDefault(scn.unit_settings, sub, {}, [])
        else:
            defaultKey(key, val, sub, "scn", [], globals(), locals())
    return

def parseRenderSettings(render, args, tokens):
    global todo
    if verbosity > 2:
        print( "Parsing RenderSettings %s" % args )
    for (key, val, sub) in tokens:
        if key == 'Layer':
            pass
            #parseDefault(scn.layers, sub, [])
        else:
            defaultKey(key, val, sub, "render", [], globals(), locals())
    return

#
#    parseDefineProperty(args, tokens):
#

def parseDefineProperty(args, tokens):
    expr = "bpy.types.Object.%s = %sProperty" % (args[0], args[1])
    c = '('
    for option in args[2:]:
        expr += "%s %s" % (c, option)
        c = ','
    expr += ')'
    #print(expr)
    exec(expr)
    #print("Done")
    return

#
#    correctRig(args):
#

def correctRig(args):
    human = args[0]
    print("CorrectRig %s" % human)    
    try:
        ob = loadedData['Object'][human]
    except:
        return
    bpy.context.scene.objects.active = ob
    bpy.ops.object.mode_set(mode='POSE')
    amt = ob.data
    cnslist = []
    for pb in ob.pose.bones:
        for cns in pb.constraints:
            if cns.type == 'CHILD_OF':
                cnslist.append((pb, cns, cns.influence))
                cns.influence = 0

    for (pb, cns, inf) in cnslist:
        amt.bones.active = pb.bone
        cns.influence = 1
        #print("Childof %s %s %s %.2f" % (amt.name, pb.name, cns.name, inf))
        bpy.ops.constraint.childof_clear_inverse(constraint=cns.name, owner='BONE')
        bpy.ops.constraint.childof_set_inverse(constraint=cns.name, owner='BONE')
        cns.influence = 0

    for (pb, cns, inf) in cnslist:
        cns.influence = inf
    return
        

#
#    postProcess(args)
#

def postProcess(args):
    human = args[0]
    print("Postprocess %s" % human)    
    try:
        ob = loadedData['Object'][human]
    except:
        ob = None
    if toggle & T_Diamond == 0 and ob:
        deleteDiamonds(ob)
    return            

#
#    deleteDiamonds(ob)
#    Delete joint diamonds in main mesh
#    Invisio = material # 1
#

def deleteDiamonds(ob):
    bpy.context.scene.objects.active = ob
    if not bpy.context.object:
        return
    print("Delete helper geometry in %s" % bpy.context.object)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    me = ob.data
    for f in me.faces:    
        if f.material_index == 1:
            for vn in f.vertices:
                me.vertices[vn].select = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.delete(type='VERT')
    bpy.ops.object.mode_set(mode='OBJECT')
    return
  
#
#    defaultKey(ext, args, tokens, var, exclude, glbals, lcals):
#

thePropTip = ""

def defaultKey(ext, args, tokens, var, exclude, glbals, lcals):
    global todo, thePropTip

    if ext == 'Property':
        thePropTip = ""
        try:
            expr = '%s["%s"] = %s' % (var, args[0], args[1])
        except:
            expr = None
        #print("Property", expr)
        if expr:
            exec(expr, glbals, lcals)
            if len(args) > 2:
                thePropTip =  '"description":"%s"' % args[2].replace("_", " ")
        return
    elif ext == 'PropKeys':
        if len(args) < 2:
            values = '{%s}' % thePropTip
        else:
            values = '{%s%s}' % (args[1], thePropTip)        
        try:
            expr = '%s["_RNA_UI"]["%s"] = %s' % (var, args[0], values)
        except:
            expr = None
        #print("PropKeys", expr)
        if expr:
            exec(expr, glbals, lcals)
        return

    if ext == 'bpyops':
        expr = "bpy.ops.%s" % args[0]
        print(expr)
        exec(expr)
        return
        
    nvar = "%s.%s" % (var, ext)
    #print(ext)
    if ext in exclude:
        return
    #print("D", nvar)

    if len(args) == 0:
        MyError("Key length 0: %s" % ext)
        
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

        if data is None:
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
        MyError("PropertyRNA!")
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
        pushOnTodoList(var, expr, glbals, lcals)
    return

#
#
#

def pushOnTodoList(var, expr, glbals, lcals):
    global todo
    print("Tdo", var)
    print(dir(eval(var, glbals, lcals)))
    MyError("Todo %s" % expr)
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
    matrix = mathutils.Matrix()
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
#    parseDefault(data, tokens, subkeys, exclude):
#

def parseDefault(data, tokens, subkeys, exclude):
    for (key, val, sub) in tokens:    
        if key in subkeys.keys():
            for (key2, val2, sub2) in sub:
                defaultKey(key2, val2, sub2, "data.%s" % subkeys[key], [], globals(), locals())
        else:
            defaultKey(key, val, sub, "data", exclude, globals(), locals())

def parseCollection(data, tokens, exclude):
    return


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
        MyError("Bool %s?" % string)
        
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
        if ob.type in ['MESH', 'ARMATURE', 'EMPTY', 'CURVE', 'LATTICE']:
            scn.objects.active = ob
            ob.name = "#" + ob.name
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except:
                pass
            scn.objects.unlink(ob)
            del ob

    for grp in bpy.data.groups:
        grp.name = "#" + grp.name
    #print(scn.objects)
    return scn

#
#    hideLayers(args):
#    args = sceneLayers sceneHideLayers boneLayers boneHideLayers or nothing
#

def hideLayers(args):
    if len(args) > 1:
        sceneLayers = int(args[2], 16)
        sceneHideLayers = int(args[3], 16)
        boneLayers = int(args[4], 16)
        boneHideLayers = int(args[5], 16)
    else:
        sceneLayers = 0x00ff
        sceneHideLayers = 0
        boneLayers = 0
        boneHideLayers = 0

    scn = bpy.context.scene
    mask = 1
    hidelayers = []
    for n in range(20):
        scn.layers[n] = True if sceneLayers & mask else False
        if sceneHideLayers & mask:
            hidelayers.append(n)
        mask = mask << 1

    for ob in scn.objects:
        for n in hidelayers:
            if ob.layers[n]:
                ob.hide = True

    if boneLayers:    
        human = args[1]
        try:
            ob = loadedData['Object'][human]
        except:
            return

        mask = 1
        hidelayers = []
        for n in range(32):
            ob.data.layers[n] = True if boneLayers & mask else False
            if boneHideLayers & mask:
                hidelayers.append(n)
            mask = mask << 1

        for b in ob.data.bones:
            for n in hidelayers:
                if b.layers[n]:
                    b.hide = True

    return
    

#
#    readDefaults():
#    writeDefaults():
#

ConfigFile = '~/mhx_import.cfg'


def readDefaults():
    global toggle, theScale
    path = os.path.realpath(os.path.expanduser(ConfigFile))
    try:
        fp = open(path, 'rU')
        print('Storing defaults')
    except:
        print('Cannot open "%s" for reading' % path)
        return
    bver = ''
    for line in fp: 
        words = line.split()
        if len(words) >= 3:
            try:
                toggle = int(words[0],16)
                theScale = float(words[1])
            except:
                print('Configuration file "%s" is corrupt' % path)                
    fp.close()
    return

def writeDefaults():
    global toggle, theScale
    path = os.path.realpath(os.path.expanduser(ConfigFile))
    try:
        fp = open(path, 'w')
        print('Storing defaults')
    except:
        print('Cannot open "%s" for writing' % path)
        return
    fp.write("%x %f Graphicall" % (toggle, theScale))
    fp.close()
    return

###################################################################################
#
#   Postprocessing of rigify rig
#
#   rigifyMhx(context, name):
#
###################################################################################

def rigifyMhx(context, name):
    print("Modifying MHX rig to Rigify")
    scn = context.scene 
    mhx = loadedData['Object'][name]
    mhx['MhxRigify'] = True
    bpy.context.scene.objects.active = mhx

    # Delete old widgets
    """
    for ob in scn.objects:
        if ob.type == 'MESH' and ob.name[0:3] == "WGT":
            scn.objects.unlink(ob)
    """

    # Save mhx bone locations    
    heads = {}
    tails = {}
    rolls = {}
    parents = {}
    extras = {}
    bpy.ops.object.mode_set(mode='EDIT')

    newParents = {
        'head' : 'DEF-head',
        'ribs' : 'DEF-ribs',
        'upper_arm.L' : 'DEF-upper_arm.L.02',
        'thigh.L' : 'DEF-thigh.L.02',
        'upper_arm.R' : 'DEF-upper_arm.R.02',
        'thigh.R' : 'DEF-thigh.R.02',
    }

    for eb in mhx.data.edit_bones:
        heads[eb.name] = eb.head.copy()
        tails[eb.name] = eb.tail.copy()
        rolls[eb.name] = eb.roll
        if eb.parent:            
            par = eb.parent.name
            # print(eb.name, par)
            try:
                parents[eb.name] = newParents[par]
            except:
                parents[eb.name] = par
        else:
            parents[eb.name] = None
        extras[eb.name] = not eb.layers[16]
    bpy.ops.object.mode_set(mode='OBJECT')
   
    # Find corresponding meshes. Can be several (clothes etc.)   
    meshes = []
    for ob in scn.objects:
        for mod in ob.modifiers:
            if (mod.type == 'ARMATURE' and mod.object == mhx):
                meshes.append((ob, mod))
    if meshes == []:
        MyError("Did not find matching mesh")
        
    # Rename Head vertex group    
    for (mesh, mod) in meshes:
        try:
            vg = mesh.vertex_groups['DfmHead']
            vg.name = 'DEF-head'
        except:
            pass

    # Change meta bone locations    
    scn.objects.active = None 
    try:
        bpy.ops.object.armature_human_advanced_add()
        success = True
    except:
        success = False
    if not success:
        MyError("Unable to create advanced human. \n" \
                "Make sure that the Rigify addon is enabled. \n" \
                "It is found under Rigging.")
        return

    meta = context.object
    bpy.ops.object.mode_set(mode='EDIT')
    for eb in meta.data.edit_bones:
        eb.head = heads[eb.name]
        eb.tail = tails[eb.name]
        eb.roll = rolls[eb.name]
        extras[eb.name] = False

    fingerPlanes = [
        ('UP-thumb.L', 'thumb.01.L', 'thumb.03.L', ['thumb.02.L']),
        ('UP-index.L', 'finger_index.01.L', 'finger_index.03.L', ['finger_index.02.L']),
        ('UP-middle.L', 'finger_middle.01.L', 'finger_middle.03.L', ['finger_middle.02.L']),
        ('UP-ring.L', 'finger_ring.01.L', 'finger_ring.03.L', ['finger_ring.02.L']),
        ('UP-pinky.L', 'finger_pinky.01.L', 'finger_pinky.03.L', ['finger_pinky.02.L']),
        ('UP-thumb.R', 'thumb.01.R', 'thumb.03.R', ['thumb.02.R']),
        ('UP-index.R', 'finger_index.01.R', 'finger_index.03.R', ['finger_index.02.R']),
        ('UP-middle.R', 'finger_middle.01.R', 'finger_middle.03.R', ['finger_middle.02.R']),
        ('UP-ring.R', 'finger_ring.01.R', 'finger_ring.03.R', ['finger_ring.02.R']),
        ('UP-pinky.R', 'finger_pinky.01.R', 'finger_pinky.03.R', ['finger_pinky.02.R']),
    ]

    for (upbone, first, last, middles) in fingerPlanes:
        extras[upbone] = False
        #lineateChain(upbone, first, last, middles, 0.01, meta, heads, tails)

    ikPlanes = [
        ('UP-leg.L', 'thigh.L', 'shin.L'),
        ('UP-arm.L', 'upper_arm.L', 'forearm.L'),
        ('UP-leg.R', 'thigh.R', 'shin.R'),
        ('UP-arm.R', 'upper_arm.R', 'forearm.R'),
    ]

    for (upbone, first, last) in ikPlanes:
        extras[upbone] = False
        lineateChain(upbone, first, last, [], 0.1, meta, heads, tails)

    bpy.ops.object.mode_set(mode='OBJECT')

    # Generate rigify rig    
    bpy.ops.pose.rigify_generate()
    scn.objects.unlink(meta)
    rigify = context.object
    rigify.name = name+"Rig"
    layers = 20*[False]
    layers[1] = True        
    rigify.layers = layers
    rigify.show_x_ray = True
    for (mesh, mod) in meshes:
        mod.object = rigify

    grp = loadedData['Group'][name]
    grp.objects.link(rigify)

    # Parent widgets under empty
    empty = bpy.data.objects.new("Widgets", None)
    scn.objects.link(empty)
    empty.layers = 20*[False]
    empty.layers[19] = True
    empty.parent = rigify
    for ob in scn.objects:
        if ob.type == 'MESH' and ob.name[0:4] == "WGT-" and not ob.parent:
            ob.parent = empty
            grp.objects.link(ob)
        elif ob.parent == mhx:
            ob.parent = rigify

    # Copy extra bones to rigify rig
    bpy.ops.object.mode_set(mode='EDIT')
    for name in heads.keys():
        if extras[name]:
            eb = rigify.data.edit_bones.new(name)
            eb.head = heads[name]
            eb.tail = tails[name]
            eb.roll = rolls[name]            
    for name in heads.keys():
        if extras[name] and parents[name]:
            eb = rigify.data.edit_bones[name]
            eb.parent = rigify.data.edit_bones[parents[name]]

    # Copy constraints etc.
    bpy.ops.object.mode_set(mode='POSE')
    for name in heads.keys():
        if extras[name]:
            pb1 = mhx.pose.bones[name]
            pb2 = rigify.pose.bones[name]
            pb2.custom_shape = pb1.custom_shape
            pb2.lock_location = pb1.lock_location
            pb2.lock_rotation = pb1.lock_rotation
            pb2.lock_scale = pb1.lock_scale
            b1 = pb1.bone
            b2 = pb2.bone
            b2.use_deform = b1.use_deform
            b2.hide_select = b1.hide_select
            b2.show_wire = b1.show_wire
            layers = 32*[False]
            if b1.layers[8]:
                layers[28] = True
            else:
                layers[29] = True
            if b1.layers[10]:
                layers[2] = True
            b2.layers = layers
            for cns1 in pb1.constraints:
                cns2 = copyConstraint(cns1, pb1, pb2, mhx, rigify)    
                if cns2.type == 'CHILD_OF':
                    rigify.data.bones.active = pb2.bone
                    bpy.ops.constraint.childof_set_inverse(constraint=cns2.name, owner='BONE')    
    
    # Create animation data
    if mhx.animation_data:
        for fcu in mhx.animation_data.drivers:
            rigify.animation_data.drivers.from_existing(src_driver=fcu)

    fixDrivers(rigify.animation_data, mhx, rigify)
    for (mesh, mod) in meshes:
        mesh.parent = rigify
        skeys = mesh.data.shape_keys
        if skeys:
            fixDrivers(skeys.animation_data, mhx, rigify)

    scn.objects.unlink(mhx)
    print("Rigify rig complete")    
    return

#
#   lineateChain(upbone, first, last, middles, minDist, rig, heads, tails):
#   lineate(pt, start, minDist, normal, offVector):
#

def lineateChain(upbone, first, last, middles, minDist, rig, heads, tails):
    fb = rig.data.edit_bones[first]
    lb = rig.data.edit_bones[last]
    uhead = heads[upbone]
    utail = tails[upbone]
    tang = lb.tail - fb.head
    tangent = tang/tang.length
    up = (uhead+utail)/2 - fb.head
    norm = up - tangent*tangent.dot(up)
    normal = norm/norm.length
    offVector = tangent.cross(normal)
    vec = utail - uhead
    fb.tail = lineate(fb.tail, fb.head, minDist, normal, offVector)
    lb.head = lineate(lb.head, fb.head, minDist, normal, offVector)
    for bone in middles:
        mb = rig.data.edit_bones[bone]
        mb.head = lineate(mb.head, fb.head, minDist, normal, offVector)
        mb.tail = lineate(mb.tail, fb.head, minDist, normal, offVector)
    return

def lineate(pt, start, minDist, normal, offVector):
    diff = pt - start
    diff = diff - offVector*offVector.dot(diff) 
    dist = diff.dot(normal)
    if dist < minDist:
        diff += (minDist - dist)*normal
    return start + diff

#
#   fixDrivers(adata, mhx, rigify):
#

def fixDrivers(adata, mhx, rigify):
    if not adata:
        return
    for fcu in adata.drivers:
        for var in fcu.driver.variables:
            for targ in var.targets:
                if targ.id == mhx:
                    targ.id = rigify
    return

#
#   copyConstraint(cns1, pb1, pb2, mhx, rigify):
#

def copyConstraint(cns1, pb1, pb2, mhx, rigify):
    substitute = {
        'Head' : 'DEF-head',
        'MasterFloor' : 'root',
        'upper_arm.L' : 'DEF-upper_arm.L.01',
        'upper_arm.R' : 'DEF-upper_arm.R.01',
        'thigh.L' : 'DEF-thigh.L.01',
        'thigh.R' : 'DEF-thigh.R.01',
        'shin.L' : 'DEF-shin.L.01',
        'shin.R' : 'DEF-shin.R.01'
    }

    cns2 = pb2.constraints.new(cns1.type)
    for prop in dir(cns1):
        if prop == 'target':
            if cns1.target == mhx:
                cns2.target = rigify
            else:
                cns2.target = cns1.target
        elif prop == 'subtarget':
            try:
                cns2.subtarget = substitute[cns1.subtarget]
            except:
                cns2.subtarget = cns1.subtarget
        elif prop[0] != '_':
            try:
                expr = "cns2.%s = cns1.%s" % (prop, prop)
                #print(pb1.name, expr)
                exec(expr)
            except:
                pass
    return cns2

#
#   class OBJECT_OT_RigifyMhxButton(bpy.types.Operator):
#

class OBJECT_OT_RigifyMhxButton(bpy.types.Operator):
    bl_idname = "mhxrig.rigify_mhx"
    bl_label = "Rigify MHX rig"
    bl_options = {'UNDO'}

    def execute(self, context):
        rigifyMhx(context, context.object.name)
        return{'FINISHED'}    
    
#
#   class RigifyMhxPanel(bpy.types.Panel):
#

class RigifyMhxPanel(bpy.types.Panel):
    bl_label = "Rigify MHX"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    
    @classmethod
    def poll(cls, context):
        if context.object:
            try:
                return context.object['MhxRigify']
            except:
                return False
        return False

    def draw(self, context):
        self.layout.operator("mhxrig.rigify_mhx")
        return

###################################################################################
#
#    Error popup
#
###################################################################################

DEBUG = False
from bpy.props import StringProperty, FloatProperty, EnumProperty, BoolProperty

class ErrorOperator(bpy.types.Operator):
    bl_idname = "mhx.error"
    bl_label = "Error when loading MHX file"

    def execute(self, context):
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        global theErrorLines
        maxlen = 0
        for line in theErrorLines:
            if len(line) > maxlen:
                maxlen = len(line)
        width = 20+5*maxlen
        height = 20+5*len(theErrorLines)
        #self.report({'INFO'}, theMessage)
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=width, height=height)

    def draw(self, context):
        global theErrorLines
        for line in theErrorLines:        
            self.layout.label(line)

def MyError(message):
    global theMessage, theErrorLines, theErrorStatus
    theMessage = message
    theErrorLines = message.split('\n')
    theErrorStatus = True
    bpy.ops.mhx.error('INVOKE_DEFAULT')
    raise NameError(theMessage)

class SuccessOperator(bpy.types.Operator):
    bl_idname = "mhx.success"
    bl_label = "MHX file successfully loaded:"
    message = StringProperty()

    def execute(self, context):
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.label(self.message)

###################################################################################
#
#    User interface
#
###################################################################################

from bpy_extras.io_utils import ImportHelper


MhxBoolProps = [
    ("enforce", "Enforce version", "Only accept MHX files of correct version", T_EnforceVersion),
    ("mesh", "Mesh", "Use main mesh", T_Mesh),
    ("proxy", "Proxies", "Use proxies", T_Proxy),
    ("armature", "Armature", "Use armature", T_Armature),
    ("replace", "Replace scene", "Replace scene", T_Replace),
    ("cage", "Cage", "Load mesh deform cage", T_Cage),
    ("clothes", "Clothes", "Include clothes", T_Clothes),
    ("stretch", "Stretchy limbs", "Stretchy limbs", T_Stretch),
    ("face", "Face shapes", "Include facial shapekeys", T_Face),
    ("shape", "Body shapes", "Include body shapekeys", T_Shape),
    ("symm", "Symmetric shapes", "Keep shapekeys symmetric", T_Symm),
    ("diamond", "Helper geometry", "Keep helper geometry", T_Diamond),
    ("rigify", "Rigify", "Create rigify control rig", T_Rigify),
]

class ImportMhx(bpy.types.Operator, ImportHelper):
    '''Import from MHX file format (.mhx)'''
    bl_idname = "import_scene.makehuman_mhx"
    bl_description = 'Import from MHX file format (.mhx)'
    bl_label = "Import MHX"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {'UNDO'}

    scale = FloatProperty(name="Scale", description="Default meter, decimeter = 1.0", default = theScale)
    filename_ext = ".mhx"
    filter_glob = StringProperty(default="*.mhx", options={'HIDDEN'})
    filepath = StringProperty(subtype='FILE_PATH')

    for (prop, name, desc, flag) in MhxBoolProps:
        expr = '%s = BoolProperty(name="%s", description="%s", default=toggle&%s)' % (prop, name, desc, flag)
        exec(expr)
        
    def execute(self, context):
        global toggle, theScale, MhxBoolProps
        toggle = 0
        for (prop, name, desc, flag) in MhxBoolProps:
            expr = '(%s if self.%s else 0)' % (flag, prop)
            toggle |=  eval(expr)
        print("execute flags %x" % toggle)
        theScale = self.scale

        try:
            readMhxFile(self.filepath)
            bpy.ops.mhx.success('INVOKE_DEFAULT', message = self.filepath)
        except NameError:
            print("Error when loading MHX file:\n" + theMessage)

        writeDefaults()
        return {'FINISHED'}

    def invoke(self, context, event):
        global toggle, theScale, MhxBoolProps
        readDefaults()
        self.scale = theScale
        for (prop, name, desc, flag) in MhxBoolProps:
            expr = 'self.%s = toggle&%s' % (prop, flag)
            exec(expr)
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


###################################################################################    
#
#    Lipsync panel
#
###################################################################################    

#
#    visemes
#

stopStaringVisemes = ({
    'Rest' : [
        ('PMouth', (0,0)), 
        ('PUpLip', (0,-0.1)), 
        ('PLoLip', (0,0.1)), 
        ('PJaw', (0,0.05)), 
        ('PTongue', (0,0.0))], 
    'Etc' : [
        ('PMouth', (0,0)),
        ('PUpLip', (0,-0.1)),
        ('PLoLip', (0,0.1)),
        ('PJaw', (0,0.15)),
        ('PTongue', (0,0.0))], 
    'MBP' : [('PMouth', (-0.3,0)),
        ('PUpLip', (0,1)),
        ('PLoLip', (0,0)),
        ('PJaw', (0,0.1)),
        ('PTongue', (0,0.0))], 
    'OO' : [('PMouth', (-1.5,0)),
        ('PUpLip', (0,0)),
        ('PLoLip', (0,0)),
        ('PJaw', (0,0.2)),
        ('PTongue', (0,0.0))], 
    'O' : [('PMouth', (-1.1,0)),
        ('PUpLip', (0,0)),
        ('PLoLip', (0,0)),
        ('PJaw', (0,0.5)),
        ('PTongue', (0,0.0))], 
    'R' : [('PMouth', (-0.9,0)),
        ('PUpLip', (0,-0.2)),
        ('PLoLip', (0,0.2)),
        ('PJaw', (0,0.2)),
        ('PTongue', (0,0.0))], 
    'FV' : [('PMouth', (0,0)),
        ('PUpLip', (0,0)),
        ('PLoLip', (0,-0.8)),
        ('PJaw', (0,0.1)),
        ('PTongue', (0,0.0))], 
    'S' : [('PMouth', (0,0)),
        ('PUpLip', (0,-0.2)),
        ('PLoLip', (0,0.2)),
        ('PJaw', (0,0.05)),
        ('PTongue', (0,0.0))], 
    'SH' : [('PMouth', (-0.6,0)),
        ('PUpLip', (0,-0.5)),
        ('PLoLip', (0,0.5)),
        ('PJaw', (0,0)),
        ('PTongue', (0,0.0))], 
    'EE' : [('PMouth', (0.3,0)),
        ('PUpLip', (0,-0.3)),
        ('PLoLip', (0,0.3)),
        ('PJaw', (0,0.025)),
        ('PTongue', (0,0.0))], 
    'AH' : [('PMouth', (-0.1,0)),
        ('PUpLip', (0,-0.4)),
        ('PLoLip', (0,0)),
        ('PJaw', (0,0.35)),
        ('PTongue', (0,0.0))], 
    'EH' : [('PMouth', (0.1,0)),
        ('PUpLip', (0,-0.2)),
        ('PLoLip', (0,0.2)),
        ('PJaw', (0,0.2)),
        ('PTongue', (0,0.0))], 
    'TH' : [('PMouth', (0,0)),
        ('PUpLip', (0,-0.5)),
        ('PLoLip', (0,0.5)),
        ('PJaw', (-0.2,0.1)),
        ('PTongue', (0,-0.6))], 
    'L' : [('PMouth', (0,0)),
        ('PUpLip', (0,-0.2)),
        ('PLoLip', (0,0.2)),
        ('PJaw', (0.2,0.2)),
        ('PTongue', (0,-0.8))], 
    'G' : [('PMouth', (0,0)),
        ('PUpLip', (0,-0.1)),
        ('PLoLip', (0,0.1)),
        ('PJaw', (-0.3,0.1)),
        ('PTongue', (0,-0.6))], 

    'Blink' : [('PUpLid', (0,1.0)), ('PLoLid', (0,-1.0))], 
    'Unblink' : [('PUpLid', (0,0)), ('PLoLid', (0,0))], 
})

bodyLanguageVisemes = ({
    'Rest' : [
        ('PMouth', (0,0)), 
        ('PMouthMid', (0,-0.6)), 
        ('PUpLipMid', (0,0)), 
        ('PLoLipMid', (0,0)), 
        ('PJaw', (0,0)), 
        ('PTongue', (0,0))], 
    'Etc' : [
        ('PMouth', (0,0)), 
        ('PMouthMid', (0,-0.4)), 
        ('PUpLipMid', (0,0)), 
        ('PLoLipMid', (0,0)), 
        ('PJaw', (0,0)), 
        ('PTongue', (0,0))], 
    'MBP' : [
        ('PMouth', (0,0)), 
        ('PMouthMid', (0,0)), 
        ('PUpLipMid', (0,0)), 
        ('PLoLipMid', (0,0)), 
        ('PJaw', (0,0)), 
        ('PTongue', (0,0))], 
    'OO' : [
        ('PMouth', (-1.0,0)), 
        ('PMouthMid', (0,0)), 
        ('PUpLipMid', (0,0)), 
        ('PLoLipMid', (0,0)), 
        ('PJaw', (0,0.4)), 
        ('PTongue', (0,0))], 
    'O' : [
        ('PMouth', (-0.9,0)), 
        ('PMouthMid', (0,0)), 
        ('PUpLipMid', (0,0)), 
        ('PLoLipMid', (0,0)), 
        ('PJaw', (0,0.8)), 
        ('PTongue', (0,0))], 
    'R' : [
        ('PMouth', (-0.5,0)), 
        ('PMouthMid', (0,0)), 
        ('PUpLipMid', (0,-0.2)), 
        ('PLoLipMid', (0,0.2)), 
        ('PJaw', (0,0)), 
        ('PTongue', (0,0))], 
    'FV' : [
        ('PMouth', (-0.2,0)), 
        ('PMouthMid', (0,1.0)), 
        ('PUpLipMid', (0,0)), 
        ('PLoLipMid', (-0.6,-0.3)), 
        ('PJaw', (0,0)), 
        ('PTongue', (0,0))], 
    'S' : [
        ('PMouth', (0,0)), 
        ('PMouthMid', (0,0)), 
        ('PUpLipMid', (0,-0.5)), 
        ('PLoLipMid', (0,0.7)), 
        ('PJaw', (0,0)), 
        ('PTongue', (0,0))], 
    'SH' : [
        ('PMouth', (-0.8,0)), 
        ('PMouthMid', (0,0)), 
        ('PUpLipMid', (0,-1.0)), 
        ('PLoLipMid', (0,1.0)), 
        ('PJaw', (0,0)), 
        ('PTongue', (0,0))], 
    'EE' : [
        ('PMouth', (0.2,0)), 
        ('PMouthMid', (0,0)), 
        ('PUpLipMid', (0,-0.6)), 
        ('PLoLipMid', (0,0.6)), 
        ('PJaw', (0,0.05)), 
        ('PTongue', (0,0))], 
    'AH' : [
        ('PMouth', (0,0)), 
        ('PMouthMid', (0,0)), 
        ('PUpLipMid', (0,-0.4)), 
        ('PLoLipMid', (0,0)), 
        ('PJaw', (0,0.7)), 
        ('PTongue', (0,0))], 
    'EH' : [
        ('PMouth', (0,0)), 
        ('PMouthMid', (0,0)), 
        ('PUpLipMid', (0,-0.5)), 
        ('PLoLipMid', (0,0.6)), 
        ('PJaw', (0,0.25)), 
        ('PTongue', (0,0))], 
    'TH' : [
        ('PMouth', (0,0)), 
        ('PMouthMid', (0,0)), 
        ('PUpLipMid', (0,0)), 
        ('PLoLipMid', (0,0)), 
        ('PJaw', (0,0.2)), 
        ('PTongue', (1.0,1.0))], 
    'L' : [
        ('PMouth', (0,0)), 
        ('PMouthMid', (0,0)), 
        ('PUpLipMid', (0,-0.5)), 
        ('PLoLipMid', (0,0.5)), 
        ('PJaw', (0,-0.2)), 
        ('PTongue', (1.0,1.0))], 
    'G' : [
        ('PMouth', (0,0)), 
        ('PMouthMid', (0,0)), 
        ('PUpLipMid', (0,-0.5)), 
        ('PLoLipMid', (0,0.5)), 
        ('PJaw', (0,-0.2)), 
        ('PTongue', (-1.0,0))], 

    'Blink' : [('PUpLid', (0,1.0)), ('PLoLid', (0,-1.0))], 
    'Unblink' : [('PUpLid', (0,0)), ('PLoLid', (0,0))], 
})

VisemeList = [
    ('Rest', 'Etc', 'AH'),
    ('MBP', 'OO', 'O'),
    ('R', 'FV', 'S'),
    ('SH', 'EE', 'EH'),
    ('TH', 'L', 'G')
]

#
#    mohoVisemes
#    magpieVisemes
#

mohoVisemes = dict({
    'rest' : 'Rest', 
    'etc' : 'Etc', 
    'AI' : 'AH', 
    'O' : 'O', 
    'U' : 'OO', 
    'WQ' : 'AH', 
    'L' : 'L', 
    'E' : 'EH', 
    'MBP' : 'MBP', 
    'FV' : 'FV', 
})

magpieVisemes = dict({
    "CONS" : "t,d,k,g,T,D,s,z,S,Z,h,n,N,j,r,tS", 
    "AI" : "i,&,V,aU,I,0,@,aI", 
    "E" : "eI,3,e", 
    "O" : "O,@U,oI", 
    "UW" : "U,u,w", 
    "MBP" : "m,b,p", 
    "L" : "l", 
    "FV" : "f,v", 
    "Sh" : "dZ", 
})

#
#    setViseme(context, vis, setKey, frame):
#    setBoneLocation(context, pbone, loc, mirror, setKey, frame):
#    class VIEW3D_OT_MhxVisemeButton(bpy.types.Operator):
#

def getVisemeSet(context, rig):
    try:
        visset = rig['MhxVisemeSet']
    except:
        return bodyLanguageVisemes
    if visset == 'StopStaring':
        return stopStaringVisemes
    elif visset == 'BodyLanguage':
        return bodyLanguageVisemes
    else:
        raise NameError("Unknown viseme set %s" % visset)

def setViseme(context, vis, setKey, frame):
    rig = getMhxRig(context.object)
    pbones = rig.pose.bones
    try:
        scale = pbones['PFace'].bone.length
    except:
        return
    visemes = getVisemeSet(context, rig)
    for (b, (x, z)) in visemes[vis]:
        loc = mathutils.Vector((float(x),0,float(z)))
        try:
            pb = pbones[b]
        except:

            pb = None
            
        if pb:
            setBoneLocation(context, pb, scale, loc, False, setKey, frame)
        else:
            setBoneLocation(context, pbones[b+'_L'], scale, loc, False, setKey, frame)
            setBoneLocation(context, pbones[b+'_R'], scale, loc, True, setKey, frame)
    updatePose(rig)
    return

def setBoneLocation(context, pb, scale, loc, mirror, setKey, frame):
    if mirror:
        loc[0] = -loc[0]
    pb.location = loc*scale*0.2

    if setKey or context.tool_settings.use_keyframe_insert_auto:
        for n in range(3):
            pb.keyframe_insert('location', index=n, frame=frame, group=pb.name)
    return

class VIEW3D_OT_MhxVisemeButton(bpy.types.Operator):
    bl_idname = 'mhx.pose_viseme'
    bl_label = 'Viseme'
    viseme = StringProperty()

    def invoke(self, context, event):
        setViseme(context, self.viseme, False, context.scene.frame_current)
        return{'FINISHED'}



#
#    openFile(context, filepath):
#    readMoho(context, filepath, offs):
#    readMagpie(context, filepath, offs):
#

def openFile(context, filepath):
    (path, fileName) = os.path.split(filepath)
    (name, ext) = os.path.splitext(fileName)
    return open(filepath, "rU")

def readMoho(context, filepath, offs):
    rig = getMhxRig(context.object)
    context.scene.objects.active = rig
    bpy.ops.object.mode_set(mode='POSE')    
    fp = openFile(context, filepath)        
    for line in fp:
        words= line.split()
        if len(words) < 2:
            pass
        else:
            vis = mohoVisemes[words[1]]
            setViseme(context, vis, True, int(words[0])+offs)
    fp.close()
    setInterpolation(rig)
    updatePose(rig)
    print("Moho file %s loaded" % filepath)
    return

def readMagpie(context, filepath, offs):
    rig = getMhxRig(context.object)
    context.scene.objects.active = rig
    bpy.ops.object.mode_set(mode='POSE')    
    fp = openFile(context, filepath)        
    for line in fp: 
        words= line.split()
        if len(words) < 3:
            pass
        elif words[2] == 'X':
            vis = magpieVisemes[words[3]]
            setViseme(context, vis, True, int(words[0])+offs)
    fp.close()
    setInterpolation(rig)
    updatePose(rig)
    print("Magpie file %s loaded" % filepath)
    return

# 
#    class VIEW3D_OT_MhxLoadMohoButton(bpy.types.Operator):
#

class VIEW3D_OT_MhxLoadMohoButton(bpy.types.Operator):
    bl_idname = "mhx.pose_load_moho"
    bl_label = "Moho (.dat)"
    filepath = StringProperty(subtype='FILE_PATH')
    startFrame = IntProperty(name="Start frame", description="First frame to import", default=1)

    def execute(self, context):
        import bpy, os, mathutils
        readMoho(context, self.properties.filepath, self.properties.startFrame-1)        
        return{'FINISHED'}    

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}    

#
#    class VIEW3D_OT_MhxLoadMagpieButton(bpy.types.Operator):
#

class VIEW3D_OT_MhxLoadMagpieButton(bpy.types.Operator):
    bl_idname = "mhx.pose_load_magpie"
    bl_label = "Magpie (.mag)"
    filepath = StringProperty(subtype='FILE_PATH')
    startFrame = IntProperty(name="Start frame", description="First frame to import", default=1)

    def execute(self, context):
        import bpy, os, mathutils
        readMagpie(context, self.properties.filepath, self.properties.startFrame-1)        
        return{'FINISHED'}    

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}    

#
#    class MhxLipsyncPanel(bpy.types.Panel):
#

class MhxLipsyncPanel(bpy.types.Panel):
    bl_label = "MHX Lipsync"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    
    @classmethod
    def poll(cls, context):
        return context.object

    def draw(self, context):
        rig = getMhxRig(context.object)
        if not rig:
            return

        layout = self.layout        
        layout.label(text="Visemes")
        for (vis1, vis2, vis3) in VisemeList:
            row = layout.row()
            row.operator("mhx.pose_viseme", text=vis1).viseme = vis1
            row.operator("mhx.pose_viseme", text=vis2).viseme = vis2
            row.operator("mhx.pose_viseme", text=vis3).viseme = vis3
        layout.separator()
        row = layout.row()
        row.operator("mhx.pose_viseme", text="Blink").viseme = 'Blink'
        row.operator("mhx.pose_viseme", text="Unblink").viseme = 'Unblink'
        layout.label(text="Load file")
        row = layout.row()
        row.operator("mhx.pose_load_moho")
        row.operator("mhx.pose_load_magpie")
        layout.operator("mhx.update")
        return
        
#
#   updatePose(rig):
#   class VIEW3D_OT_MhxUpdateButton(bpy.types.Operator):
#

def updatePose(rig):
    pb = rig.pose.bones["PFaceDisp"]
    pb.location = pb.location
    return

class VIEW3D_OT_MhxUpdateButton(bpy.types.Operator):
    bl_idname = "mhx.update"
    bl_label = "Update"

    def execute(self, context):
        rig = getMhxRig(context.object)
        updatePose(rig)
        return{'FINISHED'}    
        

###################################################################################    
#
#    Expression panel
#
###################################################################################    
#
#    class VIEW3D_OT_MhxResetExpressionsButton(bpy.types.Operator):
#

class VIEW3D_OT_MhxResetExpressionsButton(bpy.types.Operator):
    bl_idname = "mhx.pose_reset_expressions"
    bl_label = "Reset expressions"

    def execute(self, context):
        rig = getMhxRig(context.object)
        props = getShapeProps(rig)
        for (prop, name) in props:
            rig[prop] = 0.0
        updatePose(rig)
        return{'FINISHED'}    

#
#    class VIEW3D_OT_MhxKeyExpressionButton(bpy.types.Operator):
#

class VIEW3D_OT_MhxKeyExpressionsButton(bpy.types.Operator):
    bl_idname = "mhx.pose_key_expressions"
    bl_label = "Key expressions"

    def execute(self, context):
        rig = getMhxRig(context.object)
        props = getShapeProps(rig)
        frame = context.scene.frame_current
        for (prop, name) in props:
            rig.keyframe_insert('["%s"]' % prop, frame=frame)
        updatePose(rig)
        return{'FINISHED'}    
#
#    class VIEW3D_OT_MhxPinExpressionButton(bpy.types.Operator):
#

class VIEW3D_OT_MhxPinExpressionButton(bpy.types.Operator):
    bl_idname = "mhx.pose_pin_expression"
    bl_label = "Pin"
    expression = StringProperty()

    def execute(self, context):
        rig = getMhxRig(context.object)
        props = getShapeProps(rig)
        if context.tool_settings.use_keyframe_insert_auto:
            frame = context.scene.frame_current
            for (prop, name) in props:
                old = rig[prop]
                if prop == self.expression:
                    rig[prop] = 1.0
                else:
                    rig[prop] = 0.0
                if abs(rig[prop] - old) > 1e-3:
                    rig.keyframe_insert('["%s"]' % prop, frame=frame)
        else:                    
            for (prop, name) in props:
                if prop == self.expression:
                    rig[prop] = 1.0
                else:
                    rig[prop] = 0.0
        updatePose(rig)
        return{'FINISHED'}    

#
#   getShapeProps(ob):        
#

def getShapeProps(rig):
    props = []        
    plist = list(rig.keys())
    plist.sort()
    for prop in plist:
        if prop[0] == '*':
            props.append((prop, prop[1:]))
    return props                

#
#    class MhxExpressionsPanel(bpy.types.Panel):
#

class MhxExpressionsPanel(bpy.types.Panel):
    bl_label = "MHX Expressions"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    
    @classmethod
    def poll(cls, context):
        return context.object

    def draw(self, context):
        rig = getMhxRig(context.object)
        if not rig:
            return
        props = getShapeProps(rig)
        if not props:
            return
        layout = self.layout
        layout.label(text="Expressions")
        layout.operator("mhx.pose_reset_expressions")
        layout.operator("mhx.pose_key_expressions")
        #layout.operator("mhx.update")
        layout.separator()
        for (prop, name) in props:
            row = layout.split(0.85)
            row.prop(rig, '["%s"]' % prop, text=name)
            row.operator("mhx.pose_pin_expression", text="", icon='UNPINNED').expression = prop
        return

###################################################################################    
#
#    Posing panel
#
###################################################################################          
#
#    class MhxDriversPanel(bpy.types.Panel):
#

class MhxDriversPanel(bpy.types.Panel):
    bl_label = "MHX Drivers"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    
    @classmethod
    def poll(cls, context):
        return pollMhxRig(context.object)

    def draw(self, context):
        lProps = []
        rProps = []
        props = []
        plist = list(context.object.keys())
        plist.sort()
        for prop in plist:
            if prop[0] == '&':
                prop1 = prop[1:]
            else:
                continue
            if prop[-2:] == '_L':
                lProps.append((prop, prop1[:-2]))
            elif prop[-2:] == '_R':
                rProps.append((prop, prop1[:-2]))
            else:
                props.append((prop, prop1))
        ob = context.object
        layout = self.layout
        for (prop, pname) in props:
            layout.prop(ob, '["%s"]' % prop, text=pname)
        layout.label("Left")
        for (prop, pname) in lProps:
            layout.prop(ob, '["%s"]' % prop, text=pname)
        layout.label("Right")
        for (prop, pname) in rProps:
            layout.prop(ob, '["%s"]' % prop, text=pname)
        return

###################################################################################    
#
#    Visibility panel
#
###################################################################################          
#
#    class MhxVisibilityPanel(bpy.types.Panel):
#

class MhxVisibilityPanel(bpy.types.Panel):
    bl_label = "MHX Visibility"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    
    @classmethod
    def poll(cls, context):
        return pollMhxRig(context.object)

    def draw(self, context):
        ob = context.object
        props = list(ob.keys())
        props.sort()
        for prop in props:
            if prop[0:4] == "Hide": 
                self.layout.prop(ob, '["%s"]' % prop)
        return

###################################################################################    
#
#    Layers panel
#
###################################################################################    

MhxLayers = [
    (( 0,    'Root', 'MhxRoot'),
     ( 8,    'Face', 'MhxFace')),
    (( 9,    'Tweak', 'MhxTweak'),
     (10,    'Head', 'MhxHead')),
    (( 1,    'FK Spine', 'MhxFKSpine'),
     (17,    'IK Spine', 'MhxIKSpine')),
    ((13,    'Inv FK Spine', 'MhxInvFKSpine'),
     (29,    'Inv IK Spine', 'MhxInvIKSpine')),
    ('Left', 'Right'),
    (( 2,    'IK Arm', 'MhxIKArm'),
     (18,    'IK Arm', 'MhxIKArm')),
    (( 3,    'FK Arm', 'MhxFKArm'),
     (19,    'FK Arm', 'MhxFKArm')),
    (( 4,    'IK Leg', 'MhxIKLeg'),
     (20,    'IK Leg', 'MhxIKLeg')),
    (( 5,    'FK Leg', 'MhxFKLeg'),
     (21,    'FK Leg', 'MhxFKLeg')),
    ((12,    'Extra', 'MhxExtra'),
     (28,    'Extra', 'MhxExtra')),
    (( 6,    'Fingers', 'MhxFingers'),
     (22,    'Fingers', 'MhxFingers')),
    (( 7,    'Links', 'MhxLinks'),
     (23,    'Links', 'MhxLinks')),
    ((11,    'Palm', 'MhxPalm'),
     (27,    'Palm', 'MhxPalm')),
]

#
#    class MhxLayersPanel(bpy.types.Panel):
#

class MhxLayersPanel(bpy.types.Panel):
    bl_label = "MHX Layers"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    
    @classmethod
    def poll(cls, context):
        return pollMhxRig(context.object)

    def draw(self, context):
        layout = self.layout
        layout.operator("mhx.pose_enable_all_layers")
        layout.operator("mhx.pose_disable_all_layers")
        amt = context.object.data
        for (left,right) in MhxLayers:
            row = layout.row()
            if type(left) == str:
                row.label(left)
                row.label(right)
            else:
                for (n, name, prop) in [left,right]:
                    row.prop(amt, "layers", index=n, toggle=True, text=name)
        return

class VIEW3D_OT_MhxEnableAllLayersButton(bpy.types.Operator):
    bl_idname = "mhx.pose_enable_all_layers"
    bl_label = "Enable all layers"

    def execute(self, context):
        rig = getMhxRig(context.object)
        for (left,right) in MhxLayers:
            if type(left) != str:
                for (n, name, prop) in [left,right]:
                    rig.data.layers[n] = True
        return{'FINISHED'}    

class VIEW3D_OT_MhxDisableAllLayersButton(bpy.types.Operator):
    bl_idname = "mhx.pose_disable_all_layers"
    bl_label = "Disable all layers"

    def execute(self, context):
        rig = getMhxRig(context.object)
        layers = 32*[False]
        pb = context.active_pose_bone
        if pb:
            for n in range(32):
                if pb.bone.layers[n]:
                    layers[n] = True
                    break
        else:
            layers[0] = True
        rig.data.layers = layers            
        return{'FINISHED'}    
                
###################################################################################    
#
#    Common functions
#
###################################################################################    
#
#   pollMhxRig(ob):
#   getMhxRig(ob):
#

def pollMhxRig(ob):
    try:
        return (ob["MhxRig"] == "MHX")
    except:
        return False
        
def getMhxRig(ob):
    if ob.type == 'ARMATURE':
        rig = ob
    elif ob.type == 'MESH':
        rig = ob.parent
    else:
        return None
    try:        
        if (rig["MhxRig"] == "MHX"):
            return rig
        else:
            return None
    except:
        return None
    
        
#
#    setInterpolation(rig):
#

def setInterpolation(rig):
    if not rig.animation_data:
        return
    act = rig.animation_data.action
    if not act:
        return
    for fcu in act.fcurves:
        for pt in fcu.keyframe_points:
            pt.interpolation = 'LINEAR'
        fcu.extrapolation = 'CONSTANT'
    return
    

###################################################################################    
#
#    initialize and register
#
###################################################################################    

def menu_func(self, context):
    self.layout.operator(ImportMhx.bl_idname, text="MakeHuman (.mhx)...")

def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_import.remove(menu_func)

if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()





