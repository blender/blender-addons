# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

bl_addon_info = {
    "name": "Add Mesh: Regular Solids",
    "author": "DreamPainter",
    "version": "1",
    "blender": (2, 5, 3),
    "location": "View3D > Add > Mesh > Regular Solids",
    "description": "Add a Regular Solid mesh.",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/Add_Mesh/Add_Solid",
    "tracker_url": "https://projects.blender.org/tracker/index.php?func=detail&aid=22405&group_id=153&atid=469",
    "category": "Add Mesh"}


import bpy
from bpy.props import FloatProperty,EnumProperty,BoolProperty
from math import sqrt
from mathutils import Vector,Matrix
#from rawMeshUtils import *
from functools import reduce

# Apply view rotation to objects if "Align To" for
# new objects was set to "VIEW" in the User Preference.
def apply_object_align(context, ob):
    obj_align = bpy.context.user_preferences.edit.object_align

    if (context.space_data.type == 'VIEW_3D'
        and obj_align == 'VIEW'):
            view3d = context.space_data
            region = view3d.region_3d
            viewMatrix = region.view_matrix
            rot = viewMatrix.rotation_part()
            ob.rotation_euler = rot.invert().to_euler()


# Create a new mesh (object) from verts/edges/faces.
# verts/edges/faces ... List of vertices/edges/faces for the
#                       new mesh (as used in from_pydata).
# name ... Name of the new mesh (& object).
# edit ... Replace existing mesh data.
# Note: Using "edit" will destroy/delete existing mesh data.
def create_mesh_object(context, verts, edges, faces, name, edit):
    scene = context.scene
    obj_act = scene.objects.active

    # Can't edit anything, unless we have an active obj.
    if edit and not obj_act:
        return None

    # Create new mesh
    mesh = bpy.data.meshes.new(name)

    # Make a mesh from a list of verts/edges/faces.
    mesh.from_pydata(verts, edges, faces)

    # Update mesh geometry after adding stuff.
    mesh.update()

    # Deselect all objects.
    bpy.ops.object.select_all(action='DESELECT')

    if edit:
        # Replace geometry of existing object

        # Use the active obj and select it.
        ob_new = obj_act
        ob_new.select = True

        if obj_act.mode == 'OBJECT':
            # Get existing mesh datablock.
            old_mesh = ob_new.data

            # Set object data to nothing
            ob_new.data = None

            # Clear users of existing mesh datablock.
            old_mesh.user_clear()

            # Remove old mesh datablock if no users are left.
            if (old_mesh.users == 0):
                bpy.data.meshes.remove(old_mesh)

            # Assign new mesh datablock.
            ob_new.data = mesh

    else:
        # Create new object
        ob_new = bpy.data.objects.new(name, mesh)

        # Link new object to the given scene and select it.
        scene.objects.link(ob_new)
        ob_new.select = True

        # Place the object at the 3D cursor location.
        ob_new.location = scene.cursor_location

        apply_object_align(context, ob_new)

    if obj_act and obj_act.mode == 'EDIT':
        if not edit:
            # We are in EditMode, switch to ObjectMode.
            bpy.ops.object.mode_set(mode='OBJECT')

            # Select the active object as well.
            obj_act.select = True

            # Apply location of new object.
            scene.update()

            # Join new object into the active.
            bpy.ops.object.join()

            # Switching back to EditMode.
            bpy.ops.object.mode_set(mode='EDIT')

            ob_new = obj_act

    else:
        # We are in ObjectMode.
        # Make the new object the active one.
        scene.objects.active = ob_new

    return ob_new


