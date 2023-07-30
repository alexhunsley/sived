# toml spec helper
#

import sys
from .time import *
from .hexaclip import *


def get_inherited_value(key, segment, video_data, default_value=None):
    return segment.get(key, video_data.get(key, default_value))


def get_time_mode(video_data, default_value=None):
    return video_data.get('time_mode', default_value)
    # return get_inherited_value('time_mode', segment, video_data, None)


def get_output_video_size(segment, default_value=None):
    return segment.get('output_video_size', default_value)


def get_max_pixel_scale(segment, default_value=None):
    return segment.get('max_pixel_scale', default_value)


def get_video_filename(segment, video_data, toml_filename):

    video_path = get_inherited_value('video_filename', segment, video_data, None)

    if video_path is None:
        # default to mp4 file with same name as toml
        video_path = f"{toml_filename.split('.')[0]}.mp4"

    return video_path


def get_start_time(segment, video_data):
    if start_time := get_inherited_value('start_time', segment, video_data):
        return time_to_seconds(start_time)

    return 0


def get_end_time(segment, video_data, default_value):
    if end_time := get_inherited_value('end_time', segment, video_data):
        return time_to_seconds(end_time)

    return default_value


def get_rgb_mult(segment, video_data):
    return get_inherited_value('rgb_mult', segment, video_data)


def get_watermark_home(segment, video_data):
    return get_inherited_value('watermark_home', segment, video_data)


def get_watermark_filename(segment, video_data):
    fnames = get_inherited_value('watermark_filename', segment, video_data, None)

    # if nothing specified, don't try prepending 'h' to front if it's missing
    if fnames is None or len(fnames) == 0:
        return None

    # default to 'h' layout if none provided as first item
    if len(fnames.split('=')[0]) == 1:
        return fnames

    return f"h=={fnames}"


# watermark has its aspect ratio preserved
def get_watermark_dimension(segment, video_data):
    return get_inherited_value('watermark_dimension', segment, video_data, 225)


def get_watermark_position(segment, video_data):
    return get_inherited_value('watermark_position', segment, video_data, ("left", "top"))


def get_fade_mode(segment, video_data):
    return get_inherited_value('fade_mode', segment, video_data, False)


def get_fade_duration(segment, video_data):
    return get_inherited_value('fade_duration', segment, video_data, -1)


def get_temp_transpose_xy_size(segment, video_data):
    return get_inherited_value('temp_transpose_xy_size', segment, video_data, False)


def get_desc(segment, video_data):
    return get_inherited_value('desc', segment, video_data, "desc")


def get_clip_rect(segment, video_data, map_rect=None):
    value = get_inherited_value('clip_rect', segment, video_data, None)

    print(f" get_inher_value for get_clip_rect: {value}")

    # we allow hexaclip strings for clip_rect
    if isinstance(value, str):
        if map_rect is None:
            print("\n\n Error: map_rect not given, but found a hexaclip string for a clip_rect")
            sys.exit(1)

        clip_rect = Hexaclip.rect(value, map_rect)
        value = {'x': clip_rect[0], 'y': clip_rect[1], 'end_x': clip_rect[2], 'end_y': clip_rect[3] }
        print(f"------- Built hexaclip value: {value}")

    return value



def get_grab_frame(segment):
    if grab_frame := segment.get('grab_frame'):
        # print(f"got grab_frame BEFORE: {grab_frame}")
        grab_frame['time'] = time_to_seconds(grab_frame['time'])
        # print(f"got grab_frame AFTER: {grab_frame}")

    return grab_frame


def get_text(segment):
    return segment.get('text')


def get_segment_loop_count(segment, video_data):
    return get_inherited_value('segment_loop_count', segment, video_data, None)
