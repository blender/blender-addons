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

# ##### CHANGELOG #####
#
#  0.0.1
#      Initial release.
#
#  0.0.2
#      Updates to follow Blender API:
#        * bl_addon_info renamed in bl_info!
#        * adding bpy.utils.(un)register_module calls.
#      Also, in standard import, using “from . import …” now.
#
#  0.1.0
#      Renamed in “Render Copy Settings”.
#      Huge changes:
#        * It is now possible to individually copy each render setting.
#        * It is now possible to individually select each affected scene, and then filter them out
#          even further with a regex.
#      WARNING: this addon now needs a Blender patched with the ui_template_list diff, else it won’t
#               be fully functional…
#
#  0.1.1
#      Minor changes:
#        * PEP8 compliant.
#        * Moved to contrib…
#      WARNING: this addon now needs a Blender patched with the ui_template_list diff, else it won’t
#               be fully functional (even though working)…
#
#  0.1.2
#      Minor changes:
#        * Updated accordingly to the changes in enhanced ui_template_list proposal.
#      WARNING: this addon now needs a Blender patched with the ui_template_list diff, else it won’t
#               be fully functional (even though working)…
#
#  0.1.3
#      Minor changes:
#        * Fixed a small bug that was disabling the whole UI when entering a filtering regex
#          matching no scene.
#      WARNING: this addon now needs a Blender patched with the ui_template_list diff, else it won’t
#               be fully functional (even though working)…
#
# ##### END OF CHANGELOG #####

bl_info = {
    "name": "Copy Settings",
    "author": "Bastien Montagne",
    "version": (0, 1, 4),
    "blender": (2, 6, 1),
    "api": 42648,
    "location": "Render buttons (Properties window)",
    "description": "Allows to copy a selection of render settings from current scene to others.",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"\
                "Scripts/Render/Copy Settings",
    "tracker_url": "http://projects.blender.org/tracker/index.php?func=detail&aid=25832",
    "category": "Render"}


if "bpy" in locals():
    import imp
    imp.reload(operator)
    imp.reload(panel)

else:
    from . import operator, panel


import bpy
from bpy.props import StringProperty, BoolProperty, IntProperty, CollectionProperty


####################################################################################################
# Global properties for the script, for UI (as there’s no way to let them in the operator…).
####################################################################################################

class RenderCopySettingsScene(bpy.types.PropertyGroup):
    allowed = BoolProperty(default=True)

    # A string of identifiers (colon delimited) which property’s controls should be displayed
    # in a template_list.
    template_list_controls = StringProperty(default="allowed", options={"HIDDEN"})


class RenderCopySettingsSetting(bpy.types.PropertyGroup):
    strid = StringProperty(default="")
    copy = BoolProperty(default=False)

    # A string of identifiers (colon delimited) which property’s controls should be displayed
    # in a template_list.
    template_list_controls = StringProperty(default="copy", options={"HIDDEN"})


class RenderCopySettings(bpy.types.PropertyGroup):
    # XXX: The consistency of this collection is delegated to the UI code.
    #      It should only contain one element for each render setting.
    affected_settings = CollectionProperty(type=RenderCopySettingsSetting,
                                           name="Affected Settings",
                                           description="The list of all available render settings")
    # XXX Unused, but needed for template_list…
    aff_sett_idx = IntProperty()

    # XXX: The consistency of this collection is delegated to the UI code.
    #      It should only contain one element for each scene.
    allowed_scenes = CollectionProperty(type=RenderCopySettingsScene,
                                        name="Allowed Scenes",
                                        description="The list all scenes in the file")
    # XXX Unused, but needed for template_list…
    allw_scenes_idx = IntProperty()

    filter_scene = StringProperty(name="Filter Scene",
                                  description="Regex to only affect scenes which name matches it",
                                  default="")


def register():
    # Register properties.
    bpy.utils.register_class(RenderCopySettingsScene)
    bpy.utils.register_class(RenderCopySettingsSetting)
    bpy.utils.register_class(RenderCopySettings)
    bpy.types.Scene.render_copy_settings = \
        bpy.props.PointerProperty(type=RenderCopySettings)

    bpy.utils.register_module(__name__)


def unregister():
    # Unregister properties.
    bpy.utils.unregister_class(RenderCopySettingsScene)
    bpy.utils.unregister_class(RenderCopySettingsSetting)
    bpy.utils.unregister_class(RenderCopySettings)
    del bpy.types.Scene.render_copy_settings

    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
