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
#  Last modified                 : 2012-03-23
#
#  Acknowledgements: Thanks to ideasman, meta_androcto, truman, kilon,
#  dairin0d, PKHG, Valter, etc
#

bl_info = {
    "name": "PDB Atomic Blender",
    "description": "Loading and manipulating atoms from PDB files",
    "author": "Clemens Barth",
    "version": (1,3),
    "blender": (2,6),
    "location": "File -> Import -> PDB (.pdb), Panel: View 3D - Tools",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/"
                "Py/Scripts/Import-Export/PDB",
    "tracker_url": "http://projects.blender.org/tracker/"
                   "index.php?func=detail&aid=29226",
    "category": "Import-Export"
}

import os
import io
import bpy
import bmesh
from bpy.types import Operator, Panel
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.props import (StringProperty,
                       BoolProperty,
                       EnumProperty,
                       IntProperty,
                       FloatProperty)

from . import import_pdb
from . import export_pdb

ATOM_PDB_ERROR = ""
ATOM_PDB_PANEL = ""

# -----------------------------------------------------------------------------
#                                                                           GUI

# The panel, which is loaded after the file has been
# chosen via the menu 'File -> Import'
class CLASS_atom_pdb_panel(Panel):
    bl_label       = "PDB - Atomic Blender"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOL_PROPS"

    @classmethod
    def poll(self, context):
        global ATOM_PDB_PANEL
        
        if ATOM_PDB_PANEL == "0" and import_pdb.ATOM_PDB_FILEPATH == "":
            return False
        if ATOM_PDB_PANEL == "0" and import_pdb.ATOM_PDB_FILEPATH != "":
            return True
        if ATOM_PDB_PANEL == "1":
            return True
        if ATOM_PDB_PANEL == "2":
            return False
        
        return True

    def draw(self, context):
        layout = self.layout

        # This is for the case that a blend file is loaded. 
        if len(context.scene.atom_pdb) == 0:
            bpy.context.scene.atom_pdb.add()

        scn    = context.scene.atom_pdb[0]

        row = layout.row()
        row.label(text="Outputs and custom data file")
        box = layout.box()
        row = box.row()
        row.label(text="Custom data file")
        row = box.row()
        col = row.column()
        col.prop(scn, "datafile")
        col.operator("atom_pdb.datafile_apply")
        row = box.row()
        col = row.column(align=True)
        col.prop(scn, "PDB_file")
        row = layout.row()
        row.label(text="Reload structure")
        box = layout.box()
        row = box.row()
        col = row.column()
        col.prop(scn, "use_mesh")
        col = row.column()
        col.label(text="Scaling factors")
        row = box.row()
        col = row.column(align=True)  
        col.active = scn.use_mesh   
        col.prop(scn, "mesh_azimuth")
        col.prop(scn, "mesh_zenith")
        col = row.column(align=True)
        col.prop(scn, "scale_ballradius")
        col.prop(scn, "scale_distances")
        row = box.row()
        col = row.column()  
        col.prop(scn, "use_sticks")
        row = box.row()        
        row.active = scn.use_sticks
        col = row.column(align=True)
        col.prop(scn, "sticks_sectors")
        col.prop(scn, "sticks_radius")
        col.prop(scn, "sticks_unit_length")
        col = row.column(align=True)        
        col.prop(scn, "use_sticks_color")        
        col.prop(scn, "use_sticks_smooth")
        col.prop(scn, "use_sticks_bonds")
        row = box.row()        
        row.active = scn.use_sticks
        col = row.column(align=True)
        col = row.column(align=True)
        col.active = scn.use_sticks and scn.use_sticks_bonds 
        col.prop(scn, "sticks_dist")        
        row = box.row()
        row.prop(scn, "use_center")
        row = box.row()
        col = row.column()
        col.prop(scn, "use_camera")
        col.prop(scn, "use_lamp")
        col = row.column()
        col.operator("atom_pdb.button_reload")
        col.prop(scn, "number_atoms")
        row = box.row()
        row.operator("atom_pdb.button_distance")
        row.prop(scn, "distance")
        row = layout.row()
        row.label(text="Modify atom radii")
        box = layout.box()
        row = box.row()
        row.label(text="All changes concern:")
        row = box.row()
        row.prop(scn, "radius_how")
        row = box.row()
        row.label(text="1. Change type of radii")
        row = box.row()
        row.prop(scn, "radius_type")
        row = box.row()
        row.label(text="2. Change atom radii in pm")
        row = box.row()
        row.prop(scn, "radius_pm_name")
        row = box.row()
        row.prop(scn, "radius_pm")
        row = box.row()
        row.label(text="3. Change atom radii by scale")
        row = box.row()
        col = row.column()
        col.prop(scn, "radius_all")
        col = row.column(align=True)
        col.operator( "atom_pdb.radius_all_bigger" )
        col.operator( "atom_pdb.radius_all_smaller" )
        row = box.row()
        row.label(text="4. Show sticks only")
        row = box.row()
        col = row.column()
        col.operator( "atom_pdb.radius_sticks" )

        if bpy.context.mode == 'EDIT_MESH':
            row = layout.row()
            row.label(text="Separate atom")
            box = layout.box()
            row = box.row()
            row.operator( "atom_pdb.separate_atom" )


