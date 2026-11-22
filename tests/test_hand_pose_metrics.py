import numpy as np
import json
import tempfile
from pathlib import Path

from analysis.hand_pose_metrics import (
    mean_per_joint_acceleration_error,
    pck_curve_and_auc,
    vera_prediction_stability,
)
from analysis.external_hand_verification import aggregate, metrics


def test_pck_and_auc_perfect_predictions():
    errors = np.zeros((2, 21), dtype=float)
    mask = np.ones_like(errors, dtype=bool)
    result = pck_curve_and_auc(errors, mask)
    assert all(value == 1.0 for value in result['pck'].values())
    assert result['auc'] == 1.0


def test_pck_counts_missed_joint_as_failure_and_offset_affects_auc():
    errors = np.array([[0.0, 0.1, 0.3, np.nan]])
    mask = np.ones_like(errors, dtype=bool)
    result = pck_curve_and_auc(errors, mask)
    assert result['pck']['0.10'] == 0.5
    assert result['pck']['0.20'] == 0.5
    assert result['pck']['0.50'] == 0.75
    assert np.isclose(result['auc'], 0.5875)


def test_acceleration_error_zero_for_exact_and_constant_offset_tracks():
    gt = np.zeros((4, 21, 2), dtype=float)
    pred = gt + np.array([7.0, -3.0])
    got = mean_per_joint_acceleration_error(gt, pred, np.ones(4, bool), 30, pixel_scale=(1, 1))
    assert got['pixel_per_s2'] == 0.0
    assert got['valid_joint_windows'] == 42


def test_acceleration_error_scales_quadratically_with_fps_and_skips_missing_triplet():
    gt = np.zeros((3, 21, 2), dtype=float)
    pred = np.ones_like(gt)
    pred[1, :, 0] += 1
    one = mean_per_joint_acceleration_error(gt, pred, np.ones(3, bool), 1)
    two = mean_per_joint_acceleration_error(gt, pred, np.ones(3, bool), 2)
    assert np.isclose(one['pixel_per_s2'], 2.0)
    assert np.isclose(two['pixel_per_s2'], 4 * one['pixel_per_s2'])
    missed = mean_per_joint_acceleration_error(gt, pred, [True, False, True], 30)
    assert missed['pixel_per_s2'] is None
    assert missed['valid_joint_windows'] == 0


def test_vera_stability_is_prediction_intrinsic_and_respects_valid_window_minimum():
    points = np.zeros((14, 21, 2), dtype=float)
    valid = np.ones((14, 21), dtype=bool)
    result = vera_prediction_stability(points, valid, np.ones(14, bool), min_windows=10)
    assert result['jacc_image_relative'] == 0.0
    assert result['jjerk_image_relative'] == 0.0
    assert result['ev_image_relative'] == 0.0
    assert result['jacc_joints_used'] == 21
    missing = vera_prediction_stability(points, valid, [True, False] * 7, min_windows=10)
    assert missing['jacc_image_relative'] is None
    assert missing['jjerk_image_relative'] is None


def test_occlusion_level_subgroups_keep_hidden_and_all_joint_denominators_distinct():
    gt = np.full((14, 21, 2), 0.4, dtype=float)
    gt[:, 0] = [0.45, 0.50]
    gt[:, 9] = [0.50, 0.50]
    hidden = np.zeros((14, 21), dtype=bool)
    hidden[:, 4] = True
    result = metrics(gt, hidden, gt.copy(), np.ones(14, bool), 30)
    low = result['by_occlusion_level']['0-25%']
    none = result['by_occlusion_level']['none']
    assert low['hidden_joint_frames'] == 14
    assert low['hidden_joint_pck_curve_and_auc']['auc'] == 1.0
    assert low['all_joint_frames'] == 14 * 21
    assert none['hidden_joint_frames'] == 0
    assert none['hidden_joint_error_px_valid_predictions'] is None
    unoccluded = metrics(gt, np.zeros_like(hidden), gt.copy(), np.ones(14, bool), 30)
    none = unoccluded['by_occlusion_level']['none']
    assert none['all_joint_frames'] == 14 * 21
    assert np.isclose(none['all_joint_error_px_valid_predictions'], 0.0)


def test_external_aggregate_emits_new_accuracy_summary_and_video_pairs():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        gt = np.full((14, 21, 2), 0.4, dtype=float)
        gt[:, 0] = [0.45, 0.50]
        gt[:, 9] = [0.50, 0.50]
        hidden = np.zeros((14, 21), dtype=bool)
        pred = gt.tolist()
        result = {'xy': pred, 'detection': [True] * len(gt), 'total_seconds': 1.0}
        clip = {
            'session': 'demo', 'side': 'right', 'stem': 'clip',
            'video_sha256': 'v', 'label_sha256': 'l',
            'source_width': 512, 'source_height': 420, 'fps': 30.0,
            'frames': len(gt), 'duration_seconds': len(gt) / 30,
            'mask': {'center_x': 256, 'center_y': 210, 'radius_px': 95},
            'letterbox': {'scale': 1.0, 'offset_x': 0, 'offset_y': 0},
            'decode_seconds': 0.1, 'transform_seconds': 0.1,
            'xy': gt.tolist(), 'hidden': hidden.tolist(),
        }
        for backend, model in (('local', '2d'), ('realtime', '2d_A_current'),
                               ('hamer', 'hamer'), ('mediapipe', 'mediapipe')):
            row = dict(clip)
            row['models'] = {'circle': {model: result}}
            (root / f'{backend}_predictions.json').write_text(
                json.dumps({'backend': backend, 'records': [row]}), encoding='utf-8')
        aggregate(root)
        report = json.loads((root / 'external_hand_verification.json').read_text(encoding='utf-8'))
        summary = report['accuracy_summary']['local:2d:circle']
        assert summary['mpjpe_2d_px_valid_predictions_micro'] == 0.0
        assert summary['pck_auc_0_to_0_5_palm_micro'] == 1.0
        assert summary['detection_success_rate_micro'] == 1.0
        realtime_summary = report['accuracy_summary']['realtime:2d_A_current:circle']
        assert realtime_summary['mpjpe_2d_px_valid_predictions_micro'] == 0.0
        assert report['paired_video_comparisons']['results']
