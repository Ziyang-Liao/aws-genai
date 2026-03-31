"""
GeneralAgent — 兜底 Agent，处理不属于任何专业领域的对话。
"""

from agents.base import SubAgent


class GeneralAgent(SubAgent):
    name = "general"
    description = "通用对话：闲聊、问答、不属于其他专业 Agent 领域的请求"
    tools = []
    skills_dir = None

    system_prompt = (
        "你是智能家居助手的通用对话模块。\n"
        "职责：回答用户的一般性问题、闲聊、提供帮助建议。\n"
        "如果用户的问题涉及具体设备控制，告知你会转交给专业模块处理。\n"
        "用用户的语言回复，简洁友好。"
    )
