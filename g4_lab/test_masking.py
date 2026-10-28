"""Synthetic safety checks for strict 2D mask preflight and rendering."""
from __future__ import annotations

import copy
import unittest
from unittest.mock import patch

import numpy as np

from .masking import LANDMARK_NAMES, mask_video_frames, preflight_masks


TEST_W3 = 1.95  # Test scalar only; it is not a calibrated or recommended weight.


def fixture_frame(index: int, *, z: float = 0.0) -> dict:
    points = {
        name: {"x": 32.0, "y": 32.0, "z": z}
        for name in LANDMARK_NAMES
    }
    points["WRIST"].update(x=16.0 + index, y=32.0)
    points["MIDDLE_MCP"].update(x=24.0 + index, y=32.0)
    return {"frame_idx": index, "detected": True, "landmarks_px": points}


class StrictMaskingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.images = [
            np.full((64, 64, 3), 180 + i, dtype=np.uint8)
            for i in range(3)
        ]
        self.before = [image.copy() for image in self.images]
        self.frames = [fixture_frame(i, z=0.5 * i) for i in range(3)]

    def test_complete_fixture_masks_copies_and_preserves_source_images(self) -> None:
        output = mask_video_frames(self.images, self.frames, w3=TEST_W3)
        self.assertEqual(len(output), 3)
        for source, before, masked in zip(self.images, self.before, output):
            np.testing.assert_array_equal(source, before)
            self.assertFalse(np.shares_memory(source, masked))
            self.assertTrue(np.any(masked != source))

    def test_z_only_changes_do_not_change_2d_masks(self) -> None:
        changed_z = copy.deepcopy(self.frames)
        for i, frame in enumerate(changed_z):
            for point in frame["landmarks_px"].values():
                point["z"] = -10_000.0 - i
        self.assertEqual(
            preflight_masks(self.frames, w3=TEST_W3),
            preflight_masks(changed_z, w3=TEST_W3),
        )
        original_output = mask_video_frames(self.images, self.frames, w3=TEST_W3)
        changed_output = mask_video_frames(self.images, changed_z, w3=TEST_W3)
        for left, right in zip(original_output, changed_output):
            np.testing.assert_array_equal(left, right)

    def test_entire_frame_map_is_checked_before_any_circle_is_drawn(self) -> None:
        invalid = copy.deepcopy(self.frames)
        invalid[1]["detected"] = False
        with patch("g4_lab.masking.cv2.circle", wraps=__import__("cv2").circle) as draw:
            with self.assertRaises(ValueError):
                mask_video_frames(self.images, invalid, w3=TEST_W3)
            draw.assert_not_called()

    def test_image_count_mismatch_fails_before_drawing(self) -> None:
        with patch("g4_lab.masking.cv2.circle", wraps=__import__("cv2").circle) as draw:
            with self.assertRaisesRegex(ValueError, "count mismatch"):
                mask_video_frames(self.images, self.frames[:2], w3=TEST_W3)
            draw.assert_not_called()

    def test_unknown_or_missing_frame_mapping_fails_closed(self) -> None:
        bad = copy.deepcopy(self.frames)
        bad[1]["landmarks_px"].pop("MIDDLE_MCP")
        with self.assertRaises(ValueError):
            preflight_masks(bad, w3=TEST_W3)
        bad = copy.deepcopy(self.frames)
        bad[1]["detected"] = None
        with self.assertRaises(ValueError):
            preflight_masks(bad, w3=TEST_W3)

    def test_bad_shape_nonfinite_and_zero_scale_fail_closed(self) -> None:
        bad = copy.deepcopy(self.frames)
        bad[0]["landmarks_px"]["WRIST"].pop("y")
        with self.assertRaises(ValueError):
            preflight_masks(bad, w3=TEST_W3)

        bad = copy.deepcopy(self.frames)
        bad[0]["landmarks_px"]["WRIST"]["x"] = float("nan")
        with self.assertRaises(ValueError):
            preflight_masks(bad, w3=TEST_W3)

        bad = copy.deepcopy(self.frames)
        bad[0]["landmarks_px"]["MIDDLE_MCP"].update(
            bad[0]["landmarks_px"]["WRIST"]
        )
        with self.assertRaises(ValueError):
            preflight_masks(bad, w3=TEST_W3)

    def test_frame_index_order_and_w3_are_validated(self) -> None:
        bad = copy.deepcopy(self.frames)
        bad[2]["frame_idx"] = bad[1]["frame_idx"]
        with self.assertRaises(ValueError):
            preflight_masks(bad, w3=TEST_W3)
        bad = copy.deepcopy(self.frames)
        bad[1]["frame_idx"] = 2
        bad[2]["frame_idx"] = 3
        with self.assertRaisesRegex(ValueError, "contiguous"):
            preflight_masks(bad, w3=TEST_W3)
        for invalid_w3 in (True, 0.0, float("inf"), float("nan")):
            with self.subTest(w3=invalid_w3):
                with self.assertRaises(ValueError):
                    preflight_masks(self.frames, w3=invalid_w3)


if __name__ == "__main__":
    unittest.main()
