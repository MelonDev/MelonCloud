import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.environment.database import Base
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Integer


class MelonCloudBookPageDatabase(Base):
    __tablename__ = "MelonCloud_Book_Page_Database"
    __bind_key__ = 'pasaad'

    id = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4, nullable=False)
    book_id = Column(UUID(as_uuid=True), ForeignKey("MelonCloud_Book_Database.id"), nullable=False)
    url = Column(Text, nullable=False)
    preview = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    extension = Column(Text, nullable=False)
    number = Column(Integer, nullable=False)

    book = relationship("MelonCloudBookDatabase", back_populates="pages")

    def __init__(self, book_id: uuid, url: str, preview: str, name: str, extension: str, number: int):
        self.id = uuid.uuid4()
        self.book_id = book_id
        self.url = url
        self.preview = preview
        self.name = name
        self.extension = extension
        self.number = number

    @property
    def serialize(self):
        return {
            "id": self.id,
            "url": self.url,
            "preview": self.preview,
            "name": self.name,
            "extension": self.extension,
            "number": self.number
        }

    @property
    def export(self):
        return {
            "id": self.id,
            "book_id": self.book_id,
            "name": self.name,
            "url": self.url,
            "preview": self.preview,
            "extension": self.extension,
            "number": self.number,
        }
