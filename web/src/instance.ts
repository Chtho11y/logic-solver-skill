/** Instance construction and layer/value plumbing shared by editor and viewer. */

import type {
  ElementId,
  GenericLayer,
  Instance,
  LayerSpec,
  LayerTarget,
  PointKey,
  PuzzleSpec,
  SolveResult,
} from "./types";
import { REGION_VAR } from "./types";

/** Transient spec used when a Penpa+ URL is decoded but not bound to a rule. */
export const LAYERS_PREVIEW_KEY = "_layers";

export function emptyInstance(spec: PuzzleSpec, rows?: number, cols?: number): Instance {
  const r = rows ?? spec.defaultRows;
  const c = cols ?? spec.defaultCols;
  const instance: Instance = {
    puzzle: spec.key,
    rows: r,
    cols: c,
    clues: {},
    regions: {},
    params: {},
    title: "",
  };
  for (const layer of spec.layers) {
    if (layer.role === "input" && layer.var && layer.var !== REGION_VAR) {
      instance.clues[layer.var] = {};
    }
  }
  if (spec.usesRegions) {
    for (let i = 0; i < r; i++) {
      for (let j = 0; j < c; j++) instance.regions[`${i},${j}`] = 0;
    }
  }
  for (const [name, value] of Object.entries(
    (spec.params?.defaults as Record<string, unknown>) ?? {},
  )) {
    instance.params[name] = value;
  }
  return instance;
}

export function setClue(
  instance: Instance,
  variable: string,
  key: PointKey,
  value: number | null,
): Instance {
  if (variable === REGION_VAR) {
    const regions = { ...instance.regions };
    if (value === null) delete regions[key];
    else regions[key] = value;
    return { ...instance, regions };
  }
  const clues = { ...instance.clues };
  const table = { ...(clues[variable] ?? {}) };
  if (value === null) delete table[key];
  else table[key] = value;
  clues[variable] = table;
  return { ...instance, clues };
}

/** The values a layer should draw: its clues, or the solved model for outputs. */
export function layerValues(
  layer: LayerSpec,
  instance: Instance,
  result: SolveResult | null,
): Record<PointKey, number> {
  if (!layer.var) return {};
  if (layer.var === REGION_VAR) return instance.regions;
  if (layer.role === "output") return result?.values?.[layer.var] ?? {};
  return instance.clues[layer.var] ?? {};
}

/** Layer visibility state, so the board can be inspected layer by layer. */
export function defaultVisibility(spec: PuzzleSpec): Record<string, boolean> {
  return Object.fromEntries(spec.layers.map((layer) => [layer.id, true]));
}

// -- outside clues (instance params, one list per side) -----------------------

export type OutsideValue = number | number[] | null;

export function paramEntry(instance: Instance, side: string, index: number): OutsideValue {
  const arr = instance.params[side];
  if (!Array.isArray(arr)) return null;
  const value = arr[index];
  if (value === undefined || value === null || value === -1) return null;
  return value as OutsideValue;
}

export function setParamEntry(
  instance: Instance,
  side: string,
  index: number,
  value: OutsideValue,
): Instance {
  const length = side === "top" || side === "bottom" ? instance.cols : instance.rows;
  const arr = Array.isArray(instance.params[side]) ? [...(instance.params[side] as unknown[])] : [];
  while (arr.length < length) arr.push(-1);
  arr[index] = value === null ? -1 : value;
  return { ...instance, params: { ...instance.params, [side]: arr } };
}

export function outsideText(value: OutsideValue): string {
  if (value === null) return "";
  return Array.isArray(value) ? value.join(" ") : String(value);
}

/** Clear every value of one layer (clues, regions or an outside side list). */
export function clearLayer(instance: Instance, layer: LayerSpec): Instance {
  if (layer.target === "outside") {
    const params = { ...instance.params };
    for (const side of (layer.options?.sides as string[]) ?? []) params[side] = [];
    return { ...instance, params };
  }
  if (layer.var === REGION_VAR) return { ...instance, regions: {} };
  if (!layer.var) return instance;
  return { ...instance, clues: { ...instance.clues, [layer.var]: {} } };
}

const SIDES = ["top", "bottom", "left", "right"] as const;

function asPointValues(values: GenericLayer["values"]): Record<PointKey, number> {
  const out: Record<PointKey, number> = {};
  for (const [key, value] of Object.entries(values)) {
    if (typeof value === "number") out[key] = value;
  }
  return out;
}

/** Build a drawable spec+instance from generic Penpa / puzz.link layers. */
export function previewFromLayers(data: {
  rows: number;
  cols: number;
  title?: string;
  layers: GenericLayer[];
}): { spec: PuzzleSpec; instance: Instance } {
  const layers: LayerSpec[] = data.layers.map((layer) => {
    const isRegions = layer.id === "regions" || layer.element === "region";
    const isOutside = layer.id === "outside" || layer.element === "outside";
    return {
      id: layer.id,
      label: layer.id,
      element: layer.element as ElementId,
      target: (layer.target as LayerTarget) || (isOutside ? "outside" : "cell"),
      role: "input",
      var: isRegions ? REGION_VAR : isOutside ? "" : layer.id,
      param: isOutside ? "outside" : "",
      palette: layer.element === "shade" ? { "1": "#232733" } : {},
      options: isOutside ? { sides: [...SIDES], mode: "int" } : {},
    };
  });
  const spec: PuzzleSpec = {
    key: LAYERS_PREVIEW_KEY,
    en: "Imported layers",
    zh: "导入图层",
    category: "导入",
    subcategory: "",
    rule: "Penpa+ / puzz.link 解码预览，尚未绑定到可求解的题型。",
    aliases: [],
    defaultRows: data.rows,
    defaultCols: data.cols,
    usesRegions: layers.some((layer) => layer.var === REGION_VAR),
    variables: [],
    layers,
    params: {},
    notes: "选择题型后再次导入，即可把这些图层绑定到求解器。",
    source: "",
  };
  const instance: Instance = {
    puzzle: LAYERS_PREVIEW_KEY,
    rows: data.rows,
    cols: data.cols,
    clues: {},
    regions: {},
    params: {},
    title: data.title ?? "",
  };
  for (const layer of data.layers) {
    if (layer.id === "regions" || layer.element === "region") {
      instance.regions = asPointValues(layer.values);
      continue;
    }
    if (layer.id === "outside" || layer.element === "outside") {
      for (const side of SIDES) {
        const raw = layer.values[side];
        if (Array.isArray(raw)) instance.params[side] = raw;
      }
      continue;
    }
    instance.clues[layer.id] = asPointValues(layer.values);
  }
  return { spec, instance };
}
