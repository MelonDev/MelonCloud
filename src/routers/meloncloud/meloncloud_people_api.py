from fastapi import APIRouter

from src.database.meloncloud.meloncloud_people_database import MelonCloudPeopleDatabase
from src.environment.database_config import get_db
from src.models.meloncloud_twitter_model import RequestPeopleDatabaseModel
from fastapi import APIRouter, Depends, HTTPException, status as code, Response
from sqlalchemy import desc, asc, func, or_
from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query as DBQuery
from src.routers.meloncloud.meloncloud_error_response import bad_request_exception
from src.routers.meloncloud.meloncloud_twitter_extension_function import get_profile
import datetime as dt

from src.tools.verify_hub import response

router = APIRouter()


@router.post("/create")
async def add_people(params: RequestPeopleDatabaseModel = Depends(RequestPeopleDatabaseModel.as_form),
                     db: Session = Depends(get_db)):
    account = None
    partner = None
    if params.twitter_account is not None:
        profile = get_profile(params.twitter_account)
        if profile is None:
            bad_request_exception()
        account = profile['id_str']
    if params.partner_account is not None:
        profile = get_profile(params.partner_account)
        if profile is not None:
            partner = profile['id_str']
    database = db.query(MelonCloudPeopleDatabase).filter(MelonCloudPeopleDatabase.twitter_id.contains(account))
    if database.count() > 0:
        profile = database.first()
        if profile.blood is None and params.blood is not None:
            profile.blood = params.blood
        if profile.weight is None and params.weight is not None:
            profile.weight = params.weight
        if profile.height is None and params.height is not None:
            profile.height = params.height
        if profile.nationality is None and params.nationality is not None:
            profile.nationality = params.nationality
        if profile.year_of_birth is None:
            if params.age is not None and params.year_of_birth is None:
                now = dt.datetime.now()
                year = int(now.year) - params.age
            else:
                year = params.year_of_birth
            if year is not None:
                profile.year_of_birth = params.year
        db.add(profile)
        db.commit()
        return response(profile.serialize)
    else:

        if params.age is not None and params.year_of_birth is None:
            now = dt.datetime.now()
            year = int(now.year) - params.age
        else:
            year = params.year_of_birth

        people = MelonCloudPeopleDatabase()
        people.append_details(name=params.name, twitter_id=account, partner=partner, image_url=params.image_url,
                              nationality=params.nationality, gender=params.gender, weight=params.weight,
                              height=params.height, year_of_birth=year)

        db.add(people)
        db.commit()
        return response(people.serialize)
