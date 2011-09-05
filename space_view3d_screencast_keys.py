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
    'name': 'Screencast Keys',
    'author': 'Paulo Gomes, Bart Crouch, John E. Herrenyo',
    'version': (1, 2),
    'blender': (2, 5, 9),
    'api': 39576,
    'location': 'View3D > Properties panel > Screencast Keys',
    'warning': '',
    'description': 'Display keys pressed in the 3d-view, '\
        'useful for screencasts.',
    'wiki_url': 'http://wiki.blender.org/index.php/Extensions:2.5/'\
        'Py/Scripts/3D_interaction/Screencast_Key_Status_Tool',
    'tracker_url': 'http://projects.blender.org/tracker/index.php?'\
        'func=detail&aid=21612',
    'category': '3D View'}


import bgl
import blf
import bpy
import time


def draw_callback_px(self, context):
    wm = context.window_manager
    if not wm.display_keys:
        return
    
    # draw text in the 3d-view
    blf.size(0, wm.display_font_size, 72)
    r, g, b = wm.display_color
    final = 0
    for i in range(len(self.key)):
        label_time = time.time() - self.time[i]
        if label_time < 2: # only display key-presses of last 2 seconds
            blf.position(0, wm.display_pos_x,
                wm.display_pos_y + wm.display_font_size*i, 0)
            alpha = min(1.0, max(0.0, 2 * (2 - label_time)))
            bgl.glColor4f(r, g, b, alpha)
            blf.draw(0, self.key[i])
            final = i
        else:
            break

    # get rid of status texts that aren't displayed anymore
    self.key = self.key[:final+1]
    self.time = self.time[:final+1]
    
    # draw graphical representation of the mouse
    if wm.display_mouse == 'graphic':
        for shape in ["mouse", "left_button", "middle_button", "right_button"]:
            draw_mouse(context, shape, "outline", 0.5)
        final = 0
        for i in range(len(self.mouse)):
            click_time = time.time() - self.mouse_time[i]
            if click_time < 2:
                shape = map_mouse_event(self.mouse[i])
                if shape:
                    alpha = min(1.0, max(0.0, 2 * (2 - click_time)))
                    draw_mouse(context, shape, "filled", alpha)
                final = i
            else:
                break
    
    # get rid of mouse clicks that aren't displayed anymore
    self.mouse = self.mouse[:final+1]
    self.mouse_time = self.mouse_time[:final+1]


def draw_mouse(context, shape, style, alpha):
    # shape and position
    wm = context.window_manager
    size = wm.display_font_size * 3
    offset_x = context.region.width - wm.display_pos_x - (size*0.535)
    offset_y = wm.display_pos_y
    shape_data = get_shape_data(shape)
    bgl.glTranslatef(offset_x, offset_y, 0)
    # color
    r, g, b = wm.display_color
    bgl.glEnable(bgl.GL_BLEND)
    #bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE_MINUS_SRC_ALPHA)
    #bgl.glColor4f(r, g, b, alpha)
    
    # inner shape for filled style
    if style == "filled":
        inner_shape = []
        for i in shape_data:
            inner_shape.append(i[0])
    
    # outer shape
    for i in shape_data:
        shape_segment = i
        shape_segment[0] = [size * k for k in shape_segment[0]]
        shape_segment[1] = [size * k for k in shape_segment[1]]
        shape_segment[2] = [size * k for k in shape_segment[2]]
        shape_segment[3] = [size * k for k in shape_segment[3]]
        
        # create the buffer
        shape_buffer = bgl.Buffer(bgl.GL_FLOAT, [4, 3], shape_segment)
        
        # create the map and draw the triangle fan
        bgl.glMap1f(bgl.GL_MAP1_VERTEX_3, 0.0, 1.0, 3, 4, shape_buffer)
        bgl.glEnable(bgl.GL_MAP1_VERTEX_3)
        bgl.glColor4f(r, g, b, alpha)
        
        if style == "outline":
            bgl.glBegin(bgl.GL_LINE_STRIP)
        else: # style == "filled"
            bgl.glBegin(bgl.GL_TRIANGLE_FAN)
        for j in range(10):
            bgl.glEvalCoord1f(j / 10.0)
        x, y, z = shape_segment[3]
        
        # make sure the last vertex is indeed the last one, to avoid gaps
        bgl.glVertex3f(x, y, z)
        bgl.glEnd()
        bgl.glDisable(bgl.GL_MAP1_VERTEX_3)
    
    # draw interior
    if style == "filled":
        bgl.glColor4f(r, g, b, alpha)
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
        for i in inner_shape:
            j = [size * k for k in i]
            x, y, z = j
            bgl.glVertex3f(x, y, z)
        bgl.glEnd()
    
    bgl.glTranslatef(-offset_x, -offset_y, 0)


