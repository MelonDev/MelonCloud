import json

from sqlalchemy.orm import relationship

from src.environment.database import Base
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.environment.database_config import BuffManagementDatabase
from src.tools.converters.datetime_converter import current_datetime_with_timezone, convert_datetime_to_string, \
    convert_date_to_string


class BuffActivityLogDatabase(BuffManagementDatabase):
    __tablename__ = "Buff_Activity_Log_Database"
    __bind_key__ = 'buff_management'

    id = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    buff_id = Column(UUID(as_uuid=True), ForeignKey("Buff_Database.id"), nullable=False)
    name = Column(Text, nullable=False)
    value = Column(Text, nullable=True)
    secondary_value = Column(Text, nullable=True)
    bool_value = Column(Boolean, nullable=True)
    datetime_value = Column(DateTime(timezone=True), nullable=True)
    refer_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(Boolean, default=True)
    delete = Column(Boolean, default=False)

    buff = relationship("BuffDatabase", back_populates="activity")
    notify = relationship("BuffNotifyDatabase", back_populates="activity")

    def __init__(self, buff_id, name, value):
        self.id = uuid.uuid4()
        self.created_at = current_datetime_with_timezone()
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
    def breeding_serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "artificial_insemination": self.bool_value,
            # "datetime": convert_date_to_string(self.datetime_value),
            "date": self.datetime_value.date(),
            "notify": self.notify,
            "status": self.status,
            "delete": self.delete
        }

    @property
    def return_estrus_serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "estrus_message": self.value,
            "estrus_result": self.bool_value,
            "date": self.datetime_value.date(),
            "notify": self.notify,
            "status": self.status,
            "delete": self.delete
        }

    @property
    def vaccine_injection_serialize(self):
        x = self.secondary_value.split("/")
        return {
            "id": self.id,
            "name": self.name,
            "vaccine_name": self.value,
            "vaccine_key": x[0],
            "vaccine_duration": int(x[1]),
            "date": self.datetime_value.date(),
            "notify": self.notify,
            "status": self.status,
            "delete": self.delete
        }

    @property
    def deworming_serialize(self):
        return {
            "id": self.id,
            "anthelmintic_drug_name": self.value,
            "next_deworming_duration": self.secondary_value,
            "next_deworming_date": self.datetime_value,
            "notify": self.notify,
            "status": self.status,
            "delete": self.delete
        }

    @property
    def disease_treatment_serialize(self):
        obj = json.loads(str(self.secondary_value))
        return {
            "id": self.id,
            "disease_name": self.value,
            "symptom": obj['symptom'],
            "drugs": obj['drugs'],
            "healed_status": self.bool_value,
            "date": self.datetime_value,
            "status": self.status,
            "delete": self.delete
        }

    @property
    def mini_serialize(self):
        return {
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "value": self.value,
            "bool_value": self.bool_value,
            # "datetime_value": self.datetime_value,
            "date": self.datetime_value.date(),
            "refer_id": self.refer_id,
            "status": self.status,
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
            # "datetime_value": self.datetime_value,
            "date": self.datetime_value.date(),
            "refer_id": self.refer_id,
            "status": self.status,
        }
