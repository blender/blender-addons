# -*- coding:utf-8 -*-

import bpy
from .DelaunayVoronoi import (
            computeVoronoiDiagram,
            computeDelaunayTriangulation,
            )
from bpy.types import (
        Operator,
        Panel,
        )
from bpy.props import EnumProperty


class Point:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z


def unique(L):
    """Return a list of unhashable elements in s, but without duplicates.
    [[1, 2], [2, 3], [1, 2]] >>> [[1, 2], [2, 3]]"""
    # For unhashable objects, you can sort the sequence and
    # then scan from the end of the list, deleting duplicates as you go
    nDupli = 0
    nZcolinear = 0
    # sort() brings the equal elements together; then duplicates
    # are easy to weed out in a single pass
    L.sort()
    last = L[-1]
    for i in range(len(L) - 2, -1, -1):
        if last[:2] == L[i][:2]:    # XY coordinates compararison
            if last[2] == L[i][2]:  # Z coordinates compararison
                nDupli += 1         # duplicates vertices
            else:  # Z colinear
                nZcolinear += 1
            del L[i]
        else:
            last = L[i]
    # list data type is mutable, input list will automatically update
    # and doesn't need to be returned
    return (nDupli, nZcolinear)


def checkEqual(lst):
    return lst[1:] == lst[:-1]


class ToolsPanelDelaunay(Panel):
    bl_category = "Create"
    bl_label = "Delaunay Voronoi"
    bl_space_type = "VIEW_3D"
    bl_context = "objectmode"
    bl_region_type = "TOOLS"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        layout.label('Constellation')
        self.layout.operator("delaunay.triangulation")
        self.layout.operator("voronoi.tesselation")
        layout.label('Constellation')
        layout.operator("mesh.constellation", text="Cross Section")


class OBJECT_OT_TriangulateButton(Operator):
    bl_idname = "delaunay.triangulation"
    bl_label = "Triangulation"
    bl_description = "Terrain points cloud Delaunay triangulation in 2.5D"
    bl_options = {"UNDO"}

    def execute(self, context):
        # Get selected obj
        objs = bpy.context.selected_objects
        if len(objs) == 0 or len(objs) > 1:
            self.report({'INFO'}, "Selection is empty or too much object selected")
            return {'FINISHED'}

        obj = objs[0]
        if obj.type != 'MESH':
            self.report({'INFO'}, "Selection isn't a mesh")
            return {'FINISHED'}

        # Get points coodinates
        r = obj.rotation_euler
        s = obj.scale
        mesh = obj.data
        vertsPts = [vertex.co for vertex in mesh.vertices]
        # Remove duplicate
        verts = [[vert.x, vert.y, vert.z] for vert in vertsPts]
        nDupli, nZcolinear = unique(verts)
        nVerts = len(verts)
        print(str(nDupli) + " duplicates points ignored")
        print(str(nZcolinear) + " z colinear points excluded")
        if nVerts < 3:
            self.report({'ERROR'}, "Not enough points")
            return {'FINISHED'}

        # Check colinear
        xValues = [pt[0] for pt in verts]
        yValues = [pt[1] for pt in verts]

        if checkEqual(xValues) or checkEqual(yValues):
            self.report({'ERROR'}, "Points are colinear")
            return {'FINISHED'}

        # Triangulate
        print("Triangulate " + str(nVerts) + " points...")
        vertsPts = [Point(vert[0], vert[1], vert[2]) for vert in verts]
        triangles = computeDelaunayTriangulation(vertsPts)
        # reverse point order --> if all triangles are specified anticlockwise then all faces up
        triangles = [tuple(reversed(tri)) for tri in triangles]

        print(str(len(triangles)) + " triangles")

        # Create new mesh structure
        print("Create mesh...")
        tinMesh = bpy.data.meshes.new("TIN")        # create a new mesh
        tinMesh.from_pydata(verts, [], triangles)   # Fill the mesh with triangles
        tinMesh.update(calc_edges=True)             # Update mesh with new data

        # Create an object with that mesh
        tinObj = bpy.data.objects.new("TIN", tinMesh)
        # Place object
        tinObj.location = obj.location.copy()
        tinObj.rotation_euler = r
        tinObj.scale = s
        # Update scene
        bpy.context.scene.objects.link(tinObj)  # Link object to scene
        bpy.context.scene.objects.active = tinObj
        tinObj.select = True
        obj.select = False
        # Report
        self.report({'INFO'}, "Mesh created (" + str(len(triangles)) + " triangles)")
        return {'FINISHED'}


