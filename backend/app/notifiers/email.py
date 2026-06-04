"""Email notifier — supports provider_type templates + encrypted password."""
import json
import logging
import os

from app.notifiers.base import BaseNotifier

logger = logging.getLogger(__name__)

# Load provider templates
_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "email_providers.json")
with open(_TEMPLATE_PATH, "r", encoding="utf-8") as f:
    EMAIL_PROVIDERS = json.load(f)


class EmailNotifier(BaseNotifier):
    channel_type = "email"

    @staticmethod
    def get_providers():
        """Return list of available email provider types for frontend."""
        return [
            {"value": k, "label": v["label"],
             "smtp_host": v["smtp_host"], "smtp_port": v["smtp_port"]}
            for k, v in EMAIL_PROVIDERS.items()
        ]

    @staticmethod
    def resolve_smtp(config):
        """Resolve SMTP host/port from config.

        Supports two formats:
          New:  {"provider_type":"qq", "username":"...", "password":"...", "to_email":"..."}
          Old:  {"smtp_host":"...", "smtp_port":"587", "smtp_user":"...", "smtp_password":"...", "to_email":"..."}
        """
        provider_type = config.get("provider_type", "")

        if provider_type and provider_type in EMAIL_PROVIDERS and provider_type != "custom":
            tpl = EMAIL_PROVIDERS[provider_type]
            return {
                "smtp_host": tpl["smtp_host"],
                "smtp_port": tpl["smtp_port"],
                "username": config.get("username", ""),
                "password": _decrypt_password(config.get("password", "")),
                "to_email": config.get("to_email", config.get("username", "")),
            }
        elif provider_type == "custom":
            return {
                "smtp_host": config.get("smtp_host", ""),
                "smtp_port": int(config.get("smtp_port", 587)),
                "username": config.get("username", ""),
                "password": _decrypt_password(config.get("password", "")),
                "to_email": config.get("to_email", config.get("username", "")),
            }
        else:
            # Backward compatibility: old format without provider_type
            return {
                "smtp_host": config.get("smtp_host", ""),
                "smtp_port": int(config.get("smtp_port", 587)),
                "username": config.get("smtp_user", config.get("username", "")),
                "password": _decrypt_password(
                    config.get("smtp_password", config.get("password", ""))
                ),
                "to_email": config.get("to_email", ""),
            }

    async def send(self, message, config):
        try:
            import aiosmtplib
            from email.mime.text import MIMEText
        except ImportError:
            logger.error("aiosmtplib not installed")
            return False

        smtp = self.resolve_smtp(config)
        if not smtp["smtp_host"] or not smtp["username"]:
            logger.error("Email config incomplete: host=%s user=%s",
                         smtp["smtp_host"], smtp["username"])
            return False

        try:
            msg = MIMEText(message, "plain", "utf-8")
            msg["Subject"] = (
                message.split("\n")[0] if message else "[API Sentinel]"
            )
            msg["From"] = smtp["username"]
            msg["To"] = smtp["to_email"]

            await aiosmtplib.send(
                msg,
                hostname=smtp["smtp_host"],
                port=smtp["smtp_port"],
                username=smtp["username"],
                password=smtp["password"],
                start_tls=True,
            )
            logger.info("Email sent to %s via %s:%d",
                        smtp["to_email"], smtp["smtp_host"], smtp["smtp_port"])
            return True
        except Exception as e:
            logger.error("Email send failed: %s", e)
            return False


def encrypt_email_password(plain_password):
    """Encrypt email password before storing in config_json."""
    if not plain_password:
        return plain_password
    # Use the same Fernet encryption as API keys
    from app.crypto import encrypt
    return encrypt(plain_password)


def _decrypt_password(stored_password):
    """Decrypt email password. Tries Fernet first, falls back to plaintext."""
    if not stored_password:
        return stored_password
    try:
        from app.crypto import decrypt
        return decrypt(stored_password)
    except Exception:
        # If decryption fails, it's probably stored as plaintext (old format)
        return stored_password
