# game.py

import pygame
import sys
import time
import numpy as np
from constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT, COLOR_EMPTY, FONT_COLOR, TOUCHDOWN_LINE_COLOR,
    MIDDLE_LINE_COLOR, TOUCHDOWN_LINE_OFFSET, PLAYER_MAX_HEALTH, OPPONENT_MAX_HEALTH,
    CELL_SIZE, UNIT_RADIUS
)
from unit_data import UnitData
from unit_manager import UnitManager
from bullet_manager import BulletManager
from spatial_grid import SpatialGrid
from collision_detection import check_bullet_collisions
from opponent import Opponent
from user_interface import ElixirManager, UnitSelector, ClickDebouncer
from wall import Wall

class Game:
    """Main game class."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Unit Movement and Combat")

        self.clock = pygame.time.Clock()
        self.running = True

        # Initialize components
        self.unit_data = UnitData()
        self.unit_manager = UnitManager(self.unit_data)
        self.bullet_manager = BulletManager()
        self.spatial_grid = SpatialGrid(CELL_SIZE)
        self.elixir_manager = ElixirManager()
        self.unit_selector = UnitSelector()
        self.click_debouncer = ClickDebouncer()
        self.opponent = Opponent(self.unit_data)

        # Fonts
        self.font = pygame.font.Font(None, 36)

        # Game timer
        self.game_duration = 180  # 3 minutes in seconds
        self.start_time = time.time()

        # Initialize walls at the borders
        self.walls = pygame.sprite.Group()
        border_thickness = 1  # Thin walls
        top_wall = Wall(pygame.Rect(0, 0, WINDOW_WIDTH, border_thickness))
        bottom_wall = Wall(pygame.Rect(0, WINDOW_HEIGHT - border_thickness,
                                       WINDOW_WIDTH, border_thickness))
        left_wall = Wall(pygame.Rect(0, 0, border_thickness, WINDOW_HEIGHT))
        right_wall = Wall(pygame.Rect(WINDOW_WIDTH - border_thickness, 0,
                                      border_thickness, WINDOW_HEIGHT))
        self.walls.add(top_wall, bottom_wall, left_wall, right_wall)

        # Health
        self.player_health = PLAYER_MAX_HEALTH
        self.opponent_health = OPPONENT_MAX_HEALTH

    def handle_events(self):
        """Handle user input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.MOUSEBUTTONDOWN and self.click_debouncer.is_debounced():
                mouse_x, mouse_y = event.pos

                # Adjusted condition to spawn units in the bottom half (player's half)
                if WINDOW_HEIGHT / 2 < mouse_y < WINDOW_HEIGHT - 100:
                    if self.unit_selector.selected_unit:
                        selected_unit = self.unit_selector.selected_unit
                        if self.elixir_manager.current_elixir >= selected_unit['cost']:
                            # Spawn the selected unit
                            idx = self.unit_data.add_unit(
                                team=1,
                                position=np.array([mouse_x, mouse_y], dtype=np.float32),
                                velocity=np.zeros(2, dtype=np.float32),
                                health=selected_unit['health'],
                                damage=selected_unit['damage'],
                                speed=selected_unit['speed'],
                                attack_range=selected_unit['attack_range'],
                                vision_range=selected_unit['vision_range'],
                                attack_speed=selected_unit['attack_speed'],
                                is_ranged=selected_unit['is_ranged'],
                                color=selected_unit['color'],
                                radius=UNIT_RADIUS
                            )
                            self.elixir_manager.current_elixir -= selected_unit['cost']
                            # Spawn additional units
                            self.unit_manager.spawn_additional_units(idx)
                        else:
                            print("Not enough elixir to place this unit.")
                else:
                    # Handle unit selection if clicked in opponent's half
                    self.unit_selector.handle_mouse_click(event.pos)

    def process_touchdowns(self):
        """Check if any units have passed the touchdown lines and update health."""
        opponent_touchdown_y = TOUCHDOWN_LINE_OFFSET
        player_touchdown_y = WINDOW_HEIGHT - TOUCHDOWN_LINE_OFFSET

        active_indices = np.where(self.unit_data.active)[0]
        positions = self.unit_data.position[active_indices]
        teams = self.unit_data.team[active_indices]
        damages = self.unit_data.damage[active_indices]

        # Player units scoring touchdowns
        player_units = active_indices[(teams == 1) & (positions[:, 1] <= opponent_touchdown_y)]
        for idx in player_units:
            damage = damages[idx]
            self.opponent_health -= damage
            self.unit_data.remove_unit(idx)

        # Opponent units scoring touchdowns
        opponent_units = active_indices[(teams == 2) & (positions[:, 1] >= player_touchdown_y)]
        for idx in opponent_units:
            damage = damages[idx]
            self.player_health -= damage
            self.unit_data.remove_unit(idx)

    def update_spatial_grid(self):
        """Update the spatial grid with current unit positions and bullets."""
        self.spatial_grid.clear()
        active_indices = np.where(self.unit_data.active)[0]
        positions = self.unit_data.position[active_indices]

        for idx, pos in zip(active_indices, positions):
            self.spatial_grid.add_unit(idx, pos)

        for bullet in self.bullet_manager.bullets:
            self.spatial_grid.add_bullet(bullet)

    def update(self, dt: float):
        """Update game state."""
        self.elixir_manager.update_elixir()
        self.opponent.update()

        # Update Spatial Grid
        self.update_spatial_grid()

        # Compute Boid Data
        self.unit_manager.compute_boid_data(self.spatial_grid)

        # Update Units
        self.unit_manager.update_units(dt, self.spatial_grid)

        # Update Bullets
        self.bullet_manager.update(dt, self.screen.get_rect(), self.walls)

        # Check for bullet collisions
        check_bullet_collisions(self.spatial_grid, self.unit_data, self.bullet_manager)

        # Check for touchdowns and other game events
        self.process_touchdowns()

        # Remove dead units
        self.unit_data.remove_dead_units()

        # Check for game over
        if self.player_health <= 0:
            print("Opponent wins!")
            self.running = False
        if self.opponent_health <= 0:
            print("Player wins!")
            self.running = False

        # Check for time up
        elapsed_time = time.time() - self.start_time
        remaining_time = self.game_duration - elapsed_time
        if remaining_time <= 0:
            # Decide winner based on health
            if self.player_health > self.opponent_health:
                print("Player wins!")
            elif self.player_health < self.opponent_health:
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
        player_health_text = self.font.render(f"Player Health: {self.player_health}", True, FONT_COLOR)
        self.screen.blit(player_health_text, (20, WINDOW_HEIGHT - 60))

        # Opponent Health
        opponent_health_text = self.font.render(f"Opponent Health: {self.opponent_health}", True, FONT_COLOR)
        self.screen.blit(opponent_health_text, (20, 20))

    def render_timer(self):
        """Render the remaining time on the screen."""
        elapsed_time = time.time() - self.start_time
        remaining_time = max(0, self.game_duration - elapsed_time)
        minutes = int(remaining_time // 60)
        seconds = int(remaining_time % 60)
        time_text = self.font.render(f"Time Left: {minutes:02d}:{seconds:02d}", True, FONT_COLOR)
        self.screen.blit(time_text, (WINDOW_WIDTH / 2 - time_text.get_width() / 2, 20))

    def render_units(self):
        """Render units with Level of Detail (LOD)."""
        active_indices = np.where(self.unit_data.active)[0]
        positions = self.unit_data.position[active_indices]
        colors = self.unit_data.color[active_indices]
        radii = self.unit_data.radius[active_indices]

        camera_position = np.array([WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2])
        detail_distance = 200  # Units beyond this distance use simplified images

        for pos, color, radius in zip(positions, colors, radii):
            distance = np.linalg.norm(pos - camera_position)
            if distance < detail_distance:
                # Detailed rendering
                pygame.draw.circle(self.screen, color, (int(pos[0]), int(pos[1])), int(radius))
            else:
                # Simplified rendering
                pygame.draw.circle(self.screen, color, (int(pos[0]), int(pos[1])), int(radius / 2))

    def render(self):
        """Draw everything on the screen."""
        self.screen.fill(COLOR_EMPTY)

        # Draw lines
        self.draw_middle_line()
        self.draw_touchdown_lines()

        # Draw units
        self.render_units()

        # Draw bullets
        self.bullet_manager.render(self.screen)

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

        pygame.quit()
        sys.exit()

    def game_over_screen(self):
        """Display the game over screen."""
        self.screen.fill(COLOR_EMPTY)
        game_over_font = pygame.font.Font(None, 72)
        if self.player_health <= 0:
            game_over_text = game_over_font.render("Opponent Wins!", True, (255, 0, 0))
        elif self.opponent_health <= 0:
            game_over_text = game_over_font.render("Player Wins!", True, (0, 255, 0))
        else:
            game_over_text = game_over_font.render("Game Over", True, FONT_COLOR)
        text_rect = game_over_text.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
        self.screen.blit(game_over_text, text_rect)
        pygame.display.flip()
        pygame.time.wait(3000)  # Wait for 3 seconds before closing
