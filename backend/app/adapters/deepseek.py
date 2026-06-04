"""DeepSeek Adapter — fetches balance from DeepSeek Platform API."""
import logging

from app.adapters.base import BaseProviderAdapter, StandardUsageData

logger = logging.getLogger(__name__)

BASE_URL = "https://api.deepseek.com"


class DeepSeekAdapter(BaseProviderAdapter):
    provider_name = "deepseek"

    async def fetch_usage(self, api_key):
        import httpx
        async with httpx.AsyncClient(
            base_url=BASE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
            },
            timeout=30.0,
        ) as client:
            r = await client.get("/user/balance")
            if r.status_code != 200:
                raise RuntimeError(
                    f"DeepSeek balance API returned {r.status_code}: {r.text[:200]}"
                )

            data = r.json()
            if not data.get("is_available"):
                raise RuntimeError("DeepSeek account balance not available. "
                                   "Check billing settings.")

            balance_info = data.get("balance_infos", [{}])[0]
            total_balance = float(balance_info.get("total_balance", "0"))
            currency = balance_info.get("currency", "CNY")

            # DeepSeek only provides current balance, no total_credits or used_credits
            return StandardUsageData(
                total_credits=0.0,
                used_credits=0.0,
                remaining_credits=total_balance,
                currency=currency,
            )

    async def validate_key(self, api_key):
        try:
            import httpx
            async with httpx.AsyncClient(
                base_url=BASE_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10.0,
            ) as client:
                r = await client.get("/user/balance")
                return r.status_code == 200
        except Exception:
            return False
