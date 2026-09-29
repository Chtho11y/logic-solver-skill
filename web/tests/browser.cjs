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
const keys = ['easyasabc', 'fuzuli', 'slither', 'simpleloop', 'heyawake', 'fillomino', 'domino-search', 'nonogram', 'akari', 'starbattle', 'yinyang', 'mines', 'tapa', 'shakashaka'];
const specs = Object.fromEntries(keys.map((key) => {
  const spec = JSON.parse(read(`impls/${key}.json`));
  spec.layers = spec.layers.map((layer) => ({ palette: {}, options: {}, ...layer }));
  spec.source = read(`impls/${key}.dsl`);
  spec.partial = Boolean(spec.unencodedClues?.length || spec.notes?.includes('部分实现'));
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
    if (req.url === '/api/builtins') return json(JSON.parse(execFileSync(process.env.PUZZLE_PYTHON || 'python', ['-X', 'utf8', '-c', 'import json; from puzzle.dsl.builtins import function_table; print(json.dumps({"entries":[e.__dict__ for e in function_table()]}))'], { cwd: root, encoding: 'utf8' })));
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
    const drawNumber = async (name, value, row = 0, col = 0) => {
      await frame.locator('#mo_number_lb').click();
      await button(name).click();
      const point = await frame.evaluate(({row, col}) => {
        const p = pu.point[(2 + pu.space[0] + row) * pu.nx0 + 2 + pu.space[2] + col];
        return { x: p.x, y: p.y };
      }, {row, col});
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

    await t.test('actions stay in native Penpa alongside the variable overview', async () => {
      assert.equal(await page.getByRole('complementary', { name: '变量总览' }).count(), 1);
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
      await frame.locator('#pu_a_label').click();
      await frame.locator('#mo_number_lb').click();
      await addVariable('y');
      assert.equal(await frame.evaluate(() => pu.mode.qa), 'pu_q');
      assert.equal(await frame.evaluate(() => StudioBridge.getSelection().activeVariable), 'y');
      const newVariablePoint = await frame.evaluate(() => { const p = pu.point[(2 + pu.space[0]) * pu.nx0 + 2 + pu.space[2]]; return { x: p.x, y: p.y }; });
      await frame.locator('#canvas').click({ position: newVariablePoint });
      await page.keyboard.type('2');
      assert.equal(await frame.evaluate(() => Object.keys(pu.pu_a.number).length), 0);
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

    await t.test('overview hides variables independently without changing data or solve results', async () => {
      const before = await frame.evaluate(() => StudioBridge.exportDocuments());
      const revision = await frame.evaluate(() => StudioBridge.getRevision());
      await page.getByRole('button', { name: '隐藏变量 y', exact: true }).click();
      assert.equal(await frame.evaluate(() => Object.values(rendered.q.number)[0][0]), '1');
      assert.equal(await frame.evaluate(() => Object.values(rendered.a.number)[0][0]), '1');
      await page.getByRole('button', { name: '全部隐藏', exact: true }).click();
      assert.equal(await frame.evaluate(() => Object.keys(rendered.q.number).length), 0);
      assert.equal(await frame.evaluate(() => Object.keys(rendered.a.number).length), 0);
      assert.equal(await frame.evaluate(() => StudioBridge.getRevision()), revision);
      assert.deepEqual(await frame.evaluate(() => StudioBridge.exportDocuments()), before);
      assert.equal(await frame.locator('.status-sat').count(), 1);
      await page.getByRole('button', { name: '全部显示', exact: true }).click();
      const answerToggle = page.getByRole('button', { name: 'y 求解答案', exact: true });
      assert.equal(await answerToggle.getAttribute('aria-pressed'), 'true');
      await answerToggle.click();
      assert.equal(await answerToggle.getAttribute('aria-pressed'), 'false');
      assert.equal(await frame.evaluate(() => Object.values(rendered.a.number)[0][0]), '1');
      assert.equal(await frame.evaluate(() => Object.values(rendered.q.number)[0][0]), '2');
      await page.getByRole('button', { name: 'y 题目线索', exact: true }).click();
      assert.equal(await frame.evaluate(() => Object.values(rendered.q.number)[0][0]), '1');
      await page.getByRole('button', { name: '全部显示', exact: true }).click();
      await page.locator('.variable-main').filter({ hasText: 'x' }).click();
      assert.equal(await frame.evaluate(() => StudioBridge.getSelection().activeVariable), 'x');
    });

    await t.test('hidden active variable stays hidden at separate cells and after keyboard edits', async () => {
      await drawNumber('y', '3', 1, 1);
      await page.getByRole('button', { name: '隐藏变量 y', exact: true }).click();
      assert.equal(await frame.evaluate(() => Object.keys(rendered.q.number).length), 1);
      await frame.evaluate(() => { pu.pu_q.numberS['22'] = ['7', 1]; pu.redraw(); });
      assert.equal(await frame.evaluate(() => Object.keys(rendered.q.numberS).length), 0);
      await frame.evaluate(() => { delete pu.pu_q.numberS['22']; });
      await page.getByRole('button', { name: '仅显示 y', exact: true }).click();
      assert.equal(await frame.evaluate(() => Object.keys(rendered.q.number).length), 2);
      await frame.locator('#tb_undo').click();
      await page.getByRole('button', { name: '全部显示', exact: true }).click();
    });

    await t.test('variable undo histories and resizing preserve both same-cell clues', async () => {
      await button('x').click();
      await frame.locator('#tb_undo').click();
      assert.equal(await frame.evaluate(() => Object.keys(pu.pu_q.number).length), 0);
      await button('y').click();
      assert.equal(await frame.evaluate(() => Object.values(pu.pu_q.number)[0][0]), '2');
      await button('x').click();
      await frame.locator('#tb_redo').click();
      assert.equal(await frame.getByLabel('行数', { exact: true }).isVisible(), true);
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
      assert.equal(await frame.getByLabel('导入链接', { exact: true }).isVisible(), true);
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
      await page.getByRole('button', { name: '隐藏变量 手工答案', exact: true }).click();
      assert.equal(await frame.evaluate(() => Object.keys(rendered.a.number).length), 0);
      assert.equal(await frame.evaluate(() => JSON.stringify(pu.pu_a)), answer);
      await page.getByRole('button', { name: '显示变量 手工答案', exact: true }).click();
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
    await t.test('DSL highlighting, completion and searchable reference docs', async () => {
      const editor = page.getByLabel('规则 DSL', { exact: true });
      await editor.fill('cel');
      await editor.press('Control+Space');
      const editorRect = await editor.boundingBox();
      const completionRect = await page.getByRole('listbox', { name: 'DSL 补全' }).boundingBox();
      assert.ok(completionRect.y > editorRect.y && completionRect.y < editorRect.y + 50, 'completion is next to first-line caret');
      await page.getByRole('option', { name: /^cells\(/ }).click();
      assert.equal(await editor.inputValue(), 'cells');
      await editor.fill('import "fill"\nsubset_lat');
      await editor.press('Control+Space');
      await editor.press('Tab');
      assert.match(await editor.inputValue(), /subset_latin$/);
      await editor.fill('\n'.repeat(10) + '    cel');
      await editor.press('Control+Space');
      const lowerCompletion = await page.getByRole('listbox', { name: 'DSL 补全' }).boundingBox();
      assert.ok(lowerCompletion.y > completionRect.y + 150, 'completion follows caret line');
      assert.ok(lowerCompletion.x >= completionRect.x, 'completion follows column until clamped at viewport edge');
      assert.ok(lowerCompletion.x + lowerCompletion.width <= 1440, 'completion stays inside viewport');
      fs.mkdirSync(artifacts, { recursive: true });
      await page.screenshot({ path: path.join(artifacts, 'completion.png') });
      await editor.press('Escape');
      await editor.fill('import "fill"\nsubset_latin');
      assert.ok(await page.locator('.dsl-highlight .tok-keyword').count());
      await page.getByRole('button', { name: 'Doc 文档', exact: true }).click();
      await page.getByRole('button', { name: 'Builtin 函数', exact: true }).click();
      await page.getByLabel('搜索文档').fill('cells');
      assert.ok(await page.locator('.dsl-doc-content article').count());
      await page.getByRole('button', { name: '规则库', exact: true }).click();
      await page.getByLabel('搜索文档').fill('subset_latin');
      assert.ok(await page.locator('.dsl-doc-content details').count());
      await page.getByRole('button', { name: '关闭文档', exact: true }).click();
    });

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

    await t.test('variable editing preserves drawings and history, updates rules, and deletes bindings', async () => {
      await page.setViewportSize({ width: 1440, height: 900 });
      const editor = page.getByLabel('规则 DSL', { exact: true });
      await editor.fill((await editor.inputValue()) + '\n# extra remains a comment');
      await button('extra').click();
      const before = await frame.evaluate(() => JSON.stringify(pu.pu_q));
      await page.getByRole('button', { name: '编辑变量 extra', exact: true }).click();
      await page.getByLabel('编辑变量名', { exact: true }).fill('x');
      await page.getByRole('button', { name: '保存变量', exact: true }).click();
      assert.equal(await page.getByRole('alert').count(), 1);
      await page.getByLabel('编辑变量名', { exact: true }).fill('bonus');
      await page.getByLabel('编辑最大值', { exact: true }).fill('8');
      await page.getByLabel('变量说明', { exact: true }).fill('additional numbers');
      await page.screenshot({ path: path.join(artifacts, 'variable-editor.png') });
      await page.getByRole('button', { name: '保存变量', exact: true }).click();
      assert.equal(await page.getByRole('dialog').count(), 0);
      assert.equal(await frame.evaluate(() => JSON.stringify(pu.pu_q)), before);
      assert.match(await editor.inputValue(), /bonus\[p\] == 4/);
      assert.match(await editor.inputValue(), /# extra remains a comment/);
      assert.equal(await button('bonus').getAttribute('aria-pressed'), 'true');
      await runSolve();
      assert.equal(lastSolved.values.bonus['0,0'], 4);
      assert.equal(lastPayload.spec.variables.find(v => v.name === 'bonus').domain[1], 8);
      assert.equal(lastPayload.spec.variables.find(v => v.name === 'bonus').doc, 'additional numbers');
      await frame.locator('#tb_undo').click();
      assert.equal(await frame.evaluate(() => Object.keys(pu.pu_q.number).length), 0);
      await frame.locator('#tb_redo').click();
      await page.getByRole('button', { name: '编辑变量 bonus', exact: true }).click();
      await page.getByRole('button', { name: '删除变量', exact: true }).click();
      await page.getByRole('button', { name: '确认删除', exact: true }).click();
      assert.equal(await page.getByRole('button', { name: '编辑变量 bonus', exact: true }).count(), 0);
      assert.ok((await frame.evaluate(() => StudioBridge.exportDocuments())).every(doc => doc.id !== 'bonus'));
      await editor.fill(specs.easyasabc.source);
      await runSolve();
      assert.deepEqual(lastPayload.spec.variables.map(v => v.name), ['x']);
    });

    await t.test('partial presets explain gaps and Tapa native clues reach the solver', async () => {
      await preset('shakashaka');
      assert.ok(await frame.getByText(/部分实现：/).isVisible());
      await preset('tapa');
      await button('清空盘面').click();
      await frame.locator('#mo_number_lb').click();
      await button('n').click();
      await frame.evaluate(() => {
        const k = pu.centerlist.find(i => pu.point[i].use === 1);
        pu.pu_q.number[k] = ['?', 1, '4'];
        pu.redraw();
      });
      await runSolve();
      assert.ok(await frame.getByText(/满足当前已编码规则；未检查唯一性/).isVisible());
      assert.ok(Object.values(lastSolved.values.n).some(value => Array.isArray(value) && value[0] === -1));
    });

  } finally {
    if (browser) await browser.close();
    server.closeAllConnections();
    await new Promise((resolve) => server.close(resolve));
  }
});
