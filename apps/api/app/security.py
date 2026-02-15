import base64
import hashlib
import hmac
import json
import os
import time

SECRET_KEY = os.getenv("APP_SECRET_KEY", "change-me")


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hmac.compare_digest(hash_password(password), password_hash)


def create_access_token(user_id: int, email: str, expires_minutes: int = 60 * 24) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": int(time.time()) + (expires_minutes * 60),
    }
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    body = base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")
    signature = hmac.new(SECRET_KEY.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{body}.{signature}"


def decode_access_token(token: str) -> dict:
    try:
        body, signature = token.split(".", 1)
    except ValueError as exc:
        raise ValueError("invalid token format") from exc

    expected = hmac.new(SECRET_KEY.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise ValueError("invalid token signature")

    padded_body = body + "=" * (-len(body) % 4)
    payload_raw = base64.urlsafe_b64decode(padded_body.encode("utf-8"))
    payload = json.loads(payload_raw.decode("utf-8"))

    if int(payload["exp"]) < int(time.time()):
        raise ValueError("token expired")

    return payload
