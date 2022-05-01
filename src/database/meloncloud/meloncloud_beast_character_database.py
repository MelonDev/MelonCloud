from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID
import uuid
from typing import List

from sqlalchemy.orm import relationship

from src.environment.database import Base


class MelonCloudBeastCharacterDatabase(Base):
    __tablename__ = "MelonCloud_Beast_Character_Database"
    __bind_key__ = 'meloncloud'

    id = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("MelonCloud_People_Database.id"), nullable=False)
    species = Column(ARRAY(Text), nullable=False)
    colors = Column(ARRAY(Text), nullable=False)
    image_url = Column(ARRAY(Text), nullable=False)

    owner = relationship("MelonCloudPeopleDatabase", back_populates="characters")

    def __init__(self, owner_id: str, species: List[str], colors: List[str], image_url: str):
        self.id = uuid.uuid4()
        self.owner_id = owner_id
        self.species = species
        self.colors = colors
        self.image_url = image_url
