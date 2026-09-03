from datetime import UTC, datetime

from sqlalchemy import and_, or_, select
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
) -> tuple[list[EventRecord], bool]:
    statement = select(EventRecord).order_by(
        EventRecord.received_at.desc(),
        EventRecord.event_id.desc(),
    )

    if cursor is not None:
        cursor_received_at, cursor_event_id = cursor

        statement = statement.where(
            or_(
                EventRecord.received_at < cursor_received_at,
                and_(
                    EventRecord.received_at == cursor_received_at,
                    EventRecord.event_id < cursor_event_id,
                ),
            )
        )

    events = list(session.scalars(statement.limit(page_size + 1)).all())

    has_more = len(events) > page_size

    return events[:page_size], has_more
