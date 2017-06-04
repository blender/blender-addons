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

# Contributed to by:
# meta-androcto, Bill Currie, Jorge Hernandez - Melenedez  Jacob Morris, Oscurart  #
# Rebellion, Antonis Karvelas, Eleanor Howick, lijenstina, Daniel Schalla, Domlysz #
# Unnikrishnan(kodemax), Florian Meyer, Omar ahmed, Brian Hinton (Nichod), liero   #
# Atom, Dannyboy, Mano-Wii, Kursad Karatas, teldredge, Phil Cote #

bl_info = {
    "name": "Add Advanced Objects",
    "author": "Meta Androcto,",
    "version": (0, 1, 3),
    "blender": (2, 78, 0),
    "location": "View3D > Add ",
    "description": "Add Object & Camera extras",
    "warning": "",
    "wiki_url": "https://wiki.blender.org/index.php/Extensions:2.6"
                "/Py/Scripts/Object/Add_Advanced",
    "category": "Object"}

if "bpy" in locals():
    import importlib

    importlib.reload(add_light_template)
    importlib.reload(scene_objects_bi)
    importlib.reload(scene_objects_cycles)
    importlib.reload(scene_texture_render)
    importlib.reload(trilighting)
    importlib.reload(pixelate_3d)
    importlib.reload(object_add_chain)
    importlib.reload(drop_to_ground)
    importlib.reload(circle_array)
    importlib.reload(unfold_transition)
    importlib.reload(copy2)
    importlib.reload(make_struts)
    importlib.reload(random_box_structure)
    importlib.reload(cubester)
    importlib.reload(rope_alpha)
    importlib.reload(add_mesh_aggregate)
    importlib.reload(object_mangle_tools)
    importlib.reload(arrange_on_curve)
    importlib.reload(object_laplace_lightning)
    importlib.reload(mesh_easylattice)
    importlib.reload(DelaunayVoronoi)
    importlib.reload(delaunayVoronoiBlender)
    importlib.reload(oscurart_constellation)
    importlib.reload(oscurart_chain_maker)

else:
    from . import add_light_template
    from . import scene_objects_bi
    from . import scene_objects_cycles
    from . import scene_texture_render
    from . import trilighting
    from . import pixelate_3d
    from . import object_add_chain
    from . import oscurart_chain_maker
    from . import drop_to_ground
    from . import circle_array
    from . import unfold_transition
    from . import copy2
    from . import make_struts
    from . import random_box_structure
    from . import cubester
    from . import rope_alpha
    from . import add_mesh_aggregate
    from . import object_mangle_tools
    from . import arrange_on_curve
    from . import object_laplace_lightning
    from . import mesh_easylattice

    from .delaunay_voronoi import DelaunayVoronoi
    from .delaunay_voronoi import delaunayVoronoiBlender
    from .delaunay_voronoi import oscurart_constellation

import bpy
from bpy.types import (
        Menu,
        AddonPreferences,
        PropertyGroup,
        )
from bpy.props import (
        BoolProperty,
        BoolVectorProperty,
        EnumProperty,
        FloatProperty,
        FloatVectorProperty,
        IntProperty,
        StringProperty,
        PointerProperty,
        )


# Define the "Scenes" menu
class INFO_MT_scene_elements_add(Menu):
    bl_idname = "INFO_MT_scene_elements"
    bl_label = "Test Scenes"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("bi.add_scene",
                        text="Scene_Objects_BI")
        layout.operator("objects_cycles.add_scene",
                        text="Scene_Objects_Cycles")
        layout.operator("objects_texture.add_scene",
                        text="Scene_Textures_Cycles")


# Define the "Lights" menu
class INFO_MT_mesh_lamps_add(Menu):
    bl_idname = "INFO_MT_scene_lamps"
    bl_label = "Lighting Sets"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("object.add_light_template",
                        text="Add Light Template")
        layout.operator("object.trilighting",
                        text="Add Tri Lighting")


