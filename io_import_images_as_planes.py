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

bl_addon_info = {
    "name": "Import: Images as Planes",
    "author": "Florian Meyer (testscreenings)",
    "version": "0.7",
    "blender": (2, 5, 3),
    "location": "File > Import > Images as Planes",
    "description": "Imports images and creates planes with the appropiate aspect ratio. The images are mapped to the planes.",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/Add_Mesh/Planes_from_Images",
    "tracker_url": "https://projects.blender.org/tracker/index.php?func=detail&aid=21751&group_id=153&atid=469",
    "category": "Import/Export"}

"""
This script imports images and creates Planes with them as textures.
At the moment the naming for objects, materials, textures and meshes
is derived from the imagename.

One can either import a single image, or all images in one directory.
When imporing a directory one can either check the checkbox or leave
the filename empty.

As a bonus one can choose to import images of only one type.
Atm this is the list of possible extensions:
extList =
    ('jpeg', 'jpg', 'png', 'tga', 'tiff', 'tif', 'exr',
    'hdr', 'avi', 'mov', 'mp4', 'ogg', 'bmp', 'cin', 'dpx', 'psd')

If someone knows a better way of telling if a file is an image which
Blender can read, please tell so ;)

when importing images that are allready referenced they are not
reimported but the old ones reused as not to clutter the materials,
textures and image lists.
Instead the plane gets linked against an existing material.

If one reimports images but chooses different material/texture mapping
new materials are created.
So one doesn't has to go through everything if one decides differently
after importing 236 images.

It also has an option to translate pixeldimensions into Blenderunits.
"""

import bpy
from bpy.props import *
from os import listdir
from mathutils import Vector


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


# Apply view rotation to objects if "Align To" for new objects
# was set to "VIEW" in the User Preference.
def apply_view_rotation(ob):
    context = bpy.context
    align = bpy.context.user_preferences.edit.object_align

    if (context.space_data.type == 'VIEW_3D'
        and align == 'VIEW'):
            view3d = context.space_data
            region = view3d.region_3d
            viewMatrix = region.view_matrix
            rot = viewMatrix.rotation_part()
            ob.rotation_euler = rot.invert().to_euler()


# Create plane mesh
def createPlaneMesh(dimension, img):
    # x is the x-aspectRatio.
    x = img.size[0] / img.size[1]
    y = 1

    if dimension[0]:
        x = (img.size[0] * (1.0 / dimension[1])) * 0.5
        y = (img.size[1] * (1.0 / dimension[1])) * 0.5

    verts = []
    faces = []

    v1 = (-x, -y, 0)
    v2 = (x, -y, 0)
    v3 = (x, y, 0)
    v4 = (-x, y, 0)

    verts.append(v1)
    verts.append(v2)
    verts.append(v3)
    verts.append(v4)

    faces.append([0, 1, 2, 3])

    return verts, faces


# Create plane object
def createPlaneObj(img, dimension):
    scene = bpy.context.scene

    verts, faces = createPlaneMesh(dimension, img)

    me = bpy.data.meshes.new(img.name)
    me.from_pydata(verts, [], faces)
    me.update()

    plane = bpy.data.objects.new(img.name, me)
    plane.data.uv_textures.new()

    scene.objects.link(plane)
    plane.location = scene.cursor_location
    apply_view_rotation(plane)

    return plane


# Check if a file extension matches any
# valid (i.e. recognized) image/movie format.
def isImageFile(extension):
    for ext, ext_list in EXT_LIST.items():
        if extension in ext_list:
            return True

    return False


# Get imagepaths from directory
def getImageFilesInDirectory(directory, extension):
    import os

    # Get all files in the directory.
    allFiles = listdir(directory)
    allImages = []

    extensions = []

    # Import all images files?
    if extension == '*':
        all = True

    else:
        all = False
        # Get the possible extensions
        extensions = EXT_LIST[extension]

    # Put all image files in the list.
    for file in allFiles:
        # Get the file extension (includes the ".")
        e = os.path.splitext(file)[1]

        # Separate by "." and get the last list-entry.
        e = e.rpartition(".")[-1]

        # Convert to lower case
        e = e.lower()

        if (e in extensions
            or (all and isImageFile(e))):
            allImages.append(file)

    return allImages


