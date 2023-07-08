import glob
import sys
import os
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.fx.all import crop
import toml

def process_segment(video_path, idx, segment):
	# Convert start and end times to seconds
	h, m, s = map(int, segment['start_time'].split(':'))
	start_time = h*3600 + m*60 + s

	h, m, s = map(int, segment['end_time'].split(':'))
	end_time = h*3600 + m*60 + s

	# Load the video
	clip = VideoFileClip(video_path)

	# Trim the video
	clip = clip.subclip(start_time, end_time)

	# Crop the video
	rect = segment['clip_rect']
	clip = clip.fx(crop, x1=rect['x'], y1=rect['y'], x2=rect['end_x'], y2=rect['end_y'])

	# Prepare the output filename
	base_name = os.path.splitext(video_path)[0]  # get filename without extension
	output_filename = f"{base_name}__seg{idx:04d}.mp4"

	# Save the segment as a separate file
	# clip.write_videofile(output_filename)
	clip.write_videofile(output_filename, codec='libx264') #, bitrate='100k') #, audio_codec='aac', audio_bitrate='160k')

def process_video_toml(toml_file):
	# Load the TOML file
	with open(toml_file, 'r') as f:
		data = toml.load(f)

	# Extract video details
	video_data = data['video'][0]

	print(f"\n\n======= Processing video: {os.path.basename(video_data['title'])} =======\n")

	for idx, segment in enumerate(video_data['segments']):
		process_segment(video_data['title'], idx, segment)

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
