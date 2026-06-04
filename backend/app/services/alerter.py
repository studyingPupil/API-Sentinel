"""Alert checker — evaluates predictions, deduplicates, and sends notifications."""
import json
import logging
import asyncio

from app.database import SessionLocal
from app.models import ApiCredential, NotificationChannel, NotificationLog
from app.services.predictor import calculate_metrics
from app.notifiers import get_notifier, AlertLevel, AlertContext

logger = logging.getLogger(__name__)


def check_alerts():
    """Check all active credentials against alert thresholds.
    Called by the scheduler after each fetch cycle.
    """
    db = SessionLocal()
    try:
        credentials = db.query(ApiCredential).filter(
            ApiCredential.is_active == True
        ).all()

        channels = db.query(NotificationChannel).filter(
            NotificationChannel.enabled == True
        ).all()

        if not channels:
            logger.debug("No enabled notification channels, skipping alerts.")
            return

        for cred in credentials:
            metrics = calculate_metrics(cred.id)
            if metrics["status"] != "ok":
                continue

            predicted_days = metrics["predicted_exhaustion_days"]
            if predicted_days is None:
                continue

            level = _determine_level(predicted_days)
            if level is None:
                continue

            for ch in channels:
                if _already_sent(db, cred.id, ch.id, level):
                    continue

                config = _parse_config(ch.config_json)
                ctx = AlertContext(
                    provider=cred.provider,
                    alias=cred.alias or cred.provider,
                    remaining_credits=metrics["remaining_credits"],
                    currency=metrics["currency"],
                    daily_avg=metrics["avg_7d"] or metrics["avg_24h"] or 0,
                    predicted_days=predicted_days,
                    predicted_date=metrics["predicted_exhaustion_date"] or "",
                    level=level,
                )

                notifier = get_notifier(ch.channel_type)
                message = notifier.build_message(ctx)

                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                success = loop.run_until_complete(
                    notifier.send(message, config)
                )

                log = NotificationLog(
                    channel_id=ch.id,
                    credential_id=cred.id,
                    alert_level=int(level),
                    message=message,
                )
                db.add(log)
                db.commit()

                if success:
                    logger.info("Alert sent: cred=%d level=%d channel=%s",
                                cred.id, level, ch.channel_type)
                else:
                    logger.warning("Alert failed: cred=%d level=%d channel=%s",
                                   cred.id, level, ch.channel_type)

    except Exception as e:
        logger.error("check_alerts error: %s", e)
    finally:
        db.close()


def _determine_level(predicted_days):
    if predicted_days <= 0.25:   # 6 hours
        return AlertLevel.CRITICAL
    elif predicted_days <= 1.0:  # 24 hours
        return AlertLevel.WARNING
    elif predicted_days <= 3.0:  # 3 days
        return AlertLevel.INFO
    return None


def _already_sent(db, credential_id, channel_id, level):
    """Check dedup: same or higher level already sent for this cred+channel."""
    existing = db.query(NotificationLog).filter(
        NotificationLog.credential_id == credential_id,
        NotificationLog.channel_id == channel_id,
        NotificationLog.alert_level >= int(level),
    ).first()
    return existing is not None


def _parse_config(config_json):
    try:
        return json.loads(config_json)
    except (json.JSONDecodeError, TypeError):
        return {}
