"""Webhook management (RBAC: admin or higher)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import AuthContext, CurrentContext, DbSession, require_role
from app.core.rbac import Role
from app.schemas.webhook import (
    WebhookCreate,
    WebhookCreated,
    WebhookDeliveryRead,
    WebhookRead,
)
from app.services.webhook_service import WebhookService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

RequireAdmin = Depends(require_role(Role.admin))


@router.get("", response_model=list[WebhookRead], summary="List webhooks")
def list_webhooks(context: CurrentContext, db: DbSession) -> list[WebhookRead]:
    return WebhookService(db).list(context.organization_id)


@router.post(
    "",
    response_model=WebhookCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Create a webhook (signing secret returned once)",
)
def create_webhook(
    payload: WebhookCreate,
    db: DbSession,
    context: AuthContext = RequireAdmin,
) -> WebhookCreated:
    webhook, secret = WebhookService(db).create(
        org_id=context.organization_id,
        url=str(payload.url),
        event_types=payload.event_types,
        actor_user_id=context.user.id,
    )
    return WebhookCreated(
        id=webhook.id,
        url=webhook.url,
        event_types=webhook.event_types,
        is_active=webhook.is_active,
        created_at=webhook.created_at,
        secret=secret,
    )


@router.get(
    "/{webhook_id}/deliveries",
    response_model=list[WebhookDeliveryRead],
    summary="Recent delivery attempts for a webhook",
)
def list_deliveries(
    webhook_id: UUID, context: CurrentContext, db: DbSession
) -> list[WebhookDeliveryRead]:
    service = WebhookService(db)
    webhook = service.get(context.organization_id, webhook_id)
    if webhook is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found."
        )
    return service.list_deliveries(webhook_id)


@router.delete(
    "/{webhook_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a webhook",
)
def delete_webhook(
    webhook_id: UUID,
    db: DbSession,
    context: AuthContext = RequireAdmin,
) -> None:
    deleted = WebhookService(db).delete(
        org_id=context.organization_id,
        webhook_id=webhook_id,
        actor_user_id=context.user.id,
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found."
        )
