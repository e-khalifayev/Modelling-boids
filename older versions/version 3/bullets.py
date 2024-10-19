# bullets.py
import numpy as np
import pygame
from config import FONT_COLOR, WINDOW_HEIGHT, WINDOW_WIDTH, Singleton

# Define the Bullet class
class Bullet:
    def __init__(self, position, velocity, damage, color, team):
        self.position = position.copy()
        self.velocity = velocity.copy()
        self.damage = damage
        self.color = color
        self.radius = damage  # Radius of the bullet
        self.team = team

    def move(self):
        self.position += self.velocity

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.position[0]), int(self.position[1])), self.radius)
        pygame.draw.circle(surface, FONT_COLOR, (int(self.position[0]), int(self.position[1])), self.radius, 1)
