# Reproducibility artifact map

This addition follows the project specification's separation of executable analysis, documentation, derived reports, and private inputs:

- `analysis/reproducibility/`: independent replay and paired-statistics scripts.
- `docs/reproducibility/`: methodology, scope, provenance caveats, and independent verification.
- `reports/reproducibility/`: aggregate-only tables, plot, and replay validation summary.
- `data/raw/` and `data/derived/`: remain local and Git-ignored. No participant JSON, landmark coordinates, per-session error rows, participant-level table, or input hash inventory is committed.

## Local input layout

The [preregistered additional 0.493 audit plan](initial_score_0493_additional_audit_plan_2026-11-04.md) was pushed before its [execution and results](initial_score_0493_additional_audit_results_2026-11-04.md). See the [aggregate summary](../../reports/reproducibility/initial_score_0493_additional_audit_summary.json) and [public process log](../../reports/reproducibility/initial_score_0493_additional_audit_process.json). Its bounded verdict permits excluding the historical 0.493 from validated results and provisionally treating documentation confusion as a working explanation; a specific mistaken source is not proven.

Initial human-score reconciliation (2026-11-04) is documented in the [results report](initial_score_reconciliation_results_2026-11-04.md), with [aggregate JSON](../../reports/reproducibility/initial_score_reconciliation_summary.json) and [recalculation code](../../analysis/reproducibility/reconcile_initial_scores.py). It replays the distinct historical four-session cohort. Table 7's three composite metrics and the rounded Table 10 score are computationally compatible; the body scores' historical generation remains unresolved. Private inputs and trial outputs stay under ignored `data/`.

Place only authorized local copies in the ignored `data/raw/` tree, or pass equivalent paths as arguments/environment variables:

```text
data/raw/ab/captcha_ab_user_*.json
data/raw/prod_v2_pool/hand_captcha_*_user_*.json
data/raw/references/landmarks_base.json
data/raw/references/pool_manifest.json
data/raw/references/pool_landmarks/<manifest-referenced files>
data/raw/references/hand_captcha_ab.html
data/raw/references/hand_captcha_ab_base.html
data/raw/references/hand_captcha_prod.html
```

The input files are not included in this repository. The defaults are intentionally generic and do not encode a user's local Windows profile. For other locations, use `--ab-dir`, `--prod-dir`, `--ab-base`, `--pool-manifest`, `--pool-dir`, `--ab-html`, `--ab-html-base`, and `--prod-html` on `reproduce_scores.py`; use `--ab-dir`, `--ab-base`, and `--out` on `analyze_ab.py`.

```powershell
python analysis\reproducibility\reproduce_scores.py --out data\derived\reproducibility
python analysis\reproducibility\analyze_ab.py --out data\derived\reproducibility
```

The replay is conditional on the supplied candidate implementation and reference files. It does not prove which build collected historical sessions. The A/B summary is a paired analysis of the ten archived participants, not a new experiment and not a security-performance claim.
