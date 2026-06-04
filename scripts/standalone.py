"""
API Sentinel — Standalone Check Script (GitHub Actions Mode)
=============================================================
Zero dependencies beyond httpx + stdlib. Reads env secrets,
fetches balances, calculates metrics, sends bilingual alerts,
writes docs/data.json for GitHub Pages Dashboard.
"""
import json
import os
import smtplib
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText

# ── Config ──

EMAIL_PROVIDERS = {
    "qq":      {"host": "smtp.qq.com",       "port": 587},
    "gmail":   {"host": "smtp.gmail.com",    "port": 587},
    "163":     {"host": "smtp.163.com",       "port": 25},
    "outlook": {"host": "smtp.office365.com","port": 587},
    "custom":  {"host": "", "port": 587},
}

L1_DAYS = float(os.getenv("ALERT_L1_DAYS", "3"))
L2_DAYS = float(os.getenv("ALERT_L2_DAYS", "1"))
L3_DAYS = float(os.getenv("ALERT_L3_DAYS", "0.25"))

DATA_FILE = "docs/data.json"


# ── HTTP Helpers ──

def http_get(url, headers):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:300]
        print("  HTTP %d: %s" % (e.code, body))
        return None
    except Exception as ex:
        print("  Error: %s" % ex)
        return None


# ── Provider Fetchers ──

def fetch_deepseek(key):
    data = http_get("https://api.deepseek.com/user/balance",
                    {"Authorization": "Bearer " + key, "Accept": "application/json"})
    if not data or not data.get("is_available"):
        return None
    info = data["balance_infos"][0]
    return {
        "total_credits": 0.0,
        "used_credits": 0.0,
        "remaining_credits": float(info["total_balance"]),
        "currency": info.get("currency", "CNY"),
    }

