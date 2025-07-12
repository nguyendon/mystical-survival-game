import pygame
import sys
import random

# Initialize Pygame
pygame.init()

# Constants
INITIAL_WINDOW_WIDTH = 800
INITIAL_WINDOW_HEIGHT = 600
TILE_SIZE = 32
TREE_DENSITY = 0.15  # 15% chance of a tree on each tile

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BROWN = (139, 69, 19)

# Create the game window with resizable flag
screen = pygame.display.set_mode((INITIAL_WINDOW_WIDTH, INITIAL_WINDOW_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Mystical Survival Game")

# Player class
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = TILE_SIZE
        self.height = TILE_SIZE
        self.speed = 5

    def move(self, dx, dy, window_width, window_height, game_map):
        # Calculate new position
        new_x = self.x + dx * self.speed
        new_y = self.y + dy * self.speed

        # Keep player within screen bounds using current window size
        new_x = max(0, min(new_x, window_width - self.width))
        new_y = max(0, min(new_y, window_height - self.height))

        # Convert pixel coordinates to tile coordinates
        tile_x1 = new_x // TILE_SIZE
        tile_y1 = new_y // TILE_SIZE
        tile_x2 = (new_x + self.width - 1) // TILE_SIZE  # Check right edge
        tile_y2 = (new_y + self.height - 1) // TILE_SIZE  # Check bottom edge

        # Check if any corner would collide with a tree
        corners_to_check = [
            (tile_x1, tile_y1),  # Top-left
            (tile_x2, tile_y1),  # Top-right
            (tile_x1, tile_y2),  # Bottom-left
            (tile_x2, tile_y2)   # Bottom-right
        ]

        can_move = True
        for tile_x, tile_y in corners_to_check:
            if (0 <= tile_x < game_map.width and
                0 <= tile_y < game_map.height and
                game_map.tiles[tile_y][tile_x] == 1):  # Tree collision
                can_move = False
                break

        # Only update position if no collision
        if can_move:
            self.x = new_x
            self.y = new_y

    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, (self.x, self.y, self.width, self.height))

# Simple map class
class GameMap:
    def __init__(self, window_width, window_height):
        self.update_size(window_width, window_height)
        self.generate_map()

    def update_size(self, window_width, window_height):
        self.width = window_width // TILE_SIZE
        self.height = window_height // TILE_SIZE
        self.tiles = [[0 for _ in range(self.width)] for _ in range(self.height)]

    def generate_map(self):
        # Create a random map with grass (0) and trees (1)
        for y in range(self.height):
            for x in range(self.width):
                # Don't place trees in the center area (player spawn)
                center_x = self.width // 2
                center_y = self.height // 2
                if (abs(x - center_x) <= 1 and abs(y - center_y) <= 1):
                    self.tiles[y][x] = 0  # Ensure spawn area is clear
                else:
                    # Random tree placement based on TREE_DENSITY
                    self.tiles[y][x] = 1 if random.random() < TREE_DENSITY else 0

    def draw(self, screen):
        for y in range(self.height):
            for x in range(self.width):
                rect = (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if self.tiles[y][x] == 0:  # Grass
                    pygame.draw.rect(screen, GREEN, rect)
                elif self.tiles[y][x] == 1:  # Tree
                    pygame.draw.rect(screen, BROWN, rect)

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
            # Store player position as percentage of screen before resize
            player_x_percent = player.x / window_width
            player_y_percent = player.y / window_height
            game_map = GameMap(window_width, window_height)  # Regenerate map for new size
            # Restore player position relative to new screen size
            player.x = int(window_width * player_x_percent)
            player.y = int(window_height * player_y_percent)

    # Handle keyboard input
    keys = pygame.key.get_pressed()
    dx = keys[pygame.K_d] - keys[pygame.K_a]  # Right - Left
    dy = keys[pygame.K_s] - keys[pygame.K_w]  # Down - Up
    player.move(dx, dy, window_width, window_height, game_map)

    # Draw everything
    screen.fill(BLACK)
    game_map.draw(screen)
    player.draw(screen)

    # Update the display
    pygame.display.flip()

    # Control game speed
    clock.tick(60)

# Quit the game
pygame.quit()
sys.exit()
