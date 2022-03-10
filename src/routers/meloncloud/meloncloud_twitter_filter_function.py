from sqlalchemy import func, asc, desc

from src.database.meloncloud.meloncloud_twitter_database import MelonCloudTwitterDatabase
from src.engines.twitter_engines import get_user_id
from src.enums.sorting_enum import SortingTweet
from src.enums.type_enum import MelonCloudFileTypeEnum
from src.models.meloncloud_twitter_model import RequestPeopleQueryModel, RequestProfileModel, RequestHashtagQueryModel, \
    HashtagQueryDate, RequestTweetQueryModel, RequestMediaQueryModel, RequestPeopleQueryForRankModel
from src.routers.meloncloud.meloncloud_error_response import bad_request_exception
from src.routers.meloncloud.meloncloud_twitter_extension_function import get_database, get_profile
from src.tools.converters.datetime_converter import append_timezone
import datetime as dt
from sqlalchemy.orm.query import Query as DBQuery


def database_for_backup(db, name, start_date=None, end_date=None):
    database = get_database(db, name)

    if start_date is not None:
        database = database.filter(MelonCloudTwitterDatabase.stored_at >= start_date)
    if end_date is not None:
        database = database.filter(MelonCloudTwitterDatabase.stored_at <= end_date)
    return database


def append_limit_to_database(params, database):
    if not bool(params.infinite):
        page = params.page if params.page is not None else 0
        limit = params.limit if params.limit is not None else 50
        database = database.limit(limit).offset(int(page * limit))
    return database


def database_media_type_categorize(db, file_type: MelonCloudFileTypeEnum):
    if file_type is MelonCloudFileTypeEnum.PHOTOS:
        return db.query(func.unnest(MelonCloudTwitterDatabase.photos), MelonCloudTwitterDatabase.id,
                        MelonCloudTwitterDatabase.account_id, MelonCloudTwitterDatabase.stored_at)
    elif file_type is MelonCloudFileTypeEnum.VIDEOS:
        return db.query(func.unnest(MelonCloudTwitterDatabase.videos), MelonCloudTwitterDatabase.id,
                        MelonCloudTwitterDatabase.account_id, MelonCloudTwitterDatabase.stored_at,
                        MelonCloudTwitterDatabase.thumbnail)
    elif file_type is MelonCloudFileTypeEnum.ALL:
        return db.query(func.unnest(MelonCloudTwitterDatabase.photos), func.unnest(MelonCloudTwitterDatabase.videos),
                        MelonCloudTwitterDatabase.thumbnail, MelonCloudTwitterDatabase.id,
                        MelonCloudTwitterDatabase.account_id, MelonCloudTwitterDatabase.stored_at)
    else:
        bad_request_exception()


def filtering_people_database(params: RequestPeopleQueryModel, db):
    database = db if type(db) is DBQuery else db.query(MelonCloudTwitterDatabase.account,
                                                       func.count(MelonCloudTwitterDatabase.account))

    if params is None:
        bad_request_exception()

    database = database.group_by(MelonCloudTwitterDatabase.account_id)

    if params.hashtag is not None:
        database = database.filter(MelonCloudTwitterDatabase.hashtags.any(params.hashtag))
    if params.event is not None:
        database = database.filter(MelonCloudTwitterDatabase.event.contains(params.event))
    if params.me_like is not None:
        database = database.filter(MelonCloudTwitterDatabase.memories.is_(params.me_like))
    if params.start_date is not None:
        ds = append_timezone(dt.datetime.strptime(f"{params.start_date} 00:00:00", "%Y-%m-%d %H:%M:%S"))
        database = database.filter(MelonCloudTwitterDatabase.stored_at >= ds)
    if params.end_date is not None:
        de = append_timezone(dt.datetime.strptime(f"{params.end_date} 23:59:59", '%Y-%m-%d %H:%M:%S'))
        database = database.filter(MelonCloudTwitterDatabase.stored_at <= de)

    return database


