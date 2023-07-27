# rect.py

import unittest
from .size import *
from .maths import *


class Rect:
    def __init__(self, x, y, size, end_x, end_y, centre_x, centre_y):
        self.x = float(x)
        self.y = float(y)
        self.size = size
        self.end_x = float(end_x)
        self.end_y = float(end_y)
        self.area = size.area
        self.centre_x = float(centre_x)
        self.centre_y = float(centre_y)


    @classmethod
    def make(cls, x, y, arg3, arg4=None):
        if arg4:
            return Rect.make_with_end_coords(x, y, arg3, arg4)

        return Rect.make_with_size(x, y, arg3)


    @classmethod
    def make_with_end_coords(cls, x, y, end_x, end_y):
        x, end_x = Maths.asc(x, end_x)
        y, end_y = Maths.asc(y, end_y)
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


    @classmethod
    def make_with_centre_and_size(cls, centre_x, centre_y, size):
        return Rect(
            centre_x - size.width / 2.0,
            centre_y - size.height / 2.0,
            size,
            centre_x + size.width / 2.0,
            centre_y + size.height / 2.0,
            centre_x,
            centre_y
        )


    def matched_centre(self, other_rect):
        return Rect.make_with_size(
            other_rect.centre_x - self.size.width / 2.0,
            other_rect.centre_y - self.size.height / 2.0,
            self.size
        )


    def matched_size(self, other_rect):
        return Rect.make_with_size(
            self.x,
            self.y,
            other_rect.size
        )


    def match_size_maintaining_centre(self, other_rect):
        return Rect.make_with_size(
            self.x - other_rect.size.width / 2,
            self.y - other_rect.size.height / 2,
            other_rect.size
        )


    def moved_minimally_to_lie_inside(self, other_rect):
        # we check `not for self.size < other.size` rather than `self.size > other.size`
        # since inequality check on sizes demands that both width and height have the in equality hold
        # (and we need to know if even just one of width or height fails the check).
        if self.size > other_rect.size:
            raise ValueError(f"Receiver rectangle is larger than the other rectangle: {self.size} > {other_rect.size}")

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

        return Rect.make_with_size(new_x, new_y, self.size)


    def map(self, px, py, target_rect):
        x_percent = (px - self.x) / self.size.width
        y_percent = (py - self.y) / self.size.height

        return (target_rect.x + x_percent * target_rect.size.width,
                target_rect.y + y_percent * target_rect.size.height)


    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.size == other.size and self.end_x == other.end_x \
            and self.end_y == other.end_y and self.area == other.area and self.centre_x == other.centre_x and self.centre_y == other.centre_y


    def __str__(self):
        return f"Rect({self.x}, {self.y}, {self.end_x}, {self.end_y})[centre ({self.centre_x}, {self.centre_y}) size ({self.size.width}, {self.size.height})]"


Rect.unit_rect = Rect.make_with_size(0, 0, Size.unit_size)


class TestRect(unittest.TestCase):
    def test_coord_fixing(self):
        r = Rect.make_with_end_coords(1000, 2000, 210, 120)
        self.assertEqual(r, Rect.make_with_end_coords(210, 120, 1000, 2000))
        r = Rect.make_with_end_coords(-1000, 2000, 210, 120)
        self.assertEqual(r, Rect.make_with_end_coords(-1000, 120, 210, 2000))


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
        r = Rect.make_with_size(-15, -35, Size.make(200, 100))
        self.assertEqual(r.x, -15)
        self.assertEqual(r.y, -35)
        self.assertEqual(r.size.width, 200)
        self.assertEqual(r.size.height, 100)
        self.assertEqual(r.size.aspect_ratio, 2.0)
        self.assertEqual(r.size.aspect_ratio_inv, 1.0/2.0)


    def test_matched_centre(self):
        r1 = Rect.make_with_size(-10, -20, Size.make(200, 100))
        r2 = Rect.make_with_size(1000, 2000, Size.make(40, 10))
        r_expect = Rect.make_with_size(920.0, 1955.0, Size.make(200, 100))

        self.assertEqual(r1.matched_centre(r2), r_expect, f"{r1.matched_centre(r2).__str__()} != {r_expect.__str__()}")


    def test_matched_size(self):
        r1 = Rect.make_with_size(-10, -20, Size.make(200, 100))
        r2 = Rect.make_with_size(1000, 2000, Size.make(40, 10))
        # r_expect = Rect.make_with_centre_and_size(0, 0, Size(0, 0)) #r1.centre_x, r1.centre_y, r2.size)
        r_expect = Rect.make_with_end_coords(-10, -20, 30, -10) #r1.centre_x, r1.centre_y, r2.size)

        self.assertEqual(r1.matched_size(r2), r_expect, f"{r1.matched_size(r2).__str__()} != {r_expect.__str__()}")


    def test_matched_size(self):
        r1 = Rect.make_with_size(-10, -20, Size.make(200, 100))
        r2 = Rect.make_with_size(1000, 2000, Size.make(40, 10))
        # r_expect = Rect.make_with_centre_and_size(0, 0, Size(0, 0)) #r1.centre_x, r1.centre_y, r2.size)
        r_expect = Rect.make_with_end_coords(-30.0, -25.0, 10.0, -15.0)

        self.assertEqual(r1.match_size_maintaining_centre(r2), r_expect, f"{r1.match_size_maintaining_centre(r2).__str__()} != {r_expect.__str__()}")


    def test_reversed_coords(self):
        r1 = Rect.make_with_end_coords(150, 170, 120, 160)
        # r_expect = Rect.make_with_centre_and_size(0, 0, Size(0, 0)) #r1.centre_x, r1.centre_y, r2.size)
        r_expect = Rect.make_with_end_coords(120, 160, 150, 170)

        self.assertEqual(r1, r_expect, f"{r1.__str__()} != {r_expect.__str__()}")


    def test_map(self):
        r1 = Rect.unit_rect
        r2 = Rect.make_with_size(0, 0, Size.make(10, 20))
        p = r1.map(0, 0, r2)
        self.assertEqual(p, (0.0, 0.0))

        r1 = Rect.unit_rect
        r2 = Rect.make_with_size(0, 0, Size.make(10, 20))
        p = r1.map(0.5, 0.5, r2)
        self.assertEqual(p, (5.0, 10.0))

        r1 = Rect.unit_rect
        r2 = Rect.make_with_size(-7, -16, Size.make(10, 20))
        p = r1.map(0, 0, r2)
        self.assertEqual(p, (-7, -16))

        r1 = Rect.unit_rect
        r2 = Rect.make_with_size(-7, -16, Size.make(10, 20))
        p = r1.map(0.5, 0.5, r2)
        self.assertEqual(p, (-2, -6))

        r1 = Rect.unit_rect
        r2 = Rect.make_with_size(-17, 66, Size.make(10, 20))
        p = r1.map(1.0, 0.75, r2)
        self.assertEqual(p, (-7, 81))
