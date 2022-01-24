import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.environment.database import Base
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey


class MelonCloudBookPageDatabase(Base):
    __tablename__ = "MelonCloud_Book_Page_Database"
    __bind_key__ = 'pasaad'

    id = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4, nullable=False)
    book_id = Column(UUID(as_uuid=True), ForeignKey("MelonCloud_Book_Database.id"), nullable=False)
    url = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    extension = Column(Text, nullable=False)

    book = relationship("MelonCloudBookDatabase", back_populates="pages")

    def __init__(self, book_id: uuid, url: str, name: str, extension: str):
        self.id = uuid.uuid4()
        self.book_id = book_id
        self.url = url
        self.name = name
        self.extension = extension
