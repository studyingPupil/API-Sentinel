"""
Phase 0.3 — DeepSeek Balance API 验证
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared import (
    http_get, print_header, print_section, print_result,
    print_json, print_standard_data, print_mapping_table,
    StandardUsageData, get_api_key,
)


BASE_URL = "https://api.deepseek.com"


def verify_deepseek(api_key: str):
    print_header("DeepSeek Balance API 验证")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }

    balance = None

    # Endpoint 1: Balance
    print_section("1: GET /user/balance")
    status, body = http_get(f"{BASE_URL}/user/balance", headers)
    if status == 200:
        balance = json_loads(body)
        print_result(True, f"HTTP {status}")
        print_json(balance)
    else:
        print_result(False, f"HTTP {status} — {body[:300]}")

    # Explore other endpoints
    print_section("Explore other endpoints")
    endpoints = [
        "/v1/billing/usage",
        "/billing/info",
        "/user/info",
    ]
    for ep in endpoints:
        status, body = http_get(f"{BASE_URL}{ep}", headers)
        if status == 200:
            print_result(True, f"GET {ep} -> HTTP 200")
            print_json(json_loads(body))
        else:
            print_result(False, f"GET {ep} -> HTTP {status}")

    # Build StandardUsageData
    print_section("Field Mapping -> StandardUsageData")
    if balance:
        info = balance.get("balance_infos", [{}])[0]
        total_balance = float(info.get("total_balance", "0"))

        print_mapping_table([
            ("balance_infos[0].total_balance",    "remaining_credits", ""),
            ("balance_infos[0].topped_up_balance", "(top-up)",          ""),
            ("balance_infos[0].granted_balance",   "(granted)",        ""),
            ("total_credits / used_credits",       "(not provided)",   "DeepSeek only returns balance"),
        ])

        data = StandardUsageData(
            total_credits=0.0,
            used_credits=0.0,
            remaining_credits=total_balance,
            currency=info.get("currency", "CNY"),
        )
        print_standard_data(data)
        return data

    print("  [FAIL] No balance data")
    return None


def json_loads(s):
    import json
    return json.loads(s)


def main():
    key = get_api_key("DEEPSEEK_API_KEY", sys.argv[1] if len(sys.argv) > 1 else None)
    result = verify_deepseek(key)
    print_header("Result")
    if result:
        print(f"  DeepSeek Balance API available! Balance: {result.remaining_credits} {result.currency}")
        print("  Note: DeepSeek does not provide total_credits/used_credits")
    else:
        print("  Verification failed")


if __name__ == "__main__":
    main()
