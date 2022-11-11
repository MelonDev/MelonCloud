import json
import uuid

import fastapi_jwt_auth.exceptions
from fastapi import APIRouter, Depends, HTTPException, status as code
from fastapi_jwt_auth import AuthJWT
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.database.buff_management.buff_activity_log_database import BuffActivityLogDatabase
from src.database.buff_management.buff_database import BuffDatabase
from src.database.buff_management.buff_notify_database import BuffNotifyDatabase
from src.database.buff_management.buff_farm_database import BuffFarmDatabase
from src.environments.database_config import get_db
import datetime

from src.models.buff_model import BuffSettings, RegisterFarmForm, BuffAuthenticatedResponseModel, BuffLoginForm, \
    BuffChangePasswordForm, BuffChangeFarmInfoForm, EditBuffForm, AddBuffForm, BuffBreedingModel, GetBuffModel, \
    BuffEditBreedingModel, BuffActivityType, BuffReturnEstrusModel, BuffEditReturnEstrusModel, \
    BuffVaccineInjectionModel, vaccines, BuffVaccine, BuffEditVaccineInjectionModel, BuffDewormingModel, \
    BuffEditDewormingModel, BuffDiseaseTreatmentModel, BuffEditDiseaseTreatmentModel
from src.models.response_model import ResponseModel
from src.tools.converters.datetime_converter import convert_short_string_to_datetime, \
    convert_short_string_form_to_datetime, current_datetime_with_timezone
from src.tools.db_exporter import current_datetime
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
    result['buffs'] = [i.sub_serialize for i in farm.buffs]
    return await verify_return(data=ResponseModel(data=result))


@router.post("/register", include_in_schema=True, tags=['Authentication'])
async def register(form: RegisterFarmForm = Depends(RegisterFarmForm.as_form), Authorize: AuthJWT = Depends(),
                   db: Session = Depends(get_db)):
    if isDuplicate(db, form.phone_number):
        duplicate_on_database_exception()

    if form.token is not None:
        farm = BuffFarmDatabase(name=form.farm_name, token=form.token, first_name=form.first_name,
                                last_name=form.last_name,
                                address=form.address, phone_number=form.phone_number, province=form.province,
                                district=form.district, sub_district=form.sub_district)
    else:
        farm = BuffFarmDatabase(name=form.farm_name, email=form.email, first_name=form.first_name,
                                last_name=form.last_name,
                                address=form.address, password=get_password_hash(form.password),
                                phone_number=form.phone_number, province=form.province, district=form.district,
                                sub_district=form.sub_district)

    access_token = Authorize.create_access_token(subject=str(farm.id), expires_time=datetime.timedelta(days=7))
    # access_token = Authorize.create_access_token(subject=str(farm.id), expires_time=datetime.timedelta(seconds=15))

    refresh_token = Authorize.create_refresh_token(subject=str(farm.id), expires_time=datetime.timedelta(weeks=100))

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
    if form.token is not None:
        farm = get_farm_from_token(db, token=form.token)
    else:
        farm = get_farm_from_email(db, email=form.email)

    if farm is None:
        not_found_exception()

    if not verify_password(plain_password=form.password, hashed_password=farm.password) and form.token is None:
        unauthorized_exception()

    access_token = Authorize.create_access_token(subject=str(farm.id), expires_time=datetime.timedelta(days=7))
    # access_token = Authorize.create_access_token(subject=str(farm.id), expires_time=datetime.timedelta(seconds=15))

    refresh_token = Authorize.create_refresh_token(subject=str(farm.id), expires_time=datetime.timedelta(weeks=100))

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
        # new_access_token = Authorize.create_access_token(subject=current_user, expires_time=datetime.timedelta(seconds=15))

        new_access_token = Authorize.create_access_token(subject=current_user, expires_time=datetime.timedelta(days=7))

        Authorize.set_access_cookies(new_access_token)
        return await verify_return(data={"msg": "The token has been refresh", "access_token": str(new_access_token)})
    except fastapi_jwt_auth.exceptions.MissingTokenError:
        unauthorized_exception(message="UNAUTHORIZED")
        return await verify_return(data=None)
    except fastapi_jwt_auth.exceptions.RefreshTokenRequired:
        unauthorized_exception(message="REQUIRED REFRESH TOKEN")
        return await verify_return(data=None)
    except fastapi_jwt_auth.exceptions.FreshTokenRequired:
        unauthorized_exception(message="FRESH TOKEN REQUIRED")
        return await verify_return(data=None)
    except fastapi_jwt_auth.exceptions.AuthJWTException:
        unauthorized_exception(message="UNAUTHORIZED OR TOKEN IS EXPIRED")
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
async def get_buffs(params: GetBuffModel = Depends(), Authorize: AuthJWT = Depends(),
                    db: Session = Depends(get_db)):
    await check_authorize(Authorize)
    id = Authorize.get_jwt_subject()

    if id is None:
        bad_request_exception()

    database = db.query(BuffDatabase)
    database = database.filter(BuffDatabase.farm_id == uuid.UUID(id))

    if params.name is not None:
        buff = database.filter(BuffDatabase.name.ilike(params.name))
        return await verify_return(data=ResponseModel(data=buff.serialize))
    if params.tag is not None:
        buff = database.filter(BuffDatabase.tag.ilike(params.tag))
        return await verify_return(data=ResponseModel(data=buff.serialize))

    if params.gender is not None:
        gender = params.gender.name.upper()
        if gender == "MALE" or gender == "FEMALE":
            database = database.filter(BuffDatabase.gender.ilike(gender))
        else:
            bad_request_exception()
    if params.father_id is not None:
        database = database.filter(BuffDatabase.father == params.father_id)
    if params.mother_id is not None:
        database = database.filter(BuffDatabase.mother == params.mother_id)

    buffs = database.all()
    data_results = [i.serialize for i in buffs]

    return await verify_return(data=ResponseModel(data=data_results))


