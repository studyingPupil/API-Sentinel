"""API Key encryption.

Uses Fernet (cryptography) when available.
Falls back to base64 obfuscation for environments without cryptography.
"""
import base64
import logging
import os

logger = logging.getLogger(__name__)

try:
    from cryptography.fernet import Fernet
    HAS_FERNET = True
except ImportError:
    HAS_FERNET = False
    logger.warning("cryptography not installed — using base64 obfuscation. "
                   "Install cryptography for production use.")

_fernet = None
_fernet_key = ""


def _get_fernet():
    global _fernet
    if _fernet is None:
        from app.config import ENCRYPTION_KEY
        key = ENCRYPTION_KEY
        if not key:
            key = Fernet.generate_key().decode()
            logger.warning(
                "No ENCRYPTION_KEY set. Generated ephemeral key: %s\n"
                "Set this in your environment to persist encrypted API keys "
                "across restarts.", key
            )
        _fernet = Fernet(key.encode() if isinstance(key, str) else key)
    return _fernet


def encrypt(plaintext: str) -> str:
    if HAS_FERNET:
        return _get_fernet().encrypt(plaintext.encode()).decode()
    else:
        return base64.b64encode(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    if HAS_FERNET:
        return _get_fernet().decrypt(ciphertext.encode()).decode()
    else:
        try:
            return base64.b64decode(ciphertext.encode()).decode()
        except Exception:
            return ciphertext
