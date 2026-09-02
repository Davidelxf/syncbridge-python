from datetime import UTC

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
