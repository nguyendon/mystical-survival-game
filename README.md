# Mystical Survival Game

A 2D/3D survival game where you explore a procedurally generated forest, collect items, and navigate through a dynamic environment. The game features both top-down and first-person perspectives.

## Features

- **Dual View Modes**
  - Top-down 2D view for strategic navigation
  - First-person 3D view for immersive exploration
  - Toggle between views with 'V' key

- **Procedural Map Generation**
  - Random forest generation with trees and items
  - Clustered forest mode for more natural-looking environments
  - Regenerate map anytime with 'R' key
  - Lock current map with 'L' key

- **Item Collection**
  - Various items to collect:
    - Mushrooms
    - Berries
    - Sticks
    - Stones
    - Flowers
  - Inventory system (toggle with 'I' key)

- **Navigation Features**
  - Minimap for easier orientation (toggle with 'M' key)
  - Smooth collision detection
  - Visual indicators for map boundaries

## Controls

### General Controls
- **V**: Toggle between top-down and first-person view
- **I**: Toggle inventory display
- **M**: Toggle minimap
- **R**: Regenerate map (when unlocked)
- **L**: Lock/unlock map generation
- **C**: Toggle between random and clustered forest generation
- **/**: Toggle instructions display

### Movement Controls
- **W/↑**: Move forward
- **S/↓**: Move backward
- **A/←**: Move left
- **D/→**: Move right

### First-Person Mode Additional Controls
- **Q**: Rotate left
- **E**: Rotate right

## Requirements

- Python 3.x
- Pygame library

## Installation

1. Ensure Python 3.x is installed on your system
2. Install the required dependencies:
   ```bash
   pip install pygame
   ```

## Running the Game

Run the game using Python:
```bash
python main.py
```

## Game Mechanics

### Map Generation
- The forest is generated using either random placement or clustering algorithms
- Clustering creates more natural-looking forest patterns
- Items spawn randomly in open spaces

### Item Collection
- Walk near items to automatically collect them
- View your collected items in the inventory (I key)
- Items are color-coded for easy identification

### Navigation
- The minimap shows your position and surrounding area
- In first-person mode, boundary walls appear in red
- Collision detection prevents walking through trees
- Trees and items are visible from both view perspectives

## Development

The game is built using:
- Python for core game logic
- Pygame for graphics and input handling
- Raycasting for 3D rendering in first-person mode

### Code Structure
- `main.py`: Contains all game code including:
  - Player class for movement and interaction
  - GameMap class for map generation and rendering
  - Item and Inventory systems
  - Raycasting implementation for 3D view

## Future Enhancements

Potential features for future development:
- Save/load game state
- Crafting system
- Day/night cycle
- More item types
- Hostile entities
- Sound effects and music
- More complex terrain generation

## Contributing

Feel free to fork this repository and submit pull requests for any improvements or bug fixes.

## License

This project is open source and available for personal and educational use.