@router.get('/buffs/{id}', include_in_schema=True, tags=['Buff'])
async def detail_buff(id: str, Authorize: AuthJWT = Depends(),
                      db: Session = Depends(get_db)):
    await check_authorize(Authorize)
    farm_id = Authorize.get_jwt_subject()
    buff = await get_buff(db, id, farm_id)

    return await verify_return(data=get_buff_response(buff))


@router.get('/buffs/{id}/{type}', include_in_schema=True, tags=['Buff'])
async def buff_activities(id: str, type: BuffActivityType, delete: bool = None, Authorize: AuthJWT = Depends(),
                          db: Session = Depends(get_db)):
    await check_authorize(Authorize)
    farm_id = Authorize.get_jwt_subject()
    buff = await get_buff(db, id, farm_id)

    if type is not None:
        return await verify_return(data=filter_buff_activities(buff, type, delete))
    return await verify_return(data=get_buff_response(buff.name))


@router.patch('/buffs/{id}', include_in_schema=True, tags=['Buff'])
async def edit_buff(id: str, form: EditBuffForm = Depends(EditBuffForm.as_form), Authorize: AuthJWT = Depends(),
                    db: Session = Depends(get_db)):
    await check_authorize(Authorize)
    farm_id = Authorize.get_jwt_subject()

    buff = await get_buff(db, id, farm_id)

    updated = False

    if form.name is not None:
        buff.name = form.name
        updated = True
    if form.gender is not None:
        buff.gender = form.gender.name
        updated = True

    if form.birth_date is not None:
        buff.birth_date = form.birth_date
        updated = True

    if form.source is not None:
        buff.source = form.source
        updated = True

    if form.father_id is not None:
        buff.father_id = form.father_id
        updated = True

    if form.mother_id is not None:
        buff.mother_id = form.mother_id
        updated = True
    if form.tag is not None:
        buff.tag = form.tag
        updated = True

    if updated:
        buff.updated_at = current_datetime_with_timezone()
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
    buff = BuffDatabase(name=form.name, gender=form.gender.name, birth_date=birth_date, farm_id=id)
    if form.father_id is not None:
        buff.father_id = form.father_id
    if form.mother_id is not None:
        buff.mother_id = form.mother_id
    if form.father_name is not None:
        buff.father_name = form.father_name
    if form.mother_name is not None:
        buff.mother_name = form.mother_name
    if form.source is not None:
        buff.source = form.source
    if form.tag is not None:
        buff.tag = form.tag
    if form.image_url is not None:
        buff.image_url = form.image_url

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


@router.get('/activities', include_in_schema=True, tags=['Activities'], deprecated=False)
async def get_activities(
        delete: bool = None,
        Authorize: AuthJWT = Depends(),
        db: Session = Depends(get_db)):
    await check_authorize(Authorize)
    farm_id = Authorize.get_jwt_subject()
    farm = get_farm_from_id(db, farm_id)

    result = {}
    for buff in farm.buffs:
        for activity in buff.activity:
            if activity.name == 'BREEDING':
                append_activities(result, activity.name.upper(), activity.breeding_serialize,
                                  activity_delete=activity.delete, delete=delete)
            elif activity.name == "RETURN_ESTRUS":
                append_activities(result, activity.name.upper(), activity.return_estrus_serialize,
                                  activity_delete=activity.delete, delete=delete)
            elif activity.name == "VACCINE_INJECTION":
                append_activities(result, activity.name.upper(), activity.vaccine_injection_serialize,
                                  activity_delete=activity.delete, delete=delete)
            elif activity.name == "DEWORMING":
                append_activities(result, activity.name.upper(), activity.deworming_serialize,
                                  activity_delete=activity.delete, delete=delete)
            elif activity.name == "DISEASE_TREATMENT":
                append_activities(result, activity.name.upper(), activity.disease_treatment_serialize,
                                  activity_delete=activity.delete, delete=delete)
            else:
                append_activities(result, "OTHER", activity.sub_serialize, activity_delete=activity.delete,
                                  delete=delete)

    return await verify_return(ResponseModel(data=result))


