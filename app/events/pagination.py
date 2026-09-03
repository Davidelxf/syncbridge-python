import base64
import binascii
import hashlib
import hmac
import json
from datetime import UTC, datetime

CURSOR_VERSION = 1


class InvalidCursorError(ValueError):
    pass


def encode_event_cursor(
    received_at: datetime,
    event_id: str,
    signing_key: str,
) -> str:
    if not signing_key:
        raise ValueError("Cursor signing key cannot be empty")

    normalized_received_at = _to_utc(received_at)

    payload = {
        "v": CURSOR_VERSION,
        "received_at": normalized_received_at.isoformat(),
        "event_id": event_id,
    }

    payload_bytes = json.dumps(
        payload,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")

    payload_segment = _base64_encode(payload_bytes)

    signature = hmac.new(
        signing_key.encode("utf-8"),
        payload_segment.encode("ascii"),
        hashlib.sha256,
    ).digest()

    signature_segment = _base64_encode(signature)

    return f"{payload_segment}.{signature_segment}"


def decode_event_cursor(
    cursor: str,
    signing_key: str,
) -> tuple[datetime, str]:
    if not signing_key:
        raise ValueError("Cursor signing key cannot be empty")

    if cursor.count(".") != 1:
        raise InvalidCursorError("Invalid cursor")

    payload_segment, signature_segment = cursor.split(".")

    expected_signature = hmac.new(
        signing_key.encode("utf-8"),
        payload_segment.encode("ascii"),
        hashlib.sha256,
    ).digest()

    try:
        provided_signature = _base64_decode(signature_segment)
    except (ValueError, binascii.Error) as exc:
        raise InvalidCursorError("Invalid cursor") from exc

    if not hmac.compare_digest(
        provided_signature,
        expected_signature,
    ):
        raise InvalidCursorError("Invalid cursor")

    try:
        payload = json.loads(_base64_decode(payload_segment))
    except (
        ValueError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        binascii.Error,
    ) as exc:
        raise InvalidCursorError("Invalid cursor") from exc

    if not isinstance(payload, dict):
        raise InvalidCursorError("Invalid cursor")

    if payload.get("v") != CURSOR_VERSION:
        raise InvalidCursorError("Invalid cursor")

    received_at_value = payload.get("received_at")
    event_id = payload.get("event_id")

    if not isinstance(received_at_value, str):
        raise InvalidCursorError("Invalid cursor")

    if not isinstance(event_id, str) or not event_id:
        raise InvalidCursorError("Invalid cursor")

    try:
        received_at = datetime.fromisoformat(received_at_value)
    except ValueError as exc:
        raise InvalidCursorError("Invalid cursor") from exc

    if received_at.tzinfo is None:
        raise InvalidCursorError("Invalid cursor")

    return received_at.astimezone(UTC), event_id


def _base64_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64_decode(value: str) -> bytes:
    encoded = value.encode("ascii")
    padding = b"=" * (-len(encoded) % 4)

    return base64.urlsafe_b64decode(encoded + padding)


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        # SQLite CURRENT_TIMESTAMP is UTC but is returned without timezone
        # information, so normalize it explicitly before encoding the cursor.
        return value.replace(tzinfo=UTC)

    return value.astimezone(UTC)
