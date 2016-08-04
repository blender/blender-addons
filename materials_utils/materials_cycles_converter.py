# gpl: author Silvio Falcinelli. Fixes by angavrilov and others.
# special thanks to user blenderartists.org cmomoney
# -*- coding: utf-8 -*-

import bpy
import os
from os import path as os_path
from bpy.types import Operator
from bpy.props import (
            BoolProperty,
            EnumProperty,
            )
from .warning_messages_utils import (
            warning_messages,
            c_is_cycles_addon_enabled,
            c_data_has_materials,
            collect_report,
            )

# -----------------------------------------------------------------------------
# Globals #

# switch for operator's function called after AutoNodeInitiate
CHECK_AUTONODE = False

# set the node color for baked textures (default greenish)
NODE_COLOR = (0.32, 0.75, 0.32)

# -----------------------------------------------------------------------------
# Functions #


def AutoNodeSwitch(renderer="CYCLES", switch="OFF", operator=None):
    mats = bpy.data.materials
    use_nodes = (True if switch in ("ON") else False)
    warn_message = ('BI_SW_NODES_ON' if switch in ("ON") else
                    'BI_SW_NODES_OFF')
    warn_message_2 = ('CYC_SW_NODES_ON' if switch in ("ON") else
                      'CYC_SW_NODES_OFF')
    for cmat in mats:
        cmat.use_nodes = use_nodes
    renders = ('CYCLES' if renderer and renderer == "CYCLES" else
               'BLENDER_RENDER')
    bpy.context.scene.render.engine = renders
    if operator:
        warning_messages(operator, (warn_message_2 if renders in ('CYCLES') else
                                    warn_message))


def SetFakeUserTex():
    images = bpy.data.images
    for image in images:
        has_user = getattr(image, "users", -1)
        image_name = getattr(image, "name", "NONAME")

        if has_user == 0:
            image.use_fake_user = True
            collect_report("INFO: Set fake user for unused image: " + image_name)


def BakingText(tex, mode, tex_type=None):
    collect_report("INFO: start bake texture named: " + tex.name)
    saved_img_path = None
    bpy.ops.object.mode_set(mode='OBJECT')
    sc = bpy.context.scene
    tmat = ''
    img = ''
    Robj = bpy.context.active_object
    for n in bpy.data.materials:
        if n.name == 'TMP_BAKING':
            tmat = n
    if not tmat:
        tmat = bpy.data.materials.new('TMP_BAKING')
        tmat.name = "TMP_BAKING"

    bpy.ops.mesh.primitive_plane_add()
    tm = bpy.context.active_object
    tm.name = "TMP_BAKING"
    tm.data.name = "TMP_BAKING"
    bpy.ops.object.select_pattern(extend=False, pattern="TMP_BAKING",
                                  case_sensitive=False)
    sc.objects.active = tm
    bpy.context.scene.render.engine = 'BLENDER_RENDER'
    tm.data.materials.append(tmat)
    if len(tmat.texture_slots.items()) == 0:
        tmat.texture_slots.add()
    tmat.texture_slots[0].texture_coords = 'UV'
    tmat.texture_slots[0].use_map_alpha = True
    tmat.texture_slots[0].texture = tex.texture
    tmat.texture_slots[0].use_map_alpha = True
    tmat.texture_slots[0].use_map_color_diffuse = False
    tmat.use_transparency = True
    tmat.alpha = 0
    tmat.use_nodes = False
    tmat.diffuse_color = 1, 1, 1
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.unwrap()

    # clean up temporary baking images if any
    for n in bpy.data.images:
        if n.name == 'TMP_BAKING':
            n.user_clear()
            bpy.data.images.remove(n)

    if mode == "ALPHA" and tex.texture.type == 'IMAGE':
        sizeX = tex.texture.image.size[0]
        sizeY = tex.texture.image.size[1]
    else:
        bake_size = (int(sc.mat_specials.img_bake_size) if
                     sc.mat_specials.img_bake_size else 1024)
        sizeX = bake_size
        sizeY = bake_size

    bpy.ops.image.new(name="TMP_BAKING", width=sizeX, height=sizeY,
                      color=(0.0, 0.0, 0.0, 1.0), alpha=True, float=False)
    bpy.data.screens['UV Editing'].areas[1].spaces[0].image = bpy.data.images["TMP_BAKING"]
    sc.render.engine = 'BLENDER_RENDER'
    img = bpy.data.images["TMP_BAKING"]
    img = bpy.data.images.get("TMP_BAKING")
    img.file_format = ("JPEG" if not mode == "ALPHA" else "PNG")

    paths = bpy.path.abspath(sc.mat_specials.conv_path)
    tex_name = getattr(getattr(tex.texture, "image", None), "name", None)
    texture_name = (tex_name.rpartition(".")[0] if tex_name else tex.texture.name)
    new_tex_name = "baked"
    name_append = ("_BAKING" if mode == "ALPHA" and
                   tex.texture.type == 'IMAGE' else "_PTEXT")
    new_appendix = (".jpg" if not mode == "ALPHA" else ".png")

    if name_append in texture_name:
        new_tex_name = texture_name
    elif tex_type:
        new_tex_name = tex_type + name_append
    else:
        new_tex_name = texture_name + name_append

    img.filepath_raw = paths + new_tex_name + new_appendix
    saved_img_path = img.filepath_raw

    sc.render.bake_type = 'ALPHA'
    sc.render.use_bake_selected_to_active = True
    sc.render.use_bake_clear = True

    # try to bake if it fails give report
    try:
        bpy.ops.object.bake_image()
        img.save()
    except:
        # no return value so the image loading is skipped
        saved_img_path = None
        collect_report("ERROR: Baking could not be completed. "
                       "Check System Console for info")

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.delete()
    bpy.ops.object.select_pattern(extend=False, pattern=Robj.name, case_sensitive=False)
    sc.objects.active = Robj
    img.user_clear()
    bpy.data.images.remove(img)

    if tmat.users == 0:
        bpy.data.materials.remove(tmat)

    if saved_img_path:
        collect_report("________________________________________")
        return saved_img_path


