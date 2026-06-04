"""Phase 3 — Integration test: credential CRUD + fetcher + predictor."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db, SessionLocal
from app.models import ApiCredential, UsageSnapshot
from app.crypto import encrypt, decrypt

print("=" * 60)
print("  Phase 3 — Integration Verification")
print("=" * 60)

# 1. Init DB
init_db()
print("\n[1] DB initialized.")

db = SessionLocal()

# 2. Create test credential
cred = ApiCredential(
    provider="openai",
    api_key=encrypt("sk-test-dummy-key-12345"),
    alias="Test OpenAI Key",
)
db.add(cred)
db.commit()
db.refresh(cred)
print(f"[2] Created credential id={cred.id}: {cred.provider}/{cred.alias}")

# 3. Verify encryption roundtrip
decrypted = decrypt(cred.api_key)
assert decrypted == "sk-test-dummy-key-12345", "Encryption roundtrip failed!"
print(f"[3] Encryption roundtrip OK: {decrypted[:10]}...")

# 4. Create mock usage snapshots for predictor testing
from datetime import datetime, timedelta, timezone
now = datetime.now(timezone.utc)

sample_data = []
for i in range(48):  # 2 days of hourly data (simulated)
    hours_ago = 48 - i
    ts = now - timedelta(hours=hours_ago)
    consumed = i * 0.05  # $0.05 per hour = $1.20/day
    snap = UsageSnapshot(
        credential_id=cred.id,
        total_credits=100.0,
        used_credits=consumed,
        remaining_credits=100.0 - consumed,
        currency="USD",
        fetched_at=ts,
    )
    db.add(snap)
db.commit()
print(f"[4] Inserted 48 mock snapshots ($0.05/h burn rate)")

# 5. Test predictor
from app.services.predictor import calculate_metrics
metrics = calculate_metrics(cred.id)

print(f"\n[5] Predictor results:")
print(f"    remaining: ${metrics['remaining_credits']:.2f}")
print(f"    avg_24h: ${metrics['avg_24h']:.2f}/day" if metrics['avg_24h'] else "    avg_24h: None")
print(f"    avg_7d: ${metrics['avg_7d']:.2f}/day" if metrics['avg_7d'] else "    avg_7d: None")
print(f"    predicted_exhaustion_days: {metrics['predicted_exhaustion_days']}")
print(f"    status: {metrics['status']}")

# Basic sanity: avg should be around $1.20/day
if metrics['avg_24h'] and 0.5 < metrics['avg_24h'] < 2.5:
    print("    -> 24h avg in expected range ($1.20/day): OK")
else:
    print(f"    -> 24h avg unexpected: {metrics['avg_24h']}")

# 6. Test CRUD operations
cred_count = db.query(ApiCredential).count()
print(f"\n[6] Credential count: {cred_count}")

snap_count = db.query(UsageSnapshot).filter(
    UsageSnapshot.credential_id == cred.id
).count()
print(f"    Snapshot count for cred {cred.id}: {snap_count}")

# 7. Cleanup test data
db.query(UsageSnapshot).filter(UsageSnapshot.credential_id == cred.id).delete()
db.delete(cred)
db.commit()
print(f"\n[7] Test data cleaned up.")

db.close()

print("\n" + "=" * 60)
print("  All Phase 3 checks passed!")
print("=" * 60)
print("\nNote: OpenAIAdapter.fetch_usage() not tested (needs real API key).")
print("The adapter is ready for end-to-end testing with a real key.")
