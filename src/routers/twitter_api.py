from fastapi import APIRouter, Depends, HTTPException, status as code
from sqlalchemy import desc, asc
from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query as DBQuery
from sqlalchemy.orm.session import Session as DBSession
import datetime as dt

from src.database.melondev_twitter_database import MelonDevTwitterDatabase
from src.environment.database import get_db
from src.models.response_model import ResponseModel
from src.models.twitter_model import TwitterAnalyzeModel, TwitterQueryModel
from src.tools.engines.twitter_engines import get_tweet_id_from_link, get_tweet_model, get_user_id
from src.tools.onedrive_adapter import send_url_to_onedrive
from src.tools.verify_hub import verify_return

router = APIRouter()


@router.get("/")
async def status(db: Session = Depends(get_db)):
    return await verify_return(
        data="I have " + str(db.query(MelonDevTwitterDatabase).count()) + " tweets on my database")


@router.get("/count")
async def counting(db: Session = Depends(get_db)):
    count = db.query(MelonDevTwitterDatabase).count()
    return ResponseModel(count)


@router.get("/tweets")
async def tweets(params: TwitterQueryModel = Depends(), db: Session = Depends(get_db)):
    database = db.query(MelonDevTwitterDatabase)

    results = apply_database_filters(params=params, db=database).all()

    return await verify_return(data=ResponseModel([i.serialize for i in results]))


@router.post("/analyze")
async def analyzing(req: TwitterAnalyzeModel, db: Session = Depends(get_db)):
    try:
        tweet_id = get_tweet_id_from_link(req.url)
        if tweet_id is not None:
            package = await get_tweet_model(tweet_id)
            if str(req.tag)[:8] == 'HASHTAG ' and is_retweet(package.tweet.message):
                package.tweet.event = str(req.tag)
                if str(req.tag) == 'ME LIKE':
                    package.tweet.memories = True
                if is_circle_language(package.tweet.lang) or has_in_my_history(db, package.tweet.account):
                    db.add(package.tweet)
                    db.commit()
            elif is_retweet(package.tweet.message):
                item = db.query(MelonDevTwitterDatabase).filter(
                    MelonDevTwitterDatabase.id == str(tweet_id)).first()
                if item is not None:
                    if str(req.tag) == 'ME LIKE':
                        await send_url_to_onedrive(package.media_urls)
                        item.memories = True
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
            return await verify_return(code=404)
    except Exception as e:
        print(e)
        return await verify_return(data=None)


def is_retweet(value) -> bool:
    return str(value)[:3] != 'RT '


def is_circle_language(value) -> bool:
    return str(value) == 'ja' or str(value) == 'zh'


def has_in_my_history(db, account) -> bool:
    return db.query(
        MelonDevTwitterDatabase).filter(MelonDevTwitterDatabase.account.contains(str(account))).count() > 0


def apply_database_filters(params: TwitterQueryModel, db):
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

    if bool(params.asc):
        database = database.order_by(asc(MelonDevTwitterDatabase.addedAt))
    else:
        database = database.order_by(desc(MelonDevTwitterDatabase.addedAt))

    if not bool(params.unlimited):
        page = params.page if params.page is not None else 0
        limit = params.limit if params.limit is not None else 20
        database = database.limit(limit).offset(int(page * limit))

    return database


def bad_request(message=None):
    raise HTTPException(
        status_code=code.HTTP_400_BAD_REQUEST,
        detail=message if message is not None else "BAD REQUEST")
