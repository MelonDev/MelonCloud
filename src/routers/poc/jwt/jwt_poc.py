from typing import List

from fastapi import APIRouter
from fastapi import HTTPException, Depends, Request
from fastapi_jwt_auth import AuthJWT
from pydantic import BaseModel
from src.environment import OPENSSL_SECRET_KEY
from src.tools.as_form import as_form

router = APIRouter()


class User(BaseModel):
    username: str
    password: str


@as_form
class UserLoginFrom(BaseModel):
    username: str
    password: str


class Settings(BaseModel):
    authjwt_secret_key: str = OPENSSL_SECRET_KEY
    # Configure application to store and get JWT from cookies
    authjwt_token_location: set = {"cookies"}
    # Disable CSRF Protection for this example default is True
    authjwt_cookie_csrf_protect: bool = False


@AuthJWT.load_config
def get_config():
    return Settings()


class Test1(BaseModel):
    a: str
    b: int


@as_form
class Test(BaseModel):
    param: str
    test: List[Test1]
    test1: Test1
    b: int = 1
    a: str = '2342'


@router.post('/test_form', response_model=Test)
async def test_form(request: Request, form: Test = Depends(Test.as_form)):
    return form


@router.post('/login')
def login(user: UserLoginFrom = Depends(UserLoginFrom.as_form), Authorize: AuthJWT = Depends()):
    if user.username != "chaiwiwat" or user.password != "hello":
        raise HTTPException(status_code=401, detail="Bad username or password")

    # Create the tokens and passing to set_access_cookies or set_refresh_cookies
    access_token = Authorize.create_access_token(subject=user.username)
    refresh_token = Authorize.create_refresh_token(subject=user.username)

    # Set the JWT cookies in the response
    Authorize.set_access_cookies(access_token)
    Authorize.set_refresh_cookies(refresh_token)
    return {"msg": "Successfully login"}


@router.post('/refresh')
def refresh(Authorize: AuthJWT = Depends()):
    Authorize.jwt_refresh_token_required()

    current_user = Authorize.get_jwt_subject()
    new_access_token = Authorize.create_access_token(subject=current_user)
    # Set the JWT cookies in the response
    Authorize.set_access_cookies(new_access_token)
    return {"msg": "The token has been refresh"}


@router.delete('/logout')
def logout(Authorize: AuthJWT = Depends()):
    """
    Because the JWT are stored in an httponly cookie now, we cannot
    log the user out by simply deleting the cookies in the frontend.
    We need the backend to send us a response to delete the cookies.
    """
    Authorize.jwt_required()

    Authorize.unset_jwt_cookies()
    return {"msg": "Successfully logout"}


@router.get('/protected')
def protected(Authorize: AuthJWT = Depends()):
    """
    We do not need to make any changes to our protected endpoints. They
    will all still function the exact same as they do when sending the
    JWT in via a headers instead of a cookies
    """
    Authorize.jwt_required()

    current_user = Authorize.get_jwt_subject()
    return {"user": current_user}
