import uvicorn
from fastapi import FastAPI

import environment

app = FastAPI()

@app.get("/")
async def index():
    return "Hello FastAPI"

if __name__ == "__main__":
    uvicorn.run("main:app")
