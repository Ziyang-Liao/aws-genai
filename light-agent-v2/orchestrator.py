"""
SuperAgent 编排器 — 总控/路由/编排层

通过 tool calling 驱动编排，不硬编码任何业务逻辑。
SuperAgent 读取 agent-registry + orchestration skill 自主决策。
"""

from __future__ import annotations

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from strands import Agent, AgentSkills, tool
from strands.models.bedrock import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient

from registry import AgentRegistry

# ── 配置 ──

SUPER_MODEL_ID = os.environ.get("SUPER_MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")
SUB_MODEL_ID = os.environ.get("SUB_MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")
REGION = os.environ.get("AWS_REGION", "us-east-1")
MAX_RETRIES = int(os.environ.get("DISPATCH_MAX_RETRIES", "2"))

# MCP server 配置（环境变量格式: MCP_SERVERS=name1:url1,name2:url2）
MCP_SERVERS_CONFIG = os.environ.get("MCP_SERVERS", "")

# ── SubAgent 注册 ──

registry = AgentRegistry(default_model_id=SUB_MODEL_ID, default_region=REGION)


def init_registry():
    """注册所有 SubAgent。新增 Agent 在这里加一行即可。"""
    from agents.light_agent import LightAgent
    from agents.general_agent import GeneralAgent
    registry.register(LightAgent)
    registry.register(GeneralAgent)


# ── 错误处理 ──

def _is_retryable(error: str) -> bool:
    retryable_keywords = ["timeout", "throttl", "connection", "network", "502", "503", "429"]
    low = error.lower()
    return any(k in low for k in retryable_keywords)


def _dispatch_with_retry(agent_name: str, task: str, context: str = "") -> dict:
    sub = registry.get(agent_name)
    last_error = ""
    for attempt in range(1 + MAX_RETRIES):
        result = sub.run(task, context)
        if result["success"]:
            return result
        last_error = result.get("error", "unknown")
        if not _is_retryable(last_error) or attempt == MAX_RETRIES:
            break
        time.sleep(0.5 * (attempt + 1))
    return {"success": False, "agent": agent_name, "error": last_error}


# ── SuperAgent Tools（编排能力）──

@tool
def dispatch(agent_name: str, task: str, context: str = "") -> str:
    """Dispatch a task to a specialized SubAgent.

    Args:
        agent_name: Target agent name (see agent-registry skill for available agents).
        task: Task description in natural language.
        context: Optional context from previous steps or upstream agent results.
    """
    result = _dispatch_with_retry(agent_name, task, context)
    return json.dumps(result, ensure_ascii=False)


@tool
def parallel_dispatch(tasks: list[dict]) -> str:
    """Dispatch multiple independent tasks to SubAgents in parallel.

    Args:
        tasks: List of task objects, each with keys: agent_name (str), task (str), context (str, optional).
    """
    results = []
    with ThreadPoolExecutor(max_workers=min(len(tasks), 4)) as pool:
        futures = {
            pool.submit(
                _dispatch_with_retry,
                t["agent_name"],
                t["task"],
                t.get("context", ""),
            ): t["agent_name"]
            for t in tasks
        }
        for f in as_completed(futures):
            results.append(f.result())
    return json.dumps(results, ensure_ascii=False)


@tool
def ask_user(question: str) -> str:
    """Ask the user a clarifying question when intent is ambiguous.
    The question will be sent back to the user and their reply will be available in the next turn.

    Args:
        question: The question to ask the user.
    """
    # 返回特殊标记，server.py 识别后直接回传给前端
    return json.dumps({"__ask_user__": True, "question": question})


@tool
def list_available_agents() -> str:
    """List all registered SubAgents and their capabilities."""
    return json.dumps(registry.list_agents(), ensure_ascii=False)


# ── MCP 客户端管理 ──

_mcp_clients: list[MCPClient] = []


def init_mcp_clients():
    """从环境变量初始化 MCP 客户端。格式: MCP_SERVERS=name1:url1,name2:url2"""
    if not MCP_SERVERS_CONFIG:
        return []

    tools = []
    for entry in MCP_SERVERS_CONFIG.split(","):
        entry = entry.strip()
        if ":" not in entry:
            continue
        name, url = entry.split(":", 1)
        try:
            from mcp.client.streamable_http import streamablehttp_client
            client = MCPClient(lambda u=url: streamablehttp_client(u))
            client.__enter__()
            _mcp_clients.append(client)
            mcp_tools = client.list_tools_sync()
            tools.extend(mcp_tools)
            print(f"[MCP] Connected: {name} ({url}), {len(mcp_tools)} tools")
        except Exception as e:
            print(f"[MCP] Failed to connect {name} ({url}): {e}")
    return tools


def shutdown_mcp_clients():
    """关闭所有 MCP 客户端连接。"""
    for client in _mcp_clients:
        try:
            client.__exit__(None, None, None)
        except Exception:
            pass
    _mcp_clients.clear()


# ── SuperAgent 构建 ──

SUPER_SYSTEM_PROMPT = (
    "你是智能家居总控 Agent，负责理解用户意图、编排任务、调度专业 SubAgent 执行。\n\n"
    "核心原则：\n"
    "1. 你不直接执行设备操作，而是通过 dispatch/parallel_dispatch 分发给专业 Agent\n"
    "2. 先理解用户完整意图，再决定编排方案（参考 orchestration 技能）\n"
    "3. 只在意图真正模糊时才用 ask_user 澄清（如'把那个灯关掉'中的'那个'不明确）\n"
    "4. 用户指令已经明确时，直接执行，不要反复确认细节\n"
    "5. 多个独立任务尽量并行分发，有依赖的串行执行\n"
    "6. 上游 Agent 的结果可作为下游 Agent 的 context 传递（联动编排）\n"
    "7. 部分失败时返回已成功的结果并说明失败原因\n"
    "8. 用用户的语言回复，聚合所有 SubAgent 结果后给出统一、自然的回复\n"
    "9. 利用记忆了解用户偏好，减少重复询问\n"
)


def create_super_agent(session_manager=None) -> Agent:
    """创建 SuperAgent 实例。自动加载 MCP tools（如有配置）。"""
    model = BedrockModel(model_id=SUPER_MODEL_ID, region_name=REGION)
    skills = AgentSkills(skills="./skills/agent-registry:./skills/orchestration")

    all_tools = [dispatch, parallel_dispatch, ask_user, list_available_agents]
    mcp_tools = init_mcp_clients()
    if mcp_tools:
        all_tools.extend(mcp_tools)

    kwargs = dict(
        model=model,
        tools=all_tools,
        plugins=[skills],
        system_prompt=SUPER_SYSTEM_PROMPT,
    )
    if session_manager:
        kwargs["session_manager"] = session_manager
    return Agent(**kwargs)
