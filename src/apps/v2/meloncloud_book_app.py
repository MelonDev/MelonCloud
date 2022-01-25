from fastapi import FastAPI

from src.routers import meloncloud_book_api
from src.tools.configure_app import configure_cors, configure_timing

app = FastAPI(
    title="Bookshelf",
    servers=[
        {"url": "https://meloncloud.herokuapp.com/api/v2/meloncloud-book", "description": "Bookshelf"},
    ],
)

configure_cors(app)
configure_timing(app)

app.include_router(meloncloud_book_api.router)