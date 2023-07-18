# image.py

from .spec import *
from .ext_highlights import make_concatenation_video

from PIL import Image

from moviepy.editor import *
from moviepy.video.VideoClip import ImageClip
from moviepy.video.fx.all import crop, resize, rotate
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

import numpy as np

from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.fx.all import fadein, fadeout
# from moviepy.video.VideoClip import ColorClip


# ---------------------------------------------------------------------------------------------------------------------
#
# IMAGE STACKING from gpt

from .helpers import dbg
from typing import List, Tuple, Union
import re


# border = 5
border = None

def split_spec(spec: str) -> List[str]:
    dbg(f"split_spec: spec= {spec}")
    """Split an image spec into elements, which are either image filenames or sub-specs."""
    elements = []
    buffer = ""
    paren_depth = 0

    for char in spec:
        if char == "(":
            print(f"Found '(', buffer.strip() = {buffer.strip()}")
            if paren_depth == 0:
                if buffer.strip(): # If it is the start of sub-spec, append the buffer into elements.
                    print(f"    ... paren_depth = 0 and have buffer contents, so appending |{buffer.strip()}|")
                    elements.append(buffer.strip())
                    buffer = ""
            else:
                print(f"    ... paren_depth != 0 OR have no buffer contents, so appending (. paren_depth = {paren_depth}")
                buffer += "("
            paren_depth += 1
        elif char == ")":
            paren_depth -= 1
            print(f" ... found a ) and paren_depth now = {paren_depth}")
            if paren_depth == 0: # If it is the end of sub-spec, append the buffer into elements.
                # elements.append(f"({buffer.strip()})")
                elements.append(f"{buffer.strip()}")
                # elements.append(f"{buffer.strip()})")
                buffer = ""
            else:
                buffer += ")"
        elif char == "=" and paren_depth == 0: # split on "=" outside parentheses.
            if buffer.strip(): # append buffer into elements.
                elements.append(buffer.strip())
                buffer = ""
        else:
            buffer += char

    if buffer.strip(): # Append the leftover buffer into elements.
        elements.append(buffer.strip())

    dbg(f"split_spec: returning elements = {elements}")
    return elements


# spec_result = split_spec("h=1=(2=3=((4)=5))")
# print(f"split spec test: {spec_result}")
# sys.exit(0)


def process_spec(spec: str, max_dimension: int, layout: str, is_top_level_spec = False) -> Image:
    dbg(f"  ?????????????   PROCESS_SPEC called, max_dimension = {max_dimension} layout = {layout}")

    """Process an image spec, returning an image.
    The spec can contain sub-specs in parentheses, which will be processed recursively.
    """

    layout_with_case = layout
    layout = layout.lower()

    elements = split_spec(spec)

    images = []
    for el in elements:
        # sub-specs can be like 'a=b' or '(a)' or 'a=(b=c)'
        if "(" in el or "=" in el:
            sub_layout = 'v' if layout.lower() == 'h' else 'h'  # Flip layout for sub-spec
            dbg(f"   --- calling process_spec on a sublayout = {el}, before that images = {images}")

            # for H and V modes, we need to to get all sub spec images before resizing any,
            # since we need to split the desired H or V between all the images!
            #
            # so first just make existing stuff work by fetching all first.
            sub_spec_image = process_spec(el, max_dimension, sub_layout)

            # sub_spec_image = resized_image(sub_spec_image, max_dimension, layout_with_case)

            image_to_add = sub_spec_image
            dbg(f"   ---    .... now images = {images}")

        else:  # This is an image file

            image = load_single_image(el, max_dimension)
            image = resized_image(image, max_dimension, layout_with_case)

            image_to_add = image

        images.append(image_to_add)

    # do resizing of each image last (so H and V can work)
    resized_images = []

    for image in images:
        resized_im = resized_image(image, max_dimension, layout_with_case)
        resized_images.append(resized_im)

    # Get canvas size
    max_width, max_height = get_canvas_size(resized_images, max_dimension, layout)

    dbg(f"  -=-= max_w and h: {max_width} {max_height}")

    # this shows the missing image with height * 2. The sub-images aren't being resized...
    canvas = Image.new('RGB', (max_width, max_height))

    paste_images_on_canvas(resized_images, canvas, layout)

    if is_top_level_spec:
        canvas = add_border(canvas, border)

    return canvas


