from enum import Enum
from typing import List

from pydantic.color import Color
from pydantic.networks import HttpUrl
from pydantic.types import SecretStr, PastDate, PositiveInt, date

from environment import TWITTER_SECRET_PASSWORD
from fastapi import HTTPException, status
from pydantic import BaseModel, validator, constr

from src.database.meloncloud.meloncloud_twitter_database import MelonCloudTwitterDatabase
from src.enums.sorting_enum import SortingEnum, SortingTweet
from src.tools.as_form import as_form

class TweetMediaType(str, Enum):
    PHOTO = "PHOTO"
    VIDEO = "VIDEO"
    TEXT = "TEXT"


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

class RequestTweetQueryModel(BaseModel):
    event: str = None
    hashtag: str = None
    account_id: str = None
    account_name: str = None
    me_like: bool = None
    type :TweetMediaType = None
    mention_id: str = None
    mention_name: str = None
    start_date: date = None
    end_date: date = None
    limit: PositiveInt = None
    page: PositiveInt = None
    infinite: bool = None
    sorting: SortingTweet = None
    deleted: bool = None


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
