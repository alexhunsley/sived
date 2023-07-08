# ext_highlights.py

from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.video.io.VideoFileClip import VideoFileClip
# from moviepy.video.fx import crop
from moviepy.video.fx.all import crop
import toml


# Load the TOML file
with open("output_green.toml", 'r') as f:
    data = toml.load(f)

# Extract video details
video_data = data['video'][0]

for idx, segment in enumerate(video_data['segments']):

    # Convert start and end times to seconds
    h, m, s = map(int, segment['start_time'].split(':'))
    start_time = h*3600 + m*60 + s

    h, m, s = map(int, segment['end_time'].split(':'))
    end_time = h*3600 + m*60 + s

    # Load the video
    clip = VideoFileClip(video_data['title'])

    # Trim the video
    clip = clip.subclip(start_time, end_time)

    # Crop the video
    rect = segment['clip_rect']
    clip = clip.fx(crop, x1=rect['x'], y1=rect['y'], x2=rect['end_x'], y2=rect['end_y'])
    # clip = clip.fx(crop, x_start=rect['x'], y_start=rect['y'], 
    #                width=rect['end_x']-rect['x'], height=rect['end_y']-rect['y'])
    
    # Save the segment as a separate file
    clip.write_videofile(f"output_{idx}.mp4")





# # Load the TOML file
# with open("output_green.toml", 'r') as f:
# 	data = toml.load(f)

# # Extract video details
# video_data = data['video'][0]

# for idx, segment in enumerate(video_data['segments']):

# 	print(f" --------------- idx {idx} segment {segment}")

# 	# Convert start and end times to seconds
# 	h, m, s = map(int, segment['start_time'].split(':'))
# 	start_time = h*3600 + m*60 + s

# 	h, m, s = map(int, segment['end_time'].split(':'))
# 	end_time = h*3600 + m*60 + s

# 	print(f"video_data = {video_data}")

# 	# Load the video
# 	clip = VideoFileClip(video_data['title'])

# 	# Trim the video
# 	clip = clip.subclip(start_time, end_time)

# 	# Crop the video
# 	rect = segment['clip_rect']
# 	clip = clip.crop(x_start=rect['x'], y_start=rect['y'], 
# 					 width=rect['end_x']-rect['x'], height=rect['end_y']-rect['y'])
	
# 	# Save the segment as a separate file
# 	clip.write_videofile(f"output_{idx}.mp4")



# # Load the TOML file
# with open("output_green.toml", 'r') as f:
# 	data = toml.load(f)

# # Extract video details
# video_data = data.get('video')

# for idx, segment in enumerate(video_data.get('segments')):

# 	print(f"idx {idx} segment {segment}")

# 	# Convert start and end times to seconds
# 	h, m, s = map(int, segment['start_time'].split(':'))
# 	start_time = h*3600 + m*60 + s

# 	h, m, s = map(int, segment['end_time'].split(':'))
# 	end_time = h*3600 + m*60 + s

# 	# Load the video
# 	clip = VideoFileClip(video_data['title'])

# 	# Trim the video
# 	clip = clip.subclip(start_time, end_time)

# 	# Crop the video
# 	rect = segment['clip_rect']
# 	clip = clip.crop(x_start=rect['x'], y_start=rect['y'], 
# 					 x_end=rect['end_x'], y_end=rect['end_y'])
	
# 	# Save the segment as a separate file
# 	clip.write_videofile(f"output_{idx}.mp4")

