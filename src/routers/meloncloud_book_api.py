import math
import uuid

from fastapi import APIRouter, Depends, status as code, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query as DBQuery
from sqlalchemy.sql.expression import func, select

from src.database.meloncloud.meloncloud_book_database import MelonCloudBookDatabase
from src.database.meloncloud.meloncloud_book_page_database import MelonCloudBookPageDatabase
from src.environment.database import get_db
from src.environment.mock_meloncloud_book import data as mock_data
from src.models.meloncloud_book_model import RequestBookQueryModel
from src.models.response_model import ResponseModel, ResponsePageModel
from src.tools.verify_hub import verify_return

router = APIRouter()


@router.get("/", include_in_schema=True)
async def books(params: RequestBookQueryModel = Depends(), db: Session = Depends(get_db)):
    database = db.query(MelonCloudBookDatabase)

    total_page = None
    current_count = None

    if params.id is not None:
        book = database.get(params.id)
        if book is not None:
            result = book.serialize
            result['pages'] = [i.serialize for i in book.pages]
        else:
            result = None
            not_found_exception()

    else:
        compute_database = apply_database_for_book_filters(params=params, db=database)
        limit_database = apply_limit_to_database(params=params, database=compute_database)
        results = limit_database.all()
        result = [i.serialize for i in results]

        total_count = compute_database.count()
        current_count = limit_database.count()
        total_page = math.ceil(total_count / current_count)

    return await verify_return(
        data=ResponsePageModel(data=result, rows=current_count, page=params.page, total_page=total_page))


@router.get("/upload", include_in_schema=False)
async def upload(db: Session = Depends(get_db)):
    data = mock_data
    for _, value in data.items():
        info = value['info']
        pages = value['pages']
        book = MelonCloudBookDatabase(name=info['name'], category="HENTAI", language=info['language'],
                                      artist=info['artist'], group=info['group'])
        number = 0
        for p in pages:
            number += 1
            page = MelonCloudBookPageDatabase(book_id=book.id, url=p['url'], extension=p["type"], name=p['file_name'],
                                              number=number)

            if book.cover_url is None:
                book.cover_url = page.url
                db.add(book)

            db.add(page)
    db.commit()

    return "UPLOAD??"


def apply_database_for_book_filters(params: RequestBookQueryModel, db):
    database = db if type(db) is DBQuery else db.query(MelonCloudBookDatabase)

    if params is None:
        bad_request_exception()

    if params.name is not None:
        database = database.filter(MelonCloudBookDatabase.name.contains(params.name))
    if params.language is not None:
        database = database.filter(MelonCloudBookDatabase.language.contains(params.language))
    if params.artist is not None:
        database = database.filter(MelonCloudBookDatabase.artist.contains(params.artist))
    if params.group is not None:
        database = database.filter(MelonCloudBookDatabase.group.contains(params.group))
    if params.category is not None:
        database = database.filter(MelonCloudBookDatabase.category.contains(params.category))

    if params.random is not None and params.infinite is not None:
        if params.random and params.infinite:
            database = database.order_by(func.random())


    return database


def apply_limit_to_database(params: RequestBookQueryModel, database):
    if not bool(params.infinite):
        page = params.page if params.page is not None else 0
        limit = params.limit if params.limit is not None else 20
        database = database.limit(limit).offset(int(page * limit))
    return database


def bad_request_exception(message=None):
    raise HTTPException(
        status_code=code.HTTP_400_BAD_REQUEST,
        detail=message if message is not None else "BAD REQUEST")

def not_found_exception(message=None):
    raise HTTPException(
        status_code=code.HTTP_404_NOT_FOUND,
        detail=message if message is not None else "NOT FOUND")
