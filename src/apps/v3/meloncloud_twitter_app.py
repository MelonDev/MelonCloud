from fastapi import FastAPI
from src.routers.meloncloud import meloncloud_twitter_api, meloncloud_people_api
from src.tools.configure_app import configure_cors, configure_timing

app = FastAPI(
    title="MelonCloud",
    servers=[
        {"url": "https://meloncloud.herokuapp.com/api/v3/twitter", "description": "MelonCloud"},
    ],
)

configure_cors(app)
configure_timing(app)

app.include_router(meloncloud_twitter_api.router, tags=["Twitter"])
app.include_router(meloncloud_people_api.router, tags=["Peoples"])
