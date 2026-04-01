"""
Light Agent V2 — Multi-Agent 架构入口

SuperAgent（Sonnet 强推理）编排 SubAgent（Haiku 执行）。
AgentCore 能力：Runtime + Tool + Skill + Memory + OTel
"""

import json
import os
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from orchestrator import init_registry, create_super_agent
from devices import device_states

# ── Configuration ──

REGION = os.environ.get("AWS_REGION", "us-east-1")
MEMORY_ID = os.environ.get("AGENTCORE_MEMORY_ID", "")

# ── 初始化 SubAgent 注册表 ──

init_registry()

# ── Memory ──

def create_session_manager(session_id: str, actor_id: str):
    if not MEMORY_ID:
        return None
    try:
        from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig
        from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager
        config = AgentCoreMemoryConfig(memory_id=MEMORY_ID, session_id=session_id, actor_id=actor_id)
        return AgentCoreMemorySessionManager(agentcore_memory_config=config, region_name=REGION)
    except Exception as e:
        print(f"[Memory] Init failed: {e}")
        return None


# ── SuperAgent 会话缓存 ──

_agent_cache: dict[str, tuple] = {}


def get_or_create_agent(session_id: str = "default", actor_id: str = "user"):
    if session_id in _agent_cache:
        print(f"[SuperAgent] Reusing cached (session={session_id})")
        return _agent_cache[session_id]

    sm = create_session_manager(session_id, actor_id)
    agent = create_super_agent(session_manager=sm)
    entry = (sm, agent)
    _agent_cache[session_id] = entry
    print(f"[SuperAgent] Created (session={session_id}, memory={'on' if sm else 'off'})")
    return entry


# ── BedrockAgentCoreApp ──

app = BedrockAgentCoreApp()


@app.entrypoint
def handle(payload: dict):
    prompt = payload.get("prompt", "")
    if not prompt:
        return {"error": "missing prompt"}

    session_id = payload.get("session_id", "default-session")
    actor_id = payload.get("actor_id", "web-user")

    sm, agent = get_or_create_agent(session_id, actor_id)
    result = agent(prompt)
    response_text = str(result)

    # 从 animation tool 提取动画指令传给前端
    animation = None
    try:
        from tools.animation_tools import last_animation
        import tools.animation_tools as _at
        if _at.last_animation is not None:
            animation = _at.last_animation
            _at.last_animation = None  # 消费后清空
    except Exception:
        pass

    resp = {
        "response": response_text,
        "deviceState": {k: dict(v) for k, v in device_states.items()},
    }
    if animation:
        resp["animation"] = animation
    return resp


if __name__ == "__main__":
    app.run()
