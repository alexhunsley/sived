# rect.py

import unittest
from .size import *


# @functools.total_ordering
# @dataclass(frozen=True, order=True)
class Rect:
    # x: float
    # y: float
    # size: Size
    # end_x: float
    # end_y: float
    # centre_x: float
    # centre_y: float

    # x,
    # y,
    # Size(end_x - x, end_y - y),
    # end_x,
    # end_y,
    # (x + end_x) / 2.0,
    # (y + end_y) / 2.0,
    #
    def __init__(self, x, y, size, end_x, end_y, centre_x, centre_y):
        self.x = x
        self.y = y
        self.size = size
        self.end_x = end_x
        self.end_y = end_y
        # self.aspect_ratio = size.aspect_ratio
        # self.aspect_ratio_inv = size.aspect_ratio_inv
        self.area = size.area


    # Call make with either of these styles:
    #
    #    Rect.make(x, y, size)
    #    Rect.make(x, y, end_x, end_y)
    @classmethod
    def make(cls, x, y, arg3, arg4=None):
        if arg4:
            return Rect.make_with_end_coords(x, y, arg3, arg4)

        return Rect.make_with_size(x, y, arg3)


    @classmethod
    def make_with_end_coords(cls, x, y, end_x, end_y):
        return Rect(
            x,
            y,
            Size(end_x - x, end_y - y),
            end_x,
            end_y,
            (x + end_x) / 2.0,
            (y + end_y) / 2.0,
            )


    @classmethod
    def make_with_size(cls, x, y, size):
        return Rect(
            x,
            y,
            size,
            x + size.width,
            y + size.height,
            x + size.width / 2.0,
            y + size.height / 2.0
        )


    # def __lt__(self, other: 'Size') -> bool:
    #     return self.width < other.width and self.height < other.height
    #
    #
    # def __eq__(self, other: 'Size') -> bool:
    #     return self.width == other.width and self.height == other.height


    def matched_centre(self, other_rect):
        return Rect.make_with_size(
            other_rect.centre_x - self.size.width / 2.0,
            other_rect.centre_y - self.y,
            self.centre
        )


    def matched_size(self, other_rect):
        return Rect.make_with_size(
            self.x,
            self.y,
            other_rect.size
        )


    def match_size_maintaining_centre(self, other_rect):
        return Rect.make_with_size(
            self.x - other_rect.size.x / 2,
            self.y - other_rect.size.y / 2,
            other_rect.size
        )


    def moved_minimally_to_lie_inside(self, other_rect):
        # we check `not for self.size < other.size` rather than `self.size > other.size`
        # since inequality check on sizes demands that both width and height have the in equality hold
        # (and we need to know if even just one of width or height fails the check).
        if not self.size < other_rect.size:
            raise ValueError("Receiver rectangle is larger than the other rectangle.")

        new_x = self.x
        new_y = self.y

        if self.x < other_rect.x:
            new_x = other_rect.x
        elif self.end_x > other_rect.end_x:
            new_x -= (self.end_x - other_rect.end_x)

        if self.y < other_rect.y:
            new_y = other_rect.y
        elif self.end_y > other_rect.end_y:
            new_y -= (self.end_y > other_rect.end_y)

        return Size.make_with_size(new_x, new_y, self.size)


    def __str__(self):
        return f"Rect({self.x}, {self.y}, {self.end_x}, {self.end_y})"


class TestRect(unittest.TestCase):
    def test_make_with_end_coords(self):
        r = Rect.make_with_end_coords(10, 20, 210, 120)
        self.assertEqual(r.x, 10)
        self.assertEqual(r.y, 20)
        self.assertEqual(r.size.width, 200)
        self.assertEqual(r.size.width, 200)
        self.assertEqual(r.size.height, 100)
        self.assertEqual(r.size.aspect_ratio, 2.0)
        self.assertEqual(r.size.aspect_ratio_inv, 1.0/2.0)


    def test_make_with_size(self):
        r = Rect.make_with_size(10, 20, Size.make(200, 100))
        self.assertEqual(r.x, 10)
        self.assertEqual(r.y, 20)
        self.assertEqual(r.size.width, 200)
        self.assertEqual(r.size.width, 200)
        self.assertEqual(r.size.height, 100)
        self.assertEqual(r.size.aspect_ratio, 2.0)
        self.assertEqual(r.size.aspect_ratio_inv, 1.0/2.0)
