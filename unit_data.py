# unit_data.py

import numpy as np
from constants import MAX_UNITS

class UnitData:
    """Struct of Arrays to store unit data."""

    def __init__(self):
        self.max_units = MAX_UNITS
        self.active = np.zeros(self.max_units, dtype=bool)
        self.team = np.zeros(self.max_units, dtype=np.int8)  # 1 or 2
        self.position = np.zeros((self.max_units, 2), dtype=np.float32)
        self.velocity = np.zeros((self.max_units, 2), dtype=np.float32)
        self.health = np.zeros(self.max_units, dtype=np.float32)
        self.damage = np.zeros(self.max_units, dtype=np.float32)
        self.speed = np.zeros(self.max_units, dtype=np.float32)
        self.attack_range = np.zeros(self.max_units, dtype=np.float32)
        self.vision_range = np.zeros(self.max_units, dtype=np.float32)
        self.cooldown = np.zeros(self.max_units, dtype=np.float32)
        self.attack_speed = np.zeros(self.max_units, dtype=np.float32)
        self.is_ranged = np.zeros(self.max_units, dtype=bool)
        self.color = np.zeros((self.max_units, 3), dtype=np.uint8)
        self.radius = np.zeros(self.max_units, dtype=np.float32)
        self.available_indices = list(range(self.max_units))

    def add_unit(self, team, position, velocity, health, damage, speed,
                 attack_range, vision_range, attack_speed, is_ranged, color, radius):
        if not self.available_indices:
            raise Exception("Maximum unit limit reached!")
        idx = self.available_indices.pop()
        self.active[idx] = True
        self.team[idx] = team
        self.position[idx] = position
        self.velocity[idx] = velocity
        self.health[idx] = health
        self.damage[idx] = damage
        self.speed[idx] = speed
        self.attack_range[idx] = attack_range
        self.vision_range[idx] = vision_range
        self.attack_speed[idx] = attack_speed
        self.cooldown[idx] = 1 / attack_speed if attack_speed > 0 else 0.1
        self.is_ranged[idx] = is_ranged
        self.color[idx] = color
        self.radius[idx] = radius
        return idx

    def remove_unit(self, idx):
        self.active[idx] = False
        self.available_indices.append(idx)

    def remove_dead_units(self):
        """Remove units with health <= 0."""
        dead_indices = np.where((self.active) & (self.health <= 0))[0]
        for idx in dead_indices:
            self.remove_unit(idx)