# The properties (gadgets) in the panel. They all go to scene
# during initialization (see end) 
class CLASS_atom_pdb_Properties(bpy.types.PropertyGroup):

    def Callback_radius_type(self, context):
        scn = bpy.context.scene.atom_pdb[0]
        import_pdb.DEF_atom_pdb_radius_type(
                scn.radius_type,
                scn.radius_how,)

    def Callback_radius_pm(self, context):
        scn = bpy.context.scene.atom_pdb[0]
        import_pdb.DEF_atom_pdb_radius_pm(
                scn.radius_pm_name,
                scn.radius_pm,
                scn.radius_how,)

    # In the file dialog window - Import
    use_camera = BoolProperty(
        name="Camera", default=False,
        description="Do you need a camera?")
    use_lamp = BoolProperty(
        name="Lamp", default=False,
        description = "Do you need a lamp?")
    use_mesh = BoolProperty(
        name = "Mesh balls", default=False,
        description = "Use mesh balls instead of NURBS")
    mesh_azimuth = IntProperty(
        name = "Azimuth", default=32, min=1,
        description = "Number of sectors (azimuth)")
    mesh_zenith = IntProperty(
        name = "Zenith", default=32, min=1,
        description = "Number of sectors (zenith)")
    scale_ballradius = FloatProperty(
        name = "Balls", default=1.0, min=0.0001,
        description = "Scale factor for all atom radii")
    scale_distances = FloatProperty (
        name = "Distances", default=1.0, min=0.0001,
        description = "Scale factor for all distances")
    use_center = BoolProperty(
        name = "Object to origin", default=True,
        description = "Put the object into the global origin")
    use_sticks = BoolProperty(
        name="Use sticks", default=True,
        description="Do you want to display the sticks?")
    sticks_sectors = IntProperty(
        name = "Sector", default=20, min=1,
        description="Number of sectors of a stick")
    sticks_radius = FloatProperty(
        name = "Radius", default=0.1, min=0.0001,
        description ="Radius of a stick")
    sticks_unit_length = FloatProperty(
        name = "Unit", default=0.05, min=0.0001,
        description = "Length of the unit of a stick in Angstrom")        
    use_sticks_color = BoolProperty(
        name="Color", default=True,
        description="The sticks appear in the color of the atoms")
    use_sticks_smooth = BoolProperty(
        name="Smooth", default=False,
        description="The sticks are round (sectors are not visible)")     
    use_sticks_bonds = BoolProperty(
        name="Bonds", default=False,
        description="Show double and tripple bonds.")
    sticks_dist = FloatProperty(
        name="Distance", default = 1.1, min=1.0, max=3.0,
        description="Distance between sticks measured in stick diameter")        
    atomradius = EnumProperty(
        name="Type of radius",
        description="Choose type of atom radius",
        items=(('0', "Pre-defined", "Use pre-defined radius"),
               ('1', "Atomic", "Use atomic radius"),
               ('2', "van der Waals", "Use van der Waals radius")),
               default='0',)  
    # In the panel
    datafile = StringProperty(
        name = "", description="Path to your custom data file",
        maxlen = 256, default = "", subtype='FILE_PATH')
    PDB_file = StringProperty(
        name = "PDB file", default="",
        description = "Path of the PDB file")
    number_atoms = StringProperty(name="",
        default="Number", description = "This output shows "
        "the number of atoms which have been loaded")
    distance = StringProperty(
        name="", default="Distance (A)",
        description="Distance of 2 objects in Angstrom")
    radius_how = EnumProperty(
        name="",
        description="Which objects shall be modified?",
        items=(('ALL_ACTIVE',"all active objects", "in the current layer"),
               ('ALL_IN_LAYER',"all"," in active layer(s)")),
               default='ALL_ACTIVE',)
    radius_type = EnumProperty(
        name="Type",
        description="Which type of atom radii?",
        items=(('0',"predefined", "Use pre-defined radii"),
               ('1',"atomic", "Use atomic radii"),
               ('2',"van der Waals","Use van der Waals radii")),
               default='0',update=Callback_radius_type)
    radius_pm_name = StringProperty(
        name="", default="Atom name",
        description="Put in the name of the atom (e.g. Hydrogen)")
    radius_pm = FloatProperty(
        name="", default=100.0, min=0.01,
        description="Put in the radius of the atom (in pm)",
        update=Callback_radius_pm)
    radius_all = FloatProperty(
        name="Scale", default = 1.05, min=1.0, max=5.0,
        description="Put in the scale factor")


