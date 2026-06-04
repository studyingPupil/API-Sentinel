"""Provider Adapter abstract base."""
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class StandardUsageData:
    """All Provider Adapters must return this unified format."""
    total_credits: float
    used_credits: float
    remaining_credits: float
    currency: str = "USD"
    fetched_at: str = ""

    def __post_init__(self):
        if not self.fetched_at:
            self.fetched_at = datetime.utcnow().isoformat()

    def to_dict(self):
        return asdict(self)


class BaseProviderAdapter:
    """Abstract base for all Provider Adapters."""

    provider_name: str = ""
    is_manual = False  # True if provider has no billing API (e.g. GLM)

    async def fetch_usage(self, api_key: str) -> StandardUsageData:
        """Fetch usage/billing data. Must be implemented per provider."""
        raise NotImplementedError

    async def validate_key(self, api_key: str) -> bool:
        """Quick check whether the API key is valid."""
        raise NotImplementedError
