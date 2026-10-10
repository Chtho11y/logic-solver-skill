const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const penpa = path.resolve(__dirname, '../public/penpa-edit');
const plain = value => JSON.parse(JSON.stringify(value));
const drawing = (rows = 3, cols = 3, number = {}) => ({ rows, cols, marks: { number }, outside: {}, regions: {} });

// Exercise the vendored native point geometry, cage rendering segments and
// history translation in Node. Only DOM/canvas painting is stubbed.
function setup() {
  const elements = new Map();
  const element = id => {
    if (!elements.has(id)) elements.set(id, { value: '0', style: {}, getContext: () => ({}), addEventListener() {} });
    return elements.get(id);
  };
  const messages = [];
  const context = vm.createContext({
    console: { error() {} }, setTimeout, setInterval() {},
    location: { origin: 'http://localhost' },
    document: { getElementById: element, addEventListener() {} },
    UserSettings: { loadFromCookies() {} },
    PenpaUI: { set_visible_modes_by_gridtype() {} },
    Conflicts: class { constructor(pu) { this.pu = pu; } },
    parent: { postMessage: message => messages.push(plain(message)) },
    addEventListener() {},
    create_newboard() { throw new Error('Transactions must not rebuild boards'); },
  });
  context.window = context;
  for (const file of ['js/class_p.js', 'js/class_square.js']) vm.runInContext(fs.readFileSync(path.join(penpa, file), 'utf8'), context);
  vm.runInContext(`
    pu = new Puzzle_square(3, 3, 38);
    pu.create_point();
    pu.centerlist = [16,17,18,23,24,25,30,31,32];
    pu.draw = function () {};
    pu.redraw = function () { this.draw(); };
    pu.get_orientation = function () { return 0; };
    pu.search_center = function () { this.center_n = this.centerlist[0]; };
    pu.canvasxy_update = pu.canvas_size_setting = pu.point_move = pu.make_frameline = function () {};
    pu.maketext = function () { return JSON.stringify({ question: this.pu_q, answer: this.pu_a }); };
  `, context);
  vm.runInContext(fs.readFileSync(path.join(penpa, 'studio-bridge.js'), 'utf8'), context);
  const bridge = context.StudioBridge;
  assert.equal(bridge.loadDocuments([{ id: 'keep', drawing: drawing(3, 3, { '0,0': '7' }) }]), true);
  messages.length = 0;
  return { context, bridge, messages, cell: (r, c) => (r + 2) * context.pu.nx0 + c + 2 };
}

function putHistories(context, cell) {
  const q = context.pu.pu_q;
  const a = context.pu.pu_a;
  q.command_undo.push(['number', cell, ['4', 1, '1'], 'pu_q']);
  q.command_redo.push(['number', cell, ['8', 1, '1'], 'pu_q']);
  q.command_replay.push(['number', cell, ['7', 1, '1'], 'pu_q']);
  a.number[cell] = ['9', 2, '1'];
  a.command_undo.push(['number', cell, null, 'pu_a']);
  context.pu.pu_q_col.number[cell] = '#123456';
  context.pu.pu_a_col.number[cell] = '#654321';
  return { q, a, qColors: context.pu.pu_q_col, aColors: context.pu.pu_a_col };
}

test('multi-document replacement skips resize, preserves untouched data/history and emits one update', () => {
  const { context, bridge, messages, cell } = setup();
  const before = putHistories(context, cell(0, 0));
  context.pu.resize_bottom = context.pu.resize_right = () => { throw new Error('same-size resize'); };
  assert.equal(bridge.replaceDocuments([
    { id: 'a', drawing: drawing(3, 3, { '0,0': 1 }) },
    { id: 'b', drawing: drawing(3, 3, { '0,0': 2 }) },
  ]), true);
  assert.equal(bridge.getSelection().activeVariable, 'keep');
  assert.equal(context.pu.pu_q, before.q);
  assert.equal(context.pu.pu_a, before.a);
  assert.equal(context.pu.pu_q_col, before.qColors);
  assert.equal(context.pu.pu_a_col, before.aColors);
  assert.equal(before.q.command_undo.size(), 1);
  assert.equal(messages.length, 1);
  assert.deepEqual(Object.keys(bridge.variableCounts()).sort(), ['a', 'b', 'keep']);
  bridge.selectVariable('a');
  assert.equal(context.pu.pu_q.number[cell(0, 0)][0], '1');
  bridge.selectVariable('b');
  assert.equal(context.pu.pu_q.number[cell(0, 0)][0], '2');
});

