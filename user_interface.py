# user_interface.py

import pygame
import time
from constants import WINDOW_WIDTH, WINDOW_HEIGHT, FONT_COLOR, UNIT_RADIUS
from typing import List

class ElixirManager:
    """Manages the player's elixir."""

    def __init__(self):
        self.current_elixir = 5
        self.last_update_time = time.time()

    def update_elixir(self):
        """Increment elixir over time."""
        now = time.time()
        if now - self.last_update_time >= 1:
            self.current_elixir = min(self.current_elixir + 2, 20)
            self.last_update_time = now

    def draw(self, screen):
        """Draw the elixir count on the screen."""
        font = pygame.font.Font(None, 36)
        elixir_text = font.render(f"Elixir: {self.current_elixir}", True, FONT_COLOR)
        screen.blit(elixir_text, (WINDOW_WIDTH - 150, WINDOW_HEIGHT - 120))

# user_interface.py

class UnitSelector:
    """Allows the player to select units to spawn."""

    def init_buttons(self):
        """Initialize unit selection buttons."""
        # Define units with their attributes
        units = [
            {
                'damage': 2,
                'health': 1,
                'speed': 5,
                'is_ranged': False,
            },
            {
                'damage': 3,
                'health': 1,
                'speed': 1,
                'is_ranged': True,
            },
            {
                'damage': 0,
                'health': 3,
                'speed': 0,
                'is_ranged': False,
            },
        ]

        button_width = self.window_width * 0.1
        button_height = self.window_height * 0.05
        button_spacing = self.window_width * 0.025
        start_x = self.window_width * 0.05
        start_y = self.window_height - 75

        self.buttons = []
        for i, unit_attrs in enumerate(units):
            # Calculate cost
            unit_attrs['cost'] = unit_attrs['damage'] + unit_attrs['health'] + unit_attrs['speed']

            # Compute color
            unit_attrs['color'] = self.compute_color(
                damage=unit_attrs['damage'],
                speed=unit_attrs['speed'],
                health=unit_attrs['health']
            )

            # Set default values if not provided
            unit_attrs.setdefault('attack_range', 0 if not unit_attrs['is_ranged'] else 200)
            unit_attrs.setdefault('vision_range', 100)
            unit_attrs.setdefault('attack_speed', unit_attrs['speed'] if unit_attrs['speed'] > 0 else 0.1)
            unit_attrs['radius'] = UNIT_RADIUS  # Constant unit radius

            # Create button
            bx = start_x + i * (button_width + button_spacing)
            button = {
                "unit": unit_attrs,
                "pos": (bx, start_y),
                "label": f"Cost: {unit_attrs['cost']}"
            }
            self.buttons.append(button)

    def compute_color(self, damage, speed, health) -> tuple:
        """Compute RGB color based on damage, speed, and health."""
        r = min(int((damage / 10) * 255), 255)
        g = min(int((speed / 10) * 255), 255)
        b = min(int((health / 10) * 255), 255)
        return (r, g, b)

    def handle_mouse_click(self, position):
        """Handle unit selection on mouse click."""
        mouse_x, mouse_y = position
        for button in self.buttons:
            bx, by = button["pos"]
            button_width = self.window_width * 0.1
            button_height = self.window_height * 0.05
            if bx <= mouse_x <= bx + button_width and by <= mouse_y <= by + button_height:
                self.selected_unit = button["unit"]
                return True
        return False

    def draw(self, screen):
        """Draw unit selection buttons."""
        for button in self.buttons:
            bx, by = button["pos"]
            button_width = self.window_width * 0.1
            button_height = self.window_height * 0.05
            unit_color = button["unit"]['color']

            pygame.draw.rect(screen, unit_color, (bx, by, button_width, button_height))
            pygame.draw.rect(screen, FONT_COLOR, (bx, by, button_width, button_height), 1)

            font = pygame.font.Font(None, 24)
            label = font.render(button["label"], True, FONT_COLOR)
            label_rect = label.get_rect(center=(bx + button_width / 2, by - 15))
            screen.blit(label, label_rect)

class ClickDebouncer:
    """Prevents rapid multiple clicks."""

    def __init__(self, debounce_time: float = 0.2):
        self.last_click_time = 0
        self.debounce_time = debounce_time

    def is_debounced(self) -> bool:
        """Check if enough time has passed since the last click."""
        current_time = time.time()
        if (current_time - self.last_click_time) >= self.debounce_time:
            self.last_click_time = current_time
            return True
        return False
