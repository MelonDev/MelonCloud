from pydantic import BaseModel

from environment import OPENSSL_SECRET_KEY
from src.tools.as_form import as_form


class BuffSettings(BaseModel):
    authjwt_secret_key: str = OPENSSL_SECRET_KEY
    authjwt_token_location: set = {"cookies"}
    authjwt_cookie_csrf_protect: bool = False

@as_form
class RegisterFarmForm(BaseModel):
    name: str
    address: str
    email: str
    password :str
    auth_token :str = None
