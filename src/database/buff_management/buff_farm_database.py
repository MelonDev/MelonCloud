from sqlalchemy.orm import relationship

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
    email = Column(Text, nullable=True, unique=True)
    name = Column(Text, nullable=False)
    first_name = Column(Text, nullable=False)
    last_name = Column(Text, nullable=False)

    password = Column(Text, nullable=True)

    phone_number = Column(Text, nullable=True, unique=True)

    address = Column(Text, nullable=True)
    province = Column(Text, nullable=True)
    district = Column(Text, nullable=True)
    sub_district = Column(Text, nullable=True)

    token = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    delete = Column(Boolean, default=False)

    buffs = relationship("BuffDatabase", back_populates="farm")

    def __init__(self, name, first_name, last_name, phone_number, password=None, address=None, province=None,
                 district=None,
                 sub_district=None, email=None, token=None):
        self.id = uuid.uuid4()
        self.name = name
        self.phone_number = phone_number
        self.address = address
        self.province = province
        self.district = district
        self.sub_district = sub_district
        self.email = email
        self.token = token
        self.first_name = first_name
        self.last_name = last_name
        self.password = password
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
            "address": {
                "data": self.address,
                "province": self.province,
                "district": self.district,
                "sub_district": self.sub_district,
            },
            "email": self.email,
            "phone_number": self.phone_number
        }

    @property
    def test(self):
        return {
            "farm_name": self.name,
            "address": self.address,
            "email": self.email,
            "auth_token": self.auth_token,
            # "buffs": [buff.sub_serialize for buff in self.buffs]]
            "buffs": self.buffs
        }
