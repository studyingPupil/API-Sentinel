"""
Phase 0 - Shared utilities (Python 3.6+ compatible, zero external deps)
"""
from datetime import datetime
import json
import os
import sys
import urllib.request
import urllib.error


class StandardUsageData:
    def __init__(self, total_credits, used_credits, remaining_credits,
                 currency="USD", fetched_at=""):
        self.total_credits = total_credits
        self.used_credits = used_credits
        self.remaining_credits = remaining_credits
        self.currency = currency
        self.fetched_at = fetched_at or datetime.utcnow().isoformat()

    def as_dict(self):
        return {
            "total_credits": self.total_credits,
            "used_credits": self.used_credits,
            "remaining_credits": self.remaining_credits,
            "currency": self.currency,
            "fetched_at": self.fetched_at,
        }


def http_get(url, headers, timeout=30):
    """Returns (status_code, body_text)"""
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        return e.code, body
    except Exception as e:
        return 0, str(e)


def print_header(title):
    print("\n" + "=" * 60)
    print("  " + title)
    print("=" * 60)


def print_section(title):
    print("\n-- " + title + " --")


def print_result(success, message):
    tag = "[OK]" if success else "[FAIL]"
    print("  " + tag + " " + message)


def print_json(data, indent=2):
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            print(data[:500])
            return
    print(json.dumps(data, indent=indent, ensure_ascii=False))


def print_mapping_table(mappings):
    print("  {:<35} -> {:<25}  {}".format(
        "Provider Field", "StandardUsageData", "Note"))
    print("  {:<35}   {:<25}  {}".format("-" * 35, "-" * 25, "-" * 10))
    for pf, sf, notes in mappings:
        print("  {:<35} -> {:<25}  {}".format(pf, sf, notes))


def print_standard_data(data):
    print_section("StandardUsageData")
    print_json(data.as_dict())


def get_api_key(env_var, arg_value=None):
    if arg_value:
        return arg_value
    key = os.getenv(env_var)
    if not key:
        print("  [FAIL] Set env var {} or pass as argument".format(env_var))
        print("         Usage: python {} <api_key>".format(sys.argv[0]))
        sys.exit(1)
    return key