test('one native resize pass translates every document, colors and all histories', () => {
  const { context, bridge, cell } = setup();
  putHistories(context, cell(0, 0));
  bridge.replaceDrawing('other', drawing(3, 3, { '1,1': 8 }));
  context.pu.pu_q.command_undo.push(['number', cell(1, 1), null, 'pu_q']);
  bridge.selectVariable('keep');
  let rows = 0, cols = 0;
  const bottom = context.pu.resize_bottom, right = context.pu.resize_right;
  context.pu.resize_bottom = function (...args) { rows++; return bottom.apply(this, args); };
  context.pu.resize_right = function (...args) { cols++; return right.apply(this, args); };
  assert.equal(bridge.replaceDocuments([
    { id: 'a', drawing: drawing(4, 5, { '0,0': 1 }) },
    { id: 'b', drawing: drawing(4, 5, { '0,0': 2 }) },
  ], 'a'), true);
  assert.equal(rows, 1);
  assert.equal(cols, 2);
  assert.deepEqual(plain(context.pu.space), [0, 0, 0, 0]);
  assert.equal(bridge.occupancy().rows, 4);
  assert.equal(bridge.occupancy().cols, 5);
  assert.equal(context.pu.pu_a.number[cell(0, 0)][0], '9');
  assert.equal(context.pu.pu_a.command_undo.__a[0][1], cell(0, 0));
  assert.equal(context.pu.pu_a_col.number[cell(0, 0)], '#654321');
  bridge.selectVariable('keep');
  assert.equal(context.pu.pu_q.number[cell(0, 0)][0], '7');
  assert.equal(context.pu.pu_q_col.number[cell(0, 0)], '#123456');
  for (const field of ['command_undo', 'command_redo', 'command_replay']) {
    assert.equal(context.pu.pu_q[field].__a[0][1], cell(0, 0));
    assert.equal(context.pu.pu_q[field].size(), 1);
  }
  bridge.selectVariable('other');
  assert.equal(context.pu.pu_q.number[cell(1, 1)][0], '8');
  assert.equal(context.pu.pu_q.command_undo.__a[0][1], cell(1, 1));
});

for (const size of [3, 5]) test(`failed ${size === 3 ? 'same-size' : 'resized'} stamp rolls back all documents and selection`, () => {
  const { context, bridge, messages, cell } = setup();
  const before = putHistories(context, cell(0, 0));
  const oldRevision = bridge.getRevision();
  const oldPoint = context.pu.point;
  const bad = drawing(size, size);
  Object.defineProperty(bad, 'cornerNumbers', { get() { throw new Error('deliberate second stamp failure'); } });
  assert.equal(bridge.replaceDocuments([
    { id: 'first', drawing: drawing(size, size, { '0,0': 1 }) },
    { id: 'bad', drawing: bad },
  ], 'first'), false);
  assert.equal(context.pu.pu_q, before.q);
  assert.equal(context.pu.pu_a, before.a);
  assert.equal(context.pu.point, oldPoint);
  assert.equal(bridge.getSelection().activeVariable, 'keep');
  assert.equal(bridge.getRevision(), oldRevision);
  assert.equal(bridge.occupancy().rows, 3);
  assert.deepEqual(Object.keys(bridge.variableCounts()), ['keep']);
  assert.equal(messages.length, 0);
  assert.equal(context.pu.pu_q.command_undo.__a[0][1], cell(0, 0));
});

