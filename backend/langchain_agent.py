#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TVBox LangChain Agent 实现模块
严格基于 docs/UI_INTERACTIONS_AND_TOOLS_ANALYSIS.md 定义的 15 大核心 Tools
支持通过 LangChain create_tool_calling_agent 与大模型进行多轮对话与精确控制
"""

import os
import json
import logging
from typing import Optional, List, Dict, Any, Literal, Union, Sequence
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.graph.state import CompiledStateGraph

# 引入 WebSocket 连接管理器（在 server.py 中定义的 device_mgr）
from server import CURRENT_DEVICE_ID, device_mgr

load_dotenv()
logger = logging.getLogger("TVBoxLangChainAgent")

def get_dev(device_id: Optional[str] = None) -> Optional[str]:
    """返回请求入口已经过租户校验的目标设备。"""
    return device_id or CURRENT_DEVICE_ID.get()

def format_observation(tool_name: str, res: Any) -> str:
    """格式化 Tool 执行回执，构建包含 TVBox 实时页面快照与合法可用操作的 Observation，驱动下一轮大模型严格基于真实状态推理"""
    if not isinstance(res, dict):
        return f"Tool [{tool_name}] 执行返回: {res}"

    status = res.get("status", "unknown")
    msg = res.get("message", "")
    data = res.get("data", {}) if isinstance(res.get("data"), dict) else {}

    lines = [f"【Tool {tool_name} 执行结果】: {status} ({msg})"]
    lines.append("──────────────────────────────────────────")
    lines.append("【📺 TVBox 当前最新真实屏幕状态快照 (必须基于此状态进行下一步决策)】:")

    cur_page = data.get("current_page")
    page_title = data.get("page_title")
    if cur_page or page_title:
        lines.append(f"• 当前活跃界面: {page_title or ''} ({cur_page or ''})")

    # 1. 极速搜索与搜索结果页面状态感知
    if cur_page in ["FastSearchActivity", "SearchActivity"]:
        results = data.get("search_results", [])
        result_count = data.get("result_count", len(results))
        if result_count == 0 or not results:
            lines.append("• 搜索结果: 【⚠️ 没找到数据 / 搜索结果为 0 条】")
            lines.append("• ⚠️【严格禁令与决策要求】: 当前电视端搜索结果列表为空！严禁调用 select_search_item 或尝试进入详情页/播放！请尝试更换关键词重新搜索（如去除修饰词、搜索简称），或如实告知用户当前所有数据源均未检索到该影视。")
        else:
            lines.append(f"• 搜索结果 (共 {len(results)} 条，请仔细比对剧名选择最匹配的序号):")
            for item in results[:6]:
                lines.append(f"   [{item.get('index')}] 《{item.get('title')}》 ({item.get('source_key')}, {item.get('note', '')})")

    # 2. 视频详情页状态感知
    elif cur_page == "DetailActivity":
        if data.get("title"): lines.append(f"• 影片名称: 《{data.get('title')}》")
        if data.get("current_line"): lines.append(f"• 当前选中线路: {data.get('current_line')}")
        if data.get("available_lines"): lines.append(f"• 可选播放线路: {', '.join([str(x) for x in data.get('available_lines', [])])}")
        if data.get("current_episode"): lines.append(f"• 当前集数: {data.get('current_episode')} (第 {data.get('current_episode_index', 1)} 集)")
        if data.get("total_episodes"): lines.append(f"• 总集数: {data.get('total_episodes')} 集")
        if "is_collected" in data: lines.append(f"• 收藏状态: {'已收藏' if data.get('is_collected') else '未收藏'}")
        if data.get("desc"): lines.append(f"• 剧情概要: {str(data.get('desc'))[:120]}...")

    # 3. 电视直播页面状态感知
    elif cur_page == "LivePlayActivity":
        if data.get("channel_name"): lines.append(f"• 当前电视频道: {data.get('channel_name')} (台号: {data.get('channel_number', '')})")

    # 4. 播放器与窗口状态
    if "is_playing" in data:
        lines.append(f"• 播放器状态: {'正在播放' if data.get('is_playing') else '未播放/已暂停'}")
    if "is_fullscreen" in data:
        lines.append(f"• 窗口状态: {'全屏大播放器' if data.get('is_fullscreen') else '小窗预览'}")

    # 5. 当前屏幕合法可用操作
    avail = data.get("available_actions", [])
    if avail:
        lines.append(f"• 当前屏幕允许执行的操作: {', '.join([str(x) for x in avail])}")

    lines.append("──────────────────────────────────────────")
    lines.append("【💡 下一步决策必须严格依据上述最新真实状态进行。若目标页面/条目不满足前置条件，必须立即调整决策，严禁盲目执行后续步骤！】")
    return "\n".join(lines)

# ==============================================================================
# 1. 导航与页面跳转工具 (Navigation Tools)
# ==============================================================================

class NavigateToPageInput(BaseModel):
    target_page: Literal["home", "search", "fast_search", "live", "history", "collect", "setting", "push", "local_file"] = Field(
        description="目标页面标识：'home'(主页), 'search'(搜索页), 'fast_search'(极速搜索), 'live'(直播页), 'history'(历史记录), 'collect'(我的收藏), 'setting'(设置中心), 'push'(局域网推送等待), 'local_file'(本地媒体)"
    )

@tool("navigate_to_page", args_schema=NavigateToPageInput)
async def navigate_to_page(target_page: str, device_id: Optional[str] = None) -> str:
    """跳转到 TVBoxOS 的指定功能界面（如主页、搜索、直播、历史、收藏、设置等）。"""
    res = await device_mgr.send_tool_command(device_id=get_dev(device_id), tool="navigate_to_page", params={"target_page": target_page})
    return format_observation("navigate_to_page", res)


class GoBackInput(BaseModel):
    reason: Optional[str] = Field(default=None, description="返回原因，可选")

@tool("go_back", args_schema=GoBackInput)
async def go_back(reason: Optional[str] = None, device_id: Optional[str] = None) -> str:
    """模拟遥控器返回键（Back），用于退出当前弹窗浮层、关闭菜单或返回上一级页面。"""
    res = await device_mgr.send_tool_command(device_id=get_dev(device_id), tool="go_back", params={})
    return format_observation("go_back", res)


# ==============================================================================
# 2. 搜索与检索工具 (Search & Filter Tools)
# ==============================================================================

class SearchMediaInput(BaseModel):
    keyword: str = Field(description="搜索关键词（如：繁花、狂飙、阿凡达、流浪地球）")
    fast_mode: bool = Field(default=True, description="是否使用全网极速多源聚合搜索模式，默认为 true")
    source_key: Optional[str] = Field(default=None, description="可选，指定在某一个特定数据源站点中搜索")

@tool("search_media", args_schema=SearchMediaInput)
async def search_media(keyword: str, fast_mode: bool = True, source_key: Optional[str] = None, device_id: Optional[str] = None) -> str:
    """在 TVBox 影视库中搜索电影、电视剧、综艺、动漫等资源。"""
    params = {"keyword": keyword, "fast_mode": fast_mode}
    if source_key: params["source_key"] = source_key
    res = await device_mgr.send_tool_command(device_id=get_dev(device_id), tool="search_media", params=params)
    return format_observation("search_media", res)


class FilterCategoryInput(BaseModel):
    category_name: str = Field(description="主页分类名称，如：电影、电视剧、动漫、综艺、纪录片")
    year: Optional[str] = Field(default=None, description="年份筛选，如：2024, 2023, 2020年代")
    area: Optional[str] = Field(default=None, description="地区筛选，如：大陆, 香港, 台湾, 美国, 日本, 韩国")
    genre: Optional[str] = Field(default=None, description="题材类型筛选，如：动作, 悬疑, 科幻, 喜剧, 爱情")
    sort_by: Optional[Literal["latest", "popular", "rating"]] = Field(default="latest", description="排序规则：'latest'(最新), 'popular'(最热), 'rating'(评分最高)")

@tool("filter_category", args_schema=FilterCategoryInput)
async def filter_category(category_name: str, year: Optional[str] = None, area: Optional[str] = None, genre: Optional[str] = None, sort_by: Optional[str] = "latest", device_id: Optional[str] = None) -> str:
    """在主页指定影视分类下，根据年份、地区、题材类型及排序规则进行多维度组合筛选过滤。"""
    params = {"category_name": category_name}
    if year: params["year"] = year
    if area: params["area"] = area
    if genre: params["genre"] = genre
    if sort_by: params["sort_by"] = sort_by
    res = await device_mgr.send_tool_command(device_id=get_dev(device_id), tool="filter_category", params=params)
    return format_observation("filter_category", res)


class SelectSearchItemInput(BaseModel):
    index: int = Field(description="搜索结果中海报右上角标明的数字序号（从1开始计数，如 1, 2, 3, 4...）")
    action: Optional[Literal["play", "detail"]] = Field(default="play", description="动作：'play'(直接播放，默认), 'detail'(查看详情)")

@tool("select_search_item", args_schema=SelectSearchItemInput)
async def select_search_item(index: int, action: Optional[str] = "play", device_id: Optional[str] = None) -> str:
    """在搜索结果列表中根据屏幕上海报右上角标注的数字序号（1, 2, 3...）选择并播放对应影片或进入详情页。"""
    target = get_dev(device_id)
    res = await device_mgr.send_tool_command(device_id=target, tool="select_search_item", params={"index": index, "action": action})
    return format_observation("select_search_item", res)


# ==============================================================================
# 3. 详情页交互控制工具 (Detail Page Tools)
# ==============================================================================

class ControlDetailPageInput(BaseModel):
    action: Literal[
        "fullscreen",       # 全屏 / 立即播放
        "quick_search",     # 打开全网快速搜索
        "show_desc",        # 弹窗显示完整剧情简介
        "toggle_favorite",  # 收藏 / 取消收藏
        "change_source",    # 弹出切源菜单
        "switch_line",      # 切换线路 (配合 target_value 填线路名或序号)
        "select_episode",   # 切换播放集数 (配合 target_value 填集数序号如 "3" 或 "第3集")
        "sort_episodes"     # 切换剧集正序/倒序
    ] = Field(description="在视频详情页执行的具体动作")
    target_value: Optional[str] = Field(default=None, description="操作附加值，如指定的线路名称（如'非凡'）、集数序号（如'3'）或源名称")

@tool("control_detail_page", args_schema=ControlDetailPageInput)
async def control_detail_page(action: str, target_value: Optional[str] = None, device_id: Optional[str] = None) -> str:
    """控制当前视频详情页的交互按钮，支持全屏、收藏、切源、切线路、选集、查看简介、快速搜索。"""
    res = await device_mgr.send_tool_command(
        device_id=get_dev(device_id),
        tool="control_detail_page",
        params={"action": action, "target_value": target_value}
    )
    return format_observation("control_detail_page", res)


# ==============================================================================
# 4. 点播与播放控制工具 (VOD Playback Tools)
# ==============================================================================

class PlayVodInput(BaseModel):
    vod_id: Optional[str] = Field(default=None, description="影片 ID 或 片名（如'繁花'）")
    vod_name: Optional[str] = Field(default=None, description="影片名称，如：狂飙、庆余年第二季、繁花")
    item_index: Optional[int] = Field(default=None, description="搜索结果列表中的序号（例如用户说'播放第1个'、'看第3部'、'选2号'时填入 1, 2, 3...）")
    episode_index: int = Field(default=1, description="播放第几集（从1开始计数），默认为第1集或上次历史进度")
    source_key: Optional[str] = Field(default=None, description="可选，指定数据源站点 key")
    line_flag: Optional[str] = Field(default=None, description="可选，播放线路标志（如：4K原画、极速线路、蓝光）")

@tool("play_vod", args_schema=PlayVodInput)
async def play_vod(vod_id: Optional[str] = None, vod_name: Optional[str] = None, item_index: Optional[int] = None, episode_index: int = 1, source_key: Optional[str] = None, line_flag: Optional[str] = None, device_id: Optional[str] = None) -> str:
    """打开指定影片或按搜索结果序号直接播放。当用户表达想看某部影片或在搜索页指定'第几个'时调用。"""
    final_name = vod_name or vod_id or (f"第{item_index}个" if item_index else "未知影片")
    params = {"vod_id": vod_id or final_name, "vod_name": final_name, "episode_index": episode_index}
    if item_index is not None: params["item_index"] = item_index
    if source_key: params["source_key"] = source_key
    if line_flag: params["line_flag"] = line_flag
    res = await device_mgr.send_tool_command(device_id=get_dev(device_id), tool="play_vod", params=params)
    return format_observation("play_vod", res)


class ControlPlaybackInput(BaseModel):
    action: Literal["pause", "resume", "toggle_play", "next_episode", "prev_episode", "seek_to", "seek_offset", "set_speed", "change_scale", "retry"] = Field(
        description="控制动作指令：'pause'(暂停), 'resume'(恢复播放), 'toggle_play'(播放/暂停切换), 'next_episode'(下一集), 'prev_episode'(上一集), 'seek_to'(跳转到指定秒), 'seek_offset'(快进快退偏移量), 'set_speed'(设置倍速), 'change_scale'(调整比例), 'retry'(重试重播)"
    )
    seek_seconds: Optional[int] = Field(default=None, description="当 action 为 seek_to（绝对时间）或 seek_offset（相对偏移如 +60秒 或 -30秒）时的秒数")
    speed: Optional[float] = Field(default=None, description="当 action 为 set_speed 时的倍速值（如 0.75, 1.0, 1.25, 1.5, 2.0, 3.0）")
    scale: Optional[Literal["default", "16:9", "4:3", "match_screen", "original"]] = Field(default=None, description="画面比例")

@tool("control_playback", args_schema=ControlPlaybackInput)
async def control_playback(action: str, seek_seconds: Optional[int] = None, speed: Optional[float] = None, scale: Optional[str] = None, device_id: Optional[str] = None) -> str:
    """控制当前正在播放的视频，如暂停、恢复、快进、快退、切集、倍速调节或画面比例切换。"""
    params = {"action": action}
    if seek_seconds is not None: params["seek_seconds"] = seek_seconds
    if speed is not None: params["speed"] = speed
    if scale: params["scale"] = scale
    res = await device_mgr.send_tool_command(device_id=get_dev(device_id), tool="control_playback", params=params)
    return format_observation("control_playback", res)


class ControlSubtitleAndDanmakuInput(BaseModel):
    danmaku_enable: Optional[bool] = Field(default=None, description="是否开启弹幕显示")
    danmaku_speed: Optional[float] = Field(default=None, description="弹幕滚动速度（如 1.0, 1.5）")
    danmaku_size: Optional[int] = Field(default=None, description="弹幕字体大小")
    subtitle_track_index: Optional[int] = Field(default=None, description="字幕轨道索引号")
    subtitle_offset_ms: Optional[int] = Field(default=None, description="字幕时间轴微调偏移量（毫秒，正数延后，负数提前）")

@tool("control_subtitle_and_danmaku", args_schema=ControlSubtitleAndDanmakuInput)
async def control_subtitle_and_danmaku(
    danmaku_enable: Optional[bool] = None,
    danmaku_speed: Optional[float] = None,
    danmaku_size: Optional[int] = None,
    subtitle_track_index: Optional[int] = None,
    subtitle_offset_ms: Optional[int] = None,
    device_id: Optional[str] = None
) -> str:
    """设置播放器的字幕与弹幕（开启/关闭弹幕、调节弹幕速度大小、切换字幕轨、调整字幕时间轴不同步问题）。"""
    params = {}
    if danmaku_enable is not None: params["danmaku_enable"] = danmaku_enable
    if danmaku_speed is not None: params["danmaku_speed"] = danmaku_speed
    if danmaku_size is not None: params["danmaku_size"] = danmaku_size
    if subtitle_track_index is not None: params["subtitle_track_index"] = subtitle_track_index
    if subtitle_offset_ms is not None: params["subtitle_offset_ms"] = subtitle_offset_ms
    res = await device_mgr.send_tool_command(device_id=get_dev(device_id), tool="control_subtitle_and_danmaku", params=params)
    return format_observation("control_subtitle_and_danmaku", res)


# ==============================================================================
# 5. 直播控制工具 (Live Streaming Tools)
# ==============================================================================

class SwitchLiveChannelInput(BaseModel):
    channel_name: Optional[str] = Field(default=None, description="电视频道名称（如 CCTV-1、CCTV-5、浙江卫视、湖南卫视、东方卫视）")
    channel_number: Optional[int] = Field(default=None, description="频道数字台号（如 1, 5, 102）")
    group_name: Optional[str] = Field(default=None, description="频道分组类别（如 央视频道、卫视频道、地方频道、体育专区）")
    line_index: Optional[int] = Field(default=None, description="指定切换到第几条直播信号线路（从0或1开始）")

@tool("switch_live_channel", args_schema=SwitchLiveChannelInput)
async def switch_live_channel(channel_name: Optional[str] = None, channel_number: Optional[int] = None, group_name: Optional[str] = None, line_index: Optional[int] = None, device_id: Optional[str] = None) -> str:
    """切换电视直播频道或切换直播信号源线路。当用户要求看央视、卫视、某个电视台或看比赛直播时调用。"""
    params = {}
    if channel_name: params["channel_name"] = channel_name
    if channel_number is not None: params["channel_number"] = channel_number
    if group_name: params["group_name"] = group_name
    if line_index is not None: params["line_index"] = line_index
    res = await device_mgr.send_tool_command(device_id=get_dev(device_id), tool="switch_live_channel", params=params)
    return format_observation("switch_live_channel", res)


class GetLiveEpgInput(BaseModel):
    channel_name: str = Field(description="频道名称，如：CCTV-1, CCTV-5, 浙江卫视")
    date: Optional[str] = Field(default=None, description="查询日期，格式 YYYY-MM-DD，默认为今天")

@tool("get_live_epg", args_schema=GetLiveEpgInput)
async def get_live_epg(channel_name: str, date: Optional[str] = None, device_id: Optional[str] = None) -> str:
    """获取指定电视频道的电子节目单 (EPG)，包含今天正在播放及后续即将播放的节目时间表。"""
    params = {"channel_name": channel_name}
    if date: params["date"] = date
    res = await device_mgr.send_tool_command(device_id=get_dev(device_id), tool="get_live_epg", params=params)
    return format_observation("get_live_epg", res)


# ==============================================================================
# 6. 历史与收藏管理工具 (User Data Tools)
# ==============================================================================

class ManageFavoriteInput(BaseModel):
    action: Literal["add", "remove", "clear", "list"] = Field(
        description="操作动作：'add'(添加收藏), 'remove'(取消收藏), 'clear'(清空所有收藏), 'list'(获取收藏列表)"
    )
    vod_id: Optional[str] = Field(default=None, description="影片 ID")
    vod_name: Optional[str] = Field(default=None, description="影片名称")
    source_key: Optional[str] = Field(default=None, description="站点数据源 Key")

@tool("manage_favorite", args_schema=ManageFavoriteInput)
async def manage_favorite(action: str, vod_id: Optional[str] = None, vod_name: Optional[str] = None, source_key: Optional[str] = None, device_id: Optional[str] = None) -> str:
    """管理电视上的影视收藏夹（收藏当前影片、取消收藏某部影片、查看收藏列表或一键清空收藏）。"""
    params = {"action": action}
    if vod_id: params["vod_id"] = vod_id
    if vod_name: params["vod_name"] = vod_name
    if source_key: params["source_key"] = source_key
    res = await device_mgr.send_tool_command(device_id=get_dev(device_id), tool="manage_favorite", params=params)
    return format_observation("manage_favorite", res)


class ManageHistoryInput(BaseModel):
    action: Literal["get_list", "delete_item", "clear_all"] = Field(
        description="操作动作：'get_list'(获取播放历史记录), 'delete_item'(删除单条历史记录), 'clear_all'(清空全部播放历史)"
    )
    vod_id: Optional[str] = Field(default=None, description="要删除的历史记录影片 ID 或 名称")

@tool("manage_history", args_schema=ManageHistoryInput)
async def manage_history(action: str, vod_id: Optional[str] = None, device_id: Optional[str] = None) -> str:
    """管理电视上的播放历史记录（查看最近观影记录、删除某条记录或清空播放历史）。"""
    params = {"action": action}
    if vod_id: params["vod_id"] = vod_id
    res = await device_mgr.send_tool_command(device_id=get_dev(device_id), tool="manage_history", params=params)
    return format_observation("manage_history", res)


# ==============================================================================
# 7. 系统配置与站点源管理工具 (System & Settings Tools)
# ==============================================================================

class SetApiSourceInput(BaseModel):
    api_url: str = Field(description="接口配置地址 URL（例如：http://.../tvbox.json）")
    source_name: Optional[str] = Field(default=None, description="数据源别名备注")

@tool("set_api_source", args_schema=SetApiSourceInput)
async def set_api_source(api_url: str, source_name: Optional[str] = None, device_id: Optional[str] = None) -> str:
    """设置或切换 TVBoxOS 的主配置数据源接口 URL 地址。"""
    params = {"api_url": api_url}
    if source_name: params["source_name"] = source_name
    res = await device_mgr.send_tool_command(device_id=get_dev(device_id), tool="set_api_source", params=params)
    return format_observation("set_api_source", res)


class SwitchHomeSourceInput(BaseModel):
    site_key: str = Field(description="站点 key 或 站点名称（如：csp_Douban、豆瓣、极速影视、七七等）")

@tool("switch_home_source", args_schema=SwitchHomeSourceInput)
async def switch_home_source(site_key: str, device_id: Optional[str] = None) -> str:
    """切换主页默认使用的数据源站点（首页首页推荐与分类将加载该站点的内容）。"""
    res = await device_mgr.send_tool_command(device_id=get_dev(device_id), tool="switch_home_source", params={"site_key": site_key})
    return format_observation("switch_home_source", res)


# ==============================================================================
# 8. 遥控按键与设备状态感知工具 (Remote Key & State Tools)
# ==============================================================================

class SendKeyEventInput(BaseModel):
    key_code: Literal["DPAD_UP", "DPAD_DOWN", "DPAD_LEFT", "DPAD_RIGHT", "DPAD_CENTER", "BACK", "MENU", "HOME", "VOLUME_UP", "VOLUME_DOWN"] = Field(
        description="遥控器物理按键编码：'DPAD_UP'(上), 'DPAD_DOWN'(下), 'DPAD_LEFT'(左), 'DPAD_RIGHT'(右), 'DPAD_CENTER'(OK确认), 'BACK'(返回), 'MENU'(菜单), 'HOME'(主页), 'VOLUME_UP'(音量加), 'VOLUME_DOWN'(音量减)"
    )

@tool("send_key_event", args_schema=SendKeyEventInput)
async def send_key_event(key_code: str, device_id: Optional[str] = None) -> str:
    """模拟实体红外/蓝牙遥控器的物理按键点击。"""
    res = await device_mgr.send_tool_command(device_id=get_dev(device_id), tool="send_key_event", params={"key_code": key_code})
    return format_observation("send_key_event", res)


class GetDeviceStateInput(BaseModel):
    include_full_shadow: bool = Field(default=True, description="是否获取完整的设备影子状态")

@tool("get_device_state", args_schema=GetDeviceStateInput)
async def get_device_state(include_full_shadow: bool = True, device_id: Optional[str] = None) -> str:
    """获取 TVBox 电视盒子的当前实时画面与运行状态（当前活跃界面、正在播放的影片名/集数/播放进度/倍速、当前电视频道、音量等）。在需要确认电视当前状态时调用。"""
    res = await device_mgr.send_tool_command(device_id=get_dev(device_id), tool="get_device_state", params={"include_full_shadow": include_full_shadow})
    return format_observation("get_device_state", res)


# ==============================================================================
# 7. LangChain TodoListMiddleware 中间件规范实现
# 参考: https://docs.langchain.com/oss/javascript/langchain/middleware/built-in#to-do-list
# ==============================================================================

# ==============================================================================
# 7. LangChain 官方 TodoListMiddleware 中间件配置
# 参考: https://docs.langchain.com/oss/python/releases/langchain-v1#create_agent
# ==============================================================================

try:
    from langchain.agents.middleware import TodoListMiddleware
except ImportError:
    TodoListMiddleware = None

SYSTEM_TODO_PROMPT = """## `write_todos`

