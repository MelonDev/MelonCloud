from fastapi import HTTPException, status
from pydantic import BaseModel, validator

from environment import TWITTER_SECRET_PASSWORD
from src.database.melondev_twitter_database import MelonDevTwitterDatabase
from src.enums.profile_enum import ProfileQueryEnum
from src.enums.type_enum import FileTypeEnum, ImageQualityEnum
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


class TweetPeopleModel:
    profile_banner: str
    profile_image: str
    profile_text_color: str
    profile_sidebar_fill_color: str
    profile_sidebar_border_color: str
    profile_link_color: str
    id: str
    name: str
    screen_name: str
    location: str
    description: str
    protected: bool
    followers_count: int
    friends_count: int
    favourites_count: int
    statuses_count: int

    def __init__(self, id, name, screen_name, protected: bool):
        self.id = id
        self.name = name
        self.screen_name = screen_name
        self.protected = protected

    def set_description(self, location, description):
        self.location = location
        self.description = description

    def set_counters(self, followers_count: int, friends_count: int, favourites_count: int, statuses_count: int):
        self.followers_count = followers_count
        self.friends_count = friends_count
        self.favourites_count = favourites_count
        self.statuses_count = statuses_count

    def set_profile(self, profile_banner, profile_image, profile_text_color, profile_sidebar_fill_color,
                    profile_sidebar_border_color, profile_link_color):
        self.profile_banner = profile_banner
        self.profile_image = profile_image
        self.profile_text_color = profile_text_color
        self.profile_sidebar_fill_color = profile_sidebar_fill_color
        self.profile_sidebar_border_color = profile_sidebar_border_color
        self.profile_link_color = profile_link_color


class TweetPeopleResponseModel:
    profile: TweetPeopleModel
    count: int

    def __init__(self, profile: TweetPeopleModel, count: int):
        self.profile = profile
        self.count = count


class RequestAnalyzeModel(TwitterValidatorModel):
    tag: str
    url: str
    like: bool = False
    secret_like: bool = False


class RequestDirectAnalyzeModel(RequestAnalyzeModel):
    data: dict
    tweet_id: str


class RequestTweetQueryModel(BaseModel):
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


class RequestMediaQueryModel(RequestTweetQueryModel):
    quality: ImageQualityEnum = None
    file_type: FileTypeEnum = None


class RequestPeopleQueryModel(BaseModel):
    event: str = None
    hashtag: str = None
    start_date: str = None
    end_date: str = None
    me_like: bool = None
    limit: int = None
    page: int = None
    infinite: bool = None
    sorting: SortingEnum = None


class RequestIdentityModel(TwitterValidatorModel):
    id: str


class RequestTweetModel(BaseModel):
    tweet_id: str
    raw: bool = None


class RequestProfileModel(BaseModel):
    account: str
    query: ProfileQueryEnum = None
    event: str = None
    hashtag: str = None
    start_date: str = None
    end_date: str = None
    me_like: bool = None
    sorting: SortingEnum = None
    limit: int = None
    page: int = None
    infinite: bool = None
    deleted: bool = None


class RequestPlayModel:
    tweet_id: str = None
    name: str
    raw: bool = None


class TweetProfileResponseModel():
    profile: RequestProfileModel
    tweet: list

    def __init__(self, profile: RequestProfileModel, tweet: list = None):
        self.profile = profile
        self.tweet = tweet