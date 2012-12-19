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

bl_info = {
    "name": "Translate UI Messages",
    "author": "Bastien Montagne",
    "blender": (2, 63, 0),
    "location": "Any UI control",
    "description": "Allow to translate UI directly from Blender",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "support": 'OFFICIAL',
    "category": "System"}

if "bpy" in locals():
    import imp
    if "ui_utils" in locals():
        imp.reload(ui_utils)
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
    from . import utils as ui_utils

from bl_i18n_utils import utils as i18n_utils
from bl_i18n_utils import update_mo
#from bl_i18n_utils import settings

import os
import shutil


# module-level cache, as parsing po files takes a few seconds...
# Keys are po file paths, data are the results of i18n_utils.parse_messages().
PO_CACHE = {}


def clear_caches(key):
    del PO_CACHE[key]
    del ui_utils.WORK_CACHE[key]


class UI_OT_edittranslation_update_mo(bpy.types.Operator):
    """Try to "compile" given po file into relevant blender.mo file """ \
    """(WARNING: it will replace the official mo file in your user dir!)"""
    bl_idname = "ui.edittranslation_update_mo"
    bl_label = "Edit Translation Update Mo"

    # "Parameters"
    lang = StringProperty(description="Current (translated) language",
                          options={'SKIP_SAVE'})
    po_file = StringProperty(description="Path to the matching po file",
                             subtype='FILE_PATH', options={'SKIP_SAVE'})
    clean_mo = BoolProperty(description="Clean up (remove) all local "
                                        "translation files, to be able to use "
                                        "all system's ones again",
                            default=False, options={'SKIP_SAVE'})

    def execute(self, context):
        if self.clean_mo:
            root = bpy.utils.user_resource('DATAFILES', ui_utils.MO_PATH_ROOT)
            if root:
                shutil.rmtree(root)

        elif not self.lang or not self.po_file:
            return {'CANCELLED'}

        else:
            mo_dir = bpy.utils.user_resource(
                         'DATAFILES', ui_utils.MO_PATH_TEMPLATE.format(self.lang),
                         create=True)
            mo_file = os.path.join(mo_dir, ui_utils.MO_FILENAME)
            update_mo.process_po(self.po_file, None, mo_file)

        bpy.ops.ui.reloadtranslation()
        return {'FINISHED'}


class UI_OT_edittranslation(bpy.types.Operator):
    """Translate the label and tool tip of the property defined by given 'parameters'"""
    bl_idname = "ui.edittranslation"
    bl_label = "Edit Translation"

    # "Parameters"
    but_label = StringProperty(description="Label of the control", options={'SKIP_SAVE'})
    rna_label = StringProperty(description="RNA-defined label of the control, if any", options={'SKIP_SAVE'})
    enum_label = StringProperty(description="Label of the enum item of the control, if any", options={'SKIP_SAVE'})
    but_tip = StringProperty(description="Tip of the control", options={'SKIP_SAVE'})
    rna_tip = StringProperty(description="RNA-defined tip of the control, if any", options={'SKIP_SAVE'})
    enum_tip = StringProperty(description="Tip of the enum item of the control, if any", options={'SKIP_SAVE'})
    rna_struct = StringProperty(description="Identifier of the RNA struct, if any", options={'SKIP_SAVE'})
    rna_prop = StringProperty(description="Identifier of the RNA property, if any", options={'SKIP_SAVE'})
    rna_enum = StringProperty(description="Identifier of the RNA enum item, if any", options={'SKIP_SAVE'})
    rna_ctxt = StringProperty(description="RNA context for label", options={'SKIP_SAVE'})

    lang = StringProperty(description="Current (translated) language", options={'SKIP_SAVE'})
    po_file = StringProperty(description="Path to the matching po file", subtype='FILE_PATH', options={'SKIP_SAVE'})

    # Found in po file.
    org_but_label = StringProperty(description="Original label of the control", options={'SKIP_SAVE'})
    org_rna_label = StringProperty(description="Original RNA-defined label of the control, if any", options={'SKIP_SAVE'})
    org_enum_label = StringProperty(description="Original label of the enum item of the control, if any", options={'SKIP_SAVE'})
    org_but_tip = StringProperty(description="Original tip of the control", options={'SKIP_SAVE'})
    org_rna_tip = StringProperty(description="Original RNA-defined tip of the control, if any", options={'SKIP_SAVE'})
    org_enum_tip = StringProperty(description="Original tip of the enum item of the control, if any", options={'SKIP_SAVE'})

    flag_items = (('FUZZY', "Fuzzy", "Message is marked as fuzzy in po file"),
                  ('ERROR', "Error", "Some error occurred with this message"),
                 )
    but_label_flags = EnumProperty(items=flag_items, description="Flags about the label of the button", options={'SKIP_SAVE', 'ENUM_FLAG'})
    rna_label_flags = EnumProperty(items=flag_items, description="Flags about the RNA-defined label of the button", options={'SKIP_SAVE', 'ENUM_FLAG'})
    enum_label_flags = EnumProperty(items=flag_items, description="Flags about the RNA enum item label of the button", options={'SKIP_SAVE', 'ENUM_FLAG'})
    but_tip_flags = EnumProperty(items=flag_items, description="Flags about the tip of the button", options={'SKIP_SAVE', 'ENUM_FLAG'})
    rna_tip_flags = EnumProperty(items=flag_items, description="Flags about the RNA-defined tip of the button", options={'SKIP_SAVE', 'ENUM_FLAG'})
    enum_tip_flags = EnumProperty(items=flag_items, description="Flags about the RNA enum item tip of the button", options={'SKIP_SAVE', 'ENUM_FLAG'})

    stats_str = StringProperty(description="Stats from opened po", options={'SKIP_SAVE'})
    update_po = BoolProperty(description="Update po file, try to rebuild mo file, and refresh Blender UI", default=False, options={'SKIP_SAVE'})
    update_mo = BoolProperty(description="Try to rebuild mo file, and refresh Blender UI (WARNING: you should use a local Blender installation, as you probably have no right to write in the system Blender installation...)", default=False, options={'SKIP_SAVE'})
    clean_mo = BoolProperty(description="Clean up (remove) all local "
                                        "translation files, to be able to use "
                                        "all system's ones again",
                            default=False, options={'SKIP_SAVE'})

    def execute(self, context):
        if not hasattr(self, "msgmap"):
            # We must be invoked() first!
            return {'CANCELLED'}
        msgs, state, stats = PO_CACHE[self.po_file]

        done_keys = set()
        for mmap in self.msgmap.values():
            if 'ERROR' in getattr(self, mmap["msg_flags"]):
                continue
            k = mmap["key"]
