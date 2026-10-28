"""Strict all-or-nothing 2D circle masking for local video-frame batches.

The input contract follows stage1_extract's per-frame mapping, but mask
geometry uses only image-space x/y coordinates. Any unclassified/missing or
invalid frame rejects the complete batch before an output image is drawn.
This helper does not alter or authenticate the underlying source images.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real
from typing import Any, Sequence

import cv2
import numpy as np


LANDMARK_NAMES = (
    "WRIST",
    "THUMB_CMC", "THUMB_MCP", "THUMB_IP", "THUMB_TIP",
    "INDEX_MCP", "INDEX_PIP", "INDEX_DIP", "INDEX_TIP",
    "MIDDLE_MCP", "MIDDLE_PIP", "MIDDLE_DIP", "MIDDLE_TIP",
    "RING_MCP", "RING_PIP", "RING_DIP", "RING_TIP",
    "PINKY_MCP", "PINKY_PIP", "PINKY_DIP", "PINKY_TIP",
)
WRIST_INDEX = 0
MIDDLE_MCP_INDEX = LANDMARK_NAMES.index("MIDDLE_MCP")


@dataclass(frozen=True)
class CircleMask:
    """A circle in image pixel coordinates."""

    center_x: float
    center_y: float
    radius: float


def _finite_real(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{field} must be a real number")
    try:
        value = float(value)
    except (OverflowError, TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be finite") from exc
    if not math.isfinite(value):
        raise ValueError(f"{field} must be finite")
    return value


def _xy_landmarks(frame: Any, index: int) -> list[tuple[float, float]]:
    if not isinstance(frame, dict):
        raise ValueError(f"frame {index} must be a mapping")
    if frame.get("detected") is not True:
        raise ValueError(f"frame {index} is missing a positive detection label")
    if "frame_idx" not in frame:
        raise ValueError(f"frame {index} has no frame_idx")
    frame_idx = frame["frame_idx"]
    if isinstance(frame_idx, bool) or not isinstance(frame_idx, int) or frame_idx < 0:
        raise ValueError(f"frame {index} frame_idx must be a nonnegative integer")
    if "landmarks_px" not in frame or not isinstance(frame["landmarks_px"], dict):
        raise ValueError(f"frame {index} has no pixel landmark mapping")

    points = frame["landmarks_px"]
    if set(points) != set(LANDMARK_NAMES):
        raise ValueError(f"frame {index} must contain exactly 21 named landmarks")

    xy: list[tuple[float, float]] = []
    for name in LANDMARK_NAMES:
        point = points[name]
        if not isinstance(point, dict) or set(point) != {"x", "y", "z"}:
            raise ValueError(f"frame {index} landmark {name} must contain x, y, and z")
        # Validate z as input hygiene, but deliberately never use it in geometry.
        x = _finite_real(point["x"], f"frame {index} {name}.x")
        y = _finite_real(point["y"], f"frame {index} {name}.y")
        _finite_real(point["z"], f"frame {index} {name}.z")
        xy.append((x, y))
    return xy


def preflight_masks(
    frames: Sequence[dict[str, Any]],
    *,
    w3: float,
    expected_frame_count: int | None = None,
) -> list[CircleMask]:
    """Validate every frame and compute every 2D mask before any drawing.

    Frames use the `stage1_extract` mapping shape. Every frame must be
    positively detected and have all 21 finite named pixel landmarks. `w3` is
    a caller-supplied scalar; this function does not calibrate or endorse it.
    """
    if not isinstance(frames, (list, tuple)) or not frames:
        raise ValueError("frames must be a nonempty list or tuple")
    if expected_frame_count is not None:
        if (isinstance(expected_frame_count, bool)
                or not isinstance(expected_frame_count, int)
                or expected_frame_count < 0):
            raise ValueError("expected_frame_count must be a nonnegative integer")
        if len(frames) != expected_frame_count:
            raise ValueError("frame/decoded-image count mismatch")

    scale = _finite_real(w3, "w3")
    if scale <= 0:
        raise ValueError("w3 must be positive")

    masks: list[CircleMask] = []
    previous_frame_idx: int | None = None
    for index, frame in enumerate(frames):
        points = _xy_landmarks(frame, index)
        frame_idx = frame["frame_idx"]
        expected_idx = 0 if previous_frame_idx is None else previous_frame_idx + 1
        if frame_idx != expected_idx:
            raise ValueError("frame_idx values must be contiguous from zero")
        previous_frame_idx = frame_idx

        wrist_x, wrist_y = points[WRIST_INDEX]
        middle_x, middle_y = points[MIDDLE_MCP_INDEX]
        dx, dy = middle_x - wrist_x, middle_y - wrist_y
        span = math.hypot(dx, dy)
        radius = span * scale / 2.0
        center_x = (wrist_x + middle_x) / 2.0
        center_y = (wrist_y + middle_y) / 2.0
        if not math.isfinite(radius) or not math.isfinite(center_x) or not math.isfinite(center_y):
            raise ValueError(f"frame {index} produced a nonfinite mask")
        if span <= 0 or radius <= 0:
            raise ValueError(f"frame {index} has zero wrist-to-middle-MCP scale")
        masks.append(CircleMask(center_x, center_y, radius))
    return masks


def apply_masks(
    images: Sequence[np.ndarray],
    masks: Sequence[CircleMask],
) -> list[np.ndarray]:
    """Return masked image copies; validate the whole batch before drawing."""
    if not isinstance(images, (list, tuple)) or not images:
        raise ValueError("images must be a nonempty list or tuple")
    if not isinstance(masks, (list, tuple)) or len(images) != len(masks):
        raise ValueError("image/mask count mismatch")

    height_width: tuple[int, int] | None = None
    draw_args: list[tuple[tuple[int, int], int]] = []
    for index, (image, mask) in enumerate(zip(images, masks)):
        if not isinstance(image, np.ndarray) or image.dtype != np.uint8:
            raise ValueError(f"image {index} must be a uint8 NumPy array")
        if image.ndim != 3 or image.shape[2] != 3 or image.shape[0] <= 0 or image.shape[1] <= 0:
            raise ValueError(f"image {index} must have nonempty HxWx3 shape")
        current_shape = (int(image.shape[0]), int(image.shape[1]))
        if height_width is None:
            height_width = current_shape
        elif current_shape != height_width:
            raise ValueError("all images must have the same dimensions")
        if not isinstance(mask, CircleMask):
            raise ValueError(f"mask {index} is not a CircleMask")
        cx = _finite_real(mask.center_x, f"mask {index} center_x")
        cy = _finite_real(mask.center_y, f"mask {index} center_y")
        radius = _finite_real(mask.radius, f"mask {index} radius")
        if radius <= 0:
            raise ValueError(f"mask {index} radius must be positive")
        if not (0 <= cx < current_shape[1] and 0 <= cy < current_shape[0]):
            raise ValueError(f"mask {index} center is outside its image")
        int_radius = int(radius)
        if int_radius <= 0:
            raise ValueError(f"mask {index} radius is below one pixel")
        draw_args.append(((int(cx), int(cy)), int_radius))

    # Copy only after every image/mask has passed preflight.
    outputs = [image.copy() for image in images]
    for output, (center, radius) in zip(outputs, draw_args):
        cv2.circle(output, center, radius, (0, 0, 0), -1)
    return outputs


def mask_video_frames(
    images: Sequence[np.ndarray],
    frames: Sequence[dict[str, Any]],
    *,
    w3: float,
) -> list[np.ndarray]:
    """Preflight the complete frame map and decoded batch, then mask copies."""
    if not isinstance(images, (list, tuple)):
        raise ValueError("images must be a list or tuple")
    masks = preflight_masks(frames, w3=w3, expected_frame_count=len(images))
    return apply_masks(images, masks)