你拥有 `write_todos` 工具来管理和规划多步骤控制目标。
当用户的输入包含 2 个或以上连续操作/复合意图时（例如：'先搜繁花，选第1个，换线路看第3集并开弹幕' 或 '暂停播放，调大音量，然后打开我的收藏'），必须优先调用 `write_todos` 工具制定/更新 TodoList 待办清单。

【⚠️ 核心准则：电视端真实状态感知高于一切预设计划 (Perception Overrides Plan)】：
1. **每轮执行必须依据 TVBox 最新返回的 Observation 真实状态决策**：
   - 每次 Tool 执行完成后，系统都会返回 TVBox 屏幕当前的最新状态快照。
   - 你**必须仔细阅读上一轮返回的 Observation**，严格基于真实的电视屏幕状态决定下一步动作。严禁机械化死板执行 TodoList 中的旧计划！
2. **搜索页面结果校验与空结果处理规则 (Search Guard)**：
   - 若 Observation 显示【⚠️ 没找到数据 / 搜索结果为 0 条】：**严禁调用 `select_search_item` 或进入详情页/起播！** 必须尝试更换搜索关键词重新调用 `search_media` 或如实向用户说明未找到。
   - 若 Observation 中有搜索结果列表：必须仔细比对剧名选择最匹配的序号。
