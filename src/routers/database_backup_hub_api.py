from fastapi import APIRouter, Depends, status as code, HTTPException, Request, Response
from sqlalchemy.orm import Session

from src.database.melondev_twitter_database import MelonDevTwitterDatabase
from src.environment.database import get_db
from src.tools.db_exporter import export_month_in_year
import httpx

router = APIRouter()
client = httpx.AsyncClient()


@router.get("/trigger", include_in_schema=True)
async def trigger():
    path = "https://meloncloud.herokuapp.com/api/v2/database-backup/"
    items = [
        {
            "name": f"MelonDev_Twitter_Database",
            "url": f"{path}melondev-twitter-database"
        }
    ]
    for item in items:
        await call_backup_api(item)
    return "TRIGGERED!"


async def call_backup_api(payload):
    webhook_name = "auto_database_backup"
    webhook_url = f"https://maker.ifttt.com/trigger/{webhook_name}/json/with/key/c0lOuTaY1ogijIhHwlSps9"
    await client.post(webhook_url, json=payload)


@router.get("/melondev_twitter_database", include_in_schema=True)
async def melondev_twitter_database(request: Request, db: Session = Depends(get_db)):
    return export_month_in_year(db=db, session=MelonDevTwitterDatabase)
