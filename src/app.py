from pathlib import Path
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.environment.share_environment import SRC_DIR
from src.routers import user, page, playground
from src.routers.security import password_generator_api as pwg_api


def include_router(app):
    app.include_router(page.router, prefix="", tags=["webpage"])
    app.include_router(playground.router, prefix="", tags=["playground"])
    app.include_router(user.router, prefix="/user", tags=["users"])
    app.include_router(pwg_api.router, prefix="/security", tags=["security"])


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

if __name__ == "__main__":
    uvicorn.run("app:app")
