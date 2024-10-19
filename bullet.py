# bullet.py

import numpy as np
import pygame

class Bullet:
    """Bullet class with object pooling."""

    def __init__(self, position, velocity, damage, color, team, speed=300.0):
        self.reset(position, velocity, damage, color, team, speed)

    def reset(self, position, velocity, damage, color, team, speed=300.0):
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

        self.radius = 5

    def update(self, dt):
        """Move the bullet."""
        self.position += self.velocity * dt

    def render(self, screen):
        """Render the bullet."""
        pygame.draw.circle(screen, self.color, (int(self.position[0]), int(self.position[1])), self.radius)
