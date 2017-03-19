from bpy.props import *
from .Utils.core import *


class TextureMenu(bpy.types.Menu):
    bl_label = "Texture Options"
    bl_idname = "VIEW3D_MT_sv3_texture_menu"

    @classmethod
    def poll(self, context):
        if get_mode() in [sculpt, vertex_paint, texture_paint]:
            return True
        else:
            return False

    def draw(self, context):
        menu = Menu(self)

        if get_mode() == sculpt:
            self.sculpt(menu, context)

        elif get_mode() == vertex_paint:
            self.vertpaint(menu, context)

        else:
            self.texpaint(menu, context)

    def sculpt(self, menu, context):
        tex_slot = context.tool_settings.sculpt.brush.texture_slot
        
        # Menus
        menu.add_item().menu(Textures.bl_idname)
        menu.add_item().menu(TextureMapMode.bl_idname)

        # Checkboxes
        if tex_slot.map_mode != '3D':
            if tex_slot.map_mode in ['RANDOM', 'VIEW_PLANE', 'AREA_PLANE']:
                if bpy.app.version >= (2, 75):
                    menu.add_item().prop(tex_slot, "use_rake", toggle=True)
                    menu.add_item().prop(tex_slot, "use_random", toggle=True)
                else:
                    menu.add_item().menu(TextureAngleSource.bl_idname)

            # Sliders
            menu.add_item().prop(tex_slot, "angle", text=PIW+"Angle", slider=True)
            
            if tex_slot.tex_paint_map_mode in ['RANDOM', 'VIEW_PLANE'] and tex_slot.use_random:
                menu.add_item().prop(tex_slot, "random_angle", text=PIW+"Random Angle", slider=True)
            
            # Operator
            if tex_slot.tex_paint_map_mode == 'STENCIL':
                menu.add_item().operator("brush.stencil_reset_transform")

    def vertpaint(self, menu, context):
        tex_slot = context.tool_settings.vertex_paint.brush.texture_slot
        
        # Menus
        menu.add_item().menu(Textures.bl_idname)
        menu.add_item().menu(TextureMapMode.bl_idname)

        # Checkboxes
        if tex_slot.tex_paint_map_mode != '3D':

            if tex_slot.tex_paint_map_mode in ['RANDOM', 'VIEW_PLANE']:
                if bpy.app.version >= (2, 75):
                    menu.add_item().prop(tex_slot, "use_rake", toggle=True)
                    menu.add_item().prop(tex_slot, "use_random", toggle=True)
                else:
                    menu.add_item().menu(TextureAngleSource.bl_idname)

            # Sliders
            menu.add_item().prop(tex_slot, "angle", text=PIW+"Angle", slider=True)
            
            if tex_slot.tex_paint_map_mode in ['RANDOM', 'VIEW_PLANE'] and tex_slot.use_random:
                menu.add_item().prop(tex_slot, "random_angle", text=PIW+"Random Angle", slider=True)
            
            # Operator
            if tex_slot.tex_paint_map_mode == 'STENCIL':
                menu.add_item().operator("brush.stencil_reset_transform")

    def texpaint(self, menu, context):
        tex_slot = context.tool_settings.image_paint.brush.texture_slot
        mask_tex_slot = context.tool_settings.image_paint.brush.mask_texture_slot
        
        # Texture Section
        menu.add_item().label(text="Texture", icon='TEXTURE')

        # Menus
        menu.add_item().menu(Textures.bl_idname)
        menu.add_item().menu(TextureMapMode.bl_idname)

        # Checkboxes
        if tex_slot.tex_paint_map_mode != '3D':
            if tex_slot.tex_paint_map_mode in ['RANDOM', 'VIEW_PLANE']:
                if bpy.app.version >= (2, 75):
                    menu.add_item().prop(tex_slot, "use_rake", toggle=True)
                    menu.add_item().prop(tex_slot, "use_random", toggle=True)
                else:
                    menu.add_item().menu(TextureAngleSource.bl_idname)

            # Sliders
            menu.add_item().prop(tex_slot, "angle", text=PIW+"Angle", slider=True)

            if tex_slot.tex_paint_map_mode in ['RANDOM', 'VIEW_PLANE'] and tex_slot.use_random:
                menu.add_item().prop(tex_slot, "random_angle", text=PIW+"Random Angle", slider=True)
            
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
        if mask_tex_slot.mask_map_mode in ['RANDOM', 'VIEW_PLANE']:
            if bpy.app.version >= (2, 75):
                menu.add_item().prop(mask_tex_slot, "use_rake", toggle=True)
                menu.add_item().prop(mask_tex_slot, "use_random", toggle=True)
            else:
                menu.add_item().menu(TextureAngleSource.bl_idname)

        # Sliders
        menu.add_item().prop(mask_tex_slot, "angle", text=PIW+"Angle", icon_value=5, slider=True)

        if mask_tex_slot.mask_map_mode in ['RANDOM', 'VIEW_PLANE'] and mask_tex_slot.use_random:
            menu.add_item().prop(mask_tex_slot, "random_angle", text=PIW+"Random Angle", slider=True)
        
        # Operator
        if mask_tex_slot.mask_map_mode == 'STENCIL':
            prop = menu.add_item().operator("brush.stencil_reset_transform")
            prop.mask = True


