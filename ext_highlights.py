import glob
import sys
import os
import toml
from moviepy.editor import *
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.video.io.VideoFileClip import VideoFileClip
# from moviepy.video.VideoClip import ImageClip
# from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
# from moviepy.video.fx.all import crop, resize, rotate
from moviepy.editor import concatenate_videoclips
from moviepy.video.fx.all import fadein, fadeout
from moviepy.video.VideoClip import ColorClip

# This works for local run from command line: 
#
# In dir above:
#
#     python -m video-highlights.ext_highlights
#
#                   ^ package   .    ^ module (filename)
#
# or add that above dir to pythonpath by running this in this dir:
#
#   export PYTHONPATH=`cd ..:pwd`
#
# NB must use ':' not ';' for separator here!
#
# input files are looked for relative to working dir, as you'd expected.
# should output file rel path be relative to working dir, or to vid input dir?
# I think the former -- might have different video input dirs, after all.
#

toml_base_filename = None

make_concatenation_video = True
force_overwrite_existing = True

working_dir = os.getcwd()

from .spec import *
from .helpers import *
from .image import *
from .time import *
from .size import *


# s1 = Size.make(10, 10)
# s2 = Size.make(50, 100)
# print(f"s1 = {s1}")
# print(f"s2 = {s2}")
# print(f"s1.fill(s2) = {s1.aspect_filled_to(s2)}")
# print(f"s1.fit(s2) = {s1.aspect_fitted_to(s2)}")
# sys.exit(0)

# script_dir = os.path.abspath(os.path.dirname(__file__))
# working_dir = os.getcwd()

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



# clip_rect is for just this segment. It might be actual seg rect or the union'd rect.
# segment_clip_rect the segment's own clip rect as per toml.
def process_segment(video_path, idx, desc, segment, video_data, clip_rect, segment_clip_rect):
    # filename without extension
    # video_base_filename = os.path.splitext(os.path.basename(video_path))[0]

    print(f"   passed video_path = {video_path}")

    video_base_filename = os.path.basename(video_path)

    output_filename = f'{toml_base_filename}__{video_base_filename}__seg{idx:04d}__{desc}{"__concat" if make_concatenation_video else ""}.mp4'
    # output_filename = f'{toml_base_filename}__{video_path}__seg{idx:04d}__{desc}{"__concat" if make_concatenation_video else ""}.mp4'

    print(f"   video_base_filename = {video_base_filename}")
    print(f"Made output_filename = {output_filename}")

    if os.path.isfile(output_filename) and not force_overwrite_existing:
        if make_concatenation_video:
            sys.exit("\n\nFound an existing output file and force_overwrite_existing is False, so I can't make a concat video, exiting.\nChange force_overwrite_existing to True if you're ok with that.\n\n")

        print(f"File {output_filename} already exists, skipping...")
        return

    video_clip = VideoFileClip(video_path)

    if grab_frame := get_grab_frame(segment):
        print(f"found a grab_frame: {grab_frame}")
        # Convert the frame to an ImageClip
        
        frame = video_clip.get_frame(grab_frame['time']) 

        clip = ImageClip(frame, duration=grab_frame['duration'])
        # doesn't work, interacts with the xy flip further down? video corrupts as still image plays.
        # clip = (ImageClip(frame, duration=grab_frame['duration'])
        #     .resize(lambda t : 1+0.02*t)
        # )

        # TODO get from somewhere authoritative later, e.g. the reference video clip (later)
        # use 1 if no zoom? otherwise 30
        clip.fps = 30

    else:
        clip = video_clip
        # clip = VideoFileClip(video_path)

        print(f"  -------- clip rotation: {clip.rotation}")

        start_time = time_to_seconds(segment.get('start_time', "0"))
        end_time = time_to_seconds(segment.get('end_time', f"{clip.duration}"))

        # Trim
        clip = clip.subclip(start_time, end_time)
        clip_duration = clip.duration  # keep track of the duration

        # this command shows -90 for a video, but clip.rotation comes back 0!
        # and in fact I need to invert x and y, NOT do rotate.
        #   ffprobe -v 0 -select_streams v:0 -show_entries stream_side_data=rotation -of default=nw=1:nk=1 video15.mov

        # clip rotation in file comes back 0 -- but we need something != 0, clearly!
        # clip = clip.fx(rotate, -90)

        # if clip.rotation == 90:
            # clip.rotation = 0

        # Crop the video if clip_rect is specified
        # order of crop and resize matters.
        clip = clip.fx(crop, x1=clip_rect['x'], y1=clip_rect['y'], x2=clip_rect['end_x'], y2=clip_rect['end_y'])

    if get_temp_transpose_xy_size(segment, video_data):
        clip = clip.resize(clip.size[::-1])

    # segment_clip_rect has the x, y we need for clip_offset_in_context
    clip = apply_watermark(clip, clip_rect, segment_clip_rect, segment, video_data)

    # Zoom in over time - the image will zoom in by 5% per second
    # zoom_in_clip = img.fx(lambda t: img.resize(1 + 0.05*t))

    # Then pan from top to bottom over time
    # pan_clip = zoom_in_clip.fx(lambda t: crop(zoom_in_clip, y1=int(50*t), y2=int(50*t) + img.size[1]))

    clip.write_videofile(output_filename)

    return clip


def process_video_toml(toml_file):
    global toml_base_filename
    toml_base_filename = toml_file

    with open(toml_file, 'r') as f:
        data = toml.load(f)

    video_data = data['video'][0]

    # use first segment for title and hence finding res of video (assumption)
    first_segment = video_data['segments'][0]

    # wrong! want rel to curr dir.
    video_path = make_abs_path_rel_to_working_dir(get_video_filename(first_segment, video_data))

    print(f"working dir: {os.getcwd()}")

    print(f"get_video_filename gave {video_path}")

    # does this load lots of data into memory up front? I'm guessing not.
    video_clip = VideoFileClip(video_path)
    video_size = video_clip.size

    print(f"\n\n======= Processing video: {os.path.basename(video_path)}  got size = {video_size} =======\n")

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

            print(f"   IN MIN/MAX, befpre comp, clip rect {rect} and max_clip_rect is {max_clip_rect}")

            max_clip_rect['x'] = min(max_clip_rect['x'], rect['x'])  # x
            max_clip_rect['y'] = min(max_clip_rect['y'], rect['y'])  # y
            max_clip_rect['end_x'] = max(max_clip_rect['end_x'], rect['end_x'])  # end_x
            max_clip_rect['end_y'] = max(max_clip_rect['end_y'], rect['end_y'])  # end_y

            print(f"   IN MIN/MAX,     after comp, clip rect {rect} and max_clip_rect is {max_clip_rect}")


    for idx, segment in enumerate(video_data['segments']):
        # print(f"=-=-==-=   in segment bit, idx = {idx} segment = {segment}")

        # guess could cache the vids in memory? not sure what being automatically unloaded, anyhoo
        # video_path = get_video_filename(segment, video_data)
        video_path = make_abs_path_rel_to_working_dir(get_video_filename(segment, video_data))

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
