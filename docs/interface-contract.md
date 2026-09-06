# Interface Contract

This document describes the integration contract between the fictitious systems used in this project.

## Systems

### System A

Source system that sends business events to SyncBridge.

### SyncBridge

Middleware that receives, validates, stores and processes events.

### System B

Target system that receives normalized data from SyncBridge.

## Event format

System A sends events using this structure:

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

The current implementation supports only the `part.created` event type.

## Field description

| Field         | Required | Description                                          |
| ------------- | -------: | ---------------------------------------------------- |
| `event_id`    |      Yes | Unique event identifier provided by System A.        |
| `source`      |      Yes | Name of the source system.                           |
| `event_type`  |      Yes | Business event type. Currently only `part.created`.  |
| `occurred_at` |      Yes | Date and time of the event, including timezone data. |
| `payload`     |      Yes | Business data associated with the event.             |

## Supported event types

### `part.created`

Represents the creation of a part in the source warehouse system.

Its payload must contain:

| Field       | Required | Type    | Description                                     |
| ----------- | -------: | ------- | ----------------------------------------------- |
| `part_code` |      Yes | String  | Non-empty identifier of the created part.       |
| `quantity`  |      Yes | Integer | Quantity reported by System A. Must be above 0. |
| `warehouse` |      Yes | String  | Non-empty warehouse associated with the part.   |

## Validation rules

- All fields defined in the event structure are required.
- `event_type` must be `part.created` in the current implementation.
- `occurred_at` must include timezone information.
- `part_code` and `warehouse` must be non-empty strings.
- `quantity` must be an integer greater than 0.
- Fields not defined in this contract are rejected.

## API endpoints

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

### Event ingestion

```http
POST /events
```

SyncBridge validates the incoming event and stores accepted events with the initial `received` status.

A successfully accepted event returns HTTP `202 Accepted`.

Expected response:

```json
{
  "event_id": "evt_001",
  "status": "received"
}
```

Invalid events are rejected with HTTP `422 Unprocessable Entity` and are not persisted.

### Event status query

```http
GET /events/{event_id}
```

Returns the current synchronization status of an event.

Example response:

```json
{
  "event_id": "evt_001",
  "status": "received"
}
```

If the event does not exist, SyncBridge returns HTTP `404 Not Found`.

### Event listing

```http
GET /events
```

Returns events from newest to oldest using cursor-based pagination.

Optional query parameters:

| Parameter | Description |
| --------- | ----------- |
| `status`  | Filters events by synchronization status. |
| `limit`   | Maximum number of events returned. Defaults to `50` and must be between `1` and `100`. |
| `cursor`  | Opaque cursor returned by the previous page. |

Example request:

```http
GET /events?status=failed&limit=20
```

Example response:

```json
{
  "items": [
    {
      "event_id": "evt_010",
      "status": "failed"
    }
  ],
  "next_cursor": "opaque-cursor-value",
  "has_more": true
}
```

When `has_more` is `true`, `next_cursor` can be used to request the next page.

Example continuation request:

```http
GET /events?status=failed&limit=20&cursor=opaque-cursor-value
```

Clients must treat cursors as opaque values and must not modify or interpret their contents.

A cursor must be reused with the same filters that were used when it was generated.

Invalid or modified cursors return HTTP `400 Bad Request`.

A cursor reused with different filters also returns HTTP `400 Bad Request`.

Unsupported `status` values and invalid `limit` values return HTTP `422 Unprocessable Entity`.

## Event statuses

The project currently defines these synchronization statuses:

- `received`
- `queued`
- `processing`
- `completed`
- `failed`

Newly accepted events are stored with the `received` status.

Rules for valid transitions between statuses will be introduced as part of the status-management flow.

## Notes

This contract is intentionally simple.

Its purpose is to make the integration understandable and testable without adding unnecessary bureaucracy.

Implementation details such as cursor encoding, signing algorithms, database indexes and migration mechanics are intentionally kept outside this contract.
