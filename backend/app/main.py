"""FastAPI application entry point."""

from fastapi import FastAPI

from backend.app.api.routes import router
from backend.app.config import settings

app = FastAPI(title=settings.app_name)
app.include_router(router)
