"""
Phase 0.1 — OpenAI Usage / Billing API 验证
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from shared import (
    http_get, print_header, print_section, print_result,
    print_json, print_standard_data, print_mapping_table,
    StandardUsageData, get_api_key,
)


BASE_URL = "https://api.openai.com"


def verify_openai(api_key: str):
    print_header("OpenAI Billing API 验证")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    subscription = None
    billing_usage = None

    # Endpoint 1: Billing Subscription
    print_section("1: GET /v1/dashboard/billing/subscription")
    status, body = http_get(f"{BASE_URL}/v1/dashboard/billing/subscription", headers)
    if status == 200:
        subscription = json_loads(body)
        print_result(True, f"HTTP {status}")
        print_json(subscription)
    else:
        print_result(False, f"HTTP {status} — {body[:200]}")

    # Endpoint 2: Billing Usage
    print_section("2: GET /v1/dashboard/billing/usage")
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    url = f"{BASE_URL}/v1/dashboard/billing/usage?start_date={start_date}&end_date={end_date}"
    status, body = http_get(url, headers)
    if status == 200:
        billing_usage = json_loads(body)
        print_result(True, f"HTTP {status}")
        print_json(billing_usage)
    else:
        print_result(False, f"HTTP {status} — {body[:200]}")

    # Endpoint 3: Token Usage (fallback)
    print_section("3: GET /v1/usage (Token, fallback)")
    today = datetime.now().strftime("%Y-%m-%d")
    status, body = http_get(f"{BASE_URL}/v1/usage?date={today}", headers)
    if status == 200:
        print_result(True, f"HTTP {status}")
        print_json(json_loads(body))
    else:
        print_result(False, f"HTTP {status} — {body[:200]}")

    # Build StandardUsageData
    print_section("Field Mapping -> StandardUsageData")
    if subscription and billing_usage:
        hard_limit = float(subscription.get("hard_limit_usd", 0))
        total_usage = float(billing_usage.get("total_usage", 0)) / 100.0
        remaining = hard_limit - total_usage

        print_mapping_table([
            ("subscription.hard_limit_usd",    "total_credits",     ""),
            ("billing.total_usage / 100",      "used_credits",      "cents -> dollars"),
            ("hard_limit - total_usage",       "remaining_credits", "computed"),
        ])
        data = StandardUsageData(
            total_credits=hard_limit,
            used_credits=total_usage,
            remaining_credits=remaining,
            currency="USD",
        )
        print_standard_data(data)
        return data

    print("  [FAIL] No billing data available (need owner/admin API key)")
    return None


def json_loads(s):
    import json
    return json.loads(s)


def main():
    key = get_api_key("OPENAI_API_KEY", sys.argv[1] if len(sys.argv) > 1 else None)
    result = verify_openai(key)
    print_header("Result")
    if result:
        print("  Open AI Billing API available!")
        print(f"  Total: ${result.total_credits:.2f}  Used: ${result.used_credits:.2f}  Remaining: ${result.remaining_credits:.2f}")
    else:
        print("  Need billing-permissioned API key")


if __name__ == "__main__":
    main()
