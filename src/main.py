import uvicorn
from fastapi import FastAPI

import environment

app = FastAPI()


@app.get("/")
async def index():
    return "Hello FastAPI"


@app.get("/secret-key")
async def secret_key():
    return environment.SECRET_KEY


if __name__ == "__main__":
    uvicorn.run("main:app")