# hardcoded data to draw the graphical represenation of the mouse
def get_shape_data(shape):
    data = []
    if shape == "mouse":
        data = [[[0.264, 0.002, 0.0], 
            [0.096, 0.002, 0.0], 
            [0.059, 0.226, 0.0], 
            [0.04, 0.313, 0.0]], 
            [[0.04, 0.313, 0.0], 
            [-0.015, 0.565, 0.0], 
            [-0.005, 0.664, 0.0], 
            [0.032, 0.87, 0.0]], 
            [[0.032, 0.87, 0.0], 
            [0.05, 0.973, 0.0], 
            [0.16, 1.002, 0.0], 
            [0.264, 1.002, 0.0]], 
            [[0.264, 1.002, 0.0], 
            [0.369, 1.002, 0.0], 
            [0.478, 0.973, 0.0], 
            [0.497, 0.87, 0.0]], 
            [[0.497, 0.87, 0.0], 
            [0.533, 0.664, 0.0], 
            [0.544, 0.565, 0.0], 
            [0.489, 0.313, 0.0]], 
            [[0.489, 0.313, 0.0], 
            [0.47, 0.226, 0.0], 
            [0.432, 0.002, 0.0], 
            [0.264, 0.002, 0.0]]]
    elif shape == "left_button":
        data = [[[0.154, 0.763, 0.0], 
            [0.126, 0.755, 0.0], 
            [0.12, 0.754, 0.0], 
            [0.066, 0.751, 0.0]], 
            [[0.066, 0.751, 0.0], 
            [0.043, 0.75, 0.0], 
            [0.039, 0.757, 0.0], 
            [0.039, 0.767, 0.0]], 
            [[0.039, 0.767, 0.0], 
            [0.047, 0.908, 0.0], 
            [0.078, 0.943, 0.0], 
            [0.155, 0.97, 0.0]], 
            [[0.155, 0.97, 0.0], 
            [0.174, 0.977, 0.0], 
            [0.187, 0.975, 0.0], 
            [0.191, 0.972, 0.0]], 
            [[0.191, 0.972, 0.0], 
            [0.203, 0.958, 0.0], 
            [0.205, 0.949, 0.0], 
            [0.199, 0.852, 0.0]], 
            [[0.199, 0.852, 0.0], 
            [0.195, 0.77, 0.0], 
            [0.18, 0.771, 0.0], 
            [0.154, 0.763, 0.0]]]
    elif shape == "middle_button":
        data = [[[0.301, 0.8, 0.0], 
            [0.298, 0.768, 0.0], 
            [0.231, 0.768, 0.0], 
            [0.228, 0.8, 0.0]], 
            [[0.228, 0.8, 0.0], 
            [0.226, 0.817, 0.0], 
            [0.225, 0.833, 0.0], 
            [0.224, 0.85, 0.0]], 
            [[0.224, 0.85, 0.0], 
            [0.222, 0.873, 0.0], 
            [0.222, 0.877, 0.0], 
            [0.224, 0.9, 0.0]], 
            [[0.224, 0.9, 0.0], 
            [0.225, 0.917, 0.0], 
            [0.226, 0.933, 0.0], 
            [0.228, 0.95, 0.0]], 
            [[0.228, 0.95, 0.0], 
            [0.231, 0.982, 0.0], 
            [0.298, 0.982, 0.0], 
            [0.301, 0.95, 0.0]], 
            [[0.301, 0.95, 0.0], 
            [0.302, 0.933, 0.0], 
            [0.303, 0.917, 0.0], 
            [0.305, 0.9, 0.0]], 
            [[0.305, 0.9, 0.0], 
            [0.307, 0.877, 0.0], 
            [0.307, 0.873, 0.0], 
            [0.305, 0.85, 0.0]], 
            [[0.305, 0.85, 0.0], 
            [0.303, 0.833, 0.0], 
            [0.302, 0.817, 0.0], 
            [0.301, 0.8, 0.0]]]
    elif shape == "right_button":
        data = [[[0.375, 0.763, 0.0], 
            [0.402, 0.755, 0.0], 
            [0.408, 0.754, 0.0], 
            [0.462, 0.751, 0.0]], 
            [[0.462, 0.751, 0.0], 
            [0.486, 0.75, 0.0], 
            [0.49, 0.757, 0.0], 
            [0.489, 0.767, 0.0]], 
            [[0.489, 0.767, 0.0], 
            [0.481, 0.908, 0.0], 
            [0.451, 0.943, 0.0], 
            [0.374, 0.97, 0.0]], 
            [[0.374, 0.97, 0.0], 
            [0.354, 0.977, 0.0], 
            [0.341, 0.975, 0.0], 
            [0.338, 0.972, 0.0]], 
            [[0.338, 0.972, 0.0], 
            [0.325, 0.958, 0.0], 
            [0.324, 0.949, 0.0], 
            [0.329, 0.852, 0.0]], 
            [[0.329, 0.852, 0.0], 
            [0.334, 0.77, 0.0], 
            [0.348, 0.771, 0.0], 
            [0.375, 0.763, 0.0]]]
    
    return(data)


