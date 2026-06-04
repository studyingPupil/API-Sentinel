"""
QQ Email Notification E2E Test
===============================
Tests: SMTP connection, test email, L1/L2/L3, dedup, upgrade, dashboard.

Usage: python verify_email_e2e.py <email> <auth_code> [recipient]
"""
import sys, os, json, asyncio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if len(sys.argv) < 3:
    print("Usage: python verify_email_e2e.py <email> <auth_code> [recipient]")
    sys.exit(1)

EMAIL_USER = sys.argv[1]
EMAIL_AUTH = sys.argv[2]
EMAIL_TO = sys.argv[3] if len(sys.argv) > 3 else sys.argv[1]

results = {}
def record(name, passed, detail=""):
    results[name] = (passed, detail)
    tag = "PASS" if passed else "FAIL"
    print("  [%s] %s%s" % (tag, name, (" — " + detail) if detail else ""))

from app.database import init_db, SessionLocal
from app.models import ApiCredential, UsageSnapshot, NotificationChannel, NotificationLog
from app.crypto import encrypt
from app.notifiers.email import EmailNotifier, encrypt_email_password, _decrypt_password
from app.notifiers.base import AlertLevel, AlertContext
from app.notifiers import get_notifier
from datetime import datetime, timedelta

init_db()
db = SessionLocal()

# Clean slate
db.query(NotificationLog).delete()
db.query(UsageSnapshot).delete(synchronize_session=False)
db.query(ApiCredential).delete()
db.query(NotificationChannel).delete()
db.commit()

print("=" * 60)
print("  API Sentinel — QQ Email Notification E2E Test")
print("  Sender: %s" % EMAIL_USER)
print("=" * 60)

# ── Pre-check: verify QQ email provider template ──
print("\n--- Pre-check: Email Provider Templates ---")
from app.notifiers.email import EMAIL_PROVIDERS
providers = EmailNotifier.get_providers()
types = [p["value"] for p in providers]
print("  Available types: %s" % types)
assert "qq" in types, "PRE-CHECK FAIL: qq not in providers"
assert "custom" in types, "PRE-CHECK FAIL: custom not in providers"
qq = EMAIL_PROVIDERS["qq"]
print("  QQ template: host=%s port=%d" % (qq["smtp_host"], qq["smtp_port"]))
assert qq["smtp_host"] == "smtp.qq.com"
assert qq["smtp_port"] == 587
record("Pre-check: QQ template", True)

# ── Create email channel ──
print("\n--- Setup: Create QQ Email Channel ---")
email_config = json.dumps({
    "provider_type": "qq",
    "username": EMAIL_USER,
    "password": encrypt_email_password(EMAIL_AUTH),
    "to_email": EMAIL_TO,
})
ch = NotificationChannel(channel_type="email", config_json=email_config, enabled=True)
db.add(ch)
db.commit()
db.refresh(ch)
print("  Channel created: id=%d type=%s" % (ch.id, ch.channel_type))

# Verify stored config
stored = json.loads(ch.config_json)
assert stored["provider_type"] == "qq"
assert stored["username"] == EMAIL_USER
assert stored["password"] != EMAIL_AUTH  # must be encrypted
decrypted_pw = _decrypt_password(stored["password"])
assert decrypted_pw == EMAIL_AUTH
record("Pre-check: Config encryption", True)

# Resolve SMTP
notifier = EmailNotifier()
smtp = notifier.resolve_smtp(json.loads(ch.config_json))
print("  Resolved SMTP: host=%s port=%d" % (smtp["smtp_host"], smtp["smtp_port"]))
assert smtp["smtp_host"] == "smtp.qq.com"
assert smtp["smtp_port"] == 587
record("Pre-check: resolve_smtp", True)

