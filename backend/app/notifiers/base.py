"""Notification channel abstract base."""
from dataclasses import dataclass
from enum import IntEnum


class AlertLevel(IntEnum):
    INFO = 1      # 3 days
    WARNING = 2   # 24 hours
    CRITICAL = 3  # 6 hours


@dataclass
class AlertContext:
    """Data passed to notifier for message templating."""
    provider: str
    alias: str
    remaining_credits: float
    currency: str
    daily_avg: float
    predicted_days: float
    predicted_date: str
    level: AlertLevel


class BaseNotifier:
    """Abstract base for notification channels."""

    channel_type: str = ""

    async def send(self, message: str, config: dict) -> bool:
        """Send a notification. Returns True on success."""
        raise NotImplementedError

    async def test(self, config: dict) -> bool:
        """Send a test message to verify the config works."""
        return await self.send(
            "[API Sentinel] Test notification. Your notification channel is configured correctly.",
            config,
        )

    @staticmethod
    def build_message(ctx: AlertContext) -> str:
        """Build notification message from alert context."""
        remaining = f"{ctx.currency} {ctx.remaining_credits:.2f}"
        days = f"{ctx.predicted_days:.1f}"

        if ctx.level == AlertLevel.INFO:
            return (
                "[API Sentinel] {0} ({1}) — Low Balance / 额度不足\n\n"
                "Your {0} API key \"{1}\" will run out around {2} (approx. {3} days).\n"
                "{0} API Key \"{1}\" 预计在 {2} 左右耗尽 (约 {3} 天)。\n\n"
                "Remaining / 剩余: {4}\n"
                "Daily avg / 日均: {5} {6:.2f}\n\n"
                "— API Sentinel"
            ).format(ctx.provider, ctx.alias, ctx.predicted_date, days,
                     remaining, ctx.currency, ctx.daily_avg)
        elif ctx.level == AlertLevel.WARNING:
            return (
                "[API Sentinel] {0} ({1}) — Balance Warning / 额度警告\n\n"
                "Your {0} API key \"{1}\" will run out within 24 hours (est. {2}).\n"
                "{0} API Key \"{1}\" 预计在 24 小时内耗尽 ({2})。\n\n"
                "Remaining / 剩余: {3}\n"
                "Daily avg / 日均: {4} {5:.2f}\n\n"
                "Top up now / 请尽快充值。\n\n"
                "— API Sentinel"
            ).format(ctx.provider, ctx.alias, ctx.predicted_date,
                     remaining, ctx.currency, ctx.daily_avg)
        else:  # CRITICAL
            return (
                "[API Sentinel] URGENT / 紧急: {0} ({1}) — Balance Critical\n\n"
                "Your {0} API key \"{1}\" will run out within 6 hours (est. {2})!\n"
                "{0} API Key \"{1}\" 预计在 6 小时内耗尽 ({2})！\n\n"
                "Remaining / 剩余: {3}\n"
                "Daily avg / 日均: {4} {5:.2f}\n\n"
                "IMMEDIATE ACTION / 立即充值！\n\n"
                "— API Sentinel"
            ).format(ctx.provider, ctx.alias, ctx.predicted_date,
                     remaining, ctx.currency, ctx.daily_avg)
