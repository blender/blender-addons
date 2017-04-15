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

from . import functions



# UI
class SEQUENCER_EXTRA_MT_input(bpy.types.Menu):
    bl_label = "Input"

    def draw(self, context):
        self.layout.operator_context = 'INVOKE_REGION_WIN'
        self.layout.operator('sequencerextra.striprename',
        text='File Name to Strip Name', icon='PLUGIN')
        self.layout.operator('sequencerextra.editexternally',
        text='Open with External Editor', icon='PLUGIN')
        self.layout.operator('sequencerextra.edit',
        text='Open with Editor', icon='PLUGIN')
        self.layout.operator('sequencerextra.createmovieclip',
        text='Create Movieclip strip', icon='PLUGIN')

def sequencer_header_func(self, context):
    self.layout.menu("SEQUENCER_EXTRA_MT_input")

def sequencer_add_menu_func(self, context):
    self.layout.operator('sequencerextra.placefromfilebrowser', 
    text='place from file browser', icon='PLUGIN').insert = False
    self.layout.operator('sequencerextra.placefromfilebrowser', 
    text='insert from file browser', icon='PLUGIN').insert = True
    self.layout.operator('sequencerextra.recursiveload', 
    text='recursive load from browser', icon='PLUGIN')
    self.layout.separator()


def sequencer_select_menu_func(self, context):
    self.layout.operator_menu_enum('sequencerextra.select_all_by_type',
    'type', text='All by Type', icon='PLUGIN')
    self.layout.separator()
    self.layout.operator('sequencerextra.selectcurrentframe',
    text='Before Current Frame', icon='PLUGIN').mode = 'BEFORE'
    self.layout.operator('sequencerextra.selectcurrentframe',
    text='After Current Frame', icon='PLUGIN').mode = 'AFTER'
    self.layout.operator('sequencerextra.selectcurrentframe',
    text='On Current Frame', icon='PLUGIN').mode = 'ON'
    self.layout.separator()
    self.layout.operator('sequencerextra.selectsamechannel',
    text='Same Channel', icon='PLUGIN')


def sequencer_strip_menu_func(self, context):
    self.layout.operator('sequencerextra.extendtofill',
    text='Extend to Fill', icon='PLUGIN')
    self.layout.operator_menu_enum('sequencerextra.fadeinout',
    'mode', text='Fade', icon='PLUGIN')
    self.layout.operator_menu_enum('sequencerextra.copyproperties',
    'prop', icon='PLUGIN')
    
    self.layout.operator('sequencerextra.insert',
    text='Insert (Single Channel)', icon='PLUGIN').singlechannel = True
    self.layout.operator('sequencerextra.insert',
    text='Insert', icon='PLUGIN').singlechannel = False
    self.layout.operator('sequencerextra.ripplecut',
    text='Ripple Cut', icon='PLUGIN')
    self.layout.operator('sequencerextra.rippledelete',
    text='Ripple Delete', icon='PLUGIN')
    self.layout.separator()


def time_frame_menu_func(self, context):
    self.layout.operator('timeextra.trimtimelinetoselection',
    text='Trim to Selection', icon='PLUGIN')
    self.layout.operator('timeextra.trimtimeline',
    text='Trim to Timeline Content', icon='PLUGIN')
    self.layout.separator()
    self.layout.operator('screenextra.frame_skip',
    text='Skip Forward One Second', icon='PLUGIN').back = False
    self.layout.operator('screenextra.frame_skip',
    text='Skip Back One Second', icon='PLUGIN').back = True
    self.layout.separator()


def time_header_func(self, context):
    self.layout.operator('sequencerextra.jogshuttle',
    text='Jog/Shuttle', icon='NDOF_TURN')


def clip_header_func(self, context):
    self.layout.operator('sequencerextra.jogshuttle',
    text='Jog/Shuttle', icon='NDOF_TURN')


def clip_clip_menu_func(self, context):
    self.layout.operator('clipextra.openactivestrip',
    text='Open Active Strip', icon='PLUGIN')
    self.layout.operator('clipextra.openfromfilebrowser',
    text='Open from File Browser', icon='PLUGIN')
    self.layout.separator()
    
   
    
###############################


