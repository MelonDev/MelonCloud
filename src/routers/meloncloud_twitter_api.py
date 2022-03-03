import calendar
import math
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, status as code, Response
from sqlalchemy import desc, asc, func, or_
from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query as DBQuery
import csv
import io

import datetime as dt
from operator import is_not
from functools import partial
from urllib.parse import urlparse

from src.database.meloncloud.meloncloud_beast_character_database import MelonCloudBeastCharacterDatabase
from src.database.meloncloud.meloncloud_book_database import MelonCloudBookDatabase
from src.database.meloncloud.meloncloud_book_page_database import MelonCloudBookPageDatabase
from src.database.meloncloud.meloncloud_people_database import MelonCloudPeopleDatabase
from src.database.meloncloud.meloncloud_twitter_database import MelonCloudTwitterDatabase
from src.engines.twitter_engines import get_tweet_id_from_link, get_meloncloud_tweet_model, \
    hasFavorited, like_tweet, get_user_id, get_status, get_dict_lookup_user, get_user_profile
from src.enums.profile_enum import ProfileTypeEnum, ProfileQueryEnum
from src.enums.sorting_enum import SortingTweet
from src.enums.type_enum import MelonCloudFileTypeEnum
from src.environment.database import get_db
from src.models.meloncloud_twitter_model import RequestAnalyzeModel, TweetAction, RequestTweetQueryModel, \
    RequestTweetModel, RequestPeopleQueryModel, RequestProfileModel, RequestMediaQueryModel, TweetMediaType, \
    RequestHashtagQueryModel, HashtagQueryDate, get_hashtag_dict, MediaExtraOptional, ValidatorModel, \
    MelonCloudBackupModel, BackupQueryDate, DatabaseQueryName, RequestPeopleDatabaseModel
from src.tools.chunks import chunks
from src.tools.converters.datetime_converter import append_timezone, convert_datetime_to_string, \
    convert_short_string_form_to_datetime
from src.tools.date_for_backup import today, first_day_of_month, last_day_of_month, first_day_of_month_with_time, \
    last_day_of_month_with_time, first_day_of_previous_month_with_time, last_day_of_previous_month_with_time, \
    start_datetime, end_datetime, first_day_of_year, last_day_of_year, last_day_of_previous_year, \
    first_day_of_previous_year, first_day_of_year_with_time, last_day_of_year_with_time, \
    first_day_of_previous_year_with_time, last_day_of_previous_year_with_time
from src.tools.onedrive_adapter import send_url_to_meloncloud_onedrive
from src.tools.photos_endpoint import tweet_people_endpoint, tweet_photo_endpoint, tweet_video_endpoint, \
    tweet_all_media_endpoint
from src.tools.tweet_profile_endpoint import get_meloncloud_tweet_profile_endpoint
from src.tools.verify_hub import response

router = APIRouter()


@router.get("/")
async def status_of_tweet_database(params: ValidatorModel = Depends(), db: Session = Depends(get_db)):
    return response(f"I have {db.query(MelonCloudTwitterDatabase).count()} tweets on my database")


@router.get("/count")
async def number_of_tweets(params: ValidatorModel = Depends(), db: Session = Depends(get_db)):
    count = db.query(MelonCloudTwitterDatabase).count()
    return response(count)


@router.post("/create", tags=['Peoples'])
async def add_people(params: RequestPeopleDatabaseModel = Depends(RequestPeopleDatabaseModel.as_form),
                     db: Session = Depends(get_db)):
    account = None
    partner = None
    if params.twitter_account is not None:
        profile = get_profile(params.twitter_account)
        if profile is None:
            bad_request_exception()
        account = profile['id_str']
    if params.partner_account is not None:
        profile = get_profile(params.partner_account)
        if profile is not None:
            partner = profile['id_str']

    if db.query(MelonCloudPeopleDatabase).filter(MelonCloudPeopleDatabase.twitter_id.contains(account)).count() > 0:
        duplicate_on_database_exception()

    people = MelonCloudPeopleDatabase()
    people.append_details(name=params.name, twitter_id=account, partner=partner, image_url=params.image_url,
                          nationality=params.nationality,gender=params.gender,weight=params.weight,height=params.height,year_of_birth=params.year_of_birth)

    return response(people.serialize)


