"""WeCom (Enterprise WeChat) Webhook notifier."""
import logging

from app.notifiers.base import BaseNotifier

logger = logging.getLogger(__name__)


class WeComNotifier(BaseNotifier):
    channel_type = "wecom"

    async def send(self, message, config):
        webhook_url = config.get("webhook_url", "")
        if not webhook_url:
            logger.error("WeCom config missing webhook_url")
            return False

        import httpx

        body = {
            "msgtype": "markdown",
            "markdown": {"content": message},
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post(webhook_url, json=body)
                if r.status_code == 200:
                    resp = r.json()
                    if resp.get("errcode") == 0:
                        logger.info("WeCom notification sent")
                        return True
                    logger.error("WeCom webhook error: %s", r.text[:200])
                    return False
                logger.error("WeCom webhook returned %d: %s",
                             r.status_code, r.text[:200])
                return False
        except Exception as e:
            logger.error("WeCom send failed: %s", e)
            return False
