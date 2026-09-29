/** Bind a Penpa-like drawing onto a PuzzleSpec instance (mirrors puzzle/importing/bind.py). */

import {
  DRAW_TOOLS,
  numericMarks,
  regionsFromEdges,
  SIDES,
  type DrawTool,
  type Drawing,
} from "./drawing";
import type { Instance, LayerSpec, PuzzleSpec } from "./types";
import { REGION_VAR } from "./types";

export function drawingParams(drawing: Drawing, spec: PuzzleSpec): Record<string, unknown> {
  const params: Record<string, unknown> = {};
  const defaults = (spec.params?.defaults as Record<string, unknown>) ?? {};
  Object.assign(params, defaults);
  // Standard skyscrapers uses the board width unless the instance overrides k.
  if (spec.key === "skyscrapers") params.k = drawing.cols;
  if (drawing.puzzle === spec.key) Object.assign(params, drawing.params);
  params.rows = drawing.rows;
  params.cols = drawing.cols;
  return params;
}

export function bindDrawing(drawing: Drawing, spec: PuzzleSpec): Instance {
  const clues: Record<string, Record<string, number>> = {};
  const params = drawingParams(drawing, spec);

  let regions = { ...drawing.regions };
  if (spec.usesRegions && Object.keys(regions).length === 0) {
    regions = regionsFromEdges(drawing);
  }

  let usedNumbersFor: string | null = null;
  for (const layer of spec.layers) {
    if (layer.role !== "input") continue;
    if (layer.target === "outside") {
      const wanted = new Set((layer.options?.sides as string[]) ?? SIDES);
      for (const side of SIDES) {
        if (!wanted.has(side)) continue;
        const length = side === "top" || side === "bottom" ? drawing.cols : drawing.rows;
        const src = drawing.outside[side] ?? {};
        const arr: Array<number | number[]> = Array.from({ length }, (_, i) => {
          const value = src[String(i)];
          if (value === undefined || value === null || value === -1) return -1;
          return value;
        });
        params[side] = arr;
      }
      continue;
    }
    if (layer.var === REGION_VAR || layer.element === "region") continue;
    if (!layer.var) continue;
    const values = valuesForLayer(layer, drawing, usedNumbersFor);
    if (layer.element === "number" && Object.keys(values).length) {
      usedNumbersFor = layer.var;
    }
    clues[layer.var] = { ...(clues[layer.var] ?? {}), ...values };
  }

  if (spec.key === "akari") {
    const walls = { ...(clues.w ?? {}) };
    for (const key of Object.keys(clues.n ?? {})) walls[key] = 1;
    clues.w = walls;
  }
  if (spec.key === "yajilin") {
    const numbers = { ...(clues.n ?? {}) };
    for (const key of Object.keys(clues.d ?? {})) {
      if (numbers[key] === undefined) numbers[key] = 0;
    }
    clues.n = numbers;
  }

  return {
    puzzle: spec.key,
    rows: drawing.rows,
    cols: drawing.cols,
    clues,
    regions,
    params,
    title: drawing.title,
  };
}

export function valuesForLayer(
  layer: LayerSpec,
  drawing: Drawing,
  usedNumbersFor: string | null,
): Record<string, number> {
  const element = layer.element as DrawTool;
  if (element === "number") {
    const nums = numericMarks(drawing.marks.number);
    if (usedNumbersFor && usedNumbersFor !== layer.var) {
      const arrows = drawing.marks.arrow ?? {};
      const out: Record<string, number> = {};
      for (const [key, value] of Object.entries(nums)) {
        if (arrows[key] !== undefined) out[key] = value;
      }
      return out;
    }
    return nums;
  }
  if (element === "circle" && Object.hasOwn(layer.palette ?? {}, "0")) {
    return Object.fromEntries(Object.entries(numericMarks(drawing.marks.circle)).map(([key, value]) => [key, value - 1]));
  }
  if (element === "shade") {
    const out: Record<string, number> = {};
    for (const [key, value] of Object.entries(drawing.marks.shade ?? {})) {
      if (value) out[key] = 1;
    }
    return out;
  }
  if (element === "text") {
    const out: Record<string, number> = {};
    for (const [key, value] of Object.entries(drawing.marks.text ?? {})) {
      if (typeof value === "number") {
        out[key] = value;
        continue;
      }
      const letter = value.trim().slice(-1).toUpperCase();
      const code = letter.charCodeAt(0) - 64;
      if (code >= 1 && code <= 26) out[key] = code;
    }
    return out;
  }
  if (!DRAW_TOOLS.includes(element) || element === "region" || element === "outside") {
    return {};
  }
  return numericMarks(drawing.marks[element]);
}

export function instanceToDrawing(instance: Instance, spec: PuzzleSpec): Drawing {
  const drawing: Drawing = {
    rows: instance.rows,
    cols: instance.cols,
    marks: {},
    regions: { ...instance.regions },
    outside: {},
    surfaceColor: 1,
    puzzle: spec.key,
    params: structuredClone(instance.params ?? {}),
    title: instance.title ?? "",
  };
  for (const layer of spec.layers) {
    if (layer.role !== "input") continue;
    if (layer.target === "outside") {
      for (const side of SIDES) {
        const arr = instance.params[side];
        if (!Array.isArray(arr)) continue;
        const row: Record<string, number | number[]> = {};
        arr.forEach((value, i) => {
          if (value === undefined || value === null || value === -1) return;
          row[String(i)] = value as number | number[];
        });
        if (Object.keys(row).length) drawing.outside[side] = row;
      }
      continue;
    }
    if (layer.var === REGION_VAR || layer.element === "region") {
      drawing.regions = { ...instance.regions };
      continue;
    }
    if (!layer.var) continue;
    const tool = layer.element as DrawTool;
    if (!DRAW_TOOLS.includes(tool)) continue;
    const raw = instance.clues[layer.var] ?? {};
    const values = tool === "circle" && Object.hasOwn(layer.palette ?? {}, "0")
      ? Object.fromEntries(Object.entries(raw).map(([key, value]) => [key, value + 1])) : raw;
    if (!Object.keys(values).length) continue;
    drawing.marks[tool] = { ...(drawing.marks[tool] ?? {}), ...values };
  }
  return drawing;
}
