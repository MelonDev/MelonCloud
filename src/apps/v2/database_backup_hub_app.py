from fastapi import FastAPI

from src.routers import database_backup_hub_api
from src.tools.configure_app import configure_cors, configure_timing

app = FastAPI(
    title="Database Backup",
    servers=[
        {"url": "https://meloncloud.herokuapp.com/api/v2/database-backup", "description": "Database Backup"},
    ],
)

configure_cors(app)
configure_timing(app)

app.include_router(database_backup_hub_api.router)