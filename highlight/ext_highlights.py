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

from collections import namedtuple

from .rect import *
from .size import *

# TO FIX:
#
# centre and right/bottom align isn't working because we're using first image dimension, not all!
# fixes in other branch, ahead?
#
#
# NEXT:
#  Make a test video that shows the hexaclip grid. Write hexaclip parser and accept as a clip rects from toml if detected.
#  Use Size and Rect all over main code, before fixing any more zoomy stuff.
#
# Allow crop numbers to start '-' to mean from right or bottom. -0 means rhs or bottom (the visible pixel, not one off image edge).
#
# Make script output an ffmpeg concat file and then just run ffmpeg, instead of moviepy which is tediously slow.
#
# Allow text on top of clips (currenty we do a title card)
#
# Notes:
#  Will allow tag 'del' to mean that something can be deleted (intro/outro/something uninteresting). Other tags can appear, for info,
#  but existence of trim will have that effect.
#
#
# add max_pixel_scale and min_pixel_scale. They default to 'no limit'.
# 1 is 1-1 pixel size, 2 is blown up 2x, 0.5 is 4 pixels per rendered pixel, etc.
#
# Add output video size, which defaults to the union size of all the parts.

show_seg_number = False

use_threads = 8

# Sz = namedtuple('Sz', 'width height')
# sz = Sz(1, 2)
# print(sz)
# sys.exit(0)

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

# is desc not in the concat?

toml_base_filename = None

make_concatenation_video = True
# make_concatenation_video = False

# comment out to use input video framerate
# override_fps = 1


force_overwrite_existing = True

working_dir = os.getcwd()

limit_segs = None


from .helpers import *
from .image import *


# idea:
# allow nested alternating h/v style: like "h=a.png=(b.png=c.png=(d.png=e.png))", where each
# bracket flips the direction and recursively calls same func

# add text

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


def add_text(clip, text):
    txt_clip = TextClip(text, fontsize = 60, color = 'red') 
    txt_clip = txt_clip.set_pos('left').set_duration(clip.duration) 

    # Overlay the text clip on the first video clip 
    return CompositeVideoClip([clip, txt_clip])


previous_segment_start_time = None
previous_segment_end_time = None

