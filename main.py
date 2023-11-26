# dependencies
from displaylib.pygame import * # type: ignore
import pygame
# local imports
from camera import Camera
from player import PlayerBase, Player
from food import Food
from background import Background


WORLD_SIZE = Vec2(2_000, 2_000)
HALF_WORLD_SIZE = WORLD_SIZE / 2


class App(Engine, networking.Client):
    bg_color = color.WHITE
    half_world_size = Vec2i.ONE * 100 # temp
    request_batch = 64
    response_batch = 128

    def _on_start(self) -> None:
        print("[Info] Client start")
        self.width
        self.background = Background()
        self.player = Player()
        self.floating_point = Node2D()
        self.players: dict[int, PlayerBase] = {-1: self.player}
        self.foods: dict[tuple[float, float], Food] = {}
    
    def _update(self, _delta: float) -> None:
        self.floating_point.position = self.floating_point.position.lerp(self.player.get_global_position(), 0.05)
        rel = self.player.get_global_position() - self.floating_point.position
        target = self.player.get_global_position() + rel
        Camera.current.position = Camera.current.position.lerp(target, 0.25)
        self.bg_color = color.MAROON

    def _on_response(self, response: networking.Response) -> None:
        # print(response.kind)
        match response:
            case networking.Response(kind="ASSIGN_CID", data=[cid]):
                self.player.cid = int(cid)
                del self.players[-1]
                self.players[self.player.cid] = self.player # bind to given client ID

            case networking.Response(kind="SET_WORLD_SIZE", data=[width, height]):
                self.half_world_size = Vec2i(int(width) // 2, int(height) // 2)
            
            case networking.Response(kind="SET_INITIAL_POSITION", data=[x, y]):
                loc = Vec2(float(x), float(y))
                self.player.position = loc.copy()
                self.player.visual_position = loc.copy()
            
            case networking.Response(kind="SPAWN_PLAYER", data=[cid, x, y]):
                loc = Vec2(float(x), float(y))
                player_dummie = PlayerBase()
                player_dummie.position = loc
                self.players[int(cid)] = player_dummie
            
            case networking.Response(kind="FORCE_POSITION", data=[cid, x, y]):
                # print("FORCE POSITION:", f"Vec2({x}, {y}) of {cid}")
                try:
                    loc = Vec2(float(x), float(y))
                except ValueError:
                    print("[Warning] 'FORCE_POSITION': x or y could not decode properly")
                    return
                player = self.players[int(cid)]
                player.position = loc.copy()
                player.visual_position = loc.copy()
                if player is self.player:
                    self.floating_point.position = self.player.position.copy()
                    self.player.time_chilled = 0 # reset chill time
            
            case networking.Response(kind="MOVE_DUMMIE", data=[cid, x, y]):
                try:
                    loc = Vec2(float(x), float(y))
                except ValueError:
                    print("[Warning] 'MOVE_DUMMIE' x or y could not decode properly")
                    return
                self.players[int(cid)].position = loc
            
            case networking.Response(kind="SET_COLOR", data=[r, g, b]):
                self.player.color = color.rgb_color(int(r), int(g), int(b))
            
            case networking.Response(kind="SET_DUMMIE_COLOR", data=[cid, red, green, blue]):
                self.players[int(cid)].color = color.rgb_color(int(red), int(green), int(blue))
            
            case networking.Response(kind="SPAWN_FOOD", data=[x, y, red, green, blue]):
                loc = Vec2(int(x), int(y))
                food = Food()
                food.position = loc
                try:
                    food.color = color.rgb_color(int(red), int(green), int(blue))
                except ValueError:
                    print("[Warning] 'SPAWN_FOOD' red or green or blue could not decode properly")
                    food.color = color.rand_color()
                self.foods[loc.to_tuple()] = food
            
            case networking.Response(kind="SET_RADIUS", data=[cid, radius]):
                try:
                    self.players[int(cid)].radius = float(radius)
                except ValueError:
                    print("[Warning] 'SET_RADIUS' cid or radius could not decode properly")
                    return

            case networking.Response(kind="DESTROY_FOOD", data=[x, y]):
                try:
                    key = (int(x), int(y))
                except ValueError:
                    print("[Warning] 'DESTROY_FOOD': x or y could not decode properly")
                    return
                try:
                    self.foods[key].queue_free()
                    del self.foods[key]
                except KeyError:
                    return


if __name__ == "__main__":
    app = App(tps=60, icon_path="./icon.png", window_name="Agar.io - Clone", flags=pygame.RESIZABLE)
