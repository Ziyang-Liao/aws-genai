"""
LightAgent — 灯光控制 SubAgent

迁移自原 single-agent 的灯光能力。
"""

from agents.base import SubAgent
from tools.light_tools import control_light, query_lights, discover_devices, resolve_device_name


class LightAgent(SubAgent):
    name = "light"
    description = "智能灯光控制：开关、亮度、颜色、场景主题切换、设备查询与昵称解析"
    tools = [control_light, query_lights, discover_devices, resolve_device_name]
    skills_dir = "./skills/scene-mode:./skills/device-discovery"

    system_prompt = (
        "你是灯光控制专家，负责执行具体的灯光操作。\n"
        "规则：\n"
        "1. 用用户的语言回复\n"
        "2. 场景/主题/氛围请求，先激活 scene-mode 技能获取配色\n"
        "3. 昵称指代设备时，先激活 device-discovery 技能解析\n"
        "4. 未指定设备时默认操作所有设备\n"
        "5. 操作后简洁告知结果，设备离线时如实告知\n"
        "6. 只返回操作结果，不要闲聊"
    )
