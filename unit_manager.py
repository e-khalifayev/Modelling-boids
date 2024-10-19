# unit_manager.py

import numpy as np
from constants import (
    SEPARATION_WEIGHT, ALIGNMENT_WEIGHT, COHESION_WEIGHT, PURSUIT_WEIGHT,
    GOAL_WEIGHT, SEPARATION_DISTANCE, RATE_OF_GAIN, DESTINATION1, DESTINATION2, UNIT_RADIUS, WINDOW_HEIGHT, WINDOW_WIDTH
)
from boid_behaviors import compute_separation_forces, compute_alignment_and_cohesion, compute_pursuit_forces

class UnitManager:
    """Manages unit updates and behaviors."""

    def __init__(self, unit_data):
        self.unit_data = unit_data

    def compute_boid_data(self, spatial_grid):
        """Compute boid data for each cell."""
        self.cell_boid_data = {}
        for cell_key, cell_contents in spatial_grid.grid.items():
            unit_indices = cell_contents.get('units', [])
            if not unit_indices:
                continue
            positions = self.unit_data.position[unit_indices]
            velocities = self.unit_data.velocity[unit_indices]
            count = len(unit_indices)

            alignment = np.mean(velocities, axis=0)
            cohesion_center = np.mean(positions, axis=0)

            self.cell_boid_data[cell_key] = {
                'alignment': alignment,
                'cohesion_center': cohesion_center
            }

    def update_units(self, dt, spatial_grid):
        """Update all units with vectorized boid behaviors."""
        active_indices = np.where(self.unit_data.active)[0]
        positions = self.unit_data.position[active_indices]
        velocities = self.unit_data.velocity[active_indices]
        teams = self.unit_data.team[active_indices]
        max_speeds = self.unit_data.speed[active_indices] * 5

        # Initialize steering forces
        separation_forces = np.zeros_like(positions)
        alignment_forces = np.zeros_like(positions)
        cohesion_forces = np.zeros_like(positions)
        pursuit_forces = np.zeros_like(positions)
        goal_forces = np.zeros_like(positions)

        # Prepare unit properties
        cooldowns = self.unit_data.cooldown[active_indices]
        attack_speeds = self.unit_data.attack_speed[active_indices]
        is_ranged = self.unit_data.is_ranged[active_indices]
        damage = self.unit_data.damage[active_indices]
        vision_ranges = self.unit_data.vision_range[active_indices]
        attack_ranges = self.unit_data.attack_range[active_indices]
        colors = self.unit_data.color[active_indices]
        radii = self.unit_data.radius[active_indices]

        # Initialize arrays for firing bullets
        fire_bullet_mask = np.zeros(len(active_indices), dtype=bool)
        fire_target_positions = np.zeros((len(active_indices), 2), dtype=np.float32)

        # Vectorized boid behaviors and attack logic
        for cell_key in spatial_grid.grid.keys():
            # Get units in the current cell and adjacent cells
            neighbor_cells = spatial_grid.get_adjacent_cells(cell_key) + [cell_key]
            neighbor_indices = []
            for n_cell in neighbor_cells:
                neighbor_indices.extend(spatial_grid.grid.get(n_cell, {}).get('units', []))

            # Map global indices to local indices
            cell_indices_in_active = np.nonzero(np.isin(active_indices, neighbor_indices))[0]
            if len(cell_indices_in_active) == 0:
                continue

            # Get unit data
            cell_positions = positions[cell_indices_in_active]
            cell_velocities = velocities[cell_indices_in_active]
            cell_teams = teams[cell_indices_in_active]
            cell_max_speeds = max_speeds[cell_indices_in_active]
            cell_cooldowns = cooldowns[cell_indices_in_active]
            cell_attack_speeds = attack_speeds[cell_indices_in_active]
            cell_is_ranged = is_ranged[cell_indices_in_active]
            cell_damage = damage[cell_indices_in_active]
            cell_vision_ranges = vision_ranges[cell_indices_in_active]
            cell_attack_ranges = attack_ranges[cell_indices_in_active]

            # Compute separation forces
            sep_forces = compute_separation_forces(
                cell_positions, cell_teams, SEPARATION_DISTANCE, SEPARATION_WEIGHT
            )
            separation_forces[cell_indices_in_active] += sep_forces

            # Compute alignment and cohesion forces
            boid_data = self.cell_boid_data.get(cell_key, {})
            align_forces, coh_forces = compute_alignment_and_cohesion(
                cell_positions, cell_velocities, boid_data,
                ALIGNMENT_WEIGHT, COHESION_WEIGHT, cell_max_speeds
            )
            alignment_forces[cell_indices_in_active] += align_forces
            cohesion_forces[cell_indices_in_active] += coh_forces

            # Compute pursuit forces and attack logic
            pur_forces, fire_mask, target_positions, updated_cooldowns = compute_pursuit_forces(
                cell_indices_in_active, active_indices, positions, velocities, teams,
                cell_positions, cell_teams, cell_velocities, cell_max_speeds,
                cell_cooldowns, cell_attack_speeds, cell_is_ranged, cell_damage,
                cell_vision_ranges, cell_attack_ranges, PURSUIT_WEIGHT, dt
            )
            pursuit_forces[cell_indices_in_active] += pur_forces
            fire_bullet_mask[cell_indices_in_active] |= fire_mask
            fire_target_positions[cell_indices_in_active] = target_positions
            cooldowns[cell_indices_in_active] = updated_cooldowns

        # Compute goal forces
        goal_forces = self.compute_goal_forces(positions, teams, max_speeds)

        # Update velocities
        total_forces = (separation_forces + alignment_forces +
                        cohesion_forces + pursuit_forces + goal_forces)
        total_weights = (SEPARATION_WEIGHT + ALIGNMENT_WEIGHT +
                         COHESION_WEIGHT + PURSUIT_WEIGHT + GOAL_WEIGHT)
        velocities += (total_forces / total_weights) * dt * RATE_OF_GAIN

        # Limit speed to max speed
        speeds = np.linalg.norm(velocities, axis=1)
        speed_mask = speeds > max_speeds
        velocities[speed_mask] = (velocities[speed_mask].T *
                                  (max_speeds[speed_mask] / speeds[speed_mask])).T

        # Update positions
        positions += velocities * dt

        # Update unit data
        self.unit_data.position[active_indices] = positions
        self.unit_data.velocity[active_indices] = velocities
        self.unit_data.cooldown[active_indices] = cooldowns

        # Handle firing bullets
        firing_units_indices = active_indices[fire_bullet_mask]
        for idx, target_pos in zip(firing_units_indices, fire_target_positions[fire_bullet_mask]):
            self.bullet_manager.add_bullet(
                position=self.unit_data.position[idx].copy(),
                velocity=(target_pos - self.unit_data.position[idx]).copy(),
                damage=self.unit_data.damage[idx],
                color=self.unit_data.color[idx],
                team=self.unit_data.team[idx],
                speed=100.0  # Adjust as needed
            )

    def compute_goal_forces(self, positions, teams, max_speeds):
        """Compute goal forces for units moving towards objectives."""
        desired_positions = np.where(teams[:, np.newaxis] == 1,
                                     DESTINATION1, DESTINATION2)
        desired = desired_positions - positions
        distances = np.linalg.norm(desired, axis=1, keepdims=True)
        with np.errstate(divide='ignore', invalid='ignore'):
            desired = np.divide(desired, distances, where=distances != 0)
            desired[~np.isfinite(desired)] = 0
        goal_forces = desired * max_speeds[:, np.newaxis] - self.unit_data.velocity[teams]
        return goal_forces * GOAL_WEIGHT
    
    def spawn_additional_units(self, original_unit_idx):
        """Spawn additional units in a circular formation around the original unit."""
        # Retrieve original unit attributes
        damage = self.unit_data.damage[original_unit_idx]
        health = self.unit_data.health[original_unit_idx]
        speed = self.unit_data.speed[original_unit_idx]
        team = self.unit_data.team[original_unit_idx]
        position = self.unit_data.position[original_unit_idx]
        is_ranged = self.unit_data.is_ranged[original_unit_idx]
        color = self.unit_data.color[original_unit_idx]
        radius = self.unit_data.radius[original_unit_idx]
        attack_range = self.unit_data.attack_range[original_unit_idx]
        vision_range = self.unit_data.vision_range[original_unit_idx]
        attack_speed = self.unit_data.attack_speed[original_unit_idx]

        # Calculate cost
        cost = damage + health + speed
        cost_deficit = 10 - cost
        if cost_deficit <= 0:
            return  # No additional units needed

        num_additional_units = int(cost_deficit)

        # Define the radius for the circular formation
        formation_radius = UNIT_RADIUS * 3  # Adjust as needed

        # Calculate angles for even distribution
        angles = np.linspace(0, 2 * np.pi, num_additional_units, endpoint=False)

        # Calculate positions for additional units
        additional_positions = position + formation_radius * np.stack((np.cos(angles), np.sin(angles)), axis=1)

        # Spawn additional units
        for pos in additional_positions:
            # Ensure additional units are within the game boundaries
            pos[0] = np.clip(pos[0], UNIT_RADIUS, WINDOW_WIDTH - UNIT_RADIUS)
            pos[1] = np.clip(pos[1], UNIT_RADIUS, WINDOW_HEIGHT - UNIT_RADIUS)

            # Add the unit
            idx = self.unit_data.add_unit(
                team=team,
                position=pos,
                velocity=np.zeros(2, dtype=np.float32),
                health=health,
                damage=damage,
                speed=speed,
                attack_range=attack_range,
                vision_range=vision_range,
                attack_speed=attack_speed,
                is_ranged=is_ranged,
                color=color,
                radius=radius
            )
