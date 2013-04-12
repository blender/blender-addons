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
    imp.reload(bl_extract_messages)
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
    from bl_i18n_utils import bl_extract_messages

from bpy.app.translations import pgettext_iface as iface_
import addon_utils

import io
import os
import shutil
import subprocess
import tempfile


##### Helpers #####
def validate_module(op, context):
    module_name = op.module_name
    addon = getattr(context, "active_addon", None)
    if addon:
        module_name = addon.module

    if not module_name:
        op.report({'ERROR'}, "No addon module given!")
        return None, None

    mod = utils_i18n.enable_addons(addons={module_name}, check_only=True)
    if not mod:
        op.report({'ERROR'}, "Addon '{}' not found!".format(module_name))
        return None, None
    return module_name, mod[0]


# As it's a bit time heavy, I'd like to cache that enum, but this does not seem easy to do! :/
# That "self" is not the same thing as the "self" that operators get in their invoke/execute/etc. funcs... :(
def enum_addons(self, context):
    setts = getattr(self, "settings", settings.settings)
    items = []
    for mod in addon_utils.modules(addon_utils.addons_fake_modules):
        mod_info = addon_utils.module_bl_info(mod)
        # Skip OFFICIAL addons, they are already translated in main i18n system (together with Blender itself).
        if mod_info["support"] in {'OFFICIAL'}:
            continue
        src = mod.__file__
        if src.endswith("__init__.py"):
            src = os.path.dirname(src)
        has_translation, _ = utils_i18n.I18n.check_py_module_has_translations(src, setts)
        name = mod_info["name"]
        # XXX Gives ugly UUUUUUUUUUUUUUUUUUU in search list!
        #if has_translation:
            #name = name + " *"
        items.append((mod.__name__, name, mod_info["description"]))
    items.sort(key=lambda i: i[1])
    return items


##### Data #####


##### UI #####
#class UI_PT_i18n_update_translations_settings(bpy.types.Panel):
    #bl_label = "I18n Update Translation Main"
    #bl_space_type = "PROPERTIES"
    #bl_region_type = "WINDOW"
    #bl_context = "render"
#
    #def draw(self, context):
        #layout = self.layout
        #i18n_sett = context.window_manager.i18n_update_svn_settings
#
        #if not i18n_sett.is_init and bpy.ops.ui.i18n_updatetranslation_svn_init_settings.poll():
            #bpy.ops.ui.i18n_updatetranslation_svn_init_settings()
#
        #if not i18n_sett.is_init:
            #layout.label(text="Could not init languages data!")
            #layout.label(text="Please edit the preferences of the UI Translate addon")
        #else:
            #split = layout.split(0.75)
            #split.template_list("UI_UL_i18n_languages", "", i18n_sett, "langs", i18n_sett, "active_lang", rows=8)
            #col = split.column()
            #col.operator("ui.i18n_updatetranslation_svn_init_settings", text="Reset Settings")
            #if any(l.use for l in i18n_sett.langs):
                #col.operator("ui.i18n_updatetranslation_svn_settings_select", text="Deselect All").use_select = False
            #else:
                #col.operator("ui.i18n_updatetranslation_svn_settings_select", text="Select All").use_select = True
            #col.operator("ui.i18n_updatetranslation_svn_settings_select", text="Invert Selection").use_invert = True
            #col.separator()
            #col.operator("ui.i18n_updatetranslation_svn_branches", text="Update Branches")
            #col.operator("ui.i18n_updatetranslation_svn_trunk", text="Update Trunk")
            #col.operator("ui.i18n_updatetranslation_svn_statistics", text="Statistics")
#
            #if i18n_sett.active_lang >= 0 and i18n_sett.active_lang < len(i18n_sett.langs):
                #lng = i18n_sett.langs[i18n_sett.active_lang]
                #col = layout.column()
                #col.active = lng.use
                #row = col.row()
                #row.label(text="[{}]: \"{}\" ({})".format(lng.uid, iface_(lng.name), lng.num_id), translate=False)
                #row.prop(lng, "use", text="")
                #col.prop(lng, "po_path")
                #col.prop(lng, "po_path_trunk")
                #col.prop(lng, "mo_path_trunk")
            #layout.separator()
            #layout.prop(i18n_sett, "pot_path")


