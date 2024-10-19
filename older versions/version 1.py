import pygame
import sys
import time
import numpy as np
import random

# Constants for the grid and window size
GRID_SIZE = 50
CELL_SIZE = 10
WINDOW_WIDTH = GRID_SIZE * CELL_SIZE
WINDOW_HEIGHT = GRID_SIZE * CELL_SIZE + 100  # Extra space for the unit selector

# Elixir settings
INITIAL_ELIXIR = 5
ELIXIR_RATE = 1  # Elixir added every second
ELIXIR_MAX = 10  # Maximum elixir cap

# Define colors for grid elements
COLOR_EMPTY = (255, 255, 255)  # White for empty cells


# Define the unit class with RGB color mapping
class Unit:
    ### Stats
    def __init__(self, attack, health, speed, ranged, team):
        self.team = team
        self.attack = attack
        self.health = health
        self.speed = speed
        self.max_speed = speed
        self.ranged = ranged

        self.cost = attack + health + speed + ranged
        self.elixir_cost = self.cost

        self.multiplicity = 1 if self.cost >= 10 else 10 - self.cost
        
        self.color = self.compute_color()

        self.position = np.zeros(2, dtype=float)
        self.velocity = np.zeros(2, dtype=float)

    def compute_color(self):
        """Compute RGB color based on attack, speed, and health."""
        r = min(int((self.attack / 10) * 255), 255)  # Normalize to 0-255
        g = min(int((self.speed / 10) * 255), 255)  # Normalize to 0-255
        b = min(int((self.health / 10) * 255), 255)  # Normalize to 0-255
        return (r, g, b)  # Return RGB tuple

    def __str__(self):
        return f"Unit({self.attack}, {self.health}, {self.speed}, {self.ranged}, {self.cost}, {self.color})"

    ### Motion
    def move_towards(self, target):
        desired_velocity = (target - self.position)
        desired_velocity /= np.linalg.norm(desired_velocity)  # Normalize
        desired_velocity *= self.max_speed
        return desired_velocity.astype(float)  # Ensure desired velocity is float

    def pursue_enemy(self, enemy_position):
        desired_velocity = (enemy_position - self.position).astype(float)  # Ensure desired velocity is float
        desired_velocity /= np.linalg.norm(desired_velocity)  # Normalize
        desired_velocity *= self.max_speed
        return desired_velocity

    def velocity_adjustment(self):
        return self.velocity

    def separation_and_collision_avoidance(self, units, separation_distance):
        steering = np.zeros_like(self.position)
        for other_unit in units:
            if other_unit != self:
                distance = np.linalg.norm(self.position - other_unit.position)
                if distance < separation_distance:
                    diff = self.position - other_unit.position
                    diff /= distance  # Weighted by distance
                    steering += diff
        return steering
    
    def update(self, target, enemy_position, units, separation_distance):
        """Update unit velocity and position based on behaviors."""
        # Behavior weights for cohesion, pursuit, and separation
        cohesion_weight = 0.4
        pursuit_weight = 0.6
        separation_collision_weight = 0.1
        
        # Compute desired velocities for different behaviors
        cohesion = self.move_towards(target) * cohesion_weight
        pursuit = self.pursue_enemy(enemy_position) * pursuit_weight
        separation_collision = self.separation_and_collision_avoidance(units, separation_distance) * separation_collision_weight
        
        # Combine behaviors to determine desired velocity
        desired_velocity = cohesion + pursuit + separation_collision
        self.velocity = np.clip(desired_velocity, -self.max_speed, self.max_speed)  # Limit to max speed
        self.position = self.position + self.velocity  # Update the position



