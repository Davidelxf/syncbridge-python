from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, EventRecord


def test_event_record_can_be_persisted(tmp_path) -> None:
    database_path = tmp_path / "test.db"
    test_engine = create_engine(f"sqlite:///{database_path}")
    test_session_factory = sessionmaker(test_engine)
    Base.metadata.create_all(test_engine)

    event = EventRecord(
        event_id="evt_001",
        source="warehouse-system",
        event_type="part.created",
        occurred_at=datetime(2026, 6, 30, 10, 15, tzinfo=UTC),
        payload={
            "part_code": "ANT-001",
            "quantity": 4,
            "warehouse": "MURCIA",
        },
        status="received",
    )

    with test_session_factory() as session:
        session.add(event)
        session.commit()

    with test_session_factory() as session:
        stored_event = session.get(EventRecord, "evt_001")

        assert stored_event is not None
        assert stored_event.source == "warehouse-system"
        assert stored_event.event_type == "part.created"
        assert stored_event.payload["part_code"] == "ANT-001"
        assert stored_event.status == "received"
