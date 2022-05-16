from sqlalchemy.orm import relationship

from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ARRAY, ForeignKey
import uuid
from sqlalchemy.dialects.postgresql import UUID

from src.environments.database_config import MelonCloudDatabase
from src.tools.converters.datetime_converter import current_datetime_with_timezone, \
    convert_datetime_to_string_for_backup_mode
from src.tools.converters.list_converter import list_to_set


class MelonCloudBookDatabase(MelonCloudDatabase):
    __tablename__ = "MelonCloud_Book_Database"
    __bind_key__ = 'meloncloud'

    id = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4, nullable=False)
    name = Column(Text, nullable=False)
    language = Column(Text, nullable=True)
    artist = Column(Text, nullable=True)
    group = Column(Text, nullable=True)
    category = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    cover_url = Column(Text, nullable=True)
    tags = Column(ARRAY(Text), nullable=True)

    pages = relationship("MelonCloudBookPageDatabase", back_populates="book")

    def __init__(self, name: str, category: str, language: str = None, artist: str = None, group: str = None,
                 cover_url: str = None,
                 tags: list = None):
        self.id = uuid.uuid4()
        self.created_at = current_datetime_with_timezone()
        self.name = name
        self.category = category
        self.language = language
        self.artist = artist
        self.group = group
        self.cover_url = cover_url
        self.tags = tags

    @property
    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "language": self.language,
            "artist": self.artist,
            "group": self.group,
            "cover": self.cover_url
        }

    @property
    def export(self):
        return {
            "id": self.id,
            "created_at": convert_datetime_to_string_for_backup_mode(self.created_at),
            "name": self.name,
            "category": self.category,
            "language": self.language,
            "artist": self.artist,
            "group": self.group,
            "cover_url": self.cover_url,
            "tags": list_to_set(self.tags)
        }