# Define a simple grid structure
class Grid:
    def __init__(self, rows, columns):
        self.rows = rows
        self.columns = columns
        self.grid = [[None for _ in range(columns)] for _ in range(rows)]

    def can_place_unit(self, start_row, start_column, multiplicity):
        """Check if we can place units considering multiplicity."""
        if start_column + int(multiplicity) > self.columns:
            return False  # Out of bounds
        
        for col in range(start_column, start_column + int(multiplicity)):
            if self.grid[start_row][col] is not None:
                return False  # Overlap with existing unit
        
        return True


    def place_unit(self, unit, row, column):
        """Place the unit considering multiplicity."""
        if self.can_place_unit(row, column, unit.multiplicity):
            for col in range(column, column + int(unit.multiplicity)):
                self.grid[row][col] = unit
            return True
        return False

    def draw(self, screen):
        """Draw the grid with current units."""
        for r in range(self.rows):
            for c in range(self.columns):
                x = c * CELL_SIZE
                y = r * CELL_SIZE
                if self.grid[r][c] is None:
                    pygame.draw.rect(screen, COLOR_EMPTY, (x, y, CELL_SIZE, CELL_SIZE))
                else:
                    pygame.draw.rect(screen, self.grid[r][c].color, (x, y, CELL_SIZE, CELL_SIZE))
                pygame.draw.rect(screen, (0, 0, 0), (x, y, CELL_SIZE, CELL_SIZE), 1)  # Grid lines


class ElixirManager:
    def __init__(self):
        self.current_elixir = 500  # Initial elixir
        self.last_update_time = time.time()  # Track last update time

    def update_elixir(self):
        """Increase elixir over time (e.g., every second)."""
        now = time.time()
        if now - self.last_update_time >= 1:  # Elixir increases every second
            self.current_elixir = min(self.current_elixir + 10, 1000)  # Cap at 10
            self.last_update_time = now  # Reset the update time

    def draw(self, screen):
        """Display the current elixir on the screen."""
        font = pygame.font.Font(None, 36)
        elixir_text = font.render(f"Elixir: {self.current_elixir}", True, (0, 0, 0))
        screen.blit(elixir_text, (10, WINDOW_HEIGHT - 40))  # Display at the bottom


