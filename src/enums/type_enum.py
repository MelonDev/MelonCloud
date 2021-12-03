from enum import Enum


class ImageQualityEnum(str, Enum):
    thumb = 'thumb'
    small = 'small'
    medium = 'medium'
    large = 'large'
    orig = 'orig'


class FileTypeEnum(str, Enum):
    photos = 'photos'
    videos = 'videos'
