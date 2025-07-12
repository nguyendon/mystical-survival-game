import pygame
import sys
import random
import math
import asyncio
from enum import Enum

async def main():
    # Initialize Pygame
    pygame.init()

    # Constants
    INITIAL_WINDOW_WIDTH = 800
    INITIAL_WINDOW_HEIGHT = 600
    TILE_SIZE = 32
    PLAYER_SIZE = 20
    ITEM_SIZE = 16
    INITIAL_TREE_DENSITY = 0.35
    ITEM_SPAWN_CHANCE = 0.02  # 2% chance per empty tile
    FOREST_ITERATIONS = 2
    USE_CLUSTERING = True
    MAP_LOCKED = False
    FOV = math.pi / 3  # 60 degrees field of view
    NUM_RAYS = 120  # Number of rays to cast
    MAX_DEPTH = 800  # Maximum ray distance
    MIN_DISTANCE = 0.1  # Minimum ray distance to prevent division by zero
    MOVEMENT_SPEED = 4
    ROTATION_SPEED = 0.04

    class ItemType(Enum):
        MUSHROOM = "Mushroom"
        BERRY = "Berry"
        STICK = "Stick"
        STONE = "Stone"
        FLOWER = "Flower"

    # Colors
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GREEN = (0, 255, 0)
    BROWN = (139, 69, 19)
    RED = (255, 0, 0)
    YELLOW = (255, 255, 0)
    SKY_BLUE = (135, 206, 235)
    GROUND_GREEN = (34, 139, 34)
    ITEM_COLORS = {
        ItemType.MUSHROOM: (255, 235, 205),  # Light beige for mushrooms
        ItemType.BERRY: (220, 20, 60),       # Crimson red for berries
        ItemType.STICK: (205, 133, 63),      # Peru brown for sticks
        ItemType.STONE: (169, 169, 169),     # Dark gray for stones
        ItemType.FLOWER: (255, 105, 180)     # Hot pink for flowers
    }

    class Item:
        def __init__(self, item_type, x, y):
            self.type = item_type
            self.x = x
            self.y = y
            self.width = ITEM_SIZE
            self.height = ITEM_SIZE

        def draw(self, screen):
            pygame.draw.rect(screen, ITEM_COLORS[self.type],
                            (self.x, self.y, self.width, self.height))

    class Inventory:
        def __init__(self):
            self.items = {}  # Dictionary to store item counts
            self.visible = False
            self.font = pygame.font.Font(None, 32)

        def add_item(self, item_type):
            if item_type in self.items:
                self.items[item_type] += 1
            else:
                self.items[item_type] = 1

        def draw(self, screen):
            if not self.visible:
                return

            # Draw inventory background
            inventory_surface = pygame.Surface((300, 400))
            inventory_surface.fill((50, 50, 50))
            inventory_surface.set_alpha(230)

            # Draw items list
            y_offset = 10
            for item_type, count in self.items.items():
                text = f"{item_type.value}: {count}"
                text_surface = self.font.render(text, True, WHITE)
                inventory_surface.blit(text_surface, (10, y_offset))
                y_offset += 30

            # Position inventory on screen
            screen.blit(inventory_surface, (10, 10))

    class Ray:
        def __init__(self, angle):
            self.angle = angle
            self.distance = MAX_DEPTH
            self.hit_point = (0, 0)
            self.item = None
            self.item_distance = float('inf')

    class Player:
        def __init__(self, x, y):
            self.x = x
            self.y = y
            self.width = PLAYER_SIZE
            self.height = PLAYER_SIZE
            self.speed = MOVEMENT_SPEED
            self.view_mode = "top_down"
            self.angle = 0  # Facing angle in radians (0 is facing right)
            self.rotation_speed = ROTATION_SPEED
            self.inventory = Inventory()
            self.pickup_range = TILE_SIZE  # Range for picking up items

        def rotate(self, direction):
            self.angle += direction * self.rotation_speed
            self.angle %= 2 * math.pi

        def move(self, dx, dy, window_width, window_height, game_map):
            if self.view_mode == "first_person":
                # In first person, movement is relative to viewing angle
                forward = -dy * self.speed  # Forward/backward
                strafe = dx * self.speed    # Strafe left/right

                # Calculate movement vector
                move_x = math.cos(self.angle) * forward + math.cos(self.angle + math.pi/2) * strafe
                move_y = math.sin(self.angle) * forward + math.sin(self.angle + math.pi/2) * strafe

                # Try movement along both axes independently
                self.try_move(move_x, 0, window_width, window_height, game_map)
                self.try_move(0, move_y, window_width, window_height, game_map)
            else:
                # Top-down movement
                self.try_move(dx * self.speed, dy * self.speed, window_width, window_height, game_map)

        def try_move(self, dx, dy, window_width, window_height, game_map):
            """Attempt to move by the given delta, checking for collisions"""
            new_x = self.x + dx
            new_y = self.y + dy

            # Keep player within screen bounds
            new_x = max(PLAYER_SIZE, min(new_x, window_width - PLAYER_SIZE))
            new_y = max(PLAYER_SIZE, min(new_y, window_height - PLAYER_SIZE))

            # Convert pixel coordinates to tile coordinates for collision checking
            tile_x = int(new_x // TILE_SIZE)
            tile_y = int(new_y // TILE_SIZE)

            # Check if the new position would collide with any trees
            if not self.check_collision(new_x, new_y, game_map):
                self.x = new_x
                self.y = new_y

        def check_collision(self, x, y, game_map):
            """Check if a position would result in a collision"""
            # Get the tiles that the player's corners would occupy
            corners = [
                (x, y),  # Top-left
                (x + self.width, y),  # Top-right
                (x, y + self.height),  # Bottom-left
                (x + self.width, y + self.height)  # Bottom-right
            ]

            for corner_x, corner_y in corners:
                tile_x = int(corner_x // TILE_SIZE)
                tile_y = int(corner_y // TILE_SIZE)

                if (0 <= tile_x < game_map.width and
                    0 <= tile_y < game_map.height and
                    game_map.tiles[tile_y][tile_x] == 1):
                    return True
            return False

        def try_pickup_items(self, game_map):
            """Try to pick up any items within range"""
            items_to_remove = []
            player_center = (self.x + self.width/2, self.y + self.height/2)

            for item in game_map.items:
                item_center = (item.x + item.width/2, item.y + item.height/2)
                distance = math.sqrt((player_center[0] - item_center[0])**2 +
                                   (player_center[1] - item_center[1])**2)

                if distance < self.pickup_range:
                    self.inventory.add_item(item.type)
                    items_to_remove.append(item)

            # Remove collected items
            for item in items_to_remove:
                game_map.items.remove(item)

        def find_safe_spawn(self, game_map, window_width, window_height):
            """Find a safe spawn position without trees"""
            center_x = window_width // 2
            center_y = window_height // 2

            # Try center first
            if not self.check_collision(center_x - self.width/2, center_y - self.height/2, game_map):
                return center_x - self.width/2, center_y - self.height/2

            # Search in expanding circles
            for radius in range(TILE_SIZE, max(window_width, window_height) // 2, TILE_SIZE):
                for angle in range(0, 360, 30):  # Check every 30 degrees
                    rad = math.radians(angle)
                    test_x = center_x + radius * math.cos(rad) - self.width/2
                    test_y = center_y + radius * math.sin(rad) - self.height/2

                    if not self.check_collision(test_x, test_y, game_map):
                        return test_x, test_y

            # If no safe spot found, clear an area and use center
            center_tile_x = center_x // TILE_SIZE
            center_tile_y = center_y // TILE_SIZE
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if (0 <= center_tile_x + dx < game_map.width and
                        0 <= center_tile_y + dy < game_map.height):
                        game_map.tiles[center_tile_y + dy][center_tile_x + dx] = 0

            return center_x - self.width/2, center_y - self.height/2

        def cast_rays(self, game_map):
            rays = []
            start_angle = self.angle - FOV/2
            angle_step = FOV / NUM_RAYS

            for i in range(NUM_RAYS):
                ray = Ray(start_angle + i * angle_step)

                # Ray starting point (center of player)
                ray_x = self.x + self.width/2
                ray_y = self.y + self.height/2

                # Ray direction vector
                ray_cos = math.cos(ray.angle)
                ray_sin = math.sin(ray.angle)

                # Check for items first
                closest_item = None
                closest_item_dist = float('inf')

                for item in game_map.items:
                    # Calculate vector from ray origin to item center
                    item_center_x = item.x + item.width/2
                    item_center_y = item.y + item.height/2

                    # Vector from ray origin to item
                    to_item_x = item_center_x - ray_x
                    to_item_y = item_center_y - ray_y

                    # Length of this vector
                    to_item_length = math.sqrt(to_item_x**2 + to_item_y**2)

                    if to_item_length < MIN_DISTANCE:
                        continue

                    # Dot product of ray direction and normalized vector to item
                    dot_product = (to_item_x * ray_cos + to_item_y * ray_sin) / to_item_length

                    # If item is behind ray or too far to sides, skip it
                    if dot_product < 0 or abs(dot_product) > 1:
                        continue

                    # Calculate perpendicular distance to ray
                    perp_dist = abs(to_item_x * ray_sin - to_item_y * ray_cos)

                    # If item is too far from ray line, skip it
                    if perp_dist > ITEM_SIZE/2:
                        continue

                    # Calculate actual distance along ray
                    dist = to_item_length * dot_product

                    if dist < closest_item_dist:
                        closest_item_dist = dist
                        closest_item = item

                # DDA algorithm for ray casting
                map_x = int(ray_x // TILE_SIZE)
                map_y = int(ray_y // TILE_SIZE)

                # Length of ray from current position to next x or y-side
                delta_dist_x = abs(1 / ray_cos) if ray_cos != 0 else float('inf')
                delta_dist_y = abs(1 / ray_sin) if ray_sin != 0 else float('inf')

                # Calculate step and initial side_dist
                if ray_cos < 0:
                    step_x = -1
                    side_dist_x = (ray_x - map_x * TILE_SIZE) / TILE_SIZE * delta_dist_x
                else:
                    step_x = 1
                    side_dist_x = ((map_x + 1) * TILE_SIZE - ray_x) / TILE_SIZE * delta_dist_x

                if ray_sin < 0:
                    step_y = -1
                    side_dist_y = (ray_y - map_y * TILE_SIZE) / TILE_SIZE * delta_dist_y
                else:
                    step_y = 1
                    side_dist_y = ((map_y + 1) * TILE_SIZE - ray_y) / TILE_SIZE * delta_dist_y

                # Perform DDA
                hit = False
                distance = 0
                while not hit and distance < MAX_DEPTH:
                    # Jump to next map square
                    if side_dist_x < side_dist_y:
                        side_dist_x += delta_dist_x
                        map_x += step_x
                        distance = side_dist_x
                    else:
                        side_dist_y += delta_dist_y
                        map_y += step_y
                        distance = side_dist_y

                    # Check if ray has hit a wall
                    if (0 <= map_x < game_map.width and 0 <= map_y < game_map.height):
                        if game_map.tiles[map_y][map_x] == 1:
                            hit = True
                            ray.distance = max(MIN_DISTANCE, distance * TILE_SIZE)
                            ray.hit_point = (ray_x + ray_cos * distance * TILE_SIZE,
                                           ray_y + ray_sin * distance * TILE_SIZE)
                    else:
                        break

                if not hit:
                    ray.distance = MAX_DEPTH
                    ray.hit_point = (ray_x + ray_cos * MAX_DEPTH,
                                   ray_y + ray_sin * MAX_DEPTH)

                # Fix fisheye effect
                ray.distance *= math.cos(ray.angle - self.angle)
                ray.distance = max(MIN_DISTANCE, ray.distance)

                # Store item information if it's closer than the wall
                if closest_item and closest_item_dist < ray.distance:
                    ray.item = closest_item
                    ray.item_distance = closest_item_dist * math.cos(ray.angle - self.angle)
                else:
                    ray.item = None
                    ray.item_distance = float('inf')

                rays.append(ray)

            return rays

        def draw(self, screen):
            if self.view_mode == "top_down":
                # Draw player rectangle
                pygame.draw.rect(screen, WHITE, (self.x, self.y, self.width, self.height))

                # Calculate direction indicator points
                tip_x = self.x + self.width/2 + math.cos(self.angle) * self.width
                tip_y = self.y + self.height/2 + math.sin(self.angle) * self.height
                left_x = self.x + self.width/2 + math.cos(self.angle - 2.6) * self.width * 0.7
                left_y = self.y + self.height/2 + math.sin(self.angle - 2.6) * self.height * 0.7
                right_x = self.x + self.width/2 + math.cos(self.angle + 2.6) * self.width * 0.7
                right_y = self.y + self.height/2 + math.sin(self.angle + 2.6) * self.height * 0.7

                # Draw direction triangle
                pygame.draw.polygon(screen, YELLOW, [
                    (tip_x, tip_y),
                    (left_x, left_y),
                    (right_x, right_y)
                ])

        def draw_3d(self, screen, rays):
            # Clear screen with sky and ground
            screen.fill(SKY_BLUE)
            pygame.draw.rect(screen, GROUND_GREEN,
                            (0, screen.get_height()//2,
                             screen.get_width(), screen.get_height()//2))

            # Draw vertical strips for each ray
            strip_width = screen.get_width() // len(rays)
            for i, ray in enumerate(rays):
                # Calculate wall height based on distance
                wall_height = min((TILE_SIZE * screen.get_height()) / ray.distance, screen.get_height() * 2)

                # Calculate wall strip position
                wall_top = (screen.get_height() - wall_height) / 2
                wall_bottom = (screen.get_height() + wall_height) / 2

                # Draw wall strip with distance shading
                shade = max(0, min(255, 255 - ray.distance * 0.25))
                wall_color = (shade, shade * 0.8, shade * 0.6)  # Brownish color with distance shading
                pygame.draw.rect(screen, wall_color,
                               (i * strip_width, wall_top,
                                strip_width + 1, wall_bottom - wall_top))

                # Draw items if they exist and are closer than walls
                if ray.item and ray.item_distance < ray.distance:
                    # Calculate item height based on distance
                    item_height = min((ITEM_SIZE * screen.get_height()) / ray.item_distance, screen.get_height())

                    # Calculate item position
                    item_top = (screen.get_height() - item_height) / 2
                    item_bottom = (screen.get_height() + item_height) / 2

                    # Get item color and apply distance shading
                    base_color = ITEM_COLORS[ray.item.type]
                    shade_factor = max(0.3, min(1.0, 1.0 - ray.item_distance * 0.001))
                    item_color = tuple(int(c * shade_factor) for c in base_color)

                    # Draw item
                    pygame.draw.rect(screen, item_color,
                                   (i * strip_width, item_top,
                                    strip_width + 1, item_bottom - item_top))

    class GameMap:
        def __init__(self, window_width, window_height):
            self.update_size(window_width, window_height)
            self.items = []
            self.generate_map()

        def update_size(self, window_width, window_height):
            self.width = window_width // TILE_SIZE
            self.height = window_height // TILE_SIZE
            self.tiles = [[0 for _ in range(self.width)] for _ in range(self.height)]

        def spawn_items(self):
            """Spawn items randomly in empty spaces"""
            self.items.clear()
            for y in range(self.height):
                for x in range(self.width):
                    if self.tiles[y][x] == 0 and random.random() < ITEM_SPAWN_CHANCE:
                        item_type = random.choice(list(ItemType))
                        item_x = x * TILE_SIZE + (TILE_SIZE - ITEM_SIZE) // 2
                        item_y = y * TILE_SIZE + (TILE_SIZE - ITEM_SIZE) // 2
                        self.items.append(Item(item_type, item_x, item_y))

        def count_neighbor_trees(self, x, y):
            count = 0
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if (0 <= nx < self.width and 0 <= ny < self.height and
                        self.tiles[ny][nx] == 1):
                        count += 1
            return count

        def generate_random_map(self):
            for y in range(self.height):
                for x in range(self.width):
                    self.tiles[y][x] = 1 if random.random() < INITIAL_TREE_DENSITY else 0
            self.spawn_items()

        def generate_clustered_map(self):
            self.generate_random_map()

            for _ in range(FOREST_ITERATIONS):
                new_tiles = [[0 for _ in range(self.width)] for _ in range(self.height)]
                for y in range(self.height):
                    for x in range(self.width):
                        neighbors = self.count_neighbor_trees(x, y)
                        if self.tiles[y][x] == 1:
                            new_tiles[y][x] = 1 if neighbors >= 3 else 0
                        else:
                            new_tiles[y][x] = 1 if neighbors >= 5 else 0

                self.tiles = new_tiles
            self.spawn_items()

        def generate_map(self):
            if not MAP_LOCKED:
                if USE_CLUSTERING:
                    self.generate_clustered_map()
                else:
                    self.generate_random_map()

        def draw_minimap(self, screen, player, minimap_size=200):
            # Create a surface for the minimap with a black background
            minimap_surface = pygame.Surface((minimap_size, minimap_size))
            minimap_surface.fill(BLACK)

            # Calculate scaling factors
            map_width_pixels = self.width * TILE_SIZE
            map_height_pixels = self.height * TILE_SIZE
            scale_x = minimap_size / map_width_pixels
            scale_y = minimap_size / map_height_pixels
            scale = min(scale_x, scale_y)

            # Calculate tile size on minimap
            mini_tile_size = TILE_SIZE * scale

            # Draw the map tiles
            for y in range(self.height):
                for x in range(self.width):
                    mini_x = x * mini_tile_size
                    mini_y = y * mini_tile_size
                    mini_rect = (mini_x, mini_y, mini_tile_size, mini_tile_size)
                    if self.tiles[y][x] == 0:  # Grass
                        pygame.draw.rect(minimap_surface, GREEN, mini_rect)
                    elif self.tiles[y][x] == 1:  # Tree
                        pygame.draw.rect(minimap_surface, BROWN, mini_rect)

            # Draw items on minimap
            for item in self.items:
                mini_x = item.x * scale
                mini_y = item.y * scale
                mini_item_size = ITEM_SIZE * scale
                pygame.draw.rect(minimap_surface, ITEM_COLORS[item.type],
                               (mini_x, mini_y, mini_item_size, mini_item_size))

            # Draw player on minimap
            mini_player_x = player.x * scale
            mini_player_y = player.y * scale
            mini_player_size = PLAYER_SIZE * scale
            pygame.draw.rect(minimap_surface, WHITE,
                            (mini_player_x, mini_player_y, mini_player_size, mini_player_size))

            # Draw player direction indicator
            tip_x = mini_player_x + mini_player_size/2 + math.cos(player.angle) * mini_player_size
            tip_y = mini_player_y + mini_player_size/2 + math.sin(player.angle) * mini_player_size
            pygame.draw.line(minimap_surface, YELLOW,
                            (mini_player_x + mini_player_size/2, mini_player_y + mini_player_size/2),
                            (tip_x, tip_y), 2)

            # Add a border around the minimap
            pygame.draw.rect(minimap_surface, WHITE, (0, 0, minimap_size, minimap_size), 2)

            # Position the minimap in the top-right corner with some padding
            padding = 10
            screen.blit(minimap_surface, (screen.get_width() - minimap_size - padding, padding))

        def draw(self, screen, player):
                if player.view_mode == "top_down":
                    for y in range(self.height):
                        for x in range(self.width):
                            rect = (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                            if self.tiles[y][x] == 0:  # Grass
                                pygame.draw.rect(screen, GREEN, rect)
                            elif self.tiles[y][x] == 1:  # Tree
                                pygame.draw.rect(screen, BROWN, rect)

                    # Draw items
                    for item in self.items:
                        item.draw(screen)

    def draw_ui_text(screen, use_clustering, map_locked, view_mode, show_instructions):
        if not show_instructions:
            return

        font = pygame.font.Font(None, 36)
        mode = "Clustered" if use_clustering else "Random"
        lock_status = "LOCKED" if map_locked else "UNLOCKED"
        view_status = "First Person" if view_mode == "first_person" else "Top Down"

        mode_text = font.render(f"Mode: {mode}", True, RED)
        screen.blit(mode_text, (10, 10))

        controls_text = font.render(f"Map: {lock_status} (L to lock, C to toggle, R to regenerate)", True, RED)
        screen.blit(controls_text, (10, 50))

        view_text = font.render(f"View: {view_status} (V to toggle, I for inventory)", True, RED)
        screen.blit(view_text, (10, 90))

        if view_mode == "first_person":
            movement_text = font.render("Use arrows/WASD to move, Q/E to rotate", True, RED)
            screen.blit(movement_text, (10, 130))

        help_text = font.render("Press / to toggle instructions, M to toggle minimap", True, RED)
        screen.blit(help_text, (10, 170))

    # Create game objects
    window_width = INITIAL_WINDOW_WIDTH
    window_height = INITIAL_WINDOW_HEIGHT
    screen = pygame.display.set_mode((window_width, window_height))
    player = Player(window_width // 2, window_height // 2)
    game_map = GameMap(window_width, window_height)
    show_instructions = True  # Variable to track if instructions should be shown
    show_minimap = True      # Variable to track if minimap should be shown

    # Initial safe spawn
    player.x, player.y = player.find_safe_spawn(game_map, window_width, window_height)

    # Game loop
    clock = pygame.time.Clock()
    running = True

    while running:
        # Handle keyboard input
        keys = pygame.key.get_pressed()

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if not MAP_LOCKED:
                    if event.key == pygame.K_c:
                        USE_CLUSTERING = not USE_CLUSTERING
                        game_map.generate_map()
                        player.x, player.y = player.find_safe_spawn(game_map, window_width, window_height)
                    elif event.key == pygame.K_r:
                        game_map.generate_map()
                        player.x, player.y = player.find_safe_spawn(game_map, window_width, window_height)
                if event.key == pygame.K_l:
                    MAP_LOCKED = not MAP_LOCKED
                elif event.key == pygame.K_v:
                    player.view_mode = "first_person" if player.view_mode == "top_down" else "top_down"
                elif event.key == pygame.K_i:
                    player.inventory.visible = not player.inventory.visible
                elif event.key == pygame.K_SLASH:
                    show_instructions = not show_instructions
                elif event.key == pygame.K_m:
                    show_minimap = not show_minimap

        # Handle keyboard input
        keys = pygame.key.get_pressed()

        # Movement
        dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
        dy = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])

        # Rotation (in first-person mode)
        if player.view_mode == "first_person":
            if keys[pygame.K_q]:  # Rotate left
                player.rotate(-1)
            if keys[pygame.K_e]:  # Rotate right
                player.rotate(1)

        player.move(dx, dy, window_width, window_height, game_map)

        # Try to pick up items
        player.try_pickup_items(game_map)

        # Draw everything
        screen.fill(BLACK)

        if player.view_mode == "first_person":
            rays = player.cast_rays(game_map)
            player.draw_3d(screen, rays)
        else:
            game_map.draw(screen, player)
            player.draw(screen)

        # Draw minimap if enabled
        if show_minimap:
            game_map.draw_minimap(screen, player)

        # Draw inventory if visible
        player.inventory.draw(screen)

        draw_ui_text(screen, USE_CLUSTERING, MAP_LOCKED, player.view_mode, show_instructions)

        pygame.display.flip()
        await asyncio.sleep(0)  # Required for web browser
        clock.tick(60)

    pygame.quit()

asyncio.run(main())
