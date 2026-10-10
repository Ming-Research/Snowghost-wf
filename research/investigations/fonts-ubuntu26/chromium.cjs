// Independent browser oracle: the isolated offending file and its control.
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const { chromium } = require('../../../build/browser/node_modules/playwright');
(async () => {
  const offenders = JSON.parse(fs.readFileSync('results/offenders.json'));
  const server = http.createServer((req, res) => {
    const [, version, index] = req.url.split('/');
    const face = offenders[Number(index)];
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.end(fs.readFileSync(path.join(`build/fontsets/${version}/root`, face.path)));
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const browser = await chromium.launch({headless:true});
  console.log('CHROMIUM version=' + browser.version());
  const page = await browser.newPage();
  page.on('console', message => console.log('BROWSER_CONSOLE ' + message.text()));
  const cdp = await page.context().newCDPSession(page);
  await cdp.send('DOM.enable');
  await cdp.send('CSS.enable');
  for (let i = 0; i < offenders.length; i++) {
    const face = offenders[i];
    for (const version of ['24.04', '26.04']) {
      await page.setContent(`<style>@font-face {font-family: probe; src: url(http://127.0.0.1:${server.address().port}/${version}/${i})} #probe {font-family: probe; font-size:48px}</style><span id="probe"></span>`);
      await page.locator('#probe').evaluate((node, sample) => { node.textContent = sample; }, face.sample || '😀');
      const loaded = await page.evaluate(async () => { await document.fonts.ready; return [...document.fonts].map(f => f.status); });
      const doc = await cdp.send('DOM.getDocument');
      const node = await cdp.send('DOM.querySelector', {nodeId: doc.root.nodeId, selector:'#probe'});
      const fonts = await cdp.send('CSS.getPlatformFontsForNode', {nodeId:node.nodeId});
      const custom = fonts.fonts.filter(f => f.isCustomFont && f.glyphCount > 0);
      console.log(`CHROMIUM ${version} face=${face.index} file=${path.basename(face.path)} status=${loaded} customGlyphs=${custom.reduce((n, f) => n + f.glyphCount, 0)} fonts=${JSON.stringify(fonts.fonts)}`);
      if (version === '24.04' && (!custom.length || loaded.some(s => s !== 'loaded'))) throw new Error('Control font did not render');
      if (version === '26.04' && (custom.length || loaded.some(s => s !== 'error'))) throw new Error('Browser did not confirm malformed-font rejection');
      await page.screenshot({path:`results/chromium-${version}-${face.index}.png`});
    }
  }
  await browser.close();
  server.close();
})().catch(e => { console.error(e); process.exit(1); });
