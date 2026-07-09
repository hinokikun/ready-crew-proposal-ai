import base64
import hashlib
import hmac
import os
import time

from app.config import settings


def _b64_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return f"pbkdf2_sha256${_b64_encode(salt)}${_b64_encode(digest)}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, encoded_salt, encoded_digest = password_hash.split("$", 2)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = _b64_decode(encoded_salt)
        expected = _b64_decode(encoded_digest)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def create_auth_token(user_id: int, email: str, role: str) -> str:
    issued_at = str(int(time.time()))
    payload = f"{user_id}|{email}|{role}|{issued_at}"
    signature = hmac.new(settings.app_auth_secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).digest()
    return f"{_b64_encode(payload.encode('utf-8'))}.{_b64_encode(signature)}"


def verify_auth_token(token: str) -> dict[str, str | int] | None:
    if not settings.app_auth_secret or "." not in token:
        return None
    encoded_payload, encoded_signature = token.split(".", 1)
    try:
        payload = _b64_decode(encoded_payload).decode("utf-8")
        user_id, email, role, issued_at = payload.split("|", 3)
        expected = hmac.new(settings.app_auth_secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).digest()
        provided = _b64_decode(encoded_signature)
    except Exception:
        return None
    if not hmac.compare_digest(expected, provided):
        return None
    if int(time.time()) - int(issued_at) > settings.app_auth_token_ttl_seconds:
        return None
    return {"id": int(user_id), "email": email, "role": role}
