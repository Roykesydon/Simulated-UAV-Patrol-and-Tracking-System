from copy import deepcopy


class SimulationMap:
    def __init__(self):
        self.MAP_SIZE = 100
        self.CORNER_SIZE = 30
        self.MAP_CENTER = [self.MAP_SIZE // 2, self.MAP_SIZE // 2]
        self._map_corners = [
            [0 + self.CORNER_SIZE // 2, 0 + self.CORNER_SIZE // 2],
            [0 + self.CORNER_SIZE // 2, self.MAP_SIZE - 1 - self.CORNER_SIZE // 2],
            [
                self.MAP_SIZE - 1 - self.CORNER_SIZE // 2,
                self.MAP_SIZE - 1 - self.CORNER_SIZE // 2,
            ],
            [self.MAP_SIZE - 1 - self.CORNER_SIZE // 2, 0 + self.CORNER_SIZE // 2],
        ]

    def get_map_center(self):
        return self.MAP_CENTER

    def get_map_size(self):
        return self.MAP_SIZE

    def get_corner_size(self):
        return self.CORNER_SIZE

    def get_map_corners(self):
        return deepcopy(self._map_corners)

    def stay_in_bounds(self, position):
        position[0] = max(0, min(position[0], self.MAP_SIZE - 1))
        position[1] = max(0, min(position[1], self.MAP_SIZE - 1))

        return position
