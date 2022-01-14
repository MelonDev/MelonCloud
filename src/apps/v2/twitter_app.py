from fastapi import FastAPI
from src.routers import twitter_api
from src.tools.configure_app import configure_cors,configure_timing

app = FastAPI()

configure_cors(app)
configure_timing(app)

app.include_router(twitter_api.router, tags=["Twitter"])