# Define the "Chains" menu
class INFO_MT_mesh_chain_add(Menu):
    bl_idname = "INFO_MT_mesh_chain"
    bl_label = "Chains"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("mesh.primitive_chain_add", icon="LINKED")
        layout.operator("mesh.primitive_oscurart_chain_add", icon="LINKED")


# Define the "Array" Menu
class INFO_MT_array_mods_add(Menu):
    bl_idname = "INFO_MT_array_mods"
    bl_label = "Array Mods"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.menu("INFO_MT_mesh_chain", icon="LINKED")

        layout.operator("objects.circle_array_operator",
                        text="Circle Array", icon="MOD_ARRAY")
        layout.operator("object.agregate_mesh",
                        text="Aggregate Mesh", icon="MOD_ARRAY")
        layout.operator("mesh.copy2",
                text="Copy To Vert/Edge", icon="MOD_ARRAY")


# Define the "Blocks" Menu
class INFO_MT_quick_blocks_add(Menu):
    bl_idname = "INFO_MT_quick_tools"
    bl_label = "Block Tools"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("object.pixelate", icon="MESH_GRID")
        layout.operator("mesh.generate_struts",
                    text="Struts", icon="GRID")
        layout.operator("object.make_structure",
                    text="Random Boxes", icon="SEQ_SEQUENCER")
        layout.operator("object.easy_lattice",
                    text="Easy Lattice", icon="MOD_LATTICE")


# Define the "Phsysics Tools" Menu
class INFO_MT_Physics_tools_add(Menu):
    bl_idname = "INFO_MT_physics_tools"
    bl_label = "Physics Tools"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("object.drop_on_active",
                        text="Drop To Ground", icon="SORTSIZE")
        layout.operator("ball.rope",
                        text="Wrecking Ball", icon='PHYSICS')
        layout.operator("clot.rope",
                        text="Cloth Rope", icon='PHYSICS')


# Define "Extras" menu
def menu(self, context):
    layout = self.layout
    layout.operator_context = 'INVOKE_REGION_WIN'
    self.layout.separator()
    self.layout.menu("INFO_MT_scene_elements", icon="SCENE_DATA")
    self.layout.menu("INFO_MT_scene_lamps", icon="LAMP_SPOT")
    self.layout.separator()
    self.layout.menu("INFO_MT_array_mods", icon="MOD_ARRAY")
    self.layout.menu("INFO_MT_quick_tools", icon="MOD_BUILD")
    self.layout.menu("INFO_MT_physics_tools", icon="PHYSICS")


# Addons Preferences
class AdvancedObjPreferences(AddonPreferences):
    bl_idname = __name__

    show_menu_list = BoolProperty(
            name="Menu List",
            description="Show/Hide the Add Menu items",
            default=False
            )
    show_panel_list = BoolProperty(
            name="Panels List",
            description="Show/Hide the Panel items",
            default=False
            )

    def draw(self, context):
        layout = self.layout

        icon_1 = "TRIA_RIGHT" if not self.show_menu_list else "TRIA_DOWN"
        box = layout.box()
        box.prop(self, "show_menu_list", emboss=False, icon=icon_1)

        if self.show_menu_list:
            box.label(text="Items located in the Add Menu (default shortcut Ctrl + A):",
                      icon="LAYER_USED")
            box.label(text="Test Scenes:", icon="LAYER_ACTIVE")
            box.label(text="Scene Objects BI, Scene Objects Cycles, Scene Textures Cycles",
                      icon="LAYER_USED")
            box.label(text="Lighting Sets:", icon="LAYER_ACTIVE")
            box.label(text="Add Light Template, Add Tri Lighting", icon="LAYER_USED")
            box.label(text="Array Mods:", icon="LAYER_ACTIVE")
            box.label(text="Circle Array, Chains submenu, Copy Vert/Edge and Aggregate Mesh",
                         icon="LAYER_ACTIVE")
            box.label(text="Chains Submenu - Add Chain, Chain to Bones",
                      icon="LAYER_ACTIVE")
            box.label(text="Block Tools:", icon="LAYER_ACTIVE")
            box.label(text="Pixelate Object, Struts, Random Boxes, Easy Lattice",
                      icon="LAYER_USED")
            box.label(text="Physics Tools:", icon="LAYER_ACTIVE")
            box.label(text="Drop to Ground, Wrecking Ball and Cloth Rope", icon="LAYER_USED")

        icon_2 = "TRIA_RIGHT" if not self.show_panel_list else "TRIA_DOWN"
        box = layout.box()
        box.prop(self, "show_panel_list", emboss=False, icon=icon_2)

        if self.show_panel_list:
            box.label(text="Panels located in 3D View Tools Region > Create",
                      icon="LAYER_ACTIVE")
            box.label(text="Drop to Ground", icon="LAYER_USED")
            box.label(text="Unfold Transition", icon="LAYER_USED")
            box.label(text="CubeSter", icon="LAYER_USED")
            box.label(text="Mangle tools", icon="LAYER_USED")
            box.label(text="Laplacian Lighting", icon="LAYER_USED")
            box.label(text="Delaunay Voronoi", icon="LAYER_USED")
            box.label(text="Duplicate on Curve  (Shown if an Active Curve Object is it the 3D View)",
                      icon="LAYER_USED")


