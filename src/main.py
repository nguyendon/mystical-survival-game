import pygame
import sys
import random
import math

# Initialize Pygame
pygame.init()

# Constants
INITIAL_WINDOW_WIDTH = 800
INITIAL_WINDOW_HEIGHT = 600
TILE_SIZE = 32
PLAYER_SIZE = 20
INITIAL_TREE_DENSITY = 0.35
FOREST_ITERATIONS = 2
USE_CLUSTERING = True
MAP_LOCKED = False
FOV = math.pi / 3  # 60 degrees field of view
NUM_RAYS = 120  # Number of rays to cast
MAX_DEPTH = 800  # Maximum ray distance
MIN_DISTANCE = 0.1  # Minimum ray distance to prevent division by zero

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BROWN = (139, 69, 19)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
SKY_BLUE = (135, 206, 235)
GROUND_GREEN = (34, 139, 34)

# Create the game window with resizable flag
screen = pygame.display.set_mode((INITIAL_WINDOW_WIDTH, INITIAL_WINDOW_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Mystical Survival Game")

class Ray:
    def __init__(self, angle):
        self.angle = angle
        self.distance = MAX_DEPTH
        self.hit_point = (0, 0)

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = PLAYER_SIZE
        self.height = PLAYER_SIZE
        self.speed = 5
        self.view_mode = "top_down"
        self.angle = 0  # Facing angle in radians (0 is facing right)
        self.rotation_speed = 0.1

    def rotate(self, direction):
        self.angle += direction * self.rotation_speed
        # Keep angle between 0 and 2π
        self.angle %= 2 * math.pi

    def move(self, dx, dy, window_width, window_height, game_map):
        if self.view_mode == "first_person":
            # In first person, movement is relative to viewing angle
            # Invert dy for more intuitive controls (up = forward)
            forward = -dy * self.speed  # Inverted dy
            strafe = dx * self.speed

            # Calculate new position based on angle
            new_x = self.x + math.cos(self.angle) * forward + math.cos(self.angle + math.pi/2) * strafe
            new_y = self.y + math.sin(self.angle) * forward + math.sin(self.angle + math.pi/2) * strafe
        else:
            # Top-down movement
            new_x = self.x + dx * self.speed
            new_y = self.y + dy * self.speed

        # Keep player within screen bounds
        new_x = max(PLAYER_SIZE, min(new_x, window_width - PLAYER_SIZE))
        new_y = max(PLAYER_SIZE, min(new_y, window_height - PLAYER_SIZE))

        # Convert pixel coordinates to tile coordinates for collision checking
        tile_x = int(new_x // TILE_SIZE)
        tile_y = int(new_y // TILE_SIZE)

        # Check if the new position would collide with any trees
        tiles_to_check = []

        # Add all potentially overlapping tiles
        for check_y in range(tile_y - 1, tile_y + 2):
            for check_x in range(tile_x - 1, tile_x + 2):
                if (0 <= check_x < game_map.width and 0 <= check_y < game_map.height):
                    tiles_to_check.append((check_x, check_y))

        # Check if any of these tiles contain a tree
        can_move = True
        for check_x, check_y in tiles_to_check:
            if game_map.tiles[check_y][check_x] == 1:  # Tree collision
                # Calculate tile boundaries
                tile_left = check_x * TILE_SIZE
                tile_right = tile_left + TILE_SIZE
                tile_top = check_y * TILE_SIZE
                tile_bottom = tile_top + TILE_SIZE

                # Check if player's new position would overlap with this tile
                if (new_x < tile_right and new_x + self.width > tile_left and
                    new_y < tile_bottom and new_y + self.height > tile_top):
                    can_move = False
                    break

        # Only update position if no collision
        if can_move:
            self.x = new_x
            self.y = new_y

    def find_safe_spawn(self, game_map, window_width, window_height):
        """Find a safe spawn position without trees"""
        center_x = window_width // 2
        center_y = window_height // 2

        # Try center first
        if self.is_position_safe(center_x, center_y, game_map):
            return center_x, center_y

        # Search in expanding circles
        for radius in range(TILE_SIZE, max(window_width, window_height) // 2, TILE_SIZE):
            for angle in range(0, 360, 30):  # Check every 30 degrees
                rad = math.radians(angle)
                test_x = center_x + radius * math.cos(rad)
                test_y = center_y + radius * math.sin(rad)

                if self.is_position_safe(test_x, test_y, game_map):
                    return test_x, test_y

        # If no safe spot found, clear an area and use center
        center_tile_x = center_x // TILE_SIZE
        center_tile_y = center_y // TILE_SIZE
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if (0 <= center_tile_x + dx < game_map.width and
                    0 <= center_tile_y + dy < game_map.height):
                    game_map.tiles[center_tile_y + dy][center_tile_x + dx] = 0

        return center_x, center_y

    def is_position_safe(self, x, y, game_map):
        """Check if a position is safe (no trees)"""
        tile_x = int(x // TILE_SIZE)
        tile_y = int(y // TILE_SIZE)

        # Check surrounding tiles
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                check_x = tile_x + dx
                check_y = tile_y + dy
                if (0 <= check_x < game_map.width and
                    0 <= check_y < game_map.height and
                    game_map.tiles[check_y][check_x] == 1):
                    return False
        return True

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

            # DDA (Digital Differential Analysis) algorithm for ray casting
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
            ray.distance = max(MIN_DISTANCE, ray.distance)  # Ensure minimum distance

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

class GameMap:
    def __init__(self, window_width, window_height):
        self.update_size(window_width, window_height)
        self.generate_map()

    def update_size(self, window_width, window_height):
        self.width = window_width // TILE_SIZE
        self.height = window_height // TILE_SIZE
        self.tiles = [[0 for _ in range(self.width)] for _ in range(self.height)]

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

    def generate_map(self):
        if not MAP_LOCKED:
            if USE_CLUSTERING:
                self.generate_clustered_map()
            else:
                self.generate_random_map()

    def draw(self, screen, player):
        if player.view_mode == "top_down":
            for y in range(self.height):
                for x in range(self.width):
                    rect = (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    if self.tiles[y][x] == 0:  # Grass
                        pygame.draw.rect(screen, GREEN, rect)
                    elif self.tiles[y][x] == 1:  # Tree
                        pygame.draw.rect(screen, BROWN, rect)

def draw_ui_text(screen, use_clustering, map_locked, view_mode):
    font = pygame.font.Font(None, 36)
    mode = "Clustered" if use_clustering else "Random"
    lock_status = "LOCKED" if map_locked else "UNLOCKED"
    view_status = "First Person" if view_mode == "first_person" else "Top Down"

    mode_text = font.render(f"Mode: {mode}", True, RED)
    screen.blit(mode_text, (10, 10))

    controls_text = font.render(f"Map: {lock_status} (L to lock, C to toggle, R to regenerate)", True, RED)
    screen.blit(controls_text, (10, 50))

    view_text = font.render(f"View: {view_status} (V to toggle)", True, RED)
    screen.blit(view_text, (10, 90))

    if view_mode == "first_person":
        movement_text = font.render("Use arrows/WASD to move, Q/E to rotate", True, RED)
        screen.blit(movement_text, (10, 130))

# Create game objects
window_width = INITIAL_WINDOW_WIDTH
window_height = INITIAL_WINDOW_HEIGHT
player = Player(window_width // 2, window_height // 2)
game_map = GameMap(window_width, window_height)

# Initial safe spawn
player.x, player.y = player.find_safe_spawn(game_map, window_width, window_height)

# Game loop
clock = pygame.time.Clock()
running = True

while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.VIDEORESIZE:
            window_width = event.w
            window_height = event.h
            screen = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)
            if not MAP_LOCKED:
                player_x_percent = player.x / window_width
                player_y_percent = player.y / window_height
                game_map = GameMap(window_width, window_height)
                # Find safe spawn in new map
                player.x, player.y = player.find_safe_spawn(game_map, window_width, window_height)
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

    # Draw everything
    screen.fill(BLACK)

    if player.view_mode == "first_person":
        rays = player.cast_rays(game_map)
        player.draw_3d(screen, rays)
    else:
        game_map.draw(screen, player)
        player.draw(screen)

    draw_ui_text(screen, USE_CLUSTERING, MAP_LOCKED, player.view_mode)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
