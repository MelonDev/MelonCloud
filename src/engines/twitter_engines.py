import datetime

import tweepy
from fastapi import HTTPException, status as code

from environment import CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET
from src.database.melondev_twitter_database import MelonDevTwitterDatabase
from src.enums.profile_enum import ProfileTypeEnum
from src.models.twitter_model import TweetResponseModel
from src.tools.converters.datetime_converter import convert_string_to_datetime, current_datetime_with_timezone


def authentication():
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    return auth


def access():
    return tweepy.API(auth=authentication(), wait_on_rate_limit=True)


def test_client_mode():
    a = tweepy.Client(consumer_key=CONSUMER_KEY, consumer_secret=CONSUMER_SECRET, access_token=ACCESS_TOKEN,
                      access_token_secret=ACCESS_TOKEN_SECRET, wait_on_rate_limit=True)
    print(vars(a))
    a.get_user(id='2274369025')

    print(a)


def get_tweet_id_from_link(url):
    try:
        return url.split('/')[-1]
    except:
        return None


def get_status(id):
    try:
        data = access().get_status(id, tweet_mode='extended')
        return data._json
    except tweepy.errors.TweepyException:
        return None


def get_user_profile(account, type: ProfileTypeEnum = ProfileTypeEnum.user_id):
    print(account)
    try:
        if type is ProfileTypeEnum.user_id:
            data = access().get_user(user_id=account)
            return data._json
        if type is ProfileTypeEnum.screen_name:
            data = access().get_user(screen_name=account)
            return data._json
        return None
    except tweepy.errors.TweepyException as e:
        print("Error: " + str(e))
        return None


def get_lookup_user(ids: list):
    try:
        data = access().lookup_users(user_id=ids)
        return list(map(lambda x: x._json, data))
    except tweepy.errors.TweepyException:
        return None


def get_dict_lookup_user(ids: list):
    try:
        data = access().lookup_users(user_id=ids)
        return dict(map(lambda x: (x._json['id_str'], x._json), data))
    except tweepy.errors.TweepyException:
        return None


async def like(id):
    try:
        access().create_favorite(id)
        return await get_tweet_model(id)
    except tweepy.errors.TweepyException:
        return None


async def like_tweet(id):
    try:
        access().create_favorite(id)
        return True
    except tweepy.errors.TweepyException:
        return None


def unlike(id):
    try:
        data = access().destroy_favorite(id)

        return data._json
    except tweepy.errors.TweepyException:
        return None


def get_user_address(id):
    try:
        user = access().get_user(id)
        return {"name": user.screen_name, "id": user.id_str}
    except tweepy.errors.TweepyException:
        return None


def get_user_id(address):
    try:
        user = access().get_user(screen_name=address)
        return user.id_str
    except tweepy.errors.TweepyException:
        return None


def get_user_id_json(address):
    try:
        user = access().get_user(screen_name=address)
        return {"name": user.screen_name, "id": user.id_str}
    except tweepy.errors.TweepyException:
        return None


def initialize_tweet_model(data) -> MelonDevTwitterDatabase:
    created_at = convert_string_to_datetime(str(data['created_at']))

    model = MelonDevTwitterDatabase(id=data['id_str'], createdAt=created_at, addedAt=datetime.datetime.now(),
                                    account=data['user']['id_str'])
    model.message = data['full_text']
    model.lang = data['lang']
    model.deleted = False

    return model


async def hasFavorited(id) -> bool:
    tweet = await get_status(id)
    return bool(tweet['favorited']) if "favorited" in tweet else False


async def hasRetweeted(id) -> bool:
    tweet = await get_status(id)
    return bool(tweet['retweeted']) if "retweeted" in tweet else False


async def get_tweet_model(id) -> TweetResponseModel:
    data = get_status(id)

    if data is None:
        raise HTTPException(
            status_code=code.HTTP_404_NOT_FOUND,
            detail="The requested tweet was not found")

    tweet = initialize_tweet_model(data)

    video_list = []
    photo_list = []
    media_url_list = []

    hashtag_list = []
    user_mentions_list = []
    urls_list = []

    if 'extended_entities' in data:
        media = data['extended_entities']['media']
        for value in media:
            type = value['type']
            if type == 'video' or type == 'animated_gif':
                thumbnail = value['media_url_https']
                tweet.thumbnail = thumbnail
                info = value['video_info']
                variants = info['variants']
                for i in variants:
                    if 'bitrate' not in i:
                        variants.remove(i)
                video_url = max(variants, key=lambda x: x['bitrate'])['url']

                name = (video_url.split('/')[-1]).split('?')[0].replace(".mp4", "")

                video_list.append(video_url)
                media_url_list.append({
                    "name": name,
                    "url": video_url,
                    "type": "video"
                })
            if type == 'photo':
                photo_url = value['media_url_https']
                photo_list.append(photo_url)

                name = (photo_url.split('/')[-1]).replace(".jpg", "")

                media_url_list.append({
                    "name": name,
                    "url": photo_url,
                    "type": "photo"
                })

    type = "text"

    if len(video_list) > 0:
        tweet.video = video_list
        type = "video"
    else:
        tweet.video = None

    if len(photo_list) > 0:
        tweet.photo = photo_list
        type = "photo"
    else:
        tweet.photo = None

    tweet.type = type

    entities = data['entities']
    hashtag = entities['hashtags']
    if len(hashtag) > 0:
        for value in hashtag:
            hashtag_list.append(value['text'])
        tweet.hashtag = hashtag_list
    else:
        tweet.hashtag = None

    user_mentions = entities['user_mentions']
    if len(user_mentions) > 0:
        for value in user_mentions:
            user_mentions_list.append(value['id_str'])
        tweet.mention = user_mentions_list
    else:
        tweet.mention = None

    entities_url = entities['urls']
    if len(entities_url) > 0:
        for value in entities_url:
            urls_list.append(value['expanded_url'])
        tweet.urls = urls_list
    else:
        tweet.urls = None

    return TweetResponseModel(tweet=tweet, media_urls=media_url_list)