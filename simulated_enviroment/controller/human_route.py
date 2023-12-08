from domain.Human import Human
from fastapi import APIRouter

router = APIRouter()
human = Human()


@router.get("/position")
def get_human_position():
    return {"position": human.get_position()}
