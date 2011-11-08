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

# <pep8 compliant>

# TODO, currently imported names are assumed to make valid blender names
#       this is _not_ assured, so we should use a reliable dict mapping.

import bpy


class Element:
    """Element class with properties ([R, G, B], cov_radius, vdw_radius, name)"""
    def __init__(self, color, cov_radius, vdw_radius, name):
        self.color = color
        self.cov_radius = cov_radius
        self.vdw_radius = vdw_radius
        self.name = name


class Atom:
    """Atom class with properties (serial, name, altloc, resname,chainid,
        resseq, icode, x, y, z, occupancy, tempfactor, element, charge)"""

    def __init__(self, serial, name, altloc, resname, chainid, resseq, icode,
                 x, y, z, occupancy, tempfactor, element, charge):
        self.serial = serial
        self.name = name
        self.altloc = altloc
        self.resname = resname
        self.chainid = chainid
        self.resseq = resseq
        self.icode = icode
        self.x = x
        self.y = y
        self.z = z
        self.occupancy = occupancy
        self.tempfactor = tempfactor
        self.element = element
        self.charge = charge


# collection of biomolecules based on model
# all chains in model stored here
class Model:
    '''Model class'''
    def __init__(self, model_id):
        self.model_id = model_id
        self.atoms = {}
        self.atom_count = 0
        self.vert_list = []
        # Dictionary of {vert index: [list of vertex groups it belongs to]}
        # Now element only
        self.vert_group_index = {}
        # Dictionary of {vertex group: number of group members}
        self.vert_group_counts = {}
        self.chains = {}


# new object level class
class Biomolecule:
    '''Biomolecule'''
    def __init__(self, serial):
        self.serial = serial
        self.atom_count = 0
        self.vert_list = []
        self.vert_group_index = {}
        self.vert_group_counts = {}
        self.chain_transforms = {}


# Atom collection
class Chain:
    '''Chain'''
    def __init__(self, chain_id):
        self.chain_id = chain_id
        self.atoms = {}

# Atomic data from http://www.ccdc.cam.ac.uk/products/csd/radii/
# Color palatte adapted from Jmol
# "Element symbol":[[Red, Green, Blue], Covalent radius, van der Waals radius,
#                   Element name]
# Atomic radii are in angstroms (100 pm)
# Unknown covalent radii are assigned 1.5 A, unknown van der Waals radiii are
# assigned 2 A,

