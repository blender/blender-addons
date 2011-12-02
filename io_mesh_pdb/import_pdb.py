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

#
#
#  Authors           : Clemens Barth (Blendphys@root-1.de), ...
#
#  Homepage(Wiki)    : http://development.root-1.de/Atomic_Blender.php
#  Tracker           : http://projects.blender.org/tracker/index.php?func=detail&aid=29226&group_id=153&atid=467
#
#  Start of project              : 2011-08-31 by Clemens Barth
#  First publication in Blender  : 2011-11-11
#  Last modified                 : 2011-12-01
#
#  Acknowledgements: Thanks to ideasman, meta_androcto, truman, kilon,
#  dairin0d, PKHG, Valter, etc
#

import bpy
import io
import math
import os
from math import pi, cos, sin
from mathutils import Vector, Matrix

# These are variables, which contain the name of the PDB file and
# the path of the PDB file.
# They are used almost everywhere, which is the reason why they
# should stay global. First, they are empty and get 'filled' directly
# after having chosen the PDB file (see 'class LoadPDB' further below).

ATOM_PDB_FILEPATH = ""

# Some string stuff for the console.
ATOM_PDB_STRING = "Atomic Blender\n==================="


# -----------------------------------------------------------------------------
#                                                  Atom, stick and element data


# This is a list that contains some data of all possible elements. The structure
# is as follows:
#
# 1, "Hydrogen", "H", [0.0,0.0,1.0], 0.32, 0.32, 0.32 , -1 , 1.54   means
#
# No., name, short name, color, radius (used), radius (covalent), radius (atomic),
#
# charge state 1, radius (ionic) 1, charge state 2, radius (ionic) 2, ... all
# charge states for any atom are listed, if existing.
# The list is fixed and cannot be changed ... (see below)

