# game_components.py
import pygame
import time
import numpy as np
from config import WINDOW_WIDTH, WINDOW_HEIGHT, FONT_COLOR


# Elixir Manager
class ElixirManager:
    def __init__(self):
        self.current_elixir = 5
        self.last_update_time = time.time()

    def update_elixir(self):
        now = time.time()
        if now - self.last_update_time >= 1:
            self.current_elixir = min(self.current_elixir + 2, 20)
            self.last_update_time = now  # Reset the update time

    def draw(self, screen):
        font = pygame.font.Font(None, 36)
        elixir_text = font.render(f"Elixir: {self.current_elixir}", True, FONT_COLOR)
        screen.blit(elixir_text, (WINDOW_WIDTH - 150, WINDOW_HEIGHT - 120))


# Unit Selector
class UnitSelector:
    def __init__(self, window_width, window_height):
        self.window_width = window_width
        self.window_height = window_height
        self.selected_unit = None
        self.buttons = []
        self.init_buttons()

    def init_buttons(self):
        # Initialize sample units for the buttons
        from units import Unit, Ranged_Unit
        
        unit1 = Unit(damage=1, health=1, speed=1, team="team1")
        unit2 = Ranged_Unit(damage=6, health=1, speed=1, team="team1")
        unit3 = Unit(damage=0, health=3, speed=0, team="team1")
        unit4 = Unit(damage=2, health=1, speed=2, team="team2")
        unit5 = Unit(damage=1, health=2, speed=1, team="team2")

        button_width = self.window_width * 0.1
        button_height = self.window_height * 0.05
        button_spacing = self.window_width * 0.025
        start_x = self.window_width * 0.05
        start_y = self.window_height - 75

        # Set up buttons
        self.buttons = [
            {
                "unit": unit1,
                "pos": (start_x, start_y),
                "label": str(unit1.cost)
            },
            {
                "unit": unit2,
                "pos": (start_x + button_width + button_spacing, start_y),
                "label": str(unit2.cost)
            },
            {
                "unit": unit3,
                "pos": (start_x + 2 * (button_width + button_spacing), start_y),
                "label": str(unit3.cost)
            },
        ]

    def handle_mouse_click(self, position):
        """Determine if a click occurred on any unit selection button."""
        mouse_x, mouse_y = position  # Get x and y coordinates of the mouse click
        for button in self.buttons:
            bx, by = button["pos"]
            button_width = self.window_width * 0.1
            button_height = self.window_height * 0.05
            # Check if the click is within the button's boundaries
            if bx <= mouse_x <= bx + button_width and by <= mouse_y <= by + button_height:
                self.selected_unit = button["unit"]  # Select the unit
                print(f"Selected unit with RGB color: {button['unit'].color}")
                return True
        return False  # If no button was clicked, return False

    def draw(self, screen):
        """Draw the unit selection buttons on the screen."""
        for button in self.buttons:
            bx, by = button["pos"]  # Get button position
            button_width = self.window_width * 0.1
            button_height = self.window_height * 0.05
            unit_color = button["unit"].color  # Color of the unit (can be RGB or a set color)

            # Draw the button as a rectangle with the unit's color
            pygame.draw.rect(screen, unit_color, (bx, by, button_width, button_height))  # Draw the button
            pygame.draw.rect(screen, FONT_COLOR, (bx, by, button_width, button_height), 1)  # Border for the button

            # Optional: Draw a label above the button
            font = pygame.font.Font(None, 24)  # Set font and size
            label = font.render(button["label"], True, FONT_COLOR)  # White text
            screen.blit(label, (bx, by - 20))  # Position label above the button



class ClickDebouncer:
    def __init__(self, debounce_time=0.2):
        self.last_click_time = 0
        self.debounce_time = debounce_time

    def is_debounced(self):
        """Returns True if enough time has passed since the last click."""
        current_time = time.time()
        if (current_time - self.last_click_time) >= self.debounce_time:
            self.last_click_time = current_time
            return True
        return False