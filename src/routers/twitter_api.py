import math
from typing import Optional

import pandas
from fastapi import APIRouter, Depends, HTTPException, status as code, Response, WebSocket
from sqlalchemy import desc, asc, func, or_
from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query as DBQuery
import datetime as dt
from operator import is_not
from functools import partial
from urllib.parse import urlparse

from environment import TWITTER_SECRET_PASSWORD
from src.database.melondev_twitter_database import MelonDevTwitterDatabase
from src.database.twitter_observer_database import TwitterObserverDatabase
from fastapi.responses import StreamingResponse
import io

from src.enums.profile_enum import ProfileQueryEnum, ProfileTypeEnum
from src.enums.sorting_enum import SortingEnum
from src.enums.type_enum import FileTypeEnum
from src.environment.database import get_db
from src.models.access_model import AccessTwitterValidatorModel
from src.models.response_model import ResponseModel
from src.models.twitter_model import RequestAnalyzeModel, RequestTweetQueryModel, RequestMediaQueryModel, \
    RequestIdentityModel, RequestTweetModel, RequestPeopleQueryModel, RequestProfileModel, TweetProfileResponseModel, \
    RequestDirectAnalyzeModel, TwitterValidatorModel
from src.engines.twitter_engines import get_tweet_id_from_link, get_tweet_model, get_user_id, like_tweet, \
    hasFavorited, get_user_profile, get_lookup_user, get_dict_lookup_user, get_status, search_tweets, get_favorites
from src.tools.generators.database_export_generator import export_database
from src.tools.onedrive_adapter import send_url_to_onedrive
from src.tools.photos_endpoint import tweet_photo_endpoint, tweet_video_endpoint, people_endpoint
from src.tools.tweet_profile_endpoint import get_profile_endpoint, get_profile_model_endpoint
from src.tools.verify_hub import verify_return

router = APIRouter()


@router.get("/")
async def status_of_tweet_database(db: Session = Depends(get_db)):
    return await verify_return(
        data=ResponseModel("I have " + str(db.query(MelonDevTwitterDatabase).count()) + " tweets on my database"))


@router.get("/count")
async def number_of_tweets(db: Session = Depends(get_db)):
    count = db.query(MelonDevTwitterDatabase).count()
    return await verify_return(data=ResponseModel(count))


@router.get("/media/{file_type}")
async def get_all_media(params: RequestMediaQueryModel = Depends(), db: Session = Depends(get_db)):
    database = database_media_type_categorize(db=db, file_type=params.file_type)
    compute_database = apply_database_for_tweet_filters(params=params, db=database)
    limit_database = apply_limit_to_database(params=params, database=compute_database)
    results = limit_database.all()
    if params.file_type is FileTypeEnum.photos:
        data = list(map(lambda x: tweet_photo_endpoint(x, params.quality), results))
        return await verify_return(data=ResponseModel(data=data))
    elif params.file_type is FileTypeEnum.videos:
        data = list(map(lambda x: tweet_video_endpoint(x), results))
        return await verify_return(data=ResponseModel(data=data))
    else:
        bad_request_exception()


@router.get("/tweets")
async def get_all_tweets(params: RequestTweetQueryModel = Depends(), db: Session = Depends(get_db)):
    database = db.query(MelonDevTwitterDatabase)
    compute_database = apply_database_for_tweet_filters(params=params, db=database)
    limit_database = apply_limit_to_database(params=params, database=compute_database)

    results = limit_database.all()
    data_results = [i.serialize for i in results]
    return await verify_return(data=ResponseModel(data=data_results))


@router.get("/tweets/{tweet_id}", status_code=code.HTTP_200_OK)
async def get_tweet(req: RequestTweetModel = Depends(), db: Session = Depends(get_db)):
    if bool(req.raw):
        package = await get_status(req.tweet_id)
        return await verify_return(data=ResponseModel(package))
    else:
        tweet = db.query(MelonDevTwitterDatabase).get(req.tweet_id)

        if tweet is None:
            not_found_exception()

        return await verify_return(data=ResponseModel(tweet.serialize))


@router.get("/peoples", status_code=code.HTTP_200_OK)
async def get_all_peoples(params: RequestPeopleQueryModel = Depends(), db: Session = Depends(get_db)):
    database = db.query(MelonDevTwitterDatabase.account,
                        func.count(MelonDevTwitterDatabase.account))
    compute_database = apply_database_for_people_filters(params=params, db=database)
    raw = compute_database.all()
    reverse = (True if params.sorting is SortingEnum.desc else False) if params.sorting is not None else True
    data_sorted = sorted(raw, key=lambda kv: kv[1], reverse=reverse)
    limit = len(data_sorted) if bool(params.infinite) else int(params.limit if params.limit is not None else 20)
    page = 0 if bool(params.infinite) else int(params.page if params.page is not None else 0) * limit
    data_list = data_sorted[page:page + limit]

    peoples = get_dict_lookup_user(list(map(lambda x: str(x[0]), data_list)))
    results = list(filter(partial(is_not, None),
                          map(lambda x: people_endpoint(get_profile_endpoint(peoples.get(x[0], None)), x[1]),
                              data_list)))

    return await verify_return(
        data=ResponseModel(data=results))


