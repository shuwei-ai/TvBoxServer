import asyncio
import secrets
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from pymongo import ASCENDING, AsyncMongoClient, ReturnDocument
from pymongo.errors import DuplicateKeyError, OperationFailure

from .config import Settings, settings
from .security import api_key_prefix, digest_api_key, generate_api_key, hash_password, verify_password


def now() -> datetime:
    return datetime.now(timezone.utc)


def public(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not doc:
        return None
    value = deepcopy(doc)
    value["id"] = str(value.pop("_id"))
    value.pop("password_hash", None)
    value.pop("key_hash", None)
    return value


class ConflictError(Exception):
    pass


class QuotaError(Exception):
    pass


class Repository:
    """Mongo-backed repository with an in-memory mode for tests/local startup."""

    DEFAULT_CONFIG = {
        "_id": "global_settings", "allow_user_registration": True,
        "require_invite_code": True, "max_invites_per_user": 3,
        "max_registered_users": 50, "max_devices_per_user": 5, "registered_user_count": 0,
    }

    def __init__(self, config: Settings = settings, force_memory: bool = False):
        self.config = config
        self.client = None
        self.db = None
        if config.mongo_uri and not force_memory:
            self.client = AsyncMongoClient(config.mongo_uri)
            self.db = self.client[config.mongo_database]
        self._lock = asyncio.Lock()
        self._users: Dict[str, Dict[str, Any]] = {}
        self._invites: Dict[str, Dict[str, Any]] = {}
        self._keys: Dict[str, Dict[str, Any]] = {}
        self._devices: Dict[str, Dict[str, Any]] = {}
        self._config = deepcopy(self.DEFAULT_CONFIG)

    async def _safe_create_index(self, collection: Any, keys: Any, **kwargs: Any) -> None:
        try:
            await collection.create_index(keys, **kwargs)
        except OperationFailure as exc:
            if exc.code in (85, 86) or "IndexKeySpecsConflict" in str(exc) or "IndexOptionsConflict" in str(exc):
                index_name = kwargs.get("name")
                if not index_name:
                    if isinstance(keys, list):
                        index_name = "_".join(f"{k}_{v}" for k, v in keys)
                    elif isinstance(keys, str):
                        index_name = f"{keys}_1"
                if index_name:
                    try:
                        await collection.drop_index(index_name)
                    except OperationFailure:
                        pass
                await collection.create_index(keys, **kwargs)
            else:
                raise

    async def initialize(self) -> None:
        if self.db is None:
            await self._bootstrap_admin()
            return
        await self._safe_create_index(self.db.users, [("openid", ASCENDING)], unique=True, sparse=True)
        await self._safe_create_index(self.db.users, [("username", ASCENDING)], unique=True, sparse=True)
        await self._safe_create_index(self.db.invite_codes, [("code", ASCENDING)], unique=True)
        await self._safe_create_index(self.db.invite_codes, [("created_by", ASCENDING)])
        await self._safe_create_index(self.db.api_keys, [("key_hash", ASCENDING)], unique=True)
        await self._safe_create_index(self.db.api_keys, [("user_id", ASCENDING), ("status", ASCENDING)])
        await self._safe_create_index(
            self.db.api_keys, [("user_id", ASCENDING)], unique=True, partialFilterExpression={"status": "ACTIVE"}, name="one_active_key_per_user"
        )
        await self._safe_create_index(self.db.devices, [("device_id", ASCENDING)], unique=True)
        await self._safe_create_index(self.db.devices, [("user_id", ASCENDING)])
        await self.db.system_configs.update_one(
            {"_id": "global_settings"}, {"$setOnInsert": deepcopy(self.DEFAULT_CONFIG)}, upsert=True
        )
        actual_users = await self.db.users.count_documents({"role": "USER"})
        await self.db.system_configs.update_one({"_id": "global_settings"}, {"$set": {"registered_user_count": actual_users}})
        async for existing_user in self.db.users.find({}, {"_id": 1}):
            device_count = await self.db.devices.count_documents({"user_id": existing_user["_id"]})
            invite_count = await self.db.invite_codes.count_documents({"created_by": existing_user["_id"]})
            await self.db.users.update_one({"_id": existing_user["_id"]}, {"$set": {"device_count": device_count, "invite_generated_count": invite_count}})
        await self._bootstrap_admin()

    async def close(self) -> None:
        if self.client is not None:
            await self.client.close()

    async def _bootstrap_admin(self) -> None:
        if not self.config.bootstrap_admin_username or not self.config.bootstrap_admin_password:
            return
        if await self.get_user_by_username(self.config.bootstrap_admin_username):
            return
        await self.create_user(self.config.bootstrap_admin_username, self.config.bootstrap_admin_password, "ADMIN")

    async def get_config(self) -> Dict[str, Any]:
        if self.db is not None:
            return await self.db.system_configs.find_one({"_id": "global_settings"}) or deepcopy(self.DEFAULT_CONFIG)
        return deepcopy(self._config)

    async def update_config(self, changes: Dict[str, Any], updated_by: str) -> Dict[str, Any]:
        changes = {**changes, "updated_at": now(), "updated_by": updated_by}
        if self.db is not None:
            return await self.db.system_configs.find_one_and_update(
                {"_id": "global_settings"}, {"$set": changes}, return_document=ReturnDocument.AFTER, upsert=True
            )
        self._config.update(changes)
        return deepcopy(self._config)

    async def create_user(self, username: str, password: str, role: str = "USER", invite_code: Optional[str] = None) -> Dict[str, Any]:
        username = username.strip().lower()
        doc = {"_id": uuid.uuid4().hex, "username": username, "password_hash": hash_password(password),
               "role": role, "status": 1, "registered_invite_code": invite_code,
               "device_count": 0, "invite_generated_count": 0, "created_at": now(), "updated_at": now()}
        if self.db is not None:
            try:
                await self.db.users.insert_one(doc)
            except DuplicateKeyError as exc:
                raise ConflictError("用户名已存在") from exc
            return doc
        async with self._lock:
            if any(u["username"] == username for u in self._users.values()):
                raise ConflictError("用户名已存在")
            self._users[doc["_id"]] = doc
        return deepcopy(doc)

    async def register(self, username: str, password: str, invite_code: Optional[str]) -> Dict[str, Any]:
        config = await self.get_config()
        if not config["allow_user_registration"]:
            raise QuotaError("系统当前已暂停新用户注册")
        if self.db is not None:
            reserved_quota = await self.db.system_configs.find_one_and_update(
                {
                    "_id": "global_settings",
                    "allow_user_registration": True,
                    "$expr": {"$lt": [{"$ifNull": ["$registered_user_count", 0]}, "$max_registered_users"]},
                },
                {"$inc": {"registered_user_count": 1}},
                return_document=ReturnDocument.AFTER,
            )
            if not reserved_quota:
                raise QuotaError("系统注册人数已达上限")
            invite = None
            if config["require_invite_code"]:
                invite = await self.db.invite_codes.find_one_and_update(
                    {"code": invite_code, "status": "UNUSED"}, {"$set": {"status": "RESERVED", "reserved_at": now()}},
                    return_document=ReturnDocument.AFTER,
                )
                if not invite:
                    await self.db.system_configs.update_one({"_id": "global_settings"}, {"$inc": {"registered_user_count": -1}})
                    raise ConflictError("无效或已被使用的邀请码")
            try:
                user = await self.create_user(username, password, "USER", invite_code)
            except Exception:
                await self.db.system_configs.update_one({"_id": "global_settings"}, {"$inc": {"registered_user_count": -1}})
                if invite:
                    await self.db.invite_codes.update_one({"_id": invite["_id"], "status": "RESERVED"}, {"$set": {"status": "UNUSED"}, "$unset": {"reserved_at": ""}})
                raise
            if invite:
                await self.db.invite_codes.update_one({"_id": invite["_id"], "status": "RESERVED"}, {"$set": {"status": "USED", "used_by": user["_id"], "used_at": now()}, "$unset": {"reserved_at": ""}})
            return user
        async with self._lock:
            if not self._config["allow_user_registration"]:
                raise QuotaError("系统当前已暂停新用户注册")
            current_users = sum(1 for u in self._users.values() if u["role"] == "USER")
            if current_users >= self._config["max_registered_users"]:
                raise QuotaError("系统注册人数已达上限")
            if any(u["username"] == username.strip().lower() for u in self._users.values()):
                raise ConflictError("用户名已存在")
            invite = self._invites.get(invite_code or "")
            if config["require_invite_code"] and (not invite or invite["status"] != "UNUSED"):
                raise ConflictError("无效或已被使用的邀请码")
            doc = {"_id": uuid.uuid4().hex, "username": username.strip().lower(), "password_hash": hash_password(password),
                   "role": "USER", "status": 1, "registered_invite_code": invite_code, "device_count": 0, "invite_generated_count": 0, "created_at": now(), "updated_at": now()}
            self._users[doc["_id"]] = doc
            self._config["registered_user_count"] = current_users + 1
            if invite:
                invite.update({"status": "USED", "used_by": doc["_id"], "used_at": now()})
            return deepcopy(doc)

    async def count_users(self, role: Optional[str] = None) -> int:
        query = {"role": role} if role else {}
        if self.db is not None:
            return await self.db.users.count_documents(query)
        return sum(1 for u in self._users.values() if not role or u["role"] == role)

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        if self.db is not None:
            return await self.db.users.find_one({"_id": user_id})
        return deepcopy(self._users.get(user_id))

    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        normalized = username.strip().lower()
        if self.db is not None:
            return await self.db.users.find_one({"username": normalized})
        return deepcopy(next((u for u in self._users.values() if u["username"] == normalized), None))

    async def get_user_by_openid(self, openid: str) -> Optional[Dict[str, Any]]:
        if not openid:
            return None
        if self.db is not None:
            return await self.db.users.find_one({"openid": openid})
        return deepcopy(next((u for u in self._users.values() if u.get("openid") == openid), None))

    async def login_or_register_by_openid(
        self,
        openid: str,
        invite_code: Optional[str] = None,
        member_role: Optional[int] = None
    ) -> Dict[str, Any]:
        if not openid:
            raise ValueError("微信 OpenID 不能为空")

        existing = await self.get_user_by_openid(openid)
        if existing:
            if existing.get("status") != 1:
                raise QuotaError("该微信绑定的账号已被禁用，请联系管理员")
            
            is_admin_configured = openid in self.config.admin_openids
            update_data: Dict[str, Any] = {"last_login_at": now(), "updated_at": now()}
            if is_admin_configured and existing.get("role") != "ADMIN":
                update_data["role"] = "ADMIN"
            if member_role is not None:
                update_data["member_role"] = member_role
                
            if self.db is not None:
                return await self.db.users.find_one_and_update(
                    {"_id": existing["_id"]},
                    {"$set": update_data},
                    return_document=ReturnDocument.AFTER
                )
            async with self._lock:
                self._users[existing["_id"]].update(update_data)
                return deepcopy(self._users[existing["_id"]])

        # 新用户注册流程
        config = await self.get_config()
        role = "ADMIN" if openid in self.config.admin_openids else "USER"
        
        # 用户名生成，例如 wx_123456
        suffix = openid[-6:] if len(openid) >= 6 else openid
        username = f"wx_{suffix}"

        if self.db is not None:
            if role != "ADMIN":
                if not config["allow_user_registration"]:
                    raise QuotaError("系统当前已暂停新用户注册")
                reserved_quota = await self.db.system_configs.find_one_and_update(
                    {
                        "_id": "global_settings",
                        "allow_user_registration": True,
                        "$expr": {"$lt": [{"$ifNull": ["$registered_user_count", 0]}, "$max_registered_users"]},
                    },
                    {"$inc": {"registered_user_count": 1}},
                    return_document=ReturnDocument.AFTER,
                )
                if not reserved_quota:
                    raise QuotaError("系统注册人数已达上限")
            
            invite = None
            if config["require_invite_code"] and role != "ADMIN":
                if not invite_code:
                    if role != "ADMIN":
                        await self.db.system_configs.update_one({"_id": "global_settings"}, {"$inc": {"registered_user_count": -1}})
                    raise ConflictError("系统已开启邀请注册模式，请输入邀请码")
                invite = await self.db.invite_codes.find_one_and_update(
                    {"code": invite_code, "status": "UNUSED"},
                    {"$set": {"status": "RESERVED", "reserved_at": now()}},
                    return_document=ReturnDocument.AFTER,
                )
                if not invite:
                    if role != "ADMIN":
                        await self.db.system_configs.update_one({"_id": "global_settings"}, {"$inc": {"registered_user_count": -1}})
                    raise ConflictError("无效或已被使用的邀请码")

            # 确保 username 唯一
            candidate_username = username
            counter = 1
            while await self.db.users.find_one({"username": candidate_username}):
                candidate_username = f"{username}_{secrets.token_hex(2)}"
                counter += 1
                if counter > 5:
                    candidate_username = f"wx_{uuid.uuid4().hex[:8]}"
                    break

            doc = {
                "_id": uuid.uuid4().hex,
                "openid": openid,
                "username": candidate_username,
                "role": role,
                "status": 1,
                "registered_invite_code": invite_code,
                "device_count": 0,
                "invite_generated_count": 0,
                "member_role": member_role,
                "created_at": now(),
                "updated_at": now(),
                "last_login_at": now(),
            }
            try:
                await self.db.users.insert_one(doc)
            except DuplicateKeyError as exc:
                if role != "ADMIN":
                    await self.db.system_configs.update_one({"_id": "global_settings"}, {"$inc": {"registered_user_count": -1}})
                if invite:
                    await self.db.invite_codes.update_one({"_id": invite["_id"], "status": "RESERVED"}, {"$set": {"status": "UNUSED"}, "$unset": {"reserved_at": ""}})
                raise ConflictError("该微信用户已注册") from exc
            except Exception:
                if role != "ADMIN":
                    await self.db.system_configs.update_one({"_id": "global_settings"}, {"$inc": {"registered_user_count": -1}})
                if invite:
                    await self.db.invite_codes.update_one({"_id": invite["_id"], "status": "RESERVED"}, {"$set": {"status": "UNUSED"}, "$unset": {"reserved_at": ""}})
                raise

            if invite:
                await self.db.invite_codes.update_one(
                    {"_id": invite["_id"], "status": "RESERVED"},
                    {"$set": {"status": "USED", "used_by": doc["_id"], "used_at": now()}, "$unset": {"reserved_at": ""}},
                )
            return doc

        # 内存模式
        async with self._lock:
            if role != "ADMIN":
                if not self._config["allow_user_registration"]:
                    raise QuotaError("系统当前已暂停新用户注册")
                current_users = sum(1 for u in self._users.values() if u["role"] == "USER")
                if current_users >= self._config["max_registered_users"]:
                    raise QuotaError("系统注册人数已达上限")
            
            invite = self._invites.get(invite_code or "")
            if config["require_invite_code"] and role != "ADMIN":
                if not invite or invite["status"] != "UNUSED":
                    raise ConflictError("无效或已被使用的邀请码")
            
            candidate_username = username
            if any(u["username"] == candidate_username for u in self._users.values()):
                candidate_username = f"{username}_{secrets.token_hex(2)}"

            doc = {
                "_id": uuid.uuid4().hex,
                "openid": openid,
                "username": candidate_username,
                "role": role,
                "status": 1,
                "registered_invite_code": invite_code,
                "device_count": 0,
                "invite_generated_count": 0,
                "member_role": member_role,
                "created_at": now(),
                "updated_at": now(),
                "last_login_at": now(),
            }
            self._users[doc["_id"]] = doc
            if role != "ADMIN":
                self._config["registered_user_count"] = sum(1 for u in self._users.values() if u["role"] == "USER")
            if invite:
                invite.update({"status": "USED", "used_by": doc["_id"], "used_at": now()})
            return deepcopy(doc)

    async def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        user = await self.get_user_by_username(username)
        return user if user and user["status"] == 1 and verify_password(password, user["password_hash"]) else None

    async def set_user_status(self, user_id: str, status: int) -> Optional[Dict[str, Any]]:
        if self.db is not None:
            return await self.db.users.find_one_and_update({"_id": user_id}, {"$set": {"status": status, "updated_at": now()}}, return_document=ReturnDocument.AFTER)
        if user_id not in self._users:
            return None
        self._users[user_id].update({"status": status, "updated_at": now()})
        return deepcopy(self._users[user_id])

    async def create_invites(self, creator: Dict[str, Any], count: int = 1) -> List[Dict[str, Any]]:
        config = await self.get_config()
        docs = [{"_id": uuid.uuid4().hex, "code": "INV-" + secrets.token_hex(4).upper(), "created_by": creator["_id"],
                 "status": "UNUSED", "used_by": None, "used_at": None, "created_at": now()} for _ in range(count)]
        if self.db is not None:
            reserved = None
            if creator["role"] != "ADMIN":
                reserved = await self.db.users.find_one_and_update(
                    {"_id": creator["_id"], "$expr": {"$lte": [{"$add": [{"$ifNull": ["$invite_generated_count", 0]}, count]}, config["max_invites_per_user"]]}},
                    {"$inc": {"invite_generated_count": count}}, return_document=ReturnDocument.AFTER,
                )
                if not reserved:
                    raise QuotaError("邀请码生成数量已达上限")
            try:
                await self.db.invite_codes.insert_many(docs)
            except Exception:
                if reserved:
                    await self.db.users.update_one({"_id": creator["_id"]}, {"$inc": {"invite_generated_count": -count}})
                raise
        else:
            async with self._lock:
                existing_count = sum(1 for i in self._invites.values() if i["created_by"] == creator["_id"])
                if creator["role"] != "ADMIN" and existing_count + count > self._config["max_invites_per_user"]:
                    raise QuotaError("邀请码生成数量已达上限")
                for doc in docs:
                    self._invites[doc["code"]] = doc
                if creator["_id"] in self._users:
                    self._users[creator["_id"]]["invite_generated_count"] = existing_count + count
        return deepcopy(docs)

    async def list_invites(self, created_by: Optional[str] = None) -> List[Dict[str, Any]]:
        query = {"created_by": created_by} if created_by else {}
        if self.db is not None:
            return await self.db.invite_codes.find(query).sort("created_at", -1).to_list(None)
        return [deepcopy(x) for x in self._invites.values() if not created_by or x["created_by"] == created_by]

    async def get_active_api_key(self, user_id: str) -> Optional[Dict[str, Any]]:
        if self.db is not None:
            return await self.db.api_keys.find_one({"user_id": user_id, "status": "ACTIVE"})
        return deepcopy(next((k for k in self._keys.values() if k["user_id"] == user_id and k["status"] == "ACTIVE"), None))

    async def rotate_api_key(self, user_id: str) -> Tuple[Dict[str, Any], str, List[str]]:
        raw = generate_api_key()
        doc = {"_id": uuid.uuid4().hex, "user_id": user_id, "name": "默认 API Key", "key_prefix": api_key_prefix(raw),
               "key_hash": digest_api_key(raw, self.config), "status": "ACTIVE", "created_at": now(), "last_used_at": None, "revoked_at": None}
        revoked_ids: List[str] = []
        if self.db is not None:
            old = await self.db.api_keys.find({"user_id": user_id, "status": "ACTIVE"}).to_list(None)
            revoked_ids = [x["_id"] for x in old]
            await self.db.api_keys.update_many({"user_id": user_id, "status": "ACTIVE"}, {"$set": {"status": "REVOKED", "revoked_at": now()}})
            await self.db.api_keys.insert_one(doc)
        else:
            async with self._lock:
                for key in self._keys.values():
                    if key["user_id"] == user_id and key["status"] == "ACTIVE":
                        key.update({"status": "REVOKED", "revoked_at": now()})
                        revoked_ids.append(key["_id"])
                self._keys[doc["_id"]] = doc
        return deepcopy(doc), raw, revoked_ids

    async def authenticate_api_key(self, raw: str) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
        digest = digest_api_key(raw, self.config)
        if self.db is not None:
            key = await self.db.api_keys.find_one_and_update({"key_hash": digest, "status": "ACTIVE"}, {"$set": {"last_used_at": now()}}, return_document=ReturnDocument.AFTER)
        else:
            key = next((k for k in self._keys.values() if k["key_hash"] == digest and k["status"] == "ACTIVE"), None)
            if key:
                key["last_used_at"] = now()
                key = deepcopy(key)
        if not key:
            return None
        user = await self.get_user(key["user_id"])
        return (key, user) if user else None

    async def bind_device(self, user_id: str, device_id: str, device_name: str) -> Tuple[Dict[str, Any], Optional[str]]:
        config = await self.get_config()
        devices = await self.list_devices(user_id)
        doc = {"_id": uuid.uuid4().hex, "user_id": user_id, "device_id": device_id.strip(), "device_name": device_name.strip(),
               "is_active": True, "is_default": not devices, "last_online_at": None, "created_at": now(), "updated_at": now()}
        if self.db is not None:
            reserved = await self.db.users.find_one_and_update(
                {"_id": user_id, "$expr": {"$lt": [{"$ifNull": ["$device_count", 0]}, config["max_devices_per_user"]]}},
                {"$inc": {"device_count": 1}}, return_document=ReturnDocument.AFTER,
            )
            if not reserved:
                raise QuotaError("设备绑定数量已达上限")
            try:
                await self.db.devices.insert_one(doc)
            except DuplicateKeyError as exc:
                await self.db.users.update_one({"_id": user_id}, {"$inc": {"device_count": -1}})
                raise ConflictError("设备已被绑定") from exc
        else:
            async with self._lock:
                current_devices = sum(1 for d in self._devices.values() if d["user_id"] == user_id)
                if current_devices >= self._config["max_devices_per_user"]:
                    raise QuotaError("设备绑定数量已达上限")
                if doc["device_id"] in self._devices:
                    raise ConflictError("设备已被绑定")
                self._devices[doc["device_id"]] = doc
                if user_id in self._users:
                    self._users[user_id]["device_count"] = current_devices + 1
        raw = None
        if not await self.get_active_api_key(user_id):
            _, raw, _ = await self.rotate_api_key(user_id)
        return deepcopy(doc), raw

    async def list_devices(self, user_id: str) -> List[Dict[str, Any]]:
        if self.db is not None:
            return await self.db.devices.find({"user_id": user_id}).sort("created_at", 1).to_list(None)
        return [deepcopy(d) for d in self._devices.values() if d["user_id"] == user_id]

    async def find_device(self, user_id: str, device_id: str) -> Optional[Dict[str, Any]]:
        if self.db is not None:
            return await self.db.devices.find_one({"user_id": user_id, "device_id": device_id, "is_active": True})
        d = self._devices.get(device_id)
        return deepcopy(d) if d and d["user_id"] == user_id and d["is_active"] else None

    async def touch_device_online(self, user_id: str, device_id: str) -> None:
        timestamp = now()
        if self.db is not None:
            await self.db.devices.update_one({"user_id": user_id, "device_id": device_id}, {"$set": {"last_online_at": timestamp}})
        elif device_id in self._devices and self._devices[device_id]["user_id"] == user_id:
            self._devices[device_id]["last_online_at"] = timestamp

    async def delete_device(self, user_id: str, record_id: str) -> Optional[Dict[str, Any]]:
        if self.db is not None:
            deleted = await self.db.devices.find_one_and_delete(
                {"user_id": user_id, "$or": [{"_id": record_id}, {"device_id": record_id}]}
            )
            if deleted:
                await self.db.users.update_one({"_id": user_id, "device_count": {"$gt": 0}}, {"$inc": {"device_count": -1}})
                if deleted.get("is_default"):
                    first_remaining = await self.db.devices.find_one({"user_id": user_id}, sort=[("created_at", 1)])
                    if first_remaining:
                        await self.db.devices.update_one({"_id": first_remaining["_id"]}, {"$set": {"is_default": True, "updated_at": now()}})
            return deleted
        async with self._lock:
            target = next((d for d in self._devices.values() if (d["_id"] == record_id or d["device_id"] == record_id) and d["user_id"] == user_id), None)
            if target:
                self._devices.pop(target["device_id"], None)
                if user_id in self._users:
                    self._users[user_id]["device_count"] = max(0, self._users[user_id].get("device_count", 1) - 1)
                if target.get("is_default"):
                    remaining = sorted([d for d in self._devices.values() if d["user_id"] == user_id], key=lambda x: x.get("created_at", datetime.min))
                    if remaining:
                        remaining[0]["is_default"] = True
                        remaining[0]["updated_at"] = now()
            return deepcopy(target)

    async def admin_delete_device(self, record_id: str) -> Optional[Dict[str, Any]]:
        if self.db is not None:
            deleted = await self.db.devices.find_one_and_delete(
                {"$or": [{"_id": record_id}, {"device_id": record_id}]}
            )
            if deleted:
                owner_id = deleted.get("user_id")
                if owner_id:
                    await self.db.users.update_one({"_id": owner_id, "device_count": {"$gt": 0}}, {"$inc": {"device_count": -1}})
                    if deleted.get("is_default"):
                        first_remaining = await self.db.devices.find_one({"user_id": owner_id}, sort=[("created_at", 1)])
                        if first_remaining:
                            await self.db.devices.update_one({"_id": first_remaining["_id"]}, {"$set": {"is_default": True, "updated_at": now()}})
            return deleted
        async with self._lock:
            target = next((d for d in self._devices.values() if d["_id"] == record_id or d["device_id"] == record_id), None)
            if target:
                self._devices.pop(target["device_id"], None)
                owner_id = target.get("user_id")
                if owner_id and owner_id in self._users:
                    self._users[owner_id]["device_count"] = max(0, self._users[owner_id].get("device_count", 1) - 1)
                if target.get("is_default") and owner_id:
                    remaining = sorted([d for d in self._devices.values() if d["user_id"] == owner_id], key=lambda x: x.get("created_at", datetime.min))
                    if remaining:
                        remaining[0]["is_default"] = True
                        remaining[0]["updated_at"] = now()
            return deepcopy(target)

    async def update_device(self, user_id: str, record_id: str, changes: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        allowed = {k: v for k, v in changes.items() if k in {"device_name", "is_default"} and v is not None}
        allowed["updated_at"] = now()
        if self.db is not None:
            if allowed.get("is_default"):
                await self.db.devices.update_many({"user_id": user_id}, {"$set": {"is_default": False}})
            return await self.db.devices.find_one_and_update(
                {"user_id": user_id, "$or": [{"_id": record_id}, {"device_id": record_id}]},
                {"$set": allowed},
                return_document=ReturnDocument.AFTER
            )
        target = next((d for d in self._devices.values() if (d["_id"] == record_id or d["device_id"] == record_id) and d["user_id"] == user_id), None)
        if not target:
            return None
        if allowed.get("is_default"):
            for device in self._devices.values():
                if device["user_id"] == user_id:
                    device["is_default"] = False
        target.update(allowed)
        return deepcopy(target)

    async def list_users(self) -> List[Dict[str, Any]]:
        if self.db is not None:
            return await self.db.users.find({}).sort("created_at", -1).to_list(None)
        return [deepcopy(u) for u in self._users.values()]


repository = Repository()
