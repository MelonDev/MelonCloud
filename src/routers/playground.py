from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from src.database.melondev_twitter_database import MelonDevTwitterDatabase
from src.engines.twitter_engines import test_client_mode
from src.environment.database import get_db
from src.models.twitter_model import TwitterValidatorModel

router = APIRouter()


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
