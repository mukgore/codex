// Export masked RGB and separately stored projected annotations for pose research.
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.PLAYWRIGHT_CORE || '../../qa/node_modules/playwright-core');

async function main() {
  const [renderer, output] = process.argv.slice(2);
  if (!renderer || !output) throw new Error('Usage: node render_pose_benchmark.cjs <motion.js> <new-output-dir>');
  const source = fs.readFileSync(renderer, 'utf8');
  fs.mkdirSync(output);
  const browser = await chromium.launch({ headless: true,
    executablePath: process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
  const labels = [];
  try {
    const page = await browser.newPage();
    const fixture = 'http://127.0.0.1:18910/fixture';
    await page.route(fixture, route => route.fulfill({ contentType: 'text/html', body: '<title>Offline pose fixture</title>' }));
    await page.goto(fixture);
    await page.addScriptTag({ content: source });
    for (let seed = 1; seed <= 24; seed++) {
      const batch = await page.evaluate(seed => {
        let state = Math.imul(seed, 2654435761) >>> 0;
        const random = () => (state = (Math.imul(state, 1664525) + 1013904223) >>> 0) / 2 ** 32;
        const names = Array.from({ length: 21 }, (_, index) => String(index));
        const source = document.createElement('canvas');
        const input = document.createElement('canvas');
        input.width = 80;
        input.height = 66;
        const pixels = input.getContext('2d', { willReadFrequently: true });
        const { x: mx, y: my, r } = LiveMotion.mask;
        return LiveMotion.createChallenge(names, random).flatMap((clip, slot) => {
          const mirror = (seed + slot) % 2 === 0;
          const sourceId = `synthetic-${seed}-${slot}`;
          return ['2d', '3d'].map(mode => {
            const frames = [], imageBytes = [];
            for (let i = 0; i < clip.frames.length; i += 4) {
              LiveMotion.paint(source, clip, i / clip.landmarks.video_info.fps, mirror, mode);
              pixels.drawImage(source, 0, 0, input.width, input.height);
              const { data } = pixels.getImageData(0, 0, input.width, input.height);
              for (let j = 0; j < data.length; j += 4) imageBytes.push(data[j], data[j + 1], data[j + 2]);
              frames.push({
                xy: clip.frames[i].map(({ x, y }) => [(mirror ? source.width - x : x) / source.width, y / source.height]),
                hidden: clip.frames[i].map(({ x, y }) => (x - mx) ** 2 + (y - my) ** 2 <= r ** 2),
              });
            }
            return { name: sourceId + '-' + mode, source: sourceId, family: clip.motion, mode, frames, imageBytes };
          });
        });
      }, seed);
      for (const { imageBytes, ...clip } of batch) {
        fs.writeFileSync(path.join(output, clip.name + '.rgb'), Buffer.from(imageBytes));
        labels.push(clip);
      }
    }
    fs.writeFileSync(path.join(output, 'annotations.json'), JSON.stringify({ width: 80, height: 66, clips: labels }));
    console.log(JSON.stringify({ clips: labels.length, unique_sources: new Set(labels.map(clip => clip.source)).size,
      families: [...new Set(labels.map(clip => clip.family))].sort() }));
  } finally {
    await browser.close();
  }
}

main().catch(error => { console.error(error.message); process.exitCode = 1; });
