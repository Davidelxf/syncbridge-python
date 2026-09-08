from collections.abc import Iterator
from os import getenv

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import Base

TEST_DATABASE_URL = getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://syncbridge:syncbridge@localhost:5432/syncbridge_test",
)


@pytest.fixture(scope="session")
def test_engine() -> Iterator[Engine]:
    engine = create_engine(TEST_DATABASE_URL)

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    yield engine

    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def test_session_factory(
    test_engine: Engine,
) -> Iterator[sessionmaker[Session]]:
    with test_engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())

    yield sessionmaker(test_engine)

    with test_engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())
