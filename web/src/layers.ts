/** Occupied board layers: one row per solver variable (or unbound drawing tool). */

import { valuesForLayer } from "./bind";
import {
  DRAW_TOOLS,
  SIDES,
  TOOL_BY_ID,
  numericMarks,
  type DrawTool,
  type Drawing,
} from "./drawing";
import type { PuzzleSpec, SolveResult } from "./types";
import { REGION_VAR } from "./types";

export type OccupiedLayer = {
  id: string;
  /** Variable name, or the drawing-tool id when unbound. */
  title: string;
  detail: string;
  count: number;
  tool: DrawTool;
  hideKeys: string[];
  role: "input" | "output" | "drawing";
};

export type LayerCounts = Partial<Record<DrawTool, number>>;

function markCount(drawing: Drawing, tool: DrawTool): number {
  if (tool === "region") return Object.keys(drawing.regions).length;
  if (tool === "outside") {
    let n = 0;
    for (const side of SIDES) n += Object.keys(drawing.outside[side] ?? {}).length;
    return n;
  }
  return Object.keys(numericMarks(drawing.marks[tool])).length;
}

function firstTool(spec: PuzzleSpec, varName: string): DrawTool {
  const layer = spec.layers.find((item) => item.var === varName);
  const tool = layer?.element as DrawTool | undefined;
  if (tool && DRAW_TOOLS.includes(tool)) return tool;
  if (varName === REGION_VAR) return "region";
  return "number";
}

function countOf(tool: DrawTool, drawing: Drawing, counts?: LayerCounts): number {
  if (counts && typeof counts[tool] === "number") return counts[tool] ?? 0;
  return markCount(drawing, tool);
}

export function occupiedLayers(
  drawing: Drawing,
  spec: PuzzleSpec | null,
  result: SolveResult | null,
  counts?: LayerCounts,
): OccupiedLayer[] {
  const rows: OccupiedLayer[] = [];
  const claimed = new Set<DrawTool>();

  if (spec) {
    for (const variable of spec.variables) {
      const inputs = spec.layers.filter((layer) => layer.var === variable.name && layer.role === "input");
      const outputs = spec.layers.filter((layer) => layer.var === variable.name && layer.role === "output");
      let count = 0;
      const hideKeys: string[] = [];
      let tool: DrawTool = firstTool(spec, variable.name);
      let role: OccupiedLayer["role"] = "input";

      for (const layer of inputs) {
        const element = layer.element as DrawTool;
        if (layer.target === "outside") {
          count += countOf("outside", drawing, counts);
          hideKeys.push("outside");
          claimed.add("outside");
          tool = "outside";
          continue;
        }
        if (element === "region" || layer.var === REGION_VAR) {
          count += countOf("region", drawing, counts);
          hideKeys.push("region");
          claimed.add("region");
          tool = "region";
          continue;
        }
        if (!DRAW_TOOLS.includes(element)) continue;
        count += counts
          ? countOf(element, drawing, counts)
          : Object.keys(valuesForLayer(layer, drawing, null)).length;
        hideKeys.push(element);
        claimed.add(element);
        tool = element;
      }
      for (const layer of outputs) {
        const values = (layer.var && result?.values?.[layer.var]) || {};
        const n = Object.keys(values).length;
        if (n) {
          count += n;
          const element = layer.element as DrawTool;
          hideKeys.push(`out:${element}`);
          role = inputs.length ? "input" : "output";
          if (DRAW_TOOLS.includes(element)) tool = element;
        }
      }
      if (count === 0) continue;
      const label = inputs[0]?.label || outputs[0]?.label || variable.doc || variable.kind;
      rows.push({
        id: `var:${variable.name}`,
        title: variable.name,
        detail: `${label} · ${variable.kind}`,
        count,
        tool,
        hideKeys: [...new Set(hideKeys)],
        role,
      });
    }

    if (spec.usesRegions && countOf("region", drawing, counts) > 0 && !claimed.has("region")) {
      claimed.add("region");
      rows.push({
        id: "var:regions",
        title: "regions",
        detail: "房间",
        count: countOf("region", drawing, counts),
        tool: "region",
        hideKeys: ["region"],
        role: "input",
      });
    }
  }

  for (const tool of DRAW_TOOLS) {
    if (claimed.has(tool)) continue;
    const count = countOf(tool, drawing, counts);
    if (!count) continue;
    rows.push({
      id: `draw:${tool}`,
      title: TOOL_BY_ID[tool].label,
      detail: "未绑定",
      count,
      tool,
      hideKeys: [tool],
      role: "drawing",
    });
  }

  return rows;
}