def load_stacked_image_as_clip(image_spec: str, watermark_max_dimension: int, rgb_mult: float = None) -> ImageClip:
    print(f"start new version of load_stacked_image_as_clip")

    image_spec = image_spec.split('=')

    layout = image_spec[0] if len(image_spec) > 1 else None

    print(f"load_stacked_image_as_clip: watermark_max_dimension = {watermark_max_dimension} spec = {image_spec} layout = {layout}")

    if layout.lower() not in ('h', 'v', None):
        raise ValueError(f'Invalid layout: {layout}')

    image = process_spec('='.join(image_spec[1:]), watermark_max_dimension, layout, True)

    np_image = np.array(image)

    image_clip = ImageClip(np_image)

    return image_clip


# ==========================================


def add_border(image, border):
    if not border: 
        return image

    borderImage = Image.new(image.mode, (image.width + border*2, image.height + border * 2), '#080')
    borderImage.paste(image, (border, border))

    return borderImage


def load_single_image(image_file, max_dimension, border = None):
    print(f"load_single_image: max_dimension = {max_dimension}")

    image = Image.open(image_file)
    aspect_ratio = image.width / image.height
    if aspect_ratio > 1:  # width > height
        new_size = (max_dimension, int(max_dimension / aspect_ratio))
    else:
        new_size = (int(max_dimension * aspect_ratio), max_dimension)
    
    image = image.resize(new_size, Image.ANTIALIAS)

    return image
    

def resized_image(image, max_dimension, layout):
    print(f"resized_image: max_dim = {max_dimension} layout = {layout}")
    aspect_ratio = image.width / image.height
    if layout == 'h':
        new_size = (int(max_dimension * aspect_ratio), max_dimension)
    elif layout == 'v':
        new_size = (max_dimension, int(max_dimension / aspect_ratio))
    elif layout == 'H':
        new_size = (max_dimension, int(max_dimension * aspect_ratio))
    else: # 'V'
        new_size = (int(max_dimension / aspect_ratio), max_dimension)

    image = image.resize(new_size, Image.ANTIALIAS)
    return image


def get_canvas_size(images, max_dimension, layout):
    if layout == 'h':
        max_width = sum(image.width for image in images)
        max_height = max_dimension
    else:
        max_width = max_dimension
        max_height = sum(image.height for image in images)
    return max_width, max_height


def paste_images_on_canvas(images, canvas, layout):
    offset = 0
    for image in images:
        if layout.lower() == 'h':
            canvas.paste(image, (offset, 0))
            offset += image.width
        else:  # 'v'
            canvas.paste(image, (0, offset))
            offset += image.height
    return canvas


#======================================


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

    watermark_pos = (x + segment_offset_inside_context['x'], y + segment_offset_inside_context['y'])
    print(f"  >>>> get_watermark_position: to xy of {x} {y} am adding segment_offset_inside_context = {segment_offset_inside_context}, final: watermark_pos")
    return watermark_pos


# print(time_to_seconds("02"))
# print(time_to_seconds("2.0"))
# print(time_to_seconds("00:30:02.1"))
# print(time_to_seconds("01:00:02+15"))
# print(time_to_seconds("00:00:02+15/30"))
# print(time_to_seconds("00:00:02+45/60"))
# print(time_to_seconds("00:00:02.1+45/60"))
# sys.exit(1)


# applies a watermark if necessary, returning the resulting clip (or the original clip otherwise)
def apply_watermark(clip, clip_rect, clip_offset_in_context, segment, video_data):

    print(f"  >>>> apply_watermark: clip: {clip} clip_rect: {clip_rect} clip_offset_in_context: {clip_offset_in_context}")

    # global make_concatenation_video

    watermark_filename = get_watermark_filename(segment, video_data)

    if watermark_filename is None:
        print(f"  >>>> apply_watermark: early bail, no filename")
        return clip

    watermark_height = get_watermark_height(segment, video_data)

    rgb_mult = get_rgb_mult(segment, video_data)
    # Load the image and resize it
    img = load_stacked_image_as_clip(watermark_filename, watermark_height, rgb_mult)

    # Decide watermark height
    # watermark_height = get_watermark_height(segment, video_data)
    # img = img.fx(resize, height=watermark_height)

    print(f"clip.duration = {clip.duration}")
    print(f"img = {img}")

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

