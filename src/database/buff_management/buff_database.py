from sqlalchemy.orm import relationship

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.environments.database_config import BuffManagementDatabase
from src.tools.converters.datetime_converter import current_datetime_with_timezone, convert_date_to_string


class BuffDatabase(BuffManagementDatabase):
    __tablename__ = "Buff_Database"
    __bind_key__ = 'buff_management'

    id = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4, nullable=False)
    name = Column(Text, nullable=False)
    tag = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    delete = Column(Boolean, default=False)

    birth_date = Column(DateTime(timezone=True), nullable=False)
    father_id = Column(UUID(as_uuid=True), nullable=True)
    father_name = Column(Text, nullable=True)
    mother_id = Column(UUID(as_uuid=True), nullable=True)
    mother_name = Column(Text, nullable=True)

    farm_id = Column(UUID(as_uuid=True), ForeignKey("Buff_Farm_Database.id"), nullable=False)
    gender = Column(Text, nullable=False)
    source = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)

    farm = relationship("BuffFarmDatabase", back_populates="buffs")
    activity = relationship("BuffActivityLogDatabase", back_populates="buff")

    def __init__(self, name, gender, birth_date, farm_id, tag=None):
        self.name = name
        self.tag = tag
        self.gender = gender
        self.birth_date = birth_date
        self.farm_id = farm_id
        self.id = uuid.uuid4()
        dt = current_datetime_with_timezone()
        self.created_at = dt
        self.updated_at = dt
        self.delete = False

    @property
    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "tag": self.tag,
            "gender": self.gender,
            # "birth_date": convert_date_to_string(self.birth_date),
            "birth_date": self.birth_date.date(),
            "father_id": self.father_id,
            "father_name": self.father_name,
            "mother_id": self.mother_id,
            "mother_name": self.mother_name,
            "source": self.source,
            "image_url": self.image_url,
        }

    @property
    def sub_serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "tag": self.tag,
            "gender": self.gender,
            # "birth_date": convert_date_to_string(self.birth_date),
            "birth_date": self.birth_date.date(),
            "image_url": self.image_url,
        }
