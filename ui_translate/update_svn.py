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

if "bpy" in locals():
    import imp
    imp.reload(settings)
    imp.reload(utils_i18n)
    imp.reload(utils_languages_menu)
else:
    import bpy
    from bpy.props import (BoolProperty,
                           CollectionProperty,
                           EnumProperty,
                           FloatProperty,
                           FloatVectorProperty,
                           IntProperty,
                           PointerProperty,
                           StringProperty,
                           )
    from . import settings
    from bl_i18n_utils import utils as utils_i18n
    from bl_i18n_utils import utils_languages_menu

from bpy.app.translations import pgettext_iface as iface_

import io
import os
import shutil
import subprocess
import tempfile


##### Data #####
class I18nUpdateTranslationLanguage(bpy.types.PropertyGroup):
    """Settings/info about a language"""
    uid = StringProperty(name="Language ID", default="", description="ISO code, like fr_FR")
    num_id = IntProperty(name="Numeric ID", default=0, min=0, description="Numeric ID (readonly!)")
    name = StringProperty(name="Language Name", default="",
                          description="English language name/label (like \"French (Français)\")")
    use = BoolProperty(name="Use", default=True, description="Use this language in current operator")
    po_path = StringProperty(name="PO File Path", default="", subtype='FILE_PATH',
                             description="Path to the relevant po file in branches")
    po_path_trunk = StringProperty(name="PO Trunk File Path", default="", subtype='FILE_PATH',
                                   description="Path to the relevant po file in trunk")
    mo_path_trunk = StringProperty(name="MO File Path", default="", subtype='FILE_PATH',
                                   description="Path to the relevant mo file")


class I18nUpdateTranslationSettings(bpy.types.PropertyGroup):
    """Settings/info about a language"""
    langs = CollectionProperty(name="Languages", type=I18nUpdateTranslationLanguage,
                               description="Languages to update in branches")
    active_lang = IntProperty(name="Active Language", default=0,
                              description="Index of active language in langs collection")
    pot_path = StringProperty(name="POT File Path", default="", subtype='FILE_PATH',
                              description="Path to the pot template file")
    is_init = BoolProperty(default=False, options={'HIDDEN'},
                           description="Whether these settings have already been auto-set or not")


