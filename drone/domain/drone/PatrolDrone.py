import time
from enum import Enum

import requests
from domain.SimulationMap import SimulationMap

from .BaseDrone import BaseDrone


class PatrolDroneStatus(Enum):
    WAITING_FOR_COMMAND = 1
    BACKING_TO_BASE = 2
    PATROLLING = 3
    TRACKING = 4


class PatrolDroneEvent(Enum):
    FOUND_TARGET = 1
    START_PATROLLING = 2
    TARGET_LEFT = 3


class PatrolDrone(BaseDrone):
    def __init__(
        self,
        app_name,
        config,
        om2m_request_sender,
        drone_api_session,
        track_drone_api_session,
        mn_url,
    ) -> None:
        super().__init__()
        self._simulation_map = SimulationMap()
        # info
        self._app_name = app_name
        self._status = PatrolDroneStatus.WAITING_FOR_COMMAND
        # moving
        self._speed = 10
        self._position = self._simulation_map.get_map_center()
        self._target_position = None
        # time
        self._last_update_time = time.time()
        # patrol trail
        self._patrol_trail = []
        self._current_patrol_index = -1
        # detect
        self.DETECT_RADIUS = 15
        self._target_position_url = config.TARGET_POSITION_URL
        # utils
        self._config = config
        self._om2m_request_sender = om2m_request_sender
        self._human_session = requests.Session()
        # api
        self._drone_api_session = drone_api_session
        self._track_drone_api_session = track_drone_api_session
        self._mn_url = mn_url

    # Override
    def update(self):
        target_position = self._get_target_position()

        if self.get_status() == PatrolDroneStatus.WAITING_FOR_COMMAND:
            self._last_update_time = time.time()

        elif self.get_status() == PatrolDroneStatus.BACKING_TO_BASE:
            print(f"map center: {self._simulation_map.get_map_center()}")
            self.move_to(
                self._simulation_map.get_map_center()[0],
                self._simulation_map.get_map_center()[1],
            )
            if self._float_position_equal(
                self._position, self._simulation_map.get_map_center()
            ):
                self._current_patrol_index = 0
                self.set_status(PatrolDroneStatus.WAITING_FOR_COMMAND)

        elif self.get_status() == PatrolDroneStatus.PATROLLING:
            self.patrol()
            if self.detect_target(target_position):
                self.notify_server(PatrolDroneEvent.FOUND_TARGET)
                self.set_status(PatrolDroneStatus.TRACKING)

        elif self.get_status() == PatrolDroneStatus.TRACKING:
            if self._float_position_equal(target_position, [-100, -100]):
                self.set_status(PatrolDroneStatus.BACKING_TO_BASE)
                self.notify_server(PatrolDroneEvent.TARGET_LEFT)
            else:
                self.move_to(target_position[0], target_position[1])

    def notify_server(self, event):
        if event == PatrolDroneEvent.FOUND_TARGET:
            self._om2m_request_sender.create_content_instance(
                f"{self._mn_url}/~/mn-cse/mn-name",
                self._app_name,
                "event",
                {
                    "event": "FOUND_TARGET",
                    "app_name": self._app_name,
                },
            )
        elif event == PatrolDroneEvent.TARGET_LEFT:
            self._om2m_request_sender.create_content_instance(
                f"{self._mn_url}/~/mn-cse/mn-name",
                self._app_name,
                "event",
                {
                    "event": "TARGET_LEFT",
                    "app_name": self._app_name,
                },
            )

    def _get_target_position(self):
        response = self._human_session.get(self._target_position_url)
        if response.status_code == 200:
            return response.json()["position"]

        return None

    def detect_target(self, target_position):
        # if euclidean distance < DETECT_RADIUS, detect success
        # target_position = self._get_target_position()
        if target_position is not None:
            if (
                self._simulation_map.get_euclidean_distance(
                    self._position, target_position
                )
                < self.DETECT_RADIUS
            ):
                return True

        return False

    def patrol(self):
        if self._float_position_equal(
            self._position, self._patrol_trail[self._current_patrol_index]
        ):
            self._current_patrol_index = (self._current_patrol_index + 1) % len(
                self._patrol_trail
            )

        self.move_to(
            self._patrol_trail[self._current_patrol_index][0],
            self._patrol_trail[self._current_patrol_index][1],
        )

    """
    Getters and Setters
    """

    def get_status_as_string(self):
        if self._status == PatrolDroneStatus.WAITING_FOR_COMMAND:
            return "WAITING_FOR_COMMAND"
        elif self._status == PatrolDroneStatus.BACKING_TO_BASE:
            return "BACKING_TO_BASE"
        elif self._status == PatrolDroneStatus.PATROLLING:
            return "PATROLLING"
        elif self._status == PatrolDroneStatus.TRACKING:
            return "TRACKING"

    def get_status(self):
        return self._status

    def set_status(self, status):
        self._status = status

    def set_patrol_trail(self, patrol_trail):
        self._patrol_trail = patrol_trail
        self._current_patrol_index = 0
