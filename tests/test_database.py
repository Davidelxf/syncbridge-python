from sqlalchemy import text

from app.db.session import session_factory


def test_database_session_executes_query() -> None:
    with session_factory() as session:
        result = session.execute(text("SELECT 1")).scalar_one()

    assert result == 1