# Button loading a custom data file
class CLASS_atom_pdb_datafile_apply(Operator):
    bl_idname = "atom_pdb.datafile_apply"
    bl_label = "Apply"
    bl_description = "Use color and radii values stored in the custom file"

    def execute(self, context):
        scn    = bpy.context.scene.atom_pdb[0]

        if scn.datafile == "":
            return {'FINISHED'}

        import_pdb.DEF_atom_pdb_custom_datafile(scn.datafile)

        return {'FINISHED'}


# Button for separating single objects from a atom mesh
class CLASS_atom_pdb_separate_atom(Operator):
    bl_idname = "atom_pdb.separate_atom"
    bl_label = "Separate atom"
    bl_description = "Separate the atom you have chosen"

    def execute(self, context):
        scn = bpy.context.scene.atom_pdb[0]

        # Get first all important properties from the atoms, which the user
        # has chosen: location, color, scale
        obj = bpy.context.edit_object
        bm = bmesh.from_edit_mesh(obj.data)

        locations = []

        for v in bm.verts:
            if v.select:
                locations.append(obj.matrix_world * v.co)

        bm.free()
        del(bm)

        name  = obj.name
        scale = obj.children[0].scale
        material = obj.children[0].active_material

        # Separate the vertex from the main mesh and create a new mesh.
        bpy.ops.mesh.separate()
        new_object = bpy.context.scene.objects[0]
        # And now, switch to the OBJECT mode such that we can ...
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        # ... delete the new mesh including the separated vertex
        bpy.ops.object.select_all(action='DESELECT')
        new_object.select = True
        bpy.ops.object.delete()  

        # Create new atoms/vacancies at the position of the old atoms
        current_layers=bpy.context.scene.layers

        # For all selected positions do:
        for location in locations:
            if "Vacancy" not in name:
                if scn.use_mesh == False:
                    bpy.ops.surface.primitive_nurbs_surface_sphere_add(
                                    view_align=False, enter_editmode=False,
                                    location=location,
                                    rotation=(0.0, 0.0, 0.0),
                                    layers=current_layers)
                else:
                    bpy.ops.mesh.primitive_uv_sphere_add(
                                segments=scn.mesh_azimuth,
                                ring_count=scn.mesh_zenith,
                                size=1, view_align=False, enter_editmode=False,
                                location=location,
                                rotation=(0, 0, 0),
                                layers=current_layers)
            else:
                bpy.ops.mesh.primitive_cube_add(
                               view_align=False, enter_editmode=False,
                               location=location,
                               rotation=(0.0, 0.0, 0.0),
                               layers=current_layers)

            new_atom = bpy.context.scene.objects.active
            # Scale, material and name it.
            new_atom.scale = scale
            new_atom.active_material = material
            new_atom.name = name + "_sep"
            new_atom.select = False

        bpy.context.scene.objects.active = obj
        bpy.ops.object.select_all(action='DESELECT')

        return {'FINISHED'}


# Button for measuring the distance of the active objects
class CLASS_atom_pdb_distance_button(Operator):
    bl_idname = "atom_pdb.button_distance"
    bl_label = "Measure ..."
    bl_description = "Measure the distance between two objects (only in Object Mode)"

    def execute(self, context):
        scn    = bpy.context.scene.atom_pdb[0]
        dist   = import_pdb.DEF_atom_pdb_distance()

        if dist != "N.A.":
           # The string length is cut, 3 digits after the first 3 digits
           # after the '.'. Append also "Angstrom".
           # Remember: 1 Angstrom = 10^(-10) m
           pos    = str.find(dist, ".")
           dist   = dist[:pos+4]
           dist   = dist + " A"

        # Put the distance into the string of the output field.
        scn.distance = dist
        return {'FINISHED'}


