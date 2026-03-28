# Light Agent V2

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Strands Agents SDK](https://img.shields.io/badge/Strands_Agents-SDK-orange.svg)](https://github.com/strands-agents/sdk-python)
[![Amazon Bedrock AgentCore](https://img.shields.io/badge/Amazon_Bedrock-AgentCore-232F3E.svg)](https://aws.amazon.com/bedrock/agentcore/)

A production-ready smart light control agent built with **Strands Agents SDK** and **Amazon Bedrock AgentCore**. Control 4 simulated smart lights through natural language — with persistent memory, native skills, and full observability.

> Standardized rewrite of `light-assistant` (TypeScript/MCP Gateway), fully leveraging AgentCore native capabilities.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [AgentCore Capabilities](#agentcore-capabilities)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Deployment](#deployment)
- [Frontend](#frontend)
- [Configuration](#configuration)
- [Changelog](#changelog)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- 🎯 **4 `@tool` functions** — control, query, discover, resolve nicknames
- 🧠 **2 native Skills** (`SKILL.md`) — scene themes & device discovery, loaded on-demand
- 💾 **AgentCore Memory** — cross-session preference learning (SEMANTIC + USER_PREFERENCE)
- 📊 **OTel Observability** — auto-instrumented traces → CloudWatch GenAI Dashboard
- 🌐 **Bilingual** — Chinese & English nicknames, auto-detect response language
- 🎨 **6 preset themes** + 8 dynamic mood modes with per-device color/brightness
- 🖥️ **Interactive SVG frontend** — real-time scene visualization with AI chat

---

## Architecture

```
User: "Switch to Christmas theme"
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│  BedrockAgentCoreApp                                     │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Strands Agent (Claude Haiku 4.5)                  │  │
│  │                                                    │  │
│  │  ┌─ AgentCore Memory ──────────────────────────┐   │  │
│  │  │ Short-term: session context                  │   │  │
│  │  │ Long-term: user preferences (SEMANTIC/PREF)  │   │  │
│  │  └─────────────────────────────────────────────┘   │  │
│  │                                                    │  │
│  │  ┌─ Skills (SKILL.md) ────────────────────────┐    │  │
│  │  │ scene-mode: 6 presets + 8 dynamic moods     │    │  │
│  │  │ device-discovery: registry + nicknames      │    │  │
│  │  └────────────────────────────────────────────┘    │  │
│  │           │                                        │  │
│  │  ┌─ Tools (@tool) ───────────────────────────┐     │  │
│  │  │ control_light · query_lights               │     │  │
│  │  │ discover_devices · resolve_device_name      │     │  │
│  │  └────────────────────────────────────────────┘    │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌─ OTel Auto-Instrumentation ───────────────────────┐   │
│  │ Agent reasoning → Tool calls → Model requests      │   │
│  └────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

### Comparison with light-assistant (v1)

| Dimension | light-assistant (v1) | light-agent-v2 |
|-----------|---------------------|----------------|
| Language | TypeScript | Python |
| Tool definition | JSON Schema + Lambda | `@tool` decorator (auto schema) |
| Skill mechanism | ❌ Tool grouping only | ✅ Native `AgentSkills` + `SKILL.md` |
| Memory | ❌ In-process (lost on restart) | ✅ AgentCore Memory (persistent) |
| Observability | ❌ None | ✅ OTel auto-instrumentation |
| Runtime entry | Custom Express server | ✅ `BedrockAgentCoreApp` |
| Infrastructure | 7+ AWS services | 1 container |
| Code | Thousands of lines | ~300 lines |

---

## AgentCore Capabilities

| Capability | Status | Implementation |
|---|---|---|
| **Runtime** (BedrockAgentCoreApp) | ✅ | `@app.entrypoint`, auto /ping + /invocations |
| **Tool** (@tool) | ✅ | 4 decorated functions, SDK auto-extracts schema |
| **Skill** (AgentSkills) | ✅ | 2 `SKILL.md` knowledge packs, loaded on-demand |
| **Memory** | ✅ | Cross-session persistence via `AgentCoreMemorySessionManager` |
| **Observability** (OTel) | ✅ | `opentelemetry-instrument` → CloudWatch |
| **Identity/Credential** | — | No external API calls needed |
| **MCP Gateway** | — | Tools execute locally |

---

## Project Structure

```
light-agent-v2/
├── server.py                       # BedrockAgentCoreApp entry + Memory integration
├── tools.py                        # 4 @tool definitions
├── devices.py                      # Device model, state management, nickname mapping
├── demo.py                         # Local test demo (no Memory required)
├── skills/
│   ├── scene-mode/
│   │   └── SKILL.md                # 6 preset themes + 8 dynamic mood palettes
│   └── device-discovery/
│       └── SKILL.md                # Device registry + bilingual nickname table
├── infra/
│   └── lambda-proxy/
│       ├── index.py                # Lambda proxy (frontend + API → AgentCore)
│       └── frontend.html           # SPA (SVG scene + device controls + AI chat)
├── Dockerfile                      # arm64 + OTel auto-instrumentation
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- AWS credentials configured (`aws configure`)
- Amazon Bedrock model access enabled (Claude Haiku 4.5)

### Local Development

```bash
pip install -r requirements.txt
export AWS_REGION=us-east-1

# Quick demo (no Memory, no AgentCore)
python demo.py

# Full AgentCore server
python server.py
```

### Enable Memory

```bash
pip install bedrock-agentcore

# Create Memory resource
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

export AGENTCORE_MEMORY_ID=<your-memory-id>
python server.py
```

### Enable Observability

```bash
export OTEL_PYTHON_DISTRO=aws_distro
export OTEL_PYTHON_CONFIGURATOR=aws_configurator
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
export OTEL_RESOURCE_ATTRIBUTES=service.name=light-agent-v2

opentelemetry-instrument python server.py
```

> In AgentCore Runtime, OTel is auto-enabled via Dockerfile CMD.

---

## Deployment

### Build & Push to ECR

```bash
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_REGION=us-east-1
export ECR_REPO=light-agent-v2

aws ecr create-repository --repository-name $ECR_REPO --region $AWS_REGION
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

docker buildx build --platform linux/arm64 \
  --tag $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest \
  --push .
```

### Create AgentCore Runtime

```bash
export ROLE_ARN=$(aws iam get-role --role-name BedrockAgentCoreRuntimeRole \
  --query 'Role.Arn' --output text)
export IMAGE_URI=$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest

aws bedrock-agentcore-control create-agent-runtime \
  --agent-runtime-name light_agent_v2 \
  --agent-runtime-artifact "{\"containerConfiguration\":{\"containerUri\":\"$IMAGE_URI\"}}" \
  --role-arn "$ROLE_ARN" \
  --network-configuration networkMode=PUBLIC \
  --protocol-configuration serverProtocol=HTTP \
  --environment-variables '{
    "AGENTCORE_MEMORY_ID": "<your-memory-id>",
    "MODEL_ID": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "AWS_REGION": "us-east-1"
  }' \
  --region $AWS_REGION
```

### Deploy Frontend (Lambda Proxy)

```bash
cd infra/lambda-proxy
zip -j proxy.zip index.py frontend.html

aws lambda create-function \
  --function-name light-agent-proxy \
  --runtime python3.12 \
  --handler index.handler \
  --role <your-lambda-role-arn> \
  --zip-file fileb://proxy.zip \
  --timeout 120 \
  --environment "Variables={AGENTCORE_RUNTIME_ARN=<your-runtime-arn>}"
```

Then create API Gateway (HTTP API) → Lambda integration, and CloudFront → API Gateway origin.

---

## Frontend

```
Browser → CloudFront → API Gateway (HTTP) → Lambda Proxy → AgentCore Runtime
                                               │
                                        GET /  → frontend.html
                                        POST /api/chat → invoke_agent_runtime
```

### Design Decisions

- **Chat is the sole backend channel** — natural language controls lights, Agent returns `deviceState` to sync UI
- **UI controls are local-only** — toggles, sliders, color pickers update the scene instantly without backend calls
- **Session persistence** — `chatSessionId` stored in `localStorage`, survives page refresh
- **Clear = new session** — generates fresh session_id so Agent truly forgets prior context
- **Diff-based sync** — only devices whose state actually changed get updated in the UI

---

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `MODEL_ID` | `us.anthropic.claude-haiku-4-5-20251001-v1:0` | Bedrock model ID |
| `AWS_REGION` | `us-east-1` | AWS region |
| `AGENTCORE_MEMORY_ID` | _(empty)_ | Memory resource ID (optional, enables persistence) |
| `AGENTCORE_RUNTIME_ARN` | — | Runtime ARN (Lambda proxy only) |

### Supported Models

| Model | Latency | Use Case |
|-------|---------|----------|
| Claude Haiku 4.5 | 2-3s | Default — fast responses |
| Claude Opus 4 | 8-15s | Complex reasoning |

Switch models by updating the `MODEL_ID` environment variable on the Runtime (no rebuild needed).

---

## Changelog

### v2.1.0 (2026-03-28)

**Fixed**
- Align frontend/backend theme configs — Halloween, Starry, Bonfire, Sunset values now match exactly between `SKILL.md` and frontend `THEMES`
- Remove broken `PUT /api/devices/:id` endpoint call (route never existed in Lambda proxy)
- Remove dead `fetchDeviceStates()` function
- Remove fire-and-forget chat sync from UI controls (unreliable natural language round-trip)

**Added**
- `localStorage` persistence for `chatSessionId` — session survives page refresh
- Clear button now generates new session_id — Agent truly forgets prior context
- `.gitignore` for `data/` and `__pycache__/`
- Frontend deployment architecture section in README

**Changed**
- Lambda timeout: 60s → 120s (handles AgentCore cold starts)
- UI controls are now local-only (no backend sync) — Chat is the sole backend channel

### v2.0.0 (2026-03-28)

**Initial release** — standardized rewrite of light-assistant (v1)

- 4 `@tool` functions: `control_light`, `query_lights`, `discover_devices`, `resolve_device_name`
- 2 native Skills via `SKILL.md`: scene-mode (6 presets + 8 moods), device-discovery (bilingual nicknames)
- `BedrockAgentCoreApp` standard runtime entry
- `AgentCoreMemorySessionManager` for cross-session persistent memory
- OTel auto-instrumentation via `opentelemetry-instrument`
- Interactive SVG frontend with real-time scene visualization
- Lambda proxy + API Gateway + CloudFront deployment stack

---

## Known Limitations

- **Container shared state**: All sessions hitting the same AgentCore container share in-memory `device_states`. This is by design for the demo — production use should persist state externally.
- **Long-term memory extraction**: AgentCore Memory extraction jobs run asynchronously. New sessions may not immediately access preferences learned from previous sessions.
- **Container rolling update**: After image update, old containers serve until idle timeout (15 min). New containers use the updated image.
- **Max session duration**: AgentCore Runtime enforces an 8-hour maximum session timeout.

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

---

## License

This project is licensed under the MIT License — see the [LICENSE](../LICENSE) file for details.

---

## Acknowledgments

- [Strands Agents SDK](https://github.com/strands-agents/sdk-python) — Agent framework
- [Amazon Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/) — Runtime, Memory, Observability
- [Anthropic Claude](https://www.anthropic.com/) — Foundation model
