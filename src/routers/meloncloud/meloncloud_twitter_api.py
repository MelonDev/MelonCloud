import datetime
import math
from collections import Counter
import re

from fastapi import APIRouter, Depends, status as code
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
import datetime as dt
from operator import is_not
from functools import partial
from src.database.meloncloud.meloncloud_twitter_database import MelonCloudTwitterDatabase
from src.engines.twitter_engines import get_tweet_id_from_link, get_meloncloud_tweet_model, get_status, \
    get_dict_lookup_user, get_user_profile, hasFavorited, like_tweet, get_dict_lookup_statuses
from src.enums.profile_enum import ProfileQueryEnum
from src.enums.sorting_enum import SortingTweet
from src.enums.type_enum import MelonCloudFileTypeEnum
from src.environment.database_config import get_db
from src.models.meloncloud_twitter_model import RequestAnalyzeModel, RequestTweetQueryModel, \
    RequestTweetModel, RequestPeopleQueryModel, RequestProfileModel, RequestMediaQueryModel, \
    RequestHashtagQueryModel, HashtagQueryDate, get_hashtag_dict, MediaExtraOptional, ValidatorModel, \
    MelonCloudBackupModel, BackupQueryDate, DatabaseQueryName, RequestMediaQueryFromAccountModel, \
    RequestTweetAppActionModel, TweetAction
from src.routers.meloncloud.meloncloud_error_response import bad_request_exception, not_found_exception
from src.routers.meloncloud.meloncloud_twitter_extension_function import packing_backup, get_profile, \
    is_overflow, media_query_to_people_query, media_result_packing, get_day, get_database_name, processing_tweet, \
    is_action
from src.routers.meloncloud.meloncloud_twitter_filter_function import database_media_type_categorize, \
    filtering_meloncloud_twitter_database_for_media, filtering_meloncloud_twitter_database, append_limit_to_database, \
    filtering_people_database, filtering_profile_database, filtering_meloncloud_twitter_database_for_hashtags, \
    database_for_backup, filtering_people_for_rank_database, filtering_meloncloud_twitter_database_for_profile_hashtags, \
    filtering_meloncloud_twitter_database_for_media_from_account, \
    filtering_meloncloud_twitter_database_for_media_profile_hashtags
from src.tools.chunks import chunks
from src.tools.converters.datetime_converter import convert_datetime_to_string
from src.tools.date_for_backup import today, first_day_of_month_with_time, \
    last_day_of_month_with_time, first_day_of_previous_month_with_time, last_day_of_previous_month_with_time, \
    first_day_of_year_with_time, last_day_of_year_with_time, \
    first_day_of_previous_year_with_time, last_day_of_previous_year_with_time
from src.tools.onedrive_adapter import send_url_to_meloncloud_onedrive
from src.tools.photos_endpoint import tweet_people_endpoint, tweet_photo_endpoint, tweet_video_endpoint, \
    tweet_all_media_endpoint
from src.tools.translate_engine import translate
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
            if params.account is None:
                bad_request_exception(message="Request optional profile but you can't sent account id")
            else:
                extra_optional = get_meloncloud_tweet_profile_endpoint(account).compact_serialize
        if params.extra_optional is MediaExtraOptional.PEOPLES:
            peoples_params = media_query_to_people_query(params)

            peoples_database = db.query(MelonCloudTwitterDatabase.account_id,
                                        func.count(MelonCloudTwitterDatabase.account_id))
            peoples_compute_database = filtering_people_for_rank_database(params=peoples_params, db=peoples_database)
            peoples_count = peoples_compute_database.count()
            peoples_raw = peoples_compute_database.all()
            peoples_reverse = (
                True if peoples_params.sorting is SortingTweet.DESC else False) if peoples_params.sorting is not None else True
            peoples_data_sorted = sorted(peoples_raw, key=lambda kv: kv[1], reverse=peoples_reverse)
            peoples_limit = len(peoples_data_sorted) if bool(peoples_params.infinite) else int(
                peoples_params.limit if peoples_params.limit is not None else 50)
            peoples_page = 0 if bool(peoples_params.infinite) else int(
                peoples_params.page if peoples_params.page is not None else 0) * peoples_limit
            peoples_real_page = int(peoples_params.page if peoples_params.page is not None else 0)

            peoples_total_page = int(math.ceil(peoples_count / peoples_limit)) if peoples_count > 0 else 0
            is_overflow(peoples_real_page, peoples_total_page)

            peoples_data_list = peoples_data_sorted[peoples_page:peoples_page + peoples_limit]

            if len(peoples_data_list) > 100:
                peoples_list_chunks = chunks(peoples_data_list, int(math.ceil(len(peoples_data_list) / 100)))
                peoples_list = {}
                for i in peoples_list_chunks:
                    peoples = get_dict_lookup_user(list(map(lambda x: str(x[0]), i)))
                    peoples_list.update(peoples)
                peoples_results = list(filter(partial(is_not, None),
                                              map(lambda x: tweet_people_endpoint(
                                                  get_meloncloud_tweet_profile_endpoint(
                                                      peoples_list.get(x[0], None)), x[1]),
                                                  peoples_data_list)))

            else:
                peoples = get_dict_lookup_user(list(map(lambda x: str(x[0]), peoples_data_list)))
                peoples_results = list(filter(partial(is_not, None),
                                              map(lambda x: tweet_people_endpoint(
                                                  get_meloncloud_tweet_profile_endpoint(peoples.get(x[0], None)),
                                                  x[1]),
                                                  peoples_data_list)))

            extra_optional = peoples_results

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