# return the shape that belongs to the given event
def map_mouse_event(event):
    shape = False
    
    if event == 'LEFTMOUSE':
        shape = "left_button"
    elif event == 'MIDDLEMOUSE':
        shape = "middle_button"
    elif event == 'RIGHTMOUSE':
        shape = "right_button"
    
    return(shape)


class ScreencastKeysStatus(bpy.types.Operator):
    bl_idname = "view3d.screencast_keys"
    bl_label = "Screencast Key Status Tool"
    bl_description = "Display keys pressed in the 3D-view"
    
    def modal(self, context, event):
        if context.area:
            context.area.tag_redraw()
        wm = context.window_manager
        # keys that shouldn't show up in the 3d-view
        mouse_keys = ['MOUSEMOVE','MIDDLEMOUSE','LEFTMOUSE',
         'RIGHTMOUSE', 'WHEELDOWNMOUSE','WHEELUPMOUSE']
        ignore_keys = ['LEFT_SHIFT', 'RIGHT_SHIFT', 'LEFT_ALT',
         'RIGHT_ALT', 'LEFT_CTRL', 'RIGHT_CTRL', 'TIMER']
        if wm.display_mouse != 'text':
            ignore_keys.extend(mouse_keys)

        if event.value == 'PRESS':
            # add key-press to display-list
            sc_keys = []
            
            if event.ctrl:
                sc_keys.append("Ctrl ")
            if event.alt:
                sc_keys.append("Alt ")
            if event.shift:
                sc_keys.append("Shift ")
            
            sc_amount = ""
            if self.key:
                if event.type not in ignore_keys and event.type in self.key[0]:
                    mods = "+ ".join(sc_keys)
                    old_mods = "+ ".join(self.key[0].split("+ ")[:-1])
                    if mods == old_mods:
                        amount = self.key[0].split(" x")
                        if len(amount) >= 2:
                            sc_amount = " x" + str(int(amount[-1]) + 1)
                        else:
                            sc_amount = " x2"
                        del self.key[0]
                        del self.time[0]
           
            if event.type not in ignore_keys:
                sc_keys.append(event.type)
                self.key.insert(0, "+ ".join(sc_keys) + sc_amount)
                self.time.insert(0, time.time())
            
            elif event.type in mouse_keys and wm.display_mouse == 'graphic':
                self.mouse.insert(0, event.type)
                self.mouse_time.insert(0, time.time())
        
        if not context.window_manager.display_keys:
            # stop script
            context.region.callback_remove(self._handle)
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def cancel(self, context):
        if context.window_manager.display_keys:
            context.region.callback_remove(self._handle)
            context.window_manager.display_keys = False

        return {'CANCELLED'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            if context.window_manager.display_keys == False:
                # operator is called for the first time, start everything
                context.window_manager.display_keys = True
                context.window_manager.modal_handler_add(self)
                self.key = []
                self.time = []
                self.mouse = []
                self.mouse_time = []
                self._handle = context.region.callback_add(draw_callback_px,
                    (self, context), 'POST_PIXEL')
                return {'RUNNING_MODAL'}
            else:
                # operator is called again, stop displaying
                context.window_manager.display_keys = False
                self.key = []
                self.time = []
                self.mouse = []
                self.mouse_time = []
                return {'CANCELLED'}
        else:
            self.report({'WARNING'}, "View3D not found, can't run operator")
            return {'CANCELLED'}


# properties used by the script
def init_properties():
    bpy.types.WindowManager.display_keys = bpy.props.BoolProperty(
        default=False)
    bpy.types.WindowManager.display_mouse = bpy.props.EnumProperty(
        items=(("none", "None", "Don't display mouse events"), 
            ("graphic", "Graphic", "Display graphical represenation of "\
                "the mouse"),
            ("text", "Text", "Display mouse events as text lines")),
        name="Mouse display",
        description="Display mouse events",
        default='text')
    bpy.types.WindowManager.display_font_size = bpy.props.IntProperty(
        name="Size",
        description="Fontsize",
        default=20, min=10, max=150)

    bpy.types.WindowManager.display_pos_x = bpy.props.IntProperty(
        name="Pos X",
        description="Margin on the x axis",
        default=15)
    bpy.types.WindowManager.display_pos_y = bpy.props.IntProperty(
        name="Pos Y",
        description="Margin on the y axis",
        default=60)
    bpy.types.WindowManager.display_color = bpy.props.FloatVectorProperty(
        name="Color",
        description="Font color",
        default=(1.0, 1.0, 1.0),
        min=0,
        max=1,
        subtype='COLOR')


# removal of properties when script is disabled
def clear_properties():
    props = ["display_keys", "display_mouse", "display_font_size",
     "display_pos_x", "display_pos_y"]
    for p in props:
        if bpy.context.window_manager.get(p) != None:
            del bpy.context.window_manager[p]
        try:
            x = getattr(bpy.types.WindowManager, p)
            del x
        except:
            pass


# defining the panel
class OBJECT_PT_keys_status(bpy.types.Panel):
    bl_label = "Screencast Keys"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    
    def draw(self, context):
        layout = self.layout
        
        if not context.window_manager.display_keys:
            layout.operator("view3d.screencast_keys", text="Start display",
                icon='PLAY')
        else:
            layout.operator("view3d.screencast_keys", text="Stop display",
                icon='PAUSE')
        
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(context.window_manager, "display_pos_x")
        row.prop(context.window_manager, "display_pos_y")
        row = col.row(align=True)
        row.prop(context.window_manager, "display_font_size")
        row.prop(context.window_manager, "display_mouse", text="")
        
        layout.prop(context.window_manager, "display_color")


classes = [ScreencastKeysStatus,
    OBJECT_PT_keys_status]


def register():
    init_properties()
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    clear_properties()


if __name__ == "__main__":
    register()
