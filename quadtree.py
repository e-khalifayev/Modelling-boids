# quadtree.py
import pygame
from constants import MAX_OBJECTS, MAX_LEVELS, UNIT_RADIUS

class QuadTree:
    """QuadTree data structure for spatial partitioning."""

    def __init__(self, level, bounds):
        self.level = level
        self.bounds = pygame.Rect(bounds)
        self.objects = []
        self.nodes = []

    def clear(self):
        """Clear the QuadTree."""
        self.objects = []
        for node in self.nodes:
            node.clear()
        self.nodes = []

    def split(self):
        """Split the node into four subnodes."""
        sub_width = self.bounds.width / 2
        sub_height = self.bounds.height / 2
        x = self.bounds.x
        y = self.bounds.y

        self.nodes = [
            QuadTree(self.level + 1, (x + sub_width, y, sub_width, sub_height)),  # Top-right
            QuadTree(self.level + 1, (x, y, sub_width, sub_height)),              # Top-left
            QuadTree(self.level + 1, (x, y + sub_height, sub_width, sub_height)),# Bottom-left
            QuadTree(self.level + 1, (x + sub_width, y + sub_height, sub_width, sub_height))  # Bottom-right
        ]

    def get_index(self, unit):
        """Determine which node the unit belongs to."""
        index = -1
        vertical_midpoint = self.bounds.x + (self.bounds.width / 2)
        horizontal_midpoint = self.bounds.y + (self.bounds.height / 2)

        in_top_quadrant = unit.position[1] < horizontal_midpoint
        in_bottom_quadrant = unit.position[1] >= horizontal_midpoint
        in_left_quadrant = unit.position[0] < vertical_midpoint
        in_right_quadrant = unit.position[0] >= vertical_midpoint

        if in_top_quadrant:
            if in_left_quadrant:
                index = 1  # Top-left
            elif in_right_quadrant:
                index = 0  # Top-right
        elif in_bottom_quadrant:
            if in_left_quadrant:
                index = 2  # Bottom-left
            elif in_right_quadrant:
                index = 3  # Bottom-right

        return index

    def insert(self, unit):
        """Insert a unit into the QuadTree."""
        if self.nodes:
            index = self.get_index(unit)
            if index != -1:
                self.nodes[index].insert(unit)
                return

        self.objects.append(unit)

        if len(self.objects) > MAX_OBJECTS and self.level < MAX_LEVELS:
            if not self.nodes:
                self.split()

            i = 0
            while i < len(self.objects):
                index = self.get_index(self.objects[i])
                if index != -1:
                    self.nodes[index].insert(self.objects.pop(i))
                else:
                    i += 1

    def retrieve(self, return_objects, unit):
        """Retrieve objects that could collide with the given unit."""
        index = self.get_index(unit)
        if index != -1 and self.nodes:
            self.nodes[index].retrieve(return_objects, unit)

        return_objects.extend(self.objects)
        return return_objects

    def find_node(self, unit):
        """Find the node where the unit is stored."""
        index = self.get_index(unit)
        if index != -1 and self.nodes:
            return self.nodes[index].find_node(unit)
        return self

    def query_range(self, range_rect, found=None):
        """Retrieve all units within a given rectangular range."""
        if found is None:
            found = []

        # If the range does not intersect this node's bounds, return
        if not self.bounds.colliderect(range_rect):
            return found

        # Check objects at this node
        for obj in self.objects:
            if range_rect.collidepoint(float(obj.position[0]), float(obj.position[1])):
                found.append(obj)

        # If there are subnodes, check them as well
        if self.nodes:
            for node in self.nodes:
                node.query_range(range_rect, found)

        return found

