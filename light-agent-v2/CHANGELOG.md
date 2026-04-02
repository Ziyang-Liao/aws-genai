# Changelog

All notable changes to this project will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/), versioning follows [Semantic Versioning](https://semver.org/).

---

## [3.0.0] — 2026-04-01

### Added
- **Multi-Agent Architecture**: SuperAgent (Haiku 4.5) orchestration + SubAgent pool (Haiku 4.5)
- `orchestrator.py` — SuperAgent with tool-based routing (dispatch, parallel_dispatch, ask_user, list_available_agents)
- `registry.py` — Dynamic SubAgent registration center with lazy-load singleton
- `agents/base.py` — SubAgent base class, 3-step extension for new domain agents
- `agents/light_agent.py` — Light control SubAgent (migrated from v2 single-agent)
- `agents/general_agent.py` — General conversation fallback SubAgent
- `tools/light_tools.py` — Light domain tools (modularized from tools.py)
- `skills/agent-registry/SKILL.md` — SubAgent capability registry for SuperAgent routing
- `skills/orchestration/SKILL.md` — Orchestration strategy knowledge (model-driven, no hardcoded logic)
- MCP integration framework via `MCP_SERVERS` environment variable
- Error handling: auto-retry (max 2) for network/timeout, user notification for service errors

### Fixed
- Frontend session_id generation: use `crypto.randomUUID()` for stable 41-char IDs
- Lambda session_id guard: auto-pad to 33+ chars when too short
- Frontend device state sync on page load (keeps UI consistent with backend across refreshes)

### Changed
- `server.py` — Refactored to create SuperAgent instead of single Agent
- `demo.py` — Updated to multi-agent demo with orchestration test cases
- All models unified to Haiku 4.5 (speed priority)
- Memory management unified at SuperAgent level

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
