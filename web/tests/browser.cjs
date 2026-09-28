// Optional browser integration suite. Requires Playwright and an installed browser.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const { execFileSync } = require('node:child_process');
const { chromium } = require(process.env.PUZZLE_PLAYWRIGHT || 'playwright');
const root = path.resolve(__dirname, '../..');
const dist = path.join(root, 'web/dist');
const artifacts = path.join(root, 'web/.artifacts');
const read = (file) => fs.readFileSync(path.join(root, file), 'utf8');
const keys = ['easyasabc', 'fuzuli'];
const specs = Object.fromEntries(keys.map((key) => {
  const spec = JSON.parse(read(`impls/${key}.json`));
  spec.layers = spec.layers.map((layer) => ({ palette: {}, options: {}, ...layer }));
  spec.source = read(`impls/${key}.dsl`);
  return [key, spec];
}));

test('central workspace and solve lifecycle in the browser', { timeout: 60000 }, async (t) => {
  const pending = [];
  const server = http.createServer(async (req, res) => {
    const json = (body) => { res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify(body)); };
    if (req.url === '/api/health') return json({ solver: { available: true, backends: [{ name: 'auto', label: '自动', available: true, supportsTimeout: true }] } });
    if (req.url === '/api/puzzles') return json({ puzzles: Object.values(specs) });
    if (req.url.startsWith('/api/puzzles/')) {
      const key = req.url.split('/').pop();
      return json({ puzzle: specs[key], sample: JSON.parse(read(`impls/samples/${key}.json`)), rule: specs[key] });
    }
    if (req.url === '/api/solve') {
      let body = '';
      for await (const chunk of req) body += chunk;
      pending.push({ body: JSON.parse(body), respond: json });
      return;
    }
    if (req.url === '/api/import') {
      let body = '';
      for await (const chunk of req) body += chunk;
      try {
        return json(JSON.parse(execFileSync(process.env.PUZZLE_PYTHON || 'python', ['-c', 'import json,sys; from puzzle.importing import import_url; p=json.load(sys.stdin); print(json.dumps(import_url(p["url"],p.get("puzzle"))))'], { cwd: root, input: body, encoding: 'utf8' })));
      } catch (error) { return json({ error: String(error) }); }
    }
    const pathname = new URL(req.url, 'http://localhost').pathname;
    const file = path.join(dist, pathname === '/' ? 'index.html' : decodeURIComponent(pathname));
    if (!fs.existsSync(file)) { res.statusCode = 404; res.end(); return; }
    res.setHeader('Content-Type', file.endsWith('.js') ? 'text/javascript' : file.endsWith('.css') ? 'text/css' : 'text/html');
    res.end(fs.readFileSync(file));
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  let browser;
  try {
    browser = await chromium.launch({ headless: true, ...(process.platform === 'win32' ? { channel: 'msedge' } : {}) });
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    const errors = [];
    page.on('pageerror', (error) => errors.push(String(error)));
    await page.goto(`http://127.0.0.1:${server.address().port}`);
    await page.locator('.penpa-frame').waitFor();
    const frame = await (await page.locator('.penpa-frame').elementHandle()).contentFrame();
    await frame.waitForFunction(() => window.pu && window.StudioBridge && pu.centerlist.length > 1);
    await page.getByLabel('题型', { exact: true }).selectOption('easyasabc');
    await page.getByLabel('参数 k').waitFor();

    await t.test('sample parameters and all controls live in the central workspace', async () => {
      assert.equal(await page.getByLabel('参数 k').inputValue(), '2');
      assert.equal(await page.locator('.topbar').count(), 0);
      for (const label of ['题型', '行数', '列数', '求解后端', '导入链接']) {
        assert.equal(await page.locator('.penpa-ui').getByLabel(label, { exact: true }).count(), 1);
      }
      const board = await page.locator('.penpa-ui').boundingBox();
      const editor = await page.locator('.dsl-pane').boundingBox();
      assert.ok(board.width > 450 && editor.x >= board.x + board.width - 1);
      fs.mkdirSync(artifacts, { recursive: true });
      await page.screenshot({ path: path.join(artifacts, 'desktop.png'), fullPage: true });
    });

    await t.test('native Penpa input is submitted and repeated shortcut cannot queue solves', async () => {
      await page.getByRole('button', { name: '清空盘面', exact: true }).click();
      await frame.locator('#mo_number_lb').click();
      const point = await frame.evaluate(() => {
        const p = pu.point[(2 + pu.space[0]) * pu.nx0 + 2 + pu.space[2]];
        return { x: p.x, y: p.y };
      });
      await frame.locator('#canvas').click({ position: point });
      await page.keyboard.type('1');
      await frame.locator('#tb_undo').click();
      assert.equal(await frame.evaluate(() => Object.keys(pu.pu_q.number).length), 0);
      await frame.locator('#tb_redo').click();
      assert.equal(await frame.evaluate(() => Object.values(pu.pu_q.number)[0][0]), '1');
      const request = page.waitForRequest('**/api/solve');
      await page.getByRole('button', { name: '求解', exact: true }).click();
      await request;
      await page.waitForTimeout(100);
      await page.getByLabel('规则 DSL', { exact: true }).press('Control+Enter');
      await page.getByLabel('规则 DSL', { exact: true }).press('Control+Enter');
      assert.equal(pending.length, 1);
      assert.equal(pending[0].body.instance.clues.x['0,0'], 1);
      assert.equal(pending[0].body.instance.params.k, 2);
    });

    await t.test('editing during solve discards the stale answer', async () => {
      await frame.evaluate(() => { const key = Object.keys(pu.pu_q.number)[0]; pu.pu_q.number[key][0] = '2'; pu.redraw(); });
      pending[0].respond({ status: 'sat', values: { x: { '0,0': 2 } }, constraints: 1 });
      await page.waitForFunction(() => !document.querySelector('button.solve').disabled);
      assert.equal(await page.locator('.status-sat').count(), 0);
      assert.equal(await frame.evaluate(() => Object.keys(pu.pu_a.number).length), 0);
    });

    await t.test('native resize and hidden clues preserve edited content', async () => {
      await page.getByLabel('行数', { exact: true }).fill('4');
      assert.equal(await frame.evaluate(() => pu.ny), 4);
      const url = await frame.evaluate(() => {
        StudioBridge.setHidden(['number'], true);
        return StudioBridge.exportUrl();
      });
      const decoded = JSON.parse(execFileSync('python', ['-c', 'import json,sys; from puzzle.importing import import_url; print(json.dumps(import_url(sys.stdin.read(),"easyasabc")))'], { cwd: root, input: url, encoding: 'utf8' }));
      assert.equal(decoded.instance.clues.x['0,0'], 2);
      await frame.evaluate(() => StudioBridge.setHidden(['number'], false));
    });

    await t.test('empty edited DSL is sent unchanged and errors remain visible', async () => {
      await page.getByLabel('规则 DSL', { exact: true }).fill('');
      const request = page.waitForRequest('**/api/solve');
      await page.getByRole('button', { name: '求解', exact: true }).click();
      await request;
      await page.waitForTimeout(100);
      assert.equal(pending[1].body.source, '');
      pending[1].respond({ status: 'error', message: '规则不能为空', constraints: 0 });
      await page.locator('.board-status').getByText('规则不能为空').waitFor();
    });

    await t.test('fuzuli sample keeps k=2 and narrow layout has no page overflow', async () => {
      await page.getByLabel('题型', { exact: true }).selectOption('fuzuli');
      await page.getByLabel('规则 DSL', { exact: true }).getAttribute('class');
      await page.getByRole('button', { name: '样例', exact: true }).click();
      assert.equal(await page.getByLabel('参数 k').inputValue(), '2');
      for (const width of [800, 390]) {
        await page.setViewportSize({ width, height: 844 });
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
        const board = await page.locator('.penpa-frame').boundingBox();
        assert.ok(board.width > 150 && board.height > 150);
      }
      await page.screenshot({ path: path.join(artifacts, 'mobile.png'), fullPage: true });
      assert.deepEqual(errors, []);
    });

    await t.test('successful solve renders on the native answer layer and edits clear it', async () => {
      const request = page.waitForRequest('**/api/solve');
      await page.getByRole('button', { name: '求解', exact: true }).click();
      await request;
      await page.waitForTimeout(100);
      assert.equal(pending[2].body.instance.params.k, 2);
      pending[2].respond({ status: 'sat', values: { x: { '0,0': 2 } }, constraints: 1 });
      await page.locator('.status-sat').waitFor();
      assert.equal(await frame.evaluate(() => Object.values(pu.pu_a.number)[0][0]), '2');
      await page.getByLabel('参数 k').fill('3');
      assert.equal(await frame.evaluate(() => Object.keys(pu.pu_a.number).length), 0);
      assert.equal(await page.locator('.status-sat').count(), 0);
    });
  } finally {
    if (browser) await browser.close();
    server.closeAllConnections();
    await new Promise((resolve) => server.close(resolve));
  }
});