ATOM_PDB_ELEMENTS_DEFAULT = (
( 1,      "Hydrogen",        "H", (  1.0,   1.0,   1.0), 0.32, 0.32, 0.79 , -1 , 1.54 ),
( 2,        "Helium",       "He", ( 0.85,   1.0,   1.0), 0.93, 0.93, 0.49 ),
( 3,       "Lithium",       "Li", (  0.8,  0.50,   1.0), 1.23, 1.23, 2.05 ,  1 , 0.68 ),
( 4,     "Beryllium",       "Be", ( 0.76,   1.0,   0.0), 0.90, 0.90, 1.40 ,  1 , 0.44 ,  2 , 0.35 ),
( 5,         "Boron",        "B", (  1.0,  0.70,  0.70), 0.82, 0.82, 1.17 ,  1 , 0.35 ,  3 , 0.23 ),
( 6,        "Carbon",        "C", ( 0.56,  0.56,  0.56), 0.77, 0.77, 0.91 , -4 , 2.60 ,  4 , 0.16 ),
( 7,      "Nitrogen",        "N", ( 0.18,  0.31,  0.97), 0.75, 0.75, 0.75 , -3 , 1.71 ,  1 , 0.25 ,  3 , 0.16 ,  5 , 0.13 ),
( 8,        "Oxygen",        "O", (  1.0,  0.05,  0.05), 0.73, 0.73, 0.65 , -2 , 1.32 , -1 , 1.76 ,  1 , 0.22 ,  6 , 0.09 ),
( 9,      "Fluorine",        "F", ( 0.56,  0.87,  0.31), 0.72, 0.72, 0.57 , -1 , 1.33 ,  7 , 0.08 ),
(10,          "Neon",       "Ne", ( 0.70,  0.89,  0.96), 0.71, 0.71, 0.51 ,  1 , 1.12 ),
(11,        "Sodium",       "Na", ( 0.67,  0.36,  0.94), 1.54, 1.54, 2.23 ,  1 , 0.97 ),
(12,     "Magnesium",       "Mg", ( 0.54,   1.0,   0.0), 1.36, 1.36, 1.72 ,  1 , 0.82 ,  2 , 0.66 ),
(13,     "Aluminium",       "Al", ( 0.74,  0.65,  0.65), 1.18, 1.18, 1.82 ,  3 , 0.51 ),
(14,       "Silicon",       "Si", ( 0.94,  0.78,  0.62), 1.11, 1.11, 1.46 , -4 , 2.71 , -1 , 3.84 ,  1 , 0.65 ,  4 , 0.42 ),
(15,    "Phosphorus",        "P", (  1.0,  0.50,   0.0), 1.06, 1.06, 1.23 , -3 , 2.12 ,  3 , 0.44 ,  5 , 0.35 ),
(16,        "Sulfur",        "S", (  1.0,   1.0,  0.18), 1.02, 1.02, 1.09 , -2 , 1.84 ,  2 , 2.19 ,  4 , 0.37 ,  6 , 0.30 ),
(17,      "Chlorine",       "Cl", ( 0.12,  0.94,  0.12), 0.99, 0.99, 0.97 , -1 , 1.81 ,  5 , 0.34 ,  7 , 0.27 ),
(18,         "Argon",       "Ar", ( 0.50,  0.81,  0.89), 0.98, 0.98, 0.88 ,  1 , 1.54 ),
(19,     "Potassium",        "K", ( 0.56,  0.25,  0.83), 2.03, 2.03, 2.77 ,  1 , 0.81 ),
(20,       "Calcium",       "Ca", ( 0.23,   1.0,   0.0), 1.74, 1.74, 2.23 ,  1 , 1.18 ,  2 , 0.99 ),
(21,      "Scandium",       "Sc", ( 0.90,  0.90,  0.90), 1.44, 1.44, 2.09 ,  3 , 0.73 ),
(22,      "Titanium",       "Ti", ( 0.74,  0.76,  0.78), 1.32, 1.32, 2.00 ,  1 , 0.96 ,  2 , 0.94 ,  3 , 0.76 ,  4 , 0.68 ),
(23,      "Vanadium",        "V", ( 0.65,  0.65,  0.67), 1.22, 1.22, 1.92 ,  2 , 0.88 ,  3 , 0.74 ,  4 , 0.63 ,  5 , 0.59 ),
(24,      "Chromium",       "Cr", ( 0.54,   0.6,  0.78), 1.18, 1.18, 1.85 ,  1 , 0.81 ,  2 , 0.89 ,  3 , 0.63 ,  6 , 0.52 ),
(25,     "Manganese",       "Mn", ( 0.61,  0.47,  0.78), 1.17, 1.17, 1.79 ,  2 , 0.80 ,  3 , 0.66 ,  4 , 0.60 ,  7 , 0.46 ),
(26,          "Iron",       "Fe", ( 0.87,   0.4,   0.2), 1.17, 1.17, 1.72 ,  2 , 0.74 ,  3 , 0.64 ),
(27,        "Cobalt",       "Co", ( 0.94,  0.56,  0.62), 1.16, 1.16, 1.67 ,  2 , 0.72 ,  3 , 0.63 ),
(28,        "Nickel",       "Ni", ( 0.31,  0.81,  0.31), 1.15, 1.15, 1.62 ,  2 , 0.69 ),
(29,        "Copper",       "Cu", ( 0.78,  0.50,   0.2), 1.17, 1.17, 1.57 ,  1 , 0.96 ,  2 , 0.72 ),
(30,          "Zinc",       "Zn", ( 0.49,  0.50,  0.69), 1.25, 1.25, 1.53 ,  1 , 0.88 ,  2 , 0.74 ),
(31,       "Gallium",       "Ga", ( 0.76,  0.56,  0.56), 1.26, 1.26, 1.81 ,  1 , 0.81 ,  3 , 0.62 ),
(32,     "Germanium",       "Ge", (  0.4,  0.56,  0.56), 1.22, 1.22, 1.52 , -4 , 2.72 ,  2 , 0.73 ,  4 , 0.53 ),
(33,       "Arsenic",       "As", ( 0.74,  0.50,  0.89), 1.20, 1.20, 1.33 , -3 , 2.22 ,  3 , 0.58 ,  5 , 0.46 ),
(34,      "Selenium",       "Se", (  1.0,  0.63,   0.0), 1.16, 1.16, 1.22 , -2 , 1.91 , -1 , 2.32 ,  1 , 0.66 ,  4 , 0.50 ,  6 , 0.42 ),
(35,       "Bromine",       "Br", ( 0.65,  0.16,  0.16), 1.14, 1.14, 1.12 , -1 , 1.96 ,  5 , 0.47 ,  7 , 0.39 ),
(36,       "Krypton",       "Kr", ( 0.36,  0.72,  0.81), 1.31, 1.31, 1.24 ),
(37,      "Rubidium",       "Rb", ( 0.43,  0.18,  0.69), 2.16, 2.16, 2.98 ,  1 , 1.47 ),
(38,     "Strontium",       "Sr", (  0.0,   1.0,   0.0), 1.91, 1.91, 2.45 ,  2 , 1.12 ),
(39,       "Yttrium",        "Y", ( 0.58,   1.0,   1.0), 1.62, 1.62, 2.27 ,  3 , 0.89 ),
(40,     "Zirconium",       "Zr", ( 0.58,  0.87,  0.87), 1.45, 1.45, 2.16 ,  1 , 1.09 ,  4 , 0.79 ),
(41,       "Niobium",       "Nb", ( 0.45,  0.76,  0.78), 1.34, 1.34, 2.08 ,  1 , 1.00 ,  4 , 0.74 ,  5 , 0.69 ),
(42,    "Molybdenum",       "Mo", ( 0.32,  0.70,  0.70), 1.30, 1.30, 2.01 ,  1 , 0.93 ,  4 , 0.70 ,  6 , 0.62 ),
(43,    "Technetium",       "Tc", ( 0.23,  0.61,  0.61), 1.27, 1.27, 1.95 ,  7 , 0.97 ),
(44,     "Ruthenium",       "Ru", ( 0.14,  0.56,  0.56), 1.25, 1.25, 1.89 ,  4 , 0.67 ),
(45,       "Rhodium",       "Rh", ( 0.03,  0.49,  0.54), 1.25, 1.25, 1.83 ,  3 , 0.68 ),
(46,     "Palladium",       "Pd", (  0.0,  0.41,  0.52), 1.28, 1.28, 1.79 ,  2 , 0.80 ,  4 , 0.65 ),
(47,        "Silver",       "Ag", ( 0.75,  0.75,  0.75), 1.34, 1.34, 1.75 ,  1 , 1.26 ,  2 , 0.89 ),
(48,       "Cadmium",       "Cd", (  1.0,  0.85,  0.56), 1.48, 1.48, 1.71 ,  1 , 1.14 ,  2 , 0.97 ),
(49,        "Indium",       "In", ( 0.65,  0.45,  0.45), 1.44, 1.44, 2.00 ,  3 , 0.81 ),
(50,           "Tin",       "Sn", (  0.4,  0.50,  0.50), 1.41, 1.41, 1.72 , -4 , 2.94 , -1 , 3.70 ,  2 , 0.93 ,  4 , 0.71 ),
(51,      "Antimony",       "Sb", ( 0.61,  0.38,  0.70), 1.40, 1.40, 1.53 , -3 , 2.45 ,  3 , 0.76 ,  5 , 0.62 ),
(52,     "Tellurium",       "Te", ( 0.83,  0.47,   0.0), 1.36, 1.36, 1.42 , -2 , 2.11 , -1 , 2.50 ,  1 , 0.82 ,  4 , 0.70 ,  6 , 0.56 ),
(53,        "Iodine",        "I", ( 0.58,   0.0,  0.58), 1.33, 1.33, 1.32 , -1 , 2.20 ,  5 , 0.62 ,  7 , 0.50 ),
(54,         "Xenon",       "Xe", ( 0.25,  0.61,  0.69), 1.31, 1.31, 1.24 ),
(55,       "Caesium",       "Cs", ( 0.34,  0.09,  0.56), 2.35, 2.35, 3.35 ,  1 , 1.67 ),
(56,        "Barium",       "Ba", (  0.0,  0.78,   0.0), 1.98, 1.98, 2.78 ,  1 , 1.53 ,  2 , 1.34 ),
(57,     "Lanthanum",       "La", ( 0.43,  0.83,   1.0), 1.69, 1.69, 2.74 ,  1 , 1.39 ,  3 , 1.06 ),
(58,        "Cerium",       "Ce", (  1.0,   1.0,  0.78), 1.65, 1.65, 2.70 ,  1 , 1.27 ,  3 , 1.03 ,  4 , 0.92 ),
(59,  "Praseodymium",       "Pr", ( 0.85,   1.0,  0.78), 1.65, 1.65, 2.67 ,  3 , 1.01 ,  4 , 0.90 ),
(60,     "Neodymium",       "Nd", ( 0.78,   1.0,  0.78), 1.64, 1.64, 2.64 ,  3 , 0.99 ),
(61,    "Promethium",       "Pm", ( 0.63,   1.0,  0.78), 1.63, 1.63, 2.62 ,  3 , 0.97 ),
(62,      "Samarium",       "Sm", ( 0.56,   1.0,  0.78), 1.62, 1.62, 2.59 ,  3 , 0.96 ),
(63,      "Europium",       "Eu", ( 0.38,   1.0,  0.78), 1.85, 1.85, 2.56 ,  2 , 1.09 ,  3 , 0.95 ),
(64,    "Gadolinium",       "Gd", ( 0.27,   1.0,  0.78), 1.61, 1.61, 2.54 ,  3 , 0.93 ),
(65,       "Terbium",       "Tb", ( 0.18,   1.0,  0.78), 1.59, 1.59, 2.51 ,  3 , 0.92 ,  4 , 0.84 ),
(66,    "Dysprosium",       "Dy", ( 0.12,   1.0,  0.78), 1.59, 1.59, 2.49 ,  3 , 0.90 ),
(67,       "Holmium",       "Ho", (  0.0,   1.0,  0.61), 1.58, 1.58, 2.47 ,  3 , 0.89 ),
(68,        "Erbium",       "Er", (  0.0,  0.90,  0.45), 1.57, 1.57, 2.45 ,  3 , 0.88 ),
(69,       "Thulium",       "Tm", (  0.0,  0.83,  0.32), 1.56, 1.56, 2.42 ,  3 , 0.87 ),
(70,     "Ytterbium",       "Yb", (  0.0,  0.74,  0.21), 1.74, 1.74, 2.40 ,  2 , 0.93 ,  3 , 0.85 ),
(71,      "Lutetium",       "Lu", (  0.0,  0.67,  0.14), 1.56, 1.56, 2.25 ,  3 , 0.85 ),
(72,       "Hafnium",       "Hf", ( 0.30,  0.76,   1.0), 1.44, 1.44, 2.16 ,  4 , 0.78 ),
(73,      "Tantalum",       "Ta", ( 0.30,  0.65,   1.0), 1.34, 1.34, 2.09 ,  5 , 0.68 ),
(74,      "Tungsten",        "W", ( 0.12,  0.58,  0.83), 1.30, 1.30, 2.02 ,  4 , 0.70 ,  6 , 0.62 ),
(75,       "Rhenium",       "Re", ( 0.14,  0.49,  0.67), 1.28, 1.28, 1.97 ,  4 , 0.72 ,  7 , 0.56 ),
(76,        "Osmium",       "Os", ( 0.14,   0.4,  0.58), 1.26, 1.26, 1.92 ,  4 , 0.88 ,  6 , 0.69 ),
(77,       "Iridium",       "Ir", ( 0.09,  0.32,  0.52), 1.27, 1.27, 1.87 ,  4 , 0.68 ),
(78,     "Platinium",       "Pt", ( 0.81,  0.81,  0.87), 1.30, 1.30, 1.83 ,  2 , 0.80 ,  4 , 0.65 ),
(79,          "Gold",       "Au", (  1.0,  0.81,  0.13), 1.34, 1.34, 1.79 ,  1 , 1.37 ,  3 , 0.85 ),
(80,       "Mercury",       "Hg", ( 0.72,  0.72,  0.81), 1.49, 1.49, 1.76 ,  1 , 1.27 ,  2 , 1.10 ),
(81,      "Thallium",       "Tl", ( 0.65,  0.32,  0.30), 1.48, 1.48, 2.08 ,  1 , 1.47 ,  3 , 0.95 ),
(82,          "Lead",       "Pb", ( 0.34,  0.34,  0.38), 1.47, 1.47, 1.81 ,  2 , 1.20 ,  4 , 0.84 ),
(83,       "Bismuth",       "Bi", ( 0.61,  0.30,  0.70), 1.46, 1.46, 1.63 ,  1 , 0.98 ,  3 , 0.96 ,  5 , 0.74 ),
(84,      "Polonium",       "Po", ( 0.67,  0.36,   0.0), 1.46, 1.46, 1.53 ,  6 , 0.67 ),
(85,      "Astatine",       "At", ( 0.45,  0.30,  0.27), 1.45, 1.45, 1.43 , -3 , 2.22 ,  3 , 0.85 ,  5 , 0.46 ),
(86,         "Radon",       "Rn", ( 0.25,  0.50,  0.58), 1.00, 1.00, 1.34 ),
(87,      "Francium",       "Fr", ( 0.25,   0.0,   0.4), 1.00, 1.00, 1.00 ,  1 , 1.80 ),
(88,        "Radium",       "Ra", (  0.0,  0.49,   0.0), 1.00, 1.00, 1.00 ,  2 , 1.43 ),
(89,      "Actinium",       "Ac", ( 0.43,  0.67,  0.98), 1.00, 1.00, 1.00 ,  3 , 1.18 ),
(90,       "Thorium",       "Th", (  0.0,  0.72,   1.0), 1.65, 1.65, 1.00 ,  4 , 1.02 ),
(91,  "Protactinium",       "Pa", (  0.0,  0.63,   1.0), 1.00, 1.00, 1.00 ,  3 , 1.13 ,  4 , 0.98 ,  5 , 0.89 ),
(92,       "Uranium",        "U", (  0.0,  0.56,   1.0), 1.42, 1.42, 1.00 ,  4 , 0.97 ,  6 , 0.80 ),
(93,     "Neptunium",       "Np", (  0.0,  0.50,   1.0), 1.00, 1.00, 1.00 ,  3 , 1.10 ,  4 , 0.95 ,  7 , 0.71 ),
(94,     "Plutonium",       "Pu", (  0.0,  0.41,   1.0), 1.00, 1.00, 1.00 ,  3 , 1.08 ,  4 , 0.93 ),
(95,     "Americium",       "Am", ( 0.32,  0.36,  0.94), 1.00, 1.00, 1.00 ,  3 , 1.07 ,  4 , 0.92 ),
(96,        "Curium",       "Cm", ( 0.47,  0.36,  0.89), 1.00, 1.00, 1.00 ),
(97,     "Berkelium",       "Bk", ( 0.54,  0.30,  0.89), 1.00, 1.00, 1.00 ),
(98,   "Californium",       "Cf", ( 0.63,  0.21,  0.83), 1.00, 1.00, 1.00 ),
(99,   "Einsteinium",       "Es", ( 0.70,  0.12,  0.83), 1.00, 1.00, 1.00 ),
(100,       "Fermium",       "Fm", ( 0.70,  0.12,  0.72), 1.00, 1.00, 1.00 ),
(101,   "Mendelevium",       "Md", ( 0.70,  0.05,  0.65), 1.00, 1.00, 1.00 ),
(102,      "Nobelium",       "No", ( 0.74,  0.05,  0.52), 1.00, 1.00, 1.00 ),
(103,    "Lawrencium",       "Lr", ( 0.78,   0.0,   0.4), 1.00, 1.00, 1.00 ),
(104,       "Vacancy",      "Vac", (  0.5,   0.5,   0.5), 1.00, 1.00, 1.00),
(105,       "Default",  "Default", (  1.0,   1.0,   1.0), 1.00, 1.00, 1.00),
(106,         "Stick",    "Stick", (  0.5,   0.5,   0.5), 1.00, 1.00, 1.00),
)

