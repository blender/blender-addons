import bpy
import time
import sys
import os
import re

object_mode = 'OBJECT'
edit = 'EDIT'
sculpt = 'SCULPT'
vertex_paint = 'VERTEX_PAINT'
weight_paint = 'WEIGHT_PAINT'
texture_paint = 'TEXTURE_PAINT'
particle_edit = 'PARTICLE_EDIT'
pose = 'POSE'
gpencil_edit = 'GPENCIL_EDIT'

PIW = '       '

a_props = []

class Menu():
    def __init__(self, menu):
        self.layout = menu.layout
        self.items = {}
        self.current_item = None

    def add_item(self, ui_type="row", parent=None, name=None, **kwargs):
        # set the parent layout
        if parent:
            layout = parent
        else:
            layout = self.layout

        # set unique identifier for new items
        if not name:
            name = len(self.items) + 1
            
        # create and return a ui layout
        if ui_type == "row":
            self.current_item = self.items[name] = layout.row(**kwargs)

            return self.current_item

        elif ui_type == "column":
            self.current_item = self.items[name] = layout.column(**kwargs)

            return self.current_item

        elif ui_type == "column_flow":
            self.current_item = self.items[name] = layout.column_flow(**kwargs)

            return self.current_item

        elif ui_type == "box":
            self.current_item = self.items[name] = layout.box(**kwargs)

            return self.current_item

        elif ui_type == "split":
            self.current_item = self.items[name] = layout.split(**kwargs)

            return self.current_item

        else:
            print("Unknown Type")


def get_selected():
    # get the number of verts from the information string on the info header
    sel_verts_num = (e for e in bpy.context.scene.statistics().split(" | ")
                     if e.startswith("Verts:")).__next__()[6:].split("/")

    # turn the number of verts from a string to an int
    sel_verts_num = int(sel_verts_num[0].replace("," ,""))

    # get the number of edges from the information string on the info header
    sel_edges_num = (e for e in bpy.context.scene.statistics().split(" | ")
                     if e.startswith("Edges:")).__next__()[6:].split("/")

    # turn the number of edges from a string to an int
    sel_edges_num = int(sel_edges_num[0].replace(",", ""))

    # get the number of faces from the information string on the info header
    sel_faces_num = (e for e in bpy.context.scene.statistics().split(" | ")
                     if e.startswith("Faces:")).__next__()[6:].split("/")

    # turn the number of faces from a string to an int
    sel_faces_num = int(sel_faces_num[0].replace(",", ""))

    return sel_verts_num, sel_edges_num, sel_faces_num


def get_mode():
    if bpy.context.gpencil_data and \
    bpy.context.object.mode == object_mode and \
    bpy.context.scene.grease_pencil.use_stroke_edit_mode:
        return gpencil_edit
    else:
        return bpy.context.object.mode

def menuprop(item, name, value, data_path,
             icon='NONE', disable=False, disable_icon=None,
             custom_disable_exp=None, method=None, path=False):

    # disable the ui
    if disable:
        disabled = False

        # used if you need a custom expression to disable the ui
        if custom_disable_exp:
            if custom_disable_exp[0] == custom_disable_exp[1]:
                item.enabled = False
                disabled = True

        # check if the ui should be disabled for numbers
        elif isinstance(eval("bpy.context.{}".format(data_path)), float):
            if round(eval("bpy.context.{}".format(data_path)), 2) == value:
                item.enabled = False
                disabled = True

        # check if the ui should be disabled for anything else
        else:
            if eval("bpy.context.{}".format(data_path)) == value:
                item.enabled = False
                disabled = True

        # change the icon to the disable_icon if the ui has been disabled
        if disable_icon and disabled:
            icon = disable_icon

    # creates the menu item
    prop = item.operator("wm.context_set_value", text=name, icon=icon)

    # sets what the menu item changes
    if path:
        prop.value = value
        value = eval(value)

    elif type(value) == str:
        prop.value = "'{}'".format(value)

    else:
        prop.value = '{}'.format(value)

    # sets the path to what is changed
    prop.data_path = data_path

# used for global blender properties
def set_prop(prop_type, path, **kwargs):
    kwstring = ""

    # turn **kwargs into a string that can be used with exec
    for k, v in kwargs.items():
        if type(v) is str:
            v = '"{}"'.format(v)

        if callable(v):
            exec("from {0} import {1}".format(v.__module__, v.__name__))
            v = v.__name__
            
        kwstring += "{0}={1}, ".format(k, v)

    kwstring = kwstring[:-2]

    # create the property
    exec("{0} = bpy.props.{1}({2})".format(path, prop_type, kwstring))

    # add the path to a list of property paths
    a_props.append(path)

    return eval(path)

# used for removing properties created with set_prop
def del_props():
    for prop in a_props:
        exec("del {}".format(prop))

    a_props.clear()
    
class SendReport(bpy.types.Operator):
    bl_label = "Send Report"
    bl_idname = "view3d.send_report"
    
    message = bpy.props.StringProperty()
    
    def draw(self, context):
        self.layout.label("Error", icon='ERROR')
        self.layout.label(self.message)
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self, width=400, height=200)
    
    def execute(self, context):
        self.report({'INFO'}, self.message)
        print(self.message)
        return {'FINISHED'}
    
def send_report(message):
    def report(scene):
        bpy.ops.view3d.send_report('INVOKE_DEFAULT', message=message)
        bpy.app.handlers.scene_update_pre.remove(report)
        
    bpy.app.handlers.scene_update_pre.append(report)
