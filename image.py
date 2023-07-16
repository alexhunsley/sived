# image.py

from .spec import *
from .ext_highlights import make_concatenation_video
from moviepy.video.VideoClip import ImageClip
from moviepy.video.fx.all import crop, resize, rotate
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip


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

    print(f"  >>>> apply_watermark: {clip} {clip_rect} {clip_offset_in_context}")

    # global make_concatenation_video

    watermark_filename = get_watermark_filename(segment, video_data)

    if watermark_filename is None:
        print(f"  >>>> apply_watermark: early bail, no filename")
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