# This list here contains all data of the elements and will be used during
# runtime. It is a list of classes.
# During executing Atomic Blender, the list will be initialized with the fixed
# data from above via the class structure below (CLASS_atom_pdb_Elements). We
# have then one fixed list (above), which will never be changed, and a list of
# classes with same data. The latter can be modified via loading a separate
# custom data file.
ATOM_PDB_ELEMENTS = []

# This is the class, which stores the properties for one element.
class CLASS_atom_pdb_Elements(object):
    __slots__ = ('number', 'name', 'short_name', 'color', 'radii', 'radii_ionic')
    def __init__(self, number, name, short_name, color, radii, radii_ionic):
        self.number = number
        self.name = name
        self.short_name = short_name
        self.color = color
        self.radii = radii
        self.radii_ionic = radii_ionic

# This is the class, which stores the properties of one atom.
class CLASS_atom_pdb_atom(object):  
    __slots__ = ('element', 'name', 'location', 'radius', 'color', 'material')
    def __init__(self, element, name, location, radius, color, material):
        self.element = element
        self.name = name
        self.location = location
        self.radius = radius
        self.color = color
        self.material = material

# This is the class, which stores the two atoms of one stick.
class CLASS_atom_pdb_stick(object):
    __slots__ = ('atom1', 'atom2')
    def __init__(self, atom1, atom2):
        self.atom1 = atom1
        self.atom2 = atom2


