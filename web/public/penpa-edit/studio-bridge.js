/**
 * Host bridge for Logic Puzzle Studio. Same-origin iframe of Penpa+.
 * The parent React app talks through window.StudioBridge and postMessage.
 */
(function () {
  "use strict";

  // Cookies from earlier Penpa sessions overwrite display size mid-load and
  // leave a one-cell canvas. This copy is only used inside the studio iframe.
  function disableCookies() {
    if (!window.UserSettings) return false;
    UserSettings.loadFromCookies = function () {};
    return true;
  }
  if (!disableCookies()) {
    window.addEventListener("load", disableCookies);
  }

  const TOOL_MODE = {
    shade: "surface",
    number: "number",
    text: "number",
    outside: "number",
    circle: "symbol",
    square: "symbol",
    triangle: "symbol",
    star: "symbol",
    cross: "symbol",
    tree: "symbol",
    tent: "symbol",
    ship: "symbol",
    wave: "symbol",
    bulb: "symbol",
    arrow: "symbol",
    link: "line",
    edgeline: "lineE",
    diagonal: "lineE",
    dot: "symbol",
    region: "lineE",
  };

  const SYMBOL_SUB = {
    circle: "circle_M",
    dot: "circle_M",
    square: "square_M",
    triangle: "triup_M",
    star: "star",
    cross: "ox_B",
    tree: "tents",
    tent: "tents",
    ship: "battleship",
    wave: "water",
    bulb: "sun_moon",
    arrow: "arrow_S",
  };

  const hidden = {};
  let revision = 0;
  let lastQuestion = "";

  const solutions = {};
  let hookedBoard = null;

  let documents = Object.create(null);
  let documentColors = Object.create(null);
  let activeVariable = '__unbound';
  let composing = false;

  function saveActive() {
    if (window.pu && !composing) { documents[activeVariable] = pu.pu_q; documentColors[activeVariable] = pu.pu_q_col; }
  }

  function emptyQuestion(source = pu.pu_q) {
    const q = {};
    for (const [key, value] of Object.entries(source)) {
      q[key] = key.startsWith('command_') ? new value.constructor() : Array.isArray(value) ? [] : {};
    }
    return q;
  }

  function selectVariable(id, beginDrawing = false) {
    if (!window.pu) return false;
    const tool = currentTool();
    saveActive();
    if (!documents[id]) {
      if (activeVariable === '__unbound' && id !== '__unbound') {
        documents[id] = documents.__unbound;
        documentColors[id] = documentColors.__unbound;
        delete documents.__unbound;
        delete documentColors.__unbound;
      } else documents[id] = emptyQuestion();
    }
    documentColors[id] ||= emptyQuestion(pu.pu_q_col);
    activeVariable = id;
    pu.pu_q = documents[id];
    pu.pu_q_col = documentColors[id];
    if (beginDrawing) { pu.mode_qa('pu_q'); setTool(tool); }
    pu.redraw();
    notify();
    return true;
  }

  function loadDocuments(items) {
    return updateDocuments(items, items?.[0]?.id || '__unbound', true);
  }

  function renameVariable(from, to) {
    if (!window.pu || from === to) return true;
    saveActive();
    if (documents[to]) return false;
    if (documents[from]) { documents[to] = documents[from]; delete documents[from]; }
    if (documentColors[from]) { documentColors[to] = documentColors[from]; delete documentColors[from]; }
    if (solutions[from]) { solutions[to] = solutions[from]; delete solutions[from]; }
    for (const prefix of ['var:', 'in:', 'out:']) { hidden[prefix + to] = hidden[prefix + from]; delete hidden[prefix + from]; }
    if (activeVariable === from) activeVariable = to;
    pu.redraw(); notify(); return true;
  }

  function deleteVariable(id) {
    if (!window.pu) return false;
    saveActive();
    delete documents[id]; delete documentColors[id]; delete solutions[id];
    for (const prefix of ['var:', 'in:', 'out:']) delete hidden[prefix + id];
    if (activeVariable === id) {
      activeVariable = Object.keys(documents)[0] || '__unbound';
      documents[activeVariable] ||= emptyQuestion();
      documentColors[activeVariable] ||= emptyQuestion(pu.pu_q_col);
      pu.pu_q = documents[activeVariable]; pu.pu_q_col = documentColors[activeVariable];
    }
    pu.redraw(); notify(); return true;
  }

  function exportDocuments() {
    saveActive();
    const q = pu.pu_q, colors = pu.pu_q_col;
    try {
      return Object.entries(documents).map(([id, question]) => {
        pu.pu_q = question;
        pu.pu_q_col = documentColors[id];
        return { id, url: exportUrl() };
      });
    } finally { pu.pu_q = q; pu.pu_q_col = colors; }
  }

  function replaceDrawing(id, drawing) {
    return replaceDocuments([{ id, drawing }], id);
  }

  function replaceDocuments(items, activeId) {
    return updateDocuments(items, activeId, false);
  }

  // Keep native Stack/Point prototypes and shared references. DOM/canvas objects
  // are host resources, not puzzle state, and must not be copied.
  function copyState(value, copies = new Map()) {
    if (!value || typeof value !== 'object') return value;
    if (copies.has(value)) return copies.get(value);
    if (!Array.isArray(value) && Object.prototype.toString.call(value) !== '[object Object]') return value;
    const copy = Array.isArray(value) ? [] : Object.create(Object.getPrototypeOf(value));
    copies.set(value, copy);
    for (const [key, descriptor] of Object.entries(Object.getOwnPropertyDescriptors(value))) {
      if ('value' in descriptor) descriptor.value = copyState(descriptor.value, copies);
      Object.defineProperty(copy, key, descriptor);
    }
    return copy;
  }

  function validSize(rows, cols) {
    return Number.isInteger(rows) && Number.isInteger(cols) && rows >= 1 && cols >= 1 && rows <= 40 && cols <= 40;
  }

  function updateDocuments(items, activeId, reset, requestedSize) {
    if (!window.pu || composing || !Array.isArray(items)) return false;
    const size = requestedSize || items[0]?.drawing || innerSize();
    const { rows, cols } = size;
    const ids = new Set();
    if (!validSize(rows, cols)) return false;
    for (const item of items) {
      if (!item || typeof item.id !== 'string' || !item.id || ids.has(item.id) ||
          !item.drawing || item.drawing.rows !== rows || item.drawing.cols !== cols) return false;
      ids.add(item.id);
    }
    if (activeId !== undefined && (typeof activeId !== 'string' || !activeId)) return false;
    saveActive();
    const selected = activeId ?? activeVariable;
    if (!ids.has(selected) && !(reset ? selected === '__unbound' && !items.length : documents[selected])) return false;
    const board = pu;
    const snapshot = {
      board: Object.getOwnPropertyDescriptors(board), documents, documentColors,
      activeVariable, revision, lastQuestion, solutions: { ...solutions },
    };
    const oldSize = innerSize();
    const changingSize = oldSize.rows !== rows || oldSize.cols !== cols;
    composing = true;
    let ok = false;
    try {
      if (changingSize) {
        // Resize works on detached native data. A later stamp/migration failure
        // can therefore restore the exact old documents, answers and histories.
        const copies = new Map([[board, board]]);
        for (const [key, descriptor] of Object.entries(snapshot.board)) {
          if ('value' in descriptor) board[key] = copyState(descriptor.value, copies);
        }
        documents = copyState(documents, copies);
        documentColors = copyState(documentColors, copies);
      } else {
        documents = Object.assign(Object.create(null), documents);
        documentColors = Object.assign(Object.create(null), documentColors);
      }
      board.redraw = function () {};
      if (changingSize && !resizeOne(rows, cols)) throw new Error('Unable to resize the Penpa board');
      if (reset) {
        documents = Object.create(null);
        documentColors = Object.create(null);
        board.pu_a = emptyQuestion(board.pu_a);
        board.pu_a_col = emptyQuestion(board.pu_a_col);
      }
      for (const item of items) {
        board.pu_q = emptyQuestion(board.pu_q);
        board.pu_q_col = emptyQuestion(board.pu_q_col);
        if (!stamp(item.drawing, true)) throw new Error('Unable to stamp imported document');
        documents[item.id] = board.pu_q;
        documentColors[item.id] = board.pu_q_col;
      }
      activeVariable = selected;
      documents[selected] ||= emptyQuestion(board.pu_q);
      documentColors[selected] ||= emptyQuestion(board.pu_q_col);
      board.pu_q = documents[selected];
      board.pu_q_col = documentColors[selected];
      Object.keys(solutions).forEach(key => delete solutions[key]);
      ok = true;
    } catch (err) {
      console.error('penpa document transaction', err);
      for (const key of Reflect.ownKeys(board)) if (!(key in snapshot.board)) delete board[key];
      Object.defineProperties(board, snapshot.board);
      documents = snapshot.documents;
      documentColors = snapshot.documentColors;
      activeVariable = snapshot.activeVariable;
      revision = snapshot.revision;
      lastQuestion = snapshot.lastQuestion;
      Object.keys(solutions).forEach(key => delete solutions[key]);
      Object.assign(solutions, snapshot.solutions);
      // Native resize may already have changed canvas dimensions before failing.
      if (changingSize && typeof board.canvas_size_setting === 'function') board.canvas_size_setting();
    } finally {
      if (snapshot.board.redraw) Object.defineProperty(board, 'redraw', snapshot.board.redraw);
      else delete board.redraw;
      composing = false;
    }
    board.redraw();
    if (ok) notify();
    return ok;
  }

  function currentTool() {
    const mode = pu.mode[pu.mode.qa].edit_mode;
    if (mode === 'symbol') {
      const tool = symbolTool([1, pu.mode[pu.mode.qa].symbol[0]]);
      return tool === 'circle' && pu.type?.length === 2 && pu.type.every(t => t === 2 || t === 3) ? 'dot' : tool;
    }
    if (mode === 'lineE' && pu.mode[pu.mode.qa].lineE[0] === '2') return 'diagonal';
    return { surface: 'shade', number: 'number', sudoku: 'number', line: 'link', lineE: 'edgeline', wall: 'diagonal', cage: 'region' }[mode] || 'number';
  }

  function symbolTool(entry, index) {
    const family = String(entry?.[1] || '').toLowerCase();
    const sid = Number(entry?.[0]);
    const category = Math.floor(Number(index) / (pu.nx0 * pu.ny0));
    if ((category === 2 || category === 3) && (family.includes('circle') || family.startsWith('ox'))) return 'dot';
    if (family.includes('circle') || (family.startsWith('ox') && sid <= 2)) return 'circle';
    if (family.includes('square')) return 'square';
    if (family.includes('tri')) return 'triangle';
    if (family.includes('star')) return 'star';
    if (family.includes('cross') || family.startsWith('ox')) return 'cross';
    if (family === 'tents') return sid === 2 ? 'tree' : 'tent';
    if (family.includes('ship')) return 'ship';
    if (family.includes('water')) return 'wave';
    if (family.includes('sun')) return 'bulb';
    if (family.includes('arrow')) return 'arrow';
    return 'symbol';
  }

  function markTool(field, key, value) {
    if (field === 'number') return classifyIndex(key).kind === 'outside' ? 'outside' : 'number';
    if (field === 'symbol') return symbolTool(value, key);
    if (field === 'lineE' && isDiagonalPair(key)) return 'diagonal';
    return { surface: 'shade', line: 'link', lineE: 'edgeline', wall: 'diagonal', killercages: 'region' }[field];
  }

  function isDiagonalPair(key) {
    const pair = String(key).split(',').map(Number);
    if (pair.length !== 2 || !pair.every(Number.isInteger)) return false;
    const area = pu.nx0 * pu.ny0;
    if (!pair.every(index => Math.floor(index / area) === 1)) return false;
    const [a, b] = pair.map(index => index % area);
    return Math.abs(Math.floor(a / pu.nx0) - Math.floor(b / pu.nx0)) === 1 && Math.abs(a % pu.nx0 - b % pu.nx0) === 1;
  }

  function presentation(question, answer) {
    const merged = {};
    if (!composing) for (const [id, other] of Object.entries(documents)) {
      if (id === activeVariable || hidden['var:' + id] || hidden['in:' + id]) continue;
      for (const [field, marks] of Object.entries(other)) {
        if (!field.startsWith('command_')) merged[field] = Array.isArray(marks) ? marks : { ...merged[field], ...marks };
      }
    }
    if (!hidden['var:' + activeVariable] && !hidden['in:' + activeVariable]) for (const [field, marks] of Object.entries(question)) merged[field] = Array.isArray(marks) ? marks : { ...merged[field], ...marks };
    const q = { ...question, ...merged }, a = { ...answer };
    // Native modes also store marks in numberS, polygon, arrows, etc.
    // Clear every hidden field, not only the solver's supported mark types.
    for (const [field, value] of Object.entries(question)) {
      if (!field.startsWith('command_') && !(field in merged)) q[field] = Array.isArray(value) ? [] : {};
    }
    if (hidden['var:__manual']) for (const [field, value] of Object.entries(a)) {
      if (!field.startsWith('command_')) a[field] = Array.isArray(value) ? [] : {};
    }
    for (const field of ['surface', 'number', 'symbol', 'line', 'lineE', 'wall', 'killercages']) {
      const entries = merged[field] || {};
      q[field] = Array.isArray(entries)
        ? (hidden.region ? [] : entries)
        : Object.fromEntries(Object.entries(entries).filter(([key, value]) => !hidden[markTool(field, key, value)]));
    }
    // Solver marks exist only while drawing. Never mutate native answers/history.
    for (const [id, { element, fields }] of Object.entries(solutions).sort(([a], [b]) => Number(a === activeVariable) - Number(b === activeVariable))) {
      if (hidden['var:' + id] || hidden['out:' + id] || hidden['out:' + element]) continue;
      for (const [field, marks] of Object.entries(fields)) a[field] = { ...a[field], ...marks };
    }
    return { q, a };
  }

  function installPresentation() {
    if (!window.pu || hookedBoard === pu) return;
    hookedBoard = pu;
    Object.keys(solutions).forEach(key => delete solutions[key]);
    const draw = pu.draw;
    pu.draw = function () {
      const q = this.pu_q, a = this.pu_a;
      const view = presentation(q, a);
      this.pu_q = view.q;
      this.pu_a = view.a;
      try { return draw.apply(this, arguments); }
      finally { this.pu_q = q; this.pu_a = a; }
    };
  }

  function fullQuestion() { return cloneMarks(window.pu && pu.pu_q); }

  // Counts alone miss a changed number or a moved mark. Do not include answer
  // overlays, selection, mode, or undo history in the content revision.
  function getRevision() {
    if (!window.pu) return -1;
    installPresentation();
    saveActive();
    const signature = JSON.stringify([pu.gridtype, pu.nx, pu.ny, pu.space, pu.centerlist, Object.entries(documents).sort(([a], [b]) => a.localeCompare(b)).map(([id, q]) => [id, cloneMarks(q)]), cloneMarks(pu.pu_a)]);
    if (signature !== lastQuestion) { lastQuestion = signature; revision += 1; }
    return revision;
  }

  function isEmpty() {
    return [...Object.values(fullQuestion()), ...Object.values(cloneMarks(window.pu && pu.pu_a))].every(function (value) {
      return !value || (typeof value === "object" && Object.keys(value).length === 0);
    });
  }

  function innerSize() {
    const pu = window.pu;
    if (!pu) return { rows: 10, cols: 10 };
    const top = pu.space ? pu.space[0] : 0;
    const bottom = pu.space ? pu.space[1] : 0;
    const left = pu.space ? pu.space[2] : 0;
    const right = pu.space ? pu.space[3] : 0;
    return {
      rows: Math.max(1, (pu.ny || 10) - top - bottom),
      cols: Math.max(1, (pu.nx || 10) - left - right),
    };
  }

  function classifyIndex(index) {
    const pu = window.pu;
    const nx0 = pu.nx0;
    const ny0 = pu.ny0;
    const area = nx0 * ny0;
    const rest = Number(index) % area;
    const pr = Math.floor(rest / nx0);
    const pc = rest % nx0;
    const top = pu.space[0];
    const left = pu.space[2];
    const size = innerSize();
    const r0 = 2 + top;
    const c0 = 2 + left;
    if (pr >= r0 && pr < r0 + size.rows && pc >= c0 && pc < c0 + size.cols) {
      return { kind: "cell", r: pr - r0, c: pc - c0 };
    }
    return { kind: "outside" };
  }

  function cellIndex(row, col) {
    const pu = window.pu;
    const pr = row + 2 + (pu.space[0] || 0);
    const pc = col + 2 + (pu.space[2] || 0);
    return pr * pu.nx0 + pc;
  }

  function countKeys(obj) {
    if (!obj || typeof obj !== "object") return 0;
    return Object.keys(obj).length;
  }

  function bag(qa, field) {
    const pu = window.pu;
    return (pu && pu[qa] && pu[qa][field]) || {};
  }

  function occupancy() {
    const pu = window.pu;
    const size = innerSize();
    const counts = {
      shade: 0,
      number: 0,
      text: 0,
      outside: 0,
      circle: 0,
      square: 0,
      triangle: 0,
      star: 0,
      cross: 0,
      tree: 0,
      tent: 0,
      ship: 0,
      wave: 0,
      bulb: 0,
      arrow: 0,
      link: 0,
      edgeline: 0,
      diagonal: 0,
      dot: 0,
      region: 0,
    };
    if (!pu || !pu.pu_q) {
      return { rows: size.rows, cols: size.cols, counts: counts, mode: "surface" };
    }
    const surface = bag("pu_q", "surface");
    const line = bag("pu_q", "line");
    const lineE = bag("pu_q", "lineE");
    const wall = bag("pu_q", "wall");
    const numbers = bag("pu_q", "number");
    const symbols = bag("pu_q", "symbol");
    counts.shade = countKeys(surface);
    counts.link = countKeys(line);
    counts.diagonal = countKeys(wall) + Object.keys(lineE).filter(isDiagonalPair).length;
    counts.edgeline = countKeys(lineE) - Object.keys(lineE).filter(isDiagonalPair).length;
    for (const index of Object.keys(numbers || {})) {
      if (classifyIndex(index).kind === "outside") counts.outside += 1;
      else counts.number += 1;
    }
    for (const [index, entry] of Object.entries(symbols || {})) {
      const tool = symbolTool(entry, index);
      if (tool in counts) counts[tool] += 1;
    }
    counts.number += countKeys(bag("pu_q", "numberS"));
    counts.region = (pu.pu_q.killercages || []).reduce((n, cells) => n + cells.length, 0);
    const mode = (pu.mode && pu.mode[pu.mode.qa] && pu.mode[pu.mode.qa].edit_mode) || "surface";
    return { rows: size.rows, cols: size.cols, counts: counts, mode: mode };
  }

  function notify() {
    if (composing) return;
    const payload = occupancy();
    payload.tool = window.pu ? currentTool() : 'number';
    payload.activeVariable = activeVariable;
    window.parent.postMessage({ type: "penpa-occupancy", ...payload, revision: getRevision() }, location.origin);
  }

  function cloneMarks(obj) {
    const skip = { command_redo: true, command_undo: true, command_replay: true };
    const out = {};
    if (!obj) return out;
    Object.keys(obj).forEach(function (key) {
      if (skip[key]) return;
      try {
        out[key] = JSON.parse(JSON.stringify(obj[key]));
      } catch (err) { /* ignore */ }
    });
    return out;
  }

  function exportUrl() {
    if (!window.pu || typeof pu.maketext !== 'function') return '';
    // Upstream maketext clears replay arrays and temporarily removes history.
    // Solving must remain a read-only operation, including if export throws.
    const history = [];
    for (const name of ['pu_q', 'pu_a', 'pu_q_col', 'pu_a_col']) {
      for (const field of ['command_undo', 'command_redo', 'command_replay']) {
        const stack = pu[name]?.[field];
        if (stack) history.push([stack, stack.__a]);
      }
    }
    try { return pu.maketext(); }
    finally { for (const [stack, items] of history) stack.__a = items; }
  }

  function resize(rows, cols) {
    return updateDocuments([], undefined, false, { rows, cols });
  }

  function resizeOne(rows, cols) {
    if (!window.pu || pu.gridtype !== 'square' || !validSize(rows, cols)) return false;
    // Each native step migrates the active question and manual answer once.
    // Apply the same native translator to every other independent document,
    // including color and undo/redo/replay stacks, without rebuilding boards.
    const board = pu;
    const ownTranslator = Object.getOwnPropertyDescriptor(board, 'translate_puzzle_elements');
    const translate = board.translate_puzzle_elements;
    board.translate_puzzle_elements = function (translatePoint) {
      translate.call(this, translatePoint);
      for (const [id, question] of Object.entries(documents)) {
        if (question === this.pu_q) continue;
        const other = {
          pu_q: question, pu_q_col: documentColors[id],
          pu_a: emptyQuestion(this.pu_a), pu_a_col: emptyQuestion(this.pu_a_col),
          cursol: -1, cursolS: -1, freelinecircle_g: [-1, -1],
          selection: [], conflict_cells: [], solution: null,
        };
        translate.call(other, translatePoint);
      }
    };
    try {
      for (let step = 0; step <= 80; step++) {
        const size = innerSize();
        if (size.rows === rows && size.cols === cols) return true;
        // 'white' resizes the outside margin and leaves innerSize unchanged.
        if (size.rows !== rows) board.resize_bottom(rows > size.rows ? 1 : -1, 'black');
        else board.resize_right(cols > size.cols ? 1 : -1, 'black');
        const after = innerSize();
        if (after.rows === size.rows && after.cols === size.cols) return false;
      }
      return false;
    } finally {
      if (ownTranslator) Object.defineProperty(board, 'translate_puzzle_elements', ownTranslator);
      else delete board.translate_puzzle_elements;
    }
  }

  function setSize(rows, cols, quiet) {
    rows = Math.max(1, Math.min(40, Number(rows) || 10));
    cols = Math.max(1, Math.min(40, Number(cols) || 10));
    const size1 = document.getElementById("nb_size1");
    const size2 = document.getElementById("nb_size2");
    if (!size1 || !size2 || typeof create_newboard !== "function") return false;
    size1.value = String(cols);
    size2.value = String(rows);
    ["nb_space1", "nb_space2", "nb_space3", "nb_space4"].forEach(function (id) {
      const el = document.getElementById(id);
      if (el) el.value = "0";
    });
    if (window.UserSettings) {
      UserSettings.gridtype = "square";
      const size = Number(UserSettings.displaysize);
      if (!(size >= 12 && size <= 90)) UserSettings.displaysize = 38;
    }
    create_newboard();
    // The floating palette can obscure the host's variable row. Users can
    // still open it explicitly with Penpa's Panel control.
    pu.panelflag = true;
    UserSettings.panel_shown = false;
    installPresentation();
    if (!quiet) notify();
    return true;
  }

  function parseRC(key) {
    const parts = String(key).split(",");
    if (parts.length !== 2) return null;
    const r = Number(parts[0]);
    const c = Number(parts[1]);
    if (!Number.isInteger(r) || !Number.isInteger(c)) return null;
    return { r: r, c: c };
  }

  function parseEdge(key) {
    const parts = String(key).split(",");
    if (parts.length !== 3) return null;
    const orient = parts[0];
    const r = Number(parts[1]);
    const c = Number(parts[2]);
    if ((orient !== "H" && orient !== "V") || !Number.isInteger(r) || !Number.isInteger(c)) return null;
    return { orient: orient, r: r, c: c };
  }

  function cornerIndex(row, col) {
    const pu = window.pu;
    const pr = row + 1 + (pu.space[0] || 0);
    const pc = col + 1 + (pu.space[2] || 0);
    return pr * pu.nx0 + pc + pu.ny0 * pu.nx0;
  }

  const SYMBOL_STAMP = {
    circle: function (v) { return [Number(v) || 1, "circle_M", 1]; },
    square: function (v) { return [Number(v) || 1, "square_M", 1]; },
    triangle: function (v) { return [Number(v) || 1, "triup_M", 1]; },
    star: function () { return [1, "star", 1]; },
    cross: function () { return [2, "cross", 1]; },
    tree: function () { return [2, "tents", 1]; },
    tent: function () { return [1, "tents", 1]; },
    ship: function (v) { return [Number(v) || 1, "battleship", 1]; },
    wave: function () { return [1, "water", 1]; },
    bulb: function () { return [1, "sun_moon", 1]; },
  };

  const OURS_DIR_TO_PENPA = { "0": "0", "1": "3", "2": "1", "3": "2" };

  function stamp(drawing, currentBoard = false) {
    if (!drawing || !window.pu || (!currentBoard && typeof create_newboard !== "function")) return false;
    try {
      const rows = Math.max(1, Math.min(40, Number(drawing.rows) || 10));
      const cols = Math.max(1, Math.min(40, Number(drawing.cols) || 10));
      if (!currentBoard && !setSize(rows, cols, true)) return false;
      const pu = window.pu;
      if (!pu || !pu.pu_q) return false;
      const q = pu.pu_q;
      ["surface", "number", "numberS", "symbol", "line", "lineE"].forEach(function (field) {
        if (!q[field] || typeof q[field] !== "object" || Array.isArray(q[field])) q[field] = {};
      });
      const marks = drawing.marks || {};

      Object.entries(marks.shade || {}).forEach(function (pair) {
        const pos = parseRC(pair[0]);
        if (!pos) return;
        const v = Number(pair[1]);
        if (!v) return;
        q.surface[String(cellIndex(pos.r, pos.c))] = v === 1 ? 4 : v;
      });

      Object.entries(marks.number || {}).forEach(function (pair) {
        const pos = parseRC(pair[0]);
        if (!pos) return;
        q.number[String(cellIndex(pos.r, pos.c))] = [String(pair[1]), 1, "1"];
      });

      Object.entries(marks.text || {}).forEach(function (pair) {
        const pos = parseRC(pair[0]);
        if (!pos) return;
        q.number[String(cellIndex(pos.r, pos.c))] = [String(pair[1]), 1, "1"];
      });

      Object.entries(drawing.cornerNumbers || {}).forEach(function ([key, value]) {
        const pos = parseRC(key);
        if (!pos) return;
        q.numberS[String(4 * (cellIndex(pos.r, pos.c) + pu.nx0 * pu.ny0))] = [String(value), 1];
      });

      const cages = new Map();
      Object.entries(drawing.cages || {}).forEach(function ([key, value]) {
        const pos = parseRC(key);
        if (!pos) return;
        if (!cages.has(value)) cages.set(value, []);
        cages.get(value).push(cellIndex(pos.r, pos.c));
      });
      if (cages.size) {
        q.killercages = [...cages.values()];
        for (const cells of q.killercages) {
          for (const segments of pu.cage_for_selection(cells)) {
            for (const segment of segments) q.cage[segment] = 10;
          }
        }
      }

      Object.entries(marks.arrow || {}).forEach(function (pair) {
        const pos = parseRC(pair[0]);
        if (!pos) return;
        const idx = String(cellIndex(pos.r, pos.c));
        const suffix = OURS_DIR_TO_PENPA[String(pair[1])] || "0";
        const existing = q.number[idx];
        const prefix = existing ? String(existing[0]).split("_")[0] : "";
        q.number[idx] = [(prefix || "") + "_" + suffix, 1, "2"];
      });

      Object.keys(SYMBOL_STAMP).forEach(function (tool) {
        Object.entries(marks[tool] || {}).forEach(function (pair) {
          const pos = parseRC(pair[0]);
          if (!pos) return;
          q.symbol[String(cellIndex(pos.r, pos.c))] = SYMBOL_STAMP[tool](pair[1]);
        });
      });

      Object.entries(marks.dot || {}).forEach(function ([key, value]) {
        const e = parseEdge(key);
        if (!e || !Number(value)) return;
        const index = edgeCenterIndex(e);
        if (index !== null) q.symbol[String(index)] = [Number(value), 'circle_M', 1];
      });

      Object.entries(marks.diagonal || {}).forEach(function ([key, value]) {
        const pos = parseRC(key);
        if (!pos || (Number(value) !== 1 && Number(value) !== 2)) return;
        const a = cornerIndex(pos.r, pos.c + (Number(value) === 2 ? 1 : 0));
        const b = cornerIndex(pos.r + 1, pos.c + (Number(value) === 1 ? 1 : 0));
        q.lineE[Math.min(a, b) + ',' + Math.max(a, b)] = 2;
      });

      Object.entries(marks.edgeline || {}).forEach(function (pair) {
        const e = parseEdge(pair[0]);
        if (!e) return;
        const a = cornerIndex(e.r, e.c);
        const b = e.orient === "H" ? cornerIndex(e.r, e.c + 1) : cornerIndex(e.r + 1, e.c);
        q.lineE[a + "," + b] = 2;
      });

      Object.entries(marks.link || {}).forEach(function (pair) {
        const e = parseEdge(pair[0]);
        if (!e) return;
        const a = e.orient === "V" ? cellIndex(e.r, e.c - 1) : cellIndex(e.r - 1, e.c);
        const b = e.orient === "V" ? cellIndex(e.r, e.c) : cellIndex(e.r, e.c);
        q.line[a + "," + b] = 3;
      });

      const outside = drawing.outside || {};
      ["top", "bottom", "left", "right"].forEach(function (side) {
        Object.entries(outside[side] || {}).forEach(function (pair) {
          const i = Number(pair[0]);
          const v = pair[1];
          if (!Number.isInteger(i) || v === undefined || v === null || Number(v) < 0) return;
          let pr, pc;
          if (side === "top") {
            pr = 1 + (pu.space[0] || 0);
            pc = i + 2 + (pu.space[2] || 0);
          } else if (side === "bottom") {
            pr = 2 + rows + (pu.space[0] || 0);
            pc = i + 2 + (pu.space[2] || 0);
          } else if (side === "left") {
            pr = i + 2 + (pu.space[0] || 0);
            pc = 1 + (pu.space[2] || 0);
          } else {
            pr = i + 2 + (pu.space[0] || 0);
            pc = 2 + cols + (pu.space[2] || 0);
          }
          q.number[String(pr * pu.nx0 + pc)] = [String(Array.isArray(v) ? v.join(" ") : v), 1, "1"];
        });
      });

      const regions = drawing.regions || {};
      for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
        const value = regions[r + ',' + c];
        if (value === undefined) continue;
        if (c + 1 < cols && regions[r + ',' + (c + 1)] !== undefined && value !== regions[r + ',' + (c + 1)])
          q.lineE[edgePair('V,' + r + ',' + (c + 1), false)] = 2;
        if (r + 1 < rows && regions[(r + 1) + ',' + c] !== undefined && value !== regions[(r + 1) + ',' + c])
          q.lineE[edgePair('H,' + (r + 1) + ',' + c, false)] = 2;
      }

      if (typeof pu.redraw === "function") pu.redraw();
      notify();
      return true;
    } catch (err) {
      console.error("penpa stamp", err);
      return false;
    }
  }

  function setTool(tool) {
    if (!window.pu) return;
    const mode = TOOL_MODE[tool] || "surface";
    pu.mode_set(mode);
    if (mode === "symbol" && SYMBOL_SUB[tool] && typeof pu.subsymbolmode === "function") {
      try {
        pu.subsymbolmode(SYMBOL_SUB[tool]);
      } catch (err) {
        /* some families are named differently across versions */
      }
    }
    if (tool === 'dot') pu.type = [2, 3];
    if (tool === 'diagonal' && typeof pu.submode_check === 'function') pu.submode_check('sub_lineE2');
    else if ((tool === 'edgeline' || tool === 'region') && typeof pu.submode_check === 'function') pu.submode_check('sub_lineE1');
  }

  function setHidden(keys, hide) {
    if (!window.pu) return;
    installPresentation();
    (keys || []).forEach(key => { if (hide) hidden[key] = true; else delete hidden[key]; });
    pu.redraw();
  }

  function edgeCenterIndex(e) {
    const size = innerSize();
    if (e.r < 0 || e.c < 0 || (e.orient === 'H' ? e.r > size.rows || e.c >= size.cols : e.r >= size.rows || e.c > size.cols)) return null;
    // Native type 2 sits below a cell; type 3 sits to its right. H/V name
    // the lattice edge itself, matching lineE and the DSL edge convention.
    const horizontal = e.orient === 'H';
    const pr = e.r + (horizontal ? 1 : 2) + (pu.space[0] || 0);
    const pc = e.c + (horizontal ? 2 : 1) + (pu.space[2] || 0);
    return (horizontal ? 2 : 3) * pu.nx0 * pu.ny0 + pr * pu.nx0 + pc;
  }

  function edgePair(key, link) {
    const e = parseEdge(key);
    if (!e) return null;
    const size = innerSize();
    if (e.r < 0 || e.c < 0) return null;
    if (e.orient === 'H' ? e.r > size.rows || e.c >= size.cols : e.r >= size.rows || e.c > size.cols) return null;
    let a, b;
    if (link) {
      if (e.orient === 'H' ? e.r === 0 || e.r === size.rows : e.c === 0 || e.c === size.cols) return null;
      a = e.orient === 'V' ? cellIndex(e.r, e.c - 1) : cellIndex(e.r - 1, e.c);
      b = cellIndex(e.r, e.c);
    } else {
      a = cornerIndex(e.r, e.c);
      b = e.orient === 'H' ? cornerIndex(e.r, e.c + 1) : cornerIndex(e.r + 1, e.c);
    }
    return Math.min(a, b) + ',' + Math.max(a, b);
  }

  function applySolution(element, values, palette = {}, id = element) {
    if (!window.pu || !values) return false;
    installPresentation();
    const fields = {};
    const put = (field, key, value) => { if (key !== null) (fields[field] ||= {})[key] = value; };
    const size = innerSize();
    if (element === 'region') {
      for (let r = 0; r < size.rows; r++) for (let c = 0; c < size.cols; c++) {
        const value = values[r + ',' + c];
        if (value === undefined) continue;
        if (c + 1 < size.cols && values[r + ',' + (c + 1)] !== undefined && value !== values[r + ',' + (c + 1)])
          put('lineE', edgePair('V,' + r + ',' + (c + 1), false), 3);
        if (r + 1 < size.rows && values[(r + 1) + ',' + c] !== undefined && value !== values[(r + 1) + ',' + c])
          put('lineE', edgePair('H,' + (r + 1) + ',' + c, false), 3);
      }
    } else if (element === 'link' || element === 'edgeline') {
      for (const [key, value] of Object.entries(values)) if (value)
        put(element === 'link' ? 'line' : 'lineE', edgePair(key, element === 'link'), 3);
    } else if (element === 'number' || element === 'shade' || SYMBOL_STAMP[element]) {
      for (const [key, value] of Object.entries(values)) {
        const pos = parseRC(key);
        if (!pos || pos.r < 0 || pos.c < 0 || pos.r >= size.rows || pos.c >= size.cols) continue;
        const index = String(cellIndex(pos.r, pos.c));
        if (element === 'number') put('number', index, [String(value), 2, '1']);
        else if (element === 'shade' && value) put('surface', index, 4);
        else if (element === 'circle' && (value || Object.hasOwn(palette, value))) {
          const color = String(palette[value] || '').toLowerCase();
          const sid = color === '#ffffff' ? 1 : color === '#232733' ? 2 : Number(value) || 1;
          put('symbol', index, [sid, 'circle_M', 1]);
        } else if (value && SYMBOL_STAMP[element]) put('symbol', index, SYMBOL_STAMP[element](value));
      }
    } else return false;
    solutions[id] = { element, fields };
    const vis = document.getElementById('visibility_button');
    if (vis && vis.textContent === 'OFF') vis.click();
    pu.redraw();
    notify();
    return true;
  }

  function clearSolution() {
    Object.keys(solutions).forEach(key => delete solutions[key]);
    if (window.pu) pu.redraw();
  }

  window.StudioBridge = {
    renameVariable, deleteVariable,
    variableCounts: () => {
      saveActive();
      return Object.fromEntries(Object.entries(documents).map(([id, q]) => [id, Object.entries(cloneMarks(q)).reduce((sum, [, marks]) => sum + (marks && typeof marks === 'object' ? Object.keys(marks).length : 0), 0)]));
    },
    loadDocuments,
    replaceDrawing,
    replaceDocuments,
    getSelection: () => ({ tool: currentTool(), activeVariable }),
    exportDocuments,
    selectVariable,
    getRevision: getRevision,
    isEmpty: isEmpty,
    resize: resize,
    occupancy: occupancy,
    stamp: stamp,
    exportUrl: exportUrl,
    setTool: setTool,
    setHidden: setHidden,
    applySolution: applySolution,
    clearSolution: clearSolution,
    notify: notify,
  };

  if (typeof boot === "function") {
    const originalBoot = boot;
    boot = async function () {
      disableCookies();
      try {
        await originalBoot.apply(this, arguments);
      } catch (err) {
        console.error("penpa boot", err);
      }
      window.parent.postMessage({ type: "penpa-ready", ...occupancy(), revision: getRevision() }, location.origin);
    };
  }

  window.addEventListener("load", function () {
    window.onbeforeunload = null;
    document.addEventListener("beforeunload", function (e) {
      e.stopImmediatePropagation();
    }, true);
    document.addEventListener("pointerdown", function (event) {
      if (event.target.id === "canvas") {
        event.target.tabIndex = 0;
        event.target.focus({ preventScroll: true });
      }
    }, true);
    document.addEventListener("mouseup", function () { setTimeout(notify, 30); }, { passive: true });
    document.addEventListener("keyup", function () { setTimeout(notify, 30); }, { passive: true });
    window.parent.postMessage({ type: "penpa-ready", ...occupancy(), revision: getRevision() }, location.origin);
    setInterval(notify, 800);
  });

})();
