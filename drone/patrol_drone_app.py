import sys
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

import requests
import uvicorn
import xmltodict
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
            config.PATROL_DRONE_1_MN_URL,
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
            config.PATROL_DRONE_2_MN_URL,
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
            config.PATROL_DRONE_3_MN_URL,
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

            URL_MAP = {
                0: config.PATROL_DRONE_1_MN_URL,
                1: config.PATROL_DRONE_2_MN_URL,
                2: config.PATROL_DRONE_3_MN_URL,
            }
            om2m_request_sender.create_content_instance(
                f"{URL_MAP[index]}/~/mn-cse/mn-name",
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
        om2m_request_sender.subscribe(
            f"{config.IN_URL}/~/in-cse/in-name",
            drone["app_name"],
            "control",
            f"{config.PATROL_DRONE_URL_FROM_CONTAINER}/process_control",
            "MN_CONTROL_SUB",
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Create thread for each drone
    """
    for index, drone in enumerate(drone_list):
        app_name = drone["app_name"]

        URL_MAP = {
            0: config.PATROL_DRONE_1_MN_URL,
            1: config.PATROL_DRONE_2_MN_URL,
            2: config.PATROL_DRONE_3_MN_URL,
        }

        PATROL_DRONE_MN_URL = URL_MAP[index]

        # create mn data conatiner
        om2m_request_sender.create_application(
            f"{PATROL_DRONE_MN_URL}/~/mn-cse",
            app_name,
            {"Type": "patrol-drone", "Category": "drone"},
        )
        om2m_request_sender.create_application(
            f"{config.IN_URL}/~/in-cse/in-name",
            app_name,
            {"Type": "patrol-drone", "Category": "drone"},
        )

        # create info container
        om2m_request_sender.create_container(
            f"{PATROL_DRONE_MN_URL}/~/mn-cse/mn-name", app_name, "info"
        )
        om2m_request_sender.create_container(
            f"{config.IN_URL}/~/in-cse/in-name", app_name, "info"
        )
        # subscribe info container for in server
        om2m_request_sender.subscribe(
            f"{PATROL_DRONE_MN_URL}/~/mn-cse/mn-name",
            app_name,
            "info",
            f"{config.IN_APP_POA}/process_info",
            "IN_INFO_SUB",
        )

        # create event container
        om2m_request_sender.create_container(
            f"{PATROL_DRONE_MN_URL}/~/mn-cse/mn-name", app_name, "event"
        )
        om2m_request_sender.create_container(
            f"{config.IN_URL}/~/in-cse/in-name", app_name, "event"
        )
        # subscribe status container for in server
        om2m_request_sender.subscribe(
            f"{PATROL_DRONE_MN_URL}/~/mn-cse/mn-name",
            app_name,
            "event",
            f"{config.IN_APP_POA}/process_event",
            "IN_EVENT_SUB",
        )

        om2m_request_sender.create_container(
            f"{PATROL_DRONE_MN_URL}/~/mn-cse/mn-name", app_name, "control"
        )
        om2m_request_sender.create_container(
            f"{config.IN_URL}/~/in-cse/in-name", app_name, "control"
        )

        drone["drone"].set_patrol_trail(drone["patrol_trail"])

    all_threads = []
    all_threads.append(
        threading.Thread(
            target=drone_update,
        )
    )
    all_threads.append(
        threading.Thread(
            target=subscribe_in_control,
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


def xml_to_dict(xml):
    xml = xmltodict.parse(xml)
    content = xml["m2m:sgn"]["nev"]["rep"]["m2m:cin"]["con"]
    content = xmltodict.parse(content)
    content = content["obj"]["str"]
    content = {item["@name"]: item["@val"] for item in content}
    return content


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

            if content["command"] == "START_PATROLLING":
                for index, drone in enumerate(drone_list):
                    if drone["app_name"] == app_name:
                        drone["drone"].set_status(PatrolDroneStatus.PATROLLING)
                        break
            elif content["command"] == "BACKING_TO_BASE":
                for index, drone in enumerate(drone_list):
                    if drone["app_name"] == app_name:
                        drone["drone"].set_status(PatrolDroneStatus.BACKING_TO_BASE)
                        break
            elif content["command"] == "TRACKING":
                for index, drone in enumerate(drone_list):
                    if drone["app_name"] == app_name:
                        drone["drone"].set_status(PatrolDroneStatus.TRACKING)
                        break

        except Exception as e:
            print("process_control error")
            print(xmltodict.parse(body))


{
    "m2m:sgn": {
        "@xmlns:m2m": "http://www.onem2m.org/xml/protocols",
        "@xmlns:hd": "http://www.onem2m.org/xml/protocols/homedomain",
        "nev": {
            "rep": {
                "m2m:cin": {
                    "@rn": "cin_625970953",
                    "ty": "4",
                    "ri": "/in-cse/cin-625970953",
                    "pi": "/in-cse/cnt-853701029",
                    "ct": "20231214T141442",
                    "lt": "20231214T141442",
                    "st": "0",
                    "cnf": "message",
                    "cs": "81",
                    "con": '<obj>\n            <str name="command" val="START_PATROLLING"/>\n            </obj>',
                }
            },
            "rss": "1",
        },
        "sud": "false",
        "sur": "/in-cse/sub-582620975",
    }
}

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
