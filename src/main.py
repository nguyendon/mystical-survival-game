import pygame
import sys
import random

# Initialize Pygame
pygame.init()

# Constants
INITIAL_WINDOW_WIDTH = 800
INITIAL_WINDOW_HEIGHT = 600
TILE_SIZE = 32
PLAYER_SIZE = 20  # Reduced from 32 to 20
INITIAL_TREE_DENSITY = 0.35
FOREST_ITERATIONS = 2
USE_CLUSTERING = True
MAP_LOCKED = False  # New constant for map locking

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BROWN = (139, 69, 19)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)

# Create the game window with resizable flag
screen = pygame.display.set_mode((INITIAL_WINDOW_WIDTH, INITIAL_WINDOW_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Mystical Survival Game")

# Player class
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = PLAYER_SIZE
        self.height = PLAYER_SIZE
        self.speed = 5
        self.view_mode = "top_down"  # New attribute for view mode

    def move(self, dx, dy, window_width, window_height, game_map):
        # Calculate new position
        new_x = self.x + dx * self.speed
        new_y = self.y + dy * self.speed

        # Keep player within screen bounds using current window size
        new_x = max(0, min(new_x, window_width - self.width))
        new_y = max(0, min(new_y, window_height - self.height))

        # Convert pixel coordinates to tile coordinates for collision checking
        tile_x = new_x // TILE_SIZE
        tile_y = new_y // TILE_SIZE

        # Check if the new position would collide with any trees
        tiles_to_check = []

        # Add all potentially overlapping tiles
        for check_y in range(tile_y, tile_y + 2):
            for check_x in range(tile_x, tile_x + 2):
                if (check_x < game_map.width and check_y < game_map.height):
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

    def draw(self, screen):
        if self.view_mode == "top_down":
            pygame.draw.rect(screen, WHITE, (self.x, self.y, self.width, self.height))
            # Draw a small triangle to indicate direction (facing up by default)
            pygame.draw.polygon(screen, YELLOW, [
                (self.x + self.width // 2, self.y),  # Top
                (self.x + self.width // 4, self.y + self.height // 2),  # Bottom left
                (self.x + 3 * self.width // 4, self.y + self.height // 2)  # Bottom right
            ])

# Simple map class
class GameMap:
    def __init__(self, window_width, window_height):
        self.update_size(window_width, window_height)
        self.generate_map()

    def update_size(self, window_width, window_height):
        self.width = window_width // TILE_SIZE
        self.height = window_height // TILE_SIZE
        self.tiles = [[0 for _ in range(self.width)] for _ in range(self.height)]

    def count_neighbor_trees(self, x, y):
        """Count the number of neighboring trees around a position."""
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
        """Generate a completely random forest"""
        for y in range(self.height):
            for x in range(self.width):
                # Keep spawn area clear
                center_x = self.width // 2
                center_y = self.height // 2
                if abs(x - center_x) <= 1 and abs(y - center_y) <= 1:
                    self.tiles[y][x] = 0
                else:
                    self.tiles[y][x] = 1 if random.random() < INITIAL_TREE_DENSITY else 0

    def generate_clustered_map(self):
        """Generate a clustered forest using cellular automata"""
        # First pass: Random initial tree placement
        self.generate_random_map()

        # Second pass: Create clusters using cellular automata
        for _ in range(FOREST_ITERATIONS):
            new_tiles = [[0 for _ in range(self.width)] for _ in range(self.height)]
            for y in range(self.height):
                for x in range(self.width):
                    # Keep spawn area clear
                    center_x = self.width // 2
                    center_y = self.height // 2
                    if abs(x - center_x) <= 1 and abs(y - center_y) <= 1:
                        new_tiles[y][x] = 0
                        continue

                    neighbors = self.count_neighbor_trees(x, y)
                    # Tree survival/birth rules
                    if self.tiles[y][x] == 1:  # Tree exists
                        new_tiles[y][x] = 1 if neighbors >= 3 else 0
                    else:  # No tree
                        new_tiles[y][x] = 1 if neighbors >= 5 else 0

            self.tiles = new_tiles

    def generate_map(self):
        """Generate map based on current generation method"""
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

def draw_ui_text(screen, use_clustering, map_locked):
    """Draw the current forest generation mode and controls"""
    font = pygame.font.Font(None, 36)
    mode = "Clustered" if use_clustering else "Random"
    lock_status = "LOCKED" if map_locked else "UNLOCKED"

    # Mode text
    mode_text = font.render(f"Mode: {mode}", True, RED)
    screen.blit(mode_text, (10, 10))

    # Controls text
    controls_text = font.render(f"Map: {lock_status} (L to lock, C to toggle, R to regenerate)", True, RED)
    screen.blit(controls_text, (10, 50))

    # View mode text
    view_text = font.render("V to toggle view mode", True, RED)
    screen.blit(view_text, (10, 90))

# Create game objects
window_width = INITIAL_WINDOW_WIDTH
window_height = INITIAL_WINDOW_HEIGHT
player = Player(window_width // 2, window_height // 2)
game_map = GameMap(window_width, window_height)

# Game loop
clock = pygame.time.Clock()
running = True

while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.VIDEORESIZE:
            # Handle window resize event
            window_width = event.w
            window_height = event.h
            screen = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)
            if not MAP_LOCKED:
                # Store player position as percentage of screen before resize
                player_x_percent = player.x / window_width
                player_y_percent = player.y / window_height
                game_map = GameMap(window_width, window_height)  # Regenerate map for new size
                # Restore player position relative to new screen size
                player.x = int(window_width * player_x_percent)
                player.y = int(window_height * player_y_percent)
        elif event.type == pygame.KEYDOWN:
            if not MAP_LOCKED:
                if event.key == pygame.K_c:  # Toggle clustering
                    USE_CLUSTERING = not USE_CLUSTERING
                    game_map.generate_map()
                elif event.key == pygame.K_r:  # Regenerate map
                    game_map.generate_map()
            if event.key == pygame.K_l:  # Toggle map lock
                MAP_LOCKED = not MAP_LOCKED
            elif event.key == pygame.K_v:  # Toggle view mode
                player.view_mode = "first_person" if player.view_mode == "top_down" else "top_down"

    # Handle keyboard input - now supporting both WASD and arrow keys
    keys = pygame.key.get_pressed()
    dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
    dy = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
    player.move(dx, dy, window_width, window_height, game_map)

    # Draw everything
    screen.fill(BLACK)
    game_map.draw(screen, player)
    player.draw(screen)
    draw_ui_text(screen, USE_CLUSTERING, MAP_LOCKED)

    # Update the display
    pygame.display.flip()

    # Control game speed
    clock.tick(60)

# Quit the game
pygame.quit()
sys.exit()
