import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Depends, Request
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse, HTMLResponse

from src.database.melondev_twitter_database import MelonDevTwitterDatabase
from src.environment import share_environment
from src.environment.database import get_db
from src.environment.share_environment import templates
from src.routers import user, web_page

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
print("AA"+str(BASE_DIR))
# templates = Jinja2Templates(directory=str(Path(BASE_DIR, 'static/templates')))
# app.mount("/static", StaticFiles(directory=str(Path(BASE_DIR, 'static'))), name="static")
share_environment.templates = Jinja2Templates(directory=str(Path(BASE_DIR, 'static/templates')))
app.mount("/static", StaticFiles(directory=str(Path(BASE_DIR, 'static'))), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(web_page.router, prefix="/page", tags=["WebPage"])

app.include_router(user.router, prefix="/user", tags=["users"])


@app.get("/")
async def index():
    # return "Hello FastAPI"
    return RedirectResponse(url="/docs/")


@app.get("/database")
async def database(db: Session = Depends(get_db)):
    a = db.query(MelonDevTwitterDatabase).limit(10).all()
    b = [item.serialize for item in a]
    print("DATABASE")
    return b


@app.get("/main", tags=["users"])
async def read_users():
    return [{"username": "Rick"}, {"username": "Morty"}]


if __name__ == "__main__":
    uvicorn.run("main:app")
