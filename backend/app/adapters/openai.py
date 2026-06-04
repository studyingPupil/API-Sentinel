"""OpenAI Adapter — fetches billing data from OpenAI Dashboard API."""
import logging
from datetime import datetime, timedelta

from app.adapters.base import BaseProviderAdapter, StandardUsageData

logger = logging.getLogger(__name__)

BASE_URL = "https://api.openai.com"


class OpenAIAdapter(BaseProviderAdapter):
    provider_name = "openai"

    async def fetch_usage(self, api_key):
        import httpx
        async with httpx.AsyncClient(
            base_url=BASE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        ) as client:
            # 1. Get subscription (gives hard_limit_usd, soft_limit_usd)
            sub = await self._get_json(client, "/v1/dashboard/billing/subscription")
            if sub is None:
                raise RuntimeError("Failed to fetch subscription. "
                                   "API key may lack billing permissions.")

            # 2. Get billing usage (gives total_usage in cents)
            end = datetime.now().strftime("%Y-%m-%d")
            start = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
            usage = await self._get_json(
                client,
                f"/v1/dashboard/billing/usage?start_date={start}&end_date={end}",
            )
            if usage is None:
                raise RuntimeError("Failed to fetch billing usage.")

            hard_limit = float(sub.get("hard_limit_usd", 0))
            total_usage = float(usage.get("total_usage", 0)) / 100.0
            remaining = max(0.0, hard_limit - total_usage)

            return StandardUsageData(
                total_credits=hard_limit,
                used_credits=total_usage,
                remaining_credits=remaining,
                currency="USD",
            )

    async def validate_key(self, api_key):
        """Lightweight check: call the models list endpoint."""
        try:
            import httpx
            async with httpx.AsyncClient(
                base_url=BASE_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10.0,
            ) as client:
                r = await client.get("/v1/models")
                return r.status_code == 200
        except Exception:
            return False

    @staticmethod
    async def _get_json(client, path):
        try:
            r = await client.get(path)
            if r.status_code == 200:
                return r.json()
            logger.warning("OpenAI API %s returned %d: %s", path, r.status_code, r.text[:200])
            return None
        except Exception as e:
            logger.error("OpenAI API %s error: %s", path, e)
            return None
