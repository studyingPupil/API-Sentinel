"""Phase 8 Final Audit — 7 checkpoints."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

results = {}
def audit(name, passed, detail=""):
    results[name] = (passed, detail)
    print("  [%s] %s" % ("PASS" if passed else "FAIL", name))
    if detail:
        print("        %s" % detail)

print("=" * 60)
print("  API Sentinel — Phase 8 Final Audit")
print("=" * 60)

# ═══ 1. Provider Registry ═══
print("\n--- 1. Provider Registry ---")

from app.adapters.registry import ProviderRegistry
providers = ProviderRegistry.list_providers()
expected = ["openai", "deepseek", "claude", "glm"]

for p in expected:
    ok = p in providers
    audit("Provider: %s registered" % p, ok,
          "" if ok else "MISSING from %s" % providers)

audit("Count: %d/4 providers" % len(providers), len(providers) == 4)

for p in expected:
    a = ProviderRegistry.get(p)
    is_manual = (p == "glm")
    audit("%s.is_manual=%s" % (p, a.is_manual), a.is_manual == is_manual)

# ═══ 2. fetch_all_active ═══
print("\n--- 2. fetch_all_active ---")

from app.database import init_db, SessionLocal
from app.models import ApiCredential, UsageSnapshot
from app.crypto import encrypt

init_db()
db = SessionLocal()
db.query(UsageSnapshot).delete(synchronize_session=False)
db.query(ApiCredential).delete()
db.commit()

created = {}
for p in expected:
    cred = ApiCredential(provider=p, api_key=encrypt("audit-%s" % p),
                         alias="Audit %s" % p)
    db.add(cred); db.commit(); db.refresh(cred)
    created[p] = cred.id

creds = db.query(ApiCredential).filter(ApiCredential.is_active == True).all()
audit("Active credentials", len(creds) == 4, "%d found" % len(creds))

from app.services.fetcher import fetch_and_store
for p in expected:
    r = fetch_and_store(created[p])
    ok = r is None  # All return None: no real keys or manual mode
    audit("fetch(%s) -> %s" % (p, "skip" if ok else "snapshot"), ok)

# ═══ 3. Scheduler ═══
print("\n--- 3. Scheduler ---")

spath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "scheduler.py")
ok = os.path.exists(spath)
audit("scheduler.py exists", ok)
if ok:
    with open(spath, encoding="utf-8") as f:
        sc = f.read()
    audit("  imports fetch_all_active", "fetch_all_active" in sc)
    audit("  imports check_alerts", "check_alerts" in sc)
    audit("  uses IntervalTrigger", "IntervalTrigger" in sc)
    audit("  has fetch_and_alert_job", "_fetch_and_alert_job" in sc)

# ═══ 4. Dashboard Metrics ═══
print("\n--- 4. Dashboard ---")

from datetime import datetime, timedelta
cred_id = created["deepseek"]
for i in range(8):
    db.add(UsageSnapshot(credential_id=cred_id, total_credits=100.0,
           used_credits=50.0 + i*3.0, remaining_credits=50.0 - i*3.0,
           currency="USD", fetched_at=datetime.utcnow() - timedelta(days=7-i, hours=12)))
db.commit()

from app.services.predictor import calculate_metrics
m = calculate_metrics(cred_id)
audit("remaining_credits: %.2f" % m["remaining_credits"], m["remaining_credits"] is not None)
audit("avg_7d: %s" % m["avg_7d"], m["avg_7d"] is not None)
audit("predicted_days: %s" % m["predicted_exhaustion_days"],
      m["predicted_exhaustion_days"] is not None)
audit("status: %s" % m["status"], m["status"] == "ok")

latest = db.query(UsageSnapshot).filter(
    UsageSnapshot.credential_id == cred_id
).order_by(UsageSnapshot.fetched_at.desc()).first()
audit("Credential + snapshot linked", latest is not None)

# ═══ 5. Notification Engine ═══
print("\n--- 5. Notification Engine ---")

from app.notifiers import get_notifier, AlertLevel, AlertContext
from app.notifiers.email import EmailNotifier, EmailNotifier as EN

for ch in ["email", "telegram", "feishu", "wecom"]:
    n = get_notifier(ch)
    audit("Notifier: %s" % ch, n is not None)

for p in expected:
    ctx = AlertContext(provider=p, alias="a", remaining_credits=10.0,
                       currency="USD", daily_avg=2.0, predicted_days=5.0,
                       predicted_date="2026-06-09", level=AlertLevel.INFO)
    msg = EN.build_message(ctx)
    audit("Alert msg %s" % p, len(msg) > 50, "%d chars" % len(msg))

from app.models import NotificationChannel, NotificationLog
ch = NotificationChannel(channel_type="telegram", config_json="{}")
db.add(ch); db.commit()
db.add(NotificationLog(credential_id=cred_id, channel_id=ch.id,
                        alert_level=2, message="t"))
db.commit()

from app.services.alerter import _already_sent
audit("Dedup L2 after L2", _already_sent(db, cred_id, ch.id, 2),
      "correctly blocked" if _already_sent(db, cred_id, ch.id, 2) else "NOT blocked")
audit("Upgrade L3 after L2", not _already_sent(db, cred_id, ch.id, 3),
      "correctly allowed" if not _already_sent(db, cred_id, ch.id, 3) else "blocked")

# ═══ 6. SQLite Schema ═══
print("\n--- 6. SQLite ---")

from sqlalchemy import inspect
engine = __import__("app.database", fromlist=["engine"]).engine
insp = inspect(engine)
tables = insp.get_table_names()

expected_tables = ["api_credentials", "usage_snapshots",
                   "notification_channels", "notification_logs", "settings"]
for t in expected_tables:
    ok = t in tables
    ncols = len(insp.get_columns(t)) if ok else 0
    audit("Table: %s" % t, ok, "%d cols" % ncols if ok else "MISSING")

audit("Total tables: %d" % len(tables), len(tables) >= 5,
      ", ".join(tables))

# ═══ 7. Docker ═══
print("\n--- 7. Docker Compose ---")

scripts_dir = os.path.dirname(os.path.abspath(__file__))
base = os.path.dirname(scripts_dir)
dc_path = os.path.join(base, "docker-compose.yml")
ok = os.path.exists(dc_path)
audit("docker-compose.yml", ok)

if ok:
    with open(dc_path) as f:
        content = f.read()
    for keyword in ["backend", "frontend", "8000", "3000"]:
        audit("  contains '%s'" % keyword, keyword in content)

for svc in ["backend", "frontend"]:
    df = os.path.join(base, svc, "Dockerfile")
    audit("Dockerfile: %s" % svc, os.path.exists(df))

# ═══ Cleanup ═══
db.query(NotificationLog).delete()
db.query(UsageSnapshot).delete(synchronize_session=False)
db.query(ApiCredential).delete()
db.query(NotificationChannel).filter(NotificationChannel.id == ch.id).delete()
db.commit()
db.close()

# ═══ SUMMARY ═══
print("\n" + "=" * 60)
print("  AUDIT SUMMARY")
print("=" * 60)

passed = sum(1 for p, _ in results.values() if p)
total = len(results)
for name, (p, d) in results.items():
    if not p:
        print("  FAIL: %s" % name)

print("\n  %d / %d checks passed" % (passed, total))
print("  OVERALL: %s" % ("PASS" if passed == total else "FAIL"))
print("=" * 60)
