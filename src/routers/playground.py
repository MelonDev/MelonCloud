from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from src.database.melondev_twitter_database import MelonDevTwitterDatabase
from src.environment.database import get_db

router = APIRouter()

@router.get("/",include_in_schema=False)
async def index():
    # return "Hello FastAPI"
    return RedirectResponse(url="/docs/")


@router.get("/database", include_in_schema=False)
async def database(db: Session = Depends(get_db)):
    a = db.query(MelonDevTwitterDatabase).limit(10).all()
    b = [item.serialize for item in a]
    print("DATABASE")
    return b

