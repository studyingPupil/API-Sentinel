"""Telegram Bot notifier."""
import logging

from app.notifiers.base import BaseNotifier

logger = logging.getLogger(__name__)


class TelegramNotifier(BaseNotifier):
    channel_type = "telegram"

    async def send(self, message, config):
        token = config.get("bot_token", "")
        chat_id = config.get("chat_id", "")
        if not token or not chat_id:
            logger.error("Telegram config missing bot_token or chat_id")
            return False

        import httpx
        url = "https://api.telegram.org/bot{}/sendMessage".format(token)
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post(url, json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "Markdown",
                })
                if r.status_code == 200:
                    logger.info("Telegram message sent to %s", chat_id)
                    return True
                logger.error("Telegram API returned %d: %s",
                             r.status_code, r.text[:200])
                return False
        except Exception as e:
            logger.error("Telegram send failed: %s", e)
            return False
