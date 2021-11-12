import uvicorn
from fastapi import FastAPI

import environment
from src.environment.database_path import database_path_list

app = FastAPI()


@app.get("/")
async def index():
    return "Hello FastAPI"


@app.get("/secret-key")
async def secret_key():
    print(environment.SECRET_KEY)
    print(database_path_list)
    return environment.SECRET_KEY


if __name__ == "__main__":
    uvicorn.run("main:app")
