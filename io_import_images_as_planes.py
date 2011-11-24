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
    "version": (1, 0),
    "blender": (2, 5, 7),
    "api": 35622,
    "location": "File > Import > Images as Planes",
    "description": "Imports images and creates planes with the appropriate aspect ratio. "\
        "The images are mapped to the planes.",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"\
        "Scripts/Add_Mesh/Planes_from_Images",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=21751",
    "category": "Import-Export"}

import bpy, os, mathutils
from bpy.props import *
from add_utils import *
from bpy_extras.io_utils import ImportHelper
from bpy_extras.image_utils import load_image

## GLOBAL VARS ##
EXT_LIST = {
    'jpeg': ['jpeg', 'jpg', 'jpe'],
    'png': ['png'],
    'tga': ['tga', 'tpic'],
    'tiff': ['tiff', 'tif'],
    'exr': ['exr'],
    'hdr': ['hdr'],
    'avi': ['avi'],
    'mov': ['mov', 'qt'],
    'mp4': ['mp4'],
    'ogg': ['ogg', 'ogv'],
    'bmp': ['bmp', 'dib'],
    'cin': ['cin'],
    'dpx': ['dpx'],
    'psd': ['psd']}
EXT_VALS = [val for val in EXT_LIST.values()]
EXTENSIONS = []
for i in EXT_VALS:
    EXTENSIONS.extend(i)
    
## FUNCTIONS ##
def set_image_options(self, image):
    image.use_premultiply = self.use_premultiply
    
def create_image_textures(self, image):
    #look for texture with importsettings
    for texture in bpy.data.textures:
        if texture.type == 'IMAGE'\
        and texture.image\
        and texture.image.filepath == image.filepath:
            if self.use_transparency:
                texture.use_alpha = True
            else:
                texture.use_alpha = False
            return texture
    
    #if no texture is found: create one
    texture = bpy.data.textures.new(name=os.path.split(image.filepath)[1],
                                    type='IMAGE')
    texture.image = image
    if self.use_transparency:
        texture.use_alpha = True
    else:
        texture.use_alpha = False
    return texture

def create_material_for_texture(self, texture):
    #look for material with the needed texture
    for material in bpy.data.materials:
        if material.texture_slots[0]\
        and material.texture_slots[0].texture == texture:
            if self.use_transparency:
                material.alpha = 0
                material.specular_alpha = 0
                material.texture_slots[0].use_map_alpha = True
            else:
                material.alpha = 1
                material.specular_alpha = 1
                material.texture_slots[0].use_map_alpha = False
            material.use_transparency = self.use_transparency
            material.transparency_method = self.transparency_method
            material.use_shadeless = self.use_shadeless
            return material
            
    # if no material found: create one
    material = bpy.data.materials.new(name=os.path.split(texture.image.filepath)[1])
    slot = material.texture_slots.add()
    slot.texture = texture
    slot.texture_coords = 'UV'
    if self.use_transparency:
        slot.use_map_alpha = True
        material.alpha = 0
        material.specular_alpha = 0
    else:
        material.alpha = 1
        material.specular_alpha = 1
        slot.use_map_alpha = False
    material.use_transparency = self.use_transparency
    material.transparency_method = self.transparency_method
    material.use_shadeless = self.use_shadeless
    
    return material

def create_image_plane(self, context, material):
    img = material.texture_slots[0].texture.image
    px, py = img.size

    # can't load data
    if px == 0 or py == 0:
        px = py = 1

    x = px / py
    y = 1.0

    if self.use_dimension:
        x = (px * (1.0 / self.factor)) * 0.5
        y = (py * (1.0 / self.factor)) * 0.5

    verts = [(-x, -y, 0),
             (x, -y, 0),
             (x, y, 0),
             (-x, y, 0)]
    faces = [[0, 1, 2, 3]]

    mesh_data = bpy.data.meshes.new(img.name)
    mesh_data.from_pydata(verts, [], faces)
    mesh_data.update()
    add_object_data(context, mesh_data, operator=self)
    plane = context.scene.objects.active
    plane.data.uv_textures.new()
    plane.data.materials.append(material)
    plane.data.uv_textures[0].data[0].image = img

    material.game_settings.use_backface_culling = False
    material.game_settings.alpha_blend = 'ALPHA'
    return plane

