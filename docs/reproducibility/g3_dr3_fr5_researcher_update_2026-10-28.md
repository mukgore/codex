# G3 follow-up: DR3 evidence and researcher decisions — 2026-10-28

This addendum records clarifications made after the previous v0.2 status notes. It does not replace earlier reports or publish participant-level data, local paths, coordinates, or input hashes.

## DR3 — frame-count boundary reconciliation

The 18 human session records contain 8,782 segment frames and 8,764 `sessionLog` entries labeled `recording`: a difference of one frame per session.

An independent payload comparison found that all 8,641 detected segment landmark payloads map uniquely to payloads in the same session's `sessionLog`. Of these, 18 are logged with phase `matching` and 8,623 with phase `recording`. Each of the 18 first-segment starts maps to a `matching`-phase entry. The remaining 108 segment starts map to `recording` entries. Null counts agree by session, but identical null payloads do not identify individual events.

The inspected production-candidate callback order supports the boundary mechanism: the callback logs the current phase before match handling; the first-match callback changes phase to `recording`; the same callback then appends its landmark to the new segment. Thus the first detected segment frame is logged as `matching` and included in the segment, accounting for the observed +18 detected-frame offset.

**Status:** DR3 is accepted for the observed denominator and detected-frame boundary discrepancy. Exact event-time reconstruction and one-to-one identity for null events remain unavailable because the records lack a shared event identifier and use different time origins for session and segment timestamps.

Evidence files retained locally include `g3_independent_verification.md` and `g3_final_review.md`.

## DR4 and DR6 — researcher scope decisions

The researcher accepts the existing conditional replay based on the inspected `hand_captcha_prod.html` / `hand_captcha_prod_new.html` candidates as sufficient for the current purpose. This is not a claim that either exact historical build is proven to have collected each session.

“Session-level build” refers to the HTML/runtime/settings used during an individual participant's session. The researcher does not require further recovery of those historical mappings in the current scope. The missing historical build manifests remain an evidence limitation; they are not reconstructed from current file hashes or score agreement.

## FR1–FR4 — current acceptance basis

The G3 review links FR1–FR4 to existing G2 aggregates and independent verification:

- FR1: recorded-data denominators, phase/segment missingness, runs, timing and exploratory associations; missing source video prevents conclusions about unrecorded gaps or MCAR/MAR/MNAR mechanism.
- FR2: 12-variable IQR candidate counts and quartiles, candidate-level rationale, and descriptive sensitivity while retaining records absent source-error evidence.
- FR3: session-level raw/estimated distribution and correlation analyses for the three stored metrics; correlations do not establish attack discrimination.
- FR4: session-level uncertainty summaries, 10,000-replicate bootstrap with fixed seed, and Wilson interval for the stored pass rate; conclusions remain limited to this 18-session cohort.

These are accepted within the documented data and cohort limits, not as population-general claims.

## FR5 — researcher clarification

The researcher clarifies that “previous and next experiments” means the human experiments across the project's stages, as described in the project specification. All human-experiment data from the preceding stages were used to establish the score and decision criteria; no within-stage human-data subset was reserved as a separate validation set. The resulting evaluation method was then applied to the next human-experiment stage without changing it.

This is a researcher attestation about the study process. The absence of a held-out subset in the preceding stages means those data do not provide independent validation of the criteria derived from them. The unchanged application to a subsequent stage is distinct evidence, but independence of the relevant participant/sample units must not be assumed without lineage evidence. No contemporaneous dated freeze record was located in the reviewed artifacts.

### 13 sensitivity-scenario artifacts

A local G3 supplement contains calculations for 13 sensitivity scenarios and reports cross-checks against an aggregate. The researcher does not recall requesting these as part of the research and explicitly excludes them from the study scope. Their existence is recorded only for artifact provenance; they are not treated as preplanned research, preregistered scenarios, or evidence satisfying FR5. The scenario-definition source and timing are not independently established in this addendum.

## A/B, LR3, and phase boundary

The researcher accepts the existing A/B analysis as complete for the current scope. This does not resolve the provenance of the earlier reported (p \approx 0.012) versus the later exact sign-flip result; no equivalence between those analyses is asserted.

The researcher has declared G3 closed after reviewing the current interpretation. This records the researcher's decision; it does not remove the evidence limits above. FR6/G4 work is excluded from this session and remains deferred to a separate effort.
