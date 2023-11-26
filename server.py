import time
import socket
import random
import itertools
# dependencies
from displaylib.template import * # type: ignore
from displaylib.pygame import color, ColorValue


class Client(Node2D):
    cid: int = -1
    color: ColorValue = color.BLACK
    radius: float = 10


class Food(Node2D):
    color: ColorValue = color.FOREST_GREEN
    energy: float = 0.2
    radius: int = 3 # this is constant on both sides


class MainServer(networking.Server, Engine):
    WORLD_SIZE = Vec2i(2000, 2000)
    # WORLD_SIZE = Vec2i(500, 500)
    HALF_WORLD_SIZE = Vec2i(WORLD_SIZE.x // 2, WORLD_SIZE.y // 2)
    MAX_FOOD_COUNT: int = 200
    INITIAL_FOOD_BATCHES: int = 20
    FOOD_SPAWN_INTERVAL: float = 1.5 # seconds
    FOOD_SPAWN_GROUP_MIN_RADIUS: int = 10
    FOOD_SPAWN_GROUP_MAX_RADIUS: int = 35
    FOOD_SPAWN_BORDER_MARGIN = Vec2i.ONE * 5
    FOOD_SPAWN_BATCH: int = 5
    INITIAL_PLAYER_RADIUS: int = 10
    MAX_PLAYER_RADIUS: int = 100
    VALID_POSITION_CHANGE: int = 25 # adjust if speed formula on client side is changed
    request_batch = 128

    def _on_start(self) -> None:
        print("[Info] Server start")
        self.cid_counter = 0 # >= 0
        self.clients: dict[int, Client] = {}
        self.foods: dict[tuple[float, float], Food] = {}
        self.food_spawn_timestamp: float = time.perf_counter()
        for _ in range(self.INITIAL_FOOD_BATCHES):
            self.spawn_food_batch()
    
    def _on_client_disconnected(self, connection: socket.socket, error: Exception) -> None:
        print("[Info] Client disconnected", "because of", type(error).__name__, error)
    
    def _on_client_connected(self, connection: socket.socket, host: str, port: int) -> None:
        print("[Info] Client", host, "connected to", port)
        client = Client()
        rand_loc = self.make_random_position()
        half_boundary = self.HALF_WORLD_SIZE - Vec2.ONE * client.radius
        loc = rand_loc.clamped(-half_boundary, half_boundary)
        client.position = loc
        client.cid = self.make_cid()
        req = networking.Request("ASSIGN_CID", data=[client.cid])
        self.send_to(req, connection=connection)
        req = networking.Request("SET_WORLD_SIZE", data=self.WORLD_SIZE.to_tuple())
        self.send_to(req, connection=connection)
        req = networking.Request("SET_INITIAL_POSITION", data=[*client.get_global_position().to_tuple()])
        self.send_to(req, connection=connection)
        client.color = color.rand_color()
        req = networking.Request("SET_COLOR", data=client.color)
        self.send_to(req, connection=connection)
        # spawn the allready existing players for the new client
        for other_client in self.clients.values():
            req = networking.Request("SPAWN_PLAYER", data=[other_client.cid, *other_client.position.to_tuple()])
            self.send_to(req, connection=connection)
            req = networking.Request("SET_DUMMIE_COLOR", data=[other_client.cid, *other_client.color])
            self.send_to(req, connection=connection)
            req = networking.Request("SET_RADIUS", data=[other_client.cid, other_client.radius])
            self.send_to(req, connection=connection)
        for loc, food in self.foods.items():
            req = networking.Request("SPAWN_FOOD", data=[*loc, *food.color])
            self.send_to(req, connection=connection)
        # spawn new player for everyone
        self.clients[client.cid] = client
        req = networking.Request("SPAWN_PLAYER", data=[client.cid, *client.position.to_tuple()])
        self.broadcast(req, exclude=[connection])
        req = networking.Request("SET_DUMMIE_COLOR", data=[client.cid, *client.color])
        self.broadcast(req, exclude=[connection])
    
    def make_cid(self) -> int:
        cid = self.cid_counter
        self.cid_counter += 1
        return cid
    
    def spawn_food_batch(self) -> None:
        batch_center = self.make_random_position()
        for _ in range(self.FOOD_SPAWN_BATCH):
            offset = Vec2i(random.randint(self.FOOD_SPAWN_GROUP_MIN_RADIUS, self.FOOD_SPAWN_GROUP_MAX_RADIUS),
                           random.randint(self.FOOD_SPAWN_GROUP_MIN_RADIUS, self.FOOD_SPAWN_GROUP_MAX_RADIUS))
            if random.randint(0, 1):
                offset.x = -offset.x
            if random.randint(0, 1):
                offset.y = -offset.y
            loc = batch_center + offset
            half_boundary = self.HALF_WORLD_SIZE - self.FOOD_SPAWN_BORDER_MARGIN
            loc = loc.clamped(-half_boundary, half_boundary)
            food = Food()
            food.position = loc
            food.color = color.rand_color()
            self.foods[loc.to_tuple()] = food
            req = networking.Request("SPAWN_FOOD", data=[*food.get_global_position().to_tuple(), *food.color])
            self.broadcast(req)
    
    def _on_response(self, connection: socket.socket, response: networking.Response) -> None:
        # print(response.kind)
        match response:
            case networking.Response(kind="SET_POSITION", data=[cid, x, y]):
                # print(f"SET POSITION: Vec2({x}, {y}) of {cid}")
                if int(cid) == -1:
                    return
                try:
                    loc = Vec2(float(x), float(y))
                except ValueError:
                    print("[Warning] 'SET_POSITION' x or y could not decode properly")
                    return
                client = self.clients[int(cid)]
                dist = client.position.distance_to(loc)
                if dist < self.VALID_POSITION_CHANGE:
                    client.position = loc
                    req = networking.Request("MOVE_DUMMIE", data=[cid, x, y])
                    self.broadcast(req, exclude=[connection])
                else:
                    print(f"[Info] Rejected 'SET_POSITION', responding '{cid}' with 'FORCE_POSITION'")
                    req = networking.Request("FORCE_POSITION", data=[cid, *client.position.to_tuple()])
                    self.send_to(req, connection=connection)

    def make_random_position(self) -> Vec2i:
        return Vec2i(random.randint(-self.HALF_WORLD_SIZE.x, self.HALF_WORLD_SIZE.x),
                     random.randint(-self.HALF_WORLD_SIZE.y, self.HALF_WORLD_SIZE.y))
    
    def _update(self, _delta: float) -> None:
        if time.perf_counter() - self.food_spawn_timestamp >= self.FOOD_SPAWN_INTERVAL:
            if len(self.foods) < self.MAX_FOOD_COUNT:
                self.spawn_food_batch()
            self.food_spawn_timestamp = time.perf_counter()
        # collisions
        foods_eaten_keys: list[tuple[int, int]] = []
        for client in self.clients.values():
            for food in self.foods.values():
                dist = client.get_global_position().distance_to(food.get_global_position())
                if (dist - food.radius + 1) < client.radius:
                    new_radius = min(self.MAX_PLAYER_RADIUS, client.radius + food.energy)
                    client.radius = new_radius
                    foods_eaten_loc = food.get_global_position()
                    food_key = foods_eaten_loc.to_tuple()
                    if food_key not in self.foods:
                        print("[Warning] Invalid food key checked:", food_key)
                        continue
                    foods_eaten_keys.append(food_key) # type: ignore  # tuple is of type tuple[int, int]
                    x_raw, y_raw = food.get_global_position().to_tuple() # acquire by position
                    x = int(x_raw)
                    y = int(y_raw)
                    req = networking.Request("DESTROY_FOOD", data=[x, y])
                    self.broadcast(req)
                    req = networking.Request("SET_RADIUS", data=[client.cid, client.radius])
                    self.broadcast(req)
                    
        for food_key in foods_eaten_keys:
            food_eaten = self.foods[food_key]
            food_eaten.queue_free()
            del self.foods[food_key]
        if len(self.clients) > 1:
            # clients killing each other
            mutally_killed: list[Client] = []
            for client_a, client_b in itertools.permutations(self.clients.values(), r=2):
                dist = client_a.get_global_position().distance_to(client_b.get_global_position())
                if dist - client_a.radius - client_b.radius < 0:
                    if client_a.radius == self.MAX_PLAYER_RADIUS and client_b.radius == self.MAX_PLAYER_RADIUS:
                        for killed_client in (client_a, client_b):
                            if killed_client in mutally_killed:
                                continue
                            mutally_killed.append(killed_client)
                            rand_loc = self.make_random_position()
                            half_boundary = self.HALF_WORLD_SIZE - Vec2.ONE * int(killed_client.radius +1)
                            loc = rand_loc.clamped(-half_boundary, half_boundary)
                            killed_client.position = loc
                            killed_client.radius = self.INITIAL_PLAYER_RADIUS
                            print(f"[Info] Killed client {killed_client.cid} => 'FORCE_POSITION', A")
                            req = networking.Request("FORCE_POSITION", data=[killed_client.cid, *loc.to_tuple()])
                            self.broadcast(req)
                            req = networking.Request("SET_RADIUS", data=[killed_client.cid, self.INITIAL_PLAYER_RADIUS])
                            self.broadcast(req)
                elif int(client_a.radius) == int(client_b.radius):
                    continue # cannot kill with equal radius/power/size
                dist = client_a.get_global_position().distance_to(client_b.get_global_position())
                true_dist = dist - (client_a.radius + client_b.radius)
                if true_dist < 0:
                    survived_client = max(client_a, client_b, key=lambda client_arg: client_arg.radius)
                    killed_client = min(client_a, client_b, key=lambda client_arg: client_arg.radius)
                    survived_client.radius += killed_client.radius
                    rand_loc = self.make_random_position()
                    half_boundary = self.HALF_WORLD_SIZE - Vec2.ONE * int(killed_client.radius +1)
                    loc = rand_loc.clamped(-half_boundary, half_boundary)
                    killed_client.position = loc
                    killed_client.radius = self.INITIAL_PLAYER_RADIUS
                    print(f"[Info] Killed client {killed_client.cid} => 'FORCE_POSITION', B")
                    req = networking.Request("FORCE_POSITION", data=[killed_client.cid, *loc.to_tuple()])
                    self.broadcast(req)
                    req = networking.Request("SET_RADIUS", data=[killed_client.cid, killed_client.radius])
                    self.broadcast(req)
                    # update survived client radius
                    req = networking.Request("SET_RADIUS", data=[survived_client.cid, survived_client.radius])
                    self.broadcast(req)


if __name__ == "__main__":
    server = MainServer()
