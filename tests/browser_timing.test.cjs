'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {BrowserTimeline, observeFirstFrame} = require('../g4_lab/browser_timing.js');
const metadata = () => ({presentationTime: 70, expectedDisplayTime: 80, mediaTime: 0, width: 512, height: 420, presentedFrames: 1});
const timeline = () => new BrowserTimeline({clock: () => 100, documentId: 'fixture'});

test('one-document timeline forbids cross-origin events and clock regressions', () => {
  let now = 2;
  const t = new BrowserTimeline({clock: () => now, documentId: 'one'});
  const start = t.mark('issue'); now = 5; const end = t.mark('response');
  assert.equal(t.elapsed(start, end), 3);
  const other = new BrowserTimeline({clock: () => now, documentId: 'two'});
  assert.throws(() => t.elapsed(start, other.mark('response')));
  assert.throws(() => t.elapsed({...start}, end));
  assert.throws(() => t.elapsed(end, start));
  now = 1; assert.throws(() => t.mark('bad_clock'));
  assert.throws(() => new BrowserTimeline({documentId: 12}));
  assert.throws(() => t.mark(12));
  const copy = t.snapshot(); copy[0].at_ms = 999; assert.equal(start.at_ms, 2);
});

test('late callback remains observation, not a display proof; missing duration stays null', async () => {
  const video = {requestVideoFrameCallback(callback) { callback(90, metadata()); return 1; }};
  const result = await observeFirstFrame(video, {timeline: timeline()});
  assert.equal(result.outcome, 'OBSERVED'); assert.equal(result.clock_role, 'injected_fixture');
  assert.equal(result.metadata.expectedDisplayTime, 80); assert.equal(result.callback_ms, 90);
  assert.equal(result.metadata.processingDuration, null); assert.equal(result.physical_display_proven, false);
  assert.ok(Object.isFrozen(result)); assert.ok(Object.isFrozen(result.metadata));
});

test('unsupported API yields unavailable without a loadeddata/timer substitute', async () => {
  const result = await observeFirstFrame({}, {timeline: timeline()});
  assert.equal(result.outcome, 'UNAVAILABLE'); assert.equal(result.metadata, null); assert.equal(result.callback_ms, null);
});

test('timeout cancels once and late callbacks cannot rewrite missing observation', async () => {
  let callback, cancellations = 0;
  const video = {requestVideoFrameCallback(cb) { callback = cb; return 7; },
    cancelVideoFrameCallback(id) { assert.equal(id, 7); cancellations++; }};
  const result = await observeFirstFrame(video, {timeline: timeline(), timeoutMs: 1});
  callback(90, metadata());
  assert.equal(result.outcome, 'TIMEOUT'); assert.equal(result.metadata, null); assert.equal(cancellations, 1);
});

test('abort before and after registration is distinct from timeout', async () => {
  const early = new AbortController(); early.abort(); let registered = 0;
  const video = {requestVideoFrameCallback() { registered++; return 1; }, cancelVideoFrameCallback() {}};
  assert.equal((await observeFirstFrame(video, {timeline: timeline(), signal: early.signal})).outcome, 'ABORTED');
  assert.equal(registered, 0);
  const later = new AbortController(); const promise = observeFirstFrame(video, {timeline: timeline(), signal: later.signal});
  later.abort(); assert.equal((await promise).outcome, 'ABORTED'); assert.equal(registered, 1);
});

test('invalid metadata and registration errors never become observations', async () => {
  for (const change of [{presentationTime: NaN}, {presentedFrames: 0}, {width: 1.5}, {processingDuration: -1}]) {
    const video = {requestVideoFrameCallback(cb) { cb(90, {...metadata(), ...change}); return 1; }};
    const result = await observeFirstFrame(video, {timeline: timeline()});
    assert.equal(result.outcome, 'ERROR'); assert.equal(result.metadata, null);
  }
  const result = await observeFirstFrame({requestVideoFrameCallback() { throw new TypeError('private'); }}, {timeline: timeline()});
  assert.equal(result.outcome, 'ERROR'); assert.equal(result.error_type, 'TypeError');
  assert.ok(!JSON.stringify(result).includes('private'));
  assert.throws(() => observeFirstFrame({}, {timeoutMs: 0}));
});

