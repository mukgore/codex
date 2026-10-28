# Computer-use attempt log for local CAPTCHA evaluation — 2026-10-28

This is a process record, separate from the G3 evidence report. It records why Computer-use was considered, what was reported or attempted, and what remains unverified. It contains no participant data, local file paths, credentials, screenshots, or attack instructions.

## Why Computer-use was considered

The researcher asked to use Computer-use on a locally opened CAPTCHA web page, from a third-party evaluator's perspective. This was an attempted way to inspect a browser-based evaluation relevant to the project's later G4/FR6 work. The v0.2 requirements call for distinguishing gate success, score threshold passage, and end-to-end authentication; they do not require Computer-use specifically.

## Attempt history reported in the session

- Chrome could not be launched on the researcher's computer because a Microsoft parental-control program restricted it. This was reported by the researcher; it does not establish a defect in Computer-use.
- Edge was proposed as an alternative. The researcher reopened the browser/app and later reported that the CAPTCHA page was displayed.
- Despite the page being open, the session did not establish a verified Computer-use interaction with the target browser window or produce a recorded CAPTCHA evaluation result.
- Edge-related web cases, restart/reopen, and update or setup options were discussed or tried. The retained conversation does not contain a complete tool trace, exact failing API call, app/window inventory, or verbatim error message, so the technical failure point cannot be reconstructed reliably.
- Alternatives that would not depend on Computer-use were considered. No resulting run was documented as a completed G4 evaluation.

## Outcome and limits

**Outcome:** no verified Computer-use CAPTCHA interaction or G4 measurement was obtained in this attempt. The cause is unresolved; the evidence does not support concluding that Computer-use is unusable in all sessions or that the local CAPTCHA itself failed.

No gate result, score-threshold result, or end-to-end authentication result was established. Opening the CAPTCHA in a visible browser is not itself an evaluation result.

The researcher subsequently deferred FR6/G4 to a separate effort and excluded it from the current G3 closure. This log does not authorize or report a new attack run, CAPTCHA change, data collection, service deployment, or authentication bypass.

## Evidence to retain if a separate authorized attempt is made

To diagnose the integration issue, retain the exact first failing Computer-use tool response, the app/window enumeration returned by the tool, the selected window title, and whether a screenshot/state read succeeded. Record the browser and Computer-use component versions if available. Do not infer a root cause from the Chrome parental-control block alone.

If a future authorized evaluation is performed, record gate, score, and end-to-end outcomes separately under its approved protocol. This historical attempt supplies none of those outcomes.
