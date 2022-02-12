from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import ARRAY

from src.environment.database import Base


class MelonCloudTwitterDatabase(Base):
    __tablename__ = "MelonCloud_Twitter_Database"
    __bind_key__ = 'pasaad'

    id = Column(Text, primary_key=True, unique=True, nullable=False)
    createdAt = Column(DateTime(timezone=True), nullable=False)
    addedAt = Column(DateTime(timezone=True), nullable=False)
    message = Column(Text)
    account = Column(Text, nullable=False)
    hashtag = Column(ARRAY(Text))
    mention = Column(ARRAY(Text))
    photo = Column(ARRAY(Text))
    type = Column(Text)
    thumbnail = Column(Text)
    video = Column(ARRAY(Text))
    lang = Column(Text)
    urls = Column(ARRAY(Text))
    event = Column(Text)
    deleted = Column(Boolean, default=False)
    memories = Column(Boolean, default=False)

    def __init__(self, id, createdAt, addedAt, account):
        self.id = id
        self.createdAt = createdAt
        self.addedAt = addedAt
        self.account = account
