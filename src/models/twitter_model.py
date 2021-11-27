from fastapi import HTTPException, status
from pydantic import BaseModel, validator

from environment import TWITTER_SECRET_PASSWORD
from src.database.melondev_twitter_database import MelonDevTwitterDatabase


class TwitterValidatorModel(BaseModel):
    token: str

    @validator('token')
    def token_authorize(cls, value):
        if TWITTER_SECRET_PASSWORD != value:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="UNAUTHORIZED")


class ResponseTweetModel:
    tweet: MelonDevTwitterDatabase
    media_urls: list

    def __init__(self,tweet,media_urls):
        self.tweet = tweet
        self.media_urls = media_urls


class TwitterAnalyzeModel(TwitterValidatorModel):
    tag: str
    url: str
