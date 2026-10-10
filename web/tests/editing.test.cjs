const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { buildSync } = require('esbuild');
const root = path.resolve(__dirname, '../..');

// Bundle the real TypeScript modules in memory using Vite's esbuild dependency.
const { text } = buildSync({
  stdin: { contents: 'export * from "./web/src/bind"; export * from "./web/src/drawing"; export * from "./web/src/importPlan";', resolveDir: root },
  bundle: true, platform: 'node', format: 'cjs', write: false,
}).outputFiles[0];
const compiled = { exports: {} };
new Function('module', 'exports', text)(compiled, compiled.exports);
const { bindDrawing, instanceToDrawing, emptyDrawing, drawingFromGenericLayers, drawingToGenericLayers, resizeDrawing, planImport } = compiled.exports;
const read = (name) => JSON.parse(fs.readFileSync(path.join(root, name), 'utf8'));

test('Tapa: list clues and question marks survive drawing roundtrip', () => {
  const spec = read('impls/tapa.json');
  const instance = { puzzle: 'tapa', rows: 3, cols: 3, clues: { n: { '1,1': [1, 2, -1] } }, regions: {}, params: {}, title: '' };
  const drawing = instanceToDrawing(instance, spec);
  assert.equal(drawing.marks.number['1,1'], '1 2 ?');
  assert.deepEqual(bindDrawing(drawing, spec).clues.n, instance.clues.n);
  const imported = drawingFromGenericLayers([{ id: 'number', element: 'number', target: 'cell', values: { '1,1': '1 2 ?' } }], 3, 3);
  assert.deepEqual(bindDrawing(imported, spec).clues.n, instance.clues.n);
  drawing.marks.number['1,1'] = '0 1';
  assert.throws(() => bindDrawing(drawing, spec), /0/);
});

for (const key of ['easyasabc', 'fuzuli', 'skyscrapers', 'starbattle']) {
  test(`${key}: preserve sample parameters through drawing and resize`, () => {
    const spec = read(`impls/${key}.json`);
    const sample = read(`impls/samples/${key}.json`);
    const drawing = instanceToDrawing(sample, spec);
    const rebound = bindDrawing(drawing, spec);
    for (const [name, value] of Object.entries(sample.params)) assert.deepEqual(rebound.params[name], value);
    assert.equal(rebound.title, sample.title);
    const resized = bindDrawing({ ...drawing, rows: sample.rows + 1, cols: sample.cols + 1 }, spec);
    for (const name of ['k', 'stars']) if (name in sample.params) assert.equal(resized.params[name], sample.params[name]);
  });
}

test('switching puzzle does not leak instance parameters into another rule', () => {
  const drawing = instanceToDrawing(read('impls/samples/fuzuli.json'), read('impls/fuzuli.json'));
  assert.equal(bindDrawing(drawing, read('impls/easyasabc.json')).params.k, 3);
});

const customSpec = (variables = [], layers = []) => ({ key: 'custom', en: 'Custom', zh: '', category: '', subcategory: '', rule: '', aliases: [], defaultRows: 6, defaultCols: 6, usesRegions: false, variables, layers, params: {}, notes: '' });
const inputLayer = (name, element = 'number', target = 'cell', options = {}) => ({ id: `${name}_input`, label: name, element, target, role: 'input', var: name, param: '', palette: {}, options });
const importedLayers = layers => ({ kind: 'penpa', puzzle: null, instance: null, layers, rows: 5, cols: 5, warnings: [], title: '', sourceUrl: '', pid: '', tags: [] });
const clue = (id, element = id, target = 'cell', values = { '0,0': 1 }, options) => ({ id, element, target, values, options });

test('import auto-binds mixed elements independently without mutating the source spec', () => {
  const spec = customSpec();
  const plan = planImport(spec, importedLayers([clue('number'), clue('circle'), clue('surface', 'shade')]), '__unbound');
  assert.equal(spec.variables.length, 0);
  assert.deepEqual(plan.created, ['number_clues', 'circle_clues', 'shade_clues']);
  assert.ok(plan.spec.variables.every(v => v.type === 'constant'));
  assert.deepEqual(plan.documents.map(d => Object.keys(d.drawing.marks)), [['number'], ['circle'], ['shade']]);
});

