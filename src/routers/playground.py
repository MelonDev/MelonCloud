import json
import random
from enum import Enum
from string import digits
from random import choice

import firebase_admin
from firebase_admin import credentials, storage

from fastapi import APIRouter, Depends, Response, UploadFile, File, Form, Request
from pyxtension.Json import Json
from sqlalchemy import func

from sqlalchemy.orm import Session

from src.database.buff_management.buff_database import BuffDatabase
from src.database.buff_management.farm_database import FarmDatabase
from src.database.meloncloud.meloncloud_twitter_database import MelonCloudTwitterDatabase
from src.database.melondev_twitter_database import MelonDevTwitterDatabase
from src.engines.twitter_engines import test_client_mode, get_status, has_deleted, get_lookup_statuses, \
    get_dict_lookup_statuses, get_meloncloud_tweet_model, TweetMediaType
from src.environment.database import get_db
from src.environment.firebase_enviroment import create_credentials_file, firebase_storage_url
from src.models.response_model import ResponseModel
from src.models.twitter_model import TwitterValidatorModel

import io
import csv

from src.tools.db_exporter import export, last_day_of_month, export_month_on_year
from src.tools.generators.enum_generator import make_enum
from src.tools.json_tool import pretty_json, to_json_object
from src.tools.verify_hub import verify_return, response

router = APIRouter()


class TestModel(TwitterValidatorModel):
    content: dict


class NameEnumModel(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


@router.get("/tests")
async def test():
    a = test_client_mode()
    print(a)

    return "HEllo"


@router.get("/database", include_in_schema=False)
async def database(db: Session = Depends(get_db)):
    a = db.query(MelonDevTwitterDatabase).limit(10).all()
    b = [item.serialize for item in a]
    print("DATABASE")
    return b


@router.get("/poc_password_reset_code", include_in_schema=True)
async def poc_password_reset_code(request: Request):
    code = ''.join(choice(digits) for _ in range(6))
    return await verify_return(ResponseModel(data=code))


@router.get("/csv", include_in_schema=True)
async def download_csv(request: Request):
    output = io.StringIO()
    writer = csv.writer(output)

    header = [
        "Header Name 1",
        "Header Name 2",
        "Header Name 3"
    ]

    writer.writerow(header)
    writer.writerow(["data one", "data two", "data three"])
    writer.writerow(["data one", "data two", "data three"])
    writer.writerow(["data one", "data two", "data three"])

    output.seek(0)
    response = Response(content=output.read(), media_type="text/csv")
    response.headers[
        "Content-Disposition"
    ] = f"attachment; filename=filename.csv"
    return response


@router.post("/firebase", include_in_schema=True)
async def firebase(file: UploadFile = File(...)):
    data = create_credentials_file()
    if not firebase_admin._apps:
        cred = credentials.Certificate(data)
        firebase_admin.initialize_app(cred, {'storageBucket': firebase_storage_url()})
    bucket = storage.bucket()
    blob = bucket.blob("test/" + file.filename)
    print(file.content_type)

    blob.upload_from_file(file.file, content_type=file.content_type)

    # Opt : if you want to make public access from the URL
    blob.make_public()

    print("your file url", blob.public_url)

    return {"your file url": blob.public_url}


@router.get("/csv_test", include_in_schema=True)
async def download_csv_test(request: Request, db: Session = Depends(get_db)):
    return export_month_on_year(db=db, session=MelonDevTwitterDatabase)
    # return export_month_in_year(db=db, session=MelonDevTwitterDatabase)

    # return export(db=db, session=MelonCloudBookDatabase)


@router.get("/models/{name_model}/{num}")
async def get_model(name_model: NameEnumModel, num: make_enum("Table", [("HELLO", "hello"), ("HI", "hi")]),
                    name: make_enum("Name", ["John", "Edward"]) = None):
    return f'{name_model} {num.value} {name.value}'


@router.get("/test-buff", include_in_schema=True)
async def test_buff(request: Request, db: Session = Depends(get_db)):
    farms = db.query(FarmDatabase).filter(FarmDatabase.buffs.any(BuffDatabase.gender == "FEMALE")).all()
    result = [farm.test for farm in farms]
    return await verify_return(ResponseModel(data=result))


@router.get("/random-tweet", include_in_schema=True)
async def random_tweet(request: Request, db: Session = Depends(get_db)):
    tweets = db.query(MelonDevTwitterDatabase).order_by(func.random()).limit(100).all()
    # result = [tweet.serialize for tweet in tweets]
    # deleted_tweet_id = "1389449192918044672"
    # tweet = has_deleted(deleted_tweet_id)

    # ids = ["1496088918131093508","1496090053902282754","1389449192918044672","1380893596593754115","1495323508896768000"]
    ids = [i.id for i in tweets]
    data = get_dict_lookup_statuses(ids)
    for k, v in data.items():
        print(k)
        print(v)
    # a = [d for d in data if tuple(d.items()) not in ids]
    a = [target for target in ids if target not in data]
    print(a)
    print("\n")

    b = [i for i in tweets if i.id not in data]
    for i in b:
        print(i.serialize)

    # return await verify_return(ResponseModel(data=result))
    return await verify_return(ResponseModel(data="result"))


@router.get("/poc-twitter", include_in_schema=True)
async def poc_twitter(request: Request, db: Session = Depends(get_db)):
    id = "1497000640236589070"
    ae = get_status(id)
    print(pretty_json(ae))
    # json_object = to_json_object(tweet)
    # print(json_object.created_at)
    # print(type(json_object.created_at))
    # print(json_object)
    # print(pretty_json(tweet))

    return response("HELLO")


@router.get("/automatic-check-tweet-has-deleted", include_in_schema=True)
async def automatic_check_tweet_has_deleted(request: Request, db: Session = Depends(get_db)):
    tweets = db.query(MelonCloudTwitterDatabase).order_by(func.random()).limit(100).all()
    data = get_dict_lookup_statuses([i.id for i in tweets])

    for tweet in tweets:
        deleted = tweet.id not in data
        if tweet.deleted != deleted:
            tweet.deleted = deleted

    return await verify_return(ResponseModel(data="result"))
