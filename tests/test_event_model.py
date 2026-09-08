from datetime import UTC, datetime

from sqlalchemy.orm import Session, sessionmaker

from app.db.models import EventRecord
from app.events.status import EventStatus


def test_event_record_can_be_persisted(
    test_session_factory: sessionmaker[Session],
) -> None:
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
        status=EventStatus.RECEIVED.value,
    )

    with test_session_factory() as session:
        session.add(event)
        session.commit()

    with test_session_factory() as session:
        stored_event = session.get(EventRecord, "evt_001")

        assert stored_event is not None
        assert stored_event.received_at is not None
        assert stored_event.source == "warehouse-system"
        assert stored_event.event_type == "part.created"
        assert stored_event.payload["part_code"] == "ANT-001"
        assert stored_event.status == EventStatus.RECEIVED
