"""
动态灯效执行引擎 — 通用帧序列执行器

tool 不理解灯效语义，只执行帧序列；LLM 负责生成 keyframes。
"""

import json
import time

from strands import tool
from devices import update_state, get_state, DEVICE_REGISTRY


@tool
def run_light_animation(keyframes: list[dict], interval_ms: int = 500) -> str:
    """Execute a dynamic light animation as a sequence of keyframes.

    Each keyframe maps device_id to its target state for that frame.
    Frames are played in order with the given interval.

    Args:
        keyframes: List of frame dicts. Each frame: {"device_id": {"on": bool, "brightness": int, "color": "#hex"}, ...}.
        interval_ms: Milliseconds between frames. Default 500.
    """
    interval_s = interval_ms / 1000.0
    for i, frame in enumerate(keyframes):
        for device_id, s in frame.items():
            if device_id not in DEVICE_REGISTRY:
                continue
            update_state(device_id, on=s.get("on"), brightness=s.get("brightness"), color=s.get("color"))
        if i < len(keyframes) - 1:
            time.sleep(interval_s)

    states = {did: get_state(did) for did in DEVICE_REGISTRY}
    return json.dumps({"success": True, "frames": len(keyframes), "interval_ms": interval_ms, "final_state": states})
