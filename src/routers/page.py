import json

from fastapi import APIRouter, Request, Depends, Form, Response, Cookie
from fastapi.encoders import jsonable_encoder
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse, RedirectResponse
from typing import Optional

from src.environment.database import get_db
from src.environment.share_environment import templates
from src.models.meloncloud_book_model import RequestBookQueryModel
from src.routers.meloncloud_book_api import request_is_authorized, authorizing, books
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
    return templates.TemplateResponse("home/home.html",
                                      {"request": request})


@router.get("/meloncloud-book/logout", include_in_schema=False)
async def book_logout(request: Request, Authorize: AuthJWT = Depends()):
    authorized = await request_is_authorized(Authorize)

    if authorized:
        Authorize.unset_jwt_cookies()

    response = RedirectResponse('/meloncloud-book', status_code=302)
    response.delete_cookie(key='access_token_cookie')
    return response


@router.get("/meloncloud-book", include_in_schema=False)
@router.post("/meloncloud-book", include_in_schema=False)
async def book(request: Request,params: RequestBookQueryModel = Depends(), Authorize: AuthJWT = Depends(),db: Session = Depends(get_db)):
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

        res = await books(params=params,db=db,Authorize=Authorize)
        data = jsonable_encoder(res)
        print(data)
        response = templates.TemplateResponse("meloncloud_book/home.html",
                                              {"request": request, "data": data['data']})
    else:
        access_token = None

    response.set_cookie(key="access_token_cookie", value=access_token)

    return response
