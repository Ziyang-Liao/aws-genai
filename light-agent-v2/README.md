# Light Agent V2 — Multi-Agent 智能家居控制

基于 [Strands Agents SDK](https://github.com/strands-agents/sdk-python) + [Amazon Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/) 构建的 Multi-Agent 智能家居控制系统。

SuperAgent（Sonnet 强推理）负责意图理解与任务编排，SubAgent（Haiku 高效执行）负责具体领域操作。

---

## 架构

```
用户请求
    │
    ▼
┌─ CloudFront ──────────────────────────────────────────────┐
│  GET /          → 前端 HTML                                │
│  POST /api/chat → Lambda Proxy → AgentCore Runtime        │
└───────────────────────────┬───────────────────────────────┘
                            │
                            ▼
┌─ AgentCore Runtime ───────────────────────────────────────┐
│                                                           │
│  ┌─ SuperAgent (Sonnet — 强推理 + 编排) ──────────────┐   │
│  │  Tools: dispatch, parallel_dispatch, ask_user,     │   │
│  │         list_available_agents                      │   │
│  │  Skills: agent-registry, orchestration             │   │
│  │  Memory: AgentCore Memory (统一管理)               │   │
│  │                                                    │   │
│  │  编排模式（模型推理驱动，不硬编码）：                │   │
│  │  · 简单路由 → 单个 SubAgent                        │   │
│  │  · 并行分发 → 多个独立 SubAgent 同时执行            │   │
│  │  · 串行编排 → 上游结果作为下游 context              │   │
│  │  · 澄清循环 → ask_user 主动提问                    │   │
│  │  · 联动编排 → 跨 Agent 协作                        │   │
│  └────────────────────────────────────────────────────┘   │
│       │                                                   │
│       ▼                                                   │
│  ┌─ SubAgent 池 (Haiku — 高效执行) ──────────────────┐   │
│  │                                                    │   │
│  │  LightAgent     — 灯光控制/场景/设备查询           │   │
│  │  GeneralAgent   — 通用对话兜底                     │   │
│  │  (可扩展更多 SubAgent...)                          │   │
│  └────────────────────────────────────────────────────┘   │
│                                                           │
│  ┌─ 错误处理 ────────────────────────────────────────┐   │
│  │  网络/超时 → 自动重试(max 2) → 降级               │   │
│  │  服务异常 → 告知用户重试                           │   │
│  └────────────────────────────────────────────────────┘   │
│                                                           │
│  ┌─ Observability (OTel) ────────────────────────────┐   │
│  │  自动追踪: SuperAgent → dispatch → SubAgent → Tool │   │
│  └────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────┘
```

---

## 项目结构

```
light-agent-v2/
├── server.py                       # AgentCore Runtime 入口
├── orchestrator.py                 # SuperAgent 编排器 + dispatch tools
├── registry.py                     # SubAgent 注册中心
├── demo.py                         # 本地 Multi-Agent Demo
├── devices.py                      # 设备模型 + 状态管理
├── tools.py                        # (兼容保留) 原 tools 入口
├── agents/
│   ├── base.py                     # SubAgent 基类
│   ├── light_agent.py              # 灯光控制 SubAgent
│   └── general_agent.py            # 通用对话 SubAgent
├── tools/
│   └── light_tools.py              # 灯光 @tool 定义
├── skills/
│   ├── agent-registry/
│   │   └── SKILL.md                # SubAgent 能力注册表
│   ├── orchestration/
│   │   └── SKILL.md                # 编排策略知识
│   ├── scene-mode/
│   │   └── SKILL.md                # 灯光场景配色
│   └── device-discovery/
│       └── SKILL.md                # 设备昵称映射
├── infra/
│   └── lambda-proxy/
│       ├── index.py                # Lambda → AgentCore Runtime
│       └── frontend.html           # 前端页面
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 快速开始

### 本地运行

```bash
pip install -r requirements.txt
export AWS_REGION=us-east-1

# Multi-Agent Demo
python demo.py

# 或启动 AgentCore 标准服务
python server.py
```

### 自定义模型

```bash
export SUPER_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0   # SuperAgent
export SUB_MODEL_ID=us.anthropic.claude-haiku-4-5-20251001-v1:0     # SubAgent
```

### 扩展新 SubAgent

1. 在 `agents/` 下创建新文件，继承 `SubAgent`：

```python
from agents.base import SubAgent
from tools.your_tools import your_tool

class YourAgent(SubAgent):
    name = "your_domain"
    description = "描述此 Agent 的能力"
    tools = [your_tool]
    system_prompt = "你是..."
```

2. 在 `orchestrator.py` 的 `init_registry()` 中注册：

```python
from agents.your_agent import YourAgent
registry.register(YourAgent)
```

3. 在 `skills/agent-registry/SKILL.md` 中添加描述，SuperAgent 即可自动路由。

### 部署更新

```bash
# 1. 构建推送镜像
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 073090110765.dkr.ecr.us-east-1.amazonaws.com

docker buildx build --platform linux/arm64 \
  --tag 073090110765.dkr.ecr.us-east-1.amazonaws.com/light-agent-v2:latest \
  --push .

# 2. 更新 Runtime
aws bedrock-agentcore-control update-agent-runtime \
  --agent-runtime-id light_agent_v2-eW6loJ6rV1 \
  --agent-runtime-artifact '{"containerConfiguration":{"containerUri":"073090110765.dkr.ecr.us-east-1.amazonaws.com/light-agent-v2:latest"}}' \
  --region us-east-1

# 3. 等待 READY
aws bedrock-agentcore-control get-agent-runtime \
  --agent-runtime-id light_agent_v2-eW6loJ6rV1 \
  --region us-east-1 --query 'status'
```

---

## AgentCore 能力使用清单

| AgentCore 能力 | 状态 | 实现方式 |
|---|---|---|
| **Runtime** | ✅ | `BedrockAgentCoreApp` 标准入口 |
| **Tool** (@tool) | ✅ | SubAgent 领域 tools + SuperAgent 编排 tools |
| **Skill** (AgentSkills) | ✅ | 4 个 SKILL.md：agent-registry, orchestration, scene-mode, device-discovery |
| **Memory** | ✅ 可选 | SuperAgent 统一管理，跨会话记忆用户偏好 |
| **Observability** (OTel) | ✅ | 全链路追踪 SuperAgent → SubAgent → Tool |
| **Multi-Agent** | ✅ | SuperAgent 编排 + SubAgent 池 + 动态注册 |
