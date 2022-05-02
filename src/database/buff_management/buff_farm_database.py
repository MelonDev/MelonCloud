from sqlalchemy.orm import relationship

from src.environments.database import Base
from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.environments.database_config import BuffManagementDatabase
from src.tools.converters.datetime_converter import current_datetime_with_timezone


class BuffFarmDatabase(BuffManagementDatabase):
    __tablename__ = "Buff_Farm_Database"
    __bind_key__ = 'buff_management'

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

    def __init__(self, name, email, first_name, last_name, password, address=None):
        self.name = name
        self.address = address
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.password = password
        self.id = uuid.uuid4()
        dt = current_datetime_with_timezone()
        self.created_at = dt
        self.updated_at = dt
        self.delete = False

    def change_password(self, password):
        self.password = password
        self.updated_at = current_datetime_with_timezone()

    def change_info(self, first_name, last_name, address, farm_name):
        if first_name or last_name or address or farm_name:
            self.updated_at = current_datetime_with_timezone()
            if first_name:
                self.first_name = first_name
            if last_name:
                self.last_name = last_name
            if address:
                self.address = address
            if farm_name:
                self.name = farm_name

    @property
    def serialize(self):
        return {
            "farm_name": self.name,
            "address": self.address,
            "email": self.email,
        }

    @property
    def test(self):
        return {
            "farm_name": self.name,
            "address": self.address,
            "email": self.email,
            #"buffs": [buff.sub_serialize for buff in self.buffs]]
            "buffs" : self.buffs
        }