test('import prefers selected compatible variable, otherwise sole compatible binding', () => {
  const spec = customSpec(['x', 'y'].map(name => ({ name, kind: 'cell', type: 'normal', domain: [0, 9], dense: false, doc: '' })), [inputLayer('x'), inputLayer('y')]);
  assert.equal(planImport(spec, importedLayers([clue('number')]), 'y').documents[0].id, 'y');
  const plan = planImport(spec, importedLayers([clue('number')]), '__unbound');
  assert.equal(plan.documents[0].id, 'number_clues');
  assert.equal(plan.spec.variables.length, 3);
  const sole = customSpec([spec.variables[0]], [inputLayer('x')]);
  assert.equal(planImport(sole, importedLayers([clue('number')]), '__outside').documents[0].id, 'x');
});

test('cages, totals, ordinary givens and fixed regions remain separate, including repeated import', () => {
  const original = customSpec([{ name: 'x', kind: 'cell', type: 'normal', domain: [1, 9], dense: false, doc: '' }], [inputLayer('x')]);
  const layers = [clue('number', 'number', 'cell', { '0,0': 2 }), clue('cage_regions', 'region', 'cell', { '0,0': 0, '0,1': 0 }, { semantic: 'cage-region' }), clue('cage_totals', 'number', 'cell', { '0,0': 100 }, { semantic: 'cage-total', placement: 'corner' }), clue('regions', 'region', 'cell', { '0,0': 0, '0,1': 1 })];
  const plan = planImport(original, importedLayers(layers), 'x');
  assert.deepEqual(plan.documents.map(d => d.id), ['x', 'cage_regions', 'cage_totals', '__regions']);
  assert.equal(plan.documents[0].drawing.marks.number['0,0'], 2);
  assert.deepEqual(plan.documents[1].drawing.cages, { '0,0': 0, '0,1': 0 });
  assert.deepEqual(plan.documents[1].drawing.regions, {});
  assert.deepEqual(plan.documents[2].drawing.cornerNumbers, { '0,0': 100 });
  assert.deepEqual(plan.documents[2].drawing.marks, {});
  assert.equal(plan.spec.usesRegions, true);
  const again = planImport(plan.spec, importedLayers(layers), 'x');
  assert.deepEqual(again.created, []);
  assert.deepEqual(again.documents.map(d => d.id), plan.documents.map(d => d.id));
  const renamed = { ...plan.spec, variables: plan.spec.variables.map(v => v.name === 'cage_totals' ? { ...v, name: 'totals' } : v), layers: plan.spec.layers.map(l => l.var === 'cage_totals' ? { ...l, var: 'totals' } : l) };
  assert.equal(planImport(renamed, importedLayers([layers[2]]), 'x').documents[0].id, 'totals');
});

test('native cage maps and corner numbers survive generic roundtrip and clipping', () => {
  const layers = [clue('cage_regions', 'region', 'cell', { '0,0': 0, '4,4': 1 }, { semantic: 'cage-region' }), clue('cage_totals', 'number', 'cell', { '0,0': 4, '4,4': 52 }, { semantic: 'cage-total', placement: 'corner' })];
  const drawing = drawingFromGenericLayers(layers, 5, 5);
  assert.deepEqual(drawingToGenericLayers(drawing), layers);
  const smaller = resizeDrawing(drawing, 4, 4);
  assert.deepEqual(smaller.cages, { '0,0': 0 });
  assert.deepEqual(smaller.cornerNumbers, { '0,0': 4 });
});

test('import keeps outside lists and creates fixed region binding, without duplicate edge clue variable', () => {
  const layers = [clue('outside', 'outside', 'outside', { top: [[1, 2], -1, 3, -1, -1] }), clue('edgeline', 'edgeline', 'edge', { 'V,0,1': 1 }), clue('regions', 'region', 'cell', { '0,0': 0, '0,1': 1 })];
  const plan = planImport(customSpec(), importedLayers(layers), '__unbound');
  assert.deepEqual(plan.documents.map(d => d.id), ['__outside', '__regions']);
  assert.deepEqual(plan.documents[0].drawing.outside.top['0'], [1, 2]);
  assert.equal(plan.spec.usesRegions, true);
});

