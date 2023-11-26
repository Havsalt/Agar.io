from __future__ import annotations

from typing import TYPE_CHECKING
# dependencies
from displaylib.pygame import * # type: ignore
import pygame
# local imports
from camera import Camera
from movement import Movement
# type hinting
if TYPE_CHECKING:
    from main import App


class PlayerBase(Node2D):
    root: App
    default_process_priority = 1
    MAX_RADIUS = 100
    SPEED_MODIFIER = 10
    color: ColorValue = color.BLACK
    radius: float = 10
    visual_radius: float = radius
    cid = -1 # -1 is not ID set
    visual_position = Vec2.ZERO
    speed = Vec2.ONE * ((MAX_RADIUS - radius +1) * SPEED_MODIFIER +1)

    def _update(self, _delta: float) -> None:
        self.visual_radius = lerp(self.visual_radius, self.radius, 0.05)
        self.visual_position = self.visual_position.lerp(self.get_global_position(), 0.25)
        self.speed = Vec2.ONE * ((self.MAX_RADIUS - self.radius +1) * self.SPEED_MODIFIER +1)

    def _render(self, surface: Surface) -> None:
        loc = self.visual_position - Camera.current.offset
        pygame.draw.circle(surface, self.color, (loc).to_tuple(), self.visual_radius)
    

class Player(PlayerBase, Movement):
    default_process_priority = 2
    MAX_RADIUS = 100
    SPEED_MODIFIER = 0.02
    CHILL_TIME: float = 0.3
    time_chilled: float = CHILL_TIME
    last_position = Vec2.ZERO

    @property
    def is_chilling(self) -> bool:
        return self.time_chilled <= self.CHILL_TIME

    def _update(self, delta: float) -> None:
        self.time_chilled += delta
        if self.is_chilling: # frozen a bit after forced position
            return
        self.radius = min(self.MAX_RADIUS, self.radius)
        super()._update(delta)
        self.visual_position = self.get_global_position() # override
        # send request
        loc = self.get_global_position()
        half_boundary = self.root.half_world_size - (Vec2i.ONE * int(self.visual_radius))
        valid_loc = loc.clamped(-half_boundary, half_boundary)
        self.set_global_position(valid_loc)
        if self.get_global_position().distance_to(self.last_position) > 0.5: # moved more than 0.5
            req = networking.Request("SET_POSITION", data=[self.cid, *self.get_global_position().to_tuple()])
            self.root.send(req)
        self.last_position = self.get_global_position()
