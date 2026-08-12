/**
 * Board geometry: point keys <-> coordinates, and the mapping from the three
 * lattices (cell / corner / edge) onto SVG space.
 *
 * Keeping this puzzle-agnostic is what lets one renderer draw every rule.
 */

import type { PointKey, PointKind } from "./types";

export interface CellPoint {
  kind: "cell" | "corner";
  r: number;
  c: number;
}

export interface EdgePoint {
  kind: "edge";
  orient: "H" | "V";
  r: number;
  c: number;
}

export type Point = CellPoint | EdgePoint;

export function parsePoint(key: PointKey, kind: PointKind): Point {
  const parts = key.split(",");
  if (kind === "edge") {
    return { kind: "edge", orient: parts[0] as "H" | "V", r: +parts[1], c: +parts[2] };
  }
  return { kind, r: +parts[0], c: +parts[1] };
}

export function cellKey(r: number, c: number): PointKey {
  return `${r},${c}`;
}

export function cornerKey(r: number, c: number): PointKey {
  return `${r},${c}`;
}

export function edgeKey(orient: "H" | "V", r: number, c: number): PointKey {
  return `${orient},${r},${c}`;
}

/** The "H" edge above cell (r, c) — i.e. the vertical link to cell (r-1, c). */
export const edgeAbove = (r: number, c: number) => edgeKey("H", r, c);
export const edgeBelow = (r: number, c: number) => edgeKey("H", r + 1, c);
export const edgeLeft = (r: number, c: number) => edgeKey("V", r, c);
export const edgeRight = (r: number, c: number) => edgeKey("V", r, c + 1);

export interface Viewport {
  rows: number;
  cols: number;
  /** Side of one cell in SVG units. */
  size: number;
  /** Margin reserved around the board for outside clues. */
  pad: number;
}

export function makeViewport(rows: number, cols: number, size = 40, pad = 40): Viewport {
  return { rows, cols, size, pad };
}

export function viewBox(v: Viewport): string {
  return `0 0 ${v.cols * v.size + v.pad * 2} ${v.rows * v.size + v.pad * 2}`;
}

/** Top-left corner of a cell in SVG coordinates. */
export function cellOrigin(v: Viewport, r: number, c: number) {
  return { x: v.pad + c * v.size, y: v.pad + r * v.size };
}

/** Centre of a cell. */
export function cellCentre(v: Viewport, r: number, c: number) {
  const o = cellOrigin(v, r, c);
  return { x: o.x + v.size / 2, y: o.y + v.size / 2 };
}

/** A lattice corner (r, c) in SVG coordinates. */
export function cornerPoint(v: Viewport, r: number, c: number) {
  return { x: v.pad + c * v.size, y: v.pad + r * v.size };
}

/** The two endpoints of a lattice edge — used to draw region borders / walls. */
export function edgeSegment(v: Viewport, orient: "H" | "V", r: number, c: number) {
  if (orient === "H") {
    return { x1: v.pad + c * v.size, y1: v.pad + r * v.size, x2: v.pad + (c + 1) * v.size, y2: v.pad + r * v.size };
  }
  return { x1: v.pad + c * v.size, y1: v.pad + r * v.size, x2: v.pad + c * v.size, y2: v.pad + (r + 1) * v.size };
}

/**
 * The segment joining the centres of the two cells an edge separates — used to
 * draw loops and paths that run through cell centres. Returns null on the
 * board boundary, where no such link exists.
 */
export function linkSegment(v: Viewport, orient: "H" | "V", r: number, c: number) {
  const a = orient === "H" ? { r: r - 1, c } : { r, c: c - 1 };
  const b = { r, c };
  const inside = (p: { r: number; c: number }) =>
    p.r >= 0 && p.r < v.rows && p.c >= 0 && p.c < v.cols;
  if (!inside(a) || !inside(b)) return null;
  const pa = cellCentre(v, a.r, a.c);
  const pb = cellCentre(v, b.r, b.c);
  return { x1: pa.x, y1: pa.y, x2: pb.x, y2: pb.y };
}

/** Hit-test an SVG point back to a cell (returns null outside the board). */
export function pickCell(v: Viewport, x: number, y: number) {
  const c = Math.floor((x - v.pad) / v.size);
  const r = Math.floor((y - v.pad) / v.size);
  if (r < 0 || r >= v.rows || c < 0 || c >= v.cols) return null;
  return { r, c };
}

/** Hit-test an SVG point to the nearest lattice corner. */
export function pickCorner(v: Viewport, x: number, y: number) {
  const c = Math.round((x - v.pad) / v.size);
  const r = Math.round((y - v.pad) / v.size);
  if (r < 0 || r > v.rows || c < 0 || c > v.cols) return null;
  return { r, c };
}

/**
 * Hit-test an SVG point to the nearest lattice edge: whichever of the four
 * borders of the containing cell the pointer is closest to.
 */
export function pickEdge(v: Viewport, x: number, y: number): EdgePoint | null {
  const cell = pickCell(v, x, y);
  if (!cell) return null;
  const o = cellOrigin(v, cell.r, cell.c);
  const dx = x - o.x;
  const dy = y - o.y;
  const candidates: Array<{ d: number; edge: EdgePoint }> = [
    { d: dy, edge: { kind: "edge", orient: "H", r: cell.r, c: cell.c } },
    { d: v.size - dy, edge: { kind: "edge", orient: "H", r: cell.r + 1, c: cell.c } },
    { d: dx, edge: { kind: "edge", orient: "V", r: cell.r, c: cell.c } },
    { d: v.size - dx, edge: { kind: "edge", orient: "V", r: cell.r, c: cell.c + 1 } },
  ];
  candidates.sort((a, b) => a.d - b.d);
  return candidates[0].edge;
}

/** All point keys of a lattice, in reading order. */
export function enumeratePoints(rows: number, cols: number, kind: PointKind): PointKey[] {
  const out: PointKey[] = [];
  if (kind === "cell") {
    for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) out.push(cellKey(r, c));
  } else if (kind === "corner") {
    for (let r = 0; r <= rows; r++) for (let c = 0; c <= cols; c++) out.push(cornerKey(r, c));
  } else {
    for (let r = 0; r <= rows; r++) for (let c = 0; c < cols; c++) out.push(edgeKey("H", r, c));
    for (let r = 0; r < rows; r++) for (let c = 0; c <= cols; c++) out.push(edgeKey("V", r, c));
  }
  return out;
}

/** Direction codes shared with the DSL (`UP`/`DOWN`/... constants). */
export const DIRECTIONS = [
  { code: 0, glyph: "↑", dr: -1, dc: 0 },
  { code: 1, glyph: "↓", dr: 1, dc: 0 },
  { code: 2, glyph: "←", dr: 0, dc: -1 },
  { code: 3, glyph: "→", dr: 0, dc: 1 },
  { code: 4, glyph: "↖", dr: -1, dc: -1 },
  { code: 5, glyph: "↗", dr: -1, dc: 1 },
  { code: 6, glyph: "↙", dr: 1, dc: -1 },
  { code: 7, glyph: "↘", dr: 1, dc: 1 },
] as const;