@router.get('/activities/buff/{id}', include_in_schema=True, tags=['Activities'], deprecated=False)
async def get_buff_activities(
        id: uuid.UUID,
        Authorize: AuthJWT = Depends(),
        db: Session = Depends(get_db)):
    await check_authorize(Authorize)
    # farm_id = Authorize.get_jwt_subject()
    logs = db.query(BuffActivityLogDatabase).filter(BuffActivityLogDatabase.buff_id == id).all()
    buff = None
    results_logs = []
    result = {}

    if len(logs) > 0:
        buff = logs[0].buff
        for log in logs:
            if log.name == "BREEDING":
                results_log = log.breeding_serialize
            elif log.name == "RETURN_ESTRUS":
                results_log = log.return_estrus_serialize
            elif log.name == "VACCINE_INJECTION":
                results_log = log.vaccine_injection_serialize
            elif log.name == "DEWORMING":
                results_log = log.deworming_serialize
            elif log.name == "DISEASE_TREATMENT":
                results_log = log.disease_treatment_serialize
            else:
                results_log = log.sub_serialize
            results_logs.append(results_log)
        result['buff'] = buff.sub_serialize
        result['log'] = results_logs
    else:
        result['buff'] = None
        result['log'] = []

    return await verify_return(ResponseModel(data=result))


@router.get('/activities/log/{id}', include_in_schema=True, tags=['Activities'], deprecated=False)
async def get_buff_log_activities(
        id: str,
        Authorize: AuthJWT = Depends(),
        db: Session = Depends(get_db)):
    await check_authorize(Authorize)
    farm_id = Authorize.get_jwt_subject()
    log = db.query(BuffActivityLogDatabase).get(id)
    if log is None:
        not_found_exception()
    buff = log.buff
    if str(buff.farm_id) != farm_id:
        not_allowed_exception()
    result = {}
    if log.name == "BREEDING":
        result = log.breeding_serialize
    else:
        result = log.sub_serialize
    result['buff'] = buff.sub_serialize

    return await verify_return(ResponseModel(data=result))


@router.delete('/activities/log/{id}', include_in_schema=True, tags=['Activities'], deprecated=False)
async def delete_buff_log_activity(
        id: uuid.UUID,
        Authorize: AuthJWT = Depends(),
        db: Session = Depends(get_db)):
    log = db.query(BuffActivityLogDatabase).get(id)

    if log is None:
        not_found_exception()

    log.delete = True
    log.status = False
    db.add(log)
    db.commit()

    return await verify_return(ResponseModel(data="Delete successfully"))


@router.post('/breeding', include_in_schema=True, tags=['Breeding'])
async def add_breeding_buff(form: BuffBreedingModel = Depends(BuffBreedingModel.as_form),
                            Authorize: AuthJWT = Depends(),
                            db: Session = Depends(get_db)):
    await check_authorize(Authorize)
    farm_id = Authorize.get_jwt_subject()

    if form.buff_id == form.breeder_id:
        bad_request_exception()

    count_of_breeding = db.query(BuffActivityLogDatabase).filter(
        BuffActivityLogDatabase.buff_id == form.buff_id).filter(
        BuffActivityLogDatabase.name.contains("BREEDING")).filter(BuffActivityLogDatabase.delete.is_(False)).filter(
        BuffActivityLogDatabase.status.is_(True)).count()

    breeding_datetime = form.date if form.date is not None else current_datetime()

    buff = await get_buff(db=db, id=form.buff_id, farm_id=farm_id)

    if buff is None:
        not_found_exception()
    if buff.gender == "MALE":
        bad_request_exception("MALE CAN'T NOT BREEDING")

    if count_of_breeding > 0:
        not_acceptable_exception(f"'{buff.name}' in the process of breeding, Cannot be added")

    log = BuffActivityLogDatabase(buff_id=buff.id, name="BREEDING", value=form.breeder_name)
    log.bool_value = form.artificial_insemination if form.artificial_insemination is not None else False
    breeder_buff = None
    print(form.breeder_id)

    if form.breeder_id is not None:
        breeder_buff = await get_buff(db=db, id=form.breeder_id, farm_id=farm_id)
    elif form.breeder_name is not None:
        breeder_buff = await get_buff_by_name(db=db, name=form.breeder_name, farm_id=farm_id)

    if breeder_buff is None:
        not_found_exception()
    if breeder_buff.gender == "FEMALE":
        bad_request_exception("FEMALE CAN'T NOT BREEDER")

    log.refer_id = breeder_buff.id
    log.datetime_value = breeding_datetime

    db.add(log)

    if form.notify is not None:
        if form.notify:
            create_notify_to_database(db, activity_id=log.id, farm_id=farm_id, date=form.date, value="RETURN_ESTRUS",
                                      category="BREEDING", days=21)

    db.commit()

    result = log.breeding_serialize
    result['buff'] = buff.sub_serialize
    if log.refer_id is not None:
        result['breeder'] = breeder_buff.sub_serialize

    return await verify_return(ResponseModel(data=result))


