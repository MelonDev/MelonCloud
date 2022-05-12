from fastapi import FastAPI

from src.routers import azure_poc_api
from src.tools.configure_app import configure_cors, configure_timing

app = FastAPI(
    title="MelonCloud",
    servers=[
        {"url": "https://meloncloud.herokuapp.com/api/v2/azure", "description": "MelonCloud"},
    ],
)

configure_cors(app)
configure_timing(app)

app.include_router(azure_poc_api.router)