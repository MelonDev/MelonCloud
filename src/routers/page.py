from fastapi import APIRouter, Request, Depends
from fastapi.encoders import jsonable_encoder
from fastapi_jwt_auth import AuthJWT
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from src.database.meloncloud.meloncloud_book_database import MelonCloudBookDatabase
from src.environments.database_config import get_db
from src.environments.share_environment import templates
from src.models.meloncloud_book_model import RequestBookQueryModel
from src.routers.meloncloud.meloncloud_book_api import request_is_authorized, authorizing, load_book
from src.tools.generators.random_password_generator import RandomPasswordGenerator

router = APIRouter()


@router.get("/pwg", include_in_schema=False)
async def pwg(request: Request, step: int = None):
    generator = RandomPasswordGenerator()
    password = generator.simple(step=step) if step is not None else generator.simple()
    return templates.TemplateResponse("security/password_generator/home.html",
                                      {"request": request, "password": password})


@router.get("/test", include_in_schema=False)
async def test(request: Request):
    return templates.TemplateResponse("example/test-bootstrap.html",
                                      {"request": request})


@router.get("/pwg_v2", include_in_schema=False)
async def pwg_v2(request: Request, step: int = None, length: int = None, action: str = None):
    generator = RandomPasswordGenerator()
    return templates.TemplateResponse("security/password_generator_v2/home.html",
                                      {"request": request, "password": generator.simple(step=step, length=length),
                                       "length": str(length if length is not None else 6),
                                       "step": str(step if step is not None else 3),
                                       "action": action if action is not None else "hide",
                                       })


@router.get("/home", include_in_schema=False)
async def home(request: Request):
    items = [
        {
            "name": "รหัสผ่านความปลอดภัยแบบสุ่ม",
            "image": "./static/templates/home/img/towfiqu-barbhuiya-FnA5pAzqhMM-unsplash.jpg",
            "page": "pwg_v2",
            "doc": "api/v2/security/pwg_v2/docs"
        },
        {
            "name": "ทวิตเตอร์",
            "image": "./static/templates/home/img/jeremy-bezanger-Jm1YUfYjpHI-unsplash.jpg",
            "page": "meloncloud-twitter",
            "doc": "api/v3/twitter/docs"
        },
        {
            "name": "พื้นที่ทดสอบ",
            "image": "./static/templates/home/img/pankaj-patel-_SgRNwAVNKw-unsplash.jpg",
            "page": "null",
            "doc": "api/v2.0-alpha/docs"
        },
        {
            "name": "จัดการกระบือ",
            "image": "./static/templates/home/img/zachary-pearson-thC1uwWdMfM-unsplash.jpg",
            "page": "null",
            "doc": "api/v2/buff/docs"
        },
        {
            "name": "ชั้นหนังสือ",
            "image": "./static/templates/home/img/mitchell-luo-g_Y9K409vNw-unsplash.jpg",
            "page": "meloncloud-book",
            "doc": "api/v2/meloncloud-book/docs"
        },
        {
            "name": "สำรองฐานข้อมูล",
            "image": "./static/templates/home/img/markus-winkler-cV9-hOgoaok-unsplash.jpg",
            "page": "null",
            "doc": "api/v2/database-backup/docs"
        },
        {
            "name": "เงินดิจิตอล",
            "image": "./static/templates/home/img/dmitry-demidko-OG3A-ilG8AY-unsplash.jpg",
            "page": "null",
            "doc": "api/v2/crypto/docs"
        }
    ]
    return templates.TemplateResponse("home/home.html",
                                      {"request": request, "items": items})


@router.get("/meloncloud-book/logout", include_in_schema=False)
async def book_logout(request: Request, Authorize: AuthJWT = Depends()):
    authorized = await request_is_authorized(Authorize)

    if authorized:
        Authorize.unset_jwt_cookies()

    response = RedirectResponse('/meloncloud-book', status_code=302)
    response.delete_cookie(key='access_token_cookie')
    return response


@router.get("/meloncloud-twitter", include_in_schema=False)
async def twitter(request: Request):
    return RedirectResponse(url='https://meloncloud-d2fb8.web.app')


@router.get("/meloncloud-book", include_in_schema=False)
@router.post("/meloncloud-book", include_in_schema=False)
async def book(request: Request, params: RequestBookQueryModel = Depends(), Authorize: AuthJWT = Depends(),
               db: Session = Depends(get_db)):
    form = await request.form()
    form = jsonable_encoder(form)
    access_token = request.cookies['access_token_cookie'] if "access_token_cookie" in request.cookies else None
    authorized = False
    response = templates.TemplateResponse("meloncloud_book/login.html",
                                          {"request": request})

    if "password" in form:
        access_token = await authorizing(form['password'], Authorize)

        if access_token is not None:
            authorized = True


    else:
        authorized = await request_is_authorized(Authorize)

    if authorized:
        res = await load_book(params=params, db=db, Authorize=Authorize)
        data = jsonable_encoder(res)
        if params.id is not None:
            response = templates.TemplateResponse("meloncloud_book/book.html",
                                                  {"request": request, "data": data['data'], })
        else:
            raw_languages = db.query(MelonCloudBookDatabase.language, func.count(MelonCloudBookDatabase.language))
            if params.language is None and params.artist is not None:
                raw_languages = raw_languages.filter(MelonCloudBookDatabase.artist.contains(params.artist))
            raw_languages = raw_languages.group_by(MelonCloudBookDatabase.language).all()

            list_language = []
            data_languages_sorted = sorted(raw_languages, key=lambda kv: kv[1], reverse=True)
            for language in data_languages_sorted:
                list_language.append({"name": language[0], "count": language[1]})

            raw_artists = db.query(MelonCloudBookDatabase.artist, func.count(MelonCloudBookDatabase.artist))
            if params.artist is None and params.language is not None:
                raw_artists = raw_artists.filter(MelonCloudBookDatabase.language.contains(params.language))
            raw_artists = raw_artists.group_by(MelonCloudBookDatabase.artist).all()
            list_artist = []
            data_artists_sorted = sorted(raw_artists, key=lambda kv: kv[1], reverse=True)

            for artist in data_artists_sorted:
                list_artist.append({"name": artist[0], "count": artist[1]})

            s = 1
            e = 1

            t = data['total_page']
            p = data['page']

            if t <= 5:
                s = 1
                e = t
            else:
                if p == t:
                    e = t
                    s = p - 4
                elif p <= 3:
                    s = 1
                    e = 5
                else:
                    d = t - p
                    if d >= 3:
                        e = p + 2
                        s = p - 2
                    else:
                        e = t
                        s = p - (d + 2)

            response = templates.TemplateResponse("meloncloud_book/home.html",
                                                  {"request": request, "data": data['data'],
                                                   "total_page": data['total_page'], "limit": data['limit'],
                                                   "rows": data['rows'],
                                                   "page": data['page'], "languages": list_language,
                                                   "language": params.language, "artists": list_artist,
                                                   "artist": params.artist, "infinite": params.infinite,
                                                   "start_page_number": s,
                                                   "end_page_number": e})
    else:
        access_token = None

    response.set_cookie(key="access_token_cookie", value=access_token)

    return response
