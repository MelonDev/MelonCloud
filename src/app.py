from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi_jwt_auth.exceptions import AuthJWTException
from flask import Flask, escape, request
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.responses import RedirectResponse
# from fastapi_jwt_auth.exceptions import AuthJWTException
from fastapi.responses import JSONResponse
from mangum import Mangum
from sqlalchemy.orm import Session

from src.apps.v1.flask_app import app as flask_app
from src.apps.v2.twitter_app import app as twitter_app
from src.apps.v2.twitter_app import app as twitter_app
from src.apps.v2.buff_app import app as buff_app
from src.apps.v2.pwg_app import app as pwg_app_v2
from src.apps.v2.meloncloud_book_app import app as meloncloud_book_app
from src.apps.v2.database_backup_hub_app import app as database_backup_hub_app
from src.apps.v3.meloncloud_twitter_app import app as meloncloud_twitter_app
from src.apps.v2.crypto_portfolios_app import app as crypto_portfolios_app

from src.database.buff_management.buff_activity_log_database import BuffActivityLogDatabase
from src.database.buff_management.buff_database import BuffDatabase
from src.database.buff_management.buff_notify_database import BuffNotifyDatabase
from src.database.buff_management.buff_farm_database import BuffFarmDatabase
from src.database.meloncloud.meloncloud_beast_character_database import MelonCloudBeastCharacterDatabase
from src.database.meloncloud.meloncloud_book_database import MelonCloudBookDatabase
from src.database.meloncloud.meloncloud_book_page_database import MelonCloudBookPageDatabase
from src.database.meloncloud.meloncloud_crypto_portfolios_database import MelonCloudCryptoPortfoliosDatabase
from src.database.meloncloud.meloncloud_people_database import MelonCloudPeopleDatabase
from src.database.meloncloud.meloncloud_twitter_database import MelonCloudTwitterDatabase
from src.environments.database_config import get_db, meloncloud_engine, buff_management_engine

from src.environments.share_environment import SRC_DIR
from src.routers import user, page, playground
from src.routers.meloncloud.meloncloud_twitter_api import check_tweet_has_deleted
from src.routers.poc.jwt import jwt_poc
from src.routers.poc.oauth import oauth_poc
from src.routers.security import password_generator_api as pwg_api
from src.tools.configure_app import configure_timing, configure_cors


def include_router_page(app):
    app.include_router(page.router, prefix="", tags=["webpage"])


def include_router(app):
    # twitter_app.include_router(twitter_api.router, prefix="/api/twitter", tags=["Twitter"])
    # app.include_router(pwg_api.router, prefix="/api/security", tags=["Random Password Generator"])
    app.include_router(jwt_poc.router, prefix="/poc/jwt", tags=["JWT"])
    app.include_router(oauth_poc.router, prefix="/poc/oauth", tags=["OAuth2"])
    app.include_router(playground.router, prefix="/playground", tags=["playground"])
    app.include_router(user.router, prefix="/user", tags=["users"])


def configure_static(app):
    app.mount("/static", StaticFiles(directory=str(Path(SRC_DIR, 'static'))), name="static")


def configure_sub_application(app):
    # app.mount("/api/v1", WSGIMiddleware(flask_app))
    app.mount("/api/v2/twitter", twitter_app)
    app.mount("/api/v3/twitter", meloncloud_twitter_app)
    app.mount("/api/v2/security/pwg_v2", pwg_app_v2)
    app.mount("/api/v2/buff", buff_app)
    app.mount("/api/v2/meloncloud-book", meloncloud_book_app)
    app.mount("/api/v2/database-backup", database_backup_hub_app)
    app.mount("/api/v2/crypto", crypto_portfolios_app)


def init_app():
    app = FastAPI(docs_url=None, redoc_url=None)
    include_router_page(app)
    configure_sub_application(app)
    configure_static(app)

    subapp = FastAPI()
    include_router(subapp)
    configure_timing(subapp)
    configure_cors(subapp)

    app.mount("/api/v2.0-alpha", subapp)

    return app


app = init_app()


@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )


@app.get("/", include_in_schema=False)
async def index():
    return RedirectResponse(url="home")


@app.get("/api/v2", include_in_schema=False)
async def index_v2():
    return RedirectResponse(url="v2.0-alpha/docs/")


@app.get("/connect", include_in_schema=False)
async def connect():
    return "Connected!"


@app.get("/wakeup", include_in_schema=False)
async def wakeup(db: Session = Depends(get_db)):
    check_tweet_has_deleted(db)
    return "I'm Waked!"


@app.get("/create_database", include_in_schema=False)
async def create_database():
    MelonCloudTwitterDatabase.__table__.create(meloncloud_engine)
    # MelonCloudPeopleDatabase.__table__.create(meloncloud_engine)
    #MelonCloudBeastCharacterDatabase.__table__.create(meloncloud_engine)
    # BuffFarmDatabase.__table__.create(buff_management_engine)
    #BuffDatabase.__table__.create(buff_management_engine)
    #BuffActivityLogDatabase.__table__.create(buff_management_engine)
    #BuffNotifyDatabase.__table__.create(buff_management_engine)
    # MelonCloudBookDatabase.__table__.create(meloncloud_engine)
    # MelonCloudBookPageDatabase.__table__.create(meloncloud_engine)
    # MelonCloudCryptoPortfoliosDatabase.__table__.create(meloncloud_engine)

    return "Database Created!"


if __name__ == "__main__":
    uvicorn.run("app:app")

handler = Mangum(app=app)