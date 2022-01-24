from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi_jwt_auth.exceptions import AuthJWTException
from flask import Flask, escape, request
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.responses import RedirectResponse
# from fastapi_jwt_auth.exceptions import AuthJWTException
from fastapi.responses import JSONResponse

from src.apps.v1.flask_app import app as flask_app
from src.apps.v2.twitter_app import app as twitter_app
from src.apps.v2.buff_app import app as buff_app
from src.apps.v2.pwg_app import app as pwg_app_v2
from src.database.buff_management.buff_activity_log_database import BuffActivityLogDatabase
from src.database.buff_management.buff_database import BuffDatabase
from src.database.buff_management.buff_notify_database import BuffNotifyDatabase
from src.database.buff_management.farm_database import FarmDatabase
from src.database.meloncloud.meloncloud_book_database import MelonCloudBookDatabase
from src.database.meloncloud.meloncloud_book_page_database import MelonCloudBookPageDatabase

from src.database.melondev_twitter_database import MelonDevTwitterDatabase
from src.environment.database import engine
from src.environment.share_environment import SRC_DIR
from src.routers import user, page, playground
from src.routers.poc.jwt import jwt_poc
from src.routers.poc.oauth import oauth_poc
from src.routers.security import password_generator_api as pwg_api
from src.tools.configure_app import configure_timing, configure_cors


def include_router_page(app):
    app.include_router(page.router, prefix="", tags=["webpage"])


def include_router(app):
    # twitter_app.include_router(twitter_api.router, prefix="/api/twitter", tags=["Twitter"])
    # app.include_router(pwg_api.router, prefix="/api/security", tags=["Random Password Generator"])
    app.include_router(jwt_poc.router, prefix="/api/poc/jwt", tags=["JWT"])
    app.include_router(oauth_poc.router, prefix="/api/poc/oauth", tags=["OAuth2"])
    app.include_router(playground.router, prefix="/api/playground", tags=["playground"])
    app.include_router(user.router, prefix="/api/user", tags=["users"])


def configure_static(app):
    app.mount("/static", StaticFiles(directory=str(Path(SRC_DIR, 'static'))), name="static")


def configure_sub_application(app):
    app.mount("/api/v1", WSGIMiddleware(flask_app))
    app.mount("/api/v2/twitter", twitter_app)
    app.mount("/api/v2/security/pwg_v2", pwg_app_v2)
    app.mount("/api/v2/buff", buff_app)


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
async def wakeup():
    return "I'm Waked!"


@app.get("/create_database", include_in_schema=False)
async def create_database():
    # MelonDevTwitterDatabase.__table__.create(engine)
    # FarmDatabase.__table__.create(engine)
    # BuffDatabase.__table__.create(engine)
    # BuffActivityLogDatabase.__table__.create(engine)
    # BuffNotifyDatabase.__table__.create(engine)
    # MelonCloudBookDatabase.__table__.create(engine)
    # MelonCloudBookPageDatabase.__table__.create(engine)

    return "Database Created!"


if __name__ == "__main__":
    uvicorn.run("app:app")
