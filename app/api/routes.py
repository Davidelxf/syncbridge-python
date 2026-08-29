from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.events.repository import create_event
from app.schemas.events import EventReceivedResponse, IncomingEvent

router = APIRouter(tags=["events"])


@router.post(
    "/events",
    response_model=EventReceivedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def receive_event(
    event: IncomingEvent,
    session: Annotated[Session, Depends(get_session)],
) -> EventReceivedResponse:
    created_event = create_event(session, event)

    return EventReceivedResponse(
        event_id=created_event.event_id,
        status=created_event.status,
    )
