# main.py
import pygame
import sys
import random
import numpy as np
import time
from config import (WINDOW_WIDTH, WINDOW_HEIGHT, UNIT_RADIUS, COLOR_EMPTY, TARGET_POSITION1, TARGET_POSITION2, PLACEMENT_AREA_HEIGHT, SEPARATION_DISTANCE, FONT_COLOR)
from config import Singleton, UnitManager, BulletManager, Wall, WALLS
from units import Unit, Ranged_Unit
from bullets import Bullet
from user_interface import ElixirManager, UnitSelector, ClickDebouncer
from opponent import Opponent
from spatial_grid import SpatialGrid

pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Unit Movement and Combat without Grid")

# Initialize components
unit_selector = UnitSelector(WINDOW_WIDTH, WINDOW_HEIGHT)
elixir_manager = ElixirManager()
bullet_manager = BulletManager()
unit_manager = UnitManager()
click_debouncer = ClickDebouncer()

#initialize units, bullets
team1_units = unit_manager.team1_units
team2_units = unit_manager.team2_units

team1_bullets = bullet_manager.team1_bullets
team2_bullets = bullet_manager.team2_bullets

#initialize mappings for quick membership checks
team1_set = set(team1_units)
team2_set = set(team2_units)

all_units = team1_units + team2_units

# # Create some initial units for both teams with the appropriate team assignment
# for i in range(10):
#     unit = Unit(damage=random.randint(1,3), health=random.randint(1,3), speed=random.randint(1,3), team="team2")  # Add initial units for Team 2
#     unit.position = np.array([random.uniform(0, WINDOW_WIDTH), random.uniform(0, 200)])  # Random placement
#     team2_units.append(unit)

# # Adding an extra unit to Team 2 with specific parameters
# unit = Unit(damage=random.randint(1,3), health=random.randint(1,3), speed=random.randint(1,3), team="team2")
# unit.position = np.array([random.uniform(0, WINDOW_WIDTH), random.uniform(0, 200)])  # Random placement
# team2_units.append(unit)

# Integrate Opponent into the main game loop
opponent = Opponent(unit_manager)

# Initialize SpatialGrid
grid = SpatialGrid(WINDOW_WIDTH, WINDOW_HEIGHT, cell_size=50)

# Initialize clock
clock = pygame.time.Clock()


# Main game loop
while True:
    dt = clock.tick(60) / 1000.0  # 60 is desired FPS

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
                                                           team="team1")  # Assign to Team 1
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

    # Update SpatialGrid before processing units:
    grid.clear()
    for unit in all_units:
        grid.add(unit)

    # Update elixir
    elixir_manager.update_elixir()  # Increment elixir over time

    # Update opponent units
    opponent.update()

    # Shuffle the combined list of units from both teams
    all_units = team1_units + team2_units
    random.shuffle(all_units)

    # Update positions for both teams simultaneously
    for unit in all_units:
        if unit in team1_units:
            enemy_units = team2_units
            target_position = TARGET_POSITION2
        else:
            enemy_units = team1_units
            target_position = TARGET_POSITION1

        unit_pos = unit.position
        attack_range_sq = unit.attack_range ** 2
        vision_range_sq = unit.vision_range ** 2

        closest_enemy = None
        closest_enemy_distance_sq = float('inf')

        nearby_enemies = grid.get_nearby(unit_pos)
        for enemy in nearby_enemies:
            if enemy.team != unit.team:
                distance_sq = np.sum((unit_pos - enemy.position) ** 2)
                if distance_sq < closest_enemy_distance_sq:
                    closest_enemy_distance_sq = distance_sq
                    closest_enemy = enemy

        if closest_enemy and closest_enemy_distance_sq <= attack_range_sq:
            try:
                unit.attack(closest_enemy)
            except:
                pass
        else:
            if closest_enemy_distance_sq > vision_range_sq:
                unit.update(target_position, target_position, all_units, separation_distance=SEPARATION_DISTANCE, dt=dt)
            elif closest_enemy:
                unit.update(target_position, closest_enemy.position, all_units, separation_distance=SEPARATION_DISTANCE, dt=dt)


    # Clear the screen before drawing
    screen.fill(COLOR_EMPTY)

    # Draw all units from both teams
    for unit in all_units:
        pygame.draw.circle(screen, unit.color, (int(unit.position[0]), int(unit.position[1])), UNIT_RADIUS)
        pygame.draw.circle(screen, FONT_COLOR, (int(unit.position[0]), int(unit.position[1])), UNIT_RADIUS, 1)

    # Handle bullet movements, drawing, and collisions in one loop
    all_bullets = team1_bullets + team2_bullets
    random.shuffle(all_bullets)  # Shuffle to randomize processing order

    for bullet in all_bullets[:]:
        bullet.move(dt)  # Move the bullet
        bullet.draw(screen)  # Draw the bullet
        
        # Determine the set of target units dynamically to handle changes
        if bullet in team1_bullets:
            target_units = team2_units
        else:
            target_units = team1_units

        # Check for collisions with target units
        for unit in target_units[:]:  # Iterate over a copy to avoid modification during loop
            distance_sq = np.sum((bullet.position - unit.position) ** 2)
            if distance_sq < UNIT_RADIUS ** 2:
                unit.health -= bullet.damage
                if unit.health <= 0:
                    target_units.remove(unit)  # Remove the destroyed unit
                all_bullets.remove(bullet)  # Remove the bullet after a collision
                break  # Exit loop once a collision occurs

    # Check for collisions with walls
    for bullet in all_bullets[:]:
        for wall in WALLS:
            if wall.check_collision(bullet.position, bullet.radius):
                all_bullets.remove(bullet)  # Remove the bullet if it collides with a wall
                break

    # Draw additional UI components
    elixir_manager.draw(screen)  # Display current elixir level
    unit_selector.draw(screen)  # Draw unit selection interface

    # Refresh the display to update content
    pygame.display.flip()  # Update the screen with new content