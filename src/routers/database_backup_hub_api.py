import datetime

from fastapi import APIRouter, Depends, status as code, HTTPException, Request, Response
from sqlalchemy.orm import Session

from environment import IFTTT_SECRET_KEY
from src.database.meloncloud.meloncloud_book_database import MelonCloudBookDatabase
from src.database.meloncloud.meloncloud_book_page_database import MelonCloudBookPageDatabase
from src.database.meloncloud.meloncloud_twitter_database import MelonCloudTwitterDatabase
from src.database.melondev_twitter_database import MelonDevTwitterDatabase
from src.environment.database_config import get_db
from src.tools.db_exporter import export_twitter_month_on_year, export
import httpx

router = APIRouter()
client = httpx.AsyncClient()


@router.get("/trigger", include_in_schema=True)
async def trigger():
    path = "https://meloncloud.herokuapp.com/api/v2/database-backup/"

    items = [
        MelonCloudTwitterDatabase,
        MelonCloudBookDatabase,
        MelonCloudBookPageDatabase
    ]
    for item in items:
        name = f"{item.__tablename__}"
        url = f"{path}{name.lower()}"
        date = str(datetime.datetime.now().strftime('%d %b %Y'))
        await call_backup_api({"name": name, "url": url, 'folder': date})
    return "TRIGGERED!"


@router.get("/monthly-twitter-backup-trigger", include_in_schema=True)
async def monthly_trigger():
    path = "https://meloncloud.herokuapp.com/api/v2/database-backup/"
    name = f"{MelonCloudTwitterDatabase.__tablename__}"
    url = f"{path}fully_{name.lower()}"
    date = str(datetime.datetime.now().strftime('%B %Y'))
    await call_fully_backup_api({"name": name, "url": url, 'xfol': "Monthly", 'folder': date})

    return "TRIGGERED!"


@router.get("/weekly-twitter-backup-trigger", include_in_schema=True)
async def weekly_trigger():
    path = "https://meloncloud.herokuapp.com/api/v2/database-backup/"
    name = f"{MelonCloudTwitterDatabase.__tablename__}"
    url = f"{path}fully_{name.lower()}"
    date = str(datetime.datetime.now().strftime('%d %b %Y'))
    await call_fully_backup_api({"name": name, "url": url, 'xfol': "Weekly", 'folder': date})

    return "TRIGGERED!"


async def call_backup_api(payload):
    webhook_name = "auto_database_backup"
    webhook_url = f"https://maker.ifttt.com/trigger/{webhook_name}/json/with/key/{IFTTT_SECRET_KEY}"
    await client.post(webhook_url, json=payload)


async def call_fully_backup_api(payload):
    webhook_name = "fully_database_backup"
    webhook_url = f"https://maker.ifttt.com/trigger/{webhook_name}/json/with/key/{IFTTT_SECRET_KEY}"
    await client.post(webhook_url, json=payload)


@router.get("/meloncloud_twitter_database", include_in_schema=True)
async def melondev_twitter_database(request: Request, db: Session = Depends(get_db)):
    return export_twitter_month_on_year(db=db, session=MelonCloudTwitterDatabase)


@router.get("/fully_meloncloud_twitter_database", include_in_schema=True)
async def fully_melondev_twitter_database(request: Request, db: Session = Depends(get_db)):
    return export(db=db, session=MelonCloudTwitterDatabase)


@router.get("/meloncloud_book_database", include_in_schema=True)
async def meloncloud_book_database(request: Request, db: Session = Depends(get_db)):
    return export(db=db, session=MelonCloudBookDatabase)


@router.get("/meloncloud_book_page_database", include_in_schema=True)
async def melonCloud_book_page_database(request: Request, db: Session = Depends(get_db)):
    return export(db=db, session=MelonCloudBookPageDatabase)
