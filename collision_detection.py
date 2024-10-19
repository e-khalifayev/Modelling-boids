# collision_detection.py

import numpy as np

def check_bullet_collisions(spatial_grid, unit_data, bullet_manager):
    """Check for collisions between bullets and units using spatial grid."""
    for cell_key, cell_contents in spatial_grid.grid.items():
        bullets = cell_contents.get('bullets', [])
        if not bullets:
            continue

        # Get units in the same and adjacent cells
        neighbor_cells = spatial_grid.get_adjacent_cells(cell_key) + [cell_key]
        unit_indices = []
        for n_cell in neighbor_cells:
            unit_indices.extend(spatial_grid.grid.get(n_cell, {}).get('units', []))
        if not unit_indices:
            continue

        # Prepare unit data
        unit_positions = unit_data.position[unit_indices]
        unit_radii = unit_data.radius[unit_indices]
        unit_teams = unit_data.team[unit_indices]

        # Prepare bullet data
        bullet_positions = np.array([bullet.position for bullet in bullets])
        bullet_teams = np.array([bullet.team for bullet in bullets])
        bullet_objects = bullets

        # Compute differences and distances
        diffs = unit_positions[:, np.newaxis, :] - bullet_positions[np.newaxis, :, :]
        distances = np.linalg.norm(diffs, axis=2)

        # Collision mask
        collision_mask = (distances <= unit_radii[:, np.newaxis]) & \
                         (unit_teams[:, np.newaxis] != bullet_teams[np.newaxis, :])

        # Handle collisions
        unit_indices_array, bullet_indices_array = np.nonzero(collision_mask)
        for u_idx, b_idx in zip(unit_indices_array, bullet_indices_array):
            unit_global_idx = unit_indices[u_idx]
            bullet = bullet_objects[b_idx]

            # Apply damage
            unit_data.health[unit_global_idx] -= bullet.damage

            # Remove bullet
            bullet_manager.remove_bullet(bullet)
