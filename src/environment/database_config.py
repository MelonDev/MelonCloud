from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from decouple import config


@as_declarative()
class MelonCloudDatabase:
    pass


@as_declarative()
class ModelDB2:
    pass


meloncloud_engine = create_engine(config('MELONCLOUD_DATABASE', default=None))
# engine2 = create_engine('postgresql://dev@postgres:5432/db2')

DBSession = sessionmaker(...)
DBSession.configure(binds={MelonCloudDatabase: meloncloud_engine})


# DBSession.configure(binds={ModelDB1: engine1, ModelDB2: engine2})

def get_session():
    db = DBSession()
    try:
        yield db
    finally:
        db.close()