# -----------------------------------------------------------------------------
#                                                          Some small routines


# Routine which produces a cylinder. All is somewhat easy to undertsand.
def DEF_atom_pdb_build_stick(radius, length, sectors):

    vertices = []
    faces    = []

    dphi = 2.0 * pi/(float(sectors)-1)

    # Vertices
    vertices_top    = [Vector((0,0,length / 2.0))]
    vertices_bottom = [Vector((0,0,-length / 2.0))]
    for i in range(sectors-1):
        x = radius * cos( dphi * i )
        y = radius * sin( dphi * i )
        z =  length / 2.0
        vertex = Vector((x,y,z))
        vertices_top.append(vertex)
        z = -length / 2.0
        vertex = Vector((x,y,z))
        vertices_bottom.append(vertex)
    vertices = vertices_top + vertices_bottom

    # Top facets
    for i in range(sectors-1):
        if i == sectors-2:
            face_top = [0,sectors-1,1]
            face_bottom = [sectors,2*sectors-1,sectors+1]
        else:
            face_top    = [0]
            face_bottom = [sectors]
            for j in range(2):
                face_top.append(i+j+1)
                face_bottom.append(i+j+1+sectors)
        faces.append(face_top)
        faces.append(face_bottom)

    # Side facets
    for i in range(sectors-1):
        if i == sectors-2:
            faces.append(  [i+1, 1, 1+sectors, i+1+sectors] )
        else:
            faces.append(  [i+1, i+2, i+2+sectors, i+1+sectors] )

    # Build the mesh
    cylinder = bpy.data.meshes.new("Sticks_Cylinder")
    cylinder.from_pydata(vertices, [], faces)
    cylinder.update()
    new_cylinder = bpy.data.objects.new("Sticks_Cylinder", cylinder)
    bpy.context.scene.objects.link(new_cylinder)

    return new_cylinder


# This function measures the distance between two objects (atoms),
# which are active.
def DEF_atom_pdb_distance():

    if len(bpy.context.selected_bases) > 1:
        object_1 = bpy.context.selected_objects[0]
        object_2 = bpy.context.selected_objects[1]
    else:
        return "N.A."

    dv = object_2.location - object_1.location
    return str(dv.length)


# Routine to modify the radii via the type:
#                                          pre-defined, atomic or van der Waals
# Explanations here are also valid for the next 3 DEFs.
def DEF_atom_pdb_radius_type(rtype,how):

    if how == "ALL_IN_LAYER":

        # Note all layers that are active.
        layers = []
        for i in range(20):
            if bpy.context.scene.layers[i] == True:
                layers.append(i)

        # Put all objects, which are in the layers, into a list.
        change_objects = []
        for obj in bpy.context.scene.objects:
            for layer in layers:
                if obj.layers[layer] == True:
                    change_objects.append(obj)

        # Consider all objects, which are in the list 'change_objects'.
        for obj in change_objects:
            if len(obj.children) != 0:
                if obj.children[0].type == "SURFACE" or obj.children[0].type  == "MESH":
                    for element in ATOM_PDB_ELEMENTS:
                        if element.name in obj.name:
                            obj.children[0].scale = (element.radii[int(rtype)],) * 3
            else:
                if obj.type == "SURFACE" or obj.type == "MESH":
                    for element in ATOM_PDB_ELEMENTS:
                        if element.name in obj.name:
                            obj.scale = (element.radii[int(rtype)],) * 3

    if how == "ALL_ACTIVE":
        for obj in bpy.context.selected_objects:
            if len(obj.children) != 0:
                if obj.children[0].type == "SURFACE" or obj.children[0].type  == "MESH":
                    for element in ATOM_PDB_ELEMENTS:
                        if element.name in obj.name:
                            obj.children[0].scale = (element.radii[int(rtype)],) * 3
            else:
                if obj.type == "SURFACE" or obj.type == "MESH":
                    for element in ATOM_PDB_ELEMENTS:
                        if element.name in obj.name:
                            obj.scale = (element.radii[int(rtype)],) * 3


