import timestamp as timestamp
from fastapi import HTTPException, status
from fastapi.params import Query

from pydantic import BaseModel, validator, Field
from enum import Enum, IntEnum

from pydantic.types import SecretStr

from environment import TWITTER_SECRET_PASSWORD
from src.database.melondev_twitter_database import MelonDevTwitterDatabase
from src.enums.type_enum import MediaTypeEnum, FileTypeEnum
from src.enums.sorting_enum import SortingEnum


class TwitterValidatorModel(BaseModel):
    token: str

    @validator('token')
    def token_authorize(cls, value):
        if TWITTER_SECRET_PASSWORD != value:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="UNAUTHORIZED")


class TweetResponseModel:
    tweet: MelonDevTwitterDatabase
    media_urls: list

    def __init__(self, tweet, media_urls):
        self.tweet = tweet
        self.media_urls = media_urls


class TweetMediaURLResponseModel:
    id: str
    thumbnail: str
    url: str

    def __init__(self, id, url, thumbnail):
        self.id = id
        self.url = url
        self.thumbnail = thumbnail


class TweetMediaResponseModel(TweetMediaURLResponseModel):
    id: str
    tweet_id: str
    account_id: str
    timestamp: str

    def __init__(self, id, url, tweet_id, account_id, timestamp, thumbnail):
        super().__init__(id, url, thumbnail)
        self.tweet_id = tweet_id
        self.account_id = account_id
        self.timestamp = timestamp


class RequestAnalyzeModel(TwitterValidatorModel):
    tag: str
    url: str
    like: bool = None
    secret_like: bool = None


class RequestQueryModel(BaseModel):
    event: str = None
    hashtag: str = None
    account_id: str = None
    account_name: str = None
    me_like: bool = None
    mention_id: str = None
    mention_name: str = None
    start_date: str = None
    end_date: str = None
    limit: int = None
    page: int = None
    infinite: bool = None
    sorting: SortingEnum = None
    deleted: bool = None


class RequestMediaQueryModel(RequestQueryModel):
    media_type: MediaTypeEnum = None
    file_type: FileTypeEnum = None


class RequestIdentityModel(TwitterValidatorModel):
    id: str


class RequestTweetModel(BaseModel):
    tweet_id: str
    raw: bool = None
