from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from src.environment.database_path import database_path

engine = create_engine(database_path['meloncloud'])
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_dbs():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
