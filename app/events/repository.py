from datetime import UTC, datetime

from sqlalchemy import select, tuple_
from sqlalchemy.orm import Session

from app.db.models import EventRecord
from app.events.status import EventStatus
from app.schemas.events import IncomingEvent


def create_event(session: Session, event: IncomingEvent) -> EventRecord:
    event_record = EventRecord(
        event_id=event.event_id,
        source=event.source,
        event_type=event.event_type,
        occurred_at=event.occurred_at.astimezone(UTC),
        payload=event.payload.model_dump(),
        status=EventStatus.RECEIVED.value,
    )

    session.add(event_record)
    session.commit()
    session.refresh(event_record)

    return event_record


def get_event_by_id(
    session: Session,
    event_id: str,
) -> EventRecord | None:
    return session.get(EventRecord, event_id)


def list_events_page(
    session: Session,
    page_size: int,
    cursor: tuple[datetime, str] | None = None,
    event_status: EventStatus | None = None,
) -> tuple[list[EventRecord], bool]:
    statement = select(EventRecord).order_by(
        EventRecord.received_at.desc(),
        EventRecord.event_id.desc(),
    )

    if event_status is not None:
        statement = statement.where(EventRecord.status == event_status.value)

    if cursor is not None:
        cursor_received_at, cursor_event_id = cursor
        statement = statement.where(
            tuple_(
                EventRecord.received_at,
                EventRecord.event_id,
            )
            < (
                cursor_received_at,
                cursor_event_id,
            )
        )

    events = list(session.scalars(statement.limit(page_size + 1)).all())

    has_more = len(events) > page_size

    return events[:page_size], has_more
