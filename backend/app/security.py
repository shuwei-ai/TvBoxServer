import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
import jwt

from .config import Settings, settings


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str) -> str:
    if not 8 <= len(password.encode("utf-8")) <= 72:
        raise ValueError("密码长度必须为 8~72 字节")
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("ascii"))
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: str, username: str, role: str, config: Settings = settings) -> str:
    now = utcnow()
    payload: Dict[str, Any] = {
        "sub": user_id,
        "username": username,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=config.jwt_expire_minutes),
        "type": "access",
    }
    return jwt.encode(payload, config.jwt_secret, algorithm=config.jwt_algorithm)


def decode_access_token(token: str, config: Settings = settings) -> Dict[str, Any]:
    payload = jwt.decode(token, config.jwt_secret, algorithms=[config.jwt_algorithm])
    if payload.get("type") != "access" or not payload.get("sub"):
        raise jwt.InvalidTokenError("invalid access token")
    return payload


def generate_api_key() -> str:
    return "sk-tvbox-" + secrets.token_urlsafe(32)


def api_key_prefix(api_key: str) -> str:
    return api_key[:18]


def digest_api_key(api_key: str, config: Settings = settings) -> str:
    return hmac.new(config.api_key_pepper.encode("utf-8"), api_key.encode("utf-8"), hashlib.sha256).hexdigest()


def secure_equal(left: Optional[str], right: Optional[str]) -> bool:
    return bool(left and right and hmac.compare_digest(left, right))
