import uvicorn
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware

from src.database.melondev_twitter_database import MelonDevTwitterDatabase
from src.environment.share_environment import get_db

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/")
async def index():
    return "Hello FastAPI"


@app.get("/database")
async def database(db: Session = Depends(get_db)):
    a = db.query(MelonDevTwitterDatabase).limit(10).all()
    b = [item.serialize for item in a]
    return b


if __name__ == "__main__":
    uvicorn.run("main:app")
