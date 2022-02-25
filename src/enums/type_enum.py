from enum import Enum


class ImageQualityEnum(str, Enum):
    THUMB = 'THUMB'
    SMALL = 'SMALL'
    MEDIUM = 'MEDIUM'
    LARGE = 'LARGE'
    ORIG = 'ORIG'


class FileTypeEnum(str, Enum):
    PHOTOS = 'VIDEOS'
    VIDEOS = 'PHOTOS'
