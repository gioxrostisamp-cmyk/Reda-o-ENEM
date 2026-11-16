// Measures WCAG contrast of every visible text on each slide (final state) against the
// brightest 10% of the photo pixels behind it. Usage: node tools/check-contrast.js [slide numbers…]
const path = require('path'), fs = require('fs');
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const FILE = 'file://' + path.resolve(__dirname, '../dist/what-if-life-as-currency.html');
const OUT = path.resolve(__dirname, '../.check'); fs.mkdirSync(path.join(OUT, 'shots'), { recursive: true });
const slides = process.argv.slice(2).length ? process.argv.slice(2) : ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'];
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  const report = [];
  for (const n of slides) {
    await p.goto('about:blank'); await p.goto(FILE + '#' + n);
    await p.waitForFunction(() => window.__deck && __deck.S.ready && !__deck.S.build);
    await p.waitForTimeout(1500);
    await p.evaluate(() => { __deck.C.rest = null; document.getAnimations().forEach(a => a.pause()); });
    const items = await p.evaluate(() => {
      const groups = [];
      const eff = el => { let o = 1; for (let e = el; e && e.id !== 'stage'; e = e.parentElement) o *= +getComputedStyle(e).opacity; return o; };
      const roots = [...document.querySelectorAll('.slide.live .txt'), document.getElementById('ui')];
      for (const root of roots) {
        const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
        for (let t = w.nextNode(); t; t = w.nextNode()) {
          if (!t.textContent.trim()) continue;
          const el = t.parentElement, cs = getComputedStyle(el);
          if (cs.visibility === 'hidden') continue;
          const op = eff(el); if (op < 0.3) continue;
          const r = document.createRange(); r.selectNodeContents(t);
          const rects = [...r.getClientRects()].filter(q => q.width > 1 && q.height > 1).map(q => [q.left, q.top, q.width, q.height].map(Math.round));
          if (!rects.length) continue;
          const owner = el.closest('[data-b], .lbl, .rr, .row, .ann, .al, .blk-t') || el;
          const key = (owner.id || owner.className) + '|' + cs.color + '|' + op.toFixed(2) + '|' + groups.length;
          let g = groups.find(x => x.owner === owner && x.color === cs.color && Math.abs(x.op - op) < 0.02);
          if (!g) { g = { owner, name: (owner.getAttribute('aria-label') || owner.textContent).replace(/\s+/g, ' ').trim().slice(0, 40), color: cs.color, op, size: cs.fontSize, rects: [] }; groups.push(g); }
          g.rects.push(...rects);
        }
      }
      return groups.map(({ owner, ...g }) => g);
    });
    await p.screenshot({ path: path.join(OUT, `shots/c-${n}-full.png`) });
    await p.addStyleTag({ content: '.txt *,#ui *{color:transparent!important;-webkit-text-fill-color:transparent!important;text-shadow:none!important}.tc.cur{background:none!important}#ui .rule,#ui .cross{visibility:hidden!important}' });
    await p.waitForTimeout(150);
    await p.screenshot({ path: path.join(OUT, `shots/c-${n}-bg.png`) });
    report.push({ n, items });
  }
  await b.close();
  fs.writeFileSync(path.join(OUT, 'contrast.json'), JSON.stringify(report));
  process.stdout.write(execFileSync('python3', ['-I', path.resolve(__dirname, 'contrast.py'), OUT], { encoding: 'utf8' }));
})();
