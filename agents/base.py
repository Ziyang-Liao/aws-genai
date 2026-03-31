"""
SubAgent 基类 — 所有领域 Agent 继承此类注册到 SuperAgent。
"""

from __future__ import annotations
import json
from strands import Agent, AgentSkills
from strands.models.bedrock import BedrockModel


class SubAgent:
    """SubAgent 基类。子类只需定义 name/description/tools/skills_dir。"""

    name: str = ""
    description: str = ""
    model_id: str = ""
    region: str = ""
    system_prompt: str = ""
    tools: list = []
    skills_dir: str | None = None  # e.g. "./skills/scene-mode"

    def __init__(self, model_id: str = "", region: str = "us-east-1"):
        self.model_id = model_id or self.model_id
        self.region = region or self.region
        self._agent: Agent | None = None

    def _build_agent(self) -> Agent:
        model = BedrockModel(model_id=self.model_id, region_name=self.region)
        kwargs: dict = dict(
            model=model,
            tools=self.tools,
            system_prompt=self.system_prompt,
        )
        if self.skills_dir:
            kwargs["plugins"] = [AgentSkills(skills=self.skills_dir)]
        return Agent(**kwargs)

    @property
    def agent(self) -> Agent:
        if self._agent is None:
            self._agent = self._build_agent()
        return self._agent

    def run(self, task: str, context: str = "") -> dict:
        """执行任务，返回结构化结果。"""
        prompt = f"{task}\n\n附加上下文：{context}" if context else task
        try:
            result = self.agent(prompt)
            return {"success": True, "agent": self.name, "result": str(result)}
        except Exception as e:
            return {"success": False, "agent": self.name, "error": str(e)}

    def info(self) -> dict:
        return {"name": self.name, "description": self.description}
