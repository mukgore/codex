"""Train frame-only (A) and causal past+current (B) 2D hand estimators.

This is deliberately separate from the existing offline benchmark.  A and B
share the benchmark's data readers, grouped splits, CNN body, loss, optimizer,
augmentation, and epoch-selection rule; only their legal temporal inputs differ.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import numpy as np
import torch
import cv2
from torch import nn

from occluded_pose_benchmark import evaluate, read_recorded, read_synthetic


MODES = ("A_current", "B_past_current")


def input_tensor(rgb: np.ndarray, mode: str) -> torch.Tensor:
    """Build per-clip inputs. B duplicates the first frame at session start."""
    if mode not in MODES:
        raise ValueError(f"unsupported causal input mode: {mode}")
    if rgb.ndim != 4 or rgb.shape[-1] != 3 or len(rgb) == 0:
        raise ValueError("rgb must be a non-empty N×H×W×3 array")
    frames = torch.from_numpy(np.ascontiguousarray(rgb)).permute(0, 3, 1, 2).float().div_(255)
    if mode == "A_current":
        return frames
    previous = torch.cat((frames[:1], frames[:-1]), dim=0)
    return torch.cat((previous, frames), dim=1)


def network(mode: str) -> nn.Sequential:
    if mode not in MODES:
        raise ValueError(f"unsupported causal input mode: {mode}")
    channels = 3 if mode == "A_current" else 6
    return nn.Sequential(
        nn.Conv2d(channels, 24, 5, stride=2, padding=2), nn.GroupNorm(4, 24), nn.SiLU(),
        nn.Conv2d(24, 40, 3, stride=2, padding=1), nn.GroupNorm(4, 40), nn.SiLU(),
        nn.Conv2d(40, 64, 3, stride=2, padding=1), nn.GroupNorm(8, 64), nn.SiLU(),
        nn.AdaptiveAvgPool2d((4, 4)), nn.Flatten(), nn.Linear(1024, 128), nn.SiLU(),
        nn.Linear(128, 42), nn.Sigmoid(),
    )


def predict_clip(model: nn.Module, rgb: np.ndarray, mode: str) -> np.ndarray:
    model.eval()
    batches = input_tensor(rgb, mode).split(32)
    with torch.inference_mode():
        return torch.cat([model(batch) for batch in batches]).cpu().numpy()


def predict_stream_frame(model: nn.Module, current_rgb: np.ndarray,
                         previous_rgb: np.ndarray | None, mode: str,
                         input_size: tuple[int, int] | None = None) -> np.ndarray:
    """Predict one frame using only inputs available at its arrival time."""
    if mode not in MODES:
        raise ValueError(f"unsupported causal input mode: {mode}")
    current = np.asarray(current_rgb)
    if current.ndim != 3 or current.shape[-1] != 3:
        raise ValueError("current_rgb must be H×W×3 RGB")
    if current.dtype != np.uint8 or not np.isfinite(current).all():
        raise ValueError("current_rgb must contain finite uint8 RGB pixels")
    if input_size is not None:
        current = cv2.resize(current, input_size, interpolation=cv2.INTER_AREA)
    if mode == "A_current":
        batch = input_tensor(current[None], mode)
    else:
        previous = current if previous_rgb is None else np.asarray(previous_rgb)
        if previous.ndim != 3 or previous.shape[-1] != 3 or previous.dtype != np.uint8:
            raise ValueError("previous_rgb must be uint8 H×W×3 RGB")
        if input_size is not None:
            previous = cv2.resize(previous, input_size, interpolation=cv2.INTER_AREA)
        if previous.shape != current.shape:
            raise ValueError("previous and current RGB frame shapes must match")
        batch = input_tensor(np.stack((previous, current)), mode)[1:2]
    model.eval()
    with torch.inference_mode():
        return model(batch)[0].cpu().numpy().reshape(21, 2)


def load_streaming_estimator(checkpoint: Path):
    artifact = torch.load(checkpoint, map_location="cpu", weights_only=False)
    if artifact.get("format") != "realtime_occluded_hand_model_v1":
        raise ValueError("unsupported checkpoint format")
    mode = artifact.get("mode")
    model = network(mode)
    model.load_state_dict(artifact["weights"])
    model.eval()
    return StreamingEstimator(model, mode, tuple(artifact["input_size_wh"])), artifact


class StreamingEstimator:
    """Stateful one-frame API. Call reset() at each video/session boundary.

    Training labels contain hand-present clips only, so a finite pose is not a
    hand-presence decision. ``infer`` exposes that limitation in its status.
    """

    def __init__(self, model: nn.Module, mode: str,
                 input_size: tuple[int, int] | None = None):
        if mode not in MODES:
            raise ValueError(f"unsupported causal input mode: {mode}")
        self.model, self.mode = model, mode
        self.input_size = input_size
        self.previous_rgb: np.ndarray | None = None

    @classmethod
    def from_checkpoint(cls, checkpoint: Path):
        return load_streaming_estimator(checkpoint)

    def reset(self) -> None:
        self.previous_rgb = None

    def predict(self, current_rgb: np.ndarray) -> np.ndarray:
        current = np.asarray(current_rgb)
        result = predict_stream_frame(self.model, current, self.previous_rgb, self.mode,
                                      self.input_size)
        if not np.isfinite(result).all():
            raise RuntimeError("model returned non-finite joint coordinates")
        self.previous_rgb = current.copy()
        return result

    def infer(self, current_rgb: np.ndarray) -> dict:
        """Return an explicit status; malformed frames never advance stream state."""
        try:
            points = self.predict(current_rgb)
        except (TypeError, ValueError) as exc:
            return {"status": "invalid_input", "points": None, "reason": str(exc)}
        except RuntimeError as exc:
            return {"status": "prediction_failure", "points": None, "reason": str(exc)}
        return {"status": "estimated_hand_presence_unverified", "points": points}


def fit(training, validation, mode: str, epochs: int):
    # Same seed and training recipe for A and B; only input channels differ.
    torch.manual_seed(123)
    x = torch.cat([input_tensor(clip["rgb"], mode) for clip in training])
    y = torch.from_numpy(np.concatenate([clip["xy"] for clip in training])).reshape(-1, 42)
    valid = torch.isfinite(y).all(dim=1)
    x, y = x[valid], y[valid]
    model = network(mode)
    optimizer = torch.optim.AdamW(model.parameters(), lr=.001, weight_decay=.001)
    loss = nn.SmoothL1Loss(beta=.04)

    def predict(rgb):
        return predict_clip(model, rgb, mode)

    best = None
    for epoch in range(1, epochs + 1):
        model.train()
        for indices in torch.randperm(len(y)).split(32):
            images, landmarks = x[indices].clone(), y[indices].clone()
            flip = torch.rand(len(indices)) < .5
            images[flip] = images[flip].flip(-1)
            landmarks[flip, ::2] = 1 - landmarks[flip, ::2]
            optimizer.zero_grad()
            objective = loss(model(images), landmarks)
            objective.backward()
            optimizer.step()
        model.eval()
        score = evaluate(validation, predict, None, extract=lambda rgb, _: rgb)
        if best is None or score["nme"] < best[0]["nme"]:
            best = score, epoch, copy.deepcopy(model.state_dict())
    score, epoch, state = best
    model.load_state_dict(state)
    model.eval()
    return score, epoch, model, predict


def run_domain(clips, epochs: int, output_dir: Path, domain: str):
    groups = {key: [clip for clip in clips if clip["split"] == key]
              for key in ("train", "validation", "test")}
    if any(not value for value in groups.values()):
        raise ValueError("train, validation, and test partitions must all be non-empty")
    def split_group(clip):
        if domain == "recorded":
            return f"recorded-source:{clip['source']}"
        return f"synthetic-seed:{int(clip['source'].split('-')[1])}"
    group_ids = {key: {split_group(clip) for clip in value} for key, value in groups.items()}
    if any(left & right for i, left in enumerate(group_ids.values())
           for right in list(group_ids.values())[i + 1:]):
        raise ValueError("a source group crosses train/validation/test partitions")
    result = {"domain": domain, "split_clip_counts": {k: len(v) for k, v in groups.items()},
              "split_source_groups": {k: sorted(v) for k, v in group_ids.items()},
              "models": {}}
    input_shapes = {tuple(clip["rgb"].shape[1:3]) for clip in groups["train"]}
    if len(input_shapes) != 1:
        raise ValueError(f"training clips do not share an input resolution: {sorted(input_shapes)}")
    input_height, input_width = next(iter(input_shapes))
    result["split_clip_ids"] = {k: sorted(clip["name"] for clip in v)
                                for k, v in groups.items()}
    for mode in MODES:
        validation, epoch, model, predictor = fit(groups["train"], groups["validation"], mode, epochs)
        held_out = evaluate(groups["test"], predictor, None, extract=lambda rgb, _: rgb)
        artifact = {
            "format": "realtime_occluded_hand_model_v1", "mode": mode,
            "domain": domain, "input_channels": 3 if mode == "A_current" else 6,
            "input_size_wh": [input_width, input_height],
            "joint_count": 21, "coordinate_format": "normalized_image_xy",
            "session_start": "B duplicates current frame as previous frame",
            "hand_presence_policy": "hand-present training only; finite coordinates do not certify a hand is present; malformed RGB returns explicit failure status",
            "architecture": "three-stage CNN, GroupNorm+SiLU, 4x4 adaptive pool, 128 hidden units",
            "training_seed": 123, "epochs_requested": epochs, "selected_epoch": epoch,
            "weights": model.state_dict(),
        }
        path = output_dir / f"{domain}_{mode}.pt"
        with path.open("xb") as handle:
            torch.save(artifact, handle)
        result["models"][mode] = {
            "checkpoint": path.name, "selected_epoch": epoch,
            "validation": validation, "held_out": held_out,
        }
        print(json.dumps({"domain": domain, "mode": mode, "held_out": held_out}), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic", type=Path, required=True)
    parser.add_argument("--recorded", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=16, choices=range(1, 101), metavar="1..100")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(4)
    clips = [*read_synthetic(args.synthetic), *read_recorded(args.recorded)]
    report = {
        "scope": "A current RGB only; B previous and current RGB only; no future input",
        "hand_presence_policy": "A/B estimate pose on every valid RGB frame. Their training data does not teach no-hand rejection, so hand presence remains unverified and requires a separate policy for deployment.",
        "split_source": "same grouped splits as occluded_pose_benchmark.py",
        "training_conditions": {
            "seed": 123, "optimizer": "AdamW(lr=0.001, weight_decay=0.001)",
            "loss": "SmoothL1(beta=0.04)", "batch_size": 32,
            "horizontal_flip_probability": 0.5,
            "epoch_selection": "lowest validation NME; test split used once after selection",
        },
        "results": {},
    }
    for domain in ("2d", "3d", "recorded"):
        subset = [clip for clip in clips if clip["mode"] == domain]
        report["results"][domain] = run_domain(subset, args.epochs, args.output_dir, domain)
    report_path = args.output_dir / "report.json"
    with report_path.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
        handle.write("\n")


if __name__ == "__main__":
    main()