function appFixture() {
  let now = 0, nonce = 0; const nodes = {};
  for (const id of ['issue','submit','consume','export','video','frames','result','frame-status']) nodes[id] = {disabled: false, value: '', textContent: ''};
  Object.assign(nodes.video, {pause() {}, removeAttribute() {}, load() {}, play() { return Promise.resolve(); }});
  let grant = true, exportedBlob = null; const calls = [];
  const context = vm.createContext({
    LocalBrowserTiming: {BrowserTimeline: class extends BrowserTimeline {constructor(options) {super({...options, clock: () => ++now});}},
      observeFirstFrame: async () => ({outcome: 'UNAVAILABLE', metadata: null, physical_display_proven: false})},
    crypto: {randomUUID: () => (++nonce).toString(16).padStart(32, '0')}, AbortController,
    document: {getElementById: id => nodes[id], createElement: () => ({click() {}})}, performance: {timeOrigin: 0},
    Blob, URL: {createObjectURL: blob => { exportedBlob = blob; return 'blob:fixture'; }, revokeObjectURL() {}},
    fetch: async (route, options) => {
      calls.push({route, options});
      let value = {};
      if (route === '/api/session') value = {session_created: true};
      if (route === '/api/challenge') value = {challenge_id: 'private_challenge', media_url: '/media/private', input_channel: 'offline_landmark_replay'};
      if (route === '/api/submit') value = {grant_id: grant ? 'private_grant' : null, score_pass: true, gate_pass: grant};
      if (route === '/api/protected_action') value = {protected_action_allowed: true};
      return {status: 200, json: async () => value};
    }, setTimeout, clearTimeout,
  });
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../g4_lab/timing_app.js'), 'utf8'), context);
  return {nodes, calls, setGrant: value => { grant = value; }, exported: async () => JSON.parse(await exportedBlob.text())};
}

test('UI clears stale grants before parse failure and before a new challenge', async () => {
  const f = appFixture(); await f.nodes.issue.onclick(); f.nodes.frames.value = '[]';
  await f.nodes.submit.onclick(); assert.equal(f.nodes.consume.disabled, false);
  f.nodes.frames.value = 'invalid JSON'; await f.nodes.submit.onclick();
  assert.equal(f.nodes.consume.disabled, true);
  f.nodes.frames.value = '[]'; await f.nodes.submit.onclick(); await f.nodes.issue.onclick();
  assert.equal(f.nodes.consume.disabled, true);
  assert.ok(f.calls.every(call => /^[a-f0-9]{32}$/.test(call.options.headers['X-Lab-Correlation'])));
});

test('UI records response rejection and does not persist grant IDs in displayed outcomes', async () => {
  const f = appFixture(); await f.nodes.issue.onclick(); f.nodes.frames.value = '[]';
  await f.nodes.submit.onclick(); assert.ok(!f.nodes.result.textContent.includes('private_grant'));
  f.setGrant(false); await f.nodes.submit.onclick(); assert.equal(f.nodes.consume.disabled, true);
  assert.equal(f.nodes['frame-status'].textContent, '영상 callback: UNAVAILABLE');
});

test('private download retains request statuses and evaluation history without credentials', async () => {
  const f = appFixture(); await f.nodes.issue.onclick(); f.nodes.frames.value = '[]';
  await f.nodes.submit.onclick(); f.setGrant(false); await f.nodes.submit.onclick();
  f.nodes.export.onclick(); const data = await f.exported();
  assert.equal(data.attempts[0].clock_role, 'injected_fixture');
  assert.equal(data.attempts[0].evaluations.length, 2); assert.equal(data.attempts[0].requests.length, 4);
  assert.equal(data.attempts[0].evaluations[0].server_grant_issued, true);
  assert.equal(data.attempts[0].evaluations[1].server_grant_issued, false);
  assert.ok(!JSON.stringify(data).includes('private_grant')); assert.ok(!JSON.stringify(data).includes('private_challenge'));
  assert.equal(data.physical_display_proven, false); assert.equal(data.actual_camera_or_trusted_capture_proven, false);
});
