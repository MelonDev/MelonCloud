from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, validator

from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from environment import TWITTER_SECRET_PASSWORD, GITHUB_ACCESS_TOKEN
from src.database.melondev_twitter_database import MelonDevTwitterDatabase
from src.engines.twitter_engines import test_client_mode
from src.environment.database import get_db
from src.models.twitter_model import TwitterValidatorModel

router = APIRouter()


@router.get("/", include_in_schema=False)
async def index():
    # return "Hello FastAPI"
    return RedirectResponse(url="/docs/")


class TestModel(TwitterValidatorModel):
    content: dict


@router.get("/tests")
async def test():
    a = test_client_mode()
    print(a)

    return "HEllo"


@router.get("/database", include_in_schema=False)
async def database(db: Session = Depends(get_db)):
    a = db.query(MelonDevTwitterDatabase).limit(10).all()
    b = [item.serialize for item in a]
    print("DATABASE")
    return b
