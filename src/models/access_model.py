from pydantic import BaseModel, validator
from fastapi import HTTPException, status

from src.environment import TWITTER_REFRESH_SECRET_PASSWORD


class AccessTwitterValidatorModel(BaseModel):
    token: str

    @validator('token')
    def token_authorize(cls, value):
        if TWITTER_REFRESH_SECRET_PASSWORD != value:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="UNAUTHORIZED")
