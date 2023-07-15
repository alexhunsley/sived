# size.py

import unittest
from dataclasses import dataclass, field
from .maths import Maths


@dataclass(frozen=True, order=True)
class Size:
    width: float
    height: float
    aspect_ratio: float
    area: float


    @classmethod
    def make(cls, width: float, height: float):
        return cls(
            width,
            height,
            width / height if height != 0 else None,
            width * height
        )


    def scaled(self, factor):
        return Size.make(self.width * factor, self.height * factor)


    def scaled_to(self, other_size, ratio_choose_func, z_min=None, z_max=None):
        width_ratio = other_size.width / self.width
        height_ratio = other_size.height / self.height
        scale_factor = ratio_choose_func(width_ratio, height_ratio)
        scale_factor = Maths.clip(scale_factor, z_min, z_max)
        return self.scaled(scale_factor)


    def aspect_fitted_to(self, other_size):
        return self.scaled_to(other_size, Maths.min_ratio)


    def aspect_filled_to(self, other_size):
        return self.scaled_to(other_size, Maths.max_ratio)


    def __str__(self):
        return f"Size({self.width}, {self.height}, aspect: {self.aspect_ratio}, area: {self.area})"


class TestSize(unittest.TestCase):
    def test_make(self):
        s = Size.make(2.0, 3.0)
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

