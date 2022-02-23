from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from src.environment.database import Base


class MelonCloudPeopleDatabase(Base):
    __tablename__ = "MelonCloud_People_Database"
    __bind_key__ = 'pasaad'

    id = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False)
    name = Column(Text, nullable=True)
    twitter_id = Column(Text, nullable=True)
    bilibili_id = Column(Text, nullable=True)
    furaffinity_id = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    nationality = Column(Text, nullable=True)
    gender = Column(Text, nullable=True)
    weight = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    year_of_birth = Column(Integer, nullable=True)
    partner = Column(UUID(as_uuid=True), nullable=True)

    characters = relationship("MelonCloudBeastCharacterDatabase", back_populates="owner")

    def __init__(self, id: str):
        self.id = id

    def append_details(self, name: str = None, image_url: str = None, nationality: str = None, gender: str = None,
                       weight: str = None, height: str = None, year_of_birth: str = None, partner: str = None,
                       twitter_id: str = None, bilibili_id: str = None, furaffinity_id: str = None):
        self.id = uuid.uuid4()

        self.name = name
        self.image_url = image_url
        self.nationality = nationality
        self.gender = gender
        self.weight = weight
        self.height = height
        self.year_of_birth = year_of_birth
        self.partner = partner
        self.twitter_id = twitter_id
        self.bilibili_id = bilibili_id
        self.furaffinity_id = furaffinity_id



    @property
    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "account": {
                "twitter": self.twitter_id,
                "bilibili": self.bilibili_id,
                "furaffinity": self.furaffinity_id
            },
            "image_url": self.image_url,
            "physical": {
                "weight": self.weight,
                "height": self.height
            },
            "nationality": self.nationality,
            "year_of_birth": self.year_of_birth,
            "partner": self.partner,
            "characters": self.characters
        }