# Get image datablock from the (image's) filepath.
def getImage(path):
    img = []

    # Check every Image if it is already there.
    for image in bpy.data.images:
        # If image with same path exists take that one.
        if image.filepath == path:
            img = image

    # Else create new Image and load from path.
    if not img:
        name = path.rpartition('\\')[2].rpartition('.')[0]
        img = bpy.data.images.new(name)
        img.source = 'FILE'
        img.filepath = path

    return img


# Create/get Material
def getMaterial(tex, mapping):
    mat = []

    # Check all existing materials.
    for material in bpy.data.materials:
        # If a material with name and mapping
        # texture with image exists, take that one...
        if (material.name == tex.image.name
        and tex.name in material.texture_slots
        and material.mapping == mapping):
            mat = material

    # ... otherwise create new one and apply mapping.
    if not mat:
        mat = bpy.data.materials.new(name=tex.name)
        mat.add_texture(tex, texture_coordinates='UV', map_to='COLOR')
        mat.mapping = mapping
        mat.name = tex.name

    return mat


# Create/get Texture
def getTexture(path, img):
    tex = []

    # Check all existing textures.
    for texture in bpy.data.textures:
        # If an (image)texture with image exists, take that one...
        if (texture.type == 'IMAGE'
            and texture.image
            and texture.image.filepath == path):
            tex = texture

    # ... otherwise create a new one and apply mapping.
    if not tex:
        name = path.rpartition('\\')[2].rpartition('.')[0]
        tex = bpy.data.textures.new(name=name)
        tex.type = 'IMAGE'
        tex = tex.recast_type()
        tex.image = img

    return tex


# Custom material property - get
def mapget(self):
    """Custom property of the images_as_planes addon."""
    mapping = []
    mapping.append(self.use_shadeless)
    mapping.append(self.use_transparency)
    mapping.append(self.alpha)
    mapping.append(self.specular_alpha)
    mapping.append(self.transparency_method)

    if (self.texture_slots[0]
        and self.texture_slots[0].texture.type == 'IMAGE'
        and self.texture_slots[0].texture.image):
        mapping.append(self.texture_slots[0].texture.image.use_premultiply)

    else:
        mapping.append("no image")

    return mapping


# Custom material property - set
def mapset(self, value):
    self.use_shadeless = value[0]
    self.use_transparency = value[1]
    self.alpha = float(value[2])
    self.specular_alpha = float(value[3])
    self.transparency_method = value[4]

    if (self.texture_slots[0]
        and self.texture_slots[0].texture.type == 'IMAGE'
        and self.texture_slots[0].texture.image):
        self.texture_slots[0].texture.image.use_premultiply = value[5]
    if self.alpha:
        self.texture_slots[0].use_map_alpha=True


bpy.types.Material.mapping = property(mapget, mapset)


def main(filePath, options, mapping, dimension):
    images = []
    scene = bpy.context.scene

    # If "Create from Directory" (no filepath or checkbox) ####
    if options['dir'] or not filePath[1]:
        imageFiles = getImageFilesInDirectory(filePath[2], options['ext'])

        # Check if images are loaded and put them in the list.
        for imageFile in imageFiles:
            img = getImage(str(filePath[2]) + "\\" + str(imageFile))
            images.append(img)

        # Deselect all objects.
        bpy.ops.object.select_all(action='DESELECT')

        # Assign/get all things.
        for img in images:
            # Create/get Texture
            tex = getTexture(img.filepath, img)

            # Create/get Material
            mat = getMaterial(tex, mapping)

            # Create Plane
            plane = createPlaneObj(img, dimension)

            # Assign Material
            plane.data.add_material(mat)

            # Put Image into  UVTextureLayer
            plane.data.uv_textures[0].data[0].image = img
            plane.data.uv_textures[0].data[0].use_image = True
            plane.data.uv_textures[0].data[0].blend_type = 'ALPHA'
            plane.data.uv_textures[0].data[0].use_twoside = True

            plane.select = True
            scene.objects.active = plane

    # If "Create Single Plane" (filepath and is image)
    else:
        # Deselect all objects.
        bpy.ops.object.select_all(action='DESELECT')

        # Check if image is loaded.
        img = getImage(filePath[0])

        # Create/get Texture
        tex = getTexture(filePath[0], img)

        # Create/get Material
        mat = getMaterial(tex, mapping)

        # Create Plane
        plane = createPlaneObj(img, dimension)

        # Assign Material
        plane.data.add_material(mat)

        # Put image into UVTextureLayer
        plane.data.uv_textures[0].data[0].image = img
        plane.data.uv_textures[0].data[0].use_image = True
        plane.data.uv_textures[0].data[0].blend_type = 'ALPHA'
        plane.data.uv_textures[0].data[0].use_twoside = True

        plane.select = True
        scene.objects.active = plane


