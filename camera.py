from __future__ import annotations

from displaylib.pygame import Node2D, Vec2


class Camera(Node2D):
    current: Camera

    @property
    def offset(self) -> Vec2:
        return self.get_global_position() - (Vec2(self.root.width, self.root.height) / 2)

Camera.current = Camera()