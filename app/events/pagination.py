import base64
import binascii
import hashlib
import hmac
import json
from datetime import UTC, datetime

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
)

CURSOR_VERSION = 1


class _EventCursorPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    v: int
    received_at: AwareDatetime
    event_id: str = Field(min_length=1)


class InvalidCursorError(ValueError):
    pass


def encode_event_cursor(
    received_at: datetime,
    event_id: str,
    signing_key: str,
) -> str:
    if not signing_key:
        raise ValueError("Cursor signing key cannot be empty")

    payload = _EventCursorPayload(
        v=CURSOR_VERSION,
        received_at=_to_utc(received_at),
        event_id=event_id,
    )

    payload_bytes = json.dumps(
        payload.model_dump(mode="json"),
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
        raise InvalidCursorError()

    try:
        payload_segment, signature_segment = cursor.split(".")

        expected_signature = hmac.new(
            signing_key.encode("utf-8"),
            payload_segment.encode("ascii"),
            hashlib.sha256,
        ).digest()

        provided_signature = _base64_decode(signature_segment)
    except (ValueError, UnicodeError, binascii.Error) as exc:
        raise InvalidCursorError() from exc

    if not hmac.compare_digest(
        provided_signature,
        expected_signature,
    ):
        raise InvalidCursorError()

    try:
        payload = _EventCursorPayload.model_validate_json(
            _base64_decode(payload_segment)
        )
    except (ValidationError, ValueError, UnicodeError, binascii.Error) as exc:
        raise InvalidCursorError() from exc

    if payload.v != CURSOR_VERSION:
        raise InvalidCursorError()

    return payload.received_at.astimezone(UTC), payload.event_id


def _base64_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64_decode(value: str) -> bytes:
    encoded = value.encode("ascii")
    padding = b"=" * (-len(encoded) % 4)

    return base64.b64decode(
        encoded + padding,
        altchars=b"-_",
        validate=True,
    )


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        # received_at is generated in UTC by the database. Some database
        # drivers may return it without timezone information, so normalize
        # it explicitly before encoding the cursor.
        return value.replace(tzinfo=UTC)

    return value.astimezone(UTC)
