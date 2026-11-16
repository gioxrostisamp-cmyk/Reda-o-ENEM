// For each slide (final state): screenshot background without text, then measure
// WCAG contrast of each text element against the brightest 10% of pixels behind it.
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const path = require('path'); const FILE = 'file://' + path.resolve(__dirname, '../dist/what-if-life-as-currency.html');
process.chdir(path.resolve(__dirname, '../.check')); require('fs').mkdirSync('shots', { recursive: true });
const slides = process.argv.slice(2).length ? process.argv.slice(2) : ['1', '3'];
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  const report = [];
  for (const n of slides) {
    await p.goto('about:blank'); await p.goto(FILE + '#' + n); await p.waitForFunction(() => window.__deck && __deck.S.ready);
    await p.waitForTimeout(1200);
    // freeze camera so both shots line up
    await p.evaluate(() => { __deck.C.rest = null; });
    const items = await p.evaluate(() => {
      const out = [];
      const sel = '.slide.live .txt [data-b].on:not(.swap), .slide.live .swap .from.on, .slide.live .swap .to.on, #ui .lbl';
      document.querySelectorAll(sel).forEach(el => {
        const cs = getComputedStyle(el);
        const name = (el.getAttribute('aria-label') || el.textContent).trim().slice(0, 34);
        // glyph-level boxes
        const parts = el.querySelectorAll('.ci, .wd, .tc, .fc, .from, .to .ci');
        const rects = (parts.length ? Array.from(parts) : [el]).map(x => x.getBoundingClientRect()).filter(r => r.width > 2 && r.height > 2)
          .map(r => [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]);
        if (!rects.length) return;
        const colorEls = Array.from(el.querySelectorAll('.ci, .wd, .tc, .fc i, .from, .to')).concat([el]);
        out.push({ name, rects, color: getComputedStyle(colorEls[0]).color, size: cs.fontSize, op: +cs.opacity });
      });
      return out;
    });
    await p.screenshot({ path: `shots/c-${n}-full.png` });
    await p.addStyleTag({ content: '.txt,#ui{visibility:hidden!important}' });
    await p.waitForTimeout(150);
    await p.screenshot({ path: `shots/c-${n}-bg.png` });
    report.push({ n, items });
  }
  await b.close();
  require('fs').writeFileSync('contrast.json', JSON.stringify(report));
  console.log(execFileSync('python3', ['-I', path.resolve(__dirname, 'contrast.py')], { encoding: 'utf8' }));
})();
