import pygame
import sys
import time
import numpy as np
import random

# Constants for window size and other game parameters
WINDOW_WIDTH = 900  # Example screen width
WINDOW_HEIGHT = 900  # Example screen height
UNIT_RADIUS = 10  # Size of the units
PLACEMENT_AREA_HEIGHT = WINDOW_HEIGHT - 100  # Area for placing units

# Define a target position
TARGET_POSITION1 = np.array([WINDOW_WIDTH / 2, WINDOW_HEIGHT * 1])
TARGET_POSITION2 = np.array([WINDOW_WIDTH / 2, WINDOW_HEIGHT * 0])

# Colors for drawing
COLOR_EMPTY = (0, 0, 0)  # Background color
FONT_COLOR = np.array([255, 255, 255]) - COLOR_EMPTY

SEPARATION_DISTANCE = 20

# Define the unit class
class Unit:
    def __init__(self, damage, health, speed, team):
        self.damage = damage
        self.health = health
        self.speed = speed
        self.max_speed = speed / 4 # Maximum speed for this unit
        self.attack_speed = speed
        self.cooldown = (int(60/speed) if speed > 0 else 100)
        self.attack_range = 20
        self.vision_range = 200
        self.position = np.array([0.0, 0.0], dtype=float)  # Starting position
        self.velocity = np.array([0.0, 0.0], dtype=float)  # Starting velocity
        self.color = self.compute_color()  # Calculate color based on stats
        self.cost = damage + health + speed
        self.radius = 10
        self.team = team

    def compute_color(self):
        """Compute RGB color based on damage, speed, and health."""
        r = min(int((self.damage / 10) * 255), 255)  # Normalize to 0-255
        g = min(int((self.speed / 10) * 255), 255)  # Normalize to 0-255
        b = min(int((self.health / 10) * 255), 255)  # Normalize to 0-255
        return (r, g, b)  # Return RGB tuple representing the color

    def __str__(self):
        return f"Unit(Damage={self.damage}, Health={self.health}, Speed={self.speed}, Color={self.color})"

    def move_towards(self, target):
        """Move towards a given target position."""
        direction = target - self.position  # Direction vector
        if np.linalg.norm(direction) > 0:  # Avoid division by zero
            direction /= np.linalg.norm(direction)  # Normalize
            direction *= self.max_speed
        return direction.astype(float)  # Return normalized and scaled velocity

    def pursue_enemy(self, enemy_position):
        """Pursue a given enemy's position."""
        return self.move_towards(enemy_position)

    def separation_and_collision_avoidance(self, units, separation_distance):
        """Avoid collisions with other units using a separation distance."""
        steering = np.zeros_like(self.position)  # Initialize a zero vector
        for other_unit in units + walls: # handle collisions with both units and walls
            if other_unit != self or isinstance(other_unit, Wall):
                distance = np.linalg.norm(self.position - other_unit.position)
                if distance < separation_distance:
                    diff = (self.position - other_unit.position)
                    diff /= distance  # Normalize and weight by distance
                    steering += diff  # Add to steering for collision avoidance
        return steering

    def update(self, target, enemy_position, units, separation_distance):
        """Update unit velocity and position based on behaviors."""
        # Weights for cohesion, pursuit, and separation
        cohesion_weight = 0.05
        pursuit_weight = 0.7
        separation_weight = 0.25
        
        # Compute desired velocities for different behaviors
        cohesion = self.move_towards(target) * cohesion_weight
        pursuit = self.pursue_enemy(enemy_position) * pursuit_weight
        separation = self.separation_and_collision_avoidance(units, separation_distance)/np.sqrt(len(units)) * separation_weight
        
        # Combine behaviors to determine desired velocity
        desired_velocity = cohesion + pursuit + separation
        self.velocity = np.clip(desired_velocity, -self.max_speed, self.max_speed)  # Limit to max speed
        self.position += self.velocity  # Update position with the resulting velocity

        # Decrease cooldown
        self.cooldown = max(0, self.cooldown - 1)

    # Add a method to the Unit class to handle attacks
    def attack(self, target_unit):
        """Attack a target unit."""
        if self.cooldown == 0:
            target_unit.health -= self.damage  # Reduce the target's health based on attacker's attack power
            if target_unit.health <= 0:
                # Remove the target unit if its health drops to zero or below
                if target_unit.team == "team1":
                    team1_units.remove(target_unit)
                elif target_unit.team == "team2":
                    team2_units.remove(target_unit)
            if self.attack_speed > 0:
                self.cooldown = int(60/self.attack_speed)


