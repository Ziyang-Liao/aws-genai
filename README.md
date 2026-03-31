# AWS GenAI — AI Agent 实践项目集

基于 AWS 云服务构建的 AI Agent 实践项目集合，涵盖从单 Agent 到 Multi-Agent 编排的完整演进路径。

## 项目列表

| 项目 | 描述 | 技术栈 | 状态 |
|------|------|--------|------|
| [light-agent-v2](./light-agent-v2/) | Multi-Agent 智能家居控制系统 | Strands SDK + Bedrock AgentCore + Claude Sonnet/Haiku | ✅ 生产部署 |
| [strands-agent-demo](./strands-agent-demo/) | Strands Agents SDK 入门示例 | Strands SDK + Bedrock | ✅ 完成 |

## light-agent-v2

SuperAgent（Claude Sonnet 强推理）负责意图理解与任务编排，SubAgent 池（Claude Haiku 高效执行）负责具体领域操作。

核心能力：
- Multi-Agent 编排（简单路由 / 并行分发 / 串行编排 / 澄清循环 / 联动协作）
- AgentCore Runtime + Tool + Skill + Memory + OTel 全链路
- 动态 SubAgent 注册，3 步扩展新领域 Agent

👉 详见 [light-agent-v2/README.md](./light-agent-v2/README.md)

## strands-agent-demo

Strands Agents SDK 快速入门，单 Agent + Tool + Skill 基础用法演示。

👉 详见 [strands-agent-demo/README.md](./strands-agent-demo/README.md)

## 技术栈

- [Strands Agents SDK](https://github.com/strands-agents/sdk-python) — Agent 框架
- [Amazon Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/) — 托管运行时
- [Amazon Bedrock](https://aws.amazon.com/bedrock/) — Claude Sonnet / Haiku 模型
- [AWS Lambda](https://aws.amazon.com/lambda/) + [CloudFront](https://aws.amazon.com/cloudfront/) — Serverless 部署

## License

[MIT](./LICENSE)
