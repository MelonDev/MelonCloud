from enum import Enum
from string import digits
from random import choice

import firebase_admin
from firebase_admin import credentials, storage

from fastapi import APIRouter, Depends, Response, UploadFile, File, Form, Request

from sqlalchemy.orm import Session

from src.database.melondev_twitter_database import MelonDevTwitterDatabase
from src.engines.twitter_engines import test_client_mode
from src.environment.database import get_db
from src.environment.firebase_enviroment import create_credentials_file, firebase_storage_url
from src.models.response_model import ResponseModel
from src.models.twitter_model import TwitterValidatorModel

import io
import csv

from src.tools.db_exporter import export, last_day_of_month, export_month_on_year
from src.tools.generators.enum_generator import make_enum
from src.tools.verify_hub import verify_return

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
