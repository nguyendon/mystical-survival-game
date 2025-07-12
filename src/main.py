import pygame
import sys

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
TILE_SIZE = 32

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BROWN = (139, 69, 19)

# Create the game window
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Mystical Survival Game")

# Player class
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = TILE_SIZE
        self.height = TILE_SIZE
        self.speed = 5

    def move(self, dx, dy):
        self.x += dx * self.speed
        self.y += dy * self.speed

        # Keep player within screen bounds
        self.x = max(0, min(self.x, WINDOW_WIDTH - self.width))
        self.y = max(0, min(self.y, WINDOW_HEIGHT - self.height))

    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, (self.x, self.y, self.width, self.height))

# Simple map class
class GameMap:
    def __init__(self):
        self.width = WINDOW_WIDTH // TILE_SIZE
        self.height = WINDOW_HEIGHT // TILE_SIZE
        self.tiles = [[0 for _ in range(self.width)] for _ in range(self.height)]
        self.generate_map()

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
player = Player(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
game_map = GameMap()

# Game loop
clock = pygame.time.Clock()
running = True

while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Handle keyboard input
    keys = pygame.key.get_pressed()
    dx = keys[pygame.K_d] - keys[pygame.K_a]  # Right - Left
    dy = keys[pygame.K_s] - keys[pygame.K_w]  # Down - Up
    player.move(dx, dy)

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
