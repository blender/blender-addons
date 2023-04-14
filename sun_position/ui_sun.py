# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import Operator, Menu
from bl_operators.presets import AddPresetBase
import os
from math import degrees

from .sun_calc import format_lat_long, format_time, format_hms, sun


# -------------------------------------------------------------------
# Choice list of places, month and day at 12:00 noon
# -------------------------------------------------------------------


class SUNPOS_MT_Presets(Menu):
    bl_label = "Sun Position Presets"
    preset_subdir = "operator/sun_position"
    preset_operator = "script.execute_preset"
    draw = Menu.draw_preset


class SUNPOS_OT_AddPreset(AddPresetBase, Operator):
    '''Add Sun Position preset'''
    bl_idname = "world.sunpos_add_preset"
    bl_label = "Add Sun Position preset"
    preset_menu = "SUNPOS_MT_Presets"

    # variable used for all preset values
    preset_defines = [
        "sun_props = bpy.context.scene.sun_pos_properties"
    ]

    # properties to store in the preset
    preset_values = [
        "sun_props.day",
        "sun_props.month",
        "sun_props.time",
        "sun_props.year",
        "sun_props.UTC_zone",
        "sun_props.use_daylight_savings",
        "sun_props.latitude",
        "sun_props.longitude",
    ]

    # where to store the preset
    preset_subdir = "operator/sun_position"


# -------------------------------------------------------------------
#
#   Draw the Sun Panel, sliders, et. al.
#
# -------------------------------------------------------------------

class SUNPOS_PT_Panel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "world"
    bl_label = "Sun Position"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        sp = context.scene.sun_pos_properties
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(sp, "usage_mode", expand=True)
        layout.separator()

        if sp.usage_mode == "HDR":
            self.draw_environment_mode_panel(context)
        else:
            self.draw_normal_mode_panel(context)

    def draw_environment_mode_panel(self, context):
        sp = context.scene.sun_pos_properties
        layout = self.layout

        col = layout.column(align=True)
        col.prop_search(sp, "sun_object",
                        context.view_layer, "objects")
        if context.scene.world is not None:
            if context.scene.world.node_tree is not None:
                col.prop_search(sp, "hdr_texture",
                                context.scene.world.node_tree, "nodes")
            else:
                col.label(text="Please activate Use Nodes in the World panel.",
                          icon="ERROR")
        else:
            col.label(text="Please select World in the World panel.",
                      icon="ERROR")

        layout.use_property_decorate = True

        col = layout.column(align=True)
        col.prop(sp, "bind_to_sun", text="Bind Texture to Sun")
        col.prop(sp, "hdr_azimuth")
        row = col.row(align=True)
        row.active = not sp.bind_to_sun
        row.prop(sp, "hdr_elevation")
        col.prop(sp, "sun_distance")
        col.separator()

        col = layout.column(align=True)
        row = col.row(align=True)
        row.enabled = not sp.bind_to_sun
        row.operator("world.sunpos_show_hdr", icon='LIGHT_SUN')

    def draw_normal_mode_panel(self, context):
        sp = context.scene.sun_pos_properties
        prefs = context.preferences.addons[__package__].preferences
        layout = self.layout

        if prefs.show_time_place:
            row = layout.row(align=True)
            row.menu(SUNPOS_MT_Presets.__name__, text=SUNPOS_MT_Presets.bl_label)
            row.operator(SUNPOS_OT_AddPreset.bl_idname, text="", icon='ADD')
            row.operator(SUNPOS_OT_AddPreset.bl_idname, text="", icon='REMOVE').remove_active = True

        col = layout.column(align=True)
        col.prop(sp, "sun_object")
        col.separator()

        col.prop(sp, "object_collection")
        if sp.object_collection:
            col.prop(sp, "object_collection_type")
            if sp.object_collection_type == 'DIURNAL':
                col.prop(sp, "time_spread")
        col.separator()

        if context.scene.world is not None:
            if context.scene.world.node_tree is not None:
                col.prop_search(sp, "sky_texture",
                                context.scene.world.node_tree, "nodes")
            else:
                col.label(text="Please activate Use Nodes in the World panel.",
                          icon="ERROR")
        else:
            col.label(text="Please select World in the World panel.",
                      icon="ERROR")

        if prefs.show_overlays:
            col = layout.column(align=True, heading="Show")
            col.prop(sp, "show_north", text="North")
            col.prop(sp, "show_analemmas", text="Analemmas")
            col.prop(sp, "show_surface", text="Surface")

        if prefs.show_refraction:
            col = layout.column(align=True, heading="Use")
            col.prop(sp, "use_refraction", text="Refraction")


class SUNPOS_PT_Location(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "world"
    bl_label = "Location"
    bl_parent_id = "SUNPOS_PT_Panel"

    @classmethod
    def poll(self, context):
        sp = context.scene.sun_pos_properties
        return sp.usage_mode != "HDR"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        sp = context.scene.sun_pos_properties
        prefs = context.preferences.addons[__package__].preferences

        col = layout.column(align=True)
        col.prop(sp, "coordinates", icon='URL')
        col.prop(sp, "latitude")
        col.prop(sp, "longitude")

        col.separator()

        col = layout.column(align=True)
        col.prop(sp, "north_offset", text="North Offset")

        if prefs.show_az_el:
            col = layout.column(align=True)
            col.prop(sp, "sun_elevation", text="Elevation")
            col.prop(sp, "sun_azimuth", text="Azimuth")
            col.separator()

        col = layout.column()
        col.prop(sp, "sun_distance")
        col.separator()


class SUNPOS_PT_Time(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "world"
    bl_label = "Time"
    bl_parent_id = "SUNPOS_PT_Panel"

    @classmethod
    def poll(self, context):
        sp = context.scene.sun_pos_properties
        return sp.usage_mode != "HDR"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        sp = context.scene.sun_pos_properties
        prefs = context.preferences.addons[__package__].preferences

        col = layout.column(align=True)
        col.prop(sp, "use_day_of_year")
        if sp.use_day_of_year:
            col.prop(sp, "day_of_year")
        else:
            col.prop(sp, "day")
            col.prop(sp, "month")
        col.prop(sp, "year")
        col.separator()

        col = layout.column(align=True)
        col.prop(sp, "time", text="Time", text_ctxt="Hour")
        col.prop(sp, "UTC_zone")
        if prefs.show_daylight_savings:
            col.prop(sp, "use_daylight_savings")
        col.separator()

        local_time = format_time(sp.time,
                                 prefs.show_daylight_savings and sp.use_daylight_savings,
                                 sp.longitude)
        utc_time = format_time(sp.time,
                               prefs.show_daylight_savings and sp.use_daylight_savings,
                               sp.longitude,
                               sp.UTC_zone)

        col = layout.column(align=True)
        col.alignment = 'CENTER'

        split = col.split(factor=0.5, align=True)
        sub = split.column(align=True)
        sub.alignment = 'RIGHT'
        sub.label(text="Time Local:")
        sub.label(text="UTC:")

        sub = split.column(align=True)
        sub.label(text=local_time)
        sub.label(text=utc_time)
        col.separator()

        if prefs.show_rise_set:
            sunrise = format_hms(sun.sunrise)
            sunset = format_hms(sun.sunset)

            col = layout.column(align=True)
            col.alignment = 'CENTER'

            split = col.split(factor=0.5, align=True)
            sub = split.column(align=True)
            sub.alignment = 'RIGHT'
            sub.label(text="Sunrise:")
            sub.label(text="Sunset:")

            sub = split.column(align=True)
            sub.label(text=sunrise)
            sub.label(text=sunset)

        col.separator()
