"""GLM (Zhipu AI) Adapter — manual balance input mode.

Zhipu open platform does not provide a public billing REST API.
Users manually enter their balance from the console.
See Phase 0 verification: FIELD_MAPPING.md
"""
import logging

from app.adapters.base import BaseProviderAdapter, StandardUsageData

logger = logging.getLogger(__name__)


class GLMAdapter(BaseProviderAdapter):
    provider_name = "glm"
    is_manual = True

    async def fetch_usage(self, api_key):
        """GLM has no billing API. Balance must be set manually."""
        logger.warning(
            "GLM adapter is manual-only. Use POST /api/credentials/{id}/manual-balance "
            "to set the current balance."
        )
        return StandardUsageData(
            total_credits=0.0,
            used_credits=0.0,
            remaining_credits=0.0,
            currency="CNY",
        )

    async def validate_key(self, api_key):
        """Test key validity via the GLM models list endpoint."""
        try:
            import httpx
            async with httpx.AsyncClient(
                base_url="https://open.bigmodel.cn",
                headers={"Authorization": "Bearer " + api_key},
                timeout=10.0,
            ) as client:
                r = await client.get("/api/paas/v4/models")
                return r.status_code == 200
        except Exception:
            return False
