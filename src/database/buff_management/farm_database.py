from sqlalchemy.orm import relationship

from src.environment.database import Base
from sqlalchemy import Column, String, DateTime, Boolean,Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.tools.converters.datetime_converter import current_datetime_with_timezone


class FarmDatabase(Base):
    __tablename__ = "Farm_Database"
    __bind_key__ = 'pasaad'

    id = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4, nullable=False)
    email = Column(Text, nullable=False, unique=True)
    name = Column(Text, nullable=False)
    first_name = Column(Text, nullable=False)
    last_name = Column(Text, nullable=False)

    password = Column(Text, nullable=True)
    address = Column(Text, nullable=True)
    auth_token = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    delete = Column(Boolean, default=False)

    buffs = relationship("BuffDatabase", back_populates="farm")

    def __init__(self, name, address=None):
        self.name = name
        self.address = address
        self.id = str(uuid.uuid4())
        self.createdAt = current_datetime_with_timezone()
        self.updated_at = current_datetime_with_timezone()
        self.delete = False
