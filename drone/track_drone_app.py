import sys
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

import requests
import uvicorn
import xmltodict
from domain.drone.TrackDrone import (TrackDrone, TrackDroneEvent,
                                     TrackDroneStatus)
from fastapi import APIRouter, BackgroundTasks, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# import config
sys.path.append(str(Path(__file__).resolve().parents[1]))
import config
from utils.Om2mRequestSender import Om2mRequestSender

om2m_request_sender = Om2mRequestSender()
drone_api_session = requests.Session()
patrol_drone_api_session = requests.Session()

drone_list = [
    {
        "app_name": "track_drone_1",
        "drone": TrackDrone(
            "track_drone_1",
            config,
            om2m_request_sender,
            drone_api_session,
            patrol_drone_api_session,
        ),
        "position": [50, 50],
    }
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

            # update data in mn resource tree
            om2m_request_sender.create_content_instance(
                f"{config.TRACK_DRONE_1_MN_URL}/~/mn-cse/mn-name",
                drone["app_name"],
                "info",
                {
                    "app_name": drone["app_name"],
                    "position": drone["position"],
                    "status": drone["drone"].get_status_as_string(),
                },
            )

        time.sleep(0.7)


def subscribe_in_control():
    time.sleep(5)
    for drone in drone_list:
        # subcribe in server for control container
        print(f"subcribe in server for control container of {drone['app_name']}")
        print(f"{config.TRACK_DRONE_URL_FROM_CONTAINER}/process_control")
        om2m_request_sender.subscribe(
            f"{config.IN_URL}/~/in-cse/in-name",
            drone["app_name"],
            "control",
            f"{config.TRACK_DRONE_URL_FROM_CONTAINER}/process_control",
            "MN_CONTROL_SUB",
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Create thread for each drone
    """
    for drone in drone_list:
        app_name = drone["app_name"]

        # create mn data conatiner
        om2m_request_sender.create_application(
            f"{config.TRACK_DRONE_1_MN_URL}/~/mn-cse",
            app_name,
            {"Type": "track-drone", "Category": "drone"},
        )
        om2m_request_sender.create_application(
            f"{config.IN_URL}/~/in-cse/in-name",
            app_name,
            {"Type": "track-drone", "Category": "drone"},
        )

        om2m_request_sender.create_container(
            f"{config.TRACK_DRONE_1_MN_URL}/~/mn-cse/mn-name", app_name, "info"
        )
        om2m_request_sender.create_container(
            f"{config.IN_URL}/~/in-cse/in-name", app_name, "info"
        )
        # subscribe info container for in server
        om2m_request_sender.subscribe(
            f"{config.TRACK_DRONE_1_MN_URL}/~/mn-cse/mn-name",
            app_name,
            "info",
            f"{config.IN_APP_POA}/process_info",
            "IN_INFO_SUB",
        )

        om2m_request_sender.create_container(
            f"{config.TRACK_DRONE_1_MN_URL}/~/mn-cse/mn-name", app_name, "event"
        )
        om2m_request_sender.create_container(
            f"{config.IN_URL}/~/in-cse/in-name", app_name, "event"
        )
        # subscribe event container for in server
        om2m_request_sender.subscribe(
            f"{config.TRACK_DRONE_1_MN_URL}/~/mn-cse/mn-name",
            app_name,
            "event",
            f"{config.IN_APP_POA}/process_event",
            "IN_EVENT_SUB",
        )

        om2m_request_sender.create_container(
            f"{config.TRACK_DRONE_1_MN_URL}/~/mn-cse/mn-name", app_name, "control"
        )
        om2m_request_sender.create_container(
            f"{config.IN_URL}/~/in-cse/in-name", app_name, "control"
        )

    thread_list = []
    thread_list.append(threading.Thread(target=drone_update))
    thread_list.append(threading.Thread(target=subscribe_in_control))

    for thread in thread_list:
        thread.daemon = True
        thread.start()

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


class FollowPatrolIndex(BaseModel):
    index: int


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def xml_to_dict(xml):
    xml = xmltodict.parse(xml)
    content = xml["m2m:sgn"]["nev"]["rep"]["m2m:cin"]["con"]
    content = xmltodict.parse(content)
    content = content["obj"]["str"]
    content = {item["@name"]: item["@val"] for item in content}
    return content


@api_router.put("/{drone_index}/follow_patrol_index")
def update_follow_patrol_index(
    drone_index: int, follow_patrol_index: FollowPatrolIndex
):
    index = follow_patrol_index.model_dump()["index"]
    drone_list[drone_index]["drone"].set_follow_patrol_index(index)

    return {}


@api_router.post("/process_control")
async def process_control(request: Request):
    content_type = request.headers["Content-Type"]
    if content_type == "application/xml":
        body = await request.body()

        try:
            content = xml_to_dict(body)

            app_name = content["app_name"]

            om2m_request_sender.create_content_instance(
                f"{config.TRACK_DRONE_1_MN_URL}/~/mn-cse/mn-name",
                app_name,
                "control",
                content,
            )

            if content["command"] == "SEARCHING":
                for index, drone in enumerate(drone_list):
                    if drone["app_name"] == app_name:
                        drone["drone"].set_follow_patrol_index(
                            content["follow_patrol_index"]
                        )
                        drone["drone"].set_status(TrackDroneStatus.SEARCHING)
                        break
            elif content["command"] == "BACKING_TO_BASE":
                for index, drone in enumerate(drone_list):
                    if drone["app_name"] == app_name:
                        drone["drone"].set_status(TrackDroneStatus.BACKING_TO_BASE)
                        break
        except Exception as e:
            print("process_control error")
            print(body)


@api_router.put("/{drone_index}/status")
def update_status(drone_index: int, status: Status):
    status = status.model_dump()["status"]
    status_mapping = {
        "WAITING_FOR_COMMAND": TrackDroneStatus.WAITING_FOR_COMMAND,
        "TRACKING": TrackDroneStatus.TRACKING,
        "SEARCHING": TrackDroneStatus.SEARCHING,
        "BACKING_TO_BASE": TrackDroneStatus.BACKING_TO_BASE,
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
    uvicorn_thread = threading.Thread(
        target=uvicorn.run,
        kwargs={
            "app": "track_drone_app:app",
            "host": "0.0.0.0",
            "port": 8126,
            "reload": False,
            "workers": 1,
        },
    )

    uvicorn_thread.daemon = True
    uvicorn_thread.start()

    while True:
        time.sleep(1)

# uvicorn.run(app="patrol_drone_app:app", host="0.0.0.0", port=8125, reload=False, workers=1)
