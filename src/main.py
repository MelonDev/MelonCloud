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
from src.environment.share_environment import get_db
from src.routers import user

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(Path(BASE_DIR, 'static/templates')))
app.mount("/static", StaticFiles(directory=str(Path(BASE_DIR, 'static'))), name="static")



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

#script_dir = os.path.dirname(__file__)
#st_abs_file_path = os.path.join(script_dir, "static/")
#app.mount("/static", StaticFiles(directory=st_abs_file_path), name="static")

# app.mount("/static", StaticFiles(directory="static"), name="static")

#templates = Jinja2Templates(directory="./static/templates")



# app.include_router(user.router, prefix="/user", tags=["users"])


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


@app.get("/web")
async def web(request: Request):
    return templates.TemplateResponse("security/password_generator/home.html", {"request": request})


if __name__ == "__main__":
    uvicorn.run("main:app")
