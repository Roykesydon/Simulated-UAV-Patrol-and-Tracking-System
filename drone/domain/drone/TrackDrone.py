import time
from enum import Enum

import requests
from domain.SimulationMap import SimulationMap

from .BaseDrone import BaseDrone


class TrackDroneStatus(Enum):
    WAITING_FOR_COMMAND = 1
    BACKING_TO_BASE = 2
    SEARCHING = 3
    TRACKING = 4


class TrackDroneEvent(Enum):
    START_TRACKING = 1
    TARGET_LEFT = 2


class TrackDrone(BaseDrone):
    def __init__(
        self,
        app_name,
        config,
        om2m_request_sender,
        drone_api_session,
        patrol_drone_api_session,
    ) -> None:
        super().__init__()
        self._simulation_map = SimulationMap()
        # info
        self._app_name = app_name
        self._status = TrackDroneStatus.WAITING_FOR_COMMAND
        # moving
        self._speed = 10
        self._position = self._simulation_map.get_map_center()
        self._target_position = None
        # time
        self._last_update_time = time.time()
        # detect
        self.DETECT_RADIUS = 15
        self._target_position_url = config.TARGET_POSITION_URL
        self._follow_patrol_index = -1
        # utils
        self._config = config
        self._om2m_request_sender = om2m_request_sender
        self._human_session = requests.Session()
        # api
        self._drone_api_session = drone_api_session
        self._patrol_drone_api_session = patrol_drone_api_session

    # Override
    def update(self):
        target_position = self._get_target_position()

        if self.get_status() == TrackDroneStatus.WAITING_FOR_COMMAND:
            # do nothing
            self._last_update_time = time.time()

        elif self.get_status() == TrackDroneStatus.BACKING_TO_BASE:
            print(f"map center: {self._simulation_map.get_map_center()}")
            self.move_to(
                self._simulation_map.get_map_center()[0],
                self._simulation_map.get_map_center()[1],
            )
            if self._float_position_equal(
                self._position, self._simulation_map.get_map_center()
            ):
                self._current_patrol_index = 0
                self.set_status(TrackDroneStatus.WAITING_FOR_COMMAND)

        elif self.get_status() == TrackDroneStatus.SEARCHING:
            if self._follow_patrol_index == -1:
                print("need to set follow patrol index")
                return

            response = self._patrol_drone_api_session.get(
                f"{self._config.IN_APP_POA}/patrol_drone/{self._follow_patrol_index}/info"
            )
            if response.status_code == 200:
                if response.json()["status"] != "TRACKING":
                    print("follow drone is not tracking")
                    self.set_status(TrackDroneStatus.BACKING_TO_BASE)
                    return

            follow_patrol_drone_position = self._patrol_drone_api_session.get(
                f"{self._config.IN_APP_POA}/patrol_drone/{self._follow_patrol_index}/info"
            ).json()["position"]
            self.move_to(
                follow_patrol_drone_position[0], follow_patrol_drone_position[1]
            )

            if self.detect_target(target_position):
                self.set_status(TrackDroneStatus.TRACKING)
                self.notify_server(TrackDroneEvent.START_TRACKING)

        elif self.get_status() == TrackDroneStatus.TRACKING:
            if self._float_position_equal(target_position, [-100, -100]):
                print("target left")
                self.set_status(TrackDroneStatus.BACKING_TO_BASE)
                self.notify_server(TrackDroneEvent.TARGET_LEFT)
            else:
                self.move_to(target_position[0], target_position[1])

    def notify_server(self, event):
        if event == TrackDroneEvent.START_TRACKING:
            self._om2m_request_sender.create_content_instance(
                f"{self._config.TRACK_DRONE_1_MN_URL}/~/mn-cse/mn-name",
                self._app_name,
                "event",
                {
                    "event": "START_TRACKING",
                    "app_name": self._app_name,
                },
            )
        elif event == TrackDroneEvent.TARGET_LEFT:
            self._om2m_request_sender.create_content_instance(
                f"{self._config.TRACK_DRONE_1_MN_URL}/~/mn-cse/mn-name",
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

    """
    Getters and Setters
    """

    def get_status_as_string(self):
        if self._status == TrackDroneStatus.WAITING_FOR_COMMAND:
            return "WAITING_FOR_COMMAND"
        elif self._status == TrackDroneStatus.BACKING_TO_BASE:
            return "BACKING_TO_BASE"
        elif self._status == TrackDroneStatus.SEARCHING:
            return "SEARCHING"
        elif self._status == TrackDroneStatus.TRACKING:
            return "TRACKING"

    def set_follow_patrol_index(self, index):
        self._follow_patrol_index = int(index)

    def get_status(self):
        return self._status

    def set_status(self, status):
        self._status = status