# Operator
class ImportImagesAsPlanes(bpy.types.Operator):
    ''''''
    bl_idname = "import.images_as_planes"
    bl_label = "Import Images as Planes"
    bl_description = "Create mesh plane(s) from image files" \
        " with the appropiate aspect ratio."
    bl_options = {'REGISTER', 'UNDO'}

    filepath = StringProperty(name="File Path",
        description="Filepath used for importing the file",
        maxlen=1024,
        default="")
    filename = StringProperty(name="File Name",
        description="Name of the file.")
    directory = StringProperty(name="Directory",
        description="Directory of the file.")
    fromDirectory = BoolProperty(name="All in directory",
        description="Import all image files (of the selected type)" \
            " in this directory.",
        default=False)

    extEnum = [
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
        ('psd', 'PSD (.psd)', 'Photoshop Document')]
    extension = EnumProperty(name="Extension",
        description="Only import files of this type.",
        items=extEnum)

    shadeless = BoolProperty(name="Shadeless",
        description="Set material to shadeless",
        default=False)
    transp = BoolProperty(name="Use alpha",
        description="Use alphachannel for transparency.",
        default=False)
    premultiply = BoolProperty(name="Premultiply",
        description="Premultiply image",
        default=False)

    tEnum = [
        ('Z_TRANSPARENCY',
            'Z Transparency',
            'Use alpha buffer for transparent faces'),
        ('RAYTRACE',
            'Raytrace',
            'Use raytracing for transparent refraction rendering.')]
    transp_method = EnumProperty(name="Transp. Method",
        description="Transparency Method",
        items=tEnum)
    useDim = BoolProperty(name="Use image dimensions",
        description="Use the images pixels to derive the size of the plane.",
        default=False)
    factor = IntProperty(name="Pixels/BU",
        description="Number of pixels per Blenderunit.",
        min=1,
        default=500)

    def draw(self, context):
        props = self.properties
        layout = self.layout
        box = layout.box()
        box.label('Filter:', icon='FILTER')
        box.prop(props, 'fromDirectory')
        box.prop(props, 'extension', icon='FILE_IMAGE')
        box = layout.box()
        box.label('Material mappings:', icon='MATERIAL')
        box.prop(props, 'use_shadeless')
        box.prop(props, 'transp')
        box.prop(props, 'use_premultiply')
        box.prop(props, 'transp_method', expand=True)
        box = layout.box()
        box.label('Plane dimensions:', icon='ARROW_LEFTRIGHT')
        box.prop(props, 'useDim')
        box.prop(props, 'factor', expand=True)

    def execute(self, context):
        # File Path
        filepath = self.properties.filepath
        filename = self.properties.filename
        directory = self.properties.directory
        filePath = (filepath, filename, directory)

        # General Options
        fromDirectory = self.properties.fromDirectory
        extension = self.properties.extension
        options = {'dir': fromDirectory, 'ext': extension}

        # Mapping
        alphavalue = 1
        transp = self.properties.transp
        if transp:
            alphavalue = 0

        shadeless = self.properties.use_shadeless
        transp_method = self.properties.transp_method
        premultiply = self.properties.use_premultiply

        mapping = ([shadeless,
                    transp,
                    alphavalue,
                    alphavalue,
                    transp_method,
                    premultiply])

        # Use Pixelsdimensions
        useDim = self.properties.useDim
        factor = self.properties.factor
        dimension = (useDim, factor)

        # Call Main Function
        main(filePath, options, mapping, dimension)

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = bpy.context.manager
        wm.add_fileselect(self)

        return {'RUNNING_MODAL'}


# Registering / Unregister
def menu_func(self, context):
    self.layout.operator(ImportImagesAsPlanes.bl_idname, text="Images as Planes", icon='PLUGIN')


def register():
    bpy.types.INFO_MT_file_import.append(menu_func)


def unregister():
    bpy.types.INFO_MT_file_import.remove(menu_func)


if __name__ == "__main__":
    register()
