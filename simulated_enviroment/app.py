import sys

import uvicorn
from controller import human_route
from domain.Human import Human
from domain.SimulationMap import SimulationMap
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
api_router = APIRouter()

api_router.include_router(human_route.router, prefix="/human")

simulation_map = SimulationMap()

# CORS
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@api_router.get("/")
def hello_world():
    return {"msg": "Hello World"}


app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run(app="app:app", host="0.0.0.0", port=8122, reload=False, workers=1)
