from environment import TWITTER_VIEWER_PASSWORD
from src.database.meloncloud.meloncloud_beast_character_database import MelonCloudBeastCharacterDatabase
from src.database.meloncloud.meloncloud_book_database import MelonCloudBookDatabase
from src.database.meloncloud.meloncloud_book_page_database import MelonCloudBookPageDatabase
from src.database.meloncloud.meloncloud_people_database import MelonCloudPeopleDatabase
from src.database.meloncloud.meloncloud_twitter_database import MelonCloudTwitterDatabase
from src.engines.twitter_engines import get_user_profile, hasFavorited, like_tweet
from src.enums.profile_enum import ProfileTypeEnum
from src.models.meloncloud_twitter_model import DatabaseQueryName, TweetMediaType, HashtagQueryDate, \
    RequestMediaQueryModel, RequestPeopleQueryModel, TweetAction, RequestAnalyzeModel, RequestPeopleQueryForRankModel
from src.routers.meloncloud.meloncloud_error_response import bad_request_exception
from fastapi import Response
import csv
import io
from urllib.parse import urlparse
from sqlalchemy.orm import Session

from src.tools.onedrive_adapter import send_url_to_meloncloud_onedrive


def get_profile(account: str):
    if account.isdigit():
        package = get_user_profile(account, type=ProfileTypeEnum.USER_ID)
        if package is None:
            package = get_user_profile(account, type=ProfileTypeEnum.SCREEN_NAME)
    else:
        package = get_user_profile(account, type=ProfileTypeEnum.SCREEN_NAME)
        if package is None:
            package = get_user_profile(account, type=ProfileTypeEnum.USER_ID)
    return package


def packing_backup(data, filename):
    headers = list(data[0].export.keys())

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for i in data:
        x = list(v for k, v in i.export.items())
        writer.writerow(x)
    output.seek(0)

    res = Response(content=output.read(), media_type="text/csv")
    res.headers[
        "Content-Disposition"
    ] = f"attachment; filename=" + filename + ".csv"
    return res


def media_query_to_people_query(params: RequestMediaQueryModel) -> RequestPeopleQueryForRankModel:
    peoples_params = RequestPeopleQueryForRankModel()
    peoples_params.event = params.event
    peoples_params.hashtag = params.hashtag
    peoples_params.start_date = params.start_date
    peoples_params.end_date = params.end_date
    peoples_params.me_like = params.me_like
    peoples_params.limit = 30
    peoples_params.page = 0
    return peoples_params


def is_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def get_day(query: HashtagQueryDate) -> int:
    return {
        HashtagQueryDate.DAY: 1,
        HashtagQueryDate.WEEK: 7,
        HashtagQueryDate.MONTH: 30,
        HashtagQueryDate.QUARTER: 90,
        HashtagQueryDate.YEAR: 365,
        HashtagQueryDate.ALL: int(365 * 10),
        HashtagQueryDate.CUSTOM: 0,
    }[query]


def get_file_type(query: TweetMediaType) -> int:
    return {
        TweetMediaType.PHOTO: 1,
        HashtagQueryDate.WEEK: 7,
        HashtagQueryDate.MONTH: 30,
        HashtagQueryDate.QUARTER: 90,
        HashtagQueryDate.YEAR: 365,
        HashtagQueryDate.ALL: int(365 * 10),
        HashtagQueryDate.CUSTOM: 0,
    }[query]


def media_result_packing(data, payload):
    if payload is None:
        return data
    else:
        return {
            "payload": payload,
            "media": data
        }


def is_circle_language(value) -> bool:
    return str(value) == 'ja' or str(value) == 'zh'


def has_in_my_history(db, account) -> bool:
    return db.query(
        MelonCloudTwitterDatabase).filter(MelonCloudTwitterDatabase.account_id.contains(str(account))).count() > 0


def get_count_of_database(database) -> int:
    if database is None:
        bad_request_exception()
    return int(database.count())


def get_database_name(name: DatabaseQueryName):
    return {
        DatabaseQueryName.MelonCloudTwitterDatabase: MelonCloudTwitterDatabase.__tablename__,
        DatabaseQueryName.MelonCloudPeopleDatabase: MelonCloudPeopleDatabase.__tablename__,
        DatabaseQueryName.MelonCloudBeastCharacterDatabase: MelonCloudBeastCharacterDatabase.__tablename__,
        DatabaseQueryName.MelonCloudBookDatabase: MelonCloudBookDatabase.__tablename__,
        DatabaseQueryName.MelonCloudBookPageDatabase: MelonCloudBookPageDatabase.__tablename__
    }[name]


def get_database(db, name: DatabaseQueryName):
    return {
        DatabaseQueryName.MelonCloudTwitterDatabase: db.query(MelonCloudTwitterDatabase),
        DatabaseQueryName.MelonCloudPeopleDatabase: db.query(MelonCloudPeopleDatabase),
        DatabaseQueryName.MelonCloudBeastCharacterDatabase: db.query(MelonCloudBeastCharacterDatabase),
        DatabaseQueryName.MelonCloudBookDatabase: db.query(MelonCloudBookDatabase),
        DatabaseQueryName.MelonCloudBookPageDatabase: db.query(MelonCloudBookPageDatabase)

    }[name]


def is_overflow(page: int, total_page: int):
    if page >= total_page:
        bad_request_exception(
            f"Page Overflow : Total page is {total_page} and the page starts at page 0 to {total_page - 1}")


def is_action(value: str, action: str) -> bool:
    if value is None:
        return False
    return value == action


def is_not_action(value: str, action: str) -> bool:
    if value is None:
        return True
    return value != action


def is_not_retweet(value) -> bool:
    return str(value)[:3] != 'RT '


async def processing_tweet(request: RequestAnalyzeModel, package, tweet_id: str, db: Session, enable_commit=True):
    if request.tag[:8] == 'HASHTAG ' and is_not_retweet(package.tweet.message):
        package.tweet.event = request.tag
        if is_action(request.action, TweetAction.ONLY_MEDIA) and len(package.media_urls) > 0:
            db.add(package.tweet)
            if enable_commit:
                db.commit()
        elif is_not_action(request.action, TweetAction.ONLY_MEDIA) and (
                is_circle_language(package.tweet.language) or has_in_my_history(db, package.tweet.account_id)):
            db.add(package.tweet)
            if enable_commit:
                db.commit()

    elif is_not_retweet(package.tweet.message):
        item = db.query(MelonCloudTwitterDatabase).get(tweet_id)
        favorited = await hasFavorited(tweet_id)
        if is_action(request.action, TweetAction.LIKE) and not favorited:
            await like_tweet(tweet_id)
        if item is not None:
            if request.tag == 'ME LIKE':
                await send_url_to_meloncloud_onedrive(package.media_urls)
                item.memories = True
                if is_action(request.action, TweetAction.LIKE) or is_action(request.action, TweetAction.SECRET_LIKE):
                    item.event = request.tag
                db.add(item)
                if enable_commit:
                    db.commit()
        else:
            package.tweet.event = request.tag
            if request.tag == 'ME LIKE':
                package.tweet.memories = True
                await send_url_to_meloncloud_onedrive(package.media_urls)
            db.add(package.tweet)
            if enable_commit:
                db.commit()


