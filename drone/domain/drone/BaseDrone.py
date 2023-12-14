import time
from abc import ABC
from enum import Enum

from domain.SimulationMap import SimulationMap


class BaseDrone(ABC):
    def __init__(self) -> None:
        self.FLOAT_ERROR = 0.0001
        self._simulation_map = SimulationMap()
        # status
        self._status = None
        # moving
        self._speed = 5
        self._position = self._simulation_map.get_map_center()
        self._target_position = None
        # time
        self._last_update_time = time.time()

    def _float_position_equal(self, a, b):
        return (
            abs(a[0] - b[0]) < self.FLOAT_ERROR and abs(a[1] - b[1]) < self.FLOAT_ERROR
        )

    def move_to(self, x, y):
        time_elapsed = time.time() - self._last_update_time

        x_diff = x - self._position[0]
        y_diff = y - self._position[1]

        # print("--- move to ---")
        # print(f"old_position: {self._position}")
        # print(f"time_elapsed: {time.time() - self._last_update_time}")
        # print(f"speed: {self._speed}")
        # print(f"x_diff: {x_diff}")
        # print(f"y_diff: {y_diff}")

        min_xy_diff = min(abs(x_diff), abs(y_diff))

        if min_xy_diff < self.FLOAT_ERROR:
            min_xy_diff = 0
        if time_elapsed < self.FLOAT_ERROR:
            time_elapsed = 0

        # move diagonally
        new_position = self._position
        if time_elapsed * self._speed > min_xy_diff:
            time_elapsed -= abs(min_xy_diff) / self._speed
            new_position[0] += min_xy_diff * (-1 if x_diff < 0 else 1)
            new_position[1] += min_xy_diff * (-1 if y_diff < 0 else 1)
        else:
            new_position[0] += time_elapsed * self._speed * (-1 if x_diff < 0 else 1)
            new_position[1] += time_elapsed * self._speed * (-1 if y_diff < 0 else 1)
            time_elapsed = 0

        if abs(time_elapsed) < self.FLOAT_ERROR:
            time_elapsed = 0

        x_diff -= min_xy_diff * (-1 if x_diff < 0 else 1)
        y_diff -= min_xy_diff * (-1 if y_diff < 0 else 1)

        if time_elapsed == 0:
            self._position = self._simulation_map.stay_in_bounds(new_position)
            return

        # move horizontally or vertically
        if time_elapsed * self._speed > abs(x_diff):
            time_elapsed -= abs(x_diff) / self._speed
            new_position[0] = x
        else:
            new_position[0] += time_elapsed * self._speed * (-1 if x_diff < 0 else 1)
            time_elapsed = 0

        if abs(time_elapsed) < self.FLOAT_ERROR:
            time_elapsed = 0

        if time_elapsed * self._speed > abs(y_diff):
            time_elapsed -= abs(y_diff) / self._speed
            new_position[1] = y
        else:
            new_position[1] += time_elapsed * self._speed * (-1 if y_diff < 0 else 1)
            time_elapsed = 0

        self._position = self._simulation_map.stay_in_bounds(new_position)
        self._last_update_time = time.time()

    def get_status(self):
        return self._status

    def get_position(self):
        return self._position

    def update(self):
        raise NotImplementedError()
