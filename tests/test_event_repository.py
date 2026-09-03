from datetime import datetime

from sqlalchemy.orm import Session, sessionmaker

from app.db.models import EventRecord
from app.events.repository import create_event, get_event_by_id, list_events_page
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
        assert created_event.received_at is not None

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
        assert stored_event.received_at is not None


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


def test_list_events_page_uses_stable_order(
    test_session_factory: sessionmaker[Session],
) -> None:
    with test_session_factory() as session:
        _add_event(
            session,
            "evt_001",
            datetime(2026, 9, 3, 10, 0),
        )
        _add_event(
            session,
            "evt_002",
            datetime(2026, 9, 3, 11, 0),
        )
        _add_event(
            session,
            "evt_003",
            datetime(2026, 9, 3, 11, 0),
        )
        session.commit()

    with test_session_factory() as session:
        events, has_more = list_events_page(
            session,
            page_size=10,
        )

    assert [event.event_id for event in events] == [
        "evt_003",
        "evt_002",
        "evt_001",
    ]
    assert has_more is False


def test_list_events_page_continues_after_cursor(
    test_session_factory: sessionmaker[Session],
) -> None:
    same_received_at = datetime(2026, 9, 3, 11, 0)

    with test_session_factory() as session:
        _add_event(session, "evt_004", same_received_at)
        _add_event(session, "evt_003", same_received_at)
        _add_event(session, "evt_002", same_received_at)
        _add_event(
            session,
            "evt_001",
            datetime(2026, 9, 3, 10, 0),
        )
        session.commit()

    with test_session_factory() as session:
        first_page, first_has_more = list_events_page(
            session,
            page_size=2,
        )

        cursor = (
            first_page[-1].received_at,
            first_page[-1].event_id,
        )

        second_page, second_has_more = list_events_page(
            session,
            page_size=2,
            cursor=cursor,
        )

    assert [event.event_id for event in first_page] == [
        "evt_004",
        "evt_003",
    ]
    assert first_has_more is True

    assert [event.event_id for event in second_page] == [
        "evt_002",
        "evt_001",
    ]
    assert second_has_more is False


def _add_event(
    session: Session,
    event_id: str,
    received_at: datetime,
) -> None:
    session.add(
        EventRecord(
            event_id=event_id,
            source="warehouse-system",
            event_type="part.created",
            occurred_at=received_at,
            received_at=received_at,
            payload={
                "part_code": "ANT-001",
                "quantity": 1,
                "warehouse": "MURCIA",
            },
            status=EventStatus.RECEIVED.value,
        )
    )
