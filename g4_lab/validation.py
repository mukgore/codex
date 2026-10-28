"""Fail-closed structural validation for local G4 server-adapter frame input.

This validates shape, scalar types, finite values, timestamp ordering, a nonzero
wrist-to-middle-MCP scale, and a bounded frame count. It does not authenticate
the camera or establish that timestamps or landmarks came from a real device;
callers must treat all submitted values as untrusted input.
"""

from __future__ import annotations

import math
from numbers import Real
from typing import Any


MAX_FRAMES = 3000
LANDMARK_COUNT = 21
WRIST_INDEX = 0
MIDDLE_MCP_INDEX = 9


def _finite_number(value: Any, field: str) -> float:
    """Convert a JSON-style real number to float, rejecting bool and overflow."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{field} must be a real number")
    try:
        converted = float(value)
    except (OverflowError, TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a finite real number") from exc
    if not math.isfinite(converted):
        raise ValueError(f"{field} must be finite")
    return converted


def validate_frames(frames: Any) -> list[dict[str, Any]]:
    """Validate and copy frames for a local server-side adapter.

    ``frames`` must be a nonempty list or tuple of mappings with exactly
    ``t_ms`` and ``lm`` keys. ``t_ms`` is a finite real number and must increase
    strictly across every frame, including frames whose ``lm`` is null. A
    detected ``lm`` must be a 21-by-2 list/tuple of finite real coordinates.
    Its wrist (landmark 0) and middle MCP (landmark 9) must not coincide.
    Explicit null landmarks are preserved as ``None``.

    At most ``MAX_FRAMES`` frames are accepted as a local resource bound. The
    returned dictionaries and coordinate arrays are fresh objects containing
    normalized Python floats. Structural validation cannot prove camera source,
    capture-time freshness, timestamp authenticity, or human presence.

    Raises:
        ValueError: If any frame, scalar, sequence length, or detected-hand
            scale violates the input contract.
    """
    if not isinstance(frames, (list, tuple)):
        raise ValueError("frames must be a list or tuple")
    if not frames:
        raise ValueError("frames must not be empty")
    if len(frames) > MAX_FRAMES:
        raise ValueError(f"frames exceeds the {MAX_FRAMES}-frame limit")

    cleaned: list[dict[str, Any]] = []
    previous_t: float | None = None

    for frame_index, frame in enumerate(frames):
        if not isinstance(frame, dict):
            raise ValueError(f"frame {frame_index} must be a dictionary")
        if set(frame) != {"t_ms", "lm"}:
            raise ValueError(
                f"frame {frame_index} must contain exactly t_ms and lm"
            )

        t_ms = _finite_number(frame["t_ms"], f"frame {frame_index} t_ms")
        if previous_t is not None and t_ms <= previous_t:
            raise ValueError("t_ms values must be strictly increasing")
        previous_t = t_ms

        landmarks = frame["lm"]
        if landmarks is None:
            cleaned.append({"t_ms": t_ms, "lm": None})
            continue

        if not isinstance(landmarks, (list, tuple)):
            raise ValueError(f"frame {frame_index} lm must be null or an array")
        if len(landmarks) != LANDMARK_COUNT:
            raise ValueError(
                f"frame {frame_index} lm must contain {LANDMARK_COUNT} points"
            )

        points: list[list[float]] = []
        for point_index, point in enumerate(landmarks):
            if not isinstance(point, (list, tuple)) or len(point) != 2:
                raise ValueError(
                    f"frame {frame_index} lm[{point_index}] must contain x and y"
                )
            x = _finite_number(point[0], f"frame {frame_index} lm[{point_index}].x")
            y = _finite_number(point[1], f"frame {frame_index} lm[{point_index}].y")
            points.append([x, y])

        wrist = points[WRIST_INDEX]
        middle_mcp = points[MIDDLE_MCP_INDEX]
        if wrist[0] == middle_mcp[0] and wrist[1] == middle_mcp[1]:
            raise ValueError(
                f"frame {frame_index} has zero wrist-to-middle-MCP scale"
            )

        cleaned.append({"t_ms": t_ms, "lm": points})

    return cleaned