# A very simple "bridge" tool.
# Connects two equally long vertex rows with faces.
# Returns a list of the new faces (list of  lists)
#
# vertIdx1 ... First vertex list (list of vertex indices).
# vertIdx2 ... Second vertex list (list of vertex indices).
# closed ... Creates a loop (first & last are closed).
# flipped ... Invert the normal of the face(s).
#
# Note: You can set vertIdx1 to a single vertex index to create
#       a fan/star of faces.
# Note: If both vertex idx list are the same length they have
#       to have at least 2 vertices.
def createFaces(vertIdx1, vertIdx2, closed=False, flipped=False):
    faces = []

    if not vertIdx1 or not vertIdx2:
        return None

    if len(vertIdx1) < 2 and len(vertIdx2) < 2:
        return None

    fan = False
    if (len(vertIdx1) != len(vertIdx2)):
        if (len(vertIdx1) == 1 and len(vertIdx2) > 1):
            fan = True
        else:
            return None

    total = len(vertIdx2)

    if closed:
        # Bridge the start with the end.
        if flipped:
            face = [
                vertIdx1[0],
                vertIdx2[0],
                vertIdx2[total - 1]]
            if not fan:
                face.append(vertIdx1[total - 1])
            faces.append(face)

        else:
            face = [vertIdx2[0], vertIdx1[0]]
            if not fan:
                face.append(vertIdx1[total - 1])
            face.append(vertIdx2[total - 1])
            faces.append(face)

    # Bridge the rest of the faces.
    for num in range(total - 1):
        if flipped:
            if fan:
                face = [vertIdx2[num], vertIdx1[0], vertIdx2[num + 1]]
            else:
                face = [vertIdx2[num], vertIdx1[num],
                    vertIdx1[num + 1], vertIdx2[num + 1]]
            faces.append(face)
        else:
            if fan:
                face = [vertIdx1[0], vertIdx2[num], vertIdx2[num + 1]]
            else:
                face = [vertIdx1[num], vertIdx2[num],
                    vertIdx2[num + 1], vertIdx1[num + 1]]
            faces.append(face)

    return faces
# this function creates a chain of quads and, when necessary, a remaining tri
# for each polygon created in this script. be aware though, that this function
# assumes each polygon is convex.
#  poly: list of faces, or a single face, like those
#        needed for mesh.from_pydata.
#  returns the tesselated faces.
def createPolys(poly):
    # check for faces
    if len(poly) == 0:
        return []
    # one or more faces
    if type(poly[0]) == type(1):
        poly = [poly] # if only one, make it a list of one face
    faces = []
    for i in poly:
        l = len(i)
        # let all faces of 3 or 4 verts be
        if l < 5:
            faces.append(i)
        # split all polygons in half and bridge the two halves
        else:
            half = int(l/2)
            f = createFaces(i[:half],[i[-1-j] for j in range(half)])        
            faces.extend(f)
            # if the polygon has an odd number of verts, add the last tri
            if l%2 == 1:
                faces.append([i[half-1],i[half],i[half+1]])
    return faces

# function to make the reduce function work as a workaround to sum a list of vectors 
def Asum(list):
    return reduce(lambda a,b: a+b, list)

# creates the 5 platonic solids as a base for the rest
#  plato: should be one of {"4","6","8","12","20"}. decides what solid the
#         outcome will be.
#  returns a list of vertices and faces and the appropriate name
def source(plato):
    verts = []
    faces = []

    # Tetrahedron
    if plato == "4":
        # Calculate the necessary constants
        s = sqrt(2)/3.0
        t = -1/3
        u = sqrt(6)/3

        # create the vertices and faces
        v = [(0,0,1),(2*s,0,t),(-s,u,t),(-s,-u,t)]
        faces = [[0,1,2],[0,2,3],[0,3,1],[1,3,2]]

    # Hexahedron (cube)
    elif plato == "6":
        # Calculate the necessary constants
        s = 1/sqrt(3)
    
        # create the vertices and faces
        v = [(-s,-s,-s),(s,-s,-s),(s,s,-s),(-s,s,-s),(-s,-s,s),(s,-s,s),(s,s,s),(-s,s,s)]
        faces = [[0,3,2,1],[0,1,5,4],[0,4,7,3],[6,5,1,2],[6,2,3,7],[6,7,4,5]]

    # Octahedron
    elif plato == "8":
        # create the vertices and faces
        v = [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]
        faces = [[4,0,2],[4,2,1],[4,1,3],[4,3,0],[5,2,0],[5,1,2],[5,3,1],[5,0,3]]

    # Dodecahedron
    elif plato == "12":
        # Calculate the necessary constants
        s = 1/sqrt(3)
        t = sqrt((3-sqrt(5))/6)
        u = sqrt((3+sqrt(5))/6)

        # create the vertices and faces
        v = [(s,s,s),(s,s,-s),(s,-s,s),(s,-s,-s),(-s,s,s),(-s,s,-s),(-s,-s,s),(-s,-s,-s),
             (t,u,0),(-t,u,0),(t,-u,0),(-t,-u,0),(u,0,t),(u,0,-t),(-u,0,t),(-u,0,-t),(0,t,u),
             (0,-t,u),(0,t,-u),(0,-t,-u)]
        faces = [[0,8,9,4,16],[0,12,13,1,8],[0,16,17,2,12],[8,1,18,5,9],[12,2,10,3,13],
                 [16,4,14,6,17],[9,5,15,14,4],[6,11,10,2,17],[3,19,18,1,13],[7,15,5,18,19],
                 [7,11,6,14,15],[7,19,3,10,11]]

    # Icosahedron
    elif plato == "20":
        # Calculate the necessary constants
        s = (1+sqrt(5))/2
        t = sqrt(1+s*s)
        s = s/t
        t = 1/t

        # create the vertices and faces
        v = [(s,t,0),(-s,t,0),(s,-t,0),(-s,-t,0),(t,0,s),(t,0,-s),(-t,0,s),(-t,0,-s),
             (0,s,t),(0,-s,t),(0,s,-t),(0,-s,-t)]
        faces = [[0,8,4],[0,5,10],[2,4,9],[2,11,5],[1,6,8],[1,10,7],[3,9,6],[3,7,11],
                 [0,10,8],[1,8,10],[2,9,11],[3,11,9],[4,2,0],[5,0,2],[6,1,3],[7,3,1],
                 [8,6,4],[9,4,6],[10,5,7],[11,7,5]]

    # handles faulty values of plato
    else:
        print("Choose keyword 'plato' from {'4','6','8','12','20'}")
        return None

    # convert the tuples to Vectors
    verts = [Vector(i) for i in v]

    return verts,faces

