from collections.abc import Iterator
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import EventRecord
from app.db.session import get_session
from app.main import app


@pytest.fixture
def client(
    test_session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[TestClient]:
    monkeypatch.setenv(
        "CURSOR_SIGNING_KEY",
        "test-cursor-signing-key",
    )

    def override_get_session() -> Iterator[Session]:
        with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    test_client = TestClient(app)
    yield test_client

    app.dependency_overrides.clear()
    test_client.close()


def test_post_events_persists_event_and_returns_received(
    client: TestClient,
    test_session_factory: sessionmaker[Session],
) -> None:
    response = client.post(
        "/events",
        json={
            "event_id": "evt_001",
            "source": "warehouse-system",
            "event_type": "part.created",
            "occurred_at": "2026-06-30T10:15:00Z",
            "payload": {
                "part_code": "ANT-001",
                "quantity": 4,
                "warehouse": "MURCIA",
            },
        },
    )

    assert response.status_code == 202
    assert response.json() == {
        "event_id": "evt_001",
        "status": "received",
    }

    with test_session_factory() as session:
        stored_event = session.get(EventRecord, "evt_001")

        assert stored_event is not None
        assert stored_event.status == "received"


def test_post_events_rejects_invalid_event(
    client: TestClient,
    test_session_factory: sessionmaker[Session],
) -> None:
    response = client.post(
        "/events",
        json={
            "event_id": "evt_invalid",
            "source": "warehouse-system",
            "event_type": "part.created",
            "occurred_at": "2026-06-30T10:15:00Z",
            "payload": {
                "part_code": "ANT-001",
                "quantity": 0,
                "warehouse": "MURCIA",
            },
        },
    )

    assert response.status_code == 422

    with test_session_factory() as session:
        stored_event = session.get(EventRecord, "evt_invalid")

        assert stored_event is None


def test_get_event_returns_event_status(client: TestClient) -> None:
    client.post(
        "/events",
        json={
            "event_id": "evt_001",
            "source": "warehouse-system",
            "event_type": "part.created",
            "occurred_at": "2026-06-30T10:15:00Z",
            "payload": {
                "part_code": "ANT-001",
                "quantity": 4,
                "warehouse": "MURCIA",
            },
        },
    )

    response = client.get("/events/evt_001")

    assert response.status_code == 200
    assert response.json() == {
        "event_id": "evt_001",
        "status": "received",
    }


def test_get_event_returns_404_when_event_does_not_exist(
    client: TestClient,
) -> None:
    response = client.get("/events/evt_unknown")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Event not found",
    }


def test_get_events_paginates_with_cursor(
    client: TestClient,
    test_session_factory: sessionmaker[Session],
) -> None:
    received_at = datetime(2026, 9, 3, 12, 0)

    with test_session_factory() as session:
        _add_event(session, "evt_003", received_at)
        _add_event(session, "evt_002", received_at)
        _add_event(session, "evt_001", received_at)
        session.commit()

    first_response = client.get("/events?limit=2")

    assert first_response.status_code == 200

    first_page = first_response.json()

    assert first_page["items"] == [
        {
            "event_id": "evt_003",
            "status": "received",
        },
        {
            "event_id": "evt_002",
            "status": "received",
        },
    ]
    assert first_page["has_more"] is True
    assert first_page["next_cursor"] is not None

    second_response = client.get(
        "/events",
        params={
            "limit": 2,
            "cursor": first_page["next_cursor"],
        },
    )

    assert second_response.status_code == 200

    assert second_response.json() == {
        "items": [
            {
                "event_id": "evt_001",
                "status": "received",
            }
        ],
        "next_cursor": None,
        "has_more": False,
    }


def test_get_events_rejects_invalid_cursor(
    client: TestClient,
) -> None:
    response = client.get(
        "/events",
        params={"cursor": "invalid-cursor"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Invalid cursor",
    }


@pytest.mark.parametrize("limit", [0, 101])
def test_get_events_rejects_invalid_limit(
    client: TestClient,
    limit: int,
) -> None:
    response = client.get(
        "/events",
        params={"limit": limit},
    )

    assert response.status_code == 422


def test_get_events_returns_empty_page(
    client: TestClient,
) -> None:
    response = client.get("/events")

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "next_cursor": None,
        "has_more": False,
    }


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
            status="received",
        )
    )
