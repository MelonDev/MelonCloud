import uuid

import fastapi_jwt_auth.exceptions
from fastapi import APIRouter, Depends, HTTPException, status as code
from fastapi_jwt_auth import AuthJWT
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.database.buff_management.buff_database import BuffDatabase
from src.database.buff_management.farm_database import FarmDatabase
from src.environment.database import get_db

from src.models.buff_model import BuffSettings, RegisterFarmForm, BuffAuthenticatedResponseModel, BuffLoginForm, \
    BuffChangePasswordForm, BuffChangeFarmInfoForm, EditBuffForm, AddBuffForm
from src.models.response_model import ResponseModel
from src.tools.converters.datetime_converter import convert_short_string_to_datetime, \
    convert_short_string_form_to_datetime
from src.tools.verify_hub import verify_return


@AuthJWT.load_config
def get_config():
    return BuffSettings()


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


router = APIRouter()


@router.get("/", include_in_schema=False)
async def main():
    return "Buff management is connected"


@router.get('/info', include_in_schema=True, tags=['Farm'])
async def info(Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    await check_authorize(Authorize)
    id = Authorize.get_jwt_subject()
    farm = get_farm_from_id(db, id)
    result = farm.serialize
    result['buffs'] = [i.serialize for i in farm.buffs]
    return await verify_return(data=ResponseModel(data=result))


@router.post("/register", include_in_schema=True, tags=['Authentication'])
async def register(form: RegisterFarmForm = Depends(RegisterFarmForm.as_form), Authorize: AuthJWT = Depends(),
                   db: Session = Depends(get_db)):
    if isDuplicate(db, form.email):
        duplicate_on_database_exception()

    farm = FarmDatabase(name=form.farm_name, email=form.email, first_name=form.first_name, last_name=form.last_name,
                        address=form.address, password=get_password_hash(form.password))

    access_token = Authorize.create_access_token(subject=str(farm.id))
    refresh_token = Authorize.create_refresh_token(subject=str(farm.id))

    db.add(farm)
    db.commit()

    Authorize.set_access_cookies(access_token)
    Authorize.set_refresh_cookies(refresh_token)

    return await verify_return(data=ResponseModel(
        BuffAuthenticatedResponseModel(access_token=access_token, refresh_token=refresh_token,
                                       farm_name=form.farm_name)))


@router.post("/login", include_in_schema=True, tags=['Authentication'])
async def login(form: BuffLoginForm = Depends(BuffLoginForm.as_form), Authorize: AuthJWT = Depends(),
                db: Session = Depends(get_db)):
    farm = get_farm_from_email(db, email=form.email)
    if farm is None:
        not_found_exception()

    if not verify_password(plain_password=form.password, hashed_password=farm.password):
        unauthorized_exception()

    access_token = Authorize.create_access_token(subject=str(farm.id))
    refresh_token = Authorize.create_refresh_token(subject=str(farm.id))

    Authorize.set_access_cookies(access_token)
    Authorize.set_refresh_cookies(refresh_token)

    return await verify_return(data=ResponseModel(
        BuffAuthenticatedResponseModel(access_token=access_token, refresh_token=refresh_token,
                                       farm_name=farm.name)))


@router.patch('/change-info', include_in_schema=True, tags=['Farm'])
async def change_info(form: BuffChangeFarmInfoForm = Depends(BuffChangeFarmInfoForm.as_form),
                      Authorize: AuthJWT = Depends(),
                      db: Session = Depends(get_db)):
    await check_authorize(Authorize)
    id = Authorize.get_jwt_subject()

    farm = get_farm_from_id(db, id)
    if farm is None:
        bad_request_exception()

    farm.change_info(first_name=form.first_name, last_name=form.last_name, address=form.address,
                     farm_name=form.farm_name)

    db.add(farm)
    db.commit()

    return await verify_return(data=ResponseModel(data={"msg": "Change successfully"}))


@router.patch('/change-password', include_in_schema=True, tags=['Farm'])
async def change_password(form: BuffChangePasswordForm = Depends(BuffChangePasswordForm.as_form),
                          Authorize: AuthJWT = Depends(),
                          db: Session = Depends(get_db)):
    await check_authorize(Authorize)
    id = Authorize.get_jwt_subject()

    farm = get_farm_from_id(db, id)
    if farm is None:
        bad_request_exception()

    if not verify_password(plain_password=form.old_password, hashed_password=farm.password):
        bad_request_exception("YOUR OLD PASSWORD NOT CORRECT")

    farm.change_password(password=get_password_hash(form.new_password))

    db.add(farm)
    db.commit()

    return await verify_return(data=ResponseModel(data={"msg": "Change password successfully"}))


@router.post('/refresh', include_in_schema=True, tags=['Authentication'])
async def refresh(Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_refresh_token_required()

        current_user = Authorize.get_jwt_subject()
        new_access_token = Authorize.create_access_token(subject=current_user)

        Authorize.set_access_cookies(new_access_token)
        return await verify_return(data={"msg": "The token has been refresh", "access_token": str(new_access_token)})
    except fastapi_jwt_auth.exceptions.MissingTokenError:
        bad_request_exception(message="Missing Token")
        return await verify_return(data=None)
    except Exception as e:
        print(e)
        bad_request_exception(message="Found an error: " + str(e))
        return await verify_return(data=None)


@router.delete('/logout', include_in_schema=True, tags=['Authentication'])
async def logout(Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
        Authorize.unset_jwt_cookies()
        return await verify_return(data={"msg": "Successfully logout"})
    except fastapi_jwt_auth.exceptions.MissingTokenError:
        bad_request_exception(message="Missing Token")
        return await verify_return(data=None)
    except Exception as e:
        print(e)
        bad_request_exception(message="Found an error: " + str(e))
        return await verify_return(data=None)


@router.get('/buffs', include_in_schema=True, tags=['Buff'])
async def get_buffs(Authorize: AuthJWT = Depends(),
                    db: Session = Depends(get_db)):
    await check_authorize(Authorize)
    id = Authorize.get_jwt_subject()

    if id is None:
        bad_request_exception()
    buffs = db.query(BuffDatabase).filter(BuffDatabase.farm_id == uuid.UUID(id)).all()
    data_results = [i.serialize for i in buffs]

    return await verify_return(data=ResponseModel(data=data_results))


@router.get('/buffs/{id}', include_in_schema=True, tags=['Buff'])
async def detail_buff(id: str, Authorize: AuthJWT = Depends(),
                      db: Session = Depends(get_db)):
    await check_authorize(Authorize)
    farm_id = Authorize.get_jwt_subject()

    buff = await get_buff(db, id, farm_id)

    return await verify_return(data=get_buff_response(buff))


@router.patch('/buffs/{id}', include_in_schema=True, tags=['Buff'])
async def edit_buff(id: str, form: EditBuffForm = Depends(EditBuffForm.as_form), Authorize: AuthJWT = Depends(),
                    db: Session = Depends(get_db)):
    await check_authorize(Authorize)
    farm_id = Authorize.get_jwt_subject()

    buff = await get_buff(db, id, farm_id)

    if form.name:
        buff.name = form.name
    if form.gender:
        buff.gender = form.gender
    if form.birth_date:
        buff.birth_date = form.birth_date
    if form.source:
        buff.source = form.source
    if form.father_id:
        buff.father_id = form.father_id
    if form.mother_id:
        buff.mother_id = form.mother_id
    db.add(buff)
    db.commit()

    return await verify_return(data=get_buff_response(buff))


@router.patch('/buffs/{id}/restore', include_in_schema=True, tags=['Buff'])
async def restore_buff(id: str, Authorize: AuthJWT = Depends(),
                       db: Session = Depends(get_db)):
    await check_authorize(Authorize)
    farm_id = Authorize.get_jwt_subject()

    buff = await get_buff(db, id, farm_id)

    if not buff.delete:
        not_modified_exception()

    buff.delete = False
    db.add(buff)
    db.commit()

    return await verify_return(data=ResponseModel(data={"msg": "Restore successfully"}))


@router.post('/buffs', include_in_schema=True, tags=['Buff'])
async def add_buff(form: AddBuffForm = Depends(AddBuffForm.as_form),
                   Authorize: AuthJWT = Depends(),
                   db: Session = Depends(get_db)):
    await check_authorize(Authorize)
    id = Authorize.get_jwt_subject()

    if id is None:
        bad_request_exception()

    birth_date = convert_short_string_form_to_datetime(form.birth_date.strftime('%Y-%m-%d'))
    buff = BuffDatabase(name=form.name, gender=form.gender, birth_date=birth_date, farm_id=id)
    if form.father_id:
        buff.father_id = form.father_id
    if form.mother_id:
        buff.mother_id = form.mother_id
    if form.source:
        buff.source = form.source

    buffs = db.query(BuffDatabase).filter(BuffDatabase.farm_id == uuid.UUID(id)).all()
    buffs.append(buff)

    db.add(buff)
    db.commit()

    data_results = [i.serialize for i in buffs]

    return await verify_return(data=ResponseModel(data=data_results))


@router.delete('/buffs/{id}', include_in_schema=True, tags=['Buff'])
async def remove_buff(id: str, Authorize: AuthJWT = Depends(),
                      db: Session = Depends(get_db)):
    await check_authorize(Authorize)
    farm_id = Authorize.get_jwt_subject()

    buff = await get_buff(db, id, farm_id)

    if buff.delete:
        not_modified_exception()

    buff.delete = True
    db.add(buff)
    db.commit()

    return await verify_return(data=ResponseModel(data={"msg": "Delete successfully"}))


def get_buff_response(buff):
    result = buff.serialize
    result['farm'] = buff.farm.serialize
    result['activity'] = [i.sub_serialize for i in buff.activity]

    return ResponseModel(data=result)


async def get_buff(db, id, farm_id):
    buff = db.query(BuffDatabase).get(id)
    if buff.farm_id != uuid.UUID(farm_id):
        not_found_exception()
    return buff


async def check_authorize(Authorize: AuthJWT):
    try:
        Authorize.jwt_required()
    except fastapi_jwt_auth.exceptions.MissingTokenError:
        unauthorized_exception(message="UNAUTHORIZED")
        return await verify_return(data=None)
    except Exception as e:
        print(e)
        bad_request_exception(message="Found an error: " + str(e))
        return await verify_return(data=None)


def isDuplicate(db, email: str) -> bool:
    database = db.query(FarmDatabase)

    if email is not None:
        database = database.filter(FarmDatabase.email.contains(email))
        if database.count() == 0:
            return False

    return True


def get_farm_from_email(db, email: str):
    database = db.query(FarmDatabase)

    if email is not None:
        database = database.filter(FarmDatabase.email.contains(email))
        farm = database.first()
        return farm

    return None


def get_farm_from_id(db, id: str):
    database = db.query(FarmDatabase)

    if id is not None:
        farm = database.get(id)
        return farm

    return None


def auth_jwt_exception(message=None):
    raise HTTPException(
        status_code=code.HTTP_400_BAD_REQUEST,
        detail=message if message is not None else "AUTHENTICATION FAILED")


def missing_token_exception(message=None):
    raise HTTPException(
        status_code=code.HTTP_400_BAD_REQUEST,
        detail=message if message is not None else "MISSING TOKEN")


def invalid_header_exception(message=None):
    raise HTTPException(
        status_code=code.HTTP_400_BAD_REQUEST,
        detail=message if message is not None else "INVALID HEADER")


def jwt_decode_exception(message=None):
    raise HTTPException(
        status_code=code.HTTP_400_BAD_REQUEST,
        detail=message if message is not None else "AUTHENTICATION FAILED")


def csrf_exception(message=None):
    raise HTTPException(
        status_code=code.HTTP_400_BAD_REQUEST,
        detail=message if message is not None else "AUTHENTICATION FAILED")


def revoked_token_exception(message=None):
    raise HTTPException(
        status_code=code.HTTP_400_BAD_REQUEST,
        detail=message if message is not None else "REVOKED TOKEN FAILED")


def access_token_required_exception(message=None):
    raise HTTPException(
        status_code=code.HTTP_400_BAD_REQUEST,
        detail=message if message is not None else "ACCESS TOKEN REQUIRED")


def refresh_token_required_exception(message=None):
    raise HTTPException(
        status_code=code.HTTP_400_BAD_REQUEST,
        detail=message if message is not None else "REFRESH_TOKEN_REQUIRED")


def fresh_token_required_exception(message=None):
    raise HTTPException(
        status_code=code.HTTP_400_BAD_REQUEST,
        detail=message if message is not None else "FRESH_TOKEN_REQUIRED")


def bad_request_exception(message=None):
    raise HTTPException(
        status_code=code.HTTP_400_BAD_REQUEST,
        detail=message if message is not None else "BAD REQUEST")


def not_found_exception(message=None):
    raise HTTPException(
        status_code=code.HTTP_404_NOT_FOUND,
        detail=message if message is not None else "NOT FOUND")


def unauthorized_exception(message=None):
    raise HTTPException(
        status_code=code.HTTP_401_UNAUTHORIZED,
        detail=message if message is not None else "UNAUTHORIZED")


def not_modified_exception(message=None):
    raise HTTPException(
        status_code=code.HTTP_304_NOT_MODIFIED,
        detail=message if message is not None else "NOT_MODIFIED")


def duplicate_on_database_exception(message=None):
    raise HTTPException(
        status_code=code.HTTP_302_FOUND,
        detail=message if message is not None else "EMAIL ALREADY EXISTS")
