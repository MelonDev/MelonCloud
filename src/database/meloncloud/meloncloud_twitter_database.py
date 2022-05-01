import datetime

from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import ARRAY
from typing import List

from src.environment.database import Base
from src.tools.converters.datetime_converter import current_datetime_with_timezone, convert_datetime_to_string, \
    convert_datetime_to_string_for_backup_mode
from src.tools.converters.list_converter import list_to_set


class MelonCloudTwitterDatabase(Base):
    __tablename__ = "MelonCloud_Twitter_Database"
    __bind_key__ = 'meloncloud'

    id = Column(Text, primary_key=True, unique=True, nullable=False)
    tweeted_at = Column(DateTime(timezone=True), nullable=False)
    stored_at = Column(DateTime(timezone=True), nullable=False)
    message = Column(Text, nullable=True)
    account_id = Column(Text, nullable=False)
    hashtags = Column(ARRAY(Text), nullable=True)
    mentions = Column(ARRAY(Text), nullable=True)
    photos = Column(ARRAY(Text), nullable=True)
    type = Column(Text, nullable=True)
    thumbnail = Column(Text, nullable=True)
    videos = Column(ARRAY(Text), nullable=True)
    language = Column(Text, nullable=True)
    urls = Column(ARRAY(Text), nullable=True)
    event = Column(Text, nullable=True)
    deleted = Column(Boolean, default=False, nullable=True)
    memories = Column(Boolean, default=False, nullable=True)

    def __init__(self, id: str, tweeted_at: datetime, account_id: str):
        self.id = id
        self.tweeted_at = tweeted_at
        self.account_id = account_id

        self.stored_at = datetime.datetime.now()

        self.deleted = False
        self.memories = False

    def append_photos(self, photos: List[str]):
        self.photos = photos
        self.type = "PHOTO"

    def append_videos(self, videos: List[str], thumbnail: str):
        self.videos = videos
        self.thumbnail = thumbnail
        self.type = "VIDEO"

    def append_urls(self, urls: List[str]):
        self.urls = urls

    def append_mentions(self, mentions: List[str]):
        self.mentions = mentions

    def append_details(self, messages: str = None, hashtags: List[str] = None, language: str = None, event: str = None):
        self.message = messages
        self.hashtags = hashtags
        self.language = language
        self.message = messages
        self.event = event
        self.memories = event == "ME LIKE"

    @property
    def serialize(self):
        return {
            'id': self.id,
            'tweeted_at': convert_datetime_to_string(self.tweeted_at, disable_timezone=True),
            'stored_at': convert_datetime_to_string(self.stored_at, disable_timezone=True),
            'message': self.message,
            'account_id': self.account_id,
            'hashtags': self.hashtags,
            'mentions': self.mentions,
            'urls': self.urls,
            'type': self.type,
            'media': {
                'photos': self.photos,
                'videos': self.videos,
                'thumbnail': self.thumbnail
            },
            'language': self.language,
            'event': self.event,
            'memories': self.memories,
            'deleted': self.deleted

        }

    @property
    def export(self):
        return {
            'id': self.id,
            'tweeted_at': convert_datetime_to_string_for_backup_mode(self.tweeted_at),
            'stored_at': convert_datetime_to_string_for_backup_mode(self.stored_at),
            'message': self.message,
            'account_id': self.account_id,
            'hashtags': list_to_set(self.hashtags),
            'mentions': list_to_set(self.mentions),
            'urls': list_to_set(self.urls),
            'type': self.type,
            'photos': list_to_set(self.photos),
            'videos': list_to_set(self.videos),
            'thumbnail': self.thumbnail,
            'language': self.language,
            'event': self.event,
            'memories': self.memories,
            'deleted': self.deleted
        }
