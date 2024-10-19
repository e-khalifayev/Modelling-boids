class SpatialGrid:
    def __init__(self, width, height, cell_size):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.cells = {}

    def _get_cell_coords(self, position):
        return (int(position[0] // self.cell_size), int(position[1] // self.cell_size))

    def clear(self):
        self.cells = {}

    def add(self, obj):
        cell_coords = self._get_cell_coords(obj.position)
        if cell_coords not in self.cells:
            self.cells[cell_coords] = []
        self.cells[cell_coords].append(obj)

    def get_nearby(self, position):
        cell_coords = self._get_cell_coords(position)
        nearby_objs = []
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                cell = (cell_coords[0] + dx, cell_coords[1] + dy)
                if cell in self.cells:
                    nearby_objs.extend(self.cells[cell])
        return nearby_objs