"""Usage data fetcher — calls Provider Adapters and stores snapshots."""
import logging

from app.adapters.registry import ProviderRegistry
from app.crypto import decrypt
from app.database import SessionLocal
from app.models import ApiCredential, UsageSnapshot

logger = logging.getLogger(__name__)


def fetch_and_store(credential_id):
    """Fetch usage for one credential and store a new snapshot. Returns the snapshot or None."""
    db = SessionLocal()
    try:
        cred = db.query(ApiCredential).filter(
            ApiCredential.id == credential_id,
            ApiCredential.is_active == True,
        ).first()

        if not cred:
            logger.info("Credential %d not found or inactive, skipping.", credential_id)
            return None

        adapter = ProviderRegistry.get(cred.provider)

        if adapter.is_manual:
            logger.info(
                "Credential %d (%s) is manual-only, skipping auto-fetch.",
                credential_id, cred.provider,
            )
            return None

        plain_key = decrypt(cred.api_key)

        # Run async adapter inside sync context (APScheduler is sync)
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        data = loop.run_until_complete(adapter.fetch_usage(plain_key))

        snapshot = UsageSnapshot(
            credential_id=cred.id,
            total_credits=data.total_credits,
            used_credits=data.used_credits,
            remaining_credits=data.remaining_credits,
            currency=data.currency,
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)

        logger.info("Stored snapshot for %s (%s): %.2f/%.2f %s",
                     cred.provider, cred.alias, data.remaining_credits,
                     data.total_credits, data.currency)
        return snapshot

    except Exception as e:
        logger.error("Failed to fetch usage for credential %d: %s", credential_id, e)
        db.rollback()
        return None
    finally:
        db.close()


def fetch_all_active():
    """Fetch usage for all active credentials. Called by the scheduler."""
    db = SessionLocal()
    try:
        credentials = db.query(ApiCredential).filter(
            ApiCredential.is_active == True
        ).all()
    finally:
        db.close()

    results = []
    for cred in credentials:
        snapshot = fetch_and_store(cred.id)
        if snapshot:
            results.append(snapshot)

    return results


def fetch_on_create(credential):
    """Fetch immediately after a new credential is added."""
    return fetch_and_store(credential.id)
