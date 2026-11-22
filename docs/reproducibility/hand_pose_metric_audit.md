# Hand-pose metric audit and implementation

Audit date: 2026-11-22. Scope: the existing fixed-occlusion GigaHands external-video comparison in `analysis/external_hand_verification.py`. Existing grouped-v15 weights, source annotations, and prior result files are retained. The evaluator writes new result files exclusively.

## Literature-to-metric mapping

| Source and location | Source definition | This evaluation | Classification |
|---|---|---|---|
| Zeng et al., *SmoothNet: A Plug-and-Play Network for Refining Human Poses in Videos*, ECCV 2022, Sec. 2.1 and Sec. 4.3 Eqs. (3)-(4), [paper](https://arxiv.org/abs/2112.13715) | Names MPJPE as mean per-joint position error and Accel as mean per-joint acceleration error. The objective compares predicted and GT positions/accelerations; Sec. 4.2 Eq. (2) defines acceleration by adjacent first differences. | **2D MPJPE**: mean Euclidean image-plane distance over labeled joints with a valid prediction, in canonical-canvas pixels and after division by the frame's wrist-to-middle-MCP length. **Mean per-joint acceleration error (Accel)**: mean Euclidean distance between predicted and GT second differences, multiplied by `fps²`; output units px/s² and palm-length/s². Only fully labeled, detected three-frame windows count. | Position metric uses the paper's distance form in 2D (dimension adaptation). Accel uses the paper's GT-vs-estimated acceleration-error meaning and uniform-sampling finite difference (2D/unit adaptation); the benchmark reports its mask, valid-window rule, and units. |
| Sun et al., *CrossFuNet: RGB and Depth Cross-Fusion Network for Hand Pose Estimation*, Sensors 2021, Sec. 4.2 Eqs. (5)-(6), [paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC8473363/) | MPJPE is Euclidean error averaged over test frames and joints; AUC is the area under PCK, with the paper's cited 3D hand datasets using 20–50 mm thresholds. | **PCK@α** at palm-normalized thresholds α = .02, .05, .10, .20, .30, .50; `<=` is correct. **PCK-AUC** integrates the PCK curve from 0 to 0.50 palm lengths by trapezoidal integration and divides by interval width. A labeled joint missed by a model is a PCK failure. | PCK is a threshold adaptation. AUC is a disclosed 2D, palm-normalized adaptation; it is not CrossFuNet's 20–50 mm physical 3D AUC. |
| Rong & Gang, *Coordinate-Corrected and Graph-Convolution-Based Hand Pose Estimation Method*, Sensors 2024, Sec. 5.2.1 Eq. (19), [paper](https://www.mdpi.com/1424-8220/24/22/7289) | The paper names EPE and Eq. (19) writes the Euclidean distance in 3D; the paper also reports a 2D experiment table, median EPE, and AUC(0–50 mm). | No separate `EPE` field is added. Its mean Euclidean-distance form is already represented by 2D MPJPE here; median position error is included as a descriptive companion. | Redundant with the selected position metric. We retain MPJPE as the selected name for the 2D adaptation rather than treating EPE as a distinct statistic. |
| Benitez-Garcia & Takahashi, *VERA-Hand: A Verified Multidimensional Benchmark for 2D Hand Pose Estimation in Third-Person Dynamic Gesture Videos*, arXiv 2610.32517 v1 (2026), WACV 2027 accepted; [paper](https://arxiv.org/abs/2610.32517), [official release and code](https://github.com/GibranBenitez/VERA-Hand), `metrics/temporal.py` | Official code defines `Jacc` using the 3-frame second-difference stencil, `Jjerk` using its 5-frame central jerk stencil, and `Ev` using adjacent-frame velocity magnitudes. Coordinates are image-relative. Per-joint means require at least 10 valid windows; final code aggregates video values by median and scales ×100. | `Jacc`, `Jjerk`, and `Ev` are emitted per clip in image-relative units with official stencils, complete-window validity, and the 10-window-per-joint rule. They remain intrinsic prediction-stability descriptors, separate from GT accuracy. | Official release-code reproduction for stencils and per-joint eligibility; per-video median ×100 is only appropriate for the paper-style multi-video summary, not the per-clip record. |
| VERA-Hand, `vera_supervised.py` and metric package; same official source | `Det-F1` evaluates matched hand-instance detection. `Pose-F1` requires both detection and localization, using PCK threshold α and minimum per-hand PCK β (default α=.10, β=.50). | Not computed in the current single-target clip format. The selected clips contain a labeled target hand throughout, and current inference records only the assigned target pose; this does not retain all unmatched/spurious hand instances or negative no-hand frames needed for a faithful Det-F1/Pose-F1 protocol. Existing detection success/failure is reported separately. | Reviewed, not applicable to this output schema. Revisit if inference preserves all detections and the evaluation set includes no-hand/other-hand frames. |
| Kim et al., *WatchHand: Enabling Continuous Hand Pose Tracking On Off-the-Shelf Smartwatches*, CHI 2026, [paper](https://arxiv.org/abs/2602.21610) | Uses `MPJPE` and `MPJAE` for 3D tracking of 20 finger joints, but its accessible paper text does not specify a formula for MPJAE. | Existing 15-triple 2D angle comparison is named `mean_absolute_2d_joint_angle_error_degrees_15triples`. | Retained as a study-specific 2D angle-error statistic; not claimed to reproduce WatchHand MPJAE. |
| Existing `hand_captcha_prod.html` | Legacy challenge score combines 15 landmark-angle terms, an internal 1.2× target resampling/sliding-window angle comparison, and second-difference motion discrepancy with detection-rate scaling and production weights/cutoff. | Retained as `production_score_analog`, explicitly described as a whole-clip legacy-score analogue, not a pose-accuracy metric and not standard DTW. | Legacy comparator, separated from academic accuracy metrics. |

## Definitions and denominator policy

For labeled joint set `G`, prediction `p[t,j]`, reference `g[t,j]`, and per-frame palm length `s[t]` (wrist to middle MCP):

* 2D MPJPE: `mean_{(t,j) in V} ||p[t,j] - g[t,j]||_2`, where `V` contains labeled joints with a finite detected prediction. Report px and `error/s[t]` separately.
* PCK@α: `count(error[t,j] <= α*s[t]) / count(labeled joints)`. Missing prediction is a miss, not removed from the denominator. The AUC uses this same denominator at every threshold.
* PCK-AUC: `trapz(PCK(α), α) / 0.50`, on α in `[0, 0.50]`, with explicit grid `[0, .02, .05, .10, .20, .30, .50]`.
* Accel: `mean ||(p[t+1]-2p[t]+p[t-1] - (g[t+1]-2g[t]+g[t-1])) * fps²||_2`, over joints/triples that have GT and a valid model detection at all three frames. A trajectory cannot contribute an acceleration sample across a missed frame.
* VERA-Hand prediction-only stability (image-relative x/W,y/H): `Jacc = mean_joint(mean_valid_t ||q[t+1]-2q[t]+q[t-1]||₂)`; `Jjerk = mean_joint(mean_valid_t ||q[t+2]-2q[t+1]+2q[t-1]-q[t-2]||₂)`; and `Ev = mean_joint(mean_valid_t ||q[t+1]-q[t]||₂)`. A frame window is valid only when the target track is detected and the relevant coordinates are finite throughout. A joint contributes only with at least 10 valid windows. Official release-code summaries take the median across videos and scale each by 100; per-video result fields here are the unscaled values.
* Existing 20 bone-length differences and the 15 2D joint-angle differences remain custom structural summaries; they are not called MPJPE/MPJAE.
* Occlusion fraction and duration, hidden/visible position errors, and finger/joint-region breakdowns are strata of the base metrics, not newly named standards.
* Runtime, detection coverage/failure, and video-level confidence intervals are reported outside the accuracy-metric family.

## Implemented outputs

`analysis/hand_pose_metrics.py` supplies PCK/AUC, GT-relative acceleration error, and VERA-Hand temporal-stability calculations. `analysis/external_hand_verification.py` adds those fields to every model/video/occlusion-condition record while retaining existing error, failure, occlusion, and legacy-score fields. It also emits joint-frame-pooled accuracy summaries, video-level timing summaries, and paired video-bootstrap intervals. The current five-clip convenience sample remains too small and partly participant-correlated for population-level inference.

Unit checks are in `tests/test_hand_pose_metrics.py`. In the current HaMeR Python runtime, `pytest` is not installed, so all seven assertion checks were executed directly with Python and passed; these cover denominator behavior, FPS scaling, VERA stencils, occlusion strata, and a synthetic end-to-end aggregate report. The evaluator modules and test file also compiled successfully. Re-evaluation writes new JSON files and will not overwrite existing result artifacts.

PowerShell reproduction for this workspace:

```powershell
$pythonExe = 'C:\Users\조영준!\Documents\CLI\deliverables-review\private_artifacts\mano_cpu_runtime_20261105\venv\Scripts\python.exe'
& $pythonExe -c "import sys; sys.path.insert(0,'tests'); import test_hand_pose_metrics as t; [getattr(t,n)() for n in dir(t) if n.startswith('test_')]"
& $pythonExe analysis/external_hand_verification.py --backend aggregate --output-dir 'C:\Users\조영준!\Documents\CLI\usability\qa\external-hand-verification\results'
```

The aggregate command requires all three backend prediction files to exist; it writes a new `external_hand_verification.json` and intentionally errors if that path already exists.

## Reviewed but excluded

* `Det-F1` / `Pose-F1`: current output schema lacks independent all-instance matching and negative no-hand frames.
* `MPJAE`: the cited WatchHand paper reports the metric name but does not expose a calculation formula in accessible text, and its task is 3D with 20 finger joints. The current 2D 15-triple value remains custom.
* `EPE`: the cited hand paper uses it for 3D. Mean-EPE's Euclidean form overlaps with the 2D MPJPE adaptation already reported; no misleading extra alias is emitted.
* Jacc/Jjerk are included only as prediction-intrinsic stability scores. Their values are not evidence of lower GT trajectory error; the separate Accel statistic is GT-relative.