##### UI #####
class UI_UL_i18n_languages(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        #assert(isinstance(item, bpy.types.I18nUpdateTranslationLanguage))
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(item.name, icon_value=icon)
            layout.prop(item, "use", text="")
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(item.uid)
            layout.prop(item, "use", text="")


class UI_PT_i18n_update_translations_settings(bpy.types.Panel):
    bl_label = "I18n Update Translation Main"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"

    def draw(self, context):
        layout = self.layout
        i18n_sett = context.window_manager.i18n_update_svn_settings

        if not i18n_sett.is_init and bpy.ops.ui.i18n_updatetranslation_svn_init_settings.poll():
            bpy.ops.ui.i18n_updatetranslation_svn_init_settings()

        if not i18n_sett.is_init:
            layout.label(text="Could not init languages data!")
            layout.label(text="Please edit the preferences of the UI Translate addon")
        else:
            split = layout.split(0.75)
            split.template_list("UI_UL_i18n_languages", "", i18n_sett, "langs", i18n_sett, "active_lang", rows=8)
            col = split.column()
            col.operator("ui.i18n_updatetranslation_svn_init_settings", text="Reset Settings")
            if any(l.use for l in i18n_sett.langs):
                col.operator("ui.i18n_updatetranslation_svn_settings_select", text="Deselect All").use_select = False
            else:
                col.operator("ui.i18n_updatetranslation_svn_settings_select", text="Select All").use_select = True
            col.operator("ui.i18n_updatetranslation_svn_settings_select", text="Invert Selection").use_invert = True
            col.separator()
            col.operator("ui.i18n_updatetranslation_svn_branches", text="Update Branches")
            col.operator("ui.i18n_updatetranslation_svn_trunk", text="Update Trunk")
            col.operator("ui.i18n_updatetranslation_svn_statistics", text="Statistics")

            if i18n_sett.active_lang >= 0 and i18n_sett.active_lang < len(i18n_sett.langs):
                lng = i18n_sett.langs[i18n_sett.active_lang]
                col = layout.column()
                col.active = lng.use
                row = col.row()
                row.label(text="[{}]: \"{}\" ({})".format(lng.uid, iface_(lng.name), lng.num_id), translate=False)
                row.prop(lng, "use", text="")
                col.prop(lng, "po_path")
                col.prop(lng, "po_path_trunk")
                col.prop(lng, "mo_path_trunk")
            layout.separator()
            layout.prop(i18n_sett, "pot_path")

            layout.separator()
            layout.label("Addons:")
            row = layout.row()
            op = row.operator("UI_OT_i18n_addon_translation_invoke", text="Export PO...")
            op.op_id = "ui.i18n_addon_translation_export"


##### Operators #####
class UI_OT_i18n_updatetranslation_svn_init_settings(bpy.types.Operator):
    """Init settings for i18n svn's update operators"""
    bl_idname = "ui.i18n_updatetranslation_svn_init_settings"
    bl_label = "Init I18n Update Settings"
    bl_option = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.window_manager != None

    def execute(self, context):
        if not hasattr(self, "settings"):
            self.settings = settings.settings
        i18n_sett = context.window_manager.i18n_update_svn_settings

        # First, create the list of languages from settings.
        i18n_sett.langs.clear()
        root_br = self.settings.BRANCHES_DIR
        root_tr_po = self.settings.TRUNK_PO_DIR
        root_tr_mo = os.path.join(self.settings.TRUNK_DIR, self.settings.MO_PATH_TEMPLATE, self.settings.MO_FILE_NAME)
        if not (os.path.isdir(root_br) and os.path.isdir(root_tr_po)):
            return {'CANCELLED'}
        isocodes = ((e, os.path.join(root_br, e, e + ".po")) for e in os.listdir(root_br))
        isocodes = dict(e for e in isocodes if os.path.isfile(e[1]))
        for num_id, name, uid in self.settings.LANGUAGES[2:]:  # Skip "default" and "en" languages!
            best_po = utils_i18n.find_best_isocode_matches(uid, isocodes)
            #print(uid, "->", best_po)
            lng = i18n_sett.langs.add()
            lng.uid = uid
            lng.num_id = num_id
            lng.name = name
            if best_po:
                lng.use = True
                isocode = best_po[0]
                lng.po_path = isocodes[isocode]
                lng.po_path_trunk = os.path.join(root_tr_po, isocode + ".po")
                lng.mo_path_trunk = root_tr_mo.format(isocode)
            else:
                lng.use = False
                language, _1, _2, language_country, language_variant = utils_i18n.locale_explode(uid)
                for isocode in (language, language_variant, language_country, uid):
                    p = os.path.join(root_br, isocode, isocode + ".po")
                    if not os.path.exists(p):
                        lng.use = True
                        lng.po_path = p
                        lng.po_path_trunk = os.path.join(root_tr_po, isocode + ".po")
                        lng.mo_path_trunk = root_tr_mo.format(isocode)
                        break

        i18n_sett.pot_path = self.settings.FILE_NAME_POT
        i18n_sett.is_init = True
        return {'FINISHED'}


class UI_OT_i18n_updatetranslation_svn_settings_select(bpy.types.Operator):
    """(De)select (or invert selection of) all languages for i18n svn's update operators"""
    bl_idname = "ui.i18n_updatetranslation_svn_settings_select"
    bl_label = "Init I18n Update Select Languages"

    use_select = BoolProperty(name="Select All", default=True, description="Select all if True, else deselect all")
    use_invert = BoolProperty(name="Invert Selection", default=False,
                              description="Inverse selection (overrides 'Select All' when True)")

    @classmethod
    def poll(cls, context):
        return context.window_manager != None

    def execute(self, context):
        if self.use_invert:
            for lng in context.window_manager.i18n_update_svn_settings.langs:
                lng.use = not lng.use
        else:
            for lng in context.window_manager.i18n_update_svn_settings.langs:
                lng.use = self.use_select
        return {'FINISHED'}


class UI_OT_i18n_updatetranslation_svn_branches(bpy.types.Operator):
    """Update i18n svn's branches (po files)"""
    bl_idname = "ui.i18n_updatetranslation_svn_branches"
    bl_label = "Update I18n Branches"

    use_skip_pot_gen = BoolProperty(name="Skip POT", default=False, description="Skip POT file generation")

    def execute(self, context):
        if not hasattr(self, "settings"):
            self.settings = settings.settings
        i18n_sett = context.window_manager.i18n_update_svn_settings
        self.settings.FILE_NAME_POT = i18n_sett.pot_path

        if not self.use_skip_pot_gen:
            # Generate base pot from RNA messages (we use another blender instance here, to be able to perfectly
            # control our environment (factory startup, specific addons enabled/disabled...)).
            # However, we need to export current user settings about this addon!
            cmmd = (
                bpy.app.binary_path,
                "--background",
                "--factory-startup",
                "--python",
                os.path.join(os.path.dirname(utils_i18n.__file__), "bl_extract_messages.py"),
                "--",
                "bl_extract_messages.py",  # arg parser expects first arg to be prog name!
                "--settings",
                self.settings.to_json(),
            )
            if subprocess.call(cmmd):
                self.report({'ERROR'}, "Message extraction process failed!")
                return {'CANCELLED'}

        # Now we should have a valid POT file, we have to merge it in all languages po's...
        pot = utils_i18n.I18nMessages(kind='PO', src=self.settings.FILE_NAME_POT, settings=self.settings)
        for lng in i18n_sett.langs:
            if not lng.use:
                continue
            if os.path.isfile(lng.po_path):
                po = utils_i18n.I18nMessages(uid=lng.uid, kind='PO', src=lng.po_path, settings=self.settings)
                po.update(pot)
            else:
                po = pot
            po.write(kind="PO", dest=lng.po_path)
            print("{} PO written!".format(lng.uid))
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class UI_OT_i18n_updatetranslation_svn_trunk(bpy.types.Operator):
    """Update i18n svn's branches (po files)"""
    bl_idname = "ui.i18n_updatetranslation_svn_trunk"
    bl_label = "Update I18n Trunk"

    def execute(self, context):
        if not hasattr(self, "settings"):
            self.settings = settings.settings
        i18n_sett = context.window_manager.i18n_update_svn_settings
        # 'DEFAULT' and en_US are always valid, fully-translated "languages"!
        stats = {"DEFAULT": 1.0, "en_US": 1.0}

        for lng in i18n_sett.langs:
            if lng.uid in self.settings.IMPORT_LANGUAGES_SKIP:
                print("Skipping {} language ({}), edit settings if you want to enable it.".format(lng.name, lng.uid))
                continue
            if not lng.use:
                print("Skipping {} language ({}).".format(lng.name, lng.uid))
                continue
            print("Processing {} language ({}).".format(lng.name, lng.uid))
            po = utils_i18n.I18nMessages(uid=lng.uid, kind='PO', src=lng.po_path, settings=self.settings)
            print("Cleaned up {} commented messages.".format(po.clean_commented()))
            errs = po.check(fix=True)
            if errs:
                print("Errors in this po, solved as best as possible!")
                print("\t" + "\n\t".join(errs))
            if lng.uid in self.settings.IMPORT_LANGUAGES_RTL:
                po.write(kind="PO", dest=lng.po_path_trunk[:-3] + "_raw.po")
                po.rtl_process()
            po.write(kind="PO", dest=lng.po_path_trunk)
            po.write(kind="MO", dest=lng.mo_path_trunk)
            po.update_info()
            stats[lng.uid] = po.nbr_trans_msgs / po.nbr_msgs
            print("\n")

        # Copy pot file from branches to trunk.
        shutil.copy2(self.settings.FILE_NAME_POT, self.settings.TRUNK_PO_DIR)

        print("Generating languages' menu...")
        # First complete our statistics by checking po files we did not touch this time!
        po_to_uid = {os.path.basename(lng.po_path): lng.uid for lng in i18n_sett.langs}
        for po_path in os.listdir(self.settings.TRUNK_PO_DIR):
            uid = po_to_uid.get(po_path, None)
            po_path = os.path.join(self.settings.TRUNK_PO_DIR, po_path)
            if uid and uid not in stats:
                po = utils_i18n.I18nMessages(uid=uid, kind='PO', src=po_path, settings=self.settings)
                stats[uid] = po.nbr_trans_msgs / po.nbr_msgs
        utils_languages_menu.gen_menu_file(stats, self.settings)

        return {'FINISHED'}


class UI_OT_i18n_updatetranslation_svn_statistics(bpy.types.Operator):
    """Create or extend a 'i18n_info.txt' Text datablock containing statistics and checks about """
    """current branches and/or trunk"""
    bl_idname = "ui.i18n_updatetranslation_svn_statistics"
    bl_label = "Update I18n Statistics"

    use_branches = BoolProperty(name="Check Branches", default=True, description="Check po files in branches")
    use_trunk = BoolProperty(name="Check Trunk", default=False, description="Check po files in trunk")

    report_name = "i18n_info.txt"

    def execute(self, context):
        if not hasattr(self, "settings"):
            self.settings = settings.settings
        i18n_sett = context.window_manager.i18n_update_svn_settings

        buff = io.StringIO()
        lst = []
        if self.use_branches:
            lst += [(lng, lng.po_path) for lng in i18n_sett.langs]
        if self.use_trunk:
            lst += [(lng, lng.po_path_trunk) for lng in i18n_sett.langs
                                             if lng.uid not in self.settings.IMPORT_LANGUAGES_SKIP]

        for lng, path in lst:
            if not lng.use:
                print("Skipping {} language ({}).".format(lng.name, lng.uid))
                continue
            buff.write("Processing {} language ({}, {}).\n".format(lng.name, lng.uid, path))
            po = utils_i18n.I18nMessages(uid=lng.uid, kind='PO', src=path, settings=self.settings)
            po.print_info(prefix="    ", output=buff.write)
            errs = po.check(fix=False)
            if errs:
                buff.write("    WARNING! Po contains following errors:\n")
                buff.write("        " + "\n        ".join(errs))
                buff.write("\n")
            buff.write("\n\n")

        text = None
        if self.report_name not in bpy.data.texts:
            text = bpy.data.texts.new(self.report_name)
        else:
            text = bpy.data.texts[self.report_name]
        data = text.as_string()
        data = data + "\n" + buff.getvalue()
        text.from_string(data)
        self.report({'INFO'}, "Info written to {} text datablock!".format(self.report_name))

        return {'FINISHED'}


    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
