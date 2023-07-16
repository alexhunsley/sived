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


# from PIL import Image


def load_single_image(image_file, max_dimension):
    print(f"load_single_image: max_dimension = {max_dimension}")

    image = Image.open(image_file)
    aspect_ratio = image.width / image.height
    if aspect_ratio > 1:  # width > height
        new_size = (max_dimension, int(max_dimension / aspect_ratio))
    else:
        new_size = (int(max_dimension * aspect_ratio), max_dimension)
    return image.resize(new_size, Image.ANTIALIAS)


def load_and_resize_images(image_files, max_dimension, layout):
    images = []
    for img in image_files:
        image = Image.open(img)
        aspect_ratio = image.width / image.height
        if layout == 'h':
            new_size = (int(max_dimension * aspect_ratio), max_dimension)
        else:
            new_size = (max_dimension, int(max_dimension / aspect_ratio))
        images.append(image.resize(new_size, Image.ANTIALIAS))
    return images


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
        if layout == 'h':
            canvas.paste(image, (offset, 0))
            offset += image.width
        else:  # 'v'
            canvas.paste(image, (0, offset))
            offset += image.height
    return canvas


# def load_image(image_path, rgb_mult = None):
def load_stacked_image_as_clip(image_spec, watermark_max_dimension, rgb_mult = None):
    print(f"start new version of load_stacked_image_as_clip")

    image_files = image_spec.split('=')

    layout = image_files[0] if len(image_files) > 1 else None

    print(f"load_stacked_image_as_clip: watermark_max_dimension = {watermark_max_dimension} spec = {image_spec} image_files = {image_files} layout = {layout}")

    if layout not in ('h', 'v', None):
        raise ValueError(f'Invalid layout: {layout}')

    if layout is None:  # Single image
        image = load_single_image(image_files[0], watermark_max_dimension)
        print(f" >> single image, got im: {image}")
    else:
        # Multiple images
        images = load_and_resize_images(image_files[1:], watermark_max_dimension, layout)

        # Get canvas size
        max_width, max_height = get_canvas_size(images, watermark_max_dimension, layout)

        # Create new canvas
        canvas = Image.new('RGB', (max_width, max_height))

        # Paste images into canvas
        image = paste_images_on_canvas(images, canvas, layout)
        print(f" >> multiple image, got im: {image}")


    # must go via np array!
    np_image = np.array(image)

    # Create an ImageClip with MoviePy
    image_clip = ImageClip(np_image)

    # print(f"made image_clip: {image_clip} from canvas (image): {canvas} with images: {images}")

    return image_clip


# ---------------------------------------------------------------------------------------------------------------------



# def load_image(image_path, rgb_mult = None):
#     if rgb_mult == None:
#         return ImageClip(image_path)

#     (r_mul, g_mul, b_mul) = rgb_mult

#     # Load the image
#     image = Image.open(image_path)

#     # Separate the image into individual color bands (channels)
#     r, g, b, a = image.split()

#     # Enhance the channels
#     r = r.point(lambda i: i * r_mul)
#     g = g.point(lambda i: i * g_mul)
#     b = b.point(lambda i: i * b_mul)

#     # Merge the channels back
#     merged_image = Image.merge('RGB', (r, g, b))

#     # PIL image to numpy array
#     np_image = np.array(merged_image)

#     # Create an ImageClip with MoviePy
#     image_clip = ImageClip(np_image)

#     return image_clip


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

