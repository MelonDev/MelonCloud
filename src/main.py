import uvicorn
from fastapi import FastAPI

import environment
from src.environment import database_path
from src.environment.database_path import database_path_list

app = FastAPI()


@app.get("/")
async def index():
    return "Hello FastAPI"


@app.get("/secret-key")
async def secret_key():
    print(environment.SECRET_KEY)
    print(database_path_list)
    dbp = {k: v for k, v in database_path_list.items() if v is not None}
    dbp2 = dict(filter(lambda item: item[1] is not None, database_path_list.items()))
    print(dbp2)
    print(dbp)
    print(database_path)
    return dbp2


if __name__ == "__main__":
    uvicorn.run("main:app")
