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
const keys = ['easyasabc', 'fuzuli', 'slither', 'simpleloop', 'heyawake', 'fillomino', 'domino-search', 'nonogram', 'akari', 'starbattle', 'yinyang', 'mines'];
const specs = Object.fromEntries(keys.map((key) => {
  const spec = JSON.parse(read(`impls/${key}.json`));
  spec.layers = spec.layers.map((layer) => ({ palette: {}, options: {}, ...layer }));
  spec.source = read(`impls/${key}.dsl`);
  return [key, spec];
}));

test('central workspace and solve lifecycle in the browser', { timeout: 120000 }, async (t) => {
  const pending = [];
  let realSolve = true;
  let lastPayload;
  let lastSolved;
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
      lastPayload = JSON.parse(body);
      if (realSolve) {
        try { lastSolved = JSON.parse(execFileSync(process.env.PUZZLE_PYTHON || 'python', ['-X', 'utf8', '-c', 'import json,sys; from puzzle.runner import solve_payload; print(json.dumps(solve_payload(json.load(sys.stdin))))'], { cwd: root, input: body, encoding: 'utf8' }));
        } catch (error) { lastSolved = { status: 'error', message: String(error), constraints: 0 }; }
        return json(lastSolved);
      }
      pending.push({ body: JSON.parse(body), respond: json });
      return;
    }
    if (req.url === '/api/import') {
      let body = '';
      for await (const chunk of req) body += chunk;
      try {
        return json(JSON.parse(execFileSync(process.env.PUZZLE_PYTHON || 'python', ['-X', 'utf8', '-c', 'import json,sys; from puzzle.importing import import_url; p=json.load(sys.stdin); print(json.dumps(import_url(p["url"],p.get("puzzle"))))'], { cwd: root, input: body, encoding: 'utf8' })));
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
    page.setDefaultTimeout(8000);
    const errors = [];
    page.on('pageerror', (error) => errors.push(String(error)));
    await page.goto(`http://127.0.0.1:${server.address().port}`);
    await page.locator('.penpa-frame').waitFor();
    const frame = await (await page.locator('.penpa-frame').elementHandle()).contentFrame();
    await frame.waitForFunction(() => window.pu && window.StudioBridge && pu.centerlist.length > 1);
    const button = name => frame.getByRole('button', { name, exact: true });
    const captureRender = async () => frame.evaluate(() => {
      const draw = pu.draw_frame;
      pu.draw_frame = function () {
        window.rendered = JSON.parse(JSON.stringify({ q: this.pu_q, a: this.pu_a }));
        return draw.apply(this, arguments);
      };
      pu.redraw();
    });
    const addVariable = async name => {
      await button('＋ 新增变量').click();
      await frame.getByLabel('变量名', { exact: true }).fill(name);
      await button('添加变量').click();
      await frame.getByRole('button', { name, exact: true }).waitFor();
    };
    const drawNumber = async (name, value) => {
      await frame.locator('#mo_number_lb').click();
      await button(name).click();
      const point = await frame.evaluate(() => {
        const p = pu.point[(2 + pu.space[0]) * pu.nx0 + 2 + pu.space[2]];
        return { x: p.x, y: p.y };
      });
      await frame.locator('#canvas').click({ position: point });
      await page.keyboard.type(value);
    };
    const runSolve = async () => {
      await button('求解').click();
      await frame.locator('.studio-status [class^=status-]').waitFor();
      if (lastSolved.status !== 'sat') { fs.mkdirSync(artifacts, { recursive: true }); fs.writeFileSync(path.join(artifacts, 'failed-request.json'), JSON.stringify(lastPayload)); }
      assert.equal(lastSolved.status, 'sat', `${lastSolved.message} ${JSON.stringify(lastPayload.spec.variables)}\n${lastPayload.source}`);
    };
    const preset = async key => {
      await frame.getByLabel('预设', { exact: true }).selectOption(key);
      await button('导入预设').click();
      await page.waitForTimeout(100);
      await frame.getByText(/已导入 .* 预设/).waitFor();
      await captureRender();
      await frame.locator('#studio-controls details').evaluateAll(items => items.forEach(el => el.open = false));
    };

    await t.test('all actions and variable targets are inside native Penpa, without a separate sidebar', async () => {
      assert.equal(await page.locator('.board-controls, .layers').count(), 0);
      assert.equal(await page.getByRole('button', { name: '求解', exact: true }).count(), 0);
      assert.equal(await button('求解').count(), 1);
      assert.equal(await frame.locator('#mode_button + #studio-variables').count(), 1);
      assert.equal(await frame.locator('#top_button #studio-controls').count(), 1);
      assert.equal(await frame.getByText('绘制到：', { exact: true }).isVisible(), true);
    });

    await t.test('create independent variables without choosing a preset, then solve both', async () => {
      await frame.locator('#mo_number_lb').click();
      await addVariable('x');
      await drawNumber('x', '1');
      await addVariable('y');
      await drawNumber('y', '2');
      await button('x').click();
      assert.equal(await frame.evaluate(() => Object.values(pu.pu_q.number)[0][0]), '1');
      await button('y').click();
      assert.equal(await frame.evaluate(() => Object.values(pu.pu_q.number)[0][0]), '2');
      await page.getByLabel('规则 DSL', { exact: true }).fill('for p in cells():\n    x[p] == 1\n    y[p] == 2');
      await captureRender();
      await runSolve();
      assert.equal(lastPayload.spec.key, 'custom');
      assert.deepEqual(lastPayload.spec.variables.map(v => v.name), ['x', 'y']);
      assert.deepEqual(lastPayload.spec.variables.map(v => v.domain), [[0, 9], [0, 9]]);
      assert.equal(lastSolved.values.x['0,0'], 1);
      assert.equal(lastSolved.values.y['0,0'], 2);
      assert.equal(await frame.evaluate(() => Object.values(rendered.a.number)[0][0]), '2');
      assert.equal(await frame.evaluate(() => Object.keys(pu.pu_a.number).length), 0);
    });

    await t.test('variable undo histories and resizing preserve both same-cell clues', async () => {
      await button('x').click();
      await frame.locator('#tb_undo').click();
      assert.equal(await frame.evaluate(() => Object.keys(pu.pu_q.number).length), 0);
      await button('y').click();
      assert.equal(await frame.evaluate(() => Object.values(pu.pu_q.number)[0][0]), '2');
      await button('x').click();
      await frame.locator('#tb_redo').click();
      await frame.getByText('尺寸与参数', { exact: true }).click();
      await frame.getByLabel('行数', { exact: true }).fill('7');
      await frame.waitForFunction(() => pu.ny === 7);
      assert.equal(await frame.evaluate(() => Object.values(pu.pu_q.number)[0][0]), '1');
      await button('y').click();
      assert.equal(await frame.evaluate(() => Object.values(pu.pu_q.number)[0][0]), '2');
      await runSolve();
    });

    await t.test('editing invalidates a pending solve and repeated shortcuts are ignored', async () => {
      realSolve = false;
      const request = page.waitForRequest('**/api/solve');
      await button('求解').click();
      await request;
      await page.waitForTimeout(50);
      await page.getByLabel('规则 DSL', { exact: true }).press('Control+Enter');
      assert.equal(pending.length, 1);
      await page.getByLabel('规则 DSL', { exact: true }).fill('x[cell(0, 0)] == 3');
      pending[0].respond({ status: 'sat', values: { x: { '0,0': 1 } }, constraints: 1 });
      await frame.waitForFunction(() => !document.querySelector('button.solve').disabled);
      assert.equal(await frame.locator('.status-sat').count(), 0);
      realSolve = true;
    });

    await t.test('link import replaces only the chosen variable', async () => {
      await button('y').click();
      const url = await frame.evaluate(() => StudioBridge.exportUrl());
      await button('x').click();
      await frame.getByText('导入链接', { exact: true }).click();
      await frame.getByLabel('导入链接', { exact: true }).fill(url);
      await button('导入到当前变量').click();
      await frame.getByText(/已导入到 x/).waitFor();
      assert.equal(await frame.evaluate(() => Object.values(pu.pu_q.number)[0][0]), '2');
      await button('y').click();
      assert.equal(await frame.evaluate(() => Object.values(pu.pu_q.number)[0][0]), '2');
      await page.getByLabel('规则 DSL', { exact: true }).fill('for p in cells():\n    x[p] == 2\n    y[p] == 2');
      await runSolve();
    });

    await t.test('manual answers remain editable after solving or clearing solver results', async () => {
      await frame.locator('#pu_a_label').click();
      await drawNumber('x', '9');
      const answer = await frame.evaluate(() => JSON.stringify(pu.pu_a));
      await runSolve();
      assert.equal(await frame.evaluate(() => JSON.stringify(pu.pu_a)), answer);
      const editor = page.getByLabel('规则 DSL', { exact: true });
      await editor.fill((await editor.inputValue()) + '\n# changed');
      assert.equal(await frame.evaluate(() => JSON.stringify(pu.pu_a)), answer);
      await frame.locator('#tb_undo').click();
      assert.equal(await frame.evaluate(() => Object.keys(pu.pu_a.number).length), 0);
      await frame.locator('#pu_q_label').click();
    });

    for (const key of keys) {
      await t.test(`${key}: imported preset → independent drawing layers → actual solve`, async () => {
        await preset(key);
        await runSolve();
        assert.ok(lastPayload.documents.length >= lastPayload.spec.variables.length);
        const expected = JSON.parse(read(`impls/samples/${key}.json`));
        for (const [name, values] of Object.entries(expected.clues || {}))
          if (lastSolved.values[name]) for (const [point, value] of Object.entries(values)) assert.equal(lastSolved.values[name][point], value);
        assert.equal(await frame.evaluate(() => Object.keys(pu.pu_a.number).length), 0);
      });
    }
    await t.test('imported presets remain editable and accept additional variables', async () => {
      await preset('easyasabc');
      await frame.locator('#mo_number_lb').click();
      await addVariable('extra');
      await drawNumber('extra', '4');
      const editor = page.getByLabel('规则 DSL', { exact: true });
      await editor.fill((await editor.inputValue()) + '\nfor p in cells():\n    extra[p] == 4\n');
      await runSolve();
      assert.equal(lastSolved.values.extra['0,0'], 4);
      assert.equal(lastPayload.instance.params.k, 2);
      await captureRender();
      fs.mkdirSync(artifacts, { recursive: true });
      await page.screenshot({ path: path.join(artifacts, 'desktop.png'), fullPage: true });
      for (const width of [800, 390]) {
        await page.setViewportSize({ width, height: 844 });
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
        assert.equal(await button('求解').isVisible(), true);
        await button('extra').click();
      }
      await page.screenshot({ path: path.join(artifacts, 'mobile.png'), fullPage: true });
      assert.deepEqual(errors, []);
    });

  } finally {
    if (browser) await browser.close();
    server.closeAllConnections();
    await new Promise((resolve) => server.close(resolve));
  }
});
