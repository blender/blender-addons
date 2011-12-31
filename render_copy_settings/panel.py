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

import bpy
from . import presets


class RENDER_PT_copy_settings(bpy.types.Panel):
    bl_label = "Copy Settings"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'BLENDER_RENDER'}

    def draw(self, context):
        layout = self.layout
        cp_sett = context.scene.render_copy_settings

        layout.operator("scene.render_copy_settings",
                        text="Copy Render Settings")

        # This will update affected_settings/allowed_scenes (as this seems
        # to be impossible to do it from here…).
        if bpy.ops.scene.render_copy_settings_prepare.poll():
            bpy.ops.scene.render_copy_settings_prepare()

        split = layout.split(0.75)
        split.template_list(cp_sett, "affected_settings", cp_sett,
                            "aff_sett_idx",
                            prop_list="template_list_controls", rows=6)

        col = split.column()
        all_set = {sett.strid for sett in cp_sett.affected_settings
                                       if sett.copy}
        for p in presets.presets:
            label = ""
            if p.elements & all_set == p.elements:
                label = "Clear {}".format(p.ui_name)
            else:
                label = "Set {}".format(p.ui_name)
            col.operator("scene.render_copy_settings_preset",
                         text=label).presets = {p.rna_enum[0]}

        layout.prop(cp_sett, "filter_scene")
        if len(cp_sett.allowed_scenes):
            layout.label("Affected Scenes:")
            # XXX Unfortunately, there can only be one template_list per panel…
            col = layout.column_flow(columns=0)
            for i, prop in enumerate(cp_sett.allowed_scenes):
                col.prop(prop, "allowed", toggle=True, text=prop.name)
        else:
            layout.label(text="No Affectable Scenes!", icon="ERROR")
