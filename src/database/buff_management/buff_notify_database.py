from sqlalchemy.orm import relationship

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.environments.database_config import BuffManagementDatabase
from src.tools.converters.datetime_converter import current_datetime_with_timezone, convert_datetime_to_string


class BuffNotifyDatabase(BuffManagementDatabase):
    __tablename__ = "Buff_Notify_Database"
    __bind_key__ = 'buff_management'

    id = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4, nullable=False)
    activity_id = Column(UUID(as_uuid=True), ForeignKey('Buff_Activity_Log_Database.id'), nullable=False)
    farm_id = Column(UUID(as_uuid=True), nullable=False)

    status = Column(Boolean, default=True)
    datetime = Column(DateTime(timezone=True), nullable=False)
    value = Column(Text, nullable=False)
    category = Column(Text, nullable=False)
    schedule = Column(Integer, nullable=True)

    activity = relationship("BuffActivityLogDatabase", back_populates="notify")

    def __init__(self, activity_id, datetime, value, farm_id, category):
        self.id = uuid.uuid4()
        self.farm_id = farm_id
        self.activity_id = activity_id
        self.datetime = datetime
        self.value = value
        self.category = category

    @property
    def serialize(self):
        return {
            "id": self.id,
            "value": self.value,
            "category": self.category,
            # "farm_id": self.farm_id,
            # "notify_datetime": convert_datetime_to_string(self.notify_datetime),
            "notify_datetime": self.datetime.date(),
            "status": self.status
        }
