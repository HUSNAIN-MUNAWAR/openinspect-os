from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import pbkdf2_hmac
import hmac
import secrets
import jwt
from .config import settings

_ITERATIONS = 310_000


def hash_password(value: str) -> str:
    """PBKDF2-SHA256 password hash with a per-user random salt."""
    salt = secrets.token_bytes(16)
    digest = pbkdf2_hmac("sha256", value.encode("utf-8"), salt, _ITERATIONS)
    return f"pbkdf2_sha256${_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(value: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        candidate = pbkdf2_hmac("sha256", value.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations))
        return hmac.compare_digest(candidate.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def create_access_token(subject: str, organization_id: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": subject, "org": organization_id, "role": role, "iat": now, "exp": now + timedelta(minutes=settings.access_token_minutes)}
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    return token.decode("utf-8") if isinstance(token, bytes) else token
