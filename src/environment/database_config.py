from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from decouple import config


@as_declarative()
class MelonCloudDatabase:
    pass


@as_declarative()
class BuffManagementDatabase:
    pass


meloncloud_engine = create_engine(config('MELONCLOUD_DATABASE', default=None))
buff_management_engine = create_engine(config('BUFF_MANAGEMENT_DATABASE', default=None))

DBSession = sessionmaker(...)
DBSession.configure(binds={MelonCloudDatabase: meloncloud_engine, BuffManagementDatabase: buff_management_engine})


def get_db():
    db = DBSession()
    try:
        yield db
    finally:
        db.close()