##### Operators #####
# This one is a helper one, as we sometimes need another invoke function (like e.g. file selection)...
class UI_OT_i18n_addon_translation_invoke(bpy.types.Operator):
    """Wrapper operator which will invoke given op after setting its module_name"""
    bl_idname = "ui.i18n_addon_translation_invoke"
    bl_label = "Update I18n Addon"
    bl_property = "module_name"

    module_name = EnumProperty(items=enum_addons, name="Addon", description="Addon to process", options=set())
    op_id = StringProperty(name="Operator Name", description="Name (id) of the operator to invoke")
    # XXX Ugly hack! invoke_search_popup does not preserve ops' properties :(
    _op_id = ""

    def invoke(self, context, event):
        print("op_id:", self.op_id)
        # XXX Ugly hack! invoke_search_popup does not preserve ops' properties :(
        self.__class__._op_id = self.op_id
        context.window_manager.invoke_search_popup(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        print("op_id:", self.op_id, self.__class__._op_id)
        if not self.op_id:
            # XXX Ugly hack! invoke_search_popup does not preserve ops' properties :(
            if not self.__class__._op_id:
                return {'CANCELLED'}
            self.op_id = self.__class__._op_id
            self.__class__._op_id = ""
        op = bpy.ops
        for item in self.op_id.split('.'):
            op = getattr(op, item, None)
            print(self.op_id, item, op)
            if op is None:
                return {'CANCELLED'}
        return op('INVOKE_DEFAULT', module_name=self.module_name)

class UI_OT_i18n_addon_translation_update(bpy.types.Operator):
    """Update given addon's translation data (found as a py tuple in the addon's source code)"""
    bl_idname = "ui.i18n_addon_translation_update"
    bl_label = "Update I18n Addon"

    module_name = EnumProperty(items=enum_addons, name="Addon", description="Addon to process", options=set())

    def execute(self, context):
        if not hasattr(self, "settings"):
            self.settings = settings.settings
        i18n_sett = context.window_manager.i18n_update_svn_settings

        module_name, mod = validate_module(self, context)

        # Generate addon-specific messages (no need for another blender instance here, this should not have any
        # influence over the final result).
        pot = bl_extract_messages.dump_addon_messages(module_name, True, self.settings)

        # Now (try do) get current i18n data from the addon...
        path = mod.__file__
        if path.endswith("__init__.py"):
            path = os.path.dirname(path)

        trans = utils_i18n.I18n(kind='PY', src=path, settings=self.settings)

        uids = set()
        for lng in i18n_sett.langs:
            if lng.uid in self.settings.IMPORT_LANGUAGES_SKIP:
                print("Skipping {} language ({}), edit settings if you want to enable it.".format(lng.name, lng.uid))
                continue
            if not lng.use:
                print("Skipping {} language ({}).".format(lng.name, lng.uid))
                continue
            uids.add(lng.uid)
        # For now, add to processed uids all those not found in "official" list, minus "tech" ones.
        uids |= (trans.trans.keys() - {lng.uid for lng in i18n_sett.langs} -
                                      {self.settings.PARSER_TEMPLATE_ID, self.settings.PARSER_PY_ID})

        # And merge!
        for uid in uids:
            if uid not in trans.trans:
                trans.trans[uid] = utils_i18n.I18nMessages(uid=uid, settings=self.settings)
            trans.trans[uid].update(pot, keep_old_commented=False)
        trans.trans[self.settings.PARSER_TEMPLATE_ID] = pot

        # For now we write all languages found in this trans!
        trans.write(kind='PY')

        return {'FINISHED'}


class UI_OT_i18n_addon_translation_export(bpy.types.Operator):
    """Export given addon's translation data as a PO file"""
    bl_idname = "ui.i18n_addon_translation_export"
    bl_label = "I18n Addon Export"

    module_name = EnumProperty(items=enum_addons, name="Addon", description="Addon to process", options=set())
    use_export_pot = BoolProperty(name="Export POT", default=True, description="Export (generate) a POT file too")
    use_update_existing = BoolProperty(name="Update Existing", default=True,
                                       description="Update existing po files, if any, instead of overwriting them")
    directory = StringProperty(maxlen=1024, subtype='FILE_PATH', options={'HIDDEN', 'SKIP_SAVE'})

    def _dst(self, trans, path, uid, kind):
        if kind == 'PO':
            if uid == self.settings.PARSER_TEMPLATE_ID:
                return os.path.join(self.directory, "blender.pot")
            path = os.path.join(self.directory, uid)
            if os.path.isdir(path):
                return os.path.join(path, uid + ".po")
            return path + ".po"
        elif kind == 'PY':
            return trans._dst(trans, path, uid, kind)
        return path

    def invoke(self, context, event):
        if not hasattr(self, "settings"):
            self.settings = settings.settings
        module_name, mod = validate_module(self, context)
        if mod:
            self.directory = os.path.dirname(mod.__file__)
            self.module_name = module_name
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if not hasattr(self, "settings"):
            self.settings = settings.settings
        i18n_sett = context.window_manager.i18n_update_svn_settings

        module_name, mod = validate_module(self, context)
        if not (module_name and mod):
            return {'CANCELLED'}

        path = mod.__file__
        if path.endswith("__init__.py"):
            path = os.path.dirname(path)

        trans = utils_i18n.I18n(kind='PY', src=path, settings=self.settings)
        trans.dst = self._dst

        uids = [self.settings.PARSER_TEMPLATE_ID] if self.use_export_pot else []
        for lng in i18n_sett.langs:
            if lng.uid in self.settings.IMPORT_LANGUAGES_SKIP:
                print("Skipping {} language ({}), edit settings if you want to enable it.".format(lng.name, lng.uid))
                continue
            if not lng.use:
                print("Skipping {} language ({}).".format(lng.name, lng.uid))
                continue
            uid = utils_i18n.find_best_isocode_matches(lng.uid, trans.trans.keys())
            if uid:
                uids.append(uid[0])

        # Try to update existing POs instead of overwriting them, if asked to do so!
        if self.use_update_existing:
            for uid in uids:
                if uid == self.settings.PARSER_TEMPLATE_ID:
                    continue
                path = trans.dst(trans, trans.src[uid], uid, 'PO')
                if not os.path.isfile(path):
                    continue
                msgs = utils_i18n.I18nMessages(kind='PO', src=path, settings=self.settings)
                msgs.update(trans.msgs[self.settings.PARSER_TEMPLATE_ID])
                trans.msgs[uid] = msgs

        trans.write(kind='PO', langs=set(uids))

        return {'FINISHED'}


