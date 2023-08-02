# hexaclip.py
#
# Ultra-lazy video rect addressing
#

from .rect import *


def hex_to_tuple(hex_string):
    if len(hex_string) != 4:
        raise ValueError('Input should be a four character hexadecimal string')

    return tuple(int(c, 16) / 16.0 for c in hex_string)


class Hexaclip:
    # if no map_rect is given, we map hexaclip to the unit rect (0,0, Size(1,1))
    @classmethod
    def coords(cls, hex_str, map_rect=None, x_offset=0, y_offset=0):
        # pass
        map_rect = Rect.unit_rect if map_rect is None else map_rect
        print(f"Made map_rect: {map_rect}")

        hex_tuple = hex_to_tuple(hex_str)
        print(f"hex_tuple: {hex_tuple}")

        mapped_point = Rect.unit_rect.map(hex_tuple[0] + x_offset / 16.0, hex_tuple[1] + y_offset / 16.0, map_rect)

        print(f" mapped_point = {mapped_point}")
        return mapped_point


    @classmethod
    def rect(cls, hex_str, map_rect=None):
        (x0, y0) = Hexaclip.coords(hex_str[:2])
        (x1, y1) = Hexaclip.coords(hex_str[2:], x_offset=1, y_offset=1)

        print(f"made {hex_str[2:]} into {x1}, {y1} (offsets: 1, 1)")

        map_rect = Rect.unit_rect if map_rect is None else map_rect
        print(f"Made map_rect: {map_rect}")

        (xx0, yy0) = Rect.unit_rect.map(x0, y0, map_rect)
        (xx1, yy1) = Rect.unit_rect.map(x1, y1, map_rect)

        print(f" mapped_point = {xx0}, {yy0}, {xx1}, {yy1}")
        return (xx0, yy0, xx1, yy1)


class TestHexaclip(unittest.TestCase):
    def test_top_left_coord(self):
        self.assertEqual(Hexaclip.coords("88"), (0.5, 0.5))
        self.assertEqual(Hexaclip.coords("08"), (0.0, 0.5))
        self.assertEqual(Hexaclip.coords("0f"), (0.0, 0.9375))
        self.assertEqual(Hexaclip.coords("ff"), (0.9375, 0.9375))


    def test_bottom_right_coord(self):
        # resulting coords have 0.0625 added to x and y
        self.assertEqual(Hexaclip.coords("88", x_offset=1, y_offset=1), (0.5625, 0.5625))
        self.assertEqual(Hexaclip.coords("08", x_offset=1, y_offset=1), (0.0625, 0.5625))
        self.assertEqual(Hexaclip.coords("0f", x_offset=1, y_offset=1), (0.0625, 1))
        self.assertEqual(Hexaclip.coords("ff", x_offset=1, y_offset=1), (1, 1))


    def test_rect(self):
        self.assertEqual(Hexaclip.rect("00ff"), (0, 0, 1.0, 1.0))
        self.assertEqual(Hexaclip.rect("0000"), (0.0, 0.0, 0.0625, 0.0625))
        self.assertEqual(Hexaclip.rect("ffff"), (0.9375, 0.9375, 1.0, 1.0))
