import datetime
import sys
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

import requests
import uvicorn
import xmltodict
from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.append(str(Path(__file__).resolve().parents[1]))
from routes.patrol_drone import patrol_drone_router
from routes.track_drone import track_drone_router

import config
from utils.Om2mRequestSender import Om2mRequestSender

"""
Init IN
"""
om2m_request_sender = Om2mRequestSender()

app_name = "in-server"

# create in app
om2m_request_sender.create_application(
    f"{config.IN_URL}/~/in-cse",
    app_name,
    {"Type": "manager", "Category": "manager"},
    f"{config.IN_APP_POA}/notification",
)
om2m_request_sender.create_application(
    f"{config.IN_URL}/~/in-cse/in-name",
    config.IN_INFO_PROCESS_AE_NAME,
    {"Type": "manager", "Category": "manager"},
    f"{config.IN_APP_POA}/process_info",
)
om2m_request_sender.create_application(
    f"{config.IN_URL}/~/in-cse/in-name",
    config.IN_EVENT_PROCESS_AE_NAME,
    {"Type": "manager", "Category": "manager"},
    f"{config.IN_APP_POA}/process_event",
)


"""
IN APPLICATION
"""


def drone_monitor():
    last_notify_start_patrol = None
    while True:
        all_wait_flag = True
        for i in range(3):
            try:
                response = om2m_request_sender.get_latest_content_instance(
                    f"{config.IN_URL}/~/in-cse/in-name",
                    f"patrol_drone_{i+1}",
                    "info",
                )
                content = response["m2m:cin"]["con"]
                content = xmltodict.parse(content)
                content = content["obj"]["str"]
                content = {item["@name"]: item["@val"] for item in content}
                if content["status"] != "WAITING_FOR_COMMAND":
                    all_wait_flag = False
                    break
            except:
                all_wait_flag = False
                break

        try:
            if all_wait_flag:
                response = om2m_request_sender.get_latest_content_instance(
                    f"{config.IN_URL}/~/in-cse/in-name",
                    "track_drone_1",
                    "info",
                )
                content = response["m2m:cin"]["con"]
                content = xmltodict.parse(content)
                content = content["obj"]["str"]
                content = {item["@name"]: item["@val"] for item in content}
                if content["status"] != "WAITING_FOR_COMMAND":
                    all_wait_flag = False
        except:
            all_wait_flag = False

        if all_wait_flag:
            if (
                last_notify_start_patrol is None
                or (datetime.datetime.now() - last_notify_start_patrol).seconds > 10
            ):
                last_notify_start_patrol = datetime.datetime.now()
                for i in range(3):
                    om2m_request_sender.create_content_instance(
                        f"{config.IN_URL}/~/in-cse/in-name",
                        f"patrol_drone_{i+1}",
                        "control",
                        {
                            "command": "START_PATROLLING",
                            "app_name": f"patrol_drone_{i+1}",
                        },
                    )

                notification = {
                    "level": "info",
                    "app_name": "in_server",
                    "position": [-1, -1],
                    "event": "START_PATROLLING",
                    "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }

                if notification is not None:
                    notification_list.append(notification)
                if len(notification_list) > NOTIFICATION_MAX_LENGTH:
                    notification_list.pop(0)

        time.sleep(3)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Create thread for each drone
    """

    drone_update_thread = threading.Thread(
        target=drone_monitor,
    )

    drone_update_thread.daemon = True
    drone_update_thread.start()

    yield


app = FastAPI(lifespan=lifespan)
api_router = APIRouter()

api_router.include_router(
    track_drone_router, prefix="/track_drone", tags=["track_drone"]
)
api_router.include_router(
    patrol_drone_router, prefix="/patrol_drone", tags=["patrol_drone"]
)

patrol_drone_api_session = requests.Session()
track_drone_api_session = requests.Session()

# CORS
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

notification_list = []
NOTIFICATION_MAX_LENGTH = 6


def xml_to_dict(xml):
    xml = xmltodict.parse(xml)
    content = xml["m2m:sgn"]["nev"]["rep"]["m2m:cin"]["con"]
    content = xmltodict.parse(content)
    content = content["obj"]["str"]
    content = {item["@name"]: item["@val"] for item in content}
    return content


@api_router.post("/process_info")
async def process_info(request: Request):
    content_type = request.headers["Content-Type"]
    if content_type == "application/xml":
        body = await request.body()
        content = xml_to_dict(body)

        om2m_request_sender.create_content_instance(
            f"{config.IN_URL}/~/in-cse/in-name", content["app_name"], "info", content
        )


@api_router.post("/process_event")
async def process_event(request: Request):
    content_type = request.headers["Content-Type"]
    if content_type == "application/xml":
        body = await request.body()

        print(body)
        print(xmltodict.parse(body))
        content = xmltodict.parse(body)["m2m:sgn"]["nev"]["rep"]["m2m:cin"]["con"]
        content = xmltodict.parse(content)
        print(content)

        content = xml_to_dict(body)

        app_name = content["app_name"]
        om2m_request_sender.create_content_instance(
            f"{config.IN_URL}/~/in-cse/in-name", app_name, "event", content
        )

        if content["event"] == "FOUND_TARGET":
            index = int(content["app_name"].split("_")[-1])
            index -= 1
            # make other drones back to base
            for i in range(3):
                if i != index:
                    om2m_request_sender.create_content_instance(
                        f"{config.IN_URL}/~/in-cse/in-name",
                        f"patrol_drone_{i+1}",
                        "control",
                        {
                            "command": "BACKING_TO_BASE",
                            "app_name": f"patrol_drone_{i+1}",
                        },
                    )

            om2m_request_sender.create_content_instance(
                f"{config.IN_URL}/~/in-cse/in-name",
                "track_drone_1",
                "control",
                {
                    "command": "SEARCHING",
                    "follow_patrol_index": index,
                    "app_name": "track_drone_1",
                },
            )

            notification = {
                "level": "error",
                "app_name": content["app_name"],
                "event": content["event"],
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

        elif content["event"] == "START_TRACKING":
            for i in range(3):
                om2m_request_sender.create_content_instance(
                    f"{config.IN_URL}/~/in-cse/in-name",
                    f"patrol_drone_{i+1}",
                    "control",
                    {"command": "BACKING_TO_BASE", "app_name": f"patrol_drone_{i+1}"},
                )

        elif content["event"] == "TARGET_LEFT":
            notification = {
                "level": "success",
                "app_name": content["app_name"],
                "event": "TARGET_LEFT",
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            for i in range(3):
                om2m_request_sender.create_content_instance(
                    f"{config.IN_URL}/~/in-cse/in-name",
                    f"patrol_drone_{i+1}",
                    "control",
                    {"command": "BACKING_TO_BASE", "app_name": f"patrol_drone_{i+1}"},
                )
            om2m_request_sender.create_content_instance(
                f"{config.IN_URL}/~/in-cse/in-name",
                "track_drone_1",
                "control",
                {"command": "BACKING_TO_BASE", "app_name": "track_drone_1"},
            )

        if notification is not None:
            notification_list.append(notification)
        if len(notification_list) > NOTIFICATION_MAX_LENGTH:
            notification_list.pop(0)


@api_router.get("/notification")
def get_notification():
    return notification_list[::-1]


app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run(app="app:app", host="0.0.0.0", port=8127, reload=False, workers=1)
