"""Aggregate v1 API router."""

from fastapi import APIRouter

from app.api.v1 import (
    analytics,
    api_keys,
    audit,
    auth,
    events,
    members,
    webhooks,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(members.router)
api_router.include_router(api_keys.router)
api_router.include_router(events.router)
api_router.include_router(analytics.router)
api_router.include_router(webhooks.router)
api_router.include_router(audit.router)