atom_data = {
    "H" : Element((1.00000, 1.00000, 1.00000), 0.23, 1.09, "Hydrogen"     ),
    "HE": Element((0.85098, 1.00000, 1.00000), 1.5 , 1.4 , "Helium"       ),
    "LI": Element((0.80000, 0.50196, 1.00000), 1.28, 1.82, "Lithium"      ),
    "BE": Element((0.76078, 1.00000, 0.00000), 0.96, 2   , "Beryllium"    ),
    "B" : Element((1.00000, 0.70980, 0.70980), 0.83, 2   , "Boron"        ),
    "C" : Element((0.56471, 0.56471, 0.56471), 0.68, 1.7 , "Carbon"       ),
    "N" : Element((0.18824, 0.31373, 0.97255), 0.68, 1.55, "Nitrogen"     ),
    "O" : Element((1.00000, 0.05098, 0.05098), 0.68, 1.52, "Oxygen"       ),
    "F" : Element((0.56471, 0.87843, 0.31373), 0.64, 1.47, "Fluorine"     ),
    "NE": Element((0.70196, 0.89020, 0.96078), 1.5 , 1.54, "Neon"         ),
    "NA": Element((0.67059, 0.36078, 0.94902), 1.66, 2.27, "Sodium"       ),
    "MG": Element((0.54118, 1.00000, 0.00000), 1.41, 1.73, "Magnesium"    ),
    "AL": Element((0.74902, 0.65098, 0.65098), 1.21, 2   , "Aluminum"     ),
    "SI": Element((0.94118, 0.78431, 0.62745), 1.2 , 2.1 , "Silicon"      ),
    "P" : Element((1.00000, 0.50196, 0.00000), 1.05, 1.8 , "Phosphorus"   ),
    "S" : Element((1.00000, 1.00000, 0.18824), 1.02, 1.8 , "Sulfur"       ),
    "CL": Element((0.12157, 0.94118, 0.12157), 0.99, 1.75, "Chlorine"     ),
    "AR": Element((0.50196, 0.81961, 0.89020), 1.51, 1.88, "Argon"        ),
    "K" : Element((0.56078, 0.25098, 0.83137), 2.03, 2.75, "Potassium"    ),
    "CA": Element((0.23922, 1.00000, 0.00000), 1.76, 2   , "Calcium"      ),
    "SC": Element((0.90196, 0.90196, 0.90196), 1.7 , 2   , "Scandium"     ),
    "TI": Element((0.74902, 0.76078, 0.78039), 1.6 , 2   , "Titanium"     ),
    "V" : Element((0.65098, 0.65098, 0.67059), 1.53, 2   , "Vanadium"     ),
    "CR": Element((0.54118, 0.60000, 0.78039), 1.39, 2   , "Chromium"     ),
    "MN": Element((0.61176, 0.47843, 0.78039), 1.61, 2   , "Manganese"    ),
    "FE": Element((0.87843, 0.40000, 0.20000), 1.52, 2   , "Iron"         ),
    "CO": Element((0.94118, 0.56471, 0.62745), 1.26, 2   , "Cobalt"       ),
    "NI": Element((0.31373, 0.81569, 0.31373), 1.24, 1.63, "Nickel"       ),
    "CU": Element((0.78431, 0.50196, 0.20000), 1.32, 1.4 , "Copper"       ),
    "ZN": Element((0.49020, 0.50196, 0.69020), 1.22, 1.39, "Zinc"         ),
    "GA": Element((0.76078, 0.56078, 0.56078), 1.22, 1.87, "Gallium"      ),
    "GE": Element((0.40000, 0.56078, 0.56078), 1.17, 2   , "Germanium"    ),
    "AS": Element((0.74118, 0.50196, 0.89020), 1.21, 1.85, "Arsenic"      ),
    "SE": Element((1.00000, 0.63137, 0.00000), 1.22, 1.9 , "Selenium"     ),
    "BR": Element((0.65098, 0.16078, 0.16078), 1.21, 1.85, "Bromine"      ),
    "KR": Element((0.36078, 0.72157, 0.81961), 1.5 , 2.02, "Krypton"      ),
    "RB": Element((0.43922, 0.18039, 0.69020), 2.2 , 2   , "Rubidium"     ),
    "SR": Element((0.00000, 1.00000, 0.00000), 1.95, 2   , "Strontium"    ),
    "Y" : Element((0.58039, 1.00000, 1.00000), 1.9 , 2   , "Yttrium"      ),
    "ZR": Element((0.58039, 0.87843, 0.87843), 1.75, 2   , "Zirconium"    ),
    "NB": Element((0.45098, 0.76078, 0.78824), 1.64, 2   , "Niobium"      ),
    "MO": Element((0.32941, 0.70980, 0.70980), 1.54, 2   , "Molybdenum"   ),
    "TC": Element((0.23137, 0.61961, 0.61961), 1.47, 2   , "Technetium"   ),
    "RU": Element((0.14118, 0.56078, 0.56078), 1.46, 2   , "Ruthenium"    ),
    "RH": Element((0.03922, 0.49020, 0.54902), 1.45, 2   , "Rhodium"      ),
    "PD": Element((0.00000, 0.41176, 0.52157), 1.39, 1.63, "Palladium"    ),
    "AG": Element((0.75294, 0.75294, 0.75294), 1.45, 1.72, "Silver"       ),
    "CD": Element((1.00000, 0.85098, 0.56078), 1.44, 1.58, "Cadmium"      ),
    "IN": Element((0.65098, 0.45882, 0.45098), 1.42, 1.93, "Indium"       ),
    "SN": Element((0.40000, 0.50196, 0.50196), 1.39, 2.17, "Tin"          ),
    "SB": Element((0.61961, 0.38824, 0.70980), 1.39, 2   , "Antimony"     ),
    "TE": Element((0.83137, 0.47843, 0.00000), 1.47, 2.06, "Tellurium"    ),
    "I" : Element((0.58039, 0.00000, 0.58039), 1.4 , 1.98, "Iodine"       ),
    "XE": Element((0.25882, 0.61961, 0.69020), 1.5 , 2.16, "Xenon"        ),
    "CS": Element((0.34118, 0.09020, 0.56078), 2.44, 2   , "Cesium"       ),
    "BA": Element((0.00000, 0.78824, 0.00000), 2.15, 2   , "Barium"       ),
    "LA": Element((0.43922, 0.83137, 1.00000), 2.07, 2   , "Lanthanum"    ),
    "CE": Element((1.00000, 1.00000, 0.78039), 2.04, 2   , "Cerium"       ),
    "PR": Element((0.85098, 1.00000, 0.78039), 2.03, 2   , "Praseodymium" ),
    "ND": Element((0.78039, 1.00000, 0.78039), 2.01, 2   , "Neodymium"    ),
    "PM": Element((0.63922, 1.00000, 0.78039), 1.99, 2   , "Promethium"   ),
    "SM": Element((0.56078, 1.00000, 0.78039), 1.98, 2   , "Samarium"     ),
    "EE": Element((0.38039, 1.00000, 0.78039), 1.98, 2   , "Europium"     ),
    "GD": Element((0.27059, 1.00000, 0.78039), 1.96, 2   , "Gadolinium"   ),
    "TB": Element((0.18824, 1.00000, 0.78039), 1.94, 2   , "Terbium"      ),
    "DY": Element((0.12157, 1.00000, 0.78039), 1.92, 2   , "Dysprosium"   ),
    "HO": Element((0.00000, 1.00000, 0.61176), 1.92, 2   , "Holmium"      ),
    "ER": Element((0.00000, 0.90196, 0.45882), 1.89, 2   , "Erbium"       ),
    "TM": Element((0.00000, 0.83137, 0.32157), 1.9 , 2   , "Thulium"      ),
    "YB": Element((0.00000, 0.74902, 0.21961), 1.87, 2   , "Ytterbium"    ),
    "LU": Element((0.00000, 0.67059, 0.14118), 1.87, 2   , "Lutetium"     ),
    "HF": Element((0.30196, 0.76078, 1.00000), 1.75, 2   , "Hafnium"      ),
    "TA": Element((0.30196, 0.65098, 1.00000), 1.7 , 2   , "Tantalum"     ),
    "W" : Element((0.12941, 0.58039, 0.83922), 1.62, 2   , "Tungsten"     ),
    "RE": Element((0.14902, 0.49020, 0.67059), 1.51, 2   , "Rhenium"      ),
    "OS": Element((0.14902, 0.40000, 0.58824), 1.44, 2   , "Osmium"       ),
    "IR": Element((0.09020, 0.32941, 0.52941), 1.41, 2   , "Iridium"      ),
    "PT": Element((0.81569, 0.81569, 0.87843), 1.36, 1.72, "Platinum"     ),
    "AU": Element((1.00000, 0.81961, 0.13725), 1.5 , 1.66, "Gold"         ),
    "HG": Element((0.72157, 0.72157, 0.81569), 1.32, 1.55, "Mercury"      ),
    "TL": Element((0.65098, 0.32941, 0.30196), 1.45, 1.96, "Thallium"     ),
    "PB": Element((0.34118, 0.34902, 0.38039), 1.46, 2.02, "Lead"         ),
    "BI": Element((0.61961, 0.30980, 0.70980), 1.48, 2   , "Bismuth"      ),
    "PO": Element((0.67059, 0.36078, 0.00000), 1.4 , 2   , "Polonium"     ),
    "AT": Element((0.45882, 0.30980, 0.27059), 1.21, 2   , "Astatine"     ),
    "RN": Element((0.25882, 0.50980, 0.58824), 1.5 , 2   , "Radon"        ),
    "FR": Element((0.25882, 0.00000, 0.40000), 2.6 , 2   , "Francium"     ),
    "RA": Element((0.00000, 0.49020, 0.00000), 2.21, 2   , "Radium"       ),
    "AC": Element((0.43922, 0.67059, 0.98039), 2.15, 2   , "Actinium"     ),
    "TH": Element((0.00000, 0.72941, 1.00000), 2.06, 2   , "Thorium"      ),
    "PA": Element((0.00000, 0.63137, 1.00000), 2   , 2   , "Protactinium" ),
    "U" : Element((0.00000, 0.56078, 1.00000), 1.96, 1.86, "Uranium"      ),
    "NP": Element((0.00000, 0.50196, 1.00000), 1.9 , 2   , "Neptunium"    ),
    "PU": Element((0.00000, 0.41961, 1.00000), 1.87, 2   , "Plutonium"    ),
    "AM": Element((0.32941, 0.36078, 0.94902), 1.8 , 2   , "Americium"    ),
    "CM": Element((0.47059, 0.36078, 0.89020), 1.69, 2   , "Curium"       ),
    "BK": Element((0.54118, 0.30980, 0.89020), 1.54, 2   , "Berkelium"    ),
    "CF": Element((0.63137, 0.21176, 0.83137), 1.83, 2   , "Californium"  ),
    "ES": Element((0.70196, 0.12157, 0.83137), 1.5 , 2   , "Einsteinium"  ),
    "FM": Element((0.70196, 0.12157, 0.72941), 1.5 , 2   , "Fermium"      ),
    "MD": Element((0.70196, 0.05098, 0.65098), 1.5 , 2   , "Mendelevium"  ),
    "NO": Element((0.74118, 0.05098, 0.52941), 1.5 , 2   , "Nobelium"     ),
    "LR": Element((0.78039, 0.00000, 0.40000), 1.5 , 2   , "Lawrencium"   ),
    "RF": Element((0.80000, 0.00000, 0.34902), 1.5 , 2   , "Rutherfordium"),
    "DB": Element((0.81961, 0.00000, 0.30980), 1.5 , 2   , "Dubnium"      ),
    "SG": Element((0.85098, 0.00000, 0.27059), 1.5 , 2   , "Seaborgium"   ),
    "BH": Element((0.87843, 0.00000, 0.21961), 1.5 , 2   , "Bohrium"      ),
    "HS": Element((0.90196, 0.00000, 0.18039), 1.5 , 2   , "Hassium"      ),
    "MT": Element((0.92157, 0.00000, 0.14902), 1.5 , 2   , "Meitnerium"   ),
    "DS": Element((0.93725, 0.00000, 0.12157), 1.5 , 2   , "Darmstadtium" )
}


