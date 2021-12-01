import timestamp as timestamp
from fastapi import HTTPException, status
from fastapi.params import Query

from pydantic import BaseModel, validator, Field

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

    def __init__(self, tweet, media_urls):
        self.tweet = tweet
        self.media_urls = media_urls


class TweetPhotoURLResponseModel:
    id: str
    url: str

    def __init__(self, id, url):
        self.id = id
        self.url = url


class TweetPhotoResponseModel(TweetPhotoURLResponseModel):
    tweet_id: str
    account_id: str
    timestamp: str

    def __init__(self, id, url, tweet_id, account_id, timestamp):
        super().__init__(id, url)
        self.tweet_id = tweet_id
        self.account_id = account_id
        self.timestamp = timestamp


class TwitterAnalyzeModel(TwitterValidatorModel):
    tag: str
    url: str
    like: bool = None
    secret_like: bool = None


class TwitterQueryModel(BaseModel):
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
    unlimited: bool = None
    asc: bool = None
    deleted: bool = None


class TwitterUnlikeModel(TwitterValidatorModel):
    id: str
