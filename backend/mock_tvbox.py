#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TVBoxOS 客户端模拟器 (Mock TVBox Client)
通过 WebSocket 连接到 Python 后端，模拟真实电视盒子接收 JSON Tool 指令、执行播放/切台/搜索并回传响应。
"""

import sys
import json
import time
import asyncio
import logging
import os
from dotenv import load_dotenv

try:
    import websockets
except ImportError:
    print("请先安装 websockets 库: pip install websockets")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [MockTVBox] %(message)s")
logger = logging.getLogger("MockTVBox")

load_dotenv()
DEVICE_ID = os.getenv("TVBOX_DEVICE_ID", "tvbox_01")
DEVICE_API_KEY = os.getenv("TVBOX_API_KEY", "")
WS_URL = os.getenv("TVBOX_WS_URL", f"ws://127.0.0.1:8000/ws/v1/tvbox/{DEVICE_ID}")

# 模拟电视当前状态
current_state = {
    "current_activity": "HomeActivity",
    "is_playing": False,
    "media_name": "",
    "episode": 1,
    "position_sec": 0,
    "duration_sec": 0,
    "channel_name": ""
}

async def handle_command(ws, cmd: dict):
    req_id = cmd.get("request_id")
    tool = cmd.get("tool")
    params = cmd.get("params", {})
    
    logger.info(f"📥 接收到后端 Tool 指令: [{tool}] (ID: {req_id})")
    logger.info(f"   参数内容: {json.dumps(params, ensure_ascii=False)}")

    # 模拟真实电视执行耗时
    await asyncio.sleep(0.3)

    resp_data = {}
    msg = "执行成功"

    if tool == "play_vod":
        vod_name = params.get("vod_name", "未知影片")
        ep = params.get("episode_index", 1)
        current_state["is_playing"] = True
        current_state["media_name"] = vod_name
        current_state["episode"] = ep
        current_state["current_activity"] = "DetailActivity"
        current_state["position_sec"] = 0
        current_state["duration_sec"] = 2700
        logger.info(f"▶️ [电视画面] 开始全屏播放《{vod_name}》第 {ep} 集！")
        resp_data = {"vod_name": vod_name, "episode": ep, "state": "playing"}

    elif tool == "switch_live_channel":
        ch_name = params.get("channel_name", "CCTV-1")
        current_state["is_playing"] = True
        current_state["channel_name"] = ch_name
        current_state["current_activity"] = "LivePlayActivity"
        logger.info(f"📺 [电视画面] 直播已切换到频道：【{ch_name}】！")
        resp_data = {"channel": ch_name, "state": "live_streaming"}

    elif tool == "control_playback":
        action = params.get("action")
        if action == "pause":
            current_state["is_playing"] = False
            logger.info("⏸️ [电视画面] 视频已暂停")
        elif action == "resume":
            current_state["is_playing"] = True
            logger.info("▶️ [电视画面] 视频继续播放")
        elif action == "next":
            current_state["episode"] += 1
            logger.info(f"⏭️ [电视画面] 切换到下一集 (第 {current_state['episode']} 集)")
        elif action == "prev":
            current_state["episode"] = max(1, current_state["episode"] - 1)
            logger.info(f"⏮️ [电视画面] 切换到上一集 (第 {current_state['episode']} 集)")
        elif action == "seek":
            sec = params.get("seek_seconds", 30)
            current_state["position_sec"] += sec
            logger.info(f"⏩ [电视画面] 进度调整: {'+' if sec>0 else ''}{sec} 秒")
        elif action == "speed":
            sp = params.get("speed", 1.0)
            logger.info(f"⚡ [电视画面] 播放倍速调整为: {sp}x")
        resp_data = current_state

    elif tool == "search_media":
        kw = params.get("keyword", "")
        current_state["current_activity"] = "SearchActivity"
        logger.info(f"🔍 [电视画面] 正在搜索关键词: 【{kw}】...")
        resp_data = {
            "keyword": kw,
            "results_count": 3,
            "items": [
                {"title": f"{kw} 第1季", "type": "电视剧", "episodes": 39},
                {"title": f"{kw} 电影版", "type": "电影", "duration": "120分钟"},
                {"title": f"{kw} 纪录片", "type": "纪录片", "episodes": 4}
            ]
        }

    elif tool == "filter_category":
        cat = params.get("category_name", "电影")
        year = params.get("year", "全部")
        area = params.get("area", "全部")
        genre = params.get("genre", "全部")
        logger.info(f"🏷️ [电视画面] 主页分类筛选: 分类={cat} | 年份={year} | 地区={area} | 题材={genre}")
        resp_data = {"category": cat, "filters": {"year": year, "area": area, "genre": genre}, "status": "filtered"}

    elif tool == "control_subtitle_and_danmaku":
        danmaku = params.get("danmaku_enable")
        sub_offset = params.get("subtitle_offset_ms")
        logger.info(f"💬 [电视画面] 弹幕/字幕调节: 弹幕开关={danmaku} | 字幕时间轴偏移={sub_offset}ms")
        resp_data = {"danmaku": danmaku, "subtitle_offset_ms": sub_offset, "status": "applied"}

    elif tool == "select_search_item":
        idx = params.get("index", 1)
        title = params.get("vod_name") or f"影视剧第{idx}项"
        current_state["current_activity"] = "DetailActivity"
        current_state["media_name"] = title
        current_state["is_playing"] = False
        logger.info(f"👉 [电视画面] 选中搜索结果 [{idx}] 《{title}》，进入详情页")
        resp_data = {
            "current_page": "DetailActivity",
            "page_title": f"《{title}》详情页",
            "title": title,
            "current_line": "极速专线",
            "available_lines": ["极速专线", "非凡线路", "蓝光秒播", "夸克网盘"],
            "current_episode": "第1集",
            "current_episode_index": 1,
            "total_episodes": 30,
            "is_collected": False,
            "desc": f"《{title}》全网聚合高清资源，画质细腻，剧情精彩纷呈。",
            "available_actions": ["立即播放", "切换线路", "选择集数", "收藏", "全屏"]
        }

    elif tool == "control_detail_page":
        action = params.get("action", "play")
        target_val = params.get("target_value", "")
        if action == "switch_line":
            current_state["current_line"] = target_val or "非凡线路"
            logger.info(f"🔄 [电视画面] 详情页切换播放线路为: 【{current_state['current_line']}】")
            resp_data = {"current_line": current_state["current_line"], "status": "line_switched"}
        elif action == "select_episode":
            ep = int(target_val) if str(target_val).isdigit() else 1
            current_state["episode"] = ep
            logger.info(f"🔢 [电视画面] 详情页切换集数为: 第 {ep} 集")
            resp_data = {"current_episode_index": ep, "current_episode": f"第{ep}集", "status": "episode_selected"}
        elif action == "fullscreen":
            current_state["is_playing"] = True
            logger.info("🔲 [电视画面] 播放器已切换为全屏大屏模式")
            resp_data = {"is_fullscreen": True, "is_playing": True, "status": "fullscreen_activated"}
        elif action == "toggle_favorite":
            logger.info("⭐ [电视画面] 收藏状态已切换")
            resp_data = {"is_collected": True, "status": "favorite_toggled"}
        else:
            current_state["is_playing"] = True
            logger.info(f"🎬 [电视画面] 详情页执行操作: {action} (目标: {target_val})")
            resp_data = {"action": action, "target_value": target_val, "status": "success"}

    elif tool == "get_live_epg":
        ch = params.get("channel_name", "CCTV-1")
        logger.info(f"📋 [电视画面] 获取频道【{ch}】节目单")
        resp_data = {
            "channel": ch,
            "programs": [
                {"time": "19:00", "title": "新闻联播", "status": "finished"},
                {"time": "19:38", "title": "焦点访谈", "status": "playing"},
                {"time": "20:05", "title": "黄金档剧场", "status": "upcoming"}
            ]
        }

    elif tool == "manage_favorite":
        action = params.get("action", "add")
        vname = params.get("vod_name", "当前影片")
        logger.info(f"⭐ [电视画面] 收藏夹操作: [{action}] 影片《{vname}》")
        resp_data = {"action": action, "vod_name": vname, "status": "success"}

    elif tool == "manage_history":
        action = params.get("action", "get_list")
        logger.info(f"🕒 [电视画面] 历史记录操作: [{action}]")
        resp_data = {"action": action, "history_count": 12, "status": "success"}

    elif tool == "set_api_source":
        api_url = params.get("api_url", "")
        logger.info(f"⚙️ [电视画面] 更新系统接口源: {api_url}")
        resp_data = {"api_url": api_url, "status": "source_loaded_successfully"}

    elif tool == "switch_home_source":
        site_key = params.get("site_key", "")
        logger.info(f"🔄 [电视画面] 切换主页数据源站点为: 【{site_key}】")
        resp_data = {"site_key": site_key, "status": "site_switched"}

    elif tool == "navigate_to_page":
        target = params.get("target_page", "home")
        current_state["current_activity"] = f"{target.capitalize()}Activity"
        logger.info(f"🧭 [电视画面] 跳转到页面: 【{target}】")
        resp_data = {"current_page": target}

    elif tool == "go_back":
        logger.info("↩️ [电视画面] 触发遥控器返回键 (Back)")
        resp_data = {"action": "back_pressed"}

    elif tool == "send_key_event":
        key = params.get("key_code", "OK")
        logger.info(f"🎮 [电视按键] 接收到按键: [{key}]")
        resp_data = {"key_code": key}

    elif tool == "get_device_state":
        logger.info("📊 [电视状态] 上报当前设备状态")
        resp_data = current_state

    else:
        logger.warning(f"⚠️ 未知 Tool 指令: {tool}")
        msg = f"未知的工具名称 {tool}"

    # 封装并回传执行响应
    response = {
        "type": "response",
        "request_id": req_id,
        "status": "success" if msg == "执行成功" else "failed",
        "message": msg,
        "data": resp_data
    }
    
    await ws.send(json.dumps(response))
    logger.info(f"📤 已向 Python 后端回传执行结果 (ID: {req_id})\n")

async def mock_tvbox_loop():
    if not DEVICE_API_KEY:
        raise RuntimeError("请先设置 TVBOX_API_KEY（用户级 API Key）")
    while True:
        try:
            logger.info(f"正在连接 Python 后端: {WS_URL} ...")
            separator = "&" if "?" in WS_URL else "?"
            authenticated_url = f"{WS_URL}{separator}api_key={DEVICE_API_KEY}"
            async with websockets.connect(authenticated_url) as ws:
                logger.info(f"🎉 成功连接到 Python 后端！等待接收 AI Tool 指令...")
                
                # 发送首次上线注册状态
                await ws.send(json.dumps({
                    "type": "state_sync",
                    "device_id": DEVICE_ID,
                    "data": current_state
                }))

                async for message in ws:
                    try:
                        cmd = json.loads(message)
                        if cmd.get("type") == "command":
                            await handle_command(ws, cmd)
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            logger.error(f"连接断开或失败 ({e})，3 秒后尝试重连...")
            await asyncio.sleep(3)

if __name__ == "__main__":
    print("=" * 60)
    print("📺 TVBox 虚拟客户端已启动")
    print(f"📡 目标连接: {WS_URL}")
    print("=" * 60)
    asyncio.run(mock_tvbox_loop())
