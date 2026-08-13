/** Editing behaviour per element id (frontend-side mirror of the catalogue). */

import type { LayerSpec } from "./types";

export type EditorKind =
  | "paint"      // drag to fill cells (shade / region)
  | "cycle"      // click to cycle marker values
  | "int"        // select a cell, type a number
  | "text"       // select a cell, type a letter
  | "toggle"     // click/drag lattice edges or cell links
  | "direction"  // pick an arrow direction, click to stamp
  | "outside"    // edit clues around the board
  | "none";

export const EDITOR_OF: Record<string, EditorKind> = {
  number: "int",
  text: "text",
  shade: "paint",
  region: "paint",
  circle: "cycle",
  square: "cycle",
  triangle: "cycle",
  star: "cycle",
  cross: "cycle",
  dot: "cycle",
  diagonal: "cycle",
  arrow: "direction",
  edgeline: "toggle",
  link: "toggle",
  outside: "outside",
  tree: "cycle",
  tent: "cycle",
  ship: "cycle",
  wave: "cycle",
  bulb: "cycle",
};

const EDITOR_KINDS = new Set<EditorKind>([
  "paint", "cycle", "int", "text", "toggle", "direction", "outside", "none",
]);

export function editorOf(layer: LayerSpec): EditorKind {
  const override = layer.options?.editor;
  if (typeof override === "string" && EDITOR_KINDS.has(override as EditorKind)) {
    return override as EditorKind;
  }
  return EDITOR_OF[layer.element] ?? "cycle";
}

const DEFAULT_CYCLE: Record<string, number[]> = {
  circle: [1, 2, 3],
  square: [1, 2, 3],
  dot: [1, 2, 3],
  triangle: [1, 2, 3, 4],
  diagonal: [1, 2],
  star: [1],
  cross: [1],
  tree: [1],
  tent: [1],
  wave: [1],
  bulb: [1],
  ship: [1, 2, 3, 4, 5, 6],
  arrow: [0, 1, 2, 3, 4, 5, 6, 7],
};

/** The stampable values of a layer (palette buttons + click cycling order). */
export function cycleValues(layer: LayerSpec): number[] {
  const custom = layer.options?.cycle;
  if (Array.isArray(custom)) return custom.map(Number);
  if (layer.element === "shade") {
    const keys = Object.keys(layer.palette ?? {}).map(Number).filter((n) => n > 0);
    return keys.length ? keys.sort((a, b) => a - b) : [1];
  }
  return DEFAULT_CYCLE[layer.element] ?? [1];
}

/** Tint colour for a region id (stable, readable pastels). */
export function regionColor(id: number): string {
  return `hsl(${(id * 53 + 20) % 360} 62% 82%)`;
}

export const REGION_BRUSHES = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9];