# Routine to modify the radii in picometer of a specific type of atom
def DEF_atom_pdb_radius_pm(atomname, radius_pm, how):

    if how == "ALL_IN_LAYER":

        layers = []
        for i in range(20):
            if bpy.context.scene.layers[i] == True:
                layers.append(i)

        change_objects = []
        for obj in bpy.context.scene.objects:
            for layer in layers:
                if obj.layers[layer] == True:
                    change_objects.append(obj)

        for obj in change_objects:
            if len(obj.children) != 0:
                if obj.children[0].type == "SURFACE" or obj.children[0].type  == "MESH":
                    if atomname in obj.name:
                        obj.children[0].scale = (radius_pm/100,) * 3
            else:
                if obj.type == "SURFACE" or obj.type == "MESH":
                    if atomname in obj.name:
                        obj.scale = (radius_pm/100,) * 3

    if how == "ALL_ACTIVE":
        for obj in bpy.context.selected_objects:
            if len(obj.children) != 0:
                if obj.children[0].type == "SURFACE" or obj.children[0].type  == "MESH":
                    if atomname in obj.name:
                        obj.children[0].scale = (radius_pm/100,) * 3
            else:
                if obj.type == "SURFACE" or obj.type == "MESH":
                    if atomname in obj.name:
                        obj.scale = (radius_pm/100,) * 3


# Routine to scale the radii of all atoms
def DEF_atom_pdb_radius_all(scale, how):

    if how == "ALL_IN_LAYER":

        layers = []
        for i in range(20):
            if bpy.context.scene.layers[i] == True:
                layers.append(i)

        change_objects = []
        for obj in bpy.context.scene.objects:
            for layer in layers:
                if obj.layers[layer] == True:
                    change_objects.append(obj)


        for obj in change_objects:
            if len(obj.children) != 0:
                if obj.children[0].type == "SURFACE" or obj.children[0].type  == "MESH":
                    if "Stick" not in obj.name:
                        obj.children[0].scale *= scale
            else:
                if obj.type == "SURFACE" or obj.type == "MESH":
                    if "Stick" not in obj.name:
                        obj.scale *= scale

    if how == "ALL_ACTIVE":
        for obj in bpy.context.selected_objects:
            if len(obj.children) != 0:
                if obj.children[0].type == "SURFACE" or obj.children[0].type  == "MESH":
                    if "Stick" not in obj.name:
                        obj.children[0].scale *= scale
            else:
                if obj.type == "SURFACE" or obj.type == "MESH":
                    if "Stick" not in obj.name:
                        obj.scale *= scale


# This reads a custom data file.
def DEF_atom_pdb_custom_datafile(path_datafile):

    if path_datafile == "":
        return False

    path_datafile = bpy.path.abspath(path_datafile)

    if os.path.isfile(path_datafile) == False:
        return False

    # The whole list gets deleted! We build it new.
    ATOM_PDB_ELEMENTS[:] = []

    # Read the data file, which contains all data
    # (atom name, radii, colors, etc.)
    data_file_p = io.open(path_datafile, "r")

    for line in data_file_p:

        if "Atom" in line:

            line = data_file_p.readline()

            # Number
            line = data_file_p.readline()
            number = line[19:-1]
            # Name
            line = data_file_p.readline()
            name = line[19:-1]
            # Short name
            line = data_file_p.readline()
            short_name = line[19:-1]
            # Color
            line = data_file_p.readline()
            color_value = line[19:-1].split(',')
            color = [float(color_value[0]),
                     float(color_value[1]),
                     float(color_value[2])]
            # Used radius
            line = data_file_p.readline()
            radius_used = float(line[19:-1])
            # Atomic radius
            line = data_file_p.readline()
            radius_atomic = float(line[19:-1])
            # Van der Waals radius
            line = data_file_p.readline()
            radius_vdW = float(line[19:-1])

            radii = [radius_used,radius_atomic,radius_vdW]
            radii_ionic = []

            element = CLASS_atom_pdb_Elements(number,name,short_name,color,
                                              radii, radii_ionic)

            ATOM_PDB_ELEMENTS.append(element)

    data_file_p.close()

    return True


# -----------------------------------------------------------------------------
#                                                            The main routine


