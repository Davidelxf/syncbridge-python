# syncbridge-python

`syncbridge-python` is a small backend middleware project built with Python and FastAPI.

The goal is to simulate an integration between two systems:

* **System A** sends business events.
* **SyncBridge** receives, validates, stores and tracks those events.
* **System B** will receive normalized data from SyncBridge in later phases.

This project is focused on backend engineering concepts such as:

* API design
* event validation
* persistence
* traceability
* status management
* cursor-based pagination
* asynchronous processing
* retries
* idempotency
* integration contracts
* simple AWS-ready evolution with LocalStack

## Current status

Phase 2: event querying and status management.

Implemented:

* FastAPI application
* `/health` endpoint
* event validation with Pydantic
* `POST /events` event ingestion
* event persistence with SQLAlchemy
* Alembic database migrations
* `GET /events/{event_id}` event status lookup
* `GET /events` event listing
* filtering events by synchronization status
* cursor-based keyset pagination
* signed pagination cursors
* stable ordering by `received_at` and `event_id`
* database indexes for paginated event queries
* pytest test suite
* Ruff linting and formatting
* initial interface contract

Still pending in Phase 2:

* basic event status transition rules
* validated status updates
* final Phase 2 documentation review

## Event statuses

SyncBridge currently defines the following event statuses:

```text
received
queued
processing
completed
failed
```

Events are initially stored with the `received` status.

Status transitions will be introduced before the end of Phase 2 and later used by the event processing flow.

## Python version

This project uses:

```text
Python 3.11.9
```

## Local setup

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Linux or macOS:

```bash
source .venv/bin/activate
```

On Windows:

```powershell
.venv\Scripts\activate
```

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

## Environment variables

### Cursor signing key

The paginated event listing uses signed cursors.

Set a local signing key before using `GET /events`.

Linux or macOS:

```bash
export CURSOR_SIGNING_KEY="local-development-signing-key"
```

Windows PowerShell:

```powershell
$env:CURSOR_SIGNING_KEY="local-development-signing-key"
```

Do not commit real secrets to the repository.

### Database URL

By default, SyncBridge uses a local SQLite database:

```text
sqlite:///./syncbridge.db
```

A different database URL can be provided through the `DATABASE_URL` environment variable.

Example:

```bash
export DATABASE_URL="sqlite:///./syncbridge.db"
```

Windows PowerShell:

```powershell
$env:DATABASE_URL="sqlite:///./syncbridge.db"
```

Setting `DATABASE_URL` is optional when using the default SQLite configuration.

## Database migrations

Database schema evolution is managed with Alembic.

Apply all pending migrations:

```bash
alembic upgrade head
```

Check the current migration:

```bash
alembic current
```

Check whether the SQLAlchemy models contain schema changes that are not represented by migrations:

```bash
alembic check
```

## Run the API

Start the FastAPI application:

```bash
uvicorn app.main:app --reload
```

Check the health endpoint:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

Open the interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

## API endpoints

### Receive an event

```http
POST /events
```

Example request:

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

Example response:

```json
{
  "event_id": "evt_001",
  "status": "received"
}
```

The endpoint returns HTTP `202 Accepted` when the event is successfully received and stored.

### Query an event

```http
GET /events/{event_id}
```

Example response:

```json
{
  "event_id": "evt_001",
  "status": "received"
}
```

If the event does not exist, the API returns HTTP `404 Not Found`.

### List events

```http
GET /events
```

Events are returned from newest to oldest using cursor-based keyset pagination.

Available query parameters:

* `status`: optional event status filter.
* `limit`: maximum number of events returned. Defaults to `50` and must be between `1` and `100`.
* `cursor`: cursor returned by the previous page.

Example:

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

Pagination cursors must be treated as opaque values by API clients.

A cursor must be reused with the same filters that were used when it was generated.

## Pagination design

The event listing uses keyset pagination instead of offset-based pagination.

Events are ordered by:

```text
received_at DESC
event_id DESC
```

`event_id` acts as a deterministic tie-breaker when multiple events share the same reception timestamp.

The API retrieves one additional row beyond the requested page size to determine whether another page exists, avoiding the need for a `COUNT(*)` query.

Pagination cursors are signed so that clients cannot modify their contents without invalidating them.

Filtered pagination is supported by a composite database index based on:

```text
status
received_at
event_id
```

The index was introduced after inspecting the SQLite query execution plan for the filtered event listing.

## Tests

Run the complete test suite:

```bash
pytest
```

Tests currently cover areas such as:

* event schema validation
* event persistence
* event lookup
* event listing
* stable event ordering
* keyset pagination
* signed cursor encoding and validation
* pagination with status filters
* invalid cursor handling
* API query parameter validation

## Linting and formatting

Run Ruff:

```bash
ruff check .
```

Check formatting:

```bash
ruff format . --check
```

## Documentation

Project documentation currently includes:

* `docs/interface-contract.md`: basic integration contract between System A, SyncBridge and System B.

Additional architecture and technical decision documentation will be added as the project evolves.

## Roadmap

The main planned phases are:

1. Project setup
2. Event reception
3. Event querying and status management
4. Event processing
5. Asynchronous processing
6. Idempotency and retries
7. Local AWS-compatible integration with LocalStack
8. Portfolio and documentation improvements

The project intentionally evolves in small steps. Technologies and abstractions are introduced only when they solve a concrete problem.

## Project principles

The project prioritizes:

* simple and explicit Python code
* small modules and functions
* clear separation between API, persistence and processing
* behavior-focused tests
* documented technical decisions
* avoiding unnecessary abstractions and overengineering

The goal is not to build a large platform, but a small and defendable backend integration project that demonstrates practical Python backend engineering decisions.
