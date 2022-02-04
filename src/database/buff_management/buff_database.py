from sqlalchemy.orm import relationship

from src.environment.database import Base
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.tools.converters.datetime_converter import current_datetime_with_timezone


class BuffDatabase(Base):
    __tablename__ = "Buff_Database"
    __bind_key__ = 'pasaad'

    id = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4, nullable=False)
    name = Column(Text, nullable=False)
    tag = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    delete = Column(Boolean, default=False)

    birth_date = Column(DateTime(timezone=True), nullable=False)
    father_id = Column(UUID(as_uuid=True), nullable=True)
    mother_id = Column(UUID(as_uuid=True), nullable=True)
    farm_id = Column(UUID(as_uuid=True), ForeignKey("Farm_Database.id"), nullable=False)
    gender = Column(Text, nullable=False)
    source = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)

    farm = relationship("FarmDatabase", back_populates="buffs")
    activity = relationship("BuffActivityLogDatabase", back_populates="buff")

    def __init__(self, name, tag, gender, birth_date, farm_id):
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
            "birth_date": self.birth_date,
            "father_id": self.father_id,
            "mother_id": self.mother_id,
            "source": self.source,
            "image_url": self.image_url,
        }
