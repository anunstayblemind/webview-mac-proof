const R = { raf: 0, cssIter: 0, audio: {}, js2py: null, errors: [], gaps: [] };
window.onerror = (m) => R.errors.push(String(m));
document.getElementById('box').addEventListener('animationiteration', () => R.cssIter++);
const cv = document.getElementById('c'), g = cv.getContext('2d');
let last = null;
function frame(t) {
  R.raf++; if (last !== null) R.gaps.push(t - last); last = t;
  g.fillStyle = `hsl(${(t / 5) % 360},100%,50%)`; g.fillRect(0, 0, 200, 100); requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
function add(a, b) { return a + b; }                      // Python -> page, with a return value
function beep() {                                         // called from Python, no click
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    R.audio.stateAtCreate = ctx.state;
    const o = ctx.createOscillator(), v = ctx.createGain();
    v.gain.value = 0.0001; o.frequency.value = 880; o.connect(v); v.connect(ctx.destination);
    o.start(); o.stop(ctx.currentTime + 0.15);
    ctx.resume().then(() => R.audio.resumeResolved = true, e => R.audio.resumeError = String(e));
    setTimeout(() => { R.audio.stateAfter700ms = ctx.state; R.audio.currentTimeAfter700ms = ctx.currentTime; }, 700);
  } catch (e) { R.audio.error = String(e); }
  return 'beep-called';
}
function width(font) { const s = document.createElement('span'); s.style.font = font; s.style.whiteSpace = 'nowrap'; s.style.position = 'absolute'; s.textContent = 'PROOF 0123456789';
  document.body.appendChild(s); const w = s.getBoundingClientRect().width; s.remove(); return w; }
function nav() { const n = performance.getEntriesByType('navigation')[0]; if (!n) return null; const o = {};
  for (const k of ['fetchStart','domainLookupStart','domainLookupEnd','connectStart','connectEnd','requestStart','responseStart',
    'responseEnd','domInteractive','domContentLoadedEventEnd','domComplete','loadEventEnd']) o[k] = Math.round(n[k]); return o; }
async function collect() {
  const good = await document.fonts.load('20px ProofFont').catch(e => 'ERR ' + e);
  const bad = await document.fonts.load('20px MissingFont').catch(e => 'ERR ' + e);
  const gl = document.createElement('canvas').getContext('webgl2') || document.createElement('canvas').getContext('webgl');
  const box = document.getElementById('box'), anims = document.getAnimations ? document.getAnimations() : [];
  const px = Array.from(g.getImageData(5, 5, 1, 1).data);
  const gaps = R.gaps.slice(5);
  const glass = getComputedStyle(document.getElementById('glass'));
  return JSON.stringify({
    ua: navigator.userAgent, visibility: document.visibilityState, rafFrames: R.raf, canvasPixel: px,
    frameGapAvgMs: gaps.length ? Math.round(gaps.reduce((a, b) => a + b, 0) / gaps.length * 10) / 10 : null,
    frameGapWorstMs: gaps.length ? Math.round(Math.max(...gaps) * 10) / 10 : null,
    cssAnimIterations: R.cssIter, cssAnimPlayStates: anims.map(a => a.playState), cssTransformNow: getComputedStyle(box).transform,
    backdropFilter: glass.backdropFilter || glass.webkitBackdropFilter || null,
    fontCheck: document.fonts.check('20px ProofFont'), fontFacesLoaded: Array.isArray(good) ? good.map(f => f.family + ':' + f.status) : good,
    fontWidthProof: width('20px ProofFont, serif'), fontWidthFallback: width('20px serif'),
    controlMissingFontLoaded: Array.isArray(bad) ? bad.map(f => f.family + ':' + f.status) : bad,
    controlMissingFontWidth: width('20px MissingFont, serif'),
    webgl: gl ? (gl.getParameter(gl.VERSION)) : null, audio: R.audio, js2py: R.js2py, errors: R.errors,
    timeOriginMs: Math.round(performance.timeOrigin), nav: nav(), resources: performance.getEntriesByType('resource').map(
      e => [e.name.split('/').pop(), Math.round(e.startTime), Math.round(e.responseEnd), e.initiatorType]) });
}
window.addEventListener('pywebviewready', async () => {     // page -> Python, with a return value
  try { R.js2py = await window.pywebview.api.echo('hello-from-js'); } catch (e) { R.js2py = 'ERR ' + e; }
});
