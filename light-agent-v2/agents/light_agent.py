"""
LightAgent — 灯光控制 SubAgent

迁移自原 single-agent 的灯光能力，含动态灯效动画引擎。
"""

from agents.base import SubAgent
from tools.light_tools import control_light, query_lights, discover_devices, resolve_device_name
from tools.animation_tools import run_light_animation, stop_light_animation


class LightAgent(SubAgent):
    name = "light"
    description = "智能灯光控制：开关、亮度、颜色、场景主题、设备查询、昵称解析、动态灯效动画（流星/呼吸/彩虹/追逐等任意效果）"
    tools = [control_light, query_lights, discover_devices, resolve_device_name,
             run_light_animation, stop_light_animation]
    skills_dir = "./skills/scene-mode:./skills/device-discovery"

    system_prompt = (
        "你是灯光控制专家，负责执行具体的灯光操作。\n"
        "规则：\n"
        "1. 用用户的语言回复\n"
        "2. 场景/主题/氛围请求，先激活 scene-mode 技能获取配色\n"
        "3. 昵称指代设备时，先激活 device-discovery 技能解析\n"
        "4. 未指定设备时默认操作所有设备\n"
        "5. 操作后简洁告知结果，设备离线时如实告知\n"
        "6. 动态灯效请求，使用 run_light_animation 工具：\n"
        "   - 根据用户描述的效果，生成对应的 keyframes 帧序列\n"
        "   - 每帧定义每个设备在该时刻的状态（on/brightness/color）\n"
        "   - 设备顺序默认: hexa → tvb → rope → ylight（从左到右）\n"
        "   - 用户要求循环时设 repeat=-1，要求停止时用 stop_light_animation\n"
        "7. 只返回操作结果，不要闲聊"
    )
