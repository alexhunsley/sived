# maths.py

import unittest


class Maths:
    # clip with None support for either/both end values
    @classmethod
    def clip(cls, value, lower, upper):
        # catch any inverted bounds slip-ups
        if lower and upper and lower > upper:
            lower, upper = upper, lower
        return lower if lower and value < lower else (upper if upper and value > upper else value)


    # min function for a ratio, with direction reversed for a < 1.
    # this handles cases where the ratios are on different sides of 1.
    @classmethod
    def min_ratio(cls, a, b):
        # If ratios straddle 1, ensure a is the ratio <1
        a, b = min(a, b), max(a, b)
        return min(a, b) if a >= 1 else max(a, b)


    # max function for a ratio, with direction reversed for a < 1
    @classmethod
    def max_ratio(cls, a, b):
        # If ratios straddle 1, ensure a is the ratio <1
        a, b = min(a, b), max(a, b)
        return max(a, b) if a >= 1 else min(a, b)


class TestMaths(unittest.TestCase):
    def test_clip(self):
        self.assertEqual(Maths.clip(5, 1, 10), 5)
        self.assertEqual(Maths.clip(5, -1, -10), -1)
        # if lower and upper are reversed, clip should reverse them for us
        self.assertEqual(Maths.clip(-9, -12, -15), -12)
        self.assertEqual(Maths.clip(-17, -12, -15), -15)

        self.assertEqual(Maths.clip(-9, -15, -12), -12)
        self.assertEqual(Maths.clip(-17, -15, -12), -15)

        self.assertEqual(Maths.clip(5, None, 10), 5)
        self.assertEqual(Maths.clip(5, 1, None), 5)
        self.assertEqual(Maths.clip(5, 6, 10), 6)
        self.assertEqual(Maths.clip(5, 1, 4), 4)
        self.assertEqual(Maths.clip(5, None, None), 5)

    def test_min_ratio(self):
        self.assertEqual(Maths.min_ratio(2, 3), 2)
        self.assertEqual(Maths.min_ratio(0.5, 0.3), 0.5)
        self.assertEqual(Maths.min_ratio(1, 0.5), 1)
        self.assertEqual(Maths.min_ratio(1, 1.5), 1)


    def test_max_ratio(self):
        self.assertEqual(Maths.max_ratio(2, 3), 3)
        self.assertEqual(Maths.max_ratio(0.5, 0.3), 0.3)
        self.assertEqual(Maths.max_ratio(1, 0.5), 0.5)
        self.assertEqual(Maths.max_ratio(1, 1.5), 1.5)


if __name__ == '__main__':
    unittest.main()
