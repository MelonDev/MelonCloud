from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, validator

from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from environment import TWITTER_SECRET_PASSWORD
from src.database.melondev_twitter_database import MelonDevTwitterDatabase
from src.environment.database import get_db
from src.models.twitter_model import TwitterValidatorModel

router = APIRouter()


@router.get("/", include_in_schema=False)
async def index():
    # return "Hello FastAPI"
    return RedirectResponse(url="/docs/")


class TestModel(TwitterValidatorModel):
    content: dict


@router.post("/tests")
async def test(req: TestModel):
    numbers = [1, 2, 3, 4]
    result = map(lambda x: x + x, numbers)
    print(list(result))
    return "HEllo"


@router.get("/database", include_in_schema=False)
async def database(db: Session = Depends(get_db)):
    a = db.query(MelonDevTwitterDatabase).limit(10).all()
    b = [item.serialize for item in a]
    print("DATABASE")
    return b
