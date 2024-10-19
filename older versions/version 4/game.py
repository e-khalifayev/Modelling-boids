# game.py
import pygame
import sys
import numpy as np
from constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT, COLOR_EMPTY, FONT_COLOR, TOUCHDOWN_LINE_COLOR,
    MIDDLE_LINE_COLOR, TOUCHDOWN_LINE_OFFSET,
    SEPARATION_WEIGHT, ALIGNMENT_WEIGHT, COHESION_WEIGHT, PURSUIT_WEIGHT, GOAL_WEIGHT,
    VISION_RADIUS, UNIT_RADIUS, MAX_DENSITY, MAX_SPEED, SEPARATION_DISTANCE,
    DESTINATION1, DESTINATION2, RATE_OF_GAIN
)
from unit import Unit, RangedUnit
from bullet_manager import BulletManager
from manager import UnitManager
from user_interface import ElixirManager, UnitSelector, ClickDebouncer
from opponent import Opponent
from quadtree import QuadTree
from multiprocessing import Pool
import time

class Wall(pygame.sprite.Sprite):
    def __init__(self, rect):
        super().__init__()
        self.rect = rect
        self.image = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0))  # Invisible wall

class Game:
    """Main game class."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Unit Movement and Combat")

        self.clock = pygame.time.Clock()
        self.running = True

        # Initialize components
        self.unit_manager = UnitManager()
        self.bullet_manager = BulletManager()
        self.elixir_manager = ElixirManager()
        self.unit_selector = UnitSelector(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.click_debouncer = ClickDebouncer()
        self.opponent = Opponent(self.unit_manager)

        # QuadTree for spatial partitioning
        self.quadtree = QuadTree(0, (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))

        # Fonts
        self.font = pygame.font.Font(None, 36)

        # Initialize multiprocessing pool
        self.pool = Pool()

        # Game timer
        self.game_duration = 180  # 3 minutes in seconds
        self.start_time = time.time()

        # Initialize walls at the borders
        self.walls = pygame.sprite.Group()
        border_thickness = 1  # Thin walls
        top_wall = Wall(pygame.Rect(0, 0, WINDOW_WIDTH, border_thickness))
        bottom_wall = Wall(pygame.Rect(0, WINDOW_HEIGHT - border_thickness, WINDOW_WIDTH, border_thickness))
        left_wall = Wall(pygame.Rect(0, 0, border_thickness, WINDOW_HEIGHT))
        right_wall = Wall(pygame.Rect(WINDOW_WIDTH - border_thickness, 0, border_thickness, WINDOW_HEIGHT))
        self.walls.add(top_wall, bottom_wall, left_wall, right_wall)

    def handle_events(self):
        """Handle user input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.MOUSEBUTTONDOWN and self.click_debouncer.is_debounced():
                mouse_x, mouse_y = event.pos

                # Adjusted condition to spawn units in the bottom half (player's half)
                if WINDOW_HEIGHT / 2 < mouse_y < WINDOW_HEIGHT - 100:  # Player's half (bottom)
                    if self.unit_selector.selected_unit:
                        selected_unit = self.unit_selector.selected_unit
                        if self.elixir_manager.current_elixir >= selected_unit.cost:
                            # Spawn the selected unit
                            new_unit = type(selected_unit)(
                                damage=selected_unit.damage,
                                health=selected_unit.health,
                                speed=selected_unit.speed,
                                team="team1"
                            )
                            new_unit.position = np.array([mouse_x, mouse_y], dtype=np.float32)
                            new_unit.update_sprite_position()
                            self.unit_manager.add_unit(new_unit)
                            self.elixir_manager.current_elixir -= selected_unit.cost
                        else:
                            print("Not enough elixir to place this unit.")
                else:
                    # Handle unit selection if clicked in opponent's half
                    self.unit_selector.handle_mouse_click(event.pos)

    def process_touchdowns(self):
        """
        Check if any units have passed the touchdown lines and update health.
        """
        opponent_touchdown_y = TOUCHDOWN_LINE_OFFSET
        player_touchdown_y = WINDOW_HEIGHT - TOUCHDOWN_LINE_OFFSET

        # Process touchdowns for player units (team1) crossing the opponent's line
        for unit in list(self.unit_manager.team1_units):
            if unit.position[1] <= opponent_touchdown_y:
                damage = unit.damage
                self.unit_manager.opponent_health -= damage
                # print(f"Player scored a touchdown! Opponent health decreased by {damage}.")
                self.unit_manager.remove_unit(unit)

        # Process touchdowns for opponent units (team2) crossing the player's line
        for unit in list(self.unit_manager.team2_units):
            if unit.position[1] >= player_touchdown_y:
                damage = unit.damage
                self.unit_manager.player_health -= damage
                # print(f"Opponent scored a touchdown! Player health decreased by {damage}.")
                self.unit_manager.remove_unit(unit)

    def update_quadtree(self):
        """Rebuild the QuadTree with current unit positions."""
        self.quadtree.clear()
        for unit in self.unit_manager.all_units:
            self.quadtree.insert(unit)

    def find_unit_by_position(self, position, tolerance=5):
        """
        Find a unit based on its position within a certain tolerance.
        """
        for unit in self.unit_manager.all_units:
            if np.linalg.norm(unit.position - position) <= tolerance:
                return unit
        return None

    @staticmethod
    def update_unit_behavior(unit_data):
        """
        Update unit behavior with boid rules and pursuit logic.
        Collision-based damage is handled separately via groupcollide.
        Units will pursue enemies in vision range.
        """
        position = unit_data['position']
        velocity = unit_data['velocity']
        max_speed = unit_data['speed'] * 5
        health = unit_data['health']
        team = unit_data['team']
        damage = unit_data['damage']
        vision_range = unit_data['vision_range']  # For pursuit
        attack_range = unit_data['attack_range']  # For attacking
        cooldown = unit_data['cooldown']
        is_ranged = unit_data['is_ranged']
        nearby_units = unit_data['nearby_units']  # List of dicts (enemies and allies)
        dt = unit_data['dt']

        # Initialize steering vectors
        separation = np.zeros(2, dtype=np.float32)
        alignment = np.zeros(2, dtype=np.float32)
        cohesion = np.zeros(2, dtype=np.float32)
        pursuit = np.zeros(2, dtype=np.float32)
        goal = np.zeros(2, dtype=np.float32)
        count = 0

        # Decrease cooldown
        cooldown -= dt

        # Initialize firing variables
        fire_bullet = False
        fire_target_position = None

        # Pursuit logic: Look for the closest enemy within vision range
        closest_enemy = None
        closest_distance = float('inf')

        for u in nearby_units:
            if u['team'] != team:  # Enemy unit
                # Calculate the distance between this unit and the nearby enemy
                diff = u['position'] - position
                distance = np.linalg.norm(diff)

                # Check if the enemy is the closest one within vision range
                if distance < closest_distance and distance <= vision_range:
                    closest_enemy = u
                    closest_distance = distance

        if closest_enemy:
            diff = closest_enemy['position'] - position
            distance = np.linalg.norm(diff)
            if is_ranged:
                if distance <= attack_range:
                    # Enemy within attack range, attack
                    if cooldown <= 0:
                        fire_bullet = True
                        fire_target_position = closest_enemy['position']
                        cooldown = 1 / unit_data['attack_speed']
                    # Ranged unit stops moving when attacking
                    velocity = np.zeros(2, dtype=np.float32)
                else:
                    # Move towards the enemy
                    if distance > 0:
                        desired = (diff / distance) * max_speed
                        pursuit = desired - velocity
            else:
                # Melee units always move towards enemy
                if distance > 0:
                    desired = (diff / distance) * max_speed
                    pursuit = desired - velocity
        else:
            # Apply boid behaviors (separation, alignment, cohesion)
            for u in nearby_units:
                if u['team'] == team:  # Friendly units, apply boid rules
                    diff = position - u['position']
                    distance = np.linalg.norm(diff)
                    if 0 < distance < SEPARATION_DISTANCE:
                        separation += diff / distance

                    alignment += u['velocity']
                    cohesion += u['position']
                    count += 1

            if count > 0:
                alignment /= count
                alignment = alignment - velocity

                cohesion /= count
                desired = cohesion - position
                distance = np.linalg.norm(desired)
                if distance > 0:
                    desired = (desired / distance) * max_speed
                cohesion = desired - velocity

            # Move towards goals based on team
            if team == 'team1':
                desired = DESTINATION1 - position
            elif team == 'team2':
                desired = DESTINATION2 - position

            distance = np.linalg.norm(desired)
            if distance > 0:
                desired = (desired / distance) * max_speed
            goal = desired - velocity

        # Apply weights to steering forces
        separation *= SEPARATION_WEIGHT
        alignment *= ALIGNMENT_WEIGHT
        cohesion *= COHESION_WEIGHT
        pursuit *= PURSUIT_WEIGHT
        goal *= GOAL_WEIGHT

        TOTAL_WEIGHT = SEPARATION_WEIGHT + ALIGNMENT_WEIGHT + COHESION_WEIGHT + PURSUIT_WEIGHT + GOAL_WEIGHT

        # Update velocity based on steering forces
        velocity += (separation + alignment + cohesion + pursuit + goal)/TOTAL_WEIGHT * dt * RATE_OF_GAIN

        # Limit speed to max speed
        speed = np.linalg.norm(velocity)
        
        # Amortization
        if speed > max_speed:
            velocity = (velocity / speed) * max_speed

        # Store previous position
        previous_position = position.copy()

        # Update position
        position += velocity * dt

        # Prepare updated data
        updated_data = {
            'position': position,
            'velocity': velocity,
            'health': health,
            'team': team,
            'id': unit_data['id'],
            'cooldown': cooldown,
            'fire_bullet': fire_bullet,
            'fire_target_position': fire_target_position,
            'previous_position': previous_position,
        }

        return updated_data

    def update(self, dt: float):
        """Update game state."""
        self.elixir_manager.update_elixir()
        self.opponent.update()

        # Update QuadTree
        self.update_quadtree()

        # Prepare data for multiprocessing
        units = list(self.unit_manager.all_units)
        unit_data_list = []
        for unit in units:
            data = unit.get_data()

            # Define a rectangular range around the unit based on attack_range and vision_range
            max_range = max(data.get('attack_range', 0), data.get('vision_range', 0), VISION_RADIUS)
            range_rect = pygame.Rect(
                unit.position[0] - max_range,
                unit.position[1] - max_range,
                max_range * 2,
                max_range * 2
            )

            # Retrieve nearby units within the range_rect using QuadTree's query_range
            nearby_units = []
            self.quadtree.query_range(range_rect, nearby_units)

            # Exclude the unit itself from the nearby_units by comparing IDs
            nearby_data = [u.get_data() for u in nearby_units if u.id != unit.id]
            data['nearby_units'] = nearby_data
            data['dt'] = dt  # Pass delta time for updates
            unit_data_list.append(data)

            # # Debugging: Print number of nearby units
            # print(f"Unit {unit.id} has {len(nearby_units)} units within range.")

        # Multiprocessing
        try:
            # Use sequential processing for simplicity
            # updated_data_list = [Game.update_unit_behavior(data) for data in unit_data_list]
            updated_data_list = self.pool.map(Game.update_unit_behavior, unit_data_list)
        except Exception as e:
            print(f"Multiprocessing Error: {e}")
            self.running = False
            return

        # Update units with the new data
        for unit, updated_data in zip(units, updated_data_list):
            unit.set_data(updated_data)

            # # Remove units with negative or zero health
            # if unit.health <= 0:
            #     self.unit_manager.remove_unit(unit)
            #     # print(f"Unit {unit.id} removed due to negative health.")
            #     continue  # Skip further updates for this unit

            # Handle firing bullets
            if updated_data.get('fire_bullet'):
                # Create a bullet
                bullet = self.bullet_manager.bullet_pool.get_bullet(
                    position=unit.position.copy(),
                    velocity=(updated_data['fire_target_position'] - unit.position).copy(),
                    damage=unit.damage,
                    color=unit.color,
                    team=unit.team,
                    speed=100.0  # Define bullet speed as needed
                )
                self.bullet_manager.add_bullet(bullet)

            # After updating unit's position, check for collision with walls
            if pygame.sprite.spritecollide(unit, self.walls, False):
                # Collision occurred, reset position to previous position
                unit.position = updated_data['previous_position']
                unit.update_sprite_position()

        # Handle unit collisions using groupcollide
        team1_units = self.unit_manager.team1_units
        team2_units = self.unit_manager.team2_units

        # Detect collisions between team1 and team2 units
        unit_collisions = pygame.sprite.groupcollide(team1_units, team2_units, False, False)

        # Process each collision
        for unit1, units_hit in unit_collisions.items():
            for unit2 in units_hit:
                if unit1.team != unit2.team:
                    # Both units take damage
                    unit1.take_damage(unit2.damage)
                    unit2.take_damage(unit1.damage)
                    # print(f"Unit {unit1.id} collided with Unit {unit2.id}. Health updated.")

        # Handle bullet collisions
        bullet_hits = pygame.sprite.groupcollide(self.bullet_manager.all_bullets, self.unit_manager.all_units, False, False)
        for bullet, units_hit in bullet_hits.items():
            for unit in units_hit:
                if unit.team != bullet.team:
                    unit.take_damage(bullet.damage)
                    self.bullet_manager.remove_bullet(bullet)
                    # print(f"Bullet hit Unit {unit.id}. Bullet removed.")
                    break  # Bullet can hit only one unit

        # Update bullets
        self.bullet_manager.update(dt, self.screen.get_rect(), self.walls)

        # Check for touchdowns and other game events
        self.process_touchdowns()

        # Check for game over
        if self.unit_manager.player_health <= 0:
            print("Opponent wins!")
            self.running = False
        if self.unit_manager.opponent_health <= 0:
            print("Player wins!")
            self.running = False

        # Check for time up
        elapsed_time = time.time() - self.start_time
        remaining_time = self.game_duration - elapsed_time
        if remaining_time <= 0:
            # Decide winner based on health
            if self.unit_manager.player_health > self.unit_manager.opponent_health:
                print("Player wins!")
            elif self.unit_manager.player_health < self.unit_manager.opponent_health:
                print("Opponent wins!")
            else:
                print("It's a tie!")
            self.running = False

    def draw_touchdown_lines(self):
        """Draw touchdown lines for both players."""
        # Player's touchdown line (bottom of the screen)
        pygame.draw.line(
            self.screen, TOUCHDOWN_LINE_COLOR,
            (0, WINDOW_HEIGHT - TOUCHDOWN_LINE_OFFSET),
            (WINDOW_WIDTH, WINDOW_HEIGHT - TOUCHDOWN_LINE_OFFSET), 2
        )
        # Opponent's touchdown line (top of the screen)
        pygame.draw.line(
            self.screen, TOUCHDOWN_LINE_COLOR,
            (0, TOUCHDOWN_LINE_OFFSET),
            (WINDOW_WIDTH, TOUCHDOWN_LINE_OFFSET), 2
        )

    def draw_middle_line(self):
        """Draw the middle line to divide the battlefield."""
        middle_y = WINDOW_HEIGHT / 2
        pygame.draw.line(self.screen, MIDDLE_LINE_COLOR, (0, middle_y), (WINDOW_WIDTH, middle_y), 2)

    def render_health(self):
        """Render player and opponent health on the screen."""
        # Player Health
        player_health_text = self.font.render(f"Player Health: {self.unit_manager.player_health}", True, FONT_COLOR)
        self.screen.blit(player_health_text, (20, WINDOW_HEIGHT - 60))

        # Opponent Health
        opponent_health_text = self.font.render(f"Opponent Health: {self.unit_manager.opponent_health}", True, FONT_COLOR)
        self.screen.blit(opponent_health_text, (20, 20))

    def render_timer(self):
        """Render the remaining time on the screen."""
        elapsed_time = time.time() - self.start_time
        remaining_time = max(0, self.game_duration - elapsed_time)
        minutes = int(remaining_time // 60)
        seconds = int(remaining_time % 60)
        time_text = self.font.render(f"Time Left: {minutes:02d}:{seconds:02d}", True, FONT_COLOR)
        self.screen.blit(time_text, (WINDOW_WIDTH / 2 - time_text.get_width() / 2, 20))

    def render(self):
        """Draw everything on the screen."""
        self.screen.fill(COLOR_EMPTY)

        # Draw lines
        self.draw_middle_line()
        self.draw_touchdown_lines()

        # Draw units
        self.unit_manager.all_units.draw(self.screen)

        # Draw bullets
        self.bullet_manager.all_bullets.draw(self.screen)

        # Draw walls
        self.walls.draw(self.screen)

        # Draw UI components
        self.elixir_manager.draw(self.screen)
        self.unit_selector.draw(self.screen)
        self.render_health()
        self.render_timer()

        pygame.display.flip()

    def run(self):
        """Run the main game loop."""
        while self.running:
            dt = self.clock.tick(60) / 1000.0  # Delta time in seconds
            self.handle_events()
            self.update(dt)
            self.render()

        # Game Over Screen
        self.game_over_screen()

        # Close the multiprocessing pool
        self.pool.close()
        self.pool.join()

        pygame.quit()
        sys.exit()

    def game_over_screen(self):
        """Display the game over screen."""
        self.screen.fill(COLOR_EMPTY)
        game_over_font = pygame.font.Font(None, 72)
        if self.unit_manager.player_health <= 0:
            game_over_text = game_over_font.render("Opponent Wins!", True, (255, 0, 0))
        elif self.unit_manager.opponent_health <= 0:
            game_over_text = game_over_font.render("Player Wins!", True, (0, 255, 0))
        else:
            game_over_text = game_over_font.render("Game Over", True, FONT_COLOR)
        text_rect = game_over_text.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
        self.screen.blit(game_over_text, text_rect)
        pygame.display.flip()
        pygame.time.wait(3000)  # Wait for 3 seconds before closing
