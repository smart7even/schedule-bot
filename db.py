from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import settings
from collections import namedtuple

Base = declarative_base()

DB = namedtuple("DB", ["user", "password", "host", "port"])

db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")

db = DB(db_user, db_password, db_host, db_port)
connect_url = f"postgresql+psycopg2://{db.user}:{db.password}@{db.host}:{db.port}/schedule-tg-bot"

engine = create_engine(connect_url, echo=True)
Base.metadata.create_all(bind=engine)

Session = sessionmaker()
Session.configure(bind=engine)
