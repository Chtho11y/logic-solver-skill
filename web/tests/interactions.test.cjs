const { test } = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const { build } = require('esbuild');
const React = require('react');
const renderer = require('react-test-renderer');
const { act } = renderer;
const root = path.resolve(__dirname, '..');
const deferred = () => { let resolve; const promise = new Promise(r => { resolve = r; }); return { promise, resolve }; };
const imported = (value = 3) => ({ kind: 'penpa', puzzle: null, instance: null, layers: [{ id: 'number', element: 'number', target: 'cell', values: { '0,0': value } }], rows: 6, cols: 6, title: '', warnings: [], tags: [], sourceUrl: '', pid: '' });
const bundle = build({
  stdin: { contents: 'export { App } from "./src/App"; export { IntegerInput } from "./src/IntegerInput";', resolveDir: root },
  bundle: true, platform: 'node', format: 'cjs', write: false, external: ['react', 'react/jsx-runtime'],
  plugins: [{ name: 'mock-workspace-boundaries', setup(builder) {
    const mocks = {
      './api': 'export const api = new Proxy({}, { get: (_, key) => (...args) => globalThis.__puzzleHarness.api[key](...args) });',
      './dslLanguage': 'export const keywords = "if elif else for in let and or not true false def return import use".split(" ");',
      './DslEditor': 'import React from "react"; export const DslEditor = props => React.createElement("dsl-editor", props);',
      './VariablePanel': 'import React from "react"; export const VariablePanel = props => React.createElement("variable-panel", props);',
      './VariableEditor': 'export const VariableEditor = () => null;',
      './PenpaPane': 'import React from "react"; export const PenpaPane = React.forwardRef((props, ref) => { React.useImperativeHandle(ref, () => globalThis.__puzzleHarness.bridge); React.useEffect(() => { props.onOccupancy({ rows: 6, cols: 6, revision: 0, counts: {}, tool: "number", activeVariable: "__unbound", mode: "number" }); }, []); return React.createElement("penpa-pane", null, props.controls, props.variableControls); });',
    };
    builder.onResolve({ filter: /^\.\/(api|dslLanguage|DslEditor|VariablePanel|VariableEditor|PenpaPane)$/ }, args => ({ path: args.path, namespace: 'mock' }));
    builder.onLoad({ filter: /.*/, namespace: 'mock' }, args => ({ contents: mocks[args.path], resolveDir: root }));
  } }],
}).then(result => { const module = { exports: {} }; new Function('module', 'exports', 'require', result.outputFiles[0].text)(module, module.exports, require); return module.exports; });
const button = (tree, label) => tree.root.findAllByType('button').find(node => node.children.join('') === label);
const input = (tree, label) => tree.root.findAllByType('input').find(node => node.props['aria-label'] === label);
const importForm = tree => input(tree, '导入链接').parent;
const textOf = tree => JSON.stringify(tree.toJSON());

async function workspace() {
  const calls = { import: [], replace: [], clear: 0, resize: [] };
  const bridge = {
    revision: 0, selection: { tool: 'number', activeVariable: '__unbound' },
    getRevision() { return this.revision; }, getSelection() { return this.selection; },
    loadDocuments() { return true; }, setTool(tool) { this.selection.tool = tool; },
    selectVariable(id) { this.selection.activeVariable = id; return true; },
    replaceDocuments(documents, active) { calls.replace.push(structuredClone(documents)); this.selection.activeVariable = active; this.revision++; return true; },
    clearSolution() { calls.clear++; }, applySolution() {}, setHidden() {}, variableCounts() { return {}; }, exportDocuments() { return []; },
    resize(rows, cols) { calls.resize.push([rows, cols]); this.revision++; return true; },
  };
  const harness = { bridge, calls, api: {
    puzzles: async () => [], health: async () => ({ solver: { backends: [{ name: 'auto', label: 'auto', available: true }] } }),
    importUrl: () => { const pending = deferred(); calls.import.push(pending); return pending.promise; },
    solve: async () => ({ status: 'sat', values: {}, constraints: 1 }),
  } };
  globalThis.__puzzleHarness = harness;
  const { App } = await bundle;
  let tree;
  await act(async () => { tree = renderer.create(React.createElement(App), { createNodeMock: () => ({ showModal() {} }) }); });
  await act(async () => input(tree, '导入链接').props.onChange({ target: { value: 'https://example.invalid/test' } }));
  return { tree, ...harness };
}
const submit = tree => act(() => { importForm(tree).props.onSubmit({ preventDefault() {} }); });
async function addVariable(tree, name) {
  await act(async () => button(tree, '＋ 新增变量').props.onClick());
  await act(async () => input(tree, '变量名').props.onChange({ target: { value: name } }));
  await act(async () => input(tree, '变量名').parent.props.onSubmit({ preventDefault() {} }));
}

