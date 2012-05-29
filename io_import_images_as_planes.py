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

bl_info = {
    "name": "Import Images as Planes",
    "author": "Florian Meyer (tstscr)",
    "version": (1, 5),
    "blender": (2, 6, 3),
    "location": "File > Import > Images as Planes",
    "description": "Imports images and creates planes with the appropriate "
                   "aspect ratio. The images are mapped to the planes.",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"
                "Scripts/Add_Mesh/Planes_from_Images",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"
                   "func=detail&aid=21751",
    "category": "Import-Export"}

import bpy
from bpy.types import Operator
import mathutils
import os

from bpy.props import (BoolProperty,
                       EnumProperty,
                       IntProperty,
                       FloatProperty,
                       )

from bpy_extras.object_utils import AddObjectHelper, object_data_add
from bpy_extras.io_utils import ImportHelper
from bpy_extras.image_utils import load_image

# -----------------------------------------------------------------------------
# Global Vars

EXT_LIST = {
    'jpeg': ('jpeg', 'jpg', 'jpe'),
    'png': ('png', ),
    'tga': ('tga', 'tpic'),
    'tiff': ('tiff', 'tif'),
    'exr': ('exr', ),
    'hdr': ('hdr', ),
    'avi': ('avi', ),
    'mov': ('mov', 'qt'),
    'mp4': ('mp4', ),
    'ogg': ('ogg', 'ogv'),
    'bmp': ('bmp', 'dib'),
    'cin': ('cin', ),
    'dpx': ('dpx', ),
    'psd': ('psd', ),
    }

EXTENSIONS = [ext for ext_ls in EXT_LIST.values() for ext in ext_ls]


# -----------------------------------------------------------------------------
# misc
def set_image_options(self, image):
    image.use_premultiply = self.use_premultiply
    if self.relative:
        image.filepath = bpy.path.relpath(image.filepath)


def is_image_fn_any(fn):
    ext = os.path.splitext(fn)[1].lstrip(".").lower()
    return ext in EXTENSIONS


def is_image_fn_single(fn, ext_key):
    ext = os.path.splitext(fn)[1].lstrip(".").lower()
    return ext in EXT_LIST[ext_key]


def align_planes(self, planes):
    gap = self.align_offset
    offset = 0
    for i, plane in enumerate(planes):
        offset += (plane.dimensions.x / 2.0) + gap
        if i == 0:
            continue
        move_local = mathutils.Vector((offset, 0.0, 0.0))
        move_world = plane.location + move_local * plane.matrix_world.inverted()
        plane.location += move_world
        offset += (plane.dimensions.x / 2.0)


def generate_paths(self):
    directory, fn = os.path.split(self.filepath)

    if fn and not self.all_in_directory:
        # test for extension
        if not is_image_fn_any(fn):
            return [], directory

        return [self.filepath], directory

    if not fn or self.all_in_directory:
        imagepaths = []
        files_in_directory = os.listdir(directory)
        # clean files from nonimages
        files_in_directory = [fn for fn in files_in_directory
                              if is_image_fn_any(fn)]
        # clean from unwanted extensions
        if self.extension != "*":
            files_in_directory = [fn for fn in files_in_directory
                                  if is_image_fn_single(fn, self.extension)]
        # create paths
        for fn in files_in_directory:
            imagepaths.append(os.path.join(directory, fn))
        #print(imagepaths)
        return imagepaths, directory

# -----------------------------------------------------------------------------
# Blender
def create_image_textures(self, image):
    fn_full = os.path.normpath(bpy.path.abspath(image.filepath))

    # look for texture with importsettings
    for texture in bpy.data.textures:
        if texture.type == 'IMAGE':
            tex_img = texture.image
            if (tex_img is not None) and (tex_img.library is None):
                fn_tex_full = os.path.normpath(bpy.path.abspath(tex_img.filepath))
                if fn_full == fn_tex_full:
                    texture.use_alpha = self.use_transparency
                    return texture

    # if no texture is found: create one
    name_compat = bpy.path.display_name_from_filepath(image.filepath)
    texture = bpy.data.textures.new(name=name_compat, type='IMAGE')
    texture.image = image
    texture.use_alpha = self.use_transparency
    return texture


