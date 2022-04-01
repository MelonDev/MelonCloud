from fastapi import FastAPI

from src.routers.meloncloud import meloncloud_crypto_portfolios_api
from src.tools.configure_app import configure_cors, configure_timing

app = FastAPI(
    title="CryptoPortfolios",
    servers=[
        {"url": "https://meloncloud.herokuapp.com/api/v2/crypto", "description": "CryptoPortfolios"},
    ],
)

configure_cors(app)
configure_timing(app)

app.include_router(meloncloud_crypto_portfolios_api.router)