@router.get("/peoples/{account}", status_code=code.HTTP_200_OK)
async def get_people_detail(req: RequestProfileModel = Depends(), db: Session = Depends(get_db)):
    if req.account is None:
        not_found_exception()
    account = get_profile(req.account)
    if bool(req.query is ProfileQueryEnum.raw):
        return await verify_return(data=ResponseModel(account))
    else:
        profile = get_profile_endpoint(account)

        response = {}

        if profile is not None:
            response["profile"] = profile

            database = None

            if req.query is ProfileQueryEnum.tweet or req.query is None:
                database = db.query(MelonDevTwitterDatabase).filter(
                    MelonDevTwitterDatabase.account.contains(profile.id))
            if req.query is ProfileQueryEnum.mention:
                database = db.query(MelonDevTwitterDatabase).filter(
                    MelonDevTwitterDatabase.mention.any(profile.id))
            if req.query is ProfileQueryEnum.combine:
                database = db.query(MelonDevTwitterDatabase).filter(
                    or_(MelonDevTwitterDatabase.account.contains(profile.id),
                        MelonDevTwitterDatabase.mention.any(profile.id)))

            database = apply_database_for_profile_filters(params=req, database=database)
            limit_database = apply_limit_to_database(params=req, database=database)

            tweets = limit_database.all()
            if req.query is not None:
                response["tweets"] = [i.serialize for i in tweets]

            return await verify_return(data=ResponseModel(data=response))

        return await verify_return(data=ResponseModel(response))


@router.post("/analyze", summary="วิเคราะห์ทวีต",
             status_code=code.HTTP_201_CREATED)
async def analyzing_tweet(req: RequestAnalyzeModel, db: Session = Depends(get_db)):
    tweet_id = get_tweet_id_from_link(req.url)
    if tweet_id is not None:
        package = await get_tweet_model(tweet_id)
        await process_tweet(req=req, package=package, tweet_id=tweet_id, db=db)
        return await verify_return(data=ResponseModel(package.tweet.serialize))
    else:
        bad_request_exception(message="Couldn't find any applicable data")
        return await verify_return(code=404)
    '''try:
        tweet_id = get_tweet_id_from_link(req.url)
        if tweet_id is not None:
            package = await get_tweet_model(tweet_id)
            await process_tweet(req=req, package=package, tweet_id=tweet_id, db=db)
            return await verify_return(data=ResponseModel(package.tweet.serialize))
        else:
            bad_request_exception(message="Couldn't find any applicable data")
            return await verify_return(code=404)
    except Exception as e:
        print(e)
        bad_request_exception(message="Found an error: " + str(e))
        return await verify_return(data=None)'''


async def manual_analyze(model: RequestDirectAnalyzeModel, db: Session):
    if model.tweet_id is not None:
        tweet = db.query(MelonDevTwitterDatabase).get(model.tweet_id)
        package = await get_tweet_model(model.tweet_id, data=model.data, para_tweet=tweet)
        await process_tweet(req=model, package=package, tweet_id=model.tweet_id, db=db, enable_commit=False)
        return package
    return None


async def process_tweet(req, package, tweet_id, db: Session, enable_commit=True):
    if str(req.tag)[:8] == 'HASHTAG ' and is_not_retweet(package.tweet.message):
        package.tweet.event = str(req.tag)
        if str(req.tag) == 'ME LIKE':
            package.tweet.memories = True
        if is_circle_language(package.tweet.lang) or has_in_my_history(db, package.tweet.account):
            db.add(package.tweet)
            if enable_commit:
                db.commit()
    elif is_not_retweet(package.tweet.message):
        #item = db.query(MelonDevTwitterDatabase).filter(
        #    MelonDevTwitterDatabase.id.contains(str(tweet_id))).first()
        item = db.query(MelonDevTwitterDatabase).get(str(tweet_id))
        favorited = await hasFavorited(tweet_id)
        if bool(req.like) and not favorited:
            await like_tweet(tweet_id)
        if item is not None:
            if str(req.tag) == 'ME LIKE':
                await send_url_to_onedrive(package.media_urls)
                item.memories = True
                if bool(req.like) or bool(req.secret_like):
                    item.event = str(req.tag)
                    item.addedAt = dt.datetime.now()
                db.add(item)
                if enable_commit:
                    db.commit()
        else:
            package.tweet.event = str(req.tag)
            if str(req.tag) == 'ME LIKE':
                package.tweet.memories = True
                await send_url_to_onedrive(package.media_urls)
            db.add(package.tweet)
            if enable_commit:
                db.commit()


