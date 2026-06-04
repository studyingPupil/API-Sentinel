"""
Phase 0.4 — GLM (Zhipu AI) Account/Billing API 验证
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared import (
    http_get, print_header, print_section, print_result,
    print_json, get_api_key,
)


BASE_URL = "https://open.bigmodel.cn"


def verify_glm(api_key: str):
    print_header("GLM (Zhipu AI) Account/Billing API 验证")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Try all possible billing/account endpoints
    print_section("Trying known/potential endpoints...")

    endpoints = [
        ("GET",  "/api/paas/v4/user/info",         "user info"),
        ("GET",  "/api/paas/v4/account/info",       "account info"),
        ("GET",  "/api/paas/v4/account/balance",    "account balance"),
        ("GET",  "/api/paas/v4/account/resource",   "resources"),
        ("POST", "/api/paas/v4/account/resources",  "resources (POST)"),
        ("GET",  "/api/paas/v4/billing/info",       "billing info"),
        ("GET",  "/api/paas/v4/billing/usage",      "billing usage"),
        ("GET",  "/api/paas/v4/user/usage",         "user usage"),
        ("GET",  "/api/paas/v4/user/balance",       "user balance"),
        ("GET",  "/api/platform/v4/account/info",   "platform account"),
        ("GET",  "/api/account/v1/info",            "account v1"),
        ("GET",  "/api/billing/v1/balance",         "billing v1"),
    ]

    found = []
    for method, path, desc in endpoints:
        url = f"{BASE_URL}{path}"
        if method == "POST":
            # POST needs body, use empty object
            import urllib.request
            req = urllib.request.Request(url, data=b"{}", headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    body = resp.read().decode("utf-8")
                    print_result(True, f"{method} {path} ({desc}) -> HTTP {resp.status}")
                    print_json(body)
                    found.append((path, body))
            except Exception as e:
                code = getattr(e, 'code', 0)
                print_result(False, f"{method} {path} ({desc}) -> HTTP {code}")
        else:
            status, body = http_get(url, headers)
            if status == 200:
                print_result(True, f"GET {path} ({desc}) -> HTTP 200")
                print_json(body)
                found.append((path, body))
            else:
                print_result(False, f"GET {path} ({desc}) -> HTTP {status}")

    print_header("Result")
    if found:
        print(f"  Found {len(found)} working endpoint(s)!")
        for path, _ in found:
            print(f"    {path}")
    else:
        print("  No billing API endpoints found")
        print("  GLM may not have a public billing REST API")
        print("  Fallback: manual balance input in Adapter")


def main():
    key = get_api_key("GLM_API_KEY", sys.argv[1] if len(sys.argv) > 1 else None)
    verify_glm(key)


if __name__ == "__main__":
    main()
