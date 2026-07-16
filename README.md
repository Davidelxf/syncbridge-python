# syncbridge-python

`syncbridge-python` is a small backend middleware project built with Python and FastAPI.

The goal is to simulate an integration between two systems:

* **System A** sends business events.
* **SyncBridge** receives, validates, stores and processes those events.
* **System B** receives normalized data from SyncBridge.

This project is focused on backend engineering concepts such as:

* API design
* event validation
* traceability
* asynchronous processing
* retries
* idempotency
* integration contracts
* simple AWS-ready evolution with LocalStack

## Current status

Phase 0: project setup.

Implemented:

* FastAPI application skeleton
* `/health` endpoint
* pytest configuration
* Ruff configuration
* initial interface contract draft

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

Activate it:

```bash
source .venv/bin/activate
```

On Windows:

```bash
.venv\Scripts\activate
```

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

Run the API:

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

Open the interactive API docs:

```text
http://127.0.0.1:8000/docs
```

## Tests

Run tests:

```bash
pytest
```

## Linting

Run Ruff:

```bash
ruff check .
```

Format check:

```bash
ruff format . --check
```

## Documentation

Initial documentation:

* `docs/interface-contract.md`
