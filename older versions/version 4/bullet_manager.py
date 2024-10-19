# bullet_manager.py
import pygame
from bullet import Bullet

class BulletPool:
    """Object pool for bullets."""

    def __init__(self):
        self.pool = []

    def get_bullet(self, position, velocity, damage, color, team, speed=300.0):
        if self.pool:
            bullet = self.pool.pop()
            bullet.reset(position, velocity, damage, color, team, speed)
        else:
            bullet = Bullet(position, velocity, damage, color, team, speed)
        return bullet

    def return_bullet(self, bullet):
        self.pool.append(bullet)

class BulletManager:
    """Manages all bullets in the game with object pooling."""

    def __init__(self):
        self.all_bullets = pygame.sprite.Group()
        self.bullet_pool = BulletPool()

    def add_bullet(self, bullet):
        """Adds a bullet to the group."""
        self.all_bullets.add(bullet)

    def remove_bullet(self, bullet):
        """Removes a bullet and returns it to the pool."""
        self.all_bullets.remove(bullet)
        self.bullet_pool.return_bullet(bullet)

    def update(self, dt: float, screen_rect, walls_group):
        """Update bullets and handle off-screen removal."""
        for bullet in list(self.all_bullets):
            bullet.update(dt)
            if not screen_rect.colliderect(bullet.rect):
                self.remove_bullet(bullet)
            elif pygame.sprite.spritecollide(bullet, walls_group, False):
                self.remove_bullet(bullet)