class OBJECT_OT_VoronoiButton(Operator):
    bl_idname = "voronoi.tesselation"
    bl_label = "Diagram"
    bl_description = "Points cloud Voronoi diagram in 2D"
    bl_options = {"REGISTER", "UNDO"}

    meshType = EnumProperty(
                    items=[("Edges", "Edges", ""), ("Faces", "Faces", "")],
                    name="Mesh type",
                    description=""
                    )

    def execute(self, context):
        # Get selected obj
        objs = bpy.context.selected_objects
        if len(objs) == 0 or len(objs) > 1:
            self.report({'INFO'}, "Selection is empty or too much object selected")
            return {'FINISHED'}

        obj = objs[0]
        if obj.type != 'MESH':
            self.report({'INFO'}, "Selection isn't a mesh")
            return {'FINISHED'}

        # Get points coodinates
        r = obj.rotation_euler
        s = obj.scale
        mesh = obj.data
        vertsPts = [vertex.co for vertex in mesh.vertices]

        # Remove duplicate
        verts = [[vert.x, vert.y, vert.z] for vert in vertsPts]
        nDupli, nZcolinear = unique(verts)
        nVerts = len(verts)

        print(str(nDupli) + " duplicates points ignored")
        print(str(nZcolinear) + " z colinear points excluded")

        if nVerts < 3:
            self.report({'ERROR'}, "Not enough points")
            return {'FINISHED'}

        # Check colinear
        xValues = [pt[0] for pt in verts]
        yValues = [pt[1] for pt in verts]
        if checkEqual(xValues) or checkEqual(yValues):
            self.report({'ERROR'}, "Points are colinear")
            return {'FINISHED'}

        # Create diagram
        print("Tesselation... (" + str(nVerts) + " points)")
        xbuff, ybuff = 5, 5
        zPosition = 0
        vertsPts = [Point(vert[0], vert[1], vert[2]) for vert in verts]
        if self.meshType == "Edges":
            pts, edgesIdx = computeVoronoiDiagram(
                                vertsPts, xbuff, ybuff, polygonsOutput=False, formatOutput=True
                                )
        else:
            pts, polyIdx = computeVoronoiDiagram(
                                vertsPts, xbuff, ybuff, polygonsOutput=True,
                                formatOutput=True, closePoly=False
                                )

        pts = [[pt[0], pt[1], zPosition] for pt in pts]

        # Create new mesh structure
        voronoiDiagram = bpy.data.meshes.new("VoronoiDiagram")  # create a new mesh

        if self.meshType == "Edges":
            # Fill the mesh with triangles
            voronoiDiagram.from_pydata(pts, edgesIdx, [])
        else:
            # Fill the mesh with triangles
            voronoiDiagram.from_pydata(pts, [], list(polyIdx.values()))

        voronoiDiagram.update(calc_edges=True)  # Update mesh with new data
        # create an object with that mesh
        voronoiObj = bpy.data.objects.new("VoronoiDiagram", voronoiDiagram)
        # place object
        voronoiObj.location = obj.location.copy()
        voronoiObj.rotation_euler = r
        voronoiObj.scale = s

        # update scene
        bpy.context.scene.objects.link(voronoiObj)  # Link object to scene
        bpy.context.scene.objects.active = voronoiObj
        voronoiObj.select = True
        obj.select = False

        # Report
        if self.meshType == "Edges":
            self.report({'INFO'}, "Mesh created (" + str(len(edgesIdx)) + " edges)")
        else:
            self.report({'INFO'}, "Mesh created (" + str(len(polyIdx)) + " polygons)")

        return {'FINISHED'}
