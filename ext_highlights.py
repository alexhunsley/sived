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
import toml


make_concatenation_video = False

default_watermark_position = ("left", "top")
force_overwrite_existing = True

watermark_filename = "images/watermark.png"
# watermark has its aspect ratio preserved
default_watermark_height = 225
# e.g. (0.9, 1.0, 1.2)
default_rgb_mult = None


def get_rgb_mult(segment, video_data):
    return segment.get('rgb_mult', video_data.get('rgb_mult', default_rgb_mult))


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


def get_watermark_position(video_size, watermark_size, watermark_position):

    wp_dict = dict(enumerate(watermark_position))

    # Get the video width and height
    video_width, video_height = video_size

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

    return (x, y)


# Convert "h:m:s" to seconds, with all components after right-most optional.
# i.e. can be "m:s" or just "s"
def time_to_seconds(time_string):
    components = list(map(int, time_string.split(':')))[::-1]
    multipliers = [1, 60, 3600]  # Seconds, Minutes, Hours

    total_seconds = sum(component * multiplier for component, multiplier in zip(components, multipliers))

    return total_seconds


def process_segment(video_path, idx, desc, segment, video_data, clip_rect):
    # filename without extension
    base_name = os.path.splitext(video_path)[0]

    output_filename = f'{base_name}__seg{idx:04d}__{desc}{"__concat" if make_concatenation_video else ""}.mp4'

    if os.path.isfile(output_filename) and not force_overwrite_existing:
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

    # Add image overlay if watermark_filename is specified
    if watermark_filename is not None:

        rgb_mult = get_rgb_mult(segment, video_data)
        # Load the image and resize it
        img = load_image(watermark_filename, rgb_mult)

        # Decide watermark height
        watermark_height = segment.get('watermark_height',
                                        video_data.get('watermark_height', default_watermark_height))
        img = img.fx(resize, height=watermark_height)

        # Set the image clip's duration to match the video clip's
        img = img.set_duration(clip_duration)

        # Decide watermark position
        watermark_position = segment.get('watermark_position',
                                         video_data.get('watermark_position', default_watermark_position))
        watermark_position = get_watermark_position(clip.size, img.size, watermark_position)

        # a composite video clip with the watermark image overlay
        clip = CompositeVideoClip([clip, img.set_position(watermark_position)])

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
    with open(toml_file, 'r') as f:
        data = toml.load(f)

    video_data = data['video'][0]
    video_path = video_data['title']
    video_clip = VideoFileClip(video_path)
    video_size = video_clip.size  # Get video size

    print(f"\n\n======= Processing video: {os.path.basename(video_path)} =======\n")

    # Variables for concatenation
    concat_clips = []

    # Initialized as video size
    # max_clip_rect = {'x': video_size[0], 'y': video_size[1], 'end_x': 0, 'end_y': 0} if make_concatenation_video else {}

    # value which anything can trump when unioning
    # max_clip_rect = {'x': video_size[0], 'y': video_size[1], 'end_x': 0, 'end_y': 0} if make_concatenation_video else  {'x': 0, 'y': 0, 'end_x': video_size[0], 'end_y': video_size[1]}
    max_clip_rect = {'x': video_size[0], 'y': video_size[1], 'end_x': 0, 'end_y': 0}

    print(f"=-=-==-=   max_clip_rect = {max_clip_rect}")

    if make_concatenation_video:
        print(f"=-=-==-=   in make_concatenation_video bit")

        for idx, segment in enumerate(video_data['segments']):
            rect = segment.get('clip_rect', {'x': 0, 'y': 0, 'end_x': video_size[0], 'end_y': video_size[1]})  
            max_clip_rect['x'] = min(max_clip_rect['x'], rect['x'])  # x
            max_clip_rect['y'] = min(max_clip_rect['y'], rect['y'])  # y
            max_clip_rect['end_x'] = max(max_clip_rect['end_x'], rect['end_x'])  # end_x
            max_clip_rect['end_y'] = max(max_clip_rect['end_y'], rect['end_y'])  # end_y


    for idx, segment in enumerate(video_data['segments']):
        print(f"=-=-==-=   in segment bit, idx = {idx} segment = {segment}")

        use_clip_rect = max_clip_rect if make_concatenation_video else segment.get('clip_rect', {'x': 0, 'y': 0, 'end_x': video_size[0], 'end_y': video_size[1]})

        print(f"=-=-==-=      ... use_clip_rect for {idx} = {use_clip_rect}")

        output_clip = process_segment(video_path, idx, segment['desc'], segment, video_data, use_clip_rect)
        if make_concatenation_video:
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