# use_clip_rect is either the actual seg rect or the union'd rect (for a concat video).
# segment_clip_rect is always the segment's own clip rect as per toml. (Defaults to input video frame
# if not specified for a segment.)
# Returns a tuple of (clip, bool). The bool is for 'process more segments'; False means stop and is used for time_mode = 'continue'.
def process_segment(video_path, idx, desc, segment, video_data, max_size, segment_clip_rect):
    # filename without extension
    # video_base_filename = os.path.splitext(os.path.basename(video_path))[0]

    global previous_segment_start_time, previous_segment_end_time

    force_last_segment = False

    print(f"  passed segment clip rect: {segment_clip_rect}")

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
        return None, force_last_segment

    video_clip = VideoFileClip(video_path)

    if grab_frame := get_grab_frame(segment):
        print(f"found a grab_frame: {grab_frame}")
        # Convert the frame to an ImageClip
        
        numpy_img_frame = video_clip.get_frame(grab_frame['time'])

        clip = ImageClip(numpy_img_frame, duration=grab_frame['duration'])
        # doesn't work, interacts with the xy flip further down? video corrupts as still image plays.
        # clip = (ImageClip(frame, duration=grab_frame['duration'])
        #     .resize(lambda t : 1+0.02*t)
        # )

        # TODO get from somewhere authoritative later, e.g. the reference video clip (later)
        # use 1 if no zoom? otherwise 30
        clip.fps = 30

    elif text := get_text(segment):
        text, duration = text.split('|')
        duration = float(duration)

        #SparklyFontRegular-zyA3.ttf
        txt_clip = TextClip(text, fontsize=80, color='white', font='/Users/alexhunsley/Library/Fonts/SparklyFontRegular-zyA3.ttf', align='center', size=video_clip.size)

        # You can also specify the font, e.g.
        # txt_clip = TextClip("Your text here", fontsize=24, color='white', font='Arial', align='center', size=moviesize)

        # Optionally, to make it multi-line, you can include a new line character (\n)
        # txt_clip = TextClip("Line 1\nLine 2", fontsize=24, color='white', font='Arial', align='center', size=moviesize)

        segment_clip_rect_r = Rect.make_with_end_coords(0, 0, video_clip.size[0], video_clip.size[1])

        # To match the duration of the original video
        txt_clip = txt_clip.set_duration(duration)
        txt_clip.fps = 1

        clip = txt_clip

    else:
        clip = video_clip
        # clip = VideoFileClip(video_path)

        print(f"  -------- clip rotation: {clip.rotation}")

        time_mode = get_time_mode(video_data)
        if time_mode == 'continue' and previous_segment_start_time is not None and previous_segment_end_time is not None:
            start_time = previous_segment_end_time
            end_time = start_time + (previous_segment_end_time - previous_segment_start_time)

            print(f" continue mode, last seg: {previous_segment_start_time} {previous_segment_end_time} this seg: {start_time} {end_time}")

            # don't overrun end of video
            end_time = min(end_time, clip.duration)
            force_last_segment = (end_time == clip.duration)

            previous_segment_start_time = start_time
            previous_segment_end_time = end_time

        else:
            previous_segment_start_time = start_time = get_start_time(segment, video_data)
            previous_segment_end_time = end_time = get_end_time(segment, video_data, f"{clip.duration}")

        print(f" CMCM start_time, end_time = {start_time}, {end_time}")

        # Trim to time interval
        clip = clip.subclip(start_time, end_time)

        # this command shows -90 for a video, but clip.rotation comes back 0!
        # and in fact I need to invert x and y, NOT do rotate.
        #   ffprobe -v 0 -select_streams v:0 -show_entries stream_side_data=rotation -of default=nw=1:nk=1 video15.mov

        # clip rotation in file comes back 0 -- but we need something != 0, clearly!
        # clip = clip.fx(rotate, -90)

        # if clip.rotation == 90:
            # clip.rotation = 0

        # Crop the video if clip_rect is specified
        # order of crop and resize matters.
        #    TODO don't use this stuff if it's a NOP! (i.e. crop and resize)
        # clip = clip.fx(crop, x1=use_clip_rect['x'], y1=use_clip_rect['y'], x2=use_clip_rect['end_x'], y2=use_clip_rect['end_y'])


        # aspect fit so weird aspects for clips don't munt the output aspect ratio

        segment_clip_rect_r = segment_clip_rect
             #Rect.make_with_end_coords(segment_clip_rect['x'], segment_clip_rect['y'], segment_clip_rect['end_x'], segment_clip_rect['end_y'])

        max_pixel_scale = get_max_pixel_scale(video_data)

        # how much does this segment to max_size stretch pixels?
        # pixel_scale =

        # use_clip_rect_r = Rect.make_with_end_coords(use_clip_rect['x'], use_clip_rect['y'], use_clip_rect['end_x'], use_clip_rect['end_y'])

        # aspect_fitted_segment_clip_size = segment_clip_rect_r.size

        print(f"CHECK IT: max_size {max_size}, clip size: {clip.size} clip asp: {clip.size[0] / clip.size[1]}")

        aspect_filled_segment_clip_size = max_size.aspect_filled_to(segment_clip_rect_r.size, z_max=max_pixel_scale)

        x_scale = float(get_x_scale(segment, video_data))
        y_scale = float(get_y_scale(segment, video_data))

        print(f" scale x, y: {x_scale} {y_scale}")

        if x_scale != 1 or y_scale != 1:

            aspect_filled_segment_clip_size = aspect_filled_segment_clip_size.scaled_ind(x_scale, y_scale)



        # aspect_fitted_segment_clip_size = max_size.aspect_fitted_to(segment_clip_rect_r.size)

        # aspect_fitted_segment_clip_size = segment_clip_rect_r.size.aspect_fitted_to(max_size)
        # aspect_filled_segment_clip_size = segment_clip_rect_r.size.aspect_filled_to(max_size)

        # aspect_filled_segment_clip_size = segment_clip_rect_r.size.aspect_filled_to(max_size)

        print(f" before, after fill: {segment_clip_rect_r.size} {aspect_filled_segment_clip_size}  (and max_size = {max_size}")
        # print(f" before, after fit: {segment_clip_rect_r.size} {aspect_fitted_segment_clip_size}  (and max_size = {max_size}")

        # fl = use_clip_rect_r.size.aspect_fitted_to(segment_clip_rect_r.size)

        # use_clip_rect = {'x': 0, 'y': 0, 'end_x': max_size.width, 'end_y': max_size.height}
        # use_clip_rect_r = Rect.make_with_size(0, 0, max_size)

        r = Rect.make_with_centre_and_size(segment_clip_rect_r.centre_x, segment_clip_rect_r.centre_y, aspect_filled_segment_clip_size)
        # r = Rect.make_with_centre_and_size(segment_clip_rect_r.centre_x, segment_clip_rect_r.centre_y, aspect_fitted_segment_clip_size)
        video_size_rect = Rect.make_with_size(0, 0, Size.make(clip.size[0], clip.size[1]))
        # THIS needs to be the size of the input video!
        r = r.moved_minimally_to_lie_inside(video_size_rect)

        # use this instead of avoid aspect fit:
        # r = segment_clip_rect_r

        # here -- we can see the -24x coord for "0001" hexaclip thing.
        # so move back into source size.
        # print(f" filled: {use_clip_rect_r} fitted to {segment_clip_rect_r} gives asp {aspect_filled_segment_clip_rect}, so final r = {r}")

        # clip = clip.fx(crop, x1=segment_clip_rect['x'], y1=segment_clip_rect['y'], x2=segment_clip_rect['end_x'], y2=segment_clip_rect['end_y'])

        # crop the input video at original input video coordinates
        clip = clip.fx(crop, x1=r.x, y1=r.y, x2=r.end_x, y2=r.end_y)

        # if use_clip_rect != segment_clip_rect:
        #     print(f" different use_clip_rect and segment_clip_rect, so resizing. : {use_clip_rect} {segment_clip_rect}")
        #
        #     ww = use_clip_rect['end_x'] - use_clip_rect['x']
        #     hh = use_clip_rect['end_y'] - use_clip_rect['y']
        #     print(f" got ww, hh = {ww}, {hh}")
        #     # sys.exit(0)
        #     clip = clip.resize((ww, hh))

    if get_temp_transpose_xy_size(segment, video_data):
        clip = clip.resize(clip.size[::-1])

    #  {'x': 128, 'y': 128, 'end_x': 896, 'end_y': 640}
    # sys.exit(0)

    # segment_clip_rect has the x, y we need for clip_offset_in_context
    # TODO need to use stuff from above!
    clip = apply_watermark(clip, segment_clip_rect, segment_clip_rect, segment, video_data)
    # clip = apply_watermark(clip, use_clip_rect, segment_clip_rect, segment, video_data)

    # clip = apply_watermark(clip, use_clip_rect, segment_clip_rect, segment, video_data)

    # if use_clip_rect != segment_clip_rect:
    if max_size != segment_clip_rect_r.size:
        print(f" different use_clip_rect and segment_clip_rect, so resizing. : {max_size} {segment_clip_rect_r.size}")
        clip = clip.resize((max_size.width, max_size.height))

    if show_seg_number:
        seg_text = f"seg {idx}"
        clip = add_text(clip, seg_text)

    # if fps := override_fps:
    if 'override_fps' in globals():
        clip.fps = override_fps

    clip.write_videofile(output_filename, threads=use_threads)

    return clip, force_last_segment