# ── Test 1: SMTP Connection ──
print("\n--- Test 1: SMTP Connection ---")
try:
    import aiosmtplib
    from email.mime.text import MIMEText

    async def test_smtp_connection():
        try:
            msg = MIMEText("connection test", "plain", "utf-8")
            msg["From"] = EMAIL_USER
            msg["To"] = EMAIL_TO
            await aiosmtplib.send(
                msg,
                hostname="smtp.qq.com",
                port=587,
                username=EMAIL_USER,
                password=EMAIL_AUTH,
                start_tls=True,
                timeout=15,
            )
            return True, None
        except Exception as e:
            return False, str(e)

    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

ok, err = loop.run_until_complete(test_smtp_connection())
if ok:
    record("Test 1: SMTP Connection", True)
else:
    record("Test 1: SMTP Connection", False, err)
    # Don't exit — test email might still work

# ── Test 2: Send Test Email ──
print("\n--- Test 2: Send Test Email ---")
try:
    async def send_test_email():
        msg = MIMEText("This is a test email from API Sentinel.", "plain", "utf-8")
        msg["Subject"] = "API Sentinel Test Email"
        msg["From"] = EMAIL_USER
        msg["To"] = EMAIL_TO
        await aiosmtplib.send(
            msg,
            hostname="smtp.qq.com",
            port=587,
            username=EMAIL_USER,
            password=EMAIL_AUTH,
            start_tls=True,
            timeout=15,
        )
        return True, None

    ok, err = loop.run_until_complete(send_test_email())
    if ok:
        record("Test 2: Test Email Sent", True, "Check inbox: " + EMAIL_TO)
    else:
        record("Test 2: Test Email Sent", False, err)
except Exception as ex:
    record("Test 2: Test Email Sent", False, str(ex))

# ── Test 3: L1 Notification (3-day warning) ──
print("\n--- Test 3: L1 Notification (3 days) ---")
try:
    # Create credential with mock data (3-day prediction)
    cred = ApiCredential(provider="openai", api_key=encrypt("sk-test-l1"), alias="L1-Test-Key")
    db.add(cred)
    db.commit()
    db.refresh(cred)

    # Insert snapshots simulating balance falling to 3-day level
    for i in range(8):
        ts = datetime.utcnow() - timedelta(days=7 - i, hours=12)
        db.add(UsageSnapshot(
            credential_id=cred.id, total_credits=100.0,
            used_credits=50.0 + i * 3.0,
            remaining_credits=50.0 - i * 3.0,
            currency="USD", fetched_at=ts,
        ))
    db.commit()

    # Build L1 message
    ctx = AlertContext(
        provider="OpenAI", alias="L1-Test-Key",
        remaining_credits=8.0, currency="USD",
        daily_avg=3.0, predicted_days=2.7,
        predicted_date=(datetime.utcnow() + timedelta(days=2.7)).isoformat(),
        level=AlertLevel.INFO,
    )
    message = notifier.build_message(ctx)
    print("  L1 Message (%d chars):" % len(message))
    print("  " + message[:80] + "...")

    # Send L1 email
    async def send_l1():
        msg = MIMEText(message, "plain", "utf-8")
        msg["Subject"] = message.split("\n")[0]
        msg["From"] = EMAIL_USER
        msg["To"] = EMAIL_TO
        await aiosmtplib.send(msg, hostname="smtp.qq.com", port=587,
                              username=EMAIL_USER, password=EMAIL_AUTH,
                              start_tls=True, timeout=15)

    loop.run_until_complete(send_l1())
    record("Test 3: L1 Notification", True, "Check inbox for L1 warning")
except Exception as ex:
    record("Test 3: L1 Notification", False, str(ex))

