/**
 * Layer renderers, looked up by generic element id — never by puzzle type.
 * Each renderer turns `{point key -> value}` into SVG for one layer.
 */

import { regionColor } from "./editors";
import { cellCentre, cellOrigin, edgeSegment, linkSegment, parsePoint } from "./geometry";
import type { Viewport } from "./geometry";
import { glyph, INK_COLOR } from "./glyphs";
import type { Instance, LayerSpec, PointKey } from "./types";

export interface RenderContext {
  viewport: Viewport;
  layer: LayerSpec;
  instance: Instance;
  values: Record<PointKey, number>;
}

/** Where a marker sits for a given layer target. */
export function anchorFor(v: Viewport, layer: LayerSpec, key: PointKey) {
  if (layer.target === "corner") {
    const p = parsePoint(key, "corner") as { r: number; c: number };
    return { x: v.pad + p.c * v.size, y: v.pad + p.r * v.size };
  }
  if (layer.target === "edge") {
    const p = parsePoint(key, "edge") as { orient: "H" | "V"; r: number; c: number };
    const seg = edgeSegment(v, p.orient, p.r, p.c);
    return { x: (seg.x1 + seg.x2) / 2, y: (seg.y1 + seg.y2) / 2 };
  }
  const p = parsePoint(key, "cell") as { r: number; c: number };
  return cellCentre(v, p.r, p.c);
}

function paletteColor(layer: LayerSpec, value: number): string | undefined {
  return layer.palette?.[String(value)] ?? layer.palette?.["*"];
}

// -- per-element renderers ----------------------------------------------------

function renderShade({ viewport, layer, values }: RenderContext) {
  return (
    <g>
      {Object.entries(values).map(([key, value]) => {
        if (!value) return null;
        const fill = paletteColor(layer, value) ?? INK_COLOR;
        const p = parsePoint(key, "cell") as { r: number; c: number };
        const o = cellOrigin(viewport, p.r, p.c);
        return <rect key={key} x={o.x} y={o.y} width={viewport.size} height={viewport.size} fill={fill} />;
      })}
    </g>
  );
}

function renderNumber({ viewport, layer, values }: RenderContext) {
  const circled = Boolean(layer.options?.circled);
  return (
    <g fontFamily="'Segoe UI', system-ui, sans-serif" fontWeight={600}>
      {Object.entries(values).map(([key, value]) => {
        const at = anchorFor(viewport, layer, key);
        const fill = paletteColor(layer, value) ?? INK_COLOR;
        const size = layer.target === "cell" ? viewport.size : viewport.size * 0.62;
        return (
          <g key={key}>
            {circled && (
              <circle cx={at.x} cy={at.y} r={size * 0.38} fill="#fff" stroke={INK_COLOR} strokeWidth={1.6} />
            )}
            <text x={at.x} y={at.y} textAnchor="middle" dominantBaseline="central" fontSize={size * 0.52} fill={fill}>
              {value}
            </text>
          </g>
        );
      })}
    </g>
  );
}

function renderText({ viewport, layer, values }: RenderContext) {
  return (
    <g fontFamily="'Segoe UI', system-ui, sans-serif" fontWeight={600}>
      {Object.entries(values).map(([key, value]) => {
        const at = anchorFor(viewport, layer, key);
        const fill = paletteColor(layer, value) ?? INK_COLOR;
        return (
          <text key={key} x={at.x} y={at.y} textAnchor="middle" dominantBaseline="central"
            fontSize={viewport.size * 0.52} fill={fill}>
            {value >= 1 && value <= 26 ? String.fromCharCode(64 + value) : value}
          </text>
        );
      })}
    </g>
  );
}

function renderRegion({ viewport, values }: RenderContext) {
  const v = viewport;
  const at = (r: number, c: number): number | undefined => values[`${r},${c}`];
  const tiles: JSX.Element[] = [];
  const borders: JSX.Element[] = [];
  for (const [key, value] of Object.entries(values)) {
    if (value === undefined || value === null) continue;
    const p = parsePoint(key, "cell") as { r: number; c: number };
    const o = cellOrigin(v, p.r, p.c);
    tiles.push(
      <rect key={key} x={o.x} y={o.y} width={v.size} height={v.size} fill={regionColor(value)} opacity={0.55} />,
    );
    // Thick border wherever the neighbour has a different (or no) region id.
    const sides: Array<["H" | "V", number, number, number | undefined]> = [
      ["H", p.r, p.c, at(p.r - 1, p.c)],
      ["H", p.r + 1, p.c, at(p.r + 1, p.c)],
      ["V", p.r, p.c, at(p.r, p.c - 1)],
      ["V", p.r, p.c + 1, at(p.r, p.c + 1)],
    ];
    for (const [orient, er, ec, other] of sides) {
      if (other === value) continue;
      const seg = edgeSegment(v, orient, er, ec);
      borders.push(
        <line key={`${key}:${orient}${er},${ec}`} x1={seg.x1} y1={seg.y1} x2={seg.x2} y2={seg.y2}
          stroke="#3a4750" strokeWidth={3} strokeLinecap="square" />,
      );
    }
  }
  return (
    <g>
      {tiles}
      {borders}
    </g>
  );
}

function renderEdgeline({ viewport, layer, values }: RenderContext) {
  const stroke = layer.palette?.["1"] ?? INK_COLOR;
  return (
    <g stroke={stroke} strokeWidth={4} strokeLinecap="round">
      {Object.entries(values).map(([key, value]) => {
        if (!value) return null;
        const p = parsePoint(key, "edge") as { orient: "H" | "V"; r: number; c: number };
        const seg = edgeSegment(viewport, p.orient, p.r, p.c);
        return <line key={key} x1={seg.x1} y1={seg.y1} x2={seg.x2} y2={seg.y2} />;
      })}
    </g>
  );
}

function renderLink({ viewport, layer, values }: RenderContext) {
  const stroke = layer.palette?.["1"] ?? "#2f8f46";
  return (
    <g stroke={stroke} strokeWidth={viewport.size * 0.14} strokeLinecap="round">
      {Object.entries(values).map(([key, value]) => {
        if (!value) return null;
        const p = parsePoint(key, "edge") as { orient: "H" | "V"; r: number; c: number };
        const seg = linkSegment(viewport, p.orient, p.r, p.c);
        if (!seg) return null;
        return <line key={key} x1={seg.x1} y1={seg.y1} x2={seg.x2} y2={seg.y2} />;
      })}
    </g>
  );
}

function renderGlyphLayer(ctx: RenderContext) {
  const { viewport, layer, values } = ctx;
  return (
    <g>
      {Object.entries(values).map(([key, value]) => {
        if (!value && layer.element !== "arrow") return null;
        const at = anchorFor(viewport, layer, key);
        const size = layer.target === "cell" ? viewport.size : viewport.size * 0.7;
        return <g key={key}>{glyph(layer.element, value, at.x, at.y, size, paletteColor(layer, value))}</g>;
      })}
    </g>
  );
}

export function renderLayer(ctx: RenderContext): JSX.Element | null {
  switch (ctx.layer.element) {
    case "shade": return renderShade(ctx);
    case "number": return renderNumber(ctx);
    case "text": return renderText(ctx);
    case "region": return renderRegion(ctx);
    case "edgeline": return renderEdgeline(ctx);
    case "link": return renderLink(ctx);
    case "outside": return null; // drawn by the board (reads params, not values)
    default: return renderGlyphLayer(ctx);
  }
}
