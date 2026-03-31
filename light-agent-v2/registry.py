"""
SubAgent 注册中心 — 动态注册、发现、实例化 SubAgent。

新增 Agent 只需：
  1. 在 agents/ 下写一个继承 SubAgent 的类
  2. 在这里 register 即可
"""

from __future__ import annotations
from agents.base import SubAgent


class AgentRegistry:
    def __init__(self, default_model_id: str = "", default_region: str = "us-east-1"):
        self._classes: dict[str, type[SubAgent]] = {}
        self._instances: dict[str, SubAgent] = {}
        self._model_id = default_model_id
        self._region = default_region

    def register(self, cls: type[SubAgent]) -> type[SubAgent]:
        """注册一个 SubAgent 类。可作装饰器使用。"""
        name = cls.name
        if not name:
            raise ValueError(f"{cls.__name__} must define 'name'")
        self._classes[name] = cls
        return cls

    def get(self, name: str) -> SubAgent:
        """获取 SubAgent 实例（懒加载单例）。"""
        if name not in self._instances:
            cls = self._classes.get(name)
            if not cls:
                raise KeyError(f"Unknown agent: {name}. Available: {list(self._classes.keys())}")
            self._instances[name] = cls(model_id=self._model_id, region=self._region)
        return self._instances[name]

    def list_agents(self) -> list[dict]:
        """返回所有已注册 Agent 的信息。"""
        return [{"name": n, "description": c.description} for n, c in self._classes.items()]

    def available_names(self) -> list[str]:
        return list(self._classes.keys())