# Cubester update functions
def find_audio_length(self, context):
    adv_obj = context.scene.advanced_objects
    audio_file = adv_obj.cubester_audio_path
    length = 0

    if audio_file != "":
        # confirm that strip hasn't been loaded yet
        get_sequence = getattr(context.scene.sequence_editor, "sequences_all", [])
        for strip in get_sequence:
            if type(strip) == bpy.types.SoundSequence and strip.sound.filepath == audio_file:
                length = strip.frame_final_duration

        if length == 0:
            area = context.area
            old_type = area.type
            area.type = "SEQUENCE_EDITOR"
            try:
                bpy.ops.sequencer.sound_strip_add(filepath=audio_file)
                adv_obj.cubester_check_audio = True
            except Exception as e:
                print("\n[Add Advanced Objects]\n Function: "
                      "find_audio_length\n {}\n".format(e))
                adv_obj.cubester_check_audio = False
                pass

            area.type = old_type

        # find audio file
        for strip in context.scene.sequence_editor.sequences_all:
            if type(strip) == bpy.types.SoundSequence and strip.sound.filepath == audio_file:
                adv_obj.cubester_check_audio = True
                length = strip.frame_final_duration

    adv_obj.cubester_audio_file_length = length


# load image if possible
def adjust_selected_image(self, context):
    scene = context.scene.advanced_objects
    try:
        image = bpy.data.images.load(scene.cubester_load_image)
        scene.cubester_image = image.name
    except Exception as e:
        print("\n[Add Advanced Objects]\n Function: "
              "adjust_selected_image\n {}\n".format(e))


# load color image if possible
def adjust_selected_color_image(self, context):
    scene = context.scene.advanced_objects
    try:
        image = bpy.data.images.load(scene.cubester_load_color_image)
        scene.cubester_color_image = image.name
    except Exception as e:
        print("\nAdd Advanced Objects]\n Function: "
              "adjust_selected_color_image\n {}\n".format(e))


