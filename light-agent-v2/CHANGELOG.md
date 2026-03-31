# Changelog

All notable changes to this project will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/), versioning follows [Semantic Versioning](https://semver.org/).

---

## [3.0.0] — 2026-03-31

### Added
- **Multi-Agent Architecture**: SuperAgent (Sonnet) orchestration + SubAgent pool (Haiku)
- `orchestrator.py` — SuperAgent with tool-based routing (dispatch, parallel_dispatch, ask_user, list_available_agents)
- `registry.py` — Dynamic SubAgent registration center with lazy-load singleton
- `agents/base.py` — SubAgent base class, 3-step extension for new domain agents
- `agents/light_agent.py` — Light control SubAgent (migrated from v2 single-agent)
- `agents/general_agent.py` — General conversation fallback SubAgent
- `tools/light_tools.py` — Light domain tools (modularized from tools.py)
- `skills/agent-registry/SKILL.md` — SubAgent capability registry for SuperAgent routing
- `skills/orchestration/SKILL.md` — Orchestration strategy knowledge (model-driven, no hardcoded logic)
- Error handling: auto-retry (max 2) for network/timeout, user notification for service errors

### Changed
- `server.py` — Refactored to create SuperAgent instead of single Agent
- `demo.py` — Updated to multi-agent demo with orchestration test cases
- Memory management unified at SuperAgent level

## [2.0.0] — 2026-03-30

### Added
- AgentCore Runtime (`BedrockAgentCoreApp`) standard entry point
- 4 `@tool` definitions: control_light, query_lights, discover_devices, resolve_device_name
- AgentSkills: scene-mode (preset themes + dynamic ambiance), device-discovery (nickname resolution)
- AgentCore Memory integration for cross-session user preference persistence
- OTel observability with `opentelemetry-instrument` auto-instrumentation
- CloudFront + Lambda proxy deployment (`infra/lambda-proxy/`)
- Frontend chat UI (`frontend.html`)

## [1.0.0] — 2026-03-25

### Added
- Initial single-agent implementation with Strands SDK
- Basic light control tools
- Scene mode skill with 6 preset themes
- Device discovery skill with bilingual nickname mapping
- Docker containerization for AgentCore deployment
