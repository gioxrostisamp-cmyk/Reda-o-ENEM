const { chromium } = require('playwright');
const path = require('path'); const FILE = 'file://' + path.resolve(__dirname, '../dist/what-if-life-as-currency.html') + '#print';
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await p.goto(FILE); await p.waitForFunction(() => window.__deck && __deck.S.ready && document.body.classList.contains('print'));
  await p.waitForTimeout(800);
  await p.pdf({ path: process.argv[2] || path.resolve(__dirname, '../dist/what-if-life-as-currency.pdf'), width: '1920px', height: '1080px', printBackground: true, pageRanges: '' });
  await b.close();
})();
