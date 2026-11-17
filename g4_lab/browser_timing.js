(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.LocalBrowserTiming = api;
})(globalThis, function () {
  'use strict';
  const finite = value => typeof value === 'number' && Number.isFinite(value);
  const errorType = error => /^[A-Za-z0-9_]{1,64}$/.test(error?.name || '') ? error.name : 'Error';

  class BrowserTimeline {
    constructor(options = {}) {
      this.clock = options.clock || (() => performance.now());
      this.clockRole = options.clock ? 'injected_fixture' : 'browser_performance';
      this.documentId = options.documentId || crypto.randomUUID().replaceAll('-', '');
      if (typeof this.documentId !== 'string' || !/^[A-Za-z0-9_-]{1,64}$/.test(this.documentId)) throw new TypeError('Document ID required');
      this.events = []; this.last = null;
    }
    sample() {
      const now = this.clock();
      if (!finite(now) || now < 0 || (this.last !== null && now < this.last)) throw new RangeError('Clock regression');
      this.last = now; return now;
    }
    mark(name, correlation = null) {
      if (typeof name !== 'string' || !/^[A-Za-z0-9_]{1,64}$/.test(name) ||
          (correlation !== null && (typeof correlation !== 'string' || !/^[a-f0-9]{32}$/.test(correlation)))) {
        throw new TypeError('Bounded event/correlation required');
      }
      const event = Object.freeze({event_id: this.events.length, name, at_ms: this.sample(),
        document_id: this.documentId, correlation});
      this.events.push(event); return event;
    }
    elapsed(first, last) {
      if (this.events[first?.event_id] !== first || this.events[last?.event_id] !== last || last.event_id < first.event_id) {
        throw new TypeError('Ordered events from this timeline required');
      }
      return last.at_ms - first.at_ms;
    }
    snapshot() { return this.events.map(event => ({...event})); }
  }

  function frameMetadata(value) {
    // Native units: presentation/expectedDisplayTime are ms; mediaTime and
    // processingDuration are seconds. Dimensions are media pixels, not CSS px.
    const result = {};
    for (const key of ['presentationTime', 'expectedDisplayTime', 'mediaTime', 'width', 'height', 'presentedFrames']) {
      if (!finite(value?.[key])) throw new TypeError('Finite frame metadata required');
      result[key] = value[key];
    }
    if (result.presentationTime < 0 || result.expectedDisplayTime < 0 ||
        !['width', 'height', 'presentedFrames'].every(key => Number.isInteger(result[key]) && result[key] > 0)) {
      throw new TypeError('Invalid frame metadata');
    }
    // expectedDisplayTime may be earlier than callback now (a late callback).
    result.processingDuration = value.processingDuration === undefined ? null : value.processingDuration;
    if (result.processingDuration !== null && (!finite(result.processingDuration) || result.processingDuration < 0)) {
      throw new TypeError('Invalid processing duration');
    }
    return Object.freeze(result);
  }

  function observeFirstFrame(video, {timeline = new BrowserTimeline(), timeoutMs = 8000, signal} = {}) {
    if (!Number.isInteger(timeoutMs) || timeoutMs < 1 || timeoutMs > 20000) throw new RangeError('Bounded timeout required');
    return new Promise(resolve => {
      let handle = null, timer = null, settled = false;
      function finish(outcome, fields = {}) {
        if (settled) return;
        settled = true; clearTimeout(timer); signal?.removeEventListener('abort', abort);
        let cancellation = 'NOT_NEEDED';
        if (outcome !== 'OBSERVED' && handle !== null) {
          cancellation = 'UNAVAILABLE';
          if (typeof video.cancelVideoFrameCallback === 'function') {
            try { video.cancelVideoFrameCallback(handle); cancellation = 'REQUESTED'; }
            catch (_) { cancellation = 'FAILED'; }
          }
        }
        resolve(Object.freeze({outcome, clock_domain: 'browser_performance', clock_role: timeline.clockRole,
          document_id: timeline.documentId, callback_ms: null, observation_ms: null, metadata: null,
          physical_display_proven: false, cancellation, ...fields}));
      }
      function abort() { finish('ABORTED'); }
      if (signal?.aborted) { finish('ABORTED'); return; }
      if (typeof video?.requestVideoFrameCallback !== 'function') { finish('UNAVAILABLE'); return; }
      signal?.addEventListener('abort', abort, {once: true});
      timer = setTimeout(() => finish('TIMEOUT'), timeoutMs);
      try {
        handle = video.requestVideoFrameCallback((now, metadata) => {
          if (settled) return;
          try {
            if (!finite(now) || now < 0) throw new TypeError('Finite callback timestamp required');
            const data = frameMetadata(metadata), observation = timeline.sample();
            finish('OBSERVED', {callback_ms: now, observation_ms: observation, metadata: data});
          } catch (error) { finish('ERROR', {error_type: errorType(error)}); }
        });
      } catch (error) { finish('ERROR', {error_type: errorType(error)}); }
    });
  }
  return {BrowserTimeline, observeFirstFrame, frameMetadata};
});
