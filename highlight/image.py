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
from .time import *
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


# get width and height of list of images, arranged in specified way
def image_collection_total_size(images, max_dimension, layout):
    other_dimension = 0.0

    for image in images:
        if layout.lower() == 'h':
            other_dimension += image.width
        else: # 'w'
            other_dimension += image.height


    if layout.lower() == 'h':
        return (other_dimension, max_dimension, other_dimension)

    return (max_dimension, other_dimension, other_dimension)


def process_spec(spec: str, max_dimension: int, layout: str, is_top_level_spec = False, images_dir=None) -> Image:
    dbg(f"  ?????????????   PROCESS_SPEC called, max_dimension = {max_dimension} layout = {layout}, images_dir: {images_dir}")

    """Process an image spec, returning an image.
    The spec can contain sub-specs in parentheses, which will be processed recursively.
    """

    layout_with_case = layout
    layout = layout.lower()

    elements = split_spec(spec)

    total_image_dimensions_in_layout_dir = 0

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
            sub_spec_image = process_spec(el, max_dimension, sub_layout, False, images_dir)

            # sub_spec_image = resized_image(sub_spec_image, max_dimension, layout_with_case)

            image_to_add = sub_spec_image
            dbg(f"   ---    .... now images = {images}")

        else:  # This is an image file

            # for H or V, add sizes to get final wh size then compute other dim before calling resize below

            image = load_single_image(el, max_dimension, images_dir, None, False)
            print(f" ()()(()()()() loaded image: w, h {image.width} {image.height})")
            # image = resized_image(image, max_dimension, layout_with_case)

            image_to_add = image

        images.append(image_to_add)

        total_image_dimensions_in_layout_dir += image_to_add.width if layout == 'h' else image_to_add.height

    max_width, max_height, dimension_along_layout, dim_orth_to_layout = get_canvas_size(images, max_dimension, layout_with_case)

    # this looks right.
    # outputs "max_w max_h = 100, 33, d_a_layout = 100"
    print(f" ********** 1  max_w max_h = {max_width}, {max_height}, d_a_layout = {dimension_along_layout}")
    print(f" ********** 1b total_image_dimensions_in_layout_dir = {total_image_dimensions_in_layout_dir}")
    # think this ropey
    (ww, hh) = resized_size(max_width, max_height, max_dimension, layout_with_case)

    print(f" ********** 2  ww, hh = {ww}, {hh}, layout = {layout}, max_dimension = {max_dimension}")

    max_dimension = dim_orth_to_layout
    # if layout == 'h':
    #     max_dimension = hh
    # else:
    #     max_dimension = ww


    # (all_images_w, all_images_h, dimension_along_layout) = image_collection_total_size(images, max_dimension, layout)

    # do resizing of each image last (so H and V can work)
    resized_images = []

    for image in images:
        resized_im = resized_image(image, max_dimension, layout_with_case)
        resized_images.append(resized_im)

    # Get canvas size
    # max_width, max_height = get_canvas_size(resized_images, max_dimension, layout)

    dbg(f"  -=-= max_w and h: {max_width} {max_height}")

    # this shows the missing image with height * 2. The sub-images aren't being resized...
    canvas = Image.new('RGB', (max_width, max_height))

    paste_images_on_canvas(resized_images, canvas, layout)

    if is_top_level_spec:
        canvas = add_border(canvas, border)

    return canvas


def load_stacked_image_as_clip(image_spec: str, watermark_max_dimension: int, rgb_mult: float = None, images_home=None) -> ImageClip:
    print(f"start new version of load_stacked_image_as_clip")

    image_spec = image_spec.split('=')

    # default to h layout if only one image
    layout = image_spec[0] if len(image_spec[0]) == 1 else 'h'

    print(f"load_stacked_image_as_clip: watermark_max_dimension = {watermark_max_dimension} spec = {image_spec} layout = {layout}")

    if layout.lower() not in ('h', 'v'):
        raise ValueError(f'Invalid layout: {layout}')

    image = process_spec('='.join(image_spec[1:]), watermark_max_dimension, layout, True, images_home)

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


def load_single_image(image_file, max_dimension, images_home=None, border=None, resize=True):
    print(f"load_single_image: max_dimension = {max_dimension}")

    if not os.path.isabs(image_file) and images_home:
        image_file = os.path.join(images_home, image_file)

    image = Image.open(image_file)

    if resize:
        aspect_ratio = image.width / image.height
        if aspect_ratio > 1:  # width > height
            new_size = (max_dimension, int(max_dimension / aspect_ratio))
        else:
            new_size = (int(max_dimension * aspect_ratio), max_dimension)
        
        image = image.resize(new_size, Image.Resampling.LANCZOS)

    return image
    