test('auto-created names avoid DSL identifiers; list clues get list binding', () => {
  const plan = planImport(customSpec(), importedLayers([clue('number', 'number', 'cell', { '0,0': '1 2 ?' })]), '__unbound', 'let number_clues = 1');
  assert.equal(plan.created[0], 'number_clues_2');
  assert.equal(plan.spec.layers[0].options.mode, 'list');
});

test('invalid dimensions, unsupported layers and empty imports fail before any mutation', () => {
  const spec = customSpec();
  assert.throws(() => planImport(spec, { ...importedLayers([clue('number')]), rows: 41 }, '__unbound'), /尺寸/);
  assert.throws(() => planImport(spec, importedLayers([clue('polygon')]), '__unbound'), /暂不支持/);
  assert.throws(() => planImport(spec, importedLayers([]), '__unbound'), /没有可导入/);
  assert.deepEqual(spec.variables, []);
  assert.deepEqual(spec.layers, []);
});

test('recognized puzzle uses authoritative instance bindings for multiple number variables', () => {
  const spec = customSpec(['x', 'n'].map(name => ({ name, kind: 'cell', type: 'constant', domain: null, dense: false, doc: '' })), [inputLayer('x'), inputLayer('n')]);
  const data = { ...importedLayers([clue('number')]), puzzle: 'custom', instance: { puzzle: 'custom', rows: 5, cols: 5, clues: { x: { '0,0': 2 }, n: { '1,1': 7 } }, regions: {}, params: {}, title: '' } };
  const plan = planImport(spec, data, 'x');
  assert.deepEqual(plan.documents.map(d => [d.id, d.drawing.marks.number]), [['x', { '0,0': 2 }], ['n', { '1,1': 7 }]]);
});