class Textures(bpy.types.Menu):
    bl_label = "Brush Texture"
    bl_idname = "VIEW3D_MT_sv3_texture_list"

    def init(self):
        if get_mode() == sculpt:
            datapath = "tool_settings.sculpt.brush.texture"

        elif get_mode() == vertex_paint:
            datapath = "tool_settings.vertex_paint.brush.texture"

        elif get_mode() == texture_paint:
            datapath = "tool_settings.image_paint.brush.texture"

        else:
            datapath = ""

        return datapath

    def draw(self, context):
        datapath = self.init()
        current_texture = eval("bpy.context.{}".format(datapath))
        menu = Menu(self)

        # get the current texture's name
        if current_texture:
            current_texture = current_texture.name

        menu.add_item().label(text="Brush Texture")
        menu.add_item().separator()

        # add an item to set the texture to None
        menuprop(menu.add_item(), "None", "None",
                 datapath, icon='RADIOBUT_OFF', disable=True,
                 disable_icon='RADIOBUT_ON',
                 custom_disable_exp=[None, current_texture],
                 path=True)

        # add the menu items
        for item in bpy.data.textures:
            menuprop(menu.add_item(), item.name,
                     'bpy.data.textures["%s"]' % item.name,
                     datapath, icon='RADIOBUT_OFF',
                     disable=True,
                     disable_icon='RADIOBUT_ON',
                     custom_disable_exp=[item.name, current_texture],
                     path=True)


class TextureMapMode(bpy.types.Menu):
    bl_label = "Brush Mapping"
    bl_idname = "VIEW3D_MT_sv3_texture_map_mode"

    def draw(self, context):
        menu = Menu(self)

        menu.add_item().label(text="Brush Mapping")
        menu.add_item().separator()

        if get_mode() == sculpt:
            path = "tool_settings.sculpt.brush.texture_slot.map_mode"

            # add the menu items
            for item in context.tool_settings.sculpt.brush.texture_slot.bl_rna.properties['map_mode'].enum_items:
                menuprop(menu.add_item(), item.name, item.identifier, path,
                         icon='RADIOBUT_OFF',
                         disable=True,
                         disable_icon='RADIOBUT_ON')

        elif get_mode() == vertex_paint:
            path = "tool_settings.vertex_paint.brush.texture_slot.tex_paint_map_mode"

            # add the menu items
            for item in context.tool_settings.vertex_paint.brush.texture_slot.bl_rna.properties['tex_paint_map_mode'].enum_items:
                menuprop(menu.add_item(), item.name, item.identifier, path,
                         icon='RADIOBUT_OFF',
                         disable=True,
                         disable_icon='RADIOBUT_ON')

        else:
            path = "tool_settings.image_paint.brush.texture_slot.tex_paint_map_mode"

            # add the menu items
            for item in context.tool_settings.image_paint.brush.texture_slot.bl_rna.properties['tex_paint_map_mode'].enum_items:
                menuprop(menu.add_item(), item.name, item.identifier, path,
                         icon='RADIOBUT_OFF',
                         disable=True,
                         disable_icon='RADIOBUT_ON')


class MaskTextures(bpy.types.Menu):
    bl_label = "Mask Texture"
    bl_idname = "VIEW3D_MT_sv3_mask_texture_list"

    def draw(self, context):
        menu = Menu(self)
        datapath = "tool_settings.image_paint.brush.mask_texture"
        current_texture = eval("bpy.context.{}".format(datapath))

        menu.add_item().label(text="Mask Texture")
        menu.add_item().separator()

        # get the current texture's name
        if current_texture:
            current_texture = current_texture.name

        # add an item to set the texture to None
        menuprop(menu.add_item(), "None", "None",
                 datapath, icon='RADIOBUT_OFF', disable=True,
                 disable_icon='RADIOBUT_ON',
                 custom_disable_exp=[None, current_texture],
                 path=True)

        # add the menu items
        for item in bpy.data.textures:
            menuprop(menu.add_item(), item.name, 'bpy.data.textures["%s"]' % item.name,
                     datapath, icon='RADIOBUT_OFF', disable=True,
                     disable_icon='RADIOBUT_ON',
                     custom_disable_exp=[item.name, current_texture],
                     path=True)


class MaskMapMode(bpy.types.Menu):
    bl_label = "Mask Mapping"
    bl_idname = "VIEW3D_MT_sv3_mask_map_mode"

    def draw(self, context):
        menu = Menu(self)

        path = "tool_settings.image_paint.brush.mask_texture_slot.mask_map_mode"

        menu.add_item().label(text="Mask Mapping")
        menu.add_item().separator()

        # add the menu items
        for item in context.tool_settings.image_paint.brush.mask_texture_slot.bl_rna.properties['mask_map_mode'].enum_items:
            menuprop(menu.add_item(), item.name, item.identifier, path,
                     icon='RADIOBUT_OFF',
                     disable=True, 
                     disable_icon='RADIOBUT_ON')


class TextureAngleSource(bpy.types.Menu):
    bl_label = "Texture Angle Source"
    bl_idname = "VIEW3D_MT_sv3_texture_angle_source"

    def draw(self, context):
        menu = Menu(self)

        if get_mode() == sculpt:
            items = context.tool_settings.sculpt.brush.bl_rna.properties['texture_angle_source_random'].enum_items
            path = "tool_settings.sculpt.brush.texture_angle_source_random"

        elif get_mode() == vertex_paint:
            items = context.tool_settings.vertex_paint.brush.bl_rna.properties['texture_angle_source_random'].enum_items
            path = "tool_settings.vertex_paint.brush.texture_angle_source_random"

        else:
            items = context.tool_settings.image_paint.brush.bl_rna.properties['texture_angle_source_random'].enum_items
            path = "tool_settings.image_paint.brush.texture_angle_source_random"

        # add the menu items
        for item in items:
            menuprop(menu.add_item(), item[0], item[1], path,
                     icon='RADIOBUT_OFF',
                     disable=True, 
                     disable_icon='RADIOBUT_ON')
