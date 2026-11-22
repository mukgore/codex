# Real-time occluded-hand A/B models

This run follows `C:\Users\조영준!\Documents\CLI\realtime_occluded_hand_model_requirements.md`.
The existing grouped-v15 offline model and its weights remain unchanged.

## Model inputs

- **A_current:** current RGB frame only, 3 input channels.
- **B_past_current:** previous and current RGB frames, 6 input channels. The first
  frame of each session is duplicated as its own previous frame.
- Both output 21 normalized image-plane `(x, y)` coordinates in the existing
  `JOINTS` order. Checkpoint metadata records its trained input width and height;
  the streaming API resizes each incoming `uint8` RGB frame to that size.
- `StreamingEstimator.reset()` clears the temporal state. `infer()` returns
  `invalid_input` or `prediction_failure` without coordinates on failure.
  Training clips all contain a hand, so a finite pose does **not** verify hand
  presence. A no-hand detector is not part of A/B and is a deployment limitation.

## Training and held-out data

The trainer reuses the existing grouped-v15 synthetic split and recorded split,
readers, CNN stages, augmentation, loss, optimizer, batch size, seed, and
validation-NME epoch selection. A and B use the same clips and training budget.
The split audit rejects source groups that cross partitions and stores split
clip IDs/source groups in the report. Synthetic clips are grouped by generator
seed. The eight recorded clips are split according to the existing
`RECORDED_SPLIT`; their coordinates come from the legacy tracker and are not
independent anatomical ground truth.

```powershell
$repo = 'C:\Users\조영준!\Documents\CLI\usability\codex'
$python = 'C:\Users\조영준!\Documents\CLI\deliverables-review\private_artifacts\mano_cpu_runtime_20261105\venv\Scripts\python.exe'
$synthetic = 'C:\Users\조영준!\Documents\CLI\usability\qa\occluded-pose-pilot-v14'
$recorded = 'C:\Users\조영준!\Documents\CLI\usability\handcaptcha-live-motion'
$models = 'C:\Users\조영준!\Documents\CLI\usability\qa\realtime-hand-models-v1'
& $python "$repo\analysis\train_realtime_occluded_hand_models.py" `
  --synthetic $synthetic --recorded $recorded --output-dir $models --epochs 16
```

The run produces A and B checkpoints plus `report.json` for each existing
2D, 3D-projection, and recorded domain. Outputs stay outside Git.

## External-video evaluation

The external set and original circular occluder are described in
`hand_pose_metric_audit.md` and `external_hand_verification.py`. Run the
`local`, `realtime`, `hamer`, and `mediapipe` backends into one fresh results
directory, then run `--backend aggregate`. The realtime backend resets A/B at
each video and at each unoccluded/occluded condition, processes frames in order,
and records per-frame latency including resize. A/B receive RGB pixels only;
their output is mapped to the same normalized 2D image coordinates used by the
other estimators.

## Validation status

The streaming API has contract checks for input dimensions, session-start
behavior, reset behavior, malformed input, output shape, and future-frame
invariance; all five direct contract checks pass. Training completed for all
three domains and both A/B conditions. The six checkpoints and complete
per-clip report are in the external `qa/realtime-hand-models-v1/` directory.
The held-out 2D synthetic results are A NME 0.005598 and B 0.004955 over 240
clips / 9,066 frames each. The 3D-projection results are A 0.004592 and B
0.004946; the recorded two-video test set is too small and uses legacy tracker
labels. These synthetic/recorded held-out values do not establish external
accuracy.

The independent GigaHands run includes A/B, grouped-v15 C, HaMeR, and MediaPipe
on the same five clips under raw and circular-mask conditions. The committed
artifact bundle is `reports/independent_hand_verification/`: `summary.md` has
per-video metrics, confidence intervals, versions, run times, and resource
probes; `external_hand_verification.json` and the four backend prediction JSON
files preserve row-level model outputs; `training_report.json` and `checkpoints/`
preserve A/B training results and weights. `provenance_github.json` stores run
commands plus SHA-256 hashes for source code, labels, videos, weights,
checkpoints, and outputs. The masked preview videos are in
`reports/independent_hand_verification/occlusion_previews/`.

The GigaHands source archive, extracted source videos, and labels remain outside
Git. The committed masked previews and derived annotations are shared under the
GigaHands CC BY-NC 4.0 terms with attribution to Fu et al., “GigaHands,” CVPR
2025; see the artifact bundle README for the source and citation.

The A/B Python CPU run measured per-frame latency and process peak working set.
The resource probe loads all four A/B checkpoints together, so it is a
backend-process peak, not an isolated per-model RAM value. The installed
project has neither `onnx`/`onnxruntime` in its Python runtime nor
`onnxruntime-web`/TensorFlow.js in its local JavaScript packages. The current
browser page uses pinned MediaPipe Hands from a CDN. A/B `.pt` checkpoints were
not run directly in a browser; browser deployment remains unverified. The model
itself also does not distinguish a missing hand from a valid pose estimate, so
a separate hand-presence policy is still required for deployment.
