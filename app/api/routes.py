from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.events.repository import create_event, get_event_by_id
from app.schemas.events import (
    EventResponse,
    IncomingEvent,
)

router = APIRouter(tags=["events"])


@router.post(
    "/events",
    response_model=EventResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def receive_event(
    event: IncomingEvent,
    session: Annotated[Session, Depends(get_session)],
) -> EventResponse:
    created_event = create_event(session, event)

    return EventResponse(
        event_id=created_event.event_id,
        status=created_event.status,
    )


@router.get(
    "/events/{event_id}",
    response_model=EventResponse,
)
def get_event_status(
    event_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> EventResponse:
    event = get_event_by_id(session, event_id)

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    return EventResponse(
        event_id=event.event_id,
        status=event.status,
    )