def DEF_atom_pdb_main(use_mesh,Ball_azimuth,Ball_zenith,
               Ball_radius_factor,radiustype,Ball_distance_factor,
               use_stick,Stick_sectors,Stick_diameter,put_to_center,
               use_camera,use_lamp,path_datafile):

    # The list of all atoms as read from the PDB file.
    all_atoms  = []

    # The list of all sticks.
    all_sticks = []

    # List of materials
    atom_material_list = []

    # A list of ALL objects which are loaded (needed for selecting the loaded
    # structure.
    atom_object_list = []


    # ------------------------------------------------------------------------
    # INITIALIZE THE ELEMENT LIST

    ATOM_PDB_ELEMENTS[:] = []

    for item in ATOM_PDB_ELEMENTS_DEFAULT:

        # All three radii into a list
        radii = [item[4],item[5],item[6]]
        # The handling of the ionic radii will be done later. So far, it is an
        # empty list.
        radii_ionic = []

        li = CLASS_atom_pdb_Elements(item[0],item[1],item[2],item[3],
                                     radii,radii_ionic)
        ATOM_PDB_ELEMENTS.append(li)


    # ------------------------------------------------------------------------
    # READING DATA OF ATOMS


    if DEF_atom_pdb_custom_datafile(path_datafile):
        print("Custom data file is loaded.")

    # Open the file ...
    ATOM_PDB_FILEPATH_p = io.open(ATOM_PDB_FILEPATH, "r")

    #Go to the line, in which "ATOM" or "HETATM" appears.
    for line in ATOM_PDB_FILEPATH_p:
        split_list = line.split(' ')
        if "ATOM" in split_list[0]:
            break
        if "HETATM" in split_list[0]:
            break

    j = 0
    # This is in fact an endless 'while loop', ...
    while j > -1:

        # ... the loop is broken here (EOF) ...
        if line == "":
            break

        # If there is a "TER" we need to put empty entries into the lists
        # in order to not destroy the order of atom numbers and same numbers
        # used for sticks. "TER? What is that?" TER indicates the end of a
        # list of ATOM/HETATM records for a chain.
        if "TER" in line:
            short_name = "TER"
            name = "TER"
            radius = 0.0
            color = [0,0,0]
            location = Vector((0,0,0))
            # Append the TER into the list. Material remains empty so far.
            all_atoms.append(CLASS_atom_pdb_atom(short_name,
                                                 name,
                                                 location,
                                                 radius,
                                                 color,[]))
        # If 'ATOM or 'HETATM' appears in the line then do ...
        elif "ATOM" in line or "HETATM" in line:

            # What follows is due to deviations which appear from PDB to
            # PDB file. It is very special. PLEASE, DO NOT CHANGE! From here ...
            short_name = line[13:14]
            if short_name.isupper() == True:
                if line[14:15].islower() == True:
                    short_name = short_name + line[14:15]
            else:
                short_name = line[12:13]
                if short_name.isupper() == True:
                    if line[13:14].islower() == True:
                        short_name = short_name + line[13:14]
            # ... to here.

            # Go through all elements and find the element of the current atom.
            FLAG_FOUND = False
            for element in ATOM_PDB_ELEMENTS:
                if str.upper(short_name) == str.upper(element.short_name):
                    # Give the atom its proper names, color and radius:
                    short_name = str.upper(element.short_name)
                    name = element.name
                    # int(radiustype) => type of radius:
                    # pre-defined (0), atomic (1) or van der Waals (2)
                    radius = float(element.radii[int(radiustype)])
                    color = element.color
                    FLAG_FOUND = True
                    break

            # Is it a vacancy or an 'unknown atom' ?
            if FLAG_FOUND == False:
                # Give this atom also a name. If it is an 'X' then it is a
                # vacancy. Otherwise ...
                if "X" in short_name:
                    short_name = "VAC"
                    name = "Vacancy"
                    radius = float(ATOM_PDB_ELEMENTS[-3].radii[int(radiustype)])
                    color = ATOM_PDB_ELEMENTS[-3].color
                # ... take what is written in the PDB file. These are somewhat
                # unknown atoms. This should never happen, the element list is
                # almost complete. However, we do this due to security reasons.
                else:
                    short_name = str.upper(short_name)
                    name = str.upper(short_name)
                    radius = float(ATOM_PDB_ELEMENTS[-2].radii[int(radiustype)])
                    color = ATOM_PDB_ELEMENTS[-2].color

            # x,y and z are at fixed positions in the PDB file.
            x = float(line[30:38].rsplit()[0])
            y = float(line[38:46].rsplit()[0])
            z = float(line[46:55].rsplit()[0])

            location = Vector((x,y,z))

            j += 1

            # Append the atom to the list. Material remains empty so far.
            all_atoms.append(CLASS_atom_pdb_atom(short_name,
                                             name,
                                             location,
                                             radius,
                                             color,[]))

        line = ATOM_PDB_FILEPATH_p.readline()
        line = line[:-1]

    ATOM_PDB_FILEPATH_p.close()
    # From above it can be clearly seen that j is now the number of all atoms.
    Number_of_total_atoms = j


    # ------------------------------------------------------------------------
    # MATERIAL PROPERTIES FOR ATOMS


    # The list that contains info about all types of atoms is created
    # here. It is used for building the material properties for
    # instance (see below).
    atom_all_types_list = []

    for atom in all_atoms:
        FLAG_FOUND = False
        for atom_type in atom_all_types_list:
            # If the atom name is already in the list, FLAG on 'True'.
            if atom_type[0] == atom.name:
                FLAG_FOUND = True
                break
        # No name in the current list has been found? => New entry.
        if FLAG_FOUND == False:
            # Stored are: Atom label (e.g. 'Na'), the corresponding atom
            # name (e.g. 'Sodium') and its color.
            atom_all_types_list.append([atom.name, atom.element, atom.color])

    # The list of materials is built.
    # Note that all atoms of one type (e.g. all hydrogens) get only ONE
    # material! This is good because then, by activating one atom in the
    # Blender scene and changing the color of this atom, one changes the color
    # of ALL atoms of the same type at the same time.

    # Create first a new list of materials for each type of atom
    # (e.g. hydrogen)
    for atom_type in atom_all_types_list:
        material = bpy.data.materials.new(atom_type[1])
        material.name = atom_type[0]
        material.diffuse_color = atom_type[2]
        atom_material_list.append(material)

    # Now, we go through all atoms and give them a material. For all atoms ...
    for atom in all_atoms:
        # ... and all materials ...
        for material in atom_material_list:
            # ... select the correct material for the current atom via
            # comparison of names ...
            if atom.name in material.name:
                # ... and give the atom its material properties.
                # However, before we check, if it is a vacancy, because then it
                # gets some additional preparation. The vacancy is represented
                # by a transparent cube.
                if atom.name == "Vacancy":
                    material.transparency_method = 'Z_TRANSPARENCY'
                    material.alpha = 1.3
                    material.raytrace_transparency.fresnel = 1.6
                    material.raytrace_transparency.fresnel_factor = 1.6
                    material.use_transparency = True
                # The atom gets its properties.
                atom.material = material


    # ------------------------------------------------------------------------
    # READING DATA OF STICKS


    # Open the PDB file again such that the file pointer is in the first
    # line ... . Stupid, I know ... ;-)
    ATOM_PDB_FILEPATH_p = io.open(ATOM_PDB_FILEPATH, "r")

    split_list = line.split(' ')

    # Go to the first entry
    if "CONECT" not in split_list[0]:
        for line in ATOM_PDB_FILEPATH_p:
            split_list = line.split(' ')
            if "CONECT" in split_list[0]:
                break

    Number_of_sticks = 0
    sticks_double = 0
    j = 0
    # This is in fact an endless while loop, ...
    while j > -1:

        # ... which is broken here (EOF) ...
        if line == "":
            break
        # ... or here, when no 'CONECT' appears anymore.
        if "CONECT" not in line:
            break

        # The strings of the atom numbers do have a clear position in the file
        # (From 7 to 12, from 13 to 18 and so on.) and one needs to consider
        # this. One could also use the split function but then one gets into
        # trouble if there are many atoms: For instance, it may happen that one
        # has
        #                   CONECT 11111  22244444
        #
        # In Fact it means that atom No. 11111 has a connection with atom
        # No. 222 but also with atom No. 44444. The split function would give
        # me only two numbers (11111 and 22244444), which is wrong.

        # Cut spaces from the right and 'CONECT' at the beginning
        line = line.rstrip()
        line = line[6:]
        # Amount of loops
        length = len(line)
        loops  = int(length/5)

        # List of atoms
        atom_list = []
        for i in range(loops):
            number = line[5*i:5*(i+1)].rsplit()
            if number != []:
                if number[0].isdigit() == True:
                    atom_number = int(number[0])
                    atom_list.append(atom_number)

        # The first atom is connected with all the others in the list.
        atom1 = atom_list[0]

        # For all the other atoms in the list do:
        for each_atom in atom_list[1:]:

            # The second, third, ... partner atom
            atom2 = each_atom

            # Note that in a PDB file, sticks of one atom pair can appear a
            # couple of times. (Only god knows why ...)
            # So, does a stick between the considered atoms already exist?
            FLAG_BAR = False
            for k in range(Number_of_sticks):
                if ((all_sticks[k].atom1 == atom1 and all_sticks[k].atom2 == atom2) or
                    (all_sticks[k].atom2 == atom1 and all_sticks[k].atom1 == atom2)):
                    sticks_double += 1
                    # If yes, then FLAG on 'True'.
                    FLAG_BAR       = True
                    break

            # If the stick is not yet registered (FLAG_BAR == False), then
            # register it!
            if FLAG_BAR == False:
                all_sticks.append(CLASS_atom_pdb_stick(atom1,atom2))
                Number_of_sticks += 1
                j += 1

        line = ATOM_PDB_FILEPATH_p.readline()
        line = line.rstrip()

    ATOM_PDB_FILEPATH_p.close()
    # So far, all atoms and sticks have been registered.


    # ------------------------------------------------------------------------
    # TRANSLATION OF THE STRUCTURE TO THE ORIGIN


    # It may happen that the structure in a PDB file already has an offset
    # If chosen, the structure is first put into the center of the scene
    # (the offset is substracted).

    if put_to_center == True:

        sum_vec = Vector((0.0,0.0,0.0))

        # Sum of all atom coordinates
        sum_vec = sum([atom.location for atom in all_atoms], sum_vec)

        # Then the average is taken
        sum_vec = sum_vec / Number_of_total_atoms

        # After, for each atom the center of gravity is substracted
        for atom in all_atoms:
            atom.location -= sum_vec


    # ------------------------------------------------------------------------
    # SCALING


    # Take all atoms and adjust their radii and scale the distances.
    for atom in all_atoms:
        atom.location *= Ball_distance_factor


    # ------------------------------------------------------------------------
    # DETERMINATION OF SOME GEOMETRIC PROPERTIES


    # In the following, some geometric properties of the whole object are
    # determined: center, size, etc.
    sum_vec = Vector((0.0,0.0,0.0))

    # First the center is determined. All coordinates are summed up ...
    sum_vec = sum([atom.location for atom in all_atoms], sum_vec)

    # ... and the average is taken. This gives the center of the object.
    object_center_vec = sum_vec / Number_of_total_atoms

    # Now, we determine the size.The farest atom from the object center is
    # taken as a measure. The size is used to place well the camera and light
    # into the scene.
    object_size_vec = [atom.location - object_center_vec for atom in all_atoms]
    object_size = 0.0
    object_size = max(object_size_vec).length


    # ------------------------------------------------------------------------
    # CAMERA AND LAMP

    camera_factor = 15.0

    # If chosen a camera is put into the scene.
    if use_camera == True:

        # Assume that the object is put into the global origin. Then, the
        # camera is moved in x and z direction, not in y. The object has its
        # size at distance math.sqrt(object_size) from the origin. So, move the
        # camera by this distance times a factor of camera_factor in x and z.
        # Then add x, y and z of the origin of the object.
        object_camera_vec = Vector((math.sqrt(object_size) * camera_factor,
                                    0.0,
                                    math.sqrt(object_size) * camera_factor))
        camera_xyz_vec = object_center_vec + object_camera_vec

        # Create the camera
        current_layers=bpy.context.scene.layers
        bpy.ops.object.camera_add(view_align=False, enter_editmode=False,
                               location=camera_xyz_vec,
                               rotation=(0.0, 0.0, 0.0), layers=current_layers)
        # Some properties of the camera are changed.
        camera = bpy.context.scene.objects.active
        camera.name = "A_camera"
        camera.data.name = "A_camera"
        camera.data.lens = 45
        camera.data.clip_end = 500.0

        # Here the camera is rotated such it looks towards the center of
        # the object. The [0.0, 0.0, 1.0] vector along the z axis
        z_axis_vec             = Vector((0.0, 0.0, 1.0))
        # The angle between the last two vectors
        angle                  = object_camera_vec.angle(z_axis_vec, 0)
        # The cross-product of z_axis_vec and object_camera_vec
        axis_vec               = z_axis_vec.cross(object_camera_vec)
        # Rotate 'axis_vec' by 'angle' and convert this to euler parameters.
        # 4 is the size of the matrix.
        euler                  = Matrix.Rotation(angle, 4, axis_vec).to_euler()
        camera.rotation_euler  = euler

        # Rotate the camera around its axis by 90° such that we have a nice
        # camera position and view onto the object.
        bpy.ops.transform.rotate(value=(90.0*2*math.pi/360.0,),
                                 axis=object_camera_vec,
                                 constraint_axis=(False, False, False),
                                 constraint_orientation='GLOBAL',
                                 mirror=False, proportional='DISABLED',
                                 proportional_edit_falloff='SMOOTH',
                                 proportional_size=1, snap=False,
                                 snap_target='CLOSEST', snap_point=(0, 0, 0),
                                 snap_align=False, snap_normal=(0, 0, 0),
                                 release_confirm=False)


        # This does not work, I don't know why.
        #
        #for area in bpy.context.screen.areas:
        #    if area.type == 'VIEW_3D':
        #        area.spaces[0].region_3d.view_perspective = 'CAMERA'


    # Here a lamp is put into the scene, if chosen.
    if use_lamp == True:

        # This is the distance from the object measured in terms of %
        # of the camera distance. It is set onto 50% (1/2) distance.
        lamp_dl = math.sqrt(object_size) * 15 * 0.5
        # This is a factor to which extend the lamp shall go to the right
        # (from the camera  point of view).
        lamp_dy_right = lamp_dl * (3.0/4.0)

        # Create x, y and z for the lamp.
        object_lamp_vec = Vector((lamp_dl,lamp_dy_right,lamp_dl))
        lamp_xyz_vec = object_center_vec + object_lamp_vec

        # Create the lamp
        current_layers=bpy.context.scene.layers
        bpy.ops.object.lamp_add (type = 'POINT', view_align=False,
                                 location=lamp_xyz_vec,
                                 rotation=(0.0, 0.0, 0.0),
                                 layers=current_layers)
        # Some properties of the lamp are changed.
        lamp = bpy.context.scene.objects.active
        lamp.data.name = "A_lamp"
        lamp.name = "A_lamp"
        lamp.data.distance = 500.0
        lamp.data.energy = 3.0
        lamp.data.shadow_method = 'RAY_SHADOW'

        bpy.context.scene.world.light_settings.use_ambient_occlusion = True
        bpy.context.scene.world.light_settings.ao_factor = 0.2


    # ------------------------------------------------------------------------
    # SOME OUTPUT ON THE CONSOLE


    print()
    print()
    print()
    print(ATOM_PDB_STRING)
    print()
    print("Total number of atoms   : " + str(Number_of_total_atoms))
    print("Total number of sticks  : " + str(Number_of_sticks))
    print("Center of object        : ", object_center_vec)
    print("Size of object          : ", object_size)
    print()


    # ------------------------------------------------------------------------
    # SORTING THE ATOMS


    # Lists of atoms of one type are created. Example:
    # draw_all_atoms = [ data_hydrogen,data_carbon,data_nitrogen ]
    # data_hydrogen = [["Hydrogen", Material_Hydrogen, Vector((x,y,z)), 109], ...]

    draw_all_atoms = []

    # Go through the list which contains all types of atoms. It is the list,
    # which has been created on the top during reading the PDB file.
    # Example: atom_all_types_list = ["hydrogen", "carbon", ...]
    for atom_type in atom_all_types_list:

        # Don't draw 'TER atoms'.
        if atom_type[0] == "TER":
            continue

        # This is the draw list, which contains all atoms of one type (e.g.
        # all hydrogens) ...
        draw_all_atoms_type = []

        # Go through all atoms ...
        for atom in all_atoms:
            # ... select the atoms of the considered type via comparison ...
            if atom.name == atom_type[0]:
                # ... and append them to the list 'draw_all_atoms_type'.
                draw_all_atoms_type.append([atom.name,
                                           atom.material,
                                           atom.location,
                                           atom.radius])

        # Now append the atom list to the list of all types of atoms
        draw_all_atoms.append(draw_all_atoms_type)


    # ------------------------------------------------------------------------
    # DRAWING THE ATOMS


    # This is the number of all atoms which are put into the scene.
    bpy.ops.object.select_all(action='DESELECT')

    # For each list of atoms of ONE type (e.g. Hydrogen)
    for draw_all_atoms_type in draw_all_atoms:

        # Create first the vertices composed of the coordinates of all
        # atoms of one type
        atom_vertices = []
        for atom in draw_all_atoms_type:
            # In fact, the object is created in the World's origin.
            # This is why 'object_center_vec' is substracted. At the end
            # the whole object is translated back to 'object_center_vec'.
            atom_vertices.append( atom[2] - object_center_vec )

        # Build the mesh
        atom_mesh = bpy.data.meshes.new("Mesh_"+atom[0])
        atom_mesh.from_pydata(atom_vertices, [], [])
        atom_mesh.update()
        new_atom_mesh = bpy.data.objects.new(atom[0], atom_mesh)
        bpy.context.scene.objects.link(new_atom_mesh)

        # Now, build a representative sphere (atom)
        current_layers=bpy.context.scene.layers

        if atom[0] == "Vacancy":
            bpy.ops.mesh.primitive_cube_add(
                            view_align=False, enter_editmode=False,
                            location=(0.0, 0.0, 0.0),
                            rotation=(0.0, 0.0, 0.0),
                            layers=current_layers)
        else:
            # NURBS balls
            if use_mesh == False:
                bpy.ops.surface.primitive_nurbs_surface_sphere_add(
                            view_align=False, enter_editmode=False,
                            location=(0,0,0), rotation=(0.0, 0.0, 0.0),
                            layers=current_layers)
            # UV balls
            else:
                bpy.ops.mesh.primitive_uv_sphere_add(
                            segments=Ball_azimuth, ring_count=Ball_zenith,
                            size=1, view_align=False, enter_editmode=False,
                            location=(0,0,0), rotation=(0, 0, 0),
                            layers=current_layers)

        ball = bpy.context.scene.objects.active
        ball.scale  = (atom[3]*Ball_radius_factor,) * 3

        if atom[0] == "Vacancy":
            ball.name = "Cube_"+atom[0]
        else:
            ball.name = "Ball (NURBS)_"+atom[0]
        ball.active_material = atom[1]
        ball.parent = new_atom_mesh
        new_atom_mesh.dupli_type = 'VERTS'
        # The object is back translated to 'object_center_vec'.
        new_atom_mesh.location = object_center_vec
        atom_object_list.append(new_atom_mesh)

    print()


    # ------------------------------------------------------------------------
    # DRAWING THE STICKS


    if use_stick == True and all_sticks != []:

        # Create a new material with the corresponding color. The
        # color is taken from the all_atom list, it is the last entry
        # in the data file (index -1).
        bpy.ops.object.material_slot_add()
        stick_material = bpy.data.materials.new(ATOM_PDB_ELEMENTS[-1].name)
        stick_material.diffuse_color = ATOM_PDB_ELEMENTS[-1].color

        vertices = []
        faces    = []
        dl = 0.2

        i = 0
        # For all sticks, do ...
        for stick in all_sticks:

            # What follows is school mathematics! :-)
            v1 = all_atoms[stick.atom2-1].location
            v2 = all_atoms[stick.atom1-1].location

            dv = (v1 - v2)

            n  = dv / dv.length
            # m  = v1 - dv / 2.0  # UNUSED

            gamma = -n * v1
            b     = v1 + gamma * n
            n_b   = b / b.length

            loops = int(dv.length / dl)

            for j in range(loops):

                g = v1 - n * dl / 2.0 - n * dl * j

                p1 = g + n_b * Stick_diameter
                p2 = g - n_b * Stick_diameter
                p3 = g - n_b.cross(n) * Stick_diameter
                p4 = g + n_b.cross(n) * Stick_diameter

                vertices.append(p1)
                vertices.append(p2)
                vertices.append(p3)
                vertices.append(p4)
                faces.append((i*4+0,i*4+2,i*4+1,i*4+3))
                i += 1

        mesh = bpy.data.meshes.new("Sticks")
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        new_mesh = bpy.data.objects.new("Sticks", mesh)
        bpy.context.scene.objects.link(new_mesh)

        current_layers = bpy.context.scene.layers
        stick_cylinder = DEF_atom_pdb_build_stick(Stick_diameter, dl, Stick_sectors)


        stick_cylinder.active_material = stick_material
        stick_cylinder.parent = new_mesh
        new_mesh.dupli_type = 'FACES'
        atom_object_list.append(new_mesh)


    # ------------------------------------------------------------------------
    # SELECT ALL LOADED OBJECTS
    bpy.ops.object.select_all(action='DESELECT')
    obj = None
    for obj in atom_object_list:
        obj.select = True

    # activate the last selected object (perhaps another should be active?)
    if obj:
        bpy.context.scene.objects.active = obj

    print("\n\nAll atoms (%d) and sticks (%d) have been drawn - finished.\n\n"
           % (Number_of_total_atoms,Number_of_sticks))


    return Number_of_total_atoms