def generate_paths(self):
    directory, file = os.path.split(self.filepath)

    if file and not self.all_in_directory:
        #test for extension
        if not os.path.splitext(file)[1].lstrip('.').lower() in EXTENSIONS:
            return [], directory
        
        return [self.filepath], directory
        
    if not file or self.all_in_directory:
        imagepaths = []
        files_in_directory = os.listdir(directory)
        #clean files from nonimages
        files_in_directory = [file for file in files_in_directory
                              if os.path.splitext(file)[1].lstrip('.').lower()
                              in EXTENSIONS]
        #clean from unwanted extensions
        if self.extension != '*':
            files_in_directory = [file for file in files_in_directory
                                  if os.path.splitext(file)[1].lstrip('.').lower()
                                  in EXT_LIST[self.extension]]
        #create paths
        for file in files_in_directory:
            imagepaths.append(os.path.join(directory, file))
            
        #print(imagepaths)
        return imagepaths, directory

def align_planes(self, planes):
    gap = self.align_offset
    offset = 0
    for i, plane in enumerate(planes):
        offset += (plane.dimensions.x / 2) + gap
        if i == 0: continue
        move_local = mathutils.Vector((offset, 0, 0))
        move_world = plane.location + move_local * plane.matrix_world.inverted()
        plane.location += move_world
        offset += (plane.dimensions.x / 2)
        
##### MAIN #####
def import_images(self, context):
    import_list, directory = generate_paths(self)
    images = []
    textures = []
    materials = []
    planes = []
    
    for path in import_list:
        images.append(load_image(path, directory))

    for image in images:
        set_image_options(self, image)
        textures.append(create_image_textures(self, image))

    for texture in textures:
        materials.append(create_material_for_texture(self, texture))

    for material in materials:
        plane = create_image_plane(self, context, material)
        planes.append(plane)
        
    context.scene.update()
    if self.align:
        align_planes(self, planes)
        
    for plane in planes:
        plane.select = True
        
    self.report(type={'INFO'},
                message='Added %i Image Plane(s)' %len(planes))

##### OPERATOR #####
class IMPORT_OT_image_to_plane(bpy.types.Operator, ImportHelper, AddObjectHelper):
    ''''''
    bl_idname = "import.image_to_plane"
    bl_label = "Import Images as Planes"
    bl_description = "Create mesh plane(s) from image files" \
                     " with the appropiate aspect ratio"
    bl_options = {'REGISTER', 'UNDO'}

    ## OPTIONS ##
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
    extEnum = (
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
        ('psd', 'PSD (.psd)', 'Photoshop Document'),
        )
    extension = EnumProperty(
            name="Extension",
            description="Only import files of this type",
            items=extEnum)
    use_dimension = BoolProperty(name="Use image dimensions",
            description="Use the images pixels to derive the size of the plane",
            default=False)
    factor = IntProperty(name="Pixels/BU",
            description="Number of pixels per Blenderunit",
            min=1,
            default=500,
            )

    ## MATERIAL OPTIONS ##
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
    tEnum = (
            ('Z_TRANSPARENCY',
            'Z Transparency',
            'Use alpha buffer for transparent faces'),
            ('RAYTRACE',
            'Raytrace',
            'Use raytracing for transparent refraction rendering.'))
    transparency_method = EnumProperty(
            name="Transp. Method",
            description="Transparency Method",
            items=tEnum,
            )

    ## IMAGE OPTIONS ##
    use_premultiply = BoolProperty(name="Premultiply",
                                description="Premultiply image",
                                default=False)

    ## DRAW ##
    def draw(self, context):
        layout = self.layout
        
        box = layout.box()
        box.label('Import Options:', icon='FILTER')
        box.prop(self, 'all_in_directory')
        box.prop(self, 'extension', icon='FILE_IMAGE')
        box.prop(self, 'align')
        box.prop(self, 'align_offset')
        
        box = layout.box()
        box.label('Material mappings:', icon='MATERIAL')
        box.prop(self, 'use_shadeless')
        box.prop(self, 'use_transparency')
        box.prop(self, 'use_premultiply')
        box.prop(self, 'transparency_method', expand=True)
        
        box = layout.box()
        box.label('Plane dimensions:', icon='ARROW_LEFTRIGHT')
        box.prop(self, 'use_dimension')
        box.prop(self, 'factor', expand=True)


    ## EXECUTE ##
    def execute(self, context):
        #the add utils don't work in this case
        #because many objects are added
        #disable relevant things beforehand
        editmode = context.user_preferences.edit.use_enter_edit_mode
        context.user_preferences.edit.use_enter_edit_mode = False
        if context.active_object\
        and context.active_object.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        import_images(self, context)
        
        context.user_preferences.edit.use_enter_edit_mode = editmode
        return {'FINISHED'}




##### REGISTER #####

def import_images_button(self, context):
    self.layout.operator(IMPORT_OT_image_to_plane.bl_idname, text="Images as Planes", icon='PLUGIN')

def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_import.append(import_images_button)
def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_import.remove(import_images_button)
if __name__ == '__main__':
    register()