@router.put("/unlike")
async def unlike_tweet(req: RequestIdentityModel, db: Session = Depends(get_db)):
    tweet = db.query(MelonDevTwitterDatabase).filter(
        MelonDevTwitterDatabase.id == str(req.id)).first()
    if tweet is not None:
        tweet.memories = False
        db.add(tweet)
        db.commit()
    return await verify_return(data=ResponseModel(tweet.serialize))


@router.patch("/checking-completeness", include_in_schema=True)
async def checking_completeness(req: AccessTwitterValidatorModel, db: Session = Depends(get_db)):
    # try:
    database = db.query(TwitterObserverDatabase)
    database = database.filter(TwitterObserverDatabase.paused.is_(False))
    results = database.all()

    for i in results:
        last_id = None
        count = 0

        print(i.value)

        if i.objective == "SEARCH":
            data = search_tweets(keyword=i.value, since_id=i.lastTweetId)
            value = list(map(lambda x: x._json, data))
            count = len(value)

            for j in value:
                tweet_id: str = j['id_str']

                print(tweet_id)

                if last_id is None:
                    last_id = tweet_id
                tag = "HASHTAG " + str(i.value)
                model = RequestDirectAnalyzeModel(token=TWITTER_SECRET_PASSWORD, like=False, secret_like=False,
                                                  url=tweet_id, tweet_id=tweet_id, data=j,
                                                  tag=tag)
                await manual_analyze(model=model, db=db)

        if i.objective == "ME LIKE":
            data = get_favorites(since_id=i.lastTweetId)
            value = list(map(lambda x: x._json, data))
            count = len(value)

            for j in value:
                tweet_id: str = j['id_str']

                print(tweet_id)

                if last_id is None:
                    last_id = tweet_id
                tag = "ME LIKE"
                model = RequestDirectAnalyzeModel(token=TWITTER_SECRET_PASSWORD, like=False, secret_like=False,
                                                  url=tweet_id, tweet_id=tweet_id, data=j,
                                                  tag=tag)
                await manual_analyze(model=model, db=db)

        if last_id is not None:
            timestamp = dt.datetime.now()
            i.lastTweetId = last_id
            i.updatedAt = timestamp
            i.count += count
            db.add(i)

    db.commit()
    return "REFRESHED"


'''except:
    raise HTTPException(
        status_code=code.HTTP_400_BAD_REQUEST,
        detail="UNAUTHORIZED")
        '''


@router.get("/export", status_code=code.HTTP_200_OK)
async def export_twitter_data(req: TwitterValidatorModel = Depends(), db: Session = Depends(get_db)):
    data = export_database(db=db, session=MelonDevTwitterDatabase)
    df = pandas.DataFrame(data)
    stream = io.StringIO()

    name = MelonDevTwitterDatabase.__tablename__
    date = dt.datetime.now().strftime('%Y_%m_%d')

    filename = str(name) + "_" + str(date)

    df.to_csv(stream, encoding='utf-8', header=True, index=False)

    response = StreamingResponse(iter([stream.getvalue()]),
                                 media_type="text/csv"
                                 )
    response.headers["Content-Disposition"] = "attachment; filename = {file_name}.csv".format(file_name=filename)

    return response


def is_not_retweet(value) -> bool:
    return str(value)[:3] != 'RT '


def is_circle_language(value) -> bool:
    return str(value) == 'ja' or str(value) == 'zh'


def has_in_my_history(db, account) -> bool:
    return db.query(
        MelonDevTwitterDatabase).filter(MelonDevTwitterDatabase.account.contains(str(account))).count() > 0


def database_media_type_categorize(db, file_type: FileTypeEnum):
    if file_type is FileTypeEnum.photos:
        return db.query(func.unnest(MelonDevTwitterDatabase.photo), MelonDevTwitterDatabase.id,
                        MelonDevTwitterDatabase.account, MelonDevTwitterDatabase.createdAt)
    elif file_type is FileTypeEnum.videos:
        return db.query(func.unnest(MelonDevTwitterDatabase.video), MelonDevTwitterDatabase.id,
                        MelonDevTwitterDatabase.account, MelonDevTwitterDatabase.createdAt,
                        MelonDevTwitterDatabase.thumbnail)
    else:
        bad_request_exception()