class Bullet:
    def __init__(self, position, velocity, damage, color, team):
        self.position = position.copy()
        self.velocity = velocity.copy()
        self.damage = damage
        self.color = color
        self.radius = damage  # Radius of the bullet
        self.team = team

    def move(self):
        """Move the bullet according to its velocity."""
        self.position += self.velocity

    def draw(self, surface):
        """Draw the bullet on the screen."""
        pygame.draw.circle(surface, self.color, (int(self.position[0]), int(self.position[1])), self.radius)
        pygame.draw.circle(surface, FONT_COLOR, (int(self.position[0]), int(self.position[1])), self.radius, 1)


class Ranged_Unit(Unit):
    def __init__(self, damage, health, speed, team):
        super().__init__(damage, health, speed, team)
        self.is_attacking = False
        self.attack_range = self.attack_range + 200

    def attack(self, target_unit):
        if self.cooldown == 0:
            self.is_attacking = True
            bullet_velocity = target_unit.position - self.position
            bullet_velocity /= np.linalg.norm(bullet_velocity)
            bullet_velocity *= self.attack_speed
            
            # Create bullet with correct team
            bullet = Bullet(position=self.position,
                            velocity=bullet_velocity,
                            damage=self.damage,
                            color=self.color,
                            team=self.team) # Team affiliation of the bullet
            
            # Add bullet to the correct list based on the unit's team
            if self.team == "team1":
                team1_bullets.append(bullet)
            else:
                team2_bullets.append(bullet)
            
            if self.attack_speed > 0:
                self.cooldown = int(60 / self.attack_speed)

            # Send attack to cooldown
            if self.attack_speed > 0:
                self.cooldown = int(60 / self.attack_speed)
        else:
            self.cooldown = max(0, self.cooldown - 1)


    # def update(self, target, enemy_position, units, separation_distance):
    #     if not self.is_attacking:
    #         super().update(target, enemy_position, units, separation_distance)
    #     else:
    #         # Stop attacking if the target is out of range or dead
    #         target_distance = np.linalg.norm(target - self.position)
    #         if target_distance > self.attack_range:
    #             self.stop_attack()

    #         # Decrease cooldown
    #         self.cooldown = max(0, self.cooldown - 1)

    # def stop_attack(self):
    #     """Stop the unit from attacking."""
    #     self.is_attacking = False


# ElixirManager, ClickDebouncer, and other components
class ElixirManager:
    def __init__(self):
        self.current_elixir = 5
        self.last_update_time = time.time()

    def update_elixir(self):
        now = time.time()
        if now - self.last_update_time >= 1:
            self.current_elixir = min(self.current_elixir + 1, 10)
            self.last_update_time = now  # Reset the update time

    def draw(self, screen):
        font = pygame.font.Font(None, 36)
        elixir_text = font.render(f"Elixir: {self.current_elixir}", True, FONT_COLOR)
        screen.blit(elixir_text, (WINDOW_WIDTH - 150, WINDOW_HEIGHT - 120))


