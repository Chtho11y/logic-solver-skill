/** Penpa-like drawing document. Puzzle specs index tools; they do not own the canvas. */

import type { ElementId, GenericLayer, LayerSpec, LayerTarget, PuzzleSpec } from "./types";
import { REGION_VAR } from "./types";

export const DRAW_TOOLS = [
  "shade",
  "number",
  "circle",
  "square",
  "triangle",
  "star",
  "cross",
  "tree",
  "tent",
  "ship",
  "wave",
  "bulb",
  "arrow",
  "edgeline",
  "link",
  "dot",
  "diagonal",
  "region",
  "outside",
  "text",
] as const;

export type DrawTool = (typeof DRAW_TOOLS)[number];

export type ToolGroupId =
  | "surface"
  | "number"
  | "symbol"
  | "line"
  | "edge"
  | "special"
  | "composite";

export type ToolDef = {
  id: DrawTool;
  group: ToolGroupId;
  label: string;
  hint: string;
  /** Penpa+ `pu` object this most closely matches. */
  penpa: string;
};

/** Surface colors aligned with Penpa+ `pu.pu.surface` values. */
export const SURFACE_COLORS: { value: number; hex: string; label: string }[] = [
  { value: 1, hex: "#cfcfcf", label: "灰" },
  { value: 8, hex: "#a0d0a0", label: "绿" },
  { value: 3, hex: "#ffb0b0", label: "红" },
  { value: 4, hex: "#000000", label: "黑" },
];

export const SURFACE_PALETTE: Record<string, string> = Object.fromEntries(
  SURFACE_COLORS.map((c) => [String(c.value), c.hex]),
);

export const TOOLS: ToolDef[] = [
  { id: "shade", group: "surface", label: "Surface", hint: "格子着色（Penpa surface）", penpa: "surface" },
  { id: "number", group: "number", label: "Number", hint: "数字线索", penpa: "number" },
  { id: "text", group: "number", label: "Text", hint: "任意文字", penpa: "number" },
  { id: "circle", group: "symbol", label: "Circle", hint: "1 白 / 2 黑", penpa: "symbol" },
  { id: "square", group: "symbol", label: "Square", hint: "方块", penpa: "symbol" },
  { id: "triangle", group: "symbol", label: "Triangle", hint: "三角", penpa: "symbol" },
  { id: "star", group: "symbol", label: "Star", hint: "星", penpa: "symbol" },
  { id: "cross", group: "symbol", label: "Cross", hint: "叉", penpa: "symbol" },
  { id: "tree", group: "symbol", label: "Tree", hint: "树", penpa: "symbol" },
  { id: "tent", group: "symbol", label: "Tent", hint: "帐篷", penpa: "symbol" },
  { id: "ship", group: "symbol", label: "Ship", hint: "船", penpa: "symbol" },
  { id: "wave", group: "symbol", label: "Wave", hint: "波", penpa: "symbol" },
  { id: "bulb", group: "symbol", label: "Bulb", hint: "灯泡", penpa: "symbol" },
  { id: "arrow", group: "special", label: "Arrow", hint: "0↑ 1↓ 2← 3→", penpa: "symbol" },
  { id: "link", group: "line", label: "Line", hint: "格心连线（Penpa line）", penpa: "line" },
  { id: "edgeline", group: "edge", label: "Edge", hint: "格边（Penpa lineE）", penpa: "lineE" },
  { id: "diagonal", group: "edge", label: "Diagonal", hint: "格内斜线", penpa: "line" },
  { id: "dot", group: "edge", label: "Dot", hint: "边中点", penpa: "lineE" },
  { id: "region", group: "composite", label: "Region", hint: "房间（可由 Edge 自动生成）", penpa: "combi" },
  { id: "outside", group: "composite", label: "Outside", hint: "盘外线索", penpa: "number" },
];

export const TOOL_BY_ID: Record<DrawTool, ToolDef> = Object.fromEntries(
  TOOLS.map((t) => [t.id, t]),
) as Record<DrawTool, ToolDef>;

export const GROUPS: { id: ToolGroupId; label: string }[] = [
  { id: "surface", label: "Surface" },
  { id: "number", label: "Number" },
  { id: "symbol", label: "Symbol" },
  { id: "line", label: "Line" },
  { id: "edge", label: "Edge" },
  { id: "special", label: "Arrow" },
  { id: "composite", label: "Combi" },
];