class UnitSelector:
    def __init__(self):
        self.selected_unit = None  # The currently selected unit
        self.buttons = []  # List of buttons for unit selection
        self.init_buttons()  # Initialize the unit buttons

    def init_buttons(self):
        """Initialize unit selection buttons with units and positions."""

        unit1 = Unit(0, 5, 50, 1, "Team1")
        unit2 = Unit(1, 4, 30, 0, "Team1")
        unit3 = Unit(0, 7, 100, 0, "Team1")

        self.buttons = [
            {
                "unit": unit1,  # Unit with high attack
                "pos": (10, GRID_SIZE * CELL_SIZE + 10),  # Position for button
                "label": str(unit1.elixir_cost) # Optional label
            },
            {
                "unit": unit2,  # Unit with high speed
                "pos": (70, GRID_SIZE * CELL_SIZE + 10),  # Position for button
                "label": str(unit2.elixir_cost)
            },
            {
                "unit": unit3,  # Unit with high health
                "pos": (130, GRID_SIZE * CELL_SIZE + 10),  # Position for button
                "label": str(unit3.elixir_cost)
            },
        ]

    def handle_mouse_click(self, position):
        """Determine if a click occurred on any unit selection button."""
        mouse_x, mouse_y = position  # Extract x and y coordinates of the click
        for button in self.buttons:
            bx, by = button["pos"]
            # Check if the click is within the button's boundaries
            if bx <= mouse_x <= bx + 50 and by <= mouse_y <= by + 30:
                self.selected_unit = button["unit"]  # Select the unit
                print(f"Selected unit with RGB color: {button['unit'].color}")
                return True
        return False  # If no button was clicked, return False

    def draw(self, screen):
        """Draw the unit selection buttons on the screen."""
        for button in self.buttons:
            bx, by = button["pos"]  # Get button position
            unit_color = button["unit"].color  # RGB color of the unit

            # Draw the button as a rectangle with the unit's color
            pygame.draw.rect(screen, unit_color, (bx, by, CELL_SIZE, CELL_SIZE//2))
            pygame.draw.rect(screen, (0, 0, 0), (bx, by, CELL_SIZE, CELL_SIZE//2), 1)  # Border

            # Optional: Draw a label above the button
            font = pygame.font.Font(None, 24)  # Set font and size
            label = font.render(button["label"], True, (0, 0, 0))  # Black text
            screen.blit(label, (bx, by - 20))  # Position label above the button


# To avoid multiple messages for a single click, use a debounce mechanism
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

# Main game loop
pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Unit Movement and Combat with Elixir Management")

# Initialize grid, unit selector, elixir manager, and debouncer
grid = Grid(GRID_SIZE, GRID_SIZE)
unit_selector = UnitSelector()
elixir_manager = ElixirManager()
click_debouncer = ClickDebouncer()

# Initialize pygame and other components
pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Unit Movement with Team-Based Interactions")

# Initialize grid, unit selector, elixir manager, debouncer
grid = Grid(GRID_SIZE, GRID_SIZE)
unit_selector = UnitSelector()
elixir_manager = ElixirManager()
click_debouncer = ClickDebouncer()

# Create initial units for Team 1 and Team 2
unit1_team1 = Unit(attack=1, health=6, speed=2, ranged=1, team="Team1")
unit2_team1 = Unit(attack=6, health=4, speed=3, ranged=0, team="Team1")
unit1_team2 = Unit(attack=7, health=5, speed=2, ranged=0, team="Team2")
unit2_team2 = Unit(attack=5, health=3, speed=4, ranged=0, team="Team2")

# Separate lists for each team
team1_units = []
team2_units = []

# Place units on the grid using grid.place_unit function
for unit in [unit1_team1, unit2_team1, unit1_team2, unit2_team2]:
    row = random.randint(0, GRID_SIZE - 1)  # Random row within the grid size
    column = random.randint(0, GRID_SIZE - 1)  # Random column within the grid size
    while not grid.place_unit(unit, row, column):  # Place unit until successful
        row = random.randint(0, GRID_SIZE - 1)
        column = random.randint(0, GRID_SIZE - 1)
    unit.position = np.array([row, column])  # Set the unit's position
    if unit.team == "Team1":
        team1_units.append(unit)  # Add unit to Team 1 list
    else:
        team2_units.append(unit)  # Add unit to Team 2 list

# Main game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN and click_debouncer.is_debounced():
            if event.pos[1] < GRID_SIZE * CELL_SIZE:  # Click within the grid area
                if unit_selector.selected_unit:
                    row = event.pos[1] // CELL_SIZE
                    column = event.pos[0] // CELL_SIZE
                    selected_unit = unit_selector.selected_unit

                    if elixir_manager.current_elixir >= selected_unit.elixir_cost:
                        if grid.place_unit(selected_unit, row, column):
                            elixir_manager.current_elixir -= selected_unit.elixir_cost
                            # Set the unit's position on the grid
                            selected_unit.position = np.array([row, column])
                            # Add the newly placed unit to Team 1
                            team1_units.append(selected_unit)
                            print("Unit placed successfully!")
                        else:
                            print("Failed to place unit. Check boundaries and overlap.")
                    else:
                        print("Not enough elixir to place this unit.")

            else:  # Click within the unit selector area
                unit_selector.handle_mouse_click(event.pos)

    # Update elixir within the main game loop
    elixir_manager.update_elixir()

    # Update Team 1 units based on Team 2 positions
    for unit in team1_units:
        target = np.array([4.0, 4.0])  # Define a target position (adjust as needed)
        enemy_positions = [u.position for u in team2_units]  # Get all Team 2 positions
        closest_enemy_position = min(enemy_positions, key=lambda pos: np.linalg.norm(unit.position - pos))  # Find closest enemy
        
        # Update position with separation and pursuit behaviors
        unit.update(target=target, enemy_position=closest_enemy_position, units=team1_units, separation_distance=1.0)

    # Update Team 2 units based on Team 1 positions
    for unit in team2_units:
        target = np.array([4.0, 4.0])  # Define a common target position (adjust as needed)
        enemy_positions = [u.position for u in team1_units]  # Get all Team 1 positions
        closest_enemy_position = min(enemy_positions, key=lambda pos: np.linalg.norm(unit.position - pos))  # Find closest enemy
        
        # Update position with separation and pursuit behaviors
        unit.update(target=target, enemy_position=closest_enemy_position, units=team2_units, separation_distance=1.0)

    # Clear the screen before drawing
    screen.fill(COLOR_EMPTY)

    # Draw all units with updated positions
    for unit in team1_units + team2_units:
        pygame.draw.circle(screen, unit.color, (int(unit.position[0] * CELL_SIZE), int(unit.position[1] * CELL_SIZE)), 20)  # Draw units as circles
    
    # Draw other components like the grid, elixir manager, and unit selector
    elixir_manager.draw(screen)
    grid.draw(screen)
    unit_selector.draw(screen)

    # Refresh the display
    pygame.display.flip()