// Render the same safe Markdown component used in the modal, without a browser.
const markdownBundle = buildSync({
  stdin: { contents: 'export { MarkdownDocs } from "./src/MarkdownDocs"; export { renderToStaticMarkup } from "react-dom/server"; export { createElement } from "react";', resolveDir: path.join(root, 'web') },
  bundle: true, platform: 'node', format: 'cjs', write: false,
}).outputFiles[0].text;
const markdownModule = { exports: {} };
new Function('module', 'exports', 'require', markdownBundle)(markdownModule, markdownModule.exports, require);
const { MarkdownDocs, renderToStaticMarkup, createElement } = markdownModule.exports;
test('reference docs render readable headings, lists, tables, code and safe links', () => {
  const html = renderToStaticMarkup(createElement(MarkdownDocs, { source: '# Title\n\n- One **bold**\n- Two `inline`\n\n| Name | Value |\n| --- | --- |\n| x | 1 |\n\n```dsl\nx[p] == 1\n```\n\n[Safe](https://example.com)\n\n<script>alert(1)</script>\n\n[Unsafe](javascript:alert(1))' }));
  for (const tag of ['h1', 'ul', 'li', 'strong', 'table', 'th', 'td', 'pre', 'code']) assert.match(html, new RegExp(`<${tag}[ >]`));
  assert.match(html, /id="title"/);
  assert.match(html, /rel="noopener noreferrer"/);
  assert.doesNotMatch(html, /<script|href="javascript:/);
});

test('domain/kind mismatches require review and never coerce imported values', () => {
  const spec = customSpec([{ name: 'x', kind: 'cell', type: 'normal', domain: [1, 9], dense: false, doc: '' }], [inputLayer('x')]);
  const plan = planImport(spec, importedLayers([clue('number', 'number', 'cell', { '0,0': 100 })]), 'x');
  assert.equal(plan.documents[0].id, 'number_clues');
  assert.equal(plan.documents[0].drawing.marks.number['0,0'], 100);
  assert.equal(plan.review.length, 1);
  const wrongKind = { ...spec, variables: [{ ...spec.variables[0], kind: 'edge' }] };
  assert.equal(planImport(wrongKind, importedLayers([clue('number')]), 'x').created.length, 1);
});

test('corner-number reimports reuse cage totals binding and never ordinary givens', () => {
  const data = importedLayers([clue('cage_totals', 'number', 'cell', { '0,0': 100 }, { semantic: 'cage-total', placement: 'corner' })]);
  const first = planImport(customSpec(), data, '__unbound');
  const next = planImport(first.spec, importedLayers([clue('corner_numbers', 'number', 'cell', { '0,0': 4 }, { semantic: 'cage-total', placement: 'corner' })]), '__unbound');
  assert.deepEqual(next.created, []);
  assert.equal(next.documents[0].id, 'cage_totals');
  assert.deepEqual(next.documents[0].drawing.cornerNumbers, { '0,0': 4 });
});

test('shade paint styles normalize domain while keeping their native drawing color', () => {
  const plan = planImport(customSpec(), importedLayers([clue('surface', 'shade', 'cell', { '0,0': 3 })]), '__unbound');
  assert.deepEqual(plan.spec.variables[0].domain, [1, 1]);
  assert.equal(plan.documents[0].drawing.marks.shade['0,0'], 3);
  assert.equal(bindDrawing(plan.documents[0].drawing, plan.spec).clues.shade_clues['0,0'], 1);
});

test('known circles use semantic instance values once, not a second palette conversion', () => {
  const spec = customSpec([{ name: 'x', kind: 'cell', type: 'normal', domain: [0, 1], dense: false, doc: '' }], [{ ...inputLayer('x', 'circle'), palette: { '0': '#ffffff', '1': '#232733' } }]);
  const data = { ...importedLayers([clue('circle', 'circle', 'cell', { '0,0': 1 })]), puzzle: 'custom', instance: { puzzle: 'custom', rows: 5, cols: 5, clues: { x: { '0,0': 0 } }, regions: {}, params: {}, title: '' } };
  const plan = planImport(spec, data, '__unbound');
  assert.equal(plan.documents[0].id, 'x');
  assert.equal(plan.documents[0].drawing.marks.circle['0,0'], 1);
  assert.equal(bindDrawing(plan.documents[0].drawing, spec).clues.x['0,0'], 0);
});

test('single-letter clues get text bindings; arbitrary text and invalid lists fail before import', () => {
  const plan = planImport(customSpec(), importedLayers([clue('number', 'number', 'cell', { '0,0': 'A', '0,1': 3 })]), '__unbound');
  assert.deepEqual(plan.documents.map(d => d.id), ['number_clues', 'text_clues']);
  assert.equal(plan.documents[1].drawing.marks.text['0,0'], 'A');
  assert.equal(bindDrawing(plan.documents[1].drawing, plan.spec).clues.text_clues['0,0'], 1);
  for (const value of ['hello', '0 1', '1 2 3 4 5', '1 9 ?', 9007199254740992]) assert.throws(() => planImport(customSpec(), importedLayers([clue('number', 'number', 'cell', { '0,0': value })]), '__unbound'), /无法安全绑定/);
});

test('ordinary number imports cannot enter semantic-only corner bindings', () => {
  const spec = customSpec([{ name: 'totals', kind: 'cell', type: 'constant', domain: null, dense: false, doc: '' }], [inputLayer('totals', 'number', 'cell', { semantic: 'cage-total', placement: 'corner' })]);
  const plan = planImport(spec, importedLayers([clue('number')]), 'totals');
  assert.equal(plan.documents[0].id, 'number_clues');
  assert.deepEqual(plan.documents[0].drawing.marks.number, { '0,0': 1 });
  const corners = planImport({ ...spec, variables: [{ ...spec.variables[0], name: 'x', type: 'normal', domain: [1, 9] }], layers: [inputLayer('x')] }, importedLayers([clue('corner_numbers', 'number', 'cell', { '0,0': 4 }, { semantic: 'cage-total', placement: 'corner' })]), 'x');
  assert.equal(corners.documents[0].id, 'cage_totals');
});

test('outside lists create a solver-compatible list binding and conversion of scalar bindings requires review', () => {
  const data = importedLayers([clue('outside', 'outside', 'outside', { top: [[1, 2], 3, -1, -1, -1] })]);
  const plan = planImport(customSpec(), data, '__unbound');
  assert.equal(plan.spec.layers[0].options.mode, 'list');
  const rebound = bindDrawing(plan.documents[0].drawing, plan.spec);
  assert.deepEqual(rebound.params.top.slice(0, 2), [[1, 2], [3]]);
  const scalar = customSpec([], [{ ...inputLayer('', 'outside', 'outside'), options: { sides: ['top'], mode: 'int' } }]);
  const changed = planImport(scalar, data, '__outside');
  assert.equal(scalar.layers[0].options.mode, 'int');
  assert.equal(changed.spec.layers[0].options.mode, 'list');
  assert.match(changed.review[0], /列表模式/);
});