export const PRIMARY_TOOLS: DrawTool[] = [
  "shade",
  "number",
  "circle",
  "arrow",
  "link",
  "edgeline",
  "region",
  "outside",
];

export const MORE_TOOLS: DrawTool[] = [
  "text",
  "square",
  "triangle",
  "star",
  "cross",
  "tree",
  "tent",
  "ship",
  "wave",
  "bulb",
  "diagonal",
  "dot",
];

export const DRAW_Z_ORDER: DrawTool[] = [
  "shade",
  "region",
  "number",
  "text",
  "circle",
  "square",
  "triangle",
  "star",
  "cross",
  "tree",
  "tent",
  "ship",
  "wave",
  "bulb",
  "arrow",
  "diagonal",
  "dot",
  "edgeline",
  "link",
];

export const TOOL_TARGET: Record<DrawTool, LayerTarget> = {
  shade: "cell",
  number: "cell",
  text: "cell",
  circle: "cell",
  square: "cell",
  triangle: "cell",
  star: "cell",
  cross: "cell",
  tree: "cell",
  tent: "cell",
  ship: "cell",
  wave: "cell",
  bulb: "cell",
  arrow: "cell",
  diagonal: "cell",
  region: "cell",
  edgeline: "edge",
  link: "edge",
  dot: "edge",
  outside: "outside",
};

export type MarkValue = number | string;
export type Marks = Partial<Record<DrawTool, Record<string, MarkValue>>>;
export type OutsideMap = Record<string, Record<string, number | number[]>>;

export type Drawing = {
  rows: number;
  cols: number;
  marks: Marks;
  /** cell key → region id */
  regions: Record<string, number>;
  outside: OutsideMap;
  /** Active Penpa surface color when drawing shade. */
  surfaceColor: number;
};

export const DEFAULT_SIZE = 10;
export const SIDES = ["top", "bottom", "left", "right"] as const;

export function emptyDrawing(rows = DEFAULT_SIZE, cols = DEFAULT_SIZE): Drawing {
  return { rows, cols, marks: {}, regions: {}, outside: {}, surfaceColor: 1 };
}

export function isEmptyDrawing(d: Drawing): boolean {
  if (Object.keys(d.regions).length) return false;
  if (Object.values(d.outside).some((side) => Object.keys(side).length)) return false;
  return Object.values(d.marks).every((layer) => !layer || Object.keys(layer).length === 0);
}

export function posKey(r: number, c: number): string {
  return `${r},${c}`;
}

export function edgeKey(orient: "H" | "V", r: number, c: number): string {
  return `${orient},${r},${c}`;
}

export function parsePos(key: string): { r: number; c: number } | null {
  const [a, b] = key.split(",");
  const r = Number(a);
  const c = Number(b);
  if (!Number.isInteger(r) || !Number.isInteger(c)) return null;
  return { r, c };
}

export function getMark(d: Drawing, tool: DrawTool, key: string): MarkValue | undefined {
  return d.marks[tool]?.[key];
}

export function setMark(d: Drawing, tool: DrawTool, key: string, value: MarkValue | null): Drawing {
  if (tool === "region") {
    const regions = { ...d.regions };
    if (value === null || value === "") delete regions[key];
    else regions[key] = Number(value);
    return { ...d, regions };
  }
  const layer = { ...(d.marks[tool] ?? {}) };
  if (value === null || value === undefined || value === "") delete layer[key];
  else layer[key] = value;
  const marks = { ...d.marks };
  if (Object.keys(layer).length === 0) delete marks[tool];
  else marks[tool] = layer;
  return { ...d, marks };
}

export function clearTool(d: Drawing, tool: DrawTool): Drawing {
  if (tool === "region") return { ...d, regions: {} };
  if (tool === "outside") return { ...d, outside: {} };
  const marks = { ...d.marks };
  delete marks[tool];
  return { ...d, marks };
}

