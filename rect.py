# rect.py

from dataclasses import dataclass

@dataclass(frozen=True, order=True)
class Rect:


    def __init__(self, x, y, end_x, end_y):
        self.x = float(x)
        self.y = float(y)
        self.end_x = float(end_x)
        self.end_y = float(end_y)
        self.aspect_ratio = self.width() / self.height() if self.height() != 0 else None
        self.centre = (self.x + self.width() / 2, self.y + self.height() / 2)
        self.width = self.end_x - self.x
        self.height = self.end_y - self.y


    def width(self):
        return self.end_x - self.x


    def height(self):
        return self.end_y - self.y


    def match_centre(self, other_rect):
        cx, cy = other_rect.centre()
        half_width = self.width() / 2
        half_height = self.height() / 2
        self.x = cx - half_width
        self.y = cy - half_height
        self.end_x = cx + half_width
        self.end_y = cy + half_height


    def match_size(self, other_rect):
        self.end_x = self.x + other_rect.width()
        self.end_y = self.y + other_rect.height()


    def match_size_maintaining_centre(self, other_rect):
        cx, cy = self.centre()
        half_width = other_rect.width() / 2
        half_height = other_rect.height() / 2
        self.x = cx - half_width
        self.y = cy - half_height
        self.end_x = cx + half_width
        self.end_y = cy + half_height


    def moved_minimally_to_lie_inside(self, other_rect):
        if self.width() > other_rect.width() or self.height() > other_rect.height():
            raise ValueError("Receiver rectangle is larger than the other rectangle.")
        
        if self.x < other_rect.x:
            self.x = other_rect.x
        elif self.end_x > other_rect.end_x:
            self.x -= (self.end_x - other_rect.end_x)

        if self.y < other_rect.y:
            self.y = other_rect.y
        elif self.end_y > other_rect.end_y:
            self.y -= (self.end_y > other_rect.end_y)

        self.end_x = self.x + self.width()
        self.end_y = self.y + self.height()


    def __str__(self):
        return f"Rect({self.x}, {self.y}, {self.end_x}, {self.end_y})"