def process_video_toml(toml_file):
    global toml_base_filename
    toml_base_filename = toml_file

    with open(toml_file, 'r') as f:
        data = toml.load(f)

    video_data = data['video'][0]

    if limit_segs:
        video_data['segments'] = video_data['segments'][:limit_segs]

    # use first segment for title and hence finding res of video (assumption)
    first_segment = video_data['segments'][0]

    # wrong! want rel to curr dir.
    video_path = make_abs_path_rel_to_working_dir(get_video_filename(first_segment, video_data, toml_file))

    print(f"working dir: {os.getcwd()}")

    print(f"get_video_filename gave {video_path}")

    # does this load lots of data into memory up front? I'm guessing not.
    video_clip = VideoFileClip(video_path)
    video_size = Size.make(video_clip.size[0], video_clip.size[1])


    video_size_rect = Rect.make_with_size(0, 0, video_size)

    print(f"\n\n======= Processing video: {os.path.basename(video_path)}  got size = {video_size} =======\n")

    # Variables for concatenation
    concat_clips = []

    # Initialized as video size
    # max_clip_rect = {'x': video_size[0], 'y': video_size[1], 'end_x': 0, 'end_y': 0} if make_concatenation_video else {}

    # value which anything can be trumped when unioning. Note origin and size other way round! deliberate.
    # max_clip_rect = {'x': video_size[0], 'y': video_size[1], 'end_x': 0, 'end_y': 0} if make_concatenation_video else  {'x': 0, 'y': 0, 'end_x': video_size[0], 'end_y': video_size[1]}

    max_clip_rect = Rect.make_with_size(video_size_rect.size.width, video_size_rect.size.height, Size.zero)

    # print(f"=-=-==-=   max_clip_rect = {max_clip_rect}")

    global make_concatenation_video

    max_segment_size = Size.zero

    # if make_concatenation_video:

    # print(f"=-=-==-=   in make_concatenation_video bit")

    # why using video_size here? means if 'output_video_size' not set in video,
    # we keep the full video size, we dont want that?!
    # output_video_size = get_output_video_size(video_data, video_size)
    output_video_size = get_output_video_size(video_data, None)

    # if not output_video_size:
    #     output_video_size = video_size

    # we now do this bit even when not making concat videos,
    # which means that even without concat videos each clip will
    # scaled up to the output video size. May want a diff flag
    # to stop that behaviour for non-concat generation (i.e. so
    # can end up with segment vids of different sizes according to their
    # exact specified clip).
    if output_video_size is not None:
        max_segment_size = output_video_size
            #Size.make(output_video_size[0], output_video_size[1])
    else:
        for idx, segment in enumerate(video_data['segments']):
            print(f"   union seg rects: seg {idx}")
            rect_r = get_clip_rect(segment, video_data, video_size_rect)

            if not rect_r:
                # any segment without a clip rect means we use full output size for it,
                # hence use full output size for entire video
                print(f" if not rect - in here")
                max_segment_size = Size.make(output_video_size[0], output_video_size[1])
                break

            # rect_r = Rect.make_with_end_coords(rect[0], rect[1], rect[2], rect[3])
            print(f" made rect_r: {rect_r}")

            print(f"   IN MIN/MAX, before comp, clip rect {rect_r} and max_clip_rect is {max_clip_rect}; max_segment_size = {max_segment_size}")

            # max_clip_rect['x'] = min(max_clip_rect['x'], rect['x'])  # x
            # max_clip_rect['y'] = min(max_clip_rect['y'], rect['y'])  # y
            # max_clip_rect['end_x'] = max(max_clip_rect['end_x'], rect['end_x'])  # end_x
            # max_clip_rect['end_y'] = max(max_clip_rect['end_y'], rect['end_y'])  # end_y

            # clip_size = Size.make(max_clip_rect['end_x'] - max_clip_rect['x'],
            #                       max_clip_rect['end_y'] - max_clip_rect['y'])

            # clip_size = Size.make(rect['end_x'] - rect['x'], rect['end_y'] - rect['y'])

            max_segment_size = max_segment_size.unioned_with(rect_r.size)

            print(f"New max_segment_size after mixing with {rect_r.size} = {max_segment_size}")

            print(f"   IN MIN/MAX,     after comp, clip rect {rect_r} and max_segment_size is {max_segment_size}")

    # we want to calc max clip rect etc before here (so zoom etc work),
    # but now disable flag if only one segment, to avoid a pointless concat file being produced
    make_concatenation_video = make_concatenation_video and len(video_data['segments']) > 1

    time_mode = get_time_mode(video_data)

    force_last_segment = False

    # master segment output numner -- increases over all mode segments in continue mode
    base_idx = 0

    while True:
        for seg_idx, segment in enumerate(video_data['segments']):

            idx = base_idx + seg_idx

            print(f"=-=-==-=   in segment bit, idx = {idx} segment = {segment}")

            # guess could cache the vids in memory? not sure what being automatically unloaded, anyhoo
            # video_path = get_video_filename(segment, video_data)
            video_path = make_abs_path_rel_to_working_dir(get_video_filename(segment, video_data, toml_file))

            # must give the actual video res here, for hexaclip interpreting
            segment_clip_rect = get_clip_rect(segment, video_data, video_size_rect)

            if not segment_clip_rect:
                # segment_clip_rect = {'x': 0, 'y': 0, 'end_x': video_size[0], 'end_y': video_size[1]}
                segment_clip_rect = Rect.make_with_size(0, 0, Size.make(max_segment_size.width, max_segment_size.height))

            # use_clip_rect = max_clip_rect if make_concatenation_video else segment_clip_rect

            # use_clip_rect = segment_clip_rect

            # print(f"=-=-==-=      ... use_clip_rect for {idx} = {use_clip_rect}")

            desc = get_desc(segment, video_data)
            # output_clip = process_segment(video_path, idx, desc, segment, video_data, use_clip_rect, segment_clip_rect)
            # what we really need here is the aspect of max size, but pass the max_size for now and deal with inside func
            (output_clip, force_last_segment) = process_segment(video_path, idx, desc, segment, video_data, max_segment_size, segment_clip_rect)

            if make_concatenation_video:
                # Determine fade duration from the TOML data
                # (Default to -1 second i.e. disabled if not specified)
                fade_duration = get_fade_duration(segment, video_data)
                fade_mode = get_fade_mode(segment, video_data)
                print(f"  =--=-==-=-= fade_mode = {fade_mode} fade_duration = {fade_duration} ")

                if fade_duration > 0 and fade_mode:
                    print(f" ... so applying crossfade in and out")

                    # Apply fade in/out/both to clip
                    if fade_mode == "both" or fade_mode == "in":
                        output_clip = output_clip.fx(fadein, fade_duration)

                    if fade_mode == "both" or fade_mode == "out":
                        output_clip = output_clip.fx(fadeout, fade_duration)

                    # output_clip = output_clip.crossfadein(fade_duration).crossfadeout(fade_duration)

                segment_loop_count = get_segment_loop_count(segment, video_data)

                for i in range(0, segment_loop_count):
                    concat_clips.append(output_clip)

            if force_last_segment:
                # we've reach end of input video (for time_mode = 'continue')
                break


        # if make_concatenation_video:
        #     final_clip = concatenate_videoclips(concat_clips)
        #     final_output_filename = f"{os.path.splitext(video_path)[0]}__concat.mp4"
        #     final_clip.write_videofile(final_output_filename, threads=use_threads)

        print(f" CMCM break out from while True? time_mode = {time_mode}, force_last_segment = {force_last_segment}")
        # repeat all segments processing?
        if time_mode != 'continue' or force_last_segment:
            break

        base_idx += len(video_data['segments'])

    if make_concatenation_video:
        final_clip = concatenate_videoclips(concat_clips)
        final_output_filename = f"{os.path.splitext(video_path)[0]}__concat.mp4"
        final_clip.write_videofile(final_output_filename, threads=use_threads)


# w0, h0, a1, 'v'
# print(combined_aspects(100, 100, 2, 'h'))
# print(combined_aspects(100, 100, 2, 'v'))

# herus testing
# print(combined_aspects(1, 2, 'h'))
# print(combined_aspects(1, 2, 'v'))

# images = [Sz(10, 10), Sz(10, 10)]
# print("h:", get_canvas_size(images, 50, 'h'), "\n")

# print("H:", get_canvas_size(images, 50, 'H'), "\n")

# print("v:", get_canvas_size(images, 50, 'v'), "\n")

# print("V:", get_canvas_size(images, 50, 'V'), "\n")
# 
# sys.exit(0)


if __name__ == "__main__":
    # Check if the script was called with an argument
    if len(sys.argv) != 2:
        sys.exit("Error: This script requires one argument: the name of the TOML file to process, or 'all'.")

    # If the argument is 'all', process all .toml files in the current directory
    if sys.argv[1] == 'all':
        toml_files = glob.glob("*.toml")
        for toml_file in toml_files:
            print(f" doing toml_file_global file: {toml_file_global}")
            process_video_toml(toml_file)
    # Otherwise, process the specified TOML file
    else:
        process_video_toml(sys.argv[1])
