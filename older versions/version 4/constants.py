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

# Touchdown lines positions
TOUCHDOWN_LINE_OFFSET = 50  # Distance from the edge for touchdown lines

# Boid behavior weights
SEPARATION_WEIGHT = 1
ALIGNMENT_WEIGHT = 1
COHESION_WEIGHT = 0.5
GOAL_WEIGHT = 0.5
PURSUIT_WEIGHT = 1

RATE_OF_GAIN = 1

# Destinations
DESTINATION1 =(WINDOW_WIDTH/2, 0)
DESTINATION2 = (WINDOW_WIDTH/2, WINDOW_HEIGHT)

# Boid behavior parameters
VISION_RADIUS = 100
ATTACK_RADIUS = 50
MAX_DENSITY = 10

# Maximum number of objects per quadtree node
MAX_OBJECTS = 10
MAX_LEVELS = 5
