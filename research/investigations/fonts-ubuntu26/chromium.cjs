// Temporary independent browser oracle for every changed package font.
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const { chromium } = require('../../../build/browser/node_modules/playwright');
(async () => {
  const changed = JSON.parse(fs.readFileSync('results/changed.json'));
  const server = http.createServer((req, res) => {
    const font = changed[Number(req.url.slice(1))];
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.end(fs.readFileSync(path.join('build/fontsets/26.04/root', font.path)));
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const browser = await chromium.launch({headless:true});
  console.log('CHROMIUM version=' + browser.version());
  const page = await browser.newPage();
  const cdp = await page.context().newCDPSession(page);
  await cdp.send('DOM.enable');
  await cdp.send('CSS.enable');
  for (let i = 0; i < changed.length; i++) {
    const face = changed[i];
    await page.setContent(`<style>@font-face {font-family: probe; src: url(http://127.0.0.1:${server.address().port}/${i})} #probe {font-family: probe; font-size:48px}</style><span id="probe">ABC abc 123 ☺ ★ 😀 ก 日</span>`);
    if (face.sample) await page.locator('#probe').evaluate((node, sample) => { node.textContent += sample; }, face.sample);
    const loaded = await page.evaluate(async () => { await document.fonts.ready; return [...document.fonts].map(f => f.status); });
    const doc = await cdp.send('DOM.getDocument');
    const node = await cdp.send('DOM.querySelector', {nodeId: doc.root.nodeId, selector:'#probe'});
    const fonts = await cdp.send('CSS.getPlatformFontsForNode', {nodeId:node.nodeId});
    const custom = fonts.fonts.filter(f => f.isCustomFont && f.glyphCount > 0);
    console.log(`CHROMIUM face=${face.index} file=${path.basename(face.path)} status=${loaded} fonts=${JSON.stringify(fonts.fonts)}`);
    if (!custom.length || loaded.some(s => s !== 'loaded')) throw new Error('No glyphs rendered from package font');
    await page.screenshot({path:`results/chromium-${face.index}.png`});
  }
  await browser.close();
  server.close();
})().catch(e => { console.error(e); process.exit(1); });