test('invalid sizes, duplicate IDs and missing selection are rejected before changes', () => {
  const { context, bridge, messages } = setup();
  const q = context.pu.pu_q;
  for (const items of [
    [{ id: 'x', drawing: drawing(0, 3) }],
    [{ id: 'x', drawing: drawing() }, { id: 'x', drawing: drawing() }],
    [{ id: 'x', drawing: drawing() }, { id: 'y', drawing: drawing(4, 3) }],
  ]) assert.equal(bridge.replaceDocuments(items), false);
  assert.equal(bridge.replaceDocuments([], 'missing'), false);
  assert.equal(context.pu.pu_q, q);
  assert.equal(messages.length, 0);
});

test('cage membership, visible cage outlines and corner totals remain separate documents', () => {
  const { context, bridge, cell } = setup();
  const cages = { ...drawing(), cages: { '0,0': 0, '0,1': 0, '1,1': 1 } };
  const totals = { ...drawing(), cornerNumbers: { '0,0': 12, '1,1': 3 } };
  assert.equal(bridge.replaceDocuments([{ id: 'cages', drawing: cages }, { id: 'totals', drawing: totals }], 'cages'), true);
  assert.deepEqual(plain(context.pu.pu_q.killercages), [[cell(0, 0), cell(0, 1)], [cell(1, 1)]]);
  assert.ok(Object.keys(context.pu.pu_q.cage).length > 0);
  assert.equal(Object.keys(context.pu.pu_q.lineE).length, 0);
  bridge.selectVariable('totals');
  assert.equal(context.pu.pu_q.numberS[4 * (cell(0, 0) + context.pu.nx0 * context.pu.ny0)][0], '12');
  assert.equal(bridge.occupancy().counts.number, 2);
  assert.equal(Object.keys(context.pu.pu_q.number).length, 0);
});

test('public resize and legacy replaceDrawing preserve independent questions', () => {
  const { context, bridge, cell } = setup();
  assert.equal(bridge.resize(2, 2), true);
  assert.equal(bridge.occupancy().rows, 2);
  assert.equal(bridge.occupancy().cols, 2);
  assert.equal(context.pu.pu_q.number[cell(0, 0)][0], '7');
  assert.equal(bridge.replaceDrawing('legacy', drawing(2, 2, { '1,1': 4 })), true);
  assert.equal(bridge.getSelection().activeVariable, 'legacy');
  bridge.selectVariable('keep');
  assert.equal(context.pu.pu_q.number[cell(0, 0)][0], '7');
});

test('a native migration failure restores original board geometry and history references', () => {
  const { context, bridge, cell, messages } = setup();
  const before = putHistories(context, cell(0, 0));
  const points = context.pu.point;
  const centers = context.pu.centerlist;
  const right = context.pu.resize_right;
  context.pu.resize_right = function (...args) { right.apply(this, args); throw new Error('migration failed after translation'); };
  assert.equal(bridge.replaceDocuments([{ id: 'new', drawing: drawing(4, 5) }], 'new'), false);
  assert.equal(context.pu.point, points);
  assert.equal(context.pu.centerlist, centers);
  assert.equal(context.pu.pu_q, before.q);
  assert.equal(context.pu.pu_a, before.a);
  assert.equal(context.pu.pu_q.command_undo.__a[0][1], cell(0, 0));
  assert.equal(bridge.occupancy().rows, 3);
  assert.equal(bridge.occupancy().cols, 3);
  assert.equal(messages.length, 0);
});

test('full document loading is atomic and clears manual answers only on success', () => {
  const { context, bridge, cell } = setup();
  const before = putHistories(context, cell(0, 0));
  const bad = drawing();
  Object.defineProperty(bad, 'marks', { get() { throw new Error('bad document'); } });
  assert.equal(bridge.loadDocuments([{ id: 'first', drawing: drawing() }, { id: 'bad', drawing: bad }]), false);
  assert.equal(context.pu.pu_q, before.q);
  assert.equal(context.pu.pu_a, before.a);
  assert.deepEqual(Object.keys(bridge.variableCounts()), ['keep']);
  assert.equal(bridge.loadDocuments([{ id: 'fresh', drawing: drawing(3, 3, { '0,0': 6 }) }]), true);
  assert.deepEqual(Object.keys(bridge.variableCounts()), ['fresh']);
  assert.equal(context.pu.pu_a.command_undo.size(), 0);
  assert.equal(Object.keys(context.pu.pu_a.number).length, 0);
  assert.equal(bridge.getSelection().activeVariable, 'fresh');
});

