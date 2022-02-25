from enum import Enum


class ProfileQueryEnum(str, Enum):
    TWEET = 'TWEET'
    MENTION = 'MENTION'
    COMBINE = 'COMBINE'
    RAW = 'RAW'


class ProfileTypeEnum(str, Enum):
    USER_ID = 'USER_ID'
    SCREEN_NAME = 'SCREEN_NAME'