function keepKey(tool: DrawTool, key: string, rows: number, cols: number): boolean {
  if (tool === "edgeline" || tool === "link" || tool === "dot") {
    const parts = key.split(",");
    if (parts.length !== 3) return false;
    const orient = parts[0];
    const r = Number(parts[1]);
    const c = Number(parts[2]);
    if (orient === "H") return r >= 0 && r <= rows && c >= 0 && c < cols;
    if (orient === "V") return r >= 0 && r < rows && c >= 0 && c <= cols;
    return false;
  }
  const p = parsePos(key);
  return Boolean(p && p.r >= 0 && p.r < rows && p.c >= 0 && p.c < cols);
}

export function resizeDrawing(d: Drawing, rows: number, cols: number): Drawing {
  const marks: Marks = {};
  for (const [tool, layer] of Object.entries(d.marks)) {
    const next: Record<string, MarkValue> = {};
    for (const [k, v] of Object.entries(layer ?? {})) {
      if (keepKey(tool as DrawTool, k, rows, cols)) next[k] = v;
    }
    if (Object.keys(next).length) marks[tool as DrawTool] = next;
  }
  const regions: Record<string, number> = {};
  for (const [k, v] of Object.entries(d.regions)) {
    if (keepKey("region", k, rows, cols)) regions[k] = v;
  }
  const outside: OutsideMap = {};
  for (const [side, values] of Object.entries(d.outside)) {
    const max = side === "left" || side === "right" ? rows : cols;
    const clipped: Record<string, number | number[]> = {};
    for (const [i, v] of Object.entries(values)) {
      if (Number(i) >= 0 && Number(i) < max) clipped[i] = v;
    }
    if (Object.keys(clipped).length) outside[side] = clipped;
  }
  return { ...d, rows, cols, marks, regions, outside };
}

function asPointValues(values: GenericLayer["values"]): Record<string, number> {
  const out: Record<string, number> = {};
  for (const [key, value] of Object.entries(values)) {
    if (typeof value === "number") out[key] = value;
  }
  return out;
}

export function drawingFromGenericLayers(
  layers: GenericLayer[],
  rows: number,
  cols: number,
): Drawing {
  const d = emptyDrawing(rows, cols);
  for (const layer of layers) {
    if (layer.id === "regions" || layer.element === "region") {
      d.regions = asPointValues(layer.values);
      continue;
    }
    if (layer.id === "outside" || layer.element === "outside") {
      for (const side of SIDES) {
        const raw = layer.values[side];
        if (!Array.isArray(raw)) continue;
        const row: Record<string, number | number[]> = {};
        raw.forEach((value, i) => {
          if (value === undefined || value === null || value === -1) return;
          row[String(i)] = value as number;
        });
        if (Object.keys(row).length) d.outside[side] = row;
      }
      continue;
    }
    const tool = (layer.element === "shade" ? "shade" : layer.element) as DrawTool;
    if (!DRAW_TOOLS.includes(tool) || tool === "region" || tool === "outside") continue;
    const values = asPointValues(layer.values);
    if (!Object.keys(values).length) continue;
    d.marks[tool] = { ...(d.marks[tool] ?? {}), ...values };
  }
  return d;
}

export function drawingToGenericLayers(d: Drawing): GenericLayer[] {
  const layers: GenericLayer[] = [];
  for (const tool of DRAW_TOOLS) {
    if (tool === "region") {
      if (Object.keys(d.regions).length) {
        layers.push({ id: "regions", element: "region", target: "cell", values: d.regions });
      }
      continue;
    }
    if (tool === "outside") {
      const values: Record<string, unknown> = {};
      for (const side of SIDES) {
        const src = d.outside[side];
        if (!src) continue;
        const length = side === "top" || side === "bottom" ? d.cols : d.rows;
        const arr: Array<number | number[]> = Array.from({ length }, (_, i) => src[String(i)] ?? -1);
        if (arr.some((value) => value !== -1)) values[side] = arr;
      }
      if (Object.keys(values).length) {
        layers.push({ id: "outside", element: "outside", target: "outside", values });
      }
      continue;
    }
    const values = numericMarks(d.marks[tool]);
    if (!Object.keys(values).length) continue;
    layers.push({
      id: tool === "shade" ? "surface" : tool,
      element: tool,
      target: TOOL_TARGET[tool],
      values,
    });
  }
  return layers;
}

