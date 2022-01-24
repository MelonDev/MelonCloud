from sqlalchemy.orm import relationship

from src.environment.database import Base
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ARRAY, ForeignKey
import uuid
from sqlalchemy.dialects.postgresql import UUID

from src.tools.converters.datetime_converter import current_datetime_with_timezone


class MelonCloudBookDatabase(Base):
    __tablename__ = "MelonCloud_Book_Database"
    __bind_key__ = 'pasaad'

    id = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4, nullable=False)
    name = Column(Text, nullable=False)
    language = Column(Text, nullable=True)
    artist = Column(Text, nullable=True)
    group = Column(Text, nullable=True)
    category = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    cover_url = Column(Text, nullable=True)
    tags = Column(ARRAY(Text))

    pages = relationship("MelonCloudBookPageDatabase", back_populates="book")

    def __init__(self, name: str, category: str, language: str = None, artist: str = None, group: str = None,
                 cover_id: str = None,
                 tags: list = None):
        self.id = uuid.uuid4()
        self.created_at = current_datetime_with_timezone()
        self.name = name
        self.category = category
        self.language = language
        self.artist = artist
        self.group = group
        self.cover_id = cover_id
        self.tags = tags if tags is not None else []
