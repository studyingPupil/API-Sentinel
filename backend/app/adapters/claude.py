"""Claude (Anthropic) Adapter — fetches usage/cost from Admin API.

Requires an Admin API Key (sk-ant-admin...), NOT a regular API key.
Create at: https://console.anthropic.com → Settings → Admin Keys

API docs: https://docs.anthropic.com/en/docs/build-with-claude/usage-cost-api
"""
import logging
from datetime import datetime, timedelta, timezone

from app.adapters.base import BaseProviderAdapter, StandardUsageData

logger = logging.getLogger(__name__)

BASE_URL = "https://api.anthropic.com"
API_VERSION = "2023-06-01"


class ClaudeAdapter(BaseProviderAdapter):
    provider_name = "claude"

    async def fetch_usage(self, api_key):
        import httpx

        headers = {
            "x-api-key": api_key,
            "anthropic-version": API_VERSION,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(
            base_url=BASE_URL, headers=headers, timeout=30.0
        ) as client:

            # Path A: Spend Limits (Enterprise — gives limit + period spend)
            spend_limits = await self._get_json(
                client, "/v1/organizations/spend_limits/effective"
            )

            if spend_limits and spend_limits.get("data"):
                return self._parse_spend_limits(spend_limits)

            # Path B: Cost Report (all plans — gives total cost, no limit)
            now = datetime.now(timezone.utc)
            start = (now - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
            end = now.strftime("%Y-%m-%dT%H:%M:%SZ")

            cost_report = await self._get_json(
                client,
                "/v1/organizations/cost_report"
                "?starting_at={}&ending_at={}&group_by[]=workspace_id".format(
                    start, end
                ),
            )

            if cost_report:
                return self._parse_cost_report(cost_report)

            raise RuntimeError(
                "Claude API: no billing data available. "
                "Ensure you are using an Admin API Key (sk-ant-admin...)."
            )

    async def validate_key(self, api_key):
        try:
            import httpx
            async with httpx.AsyncClient(
                base_url=BASE_URL,
                headers={"x-api-key": api_key, "anthropic-version": API_VERSION},
                timeout=10.0,
            ) as client:
                r = await client.get("/v1/organizations")
                return r.status_code == 200
        except Exception:
            return False

    # ── Private helpers ──

    @staticmethod
    def _parse_spend_limits(data):
        """Parse spend_limits/effective response.

        Response format:
          {"data": [{"amount": "50000", "currency": "USD",
                      "period": "monthly",
                      "period_to_date_spend": "31402.5"}]}

        amount is in CENTS, period_to_date_spend is in DOLLARS.
        """
        total = 0.0
        used = 0.0
        currency = "USD"

        for item in data.get("data", []):
            amount = item.get("amount")
            if amount and amount != "null":
                total += float(amount) / 100.0  # cents → dollars

            pts = item.get("period_to_date_spend", "0")
            if pts:
                used += float(pts)

            currency = item.get("currency", currency)

        remaining = max(0.0, total - used)

        return StandardUsageData(
            total_credits=total,
            used_credits=used,
            remaining_credits=remaining,
            currency=currency,
        )

    @staticmethod
    def _parse_cost_report(data):
        """Parse cost_report response.

        Cost report gives total cost but no credit limit.
        Set total_credits=0 — frontend will show only used cost.
        """
        total_cost = 0.0
        currency = "USD"

        for item in data.get("data", []):
            attrs = item.get("attributes", {})
            cost = attrs.get("total_cost", attrs.get("cost", {}))
            if isinstance(cost, dict):
                total_cost += float(cost.get("amount", 0))
            elif isinstance(cost, (int, float)):
                total_cost += float(cost)
            currency = attrs.get("currency", currency)

        logger.info(
            "Claude cost report: total_cost=%.2f %s (no credit limit available)",
            total_cost, currency,
        )

        return StandardUsageData(
            total_credits=0.0,       # Not available via cost_report
            used_credits=total_cost,
            remaining_credits=0.0,
            currency=currency,
        )

    @staticmethod
    async def _get_json(client, path):
        try:
            r = await client.get(path)
            if r.status_code == 200:
                return r.json()
            logger.warning(
                "Claude API %s returned %d: %s",
                path, r.status_code, r.text[:200],
            )
            return None
        except Exception as e:
            logger.error("Claude API %s error: %s", path, e)
            return None
