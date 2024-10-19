# config.py
import numpy as np

# Constants for window size and other game parameters
WINDOW_WIDTH = 900  # Example screen width
WINDOW_HEIGHT = 900  # Example screen height
UNIT_RADIUS = 10  # Size of the units
PLACEMENT_AREA_HEIGHT = WINDOW_HEIGHT - 100  # Area for placing units

# Define a target position
TARGET_POSITION1 = np.array([WINDOW_WIDTH / 2, WINDOW_HEIGHT * 1])
TARGET_POSITION2 = np.array([WINDOW_WIDTH / 2, WINDOW_HEIGHT * 0])

# Colors for drawing
COLOR_EMPTY = (0, 0, 0)  # Background color
FONT_COLOR = np.array([255, 255, 255]) - COLOR_EMPTY

SEPARATION_DISTANCE = 20  # Distance for separation


# Define a Singleton class
class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class BulletManager(metaclass=Singleton):
    def __init__(self):
        self.team1_bullets = []
        self.team2_bullets = []

    def add_bullet(self, bullet):
        if bullet.team == "team1":
            self.team1_bullets.append(bullet)
        elif bullet.team == "team2":
            self.team2_bullets.append(bullet)
    
    def remove_bullet(self, bullet):
        if bullet.team == "team1":
            self.team1_bullets.remove(bullet)
        elif bullet.team1 == "team2":
            self.team2_bullets.remove(bullet)


class UnitManager(metaclass=Singleton):
    def __init__(self):
        self.team1_units = []
        self.team2_units = []
    
    def add_unit(self, unit):
        if unit.team == "team1":
            self.team1_units.append(unit)
        else:
            self.team2_units.append(unit)
    
    def remove_unit(self, unit):
        if unit.team =="team1":
            self.team1_units.remove(unit)
        else:
            self.team1_units.remove(unit)


class Wall:
    def __init__(self, position, size):
        self.position = np.array(position)
        self.size = np.array(size)

    def check_collision(self, object_position, object_radius):
        # Check if the object collides with the wall
        # For simplicity, let's assume the object is a circle (unit or bullet)
        # Check if any part of the circle is inside the rectangle of the wall
        closest_point_x = max(self.position[0], min(object_position[0], self.position[0] + self.size[0]))
        closest_point_y = max(self.position[1], min(object_position[1], self.position[1] + self.size[1]))
        distance = np.linalg.norm(np.array([closest_point_x, closest_point_y]) - object_position)
        return distance < object_radius


wall_thickness = 50
WALLS = [
    Wall((0, 0), (WINDOW_WIDTH, wall_thickness)),                               # Top wall
    Wall((0, 0), (wall_thickness, WINDOW_HEIGHT)),                              # Left wall
    Wall((0, WINDOW_HEIGHT - wall_thickness), (WINDOW_WIDTH, wall_thickness)),  # Bottom wall
    Wall((WINDOW_WIDTH - wall_thickness, 0), (wall_thickness, WINDOW_HEIGHT))   # Right wall
]