def create_material_for_texture(self, texture):
    # look for material with the needed texture
    for material in bpy.data.materials:
        slot = material.texture_slots[0]
        if slot and slot.texture == texture:
            if self.use_transparency:
                material.alpha = 0.0
                material.specular_alpha = 0.0
                slot.use_map_alpha = True
            else:
                material.alpha = 1.0
                material.specular_alpha = 1.0
                slot.use_map_alpha = False
            material.use_transparency = self.use_transparency
            material.transparency_method = self.transparency_method
            material.use_shadeless = self.use_shadeless
            material.use_transparent_shadows = self.use_transparent_shadows
            return material

    # if no material found: create one
    name_compat = bpy.path.display_name_from_filepath(texture.image.filepath)
    material = bpy.data.materials.new(name=name_compat)
    slot = material.texture_slots.add()
    slot.texture = texture
    slot.texture_coords = 'UV'
    if self.use_transparency:
        slot.use_map_alpha = True
        material.alpha = 0.0
        material.specular_alpha = 0.0
    else:
        material.alpha = 1.0
        material.specular_alpha = 1.0
        slot.use_map_alpha = False
    material.use_transparency = self.use_transparency
    material.transparency_method = self.transparency_method
    material.use_shadeless = self.use_shadeless
    material.use_transparent_shadows = self.use_transparent_shadows

    return material


def create_image_plane(self, context, material):
    engine = context.scene.render.engine
    if engine == 'BLENDER_RENDER':
        img = material.texture_slots[0].texture.image
    if engine == 'CYCLES':
        nodes = material.node_tree.nodes
        img_node = [node for node in nodes if node.type == 'TEX_IMAGE'][0]
        img = img_node.image
        
    px, py = img.size

    # can't load data
    if px == 0 or py == 0:
        px = py = 1

    x = px / py
    y = 1.0

    if self.use_dimension:
        x = (px * (1.0 / self.factor)) * 0.5
        y = (py * (1.0 / self.factor)) * 0.5

    verts = ((-x, -y, 0.0),
             (+x, -y, 0.0),
             (+x, +y, 0.0),
             (-x, +y, 0.0),
             )
    faces = ((0, 1, 2, 3), )

    mesh_data = bpy.data.meshes.new(img.name)
    mesh_data.from_pydata(verts, [], faces)
    mesh_data.update()
    object_data_add(context, mesh_data, operator=self)
    plane = context.scene.objects.active
    plane.data.uv_textures.new()
    plane.data.materials.append(material)
    plane.data.uv_textures[0].data[0].image = img

    material.game_settings.use_backface_culling = False
    material.game_settings.alpha_blend = 'ALPHA'
    return plane


# -----------------------------------------------------------------------------
# Cycles
def get_input_links(node, nodes, links):
    input_links = []
    for link in links:
        if link.to_node == node:
            input_links.append(link)
    
    sorted_links = []
    while input_links:
        for input in node.inputs:
            for link in input_links:
                if link.to_socket == input:
                    sorted_links.append(link)
                    input_links.remove(link)
    return sorted_links

def get_input_nodes(node, nodes, links):
    input_nodes = []
    input_links = get_input_links(node, nodes, links)
    for link in input_links:
        input_nodes.append(link.from_node)
    return input_nodes

def auto_align_nodes(node_tree):
    print('\nAligning Nodes')
    x_gap = 200
    y_gap = 100
    nodes = node_tree.nodes
    links = node_tree.links
    to_node = [node for node in nodes if node.type == 'OUTPUT_MATERIAL'][0]

    def align(to_node, nodes, links):
        from_nodes = get_input_nodes(to_node, nodes, links)
                
        for i, node in enumerate(from_nodes):
            node.location.x = to_node.location.x - x_gap
            node.location.y = to_node.location.y
            node.location.y -= i * y_gap
            node.location.y += (len(from_nodes)-1) * y_gap / (len(from_nodes))
            align(node, nodes, links)
    
    align(to_node, nodes, links)

def clean_node_tree(node_tree):
    nodes = node_tree.nodes
    for node in nodes:
        if not node.type == 'OUTPUT_MATERIAL':
            nodes.remove(node)
    return node_tree.nodes[0]