@router.get("/media")
async def get_all_media(params: RequestMediaQueryModel = Depends(), db: Session = Depends(get_db)):
    limit = params.limit if params.limit is not None else 50
    page = params.page if params.page is not None else 0

    account = None
    extra_optional = None

    if params.account is not None:
        account = get_profile(params.account)

    file_type = MelonCloudFileTypeEnum.PHOTOS if params.type is None else params.type
    database = database_media_type_categorize(db=db, file_type=file_type)
    compute_database = filtering_meloncloud_twitter_database_for_media(params=params, db=database, account=account)
    count = compute_database.count()
    total_page = int(math.ceil(count / limit)) if count > 0 else 0
    is_overflow(page, total_page)

    limit_database = compute_database.limit(limit).offset(int(page * limit))
    results = limit_database.all()

    fabric = {
        "total_items": count,
        "per_page": int(params.limit if params.limit is not None else 50),
        "item_on_page": len(results),
        "total_page": total_page,
        "current_page": page,
        "next_page": page + 1 if page < total_page - 1 else None,
        "previous_page": page - 1 if page > 0 else None
    }

    if params.extra_optional is not None:
        if params.extra_optional is MediaExtraOptional.PROFILE:
            extra_optional = get_meloncloud_tweet_profile_endpoint(account)
        if params.extra_optional is MediaExtraOptional.PEOPLES:
            peoples_params = media_query_to_people_query(params)
            response_from_peoples = await get_all_peoples(params=peoples_params, db=db)
            extra_optional = response_from_peoples.data

    if file_type is MelonCloudFileTypeEnum.PHOTOS:
        data = list(map(lambda x: tweet_photo_endpoint(x, params.quality), results))
        result = media_result_packing(data=data, payload=extra_optional)
        return response(data=result, fabric=fabric)
    elif file_type is MelonCloudFileTypeEnum.VIDEOS:
        data = list(map(lambda x: tweet_video_endpoint(x), results))
        result = media_result_packing(data=data, payload=extra_optional)
        return response(data=result, fabric=fabric)
    elif file_type is MelonCloudFileTypeEnum.ALL:
        data = list(map(lambda x: tweet_all_media_endpoint(x, params.quality), results))
        result = media_result_packing(data=data, payload=extra_optional)
        return response(data=result, fabric=fabric)
    else:
        bad_request_exception()


@router.get("/tweets-count")
async def get_count_tweets(params: RequestTweetQueryModel = Depends(),
                           db: Session = Depends(get_db)):
    if bool(params.infinite):
        bad_request_exception("The infinite has duplicated")
    database = db.query(MelonCloudTwitterDatabase)
    compute_database = filtering_meloncloud_twitter_database(params=params, db=database)
    count = compute_database.count()

    return response(count)


@router.get("/tweets")
async def get_all_tweets(params: RequestTweetQueryModel = Depends(),
                         db: Session = Depends(get_db)):
    if bool(params.infinite):
        bad_request_exception("The infinite has duplicated")
    database = db.query(MelonCloudTwitterDatabase)
    compute_database = filtering_meloncloud_twitter_database(params=params, db=database)

    page = params.page if params.page is not None else 0
    limit = params.limit if params.limit is not None else 50

    count = compute_database.count()
    total_page = int(math.ceil(count / limit)) if count > 0 else 0
    is_overflow(page, total_page)

    limit_database = append_limit_to_database(params=params, database=compute_database)
    results = limit_database.all()
    data_results = [i.serialize for i in results]

    fabric = {
        "total_items": count,
        "per_page": int(params.limit if params.limit is not None else 50),
        "item_on_page": len(results),
        "total_page": total_page,
        "current_page": page,
        "next_page": page + 1 if page < total_page - 1 else None,
        "previous_page": page - 1 if page > 0 else None
    }

    return response(data=data_results, fabric=fabric)


@router.get("/tweets/{tweet_id}", status_code=code.HTTP_200_OK)
async def get_tweet(req: RequestTweetModel = Depends(), db: Session = Depends(get_db)):
    if bool(req.raw):
        package = await get_status(req.tweet_id)
        return response(package)
    else:
        tweet = db.query(MelonCloudTwitterDatabase).get(req.tweet_id)
        if tweet is None:
            not_found_exception()

        return response(tweet.serialize)