@router.get("/media/{account}")
async def get_media_from_account(params: RequestMediaQueryFromAccountModel = Depends(), db: Session = Depends(get_db)):
    limit = params.limit if params.limit is not None else 50
    page = params.page if params.page is not None else 0

    account = get_profile(params.account)

    results = {}

    file_type = MelonCloudFileTypeEnum.PHOTOS if params.type is None else params.type
    database = database_media_type_categorize(db=db, file_type=file_type)
    compute_database = filtering_meloncloud_twitter_database_for_media_from_account(params=params, db=database,
                                                                                    account=account, query=params.query)
    count = compute_database.count()
    total_page = int(math.ceil(count / limit)) if count > 0 else 0
    is_overflow(page, total_page)

    limit_database = compute_database.limit(limit).offset(int(page * limit))
    data = limit_database.all()

    fabric = {
        "total_items": count,
        "per_page": int(params.limit if params.limit is not None else 50),
        "item_on_page": len(results),
        "total_page": total_page,
        "current_page": page,
        "next_page": page + 1 if page < total_page - 1 else None,
        "previous_page": page - 1 if page > 0 else None
    }

    profile = get_meloncloud_tweet_profile_endpoint(account)

    if profile is not None:
        tweets_count = filtering_meloncloud_twitter_database_for_media_from_account(params=params, db=db,
                                                                                    account=account,
                                                                                    query=ProfileQueryEnum.TWEET).count()
        mentions_count = filtering_meloncloud_twitter_database_for_media_from_account(params=params, db=db,
                                                                                      account=account,
                                                                                      query=ProfileQueryEnum.MENTION).count()

        profile.set_optional_stats(tweets_count=tweets_count, mentions_count=mentions_count)
        results["profile"] = profile.full_serialize

    if bool(params.with_hashtags) and params.hashtag is None:
        hashtags_database = db.query(func.unnest(MelonCloudTwitterDatabase.hashtags))
        hashtags_compute_database = filtering_meloncloud_twitter_database_for_media_profile_hashtags(params=params,
                                                                                                     db=hashtags_database,
                                                                                                     account=account)
        hashtags_raw_data = hashtags_compute_database.all()
        hashtags_data = [str(i[0]) for i in hashtags_raw_data]
        hashtags_data_dict = dict(Counter(hashtags_data))
        hashtags_data_sorted = sorted(hashtags_data_dict.items(), key=lambda kv: kv[1], reverse=True)
        hashtags_results = [get_hashtag_dict(name, count) for name, count in hashtags_data_sorted[0:0 + 30]]
        results["hashtags"] = hashtags_results

    if file_type is MelonCloudFileTypeEnum.PHOTOS:
        results['media'] = list(map(lambda x: tweet_photo_endpoint(x, params.quality, account=params.account), data))
        return response(data=results, fabric=fabric)
    elif file_type is MelonCloudFileTypeEnum.VIDEOS:
        results['media'] = list(map(lambda x: tweet_video_endpoint(x, account=params.account), data))
        return response(data=results, fabric=fabric)
    elif file_type is MelonCloudFileTypeEnum.ALL:
        results['media'] = list(
            map(lambda x: tweet_all_media_endpoint(x, params.quality, account=params.account), data))
        return response(data=results, fabric=fabric)
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
        package = get_status(req.tweet_id)
        if package is None:
            not_found_exception()

        return response(package)
    else:
        tweet = db.query(MelonCloudTwitterDatabase).get(req.tweet_id)
        if tweet is None:
            not_found_exception()

        message = tweet.message
        message = message.replace("　", " ")
        message = re.sub(r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-]) ?", '', message, flags=re.MULTILINE)
        message = re.sub(r"(#(?:[^\x00-\x7F]|\w)+)", '', message, flags=re.MULTILINE)
        message = message.strip()

        #message = tweet.message if tweet.message.rfind("https://") == -1 else tweet.message.rsplit("https://", 1)[0]
        language = tweet.language if tweet.language != "zh" else "zh-cn"

        result = tweet.serialize
        result['message'] = message

        result['translate'] = None
        if req.translate is None or bool(req.translate):
            if language != "und":
                result['translate'] = {}

                trans = translate(src=language, text=message, dest=['en', 'th'])
                if trans is not None:
                    result['translate'] = trans
                else:
                    result['translate'][language] = message
            elif len(message) > 0:
                result['translate'] = {}
                result['translate']['und'] = message

        current_tweet = get_status(req.tweet_id)
        if current_tweet is not None:
            current = {
                "retweet_count": current_tweet['retweet_count'],
                "retweeted": current_tweet['retweeted'],
                "favorite_count": current_tweet['favorite_count'],
                "favorited": current_tweet['favorited'],
                "created_at": current_tweet['created_at'],
                # "source": filter_platforms_tweet(currentTweet['source'])
            }
            result['current'] = current

            if "user" in current_tweet:
                account = get_meloncloud_tweet_profile_endpoint(current_tweet['user'])
                result['account'] = account.compact_serialize
            else:
                result['account'] = None

        else:
            result['current'] = None
            result['account'] = None

        return response(result)


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
            tweets_count = filtering_profile_database(params=req,
                                                      database=db.query(MelonCloudTwitterDatabase).filter(
                                                          MelonCloudTwitterDatabase.account_id.contains(
                                                              profile.id))).count()
            mentions_count = filtering_profile_database(params=req,
                                                        database=db.query(MelonCloudTwitterDatabase).filter(
                                                            MelonCloudTwitterDatabase.mentions.any(
                                                                profile.id))).count()

            profile.set_optional_stats(tweets_count=tweets_count, mentions_count=mentions_count)

            result["profile"] = profile.full_serialize

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

            if bool(req.with_hashtags) and req.hashtag is None:
                hashtags_database = db.query(func.unnest(MelonCloudTwitterDatabase.hashtags))
                hashtags_compute_database = filtering_meloncloud_twitter_database_for_profile_hashtags(params=req,
                                                                                                       db=hashtags_database,
                                                                                                       account=account)
                hashtags_raw_data = hashtags_compute_database.all()
                hashtags_data = [str(i[0]) for i in hashtags_raw_data]
                hashtags_data_dict = dict(Counter(hashtags_data))
                hashtags_data_sorted = sorted(hashtags_data_dict.items(), key=lambda kv: kv[1], reverse=True)
                hashtags_results = [get_hashtag_dict(name, count) for name, count in hashtags_data_sorted[0:0 + 30]]
                result["hashtags"] = hashtags_results

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
    # skip_day = dt.timedelta(days=int(page * compound_days))
    desired_datetime = dt.timedelta(days=compound_days)
    # skip_datetime = current_datetime - desired_datetime
    back_to_datetime = (current_datetime - desired_datetime).replace(hour=0,
                                                                     minute=0,
                                                                     second=0,
                                                                     microsecond=0)
    print(current_datetime)
    print(back_to_datetime)
    compute_database = filtering_meloncloud_twitter_database_for_hashtags(params=params, db=database,
                                                                          skip_datetime=current_datetime,
                                                                          back_to_datetime=back_to_datetime)

    raw_data = compute_database.all()
    data = [str(i[0]) for i in raw_data]
    data_dict = dict(Counter(data))
    data_sorted = sorted(data_dict.items(), key=lambda kv: kv[1], reverse=True)
    print(f"LEN: {len(data_sorted)}", )
    count = len(data_sorted)
    total_page = int(math.ceil(count / limit)) if count > 0 else 0
    print(page)
    print(total_page)
    is_overflow(page, total_page)

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
            "start": convert_datetime_to_string(current_datetime, disable_timezone=True),
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

            if bool(request.from_app):
                tweet = package.tweet
                message = tweet.message if tweet.message.rfind("https://") == -1 else \
                    tweet.message.rsplit("https://", 1)[0]
                language = tweet.language if tweet.language != "zh" else "zh-cn"

                result = tweet.serialize
                result['translate'] = None
                if (request.translate is None or bool(request.translate)) and language != "und":
                    trans = translate(src=language, text=message, dest=['en', 'th'])
                    if trans is not None:
                        result['translate'] = trans

                current_tweet = get_status(tweet_id)
                if current_tweet is not None:
                    current = {
                        "retweet_count": current_tweet['retweet_count'],
                        "retweeted": current_tweet['retweeted'],
                        "favorite_count": current_tweet['favorite_count'],
                        "favorited": current_tweet['favorited'],
                        "created_at": current_tweet['created_at'],
                        # "source": filter_platforms_tweet(currentTweet['source'])
                    }
                    result['current'] = current

                    if "user" in current_tweet:
                        account = get_meloncloud_tweet_profile_endpoint(current_tweet['user'])
                        result['account'] = account.compact_serialize
                    else:
                        result['account'] = None

                else:
                    result['current'] = None
                    result['account'] = None

                return response(result)
            else:
                return response(package.tweet.serialize)
        else:
            bad_request_exception(message="Couldn't find any applicable data")
    except Exception as e:
        bad_request_exception(message="Found an error: " + str(e))


