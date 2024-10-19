# constants.py

import numpy as np

# Window dimensions
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 900

# Colors
COLOR_EMPTY = (0, 0, 0)  # Background color
FONT_COLOR = (255, 255, 255)  # Text color
TOUCHDOWN_LINE_COLOR = (255, 0, 0)  # Red color for touchdown lines
MIDDLE_LINE_COLOR = (255, 255, 255)  # White color for middle line

# Unit properties
UNIT_RADIUS = 10
SEPARATION_DISTANCE = 20
MAX_SPEED = 100

# Placement area height
PLACEMENT_AREA_HEIGHT = WINDOW_HEIGHT / 2  # Half the window height

# Target positions for teams
TOUCHDOWN_LINE_OFFSET = 50
TARGET_POSITION1 = (WINDOW_WIDTH / 2, WINDOW_HEIGHT - TOUCHDOWN_LINE_OFFSET)
TARGET_POSITION2 = (WINDOW_WIDTH / 2, TOUCHDOWN_LINE_OFFSET)

# Player health
PLAYER_MAX_HEALTH = 100
OPPONENT_MAX_HEALTH = 100

# Boid behavior weights
SEPARATION_WEIGHT = 1.0
ALIGNMENT_WEIGHT = 1.0
COHESION_WEIGHT = 0.5
GOAL_WEIGHT = 0.5
PURSUIT_WEIGHT = 1.0

RATE_OF_GAIN = 1.0

# Destinations
DESTINATION1 = (WINDOW_WIDTH / 2, 0)
DESTINATION2 = (WINDOW_WIDTH / 2, WINDOW_HEIGHT)

# Boid behavior parameters
VISION_RADIUS = 200
ATTACK_RADIUS = 100
MAX_DENSITY = 10

# Spatial grid cell size
CELL_SIZE = max(VISION_RADIUS, SEPARATION_DISTANCE)

# Maximum number of units
MAX_UNITS = 5000  # Adjust based on expected maximum units

# Other constants
UNIT_POOL_SIZE = MAX_UNITS
