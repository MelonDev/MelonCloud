from uuid import UUID

from pydantic import BaseModel

from environment import OPENSSL_SECRET_KEY
from src.tools.as_form import as_form


class MelonCloudBookSettings(BaseModel):
    authjwt_secret_key: str = OPENSSL_SECRET_KEY
    authjwt_token_location: set = {"cookies"}
    authjwt_cookie_csrf_protect: bool = False


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


class MelonCloudBookTokenModel:
    access_token: str

    def __init__(self, access_token):
        self.access_token = access_token

@as_form
class MelonCloudBookLoginForm(BaseModel):
    password: str