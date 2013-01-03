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


class TimeCode:
    """
    Simple timecode class
    also supports conversion from other time strings used by EDL
    """
    __slots__ = (
        "fps",
        "hours",
        "minutes",
        "seconds",
        "frame",
    )

    def __init__(self, data, fps):
        self.fps = fps
        if type(data) == str:
            self.fromString(data)
            frame = self.asFrame()
            self.fromFrame(frame)
        else:
            self.fromFrame(data)

    def fromString(self, text):
        # hh:mm:ss:ff
        # No dropframe support yet

        if text.lower().endswith("mps"):  # 5.2mps
            return self.fromFrame(int(float(text[:-3]) * self.fps))
        elif text.lower().endswith("s"):  # 5.2s
            return self.fromFrame(int(float(text[:-1]) * self.fps))
        elif text.isdigit():  # 1234
            return self.fromFrame(int(text))
        elif ":" in text:  # hh:mm:ss:ff
            text = text.replace(";", ":").replace(",", ":").replace(".", ":")
            text = text.split(":")

            self.hours = int(text[0])
            self.minutes = int(text[1])
            self.seconds = int(text[2])
            self.frame = int(text[3])
            return self
        else:
            print("ERROR: could not convert this into timecode %r" % text)
            return self

    def fromFrame(self, frame):

        if frame < 0:
            frame = -frame
            neg = True
        else:
            neg = False

        fpm = 60 * self.fps
        fph = 60 * fpm

        if frame < fph:
            self.hours = 0
        else:
            self.hours = int(frame / fph)
            frame = frame % fph

        if frame < fpm:
            self.minutes = 0
        else:
            self.minutes = int(frame / fpm)
            frame = frame % fpm

        if frame < self.fps:
            self.seconds = 0
        else:
            self.seconds = int(frame / self.fps)
            frame = frame % self.fps

        self.frame = frame

        if neg:
            self.frame = -self.frame
            self.seconds = -self.seconds
            self.minutes = -self.minutes
            self.hours = -self.hours

        return self

    def asFrame(self):
        abs_frame = self.frame
        abs_frame += self.seconds * self.fps
        abs_frame += self.minutes * 60 * self.fps
        abs_frame += self.hours * 60 * 60 * self.fps

        return abs_frame

    def asString(self):
        self.fromFrame(int(self))
        return "%.2d:%.2d:%.2d:%.2d" % (self.hours, self.minutes, self.seconds, self.frame)

    def __repr__(self):
        return self.asString()

    # Numeric stuff, may as well have this
    def __neg__(self):
        return TimeCode(-int(self), self.fps)

    def __int__(self):
        return self.asFrame()

    def __sub__(self, other):
        return TimeCode(int(self) - int(other), self.fps)

    def __add__(self, other):
        return TimeCode(int(self) + int(other), self.fps)

    def __mul__(self, other):
        return TimeCode(int(self) * int(other), self.fps)

    def __div__(self, other):
        return TimeCode(int(self) // int(other), self.fps)

    def __abs__(self):
        return TimeCode(abs(int(self)), self.fps)

    def __iadd__(self, other):
        return self.fromFrame(int(self) + int(other))

    def __imul__(self, other):
        return self.fromFrame(int(self) * int(other))

    def __idiv__(self, other):
        return self.fromFrame(int(self) // int(other))
# end timecode


"""Comments
Comments can appear at the beginning of the EDL file (header) or between the edit lines in the EDL. The first block of comments in the file is defined to be the header comments and they are associated with the EDL as a whole. Subsequent comments in the EDL file are associated with the first edit line that appears after them.
Edit Entries
<filename|tag>  <EditMode>  <TransitionType>[num]  [duration]  [srcIn]  [srcOut]  [recIn]  [recOut]

    * <filename|tag>: Filename or tag value. Filename can be for an MPEG file, Image file, or Image file template. Image file templates use the same pattern matching as for command line glob, and can be used to specify images to encode into MPEG. i.e. /usr/data/images/image*.jpg
    * <EditMode>: 'V' | 'A' | 'VA' | 'B' | 'v' | 'a' | 'va' | 'b' which equals Video, Audio, Video_Audio edits (note B or b can be used in place of VA or va).
    * <TransitonType>: 'C' | 'D' | 'E' | 'FI' | 'FO' | 'W' | 'c' | 'd' | 'e' | 'fi' | 'fo' | 'w'. which equals Cut, Dissolve, Effect, FadeIn, FadeOut, Wipe.
    * [num]: if TransitionType = Wipe, then a wipe number must be given. At the moment only wipe 'W0' and 'W1' are supported.
    * [duration]: if the TransitionType is not equal to Cut, then an effect duration must be given. Duration is in frames.
    * [srcIn]: Src in. If no srcIn is given, then it defaults to the first frame of the video or the first frame in the image pattern. If srcIn isn't specified, then srcOut, recIn, recOut can't be specified.
    * [srcOut]: Src out. If no srcOut is given, then it defaults to the last frame of the video - or last image in the image pattern. if srcOut isn't given, then recIn and recOut can't be specified.
    * [recIn]: Rec in. If no recIn is given, then it is calculated based on its position in the EDL and the length of its input.
      [recOut]: Rec out. If no recOut is given, then it is calculated based on its position in the EDL and the length of its input. first frame of the video.

For srcIn, srcOut, recIn, recOut, the values can be specified as either timecode, frame number, seconds, or mps seconds. i.e.
[tcode | fnum | sec | mps], where:

    * tcode : SMPTE timecode in hh:mm:ss:ff
    * fnum : frame number (the first decodable frame in the video is taken to be frame 0).
    * sec : seconds with 's' suffix (e.g. 5.2s)
    * mps : seconds with 'mps' suffix (e.g. 5.2mps). This corresponds to the 'seconds' value displayed by Windows MediaPlayer.

More notes,
Key

"""

enum = 0
TRANSITION_UNKNOWN = enum
TRANSITION_CUT = enum
enum += 1
TRANSITION_DISSOLVE = enum
enum += 1
TRANSITION_EFFECT = enum
enum += 1
TRANSITION_FADEIN = enum
enum += 1
TRANSITION_FADEOUT = enum
enum += 1
TRANSITION_WIPE = enum
enum += 1
TRANSITION_KEY = enum
enum += 1

TRANSITION_DICT = {
    "c": TRANSITION_CUT,
    "d": TRANSITION_DISSOLVE,
    "e": TRANSITION_EFFECT,
    "fi": TRANSITION_FADEIN,
    "fo": TRANSITION_FADEOUT,
    "w": TRANSITION_WIPE,
    "k": TRANSITION_KEY,
    }

enum = 0
EDIT_UNKNOWN = 1 << enum
enum += 1
EDIT_VIDEO = 1 << enum
enum += 1
EDIT_AUDIO = 1 << enum
enum += 1
EDIT_AUDIO_STEREO = 1 << enum
enum += 1
EDIT_VIDEO_AUDIO = 1 << enum
enum += 1

EDIT_DICT = {
    "v": EDIT_VIDEO,
    "a": EDIT_AUDIO,
    "aa": EDIT_AUDIO_STEREO,
    "va": EDIT_VIDEO_AUDIO,
    "b": EDIT_VIDEO_AUDIO,
    }


enum = 0
WIPE_UNKNOWN = enum
WIPE_0 = enum
enum += 1
WIPE_1 = enum
enum += 1

enum = 0
KEY_UNKNOWN = enum
KEY_BG = enum  # K B
enum += 1
KEY_IN = enum  # This is assumed if no second type is set
enum += 1
KEY_OUT = enum  # K O
enum += 1


"""
Most sytems:
Non-dropframe: 1:00:00:00 - colon in last position
Dropframe: 1:00:00;00 - semicolon in last position
PAL/SECAM: 1:00:00:00 - colon in last position

SONY:
Non-dropframe: 1:00:00.00 - period in last position
Dropframe: 1:00:00,00 - comma in last position
PAL/SECAM: 1:00:00.00 - period in last position
"""

"""
t = abs(timecode('-124:-12:-43:-22', 25))
t /= 2
print t
"""


def editFlagsToText(flag):
    items = []
    for item, val in EDIT_DICT.items():
        if val & flag:
            items.append(item)
    return "/".join(items)


class EditDecision:
    __slots__ = (
        "number",
        "reel",
        "transition_duration",
        "edit_type",
        "transition_type",
        "wipe_type",
        "key_type",
        "key_fade",
        "srcIn",
        "srcOut",
        "recIn",
        "recOut",
        "m2",
        "filename",
        "custom_data",
    )

    def __init__(self, text=None, fps=25):
        # print text
        self.number = -1
        self.reel = ""  # Uniqie name for this 'file' but not filename, when BL signifies black
        self.transition_duration = 0
        self.edit_type = EDIT_UNKNOWN
        self.transition_type = TRANSITION_UNKNOWN
        self.wipe_type = WIPE_UNKNOWN
        self.key_type = KEY_UNKNOWN
        self.key_fade = -1  # true/false
        self.srcIn = None   # Where on the original field recording the event begins
        self.srcOut = None  # Where on the original field recording the event ends
        self.recIn = None   # Beginning of the original event in the edited program
        self.recOut = None  # End of the original event in the edited program
        self.m2 = None      # fps set by the m2 command
        self.filename = ""

        self.custom_data = []  # use for storing any data you want (blender strip for eg)

        if text is not None:
            self.read(text, fps)

    def __repr__(self):
        txt = "num: %d, " % self.number
        txt += "reel: %s, " % self.reel
        txt += "edit_type: "
        txt += editFlagsToText(self.edit_type) + ", "

        txt += "trans_type: "
        for item, val in TRANSITION_DICT.items():
            if val == self.transition_type:
                txt += item + ", "
                break

        txt += "m2: "
        if self.m2:
            txt += "%g" % float(self.m2.fps)
            txt += "\n\t"
            txt += self.m2.data
        else:
            txt += "nil"

        txt += ", "
        txt += "recIn: " + str(self.recIn) + ", "
        txt += "recOut: " + str(self.recOut) + ", "
        txt += "srcIn: " + str(self.srcIn) + ", "
        txt += "srcOut: " + str(self.srcOut) + ", "

        return txt

    def read(self, line, fps):
        line = line.split()
        index = 0
        self.number = int(line[index])
        index += 1
        self.reel = line[index].lower()
        index += 1

        # AA/V can be an edit type
        self.edit_type = 0
        for edit_type in line[index].lower().split("/"):
            self.edit_type |= EDIT_DICT[edit_type]
        index += 1

        tx_name = "".join([c for c in line[index].lower() if not c.isdigit()])
        self.transition_type = TRANSITION_DICT[tx_name]  # advance the index later

        if self.transition_type == TRANSITION_WIPE:
            tx_num = "".join([c for c in line[index].lower() if c.isdigit()])
            if tx_num:
                tx_num = int(tx_num)
            else:
                tx_num = 0

            self.wipe_type = tx_num

        elif self.transition_type == TRANSITION_KEY:  # UNTESTED

            val = line[index + 1].lower()

            if val == "b":
                self.key_type = KEY_BG
                index += 1
            elif val == "o":
                self.key_type = KEY_OUT
                index += 1
            else:
                self.key_type = KEY_IN  # if no args given

            # there may be an (F) after, eg 'K B (F)'
            # in the docs this should only be after K B but who knows, it may be after K O also?
            val = line[index + 1].lower()
            if val == "(f)":
                index += 1
                self.key_fade = True
            else:
                self.key_fade = False

        index += 1

        if self.transition_type in {TRANSITION_DISSOLVE, TRANSITION_EFFECT, TRANSITION_FADEIN, TRANSITION_FADEOUT, TRANSITION_WIPE}:
            self.transition_duration = TimeCode(line[index], fps)
            index += 1

        if index < len(line):
            self.srcIn = TimeCode(line[index], fps)
            index += 1
        if index < len(line):
            self.srcOut = TimeCode(line[index], fps)
            index += 1

        if index < len(line):
            self.recIn = TimeCode(line[index], fps)
            index += 1
        if index < len(line):
            self.recOut = TimeCode(line[index], fps)
            index += 1

    def renumber(self):
        self.edits.sort(key=lambda e: int(e.recIn))
        for i, edit in enumerate(self.edits):
            edit.number = i

    def clean(self):
        """
        Clean up double ups
        """
        self.renumber()

        # TODO
    def asName(self):
        cut_type = "nil"
        for k, v in TRANSITION_DICT.items():
            if v == self.transition_type:
                cut_type = k
                break

        return "%d_%s_%s" % (self.number, self.reel, cut_type)


class M2:
    __slots__ = (
        "reel",
        "fps",
        "time",
        "data",
        "index",
        "tot",
    )

    def __init__(self):
        self.reel = None
        self.fps = None
        self.time = None
        self.data = None

        self.index = -1
        self.tot = -1

    def read(self, line, fps):

        # M2   TAPEC          050.5                00:08:11:08
        words = line.split()

        self.reel = words[1].lower()
        self.fps = float(words[2])
        self.time = TimeCode(words[3], fps)

        self.data = line


class EditList:
    __slots__ = (
        "edits",
        "title",
    )

    def __init__(self):
        self.edits = []
        self.title = ""

    def parse(self, filename, fps):
        try:
            file = open(filename, "rU")
        except:
            return False

        self.edits = []
        edits_m2 = []  # edits with m2's

        has_m2 = False

        for line in file:
            line = " ".join(line.split())

            if not line or line.startswith(("*", "#")):
                continue
            elif line.startswith("TITLE:"):
                self.title = " ".join(line.split()[1:])
            elif line.split()[0].lower() == "m2":
                has_m2 = True
                m2 = M2()
                m2.read(line, fps)
                edits_m2.append(m2)
            elif not line.split()[0].isdigit():
                print("Ignoring:", line)
            else:
                self.edits.append(EditDecision(line, fps))
                edits_m2.append(self.edits[-1])

        if has_m2:
            # Group indexes
            i = 0
            for item in edits_m2:
                if isinstance(item, M2):
                    item.index = i
                    i += 1
                else:
                    # not an m2
                    i = 0

            # Set total group indexes
            for item in reversed(edits_m2):
                if isinstance(item, M2):
                    if tot_m2 == -1:
                        tot_m2 = item.index + 1

                    item.tot = tot_m2
                else:
                    # not an m2
                    tot_m2 = -1

            for i, item in enumerate(edits_m2):
                if isinstance(item, M2):
                    # make a list of all items that match the m2's reel name
                    edits_m2_tmp = [item_tmp for item_tmp in edits_m2 if (isinstance(item, M2) or item_tmp.reel == item.reel)]

                    # get the new index
                    i_tmp = edits_m2_tmp.index(item)

                    # Seek back to get the edit.
                    edit = edits_m2[i_tmp - item.tot]

                    # Note, docs say time should also match with edit start time
                    # but from final cut pro, this seems not to be the case
                    if not isinstance(edit, EditDecision):
                        print("ERROR!", "M2 incorrect")
                    else:
                        edit.m2 = item

        file.close()
        return True

    def testOverlap(self, edit_test):
        recIn = int(edit_test.recIn)
        recOut = int(edit_test.recOut)

        for edit in self.edits:
            if edit is edit_test:
                break

            recIn_other = int(edit.recIn)
            recOut_other = int(edit.recOut)

            if recIn_other < recIn < recOut_other:
                return True
            if recIn_other < recOut < recOut_other:
                return True

            if recIn < recIn_other < recOut:
                return True
            if recIn < recOut_other < recOut:
                return True

        return False

    def getReels(self):
        reels = {}
        for edit in self.edits:
            reels.setdefault(edit.reel, []).append(edit)

        return reels


# ----------------------------------
# Blender spesific stuff starts here
import bpy


def id_animdata_action_ensure(id_data):
    id_data.animation_data_create()
    animation_data = id_data.animation_data
    if animation_data.action is None:
        animation_data.action = bpy.data.actions.new(name="Scene Action")


def scale_meta_speed(sequence_editor, strip_list, strip_movie, scale):
    # Add an effect
    dummy_frame = 0
    strip_speed = sequence_editor.sequences.new_effect(
            name="Speed",
            type='SPEED',
            seq1=strip_movie,
            start_frame=dummy_frame,
            channel=strip_movie.channel + 1)
    strip_list.append(strip_speed)

    # not working in 2.6x :|
    strip_speed.use_frame_blend = True
    #meta = sequence_editor.new([strip_movie, strip_speed], 199, strip_movie.channel)

    # XXX-Meta Operator Mess
    scene = sequence_editor.id_data
    # we _know_ there are no others selected
    for strip in strip_list:
        strip.select = False
    strip_movie.select = True
    strip_speed.select = True
    bpy.ops.sequencer.meta_make()
    strip_meta = scene.sequence_editor.sequences[-1]  # XXX, weak assumption
    assert(strip_meta.type == 'META')
    strip_list.append(strip_meta)
    strip_movie.select = strip_speed.select = strip_meta.select = False
    # XXX-Meta Operator Mess (END)

    if scale >= 1.0:
        strip_movie.frame_still_end = int(strip_movie.frame_duration * (scale - 1.0))
    else:
        strip_speed.multiply_speed = 1.0 / scale
        strip_meta.frame_offset_end = strip_movie.frame_duration - int(strip_movie.frame_duration * scale)

    strip_speed.update()
    strip_meta.update()
    return strip_meta


def apply_dissolve_fcurve(strip_movie, blendin):
    scene = strip_movie.id_data
    id_animdata_action_ensure(scene)
    action = scene.animation_data.action

    data_path = strip_movie.path_from_id("blend_alpha")
    blend_alpha_fcurve = action.fcurves.new(data_path, index=0)
    blend_alpha_fcurve.keyframe_points.insert(strip_movie.frame_final_start, 0.0)
    blend_alpha_fcurve.keyframe_points.insert(strip_movie.frame_final_end, 1.0)

    blend_alpha_fcurve.keyframe_points[0].interpolation = 'LINEAR'
    blend_alpha_fcurve.keyframe_points[1].interpolation = 'LINEAR'

    if strip_movie.type != 'SOUND':
        strip_movie.blend_type = 'ALPHA_OVER'


def replace_ext(path, ext):
    return path[:path.rfind(".") + 1] + ext


def load_edl(scene, filename, reel_files, reel_offsets):
    """
    reel_files - key:reel <--> reel:filename
    """

    strip_list = []

    import os
    # For test file
    # frame_offset = -769

    fps = scene.render.fps
    dummy_frame = 1

    elist = EditList()
    if not elist.parse(filename, fps):
        return "Unable to parse %r" % filename

    scene.sequence_editor_create()
    sequence_editor = scene.sequence_editor

    for strip in sequence_editor.sequences_all:
        strip.select = False

    # elist.clean()

    track = 0

    edits = elist.edits[:]
    # edits.sort(key = lambda edit: int(edit.recIn))

    prev_edit = None
    for edit in edits:
        print(edit)
        frame_offset = reel_offsets[edit.reel]

        src_start = int(edit.srcIn) + frame_offset
        src_end = int(edit.srcOut) + frame_offset
        src_length = src_end - src_start

        rec_start = int(edit.recIn) + 1
        rec_end = int(edit.recOut) + 1
        rec_length = rec_end - rec_start

        # print src_length, rec_length, src_start

        if edit.m2 is not None:
            scale = fps / edit.m2.fps
        else:
            scale = 1.0

        unedited_start = rec_start - src_start
        offset_start = src_start - int(src_start * scale)  # works for scaling up AND down

        if edit.transition_type == TRANSITION_CUT and (not elist.testOverlap(edit)):
            track = 1

        strip = None
        final_strips = []
        if edit.reel.lower() == "bw":
            strip = sequence_editor.sequences.new_effect(
                    name="Wipe",
                    type='COLOR',
                    start_frame=rec_start,
                    channel=track + 1)
            strip_list.append(strip)

            strip.frame_duration = rec_length  # for color its simple
            final_strips.append(strip)
        else:
            path_full = reel_files[edit.reel]
            path_dironly, path_fileonly = os.path.split(path_full)

            if edit.edit_type & EDIT_VIDEO:  # and edit.transition_type == TRANSITION_CUT:

                #try:
                strip = sequence_editor.sequences.new_movie(
                        name=edit.reel,
                        filepath=path_full,
                        channel=track + 1,
                        start_frame=unedited_start + offset_start)
                strip_list.append(strip)
                #except:
                #    return "Invalid input for movie"

                # Apply scaled rec in bounds
                if scale != 1.0:
                    meta = scale_meta_speed(sequence_editor, strip_list, strip, scale)
                    final_strip = meta
                else:
                    final_strip = strip

                final_strip.update()
                final_strip.frame_offset_start = rec_start - final_strip.frame_final_start
                final_strip.frame_offset_end = rec_end - final_strip.frame_final_end
                final_strip.update()
                final_strip.frame_offset_end += (final_strip.frame_final_end - rec_end)
                final_strip.update()

                if edit.transition_duration:
                    if not prev_edit:
                        print("Error no previous strip")
                    else:
                        new_end = rec_start + int(edit.transition_duration)
                        for other in prev_edit.custom_data:
                            if other.type != 'SOUND':
                                other.frame_offset_end += (other.frame_final_end - new_end)
                                other.update()

                # Apply disolve
                if edit.transition_type == TRANSITION_DISSOLVE:
                    apply_dissolve_fcurve(final_strip, edit.transition_duration)

                if edit.transition_type == TRANSITION_WIPE:
                    other_track = track + 2
                    for other in prev_edit.custom_data:
                        if other.type != 'SOUND':
                            strip_wipe = sequence_editor.sequences.new_effect(name="Wipe", type='WIPE', seq1=final_strip, start_frame=dummy_frame, channel=other_track)
                            strip_list.append(strip_wipe)

                            from math import radians
                            if edit.wipe_type == WIPE_0:
                                strip_wipe.angle = radians(+90)
                            else:
                                strip_wipe.angle = radians(-90)

                            other_track += 1

                # strip.frame_offset_end = strip.frame_duration - int(edit.srcOut)
                # end_offset = (unedited_start + strip.frame_duration) - end
                # print start, end, end_offset
                # strip.frame_offset_end = end_offset
                #
                # break
                # print(strip)

                final_strips.append(final_strip)

            if edit.edit_type & (EDIT_AUDIO | EDIT_AUDIO_STEREO | EDIT_VIDEO_AUDIO):

                if scale == 1.0:  # TODO - scaled audio

                    try:
                        strip = sequence_editor.sequences.new_sound(
                                name=edit.reel,
                                filepath=path_full,
                                channel=track + 6,
                                start_frame=unedited_start + offset_start)
                        strip_list.append(strip)
                    except:

                        # See if there is a wave file there
                        path_full_wav = replace_ext(path_full, "wav")
                        path_fileonly_wav = replace_ext(path_fileonly, "wav")

                        #try:
                        strip = sequence_editor.sequences.new_sound(
                                name=edit.reel,
                                filepath=path_full_wav,
                                channel=track + 6,
                                start_frame=unedited_start + offset_start)
                        strip_list.append(strip)
                        #except:
                        #   return "Invalid input for audio"

                    final_strip = strip

                    # Copied from above
                    final_strip.update()
                    final_strip.frame_offset_start = rec_start - final_strip.frame_final_start
                    final_strip.frame_offset_end = rec_end - final_strip.frame_final_end
                    final_strip.update()
                    final_strip.frame_offset_end += (final_strip.frame_final_end - rec_end)
                    final_strip.update()

                    if edit.transition_type == TRANSITION_DISSOLVE:
                        apply_dissolve_fcurve(final_strip, edit.transition_duration)

                    final_strips.append(final_strip)

        if final_strips:
            for strip in final_strips:
                # strip.frame_duration = length
                final_strip.name = edit.asName()
                edit.custom_data[:] = final_strips
                # track = not track
                prev_edit = edit
            track += 1

        #break

    for strip in strip_list:
        strip.update(True)
        strip.select = True

    return ""


def _test():
    elist = EditList()
    _filename = "/fe/edl/cinesoft/rush/blender_edl.edl"
    _fps = 25
    if not elist.parse(_filename, _fps):
        assert(0)
    reels = elist.getReels()

    print(list(reels.keys()))

    # import pdb; pdb.set_trace()
    msg = load_edl(bpy.context.scene,
                   _filename,
                   {'tapec': "/fe/edl/cinesoft/rush/rushes3.avi"},
                   {'tapec': 0})  # /tmp/test.edl
    print(msg)
# _test()
