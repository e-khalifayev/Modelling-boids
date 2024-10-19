# spatial_grid.py

class SpatialGrid:
    """Spatial grid for spatial partitioning."""

    def __init__(self, cell_size):
        self.cell_size = cell_size
        self.grid = {}

    def clear(self):
        self.grid.clear()

    def add_unit(self, idx, position):
        cell_key = self.get_cell_key(position)
        self.grid.setdefault(cell_key, {'units': [], 'bullets': []})
        self.grid[cell_key]['units'].append(idx)

    def add_bullet(self, bullet):
        cell_key = self.get_cell_key(bullet.position)
        self.grid.setdefault(cell_key, {'units': [], 'bullets': []})
        self.grid[cell_key]['bullets'].append(bullet)

    def get_adjacent_cells(self, cell_key):
        """Return list of adjacent cell keys."""
        x, y = cell_key
        adjacent_cells = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                adjacent_cells.append((x + dx, y + dy))
        return adjacent_cells

    def get_cell_key(self, position):
        cell_x = int(position[0] // self.cell_size)
        cell_y = int(position[1] // self.cell_size)
        return (cell_x, cell_y)