def AutoNodeInitiate(active=False, operator=None):
    # Checks with bpy.ops.material.check_converter_path
    # if it's possible to write in the output path
    # if it passes procedes with calling AutoNode

    # if CheckImagePath(operator):
    check_path = bpy.ops.material.check_converter_path()

    global CHECK_AUTONODE

    if 'FINISHED' in check_path:
        sc = bpy.context.scene
        CHECK_AUTONODE = True
        collect_report("________________________________________", True, False)
        AutoNode(active, operator)
        if sc.mat_specials.SET_FAKE_USER:
            SetFakeUserTex()
        collect_report("Conversion finished !", False, True)
    else:
        warning_messages(operator, 'DIR_PATH_CONVERT')


def AutoNode(active=False, operator=None):
    global CHECK_AUTONODE
    sc = bpy.context.scene
    if active:
        # fix for empty slots by angavrilov
        mats = [slot.material for slot in bpy.context.active_object.material_slots if
                slot.material]
    else:
        mats = bpy.data.materials

    # No Materials for the chosen action - abort
    if not mats:
        CHECK_AUTONODE = False
        if operator:
            if active:
                act_obj = bpy.context.active_object
                warning_messages(operator, 'CONV_NO_OBJ_MAT', act_obj.name)
            else:
                warning_messages(operator, 'CONV_NO_SC_MAT')
        return

    for cmat in mats:
        # check for empty material (it will fall through the first check)
        test_empty = getattr(cmat, "name", None)
        if test_empty is None:
            collect_report("An empty material was hit, skipping")
            continue

        cmat.use_nodes = True
        TreeNodes = cmat.node_tree
        links = TreeNodes.links

        # Don't alter nodes of locked materials
        locked = False
        for n in TreeNodes.nodes:
            if n.type == 'ShaderNodeOutputMaterial':
                if n.label == 'Locked':
                    locked = True
                    break

        if not locked:
            # Convert this material from non-nodes to Cycles nodes
            shader = ''
            shtsl = ''
            Add_Emission = ''
            Add_Translucent = ''
            Mix_Alpha = ''
            sT = False

            for n in TreeNodes.nodes:
                TreeNodes.nodes.remove(n)

            # Starting point is diffuse BSDF and output material
            shader = TreeNodes.nodes.new('ShaderNodeBsdfDiffuse')
            shader.location = 0, 470
            shout = TreeNodes.nodes.new('ShaderNodeOutputMaterial')
            shout.location = 200, 400
            links.new(shader.outputs[0], shout.inputs[0])

            cmat_is_transp = cmat.use_transparency and cmat.alpha < 1

            if not cmat.raytrace_mirror.use and not cmat_is_transp:
                if not shader.type == 'ShaderNodeBsdfDiffuse':
                    collect_report("INFO: Make DIFFUSE shader node for: " + cmat.name)
                    TreeNodes.nodes.remove(shader)
                    shader = TreeNodes.nodes.new('ShaderNodeBsdfDiffuse')
                    shader.location = 0, 470
                    links.new(shader.outputs[0], shout.inputs[0])

            if cmat.raytrace_mirror.use and cmat.raytrace_mirror.reflect_factor > 0.001 and cmat_is_transp:
                if not shader.type == 'ShaderNodeBsdfGlass':
                    collect_report("INFO: Make GLASS shader node for: " + cmat.name)
                    TreeNodes.nodes.remove(shader)
                    shader = TreeNodes.nodes.new('ShaderNodeBsdfGlass')
                    shader.location = 0, 470
                    links.new(shader.outputs[0], shout.inputs[0])

            if cmat.raytrace_mirror.use and not cmat_is_transp and cmat.raytrace_mirror.reflect_factor > 0.001:
                if not shader.type == 'ShaderNodeBsdfGlossy':
                    collect_report("INFO: Make MIRROR shader node for: " + cmat.name)
                    TreeNodes.nodes.remove(shader)
                    shader = TreeNodes.nodes.new('ShaderNodeBsdfGlossy')
                    shader.location = 0, 520
                    links.new(shader.outputs[0], shout.inputs[0])

            if cmat.emit > 0.001:
                if (not shader.type == 'ShaderNodeEmission' and not
                   cmat.raytrace_mirror.reflect_factor > 0.001 and not cmat_is_transp):

                    collect_report("INFO: Mix EMISSION shader node for: " + cmat.name)
                    TreeNodes.nodes.remove(shader)
                    shader = TreeNodes.nodes.new('ShaderNodeEmission')
                    shader.location = 0, 450
                    links.new(shader.outputs[0], shout.inputs[0])
                else:
                    if not Add_Emission:
                        collect_report("INFO: Add EMISSION shader node for: " + cmat.name)
                        shout.location = 550, 330
                        Add_Emission = TreeNodes.nodes.new('ShaderNodeAddShader')
                        Add_Emission.location = 370, 490

                        shem = TreeNodes.nodes.new('ShaderNodeEmission')
                        shem.location = 180, 380

                        links.new(Add_Emission.outputs[0], shout.inputs[0])
                        links.new(shem.outputs[0], Add_Emission.inputs[1])
                        links.new(shader.outputs[0], Add_Emission.inputs[0])

                        shem.inputs['Color'].default_value = (cmat.diffuse_color.r,
                                                              cmat.diffuse_color.g,
                                                              cmat.diffuse_color.b, 1)
                        shem.inputs['Strength'].default_value = cmat.emit

            if cmat.translucency > 0.001:
                collect_report("INFO: Add BSDF_TRANSLUCENT shader node for: " + cmat.name)
                shout.location = 770, 330
                Add_Translucent = TreeNodes.nodes.new('ShaderNodeAddShader')
                Add_Translucent.location = 580, 490

                shtsl = TreeNodes.nodes.new('ShaderNodeBsdfTranslucent')
                shtsl.location = 400, 350

                links.new(Add_Translucent.outputs[0], shout.inputs[0])
                links.new(shtsl.outputs[0], Add_Translucent.inputs[1])

                if Add_Emission:
                    links.new(Add_Emission.outputs[0], Add_Translucent.inputs[0])
                    pass
                else:
                    links.new(shader.outputs[0], Add_Translucent.inputs[0])
                    pass
                shtsl.inputs['Color'].default_value = (cmat.translucency,
                                                       cmat.translucency,
                                                       cmat.translucency, 1)

            shader.inputs['Color'].default_value = (cmat.diffuse_color.r,
                                                    cmat.diffuse_color.g,
                                                    cmat.diffuse_color.b, 1)

            if shader.type == 'ShaderNodeBsdfDiffuse':
                shader.inputs['Roughness'].default_value = cmat.specular_intensity

            if shader.type == 'ShaderNodeBsdfGlossy':
                shader.inputs['Roughness'].default_value = 1 - cmat.raytrace_mirror.gloss_factor

            if shader.type == 'ShaderNodeBsdfGlass':
                shader.inputs['Roughness'].default_value = 1 - cmat.raytrace_mirror.gloss_factor
                shader.inputs['IOR'].default_value = cmat.raytrace_transparency.ior

            if shader.type == 'ShaderNodeEmission':
                shader.inputs['Strength'].default_value = cmat.emit

            # texture frame check and tex count (if bigger than 1 add frame)
            frame_check, tex_count, node_frame = False, 0, None

            for tex in cmat.texture_slots:
                if tex:
                    tex_count += 1
                    if not frame_check:
                        frame_check = True
                    if tex_count > 1:
                        break

            if frame_check:
                if tex_count > 1:
                    node_frame = TreeNodes.nodes.new('NodeFrame')
                    node_frame.name = 'Converter Textures'
                    node_frame.label = 'Converter Textures'

                # count the number of texture nodes created
                # for spreading a bit the texture nodes
                row_node, col_node = -1, False
                sM = True
                baked_path = None

                for tex in cmat.texture_slots:
                    sT = False
                    tex_use = getattr(tex, "use", None)
                    if tex_use:
                        row_node = (row_node + 1 if not col_node else row_node)
                        col_node = not col_node
                        tex_node_loc = -(200 + (row_node * 150)), (400 if col_node else 650)
                        ma_alpha = getattr(tex, "use_map_alpha", None)
                        sM = (False if ma_alpha else True)

                        if tex.texture.type == 'IMAGE':
                            if sc.mat_specials.EXTRACT_ALPHA and tex.texture.use_alpha:
                                if (not
                                   os_path.exists(bpy.path.abspath(tex.texture.image.filepath + "_BAKING.png")) or
                                   sc.mat_specials.EXTRACT_OW):
                                    baked_path = BakingText(tex, 'ALPHA')
                                try:
                                    if baked_path:
                                        img = bpy.data.images.load(baked_path)
                                        collect_report("INFO: Loading Baked texture path:")
                                        collect_report(baked_path)
                                    else:
                                        img = tex.texture.image

                                    img_name = (img.name if hasattr(img, "name") else "NO NAME")
                                    shtext = TreeNodes.nodes.new('ShaderNodeTexImage')
                                    shtext.location = tex_node_loc
                                    shtext.image = img
                                    shtext.name = img_name
                                    shtext.label = "Image " + img_name
                                    if baked_path:
                                        shtext.use_custom_color = True
                                        shtext.color = NODE_COLOR
                                    collect_report("INFO: Creating Image Node for image: " + img_name)
                                    if node_frame:
                                        shtext.parent = node_frame
                                    sT = True
                                except:
                                    collect_report("ERROR: A problem occured with loading an image for {} "
                                                   "(possibly missing)".format(tex.texture.name))
                        else:
                            if sc.mat_specials.EXTRACT_PTEX or (sc.mat_specials.EXTRACT_ALPHA and ma_alpha):
                                if (not os_path.exists(bpy.path.abspath(tex.texture.name + "_PTEXT.jpg")) or
                                   sc.mat_specials.EXTRACT_OW):
                                    tex_type = tex.texture.type.lower()
                                    collect_report("Attempting to Extract Procedural Texture type: " + tex_type)
                                    baked_path = BakingText(tex, 'PTEX', tex_type)

                                if baked_path:
                                    try:
                                        img = bpy.data.images.load(baked_path)
                                        collect_report("Loading Baked texture path:")
                                        collect_report(baked_path)
                                        img_name = (img.name if hasattr(img, "name") else "NO NAME")
                                        shtext = TreeNodes.nodes.new('ShaderNodeTexImage')
                                        shtext.location = tex_node_loc
                                        shtext.image = img
                                        shtext.name = img_name
                                        shtext.label = "Baked Image " + img_name
                                        shtext.use_custom_color = True
                                        shtext.color = NODE_COLOR
                                        collect_report("Creating Image Node for baked image: " + img_name)
                                        if node_frame:
                                            shtext.parent = node_frame
                                        sT = True
                                    except:
                                        collect_report("ERROR: Failure to load baked image: " + img_name)
                                else:
                                    collect_report("ERROR: Failure during baking, no images loaded")

                    if cmat_is_transp and cmat.raytrace_transparency.ior == 1 and not cmat.raytrace_mirror.use and sM:
                        if not shader.type == 'ShaderNodeBsdfTransparent':
                            collect_report("INFO: Make TRANSPARENT shader node for: " + cmat.name)
                            TreeNodes.nodes.remove(shader)
                            shader = TreeNodes.nodes.new('ShaderNodeBsdfTransparent')
                            shader.location = 0, 470
                            links.new(shader.outputs[0], shout.inputs[0])

                    shader.inputs['Color'].default_value = (cmat.diffuse_color.r,
                                                            cmat.diffuse_color.g,
                                                            cmat.diffuse_color.b, 1)

                    if sT:
                        if tex.use_map_color_diffuse:
                            links.new(shtext.outputs[0], shader.inputs[0])

                        if tex.use_map_emit:
                            if not Add_Emission:
                                collect_report("INFO: Mix EMISSION + Texture shader node for: " + cmat.name)
                                intensity = 0.5 + (tex.emit_factor / 2)

                                shout.location = 550, 330
                                Add_Emission = TreeNodes.nodes.new('ShaderNodeAddShader')
                                Add_Emission.name = "Add_Emission"
                                Add_Emission.location = 370, 490

                                shem = TreeNodes.nodes.new('ShaderNodeEmission')
                                shem.location = 180, 380

                                links.new(Add_Emission.outputs[0], shout.inputs[0])
                                links.new(shem.outputs[0], Add_Emission.inputs[1])
                                links.new(shader.outputs[0], Add_Emission.inputs[0])

                                shem.inputs['Color'].default_value = (cmat.diffuse_color.r,
                                                                      cmat.diffuse_color.g,
                                                                      cmat.diffuse_color.b, 1)
                                shem.inputs['Strength'].default_value = intensity * 2

                            links.new(shtext.outputs[0], shem.inputs[0])

                        if tex.use_map_mirror:
                            links.new(shader.inputs[0], shtext.outputs[0])

                        if tex.use_map_translucency:
                            if not Add_Translucent:
                                collect_report("INFO: Add Translucency + Texture shader node for: " + cmat.name)

                                intensity = 0.5 + (tex.emit_factor / 2)
                                shout.location = 550, 330
                                Add_Translucent = TreeNodes.nodes.new('ShaderNodeAddShader')
                                Add_Translucent.name = "Add_Translucent"
                                Add_Translucent.location = 370, 290

                                shtsl = TreeNodes.nodes.new('ShaderNodeBsdfTranslucent')
                                shtsl.location = 180, 240

                                links.new(shtsl.outputs[0], Add_Translucent.inputs[1])

                                if Add_Emission:
                                    links.new(Add_Translucent.outputs[0], shout.inputs[0])
                                    links.new(Add_Emission.outputs[0], Add_Translucent.inputs[0])
                                    pass
                                else:
                                    links.new(Add_Translucent.outputs[0], shout.inputs[0])
                                    links.new(shader.outputs[0], Add_Translucent.inputs[0])

                            links.new(shtext.outputs[0], shtsl.inputs[0])

                        if tex.use_map_alpha:
                            if not Mix_Alpha:
                                collect_report("INFO: Mix Alpha + Texture shader node for: " + cmat.name)

                                shout.location = 750, 330
                                Mix_Alpha = TreeNodes.nodes.new('ShaderNodeMixShader')
                                Mix_Alpha.name = "Add_Alpha"
                                Mix_Alpha.location = 570, 290
                                sMask = TreeNodes.nodes.new('ShaderNodeBsdfTransparent')
                                sMask.location = 250, 180
                                tMask, imask = None, None

                                # search if the texture node already exists, if not create
                                nodes = getattr(cmat.node_tree, "nodes", None)
                                img_name = getattr(img, "name", "NO NAME")
                                for node in nodes:
                                    if type(node) == bpy.types.ShaderNodeTexImage:
                                        node_name = getattr(node, "name")
                                        if img_name in node_name:
                                            tMask = node
                                            collect_report("INFO: Using existing Texture Node for Mask: " + node_name)
                                            break

                                if tMask is None:
                                    tMask = TreeNodes.nodes.new('ShaderNodeTexImage')

                                    if node_frame:
                                        tMask.parent = node_frame
                                    tex_node_loc = -(200 + ((row_node + 1) * 150)), (650 if col_node else 400)
                                    tMask.location = tex_node_loc

                                    try:
                                        file_path = getattr(img, "filepath", None)
                                        if file_path:
                                            imask = bpy.data.images.load(file_path)
                                        else:
                                            imask = bpy.data.images.get(img_name)
                                        collect_report("INFO: Attempting to load image for Mask: " + img_name)
                                    except:
                                        collect_report("ERROR: Failure to load image for Mask: " + img_name)

                                    if imask:
                                        tMask.image = imask

                                if tMask:
                                    links.new(Mix_Alpha.inputs[0], tMask.outputs[1])
                                    links.new(shout.inputs[0], Mix_Alpha.outputs[0])
                                    links.new(sMask.outputs[0], Mix_Alpha.inputs[1])

                                    if not Add_Translucent:
                                        if Add_Emission:
                                            links.new(Mix_Alpha.inputs[2], Add_Emission.outputs[0])
                                        else:
                                            links.new(Mix_Alpha.inputs[2], shader.outputs[0])
                                    else:
                                        links.new(Mix_Alpha.inputs[2], Add_Translucent.outputs[0])
                                else:
                                    collect_report("ERROR: Mix Alpha could not be created "
                                                   "(mask image could not be loaded)")

                        if tex.use_map_normal:
                            t = TreeNodes.nodes.new('ShaderNodeRGBToBW')
                            t.location = -0, 300
                            links.new(t.outputs[0], shout.inputs[2])
                            links.new(shtext.outputs[0], t.inputs[0])
            else:
                collect_report("No textures in the Scene, no Image Nodes to add")

    bpy.context.scene.render.engine = 'CYCLES'