def load_pdb(context,
             filepath="",
             atom_size=1.0,
             scene_scale=1.0,
             atom_subdivisions=3,
             retain_alts=False,
             multi_models=False,
             multimers=False,
             ):

    scene = context.scene

    file = open(filepath, 'r')

    model_list = {}
    model_flag = False
    biomolecule_flag = False
    biomolecule_list = {}
    chain_list = []
    mat_list = []

    # -------------------------------------------------------------------------
    # Parse data

    for line in file:
        # print(line)
        if line[:6] == 'COMPND':
            if line[11:17] == 'CHAIN:':
                s = 17
                for i in range(1, (len(line[17:]) + 1)):
                    if line[16 + i:17 + i] == ',':
                        chain_id = line[s:16 + i].strip()
                        chain_list.append(chain_id)
                        s = 17 + i
                    elif line[16 + i:17 + i] == ';':
                        chain_id = line[s:16 + i].strip()
                        chain_list.append(chain_id)
                        break
                    elif i == len(line[17:]):
                        chain_id = line[s:].strip()
                        chain_list.append(chain_id)
        elif line[:10] == 'REMARK 300':
            if line[11:23] == 'BIOMOLECULE:':
                biomolecule_flag = True
                s = 23
                for i in range(1, (len(line[23:]) + 1)):
                    if line[22 + i:23 + i] == ',':
                        bm_serial = int(line[s:22 + i])
                        biomolecule_list[bm_serial] = Biomolecule(bm_serial)
                        s = 23 + i
                    elif i == len(line[23:]):
                        bm_serial = int(line[s:])
                        biomolecule_list[bm_serial] = Biomolecule(bm_serial)

        elif line[:10] == 'REMARK 350':
            if line[11:23] == 'BIOMOLECULE:':
                cur_biomolecule = biomolecule_list[int(line[23:].strip())]
            elif line[11:41] == 'APPLY THE FOLLOWING TO CHAINS:':
                s = 41
                cur_chain_list = []
                for i in range(1, (len(line[41:]) + 1)):
                    if line[40 + i:41 + i] == ',':
                        cur_chain_list.append(line[s:40 + i].strip())
                        s = 41 + i
                    elif i == len(line[41:]):
                        cur_chain_list.append(line[s:].strip())
                cur_biomolecule.chain_transforms[tuple(cur_chain_list)] = []
            elif line[13:18] == 'BIOMT':
                if line[18:19] == '1':
                    row1 = [float(line[24:33]), float(line[34:43]),
                            float(line[44:53]), float(line[60:68])]
                elif line[18:19] == '2':
                    row2 = [float(line[24:33]), float(line[34:43]),
                            float(line[44:53]), float(line[60:68])]
                elif line[18:19] == '3':
                    row3 = [float(line[24:33]), float(line[34:43]),
                            float(line[44:53]), float(line[60:68])]
                    cur_biomolecule.chain_transforms[tuple(cur_chain_list)].append([row1, row2, row3])

        elif line[:5] == 'MODEL':
            model_id = int(line[10:14])
            model_list[model_id] = Model(model_id)
            cur_model = model_list[model_id]
            model_flag = True
            for chain in chain_list:
                cur_model.chains[chain] = Chain(chain)
        elif line[:6] == 'ENDMDL':
            cur_model = None
        elif line[:4] == 'ATOM':
            if not model_flag:
                model_list[1] = Model(1)
                cur_model = model_list[1]
                model_flag = True
                for chain in chain_list:
                    cur_model.chains[chain] = Chain(chain)

            serial = int(line[6:11])
            name = line[12:16].strip()
            altloc = line[16:17]
            resname = line[17:20]
            chainid = line[21:22]
            resseq = int(line[22:26])
            icode = line[26:28].strip()
            x = float(line[30:38]) * scene_scale
            y = float(line[38:46]) * scene_scale
            z = float(line[46:54]) * scene_scale
            occupancy = float(line[54:60])
            tempfactor = float(line[60:66])
            element = line[76:78].strip()
            charge = line[78:80].strip()

            '''
            print('******')
            print('serial       : ' )
            print(serial)
            print('name         : ' )
            print(name)
            print('altloc       : ' )
            print(altloc)
            print('resname      : ' )
            print(resname)
            print('chainid      : ' )
            print(chainid)
            print('resseq       : ' )
            print(resseq)
            print('icode        : ' )
            print(icode)
            print('x            : ' )
            print(x)
            print('y            : ' )
            print(y)
            print('z            : ' )
            print(z)
            print('occupancy    : ' )
            print(occupancy)
            print('tempfactor   : ' )
            print(tempfactor)
            print('element      : ' )
            print(element)
            print('charge       : ' )
            print(charge)
            print('******')
            '''

            cur_model.chains[chainid].atoms[serial] = Atom(serial, name, altloc,
                                                           resname, chainid,
                                                           resseq, icode,
                                                           x, y, z, occupancy,
                                                           tempfactor, element,
                                                           charge)

    file.close()

    if (not multimers) or (not biomolecule_flag):
        # Create a default biomolecule w/ all chains and identity transform
        # Overwrites original biomolecule_list
        biomolecule_flag = True
        bm_serial = 1
        biomolecule = Biomolecule(bm_serial)
        biomolecule.chain_transforms[tuple(chain_list)] = [(((1.0, 0.0, 0.0, 0.0),
                                                             (0.0, 1.0, 0.0, 0.0),
                                                             (0.0, 0.0, 1.0, 0.0)))]
        biomolecule_list = {bm_serial: biomolecule}

    # -------------------------------------------------------------------------
    # Create atom mesh template
    bpy.ops.object.select_all(action='DESELECT')

    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=atom_subdivisions,
                                          size=(atom_size * scene_scale))
    bpy.ops.object.shade_smooth()
    atom_obj = scene.objects.active
    atom_mesh = atom_obj.data
    atom_mesh.name = 'Atom_Template'
    scene.objects.unlink(atom_obj)
    bpy.data.objects.remove(atom_obj)

    layers = scene.layers

    # After parsing and preparing the templates, generate the output
    for model_id, model in model_list.items():
        if (not multi_models) and model_id != 1:
            break

        for bm_serial, biomolecule in biomolecule_list.items():
            biom_mesh_name = "Biomolecule%d.%d" % (bm_serial, model_id)
            biom_mesh = bpy.data.meshes.new(biom_mesh_name)
            cur_biom = bpy.data.objects.new(biom_mesh_name, biom_mesh)
            scene.objects.link(cur_biom)

            for chain_clones, transforms in biomolecule.chain_transforms.items():
                for chain in chain_clones:

                    for transform in transforms:
                        # rotations
                        row1 = transform[0][0:3]
                        row2 = transform[1][0:3]
                        row3 = transform[2][0:3]
                        # translations
                        dx = transform[0][3]
                        dy = transform[1][3]
                        dz = transform[2][3]

                        for serial, atom in model.chains[chain].atoms.items():
                            # Prunes alternative locations for the atoms
                            # (should pick the one with highest occupancy but doesn't)
                            if (atom.altloc == ' ' or atom.altloc == 'A') or retain_alts:

                                element = atom_data[atom.element].name

                                # Generate master element models
                                if element not in mat_list:

                                    # Create a master atom
                                    mesh = atom_mesh.copy()
                                    mesh.name = element
                                    mat = bpy.data.materials.new(element)
                                    mat.diffuse_color = atom_data[atom.element].color
                                    mesh.materials.append(mat)
                                    master_atom = bpy.data.objects.new(element, mesh)
                                    master_atom.scale = [atom_data[atom.element].vdw_radius] * 3
                                    master_atom.layers = layers
                                    master_atom.name = element  # why set again?
                                    scene.objects.link(master_atom)

                                    mat_list.append(element)
                                else:
                                    pass

                                # Generate element vertex groups
                                if element not in cur_biom.vertex_groups:
                                    cur_vert_group = cur_biom.vertex_groups.new(element)
                                    #Adds a key in the vert_group_count
                                    biomolecule.vert_group_counts[cur_vert_group] = 0

                                else:
                                    cur_vert_group = cur_biom.vertex_groups[element]

                                # Generate particle systems
                                # (can be merged with vertex group generator)
                                if element not in cur_biom.particle_systems:
                                    scene.objects.active = cur_biom
                                    bpy.ops.object.particle_system_add()

                                    psys = cur_biom.particle_systems.active
                                    part = psys.settings

                                    psys.name = element
                                    part.name = "%s.%d.%d" % (element, bm_serial, model_id)
                                    part.frame_start = 0
                                    part.frame_end = 0
                                    part.lifetime = 10000
                                    part.emit_from = 'VERT'
                                    part.use_emit_random = False
                                    part.normal_factor = 0
                                    part.particle_size = 1
                                    part.render_type = 'OBJECT'
                                    part.dupli_object = bpy.data.objects[element]
                                    part.effector_weights.gravity = 0
                                    psys.vertex_group_density = element

                                biomolecule.vert_group_index[biomolecule.atom_count] = cur_vert_group
                                biomolecule.vert_group_counts[cur_vert_group] += 1
                                biomolecule.atom_count += 1
                                tx = atom.x * row1[0] + atom.y * row1[1] + atom.z * row1[2] + (dx * scene_scale)
                                ty = atom.x * row2[0] + atom.y * row2[1] + atom.z * row2[2] + (dy * scene_scale)
                                tz = atom.x * row3[0] + atom.y * row3[1] + atom.z * row3[2] + (dz * scene_scale)
                                biomolecule.vert_list.extend([tx, ty, tz])
                            else:
                                pass

            biom_mesh.vertices.add(biomolecule.atom_count)
            biom_mesh.vertices.foreach_set('co', biomolecule.vert_list)

            for vert_index, vert_group in biomolecule.vert_group_index.items():
                aa = []  # neeed array to vertex_groups.assign
                aa.append(vert_index)
                vert_group.add(aa, 1, "ADD")

            for vert_group, count in biomolecule.vert_group_counts.items():
                bpy.data.particles["%s.%d.%d" % (vert_group.name, bm_serial, model_id)].count = count
