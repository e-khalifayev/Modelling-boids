# bullet_manager.py

import numpy as np
import pygame
from bullet import Bullet

class BulletManager:
    """Manages all bullets in the game with object pooling."""

    def __init__(self):
        self.bullets = []
        self.bullet_pool = []

    def add_bullet(self, position, velocity, damage, color, team, speed=300.0):
        """Adds a bullet to the list."""
        if self.bullet_pool:
            bullet = self.bullet_pool.pop()
            bullet.reset(position, velocity, damage, color, team, speed)
        else:
            bullet = Bullet(position, velocity, damage, color, team, speed)
        self.bullets.append(bullet)
        return bullet

    def update(self, dt, screen_rect, walls_group):
        """Update bullets and handle off-screen removal."""
        for bullet in self.bullets[:]:
            bullet.update(dt)
            if not screen_rect.collidepoint(bullet.position):
                self.remove_bullet(bullet)
            elif pygame.sprite.spritecollide(bullet, walls_group, False):
                self.remove_bullet(bullet)

    def remove_bullet(self, bullet):
        """Removes a bullet and returns it to the pool."""
        self.bullets.remove(bullet)
        self.bullet_pool.append(bullet)

    def render(self, screen):
        """Render all bullets."""
        for bullet in self.bullets:
            bullet.render(screen)
