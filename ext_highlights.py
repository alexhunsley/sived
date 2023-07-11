import glob
import sys
import os
from PIL import Image, ImageEnhance
import numpy as np
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.VideoClip import ImageClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.fx.all import crop, resize
from moviepy.editor import concatenate_videoclips
# from moviepy.video.compositing.transitions import crossfadein, crossfadeout
from moviepy.video.fx.all import fadein, fadeout
from moviepy.video.VideoClip import ColorClip
import toml

# REMINDER:
#   fading is only applied to the showreel (concat) video
#
# We now allow specifying of video_filename per segment (with fallback to video section).
# This is assuming all input videos have same resolution! This requirement might go away
# once we impl the target resolution (for output video) stuff
#
# Have a way to force closeup -- even if will be <1 input pixel per pixel rendered.
#
# Way to pull a still image from a video and make duration clip from that.
#

toml_base_filename = None

make_concatenation_video = True
force_overwrite_existing = True


def get_inherited_value(key, segment, video_data, default_value=None):
    return segment.get(key, video_data.get(key, default_value))


def get_video_filename(segment, video_data):

    video_path = get_inherited_value('video_filename', segment, video_data, None)

    if video_path is None:
        # default to mp4 file with same name as toml
        video_path = f"{toml_file.split('.')[0]}.mp4"

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


def load_image(image_path, rgb_mult = None):
    if rgb_mult == None:
        return ImageClip(image_path)

    (r_mul, g_mul, b_mul) = rgb_mult

    # Load the image
    image = Image.open(image_path)

    # Separate the image into individual color bands (channels)
    r, g, b, a = image.split()

    # Enhance the channels
    r = r.point(lambda i: i * r_mul)
    g = g.point(lambda i: i * g_mul)
    b = b.point(lambda i: i * b_mul)

    # Merge the channels back
    merged_image = Image.merge('RGB', (r, g, b))

    # PIL image to numpy array
    np_image = np.array(merged_image)

    # Create an ImageClip with MoviePy
    image_clip = ImageClip(np_image)

    return image_clip


def calc_watermark_position(video_clip_rect, watermark_size, watermark_position, segment_offset_inside_context):

    # print(f"get_watermark_position: video_clip_rect = {video_clip_rect}, watermark_size = {watermark_size}, watermark_position = {watermark_position}, segment_offset_inside_context = {segment_offset_inside_context}")

    wp_dict = dict(enumerate(watermark_position))

    # Get the video width and height
    # _, _, video_width, video_height = video_clip_rect
    video_width = video_clip_rect['end_x'] - video_clip_rect['x']
    video_height = video_clip_rect['end_y'] - video_clip_rect['y']

    # print(f"GOT VID WID, HEI: {video_width} {video_height}")
    # Get the watermark width and height
    watermark_width, watermark_height = watermark_size

    x = wp_dict.get(0)
    y = wp_dict.get(1)

    if x == None:
        x = 0

    if y == None:
        y = 0

    if watermark_position[0] == "right" or watermark_position[0] == -1:
        x = video_width - watermark_width
    elif watermark_position[0] == -2:
        x = (video_width - watermark_width) / 2.0
    elif watermark_position[0] == "left":
        x = 0

    if watermark_position[1] == "bottom" or watermark_position[1] == -1:
        y = video_height - watermark_height            
    elif watermark_position[1] == -2:
        y = (video_height - watermark_height) / 2.0
    elif watermark_position[1] == "top":
        y = 0

    # print(f"  >>>> get_watermark_position: to xy of {x} {y} am adding segment_offset_inside_context = {segment_offset_inside_context}")
    return (x + segment_offset_inside_context['x'], y + segment_offset_inside_context['y'])


# Convert "h:m:s" to seconds, with all components after right-most optional.
# i.e. can be "m:s" or just "s"
def time_to_seconds(time_string):
    components = list(map(int, time_string.split(':')))[::-1]
    multipliers = [1, 60, 3600]  # Seconds, Minutes, Hours

    total_seconds = sum(component * multiplier for component, multiplier in zip(components, multipliers))

    return total_seconds


