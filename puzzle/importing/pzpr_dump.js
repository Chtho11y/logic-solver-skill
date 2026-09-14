#!/usr/bin/env node
/**
 * Dump a puzz.link / pzprjs board as JSON on stdout.
 *
 * Usage: node pzpr_dump.js '<pid>/<w>/<h>/<body>'
 *
 * Looks for the `pzpr` module on NODE_PATH, then next to this file, then
 * cwd/node_modules.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const Module = require("module");

function loadPzpr() {
  const candidates = [];
  if (process.env.NODE_PATH) {
    for (const dir of process.env.NODE_PATH.split(path.delimiter)) {
      if (dir) candidates.push(path.join(dir, "pzpr"));
    }
  }
  candidates.push(path.join(__dirname, "node_modules", "pzpr"));
  candidates.push(path.join(process.cwd(), "node_modules", "pzpr"));
  for (const dir of candidates) {
    try {
      return require(dir);
    } catch (_) {
      /* keep looking */
    }
  }
  return require("pzpr");
}

function openPuzzle(pzpr, src) {
  return new Promise((resolve, reject) => {
    const puzzle = new pzpr.Puzzle({ type: "player" });
    const timer = setTimeout(() => reject(new Error("pzprjs open timed out")), 15000);
    puzzle.on("ready", () => {
      clearTimeout(timer);
      resolve(puzzle);
    });
    puzzle.on("fail-open", (err) => {
      clearTimeout(timer);
      reject(err || new Error("pzprjs fail-open"));
    });
    try {
      puzzle.open(src);
    } catch (err) {
      clearTimeout(timer);
      reject(err);
    }
  });
}

function borderOrient(bd) {
  // Odd/even pzpr coordinates: vertical borders sit on even bx + odd by.
  if (bd.bx % 2 === 0 && bd.by % 2 === 1) return "V";
  if (bd.bx % 2 === 1 && bd.by % 2 === 0) return "H";
  return null;
}

function excellSide(cell, rows, cols) {
  const bx = cell.bx;
  const by = cell.by;
  if (by < 0) return { side: "top", index: (bx - 1) / 2 };
  if (by > 2 * rows) return { side: "bottom", index: (bx - 1) / 2 };
  if (bx < 0) return { side: "left", index: (by - 1) / 2 };
  if (bx > 2 * cols) return { side: "right", index: (by - 1) / 2 };
  return null;
}

async function main() {
  const src = process.argv[2];
  if (!src) {
    process.stderr.write("usage: pzpr_dump.js <pid/w/h/body>\n");
    process.exit(2);
  }
  const pzpr = loadPzpr();
  const puzzle = await openPuzzle(pzpr, src);
  const board = puzzle.board;
  const rows = board.rows;
  const cols = board.cols;
  const cells = [];
  board.cell.each((c) => {
    if (c.isnull) return;
    cells.push({
      r: (c.by - 1) / 2,
      c: (c.bx - 1) / 2,
      qnum: c.qnum,
      qnum2: c.qnum2,
      qdir: c.qdir,
      ques: c.ques,
      qans: c.qans,
      qsub: c.qsub,
      anum: c.anum,
    });
  });
  const borders = [];
  if (board.border && board.border.each) {
    board.border.each((bd) => {
      if (bd.isnull) return;
      const orient = borderOrient(bd);
      if (!orient) return;
      const r = orient === "V" ? (bd.by - 1) / 2 : bd.by / 2;
      const c = orient === "V" ? bd.bx / 2 : (bd.bx - 1) / 2;
      borders.push({
        orient,
        r,
        c,
        ques: bd.ques,
        qans: bd.qans,
        qsub: bd.qsub,
      });
    });
  }
  const excells = [];
  if (board.excell && board.excell.each) {
    board.excell.each((cell) => {
      if (cell.isnull) return;
      const placed = excellSide(cell, rows, cols);
      if (!placed) return;
      excells.push({
        side: placed.side,
        index: placed.index,
        qnum: cell.qnum,
        qdir: cell.qdir,
      });
    });
  }
  const payload = {
    pid: puzzle.pid,
    rows,
    cols,
    cells,
    borders,
    excells,
  };
  process.stdout.write(JSON.stringify(payload));
}

main().catch((err) => {
  process.stderr.write(String(err && err.stack ? err.stack : err) + "\n");
  process.exit(1);
});