#            print(k)
            if k not in done_keys and len(k) == 1:
                k = tuple(k)[0]
                msgs[k]["msgstr_lines"] = [getattr(self, mmap["msgstr"])]
                if k in state["fuzzy_msg"] and 'FUZZY' not in getattr(self, mmap["msg_flags"]):
                    state["fuzzy_msg"].remove(k)
                elif k not in state["fuzzy_msg"] and 'FUZZY' in getattr(self, mmap["msg_flags"]):
                    state["fuzzy_msg"].add(k)
                done_keys.add(k)

        if self.update_po:
            # Try to overwrite po file, may fail if we have no good rights...
            try:
                i18n_utils.write_messages(self.po_file, msgs, state["comm_msg"], state["fuzzy_msg"])
            except Exception as e:
                self.report('ERROR', "Could not write to po file ({})".format(str(e)))
            # Always invalidate all caches afterward!
            clear_caches(self.po_file)
        if self.update_mo:
            lang = os.path.splitext(os.path.basename(self.po_file))[0]
            bpy.ops.ui.edittranslation_update_mo(po_file=self.po_file, lang=lang)
        elif self.clean_mo:
            bpy.ops.ui.edittranslation_update_mo(clean_mo=True)
        return {'FINISHED'}

    def invoke(self, context, event):
        if self.po_file in PO_CACHE:
            msgs, state, stats = PO_CACHE[self.po_file]
        else:
            msgs, state, stats = PO_CACHE.setdefault(self.po_file, i18n_utils.parse_messages(self.po_file))

        self.msgmap = {"but_label": {"msgstr": "but_label", "msgid": "org_but_label", "msg_flags": "but_label_flags", "key": set()},
                       "rna_label": {"msgstr": "rna_label", "msgid": "org_rna_label", "msg_flags": "rna_label_flags", "key": set()},
                       "enum_label": {"msgstr": "enum_label", "msgid": "org_enum_label", "msg_flags": "enum_label_flags", "key": set()},
                       "but_tip": {"msgstr": "but_tip", "msgid": "org_but_tip", "msg_flags": "but_tip_flags", "key": set()},
                       "rna_tip": {"msgstr": "rna_tip", "msgid": "org_rna_tip", "msg_flags": "rna_tip_flags", "key": set()},
                       "enum_tip": {"msgstr": "enum_tip", "msgid": "org_enum_tip", "msg_flags": "enum_tip_flags", "key": set()},
                      }

        ui_utils.find_best_msgs_matches(self, self.po_file, self.msgmap, msgs, state, self.rna_ctxt,
                                        self.rna_struct, self.rna_prop, self.rna_enum)
        self.stats_str = "{}: {} messages, {} translated.".format(os.path.basename(self.po_file), stats["tot_msg"], stats["trans_msg"])

        for mmap in self.msgmap.values():
            k = tuple(mmap["key"])
            if k:
                if len(k) == 1:
                    k = k[0]
                    ctxt, msgid = k
                    setattr(self, mmap["msgstr"], "".join(msgs[k]["msgstr_lines"]))
                    setattr(self, mmap["msgid"], msgid)
                    if k in state["fuzzy_msg"]:
                        setattr(self, mmap["msg_flags"], {'FUZZY'})
                else:
                    setattr(self, mmap["msgid"], "ERROR: Button label “{}” matches none or several messages in po file ({})!".format(self.but_label, k))
                    setattr(self, mmap["msg_flags"], {'ERROR'})
            else:
                setattr(self, mmap["msgstr"], "")
                setattr(self, mmap["msgid"], "")

        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=600)

    def draw(self, context):
        layout = self.layout
        layout.label(text=self.stats_str)
        src, _a, _b = ui_utils.bpy_path(self.rna_struct, self.rna_prop, self.rna_enum)
        if src:
            layout.label(text="    RNA Path: bpy.types." + src)
        if self.rna_ctxt:
            layout.label(text="    RNA Context: " + self.rna_ctxt)

        if self.org_but_label or self.org_rna_label or self.org_enum_label:
            # XXX Can't use box, labels are not enought readable in them :/