def get_profile(account: str):
    if account.isdigit():
        package = get_user_profile(account, type=ProfileTypeEnum.user_id)
        if package is None:
            package = get_user_profile(account, type=ProfileTypeEnum.screen_name)
    else:
        package = get_user_profile(account, type=ProfileTypeEnum.screen_name)
        if package is None:
            package = get_user_profile(account, type=ProfileTypeEnum.user_id)
    return package


def apply_database_for_tweet_filters(params: RequestTweetQueryModel, db):
    database = db if type(db) is DBQuery else db.query(MelonDevTwitterDatabase)

    if params is None:
        bad_request_exception()

    if params.hashtag is not None:
        database = database.filter(MelonDevTwitterDatabase.hashtag.any(params.hashtag))
    if params.mention_id is not None:
        database = database.filter(MelonDevTwitterDatabase.mention.any(params.mention_id))
    if params.mention_name is not None:
        database = database.filter(MelonDevTwitterDatabase.mention.any(get_user_id(params.mention_name)))
    if params.account_name is not None:
        database = database.filter(MelonDevTwitterDatabase.account.contains(get_user_id(params.account_name)))
    if params.account_id is not None:
        database = database.filter(MelonDevTwitterDatabase.account.contains(params.account_id))
    if params.event is not None:
        database = database.filter(MelonDevTwitterDatabase.event.contains(params.event))
    if params.me_like is not None:
        database = database.filter(MelonDevTwitterDatabase.memories.is_(params.me_like))
    if params.start_date is not None:
        ds = dt.datetime.strptime(params.start_date + " 00:00:00", '%Y-%m-%d %H:%M:%S')
        database = database.filter(MelonDevTwitterDatabase.addedAt >= ds)
    if params.end_date is not None:
        de = dt.datetime.strptime(params.end_date + " 23:59:59", '%Y-%m-%d %H:%M:%S')
        database = database.filter(MelonDevTwitterDatabase.addedAt <= de)

    if params.deleted is not None:
        database = database.filter(MelonDevTwitterDatabase.deleted.is_(params.deleted))

    if params.sorting == "asc":
        database = database.order_by(asc(MelonDevTwitterDatabase.addedAt))
    else:
        database = database.order_by(desc(MelonDevTwitterDatabase.addedAt))

    return database


def apply_limit_to_database(params, database):
    if not bool(params.infinite):
        page = params.page if params.page is not None else 0
        limit = params.limit if params.limit is not None else 20
        database = database.limit(limit).offset(int(page * limit))
    return database


def apply_database_for_people_filters(params: RequestPeopleQueryModel, db):
    database = db if type(db) is DBQuery else db.query(MelonDevTwitterDatabase.account,
                                                       func.count(MelonDevTwitterDatabase.account))

    if params is None:
        bad_request_exception()

    database = database.group_by(MelonDevTwitterDatabase.account)

    if params.hashtag is not None:
        database = database.filter(MelonDevTwitterDatabase.hashtag.any(params.hashtag))
    if params.event is not None:
        database = database.filter(MelonDevTwitterDatabase.event.contains(params.event))
    if params.me_like is not None:
        database = database.filter(MelonDevTwitterDatabase.memories.is_(params.me_like))
    if params.start_date is not None:
        ds = dt.datetime.strptime(params.start_date + " 00:00:00", '%Y-%m-%d %H:%M:%S')
        database = database.filter(MelonDevTwitterDatabase.addedAt >= ds)
    if params.end_date is not None:
        de = dt.datetime.strptime(params.end_date + " 23:59:59", '%Y-%m-%d %H:%M:%S')
        database = database.filter(MelonDevTwitterDatabase.addedAt <= de)

    return database


def apply_database_for_profile_filters(params: RequestProfileModel, database):
    if database is None or params is None:
        bad_request_exception()
    if params.hashtag is not None:
        database = database.filter(MelonDevTwitterDatabase.hashtag.any(params.hashtag))
    if params.event is not None:
        database = database.filter(MelonDevTwitterDatabase.event.contains(params.event))
    if params.me_like is not None:
        database = database.filter(MelonDevTwitterDatabase.memories.is_(params.me_like))
    if params.start_date is not None:
        ds = dt.datetime.strptime(params.start_date + " 00:00:00", '%Y-%m-%d %H:%M:%S')
        database = database.filter(MelonDevTwitterDatabase.addedAt >= ds)
    if params.end_date is not None:
        de = dt.datetime.strptime(params.end_date + " 23:59:59", '%Y-%m-%d %H:%M:%S')
        database = database.filter(MelonDevTwitterDatabase.addedAt <= de)

    if params.deleted is not None:
        database = database.filter(MelonDevTwitterDatabase.deleted.is_(params.deleted))

    if params.sorting == "asc":
        database = database.order_by(asc(MelonDevTwitterDatabase.addedAt))
    else:
        database = database.order_by(desc(MelonDevTwitterDatabase.addedAt))

    return database


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
