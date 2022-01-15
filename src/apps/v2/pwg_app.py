from fastapi import FastAPI
from src.tools.configure_app import configure_cors,configure_timing
from src.routers.security import password_generator_api as pwg_api


app = FastAPI()

configure_cors(app)
configure_timing(app)

app.include_router(pwg_api.router, tags=["Random Password Generator"])

