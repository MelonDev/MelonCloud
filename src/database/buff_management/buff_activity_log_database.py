from sqlalchemy.orm import relationship

from src.environment.database import Base
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.tools.converters.datetime_converter import current_datetime_with_timezone


class BuffActivityLogDatabase(Base):
    __tablename__ = "Buff_Activity_Log_Database"
    __bind_key__ = 'pasaad'

    id = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    buff_id = Column(UUID(as_uuid=True),ForeignKey("Buff_Database.id"), nullable=False)
    name = Column(Text, nullable=False)
    value = Column(Text, nullable=False)
    secondary_value = Column(Text, nullable=True)
    bool_value = Column(Boolean, nullable=True)
    datetime_value = Column(DateTime(timezone=True), nullable=True)
    refer_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(Boolean, default=True)
    delete = Column(Boolean, default=False)

    buff = relationship("BuffDatabase", back_populates="activity")
    notify = relationship("BuffNotifyDatabase", back_populates="activity")

    def __init__(self, buff_id, name, value):
        self.id = str(uuid.uuid4())
        self.createdAt = current_datetime_with_timezone()
        self.updated_at = current_datetime_with_timezone()

        self.buff_id = buff_id
        self.name = name
        self.value = value

        self.delete = False
        self.status = True

    @property
    def serialize(self):
        return {

        }

    @property
    def sub_serialize(self):
        return {
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "value": self.value,
            "secondary_value": self.secondary_value,
            "bool_value": self.bool_value,
            "datetime_value": self.datetime_value,
            "refer_id": self.refer_id,
            "status": self.status,
        }