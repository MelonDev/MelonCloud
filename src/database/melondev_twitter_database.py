from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import ARRAY

from src.environment.database import Base
from src.tools.converters.datetime_converter import convert_datetime_to_string, \
    convert_datetime_to_string_for_backup_mode
from src.tools.converters.list_converter import list_to_set


def dump_datetime(value):
    if value is None:
        return None
    return [value.strftime("%Y-%m-%d")]


class MelonDevTwitterDatabase(Base):
    __tablename__ = "MelonDev_Twitter_Database"
    __bind_key__ = 'pasaad'

    id = Column(String, primary_key=True, unique=True, nullable=False)
    createdAt = Column(DateTime(timezone=True), nullable=False)
    addedAt = Column(DateTime(timezone=True), nullable=False)
    message = Column(String)
    account = Column(String, nullable=False)
    hashtag = Column(ARRAY(String))
    mention = Column(ARRAY(String))
    photo = Column(ARRAY(String))
    type = Column(String)
    thumbnail = Column(String)
    video = Column(ARRAY(String))
    lang = Column(String)
    urls = Column(ARRAY(String))
    event = Column(String)
    deleted = Column(Boolean, default=False)
    memories = Column(Boolean, default=False)

    def __init__(self, id, createdAt, addedAt, account):
        self.id = id
        self.createdAt = createdAt
        self.addedAt = addedAt
        self.account = account


    @property
    def serialize(self):
        return {
            'id': self.id,
            'createdAt': convert_datetime_to_string(self.createdAt),
            'addedAt': convert_datetime_to_string(self.addedAt),
            'message': self.message,
            'account': self.account,
            'hashtag': self.hashtag,
            'mention': self.mention,
            'urls': self.urls,
            'type': self.type,
            'media': {
                'photo': self.photo,
                'video': self.video,
                'thumbnail': self.thumbnail
            },
            'lang': self.lang,
            'event': self.event,
            'memories': self.memories,
            'deleted': self.deleted
        }

    @property
    def export(self):
        return {
            'id': self.id,
            'createdAt': convert_datetime_to_string_for_backup_mode(self.createdAt),
            'addedAt': convert_datetime_to_string_for_backup_mode(self.addedAt),
            'message': self.message,
            'account': self.account,
            'hashtag': list_to_set(self.hashtag),
            'mention': list_to_set(self.mention),
            'urls': list_to_set(self.urls),
            'type': self.type,
            'photo': list_to_set(self.photo),
            'video': list_to_set(self.video),
            'thumbnail': self.thumbnail,
            'lang': self.lang,
            'event': self.event,
            'memories': self.memories,
            'deleted': self.deleted
        }

