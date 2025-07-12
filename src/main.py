import pygame
import sys

# Initialize Pygame
pygame.init()

# Constants
INITIAL_WINDOW_WIDTH = 800
INITIAL_WINDOW_HEIGHT = 600
TILE_SIZE = 32

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

    def move(self, dx, dy, window_width, window_height):
        self.x += dx * self.speed
        self.y += dy * self.speed

        # Keep player within screen bounds using current window size
        self.x = max(0, min(self.x, window_width - self.width))
        self.y = max(0, min(self.y, window_height - self.height))

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
        # Create a simple map with grass (0) and trees (1)
        for y in range(self.height):
            for x in range(self.width):
                if (x + y) % 7 == 0:  # Place trees in a pattern
                    self.tiles[y][x] = 1

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
            game_map = GameMap(window_width, window_height)  # Regenerate map for new size

    # Handle keyboard input
    keys = pygame.key.get_pressed()
    dx = keys[pygame.K_d] - keys[pygame.K_a]  # Right - Left
    dy = keys[pygame.K_s] - keys[pygame.K_w]  # Down - Up
    player.move(dx, dy, window_width, window_height)

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