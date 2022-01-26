from uuid import UUID

from pydantic import BaseModel


class RequestBookQueryModel(BaseModel):
    id: UUID = None
    name: str = None
    language: str = None
    artist: str = None
    group: str = None
    category: str = None
    limit: int = None
    page: int = None
    infinite: bool = None
    random: bool = None
