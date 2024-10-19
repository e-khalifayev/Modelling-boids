import random
import numpy as np
import time
from units import Unit, Ranged_Unit
from config import WINDOW_WIDTH, PLACEMENT_AREA_HEIGHT

# add web rtc

class Opponent:
    def __init__(self, unit_manager, spawn_interval=1.5):
        self.unit_manager = unit_manager
        self.team2_units = unit_manager.team2_units
        self.last_spawn_time = time.time()
        self.spawn_interval = spawn_interval  # Time in seconds between spawns

    def spawn_unit(self):
        # Create a new unit for Team 2 with random parameters
        if random.random() < 0.8:
            new_unit = Unit(
                damage=random.randint(1, 3),
                health=random.randint(1, 3),
                speed=random.randint(1, 3),
                team="team2"
            )
        else:
            new_unit = Ranged_Unit(
                damage=random.randint(1, 3),
                health=random.randint(1, 3),
                speed=random.randint(1, 3),
                team="team2"
            )

        new_unit.position = np.array([random.uniform(0, WINDOW_WIDTH), random.uniform(0, 200)])  # Random placement in the spawn area
        self.team2_units.append(new_unit)

    def update(self):
        # Check if enough time has passed since the last spawn
        current_time = time.time()
        if current_time - self.last_spawn_time >= self.spawn_interval:
            self.spawn_unit()
            self.last_spawn_time = current_time