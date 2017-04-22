# gpl author: Ryan Inch (Imaginer)

import bpy
from bpy.types import Menu
from . import utils_core


class TextureMenu(Menu):
    bl_label = "Texture Options"
    bl_idname = "VIEW3D_MT_sv3_texture_menu"

    @classmethod
    def poll(self, context):
        return utils_core.get_mode() in (
                        utils_core.sculpt,
                        utils_core.vertex_paint,
                        utils_core.texture_paint
                        )

    def draw(self, context):
        menu = utils_core.Menu(self)

        if utils_core.get_mode() == utils_core.sculpt:
            self.sculpt(menu, context)

        elif utils_core.get_mode() == utils_core.vertex_paint:
            self.vertpaint(menu, context)

        else:
            self.texpaint(menu, context)

    def sculpt(self, menu, context):
        has_brush = utils_core.get_brush_link(context, types="brush")
        tex_slot = has_brush.texture_slot if has_brush else None

        # Menus
        menu.add_item().menu(Textures.bl_idname)
        menu.add_item().menu(TextureMapMode.bl_idname)
        menu.add_item().separator()

        # Checkboxes
        if tex_slot:
            if tex_slot.map_mode != '3D':
                if tex_slot.map_mode in ['RANDOM', 'VIEW_PLANE', 'AREA_PLANE']:
                    menu.add_item().prop(tex_slot, "use_rake", toggle=True)
                    menu.add_item().prop(tex_slot, "use_random", toggle=True)

                # Sliders
                menu.add_item().prop(tex_slot, "angle",
                                     text=utils_core.PIW + "Angle", slider=True)

                if tex_slot.tex_paint_map_mode in ['RANDOM', 'VIEW_PLANE'] and tex_slot.use_random:
                    menu.add_item().prop(tex_slot, "random_angle",
                                         text=utils_core.PIW + "Random Angle", slider=True)

                # Operator
                if tex_slot.tex_paint_map_mode == 'STENCIL':
                    menu.add_item().operator("brush.stencil_reset_transform")
        else:
            menu.add_item().label("No Texture Slot available", icon="INFO")

    def vertpaint(self, menu, context):
        has_brush = utils_core.get_brush_link(context, types="brush")
        tex_slot = has_brush.texture_slot if has_brush else None

        # Menus
        menu.add_item().menu(Textures.bl_idname)
        menu.add_item().menu(TextureMapMode.bl_idname)

        # Checkboxes
        if tex_slot and tex_slot.tex_paint_map_mode != '3D':

            if tex_slot.tex_paint_map_mode in ['RANDOM', 'VIEW_PLANE']:
                menu.add_item().prop(tex_slot, "use_rake", toggle=True)
                menu.add_item().prop(tex_slot, "use_random", toggle=True)

            # Sliders
            menu.add_item().prop(tex_slot, "angle",
                                 text=utils_core.PIW + "Angle", slider=True)

            if tex_slot.tex_paint_map_mode in ['RANDOM', 'VIEW_PLANE'] and tex_slot.use_random:
                menu.add_item().prop(tex_slot, "random_angle",
                                     text=utils_core.PIW + "Random Angle", slider=True)

            # Operator
            if tex_slot.tex_paint_map_mode == 'STENCIL':
                menu.add_item().operator("brush.stencil_reset_transform")
        else:
            menu.add_item().label("No Texture Slot available", icon="INFO")

    def texpaint(self, menu, context):
        has_brush = utils_core.get_brush_link(context, types="brush")
        tex_slot = has_brush.texture_slot if has_brush else None
        mask_tex_slot = has_brush.mask_texture_slot if has_brush else None

        # Texture Section
        menu.add_item().label(text="Texture", icon='TEXTURE')

        # Menus
        menu.add_item().menu(Textures.bl_idname)
        menu.add_item().menu(TextureMapMode.bl_idname)

        # Checkboxes
        if tex_slot and tex_slot.tex_paint_map_mode != '3D':
            if tex_slot.tex_paint_map_mode in ['RANDOM', 'VIEW_PLANE']:
                menu.add_item().prop(tex_slot, "use_rake", toggle=True)
                menu.add_item().prop(tex_slot, "use_random", toggle=True)

            # Sliders
            menu.add_item().prop(tex_slot, "angle",
                                 text=utils_core.PIW + "Angle", slider=True)

            if tex_slot.tex_paint_map_mode in ['RANDOM', 'VIEW_PLANE'] and tex_slot.use_random:
                menu.add_item().prop(tex_slot, "random_angle",
                                     text=utils_core.PIW + "Random Angle", slider=True)

            # Operator
            if tex_slot.tex_paint_map_mode == 'STENCIL':
                menu.add_item().operator("brush.stencil_reset_transform")

        menu.add_item().separator()

        # Texture Mask Section
        menu.add_item().label(text="Texture Mask", icon='MOD_MASK')

        # Menus
        menu.add_item().menu(MaskTextures.bl_idname)
        menu.add_item().menu(MaskMapMode.bl_idname)

        # Checkboxes
        if mask_tex_slot:
            if mask_tex_slot.mask_map_mode in ['RANDOM', 'VIEW_PLANE']:
                menu.add_item().prop(mask_tex_slot, "use_rake", toggle=True)
                menu.add_item().prop(mask_tex_slot, "use_random", toggle=True)

            # Sliders
            menu.add_item().prop(mask_tex_slot, "angle",
                                text=utils_core.PIW + "Angle", icon_value=5, slider=True)

            if mask_tex_slot.mask_map_mode in ['RANDOM', 'VIEW_PLANE'] and \
              mask_tex_slot.use_random:
                menu.add_item().prop(mask_tex_slot, "random_angle",
                                     text=utils_core.PIW + "Random Angle", slider=True)

            # Operator
            if mask_tex_slot.mask_map_mode == 'STENCIL':
                prop = menu.add_item().operator("brush.stencil_reset_transform")
                prop.mask = True
        else:
            menu.add_item().label("Mask Texture not available", icon="INFO")