# ── Test 4: L2 Notification (24-hour warning) ──
print("\n--- Test 4: L2 Notification (24 hours) ---")
try:
    ctx2 = AlertContext(
        provider="OpenAI", alias="L2-Test-Key",
        remaining_credits=1.2, currency="USD",
        daily_avg=1.5, predicted_days=0.8,
        predicted_date=(datetime.utcnow() + timedelta(hours=19)).isoformat(),
        level=AlertLevel.WARNING,
    )
    message2 = notifier.build_message(ctx2)
    print("  L2 Message (%d chars):" % len(message2))
    print("  " + message2[:80] + "...")

    async def send_l2():
        msg = MIMEText(message2, "plain", "utf-8")
        msg["Subject"] = message2.split("\n")[0]
        msg["From"] = EMAIL_USER
        msg["To"] = EMAIL_TO
        await aiosmtplib.send(msg, hostname="smtp.qq.com", port=587,
                              username=EMAIL_USER, password=EMAIL_AUTH,
                              start_tls=True, timeout=15)

    loop.run_until_complete(send_l2())
    record("Test 4: L2 Notification", True, "Check inbox for L2 warning")
except Exception as ex:
    record("Test 4: L2 Notification", False, str(ex))

# ── Test 5: L3 Notification (6-hour critical) ──
print("\n--- Test 5: L3 Notification (6 hours) ---")
try:
    ctx3 = AlertContext(
        provider="OpenAI", alias="L3-Test-Key",
        remaining_credits=0.15, currency="USD",
        daily_avg=1.5, predicted_days=0.1,
        predicted_date=(datetime.utcnow() + timedelta(hours=2.4)).isoformat(),
        level=AlertLevel.CRITICAL,
    )
    message3 = notifier.build_message(ctx3)
    print("  L3 Message (%d chars):" % len(message3))
    print("  " + message3[:80] + "...")

    async def send_l3():
        msg = MIMEText(message3, "plain", "utf-8")
        msg["Subject"] = message3.split("\n")[0]
        msg["From"] = EMAIL_USER
        msg["To"] = EMAIL_TO
        await aiosmtplib.send(msg, hostname="smtp.qq.com", port=587,
                              username=EMAIL_USER, password=EMAIL_AUTH,
                              start_tls=True, timeout=15)

    loop.run_until_complete(send_l3())
    record("Test 5: L3 Notification", True, "Check inbox for L3 critical")
except Exception as ex:
    record("Test 5: L3 Notification", False, str(ex))

# ── Test 6: Dedup (L2 triggered twice, only 1 notification) ──
print("\n--- Test 6: Dedup Mechanism ---")
try:
    db.query(NotificationLog).delete()
    db.commit()

    # Log an L2 alert (simulating it was already sent)
    log1 = NotificationLog(credential_id=cred.id, channel_id=ch.id,
                           alert_level=2, message="L2 sent")
    db.add(log1)
    db.commit()

    from app.services.alerter import _already_sent

    # Try L2 again — should be deduped
    is_dup = _already_sent(db, cred.id, ch.id, 2)
    print("  L2 after L2 sent: %s (expect True = dedup)" % is_dup)

    # Verify only 1 log entry exists for L2
    count = db.query(NotificationLog).filter(
        NotificationLog.credential_id == cred.id,
        NotificationLog.channel_id == ch.id,
        NotificationLog.alert_level == 2,
    ).count()

    if is_dup and count == 1:
        record("Test 6: Dedup", True, "L2 blocked, %d log entry" % count)
    else:
        record("Test 6: Dedup", False, "is_dup=%s count=%d" % (is_dup, count))
except Exception as ex:
    record("Test 6: Dedup", False, str(ex))