def draw_color_balance(layout, color_balance):
    layout = layout.split(percentage=0.33)
    col = layout.column()
    col.label(text="Lift:")
    col.template_color_picker(color_balance, "lift", value_slider=True, cubic=True)
    row = col.row()
    row.prop(color_balance, "lift", text="")
    row.prop(color_balance, "invert_lift", text="Invert")

    col = layout.column()
    col.label(text="Gamma:")
    col.template_color_picker(color_balance, "gamma", value_slider=True, lock_luminosity=True, cubic=True)
    row = col.row()
    row.prop(color_balance, "gamma", text="")
    row.prop(color_balance, "invert_gamma", text="Invert")

    col = layout.column()
    col.label(text="Gain:")
    col.template_color_picker(color_balance, "gain", value_slider=True, lock_luminosity=True, cubic=True)
    row = col.row()
    row.prop(color_balance, "gain", text="")
    row.prop(color_balance, "invert_gain", text="Invert")


############################

        

class JumptoCut(bpy.types.Panel):
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_label = "Jump to Cut 6"

    COMPAT_ENGINES = {'BLENDER_RENDER'}
    
    _frame_rate_args_prev = None
    _preset_class = None

    @staticmethod
    def _draw_framerate_label(*args):
        # avoids re-creating text string each draw
        if JumptoCut._frame_rate_args_prev == args:
            return JumptoCut._frame_rate_ret

        fps, fps_base, preset_label = args

        if fps_base == 1.0:
            fps_rate = round(fps)
        else:
            fps_rate = round(fps / fps_base, 2)

        # TODO: Change the following to iterate over existing presets
        custom_framerate = (fps_rate not in {23.98, 24, 25, 29.97, 30, 50, 59.94, 60})

        if custom_framerate is True:
            fps_label_text = "Custom (%r fps)" % fps_rate
            show_framerate = True
        else:
            fps_label_text = "%r fps" % fps_rate
            show_framerate = (preset_label == "Custom")

        JumptoCut._frame_rate_args_prev = args
        JumptoCut._frame_rate_ret = args = (fps_label_text, show_framerate)
        return args

    @staticmethod
    def draw_framerate(sub, rd):
        if JumptoCut._preset_class is None:
            JumptoCut._preset_class = bpy.types.RENDER_MT_framerate_presets

        args = rd.fps, rd.fps_base, JumptoCut._preset_class.bl_label
        fps_label_text, show_framerate = JumptoCut._draw_framerate_label(*args)

        sub.menu("RENDER_MT_framerate_presets", text=fps_label_text)

        if show_framerate:
            sub.prop(rd, "fps")
            sub.prop(rd, "fps_base", text="/")

    @classmethod
    def poll(self, context):
        if context.space_data.view_type in {'SEQUENCER', 'SEQUENCER_PREVIEW'}:
            strip = functions.act_strip(context)
            scn = context.scene
            preferences = context.user_preferences
            prefs = preferences.addons[__package__].preferences
            if scn and scn.sequence_editor:
                if prefs.use_jumptocut:
                    return True
        else:
            return False

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon="RENDER_ANIMATION")

    def draw(self, context):
        scn = context.scene
        strip = functions.act_strip(context)
            
        preferences = context.user_preferences
        prefs = preferences.addons[__package__].preferences
        
        layout = self.layout
        layout = layout.box()
        # jump to cut main controls
        
        row=layout.row(align=True)
        
        row.label(icon='TIME', text="Secs")  
        row.operator('screenextra.frame_skip',
        text="", icon='TRIA_LEFT').back = True
        row.operator('screenextra.frame_skip',
        text="", icon='TRIA_RIGHT').back = False
        
        row.separator()
        
        row.label(icon='IPO_BOUNCE', text="Cuts")  
        row.operator("sequencer.strip_jump", icon="PLAY_REVERSE", text="").next=False
        row.operator("sequencer.strip_jump", icon='PLAY', text="").next=True
        
        row.separator()
        
        row.label(icon='MARKER_HLT', text="Marker")
        row.operator("screen.marker_jump", icon="TRIA_LEFT", text="").next=False
        row.operator("screen.marker_jump", icon='TRIA_RIGHT', text="").next=True
        
        
        rd = scn.render
        screen = context.screen
        row = layout.row(align=True)
        row.operator("screen.frame_jump", text="", icon='REW').end = False
        row.operator("screen.keyframe_jump", text="", icon='PREV_KEYFRAME').next = False
        if not screen.is_animation_playing:
            # if using JACK and A/V sync:
            #   hide the play-reversed button
            #   since JACK transport doesn't support reversed playback
            if scn.sync_mode == 'AUDIO_SYNC' and context.user_preferences.system.audio_device == 'JACK':
                sub = row.row(align=True)
                sub.scale_x = 2.0
                sub.operator("screen.animation_play", text="", icon='PLAY')
            else:
                row.operator("screen.animation_play", text="", icon='PLAY_REVERSE').reverse = True
                row.operator("screen.animation_play", text="", icon='PLAY')
        else:
            sub = row.row(align=True)
            sub.scale_x = 2.0
            sub.operator("screen.animation_play", text="", icon='PAUSE')
        row.operator("screen.keyframe_jump", text="", icon='NEXT_KEYFRAME').next = True
        row.operator("screen.frame_jump", text="", icon='FF').end = True
        
        row.separator()
        row.prop(scn, "sync_mode", text="")
        row.separator()
        self.draw_framerate(row, rd)
        
        row=layout.row(align=True)
        row.operator("sequencer.refresh_all")
        row.operator('sequencer.rendersize', text='set render size', icon='PLUGIN')

        row=layout.row(align=True)
        row.operator("sequencerextra.setstartend", icon="PREVIEW_RANGE", text="IN/OUT")
        row.operator('timeextra.trimtimelinetoselection', text='Selection', icon='PREVIEW_RANGE')
        row.operator('timeextra.trimtimeline', text='All', icon='PREVIEW_RANGE')

        layout = self.layout        
        # layout = layout.box()
        # panel setup ------------------------------------------------------
        row=layout.row(align=True)
        row = row.split(percentage=0.25)
        row.prop(prefs, "kr_show_tools", text="Tools", icon='SEQ_SEQUENCER')
        if prefs.kr_show_tools:
            row = row.split(percentage=0.25)
            row.prop(prefs, "kr_mini_ui", text="mini")
        else:
            row = row.split(percentage=0.25) 
            row.label(text = "")

        row = row.split(percentage=0.25) 
        row.label(text = "")
        row = row.split(percentage=0.25)
        row.label(text = "")
        row = row.split(percentage=0.33)   
        row.prop(prefs, "kr_show_info", text="", icon='VIEWZOOM')
        row = row.split(percentage=0.5) 
        row.prop(prefs, "kr_extra_info", text="", icon='BORDERMOVE')
        row = row.split(percentage=1) 
        row.prop(prefs, "kr_show_modifiers", text="", icon='RESTRICT_VIEW_OFF')
              
        ##########

        if prefs.kr_show_tools:
            layout = self.layout
            layout = layout.box()
            # snap, handler selector and meta tools
            
            if prefs.kr_mini_ui:
                row=layout.row(align=True)
                row.operator('sequencerextra.extrasnap', text='', icon='SNAP_ON').align=0
                row.operator('sequencerextra.extrasnap', text='', icon='SNAP_SURFACE').align=1
                row.operator('sequencerextra.extrasnap', text='', icon='SNAP_ON').align=2

                row.separator()
                row.operator('sequencerextra.extrahandles', text='', icon='TRIA_LEFT').side=0
                row.operator('sequencerextra.extrahandles', text='', icon='PMARKER').side=1
                row.operator('sequencerextra.extrahandles', text='', icon='TRIA_RIGHT').side=2

                row.separator()
                row.operator("sequencerextra.metacopy", icon="COPYDOWN", text="")
                row.operator("sequencerextra.metapaste", icon='PASTEDOWN', text="")
                row.separator()
                row.operator('sequencerextra.meta_separate_trim', text='', icon='ALIGN')
                row.separator()
                row.prop(prefs, "use_io_tools", text="I/O tools")
                
                # IN /OUT TOOLS
                
                
                if prefs.use_io_tools:
                    row=layout.row(align=True)
                    if scn.kr_auto_markers == True:
                        row.prop(scn, "kr_auto_markers", text="")
                    
                        row.separator()
                        row.operator("sequencerextra.sourcein", icon="MARKER_HLT", text="")
                        row.prop(scn, "kr_in_marker")
                        row.operator("sequencerextra.sourceout", icon='MARKER_HLT', text="")
                        row.prop(scn, "kr_out_marker")
                    else:
                        row.prop(scn, "kr_auto_markers", text="AUTO i/o") 
                        row.operator("sequencerextra.sourcein", icon="MARKER_HLT", text="IN")
                        row.operator("sequencerextra.sourceout", icon='MARKER_HLT', text="OUT")
                    row.separator()
                    row.operator("sequencerextra.setinout", icon="ARROW_LEFTRIGHT", text="")
                    row.operator("sequencerextra.triminout", icon="FULLSCREEN_EXIT", text="")
                    
                # miniUI extra actions
                row=layout.row(align=True)
                row.operator('sequencerextra.jogshuttle',
                    text='', icon='NDOF_TURN')
                row.operator('sequencerextra.navigateup',
                    text='', icon='FILE_PARENT')
                row.operator('sequencerextra.extendtofill',
                text='', icon='STYLUS_PRESSURE')
                row.operator('sequencerextra.placefromfilebrowser',
                    text='', icon='TRIA_DOWN').insert = False            
                row.operator('sequencerextra.placefromfilebrowser',
                    text='', icon='TRIA_RIGHT').insert = True
                row.operator('sequencer.slip',
                    text='', icon='MOD_SHRINKWRAP')
                row.operator_menu_enum('sequencerextra.fadeinout',
                'mode', text='fade', icon='MOD_ARRAY')
                row.operator_menu_enum('sequencerextra.copyproperties',
                'prop', text='copy',icon='SCRIPT')
            
            else:  # NOT prefs.kr_mini_ui:
                    
                row=layout.row(align=True)
                row.label("Snap:")    
                #row=layout.row(align=True)
                row.operator('sequencerextra.extrasnap', text='left', icon='SNAP_ON').align=0
                row.operator('sequencerextra.extrasnap', text='center', icon='SNAP_SURFACE').align=1
                row.operator('sequencerextra.extrasnap', text='right', icon='SNAP_ON').align=2

                row=layout.row(align=True)
                row.label("Handlers:")
                #row=layout.row(align=True)
                row.operator('sequencerextra.extrahandles', text='left', icon='TRIA_LEFT').side=0
                row.operator('sequencerextra.extrahandles', text='both', icon='PMARKER').side=1
                row.operator('sequencerextra.extrahandles', text='right', icon='TRIA_RIGHT').side=2

                row=layout.row()
                row=layout.row(align=True)
                split = row.split(percentage=0.99)
                colR2 = split.column()
                row1 = colR2.row(align=True)
                row1.operator("sequencerextra.metacopy", icon="COPYDOWN", text="meta-copy")
                row1.operator("sequencerextra.metapaste", icon='PASTEDOWN', text="paste-snap")
                split = row.split(percentage=0.99)
                colR3 = split.column()
                colR3.operator('sequencerextra.meta_separate_trim', text='unMeta & Trim', icon='ALIGN')
        
        
        
                # IN /OUT TOOLS
                row=layout.box()
                split=row.split(percentage=0.7)
                colR1 = split.column()
                row1=colR1.row(align=True)
                row1.operator("sequencerextra.sourcein", icon="MARKER_HLT", text="set IN")
                row1.operator("sequencerextra.sourceout", icon='MARKER_HLT', text="set OUT")
                colR3 = split.column()
                colR3.operator("sequencerextra.setinout", icon="ARROW_LEFTRIGHT", text="selected")
                
                split=row.split(percentage=0.7)
                colR1 = split.column()
                row1=colR1.row(align=True)
                if scn.kr_auto_markers == False:
                    row1.prop(scn, "kr_auto_markers", text="auto markers")
                else:
                    row1.prop(scn, "kr_auto_markers", text="")
                    row1.prop(scn, "kr_in_marker")
                    row1.prop(scn, "kr_out_marker")
                    row1.active = scn.kr_auto_markers
                colR3 = split.column()
                colR3.operator("sequencerextra.triminout", icon="FULLSCREEN_EXIT", text="trim",emboss=True)

        
                # UI extra actions
                row=layout.row(align=True)
                row.operator('sequencerextra.jogshuttle',
                    text='Jog/Shuttle', icon='NDOF_TURN')            
                row.operator('sequencerextra.navigateup',
                    text='Navigate Up', icon='FILE_PARENT')
                row.operator('sequencerextra.extendtofill',
                text='Extend to Fill', icon='STYLUS_PRESSURE')
                row=layout.row(align=True)
                row.operator('sequencerextra.placefromfilebrowser',
                    text='File Place', icon='TRIA_DOWN').insert = False
                row.operator('sequencerextra.placefromfilebrowser',
                    text='File Insert', icon='TRIA_RIGHT').insert = True
                row.operator('sequencer.slip',
                    text='Slip', icon='MOD_SHRINKWRAP')
                row=layout.row(align=True)
                row.operator_menu_enum('sequencerextra.fadeinout',
                'mode', text='Fade', icon='MOD_ARRAY')
                row.operator_menu_enum('sequencerextra.copyproperties',
                'prop', icon='SCRIPT')

        # INFO boxes
        # INFO boxes
        # INFO boxes
        if strip != None:
            if prefs.kr_show_info:
                layout = layout.box()
                row = layout.split(percentage=0.075)
                row.prop(prefs, "kr_show_info", text="",icon='VIEWZOOM', emboss=True)
                row = row.split(percentage=0.3)
                row.prop(strip, "type", text="")
                row = row.split(percentage=1)
                row.prop(strip, "name", text="")
                
                # MUTE INFORMATION
                layout.active = (not strip.mute)

                # basic info
                row = layout.row()
                row.prop(strip, "channel")
                row.prop(strip, "frame_start")
                row.prop(strip, "frame_final_duration")

                # source info
                row = layout.split(percentage=0.8)

                if strip.type in {'MOVIE', 'SOUND'}:
                    row.prop(strip, "filepath", text="")
                
                if strip.type == 'IMAGE':
                    row.prop(strip, "directory", text="")
                    # Current element for the filename
                    elem = strip.strip_elem_from_frame(context.scene.frame_current)
                    if elem:
                        row = layout.row()
                        row.prop(elem, "filename", text="File")  # strip.elements[0] could be a fallback
                        row.operator("sequencer.change_path", text="change files")
                
                if strip.type == 'COLOR':
                    row.prop(strip, "color", text = "")

                # trim info
                if strip.type not in {"SPEED", "WIPE", "CROSS", "ADJUSTMENT"}:
                    row = row.split(percentage=1) 
                    row.prop(prefs, "kr_show_trim", text="Trim")
                    if prefs.kr_show_trim:
                        if not isinstance(strip, bpy.types.EffectSequence):
                            row = layout.row(align=True)
                            row.label(text="hard:")
                            row.prop(strip, "animation_offset_start", text="Start")
                            row.prop(strip, "animation_offset_end", text="End")
                        row = layout.row(align=True)
                        row.label(text="soft:")
                        row.prop(strip, "frame_offset_start", text="Start")
                        row.prop(strip, "frame_offset_end", text="End")

                
                
                row = layout.row()
                    
                # special strips info
                if strip.type == 'SPEED':
                    row.prop(strip, "multiply_speed")
                if strip.type in {'CROSS', 'GAMMA_CROSS', 'WIPE', 'ALPHA_OVER', 'ALPHA_UNDER', 'OVER_DROP'}:
                    row.prop(strip, "use_default_fade", "Default Fade")
                    if not strip.use_default_fade:
                        row.prop(strip, "effect_fader", text="Effect fader")
                if strip.type == 'GAUSSIAN_BLUR':
                    row.prop(strip, "size_x")
                    row.prop(strip, "size_y")
                
                if strip.type == 'WIPE':
                    row = layout.row()
                    row.prop(strip, "transition_type", expand=True)
                    row = layout.row()
                    row.prop(strip, "direction", expand=True)
                    row.prop(strip, "blur_width", slider=True)
                    if strip.transition_type in {'SINGLE', 'DOUBLE'}:
                        row.prop(strip, "angle")

                if strip.type == 'GLOW':
                    flow = layout.column_flow()
                    flow.prop(strip, "threshold", slider=True)
                    flow.prop(strip, "clamp", slider=True)
                    flow.prop(strip, "boost_factor")
                    flow.prop(strip, "blur_radius")

                    row = layout.row()
                    row.prop(strip, "quality", slider=True)
                    row.prop(strip, "use_only_boost")

                if strip.type == 'SPEED':
                    row = layout.row()
                    row.prop(strip, "use_default_fade", "Stretch to input strip length")
                    if not strip.use_default_fade:
                        row.prop(strip, "use_as_speed")
                        if strip.use_as_speed:
                            layout.prop(strip, "speed_factor")
                        else:
                            layout.prop(strip, "speed_factor", text="Frame number")
                            layout.prop(strip, "scale_to_length")

                if strip.type == 'TRANSFORM':
                    row = layout.row(align=True)
                    row.prop(strip, "interpolation")
                    row.prop(strip, "translation_unit")
                    row = layout.row(align=True)
                    row.prop(strip, "translate_start_x", text="Pos X")
                    row.prop(strip, "translate_start_y", text="Pos Y")

                    row = layout.row(align=True)
                    if strip.use_uniform_scale:
                        row.prop(strip, "scale_start_x", text="Scale")
                    else:
                        row.prop(strip, "scale_start_x", text="Scale X")
                        row.prop(strip, "scale_start_y", text="Scale Y")
                    row = layout.row(align=True)
                    row.prop(strip, "use_uniform_scale")
                    row.prop(strip, "rotation_start", text="Rotation")

                if strip.type == 'MULTICAM':
                    layout.prop(strip, "multicam_source")

                    row = layout.row(align=True)
                    sub = row.row(align=True)
                    sub.scale_x = 2.0

                    sub.operator("screen.animation_play", text="", icon='PAUSE' if context.screen.is_animation_playing else 'PLAY')

                    row.label("Cut To")
                    for i in range(1, strip.channel):
                        row.operator("sequencer.cut_multicam", text="%d" % i).camera = i

                
                try:
                    if strip.input_count > 0:
                        col = layout.column()
                        col.prop(strip, "input_1")
                        if strip.input_count > 1:
                            col.prop(strip, "input_2")   
                except AttributeError:
                    pass
                                    
            # extra info box:
            if prefs.kr_extra_info:
                layout = self.layout
                box = layout.box()
                if strip.type not in {'SOUND'}:
                    row = box.row(align=True)
                    sub = row.row(align=True)
                    # MUTE THIS BOX 
                    box.active = (not strip.mute)
                    sub.prop(prefs, "kr_extra_info", text = "", icon='BORDERMOVE', emboss = True)
                    sub.separator()
                    sub.prop(strip, "blend_alpha", text="Opacity", slider=True)
                    row.prop(strip, "mute", toggle=True, icon_only=True)
                    row.prop(strip, "lock", toggle=True, icon_only=True)

                    row = box.row(align=True)
                    
                    col = row.column()
                    col.prop(strip, "strobe")
                    col.prop(strip, "use_flip_x", text="flip X")
                    col.prop(strip, "use_flip_y", text="flip Y")
                    col.prop(strip, "use_reverse_frames", text="Backwards")
                    col.prop(strip, "use_deinterlace")
                    
                    col = row.column()
                    col.prop(strip, "blend_type", icon='COLOR', text = "")

                    col.prop(strip, "color_saturation", text="Saturation")
                    col.prop(strip, "color_multiply", text="Multiply")
                    col.prop(strip, "use_float", text="Convert Float")
                    col.prop(strip, "alpha_mode")
                    
                    row = box.row(align=True)
                    row.prop(strip, "use_translation", text="Image Offset", icon = "AXIS_TOP")
                    row.prop(strip, "use_crop", text="Image Crop", icon = "BORDER_RECT")
                    if strip.use_translation:
                            row = box.row(align=True)
                            row.prop(strip.transform, "offset_x", text="X")
                            row.prop(strip.transform, "offset_y", text="Y")
                    if strip.use_crop:
                        row = box.row(align=True)
                        row.prop(strip.crop, "max_y")
                        row.prop(strip.crop, "min_x")
                        row.prop(strip.crop, "min_y")
                        row.prop(strip.crop, "max_x")
                                        
                    
                #sound type
                else:
                    row = box.row(align=True)
                    row.prop(strip, "volume")
                    row.prop(strip, "mute", toggle=True, icon_only=True)
                    row.prop(strip, "lock", toggle=True, icon_only=True)
                    
                    sound = strip.sound
                    if sound is not None:
                        row = box.row()
                        if sound.packed_file:
                            row.operator("sound.unpack", icon='PACKAGE', text="Unpack")
                        else:
                            row.operator("sound.pack", icon='UGLYPACKAGE', text="Pack")

                        row.prop(sound, "use_memory_cache")

                    row.prop(strip, "show_waveform")
                    
                    row = box.row()
                    row.prop(strip, "pitch")
                    row.prop(strip, "pan")
                
            
            ## modifiers
            if strip.type != 'SOUND' and prefs.kr_show_modifiers:
                sequencer = context.scene.sequence_editor
                layout = self.layout
                layout = layout.box()
                # MUTE THIS BOX
                layout.active = (not strip.mute)
                row = layout.split(percentage=0.075)
                row.prop(prefs, "kr_show_modifiers", text = "", icon='RESTRICT_VIEW_OFF', emboss = True)
                row = row.split(percentage=0.40)
                row.prop(strip, "use_linear_modifiers", text="Linear")
                row = row.split(percentage=1)
                row.operator_menu_enum("sequencer.strip_modifier_add", "type")
                for mod in strip.modifiers:
                    box = layout.box()

                    row = box.row()
                    row.prop(mod, "show_expanded", text="", emboss=False)
                    row.prop(mod, "name", text="")

                    row.prop(mod, "mute", text="")

                    sub = row.row(align=True)
                    props = sub.operator("sequencer.strip_modifier_move", text="", icon='TRIA_UP')
                    props.name = mod.name
                    props.direction = 'UP'
                    props = sub.operator("sequencer.strip_modifier_move", text="", icon='TRIA_DOWN')
                    props.name = mod.name
                    props.direction = 'DOWN'

                    row.operator("sequencer.strip_modifier_remove", text="", icon='X', emboss=False).name = mod.name

                    if mod.show_expanded:
                        row = box.row()
                        row.prop(mod, "input_mask_type", expand=True)

                        if mod.input_mask_type == 'STRIP':
                            sequences_object = sequencer
                            if sequencer.meta_stack:
                                sequences_object = sequencer.meta_stack[-1]
                            box.prop_search(mod, "input_mask_strip", sequences_object, "sequences", text="Mask")
                        else:
                            box.prop(mod, "input_mask_id")
                            row = box.row()
                            row.prop(mod, "mask_time", expand=True)

                        if mod.type == 'COLOR_BALANCE':
                            box.prop(mod, "color_multiply")
                            draw_color_balance(box, mod.color_balance)
                        elif mod.type == 'CURVES':
                            box.template_curve_mapping(mod, "curve_mapping", type='COLOR')
                        elif mod.type == 'HUE_CORRECT':
                            box.template_curve_mapping(mod, "curve_mapping", type='HUE')
                        elif mod.type == 'BRIGHT_CONTRAST':
                            col = box.column()
                            col.prop(mod, "bright")
                            col.prop(mod, "contrast")
                        elif mod.type == 'WHITE_BALANCE':
                            col = box.column()
                            col.prop(mod, "white_value")
                        elif mod.type == 'TONEMAP':
                            col = box.column()
                            col.prop(mod, "tonemap_type")
                            if mod.tonemap_type == 'RD_PHOTORECEPTOR':
                                col.prop(mod, "intensity")
                                col.prop(mod, "contrast")
                                col.prop(mod, "adaptation")
                                col.prop(mod, "correction")
                            elif mod.tonemap_type == 'RH_SIMPLE':
                                col.prop(mod, "key")
                                col.prop(mod, "offset")
                                col.prop(mod, "gamma")
                            
                if "copy_modifiers" in dir(bpy.ops.sequencer):
                    row = layout.row(align=True)
                    row.operator("sequencer.copy_modifiers", text="Copy Modifiers", icon='COPYDOWN')
                    row.operator("sequencer.paste_modifiers", text="Paste Modifiers", icon='PASTEDOWN')

                
        

        
        

        









