from __future__ import annotations as _annotations

from typing import TYPE_CHECKING as _TYPE_CHECKING

from displaylib.math import Vec2 as _Vec2
from displaylib.ascii import keyboard as _keyboard

if _TYPE_CHECKING:
    from typing import Protocol as _Protocol
    from displaylib.template.type_hints import NodeType as _NodeType, Transform2DMixin as _Transform2DMixin, UpdateFunction as _UpdateFunction
    from displaylib.ascii import keyboard as _keyboard

    class _ValidMovementNode(_Transform2DMixin, _Protocol):
        @property
        def speed(self) -> _Vec2: ...
        @speed.setter
        def speed(self, value: _Vec2) -> None: ...
        @property
        def is_chilling(self) -> float: ...
        @is_chilling.setter
        def is_chilling(self, value: float) -> None: ...


class Movement: # Component (mixin class)
    speed: _Vec2 = _Vec2.ONE

    def __new__(cls: type[_NodeType], *args, **kwargs) -> _NodeType:
        instance = super().__new__(cls, *args, **kwargs) # type: _ValidMovementNode  # type: ignore
        instance._update = instance._movement_update_wrapper(instance._update) # type: ignore
        return instance # type: ignore
    
    def _movement_update_wrapper(self: _ValidMovementNode, update_function: _UpdateFunction) -> _UpdateFunction:
        def _update(delta: float):
            if not self.is_chilling: # from Player class
                direction = _Vec2.ZERO
                if _keyboard.is_pressed("D"):
                    direction.x += delta
                if _keyboard.is_pressed("A"):
                    direction.x -= delta
                if _keyboard.is_pressed("W"):
                    direction.y -= delta
                if _keyboard.is_pressed("S"):
                    direction.y += delta
                self.position += direction.normalized() * self.speed
            update_function(delta)
        return _update
