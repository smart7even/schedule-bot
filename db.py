from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import settings

Base = declarative_base()

connect_url = os.getenv("DATABASE_URL")
print(connect_url)

engine = create_engine(connect_url, echo=True)
Base.metadata.create_all(bind=engine)

Session = sessionmaker()
Session.configure(bind=engine)