3. **页面前置条件守卫 (Page Guard)**：
   - `control_detail_page` 只能在 `DetailActivity`（视频详情页）调用。
   - `control_playback` 只能在视频正在播放时调用。
4. **失败快速中断与真实反馈 (Fail-Fast & Truthful Feedback)**：
   - 一旦前置步骤执行失败，立即中止后续无意义的连带操作，如实向用户汇报真实原因。
"""

def todo_list_middleware():
    """创建并返回配置好 TVBox 业务准则的官方 TodoListMiddleware 实例"""
    return TodoListMiddleware(system_prompt=SYSTEM_TODO_PROMPT) if TodoListMiddleware else None


# ==============================================================================
# 全量电视设备控制工具集 (16 个硬件控制 Tool)
# ==============================================================================

TVBOX_DEVICE_TOOLS = [
    # 导航与按键
    navigate_to_page,
    go_back,
    send_key_event,
    
    # 搜索与筛选
    search_media,
    select_search_item,
    filter_category,

    # 详情页专属交互
    control_detail_page,
    
    # 点播播放与控制
    play_vod,
    control_playback,
    control_subtitle_and_danmaku,
    
    # 电视直播与节目单
    switch_live_channel,
    get_live_epg,
    
    # 用户数据与设置
    manage_favorite,
    manage_history,
    set_api_source,
    switch_home_source,
    
    # 设备状态感知
    get_device_state
]

_todo_middleware = todo_list_middleware()
TVBOX_ALL_TOOLS = TVBOX_DEVICE_TOOLS + (list(_todo_middleware.tools) if _todo_middleware else [])

# ==============================================================================
# Agent 系统 Prompt 与构造工厂
# ==============================================================================

SYSTEM_PROMPT = """你是一个智能电视管家 AI，负责根据用户的自然语言需求精准控制 TVBoxOS 智能电视系统。