class UnitSelector:
    def __init__(self, window_width, window_height):
        self.window_width = window_width
        self.window_height = window_height
        self.selected_unit = None  # The currently selected unit
        self.buttons = []  # List of buttons for unit selection
        self.init_buttons()  # Initialize the unit buttons

    def init_buttons(self):
        """Initialize unit selection buttons with units and adaptive positions."""
        # Define some sample units
        unit1 = Unit(damage=1, health=1, speed=1, team="team1")
        unit2 = Ranged_Unit(damage=6, health=1, speed=1, team="team1")
        unit3 = Unit(damage=0, health=3, speed=0, team="team1")
        unit4 = Unit(damage=2, health=1, speed=2, team="team2")
        unit5 = Unit(damage=1, health=2, speed=1, team="team2")

        # Adaptive button layout parameters
        button_width = self.window_width * 0.1  # Roughly 10% of window width
        button_height = self.window_height * 0.05  # Roughly 5% of window height
        button_spacing = self.window_width * 0.025  # Roughly 2.5% spacing
        start_x = self.window_width * 0.05  # Start at 5% of the window width
        
        # Height placement for the buttons, just above the placement area
        start_y = self.window_height - 75  # Placed just above the placement area
        
        # Set up buttons with dynamic positioning
        self.buttons = [
            {
                "unit": unit1,
                "pos": (start_x, start_y),  # Position for the first button
                "label": str(unit1.cost)
            },
            {
                "unit": unit2,
                "pos": (start_x + button_width + button_spacing, start_y),  # Second button position
                "label": str(unit2.cost)
            },
            {
                "unit": unit3,
                "pos": (start_x + 2 * (button_width + button_spacing), start_y),  # Third button position
                "label": str(unit3.cost)
            },
            {
                "unit": unit4,
                "pos": (start_x + 3 * (button_width + button_spacing), start_y),  # Third button position
                "label": str(unit3.cost)
            },
            {
                "unit": unit5,
                "pos": (start_x + 4 * (button_width + button_spacing), start_y),  # Third button position
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


# Initialize pygame and other components
pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Unit Movement and Combat without Grid")

# Initialize key components
unit_selector = UnitSelector(WINDOW_WIDTH, WINDOW_HEIGHT)  # Selector for choosing units to place
elixir_manager = ElixirManager()  # Manager for elixir
click_debouncer = ClickDebouncer()  # Debouncer to prevent double-clicking

# Calculate FPS
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)

class Wall:
    def __init__(self, position, size):
        self.position = np.array(position)
        self.size = np.array(size)

    def check_collision(self, object_position, object_radius):
        # Check if the object collides with the wall
        # For simplicity, let's assume the object is a circle (unit or bullet)
        # Check if any part of the circle is inside the rectangle of the wall
        closest_point_x = max(self.position[0], min(object_position[0], self.position[0] + self.size[0]))
        closest_point_y = max(self.position[1], min(object_position[1], self.position[1] + self.size[1]))
        distance = np.linalg.norm(np.array([closest_point_x, closest_point_y]) - object_position)
        return distance < object_radius
    

wall_thickness = 50
walls = [
    Wall((0, 0), (WINDOW_WIDTH, wall_thickness)),                               # Top wall
    Wall((0, 0), (wall_thickness, WINDOW_HEIGHT)),                              # Left wall
    Wall((0, WINDOW_HEIGHT - wall_thickness), (WINDOW_WIDTH, wall_thickness)),  # Bottom wall
    Wall((WINDOW_WIDTH - wall_thickness, 0), (wall_thickness, WINDOW_HEIGHT))   # Right wall
]


# Lists to store units
team1_units = []
team2_units = []

# Create some initial units for both teams with the appropriate team assignment
for i in range(20):
    unit = Unit(damage=random.randint(1,3), health=random.randint(1,3), speed=random.randint(1,3), team="team2")  # Add initial units for Team 2
    unit.position = np.array([random.uniform(0, WINDOW_WIDTH), random.uniform(0, 200)])  # Random placement
    team2_units.append(unit)

# Adding an extra unit to Team 2 with specific parameters
unit = Unit(damage=random.randint(1,3), health=random.randint(1,3), speed=random.randint(1,3), team="team2")
unit.position = np.array([random.uniform(0, WINDOW_WIDTH), random.uniform(0, 200)])  # Random placement
team2_units.append(unit)

# Separate lists for bullets from each team
team1_bullets = []
team2_bullets = []

# Main game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:  # Exit if the user quits
            pygame.quit()
            sys.exit()

        # Inside the main game loop
        if event.type == pygame.MOUSEBUTTONDOWN and click_debouncer.is_debounced():
            # If a click occurred within the placement area
            if event.pos[1] < PLACEMENT_AREA_HEIGHT:
                if unit_selector.selected_unit:
                    selected_unit = unit_selector.selected_unit
                    if elixir_manager.current_elixir >= selected_unit.cost:  # Check if there's enough elixir
                        if selected_unit.cost < 10:
                            num_units_to_spawn = 10 - selected_unit.cost + 1
                            for _ in range(num_units_to_spawn):
                                if isinstance(selected_unit, Ranged_Unit):
                                    new_unit = Ranged_Unit(damage=selected_unit.damage,
                                                        health=selected_unit.health,
                                                        speed=selected_unit.speed,
                                                        team="team1")  # Assign to Team 1)
                                else:
                                    new_unit = Unit(damage=selected_unit.damage,
                                                    health=selected_unit.health,
                                                    speed=selected_unit.speed,
                                                    team="team1")  # Assign to Team 1
                                offset = np.random.uniform(-20, 20, size=(2,))
                                new_unit.position = np.array(event.pos, dtype=float) + offset  # Positioning the new unit
                                team1_units.append(new_unit)  # Add to Team 1
                            elixir_manager.current_elixir -= selected_unit.cost  # Deduct the cost

                    else:
                        print("Not enough elixir to place this unit.")

            else:  # Click within the unit selector area
                unit_selector.handle_mouse_click(event.pos)  # Handle unit selection

    # Update elixir
    elixir_manager.update_elixir()  # Increment elixir over time

    # Shuffle the combined list of units from both teams
    all_units = team1_units + team2_units
    random.shuffle(all_units)

    # Update positions for both teams simultaneously
    for unit in all_units:
        # Determine enemy units based on team affiliation
        enemy_units = team2_units if unit in team1_units else team1_units
        TARGET_POSITION = TARGET_POSITION2 if unit in team1_units else TARGET_POSITION1

        # Check if there are nearby enemy units within vision range
        closest_enemy = None
        closest_enemy_distance = float('inf')

        for enemy in enemy_units:
            distance = np.linalg.norm(unit.position - enemy.position)
            if distance < closest_enemy_distance:
                closest_enemy_distance = distance
                closest_enemy = enemy

        if closest_enemy and closest_enemy_distance <= unit.attack_range:
            # If an enemy is within attack range, attack it
            unit.attack(closest_enemy)
        else:
            # If no enemies are within vision range, move towards the target position
            if closest_enemy_distance > unit.vision_range:
                unit.update(TARGET_POSITION, TARGET_POSITION, all_units, separation_distance=SEPARATION_DISTANCE)
            elif closest_enemy:
                # If an enemy is within vision range but not attack range, move towards it
                unit.update(TARGET_POSITION, closest_enemy.position, all_units, separation_distance=SEPARATION_DISTANCE)

    # Clear the screen before drawing
    screen.fill(COLOR_EMPTY)

    # Draw all units from both teams
    for unit in team1_units + team2_units:
        # pygame.draw.rect(screen, unit.color, pygame.Rect(int(unit.position[0]), int(unit.position[1]), 10, 10), width=UNIT_RADIUS)
        pygame.draw.circle(screen, unit.color, (int(unit.position[0]), int(unit.position[1])), 10)
        pygame.draw.circle(screen, FONT_COLOR, (int(unit.position[0]), int(unit.position[1])), 10, 1)



    all_bullets = team1_bullets + team2_bullets
    random.shuffle(all_bullets)
    # Move and draw bullets from both teams
    for bullet in all_bullets:
        bullet.move()
        bullet.draw(screen)

    # Check for collisions between bullets and units
    for bullet in team1_bullets[:]:  # Use a copy of the list to avoid modifying it during iteration
        for unit in team2_units:
            distance = np.linalg.norm(bullet.position - unit.position)
            if distance < unit.radius:  # Bullet collides with a unit from Team 2
                unit.health -= bullet.damage  # Apply bullet damage to the unit
                team1_bullets.remove(bullet)  # Remove the bullet after collision
                if unit.health <= 0:
                    team2_units.remove(unit)  # Remove the destroyed unit from Team 2
                break  # No need to check further if a collision occurs

    for bullet in team2_bullets[:]:  # Use a copy of the list to avoid modifying it during iteration
        for unit in team1_units:
            distance = np.linalg.norm(bullet.position - unit.position)
            if distance < unit.radius:  # Bullet collides with a unit from Team 1
                unit.health -= bullet.damage  # Apply bullet damage to the unit
                team2_bullets.remove(bullet)  # Remove the bullet after collision
                if unit.health <= 0:
                    team1_units.remove(unit)  # Remove the destroyed unit from Team 1
                break  # No need to check further if a collision occurs
        
    # Check for collisions between bullets and units and walls
    for bullet in all_bullets[:]:
        for wall in walls:
            if wall.check_collision(bullet.position, bullet.radius):
                all_bullets.remove(bullet)  # Remove the bullet upon collision with the wall
                break

        for unit in all_units:
            if np.linalg.norm(unit.position - bullet.position) < unit.radius:
                all_bullets.remove(bullet)  # Remove the bullet upon collision with a unit
                break


    # Draw additional UI components like elixir manager and unit selector
    elixir_manager.draw(screen)  # Display current elixir
    unit_selector.draw(screen)  # Draw unit selection buttons

    # Calculate FPS and add to screen
    fps = clock.get_fps()  # Get the current frame rate
    fps_text = font.render(f"FPS: {int(fps)}", True, (255, 255, 255))  # Black text
    screen.blit(fps_text, (10, 10))  # Draw the FPS in the top-left corner

    # Refresh the display
    pygame.display.flip()  # Update the screen to display new content
    
    clock.tick(60)  # Cap the frame rate at 60 FPS to maintain consistency


### Multiplicity (DONE)
### Introduce range and bullets (DONE)
### Introduce attack speed equal to the speed (DONE)

### First game mode: Royal (DONE)

### WALLS (DONE)
### Bring balance
### Bot
### Multiplayer?
### FPS Counter
### Partition
### Optimization
### Softer anti-collision
### Hardware acceleration