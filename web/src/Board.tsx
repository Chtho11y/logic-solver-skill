/**
 * The board: renders the frame plus every visible drawing tool, then puzzle
 * output overlays after a solve. Gestures follow the active Penpa-like tool.
 */

import { useRef } from "react";
import { cycleValuesFor, EDITOR_OF } from "./editors";
import {
  DRAW_Z_ORDER,
  numericMarks,
  outsideEntry,
  outsideText,
  SIDES,
  TOOL_TARGET,
  toolLayer,
  type DrawTool,
  type Drawing,
} from "./drawing";
import {
  cellCentre,
  edgeKey,
  linkSegment,
  pickCell,
  pickCorner,
  pickEdge,
  viewBox,
} from "./geometry";
import type { Viewport } from "./geometry";
import { anchorFor, renderLayer } from "./render";
import type { Brush, PuzzleSpec, Selection, SolveResult } from "./types";

export interface BoardProps {
  spec: PuzzleSpec | null;
  drawing: Drawing;
  result: SolveResult | null;
  viewport: Viewport;
  visible: Record<string, boolean>;
  activeTool: DrawTool;
  brush: Brush;
  selection: Selection | null;
  draft: string;
  onEdit: (tool: DrawTool, key: string, value: number | null) => void;
  onSelect: (selection: Selection | null) => void;
}

type Drag = { kind: "paint" | "toggle"; value: number | null } | null;