test('repeat import submits once; decode failure preserves the solved workspace', async () => {
  const { tree, calls } = await workspace();
  await act(async () => button(tree, '求解').props.onClick());
  assert.match(textOf(tree), /status-sat/);
  const clears = calls.clear;
  submit(tree); submit(tree);
  assert.equal(calls.import.length, 1);
  await act(async () => calls.import[0].resolve({ error: 'invalid link' }));
  assert.equal(calls.replace.length, 0);
  assert.equal(calls.clear, clears);
  assert.match(textOf(tree), /status-sat/);
  assert.match(textOf(tree), /invalid link/);
  tree.unmount();
});

for (const change of ['drawing', 'DSL', 'selection']) test(`a newer ${change} prevents stale import from overwriting the workspace`, async () => {
  const { tree, calls, bridge } = await workspace();
  submit(tree);
  if (change === 'drawing') bridge.revision++;
  if (change === 'selection') bridge.selection.activeVariable = 'newer';
  if (change === 'DSL') await act(async () => tree.root.findByType('dsl-editor').props.onChange('newer rules'));
  await act(async () => calls.import[0].resolve(imported()));
  assert.equal(calls.replace.length, 0);
  assert.match(textOf(tree), /已取消过期/);
  if (change === 'DSL') assert.equal(tree.root.findByType('dsl-editor').props.source, 'newer rules');
  tree.unmount();
});

test('successful import binds automatically and repeated import reuses the new variable', async () => {
  const { tree, calls } = await workspace();
  for (const value of [3, 4]) {
    submit(tree);
    await act(async () => calls.import.at(-1).resolve(imported(value)));
  }
  assert.equal(calls.replace.length, 2);
  assert.equal(calls.replace[0][0].id, 'number_clues');
  assert.equal(calls.replace[1][0].id, 'number_clues');
  assert.equal(calls.replace[1][0].drawing.marks.number['0,0'], 4);
  assert.deepEqual(tree.root.findByType('variable-panel').props.rows.filter(r => !r.id.startsWith('__')).map(r => r.id), ['number_clues']);
  tree.unmount();
});

test('ambiguous binding preview can cancel without changes, then explicitly confirm a new variable', async () => {
  const { tree, calls, bridge } = await workspace();
  await addVariable(tree, 'x'); await addVariable(tree, 'y');
  bridge.selection.activeVariable = '__unbound';
  submit(tree);
  await act(async () => calls.import.at(-1).resolve(imported()));
  assert.ok(button(tree, '确认导入'));
  assert.equal(calls.replace.length, 0);
  await act(async () => button(tree, '取消导入').props.onClick());
  assert.equal(calls.replace.length, 0);
  assert.deepEqual(tree.root.findByType('variable-panel').props.rows.filter(r => !r.id.startsWith('__')).map(r => r.id), ['x', 'y']);
  submit(tree);
  await act(async () => calls.import.at(-1).resolve(imported()));
  await act(async () => button(tree, '确认导入').props.onClick());
  assert.equal(calls.replace.length, 1);
  assert.equal(calls.replace[0][0].id, 'number_clues');
  tree.unmount();
});

test('reserved names are rejected by the actual add-variable interaction', async () => {
  const { tree } = await workspace();
  await addVariable(tree, 'elif');
  assert.match(textOf(tree), /非保留英文标识符/);
  assert.equal(tree.root.findByType('variable-panel').props.rows.filter(r => !r.id.startsWith('__')).length, 0);
  tree.unmount();
});

test('integer editing commits once on blur, Escape and invalid input keep the old value', async () => {
  const { IntegerInput } = await bundle;
  const committed = [];
  let tree;
  await act(async () => { tree = renderer.create(React.createElement(IntegerInput, { value: 6, min: 1, max: 40, label: 'rows', onCommit: n => committed.push(n) })); });
  const field = () => tree.root.findByType('input');
  await act(async () => field().props.onChange({ target: { value: '1' } }));
  assert.deepEqual(committed, []);
  await act(async () => field().props.onChange({ target: { value: '12' } }));
  assert.deepEqual(committed, []);
  await act(async () => field().props.onBlur());
  assert.deepEqual(committed, [12]);
  await act(async () => field().props.onChange({ target: { value: '2' } }));
  await act(async () => field().props.onKeyDown({ key: 'Escape', preventDefault() {} }));
  await act(async () => field().props.onBlur());
  assert.deepEqual(committed, [12]);
  await act(async () => field().props.onChange({ target: { value: '' } }));
  await act(async () => field().props.onBlur());
  assert.deepEqual(committed, [12]);
  assert.equal(field().props.value, '6');
  tree.unmount();
});