@router.patch('/breeding/{id}', include_in_schema=True, tags=['Breeding'], deprecated=False)
async def edit_breeding_buff(
        id: str,
        form: BuffEditBreedingModel = Depends(BuffEditBreedingModel.as_form),
        Authorize: AuthJWT = Depends(),
        db: Session = Depends(get_db)):
    await check_authorize(Authorize)
    farm_id = Authorize.get_jwt_subject()
    log = db.query(BuffActivityLogDatabase).get(id)

    if log is None:
        not_found_exception()
    if log.delete or (log.delete and not log.status):
        bad_request_exception("This activity was deleted")

    updated = False
    notify = get_notify_from_database(db, log.id)
    date_changed = False

    if form.breeder_id is not None:
        if id == form.breeder_id:
            bad_request_exception()
        breeder_buff = await get_buff(db=db, id=form.breeder_id, farm_id=farm_id)
        if breeder_buff is None:
            not_found_exception()
        if breeder_buff.gender == "FEMALE":
            bad_request_exception("FEMALE CAN'T NOT BREEDER")
        log.refer_id = breeder_buff.id
        updated = True

    if form.artificial_insemination is not None:
        log.bool_value = form.artificial_insemination
        updated = True

    if form.date is not None:
        log.datetime_value = form.date
        date_changed = True
        updated = True

    if form.notify is not None:
        if notify is not None and not form.notify:
            delete_notify_on_database(db, activity_id=log.id)
            updated = True

        elif notify is not None and form.notify:
            update_notify_on_database(db, activity_id=log.id, date=log.datetime_value, days=21)
            updated = True

        elif notify is None and form.notify:
            create_notify_to_database(db, activity_id=log.id, farm_id=farm_id, date=form.date, value="RETURN_ESTRUS",
                                      category="BREEDING", days=21)
            updated = True

    else:
        if date_changed and notify is not None:
            update_notify_on_database(db, activity_id=log.id, date=log.datetime_value, days=21)
            updated = True

    if updated:
        log.updated_at = current_datetime_with_timezone()
        db.add(log)
        db.commit()

    result = log.breeding_serialize
    buff = await get_buff(db=db, id=log.buff_id, farm_id=farm_id)
    result['buff'] = buff.sub_serialize
    if log.refer_id is not None:
        breeder = await get_buff(db=db, id=log.refer_id, farm_id=farm_id)
        result['breeder'] = breeder.sub_serialize

    return await verify_return(ResponseModel(data=result))


@router.post('/return-estrus', include_in_schema=True, tags=['Return Estrus'])
async def add_return_estrus_buff(form: BuffReturnEstrusModel = Depends(BuffReturnEstrusModel.as_form),
                                 Authorize: AuthJWT = Depends(),
                                 db: Session = Depends(get_db)):
    await check_authorize(Authorize)
    farm_id = Authorize.get_jwt_subject()

    breeding_database = db.query(BuffActivityLogDatabase).filter(
        BuffActivityLogDatabase.buff_id == form.buff_id).filter(
        BuffActivityLogDatabase.name.contains("BREEDING")).filter(BuffActivityLogDatabase.delete.is_(False)).filter(
        BuffActivityLogDatabase.status.is_(True))

    buff = await get_buff(db=db, id=form.buff_id, farm_id=farm_id)
    if buff is None:
        not_found_exception()

    if breeding_database.count() == 0:
        not_acceptable_exception(f"{buff.name} not in the process of breeding")

    breeding = breeding_database.first()
    return_estrus = BuffActivityLogDatabase(buff_id=buff.id, name="RETURN_ESTRUS", value=form.message_result)
    return_estrus.bool_value = form.estrus_result

    breeding.delete = True
    breeding.status = False
    db.add(breeding)
    delete_notify_on_database(db, activity_id=breeding.id)

    birth_datetime = breeding.datetime_value + datetime.timedelta(days=310)
    return_estrus.datetime_value = birth_datetime
    return_estrus.status = not form.estrus_result
    return_estrus.refer_id = breeding.id
    db.add(return_estrus)

    if not form.estrus_result:
        if form.notify is not None:
            if form.notify:
                create_notify_to_database(db, activity_id=return_estrus.id, farm_id=farm_id,
                                          date=breeding.datetime_value, value="BIRTH",
                                          category="RETURN_ESTRUS", days=310)
    db.commit()

    result = return_estrus.return_estrus_serialize
    return await verify_return(ResponseModel(data=result))