@router.get("/peoples", status_code=code.HTTP_200_OK)
async def get_all_peoples(params: RequestPeopleQueryModel = Depends(), db: Session = Depends(get_db)):
    if bool(params.infinite):
        bad_request_exception("The infinite has duplicated")

    database = db.query(MelonCloudTwitterDatabase.account_id,
                        func.count(MelonCloudTwitterDatabase.account_id))
    compute_database = filtering_people_database(params=params, db=database)
    count = compute_database.count()
    raw = compute_database.all()
    reverse = (True if params.sorting is SortingTweet.DESC else False) if params.sorting is not None else True
    data_sorted = sorted(raw, key=lambda kv: kv[1], reverse=reverse)
    limit = len(data_sorted) if bool(params.infinite) else int(params.limit if params.limit is not None else 50)
    page = 0 if bool(params.infinite) else int(params.page if params.page is not None else 0) * limit
    real_page = int(params.page if params.page is not None else 0)

    total_page = int(math.ceil(count / limit)) if count > 0 else 0
    is_overflow(real_page, total_page)

    data_list = data_sorted[page:page + limit]

    if len(data_list) > 100:
        list_chunks = chunks(data_list, int(math.ceil(len(data_list) / 100)))
        peoples_list = {}
        for i in list_chunks:
            peoples = get_dict_lookup_user(list(map(lambda x: str(x[0]), i)))
            peoples_list.update(peoples)
        results = list(filter(partial(is_not, None),
                              map(lambda x: tweet_people_endpoint(
                                  get_meloncloud_tweet_profile_endpoint(peoples_list.get(x[0], None)), x[1]),
                                  data_list)))

    else:
        peoples = get_dict_lookup_user(list(map(lambda x: str(x[0]), data_list)))
        results = list(filter(partial(is_not, None),
                              map(lambda x: tweet_people_endpoint(
                                  get_meloncloud_tweet_profile_endpoint(peoples.get(x[0], None)), x[1]),
                                  data_list)))

    real_page = int(params.page if params.page is not None else 0)
    fabric = {
        "total_items": count,
        "per_page": int(params.limit if params.limit is not None else 50),
        "item_on_page": len(results),
        "total_page": total_page,
        "current_page": real_page,
        "next_page": real_page + 1 if real_page < total_page - 1 else None,
        "previous_page": real_page - 1 if real_page > 0 else None
    }

    return response(data=results, fabric=fabric)


@router.get("/peoples/{account}", status_code=code.HTTP_200_OK)
async def get_people_detail(req: RequestProfileModel = Depends(), db: Session = Depends(get_db)):
    if bool(req.infinite):
        bad_request_exception("infinite has duplicated")

    if req.account is None:
        not_found_exception()
    account = get_profile(req.account)
    if bool(req.query is ProfileQueryEnum.RAW):
        return response(account)
    else:
        profile = get_meloncloud_tweet_profile_endpoint(account)
        result = {}

        if profile is not None:
            result["profile"] = profile

            count = 0
            page = req.page if req.page is not None else 0
            limit = req.limit if req.limit is not None else 50
            total_page = 0
            item_count = limit

            if req.query is not None:
                database = None

                if req.query is ProfileQueryEnum.TWEET or req.query is None:
                    database = db.query(MelonCloudTwitterDatabase).filter(
                        MelonCloudTwitterDatabase.account_id.contains(profile.id))
                if req.query is ProfileQueryEnum.MENTION:
                    database = db.query(MelonCloudTwitterDatabase).filter(
                        MelonCloudTwitterDatabase.mentions.any(profile.id))
                if req.query is ProfileQueryEnum.COMBINE:
                    database = db.query(MelonCloudTwitterDatabase).filter(
                        or_(MelonCloudTwitterDatabase.account_id.contains(profile.id),
                            MelonCloudTwitterDatabase.mentions.any(profile.id)))

                database = filtering_profile_database(params=req, database=database)
                count = database.count()

                total_page = int(math.ceil(count / limit)) if count > 0 else 0
                is_overflow(page, total_page)

                limit_database = append_limit_to_database(params=req, database=database)
                item_count = limit_database.count()
                tweets = limit_database.all()
                result["tweets"] = [i.serialize for i in tweets]

            fabric = {
                "total_items": count,
                "per_page": limit,
                "item_on_page": item_count,
                "total_page": total_page,
                "current_page": page,
                "next_page": page + 1 if page < total_page - 1 else None,
                "previous_page": page - 1 if page > 0 else None
            }

            return response(data=result, fabric=fabric)

        return response(result)


