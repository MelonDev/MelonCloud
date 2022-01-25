from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database.meloncloud.meloncloud_book_database import MelonCloudBookDatabase
from src.database.meloncloud.meloncloud_book_page_database import MelonCloudBookPageDatabase
from src.environment.database import get_db
from src.environment.mock_meloncloud_book import data as mock_data

router = APIRouter()


@router.get("/", include_in_schema=False)
async def main():
    return "MelonCloud Book is connected"


@router.get("/upload", include_in_schema=False)
async def upload(db: Session = Depends(get_db)):
    data = mock_data
    for _, value in data.items():
        info = value['info']
        pages = value['pages']
        book = MelonCloudBookDatabase(name=info['name'], category="HENTAI", language=info['language'],
                                      artist=info['artist'], group=info['group'])
        for p in pages:

            page = MelonCloudBookPageDatabase(book_id=book.id, url=p['url'], extension=p["type"], name=p['file_name'])

            if book.cover_url is None:
                book.cover_url = page.id
                db.add(book)

            db.add(page)
    db.commit()

    return "UPLOAD??"
