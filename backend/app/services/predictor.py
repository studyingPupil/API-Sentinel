"""Consumption calculator and exhaustion predictor."""
from datetime import datetime, timedelta

from app.database import SessionLocal
from app.models import UsageSnapshot


def calculate_metrics(credential_id):
    """
    Calculate consumption metrics for a credential.
    Returns: {remaining_credits, currency, avg_24h, avg_7d,
              predicted_exhaustion_days, predicted_exhaustion_date, status}
    """
    db = SessionLocal()
    try:
        snapshots = (
            db.query(UsageSnapshot)
            .filter(UsageSnapshot.credential_id == credential_id)
            .order_by(UsageSnapshot.fetched_at.desc())
            .limit(168)  # up to 7 days of hourly data
            .all()
        )

        if not snapshots:
            return {
                "credential_id": credential_id,
                "remaining_credits": 0.0,
                "currency": "USD",
                "avg_24h": None,
                "avg_7d": None,
                "predicted_exhaustion_days": None,
                "predicted_exhaustion_date": None,
                "status": "insufficient_data",
            }

        latest = snapshots[0]
        now = datetime.utcnow()

        # Calculate daily averages from snapshot diffs
        avg_24h = _calc_daily_avg(snapshots, hours=24, now=now)
        avg_7d = _calc_daily_avg(snapshots, hours=168, now=now)

        # Use 7d avg for prediction, fall back to 24h
        daily_rate = avg_7d if avg_7d and avg_7d > 0 else (
            avg_24h if avg_24h and avg_24h > 0 else None
        )

        status = "ok"
        predicted_days = None
        predicted_date = None

        if daily_rate and daily_rate > 0:
            predicted_days = latest.remaining_credits / daily_rate
            predicted_date = (now + timedelta(days=predicted_days)).isoformat()
        else:
            status = "insufficient_data"

        return {
            "credential_id": credential_id,
            "remaining_credits": latest.remaining_credits,
            "currency": latest.currency,
            "avg_24h": round(avg_24h, 4) if avg_24h else None,
            "avg_7d": round(avg_7d, 4) if avg_7d else None,
            "predicted_exhaustion_days": round(predicted_days, 2) if predicted_days else None,
            "predicted_exhaustion_date": predicted_date,
            "status": status,
        }
    finally:
        db.close()


def _calc_daily_avg(snapshots, hours, now):
    """Calculate average daily consumption over a time window.

    Uses the difference between remaining_credits of the earliest
    snapshot within the window and the latest snapshot.
    """
    cutoff = now - timedelta(hours=hours)
    window_snaps = [s for s in snapshots if s.fetched_at >= cutoff]

    if len(window_snaps) < 2:
        return None

    newest = window_snaps[0].remaining_credits
    oldest = window_snaps[-1].remaining_credits
    days = max((window_snaps[0].fetched_at - window_snaps[-1].fetched_at).total_seconds() / 86400, 1.0 / 24)

    consumed = oldest - newest
    if consumed <= 0:
        return 0.0

    return consumed / days
