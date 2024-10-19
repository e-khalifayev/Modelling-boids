# opponent.py

import random
import numpy as np
import time
from constants import WINDOW_WIDTH, PLACEMENT_AREA_HEIGHT, UNIT_RADIUS

class Opponent:
    """AI opponent that spawns units."""

    def __init__(self, unit_data, spawn_interval=2):
        self.unit_data = unit_data
        self.spawn_interval = spawn_interval  # Time in seconds between spawns
        self.last_spawn_time = time.time()

    def spawn_unit(self):
        """Spawn a new unit for the opponent."""
        if random.random() < 0.9:
            is_ranged = False
            attack_range = 0
            vision_range = 100
        else:
            is_ranged = True
            attack_range = 200
            vision_range = 250

        damage = random.randint(1, 3)
        health = random.randint(1, 3)
        speed = random.randint(1, 3)
        team = 2  # Opponent team

        x = random.uniform(UNIT_RADIUS, WINDOW_WIDTH - UNIT_RADIUS)
        y = random.uniform(UNIT_RADIUS, PLACEMENT_AREA_HEIGHT - UNIT_RADIUS)
        position = np.array([x, y], dtype=np.float32)
        velocity = np.zeros(2, dtype=np.float32)
        attack_speed = max(speed / 4, 0.1) if is_ranged else speed
        color = (255, 0, 0) if is_ranged else (0, 0, 255)

        idx = self.unit_data.add_unit(
            team=2,
            position=position,
            velocity=np.zeros(2, dtype=np.float32),
            health=health,
            damage=damage,
            speed=speed,
            attack_range=attack_range,
            vision_range=vision_range,
            attack_speed=attack_speed,
            is_ranged=is_ranged,
            color=color,
            radius=UNIT_RADIUS
        )
        # Spawn additional units
        self.unit_manager.spawn_additional_units(idx)
        

    def update(self):
        """Update the opponent's actions."""
        current_time = time.time()
        if current_time - self.last_spawn_time >= self.spawn_interval:
            self.spawn_unit()
            self.last_spawn_time = current_time
