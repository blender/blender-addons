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

import bpy
import io
import math
import os
import copy
from math import pi, cos, sin
from mathutils import Vector, Matrix
from copy import copy

from . import import_pdb

ATOM_PDB_FILEPATH = ""
ATOM_PDB_PDBTEXT  = (  "REMARK This pdb file has been created with Blender "
                     + "and the Atomic Blender script\n"
                     + "REMARK For more details see wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Import-Export/PDB\n"
                     + "REMARK\n"
                     + "REMARK\n")


class CLASS_atom_pdb_atoms_export(object):  
    __slots__ = ('element', 'location')
    def __init__(self, element, location):
        self.element  = element
        self.location = location


def DEF_atom_pdb_export(obj_type):

    list_atoms = []
    for obj in bpy.context.selected_objects:
    
        if "Stick" in obj.name:
            continue
            
        if obj.type != "SURFACE" and obj.type != "MESH":
            continue 
       
        name = ""
        for element in import_pdb.ATOM_PDB_ELEMENTS_DEFAULT:
            if element[1] in obj.name:
                if element[2] == "Vac":
                    name = "X"
                else:
                    name = element[2]
            elif element[1][:3] in obj.name:
                if element[2] == "Vac":
                    name = "X"
                else:
                    name = element[2]
        
        if name == "":
            if obj_type == "0":
                name = "?"
            else:
                continue

        if len(obj.children) != 0:
            for vertex in obj.data.vertices:
                list_atoms.append(CLASS_atom_pdb_atoms_export(
                                                       name,
                                                       obj.location+vertex.co))
        else:
            if not obj.parent:
                list_atoms.append(CLASS_atom_pdb_atoms_export(
                                                       name,
                                                       obj.location))

    pdb_file_p = open(ATOM_PDB_FILEPATH, "w")
    pdb_file_p.write(ATOM_PDB_PDBTEXT)

    for i, atom in enumerate(list_atoms):
        string = "ATOM %6d%3s%24.3f%8.3f%8.3f%6.2f%6.2f%12s\n" % (
                                      i, atom.element,
                                      atom.location[0],
                                      atom.location[1],
                                      atom.location[2],
                                      1.00, 1.00, atom.element)
        pdb_file_p.write(string)

    pdb_file_p.close()

    return True

