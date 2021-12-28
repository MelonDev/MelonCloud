import pandas
from fastapi import APIRouter, Depends, Response

from sqlalchemy.orm import Session

from src.database.melondev_twitter_database import MelonDevTwitterDatabase
from src.engines.twitter_engines import test_client_mode
from src.environment.database import get_db
from src.models.twitter_model import TwitterValidatorModel

from fastapi.responses import StreamingResponse
import io

from src.tools.generators.database_export_generator import export_database

router = APIRouter()


class TestModel(TwitterValidatorModel):
    content: dict


@router.get("/tests")
async def test():
    a = test_client_mode()
    print(a)

    return "HEllo"


@router.get("/get_csv")
async def get_csv():
    d = [{'points': 50, 'time': '5:00', 'year': 2010},
         {'points': 25, 'time': '6:00', 'month': "february"},
         {'points': 90, 'time': '9:00', 'month': 'january'},
         {'points_h1': 20, 'month': 'june'}]

    d1 = []
    d1.append({'points': 50, 'time': '5:00', 'year': 2010})

    ''' df = pandas.DataFrame(data=list({
        "brand": "Ford",
        "model": "Mustang",
        "year": 1964
    }))'''
    df = pandas.DataFrame(d1)

    print(df)

    stream = io.StringIO()
    header = True

    df.to_csv(stream, encoding='utf-8', header=True, index=False)

    response = StreamingResponse(iter([stream.getvalue()]),
                                 media_type="text/csv"
                                 )

    response.headers["Content-Disposition"] = "attachment; filename=export.csv"

    # return response
    return "HELLO"


@router.get("/test_export")
async def test_export(db: Session = Depends(get_db)):
    data = export_database(db=db, session=MelonDevTwitterDatabase)

    print(type("\r"))

    for i in data:
        print(i)
    print(type(data))
    print(type(data[0]))

    lst = [{k.strip(): (v.strip().replace("\r", " ") if type(v) is str else v) if v is not None else None for k, v in i.items()} for i in data]
    for i in lst:
        print(i)

    df = pandas.DataFrame(lst)
    print(df)
    stream = io.StringIO()

    df.to_csv(stream, encoding='utf-8', header=True, index=False, sep=",", line_terminator='\n', quotechar='"',
              decimal=".")

    response = StreamingResponse(iter([stream.getvalue()]),
                                 media_type="text/csv"
                                 )

    response.headers["Content-Disposition"] = "attachment; filename=export.csv"

    t = iter([stream.getvalue()])

    for i in t:
        print("******************************")
        print(type(i))
        print(i)

    print(type(t))

    return response

    # return "HELLO"


@router.get("/get_csvs")
async def get_csvs(db: Session = Depends(get_db)):
    # d = iter([dict(col1=1, col2=2)])

    data = export_database(db=db, session=MelonDevTwitterDatabase)
    print(type(data))
    print(type(data[0]))
    # print(data)

    file_name = "export.csv"
    export_media_type = 'text/csv'
    export_headers = {
        "Content-Disposition": "attachment; filename={file_name}.csv".format(file_name=file_name)
    }
    return StreamingResponse(data, headers=export_headers, media_type=export_media_type)
    # return "HELLO"


@router.get("/database", include_in_schema=False)
async def database(db: Session = Depends(get_db)):
    a = db.query(MelonDevTwitterDatabase).limit(10).all()
    b = [item.serialize for item in a]
    print("DATABASE")
    return b