class AdvancedObjProperties(PropertyGroup):
    # cubester
    # main properties
    cubester_check_audio = BoolProperty(
            name="",
            default=False
            )
    cubester_audio_image = EnumProperty(
            name="Input Type",
            items=(("image", "Image",
                    "Use an Image as input for generating Geometry", "IMAGE_COL", 0),
                   ("audio", "Audio",
                    "Use a Sound Strip as input for generating Geometry", "FILE_SOUND", 1))
            )
    cubester_audio_file_length = IntProperty(
            default=0
            )
    # audio
    cubester_audio_path = StringProperty(
            default="",
            name="Audio File",
            subtype="FILE_PATH",
            update=find_audio_length
            )
    cubester_audio_min_freq = IntProperty(
            name="Minimum Frequency",
            min=20, max=100000,
            default=20
            )
    cubester_audio_max_freq = IntProperty(
            name="Maximum Frequency",
            min=21, max=999999,
            default=5000
            )
    cubester_audio_offset_type = EnumProperty(
            name="Offset Type",
            items=(("freq", "Frequency Offset", ""),
                   ("frame", "Frame Offset", "")),
            description="Type of offset per row of mesh"
            )
    cubester_audio_frame_offset = IntProperty(
            name="Frame Offset",
            min=0, max=10,
            default=2
            )
    cubester_audio_block_layout = EnumProperty(
            name="Block Layout",
            items=(("rectangle", "Rectangular", ""),
                  ("radial", "Radial", ""))
            )
    cubester_audio_width_blocks = IntProperty(
            name="Width Block Count",
            min=1, max=10000,
            default=5
            )
    cubester_audio_length_blocks = IntProperty(
            name="Length Block Count",
            min=1, max=10000,
            default=50
            )
    # image
    cubester_load_type = EnumProperty(
            name="Image Input Type",
            items=(("single", "Single Image", ""),
                  ("multiple", "Image Sequence", ""))
            )
    cubester_image = StringProperty(
            default="",
            name=""
            )
    cubester_load_image = StringProperty(
            default="",
            name="Load Image",
            subtype="FILE_PATH",
            update=adjust_selected_image
            )
    cubester_skip_images = IntProperty(
            name="Image Step",
            min=1, max=30,
            default=1,
            description="Step from image to image by this number"
            )
    cubester_max_images = IntProperty(
            name="Max Number Of Images",
            min=2, max=1000,
            default=10,
            description="Maximum number of images to be used"
            )
    cubester_frame_step = IntProperty(
            name="Frame Step Size",
            min=1, max=10,
            default=4,
            description="The number of frames each picture is used"
            )
    cubester_skip_pixels = IntProperty(
            name="Skip # Pixels",
            min=0, max=256,
            default=64,
            description="Skip this number of pixels before placing the next"
            )
    cubester_mesh_style = EnumProperty(
            name="Mesh Type",
            items=(("blocks", "Blocks", ""),
                   ("plane", "Plane", "")),
            description="Compose mesh of multiple blocks or of a single plane"
            )
    cubester_block_style = EnumProperty(
            name="Block Style",
            items=(("size", "Vary Size", ""),
                   ("position", "Vary Position", "")),
            description="Vary Z-size of block, or vary Z-position"
            )
    cubester_height_scale = FloatProperty(
            name="Height Scale",
            subtype="DISTANCE",
            min=0.1, max=2,
            default=0.2
            )
    cubester_invert = BoolProperty(
            name="Invert Height",
            default=False
            )
    # general adjustments
    cubester_size_per_hundred_pixels = FloatProperty(
            name="Size Per 100 Blocks/Points",
            subtype="DISTANCE",
            min=0.001, max=5,
            default=1
            )
    # material based stuff
    cubester_materials = EnumProperty(
            name="Material",
            items=(("vertex", "Vertex Colors", ""),
                   ("image", "Image", "")),
            description="Color with vertex colors, or uv unwrap and use an image"
            )
    cubester_use_image_color = BoolProperty(
            name="Use Original Image Colors'?",
            default=True,
            description="Use original image colors, or replace with an another one"
            )
    cubester_color_image = StringProperty(
            default="",
            name=""
            )
    cubester_load_color_image = StringProperty(
            default="",
            name="Load Color Image",
            subtype="FILE_PATH",
            update=adjust_selected_color_image
            )
    cubester_vertex_colors = {}
    # advanced
    cubester_advanced = BoolProperty(
            name="Advanced Options",
            default=False
            )
    cubester_random_weights = BoolProperty(
            name="Random Weights",
            default=False
            )
    cubester_weight_r = FloatProperty(
            name="Red",
            subtype="FACTOR",
            min=0.01, max=1.0,
            default=0.25
            )
    cubester_weight_g = FloatProperty(
            name="Green",
            subtype="FACTOR",
            min=0.01, max=1.0,
            default=0.25
            )
    cubester_weight_b = FloatProperty(
            name="Blue",
            subtype="FACTOR",
            min=0.01, max=1.0,
            default=0.25
            )
    cubester_weight_a = FloatProperty(
            name="Alpha",
            subtype="FACTOR",
            min=0.01, max=1.0,
            default=0.25
            )

    # pixelate_3d properties
    pixelate_3d_size = FloatProperty(
            name="Size",
            min=.05, max=5,
            default=.25,
            description="Size of the cube / grid"
            )
    pixelate_3d_gap = IntProperty(
            name="Gap",
            min=0, max=90,
            default=10,
            subtype='PERCENTAGE',
            description="Separation - percent of size"
            )
    pixelate_3d_smooth = FloatProperty(
            name="Smooth",
            min=0, max=1,
            default=.0,
            description="Smooth factor when subdividing mesh"
            )
    # arrange_on_curve
    arrange_c_use_selected = BoolProperty(
            name="Use Selected",
            description="Use the selected objects to duplicate",
            default=True,
            )
    arrange_c_obj_arranjar = StringProperty(
            name=""
            )
    arrange_c_select_type = EnumProperty(
            name="Type",
            description="Select object or group",
            items=[
                ('O', "Object", "Make duplicates of a specific object"),
                ('G', "Group", "Make duplicates of the objects in a group"),
            ],
            default='O',
            )
    # object_laplace_lighting props
    ORIGIN = FloatVectorProperty(
            name="Origin charge"
            )
    GROUNDZ = IntProperty(
            name="Ground Z coordinate"
            )
    HORDER = IntProperty(
            name="Secondary paths orders",
            default=1
            )
    # object_laplace_lighting UI props
    TSTEPS = IntProperty(
            name="Iterations",
            default=350,
            description="Number of cells to create\n"
                        "Will end early if hits ground plane or cloud"
            )
    GSCALE = FloatProperty(
            name="Grid unit size",
            default=0.12,
            description="scale of cells, .25 = 4 cells per blenderUnit"
            )
    BIGVAR = FloatProperty(
            name="Straightness",
            default=6.3,
            description="Straightness/branchiness of bolt, \n"
                        "<2 is mush, >12 is staight line, 6.3 is good"
            )
    GROUNDBOOL = BoolProperty(
            name="Use Ground object",
            description="Use ground plane or not",
            default=True
            )
    GROUNDC = IntProperty(
            name="Ground charge",
            default=-250,
            description="Charge of the ground plane"
            )
    CLOUDBOOL = BoolProperty(
            name="Use Cloud object",
            default=False,
            description="Use cloud object - attracts and terminates like ground but\n"
                        "any obj instead of z plane\n"
                        "Can slow down loop if obj is large, overrides ground"
            )
    CLOUDC = IntProperty(
            name="Cloud charge",
            default=-1,
            description="Charge of a cell in cloud object\n"
                        "(so total charge also depends on obj size)"
            )
    VMMESH = BoolProperty(
            name="Multi mesh",
            default=True,
            description="Output to multi-meshes for different materials on main/sec/side branches"
            )
    VSMESH = BoolProperty(
            name="Single mesh",
            default=False,
            description="Output to single mesh for using build modifier and particles for effects"
            )
    VCUBE = BoolProperty(
            name="Cubes",
            default=False,
            description="CTRL-J after run to JOIN\n"
                        "Outputs a bunch of cube objects, mostly for testing"
            )
    VVOX = BoolProperty(
            name="Voxel (experimental)",
            default=False,
            description="Output to a voxel file to bpy.data.filepath\FSLGvoxels.raw\n"
                        "(doesn't work well right now)"
            )
    IBOOL = BoolProperty(
            name="Use Insulator object",
            default=False,
            description="Use insulator mesh object to prevent growth of bolt in areas"
            )
    OOB = StringProperty(
            name="Select",
            default="",
            description="Origin of bolt, can be an Empty\n"
                        "if object is a mesh will use all verts as charges")
    GOB = StringProperty(
            name="Select",
            default="",
            description="Object to use as ground plane, uses z coord only"
            )
    COB = StringProperty(
            name="Select",
            default="",
            description="Object to use as cloud, best to use a cube"
            )
    IOB = StringProperty(
            name="Select",
            default="",
            description="Object to use as insulator, 'voxelized'\n"
                        "before generating bolt (can be slow)"
            )
    # object_mangle_tools properties
    mangle_constraint_vector = BoolVectorProperty(
            name="Mangle Constraint",
            default=(True, True, True),
            subtype='XYZ',
            description="Constrains Mangle Direction"
            )
    mangle_random_magnitude = IntProperty(
            name="Mangle Severity",
            default=5,
            min=1, max=30,
            description="Severity of mangling"
            )
    mangle_name = StringProperty(
            name="Shape Key Name",
            default="mangle",
            description="Name given for mangled shape keys"
            )
    # unfold_transition properties
    unfold_arm_name = StringProperty(
            default=""
            )
    unfold_modo = EnumProperty(
            name="",
            items=[("cursor", "3D Cursor", "Use the Distance to 3D Cursor"),
                   ("weight", "Weight Map", "Use a Painted Weight map"),
                   ("index", "Mesh Indices", "Use Faces and Vertices index")],
            description="How to Sort Bones for animation", default="cursor"
            )
    unfold_flip = BoolProperty(
            name="Flipping Faces",
            default=False,
            description="Rotate faces around the Center and skip Scaling - "
                        "keep checked for both operators"
            )
    unfold_fold_duration = IntProperty(
            name="Total Time",
            min=5, soft_min=25,
            max=10000, soft_max=2500,
            default=200,
            description="Total animation length"
            )
    unfold_sca_time = IntProperty(
            name="Scale Time",
            min=1,
            max=5000, soft_max=500,
            default=10,
            description="Faces scaling time"
            )
    unfold_rot_time = IntProperty(
            name="Rotation Time",
            min=1, soft_min=5,
            max=5000, soft_max=500,
            default=15,
            description="Faces rotation time"
            )
    unfold_rot_max = IntProperty(
            name="Angle",
            min=-180,
            max=180,
            default=135,
            description="Faces rotation angle"
            )
    unfold_fold_noise = IntProperty(
            name="Noise",
            min=0,
            max=500, soft_max=50,
            default=0,
            description="Offset some faces animation"
            )
    unfold_bounce = FloatProperty(
            name="Bounce",
            min=0,
            max=10, soft_max=2.5,
            default=0,
            description="Add some bounce to rotation"
            )
    unfold_from_point = BoolProperty(
            name="Point",
            default=False,
            description="Scale faces from a Point instead of from an Edge"
            )
    unfold_wiggle_rot = BoolProperty(
            name="Wiggle",
            default=False,
            description="Use all Axis + Random Rotation instead of X Aligned"
            )
    # oscurart_constellation
    constellation_limit = FloatProperty(
            name="Inital Threshold",
            description="Edges will be created only if the distance\n"
                        "between vertices is smaller than this value\n"
                        "This is a starting value on Operator Invoke",
            default=2,
            min=0
            )


def register():
    bpy.utils.register_module(__name__)

    bpy.types.Scene.advanced_objects = PointerProperty(
                                            type=AdvancedObjProperties
                                            )

    # Add "Extras" menu to the "Add" menu
    bpy.types.INFO_MT_add.append(menu)
    try:
        bpy.types.VIEW3D_MT_AddMenu.append(menu)
    except:
        pass


def unregister():
    # Remove "Extras" menu from the "Add" menu.
    bpy.types.INFO_MT_add.remove(menu)
    try:
        bpy.types.VIEW3D_MT_AddMenu.remove(menu)
    except:
        pass

    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.advanced_objects

    # cleanup Easy Lattice Scene Property if it was created
    if hasattr(bpy.types.Scene, "activelatticeobject"):
        del bpy.types.Scene.activelatticeobject


if __name__ == "__main__":
    register()
