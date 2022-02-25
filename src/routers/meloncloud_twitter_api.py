from fastapi import APIRouter, Depends, HTTPException, status as code, Response, WebSocket
from sqlalchemy import desc, asc, func, or_
from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query as DBQuery
import datetime as dt
from operator import is_not
from functools import partial
from urllib.parse import urlparse

from src.database.meloncloud.meloncloud_twitter_database import MelonCloudTwitterDatabase
from src.engines.twitter_engines import get_tweet_id_from_link, get_tweet_model, get_meloncloud_tweet_model, \
    hasFavorited, like_tweet, get_user_id
from src.enums.sorting_enum import SortingEnum
from src.environment.database import get_db
from src.models.meloncloud_twitter_model import RequestAnalyzeModel, TweetAction, RequestTweetQueryModel
from src.tools.onedrive_adapter import send_url_to_meloncloud_onedrive
from src.tools.verify_hub import response

router = APIRouter()


@router.get("/")
async def status_of_tweet_database(db: Session = Depends(get_db)):
    return response(f"I have {db.query(MelonCloudTwitterDatabase).count()} tweets on my database")


@router.get("/count")
async def number_of_tweets(db: Session = Depends(get_db)):
    count = db.query(MelonCloudTwitterDatabase).count()
    return response(count)


@router.get("/tweets")
async def get_all_tweets(params: RequestTweetQueryModel = Depends(),
                         db: Session = Depends(get_db)):
    database = db.query(MelonCloudTwitterDatabase)
    compute_database = filtering_meloncloud_twitter_database(params=params, db=database)
    limit_database = append_limit_to_database(params=params, database=compute_database)
    results = limit_database.all()
    data_results = [i.serialize for i in results]
    return response(data_results)


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
    if params.account_name is not None:
        database = database.filter(MelonCloudTwitterDatabase.account_id.contains(get_user_id(params.account_name)))
    if params.account_id is not None:
        database = database.filter(MelonCloudTwitterDatabase.account_id.contains(params.account_id))
    if params.event is not None:
        database = database.filter(MelonCloudTwitterDatabase.event.contains(params.event))
    if params.me_like is not None:
        database = database.filter(MelonCloudTwitterDatabase.memories.is_(params.me_like))
    if params.start_date is not None:
        ds = dt.datetime.strptime(params.start_date + " 00:00:00", '%Y-%m-%d %H:%M:%S')
        database = database.filter(MelonCloudTwitterDatabase.stored_at >= ds)
    if params.end_date is not None:
        de = dt.datetime.strptime(params.end_date + " 23:59:59", '%Y-%m-%d %H:%M:%S')
        database = database.filter(MelonCloudTwitterDatabase.stored_at <= de)

    if params.deleted is not None:
        database = database.filter(MelonCloudTwitterDatabase.deleted.is_(params.deleted))

    if params.sorting == SortingEnum.asc:
        database = database.order_by(asc(MelonCloudTwitterDatabase.stored_at))
    else:
        database = database.order_by(desc(MelonCloudTwitterDatabase.stored_at))

    return database


def append_limit_to_database(params, database):
    if not bool(params.infinite):
        page = params.page if params.page is not None else 0
        limit = params.limit if params.limit is not None else 50
        database = database.limit(limit).offset(int(page * limit))
    return database


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
