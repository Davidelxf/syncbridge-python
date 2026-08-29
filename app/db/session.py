from collections.abc import Iterator
from os import getenv

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = getenv("DATABASE_URL", "sqlite:///./syncbridge.db")

engine = create_engine(DATABASE_URL)
session_factory = sessionmaker(engine)


def get_session() -> Iterator[Session]:
    with session_factory() as session:
        yield session
