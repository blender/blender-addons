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
Version 1.0.3

"""

bl_addon_info = {
    'name': 'Import: MakeHuman (.mhx)',
    'author': 'Thomas Larsson',
    'version': (1, 0, 3),
    'blender': (2, 5, 5),
    'api': 33590,
    'location': "File > Import",
    'description': 'Import files in the MakeHuman eXchange format (.mhx)',
    'warning': '',
    'wiki_url': 'http://wiki.blender.org/index.php/Extensions:2.5/Py/'\
        'Scripts/Import-Export/Make_Human',
    'tracker_url': 'https://projects.blender.org/tracker/index.php?'\
        'func=detail&aid=21872&group_id=153&atid=469',
    'category': 'Import-Export'}

"""
Place this file in the .blender/scripts/addons dir
You have to activated the script in the "Add-Ons" tab (user preferences).
Access from the File > Import menu.
"""

MAJOR_VERSION = 1
MINOR_VERSION = 0
SUB_VERSION = 3
BLENDER_VERSION = (2, 55, 1)

#
#
#

import bpy
import os
import time
import mathutils
from mathutils import *
#import geometry
#import string

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

todo = []

#
#    toggle flags
#

T_EnforceVersion = 0x01
T_Clothes = 0x02
T_Stretch = 0x04
T_Bend = 0x08

T_Diamond = 0x10
T_Replace = 0x20
T_Face = 0x40
T_Shape = 0x80

T_Mesh = 0x100
T_Armature = 0x200
T_Proxy = 0x400
T_Cage = 0x800

T_Rigify = 0x1000
T_Preset = 0x2000
T_Symm = 0x4000
T_MHX = 0x8000

toggle = T_EnforceVersion + T_Replace + T_Mesh + T_Armature + T_Face + T_Shape + T_Proxy + T_Clothes

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
"This version of the MHX importer only works with Blender (%d, %d, %d) or later. " % (a, b, c) +
"Download a more recent Blender from www.blender.org or www.graphicall.org.\n"
    )
    raise NameError(msg)
    return

#
#    readMhxFile(filePath, scale):
#

def readMhxFile(filePath, scale):
    global todo, nErrors, theScale, defaultScale, One, toggle

    checkBlenderVersion()    
    
    theScale = scale
    defaultScale = scale
    One = 1.0/theScale

    fileName = os.path.expanduser(filePath)
    (shortName, ext) = os.path.splitext(fileName)
    if ext.lower() != ".mhx":
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
            print("Doing %s" % expr)
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
    if  major != MAJOR_VERSION or minor != MINOR_VERSION:
        if warnedVersion:
            return
        else:
            msg = (
"Wrong MHX version\n" +
"Expected MHX %d.%d but the loaded file has version MHX %d.%d\n" % (MAJOR_VERSION, MINOR_VERSION, major, minor) +
"You can disable this error message by deselecting the Enforce version option when importing. " +
"Alternatively, you can try to download the most recent nightly build from www.makehuman.org. " +
"The current version of the import script is located in the importers/mhx/blender25x folder and is called import_scene_mhx.py. " +
"The version distributed with Blender builds from www.graphicall.org may be out of date.\n"
)
        if toggle & T_EnforceVersion:
            raise NameError(msg)
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
        # print("Parse %s" % key)
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
            raise NameError(msg)    
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
        elif key == "Process":
            parseProcess(val, sub)
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
                raise NameError("ShapeKeys object %s does not exist" % val[0])
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
                pt.interpolation = 'LINEAR'
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
    n = 1
    for (key, val, sub) in tokens:
        if key == 'Driver':
            fcu = parseDriver(adata, dataPath, index, rna, val, sub)
            fmod = fcu.modifiers[0]
            fcu.modifiers.remove(fmod)
        elif key == 'FModifier':
            parseFModifier(fcu, val, sub)
        elif key == 'kp':
            pt = fcu.keyframe_points.add(n, 0)
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
    
    #print("expr", rna, expr)
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
    targ.id = loadedData['Object'][args[0]]
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
    if mat == None:
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
            if img == None:
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
            raise NameError("Failed to find data: %s %s %s" % (name, typ, datName))
            return

    try:
        ob = loadedData['Object'][name]
        bpy.context.scene.objects.active = ob
        #print("Found data", ob)
    except:
        ob = None

    if ob == None:
        print("Create", name, data, datName)
        ob = createObject(typ, name, data, datName)
        print("created", ob)
        linkObject(ob, data)

    for (key, val, sub) in tokens:
        if key == 'Modifier':
            parseModifier(ob, val, sub)
        elif key == 'Constraint':
            parseConstraint(ob.constraints, val, sub)
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
    if data and ob.data == None:
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

    for n,mat in enumerate(list(me.materials)):
        print(n, mat)
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
                ob.vertex_groups.assign( [int(val[0])], group, float(val[1]), 'REPLACE' )
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
        raise NameError("ShapeKey L/R %s" % lr)
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
    
    if mode == 'Rigify':
        toggle |= T_Rigify
        return parseRigify(amtname, obname, tokens)

    toggle &= ~T_Rigify
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
                parseBone(bone, amt, sub, heads, tails)
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
    print( "Parsing bonegroup %s" % args )
    name = args[0]
    bpy.ops.pose.group_add()
    print(dir(pose.bone_groups))
    bg = pose.bone_groups.active
    print("Created", bg)
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

    # Make posebone active - don't know how to do this in pose mode
    bpy.ops.object.mode_set(mode='OBJECT')
    amt.bones.active = amt.bones[name]
    bpy.ops.object.mode_set(mode='POSE')

    for (key, val, sub) in tokens:
        if key == 'Constraint':
            cns = parseConstraint(pb.constraints, val, sub)
        elif key == 'bpyops':
            bpy.ops.object.mode_set(mode='OBJECT')
            amt.bones.active = amt.bones[name]
            ob.constraints.active = cns            
            expr = "bpy.ops.%s" % val[0]
            # print(expr)
            exec(expr)
            bpy.ops.object.mode_set(mode='POSE')
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
            v = points[n].co
            (x,y,z) = eval(val[0])
            v.x = theScale*x
            v.y = theScale*y
            v.z = theScale*z

            v = points[n].deformed_co
            (x,y,z) = eval(val[1])
            v.x = theScale*x
            v.y = theScale*y
            v.z = theScale*z

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
    for (key, val, sub) in tokens:
        if key == 'ob':
            try:
                ob = loadedData['Object'][val[0]]
                grp.objects.link(ob)
            except:
                pass
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
#    postProcess()
#

def postProcess():
    if not toggle & T_MHX:
        return
    try:
        ob = loadedData['Object']['HumanMesh']
    except:
        ob = None
    if toggle & T_Diamond == 0 and ob:
        deleteDiamonds(ob)
    if toggle & T_Rigify and False:
        for rig in loadedData['Rigify'].values():
            bpy.context.scene.objects.active = rig
            print("Rigify", rig)
            bpy.ops.pose.metarig_generate()
            print("Metarig generated")
            #bpy.context.scene.objects.unlink(rig)

            rig = bpy.context.scene.objects.active
            print("Rigged", rig, bpy.context.object)
            ob = loadedData['Object']['HumanMesh']
            mod = ob.modifiers[0]
            print(ob, mod, mod.object)
            mod.object = rig
            print("Rig changed", mod.object)
    return            

#
#    deleteDiamonds(ob)
#    Delete joint diamonds in main mesh
#

def deleteDiamonds(ob):
    bpy.context.scene.objects.active = ob
    if not bpy.context.object:
        return
    print("Delete diamonds in %s" % bpy.context.object)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    me = ob.data
    for f in me.faces:        
        if len(f.vertices) < 4:
            for vn in f.vertices:
                me.vertices[vn].select = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.delete(type='VERT')
    bpy.ops.object.mode_set(mode='OBJECT')
    return

    
#
#    parseProcess(args, tokens):
#    applyTransform(objects, rig, parents):
#

def parseProcess(args, tokens):
    if toggle & T_Bend == 0:
        return
    try:
        rig = loadedData['Object'][args[0]]
    except:
        rig = None
    if not rig:
        return

    parents = {}
    objects = []

    for (key, val, sub) in tokens:
        #print(key, val)
        if key == 'Reparent':
            bname = val[0]
            try:
                eb = ebones[bname]
                parents[bname] = eb.parent.name
                eb.parent = ebones[val[1]]
            except:
                pass
        elif key == 'Bend':
            axis = val[1]
            angle = float(val[2])
            mat = mathutils.Matrix.Rotation(angle, 4, axis)
            try:
                pb = pbones[val[0]]
                prod = pb.matrix_local * mat
                for i in range(4):
                    for j in range(4):
                        pb.matrix_local[i][j] = prod[i][j]
            except:
                print("No bone "+val[0])
                pass
        elif key == 'Snap':
            try:
                eb = ebones[val[0]]
            except:
                eb = None
            tb = ebones[val[1]]
            typ = val[2]
            if eb == None:
                pass
            elif typ == 'Inv':
                eb.head = tb.tail
                eb.tail = tb.head
            elif typ == 'Head':
                eb.head = tb.head
            elif typ == 'Tail':
                eb.tail = tb.tail
            elif typ == 'Both':
                eb.head = tb.head
                eb.tail = tb.tail
                eb.roll = tb.roll
            else:
                raise NameError("Snap type %s" % typ)
        elif key == 'PoseMode':
            bpy.context.scene.objects.active = rig
            bpy.ops.object.mode_set(mode='POSE')
            pbones = rig.pose.bones    
        elif key == 'ObjectMode':
            bpy.context.scene.objects.active = rig
            bpy.ops.object.mode_set(mode='POSE')
            pbones = rig.pose.bones    
        elif key == 'EditMode':
            bpy.context.scene.objects.active = rig
            bpy.ops.object.mode_set(mode='EDIT')
            ebones = rig.data.edit_bones    
            bpy.ops.armature.select_all(action='DESELECT')
        elif key == 'Roll':
            try:
                eb = ebones[val[0]]
            except:
                eb = None
            if eb:
                eb.roll = float(val[1])
        elif key == 'Select':
            pass
        elif key == 'RollUp':
            pass
        elif key == 'Apply':
            applyTransform(objects, rig, parents)
        elif key == 'ApplyArmature':
            try:
                ob = loadedData['Object'][val[0]]
                objects.append((ob,sub))
            except:
                ob = None
        elif key == 'Object':
            try:
                ob = loadedData['Object'][val[0]]
            except:
                ob = None
            if ob:
                bpy.context.scene.objects.active = ob
                #mod = ob.modifiers[0]
                #ob.modifiers.remove(mod)
                for (key1, val1, sub1) in sub:
                    if key1 == 'Modifier':
                        parseModifier(ob, val1, sub1)
    return

def applyTransform(objects, rig, parents):
    for (ob,tokens) in objects:
        print("Applying transform to %s" % ob)
        bpy.context.scene.objects.active = ob        
        bpy.ops.object.visual_transform_apply()
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier='Armature')

    bpy.context.scene.objects.active = rig
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.armature_apply()
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')
    ebones = rig.data.edit_bones
    for (bname, pname) in parents.items():
        eb = ebones[bname]
        par = ebones[pname]
        if eb.use_connect:
            par.tail = eb.head
        eb.parent = par

    bpy.ops.object.mode_set(mode='OBJECT')
    return            

#
#    defaultKey(ext, args, tokens, var, exclude, glbals, lcals):
#

def defaultKey(ext, args, tokens, var, exclude, glbals, lcals):
    global todo

    if ext == 'Property':
        try:
            expr = "%s['%s'] = %s" % (var, args[0], args[1])
        except:
            expr = None
        # print("Property", expr)
        if expr:
            exec(expr, glbals, lcals)
        return
        
    nvar = "%s.%s" % (var, ext)
    #print(ext)
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
        pushOnTodoList(var, expr, glbals, lcals)
    return

#
#
#

def pushOnTodoList(var, expr, glbals, lcals):
    global todo
    print("Tdo", var)
    print(dir(eval(var, glbals, lcals)))
    raise NameError("Todo", expr)
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
        if ob.type == "MESH" or ob.type == "ARMATURE" or ob.type == 'EMPTY':
            scn.objects.active = ob
            bpy.ops.object.mode_set(mode='OBJECT')
            scn.objects.unlink(ob)
            del ob
    #print(scn.objects)
    return scn

def hideLayers():
    scn = bpy.context.scene
    for n in range(len(scn.layers)):
        if n < 8:
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

    filepath = StringProperty(name="File Path", description="File path used for importing the MHX file", maxlen= 1024, default= "")

    scale = FloatProperty(name="Scale", description="Default meter, decimeter = 1.0", default = theScale)



    enforce = BoolProperty(name="Enforce version", description="Only accept MHX files of correct version", default=toggle&T_EnforceVersion)
    mesh = BoolProperty(name="Mesh", description="Use main mesh", default=toggle&T_Mesh)
    proxy = BoolProperty(name="Proxies", description="Use proxies", default=toggle&T_Proxy)
    armature = BoolProperty(name="Armature", description="Use armature", default=toggle&T_Armature)
    replace = BoolProperty(name="Replace scene", description="Replace scene", default=toggle&T_Replace)
    cage = BoolProperty(name="Cage", description="Load mesh deform cage", default=toggle&T_Cage)
    clothes = BoolProperty(name="Clothes", description="Include clothes", default=toggle&T_Clothes)
    stretch = BoolProperty(name="Stretchy limbs", description="Stretchy limbs", default=toggle&T_Stretch)
    face = BoolProperty(name="Face shapes", description="Include facial shapekeys", default=toggle&T_Face)
    shape = BoolProperty(name="Body shapes", description="Include body shapekeys", default=toggle&T_Shape)
    symm = BoolProperty(name="Symmetric shapes", description="Keep shapekeys symmetric", default=toggle&T_Symm)
    diamond = BoolProperty(name="Diamonds", description="Keep joint diamonds", default=toggle&T_Diamond)
    bend = BoolProperty(name="Bend joints", description="Bend joints for better IK", default=toggle&T_Bend)
        
    def execute(self, context):
        global toggle
        O_EnforceVersion = T_EnforceVersion if self.properties.enforce else 0
        O_Mesh = T_Mesh if self.properties.mesh else 0
        O_Proxy = T_Proxy if self.properties.proxy else 0
        O_Armature = T_Armature if self.properties.armature else 0
        O_Replace = T_Replace if self.properties.replace else 0
        O_Cage = T_Cage if self.properties.cage else 0
        O_Clothes = T_Clothes if self.properties.clothes else 0
        O_Stretch = T_Stretch if self.properties.stretch else 0
        O_Face = T_Face if self.properties.face else 0
        O_Shape = T_Shape if self.properties.shape else 0
        O_Symm = T_Symm if self.properties.symm else 0
        O_Diamond = T_Diamond if self.properties.diamond else 0
        O_Bend = T_Bend if self.properties.bend else 0
        toggle = ( O_EnforceVersion | O_Mesh | O_Proxy | O_Armature | O_Replace | O_Stretch | O_Cage | 
                O_Face | O_Shape | O_Symm | O_Diamond | O_Bend | O_Clothes | T_MHX )

        print("Load", self.properties.filepath)
        readMhxFile(self.properties.filepath, self.properties.scale)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def menu_func(self, context):
    self.layout.operator(IMPORT_OT_makehuman_mhx.bl_idname, text="MakeHuman (.mhx)...")

def register():
    bpy.types.INFO_MT_file_import.append(menu_func)

def unregister():
    bpy.types.INFO_MT_file_import.remove(menu_func)

if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()

#
#    Testing
#
"""
#readMhxFile("C:/Documents and Settings/xxxxxxxxxxxxxxxxxxxx/Mina dokument/makehuman/exports/foo-25.mhx", 'Classic')
readMhxFile("/home/thomas/makehuman/exports/foo-25.mhx", 1.0)

#toggle = T_Replace + T_Mesh + T_Armature + T_MHX
#readMhxFile("/home/thomas/myblends/test.mhx", 1.0)
"""




