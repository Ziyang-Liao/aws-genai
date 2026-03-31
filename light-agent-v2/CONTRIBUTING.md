# Contributing

感谢你对本项目的关注！欢迎提交 Issue 和 Pull Request。

## 开发环境

```bash
# 克隆仓库
git clone https://github.com/Ziyang-Liao/aws-genai.git
cd aws-genai/light-agent-v2

# 安装依赖
pip install -r requirements.txt

# 本地运行
export AWS_REGION=us-east-1
python demo.py
```

## 扩展新 SubAgent

1. 在 `agents/` 下创建新文件，继承 `SubAgent`
2. 在 `orchestrator.py` 的 `init_registry()` 中注册
3. 在 `skills/agent-registry/SKILL.md` 中添加能力描述

详见 [README.md](./README.md#扩展新-subagent)。

## 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/)：

```
feat: 新功能
fix: 修复
docs: 文档
refactor: 重构
chore: 构建/工具
```

## 代码风格

- Python 3.12+
- Type hints
- Docstrings for public APIs

## Issue & PR

- Issue: 描述问题、预期行为、复现步骤
- PR: 关联 Issue，描述改动内容，确保本地测试通过
