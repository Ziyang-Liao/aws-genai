"""
动态灯效执行引擎 — 通用帧序列执行器

SuperAgent 根据用户需求生成帧序列（keyframes），此 tool 负责按时序执行。
支持任意灯效组合：流星、呼吸、彩虹、追逐、闪烁、波浪……

设计原则：
  - tool 不理解"流星"或"呼吸"的含义，只执行帧序列
  - SuperAgent 负责将用户的自然语言描述转化为具体的帧序列
  - 帧序列是通用数据结构，可表达任意灯效
"""

import json
import time
import threading

from strands import tool
from devices import get_device_ids, update_state, get_state, DEVICE_REGISTRY

# 全局动画控制
_animation_lock = threading.Lock()
_stop_event = threading.Event()
_animation_thread: threading.Thread | None = None


def _run_animation(keyframes: list[dict], interval_ms: int, repeat: int):
    """在后台线程执行帧序列。"""
    interval_s = interval_ms / 1000.0
    cycle = 0
    while (repeat == -1 or cycle < repeat) and not _stop_event.is_set():
        for frame in keyframes:
            if _stop_event.is_set():
                return
            for device_id, state in frame.items():
                if device_id not in DEVICE_REGISTRY:
                    continue
                update_state(
                    device_id,
                    on=state.get("on"),
                    brightness=state.get("brightness"),
                    color=state.get("color"),
                )
            if not _stop_event.is_set():
                time.sleep(interval_s)
        cycle += 1


@tool
def run_light_animation(
    keyframes: list[dict],
    interval_ms: int = 500,
    repeat: int = 1,
) -> str:
    """Execute a dynamic light animation defined as a sequence of keyframes.

    Each keyframe is a dict mapping device_id to its state for that frame.
    The engine plays frames in order with the given interval, repeating as specified.
    This is a universal animation engine — any light effect can be expressed as keyframes.

    Args:
        keyframes: List of frame dicts. Each frame: {"device_id": {"on": bool, "brightness": int, "color": "#hex"}, ...}. Omitted devices keep their current state in that frame.
        interval_ms: Milliseconds between frames. Default 500.
        repeat: Number of cycles. Use -1 for infinite loop (until stop_light_animation is called). Default 1.

    Example — meteor effect (left to right):
        keyframes: [
            {"hexa": {"on": true, "brightness": 100, "color": "#87ceeb"}, "tvb": {"on": false}, "rope": {"on": false}, "ylight": {"on": false}},
            {"hexa": {"on": true, "brightness": 40}, "tvb": {"on": true, "brightness": 100, "color": "#87ceeb"}, "rope": {"on": false}, "ylight": {"on": false}},
            {"hexa": {"on": false}, "tvb": {"on": true, "brightness": 40}, "rope": {"on": true, "brightness": 100, "color": "#87ceeb"}, "ylight": {"on": false}},
            {"hexa": {"on": false}, "tvb": {"on": false}, "rope": {"on": true, "brightness": 40}, "ylight": {"on": true, "brightness": 100, "color": "#87ceeb"}},
            {"hexa": {"on": false}, "tvb": {"on": false}, "rope": {"on": false}, "ylight": {"on": true, "brightness": 40}}
        ]
        interval_ms: 400
        repeat: 3
    """
    global _animation_thread

    with _animation_lock:
        # 停止正在运行的动画
        if _animation_thread and _animation_thread.is_alive():
            _stop_event.set()
            _animation_thread.join(timeout=5)

        _stop_event.clear()

        if repeat == -1:
            # 无限循环在后台线程运行
            _animation_thread = threading.Thread(
                target=_run_animation,
                args=(keyframes, interval_ms, repeat),
                daemon=True,
            )
            _animation_thread.start()
            return json.dumps({
                "success": True,
                "mode": "looping",
                "frames": len(keyframes),
                "interval_ms": interval_ms,
                "message": "Animation running in background. Use stop_light_animation to stop.",
            })
        else:
            # 有限次数同步执行
            _run_animation(keyframes, interval_ms, repeat)
            states = {did: get_state(did) for did in DEVICE_REGISTRY}
            return json.dumps({
                "success": True,
                "mode": "completed",
                "frames": len(keyframes),
                "cycles": repeat,
                "interval_ms": interval_ms,
                "final_state": states,
            })


@tool
def stop_light_animation() -> str:
    """Stop any currently running light animation."""
    global _animation_thread

    with _animation_lock:
        if _animation_thread and _animation_thread.is_alive():
            _stop_event.set()
            _animation_thread.join(timeout=5)
            _animation_thread = None
            states = {did: get_state(did) for did in DEVICE_REGISTRY}
            return json.dumps({"success": True, "message": "Animation stopped.", "final_state": states})
        return json.dumps({"success": True, "message": "No animation running."})
