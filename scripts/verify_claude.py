"""
Phase 0.2 — Claude (Anthropic) Usage/Cost API 验证
Requires Admin API Key (sk-ant-admin...)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta, timezone
from shared import (
    http_get, print_header, print_section, print_result,
    print_json, print_standard_data, print_mapping_table,
    StandardUsageData, get_api_key,
)


BASE_URL = "https://api.anthropic.com"
API_VERSION = "2023-06-01"


def verify_claude(api_key: str):
    print_header("Claude (Anthropic) Usage/Cost API 验证")
    print("  Note: requires Admin API Key (sk-ant-admin...)")

    headers = {
        "x-api-key": api_key,
        "anthropic-version": API_VERSION,
        "Content-Type": "application/json",
    }

    cost_report = None
    spend_limits = None

    # Endpoint A: Cost Report
    print_section("A: GET /v1/organizations/cost_report")
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    end = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    url = f"{BASE_URL}/v1/organizations/cost_report?starting_at={start}&ending_at={end}&group_by[]=workspace_id"
    status, body = http_get(url, headers)
    if status == 200:
        cost_report = json_loads(body)
        print_result(True, f"HTTP {status}")
        print_json(cost_report)
    else:
        print_result(False, f"HTTP {status} — {body[:300]}")

    # Endpoint B: Spend Limits (Enterprise)
    print_section("B: GET /v1/organizations/spend_limits/effective")
    status, body = http_get(f"{BASE_URL}/v1/organizations/spend_limits/effective", headers)
    if status == 200:
        spend_limits = json_loads(body)
        print_result(True, f"HTTP {status}")
        print_json(spend_limits)
    else:
        print_result(False, f"HTTP {status} — {body[:200]}")

    # Endpoint C: Usage Report
    print_section("C: GET /v1/organizations/usage_report/messages (7d)")
    start = (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    url = f"{BASE_URL}/v1/organizations/usage_report/messages?starting_at={start}&ending_at={end}&group_by[]=model&bucket_width=1d"
    status, body = http_get(url, headers)
    if status == 200:
        print_result(True, f"HTTP {status}")
        print_json(json_loads(body))
    else:
        print_result(False, f"HTTP {status} — {body[:200]}")

    # Endpoint D: Organizations
    print_section("D: GET /v1/organizations")
    status, body = http_get(f"{BASE_URL}/v1/organizations", headers)
    if status == 200:
        print_result(True, f"HTTP {status}")
        print_json(json_loads(body))
    else:
        print_result(False, f"HTTP {status} — {body[:200]}")

    # Build StandardUsageData
    print_section("Field Mapping -> StandardUsageData")
    if spend_limits:
        print("  -> Using Spend Limits API")
        total = 0.0
        used = 0.0
        for item in spend_limits.get("data", []):
            amt = item.get("amount")
            if amt and amt != "null":
                total += float(amt) / 100.0
            pts = item.get("period_to_date_spend", "0")
            if pts:
                used += float(pts)

        print_mapping_table([
            ("amount / 100",             "total_credits",      "cents -> dollars"),
            ("period_to_date_spend",     "used_credits",       "current period"),
            ("total - used",             "remaining_credits",  "computed"),
        ])
        data = StandardUsageData(total_credits=total, used_credits=used, remaining_credits=max(0, total - used), currency="USD")
        print_standard_data(data)
        return data

    if cost_report:
        print("  -> Cost Report available (no total_credits)")
        print("  Total credits unknown; can only track cost")
        return None

    print("  [FAIL] No billing data available")
    return None


def json_loads(s):
    import json
    return json.loads(s)


def main():
    key = get_api_key("ANTHROPIC_ADMIN_KEY", sys.argv[1] if len(sys.argv) > 1 else None)
    verify_claude(key)
    print_header("Result")
    print("  See output above for API availability")


if __name__ == "__main__":
    main()
