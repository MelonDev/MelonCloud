from sqlalchemy.orm import relationship

from src.environment.database import Base
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.tools.converters.datetime_converter import current_datetime_with_timezone


class BuffNotifyDatabase(Base):
    __tablename__ = "Buff_Notify_Database"
    __bind_key__ = 'pasaad'

    id = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4, nullable=False)
    activity_id = Column(UUID(as_uuid=True), ForeignKey('Buff_Activity_Log_Database.id'), nullable=False)

    status = Column(Boolean, default=True)
    datetime = Column(DateTime(timezone=True), nullable=False)
    value = Column(String, nullable=False)
    category = Column(String, nullable=False)
    schedule = Column(String, nullable=True)

    activity = relationship("BuffActivityLogDatabase", back_populates="notify")

    def __init__(self, activity_id, datetime, value, category):
        self.id = str(uuid.uuid4())
        self.activity_id = activity_id
        self.datetime = datetime
        self.value = value
        self.category = category

        self.status = True
