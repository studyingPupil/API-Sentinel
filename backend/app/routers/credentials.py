"""Credential CRUD — add, list, delete, update API keys."""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ApiCredential, UsageSnapshot
from app.schemas import (
    CredentialCreate,
    CredentialUpdate,
    CredentialResponse,
    CredentialWithLatest,
    MetricsResponse,
    UsageSnapshotResponse,
    ManualBalanceRequest,
    ManualBalanceResponse,
)
from app.crypto import encrypt
from app.adapters.registry import ProviderRegistry
from app.services.fetcher import fetch_on_create
from app.services.predictor import calculate_metrics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/credentials", tags=["credentials"])


def _to_response(cred: ApiCredential, latest_snap: UsageSnapshot = None) -> dict:
    base = {
        "id": cred.id,
        "provider": cred.provider,
        "alias": cred.alias,
        "is_active": cred.is_active,
        "created_at": cred.created_at,
        "updated_at": cred.updated_at,
    }
    if latest_snap:
        base.update({
            "total_credits": latest_snap.total_credits,
            "used_credits": latest_snap.used_credits,
            "remaining_credits": latest_snap.remaining_credits,
            "currency": latest_snap.currency,
            "last_fetched_at": latest_snap.fetched_at,
        })
    else:
        base.update({
            "total_credits": None,
            "used_credits": None,
            "remaining_credits": None,
            "currency": None,
            "last_fetched_at": None,
        })
    return base


def _latest_snapshot(db: Session, credential_id: int):
    return (
        db.query(UsageSnapshot)
        .filter(UsageSnapshot.credential_id == credential_id)
        .order_by(UsageSnapshot.fetched_at.desc())
        .first()
    )


@router.get("", response_model=list[CredentialWithLatest])
def list_credentials(db: Session = Depends(get_db)):
    creds = db.query(ApiCredential).order_by(ApiCredential.created_at.desc()).all()
    return [_to_response(c, _latest_snapshot(db, c.id)) for c in creds]


@router.post("", response_model=CredentialWithLatest, status_code=201)
def add_credential(body: CredentialCreate, db: Session = Depends(get_db)):
    if not ProviderRegistry.is_registered(body.provider):
        raise HTTPException(400, f"Unknown provider: {body.provider}")

    cred = ApiCredential(
        provider=body.provider,
        api_key=encrypt(body.api_key),
        alias=body.alias or "",
    )
    db.add(cred)
    db.commit()
    db.refresh(cred)

    snapshot = fetch_on_create(cred)
    return _to_response(cred, snapshot)


@router.delete("/{credential_id}", status_code=204)
def delete_credential(credential_id: int, db: Session = Depends(get_db)):
    cred = db.query(ApiCredential).get(credential_id)
    if not cred:
        raise HTTPException(404, "Credential not found")
    db.delete(cred)
    db.commit()


@router.put("/{credential_id}", response_model=CredentialResponse)
def update_credential(credential_id: int, body: CredentialUpdate,
                      db: Session = Depends(get_db)):
    cred = db.query(ApiCredential).get(credential_id)
    if not cred:
        raise HTTPException(404, "Credential not found")

    if body.api_key is not None:
        cred.api_key = encrypt(body.api_key)
    if body.alias is not None:
        cred.alias = body.alias
    if body.is_active is not None:
        cred.is_active = body.is_active

    db.commit()
    db.refresh(cred)
    return cred


@router.post("/{credential_id}/sync", response_model=CredentialWithLatest)
def sync_credential(credential_id: int, db: Session = Depends(get_db)):
    cred = db.query(ApiCredential).get(credential_id)
    if not cred:
        raise HTTPException(404, "Credential not found")

    snapshot = fetch_on_create(cred)
    return _to_response(cred, snapshot)


@router.get("/{credential_id}/metrics", response_model=MetricsResponse)
def get_metrics(credential_id: int, db: Session = Depends(get_db)):
    cred = db.query(ApiCredential).get(credential_id)
    if not cred:
        raise HTTPException(404, "Credential not found")
    return calculate_metrics(credential_id)


@router.get("/{credential_id}/history",
            response_model=list[UsageSnapshotResponse])
def get_history(credential_id: int, days: int = 7, db: Session = Depends(get_db)):
    from datetime import datetime, timedelta

    cred = db.query(ApiCredential).get(credential_id)
    if not cred:
        raise HTTPException(404, "Credential not found")

    cutoff = datetime.utcnow() - timedelta(days=days)
    return (
        db.query(UsageSnapshot)
        .filter(
            UsageSnapshot.credential_id == credential_id,
            UsageSnapshot.fetched_at >= cutoff,
        )
        .order_by(UsageSnapshot.fetched_at.asc())
        .all()
    )


@router.post("/{credential_id}/manual-balance",
              response_model=ManualBalanceResponse)
def set_manual_balance(credential_id: int,
                       body: ManualBalanceRequest,
                       db: Session = Depends(get_db)):
    """Set balance manually for providers without a billing API (GLM)."""
    cred = db.query(ApiCredential).get(credential_id)
    if not cred:
        raise HTTPException(404, "Credential not found")

    adapter = ProviderRegistry.get(cred.provider)
    if not adapter.is_manual:
        raise HTTPException(
            400,
            "Provider '{}' has an auto-fetch API. Use POST /sync instead.".format(
                cred.provider
            ),
        )

    snapshot = UsageSnapshot(
        credential_id=cred.id,
        total_credits=0.0,
        used_credits=0.0,
        remaining_credits=body.balance,
        currency="CNY",
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)

    return {
        "status": "ok",
        "snapshot_id": snapshot.id,
        "remaining_credits": snapshot.remaining_credits,
        "currency": snapshot.currency,
        "fetched_at": str(snapshot.fetched_at),
    }
