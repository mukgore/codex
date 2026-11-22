"""Metric helpers for the occluded 2D hand-pose external evaluation.

MPJPE / PCK / Accel follow their cited distance and finite-difference forms;
the coordinate spaces and missing-prediction policy are explicitly adapted
for this 2D benchmark. VERA-Hand temporal metrics are kept as estimator-only
stability descriptors, not ground-truth accuracy scores.
"""

from __future__ import annotations

import numpy as np


PCK_THRESHOLDS_PALM = (0.02, 0.05, 0.10, 0.20, 0.30, 0.50)
PCK_AUC_MAX_PALM = 0.50
VERA_MIN_WINDOWS_PER_JOINT = 10


def pck_curve_and_auc(normalized_errors, reference_mask, *, max_threshold=PCK_AUC_MAX_PALM):
    """PCK@alpha with missing estimates counted incorrect and normalized AUC.

    ``normalized_errors`` has NaN for unavailable predictions, and
    ``reference_mask`` selects annotated joints. The curve is evaluated on
    an explicit 0..max_threshold grid with trapezoidal integration; AUC is
    divided by the interval width to remain in [0, 1].
    """
    errors = np.asarray(normalized_errors, dtype=np.float64)
    mask = np.asarray(reference_mask, dtype=bool)
    if errors.shape != mask.shape:
        raise ValueError('normalized_errors and reference_mask must have equal shape')
    eligible = int(mask.sum())
    if eligible == 0:
        return {'pck': {}, 'auc': None, 'auc_interval': [0.0, float(max_threshold)],
                'auc_grid': [], 'eligible_joint_frames': 0}
    thresholds = np.asarray((0.0, *PCK_THRESHOLDS_PALM), dtype=np.float64)
    thresholds = thresholds[thresholds <= max_threshold]
    if thresholds[-1] != max_threshold:
        thresholds = np.append(thresholds, max_threshold)
    values = np.asarray([np.count_nonzero(mask & np.isfinite(errors) & (errors <= alpha)) / eligible
                         for alpha in thresholds], dtype=np.float64)
    auc = float(np.trapz(values, thresholds) / max_threshold)
    return {'pck': {f'{alpha:.2f}': float(value) for alpha, value in zip(thresholds[1:], values[1:])},
            'auc': auc, 'auc_interval': [0.0, float(max_threshold)],
            'auc_grid': [{'threshold': float(a), 'pck': float(v)} for a, v in zip(thresholds, values)],
            'eligible_joint_frames': eligible}


def mean_per_joint_acceleration_error(target, prediction, detection, fps, *, pixel_scale=(1.0, 1.0), palm_px=None):
    """Mean per-joint Euclidean difference of GT/predicted accelerations.

    Uniform-frame second differences are multiplied by ``fps**2``. Only
    triplets with GT and predictions at all three frames are scored. Returns
    pixel/s^2 and palm-length/s^2 values and the number of valid joint windows.
    """
    gt = np.asarray(target, dtype=np.float64)
    pred = np.asarray(prediction, dtype=np.float64)
    detected = np.asarray(detection, dtype=bool)
    scale = np.asarray(pixel_scale, dtype=np.float64)
    if gt.shape != pred.shape or gt.ndim != 3 or gt.shape[-1] != 2:
        raise ValueError('target and prediction must have matching [frames,joints,2] shape')
    if len(detected) != len(gt) or fps <= 0:
        raise ValueError('detection length must match frames and fps must be positive')
    valid = np.isfinite(gt).all(axis=-1) & detected[:, None] & np.isfinite(pred).all(axis=-1)
    triple = valid[:-2] & valid[1:-1] & valid[2:]
    if not triple.any():
        return {'pixel_per_s2': None, 'palm_per_s2': None, 'valid_joint_windows': 0,
                'valid_frame_triplets': int(np.count_nonzero(triple.any(axis=1)))}
    gt_px, pred_px = gt * scale, pred * scale
    gt_acc = (gt_px[2:] - 2 * gt_px[1:-1] + gt_px[:-2]) * (fps ** 2)
    pred_acc = (pred_px[2:] - 2 * pred_px[1:-1] + pred_px[:-2]) * (fps ** 2)
    error = np.linalg.norm(pred_acc - gt_acc, axis=-1)
    pixel_mean = float(error[triple].mean())
    if palm_px is None:
        palm_mean = None
    else:
        palms = np.asarray(palm_px, dtype=np.float64)
        joint_scale = np.maximum((palms[:-2] + palms[1:-1] + palms[2:]) / 3, 1e-8)
        palm_mean = float((error / joint_scale[:, None])[triple].mean())
    return {'pixel_per_s2': pixel_mean, 'palm_per_s2': palm_mean,
            'valid_joint_windows': int(triple.sum()),
            'valid_frame_triplets': int(np.count_nonzero(triple.any(axis=1)))}


def vera_prediction_stability(prediction, valid_joint, detection, *, min_windows=VERA_MIN_WINDOWS_PER_JOINT):
    """VERA-Hand Jacc/Jjerk/Ev forms on image-relative coordinates.

    This intentionally uses the official release's finite-difference
    stencils and threshold of valid windows per joint. These are intrinsic
    prediction-trajectory descriptors, not errors against ground truth.
    """
    points = np.asarray(prediction, dtype=np.float64)
    valid = np.asarray(valid_joint, dtype=bool) & np.isfinite(points).all(axis=-1)
    detected = np.asarray(detection, dtype=bool)
    if points.ndim != 3 or points.shape[-1] != 2 or len(detected) != len(points):
        raise ValueError('prediction must be [frames,joints,2] and detection must match frames')
    valid &= detected[:, None]

    def mean_by_joint(window_offsets, stencil):
        per_joint = [[] for _ in range(points.shape[1])]
        for center in range(-min(window_offsets), len(points) - max(window_offsets)):
            ids = [center + offset for offset in window_offsets]
            if not valid[ids].all():
                continue
            values = points[ids]
            delta = np.tensordot(np.asarray(stencil), values, axes=(0, 0))
            magnitude = np.linalg.norm(delta, axis=-1)
            for j in range(points.shape[1]):
                per_joint[j].append(float(magnitude[j]))
        kept = [float(np.mean(v)) for v in per_joint if len(v) >= min_windows]
        return (float(np.mean(kept)) if kept else None, len(kept),
                [len(v) for v in per_joint])

    jacc, jacc_joints, jacc_counts = mean_by_joint((-1, 0, 1), (1, -2, 1))
    jjerk, jjerk_joints, jjerk_counts = mean_by_joint((-2, -1, 0, 1, 2), (-1, 2, 0, -2, 1))
    ev, ev_joints, ev_counts = mean_by_joint((0, 1), (-1, 1))
    return {'jacc_image_relative': jacc, 'jacc_joints_used': jacc_joints,
            'jacc_windows_per_joint': jacc_counts,
            'jjerk_image_relative': jjerk, 'jjerk_joints_used': jjerk_joints,
            'jjerk_windows_per_joint': jjerk_counts,
            'ev_image_relative': ev, 'ev_joints_used': ev_joints,
            'ev_windows_per_joint': ev_counts,
            'min_windows_per_joint': int(min_windows),
            'definition': 'VERA-Hand release stencils in image-relative coordinates; median-across-video aggregation is a separate step'}
