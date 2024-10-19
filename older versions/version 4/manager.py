# manager.py
import pygame
from unit import Unit, RangedUnit
import numpy as np
from constants import UNIT_RADIUS, WINDOW_WIDTH, WINDOW_HEIGHT, PLAYER_MAX_HEALTH, OPPONENT_MAX_HEALTH

class UnitManager:
    """Manages all units in the game."""

    def __init__(self):
        self.all_units = pygame.sprite.Group()
        self.team1_units = pygame.sprite.Group()
        self.team2_units = pygame.sprite.Group()
        self.player_health = PLAYER_MAX_HEALTH  # Initialize player's health
        self.opponent_health = OPPONENT_MAX_HEALTH  # Initialize opponent's health

    def add_unit(self, unit):
        """Adds a unit to the appropriate team and overall unit list."""
        self.all_units.add(unit)
        if unit.team == "team1":
            self.team1_units.add(unit)
        else:
            self.team2_units.add(unit)

        # Handle multiplicity for original units (not additional)
        if not unit.is_additional and getattr(unit, 'cost', 0) < 10:
            self.spawn_additional_units(unit)

    def spawn_additional_units(self, original_unit):
        """Spawn additional units in a circular formation around the original unit."""
        cost_deficit = 10 - getattr(original_unit, 'cost', 0)
        if cost_deficit <= 0:
            return  # No additional units needed

        num_additional_units = cost_deficit

        # Define the radius for the circular formation
        formation_radius = UNIT_RADIUS * 3  # Adjust as needed

        # Calculate angles for even distribution
        angles = np.linspace(0, 2 * np.pi, num_additional_units, endpoint=False)

        # Calculate positions for additional units
        additional_positions = original_unit.position + formation_radius * np.stack((np.cos(angles), np.sin(angles)), axis=1)

        # Spawn additional units
        for pos in additional_positions:
            # Ensure additional units are within the game boundaries
            pos[0] = np.clip(pos[0], UNIT_RADIUS, WINDOW_WIDTH - UNIT_RADIUS)
            pos[1] = np.clip(pos[1], UNIT_RADIUS, WINDOW_HEIGHT - UNIT_RADIUS)

            # Choose the same type as the original unit
            if isinstance(original_unit, RangedUnit):
                additional_unit = RangedUnit(
                    damage=original_unit.damage,
                    health=original_unit.health,
                    speed=original_unit.speed,
                    team=original_unit.team,
                    is_additional=True
                )
            else:
                additional_unit = Unit(
                    damage=original_unit.damage,
                    health=original_unit.health,
                    speed=original_unit.speed,
                    team=original_unit.team,
                    is_additional=True
                )

            additional_unit.position = pos.copy()
            additional_unit.update_sprite_position()
            self.add_unit(additional_unit)

    def remove_unit(self, unit):
        """Removes a unit from both the global list and the specific team list."""
        self.all_units.remove(unit)
        if unit.team == "team1":
            self.team1_units.remove(unit)
        else:
            self.team2_units.remove(unit)

    def get_unit_by_id(self, unit_id: str):
        """Retrieve a unit by its unique ID."""
        for unit in self.all_units:
            if str(unit.id) == unit_id:
                return unit
        return None

    def get_team_units(self, team: str):
        """Return the units for the specified team."""
        if team == "team1":
            return self.team1_units
        elif team == "team2":
            return self.team2_units
        else:
            return pygame.sprite.Group()  # Return empty group for invalid team
