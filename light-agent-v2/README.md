# Light Agent V2 — Multi-Agent 智能家居控制

![Version](https://img.shields.io/badge/version-3.0.0-blue)
![Python](https://img.shields.io/badge/python-3.12+-green)
![License](https://img.shields.io/badge/license-MIT-brightgreen)
![AWS](https://img.shields.io/badge/AWS-Bedrock%20AgentCore-orange)

基于 [Strands Agents SDK](https://github.com/strands-agents/sdk-python) + [Amazon Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/) 构建的 Multi-Agent 智能家居控制系统。

SuperAgent（Haiku 4.5）负责意图理解与任务编排，SubAgent 池（Haiku 4.5）负责具体领域操作。

> 📋 [CHANGELOG](./CHANGELOG.md) · 🤝 [CONTRIBUTING](./CONTRIBUTING.md) · 📄 [LICENSE](../LICENSE)

---

## 系统全景

```
用户浏览器
    │
    ▼
┌─ CloudFront ──────────────────────────────────────────────────────────┐
│  GET /          → Lambda → 返回 frontend.html                         │
│  POST /api/chat → Lambda → AgentCore Runtime → 返回 JSON              │
└───────────────────────────┬───────────────────────────────────────────┘
                            │
┌─ Lambda: light-agent-proxy (index.py) ────────────────────────────────┐
│  纯代理层，不含业务逻辑                                                 │
│  · 转发 prompt + session_id 到 AgentCore Runtime                      │
│  · session_id 兜底：< 33 字符自动补齐（AgentCore 要求 ≥ 33）           │
└───────────────────────────┬───────────────────────────────────────────┘
                            │
┌─ AgentCore Runtime (server.py) ───────────────────────────────────────┐
│                                                                       │
│  ┌─ SuperAgent (Haiku 4.5 — 编排) ───────────────────────────────┐   │
│  │                                                                │   │
│  │  Tools（编排能力）:                                             │   │
│  │    dispatch          → 单任务分发给 SubAgent                    │   │
│  │    parallel_dispatch → 多任务并行分发                           │   │
│  │    ask_user          → 向用户提问澄清意图                       │   │
│  │    list_available_agents → 列出可用 SubAgent                   │   │
│  │    [MCP tools]       → 外部 MCP server 的 tools（如有配置）     │   │
│  │                                                                │   │
│  │  Skills（知识注入）:                                            │   │
│  │    agent-registry    → SubAgent 能力清单 + 路由原则             │   │
│  │    orchestration     → 5 种编排模式 + 6 条决策规则              │   │
│  │                                                                │   │
│  │  Memory: AgentCore Memory（可选，跨会话持久化）                 │   │
│  │                                                                │   │
│  │  编排模式（模型推理驱动，不硬编码）：                            │   │
│  │  · 简单路由 → 单个 SubAgent                                    │   │
│  │  · 并行分发 → 多个独立 SubAgent 同时执行                        │   │
│  │  · 串行编排 → 上游结果作为下游 context                          │   │
│  │  · 澄清循环 → ask_user 主动提问                                │   │
│  │  · 联动编排 → 跨 Agent 协作                                    │   │
│  └────────────────────────────────────────────────────────────────┘   │
│       │                                                               │
│       ▼                                                               │
│  ┌─ SubAgent 池 (Haiku 4.5 — 执行) ─────────────────────────────┐   │
│  │                                                                │   │
│  │  LightAgent                                                    │   │
│  │    Tools: control_light, query_lights,                         │   │
│  │           discover_devices, resolve_device_name                │   │
│  │    Skills: scene-mode（6 主题 + 8 氛围配色）                    │   │
│  │            device-discovery（设备列表 + 中英文昵称映射）         │   │
│  │                                                                │   │
│  │  GeneralAgent                                                  │   │
│  │    Tools: 无    Skills: 无    职责: 兜底对话                    │   │
│  │                                                                │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌─ 错误处理 ────────────────────────────────────────────────────┐   │
│  │  网络/超时 → 自动重试(max 2, 间隔递增) → 降级                  │   │
│  │  服务异常 → 告知用户重试                                       │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌─ Observability (OTel) ────────────────────────────────────────┐   │
│  │  自动追踪: SuperAgent → dispatch → SubAgent → Tool             │   │
│  └────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 核心概念关系

```
Agent = 模型 + Tools + Skills + System Prompt
  │
  ├─ Tool = Agent 的"手"，执行具体操作
  │   · @tool 装饰器定义，Strands SDK 自动提取参数 schema
  │   · 模型通过 tool calling 决定何时调用哪个 tool
  │   · SuperAgent 的 tool = 编排能力（dispatch / ask_user）
  │   · SubAgent 的 tool = 领域操作（control_light / query_lights）
  │
  ├─ Skill = Agent 的"知识"，注入到 system prompt 中
  │   · SKILL.md 文件，AgentSkills 插件自动加载
  │   · 不是代码，是结构化知识（表格 / 规则 / 映射）
  │   · SuperAgent 的 skill = 路由表 + 编排策略
  │   · SubAgent 的 skill = 场景配色表 + 设备昵称表
  │
  ├─ MCP = Agent 的"外部能力扩展"
  │   · 通过 MCP 协议连接外部服务，获取额外 tools
  │   · 通过 MCP_SERVERS 环境变量配置，启动时自动连接
  │   · 挂在 SuperAgent 上（路由前就能查外部数据做决策）
  │
  └─ Memory = Agent 的"记忆"
      · AgentCore Memory 跨会话持久化用户偏好
      · 通过 AGENTCORE_MEMORY_ID 环境变量启用
      · 挂在 SuperAgent 上（统一管理）
```

---

## 请求调用链示例

```
用户: "把电视背光调成红色"
  │
  ▼
Lambda (index.py): 转发 {prompt, session_id}
  │
  ▼
server.py: handle() → get_or_create_agent(session_id)
  │
  ▼
SuperAgent 推理（读取 agent-registry skill）
  │  → "电视背光"是灯光领域 → 选择 light agent
  │  → 调用 dispatch(agent_name="light", task="把电视背光调成红色")
  │
  ▼
orchestrator.py: dispatch() → registry.get("light") → LightAgent
  │
  ▼
LightAgent 推理（读取 device-discovery skill）
  │  → "电视背光" = tvb
  │  → 调用 resolve_device_name("电视背光") → tvb
  │  → 调用 control_light(device_ids=["tvb"], color="#ff0000")
  │
  ▼
devices.py: update_state("tvb", color="#ff0000") → 持久化
  │
  ▼
返回 {response: "电视背光已调成红色", deviceState: {tvb: {color: "#ff0000"}, ...}}
```

---

## 项目结构

```
light-agent-v2/
├── server.py              # 入口。BedrockAgentCoreApp + 会话管理 + Memory
├── orchestrator.py        # SuperAgent 构建。模型/prompt/tools/skills/MCP 组装
├── registry.py            # SubAgent 注册中心。懒加载单例
├── devices.py             # 设备模型。4 台灯状态管理 + 持久化 + 昵称解析
├── demo.py                # 本地 Multi-Agent Demo
├── tools.py               # (兼容保留) 原 tools 入口
│
├── agents/
│   ├── base.py            # SubAgent 基类。子类只需声明 name/tools/skills/prompt
│   ├── light_agent.py     # 灯光 SubAgent。4 tool + 2 skill
│   └── general_agent.py   # 兜底 SubAgent。无 tool 无 skill，纯对话
│
├── tools/
│   └── light_tools.py     # 4 个 @tool: control_light, query_lights,
│                           #   discover_devices, resolve_device_name
│
├── skills/
│   ├── agent-registry/SKILL.md     # SuperAgent 用：SubAgent 能力清单 + 路由原则
│   ├── orchestration/SKILL.md      # SuperAgent 用：5 种编排模式 + 6 条决策规则
│   ├── scene-mode/SKILL.md         # LightAgent 用：6 预设主题 + 8 氛围配色表
│   └── device-discovery/SKILL.md   # LightAgent 用：设备列表 + 中英文昵称映射
│
├── infra/lambda-proxy/
│   ├── index.py           # Lambda 代理。转发请求 + session_id 兜底
│   └── frontend.html      # 前端 UI。聊天 + 设备卡片 + SVG 灯光可视化
│
├── Dockerfile             # 容器。python:3.12-slim + OTel instrumentation
├── requirements.txt       # 依赖：strands-agents, bedrock-agentcore, boto3, otel
├── CHANGELOG.md
├── CONTRIBUTING.md
└── VERSION
```

---

## System Prompts

### SuperAgent（orchestrator.py）

```
你是智能家居总控 Agent，负责理解用户意图、编排任务、调度专业 SubAgent 执行。

核心原则：
1. 你不直接执行设备操作，而是通过 dispatch/parallel_dispatch 分发给专业 Agent
2. 先理解用户完整意图，再决定编排方案（参考 orchestration 技能）
3. 意图不明确时用 ask_user 主动澄清，不要猜测执行
4. 多个独立任务尽量并行分发，有依赖的串行执行
5. 上游 Agent 的结果可作为下游 Agent 的 context 传递（联动编排）
6. 部分失败时返回已成功的结果并说明失败原因
7. 用用户的语言回复，聚合所有 SubAgent 结果后给出统一、自然的回复
8. 利用记忆了解用户偏好，减少重复询问
9. 在没有确定用户真实意图之前，不要执行任何操作
```

### LightAgent（agents/light_agent.py）

```
你是灯光控制专家，负责执行具体的灯光操作。
规则：
1. 用用户的语言回复
2. 场景/主题/氛围请求，先激活 scene-mode 技能获取配色
3. 昵称指代设备时，先激活 device-discovery 技能解析
4. 未指定设备时默认操作所有设备
5. 操作后简洁告知结果，设备离线时如实告知
6. 只返回操作结果，不要闲聊
```

### GeneralAgent（agents/general_agent.py）

```
你是智能家居助手的通用对话模块。
职责：回答用户的一般性问题、闲聊、提供帮助建议。
如果用户的问题涉及具体设备控制，告知你会转交给专业模块处理。
用用户的语言回复，简洁友好。
```

---

## 环境变量

| 变量 | 默认值 | 作用 |
|------|--------|------|
| `SUPER_MODEL_ID` | `us.anthropic.claude-haiku-4-5-20251001-v1:0` | SuperAgent 模型 |
| `SUB_MODEL_ID` | `us.anthropic.claude-haiku-4-5-20251001-v1:0` | SubAgent 模型 |
| `AWS_REGION` | `us-east-1` | AWS 区域 |
| `AGENTCORE_MEMORY_ID` | 空（不启用） | AgentCore Memory ID |
| `MCP_SERVERS` | 空（不启用） | MCP server 列表，格式 `name:url,name:url` |
| `DISPATCH_MAX_RETRIES` | `2` | dispatch 失败重试次数 |

---

## 快速开始

### 本地运行

```bash
pip install -r requirements.txt
export AWS_REGION=us-east-1
python demo.py
```

### 扩展新 SubAgent

1. 在 `agents/` 下创建新文件，继承 `SubAgent`
2. 在 `orchestrator.py` 的 `init_registry()` 中注册
3. 在 `skills/agent-registry/SKILL.md` 中添加描述

详见 [CONTRIBUTING.md](./CONTRIBUTING.md)。

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

## AgentCore 能力清单

| 能力 | 状态 | 实现方式 |
|------|------|---------|
| **Runtime** | ✅ 已用 | `BedrockAgentCoreApp` 标准入口 |
| **Tool** | ✅ 已用 | 4 个编排 tool + 4 个灯光 tool |
| **Skill** | ✅ 已用 | 4 个 SKILL.md |
| **Multi-Agent** | ✅ 已用 | SuperAgent 编排 + 2 个 SubAgent + 动态注册 |
| **OTel** | ✅ 已用 | `opentelemetry-instrument` 全链路追踪 |
| **Memory** | ⚡ 框架就绪 | 代码已写，需配置 `AGENTCORE_MEMORY_ID` |
| **MCP** | ⚡ 框架就绪 | 代码已写，需配置 `MCP_SERVERS` |
