from fastapi import APIRouter

from src.database.meloncloud.meloncloud_book_database import MelonCloudBookDatabase

router = APIRouter()


@router.get("/", include_in_schema=False)
async def main():
    return "MelonCloud Book is connected"


@router.post("/upload", include_in_schema=True)
async def upload(req :dict):
    for key, value in req.items():
        print(key)
        print(value)
    return "RUN"
