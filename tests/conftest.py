from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import Base


@pytest.fixture
def test_session_factory(tmp_path: Path) -> sessionmaker[Session]:
    database_path = tmp_path / "test.db"
    test_engine = create_engine(f"sqlite:///{database_path}")
    Base.metadata.create_all(test_engine)

    return sessionmaker(test_engine)
