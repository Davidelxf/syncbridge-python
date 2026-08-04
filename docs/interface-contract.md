# Interface Contract

This document describes the initial integration contract between the fictitious systems used in this project.

## Systems

### System A

Source system that sends business events to SyncBridge.

### SyncBridge

Middleware that receives, validates, stores and processes events.

### System B

Target system that receives normalized data from SyncBridge.

## Initial event format

System A will send events using this structure:

```json
{
  "event_id": "evt_001",
  "source": "warehouse-system",
  "event_type": "part.created",
  "occurred_at": "2026-06-30T10:15:00Z",
  "payload": {
    "part_code": "ANT-001",
    "quantity": 4,
    "warehouse": "MURCIA"
  }
}
```

The first implementation supports only the `part.created` event type.

## Field description

| Field         | Required | Description                                             |
| ------------- | -------: | ------------------------------------------------------- |
| `event_id`    |      Yes | Unique event identifier provided by System A.           |
| `source`      |      Yes | Name of the source system.                              |
| `event_type`  |      Yes | Business event type. Initially, only `part.created`.    |
| `occurred_at` |      Yes | Date and time of the event, including timezone data.    |
| `payload`     |      Yes | Business data associated with the event.                |

## Supported event types

### `part.created`

Represents the creation of a part in the source warehouse system.

Its payload must contain:

| Field       | Required | Type    | Description                                      |
| ----------- | -------: | ------- | ------------------------------------------------ |
| `part_code` |      Yes | String  | Non-empty identifier of the created part.        |
| `quantity`  |      Yes | Integer | Quantity reported by System A. Must be above 0.  |
| `warehouse` |      Yes | String  | Non-empty warehouse associated with the part.    |

## Validation rules

- All fields defined in the event structure are required.
- `event_type` must be `part.created` in the first implementation.
- `occurred_at` must include timezone information.
- `part_code` and `warehouse` must be non-empty strings.
- `quantity` must be an integer greater than 0.
- Fields not defined in this contract are rejected.

## Initial API endpoints

### Health check

```http
GET /health
```

Expected response:

```json
{
  "status": "ok"
}
```

## Planned event ingestion endpoint

The event ingestion endpoint will be implemented during Phase 1.

```http
POST /events
```

Expected accepted response:

```json
{
  "event_id": "evt_001",
  "status": "received"
}
```

## Initial event statuses

The project will use these synchronization statuses:

- `received`
- `queued`
- `processing`
- `completed`
- `failed`

## Notes

This contract is intentionally simple.

Its purpose is to make the integration understandable and testable without adding unnecessary bureaucracy.
