from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlalchemy.dialects.postgresql import ARRAY

from src.environments.database_config import MelonCloudDatabase
from src.tools.converters.datetime_converter import convert_datetime_to_string, \
    convert_datetime_to_string_for_backup_mode
from src.tools.converters.list_converter import list_to_set


class TwitterObserverDatabase(MelonCloudDatabase):
    __tablename__ = "MelonCloud_Twitter_Observer_Database"
    __bind_key__ = 'pasaad'

    id = Column(String, primary_key=True, unique=True, nullable=False)
    updatedAt = Column(DateTime(timezone=True), nullable=False)
    value = Column(String, nullable=False)
    objective = Column(String, nullable=False)
    paused = Column(Boolean, default=False)
    lastTweetId = Column(String, nullable=True)
    count = Column(Integer, nullable=False, default=0)

    def __init__(self, id, updatedAt, objective, value):
        self.id = id
        self.updatedAt = updatedAt
        self.objective = objective
        self.value = value
        self.paused = False
        self.count = 0
        self.lastTweetId = None