export function Board(props: BoardProps) {
  const { spec, drawing, result, viewport, visible, activeTool, brush, selection, draft } = props;
  const svgRef = useRef<SVGSVGElement>(null);
  const dragRef = useRef<Drag>(null);

  const v = viewport;
  const width = v.cols * v.size + v.pad * 2;
  const height = v.rows * v.size + v.pad * 2;
  const layer = toolLayer(activeTool, spec);

  function toSvg(e: React.PointerEvent): { x: number; y: number } {
    const rect = svgRef.current!.getBoundingClientRect();
    return {
      x: ((e.clientX - rect.left) / rect.width) * width,
      y: ((e.clientY - rect.top) / rect.height) * height,
    };
  }

  function valuesOf(tool: DrawTool): Record<string, number> {
    if (tool === "region") return drawing.regions;
    return numericMarks(drawing.marks[tool]);
  }

  function applyAt(x: number, y: number, button: number, drag: boolean) {
    const editor = EDITOR_OF[activeTool] ?? "none";
    const target = TOOL_TARGET[activeTool];

    if (editor === "paint") {
      const cell = pickCell(v, x, y);
      if (!cell) return;
      const key = `${cell.r},${cell.c}`;
      let value: number | null;
      if (drag && dragRef.current?.kind === "paint") {
        value = dragRef.current.value;
      } else {
        const stamp =
          typeof brush === "number"
            ? brush
            : activeTool === "shade"
              ? drawing.surfaceColor
              : 1;
        value = button === 2 || brush === "erase" ? null : stamp;
        if (!drag && value !== null && valuesOf(activeTool)[key] === value) value = null;
        dragRef.current = { kind: "paint", value };
      }
      props.onEdit(activeTool, key, value);
      return;
    }

    if (editor === "toggle") {
      const edge = pickEdge(v, x, y);
      if (!edge) return;
      if (activeTool === "link" && !linkSegment(v, edge.orient, edge.r, edge.c)) return;
      const key = edgeKey(edge.orient, edge.r, edge.c);
      let value: number | null;
      if (drag && dragRef.current?.kind === "toggle") {
        value = dragRef.current.value;
      } else {
        value = button === 2 || brush === "erase" ? null : valuesOf(activeTool)[key] ? null : 1;
        dragRef.current = { kind: "toggle", value };
      }
      props.onEdit(activeTool, key, value);
      return;
    }

    if (drag) return;

    const pointKeyAt = (): string | null => {
      if (target === "edge") {
        const edge = pickEdge(v, x, y);
        return edge ? edgeKey(edge.orient, edge.r, edge.c) : null;
      }
      const p = target === "corner" ? pickCorner(v, x, y) : pickCell(v, x, y);
      return p ? `${p.r},${p.c}` : null;
    };

    if (editor === "cycle" || editor === "direction") {
      const key = pointKeyAt();
      if (!key) return;
      if (button === 2 || brush === "erase") {
        props.onEdit(activeTool, key, null);
        return;
      }
      if (typeof brush === "number") {
        props.onEdit(activeTool, key, valuesOf(activeTool)[key] === brush ? null : brush);
        return;
      }
      const cycle = cycleValuesFor(activeTool, layer.palette);
      const current = valuesOf(activeTool)[key];
      const idx = current === undefined ? -1 : cycle.indexOf(current);
      const next = idx + 1 >= cycle.length ? null : cycle[idx + 1];
      props.onEdit(activeTool, key, next);
      return;
    }

    if (editor === "int" || editor === "text") {
      const key = pointKeyAt();
      if (!key) {
        props.onSelect(null);
        return;
      }
      if (button === 2) {
        props.onEdit(activeTool, key, null);
        return;
      }
      props.onSelect({ kind: "point", tool: activeTool, key });
    }
  }

  function handleDown(e: React.PointerEvent) {
    if (e.button !== 0 && e.button !== 2) return;
    const { x, y } = toSvg(e);
    if (x < v.pad || y < v.pad || x > width - v.pad || y > height - v.pad) {
      const slot = pickOutside(x, y);
      if (slot) props.onSelect(slot);
      else props.onSelect(null);
      return;
    }
    svgRef.current?.setPointerCapture(e.pointerId);
    applyAt(x, y, e.button, false);
  }

  function handleMove(e: React.PointerEvent) {
    if (!dragRef.current) return;
    const { x, y } = toSvg(e);
    applyAt(x, y, 0, true);
  }

  function handleUp() {
    dragRef.current = null;
  }

  const hasOutsideMarks = SIDES.some((side) => Object.keys(drawing.outside[side] ?? {}).length > 0);
  const specWantsOutside = Boolean(spec?.layers.some((l) => l.target === "outside" && l.role === "input"));
  const showOutside = activeTool === "outside" || hasOutsideMarks || specWantsOutside;
  const sides = showOutside
    ? new Set<string>(
        (spec?.layers.find((l) => l.target === "outside")?.options?.sides as string[]) ?? [...SIDES],
      )
    : new Set<string>();
  if (hasOutsideMarks) {
    for (const side of SIDES) {
      if (Object.keys(drawing.outside[side] ?? {}).length) sides.add(side);
    }
  }
  if (activeTool === "outside") {
    for (const side of SIDES) sides.add(side);
  }

  function pickOutside(x: number, y: number): Selection | null {
    if (!showOutside) return null;
    for (const side of sides) {
      if (side === "top" && y < v.pad && x >= v.pad && x <= width - v.pad) {
        return { kind: "outside", side, index: Math.floor((x - v.pad) / v.size) };
      }
      if (side === "bottom" && y > height - v.pad && x >= v.pad && x <= width - v.pad) {
        return { kind: "outside", side, index: Math.floor((x - v.pad) / v.size) };
      }
      if (side === "left" && x < v.pad && y >= v.pad && y <= height - v.pad) {
        return { kind: "outside", side, index: Math.floor((y - v.pad) / v.size) };
      }
      if (side === "right" && x > width - v.pad && y >= v.pad && y <= height - v.pad) {
        return { kind: "outside", side, index: Math.floor((y - v.pad) / v.size) };
      }
    }
    return null;
  }

  function outsideSlots(): JSX.Element[] {
    const nodes: JSX.Element[] = [];
    for (const side of sides) {
      const count = side === "top" || side === "bottom" ? v.cols : v.rows;
      for (let i = 0; i < count; i++) {
        const isSelected =
          selection?.kind === "outside" && selection.side === side && selection.index === i;
        const text = isSelected ? draft : outsideText(outsideEntry(drawing, side, i));
        const tokens = text.split(/\s+/).filter(Boolean);
        let cx: number, cy: number;
        if (side === "top") { cx = v.pad + i * v.size + v.size / 2; cy = v.pad - 8; }
        else if (side === "bottom") { cx = v.pad + i * v.size + v.size / 2; cy = height - v.pad + 16; }
        else if (side === "left") { cx = v.pad - 8; cy = v.pad + i * v.size + v.size / 2; }
        else { cx = width - v.pad + 8; cy = v.pad + i * v.size + v.size / 2; }

        nodes.push(
          <g key={`${side}:${i}`}>
            {isSelected && (
              <rect
                x={side === "left" ? 2 : side === "right" ? width - v.pad + 2 : v.pad + i * v.size + 2}
                y={side === "top" ? 2 : side === "bottom" ? height - v.pad + 2 : v.pad + i * v.size + 2}
                width={side === "top" || side === "bottom" ? v.size - 4 : v.pad - 4}
                height={side === "left" || side === "right" ? v.size - 4 : v.pad - 4}
                fill="#fff3c4" stroke="#e2b93b" rx={4}
              />
            )}
            {side === "top" || side === "bottom" ? (
              <text x={cx} y={cy} textAnchor="middle" fontSize={14} fontWeight={600} fill="#4a5568">
                {tokens.length > 1
                  ? tokens.map((t, j) => (
                      <tspan key={j} x={cx}
                        y={side === "top" ? cy - (tokens.length - 1 - j) * 15 : cy + j * 15}>
                        {t}
                      </tspan>
                    ))
                  : text || (isSelected ? "_" : "")}
              </text>
            ) : (
              <text x={cx} y={cy} fontSize={14} fontWeight={600} fill="#4a5568"
                textAnchor={side === "left" ? "end" : "start"} dominantBaseline="central">
                {text || (isSelected ? "_" : "")}
              </text>
            )}
          </g>,
        );
      }
    }
    return nodes;
  }

  const gridLines: JSX.Element[] = [];
  for (let r = 0; r <= v.rows; r++) {
    gridLines.push(
      <line key={`h${r}`} x1={v.pad} y1={v.pad + r * v.size} x2={width - v.pad} y2={v.pad + r * v.size} />,
    );
  }
  for (let c = 0; c <= v.cols; c++) {
    gridLines.push(
      <line key={`v${c}`} x1={v.pad + c * v.size} y1={v.pad} x2={v.pad + c * v.size} y2={height - v.pad} />,
    );
  }

  let selectionNode: JSX.Element | null = null;
  if (selection?.kind === "point") {
    const selLayer = toolLayer(selection.tool as DrawTool, spec);
    const at = anchorFor(v, selLayer, selection.key);
    selectionNode = (
      <g>
        <rect x={at.x - v.size / 2 + 1.5} y={at.y - v.size / 2 + 1.5} width={v.size - 3} height={v.size - 3}
          fill="none" stroke="#e2a93b" strokeWidth={3} rx={3} />
        {draft !== "" && (
          <text x={at.x} y={at.y} textAnchor="middle" dominantBaseline="central"
            fontSize={v.size * 0.5} fontWeight={700} fill="#1565c0">
            {draft}
          </text>
        )}
      </g>
    );
  }

  const showDots =
    activeTool === "link" ||
    Boolean(drawing.marks.link && Object.keys(drawing.marks.link).length) ||
    Boolean(spec?.layers.some((l) => l.element === "link"));
  const dots: JSX.Element[] = [];
  if (showDots) {
    for (let r = 0; r < v.rows; r++) {
      for (let c = 0; c < v.cols; c++) {
        const p = cellCentre(v, r, c);
        dots.push(<circle key={`${r},${c}`} cx={p.x} cy={p.y} r={1.6} fill="#c3ccd4" />);
      }
    }
  }

  const outputLayers = spec?.layers.filter((l) => l.role === "output") ?? [];

  return (
    <svg
      ref={svgRef}
      className="board-svg"
      viewBox={viewBox(v)}
      onPointerDown={handleDown}
      onPointerMove={handleMove}
      onPointerUp={handleUp}
      onContextMenu={(e) => e.preventDefault()}
    >
      <rect x={v.pad} y={v.pad} width={width - 2 * v.pad} height={height - 2 * v.pad} fill="#ffffff" />
      <g stroke="#ccd3da" strokeWidth={1}>{gridLines}</g>
      {dots}
      {DRAW_Z_ORDER.map((tool) => {
        if (visible[tool] === false) return null;
        const values = valuesOf(tool);
        if (!Object.keys(values).length) return null;
        return (
          <g key={tool}>
            {renderLayer({ viewport: v, layer: toolLayer(tool, spec), values })}
          </g>
        );
      })}
      {outputLayers.map((outLayer) => {
        if (visible[`out:${outLayer.id}`] === false) return null;
        const values = (outLayer.var && result?.values?.[outLayer.var]) || {};
        if (!Object.keys(values).length) return null;
        return (
          <g key={`out:${outLayer.id}`} className="solve-overlay">
            {renderLayer({ viewport: v, layer: outLayer, values })}
          </g>
        );
      })}
      <rect x={v.pad} y={v.pad} width={width - 2 * v.pad} height={height - 2 * v.pad}
        fill="none" stroke="#3a4750" strokeWidth={2.5} />
      {outsideSlots()}
      {selectionNode}
    </svg>
  );
}
