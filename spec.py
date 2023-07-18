# toml spec helper
#

import toml


def get_inherited_value(key, segment, video_data, default_value=None):
    return segment.get(key, video_data.get(key, default_value))


def get_video_filename(segment, video_data, toml_filename):

    video_path = get_inherited_value('video_filename', segment, video_data, None)

    if video_path is None:
        # default to mp4 file with same name as toml
        video_path = f"{toml_filename.split('.')[0]}.mp4"

    return video_path


def get_rgb_mult(segment, video_data):
    return get_inherited_value('rgb_mult', segment, video_data)


def get_watermark_filename(segment, video_data):
    return get_inherited_value('watermark_filename', segment, video_data, None)


# watermark has its aspect ratio preserved
def get_watermark_height(segment, video_data):
    return get_inherited_value('watermark_height', segment, video_data, 225)


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


def get_grab_frame(segment):
    if grab_frame := segment.get('grab_frame'):
        # print(f"got grab_frame BEFORE: {grab_frame}")
        grab_frame['time'] = time_to_seconds(grab_frame['time'])
        # print(f"got grab_frame AFTER: {grab_frame}")

    return grab_frame
