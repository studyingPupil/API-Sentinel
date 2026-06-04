"""Feishu (Lark) Webhook notifier."""
import logging

from app.notifiers.base import BaseNotifier

logger = logging.getLogger(__name__)


class FeishuNotifier(BaseNotifier):
    channel_type = "feishu"

    async def send(self, message, config):
        webhook_url = config.get("webhook_url", "")
        if not webhook_url:
            logger.error("Feishu config missing webhook_url")
            return False

        import httpx

        title_line = message.split("\n")[0] if message else "[API Sentinel]"
        body = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": title_line},
                    "template": "red" if "URGENT" in message else "yellow",
                },
                "elements": [
                    {"tag": "markdown", "content": message.replace("\n", "\n\n")}
                ],
            },
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post(webhook_url, json=body)
                if r.status_code == 200:
                    logger.info("Feishu notification sent")
                    return True
                logger.error("Feishu webhook returned %d: %s",
                             r.status_code, r.text[:200])
                return False
        except Exception as e:
            logger.error("Feishu send failed: %s", e)
            return False