# Button for increasing the radii of all atoms
class CLASS_atom_pdb_radius_all_bigger_button(Operator):
    bl_idname = "atom_pdb.radius_all_bigger"
    bl_label = "Bigger ..."
    bl_description = "Increase the radii of the atoms"

    def execute(self, context):
        scn = bpy.context.scene.atom_pdb[0]
        import_pdb.DEF_atom_pdb_radius_all(
                scn.radius_all,
                scn.radius_how,)
        return {'FINISHED'}


# Button for decreasing the radii of all atoms
class CLASS_atom_pdb_radius_all_smaller_button(Operator):
    bl_idname = "atom_pdb.radius_all_smaller"
    bl_label = "Smaller ..."
    bl_description = "Decrease the radii of the atoms"

    def execute(self, context):
        scn = bpy.context.scene.atom_pdb[0]
        import_pdb.DEF_atom_pdb_radius_all(
                1.0/scn.radius_all,
                scn.radius_how,)
        return {'FINISHED'}


# Button for showing the sticks only - the radii of the atoms downscaled onto
# 90% of the stick radius
class CLASS_atom_pdb_radius_sticks_button(Operator):
    bl_idname = "atom_pdb.radius_sticks"
    bl_label = "Show sticks"
    bl_description = "Show only the sticks (atom radii = stick radii)"

    def execute(self, context):
        global ATOM_PDB_ERROR
        scn = bpy.context.scene.atom_pdb[0]
                
        result = import_pdb.DEF_atom_pdb_radius_sticks(
                     0.01,
                     scn.radius_how,)  
        if result == False:
            ATOM_PDB_ERROR = "No sticks => no changes"
            bpy.ops.atom_pdb.error_dialog('INVOKE_DEFAULT')
                                          
        return {'FINISHED'}


# The button for reloading the atoms and creating the scene
class CLASS_atom_pdb_load_button(Operator):
    bl_idname = "atom_pdb.button_reload"
    bl_label = "RELOAD"
    bl_description = "Load the structure again"

    def execute(self, context):
        scn = context.scene.atom_pdb[0]
        
        atom_number = import_pdb.DEF_atom_pdb_main(
                      scn.use_mesh,
                      scn.mesh_azimuth,
                      scn.mesh_zenith,
                      scn.scale_ballradius,
                      scn.atomradius,
                      scn.scale_distances,
                      scn.use_sticks,
                      scn.use_sticks_color,
                      scn.use_sticks_smooth,
                      scn.use_sticks_bonds,
                      scn.sticks_unit_length,
                      scn.sticks_dist,
                      scn.sticks_sectors,
                      scn.sticks_radius,
                      scn.use_center,
                      scn.use_camera,
                      scn.use_lamp,
                      scn.datafile)     
                      
        scn.number_atoms = str(atom_number) + " atoms"

        return {'FINISHED'}


def DEF_panel_yes_no():
    global ATOM_PDB_PANEL

    datafile_path = bpy.utils.user_resource('SCRIPTS', path='', create=False)
    if os.path.isdir(datafile_path) == False:
        bpy.utils.user_resource('SCRIPTS', path='', create=True)
    datafile_path = os.path.join(datafile_path, "presets")
    if os.path.isdir(datafile_path) == False:
        os.mkdir(datafile_path)   
    datafile = os.path.join(datafile_path, "io_mesh_pdb.pref")
    if os.path.isfile(datafile):
        datafile_fp = io.open(datafile, "r")
        for line in datafile_fp:
            if "Panel" in line:
                ATOM_PDB_PANEL = line[-2:]
                ATOM_PDB_PANEL = ATOM_PDB_PANEL[0:1]
                bpy.context.scene.use_panel = ATOM_PDB_PANEL
                break       
        datafile_fp.close()
    else:
        DEF_panel_write_pref("0") 


def DEF_panel_write_pref(value): 
    datafile_path = bpy.utils.user_resource('SCRIPTS', path='', create=False)
    datafile_path = os.path.join(datafile_path, "presets")
    datafile = os.path.join(datafile_path, "io_mesh_pdb.pref")
    datafile_fp = io.open(datafile, "w")
    datafile_fp.write("Atomic Blender PDB - Import/Export - Preferences\n")
    datafile_fp.write("================================================\n")
    datafile_fp.write("\n")
    datafile_fp.write("Panel: "+value+"\n\n\n")
    datafile_fp.close()        


