from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer
from sqlalchemy.dialects.postgresql import ARRAY

from src.environment.database import Base


class MelonCloudTwitterUserDatabase(Base):
    __tablename__ = "MelonCloud_Twitter_User_Database"
    __bind_key__ = 'pasaad'

    id = Column(Text, primary_key=True, unique=True, nullable=False)
    name = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    nationality = Column(Text, nullable=True)
    gender = Column(Text, nullable=True)
    weight = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    year_of_birth = Column(Text, nullable=True)
    relationship = Column(Text, nullable=True)