test('edge dots use native H/V midpoints and count as dots rather than cell circles', () => {
  const { context, bridge } = setup();
  const dots = { ...drawing(), marks: { dot: { 'H,2,0': 1, 'V,0,2': 2 } } };
  assert.equal(bridge.replaceDocuments([{ id: 'dot_clues', drawing: dots }], 'dot_clues'), true);
  const board = context.pu;
  const area = board.nx0 * board.ny0;
  const corner = (r, c) => board.point[area + (r + 1) * board.nx0 + c + 1];
  const expected = [
    [corner(2, 0), corner(2, 1), 1],
    [corner(0, 2), corner(1, 2), 2],
  ];
  const stamped = Object.entries(board.pu_q.symbol);
  assert.equal(stamped.length, 2);
  for (const [a, b, value] of expected) {
    const [index, mark] = stamped.find(([, mark]) => mark[0] === value);
    assert.equal(board.point[index].x, (a.x + b.x) / 2);
    assert.equal(board.point[index].y, (a.y + b.y) / 2);
    assert.equal(mark[1], 'circle_M');
  }
  assert.equal(bridge.occupancy().counts.dot, 2);
  assert.equal(bridge.occupancy().counts.circle, 0);
  assert.equal(bridge.variableCounts().dot_clues, 2);
});

test('both cell diagonals stamp native corner pairs and remain separate from region walls', () => {
  const { context, bridge } = setup();
  assert.equal(bridge.replaceDrawing('diagonals', { ...drawing(), marks: { diagonal: { '0,1': 1, '2,0': 2 } } }), true);
  const board = context.pu;
  const area = board.nx0 * board.ny0;
  const corner = (r, c) => area + (r + 1) * board.nx0 + c + 1;
  const pairs = Object.keys(board.pu_q.lineE);
  assert.ok(pairs.includes(`${corner(0, 1)},${corner(1, 2)}`));
  assert.ok(pairs.includes(`${corner(2, 1)},${corner(3, 0)}`));
  assert.equal(bridge.occupancy().counts.diagonal, 2);
  assert.equal(bridge.occupancy().counts.edgeline, 0);
});

test('imported dot and diagonal tools retain their own selection instead of switching bindings', () => {
  const { context, bridge } = setup();
  const board = context.pu;
  board.mode_set = function (mode) { this.mode[this.mode.qa].edit_mode = mode; this.type = this.type_set(); };
  board.subsymbolmode = function (family) { this.mode[this.mode.qa].symbol[0] = family; this.type = this.type_set(); };
  board.submode_check = function (name) { this.mode[this.mode.qa].lineE[0] = name.slice(-1); this.type = this.type_set(); };
  bridge.setTool('dot');
  assert.equal(bridge.getSelection().tool, 'dot');
  assert.deepEqual(plain(board.type), [2, 3]);
  bridge.setTool('circle');
  assert.equal(bridge.getSelection().tool, 'circle');
  bridge.setTool('diagonal');
  assert.equal(bridge.getSelection().tool, 'diagonal');
  bridge.setTool('edgeline');
  assert.equal(bridge.getSelection().tool, 'edgeline');
});

test('every accepted cell symbol produces a native mark, including ship, tent, wave and bulb', () => {
  const { context, bridge, cell } = setup();
  for (const tool of ['shade', 'number', 'text', 'circle', 'square', 'triangle', 'star', 'cross', 'tree', 'tent', 'ship', 'wave', 'bulb', 'arrow']) {
    assert.equal(bridge.replaceDrawing(tool, { ...drawing(), marks: { [tool]: { '1,2': tool === 'text' ? 'A' : 1 } } }), true, tool);
    const q = context.pu.pu_q;
    assert.ok(q.surface[cell(1, 2)] || q.number[cell(1, 2)] || q.symbol[cell(1, 2)], tool);
  }
});