def fetch_openai(key):
    import httpx
    # We use urllib for consistency, but OpenAI billing needs httpx for async...
    # For GitHub Actions, we use sync httpx
    sub = http_get("https://api.openai.com/v1/dashboard/billing/subscription",
                   {"Authorization": "Bearer " + key})
    if not sub:
        return None
    end = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    start = (datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y-%m-%d")
    usage = http_get(
        "https://api.openai.com/v1/dashboard/billing/usage?start_date=%s&end_date=%s" % (start, end),
        {"Authorization": "Bearer " + key})
    if not usage:
        return None
    return {
        "total_credits": float(sub.get("hard_limit_usd", 0)),
        "used_credits": float(usage.get("total_usage", 0)) / 100.0,
        "remaining_credits": max(0, float(sub.get("hard_limit_usd", 0)) -
                                    float(usage.get("total_usage", 0)) / 100.0),
        "currency": "USD",
    }

def fetch_claude(key):
    data = http_get("https://api.anthropic.com/v1/organizations/spend_limits/effective",
                    {"x-api-key": key, "anthropic-version": "2023-06-01"})
    if not data or not data.get("data"):
        return None
    total = used = 0.0
    currency = "USD"
    for item in data["data"]:
        amt = item.get("amount")
        if amt and amt != "null":
            total += float(amt) / 100.0
        pts = item.get("period_to_date_spend", "0")
        if pts:
            used += float(pts)
        currency = item.get("currency", currency)
    return {
        "total_credits": total,
        "used_credits": used,
        "remaining_credits": max(0, total - used),
        "currency": currency,
    }

PROVIDERS = {
    "deepseek": (fetch_deepseek, os.getenv("DEEPSEEK_KEY", "")),
    "openai":   (fetch_openai,   os.getenv("OPENAI_KEY", "")),
    "claude":   (fetch_claude,   os.getenv("CLAUDE_KEY", "")),
}


# ── Metrics ──

def calc_metrics(snapshots):
    if len(snapshots) < 2:
        return {"avg_24h": None, "avg_7d": None,
                "predicted_days": None, "predicted_date": None, "status": "insufficient_data"}

    now = datetime.now(timezone.utc)
    latest = snapshots[-1]
    remaining = latest["remaining_credits"]

    # 24h window
    cutoff_24 = now - timedelta(hours=24)
    w24 = [s for s in snapshots if _parse_ts(s["fetched_at"]) >= cutoff_24]
    avg_24 = None
    if len(w24) >= 2:
        old = w24[0]["remaining_credits"]
        new = w24[-1]["remaining_credits"]
        days = max((_parse_ts(w24[-1]["fetched_at"]) -
                     _parse_ts(w24[0]["fetched_at"])).total_seconds() / 86400, 1.0/24)
        diff = old - new
        avg_24 = diff / days if diff > 0 else 0.0

    # 7d window
    cutoff_7d = now - timedelta(days=7)
    w7d = [s for s in snapshots if _parse_ts(s["fetched_at"]) >= cutoff_7d]
    avg_7d = None
    if len(w7d) >= 2:
        old = w7d[0]["remaining_credits"]
        new = w7d[-1]["remaining_credits"]
        days = max((_parse_ts(w7d[-1]["fetched_at"]) -
                     _parse_ts(w7d[0]["fetched_at"])).total_seconds() / 86400, 1.0/24)
        diff = old - new
        avg_7d = diff / days if diff > 0 else 0.0

    daily_rate = avg_7d or avg_24
    predicted_days = remaining / daily_rate if daily_rate and daily_rate > 0 else None
    predicted_date = (now + timedelta(days=predicted_days)).isoformat() if predicted_days else None
    status = "ok" if predicted_days else "insufficient_data"

    return {"avg_24h": round(avg_24, 4) if avg_24 else None,
            "avg_7d": round(avg_7d, 4) if avg_7d else None,
            "predicted_days": round(predicted_days, 2) if predicted_days else None,
            "predicted_date": predicted_date, "status": status}


def _parse_ts(ts_str):
    try:
        return datetime.fromisoformat(ts_str)
    except Exception:
        return datetime.now(timezone.utc)


# ── Alerts ──

def check_alert(predicted_days, provider, alias):
    if predicted_days is None:
        return None
    if predicted_days <= L3_DAYS:
        return "L3"
    if predicted_days <= L2_DAYS:
        return "L2"
    if predicted_days <= L1_DAYS:
        return "L1"
    return None


def build_message(provider, alias, remaining, currency, daily_avg, predicted_days, predicted_date, level):
    labels = {"L1": ("Low Balance / 额度不足", "3 days / 天"),
              "L2": ("Balance Warning / 额度警告", "24 hours / 小时"),
              "L3": ("CRITICAL / 紧急", "6 hours / 小时")}
    label, timeframe = labels.get(level, (level, ""))

    return (
        "[API Sentinel] %s (%s) — %s\n\n"
        "Your %s API key \"%s\" will run out around %s (approx. %.1f %s).\n"
        "%s API Key \"%s\" 预计在 %s 左右耗尽 (约 %.1f %s)。\n\n"
        "Remaining / 剩余: %s %.2f\n"
        "Daily avg / 日均消耗: %s %.2f\n\n"
        "— API Sentinel"
    ) % (provider, alias, label,
         provider, alias, predicted_date, predicted_days, timeframe,
         provider, alias, predicted_date, predicted_days, timeframe,
         currency, remaining,
         currency, daily_avg)


def send_email(provider_name, alias, remaining, currency, daily_avg,
               predicted_days, predicted_date, level):
    ep = os.getenv("EMAIL_PROVIDER", "")
    user = os.getenv("EMAIL_USER", "")
    auth = os.getenv("EMAIL_AUTH", "")
    to_addr = os.getenv("EMAIL_TO", user)

    if not ep or not user or not auth:
        print("  Email not configured, skipping.")
        return False

    smtp_cfg = EMAIL_PROVIDERS.get(ep, EMAIL_PROVIDERS["custom"])
    host = os.getenv("SMTP_HOST", smtp_cfg["host"])
    port = int(os.getenv("SMTP_PORT", str(smtp_cfg["port"])))

    if not host:
        print("  No SMTP host configured, skipping.")
        return False

    msg_text = build_message(provider_name, alias, remaining, currency,
                             daily_avg, predicted_days, predicted_date, level)
    msg = MIMEText(msg_text, "plain", "utf-8")
    msg["Subject"] = "[API Sentinel] %s (%s) — %s" % (
        provider_name, alias,
        {"L1": "Low Balance / 额度不足",
         "L2": "Balance Warning / 额度警告",
         "L3": "CRITICAL / 紧急"}[level])
    msg["From"] = user
    msg["To"] = to_addr

    try:
        s = smtplib.SMTP(host, port, timeout=15)
        s.starttls()
        s.login(user, auth)
        s.sendmail(user, [to_addr], msg.as_string())
        s.quit()
        print("  Email sent: %s -> %s via %s:%d" % (user, to_addr, host, port))
        return True
    except Exception as e:
        print("  Email FAILED: %s" % e)
        return False


# ── Data Persistence ──

def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"providers": {}, "alerts_sent": {},
                "updated_at": "", "deploy_url": ""}


