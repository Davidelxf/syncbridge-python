from fastapi import FastAPI

app = FastAPI(
    title="SyncBridge API",
    version="0.1.0",
    description="Small middleware API for event synchronization between systems.",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
