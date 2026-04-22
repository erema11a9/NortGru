import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Решаем проблему с кодировкой Windows сразу здесь
os.environ['PGCLIENTENCODING'] = 'utf-8'

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:12393qwe@localhost:5432/nortgru_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Эта функция будет давать доступ к базе каждому твоему запросу (API)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()