def filtering_people_for_rank_database(params: RequestPeopleQueryForRankModel, db):
    database = db if type(db) is DBQuery else db.query(MelonCloudTwitterDatabase.account,
                                                       func.count(MelonCloudTwitterDatabase.account))

    if params is None:
        bad_request_exception()

    database = database.group_by(MelonCloudTwitterDatabase.account_id)

    if params.hashtag is not None:
        database = database.filter(MelonCloudTwitterDatabase.hashtags.any(params.hashtag))
    if params.event is not None:
        database = database.filter(MelonCloudTwitterDatabase.event.contains(params.event))
    if params.me_like is not None:
        database = database.filter(MelonCloudTwitterDatabase.memories.is_(params.me_like))
    if params.start_date is not None:
        ds = append_timezone(dt.datetime.strptime(f"{params.start_date} 00:00:00", "%Y-%m-%d %H:%M:%S"))
        database = database.filter(MelonCloudTwitterDatabase.stored_at >= ds)
    if params.end_date is not None:
        de = append_timezone(dt.datetime.strptime(f"{params.end_date} 23:59:59", '%Y-%m-%d %H:%M:%S'))
        database = database.filter(MelonCloudTwitterDatabase.stored_at <= de)

    return database


def filtering_profile_database(params: RequestProfileModel, database):
    if database is None or params is None:
        bad_request_exception()
    if params.hashtag is not None:
        database = database.filter(MelonCloudTwitterDatabase.hashtags.any(params.hashtag))
    if params.event is not None:
        database = database.filter(MelonCloudTwitterDatabase.event.contains(params.event))
    if params.me_like is not None:
        database = database.filter(MelonCloudTwitterDatabase.memories.is_(params.me_like))
    if params.start_date is not None:
        ds = append_timezone(dt.datetime.strptime(f"{params.start_date} 00:00:00", "%Y-%m-%d %H:%M:%S"))
        database = database.filter(MelonCloudTwitterDatabase.addedAt >= ds)
    if params.end_date is not None:
        de = append_timezone(dt.datetime.strptime(f"{params.end_date} 23:59:59", '%Y-%m-%d %H:%M:%S'))
        database = database.filter(MelonCloudTwitterDatabase.addedAt <= de)

    if params.deleted is not None:
        database = database.filter(MelonCloudTwitterDatabase.deleted.is_(params.deleted))

    if params.sorting == SortingTweet.ASC:
        database = database.order_by(asc(MelonCloudTwitterDatabase.stored_at))
    else:
        database = database.order_by(desc(MelonCloudTwitterDatabase.stored_at))

    return database


def filtering_meloncloud_twitter_database_for_hashtags(params: RequestHashtagQueryModel, db, skip_datetime,
                                                       back_to_datetime):
    database = db if type(db) is DBQuery else db.query(func.unnest(MelonCloudTwitterDatabase.hashtags))
    if params is None:
        bad_request_exception()
    if params.mention_id is not None:
        database = database.filter(MelonCloudTwitterDatabase.mentions.any(params.mention_id))
    if params.mention_name is not None:
        database = database.filter(MelonCloudTwitterDatabase.mentions.any(get_user_id(params.mention_name)))
    if params.account is not None:
        account = get_profile(params.account)
        database = database.filter(MelonCloudTwitterDatabase.account_id.contains(account.id_str))
    if params.event is not None:
        database = database.filter(MelonCloudTwitterDatabase.event.contains(params.event))
    if params.type is not None:
        database = database.filter(MelonCloudTwitterDatabase.type.contains(params.type))
    if params.me_like is not None:
        print(database.count())
        database = database.filter(MelonCloudTwitterDatabase.memories.is_(params.me_like))
        print(database.count())

    if params.deleted is not None:
        database = database.filter(MelonCloudTwitterDatabase.deleted.is_(params.deleted))
    print(database.count())

    if params.query is HashtagQueryDate.CUSTOM:
        if params.start_date is not None:
            ds = append_timezone(dt.datetime.strptime(f"{params.start_date} 00:00:00", "%Y-%m-%d %H:%M:%S"))
            database = database.filter(MelonCloudTwitterDatabase.stored_at >= ds)
        if params.end_date is not None:
            de = append_timezone(dt.datetime.strptime(f"{params.end_date} 23:59:59", '%Y-%m-%d %H:%M:%S'))
            database = database.filter(MelonCloudTwitterDatabase.stored_at <= de)
    else:
        database = database.filter(
            MelonCloudTwitterDatabase.stored_at <= skip_datetime).filter(
            MelonCloudTwitterDatabase.stored_at >= back_to_datetime)

    if params.sorting == SortingTweet.ASC:
        database = database.order_by(asc(MelonCloudTwitterDatabase.stored_at))
    else:
        database = database.order_by(desc(MelonCloudTwitterDatabase.stored_at))

    return database