def resized_size(w, h, max_dimension, layout):

    aspect_ratio = w / h

    print(f"resized_size: w {w} h {h} asp {aspect_ratio} max_dim = {max_dimension} layout = {layout}")

    if layout == 'h':
        new_size = (int(max_dimension * aspect_ratio), max_dimension)
    elif layout == 'v':
        # this looks wrong?
        # new_size = (max_dimension, int(max_dimension / aspect_ratio))
        new_size = (max_dimension, int(max_dimension / aspect_ratio))
    elif layout == 'H':
        new_size = (int(max_dimension * aspect_ratio), max_dimension)
        # new_size = (max_dimension, int(max_dimension * aspect_ratio))
    else: # 'V'
        new_size = (max_dimension, int(max_dimension / aspect_ratio))

    print(f"resized_size:     ... and made new_size = {new_size}")
    return new_size


def resized_image(image, max_dimension, layout):
    print(f"resized_image: max_dim = {max_dimension} layout = {layout}")

    new_size = resized_size(image.width, image.height, max_dimension, layout)
    image = image.resize(new_size, Image.Resampling.LANCZOS)
    return image


# Returns combination of two aspect ratios in the H or V direction
def combined_aspects(a0, a1, layout):
    if layout.lower() == 'h':
        print("combine h eqn")
        return a0 + a1
    else:
        print("combine v eqn")
        return a0 / (1.0 + a0/a1)


# returns w, h, and dimension along layout direction (w or h depending)
def get_canvas_size(images, max_dimension, layout):
    combined_aspect = images[0].width / images[0].height

    for im in images[1:]:
        asp = im.width / im.height
        combined_aspect = combined_aspects(combined_aspect, asp, layout)

    if layout == 'h' or layout == 'V':
        ret_w = int(max_dimension * combined_aspect)
        ret_h = max_dimension
        (d_a_l, d_o_t_l) = (ret_w, ret_h) if layout == 'h' else (ret_h, ret_w)
    else:  # 'H' or 'v'
        ret_w = max_dimension
        ret_h = int(max_dimension / combined_aspect)
        (d_a_l, d_o_t_l) = (ret_h, ret_w) if layout == 'v' else (ret_w, ret_h)

    return ret_w, ret_h, d_a_l, d_o_t_l


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


def calc_watermark_position(use_clip_rect, segment_clip_rect, watermark_size, watermark_position):

    # think it's just the same!
    # segment_offset_inside_context = segment_clip_rect

    print(f"get_watermark_position: use_clip_rect = {use_clip_rect}, segment_clip_rect = {segment_clip_rect}, watermark_size = {watermark_size}, watermark_position = {watermark_position}")

    wp_dict = dict(enumerate(watermark_position))

    # Get the video width and height
    # _, _, video_width, video_height = video_clip_rect

    video_width = segment_clip_rect.size.width
    video_height = segment_clip_rect.size.height

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

    segment_offset_x = segment_clip_rect.x - use_clip_rect.x
    segment_offset_y = segment_clip_rect.y - use_clip_rect.y

    watermark_pos = (x + segment_offset_x, y + segment_offset_y)
    print(f"  >>>> get_watermark_position: to xy of {x} {y} am adding segment_offset_x, y = {segment_offset_x}, {segment_offset_y}, final: watermark_pos")
    return watermark_pos


# print(time_to_seconds("02"))
# print(time_to_seconds("2.0"))
# print(time_to_seconds("00:30:02.1"))
# print(time_to_seconds("01:00:02+15"))
# print(time_to_seconds("00:00:02+15/30"))
# print(time_to_seconds("00:00:02+45/60"))
# print(time_to_seconds("00:00:02.1+45/60"))
# sys.exit(1)


# applies a watermark if necessary, returning the resulting clip (or the original clip otherwise).
# use_clip_rect is either segment_clip_rect or the union rect of all clip rects (concat mode).
def apply_watermark(clip, use_clip_rect, segment_clip_rect, segment, video_data):

    print(f"  >>>> apply_watermark: clip: {clip} clip_rect: {use_clip_rect} clip_offset_in_context: {segment_clip_rect}")

    # global make_concatenation_video

    watermark_filename = get_watermark_filename(segment, video_data)
    images_home = get_watermark_home(segment, video_data)

    if watermark_filename is None:
        print(f"  >>>> apply_watermark: early bail, no filename")
        return clip

    watermark_dimension = get_watermark_dimension(segment, video_data)

    rgb_mult = get_rgb_mult(segment, video_data)
    # Load the image and resize it
    img = load_stacked_image_as_clip(watermark_filename, watermark_dimension, rgb_mult, images_home)

    # Decide watermark height
    # watermark_height = get_watermark_height(segment, video_data)
    # img = img.fx(resize, height=watermark_height)

    print(f"clip.duration = {clip.duration}")
    print(f"img = {img}")

    # Set the image clip's duration to match the video clip's
    img = img.set_duration(clip.duration)

    # toml 'watermark_position'
    watermark_position = get_watermark_position(segment, video_data)

    print(f"apply_watermark   clip_rect = {use_clip_rect}")
    print(f"apply_watermark   clip_offset_in_context = {segment_clip_rect}")

    watermark_position = calc_watermark_position(use_clip_rect, segment_clip_rect, img.size, watermark_position)

    # a composite video clip with the watermark image overlay
    return CompositeVideoClip([clip, img.set_position(watermark_position)])

