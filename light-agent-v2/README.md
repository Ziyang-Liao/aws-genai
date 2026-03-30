# Light Agent V2 — 智能灯光控制 Agent

基于 [Strands Agents SDK](https://github.com/strands-agents/sdk-python) + [Amazon Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/) 构建的多设备智能灯光控制 Agent。

通过自然语言对话控制 4 台智能灯具，支持场景主题切换、设备昵称解析、多轮对话上下文、跨会话记忆。

---

## AgentCore 能力使用清单

| AgentCore 能力 | 状态 | 实现方式 |
|---|---|---|
| **Runtime** (BedrockAgentCoreApp) | ✅ | `@app.entrypoint` 标准入口，自动处理 /ping + /invocations |
| **Tool** (@tool) | ✅ | 4 个 `@tool` 装饰器函数，SDK 自动提取 schema |
| **Skill** (AgentSkills) | ✅ | 2 个 `SKILL.md` 知识包，按需加载 |
| **Memory** (AgentCore Memory) | ✅ 可选 | 通过环境变量启用，跨会话记忆用户偏好 |
| **Observability** (OTel) | ✅ | `opentelemetry-instrument` 自动链路追踪 → CloudWatch |
| **Identity/Credential** | — | 当前无外部 API 调用，无需凭证管理 |
| **MCP Gateway** | — | Tool 在本地执行，无需远程路由 |

---

## 架构

```
用户浏览器
    │
    ▼
┌─ CloudFront ──────────────────────────────────────────────┐
│  静态页面 + API 代理                                       │
│  GET /          → 返回前端 HTML                            │
│  POST /api/chat → Lambda Proxy → AgentCore Runtime        │
└───────────────────────────┬───────────────────────────────┘
                            │
                            ▼
┌─ AgentCore Runtime ───────────────────────────────────────┐
│  BedrockAgentCoreApp (容器)                                │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Strands Agent (Claude Haiku 4.5)                  │   │
│  │                                                    │   │
│  │  ┌─ 会话上下文 ────────────────────────────────┐   │   │
│  │  │ 进程内 Agent 缓存（按 session_id）           │   │   │  ← 多轮对话
│  │  │ AgentCore Memory（可选，跨会话持久化）       │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  │                                                    │   │
│  │  ┌─ Skill: scene-mode ────────────────────────┐    │   │
│  │  │ 6 预设主题 + 8 动态氛围配色表               │    │   │  ← 按需加载
│  │  └────────────────────────────────────────────┘    │   │
│  │  ┌─ Skill: device-discovery ──────────────────┐    │   │
│  │  │ 设备列表 + 中英文昵称映射表                 │    │   │  ← 按需加载
│  │  └────────────────────────────────────────────┘    │   │
│  │           │                                        │   │
│  │           ▼                                        │   │
│  │  ┌─ Tools ────────────────────────────────────┐    │   │
│  │  │ control_light    — 控制开关/亮度/颜色       │    │   │
│  │  │ query_lights     — 查询设备状态             │    │   │
│  │  │ discover_devices — 发现可用设备             │    │   │
│  │  │ resolve_device_name — 昵称解析              │    │   │
│  │  └────────────────────────────────────────────┘    │   │
│  └────────────────────────────────────────────────────┘   │
│                                                           │
│  ┌─ Observability (OTel) ────────────────────────────┐    │
│  │ 自动追踪: Agent 推理 → Tool 调用 → 模型请求       │    │  ← 自动 instrument
│  │ 输出到: CloudWatch GenAI Observability Dashboard   │    │
│  └────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────┘
```

---

## 项目结构

```
light-agent-v2/
├── server.py                       # AgentCore Runtime 入口 + Agent 会话缓存
├── demo.py                         # 本地测试 Demo（不依赖 AgentCore Runtime）
├── tools.py                        # 4 个 @tool 定义
├── devices.py                      # 设备模型 + 状态管理 + 昵称映射（线程安全）
├── skills/
│   ├── scene-mode/
│   │   └── SKILL.md                # 场景模式知识包 (6 预设 + 8 动态氛围)
│   └── device-discovery/
│       └── SKILL.md                # 设备发现知识包 (设备列表 + 昵称表)
├── infra/
│   └── lambda-proxy/
│       ├── index.py                # Lambda 函数：CloudFront → AgentCore Runtime
│       └── frontend.html           # 前端页面（灯光可视化 + AI 聊天）
├── Dockerfile                      # arm64 容器 + OTel auto-instrumentation
├── requirements.txt
└── README.md
```

---

## 快速开始

### 本地运行

```bash
pip install -r requirements.txt
export AWS_REGION=us-east-1

# 运行 Demo（不需要 AgentCore Runtime 和 Memory）
python demo.py

# 或启动 AgentCore 标准服务
python server.py
```

### 启用 AgentCore Memory（可选）

不启用 Memory 时，Agent 通过进程内缓存保持同一会话的多轮对话上下文（容器重启后丢失）。
启用 Memory 后，Agent 可跨会话记住用户偏好（如"喜欢暖色调"）。

```bash
# 1. 创建 Memory 资源
python -c "
from bedrock_agentcore.memory import MemoryClient
client = MemoryClient(region_name='us-east-1')
mem = client.create_memory_and_wait(
    name='LightAgentMemory',
    description='Light agent user preferences and session history',
    strategies=[
        {'userPreferenceMemoryStrategy': {
            'name': 'PreferenceLearner',
            'namespaceTemplates': ['/preferences/{actorId}/']
        }},
        {'semanticMemoryStrategy': {
            'name': 'FactExtractor',
            'namespaceTemplates': ['/facts/{actorId}/']
        }}
    ]
)
print('Memory ID:', mem['id'])
"

# 2. 设置环境变量后启动
export AGENTCORE_MEMORY_ID=<上面输出的 Memory ID>
python server.py
```

### 启用 Observability

```bash
# 本地带 OTel 追踪运行
export AGENT_OBSERVABILITY_ENABLED=true
export OTEL_PYTHON_DISTRO=aws_distro
export OTEL_PYTHON_CONFIGURATOR=aws_configurator
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
export OTEL_RESOURCE_ATTRIBUTES=service.name=light-agent-v2

opentelemetry-instrument python server.py
```

部署到 AgentCore Runtime 后，OTel 自动启用（Dockerfile CMD 已配置 `opentelemetry-instrument`）。

### 部署到 AgentCore

```bash
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_REGION=us-east-1
export ECR_REPO=light-agent-v2

# 创建 ECR + 构建推送
aws ecr create-repository --repository-name $ECR_REPO --region $AWS_REGION
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

docker buildx build --platform linux/arm64 \
  --tag $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest \
  --push .

# 创建 Runtime
export ROLE_ARN=$(aws iam get-role --role-name BedrockAgentCoreRuntimeRole --query 'Role.Arn' --output text)
export IMAGE_URI=$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest

aws bedrock-agentcore-control create-agent-runtime \
  --agent-runtime-name light_agent_v2 \
  --agent-runtime-artifact "{\"containerConfiguration\":{\"containerUri\":\"$IMAGE_URI\"}}" \
  --role-arn "$ROLE_ARN" \
  --network-configuration networkMode=PUBLIC \
  --protocol-configuration serverProtocol=HTTP \
  --region $AWS_REGION
```

---

## AgentCore 能力详解

### 1. BedrockAgentCoreApp（标准化入口）

替代手写 Flask/Express，自动处理 AgentCore 服务契约（`/ping` 健康检查 + `/invocations` 推理入口）：

```python
app = BedrockAgentCoreApp()

@app.entrypoint
def handle(payload: dict):
    sm, agent = get_or_create_agent(session_id, actor_id)
    result = agent(payload["prompt"])
    return {"response": str(result), "deviceState": device_states}

app.run()
```

### 2. 多轮对话上下文

同一 `session_id` 的请求复用同一个 Agent 实例，Strands Agent 内部的 message history 自动保持上下文：

```python
_agent_cache: dict[str, tuple] = {}

def get_or_create_agent(session_id, actor_id):
    if session_id in _agent_cache:
        return _agent_cache[session_id]  # 复用已有 Agent
    agent = Agent(model=model, tools=[...], plugins=[...])
    _agent_cache[session_id] = agent
    return agent
```

可选启用 AgentCore Memory 实现跨会话持久化记忆。

### 3. Observability（OTel 链路追踪）

Dockerfile 使用 `opentelemetry-instrument` 启动，自动追踪：
- Agent 推理过程
- 每次 Tool 调用的耗时和参数
- Bedrock 模型请求的 token 用量
- 全链路 trace 可在 CloudWatch GenAI Observability Dashboard 查看

### 4. AgentSkills（按需加载知识包）

两个 `SKILL.md` 知识包，仅在 Agent 判断需要时加载到上下文：
- `scene-mode`：6 预设主题（圣诞、万圣节、星空、篝火、极光、日落）+ 8 种动态氛围配色
- `device-discovery`：设备列表 + 双语昵称映射

不使用时不占 token，比硬编码在 System Prompt 中更高效。

### 5. 前端部署（CloudFront + Lambda Proxy）

前端通过 CloudFront 分发，Lambda 函数作为 API 代理转发请求到 AgentCore Runtime：

```
浏览器 → CloudFront → Lambda (index.py) → AgentCore Runtime (server.py)
                                         ↓
                                    invoke_agent_runtime(payload={prompt, session_id})
```

Lambda 将前端传入的 `session_id` 同时放入 `runtimeSessionId`（Runtime 路由）和 `payload`（Agent 会话缓存），确保多轮对话上下文正确传递。
