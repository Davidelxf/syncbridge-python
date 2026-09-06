from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import get_cursor_signing_key
from app.db.session import get_session
from app.events.pagination import (
    InvalidCursorError,
    decode_event_cursor,
    encode_event_cursor,
)
from app.events.repository import (
    create_event,
    get_event_by_id,
    list_events_page,
)
from app.events.status import EventStatus
from app.schemas.events import (
    EventPageResponse,
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


@router.get(
    "/events",
    response_model=EventPageResponse,
)
def get_events(
    session: Annotated[Session, Depends(get_session)],
    signing_key: Annotated[str, Depends(get_cursor_signing_key)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: Annotated[str | None, Query()] = None,
    event_status: Annotated[
        EventStatus | None,
        Query(alias="status"),
    ] = None,
) -> EventPageResponse:
    decoded_cursor = None

    if cursor is not None:
        try:
            (
                cursor_received_at,
                cursor_event_id,
                cursor_status,
            ) = decode_event_cursor(
                cursor,
                signing_key,
            )
        except InvalidCursorError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid cursor",
            ) from exc

        if cursor_status != event_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid cursor for requested filters",
            )

        decoded_cursor = (
            cursor_received_at,
            cursor_event_id,
        )

    events, has_more = list_events_page(
        session,
        page_size=limit,
        cursor=decoded_cursor,
        event_status=event_status,
    )

    next_cursor = None

    if has_more:
        last_event = events[-1]

        next_cursor = encode_event_cursor(
            last_event.received_at,
            last_event.event_id,
            signing_key,
            event_status,
        )

    return EventPageResponse(
        items=[
            EventResponse(
                event_id=event.event_id,
                status=event.status,
            )
            for event in events
        ],
        next_cursor=next_cursor,
        has_more=has_more,
    )
