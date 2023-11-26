from __future__ import annotations

# dependencies
from displaylib.pygame import * # type: ignore
import pygame
# local imports
from camera import Camera


class Food(Node2D):
    color: ColorValue = color.BLACK
    radius: int = 3

    def _render(self, surface: Surface) -> None:
        loc = self.get_global_position() - Camera.current.offset
        pygame.draw.circle(surface, self.color, (loc).to_tuple(), self.radius)
