from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.schemas.events import IncomingEvent

VALID_EVENT = {
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


def test_incoming_event_accepts_contract_example() -> None:
    event = IncomingEvent.model_validate(VALID_EVENT)

    assert event.event_id == "evt_001"
    assert event.event_type == "part.created"
    assert event.payload.part_code == "ANT-001"
    assert event.occurred_at.tzinfo is not None


@pytest.mark.parametrize(
    "missing_field",
    ["event_id", "source", "event_type", "occurred_at", "payload"],
)
def test_incoming_event_rejects_missing_required_fields(
    missing_field: str,
) -> None:
    event_data = deepcopy(VALID_EVENT)
    event_data.pop(missing_field)

    with pytest.raises(ValidationError):
        IncomingEvent.model_validate(event_data)


def test_incoming_event_rejects_unsupported_event_type() -> None:
    event_data = deepcopy(VALID_EVENT)
    event_data["event_type"] = "part.updated"

    with pytest.raises(ValidationError):
        IncomingEvent.model_validate(event_data)


def test_incoming_event_rejects_unknown_payload_fields() -> None:
    event_data = deepcopy(VALID_EVENT)
    event_data["payload"]["location"] = "AISLE-4"

    with pytest.raises(ValidationError):
        IncomingEvent.model_validate(event_data)


def test_incoming_event_requires_timezone() -> None:
    event_data = deepcopy(VALID_EVENT)
    event_data["occurred_at"] = "2026-06-30T10:15:00"

    with pytest.raises(ValidationError):
        IncomingEvent.model_validate(event_data)