class CLASS_atom_pdb_error_dialog(bpy.types.Operator):
    bl_idname = "atom_pdb.error_dialog"
    bl_label = "Attention !"
    
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text="                          "+ATOM_PDB_ERROR) 
    def execute(self, context):
        print("Atomic Blender - Error: "+ATOM_PDB_ERROR+"\n")
        return {'FINISHED'}
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)        


# This is the class for the file dialog of the importer.
class CLASS_ImportPDB(Operator, ImportHelper):
    bl_idname = "import_mesh.pdb"
    bl_label  = "Import Protein Data Bank(*.pdb)"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".pdb"
    filter_glob  = StringProperty(default="*.pdb", options={'HIDDEN'},)

    bpy.types.Scene.use_panel = EnumProperty(
        name="Panel",
        description="Choose whether the panel shall appear or not in the View 3D.",
        items=(('0', "Once", "The panel appears only in this session"),
               ('1', "Always", "The panel always appears when Blender is started"),
               ('2', "Never", "The panel never appears")),
               default='0')  
    use_camera = BoolProperty(
        name="Camera", default=False,
        description="Do you need a camera?")
    use_lamp = BoolProperty(
        name="Lamp", default=False,
        description = "Do you need a lamp?")
    use_mesh = BoolProperty(
        name = "Mesh balls", default=False,
        description = "Use mesh balls instead of NURBS")
    mesh_azimuth = IntProperty(
        name = "Azimuth", default=32, min=1,
        description = "Number of sectors (azimuth)")
    mesh_zenith = IntProperty(
        name = "Zenith", default=32, min=1,
        description = "Number of sectors (zenith)")
    scale_ballradius = FloatProperty(
        name = "Balls", default=1.0, min=0.0001,
        description = "Scale factor for all atom radii")
    scale_distances = FloatProperty (
        name = "Distances", default=1.0, min=0.0001,
        description = "Scale factor for all distances")
    atomradius = EnumProperty(
        name="Type of radius",
        description="Choose type of atom radius",
        items=(('0', "Pre-defined", "Use pre-defined radius"),
               ('1', "Atomic", "Use atomic radius"),
               ('2', "van der Waals", "Use van der Waals radius")),
               default='0',)        
    use_sticks = BoolProperty(
        name="Use sticks", default=True,
        description="Do you want to display the sticks?")
    sticks_sectors = IntProperty(
        name = "Sector", default=20, min=1,
        description="Number of sectors of a stick")
    sticks_radius = FloatProperty(
        name = "Radius", default=0.1, min=0.0001,
        description ="Radius of a stick")
    sticks_unit_length = FloatProperty(
        name = "Unit", default=0.05, min=0.0001,
        description = "Length of the unit of a stick in Angstrom")        
    use_sticks_color = BoolProperty(
        name="Color", default=True,
        description="The sticks appear in the color of the atoms")
    use_sticks_smooth = BoolProperty(
        name="Smooth", default=False,
        description="The sticks are round (sectors are not visible)")     
    use_sticks_bonds = BoolProperty(
        name="Bonds", default=False,
        description="Show double and tripple bonds.")
    sticks_dist = FloatProperty(
        name="Distance", default = 1.1, min=1.0, max=3.0,
        description="Distance between sticks measured in stick diameter")        
    use_center = BoolProperty(
        name = "Object to origin", default=True,
        description = "Put the object into the global origin")           
    datafile = StringProperty(
        name = "", description="Path to your custom data file",
        maxlen = 256, default = "", subtype='FILE_PATH')

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, "use_camera")
        row.prop(self, "use_lamp")
        row = layout.row()
        col = row.column()
        col.prop(self, "use_mesh")
        col = row.column(align=True)
        col.active = self.use_mesh
        col.prop(self, "mesh_azimuth")
        col.prop(self, "mesh_zenith")
        row = layout.row()
        col = row.column()
        col.label(text="Scaling factors")
        col = row.column(align=True)
        col.prop(self, "scale_ballradius")
        col.prop(self, "scale_distances")
        row = layout.row()
        row.prop(self, "atomradius")
        row = layout.row()
        col = row.column()
        col.prop(self, "use_sticks")
        row = layout.row()        
        row.active = self.use_sticks
        col = row.column()
        col.prop(self, "sticks_sectors")
        col.prop(self, "sticks_radius")
        col.prop(self, "sticks_unit_length")
        col = row.column(align=True)        
        col.prop(self, "use_sticks_color")        
        col.prop(self, "use_sticks_smooth")
        col.prop(self, "use_sticks_bonds")
        row = layout.row()        
        row.active = self.use_sticks
        col = row.column(align=True)
        col = row.column(align=True)
        col.active = self.use_sticks and self.use_sticks_bonds 
        col.prop(self, "sticks_dist")
        row = layout.row()
        row.prop(self, "use_center")
        row = layout.row()
        row.prop(bpy.context.scene, "use_panel")

    def execute(self, context):
        # This is in order to solve this strange 'relative path' thing.
        import_pdb.ATOM_PDB_FILEPATH = bpy.path.abspath(self.filepath)

        # Execute main routine                
        atom_number = import_pdb.DEF_atom_pdb_main(
                      self.use_mesh,
                      self.mesh_azimuth,
                      self.mesh_zenith,
                      self.scale_ballradius,
                      self.atomradius,
                      self.scale_distances,
                      self.use_sticks,
                      self.use_sticks_color,
                      self.use_sticks_smooth,
                      self.use_sticks_bonds,
                      self.sticks_unit_length,
                      self.sticks_dist,
                      self.sticks_sectors,
                      self.sticks_radius,
                      self.use_center,
                      self.use_camera,
                      self.use_lamp,
                      self.datafile)        

        # Copy the whole bunch of values into the property collection.
        scn = context.scene.atom_pdb[0]
        scn.use_mesh = self.use_mesh
        scn.mesh_azimuth = self.mesh_azimuth
        scn.mesh_zenith = self.mesh_zenith
        scn.scale_ballradius = self.scale_ballradius
        scn.atomradius = self.atomradius
        scn.scale_distances = self.scale_distances
        scn.use_sticks = self.use_sticks
        scn.use_sticks_color = self.use_sticks_color
        scn.use_sticks_smooth = self.use_sticks_smooth
        scn.use_sticks_bonds = self.use_sticks_bonds
        scn.sticks_unit_length = self.sticks_unit_length
        scn.sticks_dist = self.sticks_dist
        scn.sticks_sectors = self.sticks_sectors
        scn.sticks_radius = self.sticks_radius
        scn.use_center = self.use_center
        scn.use_camera = self.use_camera
        scn.use_lamp = self.use_lamp
        scn.datafile = self.datafile
        
        scn.number_atoms = str(atom_number) + " atoms"
        scn.PDB_file = import_pdb.ATOM_PDB_FILEPATH
      
        global ATOM_PDB_PANEL
        ATOM_PDB_PANEL = bpy.context.scene.use_panel
        DEF_panel_write_pref(bpy.context.scene.use_panel)

        return {'FINISHED'}



