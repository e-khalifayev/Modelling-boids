# user_interface.py

import pygame
import time
from constants import WINDOW_WIDTH, WINDOW_HEIGHT, FONT_COLOR
from unit import Unit, RangedUnit
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

class UnitSelector:
    """Allows the player to select units to spawn."""

    def __init__(self, window_width: int, window_height: int):
        self.window_width = window_width
        self.window_height = window_height
        self.selected_unit = None
        self.buttons = []
        self.init_buttons()

    def init_buttons(self):
        """Initialize unit selection buttons."""
        unit1 = Unit(damage=2, health=1, speed=5, team="team1")
        unit2 = RangedUnit(damage=3, health=1, speed=1, team="team1")
        unit3 = Unit(damage=0, health=3, speed=0, team="team1")

        button_width = self.window_width * 0.1
        button_height = self.window_height * 0.05
        button_spacing = self.window_width * 0.025
        start_x = self.window_width * 0.05
        start_y = self.window_height - 75

        self.buttons = [
            {
                "unit": unit1,
                "pos": (start_x, start_y),
                "label": f"Cost: {unit1.cost}"
            },
            {
                "unit": unit2,
                "pos": (start_x + button_width + button_spacing, start_y),
                "label": f"Cost: {unit2.cost}"
            },
            {
                "unit": unit3,
                "pos": (start_x + 2 * (button_width + button_spacing), start_y),
                "label": f"Cost: {unit3.cost}"
            },
        ]

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
            unit_color = button["unit"].color

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