def create_cycles_material(self, image):
    name_compat = bpy.path.display_name_from_filepath(image.filepath)
    material = None
    for mat in bpy.data.materials:
        if mat.name == name_compat and self.overwrite_node_tree:
            material = mat
    if not material:
        material = bpy.data.materials.new(name=name_compat)
    
    material.use_nodes = True
    node_tree = material.node_tree
    out_node = clean_node_tree(node_tree)
    
    if self.shader == 'BSDF_DIFFUSE':
        bsdf_diffuse = node_tree.nodes.new('BSDF_DIFFUSE')
        tex_image = node_tree.nodes.new('TEX_IMAGE')
        tex_image.image = image
        tex_image.show_texture = True
        node_tree.links.new(out_node.inputs[0], bsdf_diffuse.outputs[0])
        node_tree.links.new(bsdf_diffuse.inputs[0], tex_image.outputs[0])

    if self.shader == 'EMISSION':
        emission = node_tree.nodes.new('EMISSION')
        tex_image = node_tree.nodes.new('TEX_IMAGE')
        tex_image.image = image
        tex_image.show_texture = True
        node_tree.links.new(out_node.inputs[0], emission.outputs[0])
        node_tree.links.new(emission.inputs[0], tex_image.outputs[0])

    if self.shader == 'BSDF_DIFFUSE + BSDF TRANSPARENT':
        bsdf_diffuse = node_tree.nodes.new('BSDF_DIFFUSE')
        bsdf_transparent = node_tree.nodes.new('BSDF_TRANSPARENT')
        mix_shader = node_tree.nodes.new('MIX_SHADER')
        tex_image = node_tree.nodes.new('TEX_IMAGE')
        tex_image.image = image
        tex_image.show_texture = True
        node_tree.links.new(out_node.inputs[0], mix_shader.outputs[0])
        node_tree.links.new(mix_shader.inputs[0], tex_image.outputs[1])
        node_tree.links.new(mix_shader.inputs[2], bsdf_diffuse.outputs[0])
        node_tree.links.new(mix_shader.inputs[1], bsdf_transparent.outputs[0])
        node_tree.links.new(bsdf_diffuse.inputs[0], tex_image.outputs[0])

    
    if self.shader == 'EMISSION + BSDF TRANSPARENT':
        emission = node_tree.nodes.new('EMISSION')
        bsdf_transparent = node_tree.nodes.new('BSDF_TRANSPARENT')
        mix_shader = node_tree.nodes.new('MIX_SHADER')
        tex_image = node_tree.nodes.new('TEX_IMAGE')
        tex_image.image = image
        tex_image.show_texture = True
        node_tree.links.new(out_node.inputs[0], mix_shader.outputs[0])
        node_tree.links.new(mix_shader.inputs[0], tex_image.outputs[1])
        node_tree.links.new(mix_shader.inputs[2], emission.outputs[0])
        node_tree.links.new(mix_shader.inputs[1], bsdf_transparent.outputs[0])
        node_tree.links.new(emission.inputs[0], tex_image.outputs[0])


    auto_align_nodes(node_tree)

    return material

# -----------------------------------------------------------------------------
# Main

def import_images(self, context):
    engine = context.scene.render.engine
    import_list, directory = generate_paths(self)
    images = []
    textures = []
    materials = []
    planes = []

    for path in import_list:
        images.append(load_image(path, directory))

    if engine == 'BLENDER_RENDER':
        for image in images:
            set_image_options(self, image)
            textures.append(create_image_textures(self, image))
    
        for texture in textures:
            materials.append(create_material_for_texture(self, texture))
    
        for material in materials:
            planes.append(create_image_plane(self, context, material))
    
    if engine == 'CYCLES':
        for image in images:
            materials.append(create_cycles_material(self, image))
            
        for material in materials:
            planes.append(create_image_plane(self, context, material))


    context.scene.update()
    if self.align:
        align_planes(self, planes)

    for plane in planes:
        plane.select = True

    self.report({'INFO'}, "Added %i Image Plane(s)" % len(planes))


# -----------------------------------------------------------------------------
# Operator

