from datetime import UTC, datetime

import pytest

from app.events.pagination import (
    InvalidCursorError,
    decode_event_cursor,
    encode_event_cursor,
)
from app.events.status import EventStatus

SIGNING_KEY = "test-cursor-signing-key"


def test_event_cursor_round_trip() -> None:
    received_at = datetime(
        2026,
        9,
        3,
        15,
        30,
        tzinfo=UTC,
    )

    cursor = encode_event_cursor(
        received_at,
        "evt_001",
        SIGNING_KEY,
        EventStatus.FAILED,
    )

    (
        decoded_received_at,
        decoded_event_id,
        decoded_status,
    ) = decode_event_cursor(
        cursor,
        SIGNING_KEY,
    )

    assert decoded_received_at == received_at
    assert decoded_event_id == "evt_001"
    assert decoded_status == EventStatus.FAILED


def test_event_cursor_round_trip_without_status_filter() -> None:
    received_at = datetime(
        2026,
        9,
        3,
        15,
        30,
        tzinfo=UTC,
    )

    cursor = encode_event_cursor(
        received_at,
        "evt_001",
        SIGNING_KEY,
    )

    _, _, decoded_status = decode_event_cursor(
        cursor,
        SIGNING_KEY,
    )

    assert decoded_status is None


def test_event_cursor_rejects_tampered_payload() -> None:
    received_at = datetime(
        2026,
        9,
        3,
        15,
        30,
        tzinfo=UTC,
    )

    original_cursor = encode_event_cursor(
        received_at,
        "evt_001",
        SIGNING_KEY,
    )
    different_cursor = encode_event_cursor(
        received_at,
        "evt_999",
        SIGNING_KEY,
    )

    _, original_signature = original_cursor.split(".")
    different_payload, _ = different_cursor.split(".")

    tampered_cursor = f"{different_payload}.{original_signature}"

    with pytest.raises(InvalidCursorError):
        decode_event_cursor(
            tampered_cursor,
            SIGNING_KEY,
        )


def test_event_cursor_rejects_wrong_signing_key() -> None:
    received_at = datetime(
        2026,
        9,
        3,
        15,
        30,
        tzinfo=UTC,
    )

    cursor = encode_event_cursor(
        received_at,
        "evt_001",
        SIGNING_KEY,
    )

    with pytest.raises(InvalidCursorError):
        decode_event_cursor(
            cursor,
            "different-signing-key",
        )


def test_event_cursor_rejects_invalid_format() -> None:
    with pytest.raises(InvalidCursorError):
        decode_event_cursor(
            "not-a-valid-cursor",
            SIGNING_KEY,
        )
