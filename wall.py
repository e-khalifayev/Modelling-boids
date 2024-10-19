# wall.py

import pygame

class Wall(pygame.sprite.Sprite):
    """Wall class for game boundaries."""

    def __init__(self, rect):
        super().__init__()
        self.rect = rect
        self.image = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0))  # Invisible wall
