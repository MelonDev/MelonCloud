from enum import Enum
from typing import List

from google.type.calendar_period_pb2 import QUARTER
from pydantic.color import Color
from pydantic.networks import HttpUrl
from pydantic.types import SecretStr, PastDate, PositiveInt, date

from environment import TWITTER_SECRET_PASSWORD, TWITTER_VIEWER_PASSWORD
from fastapi import HTTPException, status
from pydantic import BaseModel, validator, constr

from src.database.meloncloud.meloncloud_twitter_database import MelonCloudTwitterDatabase
from src.enums.profile_enum import ProfileQueryEnum
from src.enums.sorting_enum import SortingEnum, SortingTweet
from src.enums.type_enum import ImageQualityEnum, FileTypeEnum, MelonCloudFileTypeEnum
from src.tools.as_form import as_form


class TweetMediaType(str, Enum):
    PHOTO = "PHOTO"
    VIDEO = "VIDEO"
    TEXT = "TEXT"


class HashtagQueryDate(str, Enum):
    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"
    QUARTER = "QUARTER"
    YEAR = "YEAR"
    ALL = "ALL"
    CUSTOM = "CUSTOM"


class BackupQueryDate(str, Enum):
    MONTH = "MONTH"
    YEAR = "YEAR"
    CUSTOM = "CUSTOM"


class MediaExtraOptional(str, Enum):
    PROFILE = "PROFILE"
    PEOPLES = "PEOPLES"


class ValidatorModel(BaseModel):
    token: str

    @validator('token')
    def token_authorize(cls, value):
        if not (TWITTER_SECRET_PASSWORD == value or TWITTER_VIEWER_PASSWORD == value):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="UNAUTHORIZED")


class TweetAction(str, Enum):
    LIKE = "LIKE"
    SECRET_LIKE = "SECRET_LIKE"
    ONLY_MEDIA = "ONLY_MEDIA"


class RequestTweetModel(ValidatorModel):
    tweet_id: str
    raw: bool = None


class RequestPeopleQueryModel(ValidatorModel):
    event: str = None
    hashtag: str = None
    start_date: date = None
    end_date: date = None
    me_like: bool = None
    limit: PositiveInt = None
    page: PositiveInt = None
    infinite: bool = None
    sorting: SortingTweet = None


class TweetQueryBaseModel(ValidatorModel):
    event: str = None
    account: str = None
    me_like: bool = None
    type: TweetMediaType = None
    mention_id: str = None
    mention_name: str = None
    start_date: date = None
    end_date: date = None
    limit: PositiveInt = None
    page: PositiveInt = None
    sorting: SortingTweet = None
    deleted: bool = None


class RequestTweetQueryModel(TweetQueryBaseModel):
    hashtag: str = None
    infinite: bool = None


class RequestHashtagQueryModel(TweetQueryBaseModel):
    query: HashtagQueryDate = None


def get_hashtag_dict(key, value):
    return {
        'name': str(key),
        'value': value
    }


class RequestMediaQueryModel(ValidatorModel):
    quality: ImageQualityEnum = None
    hashtag: str = None
    event: str = None
    account: str = None
    extra_optional: MediaExtraOptional = None
    me_like: bool = None
    type: MelonCloudFileTypeEnum = None
    mention_id: str = None
    mention_name: str = None
    start_date: date = None
    end_date: date = None
    limit: PositiveInt = None
    page: PositiveInt = None
    sorting: SortingTweet = None
    deleted: bool = None


class RequestProfileModel(ValidatorModel):
    account: str
    query: ProfileQueryEnum = None
    event: str = None
    hashtag: str = None
    start_date: date = None
    end_date: date = None
    me_like: bool = None
    sorting: SortingTweet = None
    limit: int = None
    page: int = None
    infinite: bool = None
    deleted: bool = None


class MelonCloudTweetPeopleModel:
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


class MelonCloudTweetPeopleResponseModel:
    profile: MelonCloudTweetPeopleModel
    count: int

    def __init__(self, profile: MelonCloudTweetPeopleModel, count: int):
        self.profile = profile
        self.count = count


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


class MelonCloudBackupModel(BaseModel):
    date_range: BackupQueryDate
    start_date: date = None
    end_date: date = None
