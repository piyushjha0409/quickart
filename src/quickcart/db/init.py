import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from models import Base


# connecting with the postgres db
engine = create_engine(os.getenv('DATABASE_URL'))


def create_table() -> None:
    Base.metadata.create_all(engine)