@router.patch('/return-estrus/{id}', include_in_schema=True, tags=['Return Estrus'], deprecated=False)
async def edit_return_estrus_buff(
        id: str,
        form: BuffEditReturnEstrusModel = Depends(BuffEditReturnEstrusModel.as_form),
        Authorize: AuthJWT = Depends(),
        db: Session = Depends(get_db)):
    await check_authorize(Authorize)
    farm_id = Authorize.get_jwt_subject()

    log = db.query(BuffActivityLogDatabase).get(id)

    if log is None:
        not_found_exception()
    if log.delete or (log.delete and not log.status):
        bad_request_exception("This activity was deleted")

    updated = False
    notify = get_notify_from_database(db, log.id)

    if form.message_result is not None:
        log.value = form.message_result
        updated = True

    if form.estrus_result is not None:
        log.status = not form.estrus_result

    if form.notify is not None:
        if notify is not None and not form.notify:
            delete_notify_on_database(db, activity_id=log.id)
            updated = True
        elif notify is None and form.notify:
            if not form.estrus_result:
                create_notify_to_database(db, activity_id=log.id, farm_id=farm_id, date=log.datetime_value,
                                          value="BIRTH",
                                          category="RETURN_ESTRUS")
                updated = True

    if updated:
        log.updated_at = current_datetime_with_timezone()
        db.add(log)
        db.commit()

    result = log.return_estrus_serialize
    return await verify_return(ResponseModel(data=result))


@router.post('/vaccine_injection', include_in_schema=True, tags=['Vaccine Injection'])
async def add_vaccine_injection_buff(form: BuffVaccineInjectionModel = Depends(BuffVaccineInjectionModel.as_form),
                                     Authorize: AuthJWT = Depends(),
                                     db: Session = Depends(get_db)):
    await check_authorize(Authorize)
    farm_id = Authorize.get_jwt_subject()

    buff = await get_buff(db=db, id=form.buff_id, farm_id=farm_id)
    if buff is None:
        not_found_exception()

    if form.vaccine_name.name == "OTHER" and form.other_vaccine_name is None:
        bad_request_exception()

    vaccine = vaccines[next((i for i, e in enumerate(vaccines) if
                             e.key == form.vaccine_name.name))] if form.vaccine_name.name != "OTHER" else BuffVaccine(
        name=form.other_vaccine_name, key="OTHER",
        days=(form.vaccine_duration if form.vaccine_duration is not None else -1))

    injection = BuffActivityLogDatabase(buff_id=form.buff_id, name="VACCINE_INJECTION", value=vaccine.name)
    injection.secondary_value = f"{vaccine.key}/{vaccine.days}"

    if vaccine.days >= 0:
        target_datetime = form.date if form.date is not None else current_datetime()
        injection_datetime = target_datetime + datetime.timedelta(days=vaccine.days)
        injection.datetime_value = injection_datetime
    else:
        injection.datetime_value = None

    db.add(injection)

    if form.notify is not None:
        if form.notify:
            create_notify_to_database(db, activity_id=injection.id, farm_id=farm_id, date=injection.datetime_value,
                                      value="INJECTION",
                                      category="VACCINE_INJECTION")

    db.commit()

    result = injection.vaccine_injection_serialize
    return await verify_return(ResponseModel(data=result))


@router.patch('/vaccine_injection/{id}', include_in_schema=True, tags=['Vaccine Injection'], deprecated=False)
async def edit_vaccine_injection_buff(
        id: str,
        form: BuffEditVaccineInjectionModel = Depends(BuffEditVaccineInjectionModel.as_form),
        Authorize: AuthJWT = Depends(),
        db: Session = Depends(get_db)):
    await check_authorize(Authorize)
    farm_id = Authorize.get_jwt_subject()
    injection = db.query(BuffActivityLogDatabase).get(id)

    if injection is None:
        not_found_exception()
    if injection.delete or (injection.delete and not injection.status):
        bad_request_exception("This activity was deleted")

    old_value_set = injection.secondary_value.split("/")
    old_days = int(old_value_set[1])
    old_injection_datetime = injection.datetime_value - datetime.timedelta(days=old_days)
    notify = get_notify_from_database(db, injection.id)

    date_changed = False
    updated = False

    if form.vaccine_name is not None:
        if form.vaccine_name.name == "OTHER" and form.other_vaccine_name is None:
            bad_request_exception()

        vaccine = vaccines[next((i for i, e in enumerate(vaccines) if
                                 e.key == form.vaccine_name.name))] if form.vaccine_name.name != "OTHER" else BuffVaccine(
            name=form.other_vaccine_name, key="OTHER",
            days=(form.vaccine_duration if form.vaccine_duration is not None else -1))

        injection.secondary_value = f"{vaccine.key}/{vaccine.days}"

        if vaccine.days > 0:
            target_datetime = form.date if form.date is not None else old_injection_datetime
            injection_datetime = target_datetime + datetime.timedelta(days=vaccine.days)
            injection.datetime_value = injection_datetime
        else:
            injection.datetime_value = None
        updated = True
        date_changed = True
    if form.date is not None and not date_changed:
        injection_datetime = form.date + datetime.timedelta(days=old_days)
        injection.datetime_value = injection_datetime
        updated = True

    if form.notify is not None:
        if notify is not None and not form.notify:
            delete_notify_on_database(db, activity_id=injection.id)
            updated = True

        elif notify is not None and form.notify:
            update_notify_on_database(db, activity_id=injection.id, date=injection.datetime_value)
            updated = True

        elif notify is None and form.notify:
            create_notify_to_database(db, activity_id=injection.id, farm_id=farm_id, date=injection.datetime_value,
                                      value="INJECTION",
                                      category="VACCINE_INJECTION")
            updated = True

    else:
        if date_changed and notify is not None:
            update_notify_on_database(db, activity_id=injection.id, date=injection.datetime_value)
            updated = True

    if updated:
        injection.updated_at = current_datetime_with_timezone()
        db.add(injection)
        db.commit()

    result = injection.vaccine_injection_serialize
    return await verify_return(ResponseModel(data=result))


