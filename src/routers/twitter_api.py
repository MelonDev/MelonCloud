from fastapi import APIRouter, Depends, HTTPException, status as code
from sqlalchemy import desc, asc, func
from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query as DBQuery
import datetime as dt
from operator import is_not
from functools import partial

from src.database.melondev_twitter_database import MelonDevTwitterDatabase
from src.enums.sorting_enum import SortingEnum
from src.enums.type_enum import FileTypeEnum
from src.environment.database import get_db
from src.models.response_model import ResponseModel
from src.models.twitter_model import RequestAnalyzeModel, RequestTweetQueryModel, RequestMediaQueryModel, \
    RequestIdentityModel, RequestTweetModel, RequestPeopleQueryModel
from src.engines.twitter_engines import get_tweet_id_from_link, get_tweet_model, get_user_id, like_tweet, \
    request_raw_tweet, hasFavorited, get_user_profile, get_lookup_user, get_dict_lookup_user
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
    results = apply_database_for_tweet_filters(params=params, db=database).all()
    if params.file_type is FileTypeEnum.photos:
        return await verify_return(
            data=ResponseModel(list(map(lambda x: tweet_photo_endpoint(x, params.quality), results))))
    elif params.file_type is FileTypeEnum.videos:
        return await verify_return(data=ResponseModel(list(map(lambda x: tweet_video_endpoint(x), results))))
    else:
        bad_request_exception()


@router.get("/tweets")
async def get_all_tweets(params: RequestTweetQueryModel = Depends(), db: Session = Depends(get_db)):
    database = db.query(MelonDevTwitterDatabase)
    results = apply_database_for_tweet_filters(params=params, db=database).all()
    return await verify_return(data=ResponseModel([i.serialize for i in results]))


@router.get("/tweets/{tweet_id}", status_code=code.HTTP_200_OK)
async def get_tweet(req: RequestTweetModel = Depends(), db: Session = Depends(get_db)):
    if bool(req.raw):
        package = await request_raw_tweet(req.tweet_id)
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
    raw = apply_database_for_people_filters(params=params, db=database).all()
    reverse = (True if params.sorting is SortingEnum.desc else False) if params.sorting is not None else True
    data_sorted = sorted(raw, key=lambda kv: kv[1], reverse=reverse)
    limit = len(data_sorted) if bool(params.infinite) else int(params.limit if params.limit is not None else 20)
    page = 0 if bool(params.infinite) else int(params.page if params.page is not None else 0) * limit
    data_list = data_sorted[page:page + limit]

    peoples = get_lookup_user(list(map(lambda x: str(x[0]), data_list)))
    print(peoples)
    print(len(peoples))
    # mock = ['130528023', '841629564090503169', '556550179023', '2543319608']
    # peoples = get_lookup_user(mock)

    raw_list = list(
        map(lambda x: people_endpoint(get_profile_endpoint(next(filter(lambda y: x[0] in y['id_str'], peoples), None)),
                                      x[1]), data_list))

    results = list(filter(partial(is_not, None), raw_list))

    return await verify_return(
        data=ResponseModel(results))


@router.get("/peoples/{account_id}", status_code=code.HTTP_200_OK, deprecated=True)
async def get_people(req: RequestTweetModel = Depends(), db: Session = Depends(get_db)):
    return ""


@router.get("/peoples/{account_id}/address", status_code=code.HTTP_200_OK, deprecated=True)
async def get_people_address(req: RequestTweetModel = Depends(), db: Session = Depends(get_db)):
    return ""


@router.get("/peoples/{account_name}/id", status_code=code.HTTP_200_OK, deprecated=True)
async def get_people_id(req: RequestTweetModel = Depends(), db: Session = Depends(get_db)):
    return ""


@router.post("/analyze", summary="วิเคราะห์ทวีต",
             status_code=code.HTTP_201_CREATED)
async def analyzing_tweet(req: RequestAnalyzeModel, db: Session = Depends(get_db)):
    try:
        tweet_id = get_tweet_id_from_link(req.url)
        if tweet_id is not None:
            package = await get_tweet_model(tweet_id)
            if str(req.tag)[:8] == 'HASHTAG ' and is_not_retweet(package.tweet.message):
                package.tweet.event = str(req.tag)
                if str(req.tag) == 'ME LIKE':
                    package.tweet.memories = True
                if is_circle_language(package.tweet.lang) or has_in_my_history(db, package.tweet.account):
                    db.add(package.tweet)
                    db.commit()
            elif is_not_retweet(package.tweet.message):
                item = db.query(MelonDevTwitterDatabase).filter(
                    MelonDevTwitterDatabase.id == str(tweet_id)).first()
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
                        db.commit()
                else:

                    package.tweet.event = str(req.tag)
                    if str(req.tag) == 'ME LIKE':
                        package.tweet.memories = True
                        await send_url_to_onedrive(package.media_urls)
                    db.add(package.tweet)
                    db.commit()
            return await verify_return(data=ResponseModel(package.tweet.serialize))
        else:
            bad_request_exception(message="Couldn't find any applicable data")
            return await verify_return(code=404)

    except Exception as e:
        print(e)
        bad_request_exception(message="Found an error: " + str(e))
        return await verify_return(data=None)


@router.put("/unlike")
async def unlike_tweet(req: RequestIdentityModel, db: Session = Depends(get_db)):
    tweet = db.query(MelonDevTwitterDatabase).filter(
        MelonDevTwitterDatabase.id == str(req.id)).first()
    if tweet is not None:
        tweet.memories = False
        db.add(tweet)
        db.commit()
    return await verify_return(data=ResponseModel(tweet.serialize))


@router.get("/export", status_code=code.HTTP_200_OK, deprecated=True)
async def export_twitter_data(req: RequestTweetModel = Depends(), db: Session = Depends(get_db)):
    return ""


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


def apply_database_for_tweet_filters(params: RequestTweetQueryModel, db):
    database = db if type(db) is DBQuery else db.query(MelonDevTwitterDatabase)

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

    if not bool(params.infinite):
        page = params.page if params.page is not None else 0
        limit = params.limit if params.limit is not None else 20
        database = database.limit(limit).offset(int(page * limit))

    return database


def apply_database_for_people_filters(params: RequestPeopleQueryModel, db):
    database = db if type(db) is DBQuery else db.query(MelonDevTwitterDatabase.account,
                                                       func.count(MelonDevTwitterDatabase.account))
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


def bad_request_exception(message=None):
    raise HTTPException(
        status_code=code.HTTP_400_BAD_REQUEST,
        detail=message if message is not None else "BAD REQUEST")


def not_found_exception(message=None):
    raise HTTPException(
        status_code=code.HTTP_404_NOT_FOUND,
        detail=message if message is not None else "NOT FOUND")
