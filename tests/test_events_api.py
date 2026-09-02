from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import EventRecord
from app.db.session import get_session
from app.main import app


@pytest.fixture
def client(
    test_session_factory: sessionmaker[Session],
) -> Iterator[TestClient]:
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
