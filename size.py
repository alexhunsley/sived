# size.py

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

    def min_scaled_size_that_aspect_fits(self, other_size):
        width_ratio = other_size.width / self.width
        height_ratio = other_size.height / self.height
        scale_factor = max(width_ratio, height_ratio)
        return Size(self.width * scale_factor, self.height * scale_factor)

    def __str__(self):
        return f"Size({self.width}, {self.height})"

