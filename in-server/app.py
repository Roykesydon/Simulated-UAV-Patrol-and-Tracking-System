import datetime
import sys
from pathlib import Path

import requests
import uvicorn
import xmltodict
from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.append(str(Path(__file__).resolve().parents[1]))
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
    config.IN_APP_POA,
)

"""
IN APPLICATION
"""
app = FastAPI()
api_router = APIRouter()

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


@api_router.get("/")
def hello_world():
    return {"msg": "in server"}


@api_router.get("/human/position")
def get_human_position():
    return om2m_request_sender.get_content_instance(
        f"{config.IN_URL}/~/in-cse/in-name/human/position_container"
    )


@api_router.get("/notification")
def get_notification():
    return notification_list[::-1]


@api_router.post("/notification")
async def get_new_notification(request: Request):
    content_type = request.headers["Content-Type"]
    if content_type == "application/xml":
        body = await request.body()
        # xml to dict
        body = xmltodict.parse(body)
        print(f"in-get-notification: {body}")
        content = body["m2m:sgn"]["nev"]["rep"]["m2m:cin"]["con"]
        content = xmltodict.parse(content)
        print(content)
        content = content["obj"]["str"]
        content = {item["@name"]: item["@val"] for item in content}
        notification = None

        if content["event"] == "FOUND_TARGET":
            index = int(content["app_name"].split("_")[-1])
            index -= 1
            # make other drones back to base
            for i in range(3):
                if i != index:
                    patrol_drone_api_session.put(
                        f"{config.PATROL_DRONE_URL}/{i}/status",
                        json={"status": "BACKING_TO_BASE"},
                    )

            track_drone_api_session.put(
                f"{config.TRACK_DRONE_URL}/0/follow_patrol_index",
                json={"index": index},
            )
            track_drone_api_session.put(
                f"{config.TRACK_DRONE_URL}/0/status",
                json={"status": "SEARCHING"},
            )

            notification = {
                "level": "error",
                "app_name": content["app_name"],
                "position": content["position"],
                "event": content["event"],
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

        elif content["event"] == "START_PATROLLING":
            notification = {
                "level": "info",
                "app_name": content["app_name"],
                "position": content["position"],
                "event": content["event"],
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

        elif content["event"] == "START_TRACKING":
            for i in range(3):
                patrol_drone_api_session.put(
                    f"{config.PATROL_DRONE_URL}/{i}/status",
                    json={"status": "BACKING_TO_BASE"},
                )

        elif content["event"] == "TARGET_LEFT":
            notification = {
                "level": "success",
                "app_name": content["app_name"],
                "position": content["position"],
                "event": "TARGET_LEFT",
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            for i in range(3):
                patrol_drone_api_session.put(
                    f"{config.PATROL_DRONE_URL}/{i}/status",
                    json={"status": "BACKING_TO_BASE"},
                )
            track_drone_api_session.put(
                f"{config.TRACK_DRONE_URL}/0/status",
                json={"status": "BACKING_TO_BASE"},
            )

        if notification is not None:
            notification_list.append(notification)
        if len(notification_list) > NOTIFICATION_MAX_LENGTH:
            notification_list.pop(0)

    return {}


app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run(app="app:app", host="0.0.0.0", port=8127, reload=False, workers=1)
