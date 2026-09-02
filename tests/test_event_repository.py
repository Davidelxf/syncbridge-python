from datetime import datetime

from sqlalchemy.orm import Session, sessionmaker

from app.db.models import EventRecord
from app.events.repository import create_event, get_event_by_id
from app.events.status import EventStatus
from app.schemas.events import IncomingEvent


def test_create_event_persists_received_event(
    test_session_factory: sessionmaker[Session],
) -> None:
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


def test_get_event_by_id_returns_existing_event(
    test_session_factory: sessionmaker[Session],
) -> None:
    incoming_event = IncomingEvent.model_validate(
        {
            "event_id": "evt_001",
            "source": "warehouse-system",
            "event_type": "part.created",
            "occurred_at": "2026-06-30T10:15:00Z",
            "payload": {
                "part_code": "ANT-001",
                "quantity": 4,
                "warehouse": "MURCIA",
            },
        }
    )

    with test_session_factory() as session:
        create_event(session, incoming_event)

    with test_session_factory() as session:
        stored_event = get_event_by_id(session, "evt_001")

        assert stored_event is not None
        assert stored_event.event_id == "evt_001"
        assert stored_event.status == EventStatus.RECEIVED


def test_get_event_by_id_returns_none_when_event_does_not_exist(
    test_session_factory: sessionmaker[Session],
) -> None:
    with test_session_factory() as session:
        stored_event = get_event_by_id(session, "evt_unknown")

        assert stored_event is None