def filtering_meloncloud_twitter_database(params: RequestTweetQueryModel, db):
    database = db if type(db) is DBQuery else db.query(MelonCloudTwitterDatabase)

    if params is None:
        bad_request_exception()

    if params.hashtag is not None:
        database = database.filter(MelonCloudTwitterDatabase.hashtags.any(params.hashtag))
    if params.mention_id is not None:
        database = database.filter(MelonCloudTwitterDatabase.mentions.any(params.mention_id))
    if params.mention_name is not None:
        database = database.filter(MelonCloudTwitterDatabase.mentions.any(get_user_id(params.mention_name)))
    if params.account is not None:
        account = get_profile(params.account)
        database = database.filter(MelonCloudTwitterDatabase.account_id.contains(account['id_str']))
    if params.event is not None:
        database = database.filter(MelonCloudTwitterDatabase.event.contains(params.event))
    if params.me_like is not None:
        database = database.filter(MelonCloudTwitterDatabase.memories.is_(params.me_like))
    if params.type is not None:
        database = database.filter(MelonCloudTwitterDatabase.type.contains(params.type))
    if params.start_date is not None:
        ds = append_timezone(dt.datetime.strptime(f"{params.start_date} 00:00:00", "%Y-%m-%d %H:%M:%S"))
        database = database.filter(MelonCloudTwitterDatabase.stored_at >= ds)
    if params.end_date is not None:
        de = append_timezone(dt.datetime.strptime(f"{params.end_date} 23:59:59", '%Y-%m-%d %H:%M:%S'))
        database = database.filter(MelonCloudTwitterDatabase.stored_at <= de)

    if params.deleted is not None:
        database = database.filter(MelonCloudTwitterDatabase.deleted.is_(params.deleted))

    if params.sorting == SortingTweet.ASC:
        database = database.order_by(asc(MelonCloudTwitterDatabase.stored_at))
    else:
        database = database.order_by(desc(MelonCloudTwitterDatabase.stored_at))

    return database


def filtering_meloncloud_twitter_database_for_media(params: RequestMediaQueryModel, db, account):
    database = db if type(db) is DBQuery else db.query(MelonCloudTwitterDatabase)

    if params is None:
        bad_request_exception()

    if params.hashtag is not None:
        database = database.filter(MelonCloudTwitterDatabase.hashtags.any(params.hashtag))
    if params.mention_id is not None:
        database = database.filter(MelonCloudTwitterDatabase.mentions.any(params.mention_id))
    if params.mention_name is not None:
        database = database.filter(MelonCloudTwitterDatabase.mentions.any(get_user_id(params.mention_name)))
    if account is not None:
        database = database.filter(MelonCloudTwitterDatabase.account_id.contains(account['id_str']))
    if params.event is not None:
        database = database.filter(MelonCloudTwitterDatabase.event.contains(params.event))
    if params.me_like is not None:
        database = database.filter(MelonCloudTwitterDatabase.memories.is_(params.me_like))

    if params.start_date is not None:
        ds = append_timezone(dt.datetime.strptime(f"{params.start_date} 00:00:00", "%Y-%m-%d %H:%M:%S"))
        database = database.filter(MelonCloudTwitterDatabase.stored_at >= ds)
    if params.end_date is not None:
        de = append_timezone(dt.datetime.strptime(f"{params.end_date} 23:59:59", '%Y-%m-%d %H:%M:%S'))
        database = database.filter(MelonCloudTwitterDatabase.stored_at <= de)

    if params.deleted is not None:
        database = database.filter(MelonCloudTwitterDatabase.deleted.is_(params.deleted))

    if params.sorting == SortingTweet.ASC:
        database = database.order_by(asc(MelonCloudTwitterDatabase.stored_at))
    else:
        database = database.order_by(desc(MelonCloudTwitterDatabase.stored_at))

    return database