# applies a watermark if necessary, returning the resulting clip (or the original clip otherwise)
def apply_watermark(clip, clip_rect, clip_offset_in_context, segment, video_data):

    watermark_filename = get_watermark_filename(segment, video_data)

    if watermark_filename is None:
        return clip

    rgb_mult = get_rgb_mult(segment, video_data)
    # Load the image and resize it
    img = load_image(watermark_filename, rgb_mult)

    # Decide watermark height
    watermark_height = get_watermark_height(segment, video_data)

    img = img.fx(resize, height=watermark_height)

    # Set the image clip's duration to match the video clip's
    img = img.set_duration(clip.duration)

    # Decide watermark position
    watermark_position = get_watermark_position(segment, video_data)

    watermark_offset_in_context = {'x': 0, 'y': 0}

    if make_concatenation_video:
        watermark_offset_in_context['x'] += clip_offset_in_context['x'] - clip_rect['x']
        watermark_offset_in_context['y'] += clip_offset_in_context['y'] - clip_rect['y']
        # print(f"Made a watermark_offset_in_context: {watermark_offset_in_context} from seg clip_rect = {clip_rect}")

    watermark_position = calc_watermark_position(clip_rect, img.size, watermark_position, watermark_offset_in_context)

    # a composite video clip with the watermark image overlay
    return CompositeVideoClip([clip, img.set_position(watermark_position)])


# clip_rect is for just this segment. It might be actual seg rect or the union'd rect.
# segment_clip_rect the segment's own clip rect as per toml.
def process_segment(video_path, idx, desc, segment, video_data, clip_rect, segment_clip_rect):
    # filename without extension
    video_base_filename = os.path.splitext(video_path)[0]


    # output_filename = f'{toml_base_filename}__{video_base_filename}__seg{idx:04d}__{desc}{"__concat" if make_concatenation_video else ""}.mp4'
    output_filename = f'{toml_base_filename}__{video_path}__seg{idx:04d}__{desc}{"__concat" if make_concatenation_video else ""}.mp4'

    if os.path.isfile(output_filename) and not force_overwrite_existing:
        if make_concatenation_video:
            sys.exit("\n\nFound an existing output file and force_overwrite_existing is False, so I can't make a concat video, exiting.\nChange force_overwrite_existing to True if you're ok with that.\n\n")

        print(f"File {output_filename} already exists, skipping...")
        return

    start_time = time_to_seconds(segment['start_time'])
    end_time = time_to_seconds(segment['end_time'])

    clip = VideoFileClip(video_path)

    # Trim
    clip = clip.subclip(start_time, end_time)
    clip_duration = clip.duration  # keep track of the duration

    # Crop the video if clip_rect is specified
    clip = clip.fx(crop, x1=clip_rect['x'], y1=clip_rect['y'], x2=clip_rect['end_x'], y2=clip_rect['end_y'])

    # segment_clip_rect has the x, y we need for clip_offset_in_context
    clip = apply_watermark(clip, clip_rect, segment_clip_rect, segment, video_data)

    # if watermark_filename is not None:

    #     rgb_mult = get_rgb_mult(segment, video_data)
    #     # Load the image and resize it
    #     img = load_image(watermark_filename, rgb_mult)

    #     # Decide watermark height
    #     watermark_height = get_watermark_height(segment, video_data)

    #     img = img.fx(resize, height=watermark_height)

    #     # Set the image clip's duration to match the video clip's
    #     img = img.set_duration(clip_duration)

    #     # Decide watermark position
    #     watermark_position = get_watermark_position(segment, video_data)

    #     watermark_offset_in_context = {'x': 0, 'y': 0}

    #     if make_concatenation_video:
    #         watermark_offset_in_context['x'] += segment_clip_rect['x'] - clip_rect['x']
    #         watermark_offset_in_context['y'] += segment_clip_rect['y'] - clip_rect['y']
    #         # print(f"Made a watermark_offset_in_context: {watermark_offset_in_context} from seg clip_rect = {clip_rect}")

    #     watermark_position = calc_watermark_position(clip_rect, img.size, watermark_position, watermark_offset_in_context)

    #     # a composite video clip with the watermark image overlay
    #     clip = CompositeVideoClip([clip, img.set_position(watermark_position)])

    clip.write_videofile(output_filename)

    return clip


