import hashlib
import json
import logging
import time
import uuid
from typing import Any, Dict, Optional
import requests

from .config import Settings, settings

logger = logging.getLogger("TVBoxServer.DreamAuth")


class DreamAuthException(Exception):
    """Base exception for DreamAuth client errors."""

    def __init__(self, message: str, code: int = 400, raw_response: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.raw_response = raw_response or {}


class DreamAuthClient:
    def __init__(self, config: Settings = settings):
        self.base_url = config.dreamauth_base_url
        self.access_key = config.dreamauth_access_key
        self.secret_key = config.dreamauth_secret_key
        self.app_code = config.dreamauth_app_code

    def is_configured(self) -> bool:
        return bool(self.access_key and self.secret_key)

    def _sign(self, method: str, path: str, timestamp: str, nonce: str, payload: Optional[Any]) -> str:
        payload_json = json.dumps(payload, separators=(",", ":"), ensure_ascii=False) if payload is not None else ""
        plain = f"{method.upper()}|{path}|{timestamp}|{nonce}|{payload_json}|{self.secret_key}"
        return hashlib.md5(plain.encode("utf-8")).hexdigest()

    def _build_headers(self, method: str, path: str, payload: Optional[Any] = None) -> Dict[str, str]:
        if not self.is_configured():
            raise DreamAuthException("DreamAuth AK/SK 未配置，请在环境变量中设置 DREAMAUTH_ACCESS_KEY 与 DREAMAUTH_SECRET_KEY", 500)
        timestamp = str(int(time.time()))
        nonce = uuid.uuid4().hex[:16]
        sign = self._sign(method, path, timestamp, nonce, payload)
        return {
            "X-Kite-AK": self.access_key,
            "X-Kite-Timestamp": timestamp,
            "X-Kite-Nonce": nonce,
            "X-Kite-Sign": sign,
            "Content-Type": "application/json",
        }

    def create_session(
        self,
        biz_code: str = "LOGIN",
        biz_state: str = "tvbox-web-login",
        target_type: str = "user",
        expire_seconds: int = 300,
    ) -> Dict[str, Any]:
        """
        创建微信扫码授权会话
        返回: { sessionNo, scene, qrcode, expireAt, appCode }
        """
        path = "/api/open/scan-login/session/create"
        payload = {
            "bizCode": biz_code,
            "bizState": biz_state,
            "targetType": target_type,
            "expireSeconds": expire_seconds,
        }
        headers = self._build_headers("POST", path, payload)
        url = f"{self.base_url}{path}"
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=15)
            data = resp.json()
        except Exception as exc:
            logger.error(f"DreamAuth create_session request error: {exc}")
            raise DreamAuthException(f"连接 DreamAuth 授权服务器失败: {exc}", 502)

        if data.get("code") != 200:
            msg = data.get("msg") or data.get("message") or "创建扫码会话失败"
            logger.warning(f"DreamAuth create_session failed: {data}")
            raise DreamAuthException(msg, data.get("code", 400), data)

        # data 节点可能在 data.data 或顶层
        session_data = data.get("data") if isinstance(data.get("data"), dict) else data
        return {
            "session_no": session_data.get("sessionNo"),
            "scene": session_data.get("scene"),
            "qrcode": session_data.get("qrcode"),
            "expire_at": session_data.get("expireAt"),
            "app_code": session_data.get("appCode") or self.app_code,
        }

    def get_session_status(self, session_no: str) -> Dict[str, Any]:
        """
        查询扫码会话状态
        1: waiting for scan
        2: scanned, waiting for confirm
        3: authorized
        4: canceled
        6: consumed
        7: expired
        """
        path = "/api/open/scan-login/session/status"
        sign_payload = {"sessionNo": session_no}
        headers = self._build_headers("GET", path, sign_payload)
        url = f"{self.base_url}{path}"
        try:
            resp = requests.get(url, params={"sessionNo": session_no}, headers=headers, timeout=10)
            data = resp.json()
        except Exception as exc:
            logger.error(f"DreamAuth get_session_status request error: {exc}")
            raise DreamAuthException(f"查询授权状态失败: {exc}", 502)

        if data.get("code") != 200:
            msg = data.get("msg") or data.get("message") or "查询扫码状态失败"
            raise DreamAuthException(msg, data.get("code", 400), data)

        status_data = data.get("data") if isinstance(data.get("data"), dict) else data
        return {
            "session_no": status_data.get("sessionNo") or session_no,
            "scene": status_data.get("scene"),
            "status": status_data.get("status"),
            "expire_at": status_data.get("expireAt"),
            "auth_time": status_data.get("authTime"),
            "member_role": status_data.get("memberRole"),
        }

    def get_session_result(self, session_no: str, consume: bool = True) -> Dict[str, Any]:
        """
        获取最终授权结果 (openid, authToken 等)
        """
        path = "/api/open/scan-login/session/result"
        payload = {"sessionNo": session_no, "consume": consume}
        headers = self._build_headers("POST", path, payload)
        url = f"{self.base_url}{path}"
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=15)
            data = resp.json()
        except Exception as exc:
            logger.error(f"DreamAuth get_session_result request error: {exc}")
            raise DreamAuthException(f"获取授权结果失败: {exc}", 502)

        if data.get("code") != 200:
            msg = data.get("msg") or data.get("message") or "获取授权结果失败"
            raise DreamAuthException(msg, data.get("code", 400), data)

        result_data = data.get("data") if isinstance(data.get("data"), dict) else data
        return {
            "session_no": result_data.get("sessionNo") or session_no,
            "scene": result_data.get("scene"),
            "status": result_data.get("status"),
            "openid": result_data.get("openid"),
            "auth_token": result_data.get("authToken"),
            "member_role": result_data.get("memberRole"),
            "biz_code": result_data.get("bizCode"),
            "biz_state": result_data.get("bizState"),
            "target_type": result_data.get("targetType"),
            "auth_time": result_data.get("authTime"),
        }


dreamauth_client = DreamAuthClient()
