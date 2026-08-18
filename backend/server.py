#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TVBox AI Controller Python Backend
提供:
1. WebSocket 服务供 TVBox 客户端建立长连接 (/ws/tvbox/{device_id})
2. REST API (/api/chat) 接收用户文本输入，经 LLM Agent 生成 Tool JSON 并下发给 TVBox
"""

import os
import re
import json
import time
import uuid
import asyncio
import logging
from contextvars import ContextVar
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from fastapi import Depends, FastAPI, Header, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
load_dotenv()

from app.dependencies import DeviceCredential, current_user
from app.config import settings
from app.platform_routes import router as platform_router
from app.repository import repository

CURRENT_USER_ID: ContextVar[Optional[str]] = ContextVar("current_tvbox_user_id", default=None)
CURRENT_DEVICE_ID: ContextVar[Optional[str]] = ContextVar("current_tvbox_device_id", default=None)

# 日志目录与本地文件 Handler 配置
LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE_PATH = LOGS_DIR / "server.log"

formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

# 控制台输出 Handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# 本地文件轮转 Handler (单个文件最大 10MB，保留最近 5 个备份，UTF-8 编码)
file_handler = RotatingFileHandler(
    LOG_FILE_PATH, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
)
file_handler.setFormatter(formatter)

logger = logging.getLogger("TVBoxServer")
logger.setLevel(logging.INFO)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# 避免日志重复打印
logger.propagate = False

# 从环境变量读取配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL") or os.getenv("LLM_BASE_URL") or "https://api.openai.com/v1"
LLM_MODEL = os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-4o"
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
ROOT_PATH = settings.root_path

masked_key = (OPENAI_API_KEY[:6] + "..." + OPENAI_API_KEY[-4:]) if OPENAI_API_KEY and len(OPENAI_API_KEY) > 10 else "未配置(将使用本地规则解析器)"
logger.info("=" * 55)
logger.info("📺 TVBox AI Control Center 启动配置:")
logger.info(f"   • 大模型引擎: {LLM_MODEL}")
logger.info(f"   • API BaseURL: {OPENAI_BASE_URL}")
logger.info(f"   • API Key:    {masked_key}")
logger.info(f"   • Root Path:  {ROOT_PATH or '/'}")
logger.info("=" * 55)

@asynccontextmanager
async def lifespan(_app: FastAPI):
    await repository.initialize()
    repository.device_manager = device_mgr
    _app.state.repository = repository
    yield
    await repository.close()


app = FastAPI(title="TVBox AI Control Center", lifespan=lifespan, root_path=ROOT_PATH)

_cors_origins = list(settings.cors_origins) if settings.cors_origins else ["*"]
_is_wildcard = "*" in _cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins if not _is_wildcard else ["*"],
    allow_origin_regex=r"^https?://.*" if _is_wildcard else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


def _extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    scheme, separator, token = authorization.partition(" ")
    if separator and scheme.lower() == "bearer":
        return token.strip()
    return None


async def require_api_key(authorization: Optional[str] = Header(default=None)):
    # Kept as a named dependency for route compatibility; authentication is
    # database-backed and returns the trusted user mapped from the API key.
    raw = _extract_bearer_token(authorization)
    result = await repository.authenticate_api_key(raw or "")
    if not result:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if result[1]["status"] != 1:
        raise HTTPException(status_code=403, detail="API key owner is disabled")
    return DeviceCredential(key=result[0], user=result[1])

# ==================== 1. 设备连接与请求追踪管理器 ====================

class DeviceManager:
    def __init__(self):
        # (user_id, device_id) -> (WebSocket, connection_id, api_key_id)
        self.connections: Dict[Tuple[str, str], Tuple[WebSocket, str, str]] = {}
        # request_id -> asyncio.Future
        self.pending_futures: Dict[str, Tuple[asyncio.Future, str, str]] = {}
        # (user_id, device_id) -> 实时状态字典
        self.device_states: Dict[Tuple[str, str], Dict[str, Any]] = {}

    async def register(self, user_id: str, device_id: str, ws: WebSocket, api_key_id: str) -> str:
        await ws.accept()
        key = (user_id, device_id)
        connection_id = uuid.uuid4().hex
        old = self.connections.get(key)
        if old:
            await old[0].close(code=1000, reason="Replaced by a newer connection")
        self.connections[key] = (ws, connection_id, api_key_id)
        if key not in self.device_states:
            self.device_states[key] = {
                "device_id": device_id,
                "online": True,
                "current_activity": "HomeActivity",
                "is_playing": False,
                "current_media": None,
                "volume": 50
            }
        self.device_states[key]["online"] = True
        logger.info(f"🟢 [WS] TVBox Connected: {user_id}/{device_id}")
        return connection_id

    def unregister(self, user_id: str, device_id: str, connection_id: str):
        key = (user_id, device_id)
        current = self.connections.get(key)
        if current and current[1] == connection_id:
            del self.connections[key]
            if key in self.device_states:
                self.device_states[key]["online"] = False
            logger.info(f"🔴 [WS] TVBox Disconnected: {user_id}/{device_id}")

    async def disconnect_device(self, user_id: str, device_id: str, reason: str = "Revoked"):
        key = (user_id, device_id)
        current = self.connections.pop(key, None)
        if current:
            if key in self.device_states:
                self.device_states[key]["online"] = False
            await current[0].close(code=1008, reason=reason)

    async def disconnect_user(self, user_id: str, reason: str = "Revoked"):
        for key, current in list(self.connections.items()):
            owner_id, _ = key
            if owner_id == user_id:
                self.connections.pop(key, None)
                if key in self.device_states:
                    self.device_states[key]["online"] = False
                await current[0].close(code=1008, reason=reason)

    def get_target_device_id(self, user_id: str, allowed_devices: List[dict], requested_model: Optional[str] = None, requested_device_id: Optional[str] = None) -> Optional[str]:
        """
        动态确定本次请求的目标 TVBox 设备 ID：
        1. 若请求中指定了具体的设备 ID 且该设备正处于连接在线状态，优先返回该设备
        2. 否则自动寻找并路由至当前唯一/首个在线的 TVBox 真实设备
        3. 若指定设备已离线但无其他在线设备，返回指定设备以触发离线提示
        4. 若从未有任何设备连接，返回 None
        """
        generic_names = {"default", "auto", "tvbox-agent", "tvbox_default", "gpt-4o", "gpt-3.5-turbo", ""}
        
        target = None
        if requested_model and requested_model not in generic_names:
            target = requested_model
        elif requested_device_id and requested_device_id not in generic_names:
            target = requested_device_id

        # 如果指定的目标设备当前正好在线，直接返回
        allowed_ids = {d["device_id"] for d in allowed_devices if d.get("is_active", True)}
        if target and target not in allowed_ids:
            return None
        if target and (user_id, target) in self.connections:
            return target

        # 否则寻找当前处于在线状态的第一个真实设备
        online = [d for d in allowed_devices if (user_id, d["device_id"]) in self.connections]
        if len(online) == 1:
            return online[0]["device_id"]
        default = next((d for d in online if d.get("is_default")), None)
        if default:
            return default["device_id"]

        # 若无在线设备，如果有指定目标则返回它，否则返回第一个历史设备
        if target:
            return target
        return None

    async def _send_raw_command(self, user_id: str, device_id: Optional[str], tool: str, params: dict, timeout_sec: float = 5.0) -> dict:
        key = (user_id, device_id) if device_id else None
        if not key or key not in self.connections:
            target_desc = f"[{device_id}]" if device_id else "[未检测到在线设备]"
            logger.warning(f"⚠️ TVBox 设备 {target_desc} 未在线，指令 [{tool}] 暂未实际下发")
            return {"status": "offline", "message": f"TVBox 设备 {target_desc} 未在线，请在电视端启动并连接 AI 服务", "tool": tool}

        ws = self.connections[key][0]
        req_id = f"req_{uuid.uuid4().hex[:8]}"
        command_payload = {
            "type": "command",
            "request_id": req_id,
            "tool": tool,
            "params": params,
            "timeout_ms": int(timeout_sec * 1000),
            "timestamp": int(time.time() * 1000)
        }

        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self.pending_futures[req_id] = (future, user_id, device_id)

        try:
            await ws.send_text(json.dumps(command_payload, ensure_ascii=False))
            logger.info(f"➡️ [Tool Downstream] Sent [{tool}] ({req_id}) to {device_id}: {params}")
            resp = await asyncio.wait_for(future, timeout=timeout_sec)
            return resp
        except asyncio.TimeoutError:
            logger.error(f"⏰ [Timeout] Tool [{tool}] ({req_id}) timed out after {timeout_sec}s")
            return {"status": "error", "message": f"TVBox响应超时 ({timeout_sec}s)", "tool": tool}
        finally:
            self.pending_futures.pop(req_id, None)

    async def poll_until_state_settled(self, user_id: str, device_id: str, tool: str, initial_data: dict) -> dict:
        """
        多轮轮询 TVBox 端真实状态，直到界面渲染与数据加载完全稳定（连续无变化或达到目标稳定态）
        """
        # 1. 基础 UI 动画与渲染缓冲
        await asyncio.sleep(0.4)

        last_state = initial_data or {}
        stable_count = 0
        max_polls = 6  # 最多轮询 6 次 (约 2 秒)
        poll_interval = 0.35

        for i in range(max_polls):
            state_resp = await self._send_raw_command(
                user_id=user_id, device_id=device_id,
                tool="get_device_state",
                params={"include_full_shadow": True},
                timeout_sec=1.5
            )
            if not isinstance(state_resp, dict) or state_resp.get("status") != "success":
                await asyncio.sleep(poll_interval)
                continue

            cur_data = state_resp.get("data", {})
            cur_page = cur_data.get("current_page", "")

            # A. 搜索类工具：等待搜索结果列表填充
            if tool in ["search_media", "filter_category"]:
                results = cur_data.get("search_results", [])
                if len(results) > 0:
                    if len(results) == len(last_state.get("search_results", [])):
                        stable_count += 1
                        if stable_count >= 1:
                            logger.info(f"🔍 [State Settled] 搜索结果稳定完成，获取到 {len(results)} 条数据")
                            return cur_data
                    else:
                        stable_count = 0
                last_state = cur_data

            # B. 选片/详情页/播放类工具：等待 Activity 切换完成
            elif tool in ["select_search_item", "play_vod", "control_detail_page"]:
                if cur_page == "DetailActivity" or cur_data.get("is_playing"):
                    stable_count += 1
                    if stable_count >= 1:
                        logger.info(f"🎬 [State Settled] 详情/播放页面渲染稳定: {cur_page}")
                        return cur_data
                last_state = cur_data

            # C. 导航类工具：等待目标页面切换
            elif tool in ["navigate_to_page", "go_back", "switch_live_channel"]:
                if cur_page and cur_page == last_state.get("current_page"):
                    stable_count += 1
                    if stable_count >= 1:
                        logger.info(f"🧭 [State Settled] 页面跳转渲染稳定: {cur_page}")
                        return cur_data
                else:
                    stable_count = 0
                last_state = cur_data

            else:
                # D. 其他通用状态检查
                if cur_data == last_state:
                    stable_count += 1
                    if stable_count >= 1:
                        return cur_data
                else:
                    stable_count = 0
                last_state = cur_data

            await asyncio.sleep(poll_interval)

        return last_state

    async def send_tool_command(self, device_id: Optional[str], tool: str, params: dict, timeout_sec: float = 8.0, user_id: Optional[str] = None) -> dict:
        """
        发送 Tool 指令并在执行后自动多轮感知 TVBox 端最新状态，直到界面渲染稳定后再返回给 Agent 决策
        """
        user_id = user_id or CURRENT_USER_ID.get()
        device_id = device_id or CURRENT_DEVICE_ID.get()
        if not user_id:
            return {"status": "error", "message": "缺少可信租户上下文", "tool": tool}
        resp = await self._send_raw_command(user_id, device_id, tool, params, timeout_sec=timeout_sec)
        if not isinstance(resp, dict) or resp.get("status") not in ["success", "pending"]:
            return resp

        # 针对可能引起界面跳转、异步搜索、状态变更的工具，执行状态稳定轮询
        transition_tools = {
            "search_media", "filter_category", "select_search_item",
            "play_vod", "navigate_to_page", "control_detail_page",
            "switch_live_channel", "switch_home_source", "go_back",
            "send_key_event"
        }

        if tool in transition_tools and device_id and (user_id, device_id) in self.connections:
            stabilized_data = await self.poll_until_state_settled(user_id, device_id, tool, resp.get("data", {}))
            if stabilized_data:
                resp_data = resp.get("data", {}) if isinstance(resp.get("data"), dict) else {}
                resp_data.update(stabilized_data)
                resp["data"] = resp_data

        return resp

    def resolve_response(self, user_id: str, device_id: Optional[str], response_data: dict):
        req_id = response_data.get("request_id")
        data = response_data.get("data")
        if device_id and isinstance(data, dict):
            self.update_state(user_id, device_id, data)
        if req_id and req_id in self.pending_futures:
            future, expected_user, expected_device = self.pending_futures[req_id]
            if expected_user == user_id and expected_device == device_id and not future.done():
                future.set_result(response_data)

    def update_state(self, user_id: str, device_id: str, state_patch: dict):
        key = (user_id, device_id)
        if key in self.device_states:
            self.device_states[key].update(state_patch)

device_mgr = DeviceManager()
app.include_router(platform_router)

# ==================== 2. LLM Agent 意图识别与 Tool 生成器 ====================

TVBOX_TOOLS_SCHEMA = [
    {
        "name": "select_search_item",
        "description": "在搜索结果列表中根据屏幕上海报右上角标注的数字序号（如 1, 2, 3...）选择并播放对应影片。当用户在搜索后表达'播放第1个'、'看第3部'、'选2号'时调用。",
        "parameters": {
            "type": "object",
            "properties": {
                "index": {"type": "integer", "description": "搜索列表中海报右上角的数字序号 (从1开始)"},
                "action": {"type": "string", "enum": ["play", "detail"], "description": "操作动作，默认play直接播放"}
            },
            "required": ["index"]
        }
    },
    {
        "name": "play_vod",
        "description": "播放指定的影视剧集或电影",
        "parameters": {
            "type": "object",
            "properties": {
                "vod_name": {"type": "string", "description": "影片名称，如：狂飙、繁花、流浪地球"},
                "episode_index": {"type": "integer", "description": "第几集，从1开始计数，默认第1集"},
                "line_flag": {"type": "string", "description": "播放线路名称，如：4K原画、极速线路"}
            },
            "required": ["vod_name"]
        }
    },
    {
        "name": "switch_live_channel",
        "description": "切换电视直播频道",
        "parameters": {
            "type": "object",
            "properties": {
                "channel_name": {"type": "string", "description": "频道名称，如：CCTV-1、CCTV-5、浙江卫视、湖南卫视"},
                "channel_number": {"type": "integer", "description": "台号，如 1, 5"},
                "group_name": {"type": "string", "description": "分组名称，如 央视频道、卫视频道"}
            }
        }
    },
    {
        "name": "search_media",
        "description": "在 TVBox 中搜索影片、电视剧、动漫",
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "搜索关键词"},
                "fast_mode": {"type": "boolean", "description": "是否极速多源聚合搜索"}
            },
            "required": ["keyword"]
        }
    },
    {
        "name": "control_playback",
        "description": "控制当前视频播放状态",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string", 
                    "enum": ["pause", "resume", "toggle", "next", "prev", "seek", "speed", "scale"],
                    "description": "控制动作"
                },
                "seek_seconds": {"type": "integer", "description": "快进/快退的相对秒数（正数为快进，负数为快退）或绝对秒数"},
                "speed": {"type": "number", "description": "倍速值，如 1.25, 1.5, 2.0"},
                "scale": {"type": "string", "enum": ["default", "16:9", "4:3", "fill", "original"]}
            },
            "required": ["action"]
        }
    },
    {
        "name": "navigate_to_page",
        "description": "跳转到指定的功能页面",
        "parameters": {
            "type": "object",
            "properties": {
                "target_page": {
                    "type": "string",
                    "enum": ["home", "search", "live", "history", "collect", "setting", "push"],
                    "description": "目标页面"
                }
            },
            "required": ["target_page"]
        }
    },
    {
        "name": "send_key_event",
        "description": "模拟遥控器按键操作",
        "parameters": {
            "type": "object",
            "properties": {
                "key_code": {
                    "type": "string",
                    "enum": ["DPAD_UP", "DPAD_DOWN", "DPAD_LEFT", "DPAD_RIGHT", "DPAD_CENTER", "BACK", "MENU", "VOLUME_UP", "VOLUME_DOWN"],
                    "description": "按键编码"
                }
            },
            "required": ["key_code"]
        }
    }
]

async def parse_prompt_to_tool(prompt: str) -> tuple[str, dict, str]:
    """
    使用轻量智能解析器（支持规则与兼容 OpenAI API），提取意图并返回 (tool_name, params, natural_reply)
    """
    p = prompt.strip().lower()

    # 0. 搜索列表选片/按序号播放逻辑 (如: 播放第1个, 看第3部, 选2号, 1, 2)
    m_idx = re.search(r"^(?:播放|看|选|打开|选择)?\s*第?(\d+)[个部号条]?$", prompt.strip())
    if m_idx:
        idx = int(m_idx.group(1))
        return "select_search_item", {"index": idx, "action": "play"}, f"正在为您播放第 {idx} 个搜索结果"

    # 1. 播放点播逻辑
    m_play = re.search(r"(?:播放|看|来个|放一下|我想看)\s*(.+?)(?:第(\d+)集)?$", prompt)
    if m_play and not any(k in prompt for k in ["央视", "卫视", "频道", "cctv", "台"]):
        name = m_play.group(1).replace("电视剧", "").replace("电影", "").strip()
        ep = int(m_play.group(2)) if m_play.group(2) else 1
        return "play_vod", {"vod_name": name, "episode_index": ep}, f"正在为您在电视上播放《{name}》第{ep}集"

    # 2. 直播换台逻辑
    if any(k in prompt for k in ["cctv", "卫视", "中央", "频道", "换台", "看直播", "北京台", "湖南台"]):
        c_name = prompt.replace("看", "").replace("播放", "").replace("换到", "").replace("切换到", "").strip()
        return "switch_live_channel", {"channel_name": c_name}, f"已为您切换到电视频道【{c_name}】"

    # 3. 播放控制逻辑
    if "暂停" in p:
        return "control_playback", {"action": "pause"}, "已为您暂停播放"
    if "继续" in p or "恢复" in p:
        return "control_playback", {"action": "resume"}, "已恢复播放"
    if "下一集" in p:
        return "control_playback", {"action": "next"}, "已切换到下一集"
    if "上一集" in p:
        return "control_playback", {"action": "prev"}, "已切换到上一集"
    if "快进" in p:
        m_sec = re.search(r"(\d+)\s*(?:秒|分钟)", prompt)
        sec = int(m_sec.group(1)) * (60 if "分" in prompt else 1) if m_sec else 60
        return "control_playback", {"action": "seek", "seek_seconds": sec}, f"已为您快进 {sec} 秒"
    if "快退" in p or "倒退" in p:
        m_sec = re.search(r"(\d+)\s*(?:秒|分钟)", prompt)
        sec = int(m_sec.group(1)) * (60 if "分" in prompt else 1) if m_sec else 60
        return "control_playback", {"action": "seek", "seek_seconds": -sec}, f"已为您快退 {sec} 秒"
    if "倍速" in p:
        m_sp = re.search(r"(\d+(?:\.\d+)?)\s*倍", prompt)
        sp = float(m_sp.group(1)) if m_sp else 1.5
        return "control_playback", {"action": "speed", "speed": sp}, f"已为您调整播放速度为 {sp}x"
    if "比例" in p or "画面" in p or "拉伸" in p or "满屏" in p or "铺满" in p or "16:9" in p or "4:3" in p:
        if "16:9" in p or "16比9" in p:
            return "control_playback", {"action": "change_scale", "scale": "16:9"}, "已为您切换画面比例为 16:9"
        if "4:3" in p or "4比3" in p:
            return "control_playback", {"action": "change_scale", "scale": "4:3"}, "已为您切换画面比例为 4:3"
        if "满屏" in p or "拉伸" in p or "填充" in p or "铺满" in p:
            return "control_playback", {"action": "change_scale", "scale": "match_screen"}, "已为您切换画面为铺满全屏"
        if "原始" in p:
            return "control_playback", {"action": "change_scale", "scale": "original"}, "已为您恢复原始画面比例"

    # 4. 搜索逻辑
    if "搜索" in p or "找一下" in p or "搜" in p:
        kw = re.sub(r"^(搜索|找一下|搜|查一下)", "", prompt).strip()
        return "search_media", {"keyword": kw, "fast_mode": True}, f"已为您搜索影视资源：{kw}"

    # 5. 导航与页面跳转
    if "主页" in p or "首页" in p:
        return "navigate_to_page", {"target_page": "home"}, "已回到主页"
    if "历史" in p:
        return "navigate_to_page", {"target_page": "history"}, "已打开历史记录"
    if "收藏" in p:
        return "navigate_to_page", {"target_page": "collect"}, "已打开我的收藏"
    if "设置" in p:
        return "navigate_to_page", {"target_page": "setting"}, "已打开系统设置"
    if "返回" in p:
        return "send_key_event", {"key_code": "BACK"}, "已返回上一层"

    # 默认兜底：进行全网搜索
    return "search_media", {"keyword": prompt, "fast_mode": True}, f"已为您在 TVBox 中搜索：{prompt}"

# ==================== 3. OpenAI 兼容接口与路由 ====================

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: Optional[str] = None
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.1
    stream: Optional[bool] = False
    device_id: Optional[str] = None

@app.get("/v1/models")
async def list_models(credential: DeviceCredential = Depends(require_api_key)):
    """
    OpenAI 兼容的模型列表接口 (动态将已连接/已上报的 TVBox 电视设备映射为 Model)
    """
    now = int(time.time())
    model_list = []
    
    devices = await repository.list_devices(credential.user["_id"])
    for device in devices:
        dev_id = device["device_id"]
        state = device_mgr.device_states.get((credential.user["_id"], dev_id), {})
        model_list.append({
            "id": dev_id,
            "object": "model",
            "created": now,
            "owned_by": "tvbox-device",
            "permission": [],
            "root": dev_id,
            "parent": None,
            "online": state.get("online", False),
            "device_name": device.get("device_name", dev_id),
            "current_activity": state.get("current_activity", "HomeActivity")
        })

    return {
        "object": "list",
        "data": model_list
    }

async def execute_agent_or_parser(prompt: str, user_id: str, device_id: Optional[str]) -> tuple[str, Optional[dict], Any]:
    """统一执行 LangChain Agent 或本地规则解析器，返回 (output_text, tool_call_info, exec_result)"""
    if not device_id:
        return "当前暂无 TVBox 电视设备在线，请先在电视端启动并连接 AI 服务。", None, None

    CURRENT_USER_ID.set(user_id)
    CURRENT_DEVICE_ID.set(device_id)
    openai_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
    if openai_key:
        try:
            from langchain_agent import create_tvbox_agent
            from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
            agent_graph = create_tvbox_agent(api_key=openai_key)
            result = await agent_graph.ainvoke({"messages": [HumanMessage(content=prompt)]})
            
            output_text = ""
            tool_traces = []
            todo_list = []
            
            if isinstance(result, dict) and "messages" in result:
                for m in result["messages"]:
                    if hasattr(m, "tool_calls") and m.tool_calls:
                        for tc in m.tool_calls:
                            t_name = tc.get("name")
                            t_args = tc.get("args", {})
                            if t_name in ["write_todos", "plan_todo_tasks"] and isinstance(t_args, dict) and "todos" in t_args:
                                todo_list = t_args.get("todos", [])
                            tool_traces.append({
                                "name": t_name,
                                "params": t_args,
                                "observation": ""
                            })
                    elif hasattr(m, "content") and (isinstance(m, ToolMessage) or getattr(m, "type", "") == "tool"):
                        if tool_traces:
                            tool_traces[-1]["observation"] = str(m.content)
                    elif hasattr(m, "content") and (isinstance(m, AIMessage) or getattr(m, "type", "") == "ai"):
                        if m.content and not getattr(m, "tool_calls", None):
                            output_text = m.content if isinstance(m.content, str) else str(m.content)

            tool_call_info = {
                "traces": tool_traces,
                "todo_list": todo_list,
                "total_steps": len(tool_traces),
                "name": tool_traces[-1]["name"] if tool_traces else None,
                "params": tool_traces[-1]["params"] if tool_traces else {},
                "observation": tool_traces[-1]["observation"] if tool_traces else ""
            }

            return output_text, tool_call_info, tool_traces
        except Exception as e:
            logger.warning(f"LangGraph Agent 执行异常 ({e})，自动回退到本地解析器...")

    # 本地规则解析器 (增强多意图拆解与顺序执行)
    sub_prompts = [p.strip() for p in re.split(r"[，,；;。!！\n]|然后|接着|并且|再", prompt) if p.strip()]
    if not sub_prompts:
        sub_prompts = [prompt]
        
    tool_traces = []
    reply_lines = []
    for sp in sub_prompts:
        tool_name, tool_params, natural_reply = await parse_prompt_to_tool(sp)
        exec_res = await device_mgr.send_tool_command(
            user_id=user_id,
            device_id=device_id,
            tool=tool_name,
            params=tool_params,
            timeout_sec=5.0
        )
        tool_traces.append({
            "name": tool_name,
            "params": tool_params,
            "observation": str(exec_res)
        })
        reply_lines.append(natural_reply)
        
    tool_call_info = {
        "traces": tool_traces,
        "total_steps": len(tool_traces),
        "name": tool_traces[-1]["name"] if tool_traces else None,
        "params": tool_traces[-1]["params"] if tool_traces else {},
        "observation": tool_traces[-1]["observation"] if tool_traces else ""
    }
    return "，".join(reply_lines), tool_call_info, tool_traces

async def stream_agent_or_parser(prompt: str, user_id: str, device_id: Optional[str], chat_id: str, display_model: str):
    """流式执行 LangChain Agent 或本地规则解析器，实时推送 TodoList 规划、Tool 调用事件与 Token 流"""
    created_ts = int(time.time())
    CURRENT_USER_ID.set(user_id)
    CURRENT_DEVICE_ID.set(device_id)

    def make_chunk(delta_dict, tool_call_info=None, is_done=False):
        chunk = {
            "id": chat_id,
            "object": "chat.completion.chunk",
            "created": created_ts,
            "model": display_model,
            "choices": [
                {
                    "index": 0,
                    "delta": delta_dict,
                    "finish_reason": "stop" if is_done else None
                }
            ]
        }
        if tool_call_info:
            chunk["tool_call"] = tool_call_info
        return f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    if not device_id:
        yield make_chunk({"role": "assistant", "content": "当前暂无 TVBox 电视设备在线，请先在电视端启动并连接 AI 服务。"})
        yield make_chunk({}, is_done=True)
        yield "data: [DONE]\n\n"
        return

    openai_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
    if openai_key:
        try:
            from langchain_agent import create_tvbox_agent
            from langchain_core.messages import HumanMessage
            agent_graph = create_tvbox_agent(api_key=openai_key)
            has_emitted_role = False
            full_text = ""

            async for event in agent_graph.astream_events({"messages": [HumanMessage(content=prompt)]}, version="v2"):
                kind = event.get("event")
                # 1. 捕获 Tool 开始调用 (包含 write_todos / plan_todo_tasks 或普通设备 Tool)
                if kind == "on_tool_start":
                    tool_name = event.get("name", "")
                    tool_input = event.get("data", {}).get("input", {})
                    is_plan = (tool_name in ["write_todos", "plan_todo_tasks"])
                    
                    t_info = {
                        "name": tool_name,
                        "params": tool_input,
                        "status": "running",
                        "is_plan": is_plan
                    }
                    if is_plan and isinstance(tool_input, dict):
                        t_info["todos"] = tool_input.get("todos", [])
                        t_info["reasoning"] = tool_input.get("reasoning", "")

                    yield make_chunk(
                        {"role": "assistant"} if not has_emitted_role else {},
                        tool_call_info=t_info
                    )
                    has_emitted_role = True

                # 2. 捕获 Tool 执行完毕并获取 Observation
                elif kind == "on_tool_end":
                    tool_name = event.get("name", "")
                    tool_output = event.get("data", {}).get("output", "")
                    is_plan = (tool_name in ["write_todos", "plan_todo_tasks"])
                    yield make_chunk(
                        {},
                        tool_call_info={
                            "name": tool_name,
                            "observation": str(tool_output),
                            "status": "finished",
                            "is_plan": is_plan
                        }
                    )

                # 3. 捕获 LLM 生成的内容流 (逐 token)
                elif kind == "on_chat_model_stream":
                    chunk_obj = event.get("data", {}).get("chunk")
                    if chunk_obj:
                        content = chunk_obj.content if hasattr(chunk_obj, "content") else str(chunk_obj)
                        if isinstance(content, str) and content:
                            full_text += content
                            delta = {"content": content}
                            if not has_emitted_role:
                                delta["role"] = "assistant"
                                has_emitted_role = True
                            yield make_chunk(delta)

            if not has_emitted_role and not full_text:
                yield make_chunk({"role": "assistant", "content": "已为您执行相关操作。"})

            yield make_chunk({}, is_done=True)
            yield "data: [DONE]\n\n"
            return
        except Exception as e:
            logger.warning(f"LangChain Agent 流式执行异常 ({e})，回退到本地解析器...")

    # 本地规则解析器多意图流式回退
    sub_prompts = [p.strip() for p in re.split(r"[，,；;。!！\n]|然后|接着|并且|再", prompt) if p.strip()]
    if not sub_prompts:
        sub_prompts = [prompt]

    # 若有多意图，先推送一个伪 Todo 规划
    if len(sub_prompts) > 1:
        mock_todos = [{"id": i+1, "task_name": sp, "status": "pending"} for i, sp in enumerate(sub_prompts)]
        yield make_chunk(
            {"role": "assistant"},
            tool_call_info={"name": "write_todos", "params": {"todos": mock_todos}, "status": "finished", "is_plan": True, "todos": mock_todos}
        )

    all_replies = []
    for idx, sp in enumerate(sub_prompts):
        tool_name, tool_params, natural_reply = await parse_prompt_to_tool(sp)
        yield make_chunk(
            {},
            tool_call_info={"name": tool_name, "params": tool_params, "status": "running", "step_index": idx + 1}
        )

        exec_result = await device_mgr.send_tool_command(
            user_id=user_id,
            device_id=device_id,
            tool=tool_name,
            params=tool_params,
            timeout_sec=5.0
        )
        yield make_chunk(
            {},
            tool_call_info={"name": tool_name, "params": tool_params, "observation": str(exec_result), "status": "finished", "step_index": idx + 1}
        )
        all_replies.append(natural_reply)

    # 逐字输出文本回复
    combined_reply = "，".join(all_replies)
    for char in combined_reply:
        yield make_chunk({"content": char})
        await asyncio.sleep(0.015)

    yield make_chunk({}, is_done=True)
    yield "data: [DONE]\n\n"

@app.post("/v1/chat/completions")
@app.post("/v1//chat/completions")
async def chat_completions(
    req: ChatCompletionRequest, credential: DeviceCredential = Depends(require_api_key)
):
    """
    OpenAI 格式标准 Chat Completion 接口 (支持 stream=true 流式与非流式返回)
    """
    # 提取最后一条用户输入
    user_prompt = ""
    for msg in reversed(req.messages):
        if msg.role == "user":
            user_prompt = msg.content
            break

    if not user_prompt:
        user_prompt = req.messages[-1].content if req.messages else ""

    allowed_devices = await repository.list_devices(credential.user["_id"])
    requested_target = req.device_id or (req.model if req.model not in {None, "", "default", "auto", "tvbox-agent", "gpt-4o", "gpt-3.5-turbo"} else None)
    if requested_target and not await repository.find_device(credential.user["_id"], requested_target):
        raise HTTPException(status_code=404, detail="Target device not found")
    target_device_id = device_mgr.get_target_device_id(credential.user["_id"], allowed_devices, req.model, req.device_id)
    if not target_device_id and len([d for d in allowed_devices if (credential.user["_id"], d["device_id"]) in device_mgr.connections]) > 1:
        raise HTTPException(status_code=409, detail="Multiple devices are online; specify model or device_id")

    chat_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    created_ts = int(time.time())
    display_model = target_device_id or req.model or "tvbox-agent"

    # 流式返回 (SSE)
    if req.stream:
        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            stream_agent_or_parser(user_prompt, credential.user["_id"], target_device_id, chat_id, display_model),
            media_type="text/event-stream"
        )

    # 非流式标准 JSON 返回
    output_text, tool_call_info, _ = await execute_agent_or_parser(user_prompt, credential.user["_id"], target_device_id)
    return {
        "id": chat_id,
        "object": "chat.completion",
        "created": created_ts,
        "model": display_model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": output_text
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": len(user_prompt),
            "completion_tokens": len(output_text),
            "total_tokens": len(user_prompt) + len(output_text)
        },
        "tool_call": tool_call_info,
        "device_state": device_mgr.device_states.get((credential.user["_id"], target_device_id), {}) if target_device_id else {}
    }


@app.post("/api/v1/chat/completions")
async def platform_chat_completions(req: ChatCompletionRequest, user: dict = Depends(current_user)):
    """JWT-authenticated Web-console adapter over the same tenant-aware chat flow."""
    key = await repository.get_active_api_key(user["_id"])
    return await chat_completions(req, DeviceCredential(key=key or {}, user=user))

@app.websocket("/ws/v1/tvbox/{device_id}")
@app.websocket("/ws/tvbox/{device_id}")
async def tvbox_ws_endpoint(websocket: WebSocket, device_id: str):
    """
    TVBox 客户端 WebSocket 接入点
    """
    bearer_key = _extract_bearer_token(websocket.headers.get("authorization"))
    query_key = websocket.query_params.get("api_key")
    authenticated = await repository.authenticate_api_key(bearer_key or query_key or "")
    if not authenticated:
        await websocket.close(code=1008, reason="Invalid or missing API key")
        return
    key_doc, user = authenticated
    if user["status"] != 1:
        await websocket.close(code=1008, reason="API key owner is disabled")
        return
    if not await repository.find_device(user["_id"], device_id):
        await websocket.close(code=1008, reason="Device is not bound to API key owner")
        return

    connection_id = await device_mgr.register(user["_id"], device_id, websocket, key_doc["_id"])
    await repository.touch_device_online(user["_id"], device_id)
    try:
        while True:
            text = await websocket.receive_text()
            try:
                msg = json.loads(text)
                mtype = msg.get("type")
                if mtype == "ping":
                    await websocket.send_text(json.dumps({"type": "pong", "timestamp": msg.get("timestamp")}))
                elif mtype == "response":
                    device_mgr.resolve_response(user["_id"], device_id, msg)
                elif mtype == "event":
                    logger.info(f"📢 [Event from {device_id}] {msg.get('event_name')}: {msg.get('data')}")
                    device_mgr.update_state(user["_id"], device_id, msg.get("data", {}))
                elif mtype == "state_sync":
                    device_mgr.update_state(user["_id"], device_id, msg.get("data", {}))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        pass
    finally:
        device_mgr.unregister(user["_id"], device_id, connection_id)
        await repository.touch_device_online(user["_id"], device_id)

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    return "<h1>TVBox AI Controller Backend Running.</h1>"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=SERVER_PORT, reload=True, root_path=ROOT_PATH)