#            box = layout.box()
            box = layout
            box.label(text="Labels:")
            split = box.split(percentage=0.15)
            col1 = split.column()
            col2 = split.column()
            if self.org_but_label:
                col1.label(text="Button Label:")
                row = col2.row()
                row.enabled = False
                if 'ERROR' in self.but_label_flags:
                    row.alert = True
                else:
                    col1.prop_enum(self, "but_label_flags", 'FUZZY', text="Fuzzy")
                    col2.prop(self, "but_label", text="")
                row.prop(self, "org_but_label", text="")
            if self.org_rna_label:
                col1.label(text="RNA Label:")
                row = col2.row()
                row.enabled = False
                if 'ERROR' in self.rna_label_flags:
                    row.alert = True
                else:
                    col1.prop_enum(self, "rna_label_flags", 'FUZZY', text="Fuzzy")
                    col2.prop(self, "rna_label", text="")
                row.prop(self, "org_rna_label", text="")
            if self.org_enum_label:
                col1.label(text="Enum Item Label:")
                row = col2.row()
                row.enabled = False
                if 'ERROR' in self.enum_label_flags:
                    row.alert = True
                else:
                    col1.prop_enum(self, "enum_label_flags", 'FUZZY', text="Fuzzy")
                    col2.prop(self, "enum_label", text="")
                row.prop(self, "org_enum_label", text="")

        if self.org_but_tip or self.org_rna_tip or self.org_enum_tip:
            # XXX Can't use box, labels are not enought readable in them :/
#            box = layout.box()
            box = layout
            box.label(text="Tool Tips:")
            split = box.split(percentage=0.15)
            col1 = split.column()
            col2 = split.column()
            if self.org_but_tip:
                col1.label(text="Button Tip:")
                row = col2.row()
                row.enabled = False
                if 'ERROR' in self.but_tip_flags:
                    row.alert = True
                else:
                    col1.prop_enum(self, "but_tip_flags", 'FUZZY', text="Fuzzy")
                    col2.prop(self, "but_tip", text="")
                row.prop(self, "org_but_tip", text="")
            if self.org_rna_tip:
                col1.label(text="RNA Tip:")
                row = col2.row()
                row.enabled = False
                if 'ERROR' in self.rna_tip_flags:
                    row.alert = True
                else:
                    col1.prop_enum(self, "rna_tip_flags", 'FUZZY', text="Fuzzy")
                    col2.prop(self, "rna_tip", text="")
                row.prop(self, "org_rna_tip", text="")
            if self.org_enum_tip:
                col1.label(text="Enum Item Tip:")
                row = col2.row()
                row.enabled = False
                if 'ERROR' in self.enum_tip_flags:
                    row.alert = True
                else:
                    col1.prop_enum(self, "enum_tip_flags", 'FUZZY', text="Fuzzy")
                    col2.prop(self, "enum_tip", text="")
                row.prop(self, "org_enum_tip", text="")

        row = layout.row()
        row.prop(self, "update_po", text="Save to PO File", toggle=True)
        row.prop(self, "update_mo", text="Rebuild MO File", toggle=True)
        row.prop(self, "clean_mo", text="Erase Local MO files", toggle=True)


def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
