import csv

import csv


def generate_toml_from_csv(csv_file_path, output_path):
    with open(csv_file_path, 'r') as csv_file:
        reader = csv.reader(csv_file)
        csv_data = list(reader)

        # parsing csv data
        title = csv_data[0][0]
        clip_rect = csv_data[0][1] if len(csv_data[0]) > 1 else None
        desc = csv_data[1][0]
        tags = csv_data[2]
        segments = csv_data[3:]

        # preparing toml data
        toml_string = "[[video]]\n"
        toml_string += "## Auto-generated toml; the file title given was \"{}\"\n".format(title)
        toml_string += "# video_filename = \"\"\n# watermark_home = \"images\"\n# watermark_filename = \"h=(grid1.png=grid2.png)=(grid3.png=(grid4.png=grid1.png=grid2.png))\"\n# watermark_dimension = 200\n"

        if clip_rect:
            toml_string += "clip_rect = \"{}\"\n".format(clip_rect)

        toml_string += "desc = \"{}\"\n".format(desc)
        toml_string += "tags = {}\n\n\n\n\n\n".format([tag.strip() for tag in tags])

        # adding segments
        for seg in segments:
            time_range, seg_clip_rect, description, *seg_tags = seg
            seg_start, _, seg_end = time_range.partition('-')

            toml_string += "[[video.segments]]\n#watermark_filename = \"\"\n#watermark_position = [0, 0]\n"

            if description:
                toml_string += "description = \"{}\"\n".format(description)

            if seg_start:
                toml_string += "start_time = \"{}\"\n".format(seg_start)
            if seg_end:
                toml_string += "end_time = \"{}\"\n".format(seg_end)

            if seg_clip_rect:
                toml_string += "clip_rect = \"{}\"\n".format(seg_clip_rect)

            toml_string += "tags = {}\n\n\n".format([tag.strip() for tag in seg_tags])

        # writing toml file
        with open(output_path, 'w') as toml_file:
            toml_file.write(toml_string)


# usage
generate_toml_from_csv('test_input.csv', 'generated.toml')
