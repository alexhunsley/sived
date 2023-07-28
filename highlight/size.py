# size.py

import unittest
from dataclasses import dataclass, field
from .maths import Maths


# @dataclass(frozen=True, order=True)
class Size:
    def __init__(self, width, height):
        self.width = abs(width)
        self.height = abs(height)
        self.aspect_ratio = width / height if height != 0 else None
        self.aspect_ratio_inv = height / width if height != 0 else None
        self.area = width * height


    @classmethod
    def make(cls, width: float, height: float):
        return cls(width, height)


    def scaled(self, factor):
        return Size.make(self.width * factor, self.height * factor)

    # min_width stops excessive pixel scaling (cf max_pixel_scale)
    def setting_width_maintaining_aspect(self, width, min_width=None):
        limit_width = width if min_width is None else min(width, min_width)
        # x/y = a
        # x = ya
        # y = x/a
        return Size.make(limit_width, limit_width / self.aspect_ratio)


    def setting_height_maintaining_aspect(self, height, min_height=None):
        limit_height = height if min_height is None else min(height, min_height)

        # x/y = a
        # x = ya
        # y = x/a
        return Size.make(limit_height * self.aspect_ratio, limit_height)


    def scaled_to(self, other_size, ratio_choose_func, z_min=None, z_max=None):
        width_ratio = other_size.width / self.width
        height_ratio = other_size.height / self.height
        print(f" ============ ratios for w/h: {width_ratio} {height_ratio}")
        scale_factor = ratio_choose_func(width_ratio, height_ratio)
        scale_factor = Maths.clip(scale_factor, z_min, z_max)
        print(f" ============ so chose scale factor: {scale_factor}")
        new_size = self.scaled(scale_factor)
        print(f" ============ before, after: {self} {new_size}")
        return new_size


    def aspect_fitted_to(self, other_size, z_min=None, z_max=None):
        # return self.scaled_to(other_size, Maths.min_ratio, z_min, z_max)
        if self.aspect_ratio > other_size.aspect_ratio:
            return self.setting_width_maintaining_aspect(other_size.width)
        else:
            return self.setting_height_maintaining_aspect(other_size.height)


    # self = max_size, other_size = segment rect
    def aspect_filled_to(self, other_size, z_min=None, z_max=None):
        # return self.scaled_to(other_size, Maths.min_ratio, z_min, z_max)
        if self.aspect_ratio < other_size.aspect_ratio:
            set_width = other_size.width if z_max is None else max(other_size.width, self.width / z_max)
            return self.setting_width_maintaining_aspect(set_width)
        else:
            set_height = other_size.height if z_max is None else max(other_size.height, self.height / z_max)
            return self.setting_height_maintaining_aspect(set_height)


    # def aspect_filled_to(self, other_size, z_min=None, z_max=None):
    #     # do we need max_ratio? just ratio?
    #     # return self.scaled_to(other_size, Maths.max_ratio, z_min, z_max)
    #     return self.scaled_to(other_size, max, z_min, z_max)


    # # A large man tries to walk into a bar but he's too big. So he's half filled, half fitted: he's fillited.
    # def aspect_fillited_to(self, other_size, z_min=None, z_max=None):
    #     return self.scaled_to(other_size, Maths.avg, z_min, z_max)


    # returns result of applying a function independently to widths and heights of self and other_size
    def combined_with(self, other_size, func):
        return Size.make(func(self.width, other_size.width), func(self.height, other_size.height))


    # union aka max
    def unioned_with(self, other_size):
        return self.combined_with(other_size, max)


    # union aka min
    def intersected_with(self, other_size):
        return self.combined_with(other_size, min)


    def __lt__(self, other):
        if isinstance(other, Size):
            return self.width < other.width and self.height < other.height
        else:
            raise TypeError("__lt__: Unsupported comparison between instances of 'Size' and '{}'".format(type(other).__name__))


    def __gt__(self, other):
        if isinstance(other, Size):
            return self.width > other.width and self.height > other.height
        else:
            raise TypeError("__gt__: Unsupported comparison between instances of 'Size' and '{}'".format(type(other).__name__))


    def __eq__(self, other):
        return self.width == other.width and self.height == other.height and self.aspect_ratio == other.aspect_ratio \
            and self.aspect_ratio_inv == other.aspect_ratio_inv and self.area == other.area


    def __str__(self):
        return f"Size({self.width}, {self.height}, aspect: {self.aspect_ratio}, area: {self.area})"


Size.unit_size = Size.make(1, 1)
Size.zero = Size.make(0, 0)


class TestSize(unittest.TestCase):
    def test_make(self):
        s = Size.make(2.0, 3.0)
        self.assertEqual(s.width, 2.0)
        self.assertEqual(s.height, 3.0)
        self.assertEqual(s.aspect_ratio, 2.0 / 3.0)
        self.assertEqual(s.area, 2.0 * 3.0)


    def test_abs_sizing(self):
        s = Size.make(-2.0, -3.0)
        self.assertEqual(s.width, 2.0)
        self.assertEqual(s.height, 3.0)
        self.assertEqual(s.aspect_ratio, 2.0 / 3.0)
        self.assertEqual(s.area, 2.0 * 3.0)


    def test_scaled(self):
        s = Size.make(2.0, 3.0)
        scaled_s = s.scaled(2.0)
        self.assertEqual(scaled_s.width, 4.0)
        self.assertEqual(scaled_s.height, 6.0)


    def test_scaled_to_min(self):
        s1 = Size.make(2.0, 1.0)
        s2 = Size.make(6.0, 2.0)
        # in effect, aspect fit
        scaled_s = s1.scaled_to(s2, Maths.min_ratio)
        self.assertEqual(scaled_s.width, 4.0)
        self.assertEqual(scaled_s.height, 2.0)


    def test_scaled_to_max(self):
        s1 = Size.make(2.0, 1.0)
        s2 = Size.make(6.0, 2.0)
        # in effect, aspect fill
        scaled_s = s1.scaled_to(s2, Maths.max_ratio)
        self.assertEqual(scaled_s.width, 6.0)
        self.assertEqual(scaled_s.height, 3.0)


    def test_aspect_fitted_to(self):
        s1 = Size.make(2.0, 1.0)
        s2 = Size.make(6.0, 2.0)
        fitted_s = s1.aspect_fitted_to(s2)
        self.assertEqual(fitted_s.width, 4.0)
        self.assertEqual(fitted_s.height, 2.0)


    def test_aspect_filled_to(self):
        s1 = Size.make(2.0, 1.0)
        s2 = Size.make(6.0, 2.0)
        fitted_s = s1.aspect_filled_to(s2)
        self.assertEqual(fitted_s.width, 6.0)
        self.assertEqual(fitted_s.height, 3.0)


if __name__ == '__main__':
    unittest.main()
