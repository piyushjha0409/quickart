import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from .models import Base

load_dotenv()


# connecting with the postgres db
engine = create_engine(os.getenv('DATABASE_URL'))


def create_table() -> None:
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(engine)
