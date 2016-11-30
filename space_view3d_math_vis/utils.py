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
from bpy.props import BoolProperty


def console_namespace():
    import console_python
    get_consoles = console_python.get_console
    consoles = getattr(get_consoles, "consoles", None)
    if consoles:
        for console, stdout, stderr in get_consoles.consoles.values():
            return console.locals
    return {}


def is_display_list(listvar):
    from mathutils import Vector

    for var in listvar:
        if type(var) is not Vector:
            return False
    return True


class VarStates:

    states = {}

    def store_states(self):
        # Store the display states, called upon unregister the Addon
        # This is useful when you press F8 to reload the Addons.
        # Then this function preserves the display states of the
        # console variables.
        context = bpy.context
        if len(self.states) > 0:
            state_props = context.window_manager.MathVisStateProp
            state_props.clear()
            for key, state in self.states.items():
                if key:
                    state_prop = state_props.add()
                    state_prop.key = key
                    state_prop.state = state

    def __init__(self):
        # Get the display state from the stored values (if exists)
        # This happens after you pressed F8 to reload the Addons.
        context = bpy.context
        if 'MathVisStateProp' in dir(bpy.types.WindowManager):
            state_props = context.window_manager.MathVisStateProp
            if state_props:
                for state_prop in state_props:
                    key = state_prop.key
                    state = state_prop.state
                    self.states[key] = [state[0], state[1]]
                state_props.clear()

    def get(self, key, default):
        return self.states.get(key, default)

    def delete(self, key):
        if key in self.states:
            del self.states[key]

    def is_visible(self, key):
        if key in self.states:
            disp, lock = self.states[key]
            return disp
        return True

    def toggle_display_state(self, key):
        if key in self.states:
            disp, lock = self.states[key]
            self.states[key] = [not disp, lock]
        else:
            self.states[key] = [False, False]

    def is_locked(self, key):
        if key in self.states:
            disp, lock = self.states[key]
            return lock
        return False

    def toggle_lock_state(self, key):
        if key in self.states:
            disp, lock = self.states[key]
            self.states[key] = [disp, not lock]
        else:
            self.states[key] = [True, True]

global g_var_states
g_var_states = None


def get_var_states():
    global g_var_states
    if g_var_states == None:
        g_var_states = VarStates()
    return g_var_states


def get_math_data():
    from mathutils import Matrix, Vector, Quaternion, Euler

    locals = console_namespace()
    if not locals:
        return {}

    variables = {}
    for key, var in locals.items():
        if key[0] == "_" or not var:
            continue
        if type(var) in {Matrix, Vector, Quaternion, Euler} or \
           type(var) in {tuple, list} and is_display_list(var):

            variables[key] = type(var)

    return variables


def cleanup_math_data():
    from mathutils import Matrix, Vector, Quaternion, Euler

    locals = console_namespace()
    if not locals:
        return

    var_states = get_var_states()
    variables = get_math_data()
    for key in variables.keys():
        if var_states.is_locked(key):
            continue

        del locals[key]
        var_states.delete(key)


def console_math_data():
    from mathutils import Matrix, Vector, Quaternion, Euler

    data_matrix = {}
    data_quat = {}
    data_euler = {}
    data_vector = {}
    data_vector_array = {}
    var_states = get_var_states()

    for key, var in console_namespace().items():
        if key[0] == "_":
            continue

        disp, lock = var_states.get(key, [True, False])
        if not disp:
            continue

        var_type = type(var)

        if var_type is Matrix:
            if len(var.col) != 4 or len(var.row) != 4:
                if len(var.col) == len(var.row):
                    var = var.to_4x4()
                else:  # todo, support 4x3 matrix
                    continue
            data_matrix[key] = var
        elif var_type is Vector:
            if len(var) < 3:
                var = var.to_3d()
            data_vector[key] = var
        elif var_type is Quaternion:
            data_quat[key] = var
        elif var_type is Euler:
            data_euler[key] = var
        elif var_type in {list, tuple} and is_display_list(var):
            data_vector_array[key] = var

    return data_matrix, data_quat, data_euler, data_vector, data_vector_array