class IMPORT_OT_image_to_plane(Operator, ImportHelper, AddObjectHelper):
    """Create mesh plane(s) from image files """ \
    """with the appropiate aspect ratio"""

    bl_idname = "import.image_to_plane"
    bl_label = "Import Images as Planes"
    bl_options = {'REGISTER', 'UNDO'}

    # -------
    # Options
    all_in_directory = BoolProperty(
            name="All in directory",
            description=("Import all image files (of the selected type) "
                         "in this directory"),
            default=False,
            )
    align = BoolProperty(
            name='Align Planes',
            description='Create Planes in a row',
            default=True,
            )
    align_offset = FloatProperty(
            name='Offset',
            description='Space between Planes',
            min=0,
            soft_min=0,
            default=0.1,
            )
    extension = EnumProperty(
            name="Extension",
            description="Only import files of this type",
            items=(
            ('*', 'All image formats',
                'Import all know image (or movie) formats.'),
            ('jpeg', 'JPEG (.jpg, .jpeg, .jpe)',
                'Joint Photographic Experts Group'),
            ('png', 'PNG (.png)', 'Portable Network Graphics'),
            ('tga', 'Truevision TGA (.tga, tpic)', ''),
            ('tiff', 'TIFF (.tif, .tiff)', 'Tagged Image File Format'),
            ('exr', 'OpenEXR (.exr)', 'OpenEXR HDR imaging image file format'),
            ('hdr', 'Radiance HDR (.hdr, .pic)', ''),
            ('avi', 'AVI (.avi)', 'Audio Video Interleave'),
            ('mov', 'QuickTime (.mov, .qt)', ''),
            ('mp4', 'MPEG-4 (.mp4)', ' MPEG-4 Part 14'),
            ('ogg', 'OGG Theora (.ogg, .ogv)', ''),
            ('bmp', 'BMP (.bmp, .dib)', 'Windows Bitmap'),
            ('cin', 'CIN (.cin)', ''),
            ('dpx', 'DPX (.dpx)', 'DPX (Digital Picture Exchange)'),
            ('psd', 'PSD (.psd)', 'Photoshop Document')),
            )
    use_dimension = BoolProperty(name="Use image dimensions",
            description="Use the images pixels to derive planes size in Blender Units",
            default=False,
            )
    factor = IntProperty(name="Pixels/BU",
            description="Number of pixels per Blenderunit",
            min=1,
            default=500,
            )

    # ----------------
    # Material Options
    use_shadeless = BoolProperty(
            name="Shadeless",
            description="Set material to shadeless",
            default=False,
            )
    use_transparency = BoolProperty(
            name="Use alpha",
            description="Use alphachannel for transparency",
            default=False,
            )

    transparency_method = EnumProperty(
            name="Transp. Method",
            description="Transparency Method",
            items=(
            ('Z_TRANSPARENCY',
            'Z Transparency',
            'Use alpha buffer for transparent faces'),
            ('RAYTRACE',
            'Raytrace',
            'Use raytracing for transparent refraction rendering.')),
            )
    use_transparent_shadows = BoolProperty(
            name="Receive Transparent",
            description="Set material to receive transparent shadows",
            default=False,
            )

    shader = EnumProperty(
            name="Shader",
            description="Shader",
            items=(
            ('BSDF_DIFFUSE',
            'Diffuse',
            'Diffuse Shader'),
            ('EMISSION',
            'Emission',
            'Emission Shader'),
            ('BSDF_DIFFUSE + BSDF TRANSPARENT',
            'Diffuse + Transparent',
            'Diffuse + Transparent Mix'),
            ('EMISSION + BSDF TRANSPARENT',
            'Emission + Transparent',
            'Emission + Transparent Mix')),
            )
    overwrite_node_tree = BoolProperty(
            name="overwrite Material",
            description="overwrite existing Material with new nodetree (based on material name)",
            default=True,
            )
    
    # -------------
    # Image Options
    use_premultiply = BoolProperty(name="Premultiply",
                                description="Premultiply image",
                                default=False)

    relative = BoolProperty(
            name="Relative",
            description="Apply relative paths",
            default=True,
            )

    def draw(self, context):
        engine = context.scene.render.engine
        layout = self.layout

        box = layout.box()
        box.label("Import Options:", icon='FILTER')
        box.prop(self, "all_in_directory")
        box.prop(self, "extension", icon='FILE_IMAGE')
        box.prop(self, "align")
        box.prop(self, "align_offset")

        row = box.row()
        row.active = bpy.data.is_saved
        row.prop(self, "relative")

        if engine == 'BLENDER_RENDER':
            box = layout.box()
            box.label("Material Settings: (Blender)", icon='MATERIAL')
            box.prop(self, "use_shadeless")
            box.prop(self, "use_transparency")
            box.prop(self, "use_premultiply")
            box.prop(self, "transparency_method", expand=True)
            box.prop(self, "use_transparent_shadows")

        if engine == 'CYCLES':
            box = layout.box()
            box.label("Material Settings: (Cycles)", icon='MATERIAL')
            box.prop(self, 'shader', expand = True)
            box.prop(self, 'overwrite_node_tree')
            
        box = layout.box()
        box.label("Plane dimensions:", icon='ARROW_LEFTRIGHT')
        box.prop(self, "use_dimension")
        box.prop(self, "factor", expand=True)

    def execute(self, context):

        if not bpy.data.is_saved:
            self.relative = False

        # the add utils don't work in this case
        # because many objects are added
        # disable relevant things beforehand
        editmode = context.user_preferences.edit.use_enter_edit_mode
        context.user_preferences.edit.use_enter_edit_mode = False
        if context.active_object\
        and context.active_object.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')

        import_images(self, context)

        context.user_preferences.edit.use_enter_edit_mode = editmode
        return {'FINISHED'}


# -----------------------------------------------------------------------------
# Register


def import_images_button(self, context):
    self.layout.operator(IMPORT_OT_image_to_plane.bl_idname,
                         text="Images as Planes",
                         icon='PLUGIN')


def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(import_images_button)


def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_import.remove(import_images_button)

if __name__ == '__main__':
    register()