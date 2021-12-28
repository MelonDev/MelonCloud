import uuid
import datetime
from fastapi import HTTPException, status

from src.database.melondev_twitter_database import MelonDevTwitterDatabase


def export_database(db,session):
    name = session.__tablename__
    date = datetime.datetime.now().strftime('%Y_%m_%d')

    filename = name + "_" + date

    db_session = filter_all_record_database(db,session)

    return export(db_session)
    '''try:
        name = db.__tablename__
        date = datetime.datetime.now().strftime('%Y_%m_%d')

        filename = name + "_" + date

        db_session = filter_all_record_database(db)

        return export(db_session)

    except AttributeError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error))
    except Exception as exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exception))
    '''


def export_current_year_database(db):
    try:
        name = db.__tablename__
        date = datetime.datetime.now().strftime('%Y_%m_%d')

        filename = name + "_" + date

        db_session = filter_current_year_record_database(db)

        return export(db_session)


    except AttributeError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error))
    except Exception as exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exception))


def filter_all_record_database(db,session):
    return db.query(session).filter(MelonDevTwitterDatabase.account.contains(str("102640199"))).all()


def export(raw):
    try:
        headers = list(raw[0].export.keys())
        data = [dict((k, v) for k, v in i.export.items()) for i in raw]
        return data
        # return send_csv(data, (filename if filename is not None else ("export" + "_" + str(uuid.uuid4()))) + ".csv",
        #                headers)
    except AttributeError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error))
    except Exception as exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exception))


def filter_current_year_record_database(db):
    current_year_str = datetime.datetime.now().strftime('%Y')
    start_datetime = datetime.datetime.strptime(str(current_year_str) + "-01-01 00:00:00", '%Y-%m-%d %H:%M:%S')
    end_datetime = datetime.datetime.now()
    filter_database = db.query(db)
    filter_database = filter_database.filter(db.addedAt <= end_datetime)
    filter_database = filter_database.filter(db.addedAt >= start_datetime)
    return filter_database.all()
