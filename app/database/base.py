import sys
sys.path.append("../")

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings


engine = create_engine(settings.DATABASE_URL)

SessionLoacal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

def get_db():
    db = SessionLoacal()
    try:
        yield db
    finally:
        db.close()