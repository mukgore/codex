"""Contract checks for causal A/B frame access and session reset behavior."""

import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
from train_realtime_occluded_hand_models import (  # noqa: E402
    MODES, StreamingEstimator, input_tensor, network, predict_clip, predict_stream_frame,
)


def test_input_shapes_and_b_is_past_current_only():
    rgb = np.arange(5 * 8 * 9 * 3, dtype=np.uint8).reshape(5, 8, 9, 3)
    a = input_tensor(rgb, "A_current")
    b = input_tensor(rgb, "B_past_current")
    assert tuple(a.shape) == (5, 3, 8, 9)
    assert tuple(b.shape) == (5, 6, 8, 9)
    assert torch.equal(b[0, :3], b[0, 3:])  # session start repeats current
    assert torch.equal(b[2, :3], a[1])
    assert torch.equal(b[2, 3:], a[2])


def test_prediction_at_t_is_invariant_to_future_frames():
    torch.manual_seed(17)
    rng = np.random.default_rng(42)
    frames = rng.integers(0, 256, (6, 32, 32, 3), dtype=np.uint8)
    changed_future = frames.copy()
    changed_future[3:] = 255 - changed_future[3:]
    assert not np.array_equal(frames[3:], changed_future[3:])
    for mode in MODES:
        model = network(mode).eval()
        # The batch helper also receives the full clip, but must remain causal.
        batch_original = predict_clip(model, frames, mode)[2]
        batch_altered = predict_clip(model, changed_future, mode)[2]
        assert np.array_equal(batch_original, batch_altered)
        original = StreamingEstimator(model, mode)
        altered = StreamingEstimator(model, mode)
        for frame in frames[:3]:
            prediction = original.predict(frame)
        for frame in changed_future[:3]:
            altered_prediction = altered.predict(frame)
        assert np.array_equal(prediction, altered_prediction)


def test_b_streaming_uses_previous_and_resets_between_sessions():
    torch.manual_seed(19)
    rng = np.random.default_rng(73)
    first, second = rng.integers(0, 256, (2, 32, 32, 3), dtype=np.uint8)
    model = network("B_past_current").eval()
    stream = StreamingEstimator(model, "B_past_current")
    first_prediction = stream.predict(first)
    assert np.array_equal(first_prediction, predict_stream_frame(model, first, None, "B_past_current"))
    second_prediction = stream.predict(second)
    assert np.array_equal(second_prediction,
                          predict_stream_frame(model, second, first, "B_past_current"))
    stream.reset()
    reset_prediction = stream.predict(second)
    assert np.array_equal(reset_prediction,
                          predict_stream_frame(model, second, None, "B_past_current"))


def test_rejects_future_or_unknown_context_mode():
    rgb = np.zeros((2, 8, 8, 3), dtype=np.uint8)
    try:
        input_tensor(rgb, "A_current_plus_future")
    except ValueError:
        return
    raise AssertionError("unknown/future context mode must be rejected")


def test_streaming_preprocesses_camera_size_and_rejects_bad_pixels():
    torch.manual_seed(23)
    stream = StreamingEstimator(network("A_current"), "A_current", (80, 66))
    output = stream.predict(np.zeros((420, 512, 3), dtype=np.uint8))
    assert output.shape == (21, 2)
    assert np.isfinite(output).all()
    previous_before = stream.previous_rgb.copy()
    try:
        stream.predict(np.zeros((420, 512, 3), dtype=np.float32))
    except ValueError:
        pass
    else:
        raise AssertionError("non-uint8 RGB input must be rejected")
    failed = stream.infer(np.zeros((420, 512, 3), dtype=np.float32))
    assert failed["status"] == "invalid_input" and failed["points"] is None
    assert np.array_equal(stream.previous_rgb, previous_before)
