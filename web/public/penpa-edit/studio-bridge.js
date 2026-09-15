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
    diagonal: "line",
    dot: "lineE",
    region: "combi",
  };

  const SYMBOL_SUB = {
    circle: "circle_M",
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
    const hid = hidden[qa + "." + field];
    if (hid) return hid;
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
    counts.edgeline = countKeys(lineE);
    counts.diagonal = countKeys(wall);
    for (const index of Object.keys(numbers || {})) {
      if (classifyIndex(index).kind === "outside") counts.outside += 1;
      else counts.number += 1;
    }
    for (const entry of Object.values(symbols || {})) {
      if (!Array.isArray(entry) || entry.length < 2) continue;
      const family = String(entry[1]).toLowerCase();
      if (family.includes("circle") || (family.startsWith("ox") && (entry[0] === 1 || entry[0] === 2))) counts.circle += 1;
      else if (family.includes("square")) counts.square += 1;
      else if (family.includes("tri")) counts.triangle += 1;
      else if (family.includes("star")) counts.star += 1;
      else if (family.includes("cross") || family.startsWith("ox")) counts.cross += 1;
      else if (family.includes("tree")) counts.tree += 1;
      else if (family.includes("tent")) counts.tent += 1;
      else if (family.includes("ship") || family.includes("battleship")) counts.ship += 1;
      else if (family.includes("water") || family.includes("wave")) counts.wave += 1;
      else if (family.includes("sun") || family.includes("bulb") || family.includes("moon")) counts.bulb += 1;
      else if (family.includes("arrow")) counts.arrow += 1;
      else counts.circle += 1;
    }
    const mode = (pu.mode && pu.mode[pu.mode.qa] && pu.mode[pu.mode.qa].edit_mode) || "surface";
    return { rows: size.rows, cols: size.cols, counts: counts, mode: mode };
  }

  function notify() {
    const payload = occupancy();
    window.parent.postMessage({ type: "penpa-occupancy", ...payload }, "*");
  }

  function paramFromUrl(url) {
    let raw = String(url || "").trim();
    if (!raw) return "";
    const hash = raw.indexOf("#");
    if (hash >= 0) raw = raw.slice(hash + 1);
    else {
      const q = raw.indexOf("?");
      if (q >= 0 && /(?:^|[?&])p=/.test(raw.slice(q))) raw = raw.slice(q + 1);
    }
    raw = raw.replace(/^#/, "").replace(/^\?/, "");
    if (raw && raw.indexOf("p=") === -1) raw = "m=edit&p=" + raw;
    return raw;
  }

  function ensureCenterlist() {
    const pu = window.pu;
    if (!pu || !pu.nx0) return;
    pu.centerlist = [];
    const top = (pu.space && pu.space[0]) || 0;
    const bottom = (pu.space && pu.space[1]) || 0;
    const left = (pu.space && pu.space[2]) || 0;
    const right = (pu.space && pu.space[3]) || 0;
    for (let j = 2 + top; j < pu.ny0 - 2 - bottom; j++) {
      for (let i = 2 + left; i < pu.nx0 - 2 - right; i++) {
        pu.centerlist.push(i + j * pu.nx0);
      }
    }
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

  function restoreMarks(dest, src) {
    if (!dest || !src) return;
    Object.keys(src).forEach(function (key) {
      dest[key] = src[key];
    });
  }

  function repairCanvas() {
    const pu = window.pu;
    if (!pu || typeof pu.reset_frame !== "function") {
      ensureCenterlist();
      return;
    }
    const q = cloneMarks(pu.pu_q);
    const a = cloneMarks(pu.pu_a);
    try {
      pu.reset_frame();
      restoreMarks(pu.pu_q, q);
      restoreMarks(pu.pu_a, a);
      if (typeof pu.redraw === "function") pu.redraw();
    } catch (err) {
      console.error("penpa repair", err);
      ensureCenterlist();
      if (typeof pu.redraw === "function") pu.redraw();
    }
  }

  function loadUrl(url) {
    const param = paramFromUrl(url);
    if (!param || typeof load !== "function") return false;
    function after() {
      repairCanvas();
      notify();
    }
    try {
      const result = load(param);
      if (result && typeof result.then === "function") {
        result.then(after).catch(function (err) {
          console.error("penpa load", err);
          after();
        });
      } else {
        after();
      }
    } catch (err) {
      console.error("penpa load", err);
      after();
    }
    return true;
  }

  function exportUrl() {
    if (!window.pu || typeof pu.maketext !== "function") return "";
    return pu.maketext();
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

  function stamp(drawing) {
    if (!drawing || !window.pu || typeof create_newboard !== "function") return false;
    try {
      Object.keys(hidden).forEach(function (k) { delete hidden[k]; });
      const rows = Math.max(1, Math.min(40, Number(drawing.rows) || 10));
      const cols = Math.max(1, Math.min(40, Number(drawing.cols) || 10));
      if (!setSize(rows, cols, true)) return false;
      const pu = window.pu;
      if (!pu || !pu.pu_q) return false;
      const q = pu.pu_q;
      ["surface", "number", "symbol", "line", "lineE"].forEach(function (field) {
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
          q.number[String(pr * pu.nx0 + pc)] = [String(Array.isArray(v) ? v[0] : v), 1, "1"];
        });
      });

      const groups = {};
      Object.entries(drawing.regions || {}).forEach(function (pair) {
        const pos = parseRC(pair[0]);
        if (!pos) return;
        const id = String(pair[1]);
        (groups[id] = groups[id] || []).push(cellIndex(pos.r, pos.c));
      });
      const cages = Object.keys(groups).map(function (id) { return groups[id]; });
      if (cages.length) q.killercages = cages;

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
  }

  function fieldFor(key) {
    if (key.indexOf("out:") === 0) {
      const el = key.slice(4);
      if (el === "number" || el === "text") return { qa: "pu_a", field: "number" };
      if (el === "link") return { qa: "pu_a", field: "line" };
      if (el === "edgeline" || el === "dot") return { qa: "pu_a", field: "lineE" };
      return { qa: "pu_a", field: "surface" };
    }
    if (key === "shade") return { qa: "pu_q", field: "surface" };
    if (key === "link") return { qa: "pu_q", field: "line" };
    if (key === "edgeline" || key === "dot") return { qa: "pu_q", field: "lineE" };
    if (key === "diagonal") return { qa: "pu_q", field: "wall" };
    const symbols = [
      "circle", "square", "triangle", "star", "cross", "tree", "tent", "ship", "wave", "bulb", "arrow",
    ];
    if (symbols.indexOf(key) >= 0) return { qa: "pu_q", field: "symbol" };
    if (key === "number" || key === "text" || key === "outside") return { qa: "pu_q", field: "number" };
    return null;
  }

  function setHidden(keys, hide) {
    if (!window.pu) return;
    (keys || []).forEach(function (key) {
      const spec = fieldFor(key);
      if (!spec) return;
      const bucket = pu[spec.qa];
      if (!bucket) return;
      const storeKey = spec.qa + "." + spec.field;
      if (hide) {
        if (!hidden[storeKey]) hidden[storeKey] = Object.assign({}, bucket[spec.field] || {});
        bucket[spec.field] = {};
      } else if (hidden[storeKey]) {
        bucket[spec.field] = hidden[storeKey];
        delete hidden[storeKey];
      }
    });
    pu.redraw();
  }

  function applySolution(element, values) {
    if (!window.pu || !values) return;
    const dest = element === "number" ? pu.pu_a.number : pu.pu_a.surface;
    if (!dest) return;
    Object.keys(dest).forEach(function (k) { delete dest[k]; });
    Object.entries(values).forEach(function (pair) {
      const key = pair[0];
      const value = pair[1];
      const parts = key.split(",");
      if (parts.length !== 2) return;
      const index = String(cellIndex(Number(parts[0]), Number(parts[1])));
      if (element === "number") {
        dest[index] = [String(value), 2, "1"];
      } else if (value) {
        dest[index] = value === 1 ? 4 : Number(value);
      }
    });
    if (typeof UserSettings !== "undefined") {
      /* keep solution overlay visible */
    }
    const vis = document.getElementById("visibility_button");
    if (vis && vis.textContent === "OFF") vis.click();
    pu.redraw();
    notify();
  }

  function clearSolution() {
    if (!window.pu) return;
    ["surface", "number", "symbol", "line", "lineE"].forEach(function (field) {
      if (pu.pu_a && pu.pu_a[field] && typeof pu.pu_a[field] === "object" && !Array.isArray(pu.pu_a[field])) {
        Object.keys(pu.pu_a[field]).forEach(function (k) { delete pu.pu_a[field][k]; });
      }
    });
    pu.redraw();
  }

  window.StudioBridge = {
    occupancy: occupancy,
    loadUrl: loadUrl,
    stamp: stamp,
    exportUrl: exportUrl,
    setSize: setSize,
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
      window.parent.postMessage({ type: "penpa-ready", ...occupancy() }, "*");
    };
  }

  window.addEventListener("load", function () {
    window.onbeforeunload = null;
    document.addEventListener("beforeunload", function (e) {
      e.stopImmediatePropagation();
    }, true);
    const canvas = document.getElementById("canvas");
    if (canvas) {
      ["mouseup", "touchend", "keyup"].forEach(function (ev) {
        canvas.addEventListener(ev, function () { setTimeout(notify, 30); }, { passive: true });
      });
    }
    document.addEventListener("mouseup", function () { setTimeout(notify, 30); }, { passive: true });
    document.addEventListener("keyup", function () { setTimeout(notify, 30); }, { passive: true });
    window.parent.postMessage({ type: "penpa-ready", ...occupancy() }, "*");
    setInterval(notify, 800);
  });

  window.addEventListener("message", function (event) {
    const data = event.data || {};
    const api = window.StudioBridge;
    if (!api || !data || !data.type) return;
    if (data.type === "penpa-load") api.loadUrl(data.url);
    if (data.type === "penpa-stamp") api.stamp(data.drawing);
    if (data.type === "penpa-size") api.setSize(data.rows, data.cols);
    if (data.type === "penpa-tool") api.setTool(data.tool);
    if (data.type === "penpa-hide") api.setHidden(data.keys, data.hide);
    if (data.type === "penpa-solution") api.applySolution(data.element, data.values);
    if (data.type === "penpa-clear-solution") api.clearSolution();
    if (data.type === "penpa-export") {
      window.parent.postMessage({ type: "penpa-exported", url: api.exportUrl(), requestId: data.requestId }, "*");
    }
  });
})();
