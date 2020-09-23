import bpy

def update(texcoat,tex_type,node):
    if (texcoat[tex_type][0] != node.image.filepath):
        node.image = bpy.data.images.load(texcoat[tex_type][0])
