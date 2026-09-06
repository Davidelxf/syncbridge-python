from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    yield


app = FastAPI(
    title="SyncBridge API",
    version="0.1.0",
    description="Small middleware API for event synchronization between systems.",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
