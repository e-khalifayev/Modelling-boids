# bullet.py
import numpy as np
import pygame
from constants import UNIT_RADIUS
from typing import Tuple

class Bullet(pygame.sprite.Sprite):
    """Bullet class with object pooling."""

    def __init__(self, position: np.ndarray, velocity: np.ndarray, damage: int, color: Tuple[int, int, int], team: str, speed: float = 300.0):
        super().__init__()
        self.speed = speed
        self.reset(position, velocity, damage, color, team, speed)

    def reset(self, position: np.ndarray, velocity: np.ndarray, damage: int, color: Tuple[int, int, int], team: str, speed: float = 300.0):
        """Reset bullet properties for object pooling."""
        self.position = position.astype(np.float32)
        self.velocity = velocity.astype(np.float32)
        self.damage = damage
        self.color = color
        self.team = team
        self.speed = speed

        # Normalize velocity and scale to speed
        direction = self.velocity
        distance = np.linalg.norm(direction)
        if distance > 0:
            direction = (direction / distance) * self.speed
        else:
            direction = np.zeros(2, dtype=np.float32)
        self.velocity = direction

        # Create the image and rect for the sprite
        self.radius = 5
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color, (self.radius, self.radius), self.radius)
        self.rect = self.image.get_rect(center=(int(self.position[0]), int(self.position[1])))

    def update(self, dt: float):
        """Move the bullet."""
        self.position += self.velocity * dt
        self.rect.center = (int(self.position[0]), int(self.position[1]))
