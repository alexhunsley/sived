# time.py


# Convert "h:m:s" to seconds, with all components apart from seconds optional.
# i.e. can be "m:s" or just "s". The numbers are floats, so can use e.g. "1.5" for seconds.
# If you want frames, use e.g. "6+4/30", which means 6 + 4/30 secs.
# If the denominator is 30, you can just write "6+4" as a shortcut.
def time_to_seconds(time_string):
    print(f"   time_to_seconds got time_string: {time_string}")

    components = time_string.split(':')

    # interpret the seconds
    if '+' in components[-1]:
        if '/' in components[-1]:
            int_part, fraction_part = components[-1].split('+')
            numerator, denominator = map(float, fraction_part.split('/'))
        else:
            int_part, fraction_part = components[-1].split('+')
            numerator = float(fraction_part)
            denominator = 30.0

        seconds = float(int_part) + numerator / denominator
    else:
        seconds = float(components[-1])

    # interpret the minutes and hours
    components = components[:-1] + [seconds]
    components = list(map(float, components))[::-1]
    multipliers = [1, 60, 3600]  # Seconds, Minutes, Hours

    total_seconds = sum(component * multiplier for component, multiplier in zip(components, multipliers))

    return total_seconds
