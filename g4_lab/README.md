# Actual-code local G4 lab

The actual owned HTML is read from a separate handcaptcha source copy. Only selected pure scoring/gate functions run in Node; page startup, remote scripts, camera and upload code never run. The current harness uses within-clip phase partitions and a fake-clock gate with video scheduling omitted. It is not a full production browser session.

Source revisions and results are recorded in [the report](../docs/g4_actual/g4_final_report.md). New server-side source selection, opaque media paths, evaluation, cookie sessions, expiry and one-time protected test action are implemented in `server.py`. The server binds only to 127.0.0.1 and serves an allowlisted local replay UI. It has no outbound client. Existing source repositories and research data stay unchanged.

Dependencies used: Python 3.10.3, NumPy 2.2.6, local OpenCV, Node v24.18.0. No package installation, GPU or paid API was required. Use the existing Python environment or a matching local environment. Commands run from the worktree root. Pick new output paths/run IDs; prior runs are retained.

```powershell
python -m g4_lab.run --source-root ../g4-handcaptcha-source --run-id G4-NEW --run-dir data/work/g4_new --summary reports/g4_new/summary.json
python -m g4_lab.independent_check --source-root ../g4-handcaptcha-source --run-dir data/work/g4_new
python -m g4_lab.checks --output reports/g4_new/checks.json --log data/work/g4_new/checks.log
python -m g4_lab.media_lookup --source-root ../g4-handcaptcha-source --output reports/g4_new/cache.json --run-id G4-CACHE-NEW
python -m g4_lab.blind_baseline --source-root ../g4-handcaptcha-source --run-dir data/work/g4_blind_new --summary reports/g4_new/blind.json
python -m g4_lab.pixel_ablation --source-root ../g4-handcaptcha-source --run-dir data/work/g4_pixels_new --output reports/g4_new/pixel.json
python -m g4_lab.circle_lookup --source-root ../g4-handcaptcha-source --run-dir data/work/g4_pixels_new --pixel-features data/work/g4_pixels_new/pixel_features.json --output reports/g4_new/circle.json
python -m g4_lab.mask_experiment --source-root ../g4-handcaptcha-source --run-dir data/work/g4_mask_new --output reports/g4_new/mask.json
python -m g4_lab.legacy_pool --source-root ../g4-handcaptcha-source --run-dir data/work/g4_legacy_new --summary reports/g4_new/legacy.json
python -m g4_lab.independent_legacy_check --source-root ../g4-handcaptcha-source --run-dir data/work/g4_legacy_new --summary reports/g4_new/legacy.json --output data/work/g4_legacy_new/independent_validation.json
python -m g4_lab.server --source-root ../g4-handcaptcha-source
```

The last command prints an ephemeral localhost URL for the new replay UI; terminate it when finished. It does not use a camera. An approved replay array is submitted to the actual evaluator; `passed`/`score` claims are rejected. Successfully consumed grants increment an in-memory test counter. This is not a historical service, database transaction, trusted input SDK or deployment-ready server.

Additional scripts: `pixel_ablation.py` decodes the 8 actual MP4s; `circle_lookup.py` compares their bounded circle candidates with the exposed known-source library; `blind_baseline.py` generates independent uniform coordinates; `mask_experiment.py` invokes the actual Stage6 loop using real decoded pixels with I/O spies and compares strict masking. See script arguments/default paths before reproducing; they refuse overwriting existing experiment outputs.

Detailed inputs, source IDs, input/code fingerprints, verifier output and logs are under ignored data/work. Public reports contain aggregates without human data or local absolute paths. There is no unused source holdout, participant evaluation, browser/camera experiment or real service bypass. Known published-media/reference replay still passes the new server; the stationary filter has a noise counterexample and remains disabled by default. Publication of this code, documentation and deidentified aggregates was authorized after the experiment; private artifacts remain excluded.