@router.post("/action", summary="ชื่นชอบทวีต",
             status_code=code.HTTP_201_CREATED)
async def action(params: RequestTweetAppActionModel = Depends(RequestTweetAppActionModel.as_form),
                 db: Session = Depends(get_db)):
    try:

        favorited = await hasFavorited(params.tweetid)
        if is_action(params.action, TweetAction.LIKE) and not favorited:
            await like_tweet(params.tweetid)

        item = db.query(MelonCloudTwitterDatabase).get(params.tweetid)
        package = await get_meloncloud_tweet_model(params.tweetid)

        if item is not None:
            tweet = item
        else:
            tweet = package.tweet
        tweet.stored_at = datetime.datetime.now()

        tweet.event = 'ME LIKE'
        tweet.memories = True
        db.add(tweet)
        db.commit()

        await send_url_to_meloncloud_onedrive(package.media_urls)

        message = tweet.message if tweet.message.rfind("https://") == -1 else \
            tweet.message.rsplit("https://", 1)[0]
        language = tweet.language if tweet.language != "zh" else "zh-cn"

        result = tweet.serialize
        result['translate'] = None
        if (params.translate is None or bool(params.translate)) and language != "und":
            trans = translate(src=language, text=message, dest=['en', 'th'])
            if trans is not None:
                result['translate'] = trans

        current_tweet = get_status(params.tweetid)
        if current_tweet is not None:
            current = {
                "retweet_count": current_tweet['retweet_count'],
                "retweeted": current_tweet['retweeted'],
                "favorite_count": current_tweet['favorite_count'],
                "favorited": current_tweet['favorited'],
                "created_at": current_tweet['created_at'],
                # "source": filter_platforms_tweet(currentTweet['source'])
            }
            result['current'] = current

            if "user" in current_tweet:
                account = get_meloncloud_tweet_profile_endpoint(current_tweet['user'])
                result['account'] = account.compact_serialize
            else:
                result['account'] = None

        else:
            result['current'] = None
            result['account'] = None

        return response(result)
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

def check_tweet_has_deleted(db):
    tweets = db.query(MelonCloudTwitterDatabase).filter(MelonCloudTwitterDatabase.deleted.is_(False)).order_by(func.random()).limit(100).all()
    data = get_dict_lookup_statuses([i.id for i in tweets])

    isChanged = False

    for tweet in tweets:
        deleted = tweet.id not in data
        if not tweet.memories and deleted:
            print(tweet.id)
            db.delete(tweet)
            isChanged = True
        elif tweet.deleted != deleted:
            tweet.deleted = deleted
            db.add(tweet)
            isChanged = True
    if isChanged:
        db.commit()
