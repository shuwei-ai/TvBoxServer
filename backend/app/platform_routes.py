from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from .dependencies import admin_user, current_user, get_repository
from .repository import ConflictError, QuotaError, Repository, public
from .schemas import AdminInviteRequest, DeviceBindRequest, DeviceUpdateRequest, LoginRequest, RegisterRequest, SystemConfigRequest, UserStatusRequest
from .security import create_access_token


router = APIRouter(prefix="/api/v1")


def response(data: Any = None, message: str = "success") -> Dict[str, Any]:
    return {"code": 0, "message": message, "data": data}


def token_data(user: Dict[str, Any], repository: Repository) -> Dict[str, Any]:
    token = create_access_token(user["_id"], user["username"], user["role"], repository.config)
    return {"access_token": token, "token_type": "bearer", "user": public(user)}


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, repository: Repository = Depends(get_repository)):
    try:
        user = await repository.register(body.username, body.password, body.invite_code)
    except QuotaError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc))
    except ConflictError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc))
    return response(token_data(user, repository), "注册成功")


@router.post("/auth/login")
async def login(body: LoginRequest, repository: Repository = Depends(get_repository)):
    user = await repository.authenticate_user(body.username, body.password)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户名或密码错误")
    return response(token_data(user, repository), "登录成功")


@router.get("/invite/my-codes")
async def my_invites(user=Depends(current_user), repository: Repository = Depends(get_repository)):
    items = await repository.list_invites(user["_id"])
    config = await repository.get_config()
    return response({"max_invites": config["max_invites_per_user"], "remaining_quota": max(0, config["max_invites_per_user"] - len(items)), "codes": [public(x) for x in items]})


@router.post("/invite/generate")
async def generate_invite(user=Depends(current_user), repository: Repository = Depends(get_repository)):
    try:
        items = await repository.create_invites(user, 1)
    except QuotaError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    return response(public(items[0]), "邀请码生成成功")


@router.get("/devices")
async def devices(user=Depends(current_user), repository: Repository = Depends(get_repository)):
    items = await repository.list_devices(user["_id"])
    key = await repository.get_active_api_key(user["_id"])
    manager = getattr(repository, "device_manager", None)
    visible = []
    for item in items:
        value = public(item)
        state = manager.device_states.get((user["_id"], item["device_id"]), {}) if manager else {}
        value.update({"online": state.get("online", False), "current_activity": state.get("current_activity")})
        visible.append(value)
    return response({"devices": visible, "api_key": public(key)})


@router.post("/devices/bind", status_code=status.HTTP_201_CREATED)
async def bind_device(body: DeviceBindRequest, user=Depends(current_user), repository: Repository = Depends(get_repository)):
    try:
        device, raw_key = await repository.bind_device(user["_id"], body.device_id, body.device_name)
    except QuotaError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc))
    except ConflictError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    data = {"device": public(device), "api_key": raw_key}
    return response(data, "设备绑定成功")


@router.delete("/devices/{record_id}")
async def delete_device(record_id: str, user=Depends(current_user), repository: Repository = Depends(get_repository)):
    deleted = await repository.delete_device(user["_id"], record_id)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "设备不存在")
    manager = getattr(repository, "device_manager", None)
    if manager:
        await manager.disconnect_device(user["_id"], deleted["device_id"], "Device unbound")
    return response(message="设备已解绑")


@router.put("/devices/{record_id}")
async def update_device(record_id: str, body: DeviceUpdateRequest, user=Depends(current_user), repository: Repository = Depends(get_repository)):
    device = await repository.update_device(user["_id"], record_id, body.model_dump())
    if not device:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "设备不存在")
    return response(public(device), "设备已更新")


@router.get("/api-key")
async def api_key_status(user=Depends(current_user), repository: Repository = Depends(get_repository)):
    return response(public(await repository.get_active_api_key(user["_id"])))


@router.post("/api-key/reset")
async def reset_api_key(user=Depends(current_user), repository: Repository = Depends(get_repository)):
    key, raw, revoked = await repository.rotate_api_key(user["_id"])
    manager = getattr(repository, "device_manager", None)
    if manager:
        await manager.disconnect_user(user["_id"], "API key rotated")
    return response({"api_key": raw, "key": public(key), "revoked_key_ids": revoked}, "API Key 刷新成功")


@router.get("/admin/users")
async def admin_users(_admin=Depends(admin_user), repository: Repository = Depends(get_repository)):
    users = await repository.list_users()
    result = []
    for user in users:
        item = public(user)
        item["device_count"] = len(await repository.list_devices(user["_id"]))
        result.append(item)
    return response({"total_users": len(result), "users": result})


@router.put("/admin/users/{user_id}/status")
async def admin_set_status(user_id: str, body: UserStatusRequest, _admin=Depends(admin_user), repository: Repository = Depends(get_repository)):
    user = await repository.set_user_status(user_id, body.status)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "用户不存在")
    if body.status == 0 and getattr(repository, "device_manager", None):
        await repository.device_manager.disconnect_user(user_id, "User disabled")
    return response(public(user), "用户状态已更新")


@router.post("/admin/invite/generate")
async def admin_generate_invites(body: AdminInviteRequest, admin=Depends(admin_user), repository: Repository = Depends(get_repository)):
    items = await repository.create_invites(admin, body.count)
    return response({"codes": [x["code"] for x in items]}, "系统邀请码生成成功")


@router.get("/admin/invite/codes")
async def admin_invites(_admin=Depends(admin_user), repository: Repository = Depends(get_repository)):
    return response([public(x) for x in await repository.list_invites()])


@router.get("/admin/devices")
async def admin_devices(_admin=Depends(admin_user), repository: Repository = Depends(get_repository)):
    result = []
    for user in await repository.list_users():
        for device in await repository.list_devices(user["_id"]):
            item = public(device)
            item["owner_username"] = user["username"]
            item["owner_user_id"] = user["_id"]
            manager = getattr(repository, "device_manager", None)
            state = manager.device_states.get((user["_id"], device["device_id"]), {}) if manager else {}
            item.update({"online": state.get("online", False), "current_activity": state.get("current_activity")})
            result.append(item)
    return response(result)


@router.get("/admin/system/config")
async def admin_config(_admin=Depends(admin_user), repository: Repository = Depends(get_repository)):
    config = public(await repository.get_config())
    config["current_registered_users"] = await repository.count_users("USER")
    config["remaining_quota"] = max(0, config["max_registered_users"] - config["current_registered_users"])
    return response(config)


@router.put("/admin/system/config")
async def admin_update_config(body: SystemConfigRequest, admin=Depends(admin_user), repository: Repository = Depends(get_repository)):
    config = await repository.update_config(body.model_dump(), admin["_id"])
    return response(public(config), "系统配置更新成功")
