/**
 * Host bridge for Logic Puzzle Studio. Same-origin iframe of Penpa+.
 * The parent React app talks through window.StudioBridge and postMessage.
 */
(function () {
  "use strict";

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

  function loadUrl(url) {
    const param = paramFromUrl(url);
    if (!param || typeof load !== "function") return false;
    load(param);
    notify();
    return true;
  }

  function exportUrl() {
    if (!window.pu || typeof pu.maketext !== "function") return "";
    return pu.maketext();
  }

  function setSize(rows, cols) {
    rows = Math.max(1, Math.min(40, Number(rows) || 10));
    cols = Math.max(1, Math.min(40, Number(cols) || 10));
    document.getElementById("nb_size1").value = String(cols);
    document.getElementById("nb_size2").value = String(rows);
    ["nb_space1", "nb_space2", "nb_space3", "nb_space4"].forEach(function (id) {
      const el = document.getElementById(id);
      if (el) el.value = "0";
    });
    if (window.UserSettings) UserSettings.gridtype = "square";
    if (typeof create_newboard === "function") create_newboard();
    notify();
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
    exportUrl: exportUrl,
    setSize: setSize,
    setTool: setTool,
    setHidden: setHidden,
    applySolution: applySolution,
    clearSolution: clearSolution,
    notify: notify,
  };

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