@router.post('/deworming', include_in_schema=True, tags=['Deworming'])
async def add_deworming_buff(form: BuffDewormingModel = Depends(BuffDewormingModel.as_form),
                             Authorize: AuthJWT = Depends(),
                             db: Session = Depends(get_db)):
    await check_authorize(Authorize)
    farm_id = Authorize.get_jwt_subject()

    buff = await get_buff(db=db, id=form.buff_id, farm_id=farm_id)
    if buff is None:
        not_found_exception()

    log = BuffActivityLogDatabase(buff_id=buff.id, name="DEWORMING", value=form.anthelmintic_drug_name)
    target_datetime = form.date if form.date is not None else current_datetime()

    if form.next_deworming_duration is not None:
        log.secondary_value = form.next_deworming_duration
        next_datetime = target_datetime + datetime.timedelta(days=int(form.next_deworming_duration))
        log.datetime_value = next_datetime
        if form.notify is not None:
            if form.notify:
                create_notify_to_database(db, activity_id=log.id, farm_id=farm_id, date=log.datetime_value,
                                          value="NEXT_DEWORMING",
                                          category="DEWORMING")
    else:
        log.datetime_value = target_datetime
        log.status = False

    db.add(log)
    db.commit()
    result = log.deworming_serialize
    return await verify_return(ResponseModel(data=result))


@router.patch('/deworming/{id}', include_in_schema=True, tags=['Deworming'], deprecated=False)
async def edit_deworming_buff(
        id: str,
        form: BuffEditDewormingModel = Depends(BuffEditDewormingModel.as_form),
        Authorize: AuthJWT = Depends(),
        db: Session = Depends(get_db)):
    await check_authorize(Authorize)
    farm_id = Authorize.get_jwt_subject()
    log = db.query(BuffActivityLogDatabase).get(id)

    if log is None:
        not_found_exception()
    if log.delete or (log.delete and not log.status):
        bad_request_exception("This activity was deleted")

    notify = get_notify_from_database(db, log.id)

    date_changed = False
    updated = False

    if form.anthelmintic_drug_name is not None:
        log.value = form.anthelmintic_drug_name
        if form.next_deworming_duration is not None:
            target_datetime = form.date if form.date is not None else (log.datetime_value - datetime.timedelta(
                days=int(log.secondary_value)) if log.secondary_value is not None else log.datetime_value)
            if form.next_deworming_duration > 0:
                log.secondary_value = form.next_deworming_duration
                next_deworming_datetime = target_datetime + datetime.timedelta(days=form.next_deworming_duration)
                log.datetime_value = next_deworming_datetime
                log.status = True
            else:
                log.secondary_value = None
                log.datetime_value = target_datetime
                log.status = False
            date_changed = True
        else:
            bad_request_exception("If you change anthelmintic drug name, You should add duration")

    if form.notify is not None:
        if log.status:
            if notify is not None and not form.notify:
                delete_notify_on_database(db, activity_id=log.id)
                updated = True

            elif notify is not None and form.notify:
                update_notify_on_database(db, activity_id=log.id, date=log.datetime_value)

                updated = True

            elif notify is None and form.notify:
                create_notify_to_database(db, activity_id=log.id, farm_id=farm_id, date=log.datetime_value,
                                          value="NEXT_DEWORMING",
                                          category="DEWORMING")
                updated = True
        else:
            if notify is not None:
                delete_notify_on_database(db, activity_id=log.id)
                updated = True
    else:
        if date_changed and notify is not None and not log.status:
            update_notify_on_database(db, activity_id=log.id, date=log.datetime_value)
            updated = True

    if updated:
        log.updated_at = current_datetime_with_timezone()
        db.add(log)
        db.commit()

    result = log.deworming_serialize
    return await verify_return(ResponseModel(data=result))


