from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database.melondev_twitter_database import MelonDevTwitterDatabase
from src.environment.database import get_db
from src.models.response_model import ResponseModel
from src.models.twitter_model import TwitterAnalyzeModel
from src.tools.engines.twitter_engines import get_tweet_id_from_link, get_tweet_model
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


@router.post("/analyze")
async def analyzing(req: TwitterAnalyzeModel, db: Session = Depends(get_db)):
    try:
        tweet_id = get_tweet_id_from_link(req.url)
        if tweet_id is not None:
            package = await get_tweet_model(tweet_id)
            if str(req.tag)[:3] == 'FF ' and str(package.tweet.message)[:3] != 'RT ':
                package.tweet.event = str(req.tag)
                if str(req.tag) == 'ME LIKE':
                    package.tweet.memories = True
                if str(package.tweet.lang) == 'ja' or str(package.tweet.lang) == 'zh':
                    db.add(package.tweet)
                    db.commit()
                elif db.query(MelonDevTwitterDatabase).filter(
                        MelonDevTwitterDatabase.account.contains(str(package.tweet.account))).count():
                    db.add(package.tweet)
                    db.commit()
            elif str(package.tweet.message)[:3] != 'RT ':
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
