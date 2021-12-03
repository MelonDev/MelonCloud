from pathlib import Path
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse
from timing_asgi import TimingMiddleware, TimingClient
from timing_asgi.integrations import StarletteScopeToName

from src.environment.share_environment import SRC_DIR
from src.routers import user, page, playground
from src.routers.security import password_generator_api as pwg_api
from src.routers import twitter_api as twitter_api
from src.tools.log import Colors, log


class PrintTimings(TimingClient):
    def timing(self, metric_name, timing, tags):
        if 'time:wall' in tags:
            time = "{:.5f}".format(timing)
            log.m("DURATION: " + time, color=Colors.yellow)


def include_router(app):
    app.include_router(page.router, prefix="", tags=["webpage"])
    app.include_router(twitter_api.router, prefix="/api/twitter", tags=["Twitter"])
    app.include_router(pwg_api.router, prefix="/api/security", tags=["Random Password Generator"])
    app.include_router(playground.router, prefix="/api/playground", tags=["playground"])
    app.include_router(user.router, prefix="/api/user", tags=["users"])


def configure_static(app):
    app.mount("/static", StaticFiles(directory=str(Path(SRC_DIR, 'static'))), name="static")


def configure_cors(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )


def init_app():
    app = FastAPI()
    include_router(app)
    configure_static(app)
    return app


app = init_app()

app.add_middleware(
    TimingMiddleware,
    client=PrintTimings(),
    metric_namer=StarletteScopeToName(prefix="meloncloud", starlette_app=app)
)


@app.get("/", include_in_schema=False)
async def index():
    return RedirectResponse(url="/docs/")


if __name__ == "__main__":
    uvicorn.run("app:app")
