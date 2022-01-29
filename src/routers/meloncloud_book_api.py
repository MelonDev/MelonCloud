import math
import uuid
from datetime import timedelta

import fastapi_jwt_auth.exceptions

from fastapi import APIRouter, Depends, status as code, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordBearer
from fastapi_jwt_auth import AuthJWT
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query as DBQuery
from sqlalchemy.sql.expression import func, select

from environment import MELONCLOUD_BOOK_VERIFY_KEY, SECRET_KEY
from src.database.meloncloud.meloncloud_book_database import MelonCloudBookDatabase
from src.database.meloncloud.meloncloud_book_page_database import MelonCloudBookPageDatabase
from src.environment.database import get_db
from src.environment.mock_meloncloud_book import data as mock_data
from src.models.meloncloud_book_model import RequestBookQueryModel, MelonCloudBookSettings, MelonCloudBookTokenModel, \
    MelonCloudBookLoginForm
from src.models.response_model import ResponseModel, ResponsePageModel
from src.tools.verify_hub import verify_return
from fastapi.encoders import jsonable_encoder


@AuthJWT.load_config
def get_config():
    return MelonCloudBookSettings()


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


router = APIRouter()


@router.get("/", include_in_schema=True)
async def books(params: RequestBookQueryModel = Depends(), Authorize: AuthJWT = Depends(),
                db: Session = Depends(get_db)):
    await check_authorize(Authorize)

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
        total_page = 1
        if current_count > 0:
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


@router.post("/login", include_in_schema=True, tags=['Authentication'])
async def login(form: MelonCloudBookLoginForm = Depends(MelonCloudBookLoginForm.as_form),
                Authorize: AuthJWT = Depends()):
    access_token = await authorizing(form.password, Authorize)

    return await verify_return(data=ResponseModel(
        MelonCloudBookTokenModel(access_token=access_token)))


@router.delete('/logout', include_in_schema=True, tags=['Authentication'])
async def logout(Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
        Authorize.unset_jwt_cookies()
        return await verify_return(data={"msg": "Successfully logout"})
    except fastapi_jwt_auth.exceptions.MissingTokenError:
        bad_request_exception(message="Missing Token")
        return await verify_return(data=None)
    except Exception as e:
        print(e)
        bad_request_exception(message="Found an error: " + str(e))
        return await verify_return(data=None)


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
        page = params.page - 1 if params.page is not None else 0
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


def unauthorized_exception(message=None):
    raise HTTPException(
        status_code=code.HTTP_401_UNAUTHORIZED,
        detail=message if message is not None else "UNAUTHORIZED")


async def check_authorize(Authorize: AuthJWT):
    try:
        Authorize.jwt_required()
    except fastapi_jwt_auth.exceptions.MissingTokenError:
        unauthorized_exception(message="UNAUTHORIZED")
        return await verify_return(data=None)
    except Exception as e:
        print(e)
        bad_request_exception(message="Found an error: " + str(e))
        return await verify_return(data=None)


async def request_is_authorized(Authorize: AuthJWT):
    try:
        Authorize.jwt_required()
        return True
    except fastapi_jwt_auth.exceptions.MissingTokenError:
        print("MissingTokenError")
        return False
    except Exception as e:
        print(e)
        return False


async def authorizing(password: str, Authorize: AuthJWT):
    if MELONCLOUD_BOOK_VERIFY_KEY is None:
        return None

    if not verify_password(plain_password=password, hashed_password=MELONCLOUD_BOOK_VERIFY_KEY):
        return None

    expires = timedelta(minutes=(60 * 6))

    access_token = Authorize.create_access_token(subject=str(SECRET_KEY), expires_time=expires)

    Authorize.set_access_cookies(access_token)
    return access_token


async def load_book(params: RequestBookQueryModel = Depends(), Authorize: AuthJWT = Depends(),
                    db: Session = Depends(get_db)):
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

        total_page = 1

        if params.infinite is None:
            if current_count > 0 and (current_count <= (params.limit if params.limit is not None else 20)):
                total_page = math.ceil(total_count / (params.limit if params.limit is not None else 20))
        else:
            if not params.infinite:
                if current_count > 0 and (current_count <= (params.limit if params.limit is not None else 20)):
                    total_page = math.ceil(total_count / (params.limit if params.limit is not None else 20))

    return await verify_return(
        data=ResponsePageModel(data=result, rows=current_count, page=params.page, total_page=total_page))
