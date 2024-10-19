# boid_behaviors.py

import numpy as np
from constants import DESTINATION1, DESTINATION2, MAX_SPEED
import numpy as np

def compute_separation_forces(positions, teams, SEPARATION_DISTANCE, SEPARATION_WEIGHT):
    """Compute separation forces using vectorized operations."""
    diff = positions[:, np.newaxis, :] - positions[np.newaxis, :, :]
    distances = np.linalg.norm(diff, axis=2)
    separation_mask = (distances > 0) & (distances < SEPARATION_DISTANCE) & \
                      (teams[:, np.newaxis] == teams[np.newaxis, :])
    with np.errstate(divide='ignore', invalid='ignore'):
        normalized_diff = np.divide(diff, distances[:, :, np.newaxis], where=distances[:, :, np.newaxis] != 0)
        normalized_diff[~np.isfinite(normalized_diff)] = 0
    separation_vectors = np.sum(normalized_diff * separation_mask[:, :, np.newaxis], axis=1)
    return separation_vectors * SEPARATION_WEIGHT

def compute_alignment_and_cohesion(positions, velocities, boid_data,
                                   ALIGNMENT_WEIGHT, COHESION_WEIGHT, max_speeds):
    """Compute alignment and cohesion forces."""
    alignment = boid_data.get('alignment', np.zeros(2)) - velocities
    cohesion_center = boid_data.get('cohesion_center', np.mean(positions, axis=0))
    desired = cohesion_center - positions
    distances_to_cohesion = np.linalg.norm(desired, axis=1, keepdims=True)
    with np.errstate(divide='ignore', invalid='ignore'):
        desired = np.divide(desired, distances_to_cohesion, where=distances_to_cohesion != 0)
        desired[~np.isfinite(desired)] = 0
    cohesion = desired * max_speeds[:, np.newaxis] - velocities
    return alignment * ALIGNMENT_WEIGHT, cohesion * COHESION_WEIGHT

def compute_pursuit_forces(cell_indices_in_active, active_indices, positions, velocities, teams,
                           cell_positions, cell_teams, cell_velocities, cell_max_speeds,
                           cell_cooldowns, cell_attack_speeds, cell_is_ranged, cell_damage,
                           cell_vision_ranges, cell_attack_ranges, PURSUIT_WEIGHT, dt):
    """Compute pursuit forces and handle attack logic."""
    # Initialize arrays
    pursuit_forces = np.zeros_like(cell_positions)
    fire_bullet_mask = np.zeros(len(cell_positions), dtype=bool)
    fire_target_positions = np.zeros((len(cell_positions), 2), dtype=np.float32)
    updated_cooldowns = cell_cooldowns.copy()

    # Identify enemy units
    enemy_mask = teams[:, np.newaxis] != cell_teams[np.newaxis, :]
    enemy_positions = positions[enemy_mask.any(axis=1)]
    enemy_teams = teams[enemy_mask.any(axis=1)]

    if len(enemy_positions) == 0:
        return pursuit_forces, fire_bullet_mask, fire_target_positions, updated_cooldowns

    # Compute differences and distances to enemies
    diff = enemy_positions[np.newaxis, :, :] - cell_positions[:, np.newaxis, :]
    distances = np.linalg.norm(diff, axis=2)

    # Determine enemies within vision range
    within_vision = distances <= cell_vision_ranges[:, np.newaxis]
    has_enemy_in_vision = np.any(within_vision, axis=1)
    if not np.any(has_enemy_in_vision):
        return pursuit_forces, fire_bullet_mask, fire_target_positions, updated_cooldowns

    indices_in_cell = np.arange(len(cell_positions))[has_enemy_in_vision]

    # For units with enemies in vision, find the closest enemy
    enemy_distances = distances[has_enemy_in_vision]
    enemy_diffs = diff[has_enemy_in_vision]
    # Mask distances beyond vision range
    enemy_distances[~within_vision[has_enemy_in_vision]] = np.inf

    # Find the closest enemy for each unit
    closest_enemy_indices = np.argmin(enemy_distances, axis=1)
    closest_enemy_positions = enemy_positions[closest_enemy_indices]
    closest_enemy_diffs = enemy_diffs[np.arange(len(enemy_diffs)), closest_enemy_indices]

    # Compute pursuit forces
    desired = closest_enemy_positions - cell_positions[indices_in_cell]
    distances_to_enemy = np.linalg.norm(desired, axis=1, keepdims=True)
    with np.errstate(divide='ignore', invalid='ignore'):
        desired = np.divide(desired, distances_to_enemy, where=distances_to_enemy != 0)
        desired[~np.isfinite(desired)] = 0
    pursuit_vectors = desired * cell_max_speeds[indices_in_cell][:, np.newaxis] - cell_velocities[indices_in_cell]
    pursuit_forces[indices_in_cell] += pursuit_vectors * PURSUIT_WEIGHT

    # Attack logic
    attackable = distances_to_enemy.squeeze() <= cell_attack_ranges[indices_in_cell]
    ready_to_attack = (cell_cooldowns[indices_in_cell] <= 0) & attackable

    # Handle ranged units firing bullets
    ranged_units = cell_is_ranged[indices_in_cell] & ready_to_attack
    if np.any(ranged_units):
        ranged_indices = indices_in_cell[ranged_units]
        fire_bullet_mask[ranged_indices] = True
        fire_target_positions[ranged_indices] = closest_enemy_positions[ranged_units]

        # Reset cooldowns
        updated_cooldowns[ranged_indices] = 1 / cell_attack_speeds[ranged_indices]

        # Ranged units stop moving when attacking
        cell_velocities[ranged_indices] = 0

    return pursuit_forces, fire_bullet_mask, fire_target_positions, updated_cooldowns
