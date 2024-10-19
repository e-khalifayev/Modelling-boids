# unit.py
import numpy as np
import pygame
from constants import UNIT_RADIUS
from typing import Dict, Any
import uuid

class Unit(pygame.sprite.Sprite):
    """Base class for all units."""

    def __init__(self, damage: int, health: int, speed: int, team: str, is_additional: bool = False):
        super().__init__()
        self.id = str(uuid.uuid4())  # Unique identifier as string
        self.damage = damage
        self.health = health
        self.speed = speed
        self.team = team
        self.is_additional = is_additional
        self.attack_speed = speed if speed > 0 else 0.1  # Prevent division by zero
        self.cooldown = 1/self.attack_speed
        self.attack_range = 0  # Melee units don't have attack range
        self.vision_range = 100  # Define as needed
        self.position = np.array([0.0, 0.0], dtype=np.float32)
        self.velocity = np.array([0.0, 0.0], dtype=np.float32)
        self.radius = UNIT_RADIUS
        self.color = self.compute_color()
        self.cost = damage + health + speed

        # Boid behavior weights
        self.separation_weight = 1.0  # Adjust as needed
        self.alignment_weight = 1.0
        self.cohesion_weight = 1.0
        self.goal_weight = 1.0
        self.pursuit_weight = 1.0

        # Create the image and rect for the sprite
        self.image = pygame.Surface((UNIT_RADIUS * 2, UNIT_RADIUS * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color, (UNIT_RADIUS, UNIT_RADIUS), UNIT_RADIUS)
        self.rect = self.image.get_rect(center=(int(self.position[0]), int(self.position[1])))

    def compute_color(self) -> tuple:
        """Compute RGB color based on damage, speed, and health."""
        r = min(int((self.damage / 10) * 255), 255)
        g = min(int((self.speed / 10) * 255), 255)
        b = min(int((self.health / 10) * 255), 255)
        return (r, g, b)

    def update_sprite_position(self):
        """Update the sprite's rect based on its position."""
        self.rect.center = (int(self.position[0]), int(self.position[1]))

    def set_data(self, data: Dict[str, Any]):
        """Update the unit's data with the provided dictionary."""
        self.position = data['position']
        self.velocity = data['velocity']
        self.health = data['health']
        self.cooldown = data.get('cooldown', 0)
        self.update_sprite_position()

    def get_data(self) -> Dict[str, Any]:
        """Return a dictionary of the unit's data for multiprocessing."""
        return {
            'id': self.id,
            'position': self.position.copy(),
            'velocity': self.velocity.copy(),
            'health': self.health,
            'damage': self.damage,
            'speed': self.speed,
            'team': self.team,
            'attack_range': self.attack_range,
            'vision_range': self.vision_range,
            'cooldown': self.cooldown,
            'attack_speed': self.attack_speed,
            'is_ranged': isinstance(self, RangedUnit)
        }

    def take_damage(self, damage: int):
        """Reduce health by damage and handle death."""
        self.health -= damage
        # print(f"Unit {self.id} took {damage} damage. Health now: {self.health}")
        if self.health <= 0:
            self.kill()  # Remove from all sprite groups

class RangedUnit(Unit):
    """Ranged unit class."""

    def __init__(self, damage: int, health: int, speed: int, team: str, is_additional: bool = False):
        super().__init__(damage, health, speed, team, is_additional)
        self.attack_range = 200  # Define attack range for ranged units
        self.vision_range = 250  # Define vision range for pursuit
        self.attack_speed = max(self.attack_speed / 4, 0.1)  # Prevent attack_speed from being zero
        self.color = self.compute_color()

        # Override image for ranged units if desired
        self.image = pygame.Surface((UNIT_RADIUS * 2, UNIT_RADIUS * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color, (UNIT_RADIUS, UNIT_RADIUS), UNIT_RADIUS)
        self.rect = self.image.get_rect(center=(int(self.position[0]), int(self.position[1])))

    # Note: The attack method is no longer needed as bullets are handled in the game loop
