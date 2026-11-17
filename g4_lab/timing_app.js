'use strict';
(() => {
  const {BrowserTimeline, observeFirstFrame} = LocalBrowserTiming;
  const get = id => document.getElementById(id), video = get('video');
  const documentId = crypto.randomUUID().replaceAll('-', ''), attempts = [];
  let current = null, challenge = null, grant = null, abort = null, busy = false;
  const show = value => { get('result').textContent = JSON.stringify(value, null, 2); };
  const update = () => {
    get('issue').disabled = busy || attempts.length >= 20;
    get('submit').disabled = busy || !challenge;
    get('consume').disabled = busy || !grant;
    get('export').disabled = busy || !attempts.length;
  };
  async function post(path, payload, phase, attempt) {
    const correlation = crypto.randomUUID().replaceAll('-', '');
    attempt.timeline.mark(phase + '_request', correlation);
    const response = await fetch(path, {method: 'POST', credentials: 'same-origin',
      headers: {'Content-Type': 'application/json', 'X-Lab-Correlation': correlation}, body: JSON.stringify(payload)});
    const value = await response.json();
    const end = attempt.timeline.mark(phase + '_json_response', correlation);
    attempt.requests.push({phase, correlation, http_status: response.status});
    return {value, status: response.status, end};
  }
  async function guarded(operation) {
    if (busy) return;
    busy = true; update();
    try { await operation(); }
    catch (error) {
      if (current) current.errors.push({error_type: String(error.name || 'Error').slice(0, 64)});
      show({status: 'ERROR', error_type: String(error.name || 'Error').slice(0, 64)});
    } finally { busy = false; update(); }
  }
  get('issue').onclick = () => guarded(async () => {
    abort?.abort(); abort = new AbortController(); challenge = null; grant = null;
    video.pause(); video.removeAttribute('src'); video.load();
    const attempt = {attempt_index: attempts.length, timeline: new BrowserTimeline({documentId}), requests: [], errors: [],
      frame: {outcome: 'PENDING', metadata: null}, evaluation: null, evaluations: [], actions: [], playback_error_type: null,
      issue_to_first_action_json_response_ms: null, physical_display_proven: false};
    current = attempt; attempts.push(attempt); get('frame-status').textContent = '영상 callback: 미관측';
    if ((await post('/api/session', {}, 'session', attempt)).status !== 200) throw new Error('SessionUnavailable');
    attempt.issue_start = attempt.timeline.mark('issue_start');
    const issued = await post('/api/challenge', {}, 'challenge', attempt);
    if (issued.status !== 200) throw new Error('ChallengeUnavailable');
    challenge = issued.value;
    // Register before assigning the new source. Never reuse a previous video's callback.
    observeFirstFrame(video, {timeline: attempt.timeline, signal: abort.signal}).then(frame => {
      attempt.frame = frame;
      if (current === attempt) get('frame-status').textContent = '영상 callback: ' + frame.outcome;
    });
    video.src = challenge.media_url; video.load();
    video.play().catch(error => { attempt.playback_error_type = String(error.name || 'Error').slice(0, 64); });
    show({status: 'CHALLENGE_RECEIVED', input_channel: challenge.input_channel});
  });
  get('submit').onclick = () => guarded(async () => {
    const attempt = current;
    // Clear old permissions before any new request or parse result can fail.
    grant = null;
    const frames = JSON.parse(get('frames').value);
    const reply = await post('/api/submit', {challenge_id: challenge.challenge_id, frames}, 'submit', attempt);
    const {grant_id, ...evaluation} = reply.value;
    grant = reply.status === 200 ? (grant_id || null) : null;
    attempt.evaluation = {http_status: reply.status, server_grant_issued: Boolean(grant), ...evaluation};
    attempt.evaluations.push({...attempt.evaluation});
    show(attempt.evaluation);
  });
  get('consume').onclick = () => guarded(async () => {
    const attempt = current, reply = await post('/api/protected_action', {grant_id: grant}, 'action', attempt);
    const action = {http_status: reply.status, ...reply.value};
    if (!attempt.actions.length) {
      attempt.issue_to_first_action_json_response_ms = attempt.timeline.elapsed(attempt.issue_start, reply.end);
    }
    attempt.actions.push(action); show(action);
  });
  get('export').onclick = () => {
    const data = {schema_version: 1, clock_domain: 'browser_performance', document_id: documentId,
      performance_time_origin_ms: performance.timeOrigin, actual_camera_or_trusted_capture_proven: false,
      physical_display_proven: false, historical_authentication_proven: false,
      attempts: attempts.map(attempt => ({attempt_index: attempt.attempt_index, clock_role: attempt.timeline.clockRole,
        events: attempt.timeline.snapshot(),
        requests: attempt.requests.map(request => ({...request})), frame: attempt.frame,
        evaluation: attempt.evaluation, evaluations: attempt.evaluations, actions: attempt.actions, errors: attempt.errors,
        playback_error_type: attempt.playback_error_type,
        issue_to_first_action_json_response_ms: attempt.issue_to_first_action_json_response_ms}))};
    const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'}));
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'browser_timing.private.json';
    anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 0);
  };
  update();
})();
