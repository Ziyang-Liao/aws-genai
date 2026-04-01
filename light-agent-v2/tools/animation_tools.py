"""
动态灯效执行引擎 — 通用帧序列执行器

设计：
  - 有限次数（repeat=N）：后端同步执行，直接返回结果
  - 持续循环（repeat=-1）：后端执行一轮 + 返回 animation 指令，前端驱动循环
  - tool 不理解灯效语义，只执行帧序列；LLM 负责生成 keyframes
"""

import json
import time

from strands import tool
from devices import update_state, get_state, DEVICE_REGISTRY

# 模块级变量：存储最近一次的 animation 指令，供 server.py 提取
last_animation: dict | None = None


def _execute_frames(keyframes: list[dict], interval_ms: int):
    """同步执行一轮帧序列。"""
    interval_s = interval_ms / 1000.0
    for i, frame in enumerate(keyframes):
        for device_id, state in frame.items():
            if device_id not in DEVICE_REGISTRY:
                continue
            update_state(
                device_id,
                on=state.get("on"),
                brightness=state.get("brightness"),
                color=state.get("color"),
            )
        if i < len(keyframes) - 1:
            time.sleep(interval_s)


@tool
def run_light_animation(
    keyframes: list[dict],
    interval_ms: int = 500,
    repeat: int = 1,
) -> str:
    """Execute a dynamic light animation as a sequence of keyframes.

    Each keyframe maps device_id to its target state for that frame.
    For finite repeats, executes synchronously. For infinite loop (repeat=-1),
    executes one cycle and returns animation data for the frontend to continue looping.

    Args:
        keyframes: List of frame dicts. Each frame: {"device_id": {"on": bool, "brightness": int, "color": "#hex"}, ...}.
        interval_ms: Milliseconds between frames. Default 500.
        repeat: Number of cycles to run. Use -1 for continuous loop. Default 1.

    Example — chase effect (one light at a time, left to right):
        keyframes: [
            {"hexa": {"on": true, "brightness": 100, "color": "#ffffff"}, "tvb": {"on": false}, "rope": {"on": false}, "ylight": {"on": false}},
            {"hexa": {"on": false}, "tvb": {"on": true, "brightness": 100, "color": "#ffffff"}, "rope": {"on": false}, "ylight": {"on": false}},
            {"hexa": {"on": false}, "tvb": {"on": false}, "rope": {"on": true, "brightness": 100, "color": "#ffffff"}, "ylight": {"on": false}},
            {"hexa": {"on": false}, "tvb": {"on": false}, "rope": {"on": false}, "ylight": {"on": true, "brightness": 100, "color": "#ffffff"}}
        ]
        interval_ms: 500
        repeat: -1
    """
    if repeat == -1:
        # 执行一轮让用户看到效果，然后返回动画数据让前端持续循环
        _execute_frames(keyframes, interval_ms)
        global last_animation
        last_animation = {"keyframes": keyframes, "interval_ms": interval_ms}
        return json.dumps({
            "success": True,
            "mode": "continuous",
            "animation": {
                "keyframes": keyframes,
                "interval_ms": interval_ms,
            },
            "message": "Animation playing. Frontend will continue looping. Say '停止灯效' to stop.",
        })
    else:
        for _ in range(repeat):
            _execute_frames(keyframes, interval_ms)
        states = {did: get_state(did) for did in DEVICE_REGISTRY}
        return json.dumps({
            "success": True,
            "mode": "completed",
            "cycles": repeat,
            "frames": len(keyframes),
            "interval_ms": interval_ms,
            "final_state": states,
        })


@tool
def stop_light_animation() -> str:
    """Stop the currently running light animation on the frontend."""
    global last_animation
    last_animation = {"stop": True}
    return json.dumps({
        "success": True,
        "animation": {"stop": True},
        "message": "Animation stop signal sent.",
    })
