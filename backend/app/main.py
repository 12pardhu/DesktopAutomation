from __future__ import annotations

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.deps import queue_manager
from app.api.routes import router
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    await queue_manager().start()
    try:
        yield
    finally:
        await queue_manager().stop()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Intelligent Offline Desktop Automation Assistant",
        version="1.0.0",
        description="Offline desktop automation assistant powered by local LLMs.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app


app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
