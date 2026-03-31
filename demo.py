"""
Light Agent V2 — Multi-Agent Demo

SuperAgent（Sonnet）编排 SubAgent（Haiku）。
展示：简单路由、并行分发、澄清循环、联动编排。
"""

import json
import os
from orchestrator import init_registry, create_super_agent
from devices import device_states

init_registry()
agent = create_super_agent()

test_cases = [
    ("简单路由", "打开所有灯"),
    ("简单路由", "把亮度调到60"),
    ("简单路由 + Skill", "应用圣诞主题"),
    ("澄清意图", "帮我把那个灯关掉"),
    ("兜底对话", "你好，你能做什么？"),
    ("查询状态", "查看所有灯的状态"),
    ("昵称解析", "把电视背光调成蓝色"),
    ("动态氛围", "我想要电影之夜的氛围"),
]

print("💡 Light Agent V2 — Multi-Agent Demo")
print("=" * 55)

for label, user_input in test_cases:
    print(f"\n[{label}] 📝 用户: {user_input}")
    print("-" * 55)
    result = agent(user_input)
    print(f"💡 设备状态: {json.dumps(device_states, ensure_ascii=False)[:200]}")
    print("=" * 55)
