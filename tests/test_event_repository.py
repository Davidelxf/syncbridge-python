from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, EventRecord
from app.events.repository import create_event
from app.events.status import EventStatus
from app.schemas.events import IncomingEvent


def test_create_event_persists_received_event(tmp_path) -> None:
    database_path = tmp_path / "test.db"
    test_engine = create_engine(f"sqlite:///{database_path}")
    test_session_factory = sessionmaker(test_engine)
    Base.metadata.create_all(test_engine)

    incoming_event = IncomingEvent.model_validate(
        {
            "event_id": "evt_001",
            "source": "warehouse-system",
            "event_type": "part.created",
            "occurred_at": "2026-06-30T10:15:00+02:00",
            "payload": {
                "part_code": "ANT-001",
                "quantity": 4,
                "warehouse": "MURCIA",
            },
        }
    )

    with test_session_factory() as session:
        created_event = create_event(session, incoming_event)

        assert created_event.status == EventStatus.RECEIVED

    with test_session_factory() as session:
        stored_event = session.get(EventRecord, "evt_001")

        assert stored_event is not None
        assert stored_event.source == "warehouse-system"
        assert stored_event.payload == {
            "part_code": "ANT-001",
            "quantity": 4,
            "warehouse": "MURCIA",
        }
        assert stored_event.status == EventStatus.RECEIVED
        assert stored_event.occurred_at == datetime(2026, 6, 30, 8, 15)
