from enum import Enum


class ProfileQueryEnum(str, Enum):
    tweet = 'tweet'
    mention = 'mention'
    combine = 'combine'
    raw = 'raw'


class ProfileTypeEnum(str, Enum):
    user_id = 'user_id'
    screen_name = 'screen_name'
