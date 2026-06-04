"""Notification channel CRUD + test endpoint."""
import json
import logging
import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import NotificationChannel
from app.schemas import ChannelCreate, ChannelUpdate, ChannelResponse
from app.notifiers import get_notifier
from app.notifiers.email import encrypt_email_password, EmailNotifier

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


def _prepare_config(channel_type, config_json):
    """Encrypt sensitive fields before storing."""
    if channel_type != "email":
        return config_json
    try:
        cfg = json.loads(config_json)
        if "password" in cfg and cfg["password"]:
            cfg["password"] = encrypt_email_password(cfg["password"])
        # Also handle old format
        if "smtp_password" in cfg and cfg["smtp_password"]:
            cfg["smtp_password"] = encrypt_email_password(cfg["smtp_password"])
        return json.dumps(cfg)
    except json.JSONDecodeError:
        return config_json


def _to_response(ch: NotificationChannel) -> dict:
    return {
        "id": ch.id,
        "channel_type": ch.channel_type,
        "config_json": ch.config_json,
        "enabled": ch.enabled,
        "created_at": ch.created_at,
    }


@router.get("/channels", response_model=list[ChannelResponse])
def list_channels(db: Session = Depends(get_db)):
    return db.query(NotificationChannel).order_by(
        NotificationChannel.created_at.desc()
    ).all()


@router.post("/channels", response_model=ChannelResponse, status_code=201)
def add_channel(body: ChannelCreate, db: Session = Depends(get_db)):
    # Validate channel_type
    if body.channel_type not in ("email", "telegram", "feishu", "wecom"):
        raise HTTPException(400, f"Unknown channel type: {body.channel_type}")

    # Validate config is valid JSON
    try:
        json.loads(body.config_json)
    except json.JSONDecodeError:
        raise HTTPException(400, "config_json must be valid JSON")

    ch = NotificationChannel(
        channel_type=body.channel_type,
        config_json=_prepare_config(body.channel_type, body.config_json),
        enabled=body.enabled,
    )
    db.add(ch)
    db.commit()
    db.refresh(ch)
    return ch


@router.delete("/channels/{channel_id}", status_code=204)
def delete_channel(channel_id: int, db: Session = Depends(get_db)):
    ch = db.query(NotificationChannel).get(channel_id)
    if not ch:
        raise HTTPException(404, "Channel not found")
    db.delete(ch)
    db.commit()


@router.put("/channels/{channel_id}", response_model=ChannelResponse)
def update_channel(channel_id: int, body: ChannelUpdate,
                   db: Session = Depends(get_db)):
    ch = db.query(NotificationChannel).get(channel_id)
    if not ch:
        raise HTTPException(404, "Channel not found")

    if body.config_json is not None:
        try:
            json.loads(body.config_json)
        except json.JSONDecodeError:
            raise HTTPException(400, "config_json must be valid JSON")
        ch.config_json = _prepare_config(ch.channel_type, body.config_json)
    if body.enabled is not None:
        ch.enabled = body.enabled

    db.commit()
    db.refresh(ch)
    return ch


@router.post("/channels/{channel_id}/test")
def test_channel(channel_id: int, db: Session = Depends(get_db)):
    ch = db.query(NotificationChannel).get(channel_id)
    if not ch:
        raise HTTPException(404, "Channel not found")

    notifier = get_notifier(ch.channel_type)
    config = _parse_config(ch.config_json)

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    success = loop.run_until_complete(notifier.test(config))

    if success:
        return {"status": "ok", "message": "Test notification sent"}
    else:
        raise HTTPException(500, "Failed to send test notification. Check server logs.")


@router.get("/email-providers")
def get_email_providers():
    """Return available email provider templates for the frontend dropdown."""
    return EmailNotifier.get_providers()


def _parse_config(config_json):
    try:
        return json.loads(config_json)
    except (json.JSONDecodeError, TypeError):
        return {}
