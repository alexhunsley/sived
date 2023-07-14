# size.py

def clip(value, lower, upper):
    return lower if value < lower else upper if value > upper else value


def min_ratio(a, b):
	return min(a, b) if a > 1 else max(a, b)


def max_ratio(a, b):
	return max(a, b) if a > 1 else min(a, b)


class Size:
    def __init__(self, width, height):
        self.width = float(width)
        self.height = float(height)


    def aspect_ratio(self):
        return self.width / self.height


    def scale(self, factor):
        self.width *= factor
        self.height *= factor
        return self


    def scaled(factor):
    	return Size(self.width * scale_factor, self.height * scale_factor)


    def scaled_to(self, other_size, ratio_choose_func, z_min=None, z_max=None):
        width_ratio = other_size.width / self.width
        height_ratio = other_size.height / self.height
        scale_factor = ratio_choose_func(width_ratio, height_ratio)
        scale_factor = clip(scale_factor, z_min, z_max)
        return self.scaled(scale_factor)


    def __str__(self):
        return f"Size({self.width}, {self.height})"

