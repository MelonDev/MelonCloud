import datetime

import tweepy

from environment import CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET
from src.database.melondev_twitter_database import MelonDevTwitterDatabase
from src.models.twitter_model import ResponseTweetModel
from src.tools.converters.datetime_converter import convert_string_to_datetime, current_datetime_with_timezone


def authentication():
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    return auth


def access():
    return tweepy.API(authentication(), wait_on_rate_limit=True)


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


def get_user_profile(id):
    try:
        data = access().get_user(id)
        return data._json
    except tweepy.errors.TweepyException:
        return None


def like(id):
    try:
        access().create_favorite(id)
        return get_tweet_model(id)
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


async def get_tweet_model(id) -> ResponseTweetModel:
    data = get_status(id)
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

    return ResponseTweetModel(tweet=tweet, media_urls=media_url_list)
