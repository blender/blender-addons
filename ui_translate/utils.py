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

#from bl_i18n_utils import utils as i18n_utils
from bl_i18n_utils import settings

import os


# module-level cache, as parsing po files takes a few seconds...
# Keys are po file paths, data are the results of i18n_utils.parse_messages().
WORK_CACHE = {}

# Same as in BLF_translation.h
BLF_I18NCONTEXT_DEFAULT = ""


# Num buttons report their label with a trailing ': '...
NUM_BUTTON_SUFFIX = ": "


# Mo root datapath.
MO_PATH_ROOT = "locale"

# Mo path generator for a given language.
MO_PATH_TEMPLATE = os.path.join(MO_PATH_ROOT, "{}", "LC_MESSAGES")

# Mo filename.
MO_FILENAME = "blender.mo"


def bpy_path(rstruct, rprop, renum):
    src = src_rna = src_enum = ""
    if rstruct:
        if rprop:
            src = src_rna = ".".join((rstruct, rprop))
            if renum:
                src = src_enum = "{}.{}:'{}'".format(rstruct, rprop, renum)
        else:
            src = src_rna = rstruct
    return src, src_rna, src_enum


def find_best_msgs_matches(obj, cache_key, msgmap, msgs, state, rna_ctxt, rstruct, rprop, renum):
    comm_prfx = settings.COMMENT_PREFIX_SOURCE + "bpy.types."

    # Build helper mappings.
    # XXX We do not update this cache when editing a translation, as it would
    #     prevent the same msgid/msgstr to be find again.
    #     We only invalidate the cache once new po/mo have been generated!
    if cache_key in WORK_CACHE:
        src_to_msg, ctxt_to_msg, msgid_to_msg, msgstr_to_msg = WORK_CACHE[cache_key]
    else:
        src_to_msg = {}
        ctxt_to_msg = {}
        msgid_to_msg = {}
        msgstr_to_msg = {}
        for key, val in msgs.items():
            ctxt, msgid = key
            if key in state["comm_msg"]:
                continue
            ctxt_to_msg.setdefault(ctxt, set()).add(key)
            msgid_to_msg.setdefault(msgid, set()).add(key)
            msgstr_to_msg.setdefault("".join(val["msgstr_lines"]), set()).add(key)
            for comm in val["comment_lines"]:
                if comm.startswith(comm_prfx):
                    comm = comm[len(comm_prfx):]
                    src_to_msg.setdefault(comm, set()).add(key)
        WORK_CACHE[cache_key] = (src_to_msg, ctxt_to_msg, msgid_to_msg, msgstr_to_msg)

#    print(len(src_to_msg), len(ctxt_to_msg), len(msgid_to_msg), len(msgstr_to_msg))

    # Build RNA key.
    src, src_rna, src_enum = bpy_path(rstruct, rprop, renum)
    print("src: ", src_rna, src_enum)

    # Labels.
    elbl = getattr(obj, msgmap["enum_label"]["msgstr"])
    print("enum label: %r" % elbl)
    if elbl:
        # Enum items' labels have no i18n context...
        k = ctxt_to_msg[BLF_I18NCONTEXT_DEFAULT].copy()
        if elbl in msgid_to_msg:
            k &= msgid_to_msg[elbl]
        elif elbl in msgstr_to_msg:
            k &= msgstr_to_msg[elbl]
        else:
            k = set()
        # We assume if we already have only one key, it's the good one!
        if len(k) > 1 and src_enum in src_to_msg:
            k &= src_to_msg[src_enum]
        msgmap["enum_label"]["key"] = k
    rlbl = getattr(obj, msgmap["rna_label"]["msgstr"])
    print("rna label: %r" % rlbl, rlbl in msgid_to_msg, rlbl in msgstr_to_msg)
    if rlbl:
        k = ctxt_to_msg[rna_ctxt].copy()
        if k and rlbl in msgid_to_msg:
            k &= msgid_to_msg[rlbl]
        elif k and rlbl in msgstr_to_msg:
            k &= msgstr_to_msg[rlbl]
        else:
            k = set()
        # We assume if we already have only one key, it's the good one!
        if len(k) > 1 and src_rna in src_to_msg:
            k &= src_to_msg[src_rna]
        msgmap["rna_label"]["key"] = k
    blbl = getattr(obj, msgmap["but_label"]["msgstr"])
    blbls = [blbl]
    if blbl.endswith(NUM_BUTTON_SUFFIX):
        # Num buttons report their label with a trailing ': '...
        blbls.append(blbl[:-len(NUM_BUTTON_SUFFIX)])
    print("button label: %r" % blbl)
    if blbl and elbl not in blbls and (rlbl not in blbls or rna_ctxt != BLF_I18NCONTEXT_DEFAULT):
        # Always Default context for button label :/
        k = ctxt_to_msg[BLF_I18NCONTEXT_DEFAULT].copy()
        found = False
        for bl in blbls:
            if bl in msgid_to_msg:
                k &= msgid_to_msg[bl]
                found = True
                break
            elif bl in msgstr_to_msg:
                k &= msgstr_to_msg[bl]
                found = True
                break
        if not found:
            k = set()
        # XXX No need to check against RNA path here, if blabel is different
        #     from rlabel, should not match anyway!
        msgmap["but_label"]["key"] = k

    # Tips (they never have a specific context).
    etip = getattr(obj, msgmap["enum_tip"]["msgstr"])
    print("enum tip: %r" % etip)
    if etip:
        k = ctxt_to_msg[BLF_I18NCONTEXT_DEFAULT].copy()
        if etip in msgid_to_msg:
            k &= msgid_to_msg[etip]
        elif etip in msgstr_to_msg:
            k &= msgstr_to_msg[etip]
        else:
            k = set()
        # We assume if we already have only one key, it's the good one!
        if len(k) > 1 and src_enum in src_to_msg:
            k &= src_to_msg[src_enum]
        msgmap["enum_tip"]["key"] = k
    rtip = getattr(obj, msgmap["rna_tip"]["msgstr"])
    print("rna tip: %r" % rtip)
    if rtip:
        k = ctxt_to_msg[BLF_I18NCONTEXT_DEFAULT].copy()
        if k and rtip in msgid_to_msg:
            k &= msgid_to_msg[rtip]
        elif k and rtip in msgstr_to_msg:
            k &= msgstr_to_msg[rtip]
        else:
            k = set()
        # We assume if we already have only one key, it's the good one!
        if len(k) > 1 and src_rna in src_to_msg:
            k &= src_to_msg[src_rna]
        msgmap["rna_tip"]["key"] = k
        print(k)
    btip = getattr(obj, msgmap["but_tip"]["msgstr"])
    print("button tip: %r" % btip)
    if btip and btip not in {rtip, etip}:
        k = ctxt_to_msg[BLF_I18NCONTEXT_DEFAULT].copy()
        if btip in msgid_to_msg:
            k &= msgid_to_msg[btip]
        elif btip in msgstr_to_msg:
            k &= msgstr_to_msg[btip]
        else:
            k = set()
        # XXX No need to check against RNA path here, if btip is different
        #     from rtip, should not match anyway!
        msgmap["but_tip"]["key"] = k
