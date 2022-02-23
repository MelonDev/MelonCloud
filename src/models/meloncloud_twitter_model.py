from enum import Enum
from typing import List

from environment import TWITTER_SECRET_PASSWORD
from fastapi import HTTPException, status
from pydantic import BaseModel, validator

from src.database.meloncloud.meloncloud_twitter_database import MelonCloudTwitterDatabase
from src.tools.as_form import as_form


class ValidatorModel(BaseModel):
    token: str

    @validator('token')
    def token_authorize(cls, value):
        if TWITTER_SECRET_PASSWORD != value:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="UNAUTHORIZED")


class TweetAction(str, Enum):
    LIKE = "Like"
    SECRET_LIKE = "Secret like"
    ONLY_MEDIA = "Only media"


@as_form
class RequestAnalyzeModel(ValidatorModel):
    tag: str
    url: str
    action: TweetAction = None


class MelonCloudTweetResponseModel:
    tweet: MelonCloudTwitterDatabase
    media_urls: List[str]

    def __init__(self, tweet, media_urls):
        self.tweet = tweet
        self.media_urls = media_urls
