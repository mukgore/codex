# Occluded hand-pose benchmark

Offline 2D/3D/recorded-video joint-estimation experiments. No CAPTCHA scoring endpoint is used. Inference predicts from RGB frames and adjacent-frame pixels; held-out joint coordinates are used only for scoring.

## Grouped-split result

The synthetic split groups both clips from each generator PRNG seed together: seeds 1–16 train, 17–20 validation, and 21–24 test. This prevents the two correlated clips emitted by one random stream from crossing partitions. Hyperparameters and model choice use validation data. The table uses 15 evenly spaced frames per test clip; NME is palm-normalized image-plane distance (lower is better), and PCK@0.2 is the share of joints within 0.2 palm lengths.

| Domain | Selected model | Test clips / frames | Model NME | HaMeR NME | Model PCK@0.2 | HaMeR PCK@0.2 | Model hidden NME | HaMeR hidden NME |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2D synthetic | temporal-edge ridge | 8 / 120 | 0.0055 | 0.1519 | 1.000 | 0.785 | 0.0037 | 0.1378 |
| 3D synthetic | temporal-edge ridge | 8 / 120 | 0.0049 | 0.1374 | 1.000 | 0.876 | 0.0036 | 0.1291 |
| Recorded | temporal-edge ridge, out-of-fold selected | 2 / 30 | 0.1107 | 0.2081 | 0.852 | 0.754 | n/a | n/a |

HaMeR uses pinned upstream source revision `3a01849f4148352e9260b69bf28b65d1671a4905` and its official `hamer.ckpt`. It receives the correct hand side and a fixed centered full-frame crop. The local model receives pixels only.

### Limits

- Synthetic reference points are exact projected rig landmarks, but both train and test images come from the same procedural renderer. The scores show in-renderer performance and do not establish transfer to different renderers, hands, cameras, or real lighting.
- Recorded reference points are legacy tracker estimates, not independently annotated anatomical ground truth. Recorded metrics measure agreement with that tracker, over two held-out clips, and do not establish anatomical accuracy.
- The ridge features use the previous and following frames, so they are offline, bidirectional estimates rather than a causal real-time tracker.
- Raw video, generated frames, and annotation files are not included in this commit. They remain in the local research workspace. The reports and selected model weights are included.

## Files

- `results/grouped-v2/selection-report.json`: split and validation-selected ridge results.
- `results/grouped-v2/hamer-matched-report.json`: matched HaMeR comparison for synthetic data and baseline local estimators.
- `results/grouped-v2/hamer-recorded-refined-report.json`: matched recorded comparison using the leave-one-clip-out selected estimator.
- `results/grouped-v2/ridge-weights/`: selected grouped-split 2D and 3D model weights.
- `results/grouped-v2/recorded-refinement/`: selected recorded estimator weights and out-of-fold model-selection report.
- `results/grouped-v2/cnn/report.json`: CNN comparison; the ridge estimators were selected for 2D/3D, and the out-of-fold recorded refinement was selected for recorded footage.

The source scripts are in the parent `analysis/` directory: `occluded_pose_benchmark.py`, `train_occluded_pose_cnn.py`, `refine_recorded_pose.py`, `measure_hamer_pose.py`, and `render_pose_benchmark.cjs`.