@router.post('/disease-treatment', include_in_schema=True, tags=['Disease Treatment'])
async def add_disease_treatment_buff(form: BuffDiseaseTreatmentModel = Depends(BuffDiseaseTreatmentModel.as_form),
                                     Authorize: AuthJWT = Depends(),
                                     db: Session = Depends(get_db)):
    await check_authorize(Authorize)
    farm_id = Authorize.get_jwt_subject()

    buff = await get_buff(db=db, id=form.buff_id, farm_id=farm_id)
    if buff is None:
        not_found_exception()

    log = BuffActivityLogDatabase(buff_id=buff.id, name="DISEASE_TREATMENT", value=form.disease_name)
    target_datetime = form.date if form.date is not None else current_datetime()

    data = {"symptom": form.symptom, "drugs": form.drugs}
    data_value = json.dumps(data)
    log.secondary_value = data_value
    log.bool_value = form.healed_status
    log.datetime_value = target_datetime

    log.status = False

    db.add(log)
    db.commit()

    result = log.disease_treatment_serialize
    return await verify_return(ResponseModel(data=result))


@router.patch('/disease-treatment/{id}', include_in_schema=True, tags=['Disease Treatment'], deprecated=False)
async def edit_disease_treatment_buff(
        id: str,
        form: BuffEditDiseaseTreatmentModel = Depends(BuffEditDiseaseTreatmentModel.as_form),
        Authorize: AuthJWT = Depends(),
        db: Session = Depends(get_db)):
    await check_authorize(Authorize)
    farm_id = Authorize.get_jwt_subject()
    log = db.query(BuffActivityLogDatabase).get(id)

    if log is None:
        not_found_exception()
    if log.delete or (log.delete and not log.status):
        bad_request_exception("This activity was deleted")

    obj = json.loads(str(log.secondary_value))
    symptom = obj["symptom"]
    drugs = obj["drugs"]

    log.value = form.disease_name if form.disease_name is not None else log.value
    symptom = form.symptom if form.symptom is not None else symptom
    drugs = form.drugs if form.drugs is not None else drugs
    log.datetime_value = form.date if form.date is not None else log.datetime_value
    log.bool_value = form.healed_status if form.healed_status is not None else log.bool_value

    data = {"symptom": symptom, "drugs": drugs}
    data_value = json.dumps(data)
    log.secondary_value = data_value

    log.updated_at = current_datetime_with_timezone()
    log.status = False

    db.add(log)
    db.commit()
    result = log.disease_treatment_serialize
    return await verify_return(ResponseModel(data=result))


@router.get('/notifications', include_in_schema=True, tags=['Notification'], deprecated=False)
async def get_notifications(
        Authorize: AuthJWT = Depends(),
        db: Session = Depends(get_db)):
    await check_authorize(Authorize)
    farm_id = Authorize.get_jwt_subject()
    notifications = db.query(BuffNotifyDatabase).filter(BuffDatabase.farm_id == uuid.UUID(farm_id)).all()
    return await verify_return(ResponseModel(data=notifications))


def initial_notify(activity_id, farm_id, datetime, value, category):
    return BuffNotifyDatabase(activity_id=activity_id, datetime=datetime, value=value,
                              category=category, farm_id=farm_id)


def get_notify_from_database(db, activity_id):
    return db.query(BuffNotifyDatabase).filter(BuffNotifyDatabase.activity_id == activity_id).first()


def create_notify_to_database(db, date, activity_id, farm_id, value, category, days=0, schedule=None):
    breeding_datetime = date if date is not None else current_datetime()

    notify_date = breeding_datetime + datetime.timedelta(days=days)

    notify = initial_notify(activity_id=activity_id, farm_id=farm_id, datetime=notify_date, value=value,
                            category=category)
    if schedule is not None:
        notify.schedule = str(schedule)
    db.add(notify)
    return notify


def update_notify_on_database(db, activity_id, date, days=0):
    notify = get_notify_from_database(db, activity_id)
    breeding_datetime = date if date is not None else current_datetime()
    notify_date = breeding_datetime + datetime.timedelta(days=days)
    if notify is None:
        not_found_exception()
    notify.datetime = notify_date
    db.add(notify)
    return notify


def delete_notify_on_database(db, activity_id):
    notify = get_notify_from_database(db, activity_id)
    if notify is None:
        not_found_exception()
    db.delete(notify)
    return True


