import glob
import sys
import os
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.VideoClip import ImageClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.fx.all import crop, resize
import toml


default_watermark_position = ("left", "top")
force_overwrite_existing = False

watermark_filename = "images/watermark.png"
# watermark has its aspect ratio preserved
watermark_height = 300


# Convert "h:m:s" to seconds, with all components after right-most optional.
# i.e. can be "m:s" or just "s"
def time_to_seconds(time_string):
    components = list(map(int, time_string.split(':')))[::-1]
    multipliers = [1, 60, 3600]  # Seconds, Minutes, Hours

    total_seconds = sum(component * multiplier for component, multiplier in zip(components, multipliers))

    return total_seconds


def process_segment(video_path, idx, desc, segment):
    # filename without extension
    base_name = os.path.splitext(video_path)[0]
    output_filename = f"{base_name}__seg{idx:04d}__{desc}.mp4"

    if os.path.isfile(output_filename) and not force_overwrite_existing:
        print(f"File {output_filename} already exists, skipping...")
        return

    start_time = time_to_seconds(segment['start_time'])
    end_time = time_to_seconds(segment['end_time'])

    clip = VideoFileClip(video_path)

    # Trim
    clip = clip.subclip(start_time, end_time)
    clip_duration = clip.duration  # keep track of the duration

    # print(f"======= Duration found: {clip_duration}")

    # Crop the video if clip_rect is specified
    if 'clip_rect' in segment:
        rect = segment['clip_rect']
        clip = clip.fx(crop, x1=rect['x'], y1=rect['y'], x2=rect['end_x'], y2=rect['end_y'])

    # Add image overlay if watermark_filename is specified
    if watermark_filename is not None:
        # Load the image and resize it
        img = ImageClip(watermark_filename)
        img = img.fx(resize, height=watermark_height)

        # Set the image clip's duration to match the video clip's
        img = img.set_duration(clip_duration)

        # composite video clip with the watermark image overlay
        clip = CompositeVideoClip([clip, img.set_position(default_watermark_position)])

    clip.write_videofile(output_filename)


def process_video_toml(toml_file):
    with open(toml_file, 'r') as f:
        data = toml.load(f)

    video_data = data['video'][0]

    print(f"\n\n======= Processing video: {os.path.basename(video_data['title'])} =======\n")

    for idx, segment in enumerate(video_data['segments']):
        process_segment(video_data['title'], idx, segment['desc'], segment)


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