class Textures(Menu):
    bl_label = "Brush Texture"
    bl_idname = "VIEW3D_MT_sv3_texture_list"

    def init(self):
        if utils_core.get_mode() == utils_core.sculpt:
            datapath = "tool_settings.sculpt.brush.texture"

        elif utils_core.get_mode() == utils_core.vertex_paint:
            datapath = "tool_settings.vertex_paint.brush.texture"

        elif utils_core.get_mode() == utils_core.texture_paint:
            datapath = "tool_settings.image_paint.brush.texture"

        else:
            datapath = ""

        return datapath

    def draw(self, context):
        datapath = self.init()
        has_brush = utils_core.get_brush_link(context, types="brush")
        current_texture = eval("bpy.context.{}".format(datapath)) if \
                          has_brush else None
        menu = utils_core.Menu(self)

        # get the current texture's name
        if current_texture:
            current_texture = current_texture.name

        menu.add_item().label(text="Brush Texture")
        menu.add_item().separator()

        # add an item to set the texture to None
        utils_core.menuprop(menu.add_item(), "None", "None",
                 datapath, icon='RADIOBUT_OFF', disable=True,
                 disable_icon='RADIOBUT_ON',
                 custom_disable_exp=[None, current_texture],
                 path=True)

        # add the menu items
        for item in bpy.data.textures:
            utils_core.menuprop(menu.add_item(), item.name,
                     'bpy.data.textures["%s"]' % item.name,
                     datapath, icon='RADIOBUT_OFF',
                     disable=True,
                     disable_icon='RADIOBUT_ON',
                     custom_disable_exp=[item.name, current_texture],
                     path=True)


class TextureMapMode(Menu):
    bl_label = "Brush Mapping"
    bl_idname = "VIEW3D_MT_sv3_texture_map_mode"

    def draw(self, context):
        menu = utils_core.Menu(self)
        has_brush = utils_core.get_brush_link(context, types="brush")

        menu.add_item().label(text="Brush Mapping")
        menu.add_item().separator()

        if has_brush:
            if utils_core.get_mode() == utils_core.sculpt:
                path = "tool_settings.sculpt.brush.texture_slot.map_mode"

                # add the menu items
                for item in has_brush. \
                  texture_slot.bl_rna.properties['map_mode'].enum_items:
                    utils_core.menuprop(
                            menu.add_item(), item.name, item.identifier, path,
                            icon='RADIOBUT_OFF',
                            disable=True,
                            disable_icon='RADIOBUT_ON'
                            )
            elif utils_core.get_mode() == utils_core.vertex_paint:
                path = "tool_settings.vertex_paint.brush.texture_slot.tex_paint_map_mode"

                # add the menu items
                for item in has_brush. \
                  texture_slot.bl_rna.properties['tex_paint_map_mode'].enum_items:
                    utils_core.menuprop(
                            menu.add_item(), item.name, item.identifier, path,
                            icon='RADIOBUT_OFF',
                            disable=True,
                            disable_icon='RADIOBUT_ON'
                            )
            else:
                path = "tool_settings.image_paint.brush.texture_slot.tex_paint_map_mode"

                # add the menu items
                for item in has_brush. \
                  texture_slot.bl_rna.properties['tex_paint_map_mode'].enum_items:
                    utils_core.menuprop(
                            menu.add_item(), item.name, item.identifier, path,
                            icon='RADIOBUT_OFF',
                            disable=True,
                            disable_icon='RADIOBUT_ON'
                            )
        else:
            menu.add_item().label("No brushes available", icon="INFO")