def get_buff_response(buff):
    result = buff.serialize
    result['farm'] = buff.farm.serialize
    activities = []
    for i in buff.activity:
        rechecking_activities_path_available(result)
        if i.name == 'BREEDING':
            serialize = i.breeding_serialize
            append_to_activities(result, i.name.upper(), i.breeding_serialize)
        elif i.name == 'RETURN_ESTRUS':
            serialize = i.return_estrus_serialize
            append_to_activities(result, i.name.upper(), i.return_estrus_serialize)
        elif i.name == 'VACCINE_INJECTION':
            serialize = i.vaccine_injection_serialize
            append_to_activities(result, i.name.upper(), i.vaccine_injection_serialize)
        elif i.name == 'DEWORMING':
            serialize = i.deworming_serialize
            append_to_activities(result, i.name.upper(), i.deworming_serialize)
        elif i.name == 'DISEASE_TREATMENT':
            serialize = i.disease_treatment_serialize
            append_to_activities(result, i.name.upper(), i.disease_treatment_serialize)
        else:
            serialize = i.sub_serialize
            append_to_activities(result, "OTHER", i.sub_serialize)
        activities.append(serialize)
    result['history'] = activities
    return ResponseModel(data=result)


def filter_buff_activities(buff, activity, delete):
    if type(activity) is not BuffActivityType:
        bad_request_exception()
    result = []
    for i in buff.activity:

        if activity == BuffActivityType.BREEDING:
            if delete is not None:
                if i.delete == delete:
                    result.append(i.breeding_serialize)
            else:
                result.append(i.breeding_serialize)

        if activity == BuffActivityType.RETURN_ESTRUS:
            if delete is not None:
                if i.delete == delete:
                    result.append(i.return_estrus_serialize)
            else:
                result.append(i.return_estrus_serialize)

    return result


def rechecking_activities_path_available(result):
    if "activities" not in result:
        result['activities'] = {}


def append_to_activities(result, key, value):
    if key not in result['activities']:
        result['activities'][key] = []
    result['activities'][key].append(value)


def append_activities(result, key, value, activity_delete, delete):
    if delete is not None:
        if activity_delete == delete:
            if key not in result:
                result[key] = []
            result[key].append(value)
    else:
        if key not in result:
            result[key] = []
        result[key].append(value)


async def get_buff(db, id, farm_id):
    buff = db.query(BuffDatabase).get(id)
    if buff is None:
        not_found_exception()
    if buff.farm_id != uuid.UUID(farm_id):
        not_found_exception()
    return buff


async def get_buff_by_name(db, name, farm_id):
    buff = db.query(BuffDatabase).filter(BuffDatabase.farm_id == uuid.UUID(farm_id)).filter(
        BuffDatabase.name.ilike(name)).first()

    if buff is None:
        not_found_exception()
    if buff.farm_id != uuid.UUID(farm_id):
        not_found_exception()
    return buff


async def check_authorize(Authorize: AuthJWT):
    try:
        Authorize.jwt_required()
    except fastapi_jwt_auth.exceptions.MissingTokenError:
        unauthorized_exception(message="UNAUTHORIZED")
        return await verify_return(data=None)

    except fastapi_jwt_auth.exceptions.AuthJWTException:
        unauthorized_exception(message="UNAUTHORIZED OR TOKEN IS EXPIRED")
        return await verify_return(data=None)
    except Exception as e:
        print(e)
        bad_request_exception(message="Found an error: " + str(e))
        return await verify_return(data=None)


def isDuplicate(db, phone_number: str) -> bool:
    database = db.query(BuffFarmDatabase)

    if phone_number is not None:
        database = database.filter(BuffFarmDatabase.phone_number.contains(phone_number))
        if database.count() == 0:
            return False

    return True


def get_farm_from_email(db, email: str):
    database = db.query(BuffFarmDatabase)

    if email is not None:
        database = database.filter(BuffFarmDatabase.email.contains(email))
        farm = database.first()
        return farm

    return None


def get_farm_from_token(db, token: str):
    database = db.query(BuffFarmDatabase)

    if token is not None:
        database = database.filter(BuffFarmDatabase.token.contains(token))
        farm = database.first()
        return farm

    return None


def get_farm_from_id(db, id: str):
    database = db.query(BuffFarmDatabase)

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


def not_acceptable_exception(message=None):
    raise HTTPException(
        status_code=code.HTTP_406_NOT_ACCEPTABLE,
        detail=message if message is not None else "NOT ACCEPTABLE")


def not_found_exception(message=None):
    raise HTTPException(
        status_code=code.HTTP_404_NOT_FOUND,
        detail=message if message is not None else "NOT FOUND")


def unauthorized_exception(message=None):
    raise HTTPException(
        status_code=code.HTTP_401_UNAUTHORIZED,
        detail=message if message is not None else "UNAUTHORIZED")


def not_allowed_exception(message=None):
    raise HTTPException(
        status_code=code.HTTP_405_METHOD_NOT_ALLOWED,
        detail=message if message is not None else "NOT ALLOWED")


def not_modified_exception(message=None):
    raise HTTPException(
        status_code=code.HTTP_304_NOT_MODIFIED,
        detail=message if message is not None else "NOT_MODIFIED")


def duplicate_on_database_exception(message=None):
    raise HTTPException(
        status_code=code.HTTP_302_FOUND,
        detail=message if message is not None else "PHONE NUMBER ALREADY EXISTS")
