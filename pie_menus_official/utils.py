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


import bpy


class AddonPreferences:
    _module = {}

    @classmethod
    def get_prefs(cls, package=''):
        if not package:
            package = __package__
        if '.' in package:
            pkg, name = package.split('.')
            # key = cls.__qualname__
            if package in cls._module:
                mod = cls._module[package]
            else:
                import importlib
                mod = cls._module[package] = importlib.import_module(pkg)
            return mod.get_addon_preferences(name)
        else:
            context = bpy.context
            return context.user_preferences.addons[package].preferences

    @classmethod
    def register(cls):
        if '.' in __package__:
            cls.get_prefs()

    @classmethod
    def unregister(cls):
        cls._module.clear()


class SpaceProperty:
    """
    bpy.types.Space #Add the virtual property in

    # Instantiation
    space_prop = SpaceProperty(
        [[bpy.types.SpaceView3D, 'lock_cursor_location',
          bpy.props.BoolProperty()]])

    # When drawing
    def draw(self, context):
        layout = self.layout
        view = context.space_data
        prop = space_prop.get_prop(view, 'lock_cursor_location')
        layout.prop(prop, 'lock_cursor_location')

    # register / unregister
    def register():
        space_prop.register()

    def unregister():
        space_prop.unregister()
    """

    space_types = {
        'EMPTY': bpy.types.Space,
        'NONE': bpy.types.Space,
        'CLIP_EDITOR': bpy.types.SpaceClipEditor,
        'CONSOLE': bpy.types.SpaceConsole,
        'DOPESHEET_EDITOR': bpy.types.SpaceDopeSheetEditor,
        'FILE_BROWSER': bpy.types.SpaceFileBrowser,
        'GRAPH_EDITOR': bpy.types.SpaceGraphEditor,
        'IMAGE_EDITOR': bpy.types.SpaceImageEditor,
        'INFO': bpy.types.SpaceInfo,
        'LOGIC_EDITOR': bpy.types.SpaceLogicEditor,
        'NLA_EDITOR': bpy.types.SpaceNLA,
        'NODE_EDITOR': bpy.types.SpaceNodeEditor,
        'OUTLINER': bpy.types.SpaceOutliner,
        'PROPERTIES': bpy.types.SpaceProperties,
        'SEQUENCE_EDITOR': bpy.types.SpaceSequenceEditor,
        'TEXT_EDITOR': bpy.types.SpaceTextEditor,
        'TIMELINE': bpy.types.SpaceTimeline,
        'USER_PREFERENCES': bpy.types.SpaceUserPreferences,
        'VIEW_3D': bpy.types.SpaceView3D,
    }
    # space_types_r = {v: k for k, v in space_types.items()}

    def __init__(self, *props):
        """
        :param props: [[space_type, attr, prop], ...]
            [[Or string bpy.types.Space, String,
              bpy.props.***()かPropertyGroup], ...]
            bpy.types.PropertyGroup In advance if you use register_class()so
            It is registered
        :type props: list[list]
        """
        self.props = [list(elem) for elem in props]
        for elem in self.props:
            space_type = elem[0]
            if isinstance(space_type, str):
                elem[0] = self.space_types[space_type]
        self.registered = []
        self.save_pre = self.save_post = self.load_post = None

    def gen_save_pre(self):
        @bpy.app.handlers.persistent
        def save_pre(dummy):
            wm = bpy.context.window_manager
            for (space_type, attr, prop), (cls, wm_prop_name) in zip(
                    self.props, self.registered):
                if wm_prop_name not in wm:
                    continue
                d = {p['name']: p for p in wm[wm_prop_name]}  # not p.name
                for screen in bpy.data.screens:
                    ls = []
                    for area in screen.areas:
                        for space in area.spaces:
                            if isinstance(space, space_type):
                                key = str(space.as_pointer())
                                if key in d:
                                    ls.append(d[key])
                                else:
                                    ls.append({})
                    screen[wm_prop_name] = ls
        self.save_pre = save_pre
        return save_pre

    def gen_save_post(self):
        @bpy.app.handlers.persistent
        def save_post(dummy):
            # clean up
            for cls, wm_prop_name in self.registered:
                for screen in bpy.data.screens:
                    if wm_prop_name in screen:
                        del screen[wm_prop_name]
        self.save_post = save_post
        return save_post

    def gen_load_post(self):
        @bpy.app.handlers.persistent
        def load_post(dummy):
            from collections import OrderedDict
            for (space_type, attr, prop), (cls, wm_prop_name) in zip(
                    self.props, self.registered):
                d = OrderedDict()
                for screen in bpy.data.screens:
                    if wm_prop_name not in screen:
                        continue

                    spaces = []
                    for area in screen.areas:
                        for space in area.spaces:
                            if isinstance(space, space_type):
                                spaces.append(space)

                    for space, p in zip(spaces, screen[wm_prop_name]):
                        key = p['name'] = str(space.as_pointer())
                        d[key] = p
                if d:
                    bpy.context.window_manager[wm_prop_name] = list(d.values())

            # clean up
            for cls, wm_prop_name in self.registered:
                for screen in bpy.data.screens:
                    if wm_prop_name in screen:
                        del screen[wm_prop_name]

        self.load_post = load_post
        return load_post

    def get_all(self, space_type=None, attr=''):
        """
        :param space_type: If the property is only only one optional
        :type space_type: bpy.types.Space
        :param attr: If the property is only only one optional
        :type attr: str
        :return:
        :rtype:
        """
        if space_type and isinstance(space_type, str):
            space_type = self.space_types.get(space_type)
        context = bpy.context
        for (st, attri, prop), (cls, wm_prop_name) in zip(
                self.props, self.registered):
            if (st == space_type or issubclass(space_type, st) or
                    not space_type and len(self.props) == 1):
                if attri == attr or not attr and len(self.props) == 1:
                    seq = getattr(context.window_manager, wm_prop_name)
                    return seq

    def get(self, space, attr=''):
        """
        :type space: bpy.types.Space
        :param attr: If the property is only only one optional
        :type attr: str
        :return:
        :rtype:
        """
        seq = self.get_all(type(space), attr)
        if seq is not None:
            key = str(space.as_pointer())
            if key not in seq:
                item = seq.add()
                item.name = key
            return seq[key]

    def _property_name(self, space_type, attr):
        return space_type.__name__.lower() + '_' + attr

    def register(self):
        import inspect
        for space_type, attr, prop in self.props:
            if inspect.isclass(prop) and \
                    issubclass(prop, bpy.types.PropertyGroup):
                cls = prop
            else:
                name = 'WM_PG_' + space_type.__name__ + '_' + attr
                cls = type(name, (bpy.types.PropertyGroup,), {attr: prop})
                bpy.utils.register_class(cls)

            collection_prop = bpy.props.CollectionProperty(type=cls)
            wm_prop_name = self._property_name(space_type, attr)
            setattr(bpy.types.WindowManager, wm_prop_name, collection_prop)

            self.registered.append((cls, wm_prop_name))

            def gen():
                def get(self):
                    seq = getattr(bpy.context.window_manager, wm_prop_name)
                    key = str(self.as_pointer())
                    if key not in seq:
                        item = seq.add()
                        item.name = key
                    if prop == cls:
                        return seq[key]
                    else:
                        return getattr(seq[key], attr)

                def set(self, value):
                    seq = getattr(bpy.context.window_manager, wm_prop_name)
                    key = str(self.as_pointer())
                    if key not in seq:
                        item = seq.add()
                        item.name = key
                    if prop != cls:  # PropertyGroup It is not writable
                        return setattr(seq[key], attr, value)

                return property(get, set)

            setattr(space_type, attr, gen())

        bpy.app.handlers.save_pre.append(self.gen_save_pre())
        bpy.app.handlers.save_post.append(self.gen_save_post())
        bpy.app.handlers.load_post.append(self.gen_load_post())

    def unregister(self):
        bpy.app.handlers.save_pre.remove(self.save_pre)
        bpy.app.handlers.save_post.remove(self.save_post)
        bpy.app.handlers.load_post.remove(self.load_post)

        for (space_type, attr, prop), (cls, wm_prop_name) in zip(
                self.props, self.registered):
            delattr(bpy.types.WindowManager, wm_prop_name)
            if wm_prop_name in bpy.context.window_manager:
                del bpy.context.window_manager[wm_prop_name]
            delattr(space_type, attr)

            if prop != cls:
                # originally bpy.types.PropertyGroup Skip Nara
                bpy.utils.unregister_class(cls)

            for screen in bpy.data.screens:
                if wm_prop_name in screen:
                    del screen[wm_prop_name]

        self.registered.clear()


def operator_call(op, *args, _scene_update=True, **kw):
    """vawm Than
    operator_call(bpy.ops.view3d.draw_nearest_element,
                  'INVOKE_DEFAULT', type='ENABLE', _scene_update=False)
    """
    import bpy
    from _bpy import ops as ops_module

    BPyOpsSubModOp = op.__class__
    op_call = ops_module.call
    context = bpy.context

    # Get the operator from blender
    wm = context.window_manager

    # run to account for any rna values the user changes.
    if _scene_update:
        BPyOpsSubModOp._scene_update(context)

    if args:
        C_dict, C_exec, C_undo = BPyOpsSubModOp._parse_args(args)
        ret = op_call(op.idname_py(), C_dict, kw, C_exec, C_undo)
    else:
        ret = op_call(op.idname_py(), None, kw)

    if 'FINISHED' in ret and context.window_manager == wm:
        if _scene_update:
            BPyOpsSubModOp._scene_update(context)

    return ret
