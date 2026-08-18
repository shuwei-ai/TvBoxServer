from typing import Optional

from pydantic import BaseModel, Field, field_validator


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=72)
    invite_code: Optional[str] = None

    @field_validator("username")
    @classmethod
    def valid_username(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized.replace("_", "").replace("-", "").isalnum():
            raise ValueError("用户名只能包含字母、数字、下划线和连字符")
        return normalized


class LoginRequest(BaseModel):
    username: str
    password: str


class WxSessionCreateRequest(BaseModel):
    biz_state: Optional[str] = Field(default="tvbox-web-login", max_length=128)
    expire_seconds: Optional[int] = Field(default=300, ge=60, le=600)


class WxAuthCompleteRequest(BaseModel):
    session_no: str = Field(min_length=1, max_length=128)
    invite_code: Optional[str] = None


class DeviceBindRequest(BaseModel):
    device_id: str = Field(min_length=3, max_length=128)
    device_name: str = Field(min_length=1, max_length=64)


class DeviceUpdateRequest(BaseModel):
    device_name: Optional[str] = Field(default=None, min_length=1, max_length=64)
    is_default: Optional[bool] = None


class UserStatusRequest(BaseModel):
    status: int = Field(ge=0, le=1)


class SystemConfigRequest(BaseModel):
    allow_user_registration: bool
    require_invite_code: bool
    max_invites_per_user: int = Field(ge=0, le=100)
    max_registered_users: int = Field(ge=1, le=100000)
    max_devices_per_user: int = Field(ge=1, le=1000)


class AdminInviteRequest(BaseModel):
    count: int = Field(ge=1, le=20)
