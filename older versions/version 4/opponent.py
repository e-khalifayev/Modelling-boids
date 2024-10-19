# opponent.py
import random
import numpy as np
import time
from unit import Unit, RangedUnit
from constants import WINDOW_WIDTH, PLACEMENT_AREA_HEIGHT, UNIT_RADIUS
from manager import UnitManager
import pygame

class Opponent:
    """AI opponent that spawns units."""

    def __init__(self, unit_manager: UnitManager, spawn_interval: float = 2):
        self.unit_manager = unit_manager
        self.spawn_interval = spawn_interval  # Time in seconds between spawns
        self.last_spawn_time = time.time()

    def spawn_unit(self):
        """Spawn a new unit for the opponent."""
        if random.random() < 0.9:
            new_unit = Unit(
                damage=random.randint(1, 3),
                health=random.randint(1, 3),
                speed=random.randint(1, 3),
                team="team2"
            )
        else:
            new_unit = RangedUnit(
                damage=random.randint(1, 3),
                health=random.randint(1, 3),
                speed=random.randint(1, 3),
                team="team2"
            )

        # Random placement within spawn area
        x = random.uniform(UNIT_RADIUS, WINDOW_WIDTH - UNIT_RADIUS)
        y = random.uniform(UNIT_RADIUS, PLACEMENT_AREA_HEIGHT - UNIT_RADIUS)
        new_unit.position = np.array([x, y], dtype=np.float32)

        # Add the unit to the UnitManager (handles multiplicity)
        self.unit_manager.add_unit(new_unit)

    def update(self):
        """Update the opponent's actions."""
        current_time = time.time()
        if current_time - self.last_spawn_time >= self.spawn_interval:
            self.spawn_unit()
            self.last_spawn_time = current_time