# processes the raw data from source
def createSolid(plato,vtrunc,etrunc,dual,snub):
    verts = []
    faces = []
    edges = []
    # the duals from each platonic solid
    dualSource = {"4":"4",
                  "6":"8",
                  "8":"6",
                  "12":"20",
                  "20":"12"}

    # constants saving space and readability
    vtrunc *= 0.5
    etrunc *= 0.5
    supposed_size = 0
    noSnub = (snub == "0") or (etrunc == 0.5) or (etrunc == 0)
    lSnub = (snub == "L") and (0 < etrunc < 0.5)
    rSnub = (snub == "R") and (0 < etrunc < 0.5)

    # no truncation
    if vtrunc == 0:
        if dual: # dual is as simple as another, but mirrored platonic solid
            vInput,fInput = source(dualSource[plato])
            supposed_size = Asum([vInput[i] for i in fInput[0]]).length/len(fInput[0])
            vInput = [-i*supposed_size for i in vInput]            # mirror it
            return vInput,fInput
        return source(plato)
    # simple truncation of the source
    elif 0.5 >= vtrunc > 0:
        vInput,fInput = source(plato)
    # truncation is now equal to simple truncation of the dual of the source
    elif vtrunc > 0.5: 
        vInput,fInput = source(dualSource[plato])
        supposed_size = Asum([vInput[i] for i in fInput[0]]).length/len(fInput[0])
        # account for the source being a dual
        vtrunc = 1-vtrunc
        if vtrunc == 0: # no truncation
            if dual:
                vInput,fInput = source(plato)
                vInput = [i*supposed_size for i in vInput]
                return vInput,fInput,sourceName
            vInput = [-i*supposed_size for i in vInput]
            return vInput,fInput

    # generate a database for creating the faces. this exists out of a list for
    # every vertex in the source
    # 0 : vertex id
    # 1 : vertices connected to this vertex, listed ccw(Counter Clock Wise)
    # 2 : vertices generated to form the faces of this vertex
    # 3 : faces connected to this vertex, listed ccw
    # 4 : dictionairy containing the verts used by the connected faces
    # 5 : list of edges that use this vertex, listed ccw
    # 6 : dictionairy containing the verts used by the connected edges
    v = [[i,[],[],[],{},[],{}] for i in range(len(vInput))]

    # this piece of code, generates the database and the lists in ccw order
    for x in range(len(fInput)):
        i = fInput[x]
        # in every faces, check which vertices connect the each vert and sort
        #  in ccw order
        for j in range(-1,len(i)-1):
            # only generate an edge dict, if edge truncation is needed
            if etrunc:
                # list edges as [min,max], to evade confusion
                first = min([i[j-1],i[j]])
                last = max([i[j-1],i[j]])
                # if an edge is not allready in, add it and give the index
                try:
                    y = edges.index([first,last])
                except:
                    edges.append([first,last])
                    y = len(edges)-1
                # add a dict item
                v[i[j]][6][str(y)] = [0,0]
            # the vertex before and after the current vertex, check whether they
            #  are allready in the database
            after = i[j+1] not in v[i[j]][1]
            before = i[j-1] not in v[i[j]][1]
            # sort them and add faces and, when necessary, edges in the database
            if after:
                if before:
                    v[i[j]][1].append(i[j+1])
                    v[i[j]][1].append(i[j-1])
                    v[i[j]][3].append(x)
                    if etrunc: v[i[j]][5].append(y)
                else:
                    z = v[i[j]][1].index(i[j-1])
                    v[i[j]][1].insert(z,i[j+1])
                    v[i[j]][3].insert(z,x)
                    if etrunc: v[i[j]][5].insert(z,y)
            else:
                z = v[i[j]][1].index(i[j+1])
                v[i[j]][3].insert(z,x)
                if etrunc: v[i[j]][5].insert(z,y)
                if before:
                    v[i[j]][1].insert(z+1,i[j-1])
            # add the current face to the current vertex in the dict
            v[i[j]][4][str(x)] = [0,0] 

    # generate vert-only truncated vertices by linear interpolation         
    for i in v:
        for j in range(len(i[1])):
            verts.append(vInput[i[0]]*(1-vtrunc)+vInput[i[1][j]]*vtrunc)
            l = len(verts)-1
            # face resulting from truncating this vertex
            i[2].append(l)
            # this vertex is used by both faces using this edge
            i[4][str(i[3][j])][1] = l
            i[4][str(i[3][j-1])][0] = l

    # only truncate edges when needed
    vert_faces = []
    if etrunc:
        # generate a new list of vertices, by linear interpolating each vert-face
        nVerts = []
        for i in v:
            f = []
            # weird range so we dont run out of array bounds
            for j in range(-1,len(i[2])-1):
                # making use of the fact that the snub operation takes only
                #  one of the two vertices per edge. so rSnub only takes the
                #  first, lSnub only takes the second, and noSnub takes both
                if rSnub or noSnub: 
                    # interpolate
                    nVerts.append((1-etrunc)*verts[i[2][j]] + etrunc*verts[i[2][j-1]])
                    # add last vertex to the vert-face, face-face and edge-face
                    l = len(nVerts)-1
                    f.append(l)
                    i[4][str(i[3][j-1])][0] = l
                    i[6][str(i[5][j-1])][1] = l
                if lSnub or noSnub:
                    # interpolate
                    nVerts.append((1-etrunc)*verts[i[2][j]] + etrunc*verts[i[2][j+1]])
                    # add last vertex to the vert-face, face-face and edge-face
                    l = len(nVerts)-1
                    f.append(l)
                    i[4][str(i[3][j])][1] = l
                    i[6][str(i[5][j-1])][0] = l
            # add vert-face
            vert_faces.append(f)

        # snub operator creates 2 tri's instead of a planar quad, needing the
        #  next piece of code. making use of the dictionairy to create them.
        if lSnub or rSnub:
            edge_faces = []
            for x in range(len(edges)):
                one = v[edges[x][0]]    # the first vertex of this edge
                two = v[edges[x][1]]    # the second
                # using max() since the dict consists of one filled spot and one
                #  empty('cause only one vert is created)
                f = [max(two[6][str(x)]),max(one[6][str(x)])]
                index = one[5].index(x)
                # create this tri from the middle line and the the previous edge
                #  on this vertex
                if lSnub:
                    f.append(max(one[6][str(one[5][index-1])]))
                else: # or in this case, the next
                    if index+1 >= len(one[5]): index = -1
                    f.append(max(one[6][str(one[5][index+1])]))
                edge_faces.append(f)

                # do the same for the other end of the edge
                f = [max(one[6][str(x)]),max(two[6][str(x)])]
                index = two[5].index(x)
                if lSnub:
                    f.append(max(two[6][str(two[5][index-1])]))
                else:
                    if index+1 >= len(one[5]): index = -1
                    f.append(max(two[6][str(two[5][index+1])]))
                edge_faces.append(f)
        else:
            # generate edge-faces from the dictionairy, simple quads for noSnub
            edge_faces = []
            for i in range(len(edges)):
                f = []
                for j in edges[i]:
                    f.extend(v[j][6][str(i)])
                edge_faces.append(f)
        verts = nVerts
    else:
        # generate vert-faces for non-edge-truncation
        vert_faces = [i[2] for i in v]

    # calculate supposed vertex length to ensure continuity
    if supposed_size:
        supposed_size *= len(vert_faces[0])/Asum([verts[i] for i in vert_faces[0]]).length
        verts = [-i*supposed_size for i in verts]
        
    # generate face-faces by looking up the old verts and replacing them with
    #  the vertices in the dictionairy
    face_faces = []
    for x in range(len(fInput)):
        f = []
        for j in fInput[x]:
            # again using the fact, that only one of the two verts is used
            #  for snub operation
            if rSnub and etrunc:
                f.append(v[j][4][str(x)][0])
            elif lSnub and etrunc:
                f.append(v[j][4][str(x)][1])
            else:
                # for cool graphics, comment the first line and uncomment the second line
                # then work the vTrunc property, leave the other properties at 0 
                # (can also change 0 to 1 in second line to change from ccw to cw)
                f.extend(v[j][4][str(x)])                  # first
                #f.append(v[j][4][str(x)][0])               # second
        face_faces.append(f)
    
    if dual:
        # create verts by taking the average of all vertices that make up each
        #  face. do it in this order to ease the following face creation
        nVerts = []
        for i in vert_faces:
            nVerts.append(Asum([verts[j] for j in i])/len(i))
        if etrunc:
            eStart = len(nVerts)
            for i in edge_faces:
                nVerts.append(Asum([verts[j] for j in i])/len(i))
        fStart = len(nVerts)
        for i in face_faces:
            nVerts.append(Asum([verts[j] for j in i])/len(i))
        # the special face generation for snub duals, it sucks, even i dont get it
        if lSnub or rSnub:
            for x in range(len(fInput)):
                i = fInput[x]
                for j in range(-1,len(i)-1):
                
                    if i[j] > i[j+1]: 
                        eNext = edges.index([i[j+1],i[j]])
                        [a,b] = [1,0]
                    else: 
                        eNext = edges.index([i[j],i[j+1]])
                        [a,b] = [0,1]
                    if i[j] > i[j-1]: 
                        ePrev = edges.index([i[j-1],i[j]])
                        [c,d] = [0,1]
                    else: 
                        ePrev = edges.index([i[j],i[j-1]])
                        [c,d] = [1,0]
                    if lSnub:
                        f = [eStart+2*eNext+b,eStart+2*eNext+a,i[j]]
                        f.append(eStart+2*ePrev+d)
                        f.append(fStart + x)
                    else:
                        f = [eStart+2*ePrev+c,eStart+2*ePrev+d,i[j]]
                        f.append(eStart+2*eNext+a)
                        f.append(fStart + x)
                    if supposed_size: faces.append(f)
                    else: faces.append(f[2:]+f[:2])
        else:
            # for noSnub situations, the face generation is somewhat easier.
            # first calculate what order faces must be added to ensure convex solids
            # this by calculating the angle between the middle of the four vertices
            #  and the first face. if the face is above the middle, use that diagonal
            #  otherwise use the other diagonal
            if etrunc:
                f = [v[0][0],eStart+v[0][5][-1],fStart+v[0][3][0],eStart+v[0][5][0]]
            else:
                f = [v[0][0],fStart+v[0][3][0],v[0][1][0],fStart+v[0][3][-1]]
            p = [nVerts[i] for i in f]
            mid = 0.25*Asum(p)
            norm = (p[1]-p[0]).cross(p[2]-p[0])
            dot = norm.dot(mid-p[0])/(norm.length*(mid-p[0]).length)
            tollerance = 0.001 # ~ cos(0.06 degrees)
            if ((dot > tollerance) and (not supposed_size)) or ((dot < -tollerance) and (supposed_size)):
                direction = 1 # first diagonal
            elif ((dot < -tollerance) and (not supposed_size)) or ((dot > tollerance) and (supposed_size)):
                direction = -1 # second diagonal
            else: 
                direction = 0 # no diagonal, face is planar (somewhat)
        
            if etrunc: # for every vertex
                for i in v: # add the face, consisting of the vert,edge,next
                            # edge and face between those edges
                    for j in range(len(i[1])):
                        f = [i[0],eStart+i[5][j-1],fStart+i[3][j],eStart+i[5][j]]
                        if direction == 1: # first diagonal
                            faces.extend([[f[0],f[1],f[3]],[f[1],f[2],f[3]]])
                        elif direction == -1: # first diagonal
                            faces.extend([[f[0],f[1],f[2]],[f[0],f[2],f[3]]])
                        else:
                            faces.append(f) # no diagonal
            else:
                for i in v: # for every vertex
                    for j in range(len(i[1])):
                        if i[0] < i[1][j]: # face consists of vert, vert on other
                                           # end of edge and both faces using that
                                           # edge, so exclude verts allready used
                            f = [i[0],fStart+i[3][j], i[1][j],fStart+i[3][j-1]]
                            if direction == -1: # secong diagonal
                                faces.extend([[f[0],f[1],f[3]],[f[1],f[2],f[3]]])
                            elif direction == 1: # first diagonal
                                faces.extend([[f[0],f[1],f[2]],[f[0],f[2],f[3]]])
                            else:
                                faces.append(f) # no diagonal
        verts = nVerts  # use new vertices
    else:
        # concatenate all faces, since they dont have to be used sepperately anymore
        faces = face_faces
        if etrunc: faces += edge_faces
        faces += vert_faces

    return verts,faces
            
        