@router.get("/hashtags", status_code=code.HTTP_200_OK)
def get_hashtags(params: RequestHashtagQueryModel = Depends(),
                 db: Session = Depends(get_db)):
    database = db.query(func.unnest(MelonCloudTwitterDatabase.hashtags))
    limit = params.limit if params.limit is not None else 120
    page = params.page if params.page is not None else 0

    current_datetime = dt.datetime.now()
    compound_days = get_day(params.query if params.query is not None else HashtagQueryDate.ALL)
    skip_day = dt.timedelta(days=int(page * compound_days))
    desired_datetime = dt.timedelta(days=compound_days)
    skip_datetime = current_datetime - skip_day
    back_to_datetime = (skip_datetime - desired_datetime).replace(hour=0,
                                                                  minute=0,
                                                                  second=0,
                                                                  microsecond=0)

    compute_database = filtering_meloncloud_twitter_database_for_hashtags(params=params, db=database,
                                                                          skip_datetime=skip_datetime,
                                                                          back_to_datetime=back_to_datetime)
    count = compute_database.count()
    total_page = int(math.ceil(count / limit)) if count > 0 else 0
    is_overflow(page, total_page)

    raw_data = compute_database.all()
    data = [str(i[0]) for i in raw_data]
    data_dict = dict(Counter(data))
    data_sorted = sorted(data_dict.items(), key=lambda kv: kv[1], reverse=True)
    start_at = int(page) * limit
    results = [get_hashtag_dict(name, count) for name, count in data_sorted[start_at:start_at + limit]]

    fabric = {
        "total_items": count,
        "per_page": limit,
        "item_on_page": len(results),
        "total_page": total_page,
        "current_page": page,
        "next_page": page + 1 if page < total_page - 1 else None,
        "previous_page": page - 1 if page > 0 else None,
        "time_range": {
            "start": convert_datetime_to_string(skip_datetime, disable_timezone=True),
            "end": convert_datetime_to_string(back_to_datetime, disable_timezone=True)
        }
    }
    return response(data=results, fabric=fabric)


@router.post("/analyze", summary="วิเคราะห์ทวีต",
             status_code=code.HTTP_201_CREATED)
async def analyzing_tweet(request: RequestAnalyzeModel = Depends(RequestAnalyzeModel.as_form),
                          db: Session = Depends(get_db)):
    try:
        tweet_id = get_tweet_id_from_link(request.url)
        if tweet_id is not None:
            package = await get_meloncloud_tweet_model(tweet_id)
            await processing_tweet(request=request, package=package, tweet_id=tweet_id, db=db)
            return response(package.tweet.serialize)
        else:
            bad_request_exception(message="Couldn't find any applicable data")
    except Exception as e:
        bad_request_exception(message="Found an error: " + str(e))


