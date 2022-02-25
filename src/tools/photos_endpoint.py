from sqlalchemy.engine import Row

from src.enums.type_enum import ImageQualityEnum
from src.models.meloncloud_twitter_model import MelonCloudTweetPeopleModel, MelonCloudTweetPeopleResponseModel
from src.models.twitter_model import TweetMediaResponseModel, TweetMediaURLResponseModel, TweetPeopleResponseModel, \
    TweetPeopleModel


def _photo_key(value) -> str:
    return value[len("https://pbs.twimg.com/media/"):value.find(".jpg")]


def _video_key(value) -> str:
    return value[len("https://video.twimg.com/ext_tw_video/"):value.find(".mp4")]


def _photo_type_url(value, type: ImageQualityEnum) -> str:
    if "http://" in value:
        print("FOUND")
        value = value.replace("http://", "https://")
    return value + ":" + (type if type is not None else ImageQualityEnum.ORIG).lower()


def tweet_photo_url_endpoint(value, type: ImageQualityEnum) -> TweetMediaURLResponseModel:
    return TweetMediaURLResponseModel(id=_photo_key(value), url=_photo_type_url(value, type),
                                      thumbnail=_photo_type_url(value, type=ImageQualityEnum.THUMB))


def tweet_photo_endpoint(row: Row, media_type: ImageQualityEnum) -> TweetMediaResponseModel:
    return TweetMediaResponseModel(id=_photo_key(row[0]), url=_photo_type_url(row[0], type=media_type), tweet_id=row[1],
                                   account_id=row[2], timestamp=row[3],
                                   thumbnail=_photo_type_url(row[0], type=ImageQualityEnum.THUMB))


def tweet_video_endpoint(row: Row) -> TweetMediaResponseModel:
    return TweetMediaResponseModel(id=row[1], url=row[0], tweet_id=row[1],
                                   account_id=row[2], timestamp=row[3], thumbnail=row[4])


def people_endpoint(profile: TweetPeopleModel, count: int):
    if profile is None or count is None:
        return None
    return TweetPeopleResponseModel(profile=profile, count=count)


def tweet_people_endpoint(profile: MelonCloudTweetPeopleModel, count: int):
    if profile is None or count is None:
        return None
    return MelonCloudTweetPeopleResponseModel(profile=profile, count=count)
