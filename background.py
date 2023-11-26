from __future__ import annotations

from typing import TYPE_CHECKING
# dependencies
from displaylib.pygame import * # type: ignore
import pygame
# local imports
from camera import Camera
# type hinting
if TYPE_CHECKING:
    from main import App


class Background(Node2D):
    root: App

    def _render(self, surface: Surface) -> None:
        loc = self.get_global_position() - Camera.current.offset - self.root.half_world_size
        pygame.draw.rect(surface, color.WHITE, (loc.to_tuple(), (self.root.half_world_size * 2).to_tuple()))
