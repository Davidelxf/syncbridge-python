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

## Field description

| Field         | Required | Description                                   |
| ------------- | -------: | --------------------------------------------- |
| `event_id`    |      Yes | Unique event identifier provided by System A. |
| `source`      |      Yes | Name of the source system.                    |
| `event_type`  |      Yes | Type of business event.                       |
| `occurred_at` |      Yes | Date and time when the event happened.        |
| `payload`     |      Yes | Business data associated with the event.      |

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

The event ingestion endpoint will be implemented in the next phase.

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

* `received`
* `queued`
* `processing`
* `completed`
* `failed`

## Notes

This contract is intentionally simple.

Its purpose is to make the integration understandable and testable without adding unnecessary bureaucracy.
