import datetime
from uuid import UUID

from oauthlib.oauth2.rfc6749.grant_types import refresh_token
from pydantic import BaseModel
from typing import List

from environment import OPENSSL_SECRET_KEY
from src.tools.as_form import as_form


class BuffSettings(BaseModel):
    authjwt_secret_key: str = OPENSSL_SECRET_KEY
    authjwt_token_location: set = {"cookies"}
    authjwt_cookie_csrf_protect: bool = False


@as_form
class RegisterFarmForm(BaseModel):
    farm_name: str
    first_name: str
    last_name: str
    address: str
    email: str
    password: str
    auth_token: str = None


@as_form
class BuffLoginForm(BaseModel):
    email: str
    password: str


@as_form
class BuffChangePasswordForm(BaseModel):
    old_password: str
    new_password: str


@as_form
class BuffChangeFarmInfoForm(BaseModel):
    farm_name: str = None
    first_name: str = None
    last_name: str = None
    address: str = None


@as_form
class AddBuffForm(BaseModel):
    name: str
    gender: str
    birth_date: datetime.date = None
    father_id: UUID = None
    mother_id: UUID = None
    source: str = None


@as_form
class EditBuffForm(BaseModel):
    name: str = None
    gender: str = None
    birth_date: datetime.date = None
    father_id: UUID = None
    mother_id: UUID = None
    source: str = None


@as_form
class BuffBreedingModel(BaseModel):
    buff_id: UUID
    artificial_insemination: bool
    breeder_id: UUID
    date: datetime.date = None
    notify: bool



@as_form
class BuffReturnEstrusModel(BaseModel):
    buff_id: UUID
    estrus_result: bool
    message_result: str = None
    date: datetime.date = None
    notify: bool


@as_form
class BuffVaccineInjectionModel(BaseModel):
    buff_id: UUID
    vaccine_name: str
    other_vaccine_name: str = None
    date: datetime.date = None
    notify: bool
    notify_choice: str


@as_form
class BuffDewormingModel(BaseModel):
    buff_id: UUID
    anthelmintic_drug_name: str
    date: datetime.date = None
    next_deworming_duration: int = None
    notify: bool


@as_form
class BuffDiseaseTreatmentModel(BaseModel):
    buff_id: UUID
    disease_name: str
    symptom: List[str]
    drugs: List[str]
    healed_status: bool
    date: datetime.date = None


class BuffTokenModel:
    access_token: str
    refresh_token: str

    def __init__(self, access_token, refresh_token):
        self.access_token = access_token
        self.refresh_token = refresh_token


class BuffAuthenticatedResponseModel:
    token: BuffTokenModel
    farm_name: str

    def __init__(self, access_token, refresh_token, farm_name):
        self.token = BuffTokenModel(access_token=access_token, refresh_token=refresh_token)
        self.farm_name = farm_name
