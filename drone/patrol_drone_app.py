import sys
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

import requests
import uvicorn
from domain.drone.PatrolDrone import (PatrolDrone, PatrolDroneEvent,
                                      PatrolDroneStatus)
from fastapi import APIRouter, BackgroundTasks, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# import config
sys.path.append(str(Path(__file__).resolve().parents[1]))
import config
from utils.Om2mRequestSender import Om2mRequestSender

om2m_request_sender = Om2mRequestSender()
drone_api_session = requests.Session()
track_drone_api_session = requests.Session()

drone_list = [
    {
        "app_name": "patrol_drone_1",
        "drone": PatrolDrone(
            "patrol_drone_1",
            config,
            om2m_request_sender,
            drone_api_session,
            track_drone_api_session,
        ),
        "patrol_trail": [
            [40, 50],
            [40, 10],
            [10, 10],
            [10, 90],
            [40, 90],
        ],
        "position": [50, 50],
    },
    {
        "app_name": "patrol_drone_2",
        "drone": PatrolDrone(
            "patrol_drone_2",
            config,
            om2m_request_sender,
            drone_api_session,
            track_drone_api_session,
        ),
        "patrol_trail": [
            [60, 50],
            [60, 90],
            [90, 90],
            [90, 10],
            [60, 10],
        ],
        "position": [50, 50],
    },
    {
        "app_name": "patrol_drone_3",
        "drone": PatrolDrone(
            "patrol_drone_3",
            config,
            om2m_request_sender,
            drone_api_session,
            track_drone_api_session,
        ),
        "patrol_trail": [
            [30, 50],
            [30, 90],
            [70, 90],
            [70, 10],
            [30, 10],
        ],
        "position": [50, 50],
    },
]


def drone_update():
    while True:
        # update position
        for index, drone in enumerate(drone_list):
            drone["drone"].update()
            drone["position"] = drone["drone"].get_position()

            # change it from float to int
            position = drone["position"]
            position[0] = int(position[0])
            position[1] = int(position[1])

            # send request to self api
            drone_api_session.put(
                f"{config.PATROL_DRONE_URL}/{index}/position",
                json={"position": position},
            )

        time.sleep(0.7)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Create thread for each drone
    """
    for drone in drone_list:
        app_name = drone["app_name"]
        # create mn data conatiner
        om2m_request_sender.create_application(
            f"{config.MN_URL}/~/mn-cse",
            app_name,
            {"Type": "patrol-drone", "Category": "drone"},
        )
        om2m_request_sender.create_container(
            f"{config.MN_URL}/~/mn-cse/mn-name", app_name, "status_container"
        )

        # subscribe status container for in server
        om2m_request_sender.subscribe(
            f"{config.MN_URL}/~/mn-cse/mn-name",
            app_name,
            "status_container",
            config.IN_APP_POA,
            "IN_STATUS_SUB",
        )

        drone["drone"].set_patrol_trail(drone["patrol_trail"])

    all_threads = []
    all_threads.append(
        threading.Thread(
            target=drone_update,
        )
    )

    for single_thread in all_threads:
        single_thread.daemon = True
        single_thread.start()

    yield


"""
Patrol drone API
"""
app = FastAPI(lifespan=lifespan)
api_router = APIRouter()

# CORS
origins = ["*"]


# data model
class Position(BaseModel):
    position: list


class Status(BaseModel):
    status: str


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@api_router.get("/{drone_index}/position")
def get_position(drone_index: int):
    return {"position": drone_list[drone_index]["position"]}


@api_router.put("/{drone_index}/position")
def update_position(drone_index: int, position: Position):
    position = position.model_dump()["position"]
    drone_list[drone_index]["position"] = position

    return {}


@api_router.put("/{drone_index}/status")
def update_status(drone_index: int, status: Status):
    status = status.model_dump()["status"]
    status_mapping = {
        "WAITING_FOR_COMMAND": PatrolDroneStatus.WAITING_FOR_COMMAND,
        "PATROLLING": PatrolDroneStatus.PATROLLING,
        "TRACKING": PatrolDroneStatus.TRACKING,
        "BACKING_TO_BASE": PatrolDroneStatus.BACKING_TO_BASE,
    }
    if status not in status_mapping:
        return {"msg": "status not found"}
    drone_list[drone_index]["drone"].set_status(status_mapping[status])

    return {}


@api_router.get("/{drone_index}/status")
def get_status(drone_index: int):
    return {"status": drone_list[drone_index]["drone"].get_status_as_string()}


app.include_router(api_router)

if __name__ == "__main__":
    all_threads = []
    all_threads.append(
        threading.Thread(
            target=uvicorn.run,
            kwargs={
                "app": "patrol_drone_app:app",
                "host": "0.0.0.0",
                "port": 8125,
                "reload": False,
                "workers": 1,
            },
        )
    )

    for single_thread in all_threads:
        single_thread.daemon = True
        single_thread.start()

    while True:
        time.sleep(1)

# uvicorn.run(app="patrol_drone_app:app", host="0.0.0.0", port=8125, reload=False, workers=1)
