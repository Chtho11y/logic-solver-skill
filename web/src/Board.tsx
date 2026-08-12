/**
 * The board: renders the frame plus every visible layer, and turns pointer
 * gestures into edits according to the active layer's editor kind.
 */

import { useRef } from "react";
import { cycleValues, editorOf } from "./editors";
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
import { layerValues, outsideText, paramEntry } from "./instance";
import { anchorFor, renderLayer } from "./render";
import type { Brush, Instance, LayerSpec, PuzzleSpec, Selection, SolveResult } from "./types";

export interface BoardProps {
  spec: PuzzleSpec;
  instance: Instance;
  result: SolveResult | null;
  viewport: Viewport;
  visible: Record<string, boolean>;
  activeLayer: LayerSpec | null;
  brush: Brush;
  selection: Selection | null;
  draft: string;
  onEdit: (layer: LayerSpec, key: string, value: number | null) => void;
  onSelect: (selection: Selection | null) => void;
}

type Drag = { kind: "paint" | "toggle"; value: number | null } | null;

export function Board(props: BoardProps) {
  const { spec, instance, result, viewport, visible, activeLayer, brush, selection, draft } = props;
  const svgRef = useRef<SVGSVGElement>(null);
  const dragRef = useRef<Drag>(null);

  const v = viewport;
  const width = v.cols * v.size + v.pad * 2;
  const height = v.rows * v.size + v.pad * 2;

  function toSvg(e: React.PointerEvent): { x: number; y: number } {
    const rect = svgRef.current!.getBoundingClientRect();
    return {
      x: ((e.clientX - rect.left) / rect.width) * width,
      y: ((e.clientY - rect.top) / rect.height) * height,
    };
  }

  function valuesOf(layer: LayerSpec) {
    return layerValues(layer, instance, result);
  }

  function applyAt(x: number, y: number, button: number, drag: boolean) {
    const layer = activeLayer;
    if (!layer || layer.role === "output") return;
    const editor = editorOf(layer);

    if (editor === "paint") {
      const cell = pickCell(v, x, y);
      if (!cell) return;
      const key = `${cell.r},${cell.c}`;
      let value: number | null;
      if (drag && dragRef.current?.kind === "paint") {
        value = dragRef.current.value;
      } else {
        value = button === 2 || brush === "erase" ? null : typeof brush === "number" ? brush : 1;
        if (!drag && value !== null && valuesOf(layer)[key] === value) value = null; // click same → erase
        dragRef.current = { kind: "paint", value };
      }
      props.onEdit(layer, key, value);
      return;
    }

    if (editor === "toggle") {
      const edge = pickEdge(v, x, y);
      if (!edge) return;
      if (layer.element === "link" && !linkSegment(v, edge.orient, edge.r, edge.c)) return;
      const key = edgeKey(edge.orient, edge.r, edge.c);
      let value: number | null;
      if (drag && dragRef.current?.kind === "toggle") {
        value = dragRef.current.value;
      } else {
        value = button === 2 ? null : valuesOf(layer)[key] ? null : 1;
        dragRef.current = { kind: "toggle", value };
      }
      props.onEdit(layer, key, value);
      return;
    }

    if (drag) return;

    const pointKeyAt = (): string | null => {
      if (layer.target === "edge") {
        const edge = pickEdge(v, x, y);
        return edge ? edgeKey(edge.orient, edge.r, edge.c) : null;
      }
      const p = layer.target === "corner" ? pickCorner(v, x, y) : pickCell(v, x, y);
      return p ? `${p.r},${p.c}` : null;
    };

    if (editor === "cycle" || editor === "direction") {
      const key = pointKeyAt();
      if (!key) return;
      if (button === 2 || brush === "erase") {
        props.onEdit(layer, key, null);
        return;
      }
      if (typeof brush === "number") {
        props.onEdit(layer, key, valuesOf(layer)[key] === brush ? null : brush);
        return;
      }
      const cycle = cycleValues(layer);
      const current = valuesOf(layer)[key];
      const idx = current === undefined ? -1 : cycle.indexOf(current);
      const next = idx + 1 >= cycle.length ? null : cycle[idx + 1];
      props.onEdit(layer, key, next);
      return;
    }

    if (editor === "int" || editor === "text") {
      const key = pointKeyAt();
      if (!key) {
        props.onSelect(null);
        return;
      }
      if (button === 2) {
        props.onEdit(layer, key, null);
        return;
      }
      props.onSelect({ kind: "point", layerId: layer.id, key });
    }
  }

  function handleDown(e: React.PointerEvent) {
    if (e.button !== 0 && e.button !== 2) return;
    const { x, y } = toSvg(e);
    // Outside the board → outside-clue slot or deselect.
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

  // -- outside clue slots -----------------------------------------------------

  const outsideLayers = spec.layers.filter(
    (layer) => layer.target === "outside" && visible[layer.id] !== false,
  );
  const sides = new Set<string>();
  for (const layer of outsideLayers) {
    for (const side of (layer.options?.sides as string[]) ?? []) sides.add(side);
  }

  function pickOutside(x: number, y: number): Selection | null {
    const layer = outsideLayers.find((l) => l.id === activeLayer?.id) ?? outsideLayers[0];
    if (!layer) return null;
    const layerSides = ((layer.options?.sides as string[]) ?? []).filter((s) => sides.has(s));
    for (const side of layerSides) {
      if (side === "top" && y < v.pad && x >= v.pad && x <= width - v.pad) {
        return { kind: "outside", layerId: layer.id, side, index: Math.floor((x - v.pad) / v.size) };
      }
      if (side === "bottom" && y > height - v.pad && x >= v.pad && x <= width - v.pad) {
        return { kind: "outside", layerId: layer.id, side, index: Math.floor((x - v.pad) / v.size) };
      }
      if (side === "left" && x < v.pad && y >= v.pad && y <= height - v.pad) {
        return { kind: "outside", layerId: layer.id, side, index: Math.floor((y - v.pad) / v.size) };
      }
      if (side === "right" && x > width - v.pad && y >= v.pad && y <= height - v.pad) {
        return { kind: "outside", layerId: layer.id, side, index: Math.floor((y - v.pad) / v.size) };
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
        const text = isSelected ? draft : outsideText(paramEntry(instance, side, i));
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

  // -- frame + selection --------------------------------------------------------

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
    const layer = spec.layers.find((l) => l.id === selection.layerId);
    if (layer) {
      const at = anchorFor(v, layer, selection.key);
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
  }

  // Cell centre dots on empty boards help orientation for loop puzzles.
  const showDots = spec.layers.some((l) => l.element === "link");
  const dots: JSX.Element[] = [];
  if (showDots) {
    for (let r = 0; r < v.rows; r++) {
      for (let c = 0; c < v.cols; c++) {
        const p = cellCentre(v, r, c);
        dots.push(<circle key={`${r},${c}`} cx={p.x} cy={p.y} r={1.6} fill="#c3ccd4" />);
      }
    }
  }

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
      {spec.layers.map((layer) =>
        visible[layer.id] === false || layer.target === "outside" ? null : (
          <g key={layer.id}>
            {renderLayer({ viewport: v, layer, instance, values: layerValues(layer, instance, result) })}
          </g>
        ),
      )}
      <rect x={v.pad} y={v.pad} width={width - 2 * v.pad} height={height - 2 * v.pad}
        fill="none" stroke="#3a4750" strokeWidth={2.5} />
      {outsideSlots()}
      {selectionNode}
    </svg>
  );
}
