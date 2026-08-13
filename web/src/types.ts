/**
 * Wire types shared with the Python backend.
 *
 * The front-end is deliberately puzzle-agnostic: it only ever knows about the
 * generic *elements* (number / shade / circle / arrow / link / ...) and the
 * *layers* that bind an element to a solver variable. Adding a new rule to the
 * backend therefore requires no change here.
 */

export type PointKind = "cell" | "corner" | "edge";
export type LayerTarget = PointKind | "outside";
export type LayerRole = "input" | "output";

/** Point keys are the serialised form used by the API: "r,c" or "H,r,c". */
export type PointKey = string;

/**
 * Catalogue ids (`number`, `shade`, `link`, …) plus any custom element id
 * declared on a spec layer. Unknown ids fall back to a numbered marker.
 */
export type ElementId = string;

export interface ElementType {
  id: ElementId;
  label: string;
  targets: LayerTarget[];
  doc: string;
  values: Record<string, string>;
  editor: "cycle" | "int" | "text" | "paint" | "toggle" | "direction";
}

export interface LayerSpec {
  id: string;
  label: string;
  element: ElementId;
  target: LayerTarget;
  role: LayerRole;
  /** Solver variable this layer draws (empty for `outside` layers). */
  var: string;
  /** Instance parameter this layer edits (`outside` layers only). */
  param: string;
  palette: Record<string, string>;
  options: Record<string, unknown>;
}

export interface VarSpec {
  name: string;
  kind: PointKind;
  type: "normal" | "cc" | "constant";
  domain: [number, number] | null;
  doc: string;
  /** A constant expected to have a value at every point (e.g. Hitori). */
  dense: boolean;
}

export interface PuzzleSpec {
  key: string;
  en: string;
  zh: string;
  category: string;
  subcategory: string;
  rule: string;
  aliases: string[];
  defaultRows: number;
  defaultCols: number;
  usesRegions: boolean;
  variables: VarSpec[];
  layers: LayerSpec[];
  params: Record<string, unknown>;
  notes: string;
  /** Only present on the single-puzzle endpoint. */
  source?: string;
}

export interface Instance {
  puzzle: string;
  rows: number;
  cols: number;
  /** variable name -> point key -> value */
  clues: Record<string, Record<PointKey, number>>;
  /** cell key -> region id */
  regions: Record<PointKey, number>;
  params: Record<string, unknown>;
  title: string;
}

export type SolveStatus = "sat" | "unsat" | "unknown" | "error" | "compiled";

export interface SolveResult {
  status: SolveStatus;
  message: string;
  constraints: number;
  debug: string[];
  errorLine?: number;
  /** variable name -> point key -> value (only when status === "sat"). */
  values?: Record<string, Record<PointKey, number>>;
  kinds?: Record<string, PointKind>;
}

export interface RuleEntry {
  key: string;
  en: string;
  zh: string;
  category: string;
  subcategory: string;
  rule: string;
  week: string;
  included: string;
  implemented: boolean;
  score?: number;
}

/** Region id used by the editor's region-painting layer. */
export const REGION_VAR = "__regions";

/** What the user is currently keyboard-editing. */
export type Selection =
  | { kind: "point"; layerId: string; key: PointKey }
  | { kind: "outside"; layerId: string; side: string; index: number };

/** The active stamp: a value, click-to-cycle, or the eraser. */
export type Brush = number | "cycle" | "erase";