export function numericMarks(layer: Record<string, MarkValue> | undefined): Record<string, number> {
  const out: Record<string, number> = {};
  if (!layer) return out;
  for (const [key, value] of Object.entries(layer)) {
    if (typeof value === "number") {
      out[key] = value;
      continue;
    }
    const n = Number(value);
    if (Number.isFinite(n) && value.trim() !== "") out[key] = n;
  }
  return out;
}

export function outsideEntry(
  d: Drawing,
  side: string,
  index: number,
): number | number[] | null {
  const value = d.outside[side]?.[String(index)];
  if (value === undefined || value === null || value === -1) return null;
  return value;
}

export function setOutsideEntry(
  d: Drawing,
  side: string,
  index: number,
  value: number | number[] | null,
): Drawing {
  const outside = { ...d.outside };
  const row = { ...(outside[side] ?? {}) };
  if (value === null) delete row[String(index)];
  else row[String(index)] = value;
  if (Object.keys(row).length === 0) delete outside[side];
  else outside[side] = row;
  return { ...d, outside };
}

export function outsideText(value: number | number[] | null): string {
  if (value === null) return "";
  return Array.isArray(value) ? value.join(" ") : String(value);
}

/** Rebuild rooms from Edge (lineE) marks, matching Python `regions_from_walls`. */
export function regionsFromEdges(d: Drawing): Record<string, number> {
  const walls = d.marks.edgeline ?? {};
  const parent = new Map<string, string>();
  for (let r = 0; r < d.rows; r++) {
    for (let c = 0; c < d.cols; c++) {
      const k = posKey(r, c);
      parent.set(k, k);
    }
  }
  const find = (k: string): string => {
    let p = parent.get(k)!;
    while (p !== parent.get(p)) {
      parent.set(p, parent.get(parent.get(p)!)!);
      p = parent.get(p)!;
    }
    return p;
  };
  const union = (a: string, b: string) => {
    const ra = find(a);
    const rb = find(b);
    if (ra !== rb) parent.set(rb, ra);
  };
  for (let r = 0; r < d.rows; r++) {
    for (let c = 0; c < d.cols; c++) {
      if (c + 1 < d.cols && !walls[edgeKey("V", r, c + 1)]) {
        union(posKey(r, c), posKey(r, c + 1));
      }
      if (r + 1 < d.rows && !walls[edgeKey("H", r + 1, c)]) {
        union(posKey(r, c), posKey(r + 1, c));
      }
    }
  }
  const roots = new Map<string, number>();
  const out: Record<string, number> = {};
  let next = 0;
  for (let r = 0; r < d.rows; r++) {
    for (let c = 0; c < d.cols; c++) {
      const k = posKey(r, c);
      const root = find(k);
      if (!roots.has(root)) roots.set(root, next++);
      out[k] = roots.get(root)!;
    }
  }
  return out;
}

export function indexedInputLayers(spec: PuzzleSpec | null): LayerSpec[] {
  if (!spec) return [];
  return spec.layers.filter((layer) => layer.role === "input");
}

export function indexedTools(spec: PuzzleSpec | null): DrawTool[] {
  const tools: DrawTool[] = [];
  for (const layer of indexedInputLayers(spec)) {
    const tool = layer.element as DrawTool;
    if (DRAW_TOOLS.includes(tool) && !tools.includes(tool)) tools.push(tool);
  }
  return tools;
}

export function labelsForTool(spec: PuzzleSpec | null, tool: DrawTool): string[] {
  if (!spec) return [];
  return spec.layers
    .filter((layer) => layer.element === tool && layer.role === "input")
    .map((layer) => layer.label);
}

export function toolLayer(tool: DrawTool, spec?: PuzzleSpec | null): LayerSpec {
  const indexed = spec?.layers.find((layer) => layer.element === tool && layer.role === "input");
  const palette =
    tool === "shade"
      ? SURFACE_PALETTE
      : (indexed?.palette ?? {});
  return {
    id: tool,
    label: indexed?.label ?? TOOL_BY_ID[tool].label,
    element: tool as ElementId,
    target: indexed?.target ?? TOOL_TARGET[tool],
    role: "input",
    var: indexed?.var || (tool === "region" ? REGION_VAR : tool),
    param: indexed?.param ?? "",
    palette,
    options:
      indexed?.options ??
      (tool === "outside" ? { sides: [...SIDES], mode: "int" } : {}),
  };
}