# This is the class for the file dialog of the exporter.
class CLASS_ExportPDB(Operator, ExportHelper):
    bl_idname = "export_mesh.pdb"
    bl_label  = "Export Protein Data Bank(*.pdb)"
    filename_ext = ".pdb"

    filter_glob  = StringProperty(
        default="*.pdb", options={'HIDDEN'},)

    atom_pdb_export_type = EnumProperty(
        name="Type of Objects",
        description="Choose type of objects",
        items=(('0', "All", "Export all active objects"),
               ('1', "Elements", "Export only those active objects which have"
                                 " a proper element name")),
               default='1',) 

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, "atom_pdb_export_type")

    def execute(self, context):
        # This is in order to solve this strange 'relative path' thing.
        export_pdb.ATOM_PDB_FILEPATH = bpy.path.abspath(self.filepath)
        export_pdb.DEF_atom_pdb_export(self.atom_pdb_export_type)

        return {'FINISHED'}


# The entry into the menu 'file -> import'
def DEF_menu_func_import(self, context):
    self.layout.operator(CLASS_ImportPDB.bl_idname, text="Protein Data Bank (.pdb)")

# The entry into the menu 'file -> export'
def DEF_menu_func_export(self, context):
    self.layout.operator(CLASS_ExportPDB.bl_idname, text="Protein Data Bank (.pdb)")


def register():
    DEF_panel_yes_no()
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(DEF_menu_func_import)
    bpy.types.INFO_MT_file_export.append(DEF_menu_func_export)
    bpy.types.Scene.atom_pdb = bpy.props.CollectionProperty(type=CLASS_atom_pdb_Properties)    
    bpy.context.scene.atom_pdb.add()
    
def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_import.remove(DEF_menu_func_import)
    bpy.types.INFO_MT_file_export.remove(DEF_menu_func_export)

if __name__ == "__main__":

    register()
