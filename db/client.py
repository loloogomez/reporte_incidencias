from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

MYSQL_DATABASE_URL = "mysql+pymysql://u602072991_userRoot::m3R!OxJwU6@45.151.120.12:3306/u602072991_molinetes"

engine = create_engine(MYSQL_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()