# CAPTCHA Reproducibility and Data-Lineage Audit

**Scope:** Read-only review of previously collected CAPTCHA research artifacts. No new CAPTCHA experiment or attack was run. This public report omits personal filesystem paths, participant identifiers, and session-level records.

## Findings

| Requirement | Status | Result |
|---|---|---|
| DR3: one-frame discrepancy | Partial | The aggregate difference is 8,782 segment frames versus 8,764 `recording` log frames: 18 frames, one per session. Callback order explains the count. Exact event-level alignment is unavailable without shared frame IDs or global segment offsets. |
| DR4: independent raw-metric replay | Conditional reproduction | Two separate in-memory implementations reproduced all 18 records' stored raw, estimated, and final scores from user landmarks and the available reference landmarks, to floating-point precision. This does not establish which build or reference-pool version actually ran in each session. |
| DR6: code and data lineage | Partial | The two inspected production HTML variants share the scoring formulas and constants. Their survey and save behavior differs. The JSON schema is compatible with the shared scoring code, but session-specific build/configuration manifests are absent. |
| Historical A/B, 25-combination, and HaMeR material | Reviewed; provenance gaps remain | Structures and copy relationships were inspected. Cross-cohort pooling and new attack-success calculations were not performed. |

## DR4 replay details

The inspected production code uses XY landmarks, translates the wrist to the origin, and scales by wrist-to-middle-MCP distance. It linearly resamples sequences.

- `angle`: mean absolute angular error over 15 joint triplets after resampling to the reference length.
- `dtw_angle`: despite its name, this is a sliding-window minimum angular error after resampling the user sequence to about 1.2 times the reference length; it is not general dynamic time warping.
- `accel`: difference between mean XY second-difference magnitudes after resampling. It uses frame index, not elapsed timestamp.
- Estimated terms use detection rate and clipped per-metric factors. Constants are 46.9413, 44.0014, and 0.1926 for `angle`, `dtw_angle`, and `accel`; final weights are 0.25, 0.38, and 0.37, respectively. The threshold is 0.25.

The JSON records contain user landmarks, timestamps, keyframes, and saved scores, but do not embed reference landmarks. Available reference landmark files and a pool manifest enabled a conditional replay. Two separately written implementations agreed with stored scores for all 18 records:

| Implementation | Max absolute raw-metric error | Max estimated-term error | Max final-score error |
|---|---:|---:|---:|
| JavaScript | 7.55e-14 | 1.78e-15 | 1.22e-15 |
| Python | 4.80e-14 | 9.99e-16 | 4.44e-16 |

The production function itself was not directly invoked. Agreement verifies that the inspected formulas and available reference data can reproduce the saved values; it does not prove those exact files were used at collection time.

## DR6 source and pool lineage

The inspected files `hand_captcha_prod.html` and `hand_captcha_prod_new.html` share the scoring formulas, constants, keyframe logic, normalization, and handedness handling. Their collection flows differ:

- `hand_captcha_prod.html` includes survey UX and automatic JSON blob download.
- `hand_captcha_prod_new.html` removes survey functionality and defaults local JSON saving off; its checked upload URL is empty.

All 18 JSON records self-label as `prod_v2_pool` and have structures compatible with the shared scoring logic. This strongly supports the `prod.html` family as a source candidate, but does not identify the exact build for any session. Available copies of the current pool manifest matched each other, and all observed keyframe references resolved against the current pool. No per-session HTML hash, pool-manifest hash, or full execution configuration was found. File timestamps and matching hashes identify copies, not the code that actually executed.

## DR3 callback and timestamp analysis

The first keyframe match changes the phase to `recording`, resets the segment, and then appends that callback's frame to the segment. The log records the phase before this transition, so the frame appears in the segment but is logged as `matching`. This accounts for one extra segment frame per session. Later transition callbacks append to the current segment before resetting it; they do not also append that same frame to the next segment.

Segment timestamps are relative to each recording start, while session-log timestamps are global. There is no common frame ID or saved global segment offset, so exact event-by-event timestamp alignment cannot be reconstructed. The supported result is the count and callback-order explanation, not a complete one-to-one event audit.

## Historical materials

### A/B records

Ten A/B JSON records were found, with byte-identical copies in a second approved location. They contain experiment metadata, order and hand selection, keyframe references, two trials, landmarks, raw metrics, estimated terms, and scores. A separate baseline-landmark file is available. The A/B cohort could be replayed if its exact implementation and protocol are linked, but it is not source-linked to the 18 production records or HaMeR data. No cross-cohort combination or new outcome calculation was performed.

### 25-combination notebook

The notebook describes a six-action, 5-by-5 detection/tracking sensitivity workflow and includes several metric-like calculations. Multiple notebook copies differ; the byte-identical copies can be identified, but execution provenance is not established. The base copy has no executed outputs, and available output fragments do not establish the runtime, inputs, or corresponding result workbook. Its terminology does not establish validated definitions for the four proposed candidate metrics.

### HaMeR

One artifact contains frame-level results for six actions, with an identical duplicate. Several notebook versions exist, but no exact notebook, checkpoint, or runtime is linked to that result file.

A separate third-experiment artifact contains 28 unordered pairs from eight clips. It is distinct from the six-action result file and from the 25-combination sensitivity notebook. Historical comparison documents describe 18 human records and 28 HaMeR pairs; these cohorts were not merged, and no new attack-success rate was calculated.

### Four candidate metrics

Names resembling distance, DTW distance, position tendency/variability, and trajectory consistency appear in historical material. A validated formula, input specification, and implementation lineage for all four were not found. No guessed formula was selected or calculated.

## Verification and limitations

The JavaScript and Python reimplementations were separate, in-memory implementations of the reviewed formulas. A mutable-reference issue in an initial in-memory attempt was corrected by copying reference frames before mirroring; the final two implementations were rerun and matched. No source artifact was modified.

No numerical conflict was found between the conditional DR4 replay and saved scores. DR3 is explained by one initial-transition frame per session, not one frame per segment. Exact historical runtime, session-specific pool version, full timestamp alignment, A/B cross-cohort linkage, HaMeR execution provenance, and validated definitions for the four candidate metrics remain unverified or unrecoverable from the available records.

No analysis files were persisted locally during the audit. This report records the aggregate findings only; it does not contain participant data or identifiable local paths.