def save_data(data):
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Main ──

def main():
    now = datetime.now(timezone.utc)
    print("=" * 60)
    print("  API Sentinel — GitHub Actions Check")
    print("  %s" % now.strftime("%Y-%m-%d %H:%M UTC"))
    print("=" * 60)

    data = load_data()
    active_count = 0
    alert_count = 0

    for name, (fetcher, key) in PROVIDERS.items():
        if not key:
            print("\n[%s] Skipped — no API key configured / 未配置密钥" % name)
            continue

        print("\n[%s] Fetching... / 获取数据..." % name)
        balance = fetcher(key)
        if not balance:
            print("  No data returned / 获取失败")
            continue

        active_count += 1
        print("  Balance / 余额: %s %.2f" % (balance["currency"], balance["remaining_credits"]))

        # Load provider history
        if name not in data["providers"]:
            data["providers"][name] = {"alias": name, "currency": balance["currency"],
                                       "snapshots": [], "last_alert": ""}

        prv = data["providers"][name]
        prv["currency"] = balance["currency"]

        # Keep last 200 snapshots (retention)
        snapshots = prv.get("snapshots", [])

        # Add current snapshot
        snapshots.append({
            "fetched_at": now.isoformat(),
            "total_credits": balance["total_credits"],
            "used_credits": balance["used_credits"],
            "remaining_credits": balance["remaining_credits"],
            "currency": balance["currency"],
        })
        prv["snapshots"] = snapshots[-200:]

        # Metrics
        m = calc_metrics(snapshots)
        prv["metrics"] = m
        print("  avg_24h: %s   avg_7d: %s   predicted: %s days   status: %s" % (
            m["avg_24h"], m["avg_7d"], m["predicted_days"], m["status"]))

        # Alert check
        level = check_alert(m["predicted_days"], name, prv.get("alias", name))
        if level:
            alert_key = "%s_%s" % (name, level)
            if alert_key not in data.get("alerts_sent", {}):
                daily = m["avg_7d"] or m["avg_24h"] or 0
                print("  Alert: %s — SENDING / 发送中..." % level)
                ok = send_email(name, prv.get("alias", name),
                                balance["remaining_credits"], balance["currency"],
                                daily, m["predicted_days"],
                                m["predicted_date"], level)
                if ok:
                    data["alerts_sent"] = data.get("alerts_sent", {})
                    data["alerts_sent"][alert_key] = now.isoformat()
                    alert_count += 1
            else:
                print("  Alert: %s — already sent / 已发送" % level)

        # Update deploy URL hint
        repo = os.getenv("GITHUB_REPOSITORY", "")
        if repo:
            owner = repo.split("/")[0] if "/" in repo else ""
            repo_name = repo.split("/")[-1] if "/" in repo else repo
            data["deploy_url"] = "https://%s.github.io/%s/" % (owner, repo_name)

    # Summary
    save_data(data)

    print("\n" + "=" * 60)
    print("  CHECK COMPLETE / 检查完成")
    print("  Providers: %d checked   Alerts: %d sent" % (active_count, alert_count))
    if data.get("deploy_url"):
        print("  Dashboard: %s" % data["deploy_url"])
    print("=" * 60)


if __name__ == "__main__":
    main()