class Solids(bpy.types.Operator):
    """Add one of the (regular) solids (mesh)"""
    bl_idname = "mesh.primitive_solid_add"
    bl_label = "(Regular) solids"
    bl_description = "Add one of the platoic or archimedean solids"
    bl_options = {'REGISTER', 'UNDO'}

    source = EnumProperty(items = (("4","Tetrahedron",""),
                                   ("6","Hexahedron",""),
                                   ("8","Octahedron",""),
                                   ("12","Dodecahedron",""),
                                   ("20","Icosahedron","")),
                          name = "Source",
                          description = "Starting point of your solid")
    size = FloatProperty(name = "Size",
                         description = "Radius of the sphere through the vertices",
                         min = 0.01,
                         soft_min = 0.01,
                         max = 100,
                         soft_max = 100,
                         default = 1.0)
    vTrunc = FloatProperty(name = "Vertex Truncation",
                           description = "Ammount of vertex truncation",
                           min = 0.0,
                           soft_min = 0.0,
                           max = 2.0,
                           soft_max = 2.0,
                           default = 0.0,
                           precision = 3,
                           step = 0.5)
    eTrunc = FloatProperty(name = "Edge Truncation",
                           description = "Ammount of edge truncation",
                           min = 0.0,
                           soft_min = 0.0,
                           max = 1.0,
                           soft_max = 1.0,
                           default = 0.0,
                           precision = 3,
                           step = 0.2)
    snub = EnumProperty(items = (("0","No Snub",""),
                                 ("L","Left Snub",""),
                                 ("R","Right Snub","")),
                        name = "Snub",
                        description = "Create the snub version")
    dual = BoolProperty(name="Dual",
                        description="Create the dual of the current solid",
                        default=False)
    keepSize = BoolProperty(name="Keep Size",
                        description="Keep the whole solid at a constant size",
                        default=False)
    preset = EnumProperty(items = (("0","Custom",""),
                                   ("t4","Truncated Tetrahedron",""),
                                   ("r4","Cuboctahedron",""),
                                   ("t6","Truncated Cube",""),
                                   ("t8","Truncated Octahedron",""),
                                   ("b6","Rhombicuboctahedron",""),
                                   ("c6","Truncated Cuboctahedron",""),
                                   ("s6","Snub Cube",""),
                                   ("r12","Icosidodecahedron",""),
                                   ("t12","Truncated Dodecahedron",""),
                                   ("t20","Truncated Icosahedron",""),
                                   ("b12","Rhombicosidodecahedron",""),
                                   ("c12","Truncated Icosidodecahedron",""),
                                   ("s12","Snub Dodecahedron",""),
                                   ("dt4","Triakis Tetrahedron",""),
                                   ("dr4","Rhombic Dodecahedron",""),
                                   ("dt6","Triakis Octahedron",""),
                                   ("dt8","Triakis Hexahedron",""),
                                   ("db6","Deltoidal Icositetrahedron",""),
                                   ("dc6","Disdyakis Dodecahedron",""),
                                   ("ds6","Pentagonal Icositetrahedron",""),
                                   ("dr12","Rhombic Triacontahedron",""),
                                   ("dt12","Triakis Icosahedron",""),
                                   ("dt20","Pentakis Dodecahedron",""),
                                   ("db12","Deltoidal Hexecontahedron",""),
                                   ("dc12","Disdyakis Triacontahedron",""),
                                   ("ds12","Pentagonal Hexecontahedron",""),
                                   ("c","Cube",""),
                                   ("sb","Soccer ball","")),
                            name = "Presets",
                            description = "Parameters for some hard names")
    
    # actual preset values
    p = {"t4":["4",2/3,0,0,"0"],
         "r4":["4",1,1,0,"0"],
         "t6":["6",2/3,0,0,"0"],
         "t8":["8",2/3,0,0,"0"],
         "b6":["6",1.0938,1,0,"0"],
         "c6":["6",1.0572,0.585786,0,"0"],
         "s6":["6",1.0875,0.704,0,"L"],
         "r12":["12",1,0,0,"0"],
         "t12":["12",2/3,0,0,"0"],
         "t20":["20",2/3,0,0,"0"],
         "b12":["12",1.1338,1,0,"0"],
         "c12":["20",0.921,0.553,0,"0"],
         "s12":["12",1.1235,0.68,0,"L"],
         "dt4":["4",2/3,0,1,"0"],
         "dr4":["4",1,2/3,1,"0"],
         "dt6":["6",4/3,0,1,"0"],
         "dt8":["8",1,0,1,"0"],
         "db6":["6",1.0938,0.756,1,"0"],
         "dc6":["6",1,1,1,"0"],
         "ds6":["6",1.0875,0.704,1,"L"],
         "dr12":["12",1.54,0,1,"0"],
         "dt12":["12",5/3,0,1,"0"],
         "dt20":["20",2/3,0,1,"0"],
         "db12":["12",1,0.912,1,"0"],
         "dc12":["20",0.921,1,1,"0"],
         "ds12":["12",1.1235,0.68,1,"L"],
         "c":["6",0,0,0,"0"],
         "sb":["20",2/3,0,0,"0"]}
    
    edit = BoolProperty(name="",
                        description="",
                        default=False,
                        options={'HIDDEN'})

    def execute(self,context):
        # turn off undo for better performance (3 - 5x faster), also makes sure
        #  that mesh ops are undoable and entire script acts as one operator
        bpy.context.user_preferences.edit.use_global_undo = False

        props = self.properties

        #if preset, set preset
        if props.preset != "0":
            using = self.p[props.preset]
            props.source = using[0]
            props.vTrunc = using[1]
            props.eTrunc = using[2]
            props.dual = using[3]
            props.snub = using[4]
            props.preset = "0"

        # generate mesh    
        verts,faces = createSolid(props.source,
                                  props.vTrunc,
                                  props.eTrunc,
                                  props.dual,
                                  props.snub)

        # turn n-gons in quads and tri's
        faces = createPolys(faces)
        
        # resize to normal size, or if keepSize, make sure all verts are of length 'size'
        if props.keepSize:
            rad = props.size/verts[0].length
        else: rad = props.size
        verts = [i*rad for i in verts]

        # generate object
        obj = create_mesh_object(context,verts,[],faces,"Solid",props.edit)

        # vertices will be on top of each other in some cases,
        #    so remove doubles then
        if ((props.vTrunc == 1) and (props.eTrunc == 0)) or (props.eTrunc == 1):
            current_mode = obj.mode
            if current_mode == 'OBJECT':
                bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.remove_doubles()
            bpy.ops.object.mode_set(mode=current_mode)

        # snub duals suck, so make all normals point outwards
        if props.dual and (props.snub != "0"):
            current_mode = obj.mode
            if current_mode == 'OBJECT':
                bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.normals_make_consistent()
            bpy.ops.object.mode_set(mode=current_mode)

        # turn undo back on
        bpy.context.user_preferences.edit.use_global_undo = True 

        return {'FINISHED'}