# -----------------------------------------------------------------------------
# Operator Classes #

class mllock(Operator):
    bl_idname = "ml.lock"
    bl_label = "Lock"
    bl_description = "Lock/unlock this material against modification by conversions"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (c_is_cycles_addon_enabled() and c_data_has_materials())

    def execute(self, context):
        cmat = bpy.context.selected_objects[0].active_material
        TreeNodes = cmat.node_tree
        for n in TreeNodes.nodes:
            if n.type == 'ShaderNodeOutputMaterial':
                if n.label == 'Locked':
                    n.label = ''
                else:
                    n.label = 'Locked'
        return {'FINISHED'}


class mlrefresh(Operator):
    bl_idname = "ml.refresh"
    bl_label = "Convert All Materials"
    bl_description = "Convert All Materials in the scene from non-nodes to Cycles"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (c_is_cycles_addon_enabled() and c_data_has_materials())

    def execute(self, context):
        AutoNodeInitiate(False, self)

        if CHECK_AUTONODE is True:
            bpy.ops.object.editmode_toggle()
            bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
            bpy.ops.object.editmode_toggle()

        return {'FINISHED'}


class mlrefresh_active(Operator):
    bl_idname = "ml.refresh_active"
    bl_label = "Convert All Materials From Active Object"
    bl_description = "Convert all Active Object's Materials from non-nodes to Cycles"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (c_is_cycles_addon_enabled() and c_data_has_materials() and
                context.active_object is not None)

    def execute(self, context):
        AutoNodeInitiate(True, self)
        if CHECK_AUTONODE is True:
            bpy.ops.object.editmode_toggle()
            bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
            bpy.ops.object.editmode_toggle()
        return {'FINISHED'}


class mlrestore(Operator):
    bl_idname = "ml.restore"
    bl_label = "Switch Between Renderers"
    bl_description = ("Switch between Renderers \n"
                      "(Doesn't create new nor converts existing materials)")
    bl_options = {'REGISTER', 'UNDO'}

    switcher = BoolProperty(
            name="Use Nodes",
            description="When restoring, switch Use Nodes On/Off",
            default=True
            )
    renderer = EnumProperty(
            name="Renderer",
            description="Choose Cycles or Blender Internal",
            items=(('CYCLES', "Cycles", "Switch to Cycles"),
                   ('BI', "Blender Internal", "Switch to Blender Internal")),
            default='CYCLES',
            )

    @classmethod
    def poll(cls, context):
        return c_is_cycles_addon_enabled()

    def execute(self, context):
        if self.switcher:
            AutoNodeSwitch(self.renderer, "ON", self)
        else:
            AutoNodeSwitch(self.renderer, "OFF", self)
        return {'FINISHED'}


def register():
    bpy.utils.register_module(__name__)
    pass


def unregister():
    bpy.utils.unregister_module(__name__)
    pass

if __name__ == "__main__":
    register()