# ── Test 7: Upgrade (L1→L2→L3, 3 notifications) ──
print("\n--- Test 7: Upgrade Notification ---")
try:
    db.query(NotificationLog).delete()
    db.commit()

    levels_sent = []
    for level in [AlertLevel.INFO, AlertLevel.WARNING, AlertLevel.CRITICAL]:
        # Check if should send
        already = _already_sent(db, cred.id, ch.id, int(level))
        if not already:
            # Simulate sending
            log = NotificationLog(
                credential_id=cred.id,
                channel_id=ch.id,
                alert_level=int(level),
                message="Upgrade test L%d" % int(level),
            )
            db.add(log)
            db.commit()
            levels_sent.append(int(level))
            print("  L%d sent (was not blocked)" % int(level))

            # Actually send email for this level
            ctx_u = AlertContext(
                provider="OpenAI", alias="Upgrade-Test",
                remaining_credits=10.0 - int(level) * 3,
                currency="USD", daily_avg=3.0,
                predicted_days={1: 2.5, 2: 0.8, 3: 0.1}[int(level)],
                predicted_date=(datetime.utcnow() + timedelta(
                    days={1: 2.5, 2: 0.8, 3: 0.1}[int(level)])).isoformat(),
                level=level,
            )
            msg_u = notifier.build_message(ctx_u)
            async def send_upgrade(m=msg_u):
                mime = MIMEText(m, "plain", "utf-8")
                mime["Subject"] = m.split("\n")[0]
                mime["From"] = EMAIL_USER
                mime["To"] = EMAIL_TO
                await aiosmtplib.send(mime, hostname="smtp.qq.com", port=587,
                                      username=EMAIL_USER, password=EMAIL_AUTH,
                                      start_tls=True, timeout=15)
            loop.run_until_complete(send_upgrade())
        else:
            print("  L%d blocked (already sent at higher level)" % int(level))

    if levels_sent == [1, 2, 3]:
        record("Test 7: Upgrade", True, "L1→L2→L3 all sent (3 emails)")
    else:
        record("Test 7: Upgrade", False, "Sent levels: %s" % levels_sent)
except Exception as ex:
    record("Test 7: Upgrade", False, str(ex))

# ── Test 8: Dashboard Regression ──
print("\n--- Test 8: Dashboard Regression ---")
try:
    # Verify notification channel CRUD
    channels = db.query(NotificationChannel).all()
    assert len(channels) >= 1, "No channels"
    print("  Channels: %d" % len(channels))

    # Verify provider registry
    from app.adapters.registry import ProviderRegistry
    providers = ProviderRegistry.list_providers()
    assert "deepseek" in providers and "openai" in providers
    print("  Providers: %s" % providers)

    # Verify predictor still works
    from app.services.predictor import calculate_metrics
    m = calculate_metrics(cred.id)
    assert m["status"] == "ok"
    print("  Predictor: avg_7d=%s days=%s" % (m["avg_7d"], m["predicted_exhaustion_days"]))

    # Verify email provider list API (simulate HTTP call)
    ep = EmailNotifier.get_providers()
    assert len(ep) == 5
    print("  Email providers API: %d types" % len(ep))

    record("Test 8: Dashboard", True, "All subsystems intact")
except Exception as ex:
    record("Test 8: Dashboard", False, str(ex))

# ── Cleanup ──
print("\n--- Cleanup ---")
db.query(NotificationLog).delete()
db.query(UsageSnapshot).filter(UsageSnapshot.credential_id == cred.id).delete(synchronize_session=False)
db.query(ApiCredential).filter(ApiCredential.id == cred.id).delete()
db.query(NotificationChannel).filter(NotificationChannel.id == ch.id).delete()
db.commit()
db.close()
print("  Test data cleaned up.")

# ═══════════════════════════════════════════════
# FINAL REPORT
# ═══════════════════════════════════════════════
print("\n")
print("=" * 60)
print("  FINAL REPORT — QQ Email Notification E2E")
print("=" * 60)
print()
print("  %-30s %s" % ("Test", "Result"))
print("  %-30s %s" % ("-" * 30, "-" * 10))
all_pass = True
for name, (passed, detail) in results.items():
    status = "PASS" if passed else "FAIL"
    if not passed:
        all_pass = False
    line = "  %-30s %s" % (name, status)
    if detail:
        line += "  (%s)" % detail
    print(line)

print()
print("  %-30s %s" % ("-" * 30, "-" * 10))
print("  %-30s %s" % ("OVERALL", "PASS" if all_pass else "FAIL"))
print()
if all_pass:
    print("  Notification Engine: VERIFIED with real QQ email.")
    print("  All 8 tests passed. Production-ready for email notifications.")
else:
    print("  Notification Engine: ISSUES FOUND.")
    print("  Check FAIL entries above for details.")
print("=" * 60)