【核心决策准则】：
1. **状态感知优先**：每调用一个 Tool 后，电视端都会返回实时的屏幕状态快照。你的每一步决策都必须基于上一步返回的最新真实状态，绝不可脱离实际状态盲目执行。
2. **搜索结果严格核实**：搜索后必须核对 Observation 中的搜索条目。如果搜索结果为 0 条或提示“没找到数据”，严禁盲目点击条目，必须尝试换词重搜或告知用户未找到。
3. **页面与播放前置校验**：详情页控制 (`control_detail_page`) 必须在详情页内调用；播放控制 (`control_playback`) 必须在实际播放中调用。

【你的核心能力与工具箱】：
1. 详情页控制：全屏/选集/切线路/收藏/简介/切源，调用 `control_detail_page`（仅详情页可用）。
2. 影视点播：用户想看指定电影/电视剧时，调用 `play_vod`。
3. 播放控制：暂停、继续、快进、快退、下一集、上一集、倍速、比例切换，调用 `control_playback`（仅播放中可用）。
4. 字幕弹幕：开启/关闭弹幕、弹幕调速、字幕切换、时间轴微调，调用 `control_subtitle_and_danmaku`。
5. 电视直播：看央视、卫视、换台，调用 `switch_live_channel`；查询节目单调用 `get_live_epg`。
6. 搜索与筛选：搜索影视用 `search_media`；选择搜索结果用 `select_search_item`；分类过滤用 `filter_category`。
7. 界面导航与按键：去主页/搜索/直播/设置等页面用 `navigate_to_page`；返回用 `go_back`；物理按键用 `send_key_event`。
8. 收藏与历史：收藏管理用 `manage_favorite`；历史记录用 `manage_history`。
9. 站点与源配置：换接口源用 `set_api_source`；切换主页站点用 `switch_home_source`。
10. 状态感知：若需主动确认电视实时状态，调用 `get_device_state`。
"""

# ==============================================================================
# 8. LangChain 1.3.15 官方 Agent 与 Middleware 架构 (create_agent & TodoListMiddleware)
# 参考: https://docs.langchain.com/oss/python/releases/langchain-v1#create_agent
# ==============================================================================

def create_tvbox_agent(
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: float = 0.1
) -> Any:
    """
    使用官方 create_agent + TodoListMiddleware 构建全功能 TVBox 智能管家 Agent
    """
    final_api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
    final_base_url = base_url or os.getenv("OPENAI_BASE_URL") or os.getenv("LLM_BASE_URL")
    final_model = model_name or os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-4o"

    llm_kwargs: Dict[str, Any] = {
        "model": final_model,
        "temperature": temperature,
        "extra_body": {
            "thinking": {
                "type": "disabled"
            }
        }
    }
    if final_api_key:
        llm_kwargs["api_key"] = final_api_key
    if final_base_url:
        llm_kwargs["base_url"] = final_base_url

    llm = ChatOpenAI(**llm_kwargs)

    # LangChain 1.x 使用 create_agent + middleware；0.3.x 回退到 LangGraph 的
    # create_react_agent，保持当前项目依赖也可运行。
    try:
        from langchain.agents import create_agent
        kwargs = {"model": llm, "tools": TVBOX_DEVICE_TOOLS, "system_prompt": SYSTEM_PROMPT}
        if TodoListMiddleware:
            kwargs["middleware"] = [TodoListMiddleware()]
        return create_agent(**kwargs)
    except ImportError:
        return create_react_agent(llm, TVBOX_DEVICE_TOOLS, prompt=SYSTEM_PROMPT)


def create_agent(model, tools, middleware=None, system_prompt=SYSTEM_PROMPT, **_kwargs):
    """Compatibility wrapper for the project's LangChain 0.3.x dependency."""
    return create_react_agent(model, tools, prompt=system_prompt)

if __name__ == "__main__":
    print(f"==================================================")
    print(f"TVBox LangGraph StateGraph Agent 初始化成功！已注册 {len(TVBOX_ALL_TOOLS)} 个核心 Tool:")
    for idx, t in enumerate(TVBOX_ALL_TOOLS, 1):
        print(f" {idx:02d}. {t.name:<30} -> {t.description}")
    print(f"==================================================")