# To fix: 
#   with make_concatenation_video == False:
#
#     each clip needs its own clip obeying!
#
#   with make_concatenation_video == True:
#
#     each clip needs to offset the watermark by diff between own clip rect and the max (master) clip rect
#
def process_video_toml(toml_file):
    global toml_base_filename
    toml_base_filename = toml_file

    with open(toml_file, 'r') as f:
        data = toml.load(f)

    video_data = data['video'][0]

    # use first segment for title and hence finding res of video (assumption)
    first_segment = video_data['segments'][0]
    video_path = get_video_filename(first_segment, video_data)

    # does this load lots of data into memory up front? I'm guessing not.
    video_clip = VideoFileClip(video_path)
    video_size = video_clip.size  # Get video size

    print(f"\n\n======= Processing video: {os.path.basename(video_path)} =======\n")

    # Variables for concatenation
    concat_clips = []

    # Initialized as video size
    # max_clip_rect = {'x': video_size[0], 'y': video_size[1], 'end_x': 0, 'end_y': 0} if make_concatenation_video else {}

    # value which anything can be trumped when unioning. Note origin and size other way round! deliberate.
    # max_clip_rect = {'x': video_size[0], 'y': video_size[1], 'end_x': 0, 'end_y': 0} if make_concatenation_video else  {'x': 0, 'y': 0, 'end_x': video_size[0], 'end_y': video_size[1]}
    max_clip_rect = {'x': video_size[0], 'y': video_size[1], 'end_x': 0, 'end_y': 0}

    # print(f"=-=-==-=   max_clip_rect = {max_clip_rect}")

    if make_concatenation_video:

        # print(f"=-=-==-=   in make_concatenation_video bit")

        for idx, segment in enumerate(video_data['segments']):
            rect = segment.get('clip_rect', {'x': 0, 'y': 0, 'end_x': video_size[0], 'end_y': video_size[1]})  
            # print(f"   IN MIN/MAX, befpre comp, clip rect {rect} and max_clip_rect is {max_clip_rect}")
            max_clip_rect['x'] = min(max_clip_rect['x'], rect['x'])  # x
            max_clip_rect['y'] = min(max_clip_rect['y'], rect['y'])  # y
            max_clip_rect['end_x'] = max(max_clip_rect['end_x'], rect['end_x'])  # end_x
            max_clip_rect['end_y'] = max(max_clip_rect['end_y'], rect['end_y'])  # end_y
            # print(f"   IN MIN/MAX,     after comp, clip rect {rect} and max_clip_rect is {max_clip_rect}")


    for idx, segment in enumerate(video_data['segments']):
        # print(f"=-=-==-=   in segment bit, idx = {idx} segment = {segment}")

        # guess could cache the vids in memory? not sure what being automatically unloaded, anyhoo
        video_path = get_video_filename(segment, video_data)

        # Determine fade duration from the TOML data
        # (Default to -1 second i.e. disabled if not specified)
        fade_duration = get_fade_duration(segment, video_data)
        fade_mode = get_fade_mode(segment, video_data)

        print(f"  =--=-==-=-= fade_mode = {fade_mode} fade_duration = {fade_duration} ")
        segment_clip_rect = segment.get('clip_rect', {'x': 0, 'y': 0, 'end_x': video_size[0], 'end_y': video_size[1]})
        use_clip_rect = max_clip_rect if make_concatenation_video == True else segment_clip_rect

        # print(f"=-=-==-=      ... use_clip_rect for {idx} = {use_clip_rect}")

        output_clip = process_segment(video_path, idx, segment['desc'], segment, video_data, use_clip_rect, segment_clip_rect) #, max_clip_rect if make_concatenation_video else None)

        if make_concatenation_video:
            print(f"fade_duration = {fade_duration}")
            if fade_duration > 0 and fade_mode:
                print(f" ... so applying crossfade in and out")

                # Apply fade in/out/both to clip
                if fade_mode == "both" or fade_mode == "in": 
                    output_clip = output_clip.fx(fadein, fade_duration)

                if fade_mode == "both" or fade_mode == "out":
                    output_clip = output_clip.fx(fadeout, fade_duration)

                # output_clip = output_clip.crossfadein(fade_duration).crossfadeout(fade_duration)

            reel_loop_count = segment.get('reel_loop_count', 1)
            for i in range(0, reel_loop_count):
                concat_clips.append(output_clip)

    if make_concatenation_video:
        final_clip = concatenate_videoclips(concat_clips)
        final_output_filename = f"{os.path.splitext(video_path)[0]}__concat.mp4"
        final_clip.write_videofile(final_output_filename)


if __name__ == "__main__":
    # Check if the script was called with an argument
    if len(sys.argv) != 2:
        sys.exit("Error: This script requires one argument: the name of the TOML file to process, or 'all'.")

    # If the argument is 'all', process all .toml files in the current directory
    if sys.argv[1] == 'all':
        toml_files = glob.glob("*.toml")
        for toml_file in toml_files:
            process_video_toml(toml_file)
    # Otherwise, process the specified TOML file
    else:
        process_video_toml(sys.argv[1])
