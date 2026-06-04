"""ProviderRegistry — global adapter lookup."""
from app.adapters.openai import OpenAIAdapter
from app.adapters.deepseek import DeepSeekAdapter
from app.adapters.claude import ClaudeAdapter
from app.adapters.glm import GLMAdapter


class ProviderRegistry:
    """Registry of Provider Adapters, keyed by provider_name."""

    _adapters = {}

    @classmethod
    def register(cls, adapter):
        cls._adapters[adapter.provider_name] = adapter

    @classmethod
    def get(cls, name):
        if name not in cls._adapters:
            raise ValueError("Unknown provider: {}".format(name))
        return cls._adapters[name]

    @classmethod
    def list_providers(cls):
        return list(cls._adapters.keys())

    @classmethod
    def is_registered(cls, name):
        return name in cls._adapters


# Register all available adapters on import
ProviderRegistry.register(OpenAIAdapter())
ProviderRegistry.register(DeepSeekAdapter())
ProviderRegistry.register(ClaudeAdapter())
ProviderRegistry.register(GLMAdapter())