class MaskTextures(Menu):
    bl_label = "Mask Texture"
    bl_idname = "VIEW3D_MT_sv3_mask_texture_list"

    def draw(self, context):
        menu = utils_core.Menu(self)
        datapath = "tool_settings.image_paint.brush.mask_texture"
        has_brush = utils_core.get_brush_link(context, types="brush")
        current_texture = eval("bpy.context.{}".format(datapath)) if \
                          has_brush else None

        menu.add_item().label(text="Mask Texture")
        menu.add_item().separator()

        if has_brush:
            # get the current texture's name
            if current_texture:
                current_texture = current_texture.name

            # add an item to set the texture to None
            utils_core.menuprop(
                    menu.add_item(), "None", "None",
                    datapath, icon='RADIOBUT_OFF', disable=True,
                    disable_icon='RADIOBUT_ON',
                    custom_disable_exp=[None, current_texture],
                    path=True
                    )

            # add the menu items
            for item in bpy.data.textures:
                utils_core.menuprop(
                        menu.add_item(), item.name, 'bpy.data.textures["%s"]' % item.name,
                        datapath, icon='RADIOBUT_OFF', disable=True,
                        disable_icon='RADIOBUT_ON',
                        custom_disable_exp=[item.name, current_texture],
                        path=True
                        )
        else:
            menu.add_item().label("No brushes available", icon="INFO")


class MaskMapMode(Menu):
    bl_label = "Mask Mapping"
    bl_idname = "VIEW3D_MT_sv3_mask_map_mode"

    def draw(self, context):
        menu = utils_core.Menu(self)
        path = "tool_settings.image_paint.brush.mask_texture_slot.mask_map_mode"
        has_brush = utils_core.get_brush_link(context, types="brush")

        menu.add_item().label(text="Mask Mapping")
        menu.add_item().separator()
        if has_brush:
            items = has_brush. \
                    mask_texture_slot.bl_rna.properties['mask_map_mode'].enum_items
            # add the menu items
            for item in items:
                utils_core.menuprop(
                        menu.add_item(), item.name, item.identifier, path,
                        icon='RADIOBUT_OFF',
                        disable=True,
                        disable_icon='RADIOBUT_ON'
                        )
        else:
            menu.add_item().label("No brushes available", icon="INFO")


class TextureAngleSource(Menu):
    bl_label = "Texture Angle Source"
    bl_idname = "VIEW3D_MT_sv3_texture_angle_source"

    def draw(self, context):
        menu = utils_core.Menu(self)
        has_brush = utils_core.get_brush_link(context, types="brush")

        if has_brush:
            if utils_core.get_mode() == utils_core.sculpt:
                items = has_brush. \
                        bl_rna.properties['texture_angle_source_random'].enum_items
                path = "tool_settings.sculpt.brush.texture_angle_source_random"

            elif utils_core.get_mode() == utils_core.vertex_paint:
                items = has_brush. \
                        bl_rna.properties['texture_angle_source_random'].enum_items
                path = "tool_settings.vertex_paint.brush.texture_angle_source_random"

            else:
                items = has_brush. \
                        bl_rna.properties['texture_angle_source_random'].enum_items
                path = "tool_settings.image_paint.brush.texture_angle_source_random"

            # add the menu items
            for item in items:
                utils_core.menuprop(
                        menu.add_item(), item[0], item[1], path,
                        icon='RADIOBUT_OFF',
                        disable=True,
                        disable_icon='RADIOBUT_ON'
                        )
        else:
            menu.add_item().label("No brushes available", icon="INFO")
