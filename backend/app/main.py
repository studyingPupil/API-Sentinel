"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import health, credentials, notifications, settings
from app.database import init_db
from app.config import DEFAULT_SYNC_INTERVAL_MINUTES
from app.scheduler import start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler(DEFAULT_SYNC_INTERVAL_MINUTES)
    yield


app = FastAPI(
    title="API Sentinel",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(credentials.router)
app.include_router(notifications.router)
app.include_router(settings.router)
