import random
from enum import Enum
from time import time

from .SimulationMap import SimulationMap


class HumanStatus(Enum):
    NORMAL = 1
    EXITING = 2
    INACTIVE = 3


class Human:
    def __init__(self):
        # randomly spawn at corner of map
        # map is 100x100 grid
        self.simulation_map = SimulationMap()
        self.ACTIVE_THRESHOLD = 30
        self.DISAPPEAR_THRESHOLD = 6
        self.NORMAL_SPEED = 4
        self.EXITING_SPEED = 2

        self.spawn()

    def spawn(self):
        map_corners = self.simulation_map.get_map_corners()
        self.position = random.choice(map_corners)
        self.update_time = int(time())
        self.target_position = None
        self.speed = self.NORMAL_SPEED
        self.status = HumanStatus.NORMAL
        self.appear_time = int(time())
        self.exit_time = None

    def _update_position(self, current_time: int) -> None:
        print(f"position: {self.position}")
        print(f"target_position: {self.target_position}")

        time_elapsed = current_time - self.update_time
        time_elapsed = time_elapsed % 60
        map_corners = self.simulation_map.get_map_corners()

        self.update_time = current_time

        if (
            self.status == HumanStatus.INACTIVE
            and self.exit_time is not None
            and current_time - self.exit_time > self.DISAPPEAR_THRESHOLD
        ):
            self.spawn()
            return

        if self.status == HumanStatus.INACTIVE:
            return

        # if human has appeared for more than ACTIVE_THRESHOLD seconds, exit as fast as possible
        self.status = (
            HumanStatus.NORMAL
            if int(time()) - self.appear_time < self.ACTIVE_THRESHOLD
            else HumanStatus.EXITING
        )
        if self.status == HumanStatus.EXITING:
            self.speed = self.EXITING_SPEED
            # go to closest border
            four_direction_to_border = [
                [0, self.position[1]],
                [self.position[0], 0],
                [self.simulation_map.get_map_size() - 1, self.position[1]],
                [self.position[0], self.simulation_map.get_map_size() - 1],
            ]
            closest_border = min(
                four_direction_to_border,
                key=lambda border: abs(border[0] - self.position[0])
                + abs(border[1] - self.position[1]),
            )
            self.target_position = closest_border

        if self.target_position is None or self.position == self.target_position:
            if self.status == HumanStatus.EXITING:
                self.exit_time = current_time
                self.status = HumanStatus.INACTIVE
                self.position = [-100, -100]
                return

            # get closest corner
            closest_corner = min(
                map_corners,
                key=lambda corner: abs(corner[0] - self.position[0])
                + abs(corner[1] - self.position[1]),
            )
            # randomly go to next clockwise or counter-clockwise corner
            clockwise = random.choice([True, False])
            index_diff = 1 if clockwise else -1

            new_target_position = map_corners[
                (map_corners.index(closest_corner) + index_diff + 4) % 4
            ]
            # make some random noise
            CORNER_SIZE = self.simulation_map.get_corner_size()
            new_target_position = [
                new_target_position[0]
                + random.randint(-(CORNER_SIZE // 2) + 5, CORNER_SIZE // 2 - 5),
                new_target_position[1]
                + random.randint(-(CORNER_SIZE // 2) + 5, CORNER_SIZE // 2 - 5),
            ]
            new_target_position = self.simulation_map.stay_in_bounds(
                new_target_position
            )

            self.target_position = new_target_position

        # move towards target position according to speed
        x_diff = self.target_position[0] - self.position[0]
        y_diff = self.target_position[1] - self.position[1]

        new_position = self.position
        if time_elapsed * self.speed > abs(x_diff):
            time_elapsed -= abs(x_diff) // self.speed
            new_position[0] = self.target_position[0]
        else:
            new_position[0] += time_elapsed * self.speed * (-1 if x_diff < 0 else 1)
            time_elapsed = 0

        if time_elapsed * self.speed > abs(y_diff):
            time_elapsed -= abs(y_diff) // self.speed
            new_position[1] = self.target_position[1]
        else:
            new_position[1] += time_elapsed * self.speed * (-1 if y_diff < 0 else 1)
            time_elapsed = 0

        self.position = self.simulation_map.stay_in_bounds(new_position)

    def get_position(self):
        # according to last update time, calculate new position
        self._update_position(int(time()))
        return self.position
