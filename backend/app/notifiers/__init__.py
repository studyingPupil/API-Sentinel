"""Notification channel registry."""
from app.notifiers.base import BaseNotifier, AlertLevel, AlertContext
from app.notifiers.email import EmailNotifier
from app.notifiers.telegram import TelegramNotifier
from app.notifiers.feishu import FeishuNotifier
from app.notifiers.wecom import WeComNotifier


NOTIFIERS = {
    "email": EmailNotifier(),
    "telegram": TelegramNotifier(),
    "feishu": FeishuNotifier(),
    "wecom": WeComNotifier(),
}


def get_notifier(channel_type: str) -> BaseNotifier:
    if channel_type not in NOTIFIERS:
        raise ValueError(f"Unknown channel type: {channel_type}")
    return NOTIFIERS[channel_type]