@router.get("/export", status_code=code.HTTP_200_OK)
async def export_twitter_data(params: MelonCloudBackupModel = Depends(), db: Session = Depends(get_db)):
    name = get_database_name(DatabaseQueryName.MelonCloudTwitterDatabase)

    filename = f"{name}_{today().strftime('%Y_%m_%d')}"
    data = None
    if params.date_range is None:
        data = database_for_backup(db=db, name=DatabaseQueryName.MelonCloudTwitterDatabase,
                                   start_date=first_day_of_month_with_time(),
                                   end_date=last_day_of_month_with_time())
    else:
        if params.date_range is BackupQueryDate.DAILY:
            data = database_for_backup(db=db, name=DatabaseQueryName.MelonCloudTwitterDatabase,
                                       start_date=first_day_of_month_with_time(),
                                       end_date=last_day_of_month_with_time())
        elif params.date_range is BackupQueryDate.MONTHLY:
            data = database_for_backup(db=db, name=DatabaseQueryName.MelonCloudTwitterDatabase,
                                       start_date=first_day_of_month_with_time(),
                                       end_date=last_day_of_month_with_time())
            filename = f"{name}_{str(BackupQueryDate.MONTHLY).capitalize()}_{today().strftime('%Y_%m')}"
        elif params.date_range is BackupQueryDate.LAST_MONTH:
            data = database_for_backup(db=db, name=DatabaseQueryName.MelonCloudTwitterDatabase,
                                       start_date=first_day_of_previous_month_with_time(),
                                       end_date=last_day_of_previous_month_with_time())
            filename = f"{name}_{str(BackupQueryDate.LAST_MONTH).capitalize()}_{first_day_of_previous_month_with_time().strftime('%Y_%m')}"
        elif params.date_range is BackupQueryDate.YEARLY:
            data = database_for_backup(db=db, name=DatabaseQueryName.MelonCloudTwitterDatabase,
                                       start_date=first_day_of_year_with_time(),
                                       end_date=last_day_of_year_with_time())
            filename = f"{name}_{str(BackupQueryDate.YEARLY).capitalize()}_{today().strftime('%Y')}"
        elif params.date_range is BackupQueryDate.LAST_YEAR:
            data = database_for_backup(db=db, name=DatabaseQueryName.MelonCloudTwitterDatabase,
                                       start_date=first_day_of_previous_year_with_time(),
                                       end_date=last_day_of_previous_year_with_time())
            filename = f"{name}_{str(BackupQueryDate.LAST_YEAR).capitalize()}_{first_day_of_previous_year_with_time().strftime('%Y')}"

        elif params.date_range is BackupQueryDate.ALL:
            data = database_for_backup(db=db, name=DatabaseQueryName.MelonCloudTwitterDatabase)
            filename = f"{name}_Backup_{today().strftime('%Y_%m_%d')}"

        elif params.date_range is BackupQueryDate.CUSTOM:
            if params.start_date is None or params.end_date is None:
                bad_request_exception()
            ds = dt.datetime.strptime(f"{params.start_date} 00:00:00", "%Y-%m-%d %H:%M:%S")
            de = dt.datetime.strptime(f"{params.end_date} 23:59:59", '%Y-%m-%d %H:%M:%S')
            data = database_for_backup(db=db, name=DatabaseQueryName.MelonCloudTwitterDatabase, start_date=ds,
                                       end_date=de)
            filename = f"{name}_{ds.strftime('%Y_%m_%d')}_to_{de.strftime('%Y_%m_%d')}"

    return packing_backup(data=data, filename=filename)

    # return response("HELLO")


def database_for_backup(db, name, start_date=None, end_date=None):
    database = get_database(db, name)

    if start_date is not None:
        database = database.filter(MelonCloudTwitterDatabase.stored_at >= start_date)
    if end_date is not None:
        database = database.filter(MelonCloudTwitterDatabase.stored_at <= end_date)
    return database


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


def is_circle_language(value) -> bool:
    return str(value) == 'ja' or str(value) == 'zh'


def has_in_my_history(db, account) -> bool:
    return db.query(
        MelonCloudTwitterDatabase).filter(MelonCloudTwitterDatabase.account_id.contains(str(account))).count() > 0


def bad_request_exception(message=None):
    raise HTTPException(
        status_code=code.HTTP_400_BAD_REQUEST,
        detail=message if message is not None else "BAD REQUEST")


def not_found_exception(message=None):
    raise HTTPException(
        status_code=code.HTTP_404_NOT_FOUND,
        detail=message if message is not None else "NOT FOUND")


def get_count_of_database(database) -> int:
    if database is None:
        bad_request_exception()
    return int(database.count())


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


def media_query_to_people_query(params: RequestMediaQueryModel) -> RequestPeopleQueryModel:
    peoples_params = RequestPeopleQueryModel()
    peoples_params.token = params.token
    peoples_params.event = params.event
    peoples_params.hashtag = params.hashtag
    peoples_params.start_date = params.start_date
    peoples_params.end_date = params.end_date
    peoples_params.me_like = params.me_like
    peoples_params.limit = 30
    peoples_params.page = 0
    return peoples_params


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


def duplicate_on_database_exception(message=None):
    raise HTTPException(
        status_code=code.HTTP_302_FOUND,
        detail=message if message is not None else "TWITTER USER IS EXISTS ON DATABASE")
