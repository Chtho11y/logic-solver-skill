#!/usr/bin/env node
/**
 * Dump a puzz.link / pzprjs board as JSON on stdout.
 *
 * Usage: node pzpr_dump.js '<pid>/[<flags>/]<w>/<h>/<body>'
 *
 * Uses the project's installed `pzpr`, or Node's configured module paths.
 * Decoding never installs or changes dependencies.
 */
"use strict";

function loadPzpr() {
  let resolved;
  try {
    resolved = require.resolve("pzpr", { paths: [__dirname, process.cwd()] });
  } catch (err) {
    throw new Error(
      "pzprjs dependency is unavailable; run 'npm --prefix puzzle/importing install' " +
      "from the project root, then retry the import"
    );
  }
  try {
    return require(resolved);
  } catch (err) {
    throw new Error(
      "pzprjs dependency could not load: " + err.message +
      "; reinstall with 'npm --prefix puzzle/importing install' from the project root"
    );
  }
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
  const parsed = pzpr.parser.parseURL(src);
  if (!parsed.pid || !pzpr.variety(parsed.pid).valid) {
    throw new Error("installed pzprjs does not support this puzzle type: " + src.split("/")[0]);
  }
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
      qnums: c.qnums,
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
    // A room graph alone is not enough: Shikaku, for example, partitions
    // answers. An edit-mode border tool identifies pre-drawn room borders.
    hasGivenRooms: !!(
      board.roommgr && board.roommgr.enabled &&
      puzzle.mouse.inputModes.edit.includes("border")
    ),
  };
  process.stdout.write(JSON.stringify(payload));
}

main().catch((err) => {
  process.stderr.write(String(err && err.message ? err.message : err) + "\n");
  process.exit(1);
});
