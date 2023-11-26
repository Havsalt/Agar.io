import random
import math
# override the Player class itself
from displaylib.math import Vec2, Vec2i
from displaylib.template import networking
import player


class Bot(player.PlayerBase):
    direction = Vec2.RIGHT
    speed = Vec2.ONE
    SIGHT_RANGE: int = 70
    BOUNDARY_WILL_START: float = 0.6
    BOUNDARY_AVOIDANCE: float = 0.15
    FOOD_WILL: float = 0.25
    CHILL_TIME: float = 0.3
    time_chilled: float = CHILL_TIME
    last_position = Vec2.ZERO

    @property
    def is_chilling(self) -> bool:
        return self.time_chilled <= self.CHILL_TIME

    def _update(self, delta: float) -> None:
        self.time_chilled += delta
        if self.is_chilling:
            return
        super()._update(delta)
        self.visual_position = self.get_global_position()
        #: manupulate direction
        angle = math.radians(random.randint(-12, 12))
        self.direction = self.direction.rotated(angle)
        if self.root.foods:
            loc = self.get_global_position()
            closest_food = self.root.foods[tuple(self.root.foods.keys())[0]] # start at first one
            for food in self.root.foods.values():
                if loc.distance_to(food.position) < loc.distance_to(closest_food.position):
                    closest_food = food
            if loc.distance_to(closest_food.position) < self.SIGHT_RANGE:
                dir_to_closest_food = loc.direction_to(closest_food.position)
                self.direction = self.direction.lerp(dir_to_closest_food, self.FOOD_WILL).normalized()
        # bias for moving close to border
        origin = Vec2.ZERO
        dist_to_center = self.get_global_position().distance_to(origin)
        dir_to_center = self.get_global_position().direction_to(origin)
        dist_to_corner = self.root.half_world_size.length()
        if dist_to_center == 0:
            dist_to_center = 0.1
        ratio = dist_to_center / dist_to_corner
        if ratio >= self.BOUNDARY_WILL_START: # kinda close to edge
            self.direction = self.direction.lerp(dir_to_center, self.BOUNDARY_AVOIDANCE * ratio)
        # change position
        self.position += self.direction * self.speed * delta * 0.15
        #:
        loc = self.get_global_position()
        half_boundary = self.root.half_world_size - (Vec2i.ONE * int(self.visual_radius))
        valid_loc = loc.clamped(-half_boundary, half_boundary)
        self.set_global_position(valid_loc)
        if self.get_global_position().distance_to(self.last_position) > 0.5: # moved more than 0.5
            req = networking.Request("SET_POSITION", data=[self.cid, *self.get_global_position().to_tuple()])
            self.root.send(req)
        self.last_position = self.get_global_position()


player.Player = Bot

# start the app
from main import App
import pygame


if __name__ == "__main__":
    app = App(tps=60, icon_path="./icon.png", window_name="Agar.io - Bot", flags=pygame.RESIZABLE)
