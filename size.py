# size.py

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