class Solids_add_menu(bpy.types.Menu):
    """Define the menu with presets"""
    bl_idname = "Solids_add_menu"
    bl_label = "Solids"

    def draw(self,context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator(Solids.bl_idname, text = "Solid")
        layout.menu(PlatonicMenu.bl_idname, text = "Platonic")
        layout.menu(ArchiMenu.bl_idname, text = "Archimeadean")
        layout.menu(CatalanMenu.bl_idname, text = "Catalan")
        layout.menu(OtherMenu.bl_idname, text = "Others")

class PlatonicMenu(bpy.types.Menu):
    """Define Platonic menu"""
    bl_idname = "Platonic_calls"
    bl_label = "Platonic"

    def draw(self,context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator(Solids.bl_idname, text = "Tetrahedron").source = "4"
        layout.operator(Solids.bl_idname, text = "Hexahedron").source = "6"
        layout.operator(Solids.bl_idname, text = "Octahedron").source = "8"
        layout.operator(Solids.bl_idname, text = "Dodecahedron").source = "12"
        layout.operator(Solids.bl_idname, text = "Icosahedron").source = "20"

class ArchiMenu(bpy.types.Menu):
    """Defines Achimedean preset menu"""
    bl_idname = "Achimedean_calls"
    bl_label = "Archimedean"

    def draw(self,context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator(Solids.bl_idname, text = "Truncated Tetrahedron").preset = "t4"
        layout.operator(Solids.bl_idname, text = "Cuboctahedron").preset = "r4"
        layout.operator(Solids.bl_idname, text = "Truncated Cube").preset = "t6"
        layout.operator(Solids.bl_idname, text = "Truncated Octahedron").preset = "t8"
        layout.operator(Solids.bl_idname, text = "Rhombicuboctahedron").preset = "b6"
        layout.operator(Solids.bl_idname, text = "Truncated Cuboctahedron").preset = "c6"
        layout.operator(Solids.bl_idname, text = "Snub Cube").preset = "s6"
        layout.operator(Solids.bl_idname, text = "Icosidodecahedron").preset = "r12"
        layout.operator(Solids.bl_idname, text = "Truncated Dodecahedron").preset = "t12"
        layout.operator(Solids.bl_idname, text = "Truncated Icosahedron").preset = "t20"
        layout.operator(Solids.bl_idname, text = "Rhombicosidodecahedron").preset = "b12"
        layout.operator(Solids.bl_idname, text = "Truncated Icosidodecahedron").preset = "c12"
        layout.operator(Solids.bl_idname, text = "Snub Dodecahedron").preset = "s12"

class CatalanMenu(bpy.types.Menu):
    """Defines Catalan preset menu"""
    bl_idname = "Catalan_calls"
    bl_label = "Catalan"
    
    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator(Solids.bl_idname, text = "Triakis Tetrahedron").preset = "dt4"
        layout.operator(Solids.bl_idname, text = "Rhombic Dodecahedron").preset = "dr4"
        layout.operator(Solids.bl_idname, text = "Triakis Octahedron").preset = "dt6"
        layout.operator(Solids.bl_idname, text = "Triakis Hexahedron").preset = "dt8"
        layout.operator(Solids.bl_idname, text = "Deltoidal Icositetrahedron").preset = "db6"
        layout.operator(Solids.bl_idname, text = "Disdyakis Dodecahedron").preset = "dc6"
        layout.operator(Solids.bl_idname, text = "Pentagonal Icositetrahedron").preset = "ds6"
        layout.operator(Solids.bl_idname, text = "Rhombic Triacontahedron").preset = "dr12"
        layout.operator(Solids.bl_idname, text = "Triakis Icosahedron").preset = "dt12"
        layout.operator(Solids.bl_idname, text = "Pentakis Dodecahedron").preset = "dt20"
        layout.operator(Solids.bl_idname, text = "Deltoidal Hexecontahedron").preset = "dt20"
        layout.operator(Solids.bl_idname, text = "Disdyakis Triacontahedron").preset = "db12"
        layout.operator(Solids.bl_idname, text = "Pentagonal Hexecontahedron").preset = "ds12"

class OtherMenu(bpy.types.Menu):
    """Defines Others preset menu"""
    bl_idname = "Others_calls"
    bl_label = "Others"
    
    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator(Solids.bl_idname, text = "Cube").preset = "c"
        layout.operator(Solids.bl_idname, text = "Soccer ball").preset = "sb"
        

import space_info


def menu_func(self, context):
    self.layout.menu(Solids_add_menu.bl_idname, icon="PLUGIN")


def register():
    space_info.INFO_MT_mesh_add.append(menu_func)

def unregister():
    space_info.INFO_MT_mesh_add.remove(menu_func)
      
if __name__ == "__main__":
    register()
