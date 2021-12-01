from sqlalchemy.engine import Row

from src.models.twitter_model import TweetPhotoResponseModel, TweetPhotoURLResponseModel


def _photo_key(value) -> str:
    return value[len("https://pbs.twimg.com/media/"):value.find(".jpg")]


def _photo_orig_url(value) -> str:
    return value + ":orig"


def tweet_photo_url_endpoint(value) -> TweetPhotoURLResponseModel:
    return TweetPhotoURLResponseModel(id=_photo_key(value), url=_photo_orig_url(value))


def tweet_photo_endpoint(row: Row) -> TweetPhotoResponseModel:
    return TweetPhotoResponseModel(id=_photo_key(row[0]), url=_photo_orig_url(row[0]), tweet_id=row[1],
                                   account_id=row[2], timestamp=row[3])
