import xmltodict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import config
from utils.Om2mRequestSender import Om2mRequestSender

patrol_drone_router = APIRouter()
patrol_drone_om2m_request_sender = Om2mRequestSender()


def xml_to_dict(xml):
    xml = xmltodict.parse(xml)
    content = xml["m2m:sgn"]["nev"]["rep"]["m2m:cin"]["con"]
    content = xmltodict.parse(content)
    content = content["obj"]["str"]
    content = {item["@name"]: item["@val"] for item in content}
    return content


@patrol_drone_router.get("/{index}/info", status_code=200)
async def get_drone_info(index: int):
    # get latest data from mn resource tree
    response = patrol_drone_om2m_request_sender.get_latest_content_instance(
        f"{config.IN_URL}/~/in-cse/in-name",
        f"patrol_drone_{index+1}",
        "info",
    )
    content = response["m2m:cin"]["con"]
    print(content)
    content = xmltodict.parse(content)
    content = content["obj"]["str"]
    content = {item["@name"]: item["@val"] for item in content}

    # change position from string to list
    # remove bracket
    content["position"] = content["position"][1:-1]
    content["position"] = content["position"].split(",")
    content["position"] = [int(item.strip()) for item in content["position"]]

    return content
