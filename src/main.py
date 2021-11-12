import uvicorn
from fastapi import FastAPI

import environment
from src.environment import database_path
from src.environment.database_path import database_path_list

app = FastAPI()


@app.get("/")
async def index():
    return "Hello FastAPI"


if __name__ == "__main__":
    uvicorn.run("main:app")
