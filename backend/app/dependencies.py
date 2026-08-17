from dataclasses import dataclass
from typing import Any, Dict, Optional

from fastapi import Depends, Header, HTTPException, Request, status

from .repository import Repository
from .security import decode_access_token


@dataclass
class DeviceCredential:
    key: Dict[str, Any]
    user: Dict[str, Any]


def bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    scheme, separator, token = authorization.partition(" ")
    return token.strip() if separator and scheme.lower() == "bearer" else None


def get_repository(request: Request) -> Repository:
    return request.app.state.repository


async def current_user(
    authorization: Optional[str] = Header(default=None), repository: Repository = Depends(get_repository)
) -> Dict[str, Any]:
    token = bearer_token(authorization)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing access token", headers={"WWW-Authenticate": "Bearer"})
    try:
        claims = decode_access_token(token, repository.config)
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired access token", headers={"WWW-Authenticate": "Bearer"})
    user = await repository.get_user(str(claims["sub"]))
    if not user or user["status"] != 1:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "User is disabled")
    return user


async def admin_user(user: Dict[str, Any] = Depends(current_user)) -> Dict[str, Any]:
    if user["role"] != "ADMIN":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Administrator role required")
    return user


async def device_credential(
    authorization: Optional[str] = Header(default=None), repository: Repository = Depends(get_repository)
) -> DeviceCredential:
    raw = bearer_token(authorization)
    if not raw:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing API key", headers={"WWW-Authenticate": "Bearer"})
    result = await repository.authenticate_api_key(raw)
    if not result:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or revoked API key", headers={"WWW-Authenticate": "Bearer"})
    if result[1]["status"] != 1:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "API key owner is disabled")
    return DeviceCredential(key=result[0], user=result[1])
